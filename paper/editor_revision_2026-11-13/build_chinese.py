"""Build the Chinese companion from the reviewed English Word manuscript."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import re
import unicodedata

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.table import Table

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE / 'DCCR_Editor_Revised.docx'
assert sha256(SOURCE.read_bytes()).hexdigest() == '20ab9fb1262a6a2067852598e061b62cf475cdac5986a6088ebf4da8a36eb098'
translations = json.loads((HERE / 'translation_zh.json').read_text(encoding='utf-8'))
en = Document(SOURCE)
zh = Document(SOURCE)


def write_text(p, text):
    saved = deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
    p.clear()
    for value in re.split(r'([A-Za-z]_(?:ij|m|n|b|q\*))', text):
        match = re.fullmatch(r'([A-Za-z])_(ij|m|n|b|q\*)', value)
        parts = [(match[1], False), (match[2], True)] if match else [(value, False)]
        for content, subscript in parts:
            r = p.add_run(content)
            if saved is not None:
                r._r.insert(0, deepcopy(saved))
            r.font.name = 'Times New Roman'
            r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'SimSun')
            r.font.subscript = subscript
            r.font.color.rgb = RGBColor(0, 0, 0)


for index, text in translations.items():
    p = zh.paragraphs[int(index)]
    assert p.text.strip() and not p._p.xpath('.//w:pict | .//w:drawing')
    for old, new in {'rₘ':'r_m','aₘ':'a_m','vₘ':'v_m','Xₘ':'X_m','Fᵦ':'F_b','zₙ':'z_n','yₙ':'y_n','Cᵢⱼ':'C_ij','Qᵢⱼ':'Q_ij'}.items():
        text = text.replace(old, new)
    write_text(p, text)

# Explicit coverage prevents silently leaving an untranslated body paragraph.
untranslated = {i for i,p in enumerate(en.paragraphs) if p.text.strip() and i < 88 and i not in [7,12]} - {int(k) for k in translations}
assert not untranslated, untranslated

table_text = {
    'Group':'分组', 'Range':'距离', 'Azimuth\ntake 1 / take 2':'方位角\n录音1 / 录音2', 'Elev.':'俯仰角', 'Role':'用途',
    'Development':'方法开发', 'Held-out evaluation':'保留评价', 'Method':'方法', 'Mean °':'均值\n°',
    'Median\n°':'中位数\n°', '95th pct.\n°':'95分位\n°', 'Coherence PHAT':'相干性加权PHAT',
    'Reference subtraction':'背景互谱扣除', 'DCCR without hard negatives':'DCCR无困难负例',
    'TP / 600':'检出数\n/ 600', 'FP / 200':'虚警数\n/ 200', 'TPR %':'检出率\n%',
    'FPR %':'虚警率\n%', 'Joint ≤10° %':'联合\n≤10° %'
}
for t in zh.tables:
    if len(t.rows) == 1:
        continue
    for row in t.rows:
        for cell in row.cells:
            if cell.text in table_text:
                write_text(cell.paragraphs[0], table_text[cell.text])

for name in ['Normal','Body Text','Abstract','key words','Heading 1','Heading 2','Heading 5','Author','Affiliation','table head','references']:
    style = zh.styles[name]
    style._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'SimSun')
for p in zh.paragraphs:
    if p.style.name == 'Body Text' and not p.text.startswith('图'):
        p.paragraph_format.line_spacing = 1.05
    if p.style.name == 'Abstract':
        for r in p.runs:
            r.italic = False
    if p.style.name in ['Heading 1','Heading 2','Heading 5']:
        for r in p.runs:
            r.bold = True
            r.italic = False

# The existing localized plots share the English plots' canvas and panel positions.
for rid, filename in [('rId13','geometry_weights_zh.png'),('rId18','recordings_zh.png')]:
    assert rid in zh.part.related_parts
    zh.part.related_parts[rid]._blob = (ROOT/'figures/field'/filename).read_bytes()
for shape in zh._element.xpath('.//*[local-name()="shape"]'):
    alt = shape.get('alt', '')
    if alt.startswith('Fig. 1.'):
        shape.set('alt', translations['43'])
    elif alt.startswith('Fig. 2.'):
        shape.set('alt', translations['77'])

OUTPUT = HERE / 'DCCR_Chinese_Revised.docx'
zh.save(OUTPUT)


def numbers(text):
    return Counter(re.findall(r'\d+(?:\.\d+)*', unicodedata.normalize('NFKC', text)))


for index in translations:
    i = int(index)
    if i in [3,8]:
        continue
    english = en.paragraphs[i].text.replace('unit-magnitude', '1-magnitude').replace('unit magnitude', '1 magnitude').replace('unity', '1').replace(' May ', ' 5 ')
    assert numbers(english) == numbers(zh.paragraphs[i].text), (i,en.paragraphs[i].text,zh.paragraphs[i].text)
for i in range(88,100):
    assert en.paragraphs[i].text == zh.paragraphs[i].text
for a,b in zip(en.tables,zh.tables):
    if len(a.rows)==1:
        assert a._tbl.xml == b._tbl.xml
    else:
        for ar,br in zip(a.rows,b.rows):
            for ac,bc in zip(ar.cells,br.cells):
                assert numbers(ac.text)==numbers(bc.text), (ac.text,bc.text)
for i in [7,12]:
    assert en.paragraphs[i].text==zh.paragraphs[i].text
assert 'U25A20427' in zh.paragraphs[86].text

# Export readable companions without claiming that Markdown controls Word layout.
equations = {n:expression for expression,n in re.findall(r'\$\$\s*(.*?)\s*\$\$\s*\((\d+)\)', (ROOT/'paper/field_en.md').read_text(encoding='utf-8'), re.S)}
assert len(equations)==9
for lang,document in [('en',en),('zh',zh)]:
    lines=[]
    seen_figures=set()
    for node in document._element.body:
        if node.tag==qn('w:p'):
            p=Paragraph(node,document._body)
            for image in node.xpath('.//*[local-name()="imagedata"]'):
                rid=image.get(qn('r:id'))
                if rid in ['rId13','rId18'] and rid not in seen_figures:
                    seen_figures.add(rid)
                    name='geometry_weights' if rid=='rId13' else 'recordings'
                    lines.append(f'![{name}](../../figures/field/{name}_{lang}.png)')
            if not p.text.strip():
                continue
            prefix={'paper title':'# ','Heading 1':'## ','Heading 2':'### ','Heading 5':'## '}.get(p.style.name,'')
            lines.append(prefix+p.text.strip())
        elif node.tag==qn('w:tbl'):
            table=Table(node,document._body)
            if len(table.rows)==1:
                n=table.cell(0,1).text.strip('()')
                lines.append(f'$$ {equations[n]} $$ ({n})')
            else:
                rows=['| '+' | '.join(c.text.replace('\n',' ') for c in row.cells)+' |' for row in table.rows]
                rows.insert(1,'| '+' | '.join('---' for _ in table.columns)+' |')
                lines.append('\n'.join(rows))
    (HERE/f'manuscript_{lang}.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'chinese_docx':str(OUTPUT),'translated_paragraphs':len(translations),'checks':'passed','equations':9,'data_tables':3,'figures':2,'references':12},ensure_ascii=False))
