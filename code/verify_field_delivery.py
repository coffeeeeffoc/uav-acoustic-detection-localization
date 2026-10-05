"""Verify the field manuscript package without rerunning acoustic inference."""
from pathlib import Path
import sys, re, json, hashlib, zipfile, ast
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.python-packages'))
import fitz

QA = ROOT / 'results/document_qa/field'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tables(text):
    groups = []
    for match in re.finditer(r'(?:^\|[^\n]+\n)+', text, re.M):
        rows = [x.strip().strip('|').split('|') for x in match.group().splitlines()]
        groups.append([[re.findall(r'[+−-]?\d+(?:\.\d+)?', c) for c in r[1:]] for r in rows[2:]])
    return groups

def main():
    en = (ROOT / 'paper/field_en.md').read_text(encoding='utf-8')
    zh = (ROOT / 'paper/field_zh.md').read_text(encoding='utf-8')
    assert not re.search(r'[\u4e00-\u9fff]', en)
    forbidden = ['用户提供', '用户要求', '赛题', '参赛', '声华杯',
                 'user-provided', 'user provided', 'user requirements',
                 'competition requirements', 'contest requirements']
    equations = []
    for text in [en, zh]:
        assert not re.search(r'\{\{[A-Za-z][A-Za-z0-9_]*\}\}', text)
        for term in forbidden:
            assert term.casefold() not in text.casefold(), term
        eq = re.findall(r'^\$\$(.*?)\$\$\s*\((\d+)\)', text, re.M)
        assert [int(n) for _, n in eq] == list(range(1, 10))
        equations.append(eq)
        refs = re.findall(r'^\[(\d+)\]', text, re.M)
        assert list(map(int, refs)) == list(range(1, 13))
        body = text[:re.search(r'^\[1\]', text, re.M).start()]
        seen = list(dict.fromkeys(map(int, re.findall(r'\[(\d+)\]', body))))
        assert seen == list(range(1, 13)), seen
        assert len(re.findall(r'^!\[', text, re.M)) == 3
    assert equations[0] == equations[1]
    assert len(tables(en)) == len(tables(zh)) == 4
    assert tables(en) == tables(zh)
    summary = json.loads((ROOT / 'results/field/summary.json').read_text())
    for method in ['phat', 'ranker']:
        value = f"{summary['methods'][method]['mean_deg']:.2f}"
        assert value in en and value in zh
    for metric in ['tpr', 'fpr', 'joint10']:
        value = f"{100*summary['methods']['ranker'][metric]:.1f}"
        assert value in en and value in zh
    doc_reports = []
    manifest = {}
    for name, lang, pages in [('English_Main', 'en', 10), ('Chinese_Translation', 'zh', 9)]:
        docx = ROOT / 'paper' / (name + '.docx')
        pdf = ROOT / 'paper' / (name + '.pdf')
        assert sha(pdf) == sha(QA / lang / (name + '.pdf'))
        with zipfile.ZipFile(docx) as archive:
            xml = ET.fromstring(archive.read('word/document.xml'))
            inline_images = len(xml.findall('.//wp:inline', NS))
            table_count = len(xml.findall('.//w:tbl', NS))
            assert inline_images == 12 and table_count == 13
            document_text = ' '.join(t.text or '' for t in xml.findall('.//w:t', NS))
            for term in forbidden:
                assert term.casefold() not in document_text.casefold()
        with fitz.open(pdf) as document:
            assert len(document) == pages
            content = '\n'.join(p.get_text() for p in document)
            assert '\ufffd' not in content
            for value in ['14.78', '6.97', '85.7', '1.5', '54.16', '414.9', '588.7']:
                assert value in content, (name, value)
            for n in range(1, 13):
                assert '[' + str(n) + ']' in content
            fonts = {}
            image_placements = 0
            for page in document:
                assert len(page.get_text().strip()) > 100, (name, page.number, 'empty page')
                image_placements += len(page.get_image_info())
                for block in page.get_text('dict')['blocks']:
                    x0, y0, x1, y1 = block['bbox']
                    assert min(x0, y0) >= -.5 and x1 <= page.rect.width+.5 and y1 <= page.rect.height+.5, (name, page.number, block['bbox'])
                for font in page.get_fonts(full=True):
                    fonts[font[3]] = bool(document.extract_font(font[0])[3])
            assert image_placements == 12
            assert all(fonts.values()), fonts
        doc_reports.append(dict(language=lang, docx=docx.relative_to(ROOT).as_posix(),
            pdf=pdf.relative_to(ROOT).as_posix(), pages=pages, figures=3, equations=9,
            data_tables=4, references=12, pdf_images=image_placements, fonts_embedded=fonts))
        for path in [docx, pdf]:
            manifest[path.relative_to(ROOT).as_posix()] = sha(path)
    visual = json.loads((QA / 'visual_review.json').read_text(encoding='utf-8'))
    assert visual['status'] == 'PASS'
    for path, digest in visual['reviewed_files'].items():
        assert sha(ROOT/path) == digest, ('Visual review is stale', path)
    for pattern in ['code/*field*.py', 'paper/field*.md', 'paper/field_citation_map.json',
                    'figures/field/*', 'code/requirements-field.txt']:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file():
                manifest[path.relative_to(ROOT).as_posix()] = sha(path)
                if path.suffix == '.py': ast.parse(path.read_text(encoding='utf-8'))
    for relative in ['START_HERE.md', 'code/EXPERIMENT_README.md', 'archive/README.md']:
        path = ROOT / relative
        manifest[relative] = sha(path)
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if not re.match(r'[a-z]+://', link):
                target = (path.parent / link.split('#')[0]).resolve()
                assert target.exists() or target == (QA/'delivery_verification.json').resolve(), (relative, link)
    frozen = json.loads((ROOT/'results/field/frozen_config.json').read_text())
    for path, digest in frozen['files'].items(): assert sha(ROOT/path) == digest, path
    artifacts = json.loads((ROOT/'results/field/artifact_manifest.json').read_text())
    for path, digest in artifacts.items(): assert sha(ROOT/'results/field'/path) == digest, path
    report = dict(status='PASS',documents=doc_reports, bilingual_tables_identical=True,
        bilingual_equations_identical=True, citation_order_verified=True,
        task_response_language_absent=True, frozen_files_unchanged=len(frozen['files']),
        evaluation_artifacts_unchanged=len(artifacts),visual_review='visual_review.json',
        limitations=['No external similarity service used', 'No journal acceptance or hardware real-time claim'])
    (QA / 'delivery_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT/'results/field/paper_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
