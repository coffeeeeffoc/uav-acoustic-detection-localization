"""Apply the bilingual editorial revision without changing measured results."""
from pathlib import Path
import ast, csv, hashlib, json, re, zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).parent
backup=QA/'before_revision.zip'
if not backup.exists():
    with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
        for p in (ROOT/'paper').iterdir():
            if p.is_file():z.write(p,p.relative_to(ROOT))

changes={
'en':[
('Acoustic direction finding can', 'Coherent environmental sources can dominate acoustic spatial maps and cause incorrect association of an unmanned aerial vehicle with a bearing. This study proposes direction-conditioned coherence ranking, which scores four steered-response-power candidates using 24 frequency bands of directional coherence. A class-balanced ridge model learns from background observations and competing directions within aircraft recordings. Evaluation uses outdoor measurements from a 208-channel planar array, with the 100 m position reserved for development and the 150 and 200 m positions held out for testing. Over 600 aircraft observations, the mean angular discrepancy from nominal reference directions decreases from {{PHAT_MEAN}} to {{RANK_MEAN}} degrees relative to the phase-transform baseline. The proposed method achieves a detection rate of {{RANK_TPR}} percent and a false-alarm rate of {{RANK_FPR}} percent over 200 background observations. Under a shared detection gate, the proportion of observations detected and localized within 10 degrees increases from {{SHARED_PHAT_JOINT}} to {{RANK_JOINT}} percent. The improvement primarily reflects fewer large direction errors. These results support candidate-conditioned source association under the evaluated conditions; generalization remains limited by nominal static references, temporally correlated observations, one aircraft model, one acquisition day, and location-specific background calibration.'),
('Passive acoustic sensing provides', 'Passive acoustic sensing estimates the presence and bearing of an unmanned aerial vehicle (UAV) from its radiated sound [1]. In outdoor environments, a microphone array also receives wind noise and emissions from vehicles and machinery. A spatially coherent component may produce a strong array response regardless of whether it originates from the aircraft. UAV sensing therefore requires both detection of aircraft-related acoustic evidence and association of that evidence with a direction.'),
('Generalized cross-correlation and', 'Generalized cross-correlation and steered response power (SRP) combine intermicrophone delay information for source localization [2], [3]. The phase transform (PHAT) emphasizes phase alignment by normalizing cross-spectral magnitudes. Consequently, frequency bins with little UAV energy can still influence the spatial maximum. Existing SRP extensions address spectral reliability, spatial search, and multiple sources [4]. A further association problem remains when the UAV direction forms a secondary peak: a positive scalar detection score applied uniformly to the map leaves the maximizing direction unchanged.'),
('This work addresses that', 'Direction-conditioned coherence ranking (DCCR) addresses this problem by evaluating frequency-dependent evidence separately for each candidate bearing. SRP-PHAT generates four directions from the observed audio. Steered, normalized cross-spectra then describe each candidate through 24 coherence-band features. A class-balanced linear ridge model assigns a score to each feature vector, and the highest-scoring candidate supplies the estimated bearing and acoustic detection score.'),
('The contribution is an explicit', 'The proposed method combines a direction-conditioned representation with competing-direction training examples drawn from the same UAV observations. Its contribution concerns source association using established array-processing operations. A held-out comparison on 208-channel field recordings applies a common detection gate to conventional and ranked bearings, separating changes in direction selection from changes in alarm decisions. The following sections describe the signal representation, model estimation, experimental protocol, and limitations of this comparison.'),
('Knapp and Carter established', 'Knapp and Carter formulated generalized correlation for time-delay estimation [2]. SRP aggregates pairwise delay evidence over a spatial search domain [3], [4]. PHAT, smoothed coherence transform (SCOT), and coherence-based reliability weights differ in their treatment of spectral magnitude and phase. DCCR retains these established operations as its spatial front end and learns an additional candidate-specific score.'),
('Valin et al. incorporated', 'Valin et al. integrated noise-dependent reliability with beamforming and particle-filter tracking [5]. Donohue et al. studied partial phase-transform weighting in reverberant and noisy conditions [6]. Brümann and Doclo examined an auxiliary-microphone formulation for SRP estimation in coherent noise [7]. These approaches improve spatial reliability; the present study instead examines whether a coherent candidate is associated with UAV emissions.'),
('UAV-specific work exploits', 'UAV acoustic localization can exploit rotor-related spectral structure. Uluskan evaluated SRP-PHAT around drone harmonics [8], whereas Yang et al. combined acoustic signal synthesis with neural localization and real-audio evaluation [9]. DCCR uses fixed frequency bands and a compact linear model suitable for the available development recordings. No direct comparison with those trained neural systems is available. DDL and UaVirBASE provide multichannel data for UAV detection or localization [10], [11], illustrating the importance of documented acquisition geometry and reference measurements. The present data support comparison with nominal static bearings but lack synchronized trajectories for tracking evaluation.'),
('Candidate-dependent spectral evidence', 'Unlike a detector applied to a single SRP maximum, DCCR compares several directions through their steered spectral responses. Positive and wrong-direction examples from the same UAV observation share the recording background and overall gain. Their labels therefore require direction-dependent information, although residual dependencies on the acquisition conditions may remain.'),
('The model receives only these', 'Only the 24 coherence-band values enter the regression model. Absolute power, direction coordinates, recording identifiers, range, and visual information are excluded. Array geometry enters through physical steering. Fig. 1 shows the array layout and the fitted frequency-band coefficients.'),
('The method estimates a bearing', 'The evaluated outputs are a bearing and an acoustic-presence score for a single UAV. Range estimation, identity recognition, simultaneous-UAV separation, and trajectory tracking lie outside the experiment. Validation on further aircraft, acquisition sessions, and calibrated trajectories is required to assess transfer beyond the present recordings.'),
('The reproducibility package contains', 'The accompanying reproducibility materials include the array reader, training and inference code, fitted models, development-selection records, input hashes, per-window predictions, and table and figure generation scripts. The field analysis uses the original multichannel recordings and acquisition documentation. Access to those recordings is subject to the original provider\'s distribution conditions.'),
],
'zh':[
('即使无人机声音可被接收', '相干环境声源可能主导声学空间图，导致无人机声音与估计方向之间的错误关联。本文提出方向条件相干谱排序方法，利用24个频带的方向相干特征，对导向响应功率生成的四个候选方向评分。类别平衡岭回归模型同时使用背景观测和无人机观测内的竞争方向进行训练。实验采用208通道平面阵列的室外实测录音，100 m位置用于开发，150 m和200 m位置用于保留测试。在600个无人机观测窗上，相对于标称参考方向的平均角偏差由相位变换基线的{{PHAT_MEAN}}度降至{{RANK_MEAN}}度。所提方法的检出率为{{RANK_TPR}}%，在200个背景观测窗上的虚警率为{{RANK_FPR}}%。使用同一检测门控时，检出且定位偏差不超过10度的观测窗比例由{{SHARED_PHAT_JOINT}}%升至{{RANK_JOINT}}%。改善主要体现为大角度偏差的减少。结果支持所测条件下的候选方向关联方法；标称静态参考、观测窗的时间相关性、单一机型、单日采集及测量组内背景标定限制了结论的推广范围。'),
('被动声学感知能够', '被动声学感知利用无人机（unmanned aerial vehicle，UAV）辐射的声音估计其存在状态与方向[1]。室外麦克风阵列同时接收风噪声以及车辆和机械设备的声音。具有空间相干性的成分均可能产生较强阵列响应，其声源并不一定是无人机。因此，无人机声学感知需要同时解决目标相关声学证据的检测及其方向关联问题。'),
('广义互相关和导向', '广义互相关和导向响应功率（steered response power，SRP）通过融合麦克风间时延进行声源定位[2]、[3]。相位变换（phase transform，PHAT）对互谱幅值归一化，突出相位一致性，但无人机能量较少的频点仍可能影响空间最大值。已有SRP扩展研究涉及频谱可靠性、空间搜索和多声源处理[4]。当无人机方向仅对应次强峰时，向整幅空间图施加统一的正检测分数不会改变最大值位置，因而仍需解决候选峰与目标声源之间的关联问题。'),
('本文采用紧凑监督模型', '方向条件相干谱排序（direction-conditioned coherence ranking，DCCR）通过分别评价各候选方向的频率相关证据处理上述问题。SRP-PHAT首先从观测音频生成四个方向，再以导向归一化互谱构造各候选的24维相干频带特征。类别平衡线性岭回归模型计算候选评分，得分最高的候选同时给出估计方向和声学检测分数。'),
('本文的贡献是在', '所提方法将方向条件特征与同一无人机观测中的竞争方向训练样本相结合，其贡献在于利用已有阵列处理操作实现声源关联。基于208通道实测录音的保留比较对传统方向与排序后方向使用同一检测门控，以区分方向选择和报警决策的影响。下文依次介绍信号表示、模型估计、实验协议及比较结果的适用范围。'),
('Knapp和Carter建立', 'Knapp和Carter建立了用于时延估计的广义相关框架[2]。SRP在空间搜索域内汇总麦克风对的时延证据[3]、[4]。PHAT、平滑相干变换（smoothed coherence transform，SCOT）及相干性加权在频谱幅值和相位信息的处理方式上有所不同。DCCR保留这些已有操作作为空间处理前端，并学习额外的候选方向评分。'),
('Valin等将噪声', 'Valin等将噪声相关可靠性与波束形成及粒子滤波跟踪结合[5]。Donohue等研究了混响和噪声条件下的部分相位变换加权[6]。Brümann和Doclo研究了相干噪声环境中的辅助麦克风SRP估计方案[7]。这些方法侧重空间响应的可靠性，本文则考察具有相干性的候选是否与无人机声辐射相关。'),
('面向无人机的研究利用', '无人机声学定位可利用旋翼相关的频谱结构。Uluskan研究了无人机谐波邻域的SRP-PHAT[8]，Yang等将声信号合成与神经网络定位及真实音频评价相结合[9]。DCCR采用固定频带和适合现有开发录音规模的紧凑线性模型，本文未与上述训练后的神经网络系统进行直接比较。DDL和UaVirBASE提供了用于无人机检测或定位的多通道数据[10]、[11]，体现了采集几何与参考测量记录的重要性。现有数据支持标称静态方向比较，但缺乏用于跟踪评价的同步轨迹。'),
('候选方向相关的频谱', 'DCCR通过导向后的频谱响应比较多个方向。来自同一无人机观测的正方向与错误方向样本共享录音背景和总体增益，因此需要方向相关信息才能区分。该训练设计增强了学习目标与方向关联的联系，但仍可能受到采集条件相关性的影响。'),
('模型只接收这24个', '回归模型仅接收24个相干频带数值，不使用绝对功率、方向坐标、录音标识、距离或视觉信息。阵列几何通过物理导向运算进入处理链。图1给出了阵列布局及拟合得到的频带系数。'),
('该方法估计方向和经验', '本文评价的输出为单架无人机的方向及声学存在评分，实验范围不包括距离估计、身份识别、多架无人机分离及轨迹跟踪。模型对其他机型、采集时段和标定轨迹的适用性仍需进一步实验验证。'),
('复现材料包含', '随文复现资料包括阵列读取程序、训练与推理代码、拟合模型、开发选择记录、输入摘要、逐窗预测及图表生成脚本。实测分析使用原始多通道录音和采集文档，录音的访问与分发遵循原始提供方的条件。'),
]
}
for lang,edits in changes.items():
    p=ROOT/f'paper/field_{lang}_template.md'
    with zipfile.ZipFile(backup) as z:text=z.read(p.relative_to(ROOT).as_posix()).decode('utf-8')
    paragraphs=text.split('\n\n')
    for prefix,new in edits:
        ids=[i for i,x in enumerate(paragraphs) if x.startswith(prefix)]
        assert len(ids)==1,(lang,prefix,ids)
        paragraphs[ids[0]]=new
    text='\n\n'.join(paragraphs)
    if lang=='en':
        text=text.replace('Small UAVs Using Direction Conditioned','Small Unmanned Aerial Vehicles Using Direction Conditioned')
        text=text.replace('**Index terms** —','**Keywords** —')
        text=text.replace('![Figure ', '![Fig. ')
        text=text.replace('{{RECORDING_TABLE}}\n\n', '{{RECORDING_TABLE}}\n\nFig. 2 summarizes the angular-discrepancy distributions and the independently calibrated detection operating points.\n\n')
        text=text.replace('{{TIMING_RESULTS}}\n\n', '{{TIMING_RESULTS}}\n\nFig. 3 presents the window-wise angular discrepancies for each held-out UAV recording.\n\n')
        text=text.replace('Detection rate and false-alarm rate use', 'The true-positive rate (TPR) and false-positive rate (FPR), denoting detection and false alarms, use')
        text=text.replace('Positive differences indicate an improvement over SRP-PHAT.', 'Positive differences indicate an improvement over SRP-PHAT. Differences are computed before rounding.')
    else:
        text=text.replace('\n\n英文论文中文译稿','')
        text=text.replace('{{RECORDING_TABLE}}\n\n', '{{RECORDING_TABLE}}\n\n图2汇总了角偏差分布及各方法独立标定后的检测工作点。\n\n')
        text=text.replace('{{TIMING_RESULTS}}\n\n', '{{TIMING_RESULTS}}\n\n图3给出了各段保留无人机录音的逐窗角偏差。\n\n')
        text=text.replace('正差值表示相对于SRP-PHAT有所改善。', '正差值表示相对于SRP-PHAT有所改善，差值在四舍五入前计算。')
    # Defer the first wide figure until the development examples have been defined.
    figure=re.search(r'!\[[^\n]+\]\(\.\./figures/field/geometry_weights_[^)]+\)',text).group()
    text=text.replace(figure+'\n\n','')
    heading='### B 正则化排序模型' if lang=='zh' else '### B Regularized ranking model'
    text=text.replace(heading,figure+'\n\n'+heading)
    p.write_text(text,encoding='utf-8')

# Use the existing result-formatting functions without importing the acoustic pipeline.
source=(ROOT/'code/finalize_field_paper.py').read_text(encoding='utf-8')
tree=ast.parse(source)
names={'NAMES','ZH_NAMES','ORDER','COLORS'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'table','references','text_values'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
scope={'ROOT':ROOT,'json':json,'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'finalize_field_paper.py','exec'),scope)
refs=scope['references']()
summary=json.loads((ROOT/'results/field/summary.json').read_text())
for lang in ['en','zh']:
    text=(ROOT/f'paper/field_{lang}_template.md').read_text(encoding='utf-8')
    for k,v in scope['text_values'](summary,lang,refs).items():text=text.replace('{{'+k+'}}',v)
    assert '{{' not in text
    (ROOT/f'paper/field_{lang}.md').write_text(text,encoding='utf-8')
print('Revised bilingual sources using unchanged measured result values.')
