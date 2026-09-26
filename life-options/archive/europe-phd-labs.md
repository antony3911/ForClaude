# 09. 深入研究：歐洲做 AI 硬體的 PhD 實驗室

> 第二輪深入探索的第二篇（佇列 D2）。第一輪發現「歐洲的 PhD 是有薪水的工作，而且你的碩士正好符合資格」，這篇列出**和你的背景（AI 加速器、HW/SW co-design、FPGA、生物資訊加速）最對口的歐洲實驗室**，以及怎麼找職缺、怎麼申請。
> 資料狀態：2026/09。教授名單已逐一網路查證任職單位，但**是否正在招生要看各實驗室當下的職缺**。

---

## 1. 最對口的實驗室

### 🎯 第一優先：和你的研究幾乎完全重疊

| 教授 | 學校 | 為什麼適合你 |
|---|---|---|
| **Marian Verhelst** | **KU Leuven（MICAS 實驗室）＋ imec**，比利時 | 研究嵌入式機器學習、**硬體加速器、HW-演算法 co-design**、低功耗邊緣運算；2026 年有 **LLM 加速器**與硬體生成框架的研究；曾在 Intel Labs 工作；也是荷蘭 AI 晶片新創 **Axelera AI** 的科學顧問 |
| **Luca Benini** | **ETH Zurich**（數位電路與系統實驗室，IIS），瑞士；同時任教於義大利 Bologna 大學 | 主導全球知名的開源 **PULP 平台**（RISC-V）；有 PhD 職缺是做「在 RISC-V 伺服器與加速器上部署與最佳化基礎模型（foundation models）」 |
| **Onur Mutlu** | **ETH Zurich**（SAFARI 實驗室），瑞士 | 計算機結構、**記憶體內運算**，以及**基因體分析的硬體加速**（演算法與架構 co-design 可以帶來 100 倍以上的改善）；2026 年在 FCCM 辦了「組學（omics）的新世代可調適計算」workshop。**和你的生醫加速題目最接近** |
| **Zaid Al-Ars** | **TU Delft**，荷蘭 | 大數據加速、**高效能基因體分析**、ML 架構；做過 **FPGA 上的 systolic array 加速基因比對**（BWA-MEM、Smith-Waterman）。**FPGA + 生物資訊，和你的背景高度重疊** |

### 第二優先：AI 晶片與數位 IC 設計

| 教授 | 學校 | 研究重點 |
|---|---|---|
| **Hussam Amrouch** | **TU Munich**（AI 處理器設計講座，AI-Pro），德國 | AI 處理器設計、腦啟發運算；也是 TUM 的高科技 AI 晶片中心（MACHT-AI）創始主任 |
| **Christian Mayr** | **TU Dresden**（高度平行 VLSI 系統與神經形態電路講座），德國 | **SpiNNaker2** 神經形態超級電腦（已由新創 SpiNNcloud Systems 商業化）；而且 **Dresden 是歐洲的晶片城**（ESMC、Infineon、GlobalFoundries） |
| **Tobias Gemmeke** | **RWTH Aachen**（積體數位系統，IDS），德國 | VLSI 設計、以實體為導向的數位訊號處理元件設計 |
| **Georgi Gaydadjiev** | **TU Delft**（計算機結構），荷蘭 | 可重組（reconfigurable）、高度客製化的計算系統 |

### 第三優先：FPGA 與 ML 加速器（英國）

| 教授 | 學校 | 研究重點 |
|---|---|---|
| **George Constantinides** | **Imperial College London** | 高階合成（HLS）、計算機算術、LUTNet（在 FPGA 上做高效率的神經網路推論） |
| **Christos Bouganis** | **Imperial College London**（iDSL 實驗室） | fpgaConvNet（自動把 CNN 映射到 FPGA）、嵌入式系統的 ML 加速器 |

> **注意**：英國的 PhD 通常是**獎學金（stipend）**而不是員工薪資，國際生還可能需要自行處理學費差額，申請前要確認資助條件。瑞士、荷蘭、比利時、德國多半是**正式雇用**。

---

## 2. 怎麼找職缺

歐洲的 PhD **沒有固定的申請季**，職缺全年都會開，而且通常是**一個專案、一個職缺**。

| 管道 | 說明 |
|---|---|
| **各校的職缺頁面** | 例如 ETH 的 jobs.ethz.ch、TU Delft 各系的「vacancies」頁面、KU Leuven 的 jobsite |
| **imec 的 PhD 頁面** | 2026 年秋天會開放下一輪申請，有 150 多個職缺 |
| **Academic Positions**（academicpositions.com） | 歐洲學術職缺的大型平台 |
| **EURAXESS** | 歐盟官方的研究人員職缺平台 |
| **教授的實驗室網站** | 很多教授會在網站上寫「open positions」 |
| **直接寫信給教授** | 在歐洲比美國更常見也更有效，因為教授通常自己握有專案經費 |

### 瑪麗居禮博士網絡（MSCA Doctoral Networks）
- 歐盟資助的**跨國 PhD 計畫**，同一個網絡通常有 10–15 個職缺，分散在不同國家的學校與公司
- **薪資優渥**（依國家不同，常見範圍約每月 €3,000–5,000），還有移動津貼與家庭津貼
- **所有國籍都可以申請**
- **移動規則**：到職前 3 年內，**在該國居住或工作不能超過 12 個月**。你一直在台灣，**所以歐洲每個國家的職缺你都符合資格**

---

## 3. 申請流程（一般情況）

```
找到職缺 → 準備文件 → 線上申請 → 面試（通常 1–3 輪）→ 錄取 → 簽約、辦簽證
```

| 文件 | 說明 |
|---|---|
| **CV** | 1–2 頁，研究經驗放最前面 |
| **動機信（motivation letter）** | **針對這個職缺**寫：你為什麼適合這個專案 |
| **推薦人** | 通常 2–3 位 |
| **成績單、學位證明** | 碩士學位是基本要求 |
| **研究計畫** | 有些職缺會要求 |
| **英文證明** | 依學校而定 |

**面試常見形式**：研究經驗簡報（例如 15–20 分鐘講你的碩士研究）、技術問題、和實驗室成員聊天；有些會出小作業。

---

## 4. 你的優勢與要準備的事

**優勢**
- **已經有碩士**：歐洲 PhD 的基本要求
- **研究題目在前沿**：長序列蛋白質結構預測的硬體加速，同時和 AI 硬體、生物資訊加速兩個熱門方向有關
- **FPGA 實作經驗**：很多歐洲實驗室（TU Delft、Imperial、ETH）都做 FPGA 或需要原型驗證

**要準備的**
- 碩士論文盡量**投稿**（即使還在審查，也可以寫在 CV 上）
- 準備一份**研究簡報**（15–20 分鐘，英文）
- 英文口說（面試）

---

## 5. 建議的時間安排

```
碩士期間     投稿論文、整理研究成果
畢業 → 當兵  入營前先把 CV、動機信的範本準備好
退伍後       開始瀏覽職缺、寫信給教授；可以一邊在台灣工作一邊申請
             （歐洲 PhD 全年都有職缺，不需要像美國一樣等申請季）
錄取後       約 3–6 個月辦簽證、搬家
```

---

## 6. 結論

- **KU Leuven／imec 的 Marian Verhelst** 和 **ETH 的 Luca Benini**，是你「AI 加速器 + co-design」方向的頂尖選擇
- **ETH 的 Onur Mutlu** 和 **TU Delft 的 Zaid Al-Ars**，最能延續你「生物資訊加速」的研究題目
- **Dresden（TU Dresden）** 同時有學術和產業（ESMC、Infineon），而且德國的學制讓你之後比較容易留在歐洲
- **MSCA 博士網絡**讓你一次能申請多國的職缺，而且你一定符合移動規則

---

## 來源
- [KU Leuven MICAS：Marian Verhelst](https://micas.esat.kuleuven.be/team/marian-verhelst)、[Axelera AI：Marian Verhelst](https://axelera.ai/our-team/marian-verhelst)、[Leuven.AI：Marian Verhelst](https://ai.kuleuven.be/members/00043529)
- [ETH IIS：Luca Benini](https://iis.ee.ethz.ch/people/person-detail.luca-benini.html)、[ETH 職缺：Secure Machine Learning on RISC-V Servers and Accelerators](https://jobs.ethz.ch/job/view/JOPG_ethz_uISqHLPvTjDT3E4Irn)、[ETH 職缺：Scalable Parallel Architectures for 5G/6G](https://jobs.ethz.ch/job/view/JOPG_ethz_w9LaAGpST7VEY8e6bB)
- [SAFARI Research Group（Onur Mutlu）](https://safari.ethz.ch/)、[SAFARI：FCCM 2026 Omics Workshop](https://events.safari.ethz.ch/fccm2026-omics/)
- [TU Delft Research Portal：Zaid Al-Ars](https://research.tudelft.nl/en/persons/z-al-ars)、[TU Delft：FPGA systolic array for BWA-MEM](https://research.tudelft.nl/en/publications/an-fpga-based-systolic-array-to-accelerate-the-bwa-mem-genomic-ma/)、[TU Delft：Georgi Gaydadjiev](https://www.tudelft.nl/en/eemcs/the-faculty/departments/quantum-computer-engineering/sections/computer-engineering/staff/georgi-gaydadjiev/)、[TU Delft QCE：PhD and postdoc positions](https://www.tudelft.nl/en/eemcs/the-faculty/departments/quantum-computer-engineering/join-us/phd-and-postdoc-positions)
- [TUM AI Processor Design：Hussam Amrouch](https://www.ce.cit.tum.de/en/aipro/team/hussam-amrouch/)、[TUM：Prof. Hussam Amrouch](https://www.professoren.tum.de/en/amrouch-hussam)
- [TU Dresden：Neuromorphic Computing for More Efficient AI Systems](https://tu-dresden.de/ing/elektrotechnik/die-fakultaet/aktuelles/news/durch-neuromorphes-rechnen-zu-effizienteren-ki-systemen)、[Human Brain Project：SpiNNaker2 at TU Dresden](https://www.humanbrainproject.eu/en/follow-hbp/news/second-generation-spinnaker-neurorphic-supercomputer-to-be-built-at-tu-dresden/)
- [RWTH IDS：Prof. Tobias Gemmeke](https://www.ids.rwth-aachen.de/en/chair/team/head)
- [Imperial：George Constantinides 專訪](https://www.imperial.ac.uk/news/109969/profile-dr-george-constantinides-custom-computing/)、[Imperial：Christos-Savvas Bouganis](https://www.imperial.ac.uk/people/christos-savvas.bouganis)
- [imec：PhD at imec](https://www.imec-int.com/en/work-at-imec/job-opportunities/phd-at-imec)
- [MSCA Doctoral Networks 資訊說明](https://www.kowi.de/Portaldata/2/Resources/heu/msca/information_note_for_marie_sk_odowska-curie_fellows-NC0324067ENN.pdf)、[Marie Curie PhD Scholarship 概覽](https://applyindex.com/financial-aid/marie-curie-phd-scholarship/)
