# 论文与复现资料入口

当前研究为 **Direction Conditioned Coherence Ranking（DCCR，方向条件相干谱排序）**。算法从 SRP-PHAT 生成的四个方向候选中，利用学习得到的 24 频带方向相干谱评分选择无人机方向，并进行声学检测。主文全部性能数据来自真实的 208 通道室外录音。

## 正式论文

| 版本 | Word | PDF | 在线阅读 |
|---|---|---|---|
| 英文编辑意见修订稿，5页 | [Word](paper/editor_revision_2026-11-13/DCCR_Editor_Revised.docx) | [PDF](paper/editor_revision_2026-11-13/DCCR_Editor_Revised.pdf) | [正文](paper/editor_revision_2026-11-13/manuscript_en.md) |
| 中文完整译稿，5页 | [Word](paper/editor_revision_2026-11-13/DCCR_Chinese_Revised.docx) | [PDF](paper/editor_revision_2026-11-13/DCCR_Chinese_Revised.pdf) | [正文](paper/editor_revision_2026-11-13/manuscript_zh.md) |

当前交付为2026-11-13英文修订稿及2026-11-15补齐的中文译稿和PDF。两稿均包含9个公式、3张数据表、2幅图和12条参考文献，沿用导师稿的A4双栏排版。英文正文较导师附件增加约930词，补充声学机理、测向原理、联合判决及误差分析。作者顺序、南京航空航天大学计算机科学与技术学院单位信息、两位作者邮箱、通讯作者标记和基金致谢均来自导师稿。见[修订包说明与重建方式](paper/editor_revision_2026-11-13/README.md)。

`paper/English_Main.*`、`paper/Chinese_Translation.*`、`paper/field_*.md`及根目录`START_HERE.pdf`为2026-11-08及此前材料，保留供追溯；不要将旧版生成脚本的输出误作当前导师稿修订版。

## 数据和主要结果

原始录音保留在 `赛题信息/第四届“声华杯”赛题一附件（发布版）-0609更新/`。共有 9 段录音，每段 208 个单通道 WAV，48 kHz、16 位 PCM，总计 1872 个 WAV、273.75 秒多通道观测。设备为 CRY8501/SonoCam Pi，机型为 DJI Air 3S，采集日期为 2026 年 5 月 25 日。

100 m 组仅用于算法开发。150 m 和 200 m 组保留用于评价：4 段无人机录音提供 600 个正观测窗，2 段背景录音提供 200 个负观测窗；另用不重叠的 50 个背景窗标定检测阈值。代码、模型、协议和输入摘要在保留评价前冻结。初始质量审计检查了全部文件的格式、哈希及幅值统计，未将保留组的算法输出或学习特征用于开发。

| 实测指标 | SRP-PHAT | DCCR |
|---|---:|---:|
| 相对标称参考方向的平均球面角偏差 | 14.78° | 6.97° |
| 中位角偏差 | 3.49° | 3.47° |
| 95 百分位角偏差 | 96.87° | 54.16° |
| 10° 内比例，全部 600 个正窗 | 84.8% | 94.0% |
| 使用相同 DCCR 检测门控的联合成功率 | 76.5% | 85.5% |

DCCR 检出 514/600（85.7%），背景虚警 3/200（1.5%）。各方法独立标定后的实际虚警率不相同，不能将检测率比较解释为严格相同虚警率下的比较。困难负例消融支持当前工作点的检测改善，但未显示额外的方向精度收益。

参考方向来自采集示意图，属于标称静态值；没有同步轨迹可验证绝对测角精度。观测窗存在时间相关性，不是 800 次独立实地试验，因此主稿不报告把观测窗当独立样本的置信区间。结果仅涉及单机型、单日、两个保留位置及组内背景标定。算法估计方向，不估计距离或验证跟踪。DCCR 实测计算耗时中位数 414.9 ms，另需 200 ms 采集时间，当前串行实现未实现实时运行。

## 复现与证据

| 内容 | 入口 |
|---|---|
| 环境、验证、推理和重跑命令 | [code/EXPERIMENT_README.md](code/EXPERIMENT_README.md) |
| 冻结实验协议 | [research/real_data/protocol.md](research/real_data/protocol.md) |
| 数据与参考方向口径补充 | [research/real_data/protocol_clarifications.md](research/real_data/protocol_clarifications.md) |
| 实测研究文献梳理 | [research/real_data/literature_notes.md](research/real_data/literature_notes.md) |
| 原始文件全量摘要与通道审计 | [source_manifest.json](results/field/source_manifest.json)、[inventory.json](results/field/inventory.json) |
| 阵列前端与 DCCR | [field_algorithm.py](code/field_algorithm.py)、[field_ranker.py](code/field_ranker.py) |
| 开发数据特征与两个模型 | `results/field/discriminative_features.npz`、`discriminative_model.npz`、`no_hard_negatives_model.npz` |
| 冻结文件清单 | [frozen_config.json](results/field/frozen_config.json) |
| 全部逐窗输出与候选评分 | [predictions.csv](results/field/predictions.csv)、[candidates.csv](results/field/candidates.csv) |
| 统计汇总与结果摘要清单 | [summary.json](results/field/summary.json)、[artifact_manifest.json](results/field/artifact_manifest.json) |
| 已执行的只读结果核验 | [verification.json](results/field/verification.json)、[verify_field.py](code/verify_field.py) |
| 当前论文一致性与导出检查 | [verification.json](paper/editor_revision_2026-11-13/verification.json) |
| 导师稿基准与修订过程 | [修订记录](results/document_qa/editor_revision_2026-11-13/REVISION_REPORT.md) |
| 2026-11-15 投稿前预审 | [预审报告与核验材料](results/manuscript_audit_2026-11-15/REPORT.md) |
| 旧版论文一致性与导出检查 | [delivery_verification.json](results/document_qa/field/delivery_verification.json) |
| 参考文献复核与正式稿修订 | [复核报告](research/real_data/reference_audit_2026-11-08.md)、[修订与核验记录](results/document_qa/reference_revision_2026-11-08/REVISION_REPORT.md) |
| 图形源文件 | `figures/field/`，中英文 PNG 与矢量 PDF |
| 参考文献资料 | `references/`；当前12条参考文献以[修订稿](paper/editor_revision_2026-11-13/manuscript_en.md)为准，[field_citation_map.json](paper/field_citation_map.json)对应旧版15条参考文献 |

原始录音没有被修改或重新合成。已完成全部 1921 个原始资料文件的 SHA256 检查、16 项冻结文件检查、7 项评价产物检查，以及全部角偏差、检测标志、配对和统计重算。最终文档逐页检查记录与四份文件哈希存于文档核验报告。

## 历史材料与投稿准备

旧仿真稿及旧入口说明移至 [archive/](archive/README.md)。旧仿真实验的数据、模型及冻结记录保留，供追溯使用，其数值不属于当前实测论文的结果。

当前文件是完整研究稿。正式投稿前仍需按目标刊会要求确认邮编及相关声明；通信邮箱已采用导师稿信息，当前沿用导师稿模板。2026-11-08版的[修订核验记录](results/document_qa/template_revision/REVISION_REPORT.md)和[相似文字初检](results/similarity_precheck/REPORT.md)单独保存，不能视为对本次新增正文的检查。尚未执行正式相似度检测，不能声称已满足指定重复率阈值。录音公开分发应遵守原始提供方的条件；本目录不另行授予公开再分发许可。
