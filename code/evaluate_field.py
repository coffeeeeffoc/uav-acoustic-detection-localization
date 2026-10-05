"""Frozen evaluation at points 2 and 3; never tunes models on held-out recordings."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
from field_data import *
from field_algorithm import *
from field_ranker import CoherenceRanker
from summarize_field import summarize
import argparse,csv,time,platform,datetime

BASELINES=['phat','scot','coherence','reference']
METHOD_NAMES=BASELINES+['ranker','no_hard_negatives']
FROZEN_FILES=['code/field_data.py','code/field_algorithm.py','code/field_ranker.py',
              'code/develop_field_discriminative.py','code/finalize_field_model.py',
              'code/evaluate_field.py','code/summarize_field.py',
              'research/real_data/protocol.md','results/field/source_manifest.json',
              'results/field/inventory.json','results/field/discriminative_features.npz',
              'results/field/discriminative_selection.json','results/field/no_hard_negatives_selection.json',
              'results/field/pre_freeze_verification.json',
              'results/field/discriminative_model.npz','results/field/no_hard_negatives_model.npz']

def freeze():
    path=OUT/'frozen_config.json'
    if path.exists(): raise RuntimeError('Existing freeze is immutable; use a new version for a changed study.')
    import scipy
    config=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        files={p:sha(ROOT/p) for p in FROZEN_FILES},development_site=1,test_sites=[2,3],
        noise_interval_s=[0,5],calibration_interval_s=[5,10],negative_test_interval_s=[10,30],
        positive_test_interval_s=[0,30],block_s=.2,calibration_n=25,alpha=.05,rank=25,
        detection_rule='score > max(calibration scores)',methods=METHOD_NAMES,
        proposed='Direction-conditioned coherence ranking, four PHAT proposals and 24 frequency bands',
        python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        platform=platform.platform(),processor=platform.processor(),threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']})
    path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('Frozen',sha(path),flush=True)

def check_freeze():
    f=json.loads((OUT/'frozen_config.json').read_text(encoding='utf-8'))
    for p,h in f['files'].items():assert sha(ROOT/p)==h,p
    return f

def run():
    config=check_freeze()
    if (OUT/'predictions.csv').exists() or (OUT/'progress.jsonl').exists():
        raise RuntimeError('Refusing to overwrite an evaluation. Existing evidence must be retained.')
    recs=[r for r in recordings() if r['site'] in config['test_sites']]
    e=ArrayProcessor(geometry(ROOT/recs[0]['path']))
    model=dict(np.load(OUT/'discriminative_model.npz'))
    ablation=dict(np.load(OUT/'no_hard_negatives_model.npz'))
    for m in [model,ablation]:assert str(m['source_sha256'])==sha(ROOT/'code/field_algorithm.py')
    ranker=CoherenceRanker(e,model)
    rows=[];candidates=[];thresholds={}
    progress=(OUT/'progress.jsonl').open('w',encoding='utf-8')
    def process(rec,start,split,noise):
        audio=load_block(rec,start,.2)
        tic=time.perf_counter();p,c,L=e.spectra(audio);front_ms=(time.perf_counter()-tic)*1000
        tic=time.perf_counter();q=e.weights(p,c,L,noise);weight_ms=(time.perf_counter()-tic)*1000
        estimates={}
        for name in BASELINES:
            tic=time.perf_counter();u,s,_=e.localize(q[name]);cost=(time.perf_counter()-tic)*1000
            estimates[name]=(u,s,front_ms+weight_ms+cost)
        tic=time.perf_counter();u,s,details=ranker.analyze_spectra(p,c);rank_ms=(time.perf_counter()-tic)*1000
        estimates['ranker']=(u,s,front_ms+rank_ms)
        tic=time.perf_counter();m=ablation
        other=(details['features']-m['center'])/m['scale']@m['coef']+m['intercept']
        k=int(np.argmax(other));other_ms=(time.perf_counter()-tic)*1000
        estimates['no_hard_negatives']=(details['units'][k],float(other[k]),front_ms+rank_ms+other_ms)
        # Reference labels enter ONLY the following reporting block.
        truth=directions(rec['reference_az_deg'],rec['reference_el_deg']) if rec['positive'] else None
        for name,(unit,score,cost) in estimates.items():
            az,el=angles(unit)
            row=dict(id=rec['id'],site=rec['site'],positive=int(rec['positive']),start_s=round(start,3),
                     split=split,method=name,score=score,az_deg=az,el_deg=el,
                     ux=float(unit[0]),uy=float(unit[1]),uz=float(unit[2]),
                     error_deg=float(angular_error(unit,truth)) if truth is not None else '',
                     compute_ms=cost,front_ms=front_ms,detected='',threshold='')
            rows.append(row)
            progress.write(json.dumps(row)+'\n')
        for j,(unit,score) in enumerate(zip(details['units'],details['scores'])):
            candidates.append(dict(id=rec['id'],start_s=round(start,3),split=split,index=j,
                ux=float(unit[0]),uy=float(unit[1]),uz=float(unit[2]),score=float(score),
                score_no_hard_negatives=float(other[j]),selected=int(j==details['index']),
                error_deg=float(angular_error(unit,truth)) if truth is not None else ''))
        progress.flush()

    for site in config['test_sites']:
        bg=next(r for r in recs if r['site']==site and not r['positive'])
        ps=[];cs=[]
        for k in range(25):
            p,c,_=e.spectra(load_block(bg,k*.2,.2));ps.append(p);cs.append(c)
        noise=np.mean(ps,axis=0),np.mean(cs,axis=0)
        np.savez_compressed(OUT/f'noise_s{site}.npz',p=noise[0],c=noise[1])
        for k in range(25):process(bg,5+k*.2,'calibration',noise)
        thresholds[site]={m:max(r['score'] for r in rows if r['site']==site and r['split']=='calibration' and r['method']==m) for m in METHOD_NAMES}
        print('calibrated site',site,flush=True)
        for rec in [r for r in recs if r['site']==site]:
            starts=[k*.2 for k in range(150)] if rec['positive'] else [10+k*.2 for k in range(100)]
            for k,start in enumerate(starts):
                process(rec,start,'test',noise)
                if k%25==0:print(rec['id'],round(start,2),flush=True)
    progress.close()
    for r in rows:
        t=thresholds[r['site']][r['method']];r['threshold']=t;r['detected']=int(r['score']>t)
    def write_csv(path,items):
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    write_csv(OUT/'predictions.csv',rows)
    write_csv(OUT/'candidates.csv',candidates)
    (OUT/'thresholds.json').write_text(json.dumps(thresholds,indent=2),encoding='utf-8')
    result=summarize(rows,candidates)
    (OUT/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    check_freeze()
    names=['predictions.csv','candidates.csv','thresholds.json','summary.json','noise_s2.npz','noise_s3.npz','progress.jsonl']
    (OUT/'artifact_manifest.json').write_text(json.dumps({n:sha(OUT/n) for n in names},indent=2),encoding='utf-8')
    print(json.dumps({m:{k:v for k,v in a.items() if k!='recordings'} for m,a in result['methods'].items()},indent=2),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');a.add_argument('--run',action='store_true');args=a.parse_args()
    if args.freeze:freeze()
    if args.run:run()
