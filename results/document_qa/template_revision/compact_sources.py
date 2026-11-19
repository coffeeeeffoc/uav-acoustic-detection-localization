"""Prepare the requested five-page revision without changing experimental inputs."""
from pathlib import Path
from zipfile import ZipFile
import ast, csv, json, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).resolve().parent

EN='''# Acoustic Detection and Direction Finding of Small Unmanned Aerial Vehicles Using Direction Conditioned Coherence Ranking

Ju Luo

Nanjing University of Aeronautics and Astronautics

Nanjing, China

## Abstract

Coherent background sources can dominate an acoustic spatial map and obscure an unmanned aerial vehicle (UAV). This study proposes direction-conditioned coherence ranking (DCCR), which scores four steered-response-power candidates using 24 coherence-band features and class-balanced ridge regression. Outdoor recordings from a 208-channel array are partitioned by position: 100 m for development and 150–200 m for held-out evaluation. Across 600 aircraft windows, the mean discrepancy from nominal reference directions decreases from {{PHAT_MEAN}}° to {{RANK_MEAN}}° relative to the phase-transform baseline. Detection reaches {{RANK_TPR}}%, with {{RANK_FPR}}% false alarms over 200 background windows. Under a shared detector, joint detection and localization within 10° increases from {{SHARED_PHAT_JOINT}}% to {{RANK_JOINT}}%. The improvement primarily reflects fewer large direction errors. Evidence remains limited to one aircraft model, one acquisition day, nominal static references, correlated windows, and local background calibration.

**Keywords** — UAV acoustics, microphone array, direction of arrival, spatial coherence, candidate ranking.

## I Introduction

Passive acoustic sensing must detect UAV emissions and associate them with a bearing despite wind, vehicles and machinery [1]. Generalized cross-correlation and steered response power (SRP) combine intermicrophone delay evidence [2], [3]. The phase transform (PHAT) emphasizes phase alignment, allowing coherent non-UAV sources to dominate the spatial response. Existing SRP extensions improve spectral reliability and spatial search [4], but a scalar detector applied uniformly to a spatial map cannot change its maximizing direction.

DCCR instead ranks four SRP-PHAT proposals using directional coherence spectra. Training includes competing directions from the same aircraft observations, which share background and overall gain. The contribution is candidate-conditioned source association using established array operations. A shared-detector comparison separates changes in bearing selection from changes in alarm decisions.

## II Related Work

Noise-dependent beamforming and tracking [5], partial PHAT weighting [6], and auxiliary-microphone SRP in coherent noise [7] improve spatial reliability. UAV-specific approaches exploit rotor harmonics [8] or combine synthesized signals with neural localization [9]. DCCR uses fixed frequency bands and a compact linear model; no direct comparison with those trained neural systems is available. DDL [10] and UaVirBASE [11] provide multichannel UAV data and emphasize documented geometry and reference measurements. The present recordings support nominal static-bearing comparisons but lack synchronized trajectories for tracking evaluation.

## III Signal Model and Directional Representation

### A Array and spectral estimates

For microphone position r_m and far-field unit direction u,

@@1@@

where a_m is a channel gain, v_m is background and sensor noise, and c = 343 m/s. The 0.30 m aperture is small relative to the 100–200 m nominal ranges. Search is restricted to the upper hemisphere to resolve planar-array mirror ambiguity. Clockwise azimuth a starts at native negative y; elevation e is above the array plane:

@@2@@

Each 200 ms window is centered by channel and resampled from 48 to 16 kHz using an anti-aliasing polyphase filter. A 512-sample periodic Hann window and 256-sample hop yield L = 11 centered Fourier frames over 300–7500 Hz. Let X_m(l,k) denote the spectrum at frame l and bin k. The cross- and auto-spectra are

@@3@@

The coherence-normalized and PHAT spectra are

@@4@@

The floor is 10⁻¹² times mean in-band channel power, bounded below by 10⁻³⁰. Averaging precedes normalization to avoid unit-magnitude single-frame coherence. All methods use 1124 pairs spanning all 208 channels: index offsets 17, 35, 53, 71, 89 and 103 modulo 208, deduplicated and restricted to baselines of at least 0.06 m.

### B Proposals and coherence features

For pair set P and frequency set F, the PHAT score is

@@5@@

A 1257-point horizontal direction-cosine grid with 0.05 spacing supplies four maxima separated by at least 12°. Each is refined over ±0.05 at 0.005 spacing, then over ±1° azimuth and ±2° elevation at 0.1° spacing. The search step is not a physical accuracy claim. Eightfold inverse-FFT interpolation and linear lag lookup evaluate the score.

The 300–7500 Hz band is divided into 24 adjacent 300 Hz bands, including the final bin. Candidate u has feature

@@6@@

These signed features retain frequency-dependent directional support. Positive gains cancel away from the numerical floor. The regressor receives only the 24 band values; absolute power, bearing coordinates, recording identity, range and video are excluded. Fig. 1 shows the geometry and fitted coefficients.

## IV Learning and Joint Inference

### A Development and regularization

P1 supplies 300 aircraft and 100 background windows. Reference-steered beams and proposals within 5° of the nominal direction are positive; proposals at least 15° away and background proposals are negative. Intermediate proposals are excluded. Reference beams are used only for training. The resulting 1779 examples comprise 598 positives and 1181 negatives, including 781 wrong directions from aircraft windows.

Two grouped folds each hold out one aircraft recording and one contiguous 10 s half of the development background, keeping each window's examples together. This does not test transfer across independent background recordings. Class-balanced feature means and standard deviations are fitted within each fold, with a standard-deviation floor of 0.01. For standardized z_n and y_n ∈ {−1,+1},

@@7@@

Each class has total weight N/2; the intercept is unpenalized. Balanced validation squared error selects λ = 100 from {0.1, 1, 10, 100}, followed by refitting on all development examples. Removing the 781 wrong-direction negatives gives the ablation model, which independently selects λ = 10 with the same folds and otherwise unchanged inference.

![Fig. 1. Array geometry and coefficients of the standardized coherence bands, fitted using development data only.](../figures/field/geometry_weights_en.png)

### B Selection and calibration

For the four audio-generated candidates,

@@8@@

The selected direction and detection score are u_q* and s_q*. Scores are regression outputs, not posterior probabilities. Each method uses the same 25 separate calibration-background windows per test group. At nominal upper-tail level 0.05, the order-statistic rank ceil(26 × 0.95) is 25; detection requires a score strictly above the calibration maximum. Correlation and nonstationarity prevent interpreting this as a formal 5% false-alarm guarantee. All aircraft windows receive bearings, including missed detections; joint success additionally requires detection and discrepancy ≤10°.

## V Field Experiment

### A Recordings and evaluation split

An upward-facing CRY8501/SonoCam Pi array recorded a DJI Air 3S on 25 May 2026 [12]. Each of three positions supplies two aircraft recordings and one background recording (Table I), with 208 channels at 48 kHz, 16-bit PCM. The nine recordings total 273.75 s. All 1872 WAV files have matched channel lengths and no PCM-boundary clipping; this does not independently establish phase or clock calibration. Nominal bearings come from acquisition diagrams, without synchronized trajectories to quantify hovering displacement or reference uncertainty. Videos are not estimator inputs or ground truth.

**Table I. Recording groups and nominal directions; two aircraft takes and one background recording per group.**

@@TABLE1@@

The first 30 s of each aircraft take is used. Background intervals [0,5), [5,10) and [10,30) s provide subtraction references, threshold calibration and negative evaluation, respectively. P2/P3 contribute 600 aircraft and 200 background windows, plus 50 separate calibration windows. P1 is development only. Local background calibration is an explicit operating assumption.

### B Comparisons and measures

Baselines share geometry, pairs, frequency band and search: SRP-PHAT; smoothed coherence transform (SCOT)-SRP using C_ij; and coherence-weighted PHAT using Q_ij clip((L|C_ij|²−1)/(L−1),0,1). The last weight is a finite-snapshot heuristic, not an unbiased estimate under overlapping frames. A reference-subtraction baseline scales stored background spectra by current-to-reference power ratios, subtracts the cross-spectrum, and weights residual phase by residual coherence and excess-power reliability. The reproduction code specifies its operations; it does not reproduce [5].

Each method is evaluated with its own calibrated detector and with the full DCCR detector held fixed. Candidate-oracle selection uses reference labels only after inference. For estimated and nominal reference unit vectors,

@@9@@

Localization includes all 600 aircraft windows. The true-positive rate (TPR) and false-positive rate (FPR) use aircraft and background windows, respectively. Temporal dependence precludes treating the 800 windows as independent trials; results are descriptive and include four recording-level paired differences. Code, model and input hashes were frozen before held-out execution. Runtime uses an Intel Core i7-12700KF, Python 3.12.14, NumPy 2.2.6 and SciPy 1.15.3, with numerical threads requested as one. Timings include shared front-end overhead, exclude file I/O, and are not an isolated benchmark.

## VI Results

### A Localization

{{LOCALIZATION_RESULTS}}

**Table II. Discrepancies from nominal bearings for all 600 held-out aircraft windows, including missed detections.**

{{LOCALIZATION_TABLE}}

{{RECORDING_RESULTS}}

**Table III. Recording-mean discrepancies. Positive PHAT-minus-DCCR differences indicate improvement and are calculated before rounding.**

{{RECORDING_TABLE}}

Fig. 2 summarizes error distributions and detector operating points.

![Fig. 2. Held-out discrepancy distributions and independently calibrated detection. Angles use a logarithmic scale above 1°; DCCR and its ablation nearly overlap.](../figures/field/performance_en.png)

### B Detection and ablation

{{DETECTION_RESULTS}}

**Table IV. Detection and joint localization with each method's calibrated threshold; TPR uses 600 aircraft windows and FPR uses 200 background windows.**

{{DETECTION_TABLE}}

{{JOINT_RESULTS}}

{{ABLATION_RESULTS}}

{{TIMING_RESULTS}}

Fig. 3 compares corresponding observations without smoothing or tracking.

![Fig. 3. Window-wise discrepancies for the four held-out aircraft recordings; angular axes are logarithmic above 1°.](../figures/field/recordings_en.png)

## VII Discussion

Mean-error reduction reflects fewer large departures rather than uniformly finer estimates: the median changes from 3.49° to 3.47°, and the 95th percentile remains 54.16°. Of 36 DCCR discrepancies above 10°, 34 lack a within-10° candidate; 33 occur in P3 take 2. Candidate coverage therefore limits the remaining tail. A ranker cannot recover a direction absent from its proposals.

Earlier background spectra cannot reproduce changing vehicles or wind, which can explain the limited benefit of direct subtraction. DCCR avoids that subtraction but remains sensitive to aircraft, propagation and sensor changes. Evidence comprises one model, one day and six held-out recordings with local calibration, not 800 independent field trials. Nominal static references do not separate hovering motion, orientation error and phase mismatch. Negative recordings do not exhaust confusing machinery or simultaneous sources. Range, identity, multiple-UAV separation and tracking are outside the evaluated scope. Improved proposal coverage and synchronized references require new development and held-out data.

## VIII Conclusion

{{CONCLUSION}}

## Data and Code Availability

Accompanying materials contain code, fitted models, development records, input hashes, per-window predictions and figure scripts. Original recordings remain subject to their provider's distribution conditions.

## References

{{REFERENCES}}
'''

ZH='''# 基于方向条件相干谱排序的小型无人机声学探测与测向

Ju Luo

南京航空航天大学

南京，中国

## 摘要

相干背景声源可能主导声学空间图并掩盖无人机方向。本文提出方向条件相干谱排序（DCCR），以24个相干频带特征和类别平衡岭回归对四个导向响应功率候选评分。208通道阵列室外录音按位置划分：100 m用于开发，150–200 m用于保留评价。在600个无人机观测窗上，相对于标称方向的平均偏差由相位变换基线的{{PHAT_MEAN}}°降至{{RANK_MEAN}}°；检出率为{{RANK_TPR}}%，200个背景窗上的虚警率为{{RANK_FPR}}%。共用检测门控时，检出且定位偏差不超过10°的比例由{{SHARED_PHAT_JOINT}}%升至{{RANK_JOINT}}%。改善主要体现为大角度错误减少。证据仍限于单一机型、单日采集、标称静态参考、相关观测窗及本地背景标定。

**关键词** — 无人机声学，麦克风阵列，到达方向，空间相干性，候选方向排序。

## I 引言

被动声学感知需要在风、车辆及机械噪声中检出无人机辐射声并确定其方向[1]。广义互相关与导向响应功率（steered response power，SRP）汇总麦克风间时延证据[2]、[3]。相位变换（phase transform，PHAT）强调相位一致性，相干非目标声源也可能主导空间响应。已有SRP扩展改善了频谱可靠性与空间搜索[4]，但对整幅空间图施加相同检测分数不能改变其最大值方向。

DCCR利用方向相干谱对四个SRP-PHAT候选排序。训练包含来自同一无人机观测的竞争方向，其背景和整体增益相同。本文贡献在于以既有阵列运算实现候选方向条件下的声源关联，并通过共用检测器的比较区分方向选择与报警决策的影响。

## II 相关研究

噪声相关波束形成与跟踪[5]、部分PHAT加权[6]及相干噪声中的辅助麦克风SRP[7]均着重改善空间可靠性。无人机专用方法利用旋翼谐波[8]，或结合合成信号与神经网络定位[9]。DCCR采用固定频带和紧凑线性模型，本文未与上述训练后的神经网络系统直接比较。DDL[10]和UaVirBASE[11]提供多通道无人机数据，强调采集几何及参考测量记录。现有录音支持标称静态方向比较，但缺乏用于跟踪评价的同步轨迹。

## III 信号模型与方向特征

### A 阵列与频谱估计

设麦克风位置为r_m，远场单位方向为u，则

@@1@@

其中a_m为通道增益，v_m包含背景与传感器噪声，声速c = 343 m/s。阵列孔径0.30 m远小于100–200 m标称距离。为消除平面阵列的镜像歧义，搜索限定于上半球。方位角a从原生负y方向顺时针计量，俯仰角e相对于阵列平面定义：

@@2@@

每个200 ms观测窗按通道去均值，并通过抗混叠多相滤波由48 kHz重采样至16 kHz。512点周期Hann窗、256点帧移产生L = 11个去均值傅里叶帧，分析范围为300–7500 Hz。设X_m(l,k)为第l帧、第k频点的频谱，则平均互谱与自谱为

@@3@@

相干归一化谱与PHAT谱分别为

@@4@@

数值下限为带内平均通道功率的10⁻¹²倍，且不低于10⁻³⁰。先平均后归一化，避免单帧相干幅值恒为1。所有方法共用覆盖208通道的1124个通道对：按模208的索引偏移17、35、53、71、89和103构造，去重并保留基线不小于0.06 m的通道对。

### B 候选方向与相干特征

对于通道对集合P和频率集合F，PHAT评分为

@@5@@

水平方向余弦网格包含1257点、间隔0.05，保留两两至少相隔12°的四个峰值。各候选在±0.05邻域内以0.005间隔细化，再于方位角±1°、俯仰角±2°内以0.1°间隔细化。该步长不代表物理精度。实现采用八倍插值逆FFT相关表及线性时延查表。

将300–7500 Hz划分为24个相邻300 Hz频带，并包含末端频点。方向u的特征为

@@6@@

这些有符号特征保留随频率变化的方向支持程度。未触及数值下限时，正增益在归一化中抵消。回归模型仅接收24个频带值，不使用绝对功率、方向坐标、录音标识、距离或视频。图1给出了阵列几何和拟合系数。

## IV 模型学习与联合推理

### A 开发样本与正则化

P1包含300个无人机窗及100个背景窗。参考导向波束和偏差不超过5°的候选为正例；偏差至少15°的候选及背景候选为负例；中间区域候选排除。参考波束仅用于训练。1779个样本包括598个正例和1181个负例，后者含781个来自无人机观测的错误方向。

两个分组折各保留一整段无人机录音及开发背景中连续10 s的一半，同一观测窗的样本保持在同一折。这不构成跨独立背景录音的泛化检验。特征均值与标准差在训练折内按类别平衡权重估计，标准差下限为0.01。对标准化特征z_n和标签y_n ∈ {−1,+1}，最小化

@@7@@

各类别权重之和为N/2，截距不正则化。平衡验证平方误差从{0.1，1，10，100}中选择λ = 100，再以全部开发样本拟合。消融模型仅去除781个错误方向负例，按相同分折独立选定λ = 10，其余推理过程不变。

![图1 阵列几何及标准化相干频带的拟合系数，模型仅使用开发数据学习。](../figures/field/geometry_weights_zh.png)

### B 方向选择与标定

对四个由音频产生的候选，计算

@@8@@

所选方向和检测分数为u_q*及s_q*。该分数为回归输出而非后验概率。各方法使用每个测试组内相同的25个独立划分背景窗标定。标称上尾水平为0.05时，顺序统计量秩ceil(26 × 0.95)为25；评分须严格大于标定最大值才判为检出。时间相关与非平稳性使其不具有正式5%虚警保证。所有无人机窗均估计方向，包括漏检窗；联合成功另要求检出且偏差≤10°。

## V 实测实验

### A 录音与评价划分

2026年5月25日，朝向上方的CRY8501/SonoCam Pi阵列采集DJI Air 3S录音[12]。三个位置各含两段无人机录音和一段背景录音（表I），每段208通道、48 kHz、16位PCM。九段录音总计273.75 s。1872个WAV文件通道长度一致，未达到PCM削波边界，但这不独立证明相位或时钟标定准确。标称方向来自采集示意图，缺乏用于量化悬停位移及参考不确定性的同步轨迹。视频既不输入估计器，也不替代真值。

**表I 录音分组及标称方向，各组含两段无人机录音和一段背景录音。**

@@TABLE1@@

每段无人机录音使用前30 s；背景的[0,5)、[5,10)和[10,30) s分别用于谱扣除参考、阈值标定和负例评价。P2/P3提供600个无人机窗及200个背景窗，另有50个标定窗。P1仅用于开发。本地背景标定是明确的运行前提。

### B 比较方法与指标

基线共用几何、通道对、频带和搜索过程：SRP-PHAT；使用C_ij的平滑相干变换（smoothed coherence transform，SCOT）SRP；以及以Q_ij clip((L|C_ij|²−1)/(L−1),0,1)加权的相干PHAT。最后一项为有限快拍启发式，在重叠帧下不是无偏估计。背景扣除基线按当前与参考功率比缩放背景谱，扣除互谱，再由残余相干性及超额功率可靠性加权残余相位。复现代码给出完整运算，该基线并非文献[5]的复现。

分别使用各方法自己的标定检测器及固定的完整DCCR检测器进行比较。候选理想选择仅在推理结束后使用参考标签计算。估计与标称参考单位向量的角偏差为

@@9@@

定位统计包含全部600个无人机窗；检出率及虚警率分别使用无人机和背景窗。800个观测窗存在时间相关性，不能视为独立试验，故采用描述性统计并列出四段录音的配对差值。代码、模型和输入哈希在保留评价前冻结。计时环境为Intel Core i7-12700KF、Python 3.12.14、NumPy 2.2.6和SciPy 1.15.3，数值库请求单线程；计时包含共用前端开销、排除文件读取，非隔离基准测试。

## VI 结果

### A 定位结果

{{LOCALIZATION_RESULTS}}

**表II 全部600个保留无人机窗相对于标称方向的偏差，包含漏检窗。**

{{LOCALIZATION_TABLE}}

{{RECORDING_RESULTS}}

**表III 各录音平均偏差。PHAT减DCCR的正差值表示改善，差值在四舍五入前计算。**

{{RECORDING_TABLE}}

图2汇总角偏差分布及检测工作点。

![图2 保留数据的角偏差分布及独立标定后的检测结果。角度在1°以上采用对数尺度；DCCR与消融模型的分布近乎重合。](../figures/field/performance_zh.png)

### B 检测与消融

{{DETECTION_RESULTS}}

**表IV 各方法独立标定后的检测与联合结果，检出率及虚警率分母分别为600个无人机窗和200个背景窗。**

{{DETECTION_TABLE}}

{{JOINT_RESULTS}}

{{ABLATION_RESULTS}}

{{TIMING_RESULTS}}

图3比较相同观测窗，两种估计器均未采用平滑或跟踪。

![图3 四段保留无人机录音的逐窗偏差，角度轴在1°以上采用对数尺度。](../figures/field/recordings_zh.png)

## VII 讨论

均值改善主要源于大偏差减少，而非所有估计均更精细：中位数由3.49°变为3.47°，95百分位仍为54.16°。36个超过10°的DCCR偏差中，34个没有10°以内候选，33个出现在P3录音2。候选覆盖因而限制了剩余尾部表现；排序器无法恢复候选集中不存在的方向。

较早的背景谱不能重建变化中的车辆或风声，这可解释直接扣除收益有限。DCCR避免该扣除，但仍受机型、传播及传感器变化影响。证据来自单机型、单日及具有本地标定的六段保留录音，不是800次独立现场试验。标称静态参考无法分离悬停运动、朝向误差和相位失配；负例也未穷尽易混淆机械声和同时声源。距离、身份、多无人机分离及跟踪不在评价范围内。改进候选覆盖并引入同步参考需新的开发和保留数据。

## VIII 结论

{{CONCLUSION}}

## 数据与代码可用性

随文资料包含代码、拟合模型、开发记录、输入哈希、逐窗预测及绘图脚本。原始录音的访问和分发遵循其提供方条件。

## 参考文献

{{REFERENCES}}
'''

with ZipFile(QA/'before_five_page_revision.zip') as archive:
    for lang,text in [('en',EN),('zh',ZH)]:
        old=archive.read(f'paper/field_{lang}_template.md').decode('utf-8').replace('\r\n','\n')
        equations=re.findall(r'^\$\$.*?\$\$\s*\(\d+\)',old,re.M)
        assert len(equations)==9
        for n,eq in enumerate(equations,1):text=text.replace(f'@@{n}@@',eq)
        text=text.replace('@@TABLE1@@',re.search(r'(?:^\|[^\n]+\n)+',old,re.M).group().strip())
        assert '@@' not in text
        (ROOT/f'paper/field_{lang}_template.md').write_text(text,encoding='utf-8')

# Reuse the formatter and plotting functions without importing the acoustic runtime.
tree=ast.parse((ROOT/'code/finalize_field_paper.py').read_text(encoding='utf-8'))
names={'NAMES','ZH_NAMES','ORDER','COLORS'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'table','references','text_values','figures'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
geo=next(n for n in ast.parse((ROOT/'code/field_data.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='geometry')
inventory=json.loads((ROOT/'results/field/inventory.json').read_text(encoding='utf-8'))
scope={'ROOT':ROOT,'OUT':ROOT/'results/field','json':json,'np':np,'plt':plt,'FontProperties':FontProperties,'recordings':lambda:inventory['recordings']}
exec(compile(ast.Module(body=[geo]+nodes,type_ignores=[]),'paper-formatters','exec'),scope)
refs=scope['references']();summary=json.loads((ROOT/'results/field/summary.json').read_text())
rows=list(csv.DictReader((ROOT/'results/field/predictions.csv').open(encoding='utf-8')))
for lang in ['en','zh']:
    text=(ROOT/f'paper/field_{lang}_template.md').read_text(encoding='utf-8')
    for k,v in scope['text_values'](summary,lang,refs).items():text=text.replace('{{'+k+'}}',v)
    assert '{{' not in text
    (ROOT/f'paper/field_{lang}.md').write_text(text,encoding='utf-8')
    scope['figures'](summary,rows,lang)
print('Bilingual sources and compact plots rebuilt from unchanged results.')
