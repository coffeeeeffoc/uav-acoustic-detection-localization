# Foundations 来源与获取记录

核实日期：2026-10-02（按任务指定固定）。正式引用见 `foundations_verified.json`，数组仅4条：Knapp1976、DiBiase2001、Schmidt1986、Uluskan2024。Chang2018的已核实书目及摘要级方法放在Uluskan的notes中，不另占主引用条数。Salvati只保留已获取的辅助原稿及下载记录，不进入主refs。

本任务只写上述JSON、本说明及下列2份PDF；未改其他文件，未跑实验、未研究数据集。

## 已保存的PDF

| 本地文件 | 来源与版本 | 下载结果 | 字节数 | SHA-256 |
| --- | --- | --- | ---: | --- |
| `papers/knapp_carter_1976_gcc.pdf` | [IIT Bombay机构课程目录中的原论文扫描件](https://www.ee.iitb.ac.in/course/~sachinnayak/finalpaper2.pdf)，8页；不是作者接受稿，不推定开放许可 | HTTP 200；Content-Type为application/pdf；验证了PDF文件头和可解析页数 | 2895325 | `8459b1ff1d0defd8cad60fa77bdeac18346b74d24897e2aafb42cfd067379ba3` |
| `papers/salvati_2017_gsg_arxiv_v4.pdf` | [作者arXiv稿](https://arxiv.org/pdf/1512.03261)，12页；正文版本标记1512.03261v4，2018-03-07 | HTTP 200；Content-Type为application/pdf；验证了PDF文件头和可解析页数 | 2075049 | `25e13f2db9ae31ef145e5053cdeb34f0726119ffdee692af6005554a9472da64` |

Salvati首次使用[固定v4 PDF入口](https://arxiv.org/pdf/1512.03261v4)下载返回HTTP 406，未保存该失败响应；随后从上表无版本入口取得PDF，已在内容中核实为v4。不能把文件名中的2017视为预印本版本日期。正式期刊题名是 *Exploiting a geometrically sampled grid in the steered response power algorithm for localization improvement*，JASA 141(1), 586–601 (2017)，DOI [10.1121/1.4974289](https://doi.org/10.1121/1.4974289)；arXiv题名不同。二者关系以[作者机构出版列表](https://users.dimi.uniud.it/~daniele.salvati/publications/)与[arXiv记录](https://arxiv.org/abs/1512.03261)交叉核验。按最新指令，此篇不列正式引用。

## 未保存PDF的条目及访问边界

- **DiBiase2001**：[Springer原始书章页](https://link.springer.com/chapter/10.1007/978-3-662-04619-7_8)公开元数据与摘要，正文为订阅内容；未取得正文PDF，未尝试购买或绕过访问限制。只核实2001书章，不以2000论文替代。无本地字节数/哈希。
- **Schmidt1986**：[IEEE原始入口](https://ieeexplore.ieee.org/document/1143830)显示JavaScript/机器人验证；Crossref核实出版信息。工具读取了JSON证据中列出的第三方所托管原论文复制件前两页文本，未下载到本地。无本地字节数/哈希。
- **Uluskan2024**：[SAGE原始页](https://journals.sagepub.com/doi/abs/10.1177/1475472X241259082)公开完整摘要和书目，标记Restricted access；未取得全文PDF。另核验[作者机构条目](https://akademik.eskisehir.edu.tr/seckinuluskan/makaleler)的检索可见内容及Crossref出版商摘要。无本地字节数/哈希。
- **Chang2018（仅notes）**：[IEEE原始入口](https://ieeexplore.ieee.org/document/8417601/)本次为验证页；[Crossref](https://api.crossref.org/works/10.1109/VTCSpring.2018.8417601)核实六位作者、题名、VTC Spring 2018、1–5及DOI，[官方节目单第39页](https://www.ieeevtc.org/vtc2018spring/final-program.pdf)交叉核实。未取得论文PDF；方法依据[原摘要的ResearchGate镜像](https://www.researchgate.net/publication/325555605_Feature_Extracted_DOA_Estimation_Algorithm_Using_Acoustic_Array_for_Drone_Surveillance)，不是出版商正文阅读。共作者[个人页](https://sites.google.com/view/pengfei-pub/home)误写VTC-Fall，已按官方资料纠正。无本地字节数/哈希。
- Knapp的[IEEE入口](https://ieeexplore.ieee.org/document/1162830)同样出现验证页；成功下载的是上表机构课程目录中的原论文扫描件。

以上“未取得”与“HTTP下载失败”不同：未对每篇都发起PDF下载请求，不把未尝试写成失败，不用HTML响应冒充PDF。

## 实际阅读范围与合并提示

- **Knapp**：目读印刷页320、322，其余未通读。第322页的SCOT相干性归一化、PHAT低信号功率频段误差放大，以及信号/噪声特征进一步加权讨论，是本次实际读到的noise/coherence相关先例。
- **DiBiase**：读出版商摘要/书目与[国家图书馆所存章节目录](https://d-nb.info/961270640/04)，未读章节正文。麦克风对GCC-PHAT累加实现由Salvati作者稿第1页交叉核验，不能标为已直接核查DiBiase公式。
- **Schmidt**：读原论文复制件印刷页276–277的文本，包括作者全名、1979先行版本的编辑注、模型与子空间算法开头；未读完全部示例。
- **Uluskan**：读原始摘要和元数据，未读正文或视频；能够确认谐波邻域DFT进入SRP-PHAT，但不能补写邻域宽度、基频跟踪、阵列布局与误差数字。
- **Chang**：书目有官方证据，方法只到原摘要镜像；可确认摘要描述“选谐波、逐谐波MUSIC、按谐波能量融合DOA”，不能将其等同为加权SRP。
- **Salvati（辅助）**：定点读作者稿PDF页1–3的摘要、引言、空间网格/TDOA及SRP-PHAT公式；未通读实验与全部推导。

Uluskan与Chang均以无人机声信号为被定位对象；本次取得的摘要未直接披露地面固定架设方式，JSON已保留该边界，不能宣称已完整核实地面安装几何。没有根据摘要判定其全文完全不存在额外noise/coherence处理，也没有把人工仿真建议写成作者实验结果。未执行任何定位仿真。

