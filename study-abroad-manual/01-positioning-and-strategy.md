# 01. 定位與策略

> 目標：想清楚你要走哪條路（PhD／MS），誠實盤點自己的優勢與缺口，並把研究題目包裝成美國教授會想收你的故事。

---

## 1.1 AI 加速器的職涯地圖

「做 AI 加速器」其實包含很多種職位。先搞清楚你想做哪一種，才知道該讀 PhD 還是 MS、該補哪些技能。

| 職位 | 在做什麼 | 常見學歷 | 和你目前背景的距離 |
|---|---|---|---|
| **Architecture / Performance Modeling** | 決定加速器的 dataflow、記憶體階層、運算單元配置；寫 performance model 做 design space exploration | **PhD 為主**（少數優秀 MS） | 近：co-design 經驗可以直接用上 |
| **RTL Design（micro-architecture）** | 把架構寫成可合成的 SystemVerilog，負責 timing、面積、功耗 | MS／PhD | 中：你會寫 RTL/HLS，但要補 ASIC 的時序與功耗觀念 |
| **Design Verification (DV)** | UVM testbench、coverage、formal；職缺最多的一類 | MS 為主 | 中遠：需要 SV/UVM |
| **Physical Design (PD)** | Floorplan、P&R、CTS、timing closure、signoff | MS 為主 | 遠：需要完整的 APR 經驗 |
| **DFT** | Scan、BIST、ATPG | MS | 遠 |
| **ML Compiler / Kernel / HW-SW Co-design** | 把模型映射到硬體：compiler（MLIR/TVM/Triton）、kernel、runtime | MS／PhD | 近：co-design 經驗很加分 |
| **Circuit（SRAM、CIM、高速 I/O）** | 客製電路 | PhD 較多 | 遠（除非你轉向電路） |
| **Research Scientist（NVIDIA Research、Google 等）** | 發論文、做下一代架構 | **幾乎都是 PhD** | 需要頂會論文紀錄 |

**雇主類型**（名單只是舉例，新創變動很快）：

- **GPU／CPU／SoC 大廠**：NVIDIA、AMD、Intel、Apple、Qualcomm、Arm
- **雲端業者的自研晶片**：Google（TPU）、Amazon（Annapurna Labs：Trainium/Inferentia）、Meta（MTIA）、Microsoft（Maia）
- **客製 ASIC／網通**：Broadcom、Marvell
- **AI 晶片新創**：Cerebras、Tenstorrent、Etched、MatX、d-Matrix、SambaNova 等。2025–2026 年併購、IPO、大額融資都很頻繁（例如 NVIDIA 和 Groq 在 2025 年底的授權／人才交易），**加入前要評估穩定性**
- **EDA**：Synopsys、Cadence、Siemens EDA（在 AI for EDA 方面也有很多機會）
- **記憶體**：Micron、Samsung/SK hynix 的美國據點（HBM、PIM 相關）

---

## 1.2 PhD 還是 MS？

| | PhD | MS |
|---|---|---|
| 年限 | 5–6 年（台灣碩士入學不一定會縮短） | 1–2 年 |
| 費用 | **通常全額資助**：學費全免加生活津貼（RA/TA/fellowship） | **多半自費**：總花費約 US$9–20 萬（見 [03](03-application-materials.md#38-費用估算)） |
| 錄取關鍵 | 研究經驗、推薦信、研究契合度（fit）、論文 | GPA、學校背景、專題、英文 |
| 錄取單位 | 系上委員會和／或個別教授 | 系上委員會 |
| 出路 | 架構師、research scientist、資深 RTL；也可以走學界 | RTL/DV/PD 工程師 |
| 起薪／職級 | 較高，常以 senior 或 PhD-level 聘用 | 新鮮人職級 |
| H-1B 抽籤（2026 新制） | 薪資級別通常較高 → **中籤率較高** | 新鮮人多落在 Level I–II → 中籤率較低（見 [07](07-reality-check.md#72-工作簽證與移民路徑的現實)） |
| 風險 | 時間成本、指導教授關係、研究卡關、經費 | 學貸壓力、找工作只有一次 CPT/OPT 窗口、就業市場波動 |

### 決策建議

- **想做 architecture／research，或者想要「設計下一代加速器」的角色** → PhD。
- **只想盡快進業界做 RTL/DV/PD，也有資金** → MS（選 thesis option 保留轉 PhD 的可能）。
- **不確定** → **兩者混合申請**：例如 8–10 所 PhD 加上 3–4 所 MS 當保底。不過同一所學校通常只能申請一個學位，先查規定。
- **你的狀況**：有研究題目、有 co-design 實驗室、有論文潛力，**以 PhD 為主**是 CP 值最高的路線：不用花錢、出路比較好、簽證優勢也比較大。

> 補充：美國 PhD 招生並不要求碩士學位，大學畢業就能直接申請。你的台灣碩士學歷帶來的主要優勢是**研究成果與成熟度**，而不是縮短年限（有些學校可以抵修課學分或讓你較早考資格考）。

---

## 1.3 誠實盤點：你的 SWOT

### Strengths（優勢）
- 做過**完整的 FPGA 加速器**，從演算法、架構到實作都碰過，這點很多申請者沒有
- 所在實驗室做 **HW/SW co-design**，這正是美國加速器實驗室最重視的思維
- 題目有 **真實且重要的 workload**（蛋白質結構預測，2024 年諾貝爾化學獎相關領域），故事性強
- 長序列問題本質上是「**記憶體受限、資料搬移主導**」的問題，和目前 LLM 加速的核心挑戰相通

### Weaknesses（缺口）— 接下來 12 個月要補
- **沒有 ASIC flow 經驗**（synthesis、STA、APR、PPA 分析）→ 見 1.5
- 可能缺少**嚴謹的 baseline 與評估方法**（最佳化過的 GPU baseline、能耗量測方法、準確度指標）
- **頂會論文紀錄**
- **驗證方法論**（SystemVerilog assertion、UVM 或 cocotb）
- **計算機結構的正規訓練**（如果還沒修過研究所等級的計結）
- 英文（見 [04](04-english.md)）

### Opportunities（機會）
- AI 硬體人才需求仍然很高，大廠持續聘用國際學生
- AI for Science 是新興方向，生醫加上硬體的跨域背景很少見
- 台灣有 TSRI（國研院台灣半導體研究中心）提供學界 EDA 工具與下線服務，相較許多國家的學生是優勢

### Threats（威脅）
- 美國政策不穩定（簽證、工作許可、研究經費，見 [07](07-reality-check.md)）
- 2026 Fall 頂尖研究型大學的 PhD 錄取人數比前一年約少 15%，已經是連續第二年下降（AAU 資料）
- 同領域申請者很強（中國、印度、韓國的申請者常常已有頂會論文）

---

## 1.4 研究題目的包裝：長序列蛋白質結構預測加速

這是你申請時最重要的武器，一定要包裝好。

### (1) 先徹底理解 workload

以 AlphaFold2 的 Evoformer 為例（AF3 的 Pairformer、Boltz、ESMFold 的 folding trunk 都有類似的 pair representation 與 triangle 運算）：

| 元件 | 形狀／複雜度 | 硬體上的意義 |
|---|---|---|
| Pair representation | L × L × c_z（c_z = 128） | **記憶體 O(L²)**。例如 L = 4,000 時，單一 FP32 張量約 4000² × 128 × 4 B ≈ **8.2 GB** |
| Triangle multiplicative update | 每個 (i,j) 都要沿 k 累加 → **O(L³·c)** 運算 | 計算量大，而且資料重用模式特殊 |
| Triangle attention | 每個 head 的 attention logits 有 **L × L × L** 個元素 | 不做 chunking 就放不下；做了 chunking 又會產生大量資料搬移 |
| MSA representation（AF2） | N_seq × L × c_m | 和 MSA 深度有關 |

**建議第一步**：在 GPU 上用 OpenFold、Boltz 或 ESMFold 跑 L = 256 到 4,000 以上，畫出：
1. 各個 kernel 的時間佔比
2. peak memory 和 L 的關係
3. roofline（哪些 kernel 是 memory-bound，哪些是 compute-bound）

這三張圖可以直接當論文和 SOP 裡的 motivation。

### (2) 知道前人做了什麼，並做出差異化

- **LightNobel（ISCA 2025，KAIST 團隊）**：以 token-wise adaptive activation quantization 搭配可重組的多精度矩陣單元，處理長序列 PPM 的 activation 爆量問題；論文宣稱 peak memory 降低上百倍，速度與能效都明顯超越 A100/H100。**這是你最直接的「競爭對手」，一定要精讀。**
- FastFold（2022）：從系統層面（平行化、通訊）加速 AlphaFold 的訓練與推論
- OpenFold：可訓練的開源 AlphaFold2 重現版本，適合拿來做 profiling
- 一般性的 attention 加速技術：FlashAttention 類的 tiling + online softmax、KV/activation 量化、sparsity

**可能的差異化角度**（和指導教授討論後選一個主軸）：
- **Dataflow／tiling**：針對 triangle multiplication／attention 設計跨運算融合（fusion）的資料流，減少 off-chip 存取
- **記憶體階層**：利用 HBM FPGA（例如 Alveo U280/U55C）或 near-memory 的設計
- **演算法近似**：pair representation 的稀疏性、低秩結構、跨層重用
- **Scale-out**：多 FPGA 或多晶片切分超長序列
- **精度**：和 LightNobel 不同的量化策略，或 FP8/MX 格式

### (3) 故事框架（SOP、面試、論文 intro 都能用）

```
問題  ：科學上需要預測長蛋白質與大型複合體（L > 1,000），但現有模型在長序列下記憶體爆量
瓶頸  ：pair representation 是 O(L²) 記憶體；triangle 運算是 O(L³) 的資料搬移
洞見  ：（你的關鍵觀察，例如某種 locality / precision tolerance / sparsity）
設計  ：演算法 + dataflow + 硬體的 co-design
結果  ：和強 GPU baseline 相比的速度、能效、記憶體；準確度以 lDDT / TM-score 驗證
泛化  ：同樣的方法適用於 long-context transformer、以 pairwise representation 為核心的 GNN 等
```

**最後一行「泛化」最重要。** 美國的加速器教授不一定關心蛋白質，但一定關心「你的 insight 能不能用在下一個 workload」。

### (4) 美國審稿人和教授期待的評估嚴謹度

- **Baseline 要強**：GPU baseline 必須是最佳化過的版本（例如 bf16、chunking、fused kernel），不能拿沒最佳化的 PyTorch 來比
- **能耗量測要說清楚**：FPGA 用板上量測還是工具估計？GPU 用 nvidia-smi 還是外部量測？
- **準確度**：用 CASP/CAMEO 等標準資料集，報告 lDDT/TM-score
- **Ablation**：每個設計元素各貢獻多少
- **ASIC 推估**：光有 FPGA 結果，說服力有限。若能附上 ASIC synthesis 的面積與功耗數字，說服力會高很多（見 1.5）

---

## 1.5 從 FPGA 銜接到 ASIC：最值得投資的 12 個月

你要申請的是 digital IC 方向，只有 FPGA 經驗會被認為「偏系統、偏原型」。以下是分階段的補強計畫：

### 階段 1：ASIC 綜合（1–2 個月）
- 把加速器的**核心運算單元**（例如 systolic array／triangle update engine）改寫或整理成乾淨的 SystemVerilog（如果原本是 HLS，可以先用 HLS 產生的 RTL，但最好能手寫關鍵模組）
- 用 Synopsys Design Compiler 或 Cadence Genus 做 synthesis
  - 製程：透過 **TSRI** 取得的學界製程（詢問實驗室／學校），或 **ASAP7**（學界常用的 7nm 預測型 PDK）
- 用 PrimeTime/Tempus 做 STA，報告面積、功耗、頻率

### 階段 2：APR（2–3 個月）
- ICC2 或 Innovus：floorplan → placement → CTS → routing → 修 timing
- 或者走開源流程：**OpenROAD / OpenLane**（搭配 SKY130、GF180、IHP SG13G2 或 ASAP7）
- 產出：post-layout 的 PPA、layout 截圖（很適合放在 CV 和網站上）

### 階段 3（選做）：下線
- TSRI 晶片下線服務：週期長（從設計到拿回晶片需要數個月），要看實驗室能不能配合
- Tiny Tapeout：成本低、面積小，適合放一個小型測試設計；2025 年 Efabless 倒閉後已改用 IHP 的 shuttle（2026 年仍在運作，條款有改變，要先讀清楚）
- **不一定需要下線**。對申請來說，完整的 post-layout PPA 已經很有說服力

### 階段 4：驗證能力（並行進行）
- 替你的 RTL 寫一套像樣的 testbench：SystemVerilog + assertion，或 **cocotb**（Python 驗證框架，適合 co-design 背景的人）
- 加上 coverage 報告

### 在台灣可以利用的資源
- **課程**：研究所等級的計算機結構、VLSI 系統設計、數位 IC 設計。例如陽明交大的積體電路設計實驗（ICLAB）這類高強度課程，在業界和學界都有口碑
- **競賽**（有時間再參加）：旺宏金矽獎、大學院校積體電路設計競賽、CAD Contest @ ICCAD
- **TSRI**：EDA 工具授權、製程資源、下線服務、教育訓練課程

---

## 1.6 策略總結

```
主軸   ：以 PhD 為主（8–10 所）+ 少量 MS 保底（視資金狀況）
研究   ：長序列蛋白質結構預測加速 → 包裝成「記憶體受限的長序列 pairwise 運算加速」
補強   ：ASIC flow（PPA 數字）+ 驗證 + 計算機結構
產出   ：1 篇第一作者論文 + 開源 repo + 個人網站 + 3 分鐘研究簡報
選校   ：以教授 fit 為核心，分成 A 類（加速器架構）、B 類（數位 IC 下線）、C 類（FPGA/HLS 銜接）三類混合（見 05）
```
