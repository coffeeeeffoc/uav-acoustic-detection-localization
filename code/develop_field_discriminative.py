"""Fit a direction-conditioned linear spectral score using point 1 only."""
from field_data import *
from field_algorithm import *
import argparse,csv,time

def fit(X,y,groups,alpha):
    # Equal total positive/negative weight; normalize per-class total to n/2.
    w=np.where(y>0,.5/max(1,np.sum(y>0)),.5/max(1,np.sum(y<0)))*len(y)
    center=np.average(X,axis=0,weights=w)
    scale=np.maximum(np.sqrt(np.average((X-center)**2,axis=0,weights=w)),.01)
    Z=(X-center)/scale
    Z=np.column_stack((Z,np.ones(len(Z))))
    penalty=np.eye(Z.shape[1])*alpha;penalty[-1,-1]=0
    beta=np.linalg.solve(Z.T@(w[:,None]*Z)+penalty,Z.T@(w*y))
    return dict(center=center,scale=scale,coef=beta[:-1],intercept=beta[-1])

def predict(model,X):
    return (X-model['center'])/model['scale']@model['coef']+model['intercept']

def build():
    records=[r for r in recordings() if r['site']==1]
    e=ArrayProcessor(geometry(ROOT/records[0]['path']))
    features=[];labels=[];groups=[];errors=[];ids=[];units=[]
    for rec in records:
        for start in np.arange(0 if rec['positive'] else 10,30,.2):
            p,c,L=e.spectra(load_block(rec,float(start),.2))
            q=c/np.maximum(np.abs(c),1e-30)
            spectrum=e.maps(e.correlations(q))
            order=np.argsort(spectrum)[::-1]
            candidates=[]
            for k in order:
                if not candidates or min(angular_error(e.grid[k],np.asarray(candidates)))>=12:
                    candidates.append(e.grid[k])
                if len(candidates)==4: break
            # Training-only true direction supplies a positive spectral prototype.
            # It is never a candidate supplied to validation/inference.
            if rec['positive']:
                truth=directions(rec['reference_az_deg'],rec['reference_el_deg'])
                candidates.append(truth)
                err=angular_error(np.asarray(candidates),truth)
                y=np.where(err<=5,1.,-1.)
                keep=(err<=5)|(err>=15)
            else:
                err=np.full(len(candidates),180.);y=np.full(len(candidates),-1.);keep=np.ones(len(candidates),bool)
            f=e.candidate_features(p,c,candidates)
            fold=rec['take']-1 if rec['positive'] else int(start>=20)
            for k in np.where(keep)[0]:
                features.append(f[k]);labels.append(y[k]);groups.append(fold);errors.append(err[k]);
                ids.append(f"{rec['id']}:{start:.1f}");units.append(candidates[k])
            if int(round(start*5))%25==0:print(rec['id'],round(float(start),2),flush=True)
    np.savez_compressed(OUT/'discriminative_features.npz',X=features,y=labels,fold=groups,error=errors,
                        block_id=ids,unit=units,source_sha256=sha(ROOT/'code/field_algorithm.py'),
                        builder_sha256=sha(__file__),manifest_sha256=sha(OUT/'source_manifest.json'))

def train():
    z=np.load(OUT/'discriminative_features.npz')
    assert str(z['source_sha256'])==sha(ROOT/'code/field_algorithm.py')
    assert str(z['manifest_sha256'])==sha(OUT/'source_manifest.json')
    X,y,fold=z['X'],z['y'],z['fold']
    report=[]
    for alpha in [.1,1.,10.,100.]:
        preds=np.empty(len(y))
        for f in [0,1]:
            model=fit(X[fold!=f],y[fold!=f],fold[fold!=f],alpha)
            preds[fold==f]=predict(model,X[fold==f])
        loss=float(.5*np.mean((preds[y>0]-1)**2)+.5*np.mean((preds[y<0]+1)**2))
        report.append(dict(alpha=alpha,balanced_oof_mse=loss,
                           positive_mean_score=float(preds[y>0].mean()),negative_mean_score=float(preds[y<0].mean())))
    alpha=min(report,key=lambda r:r['balanced_oof_mse'])['alpha']
    model=fit(X,y,fold,alpha)
    np.savez_compressed(OUT/'discriminative_model.npz',**model,alpha=alpha,
                        feature_sha256=sha(OUT/'discriminative_features.npz'),source_sha256=sha(ROOT/'code/field_algorithm.py'))
    (OUT/'discriminative_selection.json').write_text(json.dumps(dict(candidates=report,selected_alpha=alpha,
        training_site=1,training_candidate_count=len(y),positive_candidates=int(sum(y>0)),
        validation='Two grouped folds: entire positive take and separate contiguous background half. Candidate-level classification loss; no held-out point data.',
        note='Training labels use nominal reference directions. Inference uses audio and array geometry only.'),indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
    print('selected',alpha,'model_sha256',sha(OUT/'discriminative_model.npz'),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--train-only',action='store_true');a=ap.parse_args()
    if not a.train_only:build()
    train()
