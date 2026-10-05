"""Freeze the hard-negative ablation using the same development inputs and folds."""
from field_data import *
from develop_field_discriminative import fit,predict

def main():
    z=np.load(OUT/'discriminative_features.npz')
    assert str(z['source_sha256'])==sha(ROOT/'code/field_algorithm.py')
    assert str(z['builder_sha256'])==sha(ROOT/'code/develop_field_discriminative.py')
    assert str(z['manifest_sha256'])==sha(OUT/'source_manifest.json')
    keep=(z['y']>0)|np.char.startswith(z['block_id'],'s1_background:')
    X,y,fold=z['X'][keep],z['y'][keep],z['fold'][keep]
    candidates=[]
    for alpha in [.1,1.,10.,100.]:
        p=np.empty(len(y))
        for f in [0,1]:
            m=fit(X[fold!=f],y[fold!=f],fold[fold!=f],alpha)
            p[fold==f]=predict(m,X[fold==f])
        loss=float(.5*np.mean((p[y>0]-1)**2)+.5*np.mean((p[y<0]+1)**2))
        candidates.append(dict(alpha=alpha,balanced_oof_mse=loss))
    alpha=min(candidates,key=lambda r:r['balanced_oof_mse'])['alpha']
    m=fit(X,y,fold,alpha)
    np.savez_compressed(OUT/'no_hard_negatives_model.npz',**m,alpha=alpha,
                       feature_sha256=sha(OUT/'discriminative_features.npz'),source_sha256=sha(ROOT/'code/field_algorithm.py'))
    (OUT/'no_hard_negatives_selection.json').write_text(json.dumps(dict(candidates=candidates,
        selected_alpha=alpha,samples=len(y),positive=int(sum(y>0)),
        excluded=int(sum(~keep)),feature_digest=sha(OUT/'discriminative_features.npz')),indent=2),encoding='utf-8')
    print('ablation',alpha,'kept',len(y),'excluded',sum(~keep))

if __name__=='__main__':main()
