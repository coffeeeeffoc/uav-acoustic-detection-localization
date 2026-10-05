"""Transparent array processing. No class labels or reference directions in inference."""
from field_data import np
from scipy import signal, fft

FS = 16000
NFFT = 512
HOP = 256
INTERP = 8
C0 = 343.0
BAND = (300.0, 7500.0)
METHODS = ['srp', 'phat', 'scot', 'coherence', 'excess', 'reference', 'balanced']

def directions(az, el):
    a,e = np.deg2rad(az),np.deg2rad(el)
    return np.stack((-np.cos(e)*np.sin(a), -np.cos(e)*np.cos(a), np.sin(e)),axis=-1)

def angles(u):
    return float(np.rad2deg(np.arctan2(-u[0],-u[1]))%360),float(np.rad2deg(np.arcsin(np.clip(u[2],-1,1))))

def angular_error(u,v):
    return np.rad2deg(np.arccos(np.clip(np.sum(np.asarray(u)*np.asarray(v),axis=-1),-1,1)))

def make_grid(step=.05):
    v=np.arange(-1,1+step/2,step)
    x,y=np.meshgrid(v,v)
    xy=np.column_stack((x.ravel(),y.ravel()))
    xy=xy[(xy**2).sum(axis=1)<=1+1e-10]
    return np.column_stack((xy,np.sqrt(np.maximum(1-(xy**2).sum(axis=1),0))))

class ArrayProcessor:
    def __init__(self, xyz):
        self.xyz=np.asarray(xyz,float)
        # Six circulant offsets cover every sensor; deduplication yields 1248 pairs.
        pairs=sorted({tuple(sorted((i,(i+d)%len(xyz)))) for i in range(len(xyz)) for d in [17,35,53,71,89,103]})
        pairs=np.asarray(pairs)
        # Very short baselines provide little angular leverage in this band.
        pairs=pairs[np.linalg.norm(xyz[pairs[:,0]]-xyz[pairs[:,1]],axis=1)>=.06]
        self.i,self.j=pairs.T
        self.baseline=xyz[self.i]-xyz[self.j]
        self.grid=make_grid()
        self.f=fft.rfftfreq(NFFT,1/FS)
        self.mask=(self.f>=BAND[0])&(self.f<=BAND[1])
        self.window=signal.windows.hann(NFFT,sym=False).astype(np.float32)
        self.lookup=self._lookup(self.grid)

    def spectra(self,audio):
        a=np.asarray(audio,np.float32)
        assert a.ndim==2 and a.shape[1]==len(self.xyz) and np.isfinite(a).all()
        a=a-a.mean(axis=0)
        a=signal.resample_poly(a,1,3,axis=0,padtype='line')
        frames=np.lib.stride_tricks.sliding_window_view(a,NFFT,axis=0)[::HOP]
        frames=frames-frames.mean(axis=-1,keepdims=True)
        X=fft.rfft(frames*self.window,axis=-1)
        p=np.mean(np.abs(X)**2,axis=0).astype(float)
        cross=np.mean(X[:,self.i]*X[:,self.j].conj(),axis=0).astype(np.complex128)
        return p,cross,len(frames)

    def _lookup(self,grid):
        # X_i X_j* = exp(+j omega (r_i-r_j).u/c); inverse FFT peaks at -delay.
        t=-self.baseline@grid.T/C0*FS*INTERP
        n=NFFT*INTERP
        lo=np.floor(t).astype(int)
        return lo%n,(lo+1)%n,t-lo

    def correlations(self,q):
        q=np.asarray(q).copy()
        q[:,~self.mask]=0
        return fft.irfft(q,n=NFFT*INTERP,axis=-1)*INTERP

    def maps(self,cc,grid=None):
        lo,hi,w=self.lookup if grid is None else self._lookup(grid)
        rows=np.arange(len(cc))[:,None]
        return np.mean(cc[rows,lo]*(1-w)+cc[rows,hi]*w,axis=0)

    def localize(self,q):
        cc=self.correlations(q)
        coarse=self.maps(cc)
        k=int(np.argmax(coarse))
        center=self.grid[k,:2]
        steps=np.arange(-.05,.0501,.005)
        dx,dy=np.meshgrid(steps,steps)
        xy=np.column_stack((dx.ravel(),dy.ravel()))+center
        xy=xy[(xy**2).sum(axis=1)<=1]
        grid=np.column_stack((xy,np.sqrt(np.maximum(1-(xy**2).sum(axis=1),0))))
        refined=self.maps(cc,grid)
        j=int(np.argmax(refined))
        # Keep coarse horizon candidates as well.
        u,peak=(grid[j],refined[j]) if refined[j]>=coarse[k] else (self.grid[k],coarse[k])
        # A final angular refinement avoids poor elevation resolution near the disk rim.
        az,el=angles(u)
        aa,ee=np.meshgrid(az+np.arange(-1,1.001,.1),np.clip(el+np.arange(-2,2.001,.1),0,90))
        fine=directions(aa.ravel(),ee.ravel())
        val=self.maps(cc,fine)
        j=int(np.argmax(val))
        if val[j]>peak: u,peak=fine[j],val[j]
        return u,float(peak),coarse

    def weights(self,p,c,L,noise):
        n,b= noise
        floor=max(float(p[:,self.mask].mean())*1e-12,1e-30)
        den=np.sqrt(np.maximum(p[self.i]*p[self.j],floor**2))
        phase=c/np.maximum(np.abs(c),floor)
        coh=np.clip((L*np.abs(c/den)**2-1)/max(L-1,1),0,1)
        # Robust broadband gain alignment does not use aircraft frequency or direction.
        gain=np.median(p[:,self.mask]/np.maximum(n[:,self.mask],floor),axis=1)
        gain=np.maximum(gain,1e-6)
        scaled=gain[:,None]*n
        z=np.clip(1-scaled/np.maximum(p,floor),0,1)
        reliability=np.sqrt(z[self.i]*z[self.j])
        residual=c-np.sqrt(gain[self.i]*gain[self.j])[:,None]*b
        residual_phase=residual/np.maximum(np.abs(residual),floor)
        res_coh=np.minimum(np.abs(residual)/den,1)
        ref=residual_phase*res_coh**2*reliability
        balanced=ref.copy()
        # Prevent a single wide frequency region from dominating; no normalization of empty bands.
        for low,high in zip([300,750,1500,3000],[750,1500,3000,7501]):
            mask=(self.f>=low)&(self.f<high)
            balanced[:,mask]/=max(1,np.sum(mask))
        # SRP's global scale is normalized only for comparable numerical magnitude.
        return dict(srp=c/max(float(p[:,self.mask].mean()),floor),phat=phase,scot=c/den,
                    coherence=phase*coh,excess=phase*coh*reliability,
                    reference=ref,balanced=balanced)

    def analyze(self,audio,noise,methods=METHODS):
        p,c,L=self.spectra(audio)
        weights=self.weights(p,c,L,noise)
        return {name:self.localize(weights[name]) for name in methods}

    def candidate_features(self,p,c,units):
        """24 directional coherence bands; no azimuth/elevation coordinates as features."""
        floor=max(float(p[:,self.mask].mean())*1e-12,1e-30)
        normalized=c/np.sqrt(np.maximum(p[self.i]*p[self.j],floor**2))
        edges=np.linspace(300,7500,25)
        masks=[(self.f>=a)&(self.f<b) for a,b in zip(edges[:-1],edges[1:])]
        masks[-1]|=self.f==7500
        rows=[]
        for u in units:
            phase=np.exp(-2j*np.pi*(self.baseline@u/C0)[:,None]*self.f)
            response=np.real(normalized*phase).mean(axis=0)
            rows.append([float(response[m].mean()) for m in masks])
        return np.asarray(rows)

    def discriminative_weight(self,p,c,model):
        floor=max(float(p[:,self.mask].mean())*1e-12,1e-30)
        q=c/np.sqrt(np.maximum(p[self.i]*p[self.j],floor**2))
        # Match the direct directional-feature score, since irfft contributes 2/NFFT.
        edges=np.linspace(300,7500,25)
        weights=np.zeros_like(self.f)
        for b,(a,z) in enumerate(zip(edges[:-1],edges[1:])):
            mask=(self.f>=a)&(self.f<z)
            if b==23: mask|=self.f==7500
            weights[mask]=model['coef'][b]/model['scale'][b]/np.sum(mask)*NFFT/2
        return q*weights, float(model['intercept']-np.sum(model['coef']*model['center']/model['scale']))
