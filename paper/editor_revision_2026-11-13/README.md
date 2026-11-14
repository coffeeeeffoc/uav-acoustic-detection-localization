# 编辑意见修订版与中文译稿

本目录是当前论文交付入口。英文以导师手动修改的附件为基准，于2026-11-13针对编辑提出的“声学测向和无人机探测内容偏少、图较多、需要补充正文”完成修订；2026-11-15补齐对应的中文全文和中英文PDF。

| 版本 | 可编辑Word | PDF | 在线阅读 |
| --- | --- | --- | --- |
| 英文修订稿，5页 | [DCCR_Editor_Revised.docx](DCCR_Editor_Revised.docx) | [DCCR_Editor_Revised.pdf](DCCR_Editor_Revised.pdf) | [英文正文](manuscript_en.md) |
| 中文完整译稿，5页 | [DCCR_Chinese_Revised.docx](DCCR_Chinese_Revised.docx) | [DCCR_Chinese_Revised.pdf](DCCR_Chinese_Revised.pdf) | [中文正文](manuscript_zh.md) |

两稿均为A4双栏，包含2幅图、3张数据表、9个公式和12条参考文献。参考文献均从第5页开始。中文图内标注、表头、正文和图注均已同步。作者姓名保留导师稿的罗马字拼写，未自行推定中文姓名。

## 修订内容

- 英文正文净增约930词，补充旋翼谐波与声源关联、阵列孔径与时延、频率与相位歧义、相干归一化和方向排序的原理解释。
- 分开说明候选选向与检测阈值决策，解释相同检测门控下的联合成功计数，以及候选覆盖对剩余误差的限制。
- 删除与数值表重复的原图2；将原表III的四段录音结果转入正文。原图3改为图2，原表IV改为表III。
- 保留导师稿的作者顺序、单位、邮箱、通讯作者标记、基金致谢及原始实验结果。中文完整对应修订后的英文，不沿用旧版15条参考文献的编号。

## 重建与核验

英文Word是本次版式和内容基准，`translation_zh.json`保存逐段中文译文。使用包含`python-docx`的Python环境，从仓库根目录运行：

```powershell
python paper/editor_revision_2026-11-13/build_chinese.py
```

脚本校验英文基准文件SHA256后生成中文Word和两份在线阅读稿，并检查译文覆盖、数值、表格、公式与参考文献的一致性。Markdown是阅读副本，不用于重现Word分页。编辑英文Word后，必须同步译文映射并复核基准哈希，不能仅修改哈希跳过内容核对。

PDF使用Microsoft Word原生导出，之后逐页渲染检查。当前文件的页数、哈希和核验范围见[verification.json](verification.json)。本次没有重新训练模型或重跑原始录音实验，也没有进行新实测、正式查重或投稿。

## 历史材料

上一级的`English_Main.*`、`Chinese_Translation.*`、`field_*.md`及其生成脚本保留为2026-11-08及此前版本。它们与本目录的导师稿修订版是不同版本，旧版脚本不会重建本次交付。
