# [1]–[7] 引文外部事实核查

> 本报告为修改前审查快照，保留当时的表述和行号。后续正式稿的落实情况见[引用修订记录](../../results/document_qa/reference_revision_2026-11-08/REVISION_REPORT.md)；当前稿件共 15 条参考文献。

核查日期：2026-11-08（Asia/Shanghai）。范围仅为 `paper/field_en.md`、`paper/field_zh.md` 中 [1]–[7] 的出版元数据与引用语义。后台研究 agent 独立核查 [6]，本报告整合其结果。未审查算法代码，也未重复主线负责的 [8]–[12]、遗漏文献及 Word/PDF/中英文一致性核查。未修改主稿或其他材料。

以下行号均对应本次核查读取的 Markdown 快照。两份稿件的有关位置分别为：引言第 17 行、相关研究第 23 行、比较方法第 101 行；参考文献 [1]–[7] 依次在第 178、180、182、184、186、188、190 行。PDF 页码明确区分文件页序与正式印刷页码，不以作者稿的页数冒充期刊页码。

## 1. 结论与处理优先级

1. **[1]–[7] 未发现已确认的出版题录事实错误。** 作者、题名、载体、年、卷期（适用时）、页码/文章号及 DOI 已逐条核对。书章 [3] 和会议文献 [7] 不适用期刊卷期；[4] 使用文章号，当前写法合理。
2. **[6] 的“partial PHAT weighting／部分PHAT加权”有原文依据，不是错引。** 原文 p. 1679 式 (4) 用 β 控制白化；建议写成“PHAT-β 部分频谱白化”，并将第 23 行笼统的改善效果收窄为原文所研究的声源检测条件。无需换掉 [6]，也不应改述为幅值阈值门控。
3. **[1] 的证据不够支撑第 17 行对风、车辆、机械噪声的具体枚举。** 原文明确支持一般背景噪声和低信噪比难题；建议改成“噪声环境／低信噪比”，保留 [1]。
4. **[7] 的归属正确，建议补充条件。** 原文使用空间分离的辅助麦克风，效果随位置及噪声/混响条件变化；不宜把第 23 行的改善效果读成普遍保证。这是范围澄清，不是已证实的错误引用。
5. **[3] 存在未完成的全文证据环节。** 元数据和公开预览确认，后续 SRP 推导未取得原章全文；不能标为已逐式核实。可直接核对现有 [4] 的相关式子，不能把它冒充 [3] 原文。
6. **覆盖量：7/7 完成基本题录核查；5 篇读取本地原始 PDF，[6] 读取作者链接的原文网页转录，[3] 读取出版社两页预览。** [2]、[4]、[5] 的现有概括未见需要纠正的实质错引。

## 2. 核查覆盖表

“已确认”指有本次实际访问的出版商/作者/会议组织方原始材料支持；DOI 登记数据仅用于补核出版字段，不替代全文语义。原文可读也不表示已经复核文献的全部实验。

| 引文 | 书目位置（EN/ZH） | 作者、题名、刊物/载体、年、卷期、页码/文章号、DOI | 实际读取的原文范围 | 文内语义结论 |
|---|---|---|---|---|
| [1] Chen 等 | 178 / 178 | 全部确认 | 本地正式版 PDF，重点印刷 pp. 109–110、113、119、123；SciOpen 正式页面 | 一般噪声/低信噪比问题成立；风、车辆、机械的具体枚举未得到直接支持 |
| [2] Knapp–Carter | 180 / 180 | 全部确认；DOI 由 IEEE 存入 Crossref 的记录补核 | 本地扫描 PDF 完整查看印刷 pp. 320–322、327；IEEE 页面触发验证 | GCC 与 PHAT 概括相符；不要把该文说成 SRP 的直接出处 |
| [3] DiBiase 等 | 182 / 182 | 全部确认；为书中第 8 章，无期刊卷期 | Springer 章节/图书页及公开预览 pp. 157–158；未取得章节后续全文 | 基本研究主题相符；具体 SRP/GCC 汇总推导未在该章原文中直接核实，保留证据缺口 |
| [4] Grinstein 等 | 184 / 184 | 全部确认；2024(1)，文章号 59，无连续期刊页码 | 本地 arXiv v2 pp. 9、12；出版社正式 HTML §§3.3、4.1，并确认正式 PDF | 关于空间搜索及频谱加权扩展的概括相符 |
| [5] Valin 等 | 186 / 186 | 全部确认 | 本地及作者公开 37 页作者稿，§4.2（pp. 9–10）、§5（p. 14 起）；出版社页面 | 噪声/SNR 加权波束形成与粒子跟踪概括相符；“非复现”限定应保留 |
| [6] Donohue 等 | 188 / 188 | 全部确认；出版商与作者机构记录互证 | 作者主页链接的原文网页转录，印刷 pp. 1678–1679、1681、1684；未取得 PDF 图像 | 部分白化成立；建议明确 PHAT-β，并收窄改善效果的表述 |
| [7] Brümann–Doclo | 190 / 190 | 全部确认；会议论文，无期刊卷期 | 本地正式会议 PDF pp. 917–921，重点 pp. 917–920；EURASIP 官方全文及作者单位出版记录 | 方法归属正确；建议明确空间分离辅助麦克风及适用条件 |

## 3. 逐篇出版信息与语义证据

### [1] 陈鹏、陈洋、王威：无人机声学定位技术综述

**已确认的出版信息：** Peng Chen, Yang Chen, Wei Wang（陈鹏、陈洋、王威），英文正式题名 *Review for UAV Acoustic Positioning*，中文题名《无人机声学定位技术综述》，*Journal of South China University of Technology (Natural Science Edition)*／《华南理工大学学报（自然科学版）》，2022，50(12)：109–123；DOI [10.12141/j.issn.1000-565X.220277](https://doi.org/10.12141/j.issn.1000-565X.220277)。[SciOpen 期刊正式页面](https://www.sciopen.com/article/10.12141/j.issn.1000-565X.220277)直接列出作者、英文题名、卷期页码、DOI，发布日期为 2022-12-25。当前稿第 178 行无书目错误；英文题名虽然措辞不常见，也是期刊原题，不宜自行润色。

**本地原文：** [正式 PDF](../../参考资料/无人机声学定位技术综述_陈鹏.pdf)，15 页，印刷 pp. 109–123。印刷 p. 110 讨论低信噪比下的识别困难与阵列定位；p. 113 讨论环境噪声相关性、伪峰及 DOA 误差；p. 119 的问题与展望明确讨论无人机旋翼声被背景噪声淹没、传播和背景的频率依赖。

**稿件位置与判断：** 两稿第 17 行首句用 [1] 支撑在风、车辆和机械噪声中检出并测向。后半部分的一般研究动机得到支持，但本次检索该 PDF 全部文本并查看有关段落，未发现对这三类干扰的直接列举或专门结论。这是**引文支撑范围偏具体**，并非断言这三类噪声在现实中不存在。

**建议改法：**

- EN：`Passive acoustic sensing must detect UAV emissions and estimate their bearing in noisy environments, where low signal-to-noise ratios can hinder localization [1].`
- ZH：`被动声学感知需要在噪声环境中检出无人机辐射声并估计其方向，低信噪比会增加定位难度[1]。`

期刊旧站本次返回 403；上面结论依据实际可读的 SciOpen 正式页面及本地期刊 PDF，不依据网页 AI 摘要。

### [2] Knapp and Carter：广义互相关

**已确认的出版信息：** Charles H. Knapp, G. Clifford Carter，*The generalized correlation method for estimation of time delay*，*IEEE Transactions on Acoustics, Speech, and Signal Processing*，1976，24(4)：320–327，August；DOI [10.1109/TASSP.1976.1162830](https://doi.org/10.1109/TASSP.1976.1162830)。本地正式扫描版首页作者全名、期刊页眉与末页页码，与 [IEEE 登记的 Crossref 记录](https://api.crossref.org/works/10.1109/TASSP.1976.1162830)一致。原刊卷标为 ASSP-24，当前稿简写 vol. 24 不构成事实错误；Crossref 作者缩略为 C. Knapp、G. Carter，不应据此删除原文能确认的中间名首字母。

**本地原文：** [扫描 PDF](../../references/papers/knapp_carter_1976_gcc.pdf)无可用文本层，本次直接渲染查看印刷 pp. 320–322、327。p. 321 式 (6a)–(6c) 给出频域加权广义相关形式；p. 322 式 (19)–(23) 讨论 PHAT 的幅值归一化、相位及噪声局限。p. 327 上部仍为该文参考文献，下部已开始下一篇，页码 320–327 正确。

**稿件位置与判断：** 两稿第 17 行第二句将 GCC 和 SRP 并列概括为使用麦克风间时延证据，[2] 能支持 GCC 部分，没有发现明显错引。若要减少读者把 [2] 当作 SRP 发明出处的可能，可将两者分开描述，见 [3] 的可选改句。第 17 行 PHAT 强调相位的陈述也与该文相符。

**证据边界：** [IEEE 原始条目](https://ieeexplore.ieee.org/document/1162830)本次要求 JavaScript/机器人验证，未声称已读其网页全文；DOI、卷期页码通过实时读取 Crossref 中由 IEEE 提交的记录复核，语义判断来自原始论文扫描页。

### [3] DiBiase, Silverman and Brandstein：SRP 书章

**已确认的出版信息：** Joseph H. DiBiase, Harvey F. Silverman, Michael S. Brandstein，*Robust Localization in Reverberant Rooms*，载 *Microphone Arrays: Signal Processing Techniques and Applications*，Michael Brandstein、Darren Ward 编，Springer, Berlin, Heidelberg，2001，第 8 章，pp. 157–180；DOI [10.1007/978-3-662-04619-7_8](https://doi.org/10.1007/978-3-662-04619-7_8)。[Springer 章节页](https://link.springer.com/chapter/10.1007/978-3-662-04619-7_8)、[图书页](https://link.springer.com/book/10.1007/978-3-662-04619-7)和[公开预览](https://page-one.springer.com/pdf/preview/10.1007/978-3-662-04619-7_8)相互印证；当前稿第 182 行正确。书章无需补造期刊名、卷、期。

**原文可确认范围：** 出版社公开预览仅 pp. 157–158，确认主题为噪声/混响中的语音声源定位。p. 158 将波束形成 SRP、空间谱估计与 TDOA 三类定位策略区分开，并说明后续 §8.3 将结合已有方法提出定位算法。

**稿件位置与判断：** 两稿第 17 行将 SRP 与麦克风间时延证据联系，符合本领域方法概括，也与已读的 [4] 正式版 §2.5、式 (14)–(15)一致；但**不能用 [4] 的描述冒充已经读取 [3] 后续原文**。本次未取得 [3] 的 §8.3 全文，不将该条标记为完整原文语义核实，也不据此判当前稿错误。

**可选改法（已有编号范围内）：**

- EN：`Generalized cross-correlation estimates pairwise delays [2], while steered response power (SRP) aggregates correlation evidence over candidate source locations [3], [4].`
- ZH：`广义互相关用于估计麦克风对时延[2]，导向响应功率（SRP）则在候选声源位置上汇总相关证据[3]、[4]。`

[4] 是可直接核对聚合式的现有引文；如要求 [3] 单独承担这个细节的原始证据，仍须取得书章 §8.3 后续页面。此处仅记录证据缺口，不扩大到新增文献选题。

### [4] Grinstein 等：SRP 综述

**已确认的出版信息：** Eric Grinstein, Elisa Tengan, Bilgesu Çakmak, Thomas Dietzen, Leonardo Nunes, Toon van Waterschoot, Mike Brookes, Patrick A. Naylor，*Steered Response Power for Sound Source Localization: a tutorial review*，*EURASIP Journal on Audio, Speech, and Music Processing*，2024，2024(1)，文章号 59；DOI [10.1186/s13636-024-00377-z](https://doi.org/10.1186/s13636-024-00377-z)。[出版社正式 HTML](https://link.springer.com/article/10.1186/s13636-024-00377-z)及[正式 PDF](https://link.springer.com/content/pdf/10.1186/s13636-024-00377-z.pdf)给出正式发表日期 2024-11-12。期号 1 由[出版社提交的 Crossref 记录](https://api.crossref.org/works/10.1186/s13636-024-00377-z)补核；出版社自身推荐引文是 “2024, 59 (2024)”，故当前稿省略 no. 1 合理，不属于漏填事实字段。“59”是文章号，不是页码。

**原文及版本：** [本地 PDF](../../references/papers/grinstein2024_srp_review.pdf)是 arXiv:2405.02991v2（2024-05-09），31 页；出版社正式 PDF 为 27 页。当前稿引用正式期刊文献是正确的。这里的版本差异只用于限定核查证据，不开展全仓库一致性检查。

**稿件位置与判断：** 两稿第 17 行“频谱可靠性与空间搜索”有直接支持：本地作者稿 p. 9／正式 HTML §3.3 讨论迭代网格细化，作者稿 p. 12／正式 HTML §4.1 讨论改造 GCC-PHAT 的频率加权。**无需实质修改。** 第 17 行后半句关于整幅地图乘相同正常数不改变最大值位置，是稿件自身的数学观察，不应写成该综述已经证明了本文整套 DCCR 的优势。

### [5] Valin, Michaud and Rouat：噪声加权与跟踪

**已确认的出版信息：** Jean-Marc Valin, François Michaud, Jean Rouat，*Robust localization and tracking of simultaneous moving sound sources using beamforming and particle filtering*，*Robotics and Autonomous Systems*，2007，55(3)：216–228；DOI [10.1016/j.robot.2006.08.004](https://doi.org/10.1016/j.robot.2006.08.004)。[Elsevier/ScienceDirect 正式页面](https://www.sciencedirect.com/science/article/pii/S0921889006001576)确认上述字段及 2007-03-31 卷期日期。DOI 中的 2006 与作者稿日期均不构成把正式发表年改成 2006 的理由。

**原文及版本：** [本地作者稿](../../references/papers/valin2007_robust_localization.pdf)和[作者公开 PDF](https://jmvalin.ca/papers/valin_localization.pdf)为 37 页稿件，首页标注 2006-05-03 投 Elsevier 版本。作者稿 §4.2，pp. 9–10，式 (7)–(11) 用先验 SNR 掩膜、噪声估计和混响项增强相关；§5，p. 14 起采用粒子跟踪。其 PDF 页序不可换成正式出版 pp. 216–228 内的某一精确页，除非取得正式排版全文。

**稿件位置与判断：**

- 两稿第 23 行“噪声相关波束形成与跟踪”与原文相符。更精确的简写可为 EN `SNR-weighted beamforming with particle-filter tracking [5]`／ZH `基于信噪比加权的波束形成与粒子滤波跟踪[5]`，属可选措辞优化。
- 两稿第 101 行明确表示背景互谱扣除基线并非 [5] 的复现，这个界限应保留。[5] 的原文方案与稿件描述的存储背景互谱扣除不是同一方法。**本次没有检查代码，因此只确认两段文字与原文的区分合理，不确认基线实际实现。**

当前稿第 186 行无书目错误；没有发现需要纠正的引文归属。

### [6] Donohue、Hannemann、Dietz（2007）

#### 判定

**题录正确；支持将 PHAT-β 概括为部分白化/部分 PHAT 加权，但建议写明 PHAT-β，并将效果限定为所研究条件下的声源检测。** 第一作者主页所链接的原文全文中，第 1679 页式 (4) 的 β 是幅值分母的幂指数。不能将它改述为幅值阈值门控，也不能因文中另有检测阈值而判定该引文不支持部分白化。[作者全文](https://www.academia.edu/47489486/Performance_of_phase_transform_for_detecting_sound_sources_with_microphone_arrays_in_reverberant_and_noisy_environments)

#### 题录核对

| 字段 | 核实结果 |
| --- | --- |
| 作者及顺序 | Kevin D. Donohue；Jens Hannemann；Henry G. Dietz，与主稿缩写一致 |
| 题名 | Performance of phase transform for detecting sound sources with microphone arrays in reverberant and noisy environments |
| 期刊、年、卷期 | Signal Processing，2007，87(7)，期刊出版月份为 July |
| 页码 | 1677-1691 |
| DOI | 10.1016/j.sigpro.2007.01.013 |

以上由[Elsevier/ScienceDirect 记录](https://www.sciencedirect.com/science/article/abs/pii/S0165168407000370)与[University of Kentucky 作者机构记录](https://scholars.uky.edu/en/publications/performance-of-phase-transform-for-detecting-sound-sources-with-m/)交叉核实。第 188 行无需事实性更改。DOI [解析入口](https://doi.org/10.1016/j.sigpro.2007.01.013)已尝试访问，但本次工具未成功打开该入口；题录核实依据是前述两份实际读到的记录。

#### 原文定位及概念边界

以下页码均为期刊印刷页码。依据为[作者主页所链接的全文](https://www.academia.edu/47489486/Performance_of_phase_transform_for_detecting_sound_sources_with_microphone_arrays_in_reverberant_and_noisy_environments)，非其他论文对 [6] 的转述。

- **第 1679 页，Section 2，式 (4)：** 保留频谱相位，并将幅值除以其 β 次幂。以复数记法等价整理为：

  \[
  \widehat y_{p,l}(\omega;\beta)
  =\frac{\widehat V_{p,l}(\omega)}{|\widehat V_{p,l}(\omega)|^\beta},
  \qquad 0\leq\beta\leq1.
  \]

  原式使用幅值与相角记法；上式是等价整理，不是原版排版摹写。紧接式 (4) 的正文明确给出：β=1 对应标准 PHAT；β=0 对原信号无影响。对于非零频谱，0<β<1 保留幅值的 1-β 次幂，因此“部分白化”有直接公式依据。
- **第 1678 页引言；第 1681 页式 (20)-(21)：** 检测阈值和 ROC 分析针对 SRP 目标/噪声像素值；式 (20) 的分段比较用于计算 ROC 面积，并非式 (4) 的频谱加权定义。
- **第 1684 页，性能指标计算段：** 另有正值和相对峰值下降 6 dB 的条件，用于识别目标峰及噪声峰。这属于性能统计时的峰值归类条件，不能当作 PHAT-β 的幅值门控机制。
- **效果边界：** 原文研究噪声/混响条件下的声源检测，并区分窄带、宽带及语音；不是对任意场景定位精度改善的保证。出版商摘要报告部分参数下的改善，而非无条件提升“空间可靠性”。[出版商摘要及引言](https://www.sciencedirect.com/science/article/abs/pii/S0165168407000370)

#### 建议中英文改法

建议将 [6] 独立成句，以免共享“均改善空间可靠性”的过宽谓语。该建议仅替换两稿第 23 行中 [6] 所承担的表述。

**英文：** Donohue et al. [6] introduced PHAT-β to control spectral whitening and evaluated its effects on sound-source detection in noisy and reverberant conditions.

**中文：** Donohue等[6]提出PHAT-β以控制频谱白化程度，并评估了其在噪声与混响条件下对声源检测的影响。

若只替换术语，英文可用 “PHAT-β partial spectral whitening [6]”，中文可用“PHAT-β部分频谱白化[6]”；但这不足以解决原句效果表述过宽的问题。不建议改为“幅值阈值门控”，也无需因这项核查更换 [6]。

#### 置信程度、来源与访问限制

- **题录：高置信。** 出版商与作者机构记录一致。
- **式 (4) 的幂指数定义：高置信，但有访问形式限制。** 已读到由[Kevin Donohue 作者主页](https://uky.academia.edu/KevinDonohue)直接链接的 15 页原文全文网页转录，含期刊页眉、页码、DOI、式 (4) 及其端点解释；未成功取得 PDF 二进制或公式页面图像，因此不声称已做 PDF 视觉复核。网页存在双栏混排和符号提取缺陷，复数形式按公式及相邻正文等价整理。
- **支撑范围：** 可确认 PHAT-β/部分白化的背景引用；不能据此证明本文具体实现、参数最优性、无人机场景收益或普遍定位精度提升。本次不作这些核查。置信程度为证据评价，不是统计置信区间。

实际作为结论依据的原始来源为：

1. [作者主页：全文来源链](https://uky.academia.edu/KevinDonohue)。
2. [作者主页链接的文章全文：第 1678-1679、1681、1684 页](https://www.academia.edu/47489486/Performance_of_phase_transform_for_detecting_sound_sources_with_microphone_arrays_in_reverberant_and_noisy_environments)。工具曾将同文显示为[另一记录地址](https://www.academia.edu/108058530/Performance_of_phase_transform_for_detecting_sound_sources_with_microphone_arrays_in_reverberant_and_noisy_environments)；该地址不另算独立佐证。
3. [Elsevier/ScienceDirect：题录、摘要及引言](https://www.sciencedirect.com/science/article/abs/pii/S0165168407000370)。搜索工具可读取其索引正文，直接打开请求出现 403。
4. [University of Kentucky：作者机构题录及摘要](https://scholars.uky.edu/en/publications/performance-of-phase-transform-for-detecting-sound-sources-with-m/)。

### [7] Brümann and Doclo：辅助麦克风 SRP

**已确认的出版信息：** Klaus Brümann, Simon Doclo，*Steered Response Power-Based Direction-of-Arrival Estimation Exploiting an Auxiliary Microphone*，*2024 32nd European Signal Processing Conference (EUSIPCO)*，2024，pp. 917–921；DOI [10.23919/EUSIPCO63174.2024.10715232](https://doi.org/10.23919/EUSIPCO63174.2024.10715232)。[EURASIP 官方会议论文 PDF](https://eurasip.org/Proceedings/Eusipco/Eusipco2024/pdfs/0000917.pdf)及[会议议程](https://cmsworkshops.com/EUSIPCO2024/view_paper.php?PaperNum=2009)确认题名与作者；[作者单位 Oldenburg 的 2024 Science Bulletin](https://uol.de/f/6/Science_Bulletin/Science_Bulletin_2024.pdf)印刷 p. 79 明列正式页码与 DOI，另用 [IEEE 存入 Crossref 的记录](https://api.crossref.org/works/10.23919/EUSIPCO63174.2024.10715232)复核。姓名重音符 Brümann 应保留，Crossref 的 Brumann 是元数据转写，不应据此改错正式姓名。

**原文：** [本地正式会议 PDF](../../references/papers/brumann2024_auxiliary.pdf)，印刷 pp. 917–921。p. 917 说明紧凑阵列中噪声/混响的空间相干性问题；p. 918 式 (8) 使用空间分离的辅助麦克风构造阵列对的 PHAT 谱，辅助麦克风位置可以未知；pp. 919–920 分析距离/声学条件并在仿真语音场景验证。p. 920 明确指出某些靠近阵列或墙面的辅助位置没有改善，甚至略差。

**稿件位置与判断：** 两稿第 23 行“相干噪声中的辅助麦克风 SRP”归属正确。只是英文 `improve spatial reliability` 把有条件的结果压缩成了一般陈述，建议加一个条件，避免读者理解成任意空间位置或任意相干噪声都能改善。

- EN 短语：`SRP using a spatially separated auxiliary microphone under spatially coherent noise and reverberation [7]`；整句谓语用 `can improve localization under their respective operating conditions`。
- ZH 短语：`利用空间分离辅助麦克风缓解空间相干噪声与混响影响的SRP方法[7]`；整句谓语用 `可在各自适用条件下改善定位`。

这是**适用范围澄清**，不是错误引用。[7] 不直接验证本稿 208 通道、户外无人机、无辅助麦克风的实验性能；当前稿没有声称复现它，继续保留这一界限即可。

## 4. 核查边界与交付记录

- 网络证据均在本次核查中访问。使用出版社正式页面、作者公开论文、会议组织方原文、作者单位出版记录；Crossref 仅补核由出版社登记的出版字段。没有把第三方综述、搜索摘要或 AI 摘要当成原文证据。
- 原文阅读覆盖与缺口见覆盖表；[3] 后续正文缺口不得用其他论文转述“补成已读”。[4]、[5] 的作者稿页码与正式版出版页码已区分。
- 根目录未见 `.codegraph/`，本次未使用 CodeGraph；PDF 只读提取/内存渲染使用 PyMuPDF，未启动任何 LibreOffice，也没有保存下载 PDF、截图或中间提取文件。
- 两份主稿的核查快照 SHA-256：
  - `paper/field_en.md`：`C2A33E3C2778836E65F9913C8244F1FFC7CFAE3E4EE990B7842CA3410A59767D`
  - `paper/field_zh.md`：`26D1E6698531CB5AE8644C492258BDC03C3292E011CB42BAA58F522F2122F8CB`
- 本任务唯一写入文件：`research/real_data/reference_audit_sources_1_7_2026-11-08.md`。上述改句均为建议，未应用到主稿。
