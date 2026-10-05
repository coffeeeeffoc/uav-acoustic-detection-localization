"""Audio-only interference-resistant SRP development on the OLD synthetic data.

No new test seeds and no detector fitting. Inputs are (1600, 8) samples at 8 kHz.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import inspect
import json
import time

from experiment import ROOT, Engine, FS, N, ARRAY, C0, errors, write_csv, write_json
import numpy as np
from scipy import fft, ndimage, linalg
from scipy.spatial.distance import cdist

OUT = ROOT / "results" / "development_localizer"
VARIANTS = ("phat", "beta_0p75", "beta_0p5", "excess_soft", "coherence_excess", "pair_excess", "beta_excess")
VARIANTS += ("full_phat", "full_excess", "full_coherence_excess", "full_peak_excess")
SELECTED = "candidate_ranker"  # Frozen after trial-grouped old-development comparison.


class ImprovedLocalizer:
    """analyze(audio) -> az_hat, el_hat, score, variant, processing_ms; optional map.

    Truth, nuisance type, seed, nominal SNR and source metadata are never inputs.
    This experimental localizer does not provide a calibrated detection decision.
    """
    def __init__(self, variant=SELECTED, model_path=None):
        if variant not in VARIANTS and variant != "candidate_ranker":
            raise ValueError(f"Unknown variant: {variant}")
        self.variant = variant
        self.engine = Engine()
        self.full_engine = Engine()
        e = self.full_engine
        e.freq = fft.rfftfreq(N, 1 / FS)
        e.band = (e.freq >= 200) & (e.freq <= 3000)
        e.corr_n = N * 8
        lag = (-(ARRAY[e.i] - ARRAY[e.j]) @ e.grid.T / C0 * FS * 8) % e.corr_n
        e.left = np.floor(lag).astype(int) % e.corr_n
        e.right = (e.left + 1) % e.corr_n
        e.frac = lag - np.floor(lag)
        self.ranker = CandidateRanker.load(model_path or OUT / "candidate_ranker_model.npz") if variant == "candidate_ranker" else None

    def _spectra(self, audio):
        if audio.shape != (N, 8) or not np.isfinite(audio).all():
            raise ValueError("Expected finite (1600,8) audio at 8000 Hz")
        e = self.engine
        x = audio.T.astype(np.float64)
        x -= x.mean(axis=1, keepdims=True)
        windows = np.lib.stride_tricks.sliding_window_view(x, 512, axis=1)[:, ::256, :]
        X = fft.rfft(windows * e.window, workers=1)
        power = np.mean(np.abs(X) ** 2, axis=1)
        G = np.mean(X[e.i] * np.conj(X[e.j]), axis=1)
        magnitude = np.abs(G)
        phase = G / np.maximum(magnitude, 1e-20)
        coherence = np.clip(magnitude ** 2 / (power[e.i] * power[e.j] + 1e-20), 0, 1)
        average_power = power.mean(axis=0)
        spectral_floor = ndimage.median_filter(average_power, size=11, mode="nearest")
        excess = np.maximum(average_power / np.maximum(spectral_floor, 1e-20) - 1, 0)
        soft_excess = 0.05 + 0.95 * excess / (1 + excess)
        pair_floor = ndimage.median_filter(magnitude, size=(1, 11), mode="nearest")
        pair_excess = np.maximum(magnitude / np.maximum(pair_floor, 1e-20) - 1, 0)
        relative = magnitude / max(float(np.median(magnitude[:, e.band])), 1e-20)
        reliable = np.sqrt(0.1 + 0.9 * coherence)
        weights = {
            "phat": np.ones_like(G.real),
            "beta_0p75": relative ** 0.25,
            "beta_0p5": relative ** 0.5,
            "excess_soft": np.broadcast_to(soft_excess, G.shape),
            "coherence_excess": soft_excess * reliable,
            "pair_excess": (0.05 + 0.95 * pair_excess / (1 + pair_excess)) * reliable,
            "beta_excess": soft_excess * np.clip(relative ** 0.5, 0.2, 5),
        }
        full_X = fft.rfft(x * e.full_window, workers=1)
        full_G = full_X[e.i] * np.conj(full_X[e.j])
        full_phase = full_G / np.maximum(np.abs(full_G), 1e-20)
        full_power = np.mean(np.abs(full_X) ** 2, axis=0)
        full_floor = ndimage.median_filter(full_power, size=31, mode="nearest")
        full_excess = np.maximum(full_power / np.maximum(full_floor, 1e-20) - 1, 0)
        full_soft = full_excess / (1 + full_excess)
        full_reliability = np.array([np.interp(self.full_engine.freq, e.freq, value) for value in reliable])
        full_weights = {
            "full_phat": np.ones_like(full_G.real),
            "full_excess": np.broadcast_to(0.005 + 0.995 * full_soft, full_G.shape),
            "full_coherence_excess": (0.005 + 0.995 * full_soft) * full_reliability,
            "full_peak_excess": (0.005 + 0.995 * full_soft ** 2) * full_reliability,
        }
        spectra = {v: (phase, w, self.engine) for v, w in weights.items()}
        spectra.update({v: (full_phase, w, self.full_engine) for v, w in full_weights.items()})
        return spectra

    def _localize(self, phase, weight, e, return_map=False):
        weight = weight * e.band
        corr = fft.irfft(phase * weight, n=e.corr_n, workers=1, axis=-1)
        response = np.sum((1 - e.frac) * corr[e.pair_index, e.left] + e.frac * corr[e.pair_index, e.right], axis=0)
        response *= e.corr_n / max(2 * weight.sum(), 1e-20)
        best = int(np.argmax(response))
        result = {"az_hat": float(e.az[best]), "el_hat": float(e.el[best]), "score": float(response[best])}
        if return_map:
            result["map"] = response
        return result

    def analyze(self, audio, return_map=False):
        start = time.perf_counter_ns()
        if self.ranker is not None:
            indices, features, diagnostics = self.candidates(audio)
            scores = self.ranker.predict(features)
            best = int(np.argmax(scores))
            index = indices[best]
            result = {"az_hat": float(self.engine.az[index]), "el_hat": float(self.engine.el[index]),
                      "score": float(scores[best]), "candidate_count": len(indices),
                      "f0_hypotheses_hz": diagnostics["f0_hypotheses_hz"]}
            if return_map:
                sparse = np.full(len(self.engine.az), np.nan)
                sparse[indices] = scores
                result.update(map=sparse, map_kind="sparse_candidate_ranking", candidate_indices=indices,
                              candidate_scores=scores, proposal_maps=diagnostics["maps"])
            return {**result, "variant": self.variant, "processing_ms": (time.perf_counter_ns()-start)/1e6}
        spectra = self._spectra(audio)
        result = self._localize(*spectra[self.variant], return_map)
        return {**result, "variant": self.variant, "processing_ms": (time.perf_counter_ns() - start) / 1e6}

    def analyze_variants(self, audio):
        start = time.perf_counter_ns()
        spectra = self._spectra(audio)
        shared_ms = (time.perf_counter_ns() - start) / 1e6
        results = {}
        for variant in VARIANTS:
            begin = time.perf_counter_ns()
            result = self._localize(*spectra[variant])
            results[variant] = {**result, "processing_ms": shared_ms + (time.perf_counter_ns() - begin) / 1e6}
        return results

    def candidates(self, audio):
        """Generate competing directions and source-specific features, without labels."""
        spectra = self._spectra(audio)
        e = self.engine
        phase, _, _ = spectra["phat"]
        maps = [self._localize(*spectra[v], return_map=True)["map"] for v in ("phat", "full_excess")]
        x = audio.T.astype(np.float64)
        x -= x.mean(axis=1, keepdims=True)
        x /= max(float(np.sqrt(np.mean(x*x))), 1e-15)
        X = fft.rfft(x * e.full_window, n=2048, workers=1)
        freq = fft.rfftfreq(2048, 1 / FS)
        p = np.mean(np.abs(X) ** 2, axis=0)
        floor = ndimage.median_filter(p, size=31, mode="nearest")
        contrast = ndimage.gaussian_filter1d(np.log1p(p / np.maximum(floor, 1e-15)) - np.log(2), 1)
        comb = (contrast[e.comb_index] * e.comb_weights).sum(axis=1) / e.comb_weights.sum()
        candidates_f0 = []
        for index in np.argsort(comb)[::-1]:
            f0 = float(e.f0_candidates[index])
            if all(abs(f0 - other) >= 20 for other in candidates_f0):
                candidates_f0.append(f0)
            if len(candidates_f0) == 3:
                break
        for f0 in candidates_f0:
            distance = np.abs(e.freq - np.rint(e.freq / f0) * f0)
            weight = 0.02 + 0.98 * np.exp(-0.5 * (distance / np.maximum(8, 0.012 * e.freq)) ** 2)
            maps.append(self._localize(phase, np.broadcast_to(weight, phase.shape), e, True)["map"])
        indices = []
        for map_index, response in enumerate(maps):
            allowed = np.ones(len(response), dtype=bool)
            for _ in range(3 if map_index == 0 else 2):
                best = int(np.argmax(np.where(allowed, response, -np.inf)))
                allowed &= (e.grid @ e.grid[best]) < np.cos(np.deg2rad(20))
                if all(e.grid[best] @ e.grid[old] < np.cos(np.deg2rad(7)) for old in indices):
                    indices.append(best)
        indices = np.array(indices)
        u = e.grid[indices]
        tau = -(u @ ARRAY.T) / C0
        steering = np.exp(2j * np.pi * tau[:, :, None] * freq)
        beam = np.einsum("cmf,mf->cf", steering, X) / 8
        p_beam = np.abs(beam) ** 2
        # A two-direction linearly constrained beam removes the strongest other candidate.
        # ponytail: two sources only; a multi-source constrained beam is needed for denser mixtures.
        other = []
        for index, v in enumerate(u):
            available = (u @ v) < np.cos(np.deg2rad(15))
            other.append(int(np.argmax(np.where(available, maps[0][indices], -np.inf))))
        other = np.array(other)
        cross = np.mean(steering * np.conj(steering[other]), axis=1)
        cleaned = (beam - cross * beam[other]) / np.maximum(1 - np.abs(cross) ** 2, 0.1)
        power_clean = np.abs(cleaned) ** 2
        feats = []
        global_feature = spectral_features(p, freq, e)
        map_stack = np.array(maps)
        for i, index in enumerate(indices):
            f = list(global_feature)
            f += spectral_features(p_beam[i], freq, e)
            f += spectral_features(power_clean[i], freq, e)
            for lo, hi in [(200, 800), (800, 1600), (1600, 3000)]:
                mask = (freq >= lo) & (freq <= hi)
                ratio = p_beam[i, mask] / np.maximum(p[mask], 1e-15)
                f += list(np.quantile(ratio, [.25, .5, .9]))
                f += [float(np.log((power_clean[i, mask].sum()+1e-15) / (p_beam[i, mask].sum()+1e-15)))]
            f += list(map_stack[:, index])
            f += list(map_stack[:, index] / np.maximum(map_stack.max(axis=1), 1e-15))
            f += [float(np.min(np.rad2deg(np.arccos(np.clip(u @ v, -1, 1)))[np.arange(len(u)) != i])) for v in [u[i]]]
            feats.append(f)
        return indices, np.array(feats), {"f0_hypotheses_hz": candidates_f0, "maps": map_stack}


def spectral_features(power, freq, engine):
    p = power / max(float(power.sum()), 1e-15)
    floor = ndimage.median_filter(p, size=31, mode="nearest")
    z = ndimage.gaussian_filter1d(np.log1p(p / np.maximum(floor, 1e-15)) - np.log(2), 1)
    result = []
    for lo, hi in [(80, 3000), (80, 400), (400, 1000), (1000, 2000), (2000, 3000)]:
        mask = (freq >= lo) & (freq <= hi)
        q = p[mask] + 1e-15
        q /= q.sum()
        result += [float(np.log(p[mask].sum() + 1e-15)), float(np.exp(np.log(q).mean()) / q.mean()),
                   float(-(q*np.log(q)).sum() / np.log(len(q))), *np.quantile(z[mask], [.5, .9, .99]), float(z[mask].std())]
    comb = (z[engine.comb_index] * engine.comb_weights).sum(axis=1) / engine.comb_weights.sum()
    best = int(np.argmax(comb))
    other = np.abs(engine.f0_candidates - engine.f0_candidates[best]) >= 20
    result += [float(comb[best]), float(comb[other].max()), float(comb.mean()), float(comb.std())]
    f0 = engine.f0_candidates[best]
    distance = np.abs(freq - np.rint(freq/f0)*f0)
    band = (freq >= 200) & (freq <= 3000)
    for width in (5, 10, 20):
        result.append(float(p[band & (distance <= width)].sum() / max(p[band].sum(), 1e-15)))
    return result


class CandidateRanker:
    """Fixed-size Gaussian-basis ridge scorer; labels used only during fit."""
    def fit(self, X, y, feature_indices=None):
        self.feature_indices = np.arange(X.shape[1]) if feature_indices is None else np.asarray(feature_indices, dtype=int)
        if not np.array_equal(self.feature_indices, np.arange(X.shape[1])):
            X = X[:, self.feature_indices]
        self.center = X.mean(axis=0)
        self.scale = np.maximum(X.std(axis=0), 0.05)
        z = np.clip((X-self.center)/self.scale, -8, 8)
        rng = np.random.default_rng(90210)
        good, bad = np.flatnonzero(y >= np.exp(-1)), np.flatnonzero(y < np.exp(-1))
        anchors = np.r_[rng.choice(good, min(128,len(good)), replace=False), rng.choice(bad, min(128,len(bad)), replace=False)]
        self.anchors = z[anchors]
        self.width, self.ridge = 1.0, 0.1
        K = np.exp(-cdist(z, self.anchors, "sqeuclidean")/(2*self.width**2*X.shape[1]))
        K = np.column_stack([K, np.ones(len(K))])
        weight = np.where(y >= np.exp(-1), len(bad)/max(len(good),1), 1.0)
        self.coefficients = linalg.solve(K.T @ (weight[:,None]*K) + self.ridge*np.eye(K.shape[1]), K.T @ (weight*y), assume_a="pos")
        return self

    def predict(self, X):
        X = np.atleast_2d(X)
        if not np.array_equal(self.feature_indices, np.arange(X.shape[1])):
            X = X[:, self.feature_indices]
        z = np.clip((X-self.center)/self.scale, -8, 8)
        K = np.exp(-cdist(z, self.anchors, "sqeuclidean")/(2*self.width**2*X.shape[1]))
        return K @ self.coefficients[:-1] + self.coefficients[-1]

    def save(self, path, input_digest):
        np.savez_compressed(path, center=self.center, scale=self.scale, anchors=self.anchors,
                            coefficients=self.coefficients, width=self.width, ridge=self.ridge,
                            feature_indices=self.feature_indices, feature_sha256=np.array(candidate_digest()),
                            source_sha256=np.array(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                            input_archive_sha256=np.array(input_digest))

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path) as saved:
            if str(saved["feature_sha256"]) != candidate_digest():
                raise ValueError("Candidate feature source differs from the saved model")
            if str(saved["source_sha256"]) != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
                raise ValueError("Frozen localizer source differs from the saved model")
            for name in ("center", "scale", "anchors", "coefficients", "width", "ridge", "feature_indices"):
                setattr(model, name, saved[name])
        return model


def candidate_digest():
    return hashlib.sha256((inspect.getsource(ImprovedLocalizer.candidates) + inspect.getsource(spectral_features) +
                           inspect.getsource(ImprovedLocalizer._spectra) + inspect.getsource(ImprovedLocalizer._localize) +
                           inspect.getsource(ImprovedLocalizer.__init__) + inspect.getsource(Engine.__init__) +
                           json.dumps({"FS":FS,"N":N,"C0":C0,"ARRAY":ARRAY.tolist()},sort_keys=True)).encode()).hexdigest()


def develop_ranker():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "candidate_features.npz"
    paths = sorted((ROOT / "data" / "synthetic" / "full" / "test").glob("*.npz"))
    assert len(paths) == 2000
    inventory = [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    input_digest = hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()
    write_json(OUT / "input_archive_manifest.json", {"partition":"old full/test reclassified as development",
               "count":len(paths), "input_archive_sha256":input_digest, "files":inventory})
    model = ImprovedLocalizer(variant="phat")
    if not cache.exists():
        features, labels, trials, candidate_indices, candidate_errors = [], [], [], [], []
        items = []
        start = time.perf_counter()
        for trial, path in enumerate(paths):
            with np.load(path) as saved:
                indices, X, _ = model.candidates(saved["audio"])
                # Truth is used only after candidates/features are computed from audio.
                label = int(saved["label"][0])
                error = errors(model.engine.az[indices], model.engine.el[indices], saved["az_deg"][0], saved["el_deg"][0])[0]
                y = np.exp(-(error/10)**2) if label else np.zeros(len(indices))
                meta = json.loads(str(saved["metadata_json"]))
                items.append({"trial_id": path.stem, "label": label, "scene": meta["scene"], "snr_db": meta["snr_db"]})
            features.extend(X)
            labels.extend(y)
            trials.extend([trial]*len(indices))
            candidate_indices.extend(indices)
            candidate_errors.extend(error if label else np.full(len(indices), np.nan))
            if (trial+1) % 200 == 0:
                print(f"Candidate features {trial+1}/2000; {time.perf_counter()-start:.1f}s", flush=True)
        np.savez_compressed(cache, features=np.array(features), labels=np.array(labels), trials=np.array(trials),
                            indices=np.array(candidate_indices), errors=np.array(candidate_errors), feature_sha256=np.array(candidate_digest()),
                            input_archive_sha256=np.array(input_digest), trial_ids=np.array([p.stem for p in paths]))
        write_csv(OUT / "candidate_items.csv", items)
    with np.load(cache) as saved:
        if str(saved["feature_sha256"]) != candidate_digest():
            raise ValueError("Feature cache source mismatch; archive explicitly before recomputing")
        if "input_archive_sha256" not in saved.files or str(saved["input_archive_sha256"]) != input_digest:
            raise ValueError("Feature cache input archive mismatch; archive explicitly before recomputing")
        if not np.array_equal(saved["trial_ids"], [p.stem for p in paths]):
            raise ValueError("Feature cache trial ordering mismatch")
        X,y,trials,indices,candidate_errors = [saved[k] for k in ("features","labels","trials","indices","errors")]
    with (OUT / "candidate_items.csv").open(encoding="utf-8", newline="") as f:
        items = list(csv.DictReader(f))
    with (ROOT / "results/full/test_frames.csv").open(encoding="utf-8",newline="") as f:
        baselines = {r["trial_id"]:r for r in csv.DictReader(f) if r["method"]=="phat"}
    rng = np.random.default_rng(90210)
    trial_folds = np.zeros(len(items), dtype=int)
    for label in ("0", "1"):
        group = np.array([i for i,item in enumerate(items) if item["label"]==label])
        trial_folds[rng.permutation(group)] = np.arange(len(group))%5
    drop = np.r_[np.arange(84,126), [129,133,137]]
    variants = {"full":np.arange(149), "no_null":np.setdiff1d(np.arange(149),drop)}
    assert len(variants["no_null"]) == 104
    for name, feature_indices in variants.items():
        predictions = np.empty(len(y))
        for fold in range(5):
            valid = trial_folds[trials]==fold
            ranker = CandidateRanker().fit(X[~valid],y[~valid],feature_indices)
            predictions[valid] = ranker.predict(X[valid])
            print(f"{name} trial-grouped fold {fold+1}/5 complete", flush=True)
        rows = []
        for trial,item in enumerate(items):
            if item["label"]!="1":
                continue
            subset = np.flatnonzero(trials==trial)
            winner = subset[np.argmax(predictions[subset])]
            baseline = baselines[item["trial_id"]]
            index = indices[winner]
            err,ae,ee = errors(model.engine.az[index],model.engine.el[index],float(baseline["true_az"]),float(baseline["true_el"]))
            rows.append({"trial_id":item["trial_id"],"scene":item["scene"],"snr_db":float(item["snr_db"]),
                         "variant":f"candidate_ranker_{name}_oof","az_hat":float(model.engine.az[index]),"el_hat":float(model.engine.el[index]),
                         "score":float(predictions[winner]),"angular_error_deg":float(err),"az_error_deg":float(ae),"el_error_deg":float(ee),
                         "phat_error_deg":float(baseline["angular_error_deg"]),"candidate_oracle_min_error_deg":float(candidate_errors[subset].min()),
                         "candidate_count":len(subset),"internal_development_fold":int(trial_folds[trial])})
        prefix = "ranker_oof" if name=="full" else "ranker_no_null_oof"
        model_name = "candidate_ranker_model.npz" if name=="full" else "candidate_ranker_no_null_model.npz"
        write_csv(OUT / f"{prefix}_frames.csv",rows)
        np.savez_compressed(OUT / f"{prefix}_candidate_scores.npz", score=predictions, trial_folds=trial_folds, trials=trials)
        CandidateRanker().fit(X,y,feature_indices).save(OUT / model_name,input_digest)
        err = np.array([r["angular_error_deg"] for r in rows])
        oracle = np.array([r["candidate_oracle_min_error_deg"] for r in rows])
        result = {"development_only":True,"trial_grouped_folds":5,"positive_trials":1000,"negative_trials":1000,
                  "candidate_rows":len(y),"feature_count":len(feature_indices),"raw_feature_count":149,"feature_indices":feature_indices.tolist(),
                  "mean_deg":float(err.mean()),"within10_rate":float(np.mean(err<=10)),
                  "candidate_oracle_mean_deg":float(oracle.mean()),"candidate_oracle_within10_rate":float(np.mean(oracle<=10)),
                  "oracle_is_diagnostic_not_an_algorithm":True,"all_training_model":model_name,
                  "width":1.0,"ridge":0.1,"anchors_per_class_max":128,"feature_sha256":candidate_digest(),"input_archive_sha256":input_digest}
        write_json(OUT / f"{prefix}_summary.json",result)
        print(json.dumps({k:result[k] for k in ("feature_count","mean_deg","within10_rate","candidate_oracle_within10_rate")}),flush=True)


def summarize(rows):
    metrics = []
    for variant in dict.fromkeys(r["variant"] for r in rows):
        selected = [r for r in rows if r["variant"] == variant]
        groups = [("all", selected)]
        groups += [(scene, [r for r in selected if r["scene"] == scene]) for scene in ("sensor_noise", "wind", "directional", "engine")]
        groups += [(f"snr={snr}", [r for r in selected if r["snr_db"] == snr]) for snr in (-15, -10, -5, 0, 5)]
        groups += [(f"{scene}:{snr}", [r for r in selected if r["scene"] == scene and r["snr_db"] == snr])
                   for scene in ("sensor_noise", "wind", "directional", "engine") for snr in (-15, -10, -5, 0, 5)]
        for group, values in groups:
            error = np.array([r["angular_error_deg"] for r in values])
            metrics.append({"variant": variant, "group": group, "n": len(values), "mean_deg": float(error.mean()),
                            "median_deg": float(np.median(error)), "p95_deg": float(np.quantile(error, 0.95)),
                            "within10_rate": float(np.mean(error <= 10)),
                            "azimuth_mae_deg": float(np.mean([abs(r["az_error_deg"]) for r in values])),
                            "elevation_mae_deg": float(np.mean([abs(r["el_error_deg"]) for r in values])),
                            "mean_improvement_vs_phat_deg": float(np.mean([r["phat_error_deg"] - r["angular_error_deg"] for r in values])),
                            "within10_improvement_vs_phat": float(np.mean([(r["angular_error_deg"] <= 10) - (r["phat_error_deg"] <= 10) for r in values]))})
    return metrics


def develop():
    OUT.mkdir(parents=True, exist_ok=True)
    with (ROOT / "results" / "full" / "test_frames.csv").open(encoding="utf-8", newline="") as f:
        items = [r for r in csv.DictReader(f) if r["method"] == "phat" and r["label"] == "1"]
    assert len(items) == 1000
    model = ImprovedLocalizer(variant="phat")
    rows = []
    start = time.perf_counter()
    for index, item in enumerate(items):
        with np.load(ROOT / "data" / "synthetic" / "full" / "test" / f"{item['trial_id']}.npz") as saved:
            audio = saved["audio"]
        # Evaluation labels are read only AFTER the audio-only estimate is returned.
        results = model.analyze_variants(audio)
        for variant, result in results.items():
            error, az_error, el_error = errors(result["az_hat"], result["el_hat"], float(item["true_az"]), float(item["true_el"]))
            rows.append({"trial_id": item["trial_id"], "scene": item["scene"], "snr_db": float(item["snr_db"]),
                         "variant": variant, **result, "angular_error_deg": float(error), "az_error_deg": float(az_error),
                         "el_error_deg": float(el_error), "phat_error_deg": float(item["angular_error_deg"]),
                         "true_az": float(item["true_az"]), "true_el": float(item["true_el"])})
        assert results["phat"]["az_hat"] == float(item["az_hat"]) and results["phat"]["el_hat"] == float(item["el_hat"])
        if (index + 1) % 100 == 0:
            print(f"Development {index+1}/1000; {time.perf_counter()-start:.1f}s", flush=True)
    write_csv(OUT / "variant_frames.csv", rows)
    metrics = summarize(rows)
    write_csv(OUT / "variant_summary.csv", metrics)
    summary = {"partition": "OLD full/test positives explicitly reclassified as development", "n": 1000,
               "no_new_test_seeds": True, "variants": list(VARIANTS), "overall": [r for r in metrics if r["group"] == "all"],
               "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "wall_seconds": time.perf_counter()-start}
    write_json(OUT / "development_summary.json", summary)
    print(json.dumps(summary["overall"], indent=2), flush=True)


def finalize_development():
    """Summaries and replay of already generated old data, no fresh experiments."""
    with np.load(OUT / "candidate_features.npz") as saved:
        X, trials, indices, candidate_errors = [saved[k] for k in ("features","trials","indices","errors")]
        ids = saved["trial_ids"].tolist()
        input_digest = str(saved["input_archive_sha256"])
    with np.load(OUT / "candidate_features_pre_guard.npz") as old:
        assert np.array_equal(X,old["features"]), "Regenerated old features differ"
    models = {"full":"candidate_ranker_model.npz", "no_null":"candidate_ranker_no_null_model.npz"}
    results, all_metrics, verified = {}, [], []
    for name,filename in models.items():
        prefix = "ranker_oof" if name=="full" else "ranker_no_null_oof"
        with (OUT / f"{prefix}_frames.csv").open(encoding="utf-8",newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            for key in ("snr_db","angular_error_deg","az_error_deg","el_error_deg","phat_error_deg"):
                row[key] = float(row[key])
        metrics = summarize(rows)
        all_metrics.extend(metrics)
        write_csv(OUT / f"{prefix}_group_summary.csv",metrics)
        localizer = ImprovedLocalizer(model_path=OUT / filename)
        scores = localizer.ranker.predict(X)
        fit_rows = []
        for row in rows:
            trial = ids.index(row["trial_id"])
            group = np.flatnonzero(trials==trial)
            winner = group[np.argmax(scores[group])]
            index = indices[winner]
            fit_rows.append({"trial_id":row["trial_id"],"az_hat":float(localizer.engine.az[index]),
                             "el_hat":float(localizer.engine.el[index]),"score":float(scores[winner]),
                             "angular_error_deg":float(candidate_errors[winner]),"interpretation":"resubstitution only"})
        write_csv(OUT / f"{name}_resubstitution_frames.csv",fit_rows)
        timings = []
        for scene in range(4):
            for repeat in range(10):
                trial_id = f"pos-{scene}-2-{repeat}"
                with np.load(ROOT / "data/synthetic/full/test" / f"{trial_id}.npz") as saved:
                    audio = saved["audio"]
                if not timings:
                    localizer.analyze(audio)
                result = localizer.analyze(audio,return_map=(repeat==0))
                expected = next(r for r in fit_rows if r["trial_id"]==trial_id)
                assert result["az_hat"]==expected["az_hat"] and result["el_hat"]==expected["el_hat"]
                assert np.isclose(result["score"],expected["score"],atol=1e-10)
                timings.append(result["processing_ms"])
                verified.append(f"{name}:{trial_id}")
                if repeat==0:
                    baseline = localizer.engine.analyze(audio)["methods"]["phat"]
                    first = result["candidate_indices"][0]
                    assert localizer.engine.az[first]==baseline["az_hat"] and localizer.engine.el[first]==baseline["el_hat"]
                    np.savez_compressed(OUT / f"{name}_ranked_map_{trial_id}.npz", grid_az_deg=localizer.engine.az,
                                        grid_el_deg=localizer.engine.el,candidate_indices=result["candidate_indices"],
                                        candidate_scores=result["candidate_scores"],sparse_rank_map=result["map"],proposal_maps=result["proposal_maps"])
        diff = np.array([r["phat_error_deg"]-r["angular_error_deg"] for r in rows])
        hitdiff = np.array([int(r["angular_error_deg"]<=10)-int(r["phat_error_deg"]<=10) for r in rows])
        rng = np.random.default_rng(90210)
        boot, hitboot = np.zeros(2000), np.zeros(2000)
        for scene in ("sensor_noise","wind","directional","engine"):
            for snr in (-15,-10,-5,0,5):
                group = np.array([i for i,r in enumerate(rows) if r["scene"]==scene and r["snr_db"]==snr])
                selected = rng.choice(group,size=(2000,len(group)),replace=True)
                boot += diff[selected].sum(axis=1)/1000
                hitboot += hitdiff[selected].sum(axis=1)/1000
        results[name] = {**metrics[0],"feature_count":len(localizer.ranker.feature_indices),
                         "mean_improvement_ci95":np.quantile(boot,[.025,.975]).tolist(),
                         "within10_improvement_ci95":np.quantile(hitboot,[.025,.975]).tolist(),
                         "in_sample_mean_deg":float(np.mean([r["angular_error_deg"] for r in fit_rows])),
                         "in_sample_within10":float(np.mean([r["angular_error_deg"]<=10 for r in fit_rows])),
                         "runtime_probe_n":len(timings),"median_ms":float(np.median(timings)),"p95_ms":float(np.quantile(timings,.95)),
                         "model_path":str((OUT / filename).relative_to(ROOT)).replace(chr(92),"/"),
                         "model_sha256":hashlib.sha256((OUT / filename).read_bytes()).hexdigest()}
    with np.load(OUT / "round3/candidate_ranker_model.npz") as previous, np.load(OUT / models["full"]) as current:
        for key in ("center","scale","anchors","coefficients"):
            assert np.allclose(previous[key],current[key],rtol=1e-10,atol=1e-10), key
    assert np.isclose(results["full"]["mean_deg"],17.631875627725243) and results["full"]["within10_rate"]==0.747
    self_test()
    write_csv(OUT / "frozen_group_summary.csv",all_metrics)
    summary = {"frozen":True,"development_only":True,"positive_trials":1000,"negative_trials":1000,
               "no_fresh_acoustic_inputs":True,"primary_evidence":"five-fold trial-grouped old-development predictions",
               "default_model":"full","models":results,"input_archive_sha256":input_digest,
               "feature_sha256":candidate_digest(),"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "bootstrap_note":"2000 independent-trial resamples within scene/SNR strata of fixed OOF predictions; ignores fitting and selection uncertainty.",
               "runtime_note":"40 fixed old -5dB frames per model; excludes setup,warmup,file I/O and 200ms acquisition; four calls include optional diagnostics; host-only, one-thread request.",
               "in_sample_note":"Resubstitution is diagnostic only; primary figures are grouped OOF, not blind-test evidence."}
    write_json(OUT / "frozen_development_summary.json",summary)
    write_json(OUT / "verification.json",{"passed":True,"regenerated_features_bit_identical":True,
               "default_149_model_coefficients_unchanged":True,"audio_only_replay_scores_and_directions_match":True,
               "raw_phat_candidate_retained":True,"replayed_old_trials":verified,
               "source_sha256":summary["source_sha256"],"feature_sha256":summary["feature_sha256"],"input_archive_sha256":input_digest})
    print(json.dumps(summary,indent=2),flush=True)


def self_test():
    model = ImprovedLocalizer()
    trial = ROOT / "data" / "synthetic" / "full" / "test" / "pos-0-2-0.npz"
    with np.load(trial) as saved:
        audio = saved["audio"]
    a, b = model.analyze(audio), model.analyze(audio * 3)
    assert a["az_hat"] == b["az_hat"] and a["el_hat"] == b["el_hat"]
    assert np.isfinite(model.analyze(np.zeros((N, 8)))["score"])
    try:
        model.analyze(np.zeros((N, 7)))
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid channel count accepted")
    assert len(model.analyze(audio, return_map=True)["map"]) == 3601
    no_null = ImprovedLocalizer(model_path=OUT / "candidate_ranker_no_null_model.npz")
    assert len(no_null.ranker.feature_indices)==104 and len(model.ranker.feature_indices)==149
    assert np.array_equal(no_null.ranker.feature_indices,np.setdiff1d(np.arange(149),np.r_[np.arange(84,126),[129,133,137]]))
    assert np.isfinite(no_null.analyze(audio)["score"])
    print("Self-test passed: amplitude invariance, finite silence, input shape, map contract")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--develop", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--develop-ranker", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.develop:
        develop()
    if args.develop_ranker:
        develop_ranker()
    if args.finalize:
        finalize_development()
    if not (args.self_test or args.develop or args.develop_ranker or args.finalize):
        parser.print_help()
