"""Executable artifact audit; checks consistency/reconstruction, never desired performance."""
from pathlib import Path
import json
import hashlib

from experiment import ROOT, METHODS, SCENES, SNRS, Engine, simulate, calibrate, write_json
from summarize_experiment import read_csv, roc, bootstrap_mean
import numpy as np


def main():
    out = ROOT / "results" / "full"
    data = ROOT / "data" / "synthetic" / "full"
    cfg = json.loads((out / "config.json").read_text(encoding="utf-8"))
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    rows = read_csv(out / "test_frames.csv")
    sensitivity = read_csv(out / "sensitivity_frames.csv")
    tracks = read_csv(out / "tracking_frames.csv")
    val = read_csv(out / "validation_negatives.csv")
    checks = []
    assert len(rows) == 2000 * 4 and len(val) == 800 and len(sensitivity) == 120 * 4 * 4
    assert len(tracks) == 24 * 120 * 4 * 3
    base = [r for r in rows if r["method"] == "phat"]
    positive = [r for r in base if r["label"]]
    negative = [r for r in base if not r["label"]]
    assert len(positive) == len(negative) == 1000
    assert len(set(r["trial_id"] for r in base)) == 2000
    assert len(set(r["seed_parts"] for r in base + val)) == 2800
    threshold, rank = calibrate([r["score"] for r in val])
    assert threshold == summary["calibration"]["threshold"] and rank == 761
    for r in rows:
        assert r["detected"] == (r["score"] > threshold)
    checks.append("exact counts, disjoint trial seeds, frozen threshold and all detection flags")
    for method in METHODS:
        chosen = [r for r in rows if r["method"] == method and r["label"]]
        assert np.isclose(np.mean([r["angular_error_deg"] for r in chosen]), summary["localization"][method]["overall"]["mean_deg"])
    assert np.isclose(np.mean([r["detected"] for r in positive]), summary["detection"]["overall"]["tpr"])
    assert np.isclose(np.mean([r["detected"] for r in negative]), summary["detection"]["overall"]["fpr"])
    checks.append("summary means/recall/false alarms reproduce directly from raw CSV")
    for r in tracks:
        if r["mode"] == "gated":
            assert r["stale"] == bool(r["valid"] and not r["detected"])
            if r["consecutive_missed_detections"] >= 6:
                assert not r["valid"]
        else:
            assert r["valid"] and not r["stale"]
    checks.append("held outputs distinguished from detections, state expires after six misses")
    assert roc([{"score": 1, "label": 1}, {"score": 0, "label": 0}])[0] == 1
    assert roc([{"score": 1, "label": 0}, {"score": 0, "label": 1}])[0] == 0
    assert roc([{"score": 1, "label": 0}, {"score": 1, "label": 1}])[0] == 0.5
    assert bootstrap_mean([2, 2, 2]) == [2.0, 2.0]
    assert bootstrap_mean([]) == [None, None]
    assert bootstrap_mean([2]) == [None, None]
    checks.append("ROC handles perfect/reversed/tied scores and bootstrap constant-unit invariant")
    engine = Engine()
    reconstructed = []
    for scene in range(4):
        for prefix, parts, snr in [("pos", (3, scene, 2, 0), -5), ("neg", (2, scene, 0), None)]:
            trial_id = f"pos-{scene}-2-0" if prefix == "pos" else f"neg-{scene}-0"
            saved = np.load(data / "test" / f"{trial_id}.npz")
            audio, truth, meta = simulate(parts, SCENES[scene], snr)
            assert np.array_equal(saved["audio"], audio), trial_id
            result = engine.analyze(saved["audio"])
            for row in [r for r in rows if r["trial_id"] == trial_id]:
                assert np.isclose(row["score"], result["score"], rtol=1e-13)
                assert row["az_hat"] == result["methods"][row["method"]]["az_hat"]
                assert row["el_hat"] == result["methods"][row["method"]]["el_hat"]
            reconstructed.append(trial_id)
    checks.append("eight prespecified positive/negative trials reconstruct bit-exact float32 waveforms and estimates")
    file_count = total_bytes = frame_count = 0
    for directory, expected_count in [("validation", 800), ("test", 2000), ("sensitivity", 480), ("sequences", 24)]:
        files = list((data / directory).glob("*.npz"))
        assert len(files) == expected_count, (directory, len(files))
        for file in files:
            with np.load(file) as saved:
                audio = saved["audio"]
                assert audio.dtype == np.float32 and audio.shape[1] == 8 and np.isfinite(audio).all()
                expected_frames = 120 if directory == "sequences" else 1
                assert audio.shape[0] == expected_frames * 1600
                assert len(saved["label"]) == expected_frames and int(saved["sample_rate"]) == 8000
                frame_count += expected_frames
            file_count += 1
            total_bytes += file.stat().st_size
    checks.append("all validation/test/sensitivity/sequence NPZ audio arrays readable, finite, correct shape/rate/labels")
    assert cfg["experiment_sha256"] == hashlib.sha256((ROOT / "code" / "experiment.py").read_bytes()).hexdigest()
    for record in json.loads((out / "artifact_manifest.json").read_text(encoding="utf-8")):
        p = ROOT / record["path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == record["sha256"], p
    checks.append("executed source hash matches current experiment; every artifact manifest SHA256 matches")
    result = {"passed": True, "checks": checks, "reconstructed_trial_ids": reconstructed,
              "npz_recordings_audited": file_count, "audio_frames_audited": frame_count,
              "core_audio_bytes": total_bytes, "core_audio_mib": total_bytes / 1024 ** 2}
    write_json(out / "verification.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
