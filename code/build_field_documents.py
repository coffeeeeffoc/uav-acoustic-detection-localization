"""Build both editable manuscripts with the bundled python-docx runtime.

Scientific figures/equation rasters are generated separately by finalize_field_paper.py.
The two PDFs are exported from these DOCX files with the packaged document renderer.
"""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,re
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image
from docx.enum.section import WD_SECTION_START
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'results/document_qa/field'
TEMPLATE=ROOT/'results/document_qa/template_revision/wordtemplates.docx'

def blocks(text):
    for chunk in re.split(r'\n\s*\n',text.strip()):
        if chunk.startswith('$$'):
            m=re.fullmatch(r'\$\$\s*(.*?)\s*\$\$\s*\((\d+)\)',chunk,re.S)
            if not m:raise ValueError(chunk)
            yield 'math',m.groups()
        elif chunk.startswith('|'):
            rows=[[c.strip() for c in line.strip('|').split('|')] for line in chunk.splitlines() if not re.match(r'^\|[\s:|\-]+\|$',line)]
            assert all(len(r)==len(rows[0]) for r in rows)
            yield 'table',rows
        elif chunk.startswith('!['):
            m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',chunk,re.S);assert m
            yield 'figure',m.groups()
        elif chunk.startswith('#'):
            m=re.fullmatch(r'(#{1,3}) (.+)',chunk);assert m
            yield 'heading',(len(m[1]),m[2])
        else:yield 'paragraph',' '.join(chunk.splitlines())

def font(run,zh=False,size=None,bold=False):
    run.font.name='Times New Roman';run.font.color.rgb=RGBColor(0,0,0)
    if size:run.font.size=Pt(size)
    if bold:run.bold=True
    rf=run._element.get_or_add_rPr().get_or_add_rFonts()
    rf.set(qn('w:eastAsia'),'SimSun' if zh else 'Times New Roman')

def inline(p,text,zh):
    pattern=r'(\*\*.+?\*\*|\[[^\]]+\]\(https?://[^)]+\))'
    for t in re.split(pattern,text):
        if not t:continue
        if t.startswith('**'):
            r=p.add_run(t[2:-2]);font(r,zh,bold=True)
        elif re.fullmatch(r'\[[^\]]+\]\(https?://[^)]+\)',t):
            m=re.match(r'\[(.*?)\]\((.*?)\)',t)
            link=OxmlElement('w:hyperlink');link.set(qn('r:id'),p.part.relate_to(m[2],RT.HYPERLINK,is_external=True))
            r=OxmlElement('w:r');pr=OxmlElement('w:rPr')
            c=OxmlElement('w:color');c.set(qn('w:val'),'000000');pr.append(c);r.append(pr)
            tx=OxmlElement('w:t');tx.text=m[1];r.append(tx);link.append(r);p._p.append(link)
        else:
            for s in re.split(r'([A-Za-z]_(?:ij|ii|ref|m|i|j|n|b|q\*))',t):
                m=re.fullmatch(r'([A-Za-z])_(ij|ii|ref|m|i|j|n|b|q\*)',s)
                if m:
                    font(p.add_run(m[1]),zh)
                    r=p.add_run(m[2]);font(r,zh);r.font.subscript=True
                else:font(p.add_run(s),zh)

def no_split(row):
    p=row._tr.get_or_add_trPr();p.append(OxmlElement('w:cantSplit'))

def set_borders(table,visible):
    props=table._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        v=OxmlElement('w:'+edge);v.set(qn('w:val'),'single' if visible else 'nil')
        if visible:v.set(qn('w:sz'),'4');v.set(qn('w:color'),'000000')
        borders.append(v)
    props.append(borders)
    margins=OxmlElement('w:tblCellMar')
    for edge in ['top','left','bottom','right']:
        value=OxmlElement('w:'+edge)
        value.set(qn('w:w'),'30' if visible else '0');value.set(qn('w:type'),'dxa');margins.append(value)
    props.append(margins)

def unnumber(p):
    num=p._p.get_or_add_pPr().get_or_add_numPr()
    num.get_or_add_numId().val=0

def section(doc,pattern):
    doc.add_section(WD_SECTION_START.CONTINUOUS)
    target=doc.sections[-1]._sectPr
    target.getparent().replace(target,deepcopy(pattern))
    p=doc.paragraphs[-1]
    p.paragraph_format.space_before=p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.line_spacing=Pt(1)
    p.add_run().font.size=Pt(1)

def equation_image(expression,n):
    """Split long displays at mathematical boundaries, keeping one equation number."""
    lines=expression.split(r'\qquad')
    if n in ('5','6'):
        split=expression.index(r'\operatorname{Re}')
        lines=[expression[:split],r'\times '+expression[split:]]
    key=hashlib.sha256(('template-columns-v2:'+expression).encode()).hexdigest()[:20]
    path=QA/'equations'/(key+'.png')
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        imgs=[]
        matplotlib.rcParams['mathtext.fontset']='stix'
        for line in lines:
            buf=BytesIO()
            math_to_image('$'+line.strip().replace(r'\frac',r'\dfrac')+'$',buf,prop=FontProperties(family='STIXGeneral',size=10),dpi=450,format='png')
            buf.seek(0);imgs.append(Image.open(buf).convert('RGB'))
        canvas=Image.new('RGB',(max(i.width for i in imgs),sum(i.height for i in imgs)+18*(len(imgs)-1)),'white')
        y=0
        for im in imgs:canvas.paste(im,((canvas.width-im.width)//2,y));y+=im.height+18
        canvas.save(path)
    return path

def build(lang):
    zh=lang=='zh'
    assert hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()=='54507756c7bcd18efbc1f0272c269d388e7efa335949bce061d9d25a00e2d251'
    doc=Document(TEMPLATE)
    title_section=deepcopy(doc.sections[0]._sectPr)
    body_section=deepcopy(doc.sections[4]._sectPr)
    wide_section=deepcopy(doc.sections[5]._sectPr)
    body=doc._element.body
    for child in list(body):body.remove(child)
    body.append(title_section)
    for rid,rel in list(doc.part.rels.items()):
        if rel.reltype in (RT.IMAGE,RT.HYPERLINK,RT.COMMENTS):doc.part.drop_rel(rid)
    for rid,rel in list(doc.part.package.rels.items()):
        if rel.reltype.endswith('/custom-properties'):del doc.part.package.rels[rid]
    width=(11906-2160)/1440
    col=(width-.25)/2
    # The legacy DOC stores an invalid East Asian font name after conversion.
    for st in doc.styles:
        if st.type==WD_STYLE_TYPE.PARAGRAPH:
            st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'SimSun')
    title=doc.styles.add_style('Title',WD_STYLE_TYPE.PARAGRAPH) if 'Title' not in doc.styles else doc.styles['Title']
    title.base_style=doc.styles['paper title'];title.font.size=Pt(14);title.font.bold=True
    title.font.color.rgb=RGBColor(0,0,0)
    title.paragraph_format.keep_with_next=True
    title.paragraph_format.space_after=Pt(6)
    # Follow the template's explicit 9 pt reference instruction over its 8 pt style.
    doc.styles['references'].font.size=Pt(9)
    doc.styles['references'].paragraph_format.line_spacing=1
    data=(ROOT/f'paper/field_{lang}.md').read_text(encoding='utf-8')
    assert '{{' not in data
    in_refs=False;abstract=False;frontmatter=True;author=''
    counts=dict(figures=0,equations=0,data_tables=0)
    for kind,item in blocks(data):
        if kind=='heading':
            level,label=item
            if level==1:
                p=doc.add_paragraph(style='Title');inline(p,label,zh)
                continue
            if label in ['Abstract','摘要']:
                assert author=='Ju Luo, Yuqian Zhou'
                frontmatter=False;section(doc,body_section)
                abstract=True;continue
            in_refs=label in ['References','参考文献']
            numbered=bool(re.match(r'^[IVX]+ ',label)) if level==2 else True
            p=doc.add_paragraph(style=f'Heading {level-1}' if numbered else 'Heading 5')
            inline(p,re.sub(r'^(?:[IVX]+|[A-Z]) ','',label) if numbered else label,zh)
            p.paragraph_format.keep_with_next=True
        elif kind=='paragraph':
            if frontmatter:
                p=doc.add_paragraph(style='Affiliation' if author else 'Author')
                p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.space_after=Pt(2)
                p.paragraph_format.keep_with_next=True
                inline(p,item,zh)
                if not author:author=item
            elif abstract:
                p=doc.add_paragraph(style='Abstract')
                r=p.add_run('摘要—' if zh else 'Abstract—');font(r,zh);r.italic=True
                inline(p,item,zh);abstract=False
            elif item.startswith('**Keywords') or item.startswith('**关键词'):
                p=doc.add_paragraph(style='key words');inline(p,item.replace('**',''),zh)
            elif item.startswith('**Table') or item.startswith('**表'):
                # Keep the last table and its caption off the preceding page's short tail.
                if counts['data_tables']==3:
                    section(doc,body_section)
                    doc.sections[-1].start_type=WD_SECTION_START.NEW_PAGE
                p=doc.add_paragraph(style='table head');unnumber(p)
                inline(p,item.replace('**',''),zh)
                p.paragraph_format.keep_with_next=True
            elif in_refs:
                p=doc.add_paragraph(style='references');unnumber(p);inline(p,item,zh)
                p.paragraph_format.keep_together=True
                p.paragraph_format.left_indent=Inches(.22)
                p.paragraph_format.first_line_indent=Inches(-.22)
            else:
                p=doc.add_paragraph(style='Body Text');inline(p,item,zh)
        elif kind=='math':
            exp,n=item;path=equation_image(exp,n)
            doc.paragraphs[-1].paragraph_format.keep_with_next=True
            t=doc.add_table(rows=1,cols=2);t.autofit=False
            t.alignment=WD_TABLE_ALIGNMENT.CENTER;set_borders(t,False)
            widths=[col-.28,.28]
            for c,w in zip(t.columns,widths):c.width=Inches(w)
            for c,w in zip(t.rows[0].cells,widths):
                c.width=Inches(w);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p=c.paragraphs[0];p.paragraph_format.space_before=p.paragraph_format.space_after=Pt(3)
            p=t.cell(0,0).paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            with Image.open(path) as im:w=min(im.width/450,widths[0]-.1)
            drawing=p.add_run().add_picture(str(path),width=Inches(w))
            drawing._inline.docPr.set('descr',f'Equation ({n}): {exp}')
            p=t.cell(0,1).paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
            font(p.add_run(f'({n})'),zh,9)
            no_split(t.rows[0]);counts['equations']+=1
        elif kind=='table':
            n=len(item[0]);t=doc.add_table(rows=1,cols=n);t.autofit=False
            t.alignment=WD_TABLE_ALIGNMENT.CENTER;set_borders(t,True)
            if counts['data_tables']==0:widths=[.4,.51,1.03,.5,col-2.44]
            elif n==4:widths=[.7]+[(col-.7)/3]*3
            else:widths=[1.0]+[(col-1.0)/(n-1)]*(n-1)
            for c,w in zip(t.columns,widths):c.width=Inches(w)
            for i,row in enumerate(item):
                cells=t.rows[0].cells if i==0 else t.add_row().cells
                for j,(cell,txt) in enumerate(zip(cells,row)):
                    cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    p=cell.paragraphs[0];p.paragraph_format.space_before=p.paragraph_format.space_after=Pt(2)
                    p.paragraph_format.line_spacing=1
                    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
                    if i==0 and not zh:
                        txt={'Group':'Group','Nominal range':'Range','Azimuth take 1 / take 2':'Azimuth\ntake 1 / take 2',
                             'Elevation':'Elev.','Median °':'Median\n°','95th pct. °':'95th pct.\n°'}.get(txt,txt)
                    font(p.add_run(txt),zh,8,bold=i==0)
                    if i<len(item)-1:p.paragraph_format.keep_with_next=True
                no_split(t.rows[i])
            counts['data_tables']+=1
        elif kind=='figure':
            caption,rel=item
            section(doc,wide_section)
            p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next=True
            p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(0)
            drawing=p.add_run().add_picture(str((ROOT/'paper'/rel).resolve()),width=Inches(width))
            drawing._inline.docPr.set('descr',caption)
            p=doc.add_paragraph(style='figure caption');unnumber(p);inline(p,caption,zh)
            p.paragraph_format.keep_together=True
            section(doc,body_section)
            counts['figures']+=1
    section(doc,wide_section)
    assert counts==dict(figures=3,equations=9,data_tables=4),counts
    doc.core_properties.title=next(item[1] for kind,item in blocks(data) if kind=='heading')
    doc.core_properties.subject='Field evaluation of direction-conditioned coherence ranking'
    doc.core_properties.author=author;doc.core_properties.last_modified_by=''
    doc.core_properties.comments='';doc.core_properties.keywords='UAV; acoustic localization; spatial coherence; SRP-PHAT'
    path=ROOT/'paper'/('Chinese_Translation.docx' if zh else 'English_Main.docx')
    doc.save(path)
    # Keep opaque design parts byte-for-byte from the converted reference.
    with ZipFile(TEMPLATE) as src,ZipFile(path) as out:
        entries={n:out.read(n) for n in out.namelist()}
        for n in ['word/numbering.xml','word/theme/theme1.xml','word/fontTable.xml']:
            if n in entries and n in src.namelist():entries[n]=src.read(n)
    with ZipFile(path,'w',ZIP_DEFLATED) as out:
        for n,b in entries.items():out.writestr(n,b)
    return dict(path=path.relative_to(ROOT).as_posix(),**counts,sections=len(doc.sections),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    QA.mkdir(parents=True,exist_ok=True)
    result=[build('en'),build('zh')]
    (QA/'docx_structure.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
