# SCCR experiment and reproduction / 算法与实验复现

The current paper studies source-conditioned candidate ranking and a spectral-spatial detector. All quantitative evaluation is synthetic. A real IDMT recording is retained separately as supplementary signal material, not as performance evidence.

## Read or verify the completed experiment

Run from the project root in PowerShell:

```powershell
$experimentPython = 'C:\Users\15211\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $experimentPython -B code/verify_improved.py
& $experimentPython code/verify_delivery.py --render
```

`verify_improved.py` checks frozen inputs, every recorded artifact hash, thresholds, partitions, paired rows, saved labels, direction errors, timing algebra and all summary fields. It does not synthesize data or execute fitted models; only `results/improved_verification.json` is refreshed. Its component-hash check verifies metadata structure and uniqueness, not regenerated component waveforms.

The executed environment is Python 3.12.14, NumPy 2.2.6 and SciPy 1.15.3, with numerical-library thread requests set to one. Exact packages are listed in `requirements-lock.txt` and `paper-requirements.txt`. On another Python 3.12 installation use `python -m pip install -r code/requirements-lock.txt -r code/paper-requirements.txt`. This workstation uses the local `.python-packages` directory for scientific dependencies.

## Audio-only inference

The learned algorithms require finite `(1600, 8)` audio at 8 kHz and the documented nominal microphone geometry/channel order. Changing the array requires new feature/model development; the example is not a hardware SDK.

```python
import sys
sys.path.insert(0, 'code')
from experiment import ROOT
from improved_detector import Detector
from improved_localizer import ImprovedLocalizer
import json
import numpy as np

with np.load(ROOT / 'data/synthetic/improved/test/pos-0-2-000.npz') as saved:
    audio = saved['audio']
detector = Detector.load(ROOT / 'results/development_detector/model.npz')
localizer = ImprovedLocalizer()
threshold = json.loads((ROOT / 'results/improved/thresholds.json').read_text())['thresholds']['proposed']
score = detector.analyze(audio)
estimate = localizer.analyze(audio)
print({'detected': score > threshold, 'score': score,
       'azimuth_deg': estimate['az_hat'], 'elevation_deg': estimate['el_hat']})
```

The raw bearing exists even for a rejected frame; it must not be counted as an accepted detection. `return_map=True` additionally returns the sparse scored-candidate map (NaN elsewhere) and dense proposal maps. The learned score is not a calibrated class probability. Source and feature digests guard model loading; failures are intentional, not a reason to bypass the guard.

## Partitions and files

- `data/synthetic/full/test/`: 2000 previously examined recordings, now development inputs. They are not the new independent test.
- `data/synthetic/development_augmented/`: 800 negative mixtures made only from old development recordings; 600 internal training and 200 validation items, with constituent recordings separated by fold.
- `results/development_detector/`: 87- and 39-feature models, cached features, fold/provenance records and selection results.
- `results/development_localizer/`: 149-feature full and 104-feature no-suppression models, grouped OOF predictions, cache/input manifests, source hashes and development reports.
- `research/algorithm_revision_protocol.md`: frozen protocol; `results/improved/frozen_config.json`: source/model hashes, random namespaces and evaluation sizes.
- `data/synthetic/improved/`: 800 calibration negatives, 3000 independent static test recordings and 24 complete 24-second sequences; 3824 NPZ files and 6680 audio frames. NPZ includes float32 audio, truth arrays, sample rate, geometry and JSON generation metadata. Multiple-source metadata includes constituent seeds, parameters, mixing weights and raw-waveform SHA256 values.
- `results/improved/calibration.csv`, `thresholds.json`: the same 800 negatives for each detector; the 761st order statistic and strict score > threshold.
- `detection_frames.csv`, `localization_frames.csv`, `timing_frames.csv` inside `results/improved/`: respectively 9000, 6000 and 3000 rows. All six localizers are evaluated on every positive trial.
- `sequence_detection.csv`, `sequence_localization.csv`: 8640 and 14400 rows; neighboring frames are not independent trials. Raw localization only, without a motion filter.
- `summary.json`, `run_complete.json`, `artifact_manifest.json` inside `results/improved/`: fixed-model statistics, successful completion and SHA256 inventory. Manifest excludes itself.
- `results/improved_method_review.md`, `results/improved_verification.json`: independent method and final-output checks.

The three timing columns distinguish shared extraction plus both detector predictions, candidate localization, and their sum. The latter is a conservative proposed-pipeline bound, not the precise time of one deployed detector. It excludes 200 ms acquisition, file I/O, synthesis, initialization and display.

## Reproduce acoustics and development

Preserve the delivered directory. Use a separate copy, explicitly archive its existing `results/improved/` and `data/synthetic/improved/`, then execute `python code/evaluate_improved.py`. The script refuses to overwrite an existing frozen run. Deterministic IDs and seeds reproduce acoustic outcomes; timing varies with the host. Do not alter models or source between calibration and evaluation.

For a development rerun in a separate copy, `python code/improved_detector.py` fits the detector candidates, and `python code/improved_localizer.py --finalize` rebuilds the final grouped candidate models against the retained old development archive. The latter checks the selected historical candidate model and old-feature reproduction. These commands can overwrite development outputs; they are not required to use the delivered models. Changing the feature implementation is a new development version and needs a new frozen evaluation, not a retroactive edit of this run.

The earlier `experiment.py --full`, `summarize_experiment.py results/full` and `verify_experiment.py` reproduce/check the historical weighted-SRP experiment. `results/quick/` is an older engineering checkpoint; neither quick nor old full results are the independent final scores of SCCR. Do not regenerate historical artifacts in place while using their hashes as development provenance.

## Rebuild manuscripts

```powershell
& $experimentPython code/finalize_manuscripts.py
& $experimentPython code/build_papers.py --assets
& $experimentPython code/build_papers.py
& $experimentPython code/verify_delivery.py --render
```

The two `paper/improved_*_draft.md` files are numeric-placeholder templates, not alternate final manuscripts. `finalize_manuscripts.py` inserts the frozen result tables, bilingual result discussion and ordered citations. Its interpretive prose describes this fixed experiment and must be reviewed if the experiment changes. It preserves the original 19 references from the archived first manuscript and adds two verified sources. Final reading files are `paper/manuscript_en.md/.pdf` and `paper/manuscript_zh.md/.pdf`.

PDF generation uses local Times New Roman and SimSun files under `C:/Windows/Fonts`; provide suitable fonts and edit the paths for another platform. Equations are rendered at 300 dpi; Markdown retains editable mathematical source. Figures have PNG and vector-PDF versions. The PDF is a generic scholarly layout, not a supplied conference template.
