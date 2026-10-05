"""Read-only consistency verification; does not run estimators or generate audio."""
from pathlib import Path
import sys,json,csv,math,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.python-packages'))
import numpy as np
from summarize_field import summarize
OUT=ROOT/'results/field'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def compare(a,b,path='summary'):
    if isinstance(a,dict):
        assert set(a)==set(b),path
        for k in a:compare(a[k],b[k],path+'.'+k)
    elif isinstance(a,(float,int)):
        assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),(path,a,b)
    else:assert a==b,(path,a,b)

def main(full_source=False):
    frozen=json.loads((OUT/'frozen_config.json').read_text())
    for p,h in frozen['files'].items():assert digest(ROOT/p)==h,p
    artifacts=json.loads((OUT/'artifact_manifest.json').read_text())
    for p,h in artifacts.items():assert digest(OUT/p)==h,p
    manifest=json.loads((OUT/'source_manifest.json').read_text(encoding='utf-8'))
    for r in manifest:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'],str(p)
        if full_source:assert digest(p)==r['sha256'],str(p)
    rows=list(csv.DictReader((OUT/'predictions.csv').open(encoding='utf-8')))
    candidates=list(csv.DictReader((OUT/'candidates.csv').open(encoding='utf-8')))
    assert len(rows)==5100 and len(candidates)==3400
    unique={(r['id'],r['start_s'],r['method']) for r in rows};assert len(unique)==len(rows)
    inventory=json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))['recordings']
    refs={r['id']:(r['reference_az_deg'],r['reference_el_deg']) for r in inventory if r['positive']}
    pred={(r['id'],r['start_s'],r['method']):r for r in rows}
    for r in rows:
        assert int(r['site']) in [2,3]
        unit=np.array([float(r[k]) for k in ['ux','uy','uz']]);assert abs(np.linalg.norm(unit)-1)<1e-9
        assert unit[2]>=-1e-12
        el=math.degrees(math.asin(np.clip(unit[2],-1,1)));az=math.degrees(math.atan2(-unit[0],-unit[1]))%360
        assert abs(el-float(r['el_deg']))<1e-8
        assert abs((az-float(r['az_deg'])+180)%360-180)<1e-8
        assert int(r['detected'])==int(float(r['score'])>float(r['threshold']))
        assert math.isfinite(float(r['score'])) and float(r['compute_ms'])>=float(r['front_ms'])>=0
        if int(r['positive']):
            a,e=map(math.radians,refs[r['id']]);truth=np.array([-math.cos(e)*math.sin(a),-math.cos(e)*math.cos(a),math.sin(e)])
            err=math.degrees(math.acos(np.clip(unit@truth,-1,1)))
            assert abs(err-float(r['error_deg']))<1e-7
            assert r['split']=='test'
        else:assert r['error_deg']==''
    for m in frozen['methods']:
        rr=[r for r in rows if r['method']==m]
        assert sum(int(r['positive']) for r in rr)==600
        assert sum(r['split']=='calibration' for r in rr)==50
        assert sum(not int(r['positive']) and r['split']=='test' for r in rr)==200
        for site in [2,3]:
            cal=[r for r in rr if int(r['site'])==site and r['split']=='calibration']
            assert len(cal)==25
            assert {float(r['start_s']) for r in cal}=={round(5+k*.2,3) for k in range(25)}
            threshold=max(float(r['score']) for r in cal)
            assert all(float(r['threshold'])==threshold for r in rr if int(r['site'])==site)
            assert all(int(r['detected'])==0 for r in cal)
        for rid in sorted({r['id'] for r in rr}):
            block=[r for r in rr if r['id']==rid and r['split']=='test']
            expected={round(k*.2,3) for k in range(150)} if int(block[0]['positive']) else {round(10+k*.2,3) for k in range(100)}
            assert {float(r['start_s']) for r in block}==expected
    groups={}
    for r in candidates:groups.setdefault((r['id'],r['start_s']),[]).append(r)
    for key,rr in groups.items():
        rr=sorted(rr,key=lambda r:int(r['index']));assert [int(r['index']) for r in rr]==[0,1,2,3]
        for method,column in [('ranker','score'),('no_hard_negatives','score_no_hard_negatives')]:
            k=int(np.argmax([float(r[column]) for r in rr]));p=pred[(*key,method)]
            assert float(p['score'])==float(rr[k][column])
            for coord in ['ux','uy','uz']:assert float(p[coord])==float(rr[k][coord])
            assert p['error_deg']==rr[k]['error_deg']
        assert sum(int(r['selected']) for r in rr)==1
        assert int(rr[np.argmax([float(r['score']) for r in rr])]['selected'])==1
    saved=json.loads((OUT/'summary.json').read_text())
    compare(saved,summarize(rows,candidates))
    # Independently aggregate central metrics without the summarizer's implementation.
    independent={}
    for m in frozen['methods']:
        pos=[r for r in rows if r['method']==m and int(r['positive'])]
        neg=[r for r in rows if r['method']==m and not int(r['positive']) and r['split']=='test']
        a=dict(mean_deg=sum(float(r['error_deg']) for r in pos)/600,
               tpr=sum(int(r['detected']) for r in pos)/600,fpr=sum(int(r['detected']) for r in neg)/200,
               joint10=sum(int(r['detected']) and float(r['error_deg'])<=10 for r in pos)/600)
        for k,v in a.items():assert math.isclose(saved['methods'][m][k],v,abs_tol=1e-10)
        independent[m]=a
    z=np.load(OUT/'discriminative_features.npz');assert all(str(x).startswith('s1_') for x in z['block_id'])
    assert z['X'].shape==(1779,24) and np.isfinite(z['X']).all()
    for f in [0,1]:
        ids=set(z['block_id'][z['fold']==f]);other=set(z['block_id'][z['fold']!=f]);assert not ids&other
    report=dict(status='PASS',frozen_files=len(frozen['files']),artifact_files=len(artifacts),source_files=len(manifest),
        all_source_hashes_verified=full_source,prediction_rows=len(rows),candidate_rows=len(candidates),
        positive_windows=600,negative_windows=200,calibration_windows=50,
        independent_metrics=independent,summary_recomputed=True,
        limitations=['Four positive and two negative test recordings, single aircraft/day',
                     'Nominal static reference angles, no synchronized trajectory',
                     'Group-specific background calibration; temporal windows not independent'])
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full-source',action='store_true');a=p.parse_args();main(a.full_source)
