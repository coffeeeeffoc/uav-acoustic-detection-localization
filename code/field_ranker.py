"""Direction-conditioned coherence ranking of audio-generated SRP candidates."""
from field_algorithm import *

class CoherenceRanker:
    def __init__(self,processor,model):
        self.e=processor
        self.model=model

    def candidates(self,p,c):
        floor=max(float(p[:,self.e.mask].mean())*1e-12,1e-30)
        q=c/np.maximum(np.abs(c),floor)
        cc=self.e.correlations(q)
        coarse=self.e.maps(cc)
        candidates=[]
        for k in np.argsort(coarse)[::-1]:
            if not candidates or min(angular_error(self.e.grid[k],np.asarray(candidates)))>=12:
                candidates.append(self.e.grid[k])
            if len(candidates)==4: break
        refined=[]
        for u in candidates:
            steps=np.arange(-.05,.0501,.005)
            dx,dy=np.meshgrid(steps,steps)
            xy=np.column_stack((dx.ravel(),dy.ravel()))+u[:2]
            xy=xy[(xy**2).sum(axis=1)<=1]
            grid=np.column_stack((xy,np.sqrt(np.maximum(1-(xy**2).sum(axis=1),0))))
            val=self.e.maps(cc,grid)
            v=grid[np.argmax(val)]
            az,el=angles(v)
            aa,ee=np.meshgrid(az+np.arange(-1,1.001,.1),np.clip(el+np.arange(-2,2.001,.1),0,90))
            fine=directions(aa.ravel(),ee.ravel())
            vals=self.e.maps(cc,fine)
            if np.max(vals)>np.max(val):v=fine[np.argmax(vals)]
            refined.append(v)
        return np.asarray(refined)

    def analyze_spectra(self,p,c):
        units=self.candidates(p,c)
        X=self.e.candidate_features(p,c,units)
        m=self.model
        scores=(X-m['center'])/m['scale']@m['coef']+m['intercept']
        k=int(np.argmax(scores))
        return units[k],float(scores[k]),dict(units=units,features=X,scores=scores,index=k)

    def analyze(self,audio):
        p,c,_=self.e.spectra(audio)
        return self.analyze_spectra(p,c)
