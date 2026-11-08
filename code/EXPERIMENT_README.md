# DCCR field study: code, evidence and reproduction

The current paper uses real 208-channel CRY8501/SonoCam Pi recordings of a DJI Air 3S. No synthetic observations enter its field metrics. Run commands from the project root and retain the raw folder names.

## Environment and read-only verification

Executed environment: Python 3.12.14, NumPy 2.2.6 and SciPy 1.15.3. Numerical-library thread requests are set to one before importing NumPy. Hardware: Intel Core i7-12700KF; see `results/field/hardware.json`.

```powershell
$fieldPython = 'C:\Users\15211\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $fieldPython -B code/verify_field.py --full-source
& $fieldPython -B code/verify_field_delivery.py
```

On another Python 3.12 installation, install `code/requirements-field.txt` in an isolated environment and use its Python executable. This workstation uses `.python-packages` for scientific dependencies and bundled `python-docx` for documents. Paper scripts use Windows Times New Roman and SimSun; another platform needs corresponding fonts or explicit path changes.

`verify_field.py` checks 16 frozen files, seven evaluation artifacts, input sizes, complete paired rows, direction normalization, angular errors, strict threshold decisions, candidate argmax choices and every saved summary field. `--full-source` additionally recomputes all 1921 original-file SHA256 values. It does not execute estimators or create audio; it refreshes only `results/field/verification.json`. The delivered report records a completed full-source check.

`verify_field_delivery.py` checks bilingual table values, equation identity, reference numbering, document structure, PDF bounds, selected reported values and file hashes. It does not rerun acoustics. The separate visual inspection record covers all 10 final pages (five per language, including references).

## Partition and inference contract

- Original data: nine recordings, each with 208 mono PCM16 files at 48 kHz (`0.wav` to `207.wav`) and `posXY.data` geometry.
- P1, nominal 100 m: development only. Its 300 aircraft windows and 100 background windows yield 1779 candidate examples.
- P2/P3, nominal 150/200 m: evaluation only. Each background uses [0,5) s for reference subtraction, [5,10) s for calibration and [10,30) s for negative evaluation. Aircraft evaluation uses [0,30) s.
- Nonoverlapping 200 ms windows: 600 positive and 200 negative test windows, plus 50 calibration windows. Windows within a recording are correlated.
- Nominal labels use clockwise azimuth from the device mark; zero maps to native negative y. No synchronized flight trajectory or independent hardware alignment calibration is available. The `site` field identifies a measurement group, not necessarily an independent venue.

Read `research/real_data/protocol.md` and `protocol_clarifications.md`. Reference labels enter development and final error reporting, never held-out candidate search/scoring. Group-specific background calibration is an explicit operational assumption.

Example audio-only inference on an existing observation:

```python
import os, sys
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.path.insert(0, 'code')
from field_data import ROOT, OUT, recordings, geometry, load_block, np, json
from field_algorithm import ArrayProcessor, angles
from field_ranker import CoherenceRanker

record = next(r for r in recordings() if r['id'] == 's2_uav1')
processor = ArrayProcessor(geometry(ROOT / record['path']))
model = dict(np.load(OUT / 'discriminative_model.npz'))
ranker = CoherenceRanker(processor, model)
audio = load_block(record, 0.0, 0.2)  # (9600, 208), 48 kHz
unit, score, details = ranker.analyze(audio)
threshold = json.loads((OUT / 'thresholds.json').read_text())['2']['ranker']
azimuth, elevation = angles(unit)
print(dict(azimuth_deg=azimuth, elevation_deg=elevation,
           score=score, detected=bool(score > threshold)))
```

A rejected observation still has a raw bearing. The score is not a posterior probability. The threshold is specific to P2, not a universal deployment threshold. Changing the array, channel order or front end requires new development and evaluation.

## Reproduce without overwriting delivered evidence

```powershell
& $fieldPython -B code/reproduce_field.py --out results/field_reproduction
# Optional: also rebuild P1 training features and both models.
& $fieldPython -B code/reproduce_field.py --out results/field_retraining --retrain
```

The helper requires a new output directory inside this project and verifies the original freeze first. It copies frozen inputs, reruns the same recordings and compares every nontiming summary field. The retraining option also compares numerical model parameters. Timing varies with host and load. This reproduces the existing dataset; it is not a new independent field trial. The delivered original experiment and read-only verification were executed. The helper's syntax and command-line contract were checked; a second full replay is not claimed.

Do not run development scripts in place against delivered `results/field/`. Retain the original freeze. A new algorithm revision requires a new development version and fresh validation.

| Purpose | Files |
|---|---|
| Data reader/audit | `field_data.py`, `results/field/source_manifest.json`, `inventory.json` |
| Shared processing and DCCR | `field_algorithm.py`, `field_ranker.py` |
| Development/ablation | `develop_field_discriminative.py`, `finalize_field_model.py` |
| Learned models/features | `results/field/*model.npz`, `discriminative_features.npz`, `*selection.json` |
| Frozen definition | `research/real_data/protocol.md`, `results/field/frozen_config.json` |
| Evaluation/statistics | `evaluate_field.py`, `summarize_field.py` |
| Full outputs | `results/field/predictions.csv` (5100 rows), `candidates.csv` (3400 rows) |
| Summary/thresholds | `results/field/summary.json`, `thresholds.json` |
| Verification | `verify_field.py`, `results/field/verification.json` |

The early P1 reference-subtraction pilot failed to improve the development result. `development.csv` and `development_history.json` preserve that evidence; its values are not pooled with held-out results.

## Rebuild manuscripts

```powershell
& $fieldPython -B code/finalize_field_paper.py
& $fieldPython -B code/build_field_documents.py
```

The first script fills `paper/field_en_template.md` and `field_zh_template.md` from the frozen summary, creates both Markdown manuscripts, and generates bilingual figures and equation rasters. The second builds `paper/English_Main.docx` and `Chinese_Translation.docx` from the converted reference `results/document_qa/template_revision/wordtemplates.docx`. Keep that reference and its template contract (`artifact.md`); the original `模板/wordtemplates.doc` is unchanged. Interpretive prose describes this fixed experiment and needs review if the experiment changes. Mathematical source remains editable in Markdown; DOCX equations are high-resolution images, with long displays split for the template columns. The November 2026 document revision changes typography and prose only; it does not rerun acoustic inference.

This workstation retains an administrative extraction of official LibreOffice 26.2.6.3 under `.tools/LibreOffice/`. The packaged document renderer exports matching PDFs and page previews:

```powershell
$env:PYTHONUTF8 = '0'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = (Resolve-Path '.tools/LibreOffice/program').Path + ';C:\Users\15211\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin;' + $env:PATH
$docRenderer = 'C:\Users\15211\.codex\plugins\cache\openai-primary-runtime\documents\26.1105.12137\skills\documents\render_docx.py'
& $fieldPython $docRenderer paper/English_Main.docx --output_dir results/document_qa/field/en --emit_pdf --dpi 120
& $fieldPython $docRenderer paper/Chinese_Translation.docx --output_dir results/document_qa/field/zh --emit_pdf --dpi 120
Copy-Item -LiteralPath results/document_qa/field/en/English_Main.pdf -Destination paper/English_Main.pdf
Copy-Item -LiteralPath results/document_qa/field/zh/Chinese_Translation.pdf -Destination paper/Chinese_Translation.pdf
& $fieldPython -B code/verify_field_delivery.py
```

On another machine, export through Word/LibreOffice and inspect all pages again. Pagination depends on fonts and renderer. Current previews and document checks are in `results/document_qa/field/`.

## Historical synthetic work

The earlier SCCR simulation, models and frozen records remain historical material. Its manuscripts and old instructions are under `archive/legacy_manuscripts/`. Old `improved_*`, `experiment.py` and `build_papers.py` scripts do not build/evaluate the current DCCR paper. Synthetic results are not real-audio evidence for the current method.

The 2026-11-08 authoring runtime and package versions are recorded in `results/document_qa/template_revision/authoring_environment.json`. Document checks import PyMuPDF from that runtime rather than the repository scientific package directory. Resolve current bundled runtime paths before rebuilding; the acoustic experiment environment above remains its original measured environment.
