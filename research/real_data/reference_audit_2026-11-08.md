# 当前实测论文参考文献复核

> 本报告保留修改前的 12 条参考文献快照、编号和行号。后续已按用户要求修订正式稿；当前 15 条引用及导出核验结果见[引用修订记录](../../results/document_qa/reference_revision_2026-11-08/REVISION_REPORT.md)。

核查日期：2026-11-08。对象为 `paper/field_en.md`、`paper/field_zh.md` 及对应的两份 Word、两份 PDF，均为当前 5 页 DCCR 实测稿。本次只形成审查记录，未修改正式稿、算法或实验结果。

## 结论

引用结构和中英文导出一致：12 条文献全部在正文出现，首次出现顺序为 [1] 至 [12]，随后再次引用 [5]；没有发现缺号、重复编号、正文无对应条目、文后条目未被引用或 DOI 在不同格式间变更。

11 条已出版论文/书章的作者、题名、年份、载体、卷期页码或文章号以及 DOI 未发现明确错配；第 [12] 条也有对应原件。需要优先完善的是 [12] 的来源著录，以及与本文接近的学习型空间谱方法的覆盖。另建议交代已经调研过的 EchoHawk、给岭回归补一个基础来源，并收紧个别转述。这些建议区分为来源信息缺项、相关研究覆盖判断和可选补强，不将它们等同于已经证实的引文造假或方法错误。

## 具体发现和最小修改建议

### 1. [12] 原始数据和采集说明的来源信息不足

位置：两稿第五节 A 段及参考文献 [12]；英文源稿第 87、200 行。

现有条目只有泛化译名 “Experimental measurement description”、设备和采集日期，并以 “unpublished technical dataset” 收尾。它没有标明赛事、附件编号、所用资料包版本，也没有区分采集说明文档和录音数据包，读者难以唯一识别原件。

本次直接检查的原件为：

- `赛题信息/第四届“声华杯”赛题一附件（发布版）-0609更新/附件4：试验说明文档.docx`。
- 文档内正式标题为《声华杯2026赛题附件4：试验说明文档》，副题为《复杂噪声环境下低慢小无人机声学探测定位算法》。它明确交代 208 通道、48 kHz、16 bit、Air 3s、三个距离组及角度定义。
- [中国声学学会赛事通知](https://www.aschina.org.cn/details.html?contentId=851&id=71)确认赛事名称及赛题一背景；该通知不是附件4全文或数据下载地址。

建议保留标题起首的著录方式，先改为能够核验的内容，例如：

> [12] “Shenghua Cup 2026, Attachment 4: Experimental Description” [声华杯2026赛题附件4：试验说明文档], technical documentation accompanying the problem-1 data package of the 4th Shenghua Cup Acoustic Technology Competition, release package “0609 update,” 2026 (in Chinese).

上述英文标题是对原中文标题的译写。责任机构若未在原件明确署名，不应凭赛事主办关系代填个人作者或采集责任人。若投稿格式要求访问方式，应说明竞赛资料的实际获取渠道；不能把赛事通知链接写成可直接下载数据的链接，也不能将仓库中的未验证网盘链接宣称为永久开放数据存储库。

正文建议将数据来源写清为“使用竞赛提供的 CRY8501/Air 3S 录音”，而不是仅靠 [12] 让读者推断来源。“未正式出版”本身不构成错误，问题在于当前信息不足以识别资料。

### 2. 建议补充 Rodríguez 等的空间频谱图学习工作

位置：两稿第二节相关研究，以及第一节介绍 DCCR 增量的段落。

[Acoustic Imaging for UAV Detection: Dense Beamformed Energy Maps and U-Net SELD](https://arxiv.org/abs/2508.00307v4) 使用波束形成的空间—频率表示训练 U-Net，完成无人机检测和方向估计。已检查本地原始 PDF 的摘要、方法概述及 §§3.3–3.6；本地文件的固定版本为 v4，修订日期 2026-07-17。arXiv 首发于 2025 年，引用 v4 时应把版本和修订年份说清，不应标成已确认的期刊论文。

它与本文都采用“阵列空间信息加目标相关学习”，是比一般检测数据集更直接的方法近邻。当前第二节仅用 Yang 等 [9] 概括神经定位，未覆盖这种空间频谱图学习路线。建议加一句方法差别，而不是只往文献表追加题名：

> Rodríguez et al. learn UAV activity from dense beamformed spectral maps using a U-Net [新增引用]. DCCR instead scores four SRP-PHAT candidates with normalized band-coherence features and a linear model.

这属于相关研究覆盖建议，不表示两种算法相同，也不表示已证明 DCCR 优于该方法。当前实验没有直接比较这套 U-Net，不能把新增引用改写为性能胜出声明。

### 3. 建议交代已调研的 EchoHawk

位置：两稿第二节；必要时在第五节数据划分说明附近补一句。

[EchoHawk v2](https://arxiv.org/abs/2606.29589v2)已在本项目 `references/references.json`、`references/improved/` 和 `research/improved_algorithm_prior_art.md` 中记录，但未进入当前 12 条参考文献。它讨论无人机检测与经典阵列测向的组合，并专门分析按连续录音会话分组的重要性。本文同样强调检测与测向的区分及防止相邻窗跨集合，因此值得给出简短定位。

建议措辞：

> EchoHawk combines drone detection with classical array localization and examines recording-session leakage [新增引用]. The present study focuses on selecting the target bearing among four directional candidates.

本次核对固定版本 PDF 的摘要及 §§10–11；其在线摘要页和 v2 PDF 中部分示例数字不一致。因此如补引，只引用已核查的方法和分组原则，不混用其在线摘要与正文成绩，也不将其检测指标与本文不同数据和工作点的指标直接比较。是否存在代码借用不在本次审查范围；保存其代码副本本身不证明当前实现使用了该代码。

### 4. 岭回归缺少基础出处，建议补一条

位置：第四节 A 段、公式 (7) 附近，英文源稿第 67–71 行。

类别平衡加权和方向候选训练规则由本文定义；岭回归本身是既有方法。当前在摘要中直接使用该名称，正文给出目标函数，但没有基础方法引用。建议在正文第一次解释 ridge regression 时补 Hoerl 和 Kennard 的原始论文，而不是在摘要塞入引用：

> A. E. Hoerl and R. W. Kennard, “Ridge Regression: Biased Estimation for Nonorthogonal Problems,” *Technometrics*, vol. 12, no. 1, pp. 55–67, 1970, doi: 10.1080/00401706.1970.10488634.

书目信息以[出版商条目](https://www.tandfonline.com/doi/abs/10.1080/00401706.1970.10488634)为准。1970 是原刊年，不能把网页上线日期 2012 或另一篇 2000 年重印记录的 DOI 混进来。这是基础归属补强，优先级低于原始数据来源和最接近的方法先例；现有正文未声称发明岭回归。

### 5. [10]、[11] 的参考测量描述可更精确

位置：两稿第二节后半段，英文源稿第 23 行。

当前“二者提供多通道数据和参考测量”的概括可以得到支持，不属于已确认的错引。但下一句马上谈缺少同步轨迹，容易使读者将两套资料都理解成具有动态同步真值：

- DDL：作者论文 §2 描述飞行日志、GPS 及与音频的时间同步。[作者原文](https://personalpages.surrey.ac.uk/w.wang/papers/Safavi%20et%20al_MLSP_2025.pdf)
- UaVirBASE：论文 §2.1 明确静态定位没有采用 GPS，水平距离使用测距轮并以激光测距仪核验；动态定位与高分辨率 GPS 当时属于后续方向。[期刊原文](https://www.mdpi.com/2076-3417/15/10/5378)

可将原概括句改成：

> DDL [10] aligns multichannel audio with flight-log positions, whereas UaVirBASE [11] documents measured static UAV configurations. These datasets illustrate different forms of reference information; the present recordings provide nominal static bearings without synchronized trajectories.

不需要因此更换 [10] 或 [11]，也不应把 UaVirBASE 描述成已核实的同步动态飞行轨迹数据集。

### 6. 个别引文的支撑范围可再收紧

这三处属于表述精度建议，没有发现文献被引成完全无关的方法：

- **[1]，引言首句：** 原文直接讨论低信噪比和背景噪声；本次全文文本检索和相关页面阅读未找到对“风、车辆、机械”这组三类干扰的直接列举。建议将枚举改为“噪声环境，尤其是低信噪比条件”；若要保留具体例子，应补能直接支持这些例子的来源。[期刊正式条目](https://www.sciopen.com/article/10.12141/j.issn.1000-565X.220277)
- **[6]，相关研究首句：** “部分 PHAT 加权”有依据，建议明确为 PHAT-β 部分频谱白化。原论文主要评估特定噪声、混响和信号类型下的声源检测效果；可改为“评估了部分频谱白化对噪声和混响条件下声源检测的影响”，避免把当前笼统的 improve spatial reliability 读成普遍精度保证。[作者机构记录和摘要](https://scholars.uky.edu/en/publications/performance-of-phase-transform-for-detecting-sound-sources-with-m/)
- **[7]，同句：** 应点明“空间分离的辅助麦克风”，并保留位置、噪声及混响条件。原论文有部分辅助位置不改善甚至略差的情况；可改为“在相应条件下改善定位”。本文没有辅助麦克风，也未声称复现它，现有方法归属无需更换。[EURASIP 原文](https://eurasip.org/Proceedings/Eusipco/Eusipco2024/pdfs/0000917.pdf)

中英文具体替换句及原文位置已列在下述独立复核记录中。

## 逐条核查结果

[1]–[7] 的独立复核记录见同目录 [详细来源复核](reference_audit_sources_1_7_2026-11-08.md)，已完成整合；[1] 的具体支撑范围和 [6] 的机构原始记录另由主审复查。

| 编号 | 主要核对内容 | 目前结论与证据 |
|---|---|---|
| [1] | 中文综述英译题名、作者、2022、50(12)、109–123 | 题录正确。正式英文题名虽不常见，也不应自行润色；噪声枚举的支撑范围建议收紧。 |
| [2] | GCC/PHAT 基础文献，1976、24(4)、320–327 | 题录和目前概括相符。扫描原文和 IEEE 登记元数据互证；没有将其误当作 SRP 直接出处。 |
| [3] | SRP 书章，三位作者、2001、157–180、书章 DOI | 题录确认，仅取得原章 pp. 157–158 预览；后续 SRP 推导未逐式核实。该证据缺口不等于当前引用错误。 |
| [4] | SRP 综述，2024、article 59、题名、DOI | 题录和概括相符。本地作者稿与正式版不同，已对照出版社正式 HTML；59 为文章号。 |
| [5] | Valin 噪声加权波束形成和跟踪，2007、55(3)、216–228 | 题录和概括相符。正文明确背景扣除基线不是其复现，应保留；作者稿年份和 DOI 内的 2006 不应替换正式发表年 2007。 |
| [6] | Donohue 的部分 PHAT，2007、87(7)、1677–1691 | 题录正确，确实支持 PHAT-β 部分白化；建议收紧效果表述。已读作者链接的原文网页转录，未完成 PDF 公式图像复核。 |
| [7] | Brümann/Doclo 辅助麦克风 SRP，2024、917–921 | 题录和方法归属正确；建议补空间分离及适用条件，保留姓名重音符。 |
| [8] | Uluskan 单作者、2024、23(5–6)、558–577、DOI；谐波邻域 SRP | 未发现错配。[SAGE 原刊页面和摘要](https://journals.sagepub.com/doi/10.1177/1475472X241259082)支持当前简要描述；全文受限，未声称核清所有公式。 |
| [9] | Yang 等四位作者、EUSIPCO 2025、256–260、DOI；合成信号训练神经定位 | 未发现错配。[官方会议 PDF](https://eurasip.org/Proceedings/Eusipco/Eusipco2025/pdfs/0000256.pdf)实际页脚为 256–260。Crossref 登记为 256–560 属外部元数据异常，不应改坏当前页码。 |
| [10] | Safavi 等五位作者、MLSP 2025、1–6、DOI；多通道数据和位置参考 | 未发现错配。[IEEE 条目](https://ieeexplore.ieee.org/abstract/document/11204285)及作者 PDF 一致。作者 PDF 为 Çaylı，不能仅因元数据以 Çayli 转写就判当前拼写错误。 |
| [11] | Jekateryńczuk 等三位作者、2025、15(10)、5378、DOI；静态测量 | 未发现错配。[期刊条目](https://www.mdpi.com/2076-3417/15/10/5378)及实时 Crossref 记录支持书目；5378 为文章编号，应保留 Art. no. 写法。 |
| [12] | 原始资料身份、版本及与采集描述的对应关系 | 原件存在且支持核心设备和场景描述；正式题名、附件编号和资料包版本应补全。 |

## 文件与编号一致性

六个正式文件逐一提取并比较了文内引用和参考文献。忽略 Markdown 链接语法、空白换行及 Unicode 排版规范化后，中英文文献表和各自 Word/PDF 的 12 条文本全部一致，11 个 DOI 与 `paper/field_citation_map.json` 一致。两份 PDF 均为 5 页；已目视检查第 1 页的引用段落和第 4–5 页的参考文献，没有在文献区发现截断或漏项。

机器检查结果、文件 SHA256 和文本提取存于 `results/document_qa/reference_audit_2026-11-08/structure_check.json`，超链接检查见同目录 `link_check.json`。两份 Word 的 11 个 DOI 超链接均与显示文字相符，两份 PDF 的链接目标集合也一致；跨行产生多个链接区域是排版结果，不是重复条目。核查结束时六个正式文件的哈希均未改变。两份 `field_*_template.md` 含生成占位符，与正式 Markdown 不逐字相同是正常情况；参考文献由 `code/finalize_field_paper.py` 的 `references()` 生成。`references/references.json` 是更大的资料库，其历史 `number` 不能直接当作当前论文编号；当前编号以 `field_citation_map.json` 为准，资料库有未选入的论文不自动构成漏引。

若落实补引，应同步模板、文献生成函数、资料库和当前编号映射，再重建两种语言的 Markdown、Word 和 PDF。还需更新 `code/verify_field_delivery.py` 中固定为 12 条的核验条件及相关入口说明，不能只手改 PDF 或仅在文后追加未引用条目。本次没有执行这些改稿操作。

## 审查边界

本次核查的是当前选入文献、直接相关的既有资料及必要的一手网页，未进行穷尽性领域检索或新颖性证明。未重新执行实验，未验证外部论文成绩，未做正式查重。[3] 未取得完整书章，[8] 只核实出版商摘要和题录，[6] 的全文证据为作者链接的网页转录而非 PDF 图像。原件和公开记录之间存在版本或登记差异时，采用可识别的原文版本并记录差异，不能据此次复核承诺“绝无漏引”或投稿审查一定通过。
