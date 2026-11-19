"""Audit the delivered revision without changing manuscripts or frozen evidence."""
from pathlib import Path
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
import csv
import io
import json
import re
import sys
import unicodedata
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / '.python-packages'), str(ROOT / 'code')]
import numpy as np
import pymupdf as fitz
from docx import Document
import similarity_precheck as overlap
import verify_field

PACKAGE = ROOT / 'paper/editor_revision_2026-11-13'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text).replace('−', '-').replace('\xad', '')).casefold()


def numbers(text):
    return Counter(re.findall(r'\d+(?:\.\d+)*', unicodedata.normalize('NFKC', text)))


# Check duplicate/overlapping matches and paragraph boundaries before reuse.
test = overlap.audit(['one two three four', 'five six'], [{'path': 'a', 'text': 'one two three four one two three'}], 'en', [3])[0]
assert test['union_covered_units'] == 4 and test['total_units'] == 6
test = overlap.audit(['one two', 'three four'], [{'path': 'a', 'text': 'two three'}], 'en', [2])[0]
assert test['union_covered_units'] == 0
test = overlap.audit(['甲乙丙丁'], [{'path': 'a', 'text': '甲乙丙丁'}], 'zh', [3])[0]
assert test['union_covered_units'] == 4

old = json.loads((ROOT / 'results/similarity_precheck/local_metrics.json').read_text(encoding='utf-8'))
sources, full_sources, source_manifest = [], [], []
for entry in old['sources']:
    path = ROOT / entry['path']
    text = overlap.extract(path)
    included = len(text.strip()) >= 500
    source_manifest.append({'path': entry['path'], 'sha256': digest(path), 'characters': len(text), 'included': included})
    if included:
        full_sources.append({'path': entry['path'], 'text': text})
        sources.append({'path': entry['path'], 'text': overlap.without_references(text)})

report = {'date': '2026-11-15', 'target': 'IEEE ISAICS 2026', 'status': 'LOCAL_PRECHECK_NOT_OFFICIAL_AI_OR_SIMILARITY_REPORT',
          'source_manifest': source_manifest, 'documents': {}, 'translation_checks': {}, 'result_checks': {}}
documents = []
for lang, stem in [('en', 'DCCR_Editor_Revised'), ('zh', 'DCCR_Chinese_Revised')]:
    path = PACKAGE / (stem + '.docx')
    d = Document(path)
    documents.append(d)
    body = overlap.docx_body_blocks(path)
    full = [overlap.normalize(p) for p in overlap.extract(path).splitlines() if p.strip()]
    widths = [5, 8, 12] if lang == 'en' else [13, 20, 30]
    result = {'sha256': digest(path), 'body_exact_overlap': overlap.audit(body, sources, lang, widths),
              'full_text_including_references_exact_overlap': overlap.audit(full, full_sources, lang, widths)}
    with fitz.open(PACKAGE / (stem + '.pdf')) as pdf:
        text = norm(''.join(p.get_text(sort=False) for p in pdf))
        paragraphs = [p.text for p in d.paragraphs if p.text.strip()]
        cells = [c.text for t in d.tables if len(t.rows) > 1 for r in t.rows for c in r.cells]
        missing = [p for p in paragraphs + cells if norm(p) not in text]
        assert not missing, missing
        fonts = {item[0]: item[3] for page in pdf for item in page.get_fonts()}
        embedded = {name: bool(pdf.extract_font(xref)[3]) for xref, name in fonts.items()}
        assert all(embedded.values()), embedded
        result['pdf'] = {'sha256': digest(PACKAGE / (stem + '.pdf')), 'pages': len(pdf),
                         'page_sizes_points': [list(p.rect)[2:] for p in pdf],
                         'fonts_embedded': embedded, 'paragraphs_matched': len(paragraphs), 'table_cells_matched': len(cells)}
        assert len(pdf) == 5
    with ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
        result['word_markup'] = {name: len(re.findall(pattern, xml)) for name, pattern in {
            'tracked_insertions': r'<w:ins\b', 'tracked_deletions': r'<w:del\b',
            'comment_references': r'<w:commentReference\b', 'hidden_runs': r'<w:vanish\b'}.items()}
    body_text = '\n'.join(p.text for p in d.paragraphs[:87])
    refs = list(dict.fromkeys(map(int, re.findall(r'\[(\d+)\]', body_text))))
    assert refs == list(range(1, 13)), refs
    result['citation_first_appearance_order'] = refs
    result['tables'] = {'equation_tables': sum(len(t.rows) == 1 for t in d.tables), 'data_tables': sum(len(t.rows) > 1 for t in d.tables)}
    report['documents'][lang] = result

en, zh = documents
mapping = json.loads((PACKAGE / 'translation_zh.json').read_text(encoding='utf-8'))
for index in mapping:
    i = int(index)
    if i not in [3, 8]:
        text = en.paragraphs[i].text.replace('unit-magnitude', '1-magnitude').replace('unit magnitude', '1 magnitude').replace('unity', '1').replace(' May ', ' 5 ')
        assert numbers(text) == numbers(zh.paragraphs[i].text), i
for a, b in zip(en.tables, zh.tables):
    if len(a.rows) == 1:
        assert a._tbl.xml == b._tbl.xml
    else:
        for ar, br in zip(a.rows, b.rows):
            for ac, bc in zip(ar.cells, br.cells):
                assert numbers(ac.text) == numbers(bc.text)
assert all(en.paragraphs[i].text == zh.paragraphs[i].text for i in range(88, 100))
report['translation_checks'] = {'paragraph_numeric_tokens': 'PASS', 'table_numeric_tokens': 'PASS', 'equation_xml': 'IDENTICAL', 'references': 'IDENTICAL'}

# Reuse the established verifier and retain its report separately; restore the old output exactly.
previous_report = ROOT / 'results/field/verification.json'
previous_bytes = previous_report.read_bytes()
try:
    with redirect_stdout(io.StringIO()):
        verify_field.main(full_source=False)
    field_report = json.loads(previous_report.read_text(encoding='utf-8'))
    (OUT / 'field_verification.json').write_text(json.dumps(field_report, indent=2) + '\n', encoding='utf-8')
finally:
    previous_report.write_bytes(previous_bytes)
assert previous_report.read_bytes() == previous_bytes

summary = json.loads((ROOT / 'results/field/summary.json').read_text())
methods = ['phat', 'scot', 'coherence', 'reference', 'no_hard_negatives', 'ranker']
data_tables = [t for t in en.tables if len(t.rows) > 1]
for row, method in zip(data_tables[1].rows[1:], methods):
    m = summary['methods'][method]
    expected = [f'{m[k]:.2f}' for k in ['mean_deg', 'median_deg', 'p95_deg']] + [f'{100*m[k]:.1f}' for k in ['within5', 'within10']]
    assert [c.text for c in row.cells[1:]] == expected, method
for row, method in zip(data_tables[2].rows[1:], methods):
    m = summary['methods'][method]
    expected = [str(m[k]) for k in ['detected_positive', 'false_positive']] + [f'{100*m[k]:.1f}' for k in ['tpr', 'fpr', 'joint10']]
    assert [c.text for c in row.cells[1:]] == expected, method
rows = list(csv.DictReader((ROOT / 'results/field/predictions.csv').open(encoding='utf-8')))
candidates = list(csv.DictReader((ROOT / 'results/field/candidates.csv').open(encoding='utf-8')))
positives = {(r['id'], r['start_s'], r['method']): r for r in rows if int(r['positive'])}
ranked = [r for r in positives.values() if r['method'] == 'ranker']
failed = [r for r in ranked if float(r['error_deg']) > 10]
candidate_groups = {}
for r in candidates:
    candidate_groups.setdefault((r['id'], r['start_s']), []).append(r)
shared = {}
for method in ['phat', 'ranker']:
    shared[method] = sum(int(r['detected']) and float(positives[(r['id'], r['start_s'], method)]['error_deg']) <= 10 for r in ranked)
report['result_checks'] = {'field_verifier': field_report['status'], 'table_II_values': 'PASS', 'table_III_values': 'PASS',
    'phat_errors_over_10_degrees': sum(float(r['error_deg']) > 10 for r in positives.values() if r['method'] == 'phat'),
    'dccr_errors_over_10_degrees': len(failed),
    'failures_without_candidate_within_10_degrees': sum(min(float(c['error_deg']) for c in candidate_groups[(r['id'], r['start_s'])]) > 10 for r in failed),
    'failures_in_P3_take2': sum(r['id'] == 's3_uav2' for r in failed), 'shared_gate_joint_counts': shared,
    'mean_reduction_before_rounding': summary['methods']['phat']['mean_deg'] - summary['methods']['ranker']['mean_deg']}
assert [report['result_checks'][k] for k in ['phat_errors_over_10_degrees', 'dccr_errors_over_10_degrees', 'failures_without_candidate_within_10_degrees', 'failures_in_P3_take2']] == [91, 36, 34, 33]
assert shared == {'phat': 459, 'ranker': 513}
report['method_limits'] = ['Finite 15-source readable local corpus; exact overlap only, not official similarity or AI detection.',
    'Body mode excludes reference lists, display equations, and table contents; full-text mode includes references and table text but not text inside raster figures/equations.',
    'English 5/8/12 normalized tokens; Chinese 13/20/30 CJK characters with non-CJK removed.',
    'No semantic plagiarism, translated plagiarism, paywalled database or image-only OCR comparison.',
    'No rerun of estimators or new measurements; original source sizes checked, large raw-media hashes not recomputed.']
(OUT / 'audit_metrics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'sources': len(source_manifest), 'readable': len(sources), 'result_checks': report['result_checks'],
    'overlap': {lang: {key: [{k: v for k, v in item.items() if k != 'by_source'} for item in d[key]] for key in ['body_exact_overlap', 'full_text_including_references_exact_overlap']} for lang, d in report['documents'].items()}}, ensure_ascii=False, indent=2))
