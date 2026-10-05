"""Build the two local PDF papers from their editable Markdown sources.

Use --assets with a Python that has matplotlib, then run normally with
reportlab and Pillow. No remote typesetting service is used.
"""
from pathlib import Path
import argparse
import hashlib
import html
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if sys.version_info[:2] == (3, 12) and (ROOT / '.python-packages').exists():
    sys.path.insert(0, str(ROOT / '.python-packages'))
PAPERS = ROOT / 'paper'
CACHE = ROOT / 'results' / 'document_qa' / 'equations'


def math_path(expression):
    return CACHE / (hashlib.sha256(expression.encode()).hexdigest()[:20] + '.png')


def blocks(text):
    """Only the documented manuscript subset of Markdown is accepted."""
    chunks = re.split(r'\n\s*\n', text.strip())
    for chunk in chunks:
        if chunk.startswith('<!--'):
            continue
        if chunk.startswith('$$'):
            match = re.fullmatch(r'\$\$\s*(.*?)\s*\$\$(?:\s*\((\d+)\))?', chunk, re.S)
            if not match:
                raise ValueError('Malformed equation: ' + chunk)
            yield 'math', (match[1].strip(), match[2] or '')
        elif chunk.startswith('|'):
            rows = [[c.strip() for c in line.strip().strip('|').split('|')]
                    for line in chunk.splitlines() if not re.match(r'^\|[\s:|\-]+\|$', line)]
            assert rows and all(len(r) == len(rows[0]) for r in rows), 'Ragged table'
            yield 'table', rows
        elif chunk.startswith('!['):
            match = re.fullmatch(r'!\[(.*?)\]\((.*?)\)', chunk, re.S)
            if not match:
                raise ValueError('Malformed figure: ' + chunk)
            yield 'figure', match.groups()
        elif chunk.startswith('#'):
            match = re.match(r'^(#{1,4})\s+(.+)$', chunk)
            if not match:
                raise ValueError('Malformed heading: ' + chunk)
            yield 'heading', (len(match[1]), match[2])
        elif chunk.startswith('- '):
            yield 'list', [line[2:] for line in chunk.splitlines()]
        else:
            yield 'paragraph', ' '.join(chunk.splitlines())


def render_assets():
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.mathtext import math_to_image
    from matplotlib.font_manager import FontProperties
    CACHE.mkdir(parents=True, exist_ok=True)
    expressions = set()
    for path in PAPERS.glob('manuscript_*.md'):
        for kind, item in blocks(path.read_text(encoding='utf-8')):
            if kind == 'math':
                expressions.add(item[0])
    for expression in sorted(expressions):
        math_to_image('$' + expression + '$', str(math_path(expression)),
                      prop=FontProperties(size=11), dpi=300, format='png', color='black')
    print(f'Rendered {len(expressions)} distinct equations.')
    import json
    import matplotlib.pyplot as plt
    from summarize_experiment import read_csv, roc
    summary = json.loads((ROOT / 'results/improved/summary.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 8})
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(3.45, 3.5))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')
    def box(x, y, width, label, shade):
        ax.add_patch(FancyBboxPatch((x, y), width, .13, boxstyle='round,pad=0.01',
                                   edgecolor='#24384a', facecolor=shade, linewidth=.8))
        ax.text(x + width / 2, y + .065, label, ha='center', va='center', fontsize=8)
    def arrow(start, finish):
        ax.annotate('', xy=finish, xytext=start, arrowprops={'arrowstyle': '->', 'lw': .85, 'color': '#24384a'})
    box(.12, .85, .76, 'Eight channels / 200 ms / 8 kHz\nMean removal and normalization', '#eeeeee')
    for x in (.02, .54):
        arrow((.5, .84), (x + .22, .76))
    for y, left, right in [(.62, 'Global spectral +\nspatial features (87)', 'Five acoustic maps\nAt most 11 candidates'),
                            (.40, 'Kernel ridge\npresence score', 'Ordinary and\nsuppressed beams'),
                            (.18, 'Frozen threshold\nTarget decision', 'Candidate features\nand quality ranking')]:
        box(.02, y, .44, left, '#f3e7d9')
        box(.54, y, .44, right, '#e2eef5')
    for x in (.24, .76):
        arrow((x, .61), (x, .54))
        arrow((x, .39), (x, .32))
        arrow((x, .17), (.5, .08))
    ax.text(.5, .035, 'Detection + selected azimuth / elevation', ha='center', fontsize=8)
    fig.subplots_adjust(left=.02, right=.98, top=.99, bottom=.01)
    fig.savefig(ROOT / 'figures/improved_pipeline.png', dpi=320)
    fig.savefig(ROOT / 'figures/improved_pipeline.pdf')
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(3.45, 2.65), constrained_layout=True)
    for method, label in [('phat', 'PHAT'), ('combined', 'Harmonic + coherence'),
                          ('no_null', 'Without suppression'), ('proposed', 'SCCR')]:
        rows = summary['localization'][method]['by_snr']
        snrs = sorted(int(k) for k in rows)
        ax.plot(snrs, [rows[str(k)]['mean_deg'] for k in snrs], marker='o', markersize=3,
                label=label)
    ax.set(xlabel='Mixture SNR (dB)', ylabel='Mean spherical error (deg)', ylim=(0, None))
    ax.set_xticks(snrs)
    ax.grid(alpha=.22)
    ax.legend(loc='upper right', framealpha=.92)
    fig.savefig(ROOT / 'figures/improved_localization.png', dpi=320)
    fig.savefig(ROOT / 'figures/improved_localization.pdf')
    plt.close(fig)
    rows = read_csv(ROOT / 'results/improved/detection_frames.csv')
    fig, ax = plt.subplots(figsize=(3.45, 2.65), constrained_layout=True)
    for name, label in [('harmonic_coherence', 'Harmonic-coherence'), ('spectral', 'Spectral'), ('proposed', 'Spectral-spatial')]:
        subset = [r for r in rows if r['detector'] == name]
        area, points = roc(subset)
        ax.plot([p['fpr'] for p in points], [p['tpr'] for p in points],
                label=f'{label} (AUC {area:.3f})')
        d = summary['detection'][name]
        ax.scatter([d['fpr']], [d['tpr']], marker='x', c='black', s=25, zorder=4)
    ax.plot([0, 1], [0, 1], ':', color='0.6', linewidth=.8)
    ax.set(xlabel='False-alarm rate', ylabel='Recall', xlim=(0, 1), ylim=(0, 1))
    ax.legend(loc='lower right')
    ax.grid(alpha=.2)
    fig.savefig(ROOT / 'figures/improved_roc.png', dpi=320)
    fig.savefig(ROOT / 'figures/improved_roc.pdf')
    plt.close(fig)


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',
                  r'<link href="\2" color="#17293a">\1</link>', text)
    return text


def build(language):
    from PIL import Image as PILImage
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                  Spacer, Image, Table, TableStyle, KeepTogether,
                                  NextPageTemplate, FrameBreak)
    fonts = Path('C:/Windows/Fonts')
    # ponytail: local Windows font paths; pass portable font files if moving platforms.
    for name, filename in [('PaperRoman', 'times.ttf'), ('PaperBold', 'timesbd.ttf'),
                           ('PaperItalic', 'timesi.ttf'), ('PaperChinese', 'simsun.ttc')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily('PaperRoman', normal='PaperRoman', bold='PaperBold',
                                  italic='PaperItalic', boldItalic='PaperBold')
    pdfmetrics.registerFontFamily('PaperChinese', normal='PaperChinese', bold='PaperChinese',
                                  italic='PaperChinese', boldItalic='PaperChinese')
    zh = language == 'zh'
    font = 'PaperChinese' if zh else 'PaperRoman'
    bold = 'PaperChinese' if zh else 'PaperBold'
    width, height = A4
    margin = 48 if zh else 40.6
    gap = 16
    usable = width - 2 * margin
    col = usable if zh else (usable - gap) / 2
    fontsize = 10.2 if zh else 10
    common = dict(fontName=font, fontSize=fontsize, leading=14.3 if zh else 11.5,
                  spaceAfter=4.5, splitLongWords=True, allowWidows=0, allowOrphans=0,
                  wordWrap='CJK' if zh else None)
    styles = {
        'body': ParagraphStyle('body', alignment=TA_JUSTIFY, **common),
        'title': ParagraphStyle('title', fontName=bold, fontSize=19 if zh else 21,
                                leading=25, alignment=TA_CENTER, spaceAfter=14),
        'h2': ParagraphStyle('h2', fontName=bold, fontSize=11 if zh else 10.8,
                             leading=14, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName=bold, fontSize=10.2,
                             leading=13.5, spaceBefore=7, spaceAfter=4, keepWithNext=True),
        'small': ParagraphStyle('small', fontName=font, fontSize=8.1, leading=9.4,
                               spaceAfter=3, wordWrap='CJK' if zh else None),
        'caption': ParagraphStyle('caption', fontName=font, fontSize=8.5, leading=10.5,
                                 spaceAfter=7, alignment=TA_LEFT,
                                 wordWrap='CJK' if zh else None),
        'cell': ParagraphStyle('cell', fontName=font, fontSize=8.0 if zh else 7.4,
                              leading=10.3 if zh else 9.0, wordWrap='CJK' if zh else None),
    }
    document = BaseDocTemplate(str(PAPERS / f'manuscript_{language}.pdf'), pagesize=A4,
                               leftMargin=margin, rightMargin=margin,
                               topMargin=35, bottomMargin=39,
                               title=(PAPERS / f'manuscript_{language}.md').read_text(encoding='utf-8').splitlines()[0][2:],
                               author='', subject='Reproducible simulation study')

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor('#404040'))
        canvas.drawCentredString(width / 2, 22, str(doc.page))
        canvas.restoreState()

    frame_height = height - 76
    if zh:
        frames = [Frame(margin, 39, usable, frame_height, id='main',
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
        document.addPageTemplates(PageTemplate(id='body', frames=frames, onPage=footer))
    else:
        title_height = 85
        first_frames = [Frame(margin, height - 35 - title_height, usable, title_height,
                              id='title', leftPadding=0, rightPadding=0,
                              topPadding=0, bottomPadding=0)]
        for i in range(2):
            first_frames.append(Frame(margin + i * (col + gap), 39, col,
                                      frame_height - title_height - 3, id=f'first{i}',
                                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0))
        rest = [Frame(margin + i * (col + gap), 39, col, frame_height, id=f'col{i}',
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
                for i in range(2)]
        document.addPageTemplates([PageTemplate(id='first', frames=first_frames, onPage=footer),
                                   PageTemplate(id='body', frames=rest, onPage=footer)])
    story = []
    in_references = False
    for kind, item in blocks((PAPERS / f'manuscript_{language}.md').read_text(encoding='utf-8')):
        if kind == 'heading':
            level, title = item
            if level == 1:
                story.append(Paragraph(inline(title), styles['title']))
                if not zh:
                    story.extend([NextPageTemplate('body'), FrameBreak()])
            else:
                if title in ('References', '参考文献'):
                    in_references = True
                story.append(Paragraph(inline(title), styles['h2' if level == 2 else 'h3']))
        elif kind == 'paragraph':
            st = styles['small' if in_references else 'body']
            if re.match(r'^(Table [IVX\d]+\.|表\s*[IVX\d]+\.)', item):
                st = styles['caption']
                p = Paragraph(inline(item), st)
                p.keepWithNext = True
                story.append(p)
            else:
                story.append(Paragraph(inline(item), st))
        elif kind == 'list':
            for line in item:
                story.append(Paragraph('• ' + inline(line), styles['body']))
        elif kind == 'math':
            expression, number = item
            path = math_path(expression)
            if not path.exists():
                raise FileNotFoundError(f'Run --assets first: {expression}')
            w, h = PILImage.open(path).size
            draw_w = min(w * 72 / 300, col - 24)
            eq = Image(str(path), width=draw_w, height=draw_w * h / w)
            table = Table([[eq, Paragraph('(' + number + ')' if number else '', styles['small'])]],
                          colWidths=[col - 22, 22])
            table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                       ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                                       ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                       ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                       ('TOPPADDING', (0, 0), (-1, -1), 3),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
            story.append(table)
        elif kind == 'table':
            cells = [[Paragraph(inline(c), styles['cell']) for c in row] for row in item]
            n = len(item[0])
            widths = [col / n] * n
            if n >= 3:
                widths = [col * .29] + [col * .71 / (n - 1)] * (n - 1)
            table = Table(cells, colWidths=widths, repeatRows=1, hAlign='CENTER')
            table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                       ('LINEABOVE', (0, 0), (-1, 0), .7, colors.black),
                                       ('LINEBELOW', (0, 0), (-1, 0), .4, colors.black),
                                       ('LINEBELOW', (0, -1), (-1, -1), .7, colors.black),
                                       ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
                                       ('LEFTPADDING', (0, 0), (-1, -1), 3),
                                       ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                                       ('TOPPADDING', (0, 0), (-1, -1), 4),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
            story.extend([table, Spacer(1, 7)])
        elif kind == 'figure':
            caption, relative = item
            path = (PAPERS / relative).resolve()
            path.relative_to(ROOT)
            w, h = PILImage.open(path).size
            draw_w = min(col, 430)
            figure = Image(str(path), width=draw_w, height=draw_w * h / w)
            story.append(KeepTogether([figure, Spacer(1, 4),
                                        Paragraph(inline(caption), styles['caption'])]))
    document.build(story)
    print(PAPERS / f'manuscript_{language}.pdf')


def self_test():
    got = list(blocks('# Title\n\nText.\n\n$$x^2$$ (1)\n\n| A | B |\n|---|---|\n| 1 | 2 |'))
    assert [k for k, _ in got] == ['heading', 'paragraph', 'math', 'table']
    assert got[2][1] == ('x^2', '1') and len(got[3][1]) == 2
    assert inline('a < b **bold**') == 'a &lt; b <b>bold</b>'
    print('Manuscript parser self-test passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.assets:
        render_assets()
    else:
        for lang in ('en', 'zh'):
            build(lang)
