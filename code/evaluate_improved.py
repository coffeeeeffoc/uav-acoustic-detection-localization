"""One frozen fresh evaluation: shared observations, independent calibration, hard negatives."""
import argparse
import hashlib
import json
import time
import platform
import sys
from pathlib import Path

from experiment import (ROOT, SCENES, SNRS, N, FS, Engine, simulate, errors, calibrate,
                        save_audio, write_json, write_csv)
from improved_detector import Detector, features, MIXES, mix_audio
from improved_localizer import ImprovedLocalizer
from summarize_experiment import read_csv, detection, localization, bootstrap_mean, roc, wilson
import numpy as np

OUT = ROOT / 'results/improved'
DATA = ROOT / 'data/synthetic/improved'
DETECTORS = ('harmonic_coherence', 'spectral', 'proposed')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def negative(split, group_index, trial):
    groups = list(SCENES) + list(MIXES)
    group = groups[group_index]
    if group_index < 4:
        return simulate((split, group_index, trial, 0), group)
    sources, metadata, seeds, component_hashes = [], [], [], []
    for index, scene in enumerate(MIXES[group]):
        parts = (split, group_index, trial, index + 1)
        audio, _, meta = simulate(parts, scene)
        sources.append(audio)
        component_hashes.append(hashlib.sha256(audio.tobytes(order='C')).hexdigest())
        metadata.append(meta)
        seeds.append(list(parts))
    rng = np.random.default_rng(np.random.SeedSequence([20261002, split, group_index, trial, 99]))
    audio, weights = mix_audio(sources, rng)
    truth = {'az': np.array([0.]), 'el': np.array([0.]), 'label': np.array([0]),
             'measured_snr': np.array([-300.])}
    meta = {'scene': group, 'snr_db': None, 'seed_parts': [split, group_index, trial],
            'component_seed_parts': seeds, 'components': metadata, 'weights': weights,
            'component_audio_sha256': component_hashes,
            'component_hash_encoding': 'float32, C-order, sample-major (1600,8)',
            'target_present': False}
    return audio, truth, meta


def run():
    if (OUT / 'frozen_config.json').exists():
        raise RuntimeError('Fresh experiment already frozen; preserve it instead of silently rerunning')
    models = {name: Detector.load(ROOT / 'results/development_detector' / filename)
              for name, filename in [('proposed', 'model.npz'), ('spectral', 'model_spectral.npz')]}
    localizer, baseline = ImprovedLocalizer(), Engine()
    no_null = ImprovedLocalizer(model_path=ROOT / 'results/development_localizer/candidate_ranker_no_null_model.npz')
    sources = [ROOT / 'code' / name for name in ('experiment.py', 'improved_detector.py',
               'improved_localizer.py', 'evaluate_improved.py', 'summarize_experiment.py', 'requirements-lock.txt')]
    sources.append(ROOT / 'research/algorithm_revision_protocol.md')
    model_paths = list((ROOT / 'results/development_detector').glob('model*.npz'))
    model_paths += [p for p in (ROOT / 'results/development_localizer').glob('*.npz') if 'model' in p.name]
    model_paths += list((ROOT / 'results/development_localizer').glob('*model*.json'))
    frozen = {'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
              'model_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in model_paths},
              'master_seed': 20261002, 'calibration_split': 1101, 'negative_test_split': 1102,
              'positive_test_split': 1103, 'sensitivity_split': 1104, 'sequence_split': 1105,
              'calibration_n': 800, 'test_positive_n': 1000, 'test_negative_n': 2000,
              'negative_groups': list(SCENES) + list(MIXES), 'positive_scenes': list(SCENES),
              'snr_db': list(SNRS), 'detector_alpha': .05, 'strict_threshold': True,
              'development_data': 'old full/test plus 800 old-source hard-negative mixtures',
              'inference_contract': 'only audio plus fixed learned parameters/array',
              'runtime': {'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__,
                          'thread_request': 1, 'frame_seconds': N / FS,
                          'timing_excludes': 'acquisition, synthesis, file IO, initialization, display'},
              'protocol': 'research/algorithm_revision_protocol.md'}
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / 'frozen_config.json', frozen)
    calibration = []
    start = time.perf_counter()
    # Initialization/warm-up excluded from compute measurements.
    warm = simulate((1190, 0), 'sensor_noise', 0)[0]
    baseline.analyze(warm)
    localizer.analyze(warm)
    no_null.analyze(warm)
    for model in models.values():
        model.analyze(warm)

    def scores(audio, old=None):
        old = baseline.analyze(audio) if old is None else old
        begin = time.perf_counter_ns()
        vector = features(audio)
        result = {'harmonic_coherence': old['score']}
        for name, model in models.items():
            result[name] = float(model.predict(vector[:int(model.feature_count)])[0])
        return result, (time.perf_counter_ns() - begin) / 1e6

    for group in range(8):
        for trial in range(100):
            audio, truth, meta = negative(1101, group, trial)
            trial_id = f'cal-{group}-{trial:03}'
            save_audio(DATA / 'calibration' / trial_id, audio, truth, meta)
            score, _ = scores(audio)
            calibration.append({'trial_id': trial_id, 'scene': meta['scene'], **score})
        print('calibration group', group, flush=True)
    threshold = {name: calibrate([row[name] for row in calibration])[0] for name in DETECTORS}
    write_csv(OUT / 'calibration.csv', calibration)
    write_json(OUT / 'thresholds.json', {'thresholds': threshold, 'n': 800, 'order': 761,
               'rule': 'strict score > threshold',
               'validation_fpr': {name: float(np.mean([r[name] > threshold[name] for r in calibration]))
                                  for name in DETECTORS}})
    detector_rows, local_rows, timing_rows = [], [], []

    def evaluate(trial_id, split, audio, truth, meta, frame=None):
        old = baseline.analyze(audio)
        score, detect_ms = scores(audio, old)
        tic = time.perf_counter_ns()
        estimate = localizer.analyze(audio)
        local_ms = (time.perf_counter_ns() - tic) / 1e6
        # Ablation runs separately and is excluded from proposed-pipeline timing.
        no_null_estimate = no_null.analyze(audio)
        label = int(truth['label'][0])
        base = {'trial_id': trial_id, 'split': split, 'scene': meta['scene'], 'snr_db': meta['snr_db'],
                'label': label, 'frame': frame}
        drows = [{**base, 'detector': name, 'score': score[name], 'detected': int(score[name] > threshold[name])}
                 for name in DETECTORS]
        lrows = []
        if label:
            for method, item in {**old['methods'], 'no_null': no_null_estimate, 'proposed': estimate}.items():
                sphere, azerr, elerr = errors(item['az_hat'], item['el_hat'], truth['az'][0], truth['el'][0])
                lrows.append({**base, 'method': method, 'az_hat': item['az_hat'], 'el_hat': item['el_hat'],
                              'true_az': float(truth['az'][0]), 'true_el': float(truth['el'][0]),
                              'angular_error_deg': float(sphere), 'az_error_deg': float(azerr),
                              'el_error_deg': float(elerr), 'detected': int(score['proposed'] > threshold['proposed']),
                              'original_detected': int(score['harmonic_coherence'] > threshold['harmonic_coherence']),
                              'spectral_detected': int(score['spectral'] > threshold['spectral'])})
        timing = {**base, 'shared_full_and_spectral_detector_ms': detect_ms, 'localizer_ms': local_ms,
                  'proposed_pipeline_upper_bound_ms': detect_ms + local_ms,
                  'phat_front_and_search_ms': old['frontend_ms'] + old['methods']['phat']['search_ms']}
        return drows, lrows, timing

    for group in range(8):
        for trial in range(250):
            audio, truth, meta = negative(1102, group, trial)
            trial_id = f'neg-{group}-{trial:03}'
            save_audio(DATA / 'test' / trial_id, audio, truth, meta)
            d, l, t = evaluate(trial_id, 'test', audio, truth, meta)
            detector_rows.extend(d)
            timing_rows.append(t)
        print('test negative group', group, flush=True)
    for scene_index, scene in enumerate(SCENES):
        for snr_index, snr in enumerate(SNRS):
            for trial in range(50):
                audio, truth, meta = simulate((1103, scene_index, snr_index, trial), scene, snr)
                trial_id = f'pos-{scene_index}-{snr_index}-{trial:03}'
                save_audio(DATA / 'test' / trial_id, audio, truth, meta)
                d, l, t = evaluate(trial_id, 'test', audio, truth, meta)
                detector_rows.extend(d)
                local_rows.extend(l)
                timing_rows.append(t)
        print('test positive scene', scene, flush=True)
    write_csv(OUT / 'detection_frames.csv', detector_rows)
    write_csv(OUT / 'localization_frames.csv', local_rows)
    write_csv(OUT / 'timing_frames.csv', timing_rows)
    # Quantitative headline evidence is now frozen. Additional stress tests keep all outcomes.
    sequence_detection, sequence_localization = [], []
    for scene_index, scene in enumerate(SCENES):
        for snr_index, snr in enumerate((-10, -5, 0)):
            for repeat in range(2):
                audio, truth, meta = simulate((1105, scene_index, snr_index, repeat), scene, snr,
                                               duration=24, dynamic=True)
                sequence = f'seq-{scene_index}-{snr_index}-{repeat}'
                save_audio(DATA / 'sequences' / sequence, audio, truth, meta)
                for frame in range(len(audio) // N):
                    frame_truth = {key: value[frame:frame + 1] for key, value in truth.items()}
                    d, l, _ = evaluate(sequence, 'sequence', audio[frame * N:(frame + 1) * N],
                                        frame_truth, meta, frame)
                    sequence_detection.extend(d)
                    sequence_localization.extend(l)
        print('continuous scene', scene, flush=True)
    write_csv(OUT / 'sequence_detection.csv', sequence_detection)
    write_csv(OUT / 'sequence_localization.csv', sequence_localization)
    for relative, expected in {**frozen['source_sha256'], **frozen['model_sha256']}.items():
        assert sha(ROOT / relative) == expected, 'A frozen input changed during evaluation: ' + relative
    write_json(OUT / 'run_complete.json', {'wall_seconds': time.perf_counter() - start, 'simulation_only': True})
    summarize()


def summarize():
    detected = read_csv(OUT / 'detection_frames.csv')
    localized = read_csv(OUT / 'localization_frames.csv')
    timing = read_csv(OUT / 'timing_frames.csv')
    summary = {'detection': {}, 'localization': {}, 'joint': {}, 'paired': {}, 'timing': {}}
    for name in DETECTORS:
        rows = [r for r in detected if r['detector'] == name]
        pos, neg = [r for r in rows if r['label']], [r for r in rows if not r['label']]
        item = detection(pos, neg)
        item['auc'] = roc(rows)[0]
        item['fpr_by_group'] = {scene: float(np.mean([r['detected'] for r in neg if r['scene'] == scene]))
                                for scene in list(SCENES) + list(MIXES)}
        item['single_fpr'] = float(np.mean([r['detected'] for r in neg if r['scene'] in SCENES]))
        item['multiple_fpr'] = float(np.mean([r['detected'] for r in neg if r['scene'] in MIXES]))
        item['tpr_by_snr'] = {str(snr): float(np.mean([r['detected'] for r in pos if r['snr_db'] == snr])) for snr in SNRS}
        summary['detection'][name] = item
    methods = ('phat', 'coherence', 'harmonic', 'combined', 'no_null', 'proposed')
    for name in methods:
        rows = [r for r in localized if r['method'] == name]
        summary['localization'][name] = {'overall': localization(rows),
              'by_scene': {scene: localization([r for r in rows if r['scene'] == scene]) for scene in SCENES},
              'by_snr': {str(snr): localization([r for r in rows if r['snr_db'] == snr]) for snr in SNRS}}
    baseline = [r for r in localized if r['method'] == 'phat']
    for method in methods[1:]:
        other = [r for r in localized if r['method'] == method]
        assert [r['trial_id'] for r in baseline] == [r['trial_id'] for r in other]
        delta = np.array([a['angular_error_deg'] - b['angular_error_deg'] for a, b in zip(baseline, other)])
        strata = [f"{r['scene']}:{r['snr_db']}" for r in baseline]
        summary['paired'][method] = {'phat_minus_method_mean_deg': float(delta.mean()),
                                    'ci95': bootstrap_mean(delta, strata)}
    full = [r for r in localized if r['method'] == 'proposed']
    ablated = [r for r in localized if r['method'] == 'no_null']
    delta = np.array([a['angular_error_deg'] - b['angular_error_deg'] for a, b in zip(ablated, full)])
    summary['nuller_ablation'] = {'no_null_minus_full_mean_deg': float(delta.mean()),
                                  'ci95': bootstrap_mean(delta, strata)}
    for detector, key in [('harmonic_coherence', 'original_detected'), ('spectral', 'spectral_detected'), ('proposed', 'detected')]:
        for method in ('phat', 'proposed'):
            rows = [r for r in localized if r['method'] == method]
            success = [r[key] and r['angular_error_deg'] <= 10 for r in rows]
            summary['joint'][detector + '+' + method] = {'n': len(rows), 'success_rate': float(np.mean(success)),
                                                         'ci95': wilson(sum(success), len(rows))}
    for label, first, second in [('detector_gain', 'original_detected', 'detected')]:
        delta = np.array([int(r[second] and r['angular_error_deg'] <= 10)
                          - int(r[first] and r['angular_error_deg'] <= 10) for r in baseline])
        summary['joint'][label] = {'paired_success_gain': float(delta.mean()), 'ci95': bootstrap_mean(delta, strata)}
    delta = np.array([int(b['detected'] and b['angular_error_deg'] <= 10)
                      - int(a['detected'] and a['angular_error_deg'] <= 10) for a, b in zip(baseline, full)])
    summary['joint']['localizer_gain'] = {'paired_success_gain': float(delta.mean()), 'ci95': bootstrap_mean(delta, strata)}
    for key in ('shared_full_and_spectral_detector_ms', 'localizer_ms', 'proposed_pipeline_upper_bound_ms', 'phat_front_and_search_ms'):
        values = [r[key] for r in timing]
        summary['timing'][key] = {'median': float(np.median(values)), 'p95': float(np.quantile(values, .95))}
    sequence_d = read_csv(OUT / 'sequence_detection.csv')
    sequence_l = read_csv(OUT / 'sequence_localization.csv')
    sequence_ids = sorted({r['trial_id'] for r in sequence_d})
    summary['sequences'] = {'n': len(sequence_ids), 'raw_localization': {}, 'detection': {}}
    for method in methods:
        means = [np.mean([r['angular_error_deg'] for r in sequence_l if r['trial_id'] == item and r['method'] == method]) for item in sequence_ids]
        summary['sequences']['raw_localization'][method] = {'mean_deg': float(np.mean(means)), 'ci95': bootstrap_mean(means)}
    for detector in DETECTORS:
        rows = [r for r in sequence_d if r['detector'] == detector]
        summary['sequences']['detection'][detector] = {
            'tpr': float(np.mean([r['detected'] for r in rows if r['label']])),
            'fpr': float(np.mean([r['detected'] for r in rows if not r['label']]))}
    write_json(OUT / 'summary.json', summary)
    inventory = [p for folder in (OUT, DATA) for p in sorted(folder.rglob('*'))
                 if p.is_file() and p.name != 'artifact_manifest.json']
    write_json(OUT / 'artifact_manifest.json', [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in inventory])
    print(json.dumps({'detection': summary['detection'], 'paired': summary['paired'], 'joint': summary['joint']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summarize', action='store_true')
    args = parser.parse_args()
    summarize() if args.summarize else run()
