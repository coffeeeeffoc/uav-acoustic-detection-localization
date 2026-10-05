"""Tables, independent-unit bootstrap intervals, figures, and exact methods report."""
from pathlib import Path
import csv
import json
import sys
import hashlib

from experiment import (ROOT, METHODS, SCENES, SNRS, ARRAY, FS, N, SEED, Engine, direction,
                        errors, rng_for, write_csv, write_json)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

LABELS = {"phat": "SRP-PHAT", "coherence": "Coherence", "harmonic": "Harmonic", "combined": "Combined"}
COLORS = {"phat": "#333333", "coherence": "#0072B2", "harmonic": "#D55E00", "combined": "#009E73"}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k, v in row.items():
            if not v:
                row[k] = None
            else:
                try:
                    row[k] = float(v)
                except ValueError:
                    pass
    return rows


def values(rows, key):
    return np.array([r[key] for r in rows if r[key] is not None], dtype=float)


def mean(a):
    return float(np.mean(a)) if len(a) else None


def wilson(k, n):
    if not n:
        return [None, None]
    z = norm.ppf(0.975)
    p = k / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(center - half), float(center + half)]


def bootstrap_mean(a, strata=None, seed=0, replicates=2000):
    """Each input is ONE independent trial/sequence, never a dynamic frame."""
    a = np.asarray(a, dtype=float)
    if len(a) < 2:
        return [None, None]
    groups = np.asarray(strata) if strata is not None else np.zeros(len(a))
    rng = rng_for(6, seed)
    sample = np.zeros(replicates)
    for group in np.unique(groups):
        v = a[groups == group]
        sample += v[rng.integers(0, len(v), size=(replicates, len(v)))].sum(axis=1) / len(a)
    return [float(v) for v in np.quantile(sample, [0.025, 0.975])]


def detection(pos, neg):
    p, n = values(pos, "detected"), values(neg, "detected")
    tpr, fpr = mean(p), mean(n)
    # Equivalent to stratified resampling of positives and negatives, preserving class balance.
    rng = rng_for(6, 900)
    b = np.zeros(2000)
    for rows, sign in [(pos, 1), (neg, -1)]:
        groups = sorted(set((r["scene"], r["snr_db"]) for r in rows), key=str)
        for scene, snr in groups:
            v = values([r for r in rows if r["scene"] == scene and r["snr_db"] == snr], "detected")
            b += sign * v[rng.integers(0, len(v), size=(2000, len(v)))].sum(axis=1) / (2 * len(rows))
    lo, hi = np.quantile(0.5 + b, [0.025, 0.975])
    return {"positive_n": len(p), "negative_n": len(n), "tp": int(p.sum()), "fp": int(n.sum()),
            "tpr": tpr, "fpr": fpr, "balanced_accuracy": (tpr + 1 - fpr) / 2,
            "tpr_ci95": wilson(p.sum(), len(p)), "fpr_ci95": wilson(n.sum(), len(n)),
            "balanced_accuracy_ci95": [float(lo), float(hi)]}


def localization(rows):
    e = values(rows, "angular_error_deg")
    detected = [r for r in rows if r["detected"]]
    de = values(detected, "angular_error_deg")
    strata = [f"{r['scene']}:{r['snr_db']}" for r in rows]
    return {"n": len(rows), "mean_deg": mean(e), "median_deg": float(np.median(e)),
            "rmse_deg": float(np.sqrt(np.mean(e * e))), "p90_deg": float(np.quantile(e, 0.90)),
            "p95_deg": float(np.quantile(e, 0.95)), "mean_ci95": bootstrap_mean(e, strata),
            "azimuth_mae_deg": mean(np.abs(values(rows, "az_error_deg"))),
            "elevation_mae_deg": mean(np.abs(values(rows, "el_error_deg"))),
            "within10_rate": mean(e <= 10), "detected_n": len(detected),
            "detected_mean_deg": mean(de), "detected_median_deg": float(np.median(de)) if len(de) else None,
            "detected_within10_rate": mean(de <= 10),
            "joint_detection_within10_rate": sum(r["detected"] and r["angular_error_deg"] <= 10 for r in rows) / len(rows)}


def longest_run(flags):
    best = count = 0
    for flag in flags:
        count = count + 1 if flag else 0
        best = max(best, count)
    return best


def roc(rows):
    ordered = sorted(rows, key=lambda r: -r["score"])
    positive_n = sum(r["label"] for r in ordered)
    negative_n = len(ordered) - positive_n
    points = [{"threshold_inclusive": None, "fpr": 0.0, "tpr": 0.0}]
    tp = fp = 0
    for i, row in enumerate(ordered):
        tp += row["label"]
        fp += 1 - row["label"]
        if i == len(ordered) - 1 or ordered[i + 1]["score"] != row["score"]:
            points.append({"threshold_inclusive": row["score"], "fpr": fp / negative_n, "tpr": tp / positive_n})
    auc = float(np.trapezoid([p["tpr"] for p in points], [p["fpr"] for p in points]))
    return auc, points


def sequence_metrics(rows):
    positive = [r for r in rows if r["label"]]
    negative = [r for r in rows if not r["label"]]
    valid = [r for r in positive if r["valid"]]
    e = values(valid, "angular_error_deg")
    turn = (rows[-1]["time_s"] + 0.1) / 2
    turning = values([r for r in valid if abs(r["time_s"] - turn) <= 1], "angular_error_deg")
    velocity_errors = []
    step_angles = []
    for a, b in zip(rows, rows[1:]):
        if not (a["valid"] and b["valid"] and a["label"] and b["label"]):
            continue
        delta_hat = direction(b["az_hat"], b["el_hat"]) - direction(a["az_hat"], a["el_hat"])
        delta_true = direction(b["true_az"], b["true_el"]) - direction(a["true_az"], a["true_el"])
        velocity_errors.append(np.rad2deg(np.linalg.norm(delta_hat - delta_true)) / 0.2)
        step_angles.append(float(errors(b["az_hat"], b["el_hat"], a["az_hat"], a["el_hat"])[0]))
    detected = [r["detected"] for r in positive]
    windows = [detected[i:i + 25] for i in range(len(detected) - 24)]
    passing_windows = [np.mean(w) >= 0.8 and longest_run([not d for d in w]) * 0.2 <= 0.5 for w in windows]
    first = next((r["time_s"] + 0.1 - 2 for r in positive if r["detected"]), None)
    return {"positive_frames": len(positive), "available_frames": len(valid),
            "coverage": len(valid) / len(positive), "mean_deg": mean(e),
            "stale_positive_rate": mean(values(positive, "stale")),
            "p95_deg": float(np.quantile(e, 0.95)) if len(e) else None,
            "turn_mean_deg": mean(turning), "azimuth_mae_deg": mean(np.abs(values(valid, "az_error_deg"))),
            "elevation_mae_deg": mean(np.abs(values(valid, "el_error_deg"))),
            "within10_all_positive_rate": sum(r["angular_error_deg"] <= 10 for r in valid) / len(positive),
            "detected_within10_all_positive_rate": sum(r["detected"] and r["angular_error_deg"] <= 10 for r in valid) / len(positive),
            "chord_velocity_rmse_deg_s": float(np.sqrt(np.mean(np.square(velocity_errors)))) if velocity_errors else None,
            "step_rms_deg": float(np.sqrt(np.mean(np.square(step_angles)))) if step_angles else None,
            "detection_recall": mean(detected), "detection_fpr": mean(values(negative, "detected")),
            "absent_output_rate": mean(values(negative, "valid")), "max_miss_s": longest_run([not d for d in detected]) * 0.2,
            "first_detection_delay_s": first, "five_second_window_pass_rate": mean(passing_windows)}


def table(rows, columns):
    def cell(value):
        if value is None:
            return "NA"
        if isinstance(value, (float, np.floating)):
            return f"{value:.4f}"
        return str(value)
    head = "| " + " | ".join(columns) + " |\n|" + "|".join(["---"] * len(columns)) + "|\n"
    return head + "\n".join("| " + " | ".join(cell(r.get(k)) for k in columns) + " |" for r in rows) + "\n"


def summarize(out):
    cfg = json.loads((out / "config.json").read_text(encoding="utf-8"))
    cal = json.loads((out / "detector_calibration.json").read_text(encoding="utf-8"))
    env = json.loads((out / "runtime_environment.json").read_text(encoding="utf-8"))
    rows = read_csv(out / "test_frames.csv")
    sens = read_csv(out / "sensitivity_frames.csv")
    track = read_csv(out / "tracking_frames.csv")
    base = [r for r in rows if r["method"] == "phat"]
    pos = [r for r in base if r["label"]]
    neg = [r for r in base if not r["label"]]
    summary = {"simulation_only": True, "mode": cfg["mode"], "calibration": cal,
               "detection": {"overall": detection(pos, neg),
                             "by_snr": {str(s): detection([r for r in pos if r["snr_db"] == s], neg) for s in SNRS},
                             "by_scene": {s: detection([r for r in pos if r["scene"] == s], [r for r in neg if r["scene"] == s]) for s in SCENES}},
               "localization": {}, "paired_improvements": [], "sensitivity": [], "tracking": {}, "runtime": {},
               "f0_diagnostic": {"median_absolute_percentage_error": float(np.median([100 * abs(r["f0_hat_hz"] - r["true_f0_hz"]) / r["true_f0_hz"] for r in pos])),
                                 "note": "Diagnostic against nominal source base; multiple perturbed rotors have no single instantaneous exact f0. Never provided to estimator."}}
    auc, roc_points = roc(base)
    summary["detection"]["descriptive_test_auc"] = auc
    summary["detection"]["descriptive_auc_by_scene"] = {s: roc([r for r in base if r["scene"] == s])[0] for s in SCENES}
    write_csv(out / "test_roc.csv", roc_points)
    local_table = []
    for method in METHODS:
        selected = [r for r in rows if r["method"] == method and r["label"]]
        overall = localization(selected)
        by_snr = {str(s): localization([r for r in selected if r["snr_db"] == s]) for s in SNRS}
        by_scene = {s: localization([r for r in selected if r["scene"] == s]) for s in SCENES}
        by_cell = {f"{scene}:{snr}": localization([r for r in selected if r["scene"] == scene and r["snr_db"] == snr]) for scene in SCENES for snr in SNRS}
        summary["localization"][method] = {"overall": overall, "by_snr": by_snr, "by_scene": by_scene, "by_scene_snr": by_cell}
        local_table.append({"method": method, "group": "all", **overall})
        local_table.extend({"method": method, "group": f"snr={snr}", **v} for snr, v in by_snr.items())
        local_table.extend({"method": method, "group": scene, **v} for scene, v in by_scene.items())
        local_table.extend({"method": method, "group": cell, **v} for cell, v in by_cell.items())
        if method != "phat":
            match = {r["trial_id"]: r for r in selected}
            for group, subset in [("all", pos)] + [(f"snr={s}", [r for r in pos if r["snr_db"] == s]) for s in SNRS] + [(s, [r for r in pos if r["scene"] == s]) for s in SCENES]:
                differences = [r["angular_error_deg"] - match[r["trial_id"]]["angular_error_deg"] for r in subset]
                ci = bootstrap_mean(differences, [f"{r['scene']}:{r['snr_db']}" for r in subset])
                summary["paired_improvements"].append({"method": method, "group": group, "n": len(subset),
                        "baseline_minus_method_mean_deg": mean(differences), "ci95_low": ci[0], "ci95_high": ci[1]})
        timing = values([r for r in rows if r["method"] == method], "processing_ms")
        summary["runtime"][method] = {"n": len(timing), "median_ms": float(np.median(timing)),
                  "p95_ms": float(np.quantile(timing, 0.95)), "mean_ms": mean(timing), "max_ms": float(timing.max()),
                  "compute_throughput_fps": 1000 / mean(timing), "window_plus_p95_ms": 200 + float(np.quantile(timing, 0.95))}
    for method in METHODS:
        baseline = {r["trial_id"]: r for r in sens if r["method"] == method and r["condition"] == "nominal"}
        for condition in cfg["sensitivity_conditions"]:
            selected = [r for r in sens if r["method"] == method and r["condition"] == condition]
            differences = [r["angular_error_deg"] - baseline[r["trial_id"]]["angular_error_deg"] for r in selected]
            ci = bootstrap_mean(differences, [f"{r['scene']}:{r['snr_db']}" for r in selected])
            summary["sensitivity"].append({"method": method, "condition": condition, "n": len(selected),
                "mean_deg": mean(values(selected, "angular_error_deg")), "increase_vs_nominal_deg": mean(differences),
                "ci95_low": ci[0], "ci95_high": ci[1]})
    sequence_table = []
    for seq in sorted(set(r["sequence_id"] for r in track)):
        seq_rows = [r for r in track if r["sequence_id"] == seq]
        for method in METHODS:
            for mode in ("raw", "smooth_all", "gated"):
                selected = [r for r in seq_rows if r["method"] == method and r["mode"] == mode]
                sequence_table.append({"sequence_id": seq, "scene": selected[0]["scene"], "snr_db": selected[0]["snr_db"],
                                       "method": method, "mode": mode, **sequence_metrics(selected)})
    tracking_table = []
    for method in METHODS:
        summary["tracking"][method] = {}
        for mode in ("raw", "smooth_all", "gated"):
            selected = [r for r in sequence_table if r["method"] == method and r["mode"] == mode]
            metric = {k: mean(values(selected, k)) for k in selected[0] if k not in ("sequence_id", "scene", "snr_db", "method", "mode")}
            metric["sequences"] = len(selected)
            metric["sequences_with_output"] = sum(r["available_frames"] > 0 for r in selected)
            metric["sequences_with_detection"] = sum(r["first_detection_delay_s"] is not None for r in selected)
            metric["mean_deg_ci95"] = bootstrap_mean(values(selected, "mean_deg"))
            summary["tracking"][method][mode] = metric
            tracking_table.append({"method": method, "mode": mode, **metric})
        raw = {r["sequence_id"]: r for r in sequence_table if r["method"] == method and r["mode"] == "raw"}
        smoothed = [r for r in sequence_table if r["method"] == method and r["mode"] == "smooth_all"]
        d = [raw[r["sequence_id"]]["mean_deg"] - r["mean_deg"] for r in smoothed]
        summary["tracking"][method]["paired_raw_minus_smooth"] = {"mean_deg": mean(d), "ci95": bootstrap_mean(d),
                                                                 "independent_sequences": len(d)}
    det_table = [{"group": "all", **summary["detection"]["overall"]}]
    det_table += [{"group": f"snr={k}", **v} for k, v in summary["detection"]["by_snr"].items()]
    det_table += [{"group": k, **v} for k, v in summary["detection"]["by_scene"].items()]
    runtime_table = [{"method": k, **v} for k, v in summary["runtime"].items()]
    write_csv(out / "detection_summary.csv", det_table)
    write_csv(out / "localization_summary.csv", local_table)
    write_csv(out / "paired_improvements.csv", summary["paired_improvements"])
    write_csv(out / "sensitivity_summary.csv", summary["sensitivity"])
    write_csv(out / "tracking_sequence_metrics.csv", sequence_table)
    write_csv(out / "tracking_summary.csv", tracking_table)
    write_csv(out / "runtime_summary.csv", runtime_table)
    write_json(out / "summary.json", summary)
    figures(out, cfg, summary, track)
    report = methods_text(cfg, cal, env, summary)
    report += "\n## Detection (rates, not percentages)\n\n" + table(det_table, ["group", "positive_n", "negative_n", "tp", "fp", "tpr", "fpr", "balanced_accuracy", "balanced_accuracy_ci95"])
    report += "\n## Unconditional and detected-only localization\n\n" + table(local_table, ["method", "group", "n", "mean_deg", "median_deg", "p95_deg", "azimuth_mae_deg", "elevation_mae_deg", "detected_n", "detected_mean_deg", "joint_detection_within10_rate"])
    report += "\n## Paired localization improvements (positive is better than PHAT)\n\n" + table(summary["paired_improvements"], ["method", "group", "n", "baseline_minus_method_mean_deg", "ci95_low", "ci95_high"])
    report += "\n## Sensor-error sensitivity (positive increase is worse)\n\n" + table(summary["sensitivity"], ["method", "condition", "n", "mean_deg", "increase_vs_nominal_deg", "ci95_low", "ci95_high"])
    report += "\n## Tracking (equal-weight means of independent sequence metrics)\n\n" + table(tracking_table, ["method", "mode", "sequences", "sequences_with_output", "coverage", "mean_deg", "p95_deg", "turn_mean_deg", "within10_all_positive_rate", "chord_velocity_rmse_deg_s", "absent_output_rate"])
    report += "\n### Tracking detection continuity, latency and paired intervals\n\n" + table(tracking_table, ["method", "mode", "detection_recall", "detection_fpr", "max_miss_s", "sequences_with_detection", "first_detection_delay_s", "five_second_window_pass_rate"])
    report += "\n" + table([{"method": m, **summary["tracking"][m]["paired_raw_minus_smooth"]} for m in METHODS], ["method", "independent_sequences", "mean_deg", "ci95"])
    report += "\n## Host-only processing benchmark\n\n" + table(runtime_table, ["method", "n", "median_ms", "p95_ms", "max_ms", "compute_throughput_fps", "window_plus_p95_ms"])
    report += "\n## Per-sequence results (no sequence discarded)\n\n" + table(sequence_table, ["sequence_id", "scene", "snr_db", "method", "mode", "coverage", "mean_deg", "p95_deg", "turn_mean_deg", "within10_all_positive_rate", "max_miss_s"])
    (out / "method_and_results.md").write_text(report, encoding="utf-8")
    source_paths = [ROOT / "code" / name for name in ("experiment.py", "summarize_experiment.py", "verify_experiment.py", "requirements-lock.txt", "EXPERIMENT_README.md")]
    source_manifest = [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_paths]
    write_json(out / "source_manifest.json", {"sources": source_manifest,
               "executed_experiment_sha256": cfg["experiment_sha256"],
               "current_experiment_matches_executed": source_manifest[0]["sha256"] == cfg["experiment_sha256"],
               "analysis_note": "Summary and audit source hashes describe final analysis; acoustic generation source hash was fixed in config before execution."})
    # Root-level index files are convenient for the separately owned manuscript builder.
    if cfg["mode"] == "full":
        write_json(ROOT / "results" / "summary.json", summary)
        (ROOT / "results" / "method_and_results.md").write_text(report, encoding="utf-8")
    inventory = []
    artifact_paths = list(source_paths)
    if cfg["mode"] == "full":
        artifact_paths += [ROOT / "results" / "summary.json", ROOT / "results" / "method_and_results.md", ROOT / "results" / "self_test.json"]
    for directory in (out, ROOT / "data" / "synthetic" / cfg["mode"], ROOT / "figures" / cfg["mode"]):
        artifact_paths += [p for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "artifact_manifest.json"]
    for p in artifact_paths:
        inventory.append({"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                          "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    write_json(out / "artifact_manifest.json", inventory)
    print(json.dumps({"detection": summary["detection"]["overall"], "localization_mean_deg": {m: summary["localization"][m]["overall"]["mean_deg"] for m in METHODS}}, indent=2), flush=True)


def figures(out, cfg, summary, track):
    target = ROOT / "figures" / cfg["mode"]
    target.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.labelsize": 11, "axes.titlesize": 11, "legend.fontsize": 10,
                         "xtick.labelsize": 10, "ytick.labelsize": 10, "savefig.dpi": 300, "pdf.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    def save(fig, name):
        fig.savefig(target / f"{name}.png", dpi=300, bbox_inches="tight")
        fig.savefig(target / f"{name}.pdf", bbox_inches="tight")
        plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(7, 3.1), layout="constrained")
    ax[0].scatter(ARRAY[:, 0], ARRAY[:, 1], s=35)
    for i, p in enumerate(ARRAY):
        ax[0].annotate(str(i), p[:2], xytext=(5, 4), textcoords="offset points")
    ax[0].set(xlabel="x (m)", ylabel="y (m)", title="Illustrative planar array", aspect="equal")
    sample = np.load(ROOT / "data" / "synthetic" / cfg["mode"] / "representative_positive_sensor_noise.npz")
    x = sample["audio"][:, 0]
    f = np.fft.rfftfreq(N, 1 / FS)
    p = np.abs(np.fft.rfft(x * np.hanning(N))) ** 2
    ax[1].plot(f, 10 * np.log10(p / p.max() + 1e-12), linewidth=0.8)
    ax[1].set(xlim=(0, 3200), ylim=(-60, 3), xlabel="Frequency (Hz)", ylabel="Relative power (dB)", title="Synthetic mixture, -5 dB")
    save(fig, "array_and_spectrum")
    fig, ax = plt.subplots(1, 2, figsize=(7, 3.1), layout="constrained")
    det = summary["detection"]
    for key, label in [("tpr", "Detection recall"), ("balanced_accuracy", "Balanced accuracy")]:
        ax[0].plot(SNRS, [det["by_snr"][str(s)][key] for s in SNRS], "o-", label=label)
    ax[0].axhline(det["overall"]["fpr"], color="#777777", linestyle="--", label="Test false alarms")
    ax[0].set(xlabel="Mixture SNR (dB)", ylabel="Rate", ylim=(0, 1), xticks=SNRS)
    ax[0].legend(loc="best", fontsize=8)
    x = np.arange(4)
    ax[1].bar(x, [det["by_scene"][s]["fpr"] for s in SCENES], color="#D55E00")
    ax[1].axhline(0.05, linestyle="--", color="#777777")
    ax[1].set(xticks=x, xticklabels=["Sensor", "Wind", "Broadband", "Engine"], ylabel="False-alarm rate", title="Negative-scene breakdown")
    ax[1].tick_params(axis="x", rotation=20)
    save(fig, "detection")
    fig, ax = plt.subplots(figsize=(7, 3.5), layout="constrained")
    points = read_csv(out / "test_roc.csv")
    ax.plot(values(points, "fpr"), values(points, "tpr"), label=f"Test ROC; AUC={det['descriptive_test_auc']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="#999999", linewidth=1)
    ax.plot(det["overall"]["fpr"], det["overall"]["tpr"], "o", color="#D55E00", label="Frozen validation threshold")
    ax.set(xlabel="False-alarm rate", ylabel="Detection recall", xlim=(0, 1), ylim=(0, 1), title="Descriptive ROC; no test-threshold selection")
    ax.legend()
    save(fig, "detection_roc")
    fig, ax = plt.subplots(1, 2, figsize=(7, 3.2), layout="constrained")
    for method in METHODS:
        data = summary["localization"][method]["by_snr"]
        for axis, key in zip(ax, ["mean_deg", "p95_deg"]):
            axis.plot(SNRS, [data[str(s)][key] for s in SNRS], "o-", label=LABELS[method], color=COLORS[method], markersize=4)
            axis.set(xlabel="Mixture SNR (dB)", xticks=SNRS)
    ax[0].set(ylabel="Mean spherical error (deg)", title="All positive trials")
    ax[1].set(ylabel="95th percentile error (deg)", title="Tail errors retained")
    ax[0].legend(fontsize=9)
    save(fig, "localization")
    fig, ax = plt.subplots(figsize=(7, 3.3), layout="constrained")
    for offset, method in zip([-0.15, 0, 0.15], METHODS[1:]):
        data = [r for r in summary["paired_improvements"] if r["method"] == method and str(r["group"]).startswith("snr=")]
        y = np.array([r["baseline_minus_method_mean_deg"] for r in data])
        low, high = np.array([r["ci95_low"] for r in data]), np.array([r["ci95_high"] for r in data])
        ax.errorbar(np.arange(5) + offset, y, yerr=[np.maximum(0, y-low), np.maximum(0, high-y)], fmt="o", capsize=3, label=LABELS[method], color=COLORS[method])
    ax.axhline(0, color="#777777", linestyle="--")
    ax.set(xticks=np.arange(5), xticklabels=SNRS, xlabel="Mixture SNR (dB)", ylabel="PHAT minus method mean error (deg)", title="Paired 95% trial-bootstrap intervals")
    ax.legend(ncol=3)
    save(fig, "paired_improvements")
    fig, ax = plt.subplots(1, 2, figsize=(7, 3.4), layout="constrained")
    representative = [r for r in track if r["sequence_id"] == "seq-0-1-0" and r["method"] == "combined" and r["label"]]
    for mode, label in [("raw", "Raw"), ("smooth_all", "Causal smooth")]:
        selected = [r for r in representative if r["mode"] == mode]
        ax[0].plot([r["time_s"] for r in selected], [r["angular_error_deg"] for r in selected], label=label, linewidth=1)
    ax[0].set(xlabel="Time (s)", ylabel="Spherical error (deg)", title="Fixed example: sensor, -5 dB")
    ax[0].legend(fontsize=9)
    for offset, mode, label in [(-0.18, "raw", "Raw"), (0.18, "smooth_all", "Causal smooth")]:
        ax[1].bar(np.arange(4) + offset, [summary["tracking"][m][mode]["mean_deg"] for m in METHODS], width=0.35, label=label)
    ax[1].set(xticks=np.arange(4), xticklabels=["PHAT", "Coh.", "Harm.", "Comb."], ylabel="Sequence-mean error (deg)", title="Every independent sequence")
    ax[1].legend(fontsize=9)
    save(fig, "tracking")
    fig, ax = plt.subplots(figsize=(7, 3.4), layout="constrained")
    for i, method in enumerate(METHODS):
        data = [r for r in summary["sensitivity"] if r["method"] == method]
        ax.bar(np.arange(4) + (i - 1.5) * 0.19, [r["mean_deg"] for r in data], width=0.19, label=LABELS[method], color=COLORS[method])
    ax.set(xticks=np.arange(4), xticklabels=["Nominal", "Position 5 mm", "Delay 20 us", "Both"], ylabel="Mean spherical error (deg)", title="Paired sensor-uncertainty scenarios")
    ax.legend(ncol=4, fontsize=9)
    save(fig, "sensitivity")
    # Prespecified before the full run; never select an attractive map after seeing test errors.
    trial_id = "pos-2-2-0"
    sample = np.load(ROOT / "data" / "synthetic" / cfg["mode"] / "test" / f"{trial_id}.npz")
    engine = Engine()
    result = engine.analyze(sample["audio"], return_maps=True)
    meta = json.loads(str(sample["metadata_json"]))
    maps = np.array([result["methods"][m]["map"] for m in METHODS])
    np.savez_compressed(out / "acoustic_maps_fixed_trial.npz", trial_id=np.array(trial_id), methods=np.array(METHODS),
                        grid_az_deg=engine.az, grid_el_deg=engine.el, responses=maps,
                        true_az_deg=sample["az_deg"], true_el_deg=sample["el_deg"],
                        nuisance_az_deg=np.array(meta["nuisance_az_deg"]), nuisance_el_deg=np.array(meta["nuisance_el_deg"]))
    write_csv(out / "acoustic_map_peaks.csv", [{"trial_id": trial_id, "method": m,
              "peak_az_deg": result["methods"][m]["az_hat"], "peak_el_deg": result["methods"][m]["el_hat"],
              "peak_response": result["methods"][m]["peak"], "true_az_deg": float(sample["az_deg"][0]),
              "true_el_deg": float(sample["el_deg"][0])} for m in METHODS])
    fig, axes = plt.subplots(2, 2, figsize=(7, 5.4), layout="constrained", sharex=True, sharey=True)
    for ax, method, response in zip(axes.ravel(), METHODS, maps):
        im = ax.pcolormesh(np.arange(0, 360, 3), np.arange(0, 90, 3), response[:-1].reshape(30, 120),
                           shading="nearest", cmap="viridis", vmin=maps.min(), vmax=maps.max())
        ax.plot(float(sample["az_deg"][0]), float(sample["el_deg"][0]), "x", color="white", ms=8, mew=2)
        ax.plot(result["methods"][method]["az_hat"], result["methods"][method]["el_hat"], "o", color="#E69F00", mfc="none", ms=8)
        ax.plot(meta["nuisance_az_deg"], meta["nuisance_el_deg"], "^", color="#E69F00", ms=5)
        ax.set(title=LABELS[method], xlim=(0, 360), ylim=(0, 90), xticks=[0, 90, 180, 270, 360], yticks=[0, 30, 60, 90])
    axes[1, 0].set_xlabel("Azimuth (deg)")
    axes[1, 1].set_xlabel("Azimuth (deg)")
    axes[0, 0].set_ylabel("Elevation (deg)")
    axes[1, 0].set_ylabel("Elevation (deg)")
    fig.colorbar(im, ax=axes, label="Normalized SRP response", shrink=0.8)
    fig.suptitle("Fixed trial: x target, circle peak, triangle interferer", fontsize=11)
    save(fig, "acoustic_maps")


def methods_text(cfg, cal, env, summary):
    det = summary["detection"]["overall"]
    loc = summary["localization"]
    return rf"""# Exact method and results: simulation-only acoustic detection and direction estimation

This file is generated from executed CSV records. Run mode: **{cfg['mode']}**. Master seed: **{SEED}**. No organizer data, measured array, calibrated source levels, actual-flight localization labels, or target-device benchmark are used. The model's 20–80 m distance is solely a geometric curvature parameter: prescribed SNR is normalized independently of range. Neither 100 m detection nor a maximum effective range is established. No result from `data/public` is included here. This is an interpretable combination/ablation study, not a priority claim for SRP, PHAT, harmonic selection, coherence, or smoothing.

## Frozen experiment and independent units

{cfg['validation_negatives_per_scene'] * 4} validation negatives; {cfg['test_negatives_per_scene'] * 4} test negatives; {cfg['test_positives_per_scene_snr'] * 20} test positives. Positives are balanced across SNR = -15, -10, -5, 0, +5 dB and four nuisance scenes. Every static trial has fresh source, noise, direction, sound speed, source phases and gains. SNR cells do not recycle the same waveform. The four algorithms are paired on the same trial. {cfg['tracking_repeats_per_scene_snr'] * 12} independent continuous sequences last {cfg['tracking_seconds']} s each. Tracking is balanced across four scenes and nominal SNR -10, -5, 0 dB. There are {cfg['sensitivity_per_scene_snr'] * 12} new sensitivity trials, each evaluated under four paired conditions. Quick mode is an engineering smoke check and is not combined with full mode. Parameters were fixed before the full run; there is no test-driven parameter search.

SeedSequence entropy is `[20261002, split, scene_index, ...]`; exact per-trial lists are stored in NPZ metadata, CSV and `data/synthetic/{cfg['mode']}/manifest.jsonl`. Split codes are 1 validation negatives, 2 test negatives, 3 test positives, 4 sensitivity, 5 tracking, 6 bootstrap, 77 sensor perturbations, 90 self-test. Static positive suffixes are `[snr_index, trial_index]`; static negative suffixes are `[trial_index]`; tracking/sensitivity suffixes are `[snr_index, repeat_index]`. Scene families are shared between calibration and test but realized physical scenes are independent; this is not a held-out-environment or held-out-drone experiment.

## Coordinate and synthesis model

Azimuth increases counterclockwise from +x; elevation is above the array plane. $u(a,e)=(\cos e\cos a,\cos e\sin a,\sin e)$. Eight microphones use the exact coordinates in `config.json`; diameter is {cfg['diameter_m']:.6f} m. The array is planar, so an upper-hemisphere prior is essential; it cannot resolve the lower/upper mirror ambiguity. The search includes a single zenith point and full azimuth coverage. Zenith azimuth is intrinsically undefined; spherical error is the principal metric and raw wrapped azimuth errors are also disclosed. True static directions are uniform in azimuth and in sine elevation (uniform solid angle on the upper hemisphere).

A source waveform is synthesized at 24 kHz, then evaluated at fractional arrival times by linear interpolation to 8 kHz. For microphone $m$, $x_m(t)=g_m[d_m(t)+r_m(t)+n_m(t)]$ conceptually, with each contribution's normalization implemented explicitly in `simulate`. Direct source delay is $\tau_m(t)=(\|R(t)u(t)-p_m^{{actual}}\|-R(t))/c+\delta_m$. Propagation uses spherical distances and relative amplitude $R/\|Ru-p_m\|$. Actual sound speed is uniform 338–348 m/s; steering assumes 343 m/s. Per-channel gains are log-normal with Gaussian 0.6 dB standard deviation. Nominal geometry/delay perturbations are zero; sensitivity adds Gaussian xyz offsets (including z) and Gaussian fixed channel time offsets. Different generation and steering models reduce the most direct inverse crime, but do not establish real-world validity.

The multirotor-like signal sums four oscillators. A nominal base is uniform 85–230 Hz. Each rotor has a Gaussian relative offset SD 0.012 and sinusoidal frequency modulation of relative depth uniform 0.008–0.025, rate 0.6–2 Hz and random phase. Harmonic phases are independent; amplitudes are uniform(0.6,1.4)/$k^{{0.65}}$, for $k=1,\ldots,\min(15,\lfloor3200/(1.07f_0)\rfloor)$. Unit-RMS tonal and 120–3200 Hz third-order Butterworth-filtered Gaussian broadband parts have nominal tonal power fraction uniform 0.55–0.85 before their combination and final normalization. A sinusoidal amplitude envelope has depth 0.12 and frequency 0.3–1.5 Hz. This phenomenological model is not a validated aircraft sound-emission model.

A weak echo has RMS ratio uniform 0.05–0.25 relative to the direct target, delay 3–12 ms, azimuth offset 25–80 degrees and elevation max(5 degrees,0.65 times target elevation). It is a synthetic secondary path, not a physically ray-traced outdoor ground reflection. The target direct-path mean-square power across all microphones divided by total nuisance power defines SNR; the echo is excluded from the SNR numerator and nuisance denominator. Exact achieved per-frame SNR is saved. There is no source-level calibration, atmospheric absorption model, exact retarded-time solution, moving-source Doppler validation, or distance-to-SNR conversion.

Nuisance scenes: (1) independent unit Gaussian sensor noise; (2) 0.35 times sensor noise plus independent 180 Hz second-order low-pass noise per channel, plus 0.25 times a shared 90 Hz low-pass component, normalized before mixing; (3) 0.6 times sensor noise plus a directional 160–3200 Hz third-order band-pass noise source; (4) 0.6 times sensor noise plus a directional one-oscillator engine-like harmonic confounder. Engine base/offset distributions overlap the target; its modulation depth is 0.001–0.004 and harmonic fraction 0.82–0.95. Nuisance direction is uniform azimuth and elevation 0–65 degrees; range is uniform 10–60 m. No minimum target/interferer angular separation is imposed. The wind model is colored correlated noise, not measured atmospheric turbulence. Engine negatives are deliberately difficult: harmonicity and spatial coherence do not identify drone class.

## Spectral front end, estimated base and detector

Frames are disjoint 1600-sample (0.2 s) blocks at 8 kHz: output cadence 5 Hz. Each channel is demeaned over the frame. Five 512-point periodic-Hann segments, hop 256, start at samples 0,256,512,768,1024; the remaining 64 samples enter the full-frame harmonic estimator but not the Welch estimate. For pair $i<j$, $G_{{ij}}(f)=\frac15\sum_\ell X_{{i\ell}}(f)X_{{j\ell}}^*(f)$ and $P_i(f)=\frac15\sum_\ell|X_{{i\ell}}(f)|^2$. Define $\gamma_{{ij}}^2=\mathrm{{clip}}(|G_{{ij}}|^2/(P_iP_j+10^{{-20}}),0,1)$ and $Q_{{ij}}=G_{{ij}}/\max(|G_{{ij}}|,10^{{-20}})$. This is a finite-sample Welch magnitude-squared coherence estimate; overlap reduces effective sample count and no unbiased-coherence claim is made. It is not computed from a single snapshot, which would give trivial coherence.

An additional 2048-point real FFT of the entire periodic-Hann-windowed frame is used for harmonic evidence; zero-padding interpolates spectral samples but does not improve the physical 5 Hz window resolution. Average the eight channel powers into $P(f)$. Let $M(f)$ be a 31-bin local median, nearest-edge padding, and $L(f)=\log(1+P(f)/\max(M(f),10^{{-20}}))-\log2$. Smooth $L$ with a Gaussian of SD one FFT bin (SciPy default reflect edges). For $b\in\{{80,82,\ldots,240\}}$ Hz, evaluate $J(b)=\sum_{{k=1}}^{{12}}k^{{-1/2}}L(\operatorname{{round}}(kb\cdot2048/8000))/\sum_{{k=1}}^{{12}}k^{{-1/2}}$. The argument denotes a nearest FFT-bin index, not interpolation. $\hat f_0=\arg\max_b J(b)$; ties use the first candidate. There is no true-base input. Absolute percentage error against the generator's nominal base is a diagnostic only: median {summary['f0_diagnostic']['median_absolute_percentage_error']:.4f}% across all positive test trials. Four perturbed rotors do not possess one exact common instantaneous base.

Within the 200–3000 Hz band, $d(f)=|f-\operatorname{{round}}(f/\hat f_0)\hat f_0|$, $\sigma(f)=\max(8,0.012f)$ Hz, and $H(f)=0.1+0.9\exp[-d(f)^2/(2\sigma(f)^2)]$. $H=0$ outside the band. On the 512-point FFT grid the retained bins actually run from 203.125 to 3000 Hz. The floor retains broadband evidence. Detection score is $D=\max(0,J(\hat f_0))[0.25+\sum_{{i<j,f}}H(f)\gamma_{{ij}}^2(f)/(28\sum_fH(f))]$. One common detector is used for all four localizers: detection results must not be presented as four different trained detectors.

Only independent validation-negative scores set the threshold. Sort $n={cal['n']}$ scores, take order statistic $k=\lceil(n+1)(1-0.05)\rceil={cal['order_statistic_1_based']}$ (1-based), and declare detection iff $D>\theta$. The fitted threshold is **{cal['threshold']:.12g}**, validation empirical FPR **{cal['validation_fpr']:.6f}**. Equal-scene stratification targets this explicit nuisance mixture. The order-statistic rule is inspired by finite-sample calibration, but stratified non-identical draws mean no universal distribution-free or per-scene 5% guarantee is asserted. There is no positive-label fitting, test-threshold adjustment or double-threshold hysteresis. Engine-specific false alarms may exceed 5% even when aggregate FPR does not.

## Four paired localization ablations

Nominal predicted pair delay is $\tau_{{ij}}(u)=-(p_i-p_j)^Tu/343$. The common objective is

$$S_w(u)=\sum_{{i<j}}\sum_{{f\in B}} w_{{ij}}(f)\Re\{{Q_{{ij}}(f)e^{{j2\pi f\tau_{{ij}}(u)}}\}}.$$

Weights are PHAT: $w=1$; coherence: $w=C_{{ij}}=0.05+0.95\gamma_{{ij}}^2$; harmonic: $w=H$; combined: $w=C_{{ij}}H$. Frequency bins outside B are zero. Implementation takes a 4096-point inverse real FFT (8x interpolation), evaluates pair correlations with linear lag interpolation and sums all 28 pairs. The search is 3-degree azimuth 0–357 and elevation 0–87, plus one zenith, totaling 3601 directions. No local refinement or test-selected grid is used. Peak values are normalized by total weight; multiplying a method's whole map by a positive scalar does not affect argmax. Detector/f0 data are shared but scoring truth is not passed into `Engine.analyze(audio)`.

## Causal tracking and latency

Continuous sequences have a target absent during the first and last 2 s (20 ms boundary ramps); it is present in between. The same continuous waveform, nuisance, gains, geometry and sound speed are used throughout a sequence. Target azimuth starts uniform 0–360, moves with signed speed uniform 6–18 deg/s and reverses at half the sequence duration to -0.7 times the original speed. Elevation is $40+25\sin(2\pi t/T+\phi)$ degrees, range is $R_0+1.5\sin(2\pi t/T)$ m, and target level varies by $3\sin(2\pi t/T)$ dB. These are angular-maneuver stress trajectories, not validated low-speed flight kinematics: azimuth motion alone can imply approximately 25 m/s at the largest modeled radius and angular rate; elevation motion adds velocity and the abrupt turn has no acceleration constraint. The trajectory is evaluated at each frame center. Subframe motion therefore differs from the estimator's constant-within-frame steering assumption. Labels/trajectory never initialize or update a tracker.

For each localizer independently, raw estimates and two causal smoothers are saved. An accepted unit-vector observation $u_t$ gives $z_t=\mathrm{{normalize}}(0.65z_{{t-1}}+0.35u_t)$; the first accepted observation initializes state. `smooth_all` accepts every frame, including absence. `gated` accepts only detections; it holds the last state for at most 5 consecutive misses (1.0 s), invalidates on miss 6, and restarts on the next detection. `detected`, `valid`, `stale` and `consecutive_missed_detections` are stored separately. A held direction is not a new detection. Missing output is retained as unavailable, never discarded from coverage/success denominators. No future observation, centered smoothing, true direction, prelabelled target start or fitted trajectory is used.

This fixed smoother trades noise reduction for maneuver lag. The 1 s hold rule can violate the competition's 0.5 s interruption requirement and can retain false directions. Accordingly coverage, absent-period output rate, raw/smoothed mean error, per-sequence p95 error, error within one second of the turn, movement-step RMS and chord-velocity residual are all retained. Chord-velocity residual is $(180/\pi)\|(\hat u_t-\hat u_{{t-1}})-(u_t-u_{{t-1}})\|/0.2$; its sequence RMS is reported only on adjacent available positive frames and is not an exact spherical angular velocity. Detection continuity is scored separately from held-output continuity. The fraction of contiguous 25-positive-frame windows with detection recall at least 0.8 and no miss run over 0.5 s is an illustrative simulation check, not a range result. Overlapping windows are descriptive and never bootstrap units.

## Metrics and uncertainty

TPR = TP/Npositive, FPR = FP/Nnegative, balanced accuracy = (TPR + 1 - FPR)/2. For each SNR, the same complete negative test set is used; it is not resampled audio or an SNR-conditioned negative set. Spherical error is $\operatorname{{atan2}}(\|\hat u\times u\|,\hat u^Tu)$ in degrees. Signed azimuth error is $(\hat a-a+180)\bmod360-180$, elevation error is $\hat e-e$. Report mean/median/RMSE/p90/p95, absolute coordinate errors, unconditional fraction within 10 degrees, detected-only error and denominator, and joint (detected AND error at most 10 degrees)/all positives. Conditional localization errors must not be used as unconditional success rates. These are explicitly defined research metrics, not the organizer's unspecified official combined-angle score.

For static data, 2000 bootstrap replicates independently sample whole trials with replacement within scene x SNR strata (within scene for negatives), preserving the designed mix. A method difference is paired before resampling: PHAT error minus alternative error. Positive paired values mean improvement. Detection-rate intervals use Wilson binomial intervals; balanced-accuracy intervals independently resample positive and negative strata. Intervals are descriptive Monte Carlo uncertainty under this generator, not uncertainty over all real drone/environment populations; there is no multiplicity correction. Sensitivity paired increases use condition error minus nominal error, so positive is worse. All sensitivity changes reuse exactly the same source and noise random draws; only a separate standard-normal sensor perturbation stream is scaled.

Tracking summary values are equal-weight means of per-sequence metrics, with 2000 whole-sequence bootstrap samples for means and paired raw-minus-smoothed errors. Frames, STFT windows and overlapping detection windows are never bootstrap units. Fewer than two independent units provide no informative bootstrap interval: `bootstrap_mean` returns `[None, None]` (JSON `[null, null]`), including a one-sequence quick gated subset. Gated conditional-error averages use only sequences with available output; their counts and coverage are explicitly reported, and no favorable comparison is inferred from dropping unavailable sequences. In this run the combined gate produces any positive-period output in only {summary['tracking']['combined']['gated']['sequences_with_output']} of {summary['tracking']['combined']['gated']['sequences']} sequences. Any available conditional bootstrap interval is weak evidence about this selected subset and is not generalized to missed sequences or real flight populations. The `p95_deg` tracking aggregate is the mean of within-sequence p95s, not a pooled p95. First-detection latency is measured at the end of the first positive detected frame relative to target onset; sequences never detected are counted and omitted only from the conditional latency average.

## Observed primary outcomes and limits

Test recall is **{det['tpr']:.6f}**, false-alarm rate **{det['fpr']:.6f}**, and balanced accuracy **{det['balanced_accuracy']:.6f}**. Descriptive test ROC AUC is **{summary['detection']['descriptive_test_auc']:.6f}** (no AUC CI is claimed); equal-score groups enter the curve together and trapezoidal integration handles ties. ROC thresholds use inclusive score comparisons, and the independently frozen strict-threshold operating point is separately marked. The ROC is descriptive only and selects no deployment threshold. Unconditional mean spherical errors are PHAT **{loc['phat']['overall']['mean_deg']:.4f} deg**, coherence **{loc['coherence']['overall']['mean_deg']:.4f} deg**, harmonic **{loc['harmonic']['overall']['mean_deg']:.4f} deg**, combined **{loc['combined']['overall']['mean_deg']:.4f} deg**. These are measured program outputs, not expected/theoretical or fabricated values. The tables below disclose all SNR/scene cells, tails, conditional failures and independent-sequence results. A combination must not be described as superior when its paired intervals/point estimates do not support that statement. Harmonic confounders, coherent distractors and planar-array elevation conditioning are structural limitations of this simple method, not test exclusions.

Host: **{env['cpu']}**, {env['platform']}. Python {env['python'].split()[0]}, one thread requested through OpenBLAS/OMP/MKL/NumExpr environment variables and SciPy FFT workers=1. Timings use `perf_counter_ns` over a shared front end (including the detector and estimated base) plus one method's search. Geometry construction ({env['setup_seconds_excluded']:.6f} s), warm-up, signal generation, disk I/O, plotting and the 200 ms acquisition window are excluded. Per-method timings share the same front end; their sum double counts it. Compute throughput is not acquisition/output cadence, nor end-to-end device performance. Window plus p95 is the nominal 200 ms frame fill plus measured p95 compute, excluding hardware/buffering/transport/display. Workstation background load and process scheduling were not isolated. The benchmark does not certify the organizer's target hardware.

## Artifacts and reproduction

- `code/experiment.py --self-test`: runnable assertions for wrap/zenith/antipodal metrics, calibration rank, known-direction localization, deterministic synthesis, exact SNR, steering sign, causal wrap and bounded hold. Actual self-test record: `results/self_test.json`.
- `code/experiment.py --quick` and `--full`: full pipeline with separate outputs. Completed runs are protected from silent overwrite. Move their output folders intentionally to rerun.
- `code/summarize_experiment.py results/full`: rebuild reports/tables/figures from saved CSV without rerunning acoustics.
- `code/requirements-lock.txt`: exact installed Python 3.12 package versions. Dependencies used locally are in `.python-packages`; the script inserts that directory only under Python 3.12 to avoid loading incompatible NumPy wheels into 3.10.
- All static validation/test/sensitivity audio, not just examples, is float32 in `data/synthetic/{cfg['mode']}/validation`, `test`, `sensitivity`; filenames are trial IDs, sample-major shape (1600,8), unscaled mixtures. Seed tuples, actual geometry/delays, sample rate, frame truth and nominal array are embedded. Continuous tracking recordings are saved under `sequences`; a representative sequence and each static nuisance/label example additionally have 8-channel PCM16 WAV copies and scale sidecars.
- `test_frames.csv`, `sensitivity_frames.csv`, `tracking_frames.csv` contain raw per-frame/per-method outputs; repeated static method rows are paired observations, not independent trials. `validation_negatives.csv` contains every calibration score. `manifest.jsonl`, `config.json`, `runtime_environment.json`, `summary.json`, `source_manifest.json` and SHA256 `artifact_manifest.json` support inspection and reconstruction. The latter hashes all experiment scripts, lock/readme, full result files, all synthetic recordings and generated figures (excluding its own self-reference). `verify_experiment.py` verifies the executed source hash, every listed artifact, exact counts, preserved gate/miss semantics and eight prespecified bit-exact waveform/estimator reconstructions. The saved `quick` folder is a prior engineering checkpoint with its own earlier source hash, not the final scientific run; its conditional intervals are not publication evidence.
- Figure pairs (7-inch source width, 300 dpi PNG, vector PDF): `array_and_spectrum`, `detection`, `detection_roc`, `localization`, `paired_improvements`, `tracking`, `sensitivity`, `acoustic_maps` under `figures/{cfg['mode']}`. The example sequence is fixed by ID before evaluating results, not chosen for successful tracking. Acoustic maps use preselected test trial `pos-2-2-0` (directional broadband nuisance, -5 dB, replicate 0); all 3601 grid responses, including the single zenith, are in `acoustic_maps_fixed_trial.npz`, with peak azimuth/elevation in `acoustic_map_peaks.csv`. The map image shows the rectangular 0–87-degree elevation grid; a possible zenith peak is marked at 90 degrees. White x marks the target, orange circle the estimate and orange triangle the nuisance direction.

## Prior-method attribution for the manuscript author

The supplied Chen, Chen and Wang (2022) review, DOI 10.12141/j.issn.1000-565X.220277, establishes the broader TDOA/GCC, harmonic UAV acoustics and array background. The present equations are a particular reproducible implementation, not a reproduction of every published variant. Conventional SRP sums generalized pair correlations at geometric delays; see the primary article [Source Localization with Acoustic Sensor Arrays Using Generative Model Based Fitting with Sparse Constraints](https://pmc.ncbi.nlm.nih.gov/articles/PMC3545592/). The Welch coherence definition is documented by [SciPy 1.15.3](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.coherence.html), citing Welch (1967). The manuscript should use its independently verified primary references for SRP-PHAT and drone harmonic localization; a new implementation is not evidence of methodological priority.
"""


if __name__ == "__main__":
    summarize(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "results" / "full")
