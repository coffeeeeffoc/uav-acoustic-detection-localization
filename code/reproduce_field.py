"""Replay the frozen field study in a new output directory, preserving original evidence.

Example: python code/reproduce_field.py --out results/field_reproduction
Add --retrain to rebuild point-1 features and both models before the replay.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
from field_data import *
import argparse,shutil

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--retrain',action='store_true')
    args=parser.parse_args()
    destination=(ROOT/args.out).resolve()
    if not destination.is_relative_to(ROOT) or destination.exists():
        raise ValueError('Output must be a new directory inside the project; existing evidence is never overwritten.')
    import evaluate_field as evaluation
    frozen=evaluation.check_freeze()
    destination.mkdir(parents=True)
    for p in frozen['files']:
        path=Path(p)
        if path.parent.as_posix()=='results/field':shutil.copy2(ROOT/path,destination/path.name)
    shutil.copy2(OUT/'frozen_config.json',destination/'frozen_config.json')
    if args.retrain:
        import develop_field_discriminative as development
        import finalize_field_model as ablation
        development.OUT=destination;ablation.OUT=destination
        development.build();development.train();ablation.main()
        for name in ['discriminative_model.npz','no_hard_negatives_model.npz']:
            original=np.load(OUT/name);new=np.load(destination/name)
            for key in ['coef','center','scale','intercept','alpha']:
                if not np.allclose(original[key],new[key],rtol=1e-9,atol=1e-10):
                    raise AssertionError('Retrained numerical parameters differ: '+name+':'+key)
    evaluation.OUT=destination
    evaluation.run()
    # Timing is machine/load dependent. Check all accuracy, operating-point and paired statistics.
    expected=json.loads((OUT/'summary.json').read_text())
    actual=json.loads((destination/'summary.json').read_text())
    for summary in [expected,actual]:
        for v in summary['methods'].values():
            v.pop('compute_ms_median');v.pop('compute_ms_p95')
    from verify_field import compare
    compare(expected,actual)
    (destination/'reproduction_check.json').write_text(json.dumps(dict(status='PASS',
        retrained=args.retrain,nontiming_summary_matches=True,original_freeze_sha256=sha(OUT/'frozen_config.json')),indent=2),encoding='utf-8')
    print('Reproduction matches all nontiming summary fields:',destination)

if __name__=='__main__':main()
