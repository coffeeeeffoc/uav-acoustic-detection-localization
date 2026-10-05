"""Insert the frozen experiment's numbers into the bilingual manuscript templates."""
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
s = json.loads((ROOT / 'results/improved/summary.json').read_text(encoding='utf-8'))
loc, det, joint = s['localization'], s['detection'], s['joint']
methods = ('phat', 'coherence', 'harmonic', 'combined', 'no_null', 'proposed')
detectors = ('harmonic_coherence', 'spectral', 'proposed')
scenes = ('sensor_noise', 'wind', 'directional', 'engine')
groups = tuple(det['proposed']['fpr_by_group'])


def table(caption, headers, rows):
    return caption + '\n\n' + '\n'.join('| ' + ' | '.join(row) + ' |' for row in
                                        [headers, ['---'] * len(headers), *rows])


def interval(values, scale=1):
    return f'[{scale * values[0]:.2f}, {scale * values[1]:.2f}]'


p, b = loc['proposed']['overall'], loc['phat']['overall']
gain, ablation, d = s['paired']['proposed'], s['nuller_ablation'], det['proposed']
seq, timing = s['sequences'], s['timing']
values = {
    'PHAT_MEAN': f"{b['mean_deg']:.2f}", 'PROPOSED_MEAN': f"{p['mean_deg']:.2f}",
    'PHAT_WITHIN': f"{100*b['within10_rate']:.1f}", 'PROPOSED_WITHIN': f"{100*p['within10_rate']:.1f}",
    'TPR': f"{100*d['tpr']:.1f}", 'FPR': f"{100*d['fpr']:.1f}",
    'JOINT': f"{100*joint['proposed+proposed']['success_rate']:.1f}",
}
en = {
    'LOCALIZATION_RESULTS': f"Table II reports every positive trial. SCCR reduces the PHAT mean error by {gain['phat_minus_method_mean_deg']:.2f} degrees, with paired 95% CI {interval(gain['ci95'])} degrees, a relative reduction of {100*gain['phat_minus_method_mean_deg']/b['mean_deg']:.1f}%. The within-10-degree rate increases from {100*b['within10_rate']:.1f}% to {100*p['within10_rate']:.1f}%. The suppressed-beam descriptors provide an additional {ablation['no_null_minus_full_mean_deg']:.2f}-degree mean reduction over the otherwise matched 104-feature ranker; its paired 95% CI is {interval(ablation['ci95'])} degrees. This supports candidate conditioning and the suppression descriptors under the tested distribution. Large failures remain: SCCR's 95th-percentile error is {p['p95_deg']:.2f} degrees despite a {p['median_deg']:.2f}-degree median.\n\nThe weighted analytic references have larger overall mean errors than PHAT. Candidate association therefore improves on these particular weighted-peak implementations rather than simply inheriting their average accuracy. Figure 2 shows that gains concentrate at intermediate SNRs. At 5 dB, SCCR and PHAT have identical aggregate mean error; at -15 dB, SCCR still has a 41.07-degree mean error. The method is not uniformly accurate across SNRs.",
    'SCENE_RESULTS': 'Table III locates the principal improvements in competing-source scenes. SCCR lowers mean error from 58.39 to 43.27 degrees for directional broadband interference and from 36.47 to 22.90 degrees for engine-like interference. The latter remains much larger than its 2.71-degree median, indicating occasional severe target-association failures. Wind-like noise is already easy for PHAT; SCCR gives no meaningful mean improvement there. Suppression also has no universal benefit: engine-scene within-10-degree success is 70.8% with all features and 71.6% without suppression, even though the overall mean favors the full model.',
    'DETECTION_RESULTS': f"The proposed detector yields 905/1000 true detections and 108/2000 false alarms. Recall is {100*d['tpr']:.2f}% (95% Wilson CI {interval(d['tpr_ci95'],100)}%) and FPR is {100*d['fpr']:.2f}% (CI {interval(d['fpr_ci95'],100)}%). Table IV shows higher recall and AUC than both the harmonic-coherence reference and the spectral ablation. The full detector gains 7.70 percentage points of recall over the spectral detector, with 0.90 percentage points more false alarms. The comparison uses a common calibration procedure, not identical realized test FPR. At -15 dB its recall is 63.5%; it reaches 92.0% at -10 dB and 99.0% at each higher SNR.\n\nMultiple-source false alarms remain a limitation (Table V). The full detector's single-source and multiple-source FPRs are 2.20% and 8.60%; the spectral detector's are 0.90% and 8.10%. Engine–engine negatives reach 14.00% FPR for the full detector. Thus the nominal 5% calibration level is not a per-environment guarantee. Multiple-source training prevents these conditions from being wholly unseen, but the present ablation does not isolate the causal benefit of that augmentation. Overall FPR is the equally weighted mean over all eight negative groups.",
    'JOINT_RESULTS': f"Table VI separates detector and localizer changes. Replacing the original detector while retaining PHAT increases joint success by {100*joint['detector_gain']['paired_success_gain']:.2f} percentage points (paired 95% CI {interval(joint['detector_gain']['ci95'],100)}). With the proposed detector fixed, replacing PHAT by SCCR adds {100*joint['localizer_gain']['paired_success_gain']:.2f} points (CI {interval(joint['localizer_gain']['ci95'],100)}). Both contributions use all 1000 positive trials as the denominator.\n\n",
    'DYNAMIC_RESULTS': f"On 24 continuous sequences, sequence-averaged raw error is {seq['raw_localization']['phat']['mean_deg']:.2f} degrees for PHAT, {seq['raw_localization']['no_null']['mean_deg']:.2f} degrees without suppression and {seq['raw_localization']['proposed']['mean_deg']:.2f} degrees for SCCR. Complete-sequence bootstrap intervals are wide: {interval(seq['raw_localization']['phat']['ci95'])} degrees for PHAT and {interval(seq['raw_localization']['proposed']['ci95'])} degrees for SCCR. Proposed detection recall/FPR is {100*seq['detection']['proposed']['tpr']:.2f}%/{100*seq['detection']['proposed']['fpr']:.2f}% over 2400 target-present and 480 target-absent frames. These descriptive frame rates do not assume independent neighboring frames. The negative portions use the four original scenes, so their FPR is not an eight-group robustness estimate. These results support per-frame operation on moving-source observations; they do not measure continuity, motion-filter improvement or reliable track persistence.",
    'COMPUTE_RESULTS': f"The proposed-pipeline compute bound has median {timing['proposed_pipeline_upper_bound_ms']['median']:.2f} ms and 95th percentile {timing['proposed_pipeline_upper_bound_ms']['p95']:.2f} ms. Its localization component takes {timing['localizer_ms']['median']:.2f}/{timing['localizer_ms']['p95']:.2f} ms (median/95th percentile); shared feature extraction plus both detector predictions takes {timing['shared_full_and_spectral_detector_ms']['median']:.2f}/{timing['shared_full_and_spectral_detector_ms']['p95']:.2f} ms. PHAT front-end and search take {timing['phat_front_and_search_ms']['median']:.2f}/{timing['phat_front_and_search_ms']['p95']:.2f} ms. SCCR therefore incurs a substantial compute increase over PHAT, while its measured compute remains below the 200 ms block duration on this workstation. This excludes acquisition latency and is not an embedded or hard real-time guarantee.",
    'CONCLUSION': 'Source-conditioned candidate ranking improves acoustic UAV bearing estimation by retaining competing spatial hypotheses and evaluating their ordinary and interference-suppressed spectra. On the frozen independent simulation test, mean spherical error decreases from 25.40 to 18.12 degrees, and a separately calibrated spectral-spatial detector obtains 90.5% recall with 5.4% overall false alarms. Holding that detector fixed, candidate ranking raises joint detection-and-localization success from 64.5% to 72.8%. The suppression ablation supports a modest additional localization benefit. The remaining large-error tail, multiple-source false alarms and simulation-defined class semantics delimit the result. The work establishes an implemented improvement over the specified baselines and a reproducible basis for subsequent field validation.'
}
zh = {
    'LOCALIZATION_RESULTS': f"表 II 纳入全部正例。SCCR 相对 PHAT 的平均误差减少 {gain['phat_minus_method_mean_deg']:.2f} 度，配对 95% 置信区间为 {interval(gain['ci95'])} 度，相对降幅为 {100*gain['phat_minus_method_mean_deg']/b['mean_deg']:.1f}%。误差不超过 10 度的比例从 {100*b['within10_rate']:.1f}% 提高到 {100*p['within10_rate']:.1f}%。与其余设置相同的 104 维排序器相比，加入抑制波束描述后，平均误差进一步减少 {ablation['no_null_minus_full_mean_deg']:.2f} 度，配对 95% 置信区间为 {interval(ablation['ci95'])} 度。这些结果支持候选条件描述与抑制特征在所测分布下的作用。不过，大误差失败仍然存在：SCCR 的中位误差为 {p['median_deg']:.2f} 度，而第 95 百分位误差仍达 {p['p95_deg']:.2f} 度。\n\n解析加权基线的总体平均误差均大于 PHAT。因此，候选关联改善了这些具体加权峰值实现的结果，而非仅仅继承其平均精度。图 2 表明，收益主要集中在中等信噪比。5 dB 时，SCCR 与 PHAT 的总体平均误差相同；-15 dB 时，SCCR 的平均误差仍为 41.07 度。该方法并未在所有信噪比下都获得高精度。",
    'SCENE_RESULTS': '表 III 表明，主要改进来自存在竞争声源的场景。定向宽带干扰下，SCCR 将平均误差从 58.39 度降至 43.27 度；发动机类干扰下，从 36.47 度降至 22.90 度。后者仍明显高于其 2.71 度的中位误差，说明偶发的严重目标关联失败仍然存在。类风噪声对于 PHAT 已较容易，SCCR 在该场景没有实质性的平均误差改善。抑制特征也并非普遍有效：发动机场景中，全特征模型与无抑制模型的 10 度内成功率分别为 70.8% 和 71.6%，尽管总体平均误差仍以全特征模型更优。',
    'DETECTION_RESULTS': f"所提检测器在 1000 个正例中检出 905 个，在 2000 个负例中产生 108 次虚警。召回率为 {100*d['tpr']:.2f}%（95% Wilson 置信区间 {interval(d['tpr_ci95'],100)}%），虚警率为 {100*d['fpr']:.2f}%（置信区间 {interval(d['fpr_ci95'],100)}%）。表 IV 显示，其召回率和 AUC 均高于谐波—相干基线及纯频谱消融模型。相对纯频谱检测器，全特征检测器的召回率提高 7.70 个百分点，同时虚警率增加 0.90 个百分点。比较采用相同的校准程序，并不意味着实际测试虚警率完全相同。-15 dB 时召回率为 63.5%，-10 dB 时达到 92.0%，更高各信噪比下均为 99.0%。\n\n多声源虚警仍是一项限制（表 V）。全特征检测器在单声源和多声源负例上的虚警率分别为 2.20% 和 8.60%，纯频谱检测器则为 0.90% 和 8.10%。全特征检测器在发动机—发动机负例上的虚警率达到 14.00%。因此，标称 5% 校准水平并不保证每种环境的虚警率均为 5%。多声源训练使这些条件不再完全未见，但当前消融并未单独辨识该数据增强的因果收益。总体虚警率是八类负例虚警率的等权平均。",
    'JOINT_RESULTS': f"表 VI 区分检测器与定位器变化的作用。保留 PHAT、仅替换原检测器时，联合成功率提高 {100*joint['detector_gain']['paired_success_gain']:.2f} 个百分点（配对 95% 置信区间 {interval(joint['detector_gain']['ci95'],100)}）。固定所提检测器、将 PHAT 替换为 SCCR 后，再提高 {100*joint['localizer_gain']['paired_success_gain']:.2f} 个百分点（置信区间 {interval(joint['localizer_gain']['ci95'],100)}）。两项比较均以全部 1000 个正例为分母。\n\n",
    'DYNAMIC_RESULTS': f"在 24 条连续序列上，先按序列求平均的原始角误差分别为：PHAT {seq['raw_localization']['phat']['mean_deg']:.2f} 度、无抑制模型 {seq['raw_localization']['no_null']['mean_deg']:.2f} 度、SCCR {seq['raw_localization']['proposed']['mean_deg']:.2f} 度。以完整序列为重采样单位的区间较宽：PHAT 为 {interval(seq['raw_localization']['phat']['ci95'])} 度，SCCR 为 {interval(seq['raw_localization']['proposed']['ci95'])} 度。在 2400 个有目标帧和 480 个无目标帧上，所提检测器的召回率和虚警率分别为 {100*seq['detection']['proposed']['tpr']:.2f}% 和 {100*seq['detection']['proposed']['fpr']:.2f}%。这些帧级比例为描述性统计，不假设相邻帧相互独立。无目标片段仅包含原始四类场景，其虚警率不能作为八类负例鲁棒性估计。这些结果支持算法处理运动声源观测的逐帧能力，但没有衡量输出连续性、运动滤波收益或可靠的轨迹持续性。",
    'COMPUTE_RESULTS': f"所提流程的计算耗时上界中位数为 {timing['proposed_pipeline_upper_bound_ms']['median']:.2f} ms，第 95 百分位为 {timing['proposed_pipeline_upper_bound_ms']['p95']:.2f} ms。其中，定位部分的中位数和第 95 百分位为 {timing['localizer_ms']['median']:.2f}/{timing['localizer_ms']['p95']:.2f} ms；共享特征提取及两个检测器预测为 {timing['shared_full_and_spectral_detector_ms']['median']:.2f}/{timing['shared_full_and_spectral_detector_ms']['p95']:.2f} ms。PHAT 前端与搜索耗时为 {timing['phat_front_and_search_ms']['median']:.2f}/{timing['phat_front_and_search_ms']['p95']:.2f} ms。因此，SCCR 相对 PHAT 增加了明显计算开销，但在该工作站上的实测计算时间仍短于 200 ms 观测块时长。这不包含采集延迟，也不构成嵌入式性能或硬实时保证。",
    'CONCLUSION': '声源条件化候选排序通过保留相互竞争的空间假设，并分析普通波束与干扰抑制波束的声谱，改善了无人机声学测向。在冻结后的独立仿真测试中，平均球面角误差从 25.40 度降至 18.12 度；单独校准的频谱—空间检测器取得 90.5% 召回率和 5.4% 总体虚警率。在固定该检测器时，候选排序将联合检测与定位成功率从 64.5% 提高到 72.8%。抑制特征消融支持其带来幅度较小的额外定位收益。残余大误差尾部、多声源虚警及由仿真模型定义的类别语义限定了结论范围。本研究实现了相对明确基线的算法改进，并为后续现场验证提供了可复现基础。'
}
labels = {
    'en': ['PHAT', 'Coherence', 'Harmonic', 'Combined', 'No suppression', 'SCCR'],
    'zh': ['PHAT', '相干加权', '谐波加权', '联合加权', '无抑制', 'SCCR']}
scene_labels = {'en': ['Sensor noise', 'Wind', 'Broadband', 'Engine'],
                'zh': ['传感器噪声', '类风噪声', '定向宽带', '发动机']}
group_labels = {'en': scene_labels['en'] + ['Engine + engine', 'Broadband + broadband', 'Engine + broadband', 'Engine + broadband + engine'],
                'zh': scene_labels['zh'] + ['发动机 + 发动机', '宽带 + 宽带', '发动机 + 宽带', '发动机 + 宽带 + 发动机']}
det_labels = {'en': ['Harmonic-coherence', 'Spectral', 'Spectral-spatial'],
              'zh': ['谐波—相干', '纯频谱', '频谱—空间']}
for lang, content in [('en', en), ('zh', zh)]:
    is_en = lang == 'en'
    content['LOCALIZATION_TABLE'] = table(
        'Table II. Unconditional localization on 1000 positive trials.' if is_en else '表 II. 全部 1000 个正例上的无条件定位结果。',
        ['Method', 'Mean (deg)', 'Median (deg)', 'P95 (deg)', 'Within 10° (%)'] if is_en else ['方法', '平均值（度）', '中位数（度）', 'P95（度）', '10°内（%）'],
        [[name] + [f"{loc[m]['overall'][k]:.2f}" for k in ('mean_deg','median_deg','p95_deg')] + [f"{100*loc[m]['overall']['within10_rate']:.1f}"] for name,m in zip(labels[lang],methods)])
    content['SCENE_TABLE'] = table(
        'Table III. Mean error by nuisance scene (degrees; 250 trials per row).' if is_en else '表 III. 各干扰场景的平均误差（度；每行 250 次试验）。',
        ['Scene', 'PHAT', 'Combined', 'No suppression', 'SCCR'] if is_en else ['场景', 'PHAT', '联合加权', '无抑制', 'SCCR'],
        [[name] + [f"{loc[m]['by_scene'][scene]['mean_deg']:.2f}" for m in ('phat','combined','no_null','proposed')] for name,scene in zip(scene_labels[lang],scenes)])
    content['DETECTION_TABLE'] = table(
        'Table IV. Detection on 1000 positive and 2000 negative trials; BA denotes balanced accuracy.' if is_en else '表 IV. 1000 个正例和 2000 个负例上的检测结果；BA 为平衡准确率。',
        ['Detector', 'Recall (%)', 'FPR (%)', 'BA (%)', 'AUC'] if is_en else ['检测器', '召回率（%）', 'FPR（%）', 'BA（%）', 'AUC'],
        [[name] + [f"{100*det[m][k]:.2f}" for k in ('tpr','fpr','balanced_accuracy')] + [f"{det[m]['auc']:.3f}"] for name,m in zip(det_labels[lang],detectors)])
    content['FPR_TABLE'] = table(
        'Table V. False-alarm rate by negative group (%; 250 trials each).' if is_en else '表 V. 各类负例的虚警率（%；每类 250 次试验）。',
        ['Negative group'] + det_labels[lang] if is_en else ['负例类别'] + det_labels[lang],
        [[name] + [f"{100*det[m]['fpr_by_group'][group]:.2f}" for m in detectors] for name,group in zip(group_labels[lang],groups)])
    content['JOINT_RESULTS'] += table(
        'Table VI. Detected and localized within 10 degrees; all 1000 positive trials are retained.' if is_en else '表 VI. 检出且定位误差不超过 10 度的联合成功率；保留全部 1000 个正例。',
        ['Detector / localizer', 'Success (%)', '95% Wilson CI (%)'] if is_en else ['检测器 / 定位器', '成功率（%）', '95% Wilson 区间（%）'],
        [[name, f"{100*joint[m]['success_rate']:.2f}", interval(joint[m]['ci95'],100)] for name,m in zip(
            ['Original / PHAT', 'Proposed / PHAT', 'Proposed / SCCR'] if is_en else ['原检测器 / PHAT', '所提检测器 / PHAT', '所提检测器 / SCCR'],
            ('harmonic_coherence+phat','proposed+phat','proposed+proposed'))])

# Preserve the original bibliography exactly, then append verified additional sources.
with zipfile.ZipFile(ROOT / 'paper/controlled_evaluation_v1.zip') as archive:
    old = archive.read('manuscript_en.md').decode('utf-8')
    citation_map = json.loads(archive.read('citation_map.json'))
refs = re.findall(r'^\[(\d+)\] (.*)$', old.split('## References')[1], re.M)
bibliography = {int(n): text for n,text in refs}
bibliography[20] = 'D. Shulman, "EchoHawk: A Reproducible Acoustic Pipeline for Drone Detection, Classification, and Direction-Finding, with a Cautionary Study of Session-Level Data Leakage," arXiv preprint arXiv:2606.29589v2, 2026. [doi: 10.48550/arXiv.2606.29589](https://doi.org/10.48550/arXiv.2606.29589).'
bibliography[21] = 'C. Dreier and M. Vorländer, "Drone auralization model with statistical synthesis of amplitude and frequency modulations," Acta Acustica, vol. 8, article 35, 2024. [doi: 10.1051/aacus/2024026](https://doi.org/10.1051/aacus/2024026).'
citation_map.update(echohawk2026=20, dreier2024=21)
templates = {lang:(ROOT / f'paper/improved_{lang}_draft.md').read_text(encoding='utf-8') for lang in ('en','zh')}
order = list(dict.fromkeys(int(n) for group in re.findall(r'\[([\d, ]+)\]', templates['en']) for n in group.replace(' ','').split(',')))
assert set(order) == set(range(1,22))
renumber = {old:new for new,old in enumerate(order,1)}
for lang, content in [('en', en), ('zh', zh)]:
    text = templates[lang]
    if lang == 'en':
        text = text.replace('The floor limits amplification when the steering vectors are nearly dependent.', 'The floor limits amplification when the steering vectors are nearly dependent. When the floor is active, ideal target gain is (1 - |a_uv|²)/0.1 < 1; the stabilized feature is therefore not distortionless at every frequency.')
    for key,value in {**values, **content}.items():
        text = text.replace('{{' + key + '}}', value)
    assert '{{' not in text
    text = re.sub(r'\[([\d, ]+)\]', lambda match: '[' + ', '.join(str(renumber[int(n)]) for n in match[1].replace(' ','').split(',')) + ']', text)
    text += '\n## ' + ('References' if lang == 'en' else '参考文献') + '\n\n'
    text += '\n\n'.join(f'[{renumber[n]}] {bibliography[n]}' for n in order) + '\n'
    (ROOT / f'paper/manuscript_{lang}.md').write_text(text,encoding='utf-8')

catalog_path = ROOT / 'references/references.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
extra = json.loads((ROOT / 'references/improved/source_records.json').read_text(encoding='utf-8'))
known = {r['id'] for r in catalog}
catalog += [r for r in extra if r['id'] in ('echohawk2026','dreier2024') and r['id'] not in known]
for record in catalog:
    record['number'] = renumber[citation_map[record['id']]]
catalog_path.write_text(json.dumps(sorted(catalog,key=lambda r:r['number']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT / 'paper/citation_map.json').write_text(json.dumps({k:renumber[v] for k,v in citation_map.items()},indent=2)+'\n',encoding='utf-8')
bibpath = ROOT / 'references/references.bib'
bib = bibpath.read_text(encoding='utf-8')
if '@misc{echohawk2026,' not in bib:
    bibpath.write_text(bib+'\n'+(ROOT / 'references/improved/additional_references.bib').read_text(encoding='utf-8'),encoding='utf-8')
print('Finalized bilingual papers, six result/protocol tables and 21 references.')
