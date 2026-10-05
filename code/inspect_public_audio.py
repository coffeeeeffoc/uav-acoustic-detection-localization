"""Describe one licensed real recording; does not evaluate detection or DOA."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if sys.version_info[:2] == (3, 12) and (ROOT / '.python-packages').exists():
    sys.path.insert(0, str(ROOT / '.python-packages'))
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def inspect(path):
    sample_rate, raw = wavfile.read(path)
    if raw.ndim != 2 or raw.shape[1] < 2 or raw.dtype != np.int16:
        raise ValueError('Expected a multichannel signed 16-bit PCM recording')
    audio = raw.astype(np.float64) / 32768.0
    if len(audio) < 4096 or not np.isfinite(audio).all():
        raise ValueError('Audio is too short or contains invalid samples')
    frequency, time, psd = spectrogram(audio[:, 0], sample_rate, nperseg=4096,
                                      noverlap=3072, scaling='density')
    report = {
        'file': path.relative_to(ROOT).as_posix(),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'sample_rate_hz': sample_rate, 'channels': audio.shape[1],
        'duration_s': len(audio) / sample_rate, 'sample_count': len(audio),
        'rms_per_channel': np.sqrt(np.mean(audio ** 2, axis=0)).tolist(),
        'clipped_sample_fraction': float(np.mean((raw == -32768) | (raw == 32767))),
        'analysis': 'First recorded channel, 4096-sample Tukey window, 3072 overlap; '
                    'power spectral density relative to its maximum in the shown band.',
        'evidence_boundary': 'Descriptive inspection of one real recording only; '
                             'not a classification, localization or field-range evaluation.'
    }
    shown = (frequency >= 100) & (frequency <= 3000)
    relative_db = 10 * np.log10(np.maximum(psd[shown], 1e-20) / np.max(psd[shown]))
    plt.rcParams.update({'font.size': 10, 'axes.labelsize': 11})
    fig, ax = plt.subplots(figsize=(5.0, 3.5), constrained_layout=True)
    plot = ax.pcolormesh(time, frequency[shown] / 1000, relative_db,
                         shading='auto', cmap='magma', vmin=-55, vmax=0)
    ax.set(xlabel='Time (s)', ylabel='Frequency (kHz)',
           title='Real IDMT sample: first microphone')
    fig.colorbar(plot, ax=ax, label='Relative PSD (dB)')
    (ROOT / 'figures').mkdir(exist_ok=True)
    (ROOT / 'results').mkdir(exist_ok=True)
    fig.savefig(ROOT / 'figures/public_audio_spectrogram.png', dpi=300)
    fig.savefig(ROOT / 'figures/public_audio_spectrogram.pdf')
    plt.close(fig)
    (ROOT / 'results/public_audio_inspection.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    # A runnable data-contract check guards accidental replacement or channel loss.
    assert report['channels'] == 8 and report['sample_rate_hz'] == 48000
    assert report['duration_s'] == 30.0
    provenance = json.loads((path.parent / 'provenance.json').read_text(encoding='utf-8'))
    expected = next(x['sha256'] for x in provenance['files'] if x['path'].endswith(path.name))
    assert report['sha256'] == expected
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    files = list((ROOT / 'data/public/idmt_sample').glob('*.wav'))
    if len(files) != 1:
        raise ValueError('Expected exactly one licensed public audio sample')
    inspect(files[0])
