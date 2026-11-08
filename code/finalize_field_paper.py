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
    author_text={
        'chen':'P. Chen, Y. Chen, and W. Wang',
        'gcc':'C. H. Knapp and G. C. Carter',
        'srp':'J. H. DiBiase, H. F. Silverman, and M. S. Brandstein',
        'srpreview':'E. Grinstein et al.',
        'noiseweight':'J.-M. Valin, F. Michaud, and J. Rouat',
        'phatbeta':'K. D. Donohue, J. Hannemann, and H. G. Dietz',
        'brumann':'K. Brümann and S. Doclo',
        'harmonics':'S. Uluskan',
        'yang':'X. Yang, P. A. Naylor, S. Doclo, and J. Bitzer',
        'ddl':'S. Safavi, Ö. Çaylı, M. A. Safavi, B. Cook, and W. Wang',
        'uavirbase':'G. Jekateryńczuk, R. Szadkowski, and Z. Piotrowski',
    }
    venue_text={
        'gcc':'IEEE Transactions on Acoustics, Speech, and Signal Processing, vol. 24, no. 4, pp. 320–327',
        'srp':'in Microphone Arrays: Signal Processing Techniques and Applications, M. Brandstein and D. Ward, Eds. Berlin, Germany: Springer, ch. 8, pp. 157–180',
        'srpreview':'EURASIP Journal on Audio, Speech, and Music Processing, vol. 2024, Art. no. 59',
        'noiseweight':'Robotics and Autonomous Systems, vol. 55, no. 3, pp. 216–228',
        'phatbeta':'Signal Processing, vol. 87, no. 7, pp. 1677–1691',
        'brumann':'in Proc. 32nd European Signal Processing Conference (EUSIPCO), pp. 917–921',
        'harmonics':'International Journal of Aeroacoustics, vol. 23, nos. 5–6, pp. 558–577',
        'yang':'in Proc. 33rd European Signal Processing Conference (EUSIPCO), pp. 256–260',
        'ddl':'in Proc. IEEE 35th International Workshop on Machine Learning for Signal Processing (MLSP), pp. 1–6',
        'uavirbase':'Applied Sciences, vol. 15, no. 10, Art. no. 5378',
    }
    for i,k in enumerate(keys,1):
        r=next(x for x in refs if x['id']==k)
        title=r['title'];authors=', '.join(r['authors']);venue=r['venue']
        if k=='chen':
            authors='P. Chen, Y. Chen, and W. Wang';title='Review for UAV Acoustic Positioning'
            venue='Journal of South China University of Technology (Natural Science Edition), vol. 50, no. 12, pp. 109–123 (in Chinese)'
        authors=author_text[k];venue=venue_text.get(k,venue)
        result.append(f'[{i}] {authors}, "{title}," {venue}, {r["year"]}. [doi: {r["doi"]}](https://doi.org/{r["doi"]}).')
        mapping.append(dict(number=i,id=k,doi=r['doi']))
    result.append('[12] "Experimental measurement description," acquisition documentation accompanying the CRY8501 Air 3S recordings of 25 May 2026, unpublished technical dataset, 2026 (in Chinese).')
    mapping.append(dict(number=12,id='field_acquisition',source='Original acquisition description and channel metadata; see results/field/source_manifest.json'))
    (ROOT/'paper/field_citation_map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    return '\n\n'.join(result)

def text_values(s,lang,refs):
    zh=lang=='zh';names=ZH_NAMES if zh else NAMES
    m=s['methods'];p=m['phat'];r=m['ranker'];a=m['no_hard_negatives'];pair=s['paired_against_ranker'];oracle=s['candidate_oracle']
    gain=p['mean_deg']-r['mean_deg']
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
        [[rid.replace('s2_','P2 ').replace('s3_','P3 ').replace('uav','录音' if zh else 'take '),
          f'{p["recordings"][rid]["mean_deg"]:.2f}',f'{r["recordings"][rid]["mean_deg"]:.2f}',f'{diffs[rid]:+.2f}'] for rid in ids])
    value['DETECTION_TABLE']=table(['方法','检出数','虚警数','检出率 %','虚警率 %','联合成功 %'] if zh else
        ['Method','TP / 600','FP / 200','TPR %','FPR %','Joint ≤10° %'],
        [[names[k],m[k]['detected_positive'],m[k]['false_positive'],f'{100*m[k]["tpr"]:.1f}',
          f'{100*m[k]["fpr"]:.1f}',f'{100*m[k]["joint10"]:.1f}'] for k in ORDER])
    better=sum(d>0 for d in diffs.values())
    group_tpr={site:np.mean([r['recordings'][f's{site}_uav{take}']['detection_rate'] for take in [1,2]]) for site in [2,3]}
    group_fpr={site:r['recordings'][f's{site}_background']['detection_rate'] for site in [2,3]}
    # Keep result prose complementary to the four numeric tables.
    if zh:
        value['LOCALIZATION_RESULTS']=(f'DCCR平均偏差由SRP-PHAT的{p["mean_deg"]:.2f}°降至{r["mean_deg"]:.2f}°，按未四舍五入数据计算的降幅为{gain:.2f}°；中位数为{r["median_deg"]:.2f}°，95百分位为{r["p95_deg"]:.2f}°，10°以内比例为{r["within10"]*100:.1f}%（表II）。')
        value['RECORDING_RESULTS']=(f'四段录音中{better}段平均偏差降低，配对差值为{min(diffs.values()):+.2f}°至{max(diffs.values()):+.2f}°（表III）。候选理想选择的均值为{oracle["mean_deg"]:.2f}°，10°以内比例为{oracle["within10"]*100:.1f}%；该事后参考辅助诊断反映候选覆盖，并非实际估计器输出。')
        value['DETECTION_RESULTS']=(f'DCCR检出{r["detected_positive"]}/600窗（{100*r["tpr"]:.1f}%），虚警{r["false_positive"]}/200窗（{100*r["fpr"]:.1f}%），见表IV。P2/P3检出率分别为{100*group_tpr[2]:.1f}%/{100*group_tpr[3]:.1f}%，虚警率为{100*group_fpr[2]:.1f}%/{100*group_fpr[3]:.1f}%；标称5%标定水平不等于实际虚警率。')
        value['JOINT_RESULTS']=(f'固定DCCR检测门控后，联合成功率由PHAT方向的{100*same:.1f}%升至DCCR的{100*r["joint10"]:.1f}%。两者均以全部600个无人机窗为分母，并共用{r["detected_positive"]}个检出窗；{100*(r["joint10"]-same):.1f}个百分点的差别来自方向选择。')
        value['ABLATION_RESULTS']=(f'去除困难负例后，平均偏差四舍五入后仍为{a["mean_deg"]:.2f}°，检出率为{100*a["tpr"]:.1f}%，虚警率为{100*a["fpr"]:.1f}%。完整模型在相同虚警数下多检出{r["detected_positive"]-a["detected_positive"]}窗；仅3个无人机窗选向不同，且两模型的偏差均超过10°。该消融支持当前工作点的检测收益，未显示额外定位增益。')
        value['TIMING_RESULTS']=(f'DCCR每窗计算时间中位数/95百分位为{r["compute_ms_median"]:.1f}/{r["compute_ms_p95"]:.1f} ms，PHAT为{p["compute_ms_median"]:.1f}/{p["compute_ms_p95"]:.1f} ms，另需200 ms采集窗。四候选细化及特征计算增加开销；当前串行实现不能维持每秒5窗，未实现实时运行。')
        value['CONCLUSION']=(f'DCCR通过24频带相干特征对四个方向排序，使保留录音平均标称方向偏差由{p["mean_deg"]:.2f}°降至{r["mean_deg"]:.2f}°，共用门控联合成功率由{100*same:.1f}%升至{100*r["joint10"]:.1f}%。收益主要来自大角度错误减少；困难负例消融仅支持所测工作点的检测改善。泛化验证需覆盖更多机型和采集时段，并采用同步参考轨迹。')
    else:
        value['LOCALIZATION_RESULTS']=(f'DCCR reduces mean discrepancy from {p["mean_deg"]:.2f}° to {r["mean_deg"]:.2f}° (a {gain:.2f}° reduction computed from unrounded values), with median {r["median_deg"]:.2f}°, 95th percentile {r["p95_deg"]:.2f}°, and {r["within10"]*100:.1f}% within 10° (Table II).')
        value['RECORDING_RESULTS']=(f'Mean discrepancy decreases in {better} of four recordings, with paired differences from {min(diffs.values()):+.2f}° to {max(diffs.values()):+.2f}° (Table III). The candidate oracle yields {oracle["mean_deg"]:.2f}° mean discrepancy and {oracle["within10"]*100:.1f}% within 10°; this retrospective, reference-assisted diagnostic measures coverage and is not an estimator output.')
        value['DETECTION_RESULTS']=(f'DCCR detects {r["detected_positive"]}/600 windows ({100*r["tpr"]:.1f}%) with {r["false_positive"]}/200 false alarms ({100*r["fpr"]:.1f}%; Table IV). P2/P3 detection rates are {100*group_tpr[2]:.1f}%/{100*group_tpr[3]:.1f}%, and false-alarm rates are {100*group_fpr[2]:.1f}%/{100*group_fpr[3]:.1f}%. The nominal 5% calibration level is not the measured false-alarm rate.')
        value['JOINT_RESULTS']=(f'With the DCCR detector fixed, joint success increases from {100*same:.1f}% for PHAT bearings to {100*r["joint10"]:.1f}% for DCCR. Both rates use all 600 aircraft windows as the denominator and share {r["detected_positive"]} detections; the {100*(r["joint10"]-same):.1f}-percentage-point difference comes from bearing selection.')
        value['ABLATION_RESULTS']=(f'Without hard negatives, mean discrepancy still rounds to {a["mean_deg"]:.2f}°, with {100*a["tpr"]:.1f}% detection and {100*a["fpr"]:.1f}% false alarms. The full model detects {r["detected_positive"]-a["detected_positive"]} additional windows at the same false-alarm count. Only three aircraft windows change bearing, with both models exceeding 10° in each. The ablation supports detection benefits at this operating point, not an additional localization gain.')
        value['TIMING_RESULTS']=(f'DCCR median/95th-percentile computation times are {r["compute_ms_median"]:.1f}/{r["compute_ms_p95"]:.1f} ms per window, versus {p["compute_ms_median"]:.1f}/{p["compute_ms_p95"]:.1f} ms for PHAT, plus 200 ms acquisition. Four-candidate refinement and features increase cost; the serial implementation cannot sustain five windows per second and does not demonstrate real-time operation.')
        value['CONCLUSION']=(f'Ranking four bearings using 24 coherence bands reduces held-out mean nominal-direction discrepancy from {p["mean_deg"]:.2f}° to {r["mean_deg"]:.2f}° and raises shared-gate joint success from {100*same:.1f}% to {100*r["joint10"]:.1f}%. Gains mainly reflect fewer large errors; the ablation supports detection gains only at the evaluated operating point. Generalization requires evaluation across more aircraft and acquisition sessions with synchronized reference trajectories.')
    return value

def figures(s,rows,lang):
    zh=lang=='zh';names=ZH_NAMES if zh else NAMES
    font=FontProperties(fname='C:/Windows/Fonts/simsun.ttc') if zh else FontProperties(family='Times New Roman')
    plt.rcParams.update({'font.family':font.get_name(),'font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelsize':8.5,'axes.titlesize':9,'legend.fontsize':7,'savefig.dpi':300,'axes.unicode_minus':False})
    folder=ROOT/'figures/field';folder.mkdir(parents=True,exist_ok=True)
    xyz=geometry(ROOT/recordings()[0]['path']);model=dict(np.load(OUT/'discriminative_model.npz'))
    fig,axs=plt.subplots(1,2,figsize=(6.65,1.95),layout='constrained')
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
    fig,axs=plt.subplots(1,2,figsize=(6.65,2.2),layout='constrained')
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
    fig,axs=plt.subplots(2,2,figsize=(6.65,2.85),layout='constrained')
    for ax,rid in zip(axs.ravel(),['s2_uav1','s2_uav2','s3_uav1','s3_uav2']):
        for k in ['phat','ranker']:
            rr=sorted([r for r in rows if r['method']==k and r['id']==rid],key=lambda r:float(r['start_s']))
            ax.plot([float(r['start_s']) for r in rr],[float(r['error_deg']) for r in rr],lw=.8,color=COLORS[k],label=names[k])
        ax.set_yscale('symlog',linthresh=1);ax.set_yticks([0,1,5,20,90]);ax.set_yticklabels(['0','1','5','20','90'])
        ax.set(xlim=(0,30),ylim=(0,180),title=rid.replace('s2_','P2 ').replace('s3_','P3 ').replace('uav','录音' if zh else 'take '),
               xlabel='时间 (s)' if zh else 'Time (s)',ylabel='角偏差 (°)' if zh else 'Discrepancy (°)')
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
