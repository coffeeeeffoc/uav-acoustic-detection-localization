"""Reproducible, simulation-only UAV-like acoustic experiment (no range claim)."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if sys.version_info[:2] == (3, 12) and (ROOT / ".python-packages").exists():
    sys.path.insert(0, str(ROOT / ".python-packages"))
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "results" / ".mplconfig"))

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from datetime import datetime, timezone

import numpy as np
from scipy import fft, ndimage, signal
from scipy.io import wavfile

METHODS = ("phat", "coherence", "harmonic", "combined")
SCENES = ("sensor_noise", "wind", "directional", "engine")
SNRS = (-15, -10, -5, 0, 5)
FS, N, C0 = 8000, 1600, 343.0
SEED = 20261002
# A fixed illustrative geometry, not the organizer's array.
ARRAY = np.array([[0, 0, 0], [0.200, 0, 0], [0.104, 0.162, 0],
                  [-0.073, 0.180, 0], [-0.194, 0.023, 0],
                  [-0.111, -0.154, 0], [0.056, -0.190, 0], [0.143, -0.081, 0]])
ARRAY -= ARRAY.mean(axis=0)


def rng_for(split, *index):
    return np.random.default_rng(np.random.SeedSequence([SEED, split, *index]))


def direction(az, el):
    a, e = np.deg2rad(az), np.deg2rad(el)
    return np.stack((np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)), axis=-1)


def angles(u):
    return np.rad2deg(np.arctan2(u[..., 1], u[..., 0])) % 360, np.rad2deg(np.arcsin(np.clip(u[..., 2], -1, 1)))


def errors(az, el, true_az, true_el):
    a = (az - true_az + 180) % 360 - 180
    e = el - true_el
    u, v = direction(az, el), direction(true_az, true_el)
    # atan2 remains well conditioned near zero and pi.
    spherical = np.rad2deg(np.arctan2(np.linalg.norm(np.cross(u, v), axis=-1), np.sum(u * v, axis=-1)))
    return spherical, a, e


def unit_rms(x, axis=None):
    return x / np.sqrt(np.mean(x * x, axis=axis, keepdims=True) + 1e-20)


def sound(rng, t, source_fs, engine=False):
    """Continuous multi-rotor waveform with independent offsets and microvariation."""
    f0 = rng.uniform(85, 230)
    harmonic = np.zeros(len(t))
    rotors = 1 if engine else 4
    offsets = rng.normal(0, 0.012, rotors)
    for rotor in range(rotors):
        rate, phase = rng.uniform(0.6, 2.0), rng.uniform(0, 2 * np.pi)
        depth = rng.uniform(0.001, 0.004) if engine else rng.uniform(0.008, 0.025)
        inst_f = f0 * (1 + offsets[rotor]) * (1 + depth * np.sin(2 * np.pi * rate * t + phase))
        theta = 2 * np.pi * np.cumsum(inst_f) / source_fs
        for k in range(1, min(15, int(3200 / (f0 * 1.07))) + 1):
            harmonic += rng.uniform(0.6, 1.4) / k ** 0.65 * np.sin(k * theta + rng.uniform(0, 2 * np.pi))
    broad = signal.sosfilt(signal.butter(3, [120, 3200], fs=source_fs, btype="bandpass", output="sos"), rng.normal(size=len(t)))
    fraction = rng.uniform(0.82, 0.95) if engine else rng.uniform(0.55, 0.85)
    envelope = 1 + 0.12 * np.sin(2 * np.pi * rng.uniform(0.3, 1.5) * t + rng.uniform(0, 6.28))
    waveform = envelope * (np.sqrt(fraction) * unit_rms(harmonic) + np.sqrt(1 - fraction) * unit_rms(broad))
    return unit_rms(waveform), f0, fraction


def propagate(wave, source_t, t, u, distance, xyz, sound_speed, delays):
    """Spherical distances and time-domain interpolation; no steering vector used."""
    source_pos = np.asarray(distance)[..., None] * u
    result = np.empty((len(t), len(xyz)))
    for m, pos in enumerate(xyz):
        d = np.linalg.norm(source_pos - pos, axis=-1)
        relative_delay = (d - distance) / sound_speed + delays[m]
        result[:, m] = np.interp(t - relative_delay, source_t, wave) * distance / d
    return result


def simulate(seed_parts, scene, snr_db=None, duration=0.2, dynamic=False, coord_sd=0.0, delay_sd=0.0):
    """Return audio and scoring metadata. Metadata never enters Engine.analyze()."""
    rng = rng_for(*seed_parts)
    n = round(duration * FS)
    t = np.arange(n) / FS
    source_fs = 3 * FS
    source_t = np.arange(-round(0.05 * source_fs), round((duration + 0.05) * source_fs)) / source_fs
    c = rng.uniform(338, 348)
    # A separate random stream makes perturbation conditions paired exactly.
    perturb = rng_for(77, *seed_parts)
    xyz = ARRAY + perturb.normal(size=ARRAY.shape) * coord_sd
    delays = perturb.normal(size=8) * delay_sd
    gains = 10 ** (rng.normal(0, 0.6, 8) / 20)
    az, el = rng.uniform(0, 360), np.rad2deg(np.arcsin(rng.uniform(0, 1)))
    distance = rng.uniform(20, 80)
    if dynamic:
        speed = rng.uniform(6, 18) * rng.choice([-1, 1])
        turn = duration / 2
        az = (az + speed * np.minimum(t, turn) - 0.7 * speed * np.maximum(t - turn, 0)) % 360
        el = 40 + 25 * np.sin(2 * np.pi * t / duration + rng.uniform(0, 6.28))
        distance = distance + 1.5 * np.sin(2 * np.pi * t / duration)
    u = direction(az, el)
    noise = rng.normal(size=(n, 8))
    noise = unit_rms(noise)
    nuisance_az, nuisance_el = rng.uniform(0, 360), rng.uniform(0, 65)
    nuisance_f0 = None
    if scene == "wind":
        w = signal.sosfilt(signal.butter(2, 180, fs=FS, output="sos"), rng.normal(size=(n, 8)), axis=0)
        shared = signal.sosfilt(signal.butter(2, 90, fs=FS, output="sos"), rng.normal(size=n))
        noise = 0.35 * noise + unit_rms(w, axis=0) + 0.25 * unit_rms(shared)[:, None]
    elif scene in ("directional", "engine"):
        if scene == "engine":
            nuisance, nuisance_f0, _ = sound(rng, source_t, source_fs, engine=True)
        else:
            nuisance = signal.sosfilt(signal.butter(3, [160, 3200], fs=source_fs, btype="bandpass", output="sos"), rng.normal(size=len(source_t)))
        nuisance = propagate(unit_rms(nuisance), source_t, t, direction(nuisance_az, nuisance_el), rng.uniform(10, 60), xyz, c, delays)
        noise = 0.6 * noise + unit_rms(nuisance)
    elif scene != "sensor_noise":
        raise ValueError(scene)
    noise = unit_rms(noise * gains)
    frame_count = n // N
    center = np.arange(frame_count) * N + N // 2
    true_az = np.broadcast_to(az, (n,))[center]
    true_el = np.broadcast_to(el, (n,))[center]
    label = np.ones(frame_count, dtype=int) if snr_db is not None else np.zeros(frame_count, dtype=int)
    direct = np.zeros_like(noise)
    target_f0 = fraction = echo_gain = echo_delay = None
    if snr_db is not None:
        wave, target_f0, fraction = sound(rng, source_t, source_fs)
        direct = propagate(wave, source_t, t, u, distance, xyz, c, delays) * gains
        direct = unit_rms(direct)
        level = snr_db + (3 * np.sin(2 * np.pi * t / duration) if dynamic else np.zeros(n))
        direct *= (10 ** (level / 20))[:, None]
        echo_gain, echo_delay = rng.uniform(0.05, 0.25), rng.uniform(0.003, 0.012)
        echo_u = direction((az + rng.uniform(25, 80)) % 360, np.maximum(5, np.asarray(el) * 0.65))
        echo = propagate(wave, source_t, t - echo_delay, echo_u, distance, xyz, c, delays) * gains
        echo *= echo_gain * np.sqrt(np.mean(direct * direct) / (np.mean(echo * echo) + 1e-20))
        if dynamic:
            active = (t >= 2) & (t < duration - 2)
            ramp = np.clip((t - 2) / 0.02, 0, 1) * np.clip((duration - 2 - t) / 0.02, 0, 1)
            direct *= ramp[:, None]
            echo *= ramp[:, None]
            label = active[center].astype(int)
        audio = noise + direct + echo
    else:
        audio = noise
    measured_snr = 10 * np.log10((np.mean(direct.reshape(frame_count, N, 8) ** 2, axis=(1, 2)) + 1e-30) /
                                np.mean(noise.reshape(frame_count, N, 8) ** 2, axis=(1, 2)))
    meta = {"seed_parts": list(seed_parts), "scene": scene, "snr_db": snr_db,
            "sound_speed_m_s": c, "range_m_geometry_only": float(np.mean(distance)),
            "target_f0_hz": target_f0, "harmonic_power_fraction": fraction,
            "nuisance_f0_hz": nuisance_f0, "nuisance_az_deg": nuisance_az, "nuisance_el_deg": nuisance_el,
            "echo_gain": echo_gain, "echo_delay_s": echo_delay,
            "coord_sd_m": coord_sd, "delay_sd_s": delay_sd,
            "actual_xyz_m": xyz.tolist(), "actual_channel_delays_s": delays.tolist(), "channel_gain": gains.tolist()}
    truth = {"az": true_az, "el": true_el, "label": label, "measured_snr": measured_snr}
    return audio.astype(np.float32), truth, meta


class Engine:
    def __init__(self):
        self.i, self.j = np.triu_indices(8, 1)
        az, el = np.meshgrid(np.arange(0, 360, 3), np.arange(0, 90, 3))
        self.az = np.r_[az.ravel(), 0.0]
        self.el = np.r_[el.ravel(), 90.0]
        self.grid = direction(self.az, self.el)
        tau = -(ARRAY[self.i] - ARRAY[self.j]) @ self.grid.T / C0
        self.interp = 8
        self.fft_n = 512
        self.corr_n = self.fft_n * self.interp
        lag = (tau * FS * self.interp) % self.corr_n
        self.left = np.floor(lag).astype(int) % self.corr_n
        self.right = (self.left + 1) % self.corr_n
        self.frac = lag - np.floor(lag)
        self.pair_index = np.arange(len(self.i))[:, None]
        self.freq = fft.rfftfreq(512, 1 / FS)
        self.band = (self.freq >= 200) & (self.freq <= 3000)
        self.window = signal.windows.hann(512, sym=False)
        self.full_window = signal.windows.hann(N, sym=False)
        self.f0_candidates = np.arange(80, 241, 2)
        k = np.arange(1, 13)
        self.comb_index = np.rint(self.f0_candidates[:, None] * k * 2048 / FS).astype(int)
        self.comb_weights = 1 / np.sqrt(k)

    def analyze(self, audio, return_maps=False):
        if audio.shape != (N, 8) or not np.isfinite(audio).all():
            raise ValueError("Expected finite (1600, 8) frame at 8 kHz")
        begin = time.perf_counter_ns()
        x = audio.T.astype(np.float64)
        x -= x.mean(axis=1, keepdims=True)
        frames = np.lib.stride_tricks.sliding_window_view(x, 512, axis=1)[:, ::256, :]
        X = fft.rfft(frames * self.window, workers=1)
        power = np.mean(np.abs(X) ** 2, axis=1)
        G = np.mean(X[self.i] * np.conj(X[self.j]), axis=1)
        coherence = np.clip(np.abs(G) ** 2 / (power[self.i] * power[self.j] + 1e-20), 0, 1)
        phat = G / np.maximum(np.abs(G), 1e-20)
        full_power = np.mean(np.abs(fft.rfft(x * self.full_window, n=2048, workers=1)) ** 2, axis=0)
        floor = ndimage.median_filter(full_power, size=31, mode="nearest")
        contrast = np.log1p(full_power / np.maximum(floor, 1e-20)) - np.log(2)
        contrast = ndimage.gaussian_filter1d(contrast, 1.0)
        comb = (contrast[self.comb_index] * self.comb_weights).sum(axis=1) / self.comb_weights.sum()
        winner = int(np.argmax(comb))
        f0 = float(self.f0_candidates[winner])
        distance = np.abs(self.freq - np.rint(self.freq / f0) * f0)
        harmonic = 0.1 + 0.9 * np.exp(-0.5 * (distance / np.maximum(8, 0.012 * self.freq)) ** 2)
        harmonic *= self.band
        harmonic_coherence = np.sum(coherence * harmonic) / (len(self.i) * harmonic.sum())
        detector_score = float(max(0, comb[winner]) * (0.25 + harmonic_coherence))
        weights = [np.broadcast_to(self.band, G.shape), (0.05 + 0.95 * coherence) * self.band,
                   np.broadcast_to(harmonic, G.shape), (0.05 + 0.95 * coherence) * harmonic]
        front_ms = (time.perf_counter_ns() - begin) / 1e6
        out = {}
        for method, weight in zip(METHODS, weights):
            tic = time.perf_counter_ns()
            corr = fft.irfft(phat * weight, n=self.corr_n, workers=1, axis=-1)
            response = np.sum((1 - self.frac) * corr[self.pair_index, self.left] +
                              self.frac * corr[self.pair_index, self.right], axis=0)
            index = int(np.argmax(response))
            out[method] = {"az_hat": float(self.az[index]), "el_hat": float(self.el[index]),
                           "peak": float(response[index] * self.corr_n / (2 * weight.sum())),
                           "search_ms": (time.perf_counter_ns() - tic) / 1e6}
            if return_maps:
                out[method]["map"] = response * self.corr_n / (2 * weight.sum())
        return {"f0_hat_hz": f0, "score": detector_score, "harmonic_contrast": float(comb[winner]),
                "harmonic_coherence": float(harmonic_coherence), "frontend_ms": front_ms, "methods": out}


class CausalSmoother:
    def __init__(self, alpha=0.35, max_misses=5):
        self.alpha, self.max_misses = alpha, max_misses
        self.state, self.misses = None, 0

    def step(self, az, el, accept=True):
        if accept:
            observation = direction(az, el)
            value = observation if self.state is None else (1 - self.alpha) * self.state + self.alpha * observation
            self.state = value / np.linalg.norm(value)
            self.misses = 0
        else:
            self.misses += 1
            if self.misses > self.max_misses:
                self.state = None
        if self.state is None:
            return None
        return tuple(float(v) for v in angles(self.state))


def calibrate(scores, alpha=0.05):
    k = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    if not 1 <= k <= len(scores):
        raise ValueError("Too few validation negatives for the requested false-alarm level")
    return float(np.sort(scores)[k - 1]), k


def write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_audio(path, audio, truth, meta, wav=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path.with_suffix(".npz"), audio=audio, sample_rate=np.array(FS),
                        az_deg=truth["az"], el_deg=truth["el"], label=truth["label"],
                        measured_snr_db=truth["measured_snr"], metadata_json=np.array(json.dumps(meta)),
                        nominal_array_m=ARRAY)
    if wav:
        scale = 0.95 / np.max(np.abs(audio))
        wavfile.write(path.with_suffix(".wav"), FS, np.round(audio * scale * 32767).astype(np.int16))
        write_json(path.with_suffix(".json"), {**meta, "wav_multiplier_before_pcm16": float(scale),
                                             "npz_audio_unscaled": True, "simulation_only": True})


def result_rows(trial, split, audio, truth, meta, engine, threshold, condition="nominal"):
    result = engine.analyze(audio)
    base = {"trial_id": trial, "split": split, "scene": meta["scene"], "condition": condition,
            "seed_parts": json.dumps(meta["seed_parts"]), "label": int(truth["label"][0]),
            "snr_db": meta["snr_db"], "measured_snr_db": float(truth["measured_snr"][0]) if truth["label"][0] else None,
            "true_az": float(truth["az"][0]) if truth["label"][0] else None,
            "true_el": float(truth["el"][0]) if truth["label"][0] else None,
            "true_f0_hz": meta["target_f0_hz"], "f0_hat_hz": result["f0_hat_hz"],
            "score": result["score"], "detected": int(result["score"] > threshold) if threshold is not None else None,
            "harmonic_contrast": result["harmonic_contrast"], "harmonic_coherence": result["harmonic_coherence"],
            "frontend_ms": result["frontend_ms"]}
    rows = []
    for method, estimate in result["methods"].items():
        sphere, az_error, el_error = errors(estimate["az_hat"], estimate["el_hat"], truth["az"][0], truth["el"][0])
        rows.append({**base, "method": method, **estimate,
                     "processing_ms": result["frontend_ms"] + estimate["search_ms"],
                     "angular_error_deg": float(sphere) if base["label"] else None,
                     "az_error_deg": float(az_error) if base["label"] else None,
                     "el_error_deg": float(el_error) if base["label"] else None})
    return rows


def config(quick):
    return {"simulation_only": True, "mode": "quick" if quick else "full", "master_seed": SEED,
            "sample_rate_hz": FS, "frame_samples": N, "frame_seconds": N / FS,
            "nominal_sound_speed_m_s": C0, "array_m": ARRAY.tolist(),
            "diameter_m": float(np.max(np.linalg.norm(ARRAY[:, None] - ARRAY[None, :], axis=-1))),
            "validation_negatives_per_scene": 20 if quick else 200,
            "test_negatives_per_scene": 10 if quick else 250,
            "test_positives_per_scene_snr": 3 if quick else 50,
            "tracking_repeats_per_scene_snr": 1 if quick else 2,
            "tracking_snr_db": [-10, -5, 0], "tracking_seconds": 8 if quick else 24,
            "sensitivity_per_scene_snr": 1 if quick else 10,
            "sensitivity_snr_db": [-10, -5, 0],
            "sensitivity_conditions": {"nominal": [0, 0], "position_5mm": [0.005, 0],
                                       "delay_20us": [0, 20e-6], "both": [0.005, 20e-6]},
            "snr_db": list(SNRS), "scenes": list(SCENES), "methods": list(METHODS),
            "stft_nfft": 512, "stft_hop": 256, "stft_segments": 5, "frequency_band_hz": [200, 3000],
            "gcc_oversampling": 8, "grid_step_deg": 3, "grid_points": 3601,
            "f0_search_hz": [80, 240, 2], "f0_fft_n": 2048, "comb_harmonics": 12,
            "detector_alpha": 0.05, "detector_rule": "score > sorted_validation[ceil((n+1)*0.95)-1]",
            "tracking_alpha": 0.35, "max_held_misses": 5, "bootstrap_replicates": 2000,
            "split_codes": {"validation_negative": 1, "test_negative": 2, "test_positive": 3,
                            "sensitivity": 4, "tracking": 5, "bootstrap": 6, "self_test": 90},
            "threads": 1, "source_oversampling": 3,
            "protocol": "Fixed before full run; quick is engineering validation, not a tuning set; no method parameters are optimized on test."}


def self_test():
    start = time.perf_counter()
    engine = Engine()
    assert np.isclose(errors(1, 0, 359, 0)[0], 2)
    assert errors(1, 0, 359, 0)[1] == 2
    assert np.isclose(errors(15, 90, 200, 90)[0], 0, atol=1e-10)
    assert np.isclose(errors(180, 0, 0, 0)[0], 180)
    threshold, k = calibrate(list(range(100)))
    assert threshold == 95 and k == 96 and sum(np.arange(100) > threshold) == 4
    r = rng_for(90, 1)
    st = np.arange(-2400, 8000) / (3 * FS)
    source = signal.sosfilt(signal.butter(3, [200, 2800], btype="bandpass", fs=3 * FS, output="sos"), r.normal(size=len(st)))
    t = np.arange(N) / FS
    for az, el in [(1, 25), (123, 42), (271, 65), (359, 3), (0, 90)]:
        audio = propagate(source, st, t, direction(az, el), 35.0, ARRAY, 346.0, np.zeros(8))
        result = engine.analyze(audio)
        for method in METHODS:
            estimate = result["methods"][method]
            assert errors(estimate["az_hat"], estimate["el_hat"], az, el)[0] < 5, (method, az, el, estimate)
    x, truth, meta = simulate((90, 2), "wind", -5)
    y, _, _ = simulate((90, 2), "wind", -5)
    assert np.array_equal(x, y) and abs(truth["measured_snr"][0] + 5) < 1e-8
    z, _, _ = simulate((90, 3), "wind", -5)
    assert not np.array_equal(x, z)
    smoother = CausalSmoother()
    assert smoother.step(359, 20) is not None
    a, _ = smoother.step(1, 20)
    assert min(a, 360 - a) < 2
    for _ in range(5):
        assert smoother.step(100, 50, False) is not None
    assert smoother.step(100, 50, False) is None
    first, second = CausalSmoother(), CausalSmoother()
    prefix = [(20, 30), (25, 31), (27, 32)]
    assert [first.step(*p) for p in prefix] == [second.step(*p) for p in prefix]
    # FFT cross-spectrum and lag lookup must match direct complex steering.
    m, g = 5, 91
    tau = -(ARRAY[engine.i[m]] - ARRAY[engine.j[m]]) @ engine.grid[g] / C0
    spec = np.exp(-2j * np.pi * engine.freq * tau) * engine.band
    cc = fft.irfft(spec, n=engine.corr_n)
    lag_value = (1 - engine.frac[m, g]) * cc[engine.left[m, g]] + engine.frac[m, g] * cc[engine.right[m, g]]
    assert abs(lag_value * engine.corr_n / (2 * engine.band.sum()) - 1) < 0.003
    record = {"passed": True, "checks": ["wrapped and spherical angular error", "finite-sample threshold order statistic",
              "five known-direction broadband localization cases, all four weights", "reproducible independent seeds and SNR",
              "wrap-safe causal smoothing and bounded hold", "frequency/time steering sign agreement"],
              "seconds": time.perf_counter() - start, "python": sys.version}
    write_json(ROOT / "results" / "self_test.json", record)
    print(json.dumps(record), flush=True)


def run(quick=False):
    cfg = config(quick)
    out = ROOT / "results" / ("quick" if quick else "full")
    data = ROOT / "data" / "synthetic" / cfg["mode"]
    out.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    if (out / "run_complete.json").exists():
        raise SystemExit(f"Completed run exists at {out}; move it explicitly before rerunning (no silent overwrite).")
    cfg["started_utc"] = datetime.now(timezone.utc).isoformat()
    cfg["experiment_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(out / "config.json", cfg)
    start = time.perf_counter()
    engine = Engine()
    setup_s = time.perf_counter() - start
    engine.analyze(simulate((90, 10), "sensor_noise", 0)[0])  # warm-up excluded
    manifest, validation = [], []
    for s, scene in enumerate(SCENES):
        for j in range(cfg["validation_negatives_per_scene"]):
            audio, truth, meta = simulate((1, s, j), scene)
            manifest.append({"trial_id": f"val-{s}-{j}", **meta})
            save_audio(data / "validation" / f"val-{s}-{j}", audio, truth, meta)
            result = engine.analyze(audio)
            validation.append({"trial_id": f"val-{s}-{j}", "scene": scene, "seed_parts": json.dumps(meta["seed_parts"]),
                               "score": result["score"], "f0_hat_hz": result["f0_hat_hz"]})
        print(f"validation {scene} complete", flush=True)
    threshold, k = calibrate([row["score"] for row in validation])
    write_csv(out / "validation_negatives.csv", validation)
    write_json(out / "detector_calibration.json", {"threshold": threshold, "order_statistic_1_based": k,
              "n": len(validation), "target_fpr": 0.05, "rule": "strictly greater than threshold",
              "validation_fpr": float(np.mean([r["score"] > threshold for r in validation]))})
    rows = []
    for s, scene in enumerate(SCENES):
        for j in range(cfg["test_negatives_per_scene"]):
            audio, truth, meta = simulate((2, s, j), scene)
            trial = f"neg-{s}-{j}"
            manifest.append({"trial_id": trial, **meta})
            save_audio(data / "test" / trial, audio, truth, meta)
            rows.extend(result_rows(trial, "test", audio, truth, meta, engine, threshold))
            if j == 0:
                save_audio(data / f"representative_negative_{scene}", audio, truth, meta, wav=True)
        for si, snr in enumerate(SNRS):
            for j in range(cfg["test_positives_per_scene_snr"]):
                audio, truth, meta = simulate((3, s, si, j), scene, snr)
                trial = f"pos-{s}-{si}-{j}"
                manifest.append({"trial_id": trial, **meta})
                save_audio(data / "test" / trial, audio, truth, meta)
                rows.extend(result_rows(trial, "test", audio, truth, meta, engine, threshold))
                if j == 0 and snr == -5:
                    save_audio(data / f"representative_positive_{scene}", audio, truth, meta, wav=True)
        write_csv(out / "test_frames.csv", rows)
        print(f"test {scene} complete; {len(rows) // 4} independent trials", flush=True)
    sensitivity = []
    for s, scene in enumerate(SCENES):
        for si, snr in enumerate(cfg["sensitivity_snr_db"]):
            for j in range(cfg["sensitivity_per_scene_snr"]):
                for condition, (pos_sd, delay_sd) in cfg["sensitivity_conditions"].items():
                    audio, truth, meta = simulate((4, s, si, j), scene, snr, coord_sd=pos_sd, delay_sd=delay_sd)
                    trial = f"sens-{s}-{si}-{j}"
                    manifest.append({"trial_id": trial, "condition": condition, **meta})
                    save_audio(data / "sensitivity" / f"{trial}-{condition}", audio, truth, meta)
                    sensitivity.extend(result_rows(trial, "sensitivity", audio, truth, meta, engine, threshold, condition))
        print(f"sensitivity {scene} complete", flush=True)
    write_csv(out / "sensitivity_frames.csv", sensitivity)
    tracks = []
    for s, scene in enumerate(SCENES):
        for si, snr in enumerate(cfg["tracking_snr_db"]):
            for j in range(cfg["tracking_repeats_per_scene_snr"]):
                seq = f"seq-{s}-{si}-{j}"
                audio, truth, meta = simulate((5, s, si, j), scene, snr, cfg["tracking_seconds"], dynamic=True)
                manifest.append({"trial_id": seq, **meta})
                save_audio(data / "sequences" / seq, audio, truth, meta, wav=(s == 0 and si == 1 and j == 0))
                smoothers = {(method, mode): CausalSmoother() for method in METHODS for mode in ("smooth_all", "gated")}
                consecutive_misses = 0
                for frame in range(len(truth["label"])):
                    estimate = engine.analyze(audio[frame * N:(frame + 1) * N])
                    detected = estimate["score"] > threshold
                    consecutive_misses = 0 if detected else consecutive_misses + 1
                    for method in METHODS:
                        raw = estimate["methods"][method]
                        candidates = {"raw": (raw["az_hat"], raw["el_hat"]),
                                      "smooth_all": smoothers[method, "smooth_all"].step(raw["az_hat"], raw["el_hat"]),
                                      "gated": smoothers[method, "gated"].step(raw["az_hat"], raw["el_hat"], detected)}
                        for mode, value in candidates.items():
                            err = errors(*value, truth["az"][frame], truth["el"][frame]) if value else (None, None, None)
                            tracks.append({"sequence_id": seq, "scene": scene, "snr_db": snr, "frame": frame,
                                           "time_s": (frame + 0.5) * N / FS, "label": int(truth["label"][frame]),
                                           "measured_snr_db": float(truth["measured_snr"][frame]) if truth["label"][frame] else None,
                                           "true_az": float(truth["az"][frame]), "true_el": float(truth["el"][frame]),
                                           "method": method, "mode": mode, "detected": int(detected),
                                           "score": estimate["score"], "f0_hat_hz": estimate["f0_hat_hz"], "valid": int(value is not None),
                                           "stale": int(mode == "gated" and value is not None and not detected),
                                           "consecutive_missed_detections": consecutive_misses,
                                           "az_hat": value[0] if value else None, "el_hat": value[1] if value else None,
                                           "angular_error_deg": float(err[0]) if value and truth["label"][frame] else None,
                                           "az_error_deg": float(err[1]) if value and truth["label"][frame] else None,
                                           "el_error_deg": float(err[2]) if value and truth["label"][frame] else None})
                print(f"tracking {seq} saved ({len(truth['label'])} frames)", flush=True)
    write_csv(out / "tracking_frames.csv", tracks)
    with (data / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for meta in manifest:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    distributions = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions(path=[str(ROOT / ".python-packages")])}
    (ROOT / "code" / "requirements-lock.txt").write_text("# Python 3.12; exact versions used, including plotting/PDF helpers\n" +
                                                        "\n".join(f"{k}=={v}" for k, v in sorted(distributions.items(), key=lambda x: x[0].lower())) + "\n", encoding="utf-8")
    try:
        cpu = subprocess.check_output(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"], text=True).strip()
    except (OSError, subprocess.SubprocessError):
        cpu = platform.processor()
    write_json(out / "runtime_environment.json", {"python": sys.version, "executable": sys.executable,
               "platform": platform.platform(), "cpu": cpu, "logical_cpus": os.cpu_count(),
               "thread_environment": {k: os.environ[k] for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
               "packages": distributions, "setup_seconds_excluded": setup_s,
               "experiment_wall_seconds": time.perf_counter() - start,
               "timing_definition": "perf_counter_ns; frontend plus one SRP search; warm-up, geometry setup, synthesis, file I/O, plotting and 200-ms acquisition excluded; host loaded state not controlled"})
    write_json(out / "run_complete.json", {"completed_utc": datetime.now(timezone.utc).isoformat(),
               "test_trials": len(rows) // 4, "sensitivity_pairs": len(sensitivity) // 16,
               "sequence_count": 4 * 3 * cfg["tracking_repeats_per_scene_snr"]})
    from summarize_experiment import summarize
    summarize(out)
    print(f"COMPLETE: {out}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.quick or args.full:
        run(quick=args.quick)
    if not (args.self_test or args.quick or args.full):
        parser.print_help()
