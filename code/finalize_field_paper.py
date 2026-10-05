"""Populate both manuscripts and figures from the frozen field result tables."""
from field_data import *
import csv,re,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image

NAMES={'phat':'SRP-PHAT','scot':'SCOT-SRP','coherence':'Coherence PHAT','reference':'Reference subtraction',
       'ranker':'DCCR','no_hard_negatives':'DCCR without hard negatives'}
ZH_NAMES={'phat':'SRP-PHAT','scot':'SCOT-SRP','coherence':'相干性加权PHAT','reference':'背景互谱扣除',
          'ranker':'DCCR','no_hard_negatives':'DCCR无困难负例'}
ORDER=['phat','scot','coherence','reference','no_hard_negatives','ranker']
COLORS={'phat':'#777777','scot':'#B07C2E','coherence':'#46735F','reference':'#AB5864',
        'ranker':'#005A98','no_hard_negatives':'#8466A0'}

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

def references():
    refs=json.loads((ROOT/'references/references.json').read_text(encoding='utf-8'))
    keys=['chen','gcc','srp','srpreview','noiseweight','phatbeta','brumann','harmonics','yang','ddl','uavirbase']
    result=[];mapping=[]
    for i,k in enumerate(keys,1):
        r=next(x for x in refs if x['id']==k)
        title=r['title'];authors=', '.join(r['authors']);venue=r['venue']
        if k=='chen':
            authors='P. Chen, Y. Chen, and W. Wang';title='Review for UAV Acoustic Positioning'
            venue='Journal of South China University of Technology (Natural Science Edition), vol. 50, no. 12, pp. 109–123 (in Chinese)'
        if len(r['authors'])>5:authors=r['authors'][0]+' et al.'
        result.append(f'[{i}] {authors}, "{title}," {venue}, {r["year"]}. [doi: {r["doi"]}](https://doi.org/{r["doi"]}).')
        mapping.append(dict(number=i,id=k,doi=r['doi']))
    result.append('[12] "Experimental measurement description," acquisition documentation accompanying the CRY8501 Air 3S recordings of 25 May 2026, unpublished technical dataset, 2026 (in Chinese).')
    mapping.append(dict(number=12,id='field_acquisition',source='Original acquisition description and channel metadata; see results/field/source_manifest.json'))
    (ROOT/'paper/field_citation_map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    return '\n\n'.join(result)

def text_values(s,lang,refs):
    zh=lang=='zh';names=ZH_NAMES if zh else NAMES
    m=s['methods'];p=m['phat'];r=m['ranker'];a=m['no_hard_negatives'];pair=s['paired_against_ranker'];oracle=s['candidate_oracle']
    gain=p['mean_deg']-r['mean_deg'];abgain=a['mean_deg']-r['mean_deg']
    same=pair['phat']['same_ranker_gate_joint10']
    value={k:f'{v:.2f}' for k,v in [('PHAT_MEAN',p['mean_deg']),('RANK_MEAN',r['mean_deg'])]}
    value.update({k:f'{100*v:.1f}' for k,v in [('RANK_TPR',r['tpr']),('RANK_FPR',r['fpr']),('RANK_JOINT',r['joint10']),('SHARED_PHAT_JOINT',same)]})
    value['REFERENCES']=refs
    value['LOCALIZATION_TABLE']=table(['方法','均值 °','中位数 °','95百分位 °','≤5° %','≤10° %'] if zh else
        ['Method','Mean °','Median °','95th pct. °','≤5° %','≤10° %'],
        [[names[k],f'{m[k]["mean_deg"]:.2f}',f'{m[k]["median_deg"]:.2f}',f'{m[k]["p95_deg"]:.2f}',
          f'{m[k]["within5"]*100:.1f}',f'{m[k]["within10"]*100:.1f}'] for k in ORDER])
    ids=['s2_uav1','s2_uav2','s3_uav1','s3_uav2']
    diffs=pair['phat']['recording_improvement_deg']
    value['RECORDING_TABLE']=table(['录音','SRP-PHAT °','DCCR °','差值 °'] if zh else ['Recording','SRP-PHAT °','DCCR °','Difference °'],
        [[rid.replace('s2_','P2 ').replace('s3_','P3 ').replace('uav','take '),
          f'{p["recordings"][rid]["mean_deg"]:.2f}',f'{r["recordings"][rid]["mean_deg"]:.2f}',f'{diffs[rid]:+.2f}'] for rid in ids])
    value['DETECTION_TABLE']=table(['方法','检出数','虚警数','检出率 %','虚警率 %','联合成功 %'] if zh else
        ['Method','TP / 600','FP / 200','TPR %','FPR %','Joint ≤10° %'],
        [[names[k],m[k]['detected_positive'],m[k]['false_positive'],f'{100*m[k]["tpr"]:.1f}',
          f'{100*m[k]["fpr"]:.1f}',f'{100*m[k]["joint10"]:.1f}'] for k in ORDER])
    better=sum(d>0 for d in diffs.values())
    group_tpr={site:np.mean([r['recordings'][f's{site}_uav{take}']['detection_rate'] for take in [1,2]]) for site in [2,3]}
    group_fpr={site:r['recordings'][f's{site}_background']['detection_rate'] for site in [2,3]}
    if zh:
        value['LOCALIZATION_RESULTS']=(f'DCCR的平均球面角偏差为{r["mean_deg"]:.2f}°，SRP-PHAT为{p["mean_deg"]:.2f}°，配对平均差值（PHAT减DCCR）为{gain:+.2f}°。'
            f'DCCR的中位数和95百分位分别为{r["median_deg"]:.2f}°和{r["p95_deg"]:.2f}°，10°以内比例为{r["within10"]*100:.1f}%。'
            f'SCOT-SRP和相干性加权PHAT的平均偏差分别为{m["scot"]["mean_deg"]:.2f}°和{m["coherence"]["mean_deg"]:.2f}°。全部定位统计见表II。')
        value['RECORDING_RESULTS']=(f'相对于SRP-PHAT，DCCR在四段无人机录音中的{better}段降低了平均偏差。各段配对差值为{min(diffs.values()):+.2f}°至{max(diffs.values()):+.2f}°，详见表III。'
            f'四候选理想选择诊断的平均偏差为{oracle["mean_deg"]:.2f}°，10°以内比例为{oracle["within10"]*100:.1f}%。该数值使用评价参考进行事后理想选择，只用于说明候选覆盖限制，不能当作可实现的推理成绩。')
        value['DETECTION_RESULTS']=(f'DCCR检出{r["detected_positive"]}/600个无人机观测窗，并在{r["false_positive"]}/200个背景观测窗上产生虚警，对应{100*r["tpr"]:.1f}%检出率和{100*r["fpr"]:.1f}%虚警率。'
            f'P2和P3的检出率分别为{100*group_tpr[2]:.1f}%和{100*group_tpr[3]:.1f}%，背景虚警率分别为{100*group_fpr[2]:.1f}%和{100*group_fpr[3]:.1f}%。'
            '这些组间结果体现固定经验阈值在不同观测时段上的实际行为，不能以标定规则中的5%代替测得的虚警率。')
        value['JOINT_RESULTS']=(f'固定使用完整DCCR检测门控时，SRP-PHAT方向的联合成功率为{100*same:.1f}%，DCCR方向为{100*r["joint10"]:.1f}%，差值为{100*(r["joint10"]-same):+.1f}个百分点。'
            f'两者采用相同的{r["detected_positive"]}个已检出正观测窗，差别来自方向选择。单独报告的600窗定位指标仍包含漏检观测。')
        value['ABLATION_RESULTS']=(f'去除同一无人机录音中的错误方向训练反例后，平均偏差为{a["mean_deg"]:.2f}°，完整模型为{r["mean_deg"]:.2f}°，两者在所示精度下相同。'
            f'消融模型的检出率为{100*a["tpr"]:.1f}%，虚警率为{100*a["fpr"]:.1f}%。'
            f'完整模型多检出{r["detected_positive"]-a["detected_positive"]}个正观测窗，虚警数相同。两个模型只在3个正观测窗中选择不同方向，且这3个观测窗的偏差均超过10°。'
            '因此，困难负例的实测收益体现在当前标定工作点的检测上，而非方向精度；不能将其单独宣称为已验证的定位增益。')
        value['TIMING_RESULTS']=(f'DCCR每窗计算时间的中位数和95百分位分别为{r["compute_ms_median"]:.1f} ms和{r["compute_ms_p95"]:.1f} ms；SRP-PHAT对应为{p["compute_ms_median"]:.1f} ms和{p["compute_ms_p95"]:.1f} ms。'
            '计时包括重采样和互谱前端，不包括文件读取，另需200 ms采集窗。四候选细化和方向特征计算增加了处理开销。当前串行实现在该工作站上也不能维持每秒5个观测窗的持续处理速率，因而不能据此声称实时运行。')
        value['CONCLUSION']=(f'本文提出DCCR，将SRP-PHAT的四个候选方向与24频带方向相干谱的紧凑监督评分相结合。在保留的150 m和200 m实测录音上，平均标称方向偏差由SRP-PHAT的{p["mean_deg"]:.2f}°变为{r["mean_deg"]:.2f}°，'
            f'检出率为{100*r["tpr"]:.1f}%，背景虚警率为{100*r["fpr"]:.1f}%。共用检测门控下，10°以内联合成功率由{100*same:.1f}%变为{100*r["joint10"]:.1f}%。'
            '该方法将声源关联落实为候选方向上的学习问题，并给出完整可复现实现。现有结果的适用范围仍受候选覆盖、标称参考精度、背景标定及单机型单日采集条件限制。')
    else:
        value['LOCALIZATION_RESULTS']=(f'DCCR obtains a mean spherical discrepancy of {r["mean_deg"]:.2f}°, compared with {p["mean_deg"]:.2f}° for SRP-PHAT, giving a paired mean difference (PHAT minus DCCR) of {gain:+.2f}°. '
            f'Its median and 95th percentile are {r["median_deg"]:.2f}° and {r["p95_deg"]:.2f}°, and {100*r["within10"]:.1f}% of windows lie within 10°. '
            f'SCOT-SRP and coherence-weighted PHAT obtain mean discrepancies of {m["scot"]["mean_deg"]:.2f}° and {m["coherence"]["mean_deg"]:.2f}°, respectively. Complete localization statistics appear in Table II.')
        value['RECORDING_RESULTS']=(f'DCCR reduces the recording-mean discrepancy relative to SRP-PHAT in {better} of the four aircraft recordings. The paired recording differences range from {min(diffs.values()):+.2f}° to {max(diffs.values()):+.2f}° (Table III). '
            f'The four-candidate oracle has a mean discrepancy of {oracle["mean_deg"]:.2f}° and a within-10° fraction of {100*oracle["within10"]:.1f}%. This diagnostic uses evaluation references to choose the best candidate after inference; it describes proposal coverage and is not attainable-estimator performance.')
        value['DETECTION_RESULTS']=(f'DCCR detects {r["detected_positive"]}/600 aircraft windows and produces {r["false_positive"]}/200 background false alarms, corresponding to {100*r["tpr"]:.1f}% TPR and {100*r["fpr"]:.1f}% FPR. '
            f'The TPRs at P2 and P3 are {100*group_tpr[2]:.1f}% and {100*group_tpr[3]:.1f}%; their background FPRs are {100*group_fpr[2]:.1f}% and {100*group_fpr[3]:.1f}%. '
            'These group results show the behavior of a fixed empirical threshold across observation intervals. The nominal 5% calibration setting cannot replace the measured false-alarm rates.')
        value['JOINT_RESULTS']=(f'With the full DCCR detector held fixed, joint detection and localization within 10° is {100*same:.1f}% for SRP-PHAT bearings and {100*r["joint10"]:.1f}% for DCCR bearings, a change of {100*(r["joint10"]-same):+.1f} percentage points. '
            f'Both use the same {r["detected_positive"]} detected aircraft windows, so the difference arises from direction selection. The separately reported 600-window localization statistics still include missed detections.')
        value['ABLATION_RESULTS']=(f'Removing wrong-direction training negatives from aircraft recordings yields a mean discrepancy of {a["mean_deg"]:.2f}°, compared with {r["mean_deg"]:.2f}° for the full model; the values agree at the displayed precision. '
            f'The ablation obtains {100*a["tpr"]:.1f}% TPR and {100*a["fpr"]:.1f}% FPR. '
            f'The full model detects {r["detected_positive"]-a["detected_positive"]} additional aircraft windows at the same false-alarm count. The models select different directions in only three aircraft windows, all with discrepancies exceeding 10°. '
            'Thus the measured benefit of hard negatives concerns detection at this calibrated operating point, not bearing accuracy; a separate localization gain from this component is not established.')
        value['TIMING_RESULTS']=(f'DCCR has median and 95th-percentile computation times of {r["compute_ms_median"]:.1f} and {r["compute_ms_p95"]:.1f} ms per observation; the corresponding SRP-PHAT values are {p["compute_ms_median"]:.1f} and {p["compute_ms_p95"]:.1f} ms. '
            'These times include resampling and the cross-spectral front end, exclude file I/O, and are additional to the 200 ms acquisition window. Refining four candidates and computing their directional features increases processing cost. The current serial implementation cannot sustain five observations per second even on this workstation; real-time operation is therefore not demonstrated.')
        value['CONCLUSION']=(f'DCCR combines four SRP-PHAT proposals with a compact supervised score over 24 directional coherence bands. On held-out field recordings at nominal ranges of 150 and 200 m, mean discrepancy from nominal reference directions changes from {p["mean_deg"]:.2f}° for SRP-PHAT to {r["mean_deg"]:.2f}°, '
            f'with {100*r["tpr"]:.1f}% detection and {100*r["fpr"]:.1f}% background false alarms. Under a shared detector gate, joint success within 10° changes from {100*same:.1f}% to {100*r["joint10"]:.1f}%. '
            'The method makes source association an explicit candidate-conditioned learning problem and provides a complete reproducible implementation. Proposal coverage, nominal-reference accuracy, background calibration and the single-aircraft, single-day acquisition constrain its demonstrated scope.')
    return value

def figures(s,rows,lang):
    zh=lang=='zh';names=ZH_NAMES if zh else NAMES
    font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc') if zh else FontProperties(family='DejaVu Sans')
    plt.rcParams.update({'font.family':font.get_name(),'font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelsize':8.5,'axes.titlesize':9,'legend.fontsize':7,'savefig.dpi':300,'axes.unicode_minus':False})
    folder=ROOT/'figures/field';folder.mkdir(parents=True,exist_ok=True)
    xyz=geometry(ROOT/recordings()[0]['path']);model=dict(np.load(OUT/'discriminative_model.npz'))
    fig,axs=plt.subplots(1,2,figsize=(6.65,2.7),layout='constrained')
    ax=axs[0];ax.scatter(xyz[:,0],xyz[:,1],s=8,c='#215A77',edgecolors='none')
    ax.add_patch(plt.Circle((0,0),.15,fill=False,lw=.65,color='#555555'))
    ax.annotate('',xy=(0,-.20),xytext=(0,-.155),arrowprops=dict(arrowstyle='->',lw=.8))
    ax.text(.017,-.185,'0°',va='center')
    ax.set(aspect='equal',xlabel='原生 x 坐标 (m)' if zh else 'Native x (m)',ylabel='原生 y 坐标 (m)' if zh else 'Native y (m)',
           title='(a) 208通道阵列' if zh else '(a) 208-channel array',xlim=(-.18,.18),ylim=(-.21,.18))
    ax=axs[1];freq=np.arange(24)*.3+.45;coef=model['coef']
    ax.bar(freq,coef,width=.24,color=np.where(coef>=0,'#005A98','#AB5864'))
    ax.axhline(0,color='black',lw=.5)
    ax.set(xlabel='频带中心 (kHz)' if zh else 'Band center (kHz)',ylabel='标准化特征系数' if zh else 'Standardized-feature coefficient',
           title='(b) 仅由开发数据学习' if zh else '(b) Learned on development data')
    fig.savefig(folder/f'geometry_weights_{lang}.png');fig.savefig(folder/f'geometry_weights_{lang}.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(6.65,3.0),layout='constrained')
    for k in ORDER:
        err=sorted(float(r['error_deg']) for r in rows if r['method']==k and r['split']=='test' and int(r['positive']))
        axs[0].plot(err,np.arange(1,len(err)+1)/len(err),color=COLORS[k],lw=1.5 if k=='ranker' else .9,label=names[k])
        v=s['methods'][k]
        markers={'phat':'o','scot':'v','coherence':'D','reference':'^','ranker':'s','no_hard_negatives':'P'}
        axs[1].scatter(100*v['fpr'],100*v['tpr'],s=38 if k=='ranker' else 27,color=COLORS[k],marker=markers[k])
    axs[0].set_xscale('symlog',linthresh=1);axs[0].set_xticks([0,1,3,10,30,90,180]);axs[0].set_xticklabels(['0','1','3','10','30','90','180'])
    axs[0].set(xlim=(0,180),ylim=(0,1.02),xlabel='角偏差 (°)' if zh else 'Angular discrepancy (°)',
               ylabel='累计比例' if zh else 'Cumulative fraction',title='(a) 600个无人机观测窗' if zh else '(a) 600 aircraft windows')
    axs[1].set(xlim=(0,5),ylim=(0,102),xlabel='虚警率 (%)' if zh else 'False-alarm rate (%)',ylabel='检出率 (%)' if zh else 'Detection rate (%)',
               title='(b) 固定标定阈值' if zh else '(b) Fixed calibrated thresholds')
    for ax in axs:ax.grid(alpha=.2,lw=.5)
    handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
    fig.savefig(folder/f'performance_{lang}.png');fig.savefig(folder/f'performance_{lang}.pdf');plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(6.65,3.9),layout='constrained')
    for ax,rid in zip(axs.ravel(),['s2_uav1','s2_uav2','s3_uav1','s3_uav2']):
        for k in ['phat','ranker']:
            rr=sorted([r for r in rows if r['method']==k and r['id']==rid],key=lambda r:float(r['start_s']))
            ax.plot([float(r['start_s']) for r in rr],[float(r['error_deg']) for r in rr],lw=.8,color=COLORS[k],label=names[k])
        ax.set_yscale('symlog',linthresh=1);ax.set_yticks([0,1,5,20,90]);ax.set_yticklabels(['0','1','5','20','90'])
        ax.set(xlim=(0,30),ylim=(0,180),title=rid.replace('s2_','P2 ').replace('s3_','P3 ').replace('uav','录音' if zh else 'take '),
               xlabel='时间 (s)' if zh else 'Time (s)',ylabel='角偏差 (°)' if zh else 'Angular discrepancy (°)')
        ax.grid(alpha=.2,lw=.5)
    handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
    fig.savefig(folder/f'recordings_{lang}.png');fig.savefig(folder/f'recordings_{lang}.pdf');plt.close(fig)

def main():
    s=json.loads((OUT/'summary.json').read_text())
    rows=list(csv.DictReader((OUT/'predictions.csv').open(encoding='utf-8')))
    refs=references()
    for lang in ['en','zh']:
        values=text_values(s,lang,refs)
        text=(ROOT/f'paper/field_{lang}_template.md').read_text(encoding='utf-8')
        for key,val in values.items():text=text.replace('{{'+key+'}}',val)
        assert '{{' not in text
        (ROOT/f'paper/field_{lang}.md').write_text(text,encoding='utf-8')
        figures(s,rows,lang)
    eqdir=ROOT/'results/document_qa/field/equations';eqdir.mkdir(parents=True,exist_ok=True)
    plt.rcParams['mathtext.fontset']='stix'
    for exp in re.findall(r'\$\$\s*(.*?)\s*\$\$',text,re.S):
        key=hashlib.sha256(exp.encode()).hexdigest()[:20]
        math_to_image('$'+exp+'$',eqdir/(key+'.png'),prop=FontProperties(family='STIXGeneral',size=12),dpi=450,format='png',color='black')
    print('Both manuscripts, 6 figures and 9 equations generated from frozen results.')

if __name__=='__main__':main()
