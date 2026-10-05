"""Read-only audit of completed fresh outputs; never fit, infer, synthesize, or rewrite them.

Run with Python 3.12: python -B code/verify_improved.py
Only results/improved_verification.json is written.
"""
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys

from experiment import ROOT, N, FS
import evaluate_improved as evaluation
from summarize_experiment import read_csv
import numpy as np

OUT = ROOT / 'results/improved'
DATA = ROOT / 'data/synthetic/improved'
REPORT = ROOT / 'results/improved_verification.json'
DETECTORS = ('harmonic_coherence', 'spectral', 'proposed')
METHODS = ('phat', 'coherence', 'harmonic', 'combined', 'no_null', 'proposed')
checks = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def same(actual, expected, context='value'):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), context
        for key in expected:
            same(actual[key], expected[key], f'{context}.{key}')
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected), context
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, f'{context}[{i}]')
    elif isinstance(expected, (int, float, np.number)):
        assert np.isclose(actual, expected, rtol=1e-10, atol=1e-10), context
    else:
        assert actual == expected, context


def unique(rows, fields):
    keyed = {tuple(r[k] for k in fields): r for r in rows}
    assert len(keyed) == len(rows), f'duplicate keys: {fields}'
    return keyed


def verify():
    if not __debug__:
        raise RuntimeError('Do not disable assertions with python -O')
    for name in ('run_complete.json', 'summary.json', 'artifact_manifest.json'):
        assert (OUT / name).is_file(), f'Run not complete: {name}'
    cfg, summary, threshold = read('frozen_config.json'), read('summary.json'), read('thresholds.json')
    frozen = {**cfg['source_sha256'], **cfg['model_sha256']}
    for relative, expected in frozen.items():
        assert digest(ROOT / relative) == expected, f'frozen input changed: {relative}'
    inventory = read('artifact_manifest.json')
    listed = {item['path'] for item in inventory}
    assert len(listed) == len(inventory), 'duplicate manifest paths'
    actual = {p.relative_to(ROOT).as_posix() for folder in (OUT, DATA)
              for p in folder.rglob('*') if p.is_file() and p.name != 'artifact_manifest.json'}
    assert listed == actual, 'manifest does not cover current fresh files exactly'
    for item in inventory:
        path = (ROOT / item['path']).resolve()
        assert path.is_relative_to(ROOT.resolve()), item['path']
        assert digest(path) == item['sha256'], f'artifact changed: {item["path"]}'
    checks.append({'check': 'frozen_inputs_and_complete_artifact_manifest', 'frozen_n': len(frozen), 'artifact_n': len(inventory)})

    cal = read_csv(OUT / 'calibration.csv')
    det = read_csv(OUT / 'detection_frames.csv')
    loc = read_csv(OUT / 'localization_frames.csv')
    timing = read_csv(OUT / 'timing_frames.csv')
    seq_d = read_csv(OUT / 'sequence_detection.csv')
    seq_l = read_csv(OUT / 'sequence_localization.csv')
    assert len(cal) == 800 and len(det) == 9000 and len(loc) == 6000 and len(timing) == 3000
    assert len(seq_d) == 8640 and len(seq_l) == 14400
    unique(cal, ('trial_id',))
    dm, lm = unique(det, ('trial_id', 'detector')), unique(loc, ('trial_id', 'method'))
    tm = unique(timing, ('trial_id',))
    sdm = unique(seq_d, ('trial_id', 'frame', 'detector'))
    unique(seq_l, ('trial_id', 'frame', 'method'))
    assert Counter(r['scene'] for r in cal) == Counter({g: 100 for g in cfg['negative_groups']})
    assert threshold['n'] == 800 and threshold['order'] == 761 and cfg['strict_threshold']
    for name in DETECTORS:
        t = sorted(r[name] for r in cal)[760]
        assert threshold['thresholds'][name] == t, name
        same(threshold['validation_fpr'][name], np.mean([r[name] > t for r in cal]))
    for row in det + seq_d:
        assert row['detected'] == int(row['score'] > threshold['thresholds'][row['detector']])
    checks.append({'check': 'rank_761_strict_threshold_all_rows', 'calibration_n': 800})

    reference = [r for r in det if r['detector'] == 'harmonic_coherence']
    positive = {r['trial_id'] for r in reference if r['label'] == 1}
    negative = {r['trial_id'] for r in reference if r['label'] == 0}
    assert len(positive) == 1000 and len(negative) == 2000 and positive.isdisjoint(negative)
    assert {key[0] for key in tm} == positive | negative
    expected_cells = Counter({(s, snr): 50 for s in cfg['positive_scenes'] for snr in cfg['snr_db']})
    assert Counter((r['scene'], r['snr_db']) for r in reference if r['label']) == expected_cells
    assert Counter(r['scene'] for r in reference if not r['label']) == Counter({g: 250 for g in cfg['negative_groups']})
    assert set(dm) == {(trial, name) for trial in positive | negative for name in DETECTORS}
    assert set(lm) == {(trial, name) for trial in positive for name in METHODS}
    for row in reference:
        for name in DETECTORS:
            other = dm[row['trial_id'], name]
            assert all(row[k] == other[k] for k in ('scene', 'snr_db', 'label', 'split', 'frame'))
    sequence_ids = {r['trial_id'] for r in seq_d}
    assert len(sequence_ids) == 24
    assert set(sdm) == {(s, f, d) for s in sequence_ids for f in range(120) for d in DETECTORS}
    for seq in sequence_ids:
        for name in DETECTORS:
            assert sum(sdm[seq, f, name]['label'] for f in range(120)) == 100
    checks.append({'check': 'exact_counts_cells_pairing', 'static_trials': 3000, 'positive_trials': 1000, 'sequences': 24})

    # Inspect saved labels/metadata, not model inference or fresh synthesis.
    seeds, component_hashes = [], []
    truths = {}
    folders = {'calibration': 800, 'test': 3000, 'sequences': 24}
    for folder, count in folders.items():
        files = sorted((DATA / folder).glob('*.npz'))
        assert len(files) == count, folder
        for path in files:
            with np.load(path) as saved:
                assert int(saved['sample_rate']) == FS
                meta = json.loads(str(saved['metadata_json']))
                label, az, el = saved['label'], saved['az_deg'], saved['el_deg']
                expected_length = 120 if folder == 'sequences' else 1
                assert label.shape == az.shape == el.shape == (expected_length,)
                assert np.isin(label, (0, 1)).all()
                if folder != 'calibration':
                    for frame in range(expected_length):
                        truths[folder, path.stem, frame] = (int(label[frame]), float(az[frame]), float(el[frame]))
                else:
                    assert label[0] == 0
                parts = meta.get('component_seed_parts', [meta['seed_parts']])
                expected_split = 1101 if folder == 'calibration' else 1105 if folder == 'sequences' else 1103 if label[0] else 1102
                assert all(part[0] == expected_split for part in parts)
                seeds.extend(tuple(part) for part in parts)
                if 'component_seed_parts' in meta:
                    assert len(parts) == len(meta['components']) == len(meta['weights']) == len(meta['component_audio_sha256'])
                    assert all(part == child['seed_parts'] for part, child in zip(parts, meta['components']))
                    assert meta['component_hash_encoding'] == 'float32, C-order, sample-major (1600,8)'
                    assert label[0] == 0 and not meta['target_present']
                    component_hashes.extend(meta['component_audio_sha256'])
    assert len(seeds) == len(set(seeds)) == 5574
    assert len(component_hashes) == len(set(component_hashes)) == 3150
    for row in det + seq_d:
        key = ('test', row['trial_id'], 0) if row['split'] == 'test' else ('sequences', row['trial_id'], int(row['frame']))
        assert row['label'] == truths[key][0]
    checks.append({'check': 'saved_truth_seed_independence_component_provenance', 'unique_seeds': len(seeds),
                   'component_hashes': len(component_hashes), 'note': 'Component hashes checked for structure/uniqueness; components not regenerated.'})

    for row in loc + seq_l:
        seq = row['split'] == 'sequence'
        key = ('sequences', row['trial_id'], int(row['frame'])) if seq else ('test', row['trial_id'], 0)
        label, az, el = truths[key]
        assert label == 1 and row['true_az'] == az and row['true_el'] == el
        # Independent spherical distance through haversine, with wrapped coordinates.
        da = (row['az_hat'] - az + 180) % 360 - 180
        de = row['el_hat'] - el
        h = np.sin(np.deg2rad(de) / 2)**2 + np.cos(np.deg2rad(el)) * np.cos(np.deg2rad(row['el_hat'])) * np.sin(np.deg2rad(da) / 2)**2
        angle = np.rad2deg(2 * np.arctan2(np.sqrt(np.clip(h, 0, 1)), np.sqrt(np.clip(1-h, 0, 1))))
        assert np.isclose(angle, row['angular_error_deg'], atol=1e-7)
        same(row['az_error_deg'], da)
        same(row['el_error_deg'], de)
        for name, field in [('proposed', 'detected'), ('spectral', 'spectral_detected'), ('harmonic_coherence', 'original_detected')]:
            d = sdm[row['trial_id'], row['frame'], name] if seq else dm[row['trial_id'], name]
            assert row[field] == d['detected']
    for row in timing:
        same(row['proposed_pipeline_upper_bound_ms'], row['shared_full_and_spectral_detector_ms'] + row['localizer_ms'])
        assert all(np.isfinite(row[k]) and row[k] >= 0 for k in row if k.endswith('_ms'))
    checks.append({'check': 'all_angles_labels_detector_flags_and_timing_algebra'})

    # Recompute every frozen summary field without allowing any writes into OUT.
    captured = {}
    original_writer = evaluation.write_json
    def capture(path, value):
        captured[path.name] = value
    try:
        evaluation.write_json = capture
        with redirect_stdout(io.StringIO()):
            evaluation.summarize()
    finally:
        evaluation.write_json = original_writer
    same(summary, captured['summary.json'], 'summary')
    for name in DETECTORS:
        rows = [r for r in det if r['detector'] == name]
        pos, neg = [r for r in rows if r['label']], [r for r in rows if not r['label']]
        tpr, fpr = sum(r['detected'] for r in pos) / 1000, sum(r['detected'] for r in neg) / 2000
        same(summary['detection'][name]['tpr'], tpr)
        same(summary['detection'][name]['fpr'], fpr)
        same(summary['detection'][name]['balanced_accuracy'], (tpr + 1 - fpr) / 2)
    checks.append({'check': 'all_summary_fields_read_only_recomputed_and_primary_rates_independently_counted'})
    for relative, expected in frozen.items():
        assert digest(ROOT / relative) == expected, f'frozen input changed during verification: {relative}'
    return {'summary_sha256': digest(OUT / 'summary.json'), 'frozen_config_sha256': digest(OUT / 'frozen_config.json'),
            'actual_results': summary,
            'interpretation_boundaries': ['Simulation distribution only; no range or field claim.',
                'Sequence outputs are raw detection/localization, not a new tracker.',
                'Runtime is a host compute upper bound including both detector predictions; acquisition excluded.',
                'Confidence intervals condition on the frozen model and calibration threshold.',
                'Multiple-source negative stress tests do not establish positive-target localization among multiple interferers.']}


if __name__ == '__main__':
    result = {'verified_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'verifier_sha256': digest(Path(__file__)), 'no_model_execution_or_new_data': True}
    try:
        result.update(verify())
        result['passed'] = True
    except Exception as error:
        result.update(passed=False, error=f'{type(error).__name__}: {error}')
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'report': str(REPORT), 'error': result.get('error')}, ensure_ascii=False))
    sys.exit(0 if result['passed'] else 1)
