"""Revise the supplied supervisor manuscript without changing experimental results."""
from copy import deepcopy
from pathlib import Path
import csv
import hashlib
import json
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
OUT = ROOT / 'paper' / 'editor_revision_2026-11-13'
OUT.mkdir(exist_ok=True)
source = QA / 'supervisor_original.docx'
doc = Document(source)
p = list(doc.paragraphs)
tables = list(doc.tables)
changes = []


def replace(index, text):
    para = p[index]
    before = para.text
    fmt = deepcopy(para.runs[0]._r.rPr) if para.runs and para.runs[0]._r.rPr is not None else None
    para.clear()
    run = para.add_run(text)
    if fmt is not None:
        run._r.insert(0, fmt)
    changes.append({'kind': 'replace', 'original_paragraph': index, 'before': before, 'after': text})


def insert_after(anchor, text, style='Body Text'):
    element = OxmlElement('w:p')
    anchor._p.addnext(element)
    para = Paragraph(element, anchor._parent)
    para.style = style
    para.add_run(text)
    changes.append({'kind': 'insert', 'after': text})
    return para


def remove(para):
    para._p.getparent().remove(para._p)


replace(18, 'Passive acoustic sensing must detect unmanned aerial vehicle (UAV) emissions and estimate their bearing in noisy environments, where low signal-to-noise ratios hinder localization [1]. Generalized cross-correlation estimates pairwise delays [2], while steered response power (SRP) aggregates correlation evidence over candidate directions [3], [4]. The phase transform (PHAT) emphasizes phase alignment, so coherent non-UAV sources can also dominate the response. Existing SRP extensions improve spectral reliability and spatial search [4], but multiplying an entire spatial map by a positive detection weight leaves its maximizing direction unchanged.')
replace(19, 'In this paper, we propose direction-conditioned coherence ranking (DCCR), which ranks four SRP-PHAT proposals using directional coherence spectra. Training includes competing directions from the same aircraft observations, which share background and overall gain. The contribution is candidate-conditioned source association using established array operations. A shared-detector comparison separates changes in bearing selection from changes in alarm decisions.')
insert_after(p[19], 'The practical question is whether the direction selected by an acoustic array belongs to the UAV. A strong spatial peak establishes agreement with a propagation delay pattern, but does not by itself identify the emitting source. Conversely, an alarm derived from a spectrum averaged across microphones does not specify which peak should be reported. DCCR links these decisions by evaluating the acoustic evidence separately at each proposed bearing, then using the best candidate score for detection.')

replace(21, 'SNR-weighted beamforming with particle tracking [5], PHAT-β partial spectral whitening [6], and SRP with a spatially separated auxiliary microphone [7] address noise and reverberation under different operating conditions. UAV approaches exploit rotor harmonics [8] or combine synthesized signals with neural localization [9]. DCCR uses fixed frequency bands and a compact linear model; no direct comparison with those trained neural systems is available. DDL [10] synchronizes audio with flight-log positions, whereas UaVirBASE [11] documents measured static configurations. The present recordings support nominal static-bearing comparisons but lack synchronized trajectories for tracking evaluation.')
remove(p[22])
insert_after(p[21], 'Rotor-generated sound contains harmonic components whose spacing depends on propeller rotation and blade count [8]. This gives acoustic detection a source-related cue beyond broadband sound level. In DCCR, no rotor speed or harmonic spacing is estimated explicitly. Instead, the frequency distribution of spatially coherent sound is represented by 24 bands and learned from the development recordings. This choice allows the same representation to inform source detection and bearing selection, while leaving transfer to other rotor configurations an empirical question.')

# The paragraph follows equation (2), retaining the original nine equation objects.
geometry = OxmlElement('w:p')
tables[1]._tbl.addnext(geometry)
geometry_para = Paragraph(geometry, doc._body)
geometry_para.style = 'Body Text'
geometry_text = 'The aperture bounds the intermicrophone propagation delay by approximately 0.30/343 = 0.875 ms, or 14 samples at 16 kHz. Delay interpolation therefore reduces numerical quantization but cannot remove uncertainty in sensor positions, channel phase or sound speed. Across the analysis band, wavelengths range from about 1.14 m at 300 Hz to 0.046 m at 7500 Hz. Low frequencies provide smaller phase differences across the aperture, whereas higher frequencies can yield ambiguous phase patterns for individual pairs [4]. Combining multiple baselines and frequencies supplies complementary directional evidence. The far-field model estimates azimuth and elevation; it provides no independent range measurement.'
geometry_para.add_run(geometry_text)
changes.append({'kind': 'insert', 'after': geometry_text})

insert_after(p[29], 'The distinction between the two normalizations is important for UAV sensing. Away from the numerical floor, PHAT gives a nonzero cross-spectrum unit magnitude and retains its phase, including bins whose interchannel agreement is weak. Coherence normalization also retains the degree of agreement, so weakly coherent components contribute less to the directional features. With only one Fourier frame, the magnitude of the normalized cross-product would be unity away from the floor; averaging cross- and auto-spectra first makes the magnitude informative. Nevertheless, a coherent interferer can also produce a large value. Coherence alone is therefore insufficient to identify a UAV, motivating a learned comparison across frequency bands.')

insert_after(p[34], 'For a candidate consistent with the arriving wave, the steering factor compensates intermicrophone phase differences and the real parts tend to add constructively. A mismatched direction leaves residual phases that can cancel within a band. Thus, two peaks with similar broadband PHAT responses may have different coherence spectra. Equation (8) exploits this distinction: positive and negative fitted coefficients reward or suppress particular standardized band responses. These coefficients describe discrimination within the development data, rather than a universal UAV emission spectrum. Unlike a scalar multiplier applied to an entire spatial map, candidate-dependent scores can change the selected direction.')

insert_after(p[45], 'Inference consequently has two separate decisions. First, the largest of the four scores selects a bearing, even when all candidates resemble background. Second, comparison with the calibrated threshold determines whether that bearing is accompanied by a UAV alarm. Calibration is applied to the maximum candidate score, matching the quantity used at inference; calibrating individual candidate scores would describe a different decision rule. A rejected observation still contributes to the reported all-window angular statistics, but not to joint detection and localization success. This distinction prevents accurate bearings on missed detections from being counted as successful UAV surveillance.')

replace(48, 'We use recordings supplied for the 4th Shenghua Cup Acoustic Technology Competition: an upward-facing CRY8501/SonoCam Pi array captured a DJI Air 3S on 25 May 2026 [12]. Each acquisition group supplies two aircraft recordings and one background recording (Table I), with 208 channels at 48 kHz, 16-bit PCM. The nine recordings total 273.75 s. Channel sample counts agree within each recording, and no sample reaches the PCM limits across 1872 WAV files; this does not independently verify phase or clock calibration. Nominal bearings come from acquisition diagrams, without synchronized trajectories to quantify hovering displacement or reference uncertainty. Videos are not estimator inputs or ground truth.')

replace(59, 'Mean discrepancy decreases in all four aircraft recordings. For P2 takes 1 and 2, PHAT/DCCR means are 6.95°/4.28° and 3.23°/2.55°; for P3 they are 17.32°/4.16° and 31.62°/16.87°. Paired reductions, calculated before rounding, are 2.67°, 0.68°, 13.16° and 14.76°, respectively. The larger reductions at P3 reflect greater scope to correct competing peaks in these recordings. They do not establish that performance improves with range, because range, bearing and acoustic conditions change together. The candidate oracle yields 6.44° mean discrepancy and 94.3% within 10°; this retrospective, reference-assisted diagnostic measures coverage and is not an estimator output.')
p[58]._p.addprevious(p[59]._p)
remove(p[60])
tables[11]._tbl.getparent().remove(tables[11]._tbl)
for i in [61, 62, 63, 64]:
    remove(p[i])
replace(66, 'DCCR detects 514/600 windows (85.7%) with 3/200 false alarms (1.5%; Table III). P2/P3 detection rates are 83.0%/88.3%, and false-alarm rates are 0.0%/3.0%. The nominal 5% calibration level is not the measured false-alarm rate.')
caption = insert_after(p[66], "Table III. Detection and joint localization using each method's calibrated threshold; 600 aircraft and 200 background windows.", 'table head')
caption.paragraph_format.keep_with_next = True
caption.paragraph_format.keep_together = True
num_pr = caption._p.get_or_add_pPr().get_or_add_numPr()
num_pr.get_or_add_numId().val = 0

insert_after(p[67], 'In counts, the shared gate gives 459 successful PHAT bearings and 513 successful DCCR bearings, a net increase of 54 observations without changing the alarm set. This paired comparison isolates source association from threshold selection. Independently calibrated detector results in Table III answer a different question: they describe each complete pipeline at its own measured operating point. Since the baselines have 0.5% false alarms and DCCR has 1.5%, the detection-rate difference alone cannot establish superiority at an equal false-alarm rate.')
replace(70, 'Fig. 2 shows the corresponding window-wise discrepancies without smoothing or tracking. The traces help distinguish isolated peak-selection failures from the more persistent errors in P3 take 2.')
last_caption = insert_after(p[76], 'Fig. 2. Window-wise discrepancies for the four held-out aircraft recordings. Angular axes are logarithmic above 1°; no temporal smoothing or tracking is used.')
last_caption.paragraph_format.first_line_indent = Pt(0)
last_caption.paragraph_format.space_after = Pt(5)
last_caption.paragraph_format.keep_together = True
last_caption.runs[0].font.size = Pt(8)

replace(78, 'The lower mean discrepancy primarily reflects fewer large errors: the median changes from 3.49° to 3.47°, whereas the 95th percentile decreases from 96.87° to 54.16°. The number of aircraft windows exceeding 10° falls from 91 for PHAT to 36 for DCCR. Of the 36 remaining failures, 34 lack a candidate within 10° and 33 belong to P3 take 2. Only two failures therefore offer an in-tolerance candidate that the ranker fails to choose. This separates proposal coverage from ranking quality and explains the small difference between DCCR and the candidate oracle. Improving the score alone cannot recover a UAV direction absent from all four proposals; a broader proposal search would require a new development and computational-cost study.')
replace(79, 'Temporal mismatch between stored and current background spectra may limit direct subtraction. DCCR avoids subtracting those spectra, but still uses background recordings to calibrate its alarm threshold. Normalization removes positive channel-gain factors away from the numerical floor; it does not remove phase mismatch, changing propagation or differences in aircraft spectra. A deployed array would therefore require verified channel synchronization, microphone geometry, orientation and an appropriate sound-speed model. The agreement of file lengths and absence of clipping in this dataset establish basic recording integrity, not these calibration properties.')
discussion = insert_after(p[79], 'The P2 and P3 observations also show why detection rate should not be interpreted as a detection-range curve. DCCR detects 83.0% of aircraft windows at P2 and 88.3% at P3, although the nominal range is greater at P3. Each group has a different background and its own threshold; aircraft orientation and emission level are not controlled between groups. These data consequently support the reported comparisons at the recorded positions, but neither a maximum detection range nor a monotonic dependence on distance.')
insert_after(discussion, 'Evidence comes from one aircraft model, one day and six held-out recordings with local calibration, not 800 independent field trials. Nominal static references cannot separate hovering motion, orientation error and phase mismatch. Recorded negatives do not exhaust confusing machinery or simultaneous sources, and the signed band scores are not probabilities of UAV identity. Range estimation, identity recognition, multiple-UAV separation and tracking remain outside the evaluated scope. Broader validation requires new development data and independent recordings with synchronized reference trajectories. The measured processing time also leaves real-time implementation unverified. Computational improvements must be assessed together with their effect on proposal coverage and detection performance.')

# Keep the supervisor's supplied author, correspondence and funding information.
replace(97, '[12] "Shenghua Cup 2026, Attachment 4: Experimental Description," technical documentation accompanying the problem-1 data package of the 4th Shenghua Cup Acoustic Technology Competition, release package "0609 update," 2026 (in Chinese).')
p[97].style = 'references'
p[97]._p.get_or_add_pPr().get_or_add_numPr().get_or_add_numId().val = 0
p[97].paragraph_format.first_line_indent = Pt(-12)
p[97].paragraph_format.left_indent = Pt(12)
p[97].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for run in p[97].runs:
    run.font.size = Pt(8)

# Prevent floating tables and forced line spacing from splitting captions or rows.
for table in doc.tables:
    for node in table._tbl.xpath('./w:tblPr/w:tblpPr'):
        node.getparent().remove(node)
    if len(table.rows) == 1:
        continue
    for row_index, row in enumerate(table.rows):
        pr = row._tr.get_or_add_trPr()
        for height in pr.findall(qn('w:trHeight')):
            pr.remove(height)
        if pr.find(qn('w:cantSplit')) is None:
            pr.append(OxmlElement('w:cantSplit'))
        for cell in row.cells:
            for para in cell.paragraphs:
                para.paragraph_format.keep_with_next = row_index < len(table.rows) - 1
                para.paragraph_format.keep_together = True
    header = table.rows[0]._tr.get_or_add_trPr()
    if header.find(qn('w:tblHeader')) is None:
        header.append(OxmlElement('w:tblHeader'))

for para in doc.paragraphs:
    if para.text.startswith('Table '):
        para.paragraph_format.keep_with_next = True
        para.paragraph_format.keep_together = True
    if para.style.name in ['Heading 1', 'Heading 2', 'Heading 5']:
        para.paragraph_format.keep_with_next = True
        for run in para.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
for index in [38, 72, 73, 74, 75, 76]:
    p[index].paragraph_format.keep_with_next = True
    p[index].paragraph_format.keep_together = True
for shape in doc._element.xpath('.//*[local-name()="shape"]'):
    alt = shape.get('alt')
    if alt and alt.startswith('Fig. 3.'):
        shape.set('alt', alt.replace('Fig. 3.', 'Fig. 2.', 1))

# Delete excess empty paragraphs while preserving section boundaries and image anchors.
for para in list(doc.paragraphs)[15:]:
    if not para.text.strip() and not para._p.xpath('.//w:pict | .//w:drawing | ./w:pPr/w:sectPr | .//w:br'):
        remove(para)

output = OUT / 'DCCR_Editor_Revised.docx'
doc.save(output)

# Small, independent consistency checks against the frozen evaluation outputs.
rows = list(csv.DictReader((ROOT/'results/field/predictions.csv').open(encoding='utf-8')))
positive = {method: [r for r in rows if r['positive']=='1' and r['method']==method] for method in ['phat', 'ranker']}
assert all(len(v)==600 for v in positive.values())
assert sum(float(r['error_deg']) > 10 for r in positive['phat']) == 91
assert sum(float(r['error_deg']) > 10 for r in positive['ranker']) == 36
assert sum(int(r['detected']) for r in positive['ranker']) == 514
assert sum(int(r['detected']) and float(r['error_deg']) <= 10 for r in positive['ranker']) == 513
gate = {(r['id'],r['start_s']):int(r['detected']) for r in positive['ranker']}
assert sum(gate[r['id'],r['start_s']] and float(r['error_deg']) <= 10 for r in positive['phat']) == 459
candidates = list(csv.DictReader((ROOT/'results/field/candidates.csv').open(encoding='utf-8')))
failures = {(r['id'],r['start_s']) for r in positive['ranker'] if float(r['error_deg']) > 10}
assert sum(key[0]=='s3_uav2' for key in failures) == 33
covered = {(r['id'],r['start_s']) for r in candidates if r['error_deg'] and float(r['error_deg'])<=10}
assert len(failures - covered) == 34

check = Document(output)
for old, new in [(tables[8], check.tables[8]), (tables[10], check.tables[10]), (tables[12], check.tables[11])]:
    assert [[c.text for c in r.cells] for r in old.rows] == [[c.text for c in r.cells] for r in new.rows]
equations = [t for t in check.tables if len(t.rows)==1]
assert [t.cell(0,1).text for t in equations] == [f'({i})' for i in range(1,10)]
text = '\n'.join(x.text for x in check.paragraphs)
for token in ['ytxlj12345@163.com', 'zhouyuqian@nuaa.edu.cn', 'U25A20427', '1st Ju Luo', '2nd Yuqian Zhou*']:
    assert token in text
assert 'Fig. 3' not in text and 'Table IV' not in text
assert len([x for x in check.paragraphs if re.match(r'^\[\d+\]',x.text)]) == 12
assert len([x for x in check.paragraphs if re.match(r'^Fig\. \d+\.', x.text)]) == 2
assert len([x for x in check.paragraphs if x.text.startswith('Table ')]) == 3
assert 'nearly overlap.Detection' not in text
original_text = '\n'.join(x.text for x in Document(source).paragraphs)
report = {'output':str(output), 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(), 'body_words_before': len(original_text.split(' Introduction ')[-1].split('References')[0].split()), 'body_words_after': len(text.split(' Introduction ')[-1].split('References')[0].split()), 'figures':2,'data_tables':3,'equations':9,'references':12,'numeric_checks':'passed','changes':changes}
(QA/'revision_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'revised_text.txt').write_text(text,encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='changes'},ensure_ascii=False,indent=2))
