# 导师稿编辑意见修订记录

修订基准为用户提供的[导师原件](supervisor_original.doc)，SHA256 为 `494b2f2b789be7ee495df33ad3be67720d271fce44caeca8f6a7660b70de53c2`。[转换后的 DOCX](supervisor_original.docx)是[英文修订脚本](revise_manuscript.py)的输入，输入与输出文件的哈希见[核验记录](revision_checks.json)。运行脚本会写入 `paper/editor_revision_2026-11-13/DCCR_Editor_Revised.docx`，回放时请使用单独的检出目录。

- 补充无人机旋翼谐波与声源关联、阵列孔径和时延、频率与相位歧义、相干归一化、候选方向排序以及检测门控解释。
- 新增同一检测门控下的成功计数、候选覆盖与排序失误的区分、距离与背景标定条件的分析。
- 删除原图2（与结果表重复的分布及工作点图）；删除原表III并将四段录音结果保留在正文。原图3改为图2，原表IV改为表III。最终2图、3张数据表、9个公式、12条参考文献。
- 修复图注粘连、缺失图注、表题粘连、浮动表格和末条参考文献格式。保留导师的标题、作者单位、邮箱、通讯作者标记、基金致谢和摘要。
- 正文段落按空白切词（不含标题作者、摘要关键词、参考文献及表格内文字）从1795词增至2726词，净增931词。净增量包含用正文替代原表III的数据解释。
- Word实排5页，参考文献从第5页右栏开始。最终5页均已渲染并人工视觉检查。

## 数据核对

只读核对 `results/field/predictions.csv` 和 `candidates.csv`。PHAT/DCCR超过10度的窗为91/36；DCCR检出514窗，联合成功513窗；相同门控下PHAT联合成功459窗。DCCR失败窗中34窗无10度以内候选，33窗来自P3 take 2。三张保留数据表的所有单元格与导师稿一致；九个公式XML与转换后的导师稿一致。

## 文献与边界

新增旋翼谐波说明使用原参考文献[8]，核对出版社摘要：https://journals.sagepub.com/doi/10.1177/1475472X241259082 。阵列与频率解释核对原参考文献[4]：https://link.springer.com/article/10.1186/s13636-024-00377-z 。[12]按本地采集材料补全来源名称。未增加文献数量。

未重新训练或运行原始录音实验，未进行新的现场试验、正式查重或投稿。新增数值为现有逐窗记录的统计及已给定参数的算术推导。期刊总页数上限未收到明确回复，本版保持5页。

## 渲染

技能包render_docx.py因当时的Windows运行时不带LibreOffice而失败；随后使用Microsoft Word导出PDF，用Poppler渲染PNG。[导师稿预览](supervisor_original.pdf)、[首轮修订预览](revised_v1.pdf)和[最终交付 PDF](../../../paper/editor_revision_2026-11-13/DCCR_Editor_Revised.pdf)保留供版式对照。
