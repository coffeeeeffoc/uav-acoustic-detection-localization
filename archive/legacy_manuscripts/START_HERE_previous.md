# 论文与复现资料入口

当前论文提出**声源条件化候选排序（SCCR）**：用多个声学响应图保留竞争方向，结合普通波束和干扰抑制波束的频谱特征选出目标方向；另以频谱—空间检测器和多声源负例训练改善目标检测。

## 阅读论文

- [英文论文 PDF，8 页](paper/manuscript_en.pdf) · [英文可编辑稿](paper/manuscript_en.md)
- [完整中文译稿 PDF，11 页](paper/manuscript_zh.pdf) · [中文可编辑稿](paper/manuscript_zh.md)
- 两稿包含相同的 16 个公式、6 张表、3 幅图和 21 条参考文献。英文采用通用 IEEE 式双栏，中文采用单栏阅读版。正文独立讨论研究问题，没有任务答复或赛题说明措辞。

## 已执行的独立测试

开发数据与最终评价分开。固定源码及模型后，新生成 800 个校准负例、1000 个正例和 2000 个负例静态测试，以及 24 条连续序列；保存 3824 份八通道 NPZ 录音、6680 个音频帧。

| 指标 | 基线 / 消融 | 所提方法 |
|---|---|---|
| 无条件平均球面角误差 | PHAT 25.40° | SCCR 18.12°，降低 28.7% |
| 10° 内定位比例 | PHAT 66.0% | SCCR 75.1% |
| 抑制特征消融平均误差 | 104维无抑制模型 19.08° | 149维完整模型 18.12° |
| 检测召回率 / 总体虚警率 | 谐波—相干 7.2% / 6.1% | 90.5% / 5.4% |
| 同一新检测器下的联合成功率 | PHAT 64.5% | SCCR 72.8% |

PHAT 与 SCCR 的配对平均误差改善为 7.284°，95% 区间 [6.141°, 8.405°]。抑制特征带来的额外改善为 0.962°，区间 [0.383°, 1.604°]。所有正例均保留，未用检测门控筛掉困难定位样本。

结果也保留明显限制：SCCR 的总体第95百分位误差仍为101.61°，定向宽带干扰下平均误差43.27°；检测器多声源负例虚警率8.6%，发动机—发动机组14.0%。频谱消融模型召回率82.8%、虚警率4.5%，全模型并非每项指标都更好。连续序列仅验证逐帧估计，没有声明可靠跟踪。计算耗时上界中位数25.84 ms，不包含200 ms采集时间。

以上均为声明分布下的仿真结果，不是实测距离或真实机型泛化证据。保存的 IDMT 实测录音具有 CC BY 4.0 许可，仅作为补充声音资料，没有用于拟合或性能评分。

## 资料目录

| 内容 | 入口 |
|---|---|
| 原始文献调研 | [research/literature_review.md](research/literature_review.md) |
| 改进算法与相关工作的区别 | [research/improved_algorithm_prior_art.md](research/improved_algorithm_prior_art.md) |
| 冻结实验方案 | [research/algorithm_revision_protocol.md](research/algorithm_revision_protocol.md) |
| 参考文献、BibTeX、来源记录与原文 | [references/references.json](references/references.json)、[references/references.bib](references/references.bib)、`references/papers/`、`references/improved/` |
| 推理接口与完整复现命令 | [code/EXPERIMENT_README.md](code/EXPERIMENT_README.md) |
| 检测器 / 定位器源码 | [code/improved_detector.py](code/improved_detector.py)、[code/improved_localizer.py](code/improved_localizer.py) |
| 独立评价源码 | [code/evaluate_improved.py](code/evaluate_improved.py) |
| 开发阶段模型和证据 | `results/development_detector/`、`results/development_localizer/` |
| 完整新校准 / 测试录音 | `data/synthetic/improved/` |
| 独立测试原始逐帧输出与汇总 | [results/improved/summary.json](results/improved/summary.json)、`results/improved/*frames.csv` |
| 冻结源码 / 模型清单 | [results/improved/frozen_config.json](results/improved/frozen_config.json) |
| 独立方法审查 | [results/improved_method_review.md](results/improved_method_review.md) |
| 全部输出一致性核验 | [results/improved_verification.json](results/improved_verification.json)、[code/verify_improved.py](code/verify_improved.py) |
| 中英文内容和 PDF 检查 | [results/document_qa/delivery_verification.json](results/document_qa/delivery_verification.json) |
| 公开实测录音与许可 | [data/public/idmt_sample/README.md](data/public/idmt_sample/README.md) |

`paper/improved_*_draft.md` 是构建用占位模板；阅读与编辑最终论文请使用 `manuscript_en` / `manuscript_zh`。数值解释文本针对本次冻结实验编写，若变更实验应重新审查。

## 核验与重新排版

在当前目录的 PowerShell 中运行：

```powershell
$experimentPython = 'C:\Users\15211\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $experimentPython -B code/verify_improved.py
& $experimentPython code/build_papers.py --assets
& $experimentPython code/build_papers.py
& $experimentPython code/verify_delivery.py --render
```

当前机器已保存并实际使用 Python 3.12.14 及相应本地依赖。首次在其他机器运行，按 `code/EXPERIMENT_README.md` 安装锁定依赖和配置字体。上述核验不重新生成声学实验；重跑实验请使用副本，保留当前冻结证据。

## 旧实验与投稿准备

此前的加权消融及失败分析稿已完整归档为 [paper/controlled_evaluation_v1.zip](paper/controlled_evaluation_v1.zip)。`results/full/` 和 `data/synthetic/full/` 原样保留，其中旧静态测试数据现在是新方法的开发数据，不能再作为新算法的独立最终测试。`results/quick/` 是更早的工程检查点。

原始 `README.md` 及参考材料保持原样。作者和单位信息待补充，投稿前需套用目标刊会正式模板。尚未取得正式相似度报告，因此不能声明已满足总重复率24%或单篇来源3%的要求。实测有效距离、真实机型泛化及设备端性能仍待外部验证。
