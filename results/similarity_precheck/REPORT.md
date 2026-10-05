# 论文相似文本初检报告

检测日期：2026-10-05（北京时间）。

**结论：在本次本地资料范围内，未发现英文正文连续 8 个或更多词完全相同的文本；短语重合约 0.50%。尚未取得 iThenticate 报告，正式总重复率与单一来源重复率均未知，不能认定已满足投稿阈值。**

## 检测对象与完成状态

本次检查当前 DCCR 实测论文，英文提交文件为 `paper/English_Main.docx`、`paper/English_Main.pdf`（10 页），可重建源稿为 `paper/field_en.md`。另对 `paper/field_zh.md` 中文译稿进行辅助字符比对。文件 SHA256、完整逐来源结果和统计口径记录在 `local_metrics.json`。

投稿要求来自本项目 `README.md`：总重复率不得超过 24%，单条引用源不得高于 3%。该要求未说明参考文献、引号和短匹配的过滤设置。

已打开 iThenticate 官方登录页，页面没有已登录会话。用户确认没有可用账号，选择先查看初检结果。因此本次没有向 iThenticate 上传全文、消耗额度或产生平台检测报告。

## 本地英文结果

核心计算是连续相同词/token 匹配：大小写统一、标点规范化，重合位置去重。分母为正文、章节标题及图表说明；不包括参考文献、显示公式和表格数值。词/token 包括数字，不能视为平台的官方字数统计。

| 最短连续匹配长度 | 实际英文 Word 正文重合覆盖 | 单一来源最高覆盖 | Markdown 源稿重合覆盖 |
|---|---:|---:|---:|
| 5 词/token | 21 / 4177 = **0.5028%** | 11 / 4177 = **0.2633%** | 21 / 4188 = 0.5014% |
| 8 词/token | **0%** | **0%** | 0% |
| 12 词/token | **0%** | **0%** | 0% |

两种文件得到相同的重合词位置数量；分母小幅差异来自导出文档的索引词/字符及排版表示。PDF 文本层确认是同一题名和 DCCR 稿，内容覆盖核对及首页图留在本目录。

连续 5 词的重合主要来自以下通用或题名短语；没有发现长段落照搬的证据：

| 主稿中的重合片段 | 匹配资料 |
|---|---|
| c is the speed of sound | Valin 2007、Salvati 2017、Rodriguez 2025 |
| in noisy and reverberant environments | Valin 2007 |
| recordings of a DJI Air | Rodriguez 2025 |
| and direction finding of small | 陈鹏等 2022 综述的英文参考文献题名 |

最高单源为 Valin 2007 与 Rodriguez 2025，各覆盖 11 个主稿 token。匹配是按相同字符顺序识别，未据此判断是否属于抄袭。通用声速定义、环境描述及机型名称不需要仅为消除匹配而改动。

## 比对库与缺口

共读取 15 份外部资料，其中 14 份具有可用文本层并纳入比对：

- 英文论文全文 9 份：Brümann 2024、Grinstein 2024、Gupta 2025、Jekateryńczuk 2025、Rodriguez 2025、Safavi 2025、Salvati 2017、Valin 2007、Yang 2025。
- 中文参考资料 1 份：陈鹏等《无人机声学定位技术综述》。
- 赛题与设备原始资料 4 份：试验说明、赛题说明、赛题题目、产品手册。

本稿 12 条引用中，能够比对相关全文/原始文档的是 [1]、[4]、[5]、[7]、[9]、[10]、[11]、[12]。以下 4 条没有完成全文比对：

- [2] Knapp and Carter 1976：本地 PDF 为纯扫描图像，没有可用文本层，本次未执行 OCR。
- [3] DiBiase et al. 2001：本地没有全文。
- [6] Donohue et al. 2007：本地没有全文。
- [8] Uluskan 2024：本地没有全文。

旧稿、模板、当前稿的中英文互译、内部研究笔记及生成报告均未当作外部来源计入。这样避免同一论文的工作副本影响外部资料初检。

## 中文辅助初检

中文译稿按连续 13、20、30 个汉字统计，与本地资料均未产生匹配；分母为 6491 个汉字。该方法去除非汉字字符后比对，可能跨越英文和数字，且不能检测翻译式重用。此结果仅为辅助观察，不能解释为知网或其他平台的 0% 查重率。

## 公开网页抽查

抽查了稿件题名及 11 个特色句/短语，覆盖引言、方法与讨论。返回结果中的摘要没有展示与被检索表述完全一致的句子；部分返回结果明显放宽了引号条件或仅按主题词匹配，因此这里不计算网页重复率，也不据此认定互联网上不存在重合。

查询表述如下（每条作为带引号查询）：

1. direction-conditioned coherence ranking
2. A strong spatial peak establishes + UAV
3. PHAT searches for broadband phase agreement
4. The score is a regression score for ranking and thresholding
5. Multiplying the entire map by a single positive detector score
6. Each direction is then represented + cross-spectral coherence
7. Passive acoustic sensing provides a direct observation
8. Wind, vehicles, machinery and other coherent backgrounds
9. Acoustic Detection and Direction Finding of Small UAVs Using Direction Conditioned Coherence Ranking
10. A linear ridge score learns which profiles correspond to the aircraft
11. The six held-out recordings are the relevant units of evidence
12. positive channel gains cancel between cross- and auto-spectra

这里只核查返回的搜索结果摘要，未声称读取所有候选网页全文。短句抽查无法覆盖付费文献库、学生论文库、未索引全文和改写或翻译形式的相似内容。

## 正式检测需要的结果

iThenticate 的相似度来自提交文本与所选比对库的匹配，涉及平台库和过滤设置；本地覆盖率不能换算为它的最终得分。[Crossref 官方说明](https://www.crossref.org/documentation/similarity-check/similarity-report-understand/)

后续应通过有额度的 iThenticate 账号检测当前英文主稿，保留报告全文、总相似度、最高单一来源比例及过滤设置。参考文献、引号与短匹配如何处理应按目标刊会要求，不能为了达到阈值任意排除实际来源。取得报告前，24% 与 3% 两项合规状态均为**未验证**。[iThenticate 官方操作指南](https://guides.ithenticate.com/hc/en-us/articles/27241470046989-iThenticate-quickstart-guide)

本次未修改论文正文。已保存的本地比对脚本为 `code/similarity_precheck.py`，重跑会更新本目录 `local_metrics.json`。
