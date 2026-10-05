"""Read-only access and provenance audit for the 208-channel field recordings."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.python-packages'))
import hashlib
import json
import wave
import numpy as np
from scipy.io import wavfile

OUT = ROOT / 'results' / 'field'
SOURCE = next((ROOT / '赛题信息').glob('*附件*'))
RAW = next(SOURCE.rglob('无人机数据文件'))
REFERENCES = {1: [(225.0, 88.3), (251.5, 88.3)],
              2: [(97.17, 60.0), (92.41, 60.0)],
              3: [(131.88, 66.4), (135.0, 66.4)]}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''): h.update(b)
    return h.hexdigest()

def geometry(directory):
    b = (directory / 'posXY.data').read_bytes()
    n = len(b) // 12
    ids = np.frombuffer(b[:n*4], '<i4')
    assert np.array_equal(ids, np.arange(n))
    phi = np.frombuffer(b[n*4:n*8], '<f4').astype(float)
    rad = np.frombuffer(b[n*8:], '<f4').astype(float)
    return np.column_stack((rad*np.cos(phi), rad*np.sin(phi), np.zeros(n)))

def recordings():
    rows = []
    for p in sorted(RAW.iterdir()):
        if not p.is_dir(): continue
        site = int(p.name.split('点位')[1][0])
        positive = '环境噪声' not in p.name
        take = int(p.name[-1]) if positive else 0
        rows.append(dict(id=f's{site}_'+(f'uav{take}' if positive else 'background'),
                         site=site, positive=positive, take=take,
                         range_m=[100, 150, 200][site-1],
                         reference_az_deg=REFERENCES[site][take-1][0] if positive else None,
                         reference_el_deg=REFERENCES[site][take-1][1] if positive else None,
                         path=p.relative_to(ROOT).as_posix()))
    return rows

def load_block(record, start_s, duration_s, channels=None):
    p = ROOT / record['path'] / 'wav'
    channels = range(208) if channels is None else channels
    start, n = int(round(start_s*48000)), int(round(duration_s*48000))
    data = []
    for ch in channels:
        fs, x = wavfile.read(p / f'{ch}.wav', mmap=True)
        assert fs == 48000 and x.dtype == np.int16 and x.ndim == 1
        assert start+n <= len(x)
        data.append(x[start:start+n].astype(np.float32)/32768)
    return np.stack(data, axis=1)

def audit():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, all_rows = [], []
    for rec in recordings():
        p = ROOT / rec['path']
        xy = geometry(p)
        files = list((p / 'wav').glob('*.wav'))
        assert {x.name for x in files} == {f'{i}.wav' for i in range(208)}
        stats = []
        for ch in range(208):
            f = p / 'wav' / f'{ch}.wav'
            with wave.open(str(f)) as w:
                params = w.getparams()
                assert params.nchannels == 1 and params.sampwidth == 2
                assert params.framerate == 48000 and params.comptype == 'NONE'
            fs, x = wavfile.read(f, mmap=True)
            xf = x.astype(np.float64)
            stats.append(dict(ch=ch, frames=len(x), rms=float(np.sqrt(np.mean(xf**2))/32768),
                              mean=float(xf.mean()/32768),
                              peak=int(np.max(np.abs(x.astype(np.int32)))),
                              clipped=int(np.sum((x == -32768) | (x == 32767)))))
            manifest.append(dict(path=f.relative_to(ROOT).as_posix(), bytes=f.stat().st_size, sha256=sha(f)))
        assert len({s['frames'] for s in stats}) == 1
        for fn in ['file.info', 'posXY.data', 'image.jpg', 'video.mp4', 'ccdVideo.mp4']:
            f=p/fn
            if f.exists(): manifest.append(dict(path=f.relative_to(ROOT).as_posix(), bytes=f.stat().st_size, sha256=sha(f)))
        rec.update(duration_s=stats[0]['frames']/48000, channels=208, sample_rate_hz=48000,
                   pcm_bits=16, geometry_sha256=sha(p/'posXY.data'),
                   max_radius_m=float(np.max(np.linalg.norm(xy[:,:2], axis=1))),
                   channel_statistics=stats)
        all_rows.append(rec)
        print(rec['id'], rec['duration_s'], 'rms range', min(s['rms'] for s in stats), max(s['rms'] for s in stats),
              'clipped',sum(s['clipped'] for s in stats),flush=True)
    for f in SOURCE.glob('*'):
        if f.is_file(): manifest.append(dict(path=f.relative_to(ROOT).as_posix(),bytes=f.stat().st_size,sha256=sha(f)))
    assert len({r['geometry_sha256'] for r in all_rows}) == 1
    (OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'inventory.json').write_text(json.dumps(dict(recordings=all_rows,
        reference_source='附件4：试验说明文档.docx, embedded images 2–4; nominal static references, no synchronized per-frame trajectory',
        geometry_units='angle radians, radius metres, interpreted from supplied reader and geometry scale',
        synchronization='Matching channel sample counts and sampling rates verified; hardware clock skew not independently calibrated',
        coordinate_registration='To be checked against supplied interface before evaluation'),ensure_ascii=False,indent=2),encoding='utf-8')

if __name__ == '__main__': audit()
