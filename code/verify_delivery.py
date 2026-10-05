"""Check manuscript/result consistency and PDF geometry; optionally render every page."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from build_papers import ROOT, PAPERS, blocks, self_test
import fitz


def numbers(value):
    return re.findall(r'-?\d+(?:\.\d+)?', value)


def main(render=False):
    self_test()
    summary = json.loads((ROOT / 'results/improved/summary.json').read_text(encoding='utf-8'))
    documents = {}
    tables = {}
    equations = {}
    figures = {}
    prohibited = r'用户|赛题|主办方|user.provided|competition|organizer|\bTODO\b|\{\{'
    report = {'passed': True, 'checks': [], 'documents': {}}
    qa = ROOT / 'results/document_qa'
    for lang in ('en', 'zh'):
        text = (PAPERS / f'manuscript_{lang}.md').read_text(encoding='utf-8')
        assert not re.search(prohibited, text, re.I), lang
        documents[lang] = text
        parsed = list(blocks(text))
        equations[lang] = [v for k, v in parsed if k == 'math']
        tables[lang] = [v for k, v in parsed if k == 'table']
        figures[lang] = [v[1] for k, v in parsed if k == 'figure']
        assert len(equations[lang]) == 16 and len(tables[lang]) == 6 and len(figures[lang]) == 3
        assert [len(t) for t in tables[lang]] == [6, 7, 5, 4, 9, 4]
        assert [n for _, n in equations[lang]] == [str(i) for i in range(1, 17)]
        assert all((PAPERS / path).is_file() for path in figures[lang])
        body, bibliography = text.split('## ' + ('References' if lang == 'en' else '参考文献'))
        assert re.findall(r'^\[(\d+)\]', bibliography, re.M) == [str(i) for i in range(1, 22)]
        cited = {int(n) for group in re.findall(r'\[([\d, ]+)\]', body)
                 for n in group.replace(' ', '').split(',')}
        assert cited == set(range(1, 22)), cited
        # Numeric claims come from executed results, never desired performance.
        for row, method in zip(tables[lang][1][1:], ('phat', 'coherence', 'harmonic', 'combined', 'no_null', 'proposed')):
            result = summary['localization'][method]['overall']
            expected = [f"{result[key]:.2f}" for key in ('mean_deg', 'median_deg', 'p95_deg')]
            expected.append(f"{100 * result['within10_rate']:.1f}")
            assert row[1:] == expected, (lang, method, row, expected)
        for row, scene in zip(tables[lang][2][1:], ('sensor_noise', 'wind', 'directional', 'engine')):
            assert row[1:] == [f"{summary['localization'][method]['by_scene'][scene]['mean_deg']:.2f}"
                               for method in ('phat', 'combined', 'no_null', 'proposed')]
        for row, name in zip(tables[lang][3][1:], ('harmonic_coherence', 'spectral', 'proposed')):
            result = summary['detection'][name]
            assert row[1:] == [f"{100 * result[key]:.2f}" for key in ('tpr', 'fpr', 'balanced_accuracy')] + [f"{result['auc']:.3f}"]
        for row, group in zip(tables[lang][4][1:], summary['detection']['proposed']['fpr_by_group']):
            assert row[1:] == [f"{100 * summary['detection'][name]['fpr_by_group'][group]:.2f}"
                               for name in ('harmonic_coherence', 'spectral', 'proposed')]
        for row, name in zip(tables[lang][5][1:], ('harmonic_coherence+phat', 'proposed+phat', 'proposed+proposed')):
            result = summary['joint'][name]
            assert row[1:] == [f"{100 * result['success_rate']:.2f}",
                               f"[{100 * result['ci95'][0]:.2f}, {100 * result['ci95'][1]:.2f}]"]
        pdf_path = PAPERS / f'manuscript_{lang}.pdf'
        with fitz.open(pdf_path) as pdf:
            assert len(pdf) >= 4
            page_details = []
            for index, page in enumerate(pdf):
                page_text = page.get_text()
                assert '\ufffd' not in page_text and not re.search(prohibited, page_text, re.I)
                assert len(page_text.strip()) > 100, (lang, index + 1, 'near-empty page')
                for block in page.get_text('dict')['blocks']:
                    x0, y0, x1, y1 = block['bbox']
                    assert 20 <= x0 < x1 <= page.rect.width - 20, (lang, index + 1, block['bbox'])
                    assert 15 <= y0 < y1 <= page.rect.height - 10, (lang, index + 1, block['bbox'])
                page_details.append({'page': index + 1, 'text_characters': len(page_text)})
                if render:
                    folder = qa / 'improved'
                    folder.mkdir(parents=True, exist_ok=True)
                    page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(folder / f'{lang}-{index + 1:02}.png')
            report['documents'][lang] = {'pages': len(pdf), 'page_details': page_details,
                                         'pdf_sha256': hashlib.sha256(pdf_path.read_bytes()).hexdigest()}
    assert equations['en'] == equations['zh'] and figures['en'] == figures['zh']
    for english, chinese in zip(tables['en'], tables['zh']):
        assert len(english) == len(chinese)
        for en_row, zh_row in zip(english, chinese):
            assert numbers(' '.join(en_row)) == numbers(' '.join(zh_row)), (en_row, zh_row)
    report['checks'] = ['16 identical numbered equations; six bilingual tables with identical numbers',
                        'three existing figure files and all 21 references cited in each manuscript',
                        'localization, detection, eight negative-group FPRs and joint-success tables match frozen fresh results',
                        'no task/competition language, unresolved placeholders or replacement characters',
                        'both PDFs at least four pages; all text/image boxes within printable page boundaries']
    qa.mkdir(parents=True, exist_ok=True)
    (qa / 'delivery_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    main(parser.parse_args().render)
