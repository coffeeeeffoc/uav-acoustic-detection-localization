"""Build both editable manuscripts with the bundled python-docx runtime.

Scientific figures/equation rasters are generated separately by finalize_field_paper.py.
The two PDFs are exported from these DOCX files with the packaged document renderer.
"""
from pathlib import Path
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

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'results/document_qa/field'

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
            for s in re.split(r'([A-Za-z]_(?:ij|ii|ref|m|i|j|n|q\*))',t):
                m=re.fullmatch(r'([A-Za-z])_(ij|ii|ref|m|i|j|n|q\*)',s)
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
        if visible:v.set(qn('w:sz'),'4');v.set(qn('w:color'),'BBBBBB')
        borders.append(v)
    props.append(borders)

def build(lang):
    zh=lang=='zh';doc=Document();s=doc.sections[0]
    s.page_width=Inches(8.2677);s.page_height=Inches(11.6929)
    s.left_margin=s.right_margin=Inches(.8);s.top_margin=Inches(.72);s.bottom_margin=Inches(.72)
    s.header_distance=s.footer_distance=Inches(.3)
    width=6.6677
    for name,size in [('Normal',10.5 if zh else 11),('Title',17 if zh else 18),('Heading 1',12),('Heading 2',11),('Caption',9.5)]:
        st=doc.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
        st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'SimSun')
        st.paragraph_format.widow_control=True
    normal=doc.styles['Normal'].paragraph_format
    normal.line_spacing=1.12 if zh else 1.08;normal.space_after=Pt(5.5)
    for name in ['Heading 1','Heading 2']:
        st=doc.styles[name];st.font.bold=True
        st.paragraph_format.space_before=Pt(11 if name=='Heading 1' else 7)
        st.paragraph_format.space_after=Pt(4);st.paragraph_format.keep_with_next=True
    doc.styles['Title'].paragraph_format.space_after=Pt(13)
    doc.styles['Title'].paragraph_format.line_spacing=1.03
    doc.styles['Title'].font.bold=True
    doc.styles['Caption'].font.color.rgb=RGBColor(0,0,0)
    doc.styles['Caption'].font.bold=False;doc.styles['Caption'].font.italic=False
    for st in doc.styles:
        for border in list(st._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    refstyle=doc.styles.add_style('Field References',WD_STYLE_TYPE.PARAGRAPH)
    refstyle.base_style=doc.styles['Normal'];refstyle.font.size=Pt(9)
    header=s.header.paragraphs[0];header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    font(header.add_run('小型无人机声学探测与测向' if zh else 'Acoustic UAV detection and direction finding'),zh,8.5)
    footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');footer._p.append(f)
    data=(ROOT/f'paper/field_{lang}.md').read_text(encoding='utf-8')
    assert '{{' not in data
    in_refs=False
    counts=dict(figures=0,equations=0,data_tables=0)
    for kind,item in blocks(data):
        if kind=='heading':
            level,title=item
            p=doc.add_paragraph(style='Title' if level==1 else f'Heading {level-1}')
            inline(p,title,zh)
            if level==1:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            if title in ['References','参考文献']:in_refs=True
        elif kind=='paragraph':
            p=doc.add_paragraph();inline(p,item,zh)
            p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
            if item.startswith('**Table') or item.startswith('**表'):
                p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(6)
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:r.font.size=Pt(9.5)
            elif in_refs:
                p.style=refstyle
                p.paragraph_format.left_indent=Inches(.22);p.paragraph_format.first_line_indent=Inches(-.22)
                p.paragraph_format.line_spacing=1.02;p.paragraph_format.space_after=Pt(4)
                for r in p.runs:r.font.size=Pt(9)
            elif item=='英文论文中文译稿':
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:r.font.size=Pt(10)
        elif kind=='math':
            expression,n=item
            if doc.paragraphs:doc.paragraphs[-1].paragraph_format.keep_with_next=True
            key=hashlib.sha256(expression.encode()).hexdigest()[:20]
            img=QA/'equations'/f'{key}.png';assert img.exists()
            t=doc.add_table(rows=1,cols=3);t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER;set_borders(t,False)
            widths=[.28,width-.83,.55]
            for c,w in zip(t.rows[0].cells,widths):c.width=Inches(w);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for c,w in zip(t.columns,widths):c.width=Inches(w)
            p=t.cell(0,1).paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
            im=Image.open(img);w=min(im.width/450,widths[1])
            p.add_run().add_picture(str(img),width=Inches(w))
            p=t.cell(0,2).paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;font(p.add_run(f'({n})'),zh,10)
            no_split(t.rows[0]);counts['equations']+=1
        elif kind=='table':
            n=len(item[0]);t=doc.add_table(rows=1,cols=n);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
            widths=([1.0,1.0,2.25,.9,1.5177] if counts['data_tables']==0 else
                    ([1.8]+[(width-1.8)/(n-1)]*(n-1)))
            for c,w in zip(t.columns,widths):c.width=Inches(w)
            set_borders(t,True)
            for i,row in enumerate(item):
                cells=t.rows[0].cells if i==0 else t.add_row().cells
                for j,(cell,txt) in enumerate(zip(cells,row)):
                    cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    p=cell.paragraphs[0];p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3)
                    p.paragraph_format.line_spacing=1.05;p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
                    r=p.add_run(txt);font(r,zh,9.2 if zh else 9.5,bold=i==0)
                    if i==0:
                        shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'F1F1F1');cell._tc.get_or_add_tcPr().append(shading)
                no_split(t.rows[i])
                if i==0:t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
            doc.add_paragraph().paragraph_format.space_after=Pt(0)
            counts['data_tables']+=1
        elif kind=='figure':
            caption,rel=item;path=(ROOT/'paper'/rel).resolve();assert path.exists()
            p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
            p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(3)
            p.add_run().add_picture(str(path),width=Inches(width))
            p=doc.add_paragraph(style='Caption');inline(p,caption,zh);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after=Pt(8);counts['figures']+=1
    assert counts==dict(figures=3,equations=9,data_tables=4),counts
    doc.core_properties.title=next(item[1] for kind,item in blocks(data) if kind=='heading')
    doc.core_properties.subject='Acoustic UAV detection and direction finding with real array recordings'
    doc.core_properties.author='';doc.core_properties.keywords='UAV; acoustic localization; spatial coherence; SRP-PHAT'
    path=ROOT/'paper'/('Chinese_Translation.docx' if zh else 'English_Main.docx')
    doc.save(path)
    return dict(path=path.relative_to(ROOT).as_posix(),**counts,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    QA.mkdir(parents=True,exist_ok=True)
    result=[build('en'),build('zh')]
    (QA/'docx_structure.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
