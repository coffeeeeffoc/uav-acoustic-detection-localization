"""Amplitude-invariant spectral/spatial detector; development uses the old dataset only."""
import argparse
import hashlib
import inspect
import json
import time
from pathlib import Path

from experiment import ROOT, N, FS, Engine, write_json, write_csv
import numpy as np
from scipy import fft, ndimage, signal, linalg
from scipy.spatial.distance import cdist
from summarize_experiment import roc, read_csv


def features(audio):
    if audio.shape != (N, 8) or not np.isfinite(audio).all():
        raise ValueError('Expected finite (1600,8) frame')
    x = audio.T.astype(float)
    x -= x.mean(axis=1, keepdims=True)
    x /= max(np.sqrt(np.mean(x * x)), 1e-15)
    values = []
    spectrum = np.mean(np.abs(fft.rfft(x * signal.windows.hann(N, sym=False), n=2048)) ** 2, axis=0)
    spectrum /= max(spectrum.sum(), 1e-15)
    freq = fft.rfftfreq(2048, 1 / FS)
    floor = ndimage.median_filter(spectrum, size=31, mode='nearest')
    z = ndimage.gaussian_filter1d(np.log1p(spectrum / np.maximum(floor, 1e-15)) - np.log(2), 1)
    for lo, hi in [(80, 3000), (80, 400), (400, 1000), (1000, 2000), (2000, 3000)]:
        mask = (freq >= lo) & (freq <= hi)
        p = spectrum[mask] + 1e-15
        p /= p.sum()
        values.extend([np.log(spectrum[mask].sum() + 1e-15),
                       np.exp(np.log(p).mean()) / p.mean(),
                       -(p * np.log(p)).sum() / np.log(len(p)),
                       *np.quantile(z[mask], [.5, .9, .99]), np.std(z[mask])])
    f0 = np.arange(80, 241, 2)
    harmonic = np.arange(1, 13)
    comb = (z[np.rint(f0[:, None] * harmonic * 2048 / FS).astype(int)] / np.sqrt(harmonic)).mean(axis=1)
    first = int(np.argmax(comb))
    separated = np.abs(f0 - f0[first]) >= 20
    values.extend([comb[first], np.max(comb[separated]), np.mean(comb), np.std(comb)])
    for size, hop in [(512, 256), (1024, 256)]:
        blocks = np.lib.stride_tricks.sliding_window_view(x, size, axis=1)[:, ::hop]
        X = fft.rfft(blocks * signal.windows.hann(size, sym=False), axis=-1)
        covariance = np.einsum('mlk,nlk->kmn', X, X.conj()) / X.shape[1]
        powers = np.real(np.diagonal(covariance, axis1=1, axis2=2))
        eig = np.maximum(np.linalg.eigvalsh(covariance), 0)
        eig /= np.maximum(eig.sum(axis=1, keepdims=True), 1e-15)
        i, j = np.triu_indices(8, 1)
        coherence = np.abs(covariance[:, i, j]) ** 2 / np.maximum(powers[:, i] * powers[:, j], 1e-15)
        coherence = np.clip(coherence.mean(axis=1), 0, 1)
        freq = fft.rfftfreq(size, 1 / FS)
        for lo, hi in [(200, 3000), (200, 800), (800, 1600), (1600, 3000)]:
            mask = (freq >= lo) & (freq <= hi)
            values.extend([*np.quantile(coherence[mask], [.25, .5, .9]),
                           np.mean(eig[mask, -1]), np.mean(eig[mask, -2]),
                           np.std(eig[mask, -1])])
    result = np.asarray(values)
    assert result.shape == (87,) and np.isfinite(result).all()
    return result


def feature_digest():
    return hashlib.sha256((inspect.getsource(features) + f'FS={FS};N={N}').encode()).hexdigest()


MIXES = {'engine_engine': ('engine', 'engine'),
         'directional_directional': ('directional', 'directional'),
         'engine_directional': ('engine', 'directional'),
         'engine_directional_engine': ('engine', 'directional', 'engine')}


def mix_audio(parts, rng):
    weights = 10 ** (rng.uniform(-6, 6, len(parts)) / 20)
    audio = sum(weight * part for weight, part in zip(weights, parts))
    audio /= max(float(np.sqrt(np.mean(audio.astype(float) ** 2))), 1e-15)
    return audio.astype(np.float32), weights.tolist()


def augmented_negatives(out, input_hash, train, valid):
    cache = out / 'augmented_features.npz'
    signature = hashlib.sha256((inspect.getsource(mix_audio) + input_hash
                               + json.dumps([train.tolist(), valid.tolist(), MIXES, [150, 50]])).encode()).hexdigest()
    if cache.exists():
        with np.load(cache) as saved:
            if str(saved['signature']) == signature and str(saved['feature_sha256']) == feature_digest():
                return saved['features'], saved['training'].astype(bool)
    records = read_csv(out / 'items.csv')
    X, training, provenance = [], [], []
    folder = ROOT / 'data/synthetic/development_augmented'
    folder.mkdir(parents=True, exist_ok=True)
    for fold, indices, count in [('train', train, 150), ('validation', valid, 50)]:
        pools = {scene: [records[i]['trial_id'] for i in indices
                        if records[i]['label'] == 0 and records[i]['scene'] == scene]
                 for scene in ('engine', 'directional')}
        for group_index, (group, scenes) in enumerate(MIXES.items()):
            for repeat in range(count):
                rng = np.random.default_rng(np.random.SeedSequence([48291, int(fold == 'train'), group_index, repeat]))
                ids, audio_parts = [], []
                for scene in scenes:
                    candidates = [item for item in pools[scene] if item not in ids]
                    item = str(rng.choice(candidates))
                    ids.append(item)
                    with np.load(ROOT / f'data/synthetic/full/test/{item}.npz') as saved:
                        audio_parts.append(saved['audio'])
                audio, weights = mix_audio(audio_parts, rng)
                trial_id = f'{fold}-{group}-{repeat:03}'
                meta = {'trial_id': trial_id, 'fold': fold, 'group': group, 'label': 0,
                        'source_ids': ids, 'weights': weights, 'input_sha256': input_hash}
                np.savez_compressed(folder / f'{trial_id}.npz', audio=audio, sample_rate=FS,
                                    label=np.array([0]), metadata_json=json.dumps(meta))
                X.append(features(audio))
                training.append(fold == 'train')
                provenance.append(meta)
            print('hard-negative development', fold, group, flush=True)
    np.savez_compressed(cache, features=np.stack(X), training=np.array(training),
                        signature=signature, feature_sha256=feature_digest())
    write_json(out / 'augmentation.json', provenance)
    # A recording contributing to training cannot contribute to internal validation.
    train_ids = {item for row in provenance if row['fold'] == 'train' for item in row['source_ids']}
    valid_ids = {item for row in provenance if row['fold'] == 'validation' for item in row['source_ids']}
    assert train_ids.isdisjoint(valid_ids)
    return np.stack(X), np.array(training)


class Detector:
    """Gaussian-kernel ridge score. Fit uses labels; inference never does."""
    def fit(self, X, y, width=2.0, ridge=.1):
        if X.ndim != 2 or len(y) != len(X) or X.shape[1] not in (39, 87):
            raise ValueError('Expected aligned labels and a 39- or 87-feature matrix')
        if not np.isfinite(X).all() or not np.isin(y, [0, 1]).all() or width <= 0 or ridge <= 0:
            raise ValueError('Invalid training observations or kernel parameters')
        self.feature_count = int(X.shape[1])
        self.center = X.mean(axis=0)
        self.scale = np.maximum(X.std(axis=0), .05)
        self.training = (X - self.center) / self.scale
        self.width = float(width)
        distance = cdist(self.training, self.training, metric='sqeuclidean') / X.shape[1]
        kernel = np.exp(-distance / (2 * width ** 2))
        self.coefficients = linalg.solve(kernel + ridge * np.eye(len(X)), 2 * y - 1, assume_a='pos')
        self.ridge = float(ridge)
        return self

    def predict(self, X):
        X = np.atleast_2d(X)
        if X.shape[1] != int(self.feature_count) or not np.isfinite(X).all():
            raise ValueError('Feature dimension or values disagree with the fitted model')
        distance = cdist((X - self.center) / self.scale, self.training, metric='sqeuclidean') / X.shape[1]
        return np.exp(-distance / (2 * self.width ** 2)) @ self.coefficients

    def analyze(self, audio):
        # The 39-feature ablation is the fixed spectral prefix of the 87-feature vector.
        return float(self.predict(features(audio)[:int(self.feature_count)])[0])

    def save(self, path):
        np.savez_compressed(path, center=self.center, scale=self.scale, training=self.training,
                            coefficients=self.coefficients, width=self.width, ridge=self.ridge,
                            feature_sha256=feature_digest(), feature_count=self.feature_count)

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path) as saved:
            if str(saved['feature_sha256']) != feature_digest():
                raise ValueError('Model was trained with a different feature implementation')
            for key in saved.files:
                setattr(model, key, saved[key])
        if int(model.feature_count) not in (39, 87) or model.center.size != int(model.feature_count):
            raise ValueError('Invalid model feature contract')
        return model


def develop():
    out = ROOT / 'results/development_detector'
    out.mkdir(parents=True, exist_ok=True)
    cache = out / 'features.npz'
    inputs = sorted((ROOT / 'data/synthetic/full/test').glob('*.npz'))
    inventory = [(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) for p in inputs]
    input_digest = hashlib.sha256(json.dumps(inventory).encode()).hexdigest()
    valid_cache = False
    if cache.exists():
        with np.load(cache) as saved:
            valid_cache = ('feature_sha256' in saved.files and 'input_sha256' in saved.files
                           and str(saved['feature_sha256']) == feature_digest()
                           and str(saved['input_sha256']) == input_digest)
    if not valid_cache:
        rows, X, y = [], [], []
        for index, path in enumerate(inputs):
            with np.load(path) as data:
                X.append(features(data['audio']))
                y.append(int(data['label'][0]))
                metadata = json.loads(str(data['metadata_json']))
            rows.append({'trial_id': path.stem, 'label': y[-1], 'scene': metadata['scene'], 'snr_db': metadata['snr_db']})
            if index % 200 == 0:
                print('development features', index, flush=True)
        np.savez_compressed(cache, features=np.stack(X), labels=np.array(y),
                            feature_sha256=feature_digest(), input_sha256=input_digest)
        write_csv(out / 'items.csv', rows)
    with np.load(cache) as data:
        X, y = data['features'], data['labels']
    rng = np.random.default_rng(90210)
    # Old results are development-only even when this internal split is held out.
    train = np.concatenate([rng.permutation(np.where(y == label)[0])[:750] for label in (0, 1)])
    valid = np.setdiff1d(np.arange(len(y)), train)
    augmented, train_mask = augmented_negatives(out, input_digest, train, valid)
    start = len(y)
    X = np.concatenate([X, augmented])
    y = np.r_[y, np.zeros(len(augmented), dtype=int)]
    train = np.r_[train, start + np.where(train_mask)[0]]
    valid = np.r_[valid, start + np.where(~train_mask)[0]]
    variants, selected = [], {}
    for name, count in [('full', 87), ('spectral', 39)]:
        candidates = []
        for width in (1., 2., 4.):
            for ridge in (.01, .1, 1.):
                model = Detector().fit(X[train, :count], y[train], width, ridge)
                score = model.predict(X[valid, :count])
                auc = roc([{'score': float(s), 'label': int(label)} for s, label in zip(score, y[valid])])[0]
                threshold = np.quantile(score[y[valid] == 0], .95)
                row = {'features': name, 'width': width, 'ridge': ridge, 'development_auc': auc,
                       'development_recall_at_empirical_5pct_fpr': float(np.mean(score[y[valid] == 1] > threshold))}
                candidates.append(row)
                print(row, flush=True)
        best = max(candidates, key=lambda row: row['development_auc'])
        variants.extend(candidates)
        selected[name] = best
        model = Detector().fit(X[:, :count], y, best['width'], best['ridge'])
        model.save(out / ('model.npz' if name == 'full' else 'model_spectral.npz'))
    write_json(out / 'selection.json', {'development_only': True, 'training_items': len(y),
               'features': X.shape[1], 'selection_criterion': 'internal development ROC AUC',
               'variants': variants, 'selected': selected,
               'features_include_absolute_amplitude': False,
               'feature_sha256': feature_digest(), 'input_sha256': input_digest,
               'model_sha256': hashlib.sha256((out / 'model.npz').read_bytes()).hexdigest(),
               'spectral_model_sha256': hashlib.sha256((out / 'model_spectral.npz').read_bytes()).hexdigest(),
               'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


def self_test():
    from experiment import simulate
    from tempfile import TemporaryDirectory
    audio, _, _ = simulate((1090, 1), 'engine', -5)
    reference = features(audio)
    assert np.allclose(reference, features(audio.astype(float) * .003), atol=1e-10)
    assert np.allclose(reference, features(audio.astype(float) * 73), atol=1e-10)
    assert np.isfinite(features(np.zeros((N, 8)))).all()
    try:
        features(np.zeros((10, 8)))
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid audio accepted')
    X = np.stack([features(simulate((1090, i + 2), 'engine', -5 if i % 2 else None)[0]) for i in range(6)])
    with TemporaryDirectory() as temp:
        for count in (39, 87):
            model = Detector().fit(X[:, :count], np.arange(6) % 2)
            path = Path(temp) / f'{count}.npz'
            model.save(path)
            loaded = Detector.load(path)
            assert abs(loaded.analyze(audio) - model.analyze(audio)) < 1e-12
            assert abs(loaded.analyze(audio.astype(float) * .003) - loaded.analyze(audio)) < 1e-9
    print('Detector scale invariance, zero/input contracts and both model serialization paths passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    self_test() if args.self_test else develop()
