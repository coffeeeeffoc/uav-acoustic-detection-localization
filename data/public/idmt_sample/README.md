# IDMT 真实录音小样

核验日期：2026-10-02。正式引用key：`idmt`，JSON第19项。

来源：https://zenodo.org/records/17525811 ，作者Ximei Yang、Joerg Bitzer。音频/CSV：CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）。下载时仅通过HTTP Range提取ZIP指定成员，未下载1.515GB全包，更未下载13GB库；音频与CSV保持原字节。原成员名、URL、哈希见`provenance.json`。

- WAV：30秒，8通道，48000 Hz，16-bit PCM，23,040,044 bytes。
- `DOATruePos.csv`：3000行，time/X/Y/Z/ele/azi；time约0至29.99秒。当前Z恒0、ele恒90，**不是真实俯仰/高度标注**；官方README说明只能评估方位。
- CSV是0.01秒网格，不能把它称为100Hz原始GPS测量；官方描述GPS采样10Hz。
- `upstream_Reusev301.yaml`：官方8麦克风坐标及中心/旋转参数，坐标与论文Fig.1一致；**WAV实际通道对应和157.5度世界坐标旋转未独立验证**。
- `upstream_README.md`、`upstream_LICENSE`、`upstream_params_srp.json`：作者仓库固定提交的原始小文件，代码许可MIT，与数据CC BY 4.0分开。
- `sample_metadata.json`：读取头部和CSV得到的元数据，非定位结果。

本稿仅用于描述性频谱，不开展单样本方位pilot、不报告方位成绩。将来若做pilot，须另行核对通道、坐标、角度方向和时间/传播延迟，本次不新增校准或对齐假设。一个session的片段不代表完整benchmark，不支持分类准确率、跨场地泛化或俯仰精度结论。本调研人员没有运行定位/分类实验。
