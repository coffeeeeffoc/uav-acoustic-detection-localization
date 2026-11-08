# 论文与复现资料入口

当前研究为 **Direction Conditioned Coherence Ranking（DCCR，方向条件相干谱排序）**。算法从 SRP-PHAT 生成的四个方向候选中，利用学习得到的 24 频带方向相干谱评分选择无人机方向，并进行声学检测。主文全部性能数据来自真实的 208 通道室外录音。

## 正式论文

| 版本 | Word | PDF | 可重建源稿 |
|---|---|---|---|
| 英文主稿，5 页 | [English_Main.docx](paper/English_Main.docx) | [English_Main.pdf](paper/English_Main.pdf) | [field_en.md](paper/field_en.md) |
| 中文完整译稿，5 页 | [Chinese_Translation.docx](paper/Chinese_Translation.docx) | [Chinese_Translation.pdf](paper/Chinese_Translation.pdf) | [field_zh.md](paper/field_zh.md) |

两稿均包含 9 个公式、4 张表、3 幅图和 12 条参考文献，按 `模板/wordtemplates.doc` 的实际 A4 页面及双栏样式排版，图形紧凑跨栏、四张表采用单栏。论文围绕研究问题、算法、实验和局限展开。作者顺序为 Ju Luo、Yuqian Zhou，两人单位均为南京航空航天大学，城市为南京；尚未提供邮编和通信邮箱，未限定目标期刊。

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
| 论文一致性与导出检查 | [delivery_verification.json](results/document_qa/field/delivery_verification.json) |
| 图形源文件 | `figures/field/`，中英文 PNG 与矢量 PDF |
| 参考文献资料 | `references/`；本稿引用映射为 [field_citation_map.json](paper/field_citation_map.json) |

原始录音没有被修改或重新合成。已完成全部 1921 个原始资料文件的 SHA256 检查、16 项冻结文件检查、7 项评价产物检查，以及全部角偏差、检测标志、配对和统计重算。最终文档逐页检查记录与四份文件哈希存于文档核验报告。

## 历史材料与投稿准备

旧仿真稿及旧入口说明移至 [archive/](archive/README.md)。旧仿真实验的数据、模型及冻结记录保留，供追溯使用，其数值不属于当前实测论文的结果。

当前文件是完整研究稿。正式投稿前仍需补充邮编、通信邮箱及目标刊会要求的声明，当前已应用提供的模板。2026-11-08 版的[修订核验记录](results/document_qa/template_revision/REVISION_REPORT.md)和[相似文字初检](results/similarity_precheck/REPORT.md)单独保存。尚未执行正式相似度检测，不能声称已满足指定重复率阈值。录音公开分发应遵守原始提供方的条件；本目录不另行授予公开再分发许可。
