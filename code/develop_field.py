"""Development-only experiment at point 1. No held-out audio is loaded."""
from field_data import *
from field_algorithm import *
import csv,time

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    recs=[r for r in recordings() if r['site']==1]
    engine=ArrayProcessor(geometry(ROOT/recs[0]['path']))
    background=next(r for r in recs if not r['positive'])
    ps,cs=[],[]
    for start in np.arange(0,5,.2):
        p,c,_=engine.spectra(load_block(background,float(start),.2))
        ps.append(p);cs.append(c)
    noise=np.mean(ps,axis=0),np.mean(cs,axis=0)
    np.savez_compressed(OUT/'development_noise.npz',p=noise[0],c=noise[1])
    rows=[]
    for r in recs:
        # Initial development sweep covers full durations at 1 s spacing.
        starts=np.arange(0,30,1.) if r['positive'] else np.arange(5,30,.2)
        for start in starts:
            tic=time.perf_counter()
            out=engine.analyze(load_block(r,float(start),.2),noise)
            for method,(u,score,_) in out.items():
                az,el=angles(u)
                error=float(angular_error(u,directions(r['reference_az_deg'],r['reference_el_deg']))) if r['positive'] else None
                rows.append(dict(id=r['id'],positive=int(r['positive']),start_s=round(float(start),3),method=method,
                                 score=score,az_deg=az,el_deg=el,error_deg=error))
            if int(round(start*5))%25==0: print(r['id'],round(float(start),2),round(time.perf_counter()-tic,3),flush=True)
    with (OUT/'development.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for m in METHODS:
        pos=[r for r in rows if r['method']==m and r['positive']]
        cal=[r['score'] for r in rows if r['method']==m and not r['positive'] and r['start_s']<10]
        neg=[r for r in rows if r['method']==m and not r['positive'] and r['start_s']>=10]
        t=max(cal)
        print(m,'mean',np.mean([r['error_deg'] for r in pos]),'median',np.median([r['error_deg'] for r in pos]),
              'TPR',np.mean([r['score']>t for r in pos]),'FPR',np.mean([r['score']>t for r in neg]),flush=True)

if __name__=='__main__':main()
