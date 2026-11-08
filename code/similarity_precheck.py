"""Local exact-text overlap audit; this is not an iThenticate replacement."""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
import pymupdf as fitz

OUT = ROOT / 'results' / 'similarity_precheck'
WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)


def normalize(text):
    text = unicodedata.normalize('NFKC', text).replace('\u00ad', '')
    # Rejoin PDF line-wrap hyphens; preserve real hyphens within a line.
    return re.sub(r'(?<=[A-Za-z])-\s*\n\s*(?=[a-z])', '', text)


def without_references(text):
    matches = list(re.finditer(r'^\s*(?:[IVX0-9]+[. ]+)?References\s*$', text, re.I | re.M))
    cuts = [m.start() for m in matches if m.start() > len(text) * .25]
    return text[:min(cuts)] if cuts else text


def markdown_blocks(path):
    text = path.read_text(encoding='utf-8')
    text = re.split(r'^## (?:References|参考文献)\s*$', text, flags=re.M)[0]
    text = re.sub(r'\$\$.*?\$\$\s*\(\d+\)', '', text, flags=re.S)
    blocks = []
    for paragraph in re.split(r'\n\s*\n', text):
        if not paragraph.strip() or paragraph.lstrip().startswith('|'):
            continue
        paragraph = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', paragraph)
        paragraph = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', paragraph)
        paragraph = re.sub(r'https?://\S+', '', paragraph)
        blocks.append(normalize(paragraph.strip()))
    return blocks


def extract(path):
    if path.suffix.lower() == '.pdf':
        with fitz.open(path) as doc:
            # Geometric sorting interleaves columns and corrupts hyphenated words.
            text = '\n'.join(page.get_text(sort=False) for page in doc)
    else:
        with ZipFile(path) as doc:
            xml = ET.fromstring(doc.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            text = '\n'.join(''.join(p.itertext()) for p in xml.findall('.//w:p', ns))
    return normalize(text)


def docx_body_blocks(path):
    with ZipFile(path) as doc:
        xml = ET.fromstring(doc.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    result = []
    for p in xml.findall('./w:body/w:p', ns):
        text = ''.join(p.itertext()).strip()
        if text in ['References','参考文献']:
            break
        if not text or re.fullmatch(r'\(\d+\)', text):
            continue
        text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
        result.append(normalize(text))
    return result


def units(text, lang):
    if lang == 'en':
        return WORD.findall(text.casefold())
    # Removing non-CJK characters can bridge English/numbers; this is indicative.
    return re.findall(r'[\u4e00-\u9fff]', text)


def audit(blocks, sources, lang, widths):
    token_blocks = [units(b, lang) for b in blocks]
    offset = 0
    grams = {n: defaultdict(list) for n in widths}
    for bi, tokens in enumerate(token_blocks):
        for n in widths:
            for i in range(len(tokens) - n + 1):
                grams[n][tuple(tokens[i:i+n])].append((offset+i, bi, i))
        offset += len(tokens)
    results = []
    for n in widths:
        union = set()
        by_source = []
        for source in sources:
            # Paragraphs are kept separate for the manuscript; source text is a
            # continuous stream because PDF line breaks rarely mark paragraphs.
            # This is deliberately permissive for short exact matches.
            tokens = units(source['text'], lang)
            matches = set()
            snippets = {}
            for i in range(len(tokens) - n + 1):
                key = tuple(tokens[i:i+n])
                for start, bi, local in grams[n].get(key, []):
                    matches.update(range(start, start+n))
                    snippets[(bi, local)] = ' '.join(token_blocks[bi][local:local+n]) if lang == 'en' else ''.join(token_blocks[bi][local:local+n])
            union.update(matches)
            by_source.append({
                'source': source['path'], 'covered_units': len(matches),
                'coverage_percent': round(len(matches) / offset * 100, 4),
                'match_start_count': len(snippets),
                'examples': list(dict.fromkeys(snippets.values()))[:8],
            })
        by_source.sort(key=lambda s: (-s['covered_units'], s['source']))
        results.append({
            'minimum_consecutive_units': n, 'total_units': offset,
            'union_covered_units': len(union),
            'union_coverage_percent': round(len(union) / offset * 100, 4),
            'maximum_single_source_percent': by_source[0]['coverage_percent'],
            'by_source': by_source,
        })
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    attachment = ROOT / '赛题信息' / '第四届“声华杯”赛题一附件（发布版）-0609更新'
    paths = sorted((ROOT / 'references' / 'papers').glob('*.pdf'))
    paths += sorted((ROOT / 'references' / 'improved').glob('*.pdf'))
    paths += sorted((ROOT / '参考资料').glob('*.pdf'))
    paths += [attachment / name for name in (
        '附件4：试验说明文档.docx', '赛题一：说明文档.docx',
        '赛题一题目-发布版-更新方位角定义.pdf', '附件1：声像派产品手册.pdf',
    )]
    sources, manifest = [], []
    for path in paths:
        text = extract(path)
        rel = path.relative_to(ROOT).as_posix()
        cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
        latin = len(WORD.findall(text))
        readable = len(text.strip()) >= 500
        manifest.append({
            'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'extracted_characters': len(text), 'english_tokens': latin,
            'cjk_characters': cjk, 'included': readable,
            'limitation': None if readable else 'No usable text layer; scanned PDF not OCR-checked.',
        })
        if readable:
            sources.append({'path': rel, 'text': without_references(text)})
    en_path, zh_path = ROOT / 'paper/field_en.md', ROOT / 'paper/field_zh.md'
    en, zh = markdown_blocks(en_path), markdown_blocks(zh_path)
    english = audit(en, sources, 'en', [5, 8, 12])
    docx_blocks = docx_body_blocks(ROOT/'paper/English_Main.docx')
    english_docx = audit(docx_blocks, sources, 'en', [5, 8, 12])
    chinese = audit(zh, sources, 'zh', [13, 20, 30])
    chinese_docx=audit(docx_body_blocks(ROOT/'paper/Chinese_Translation.docx'),sources,'zh',[13,20,30])
    main_pdf = ROOT / 'paper/English_Main.pdf'
    pdf_text = extract(main_pdf)
    pdf_source=re.sub(r'([A-Za-z])_(ij|ii|ref|m|i|j|n|b|q\*)',r'\1\2',' '.join(en))
    md_words = set(units(pdf_source, 'en'))
    pdf_words = set(WORD.findall(pdf_text.casefold()))
    with fitz.open(main_pdf) as document:
        # Preserve genuine compound-word hyphens as well as joined wrap hyphens.
        pdf_words.update(WORD.findall('\n'.join(p.get_text() for p in document).casefold()))
    missing = sorted(md_words - pdf_words)
    with fitz.open(main_pdf) as doc:
        pdf_pages = len(doc)
        doc[0].get_pixmap(matrix=fitz.Matrix(1, 1)).save(OUT / 'english_first_page.png')
    output = {
        'checked_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'status': 'LOCAL_PRECHECK_ONLY_NO_ITHENTICATE_REPORT',
        'submission_limits': {'overall_percent': 24, 'single_source_percent': 3},
        'method': {
            'english': 'Case-insensitive exact consecutive word/token matching; punctuation normalized; 5/8/12-token sensitivity.',
            'chinese': 'Exact CJK character runs after removing non-CJK characters; 13/20/30-character sensitivity; indicative only.',
            'denominator': 'Markdown body before References, including headings/captions; excludes bibliography, display equations and table rows.',
            'docx_crosscheck': 'Independent audit of actual English_Main.docx body paragraphs; excludes tables, reference list and empty equation-image paragraphs.',
            'aggregation': 'Union of covered manuscript token positions; each position counted once; single-source coverage uses same denominator.',
            'exclusions': 'Previous drafts, templates, translations of this manuscript, internal research notes, and internal generated reports are not external sources.',
            'limitations': 'Finite local corpus, text extraction errors, no semantic/translation/paid-database detection, no inference of iThenticate percentage or submission compliance.',
        },
        'manuscripts': [
            {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in [en_path, zh_path, main_pdf, ROOT/'paper/English_Main.docx', ROOT/'paper/Chinese_Translation.pdf',ROOT/'paper/Chinese_Translation.docx']
        ],
        'pdf_crosscheck': {'pages': pdf_pages, 'unique_markdown_tokens': len(md_words), 'missing_from_pdf': missing},
        'sources': manifest, 'english': english, 'english_docx_crosscheck': english_docx, 'chinese_translation': chinese,
        'chinese_docx_crosscheck':chinese_docx,
        'missing_cited_full_text': [
            '[2] Knapp and Carter 1976: local PDF is image-only; no OCR comparison.',
            '[3] DiBiase et al. 2001: no local full text.',
            '[6] Donohue et al. 2007: no local full text.',
            '[8] Uluskan 2024: no local full text.',
        ],
    }
    (OUT/'local_metrics.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({
        'included_sources': sum(s['included'] for s in manifest), 'total_sources': len(manifest),
        'pdf_crosscheck': output['pdf_crosscheck'],
        'english': [{k: v for k, v in r.items() if k != 'by_source'} for r in english],
        'english_docx_crosscheck': [{k: v for k, v in r.items() if k != 'by_source'} for r in english_docx],
        'chinese_translation': [{k: v for k, v in r.items() if k != 'by_source'} for r in chinese],
        'english_matches': english[1]['by_source'][:4],
        'chinese_matches': chinese[0]['by_source'][:3],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
