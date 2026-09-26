# 08. 技術能力路線圖

> 目標：從「FPGA 加速器研究者」變成「懂 ASIC、也懂架構的 AI 加速器設計者」。
> 對 MS 路線來說，這一章的最終目的是**入學第一學期就能通過業界的技術面試**。這些能力也同時支撐你的研究和申請。

---

## 8.1 知識地圖

### (1) 數位設計基礎（面試必考）
- FSM、pipelining、valid/ready handshake、FIFO（同步與非同步）、arbiter
- **CDC**（clock domain crossing）：雙級同步器、gray code、非同步 FIFO
- Reset 策略（同步 vs 非同步）
- **時序**：setup／hold、clock skew／jitter、multicycle path、false path
- **低功耗**：clock gating、power gating、multi-Vt、DVFS
- SRAM macro、banking、register file 與 SRAM 的取捨

### (2) ASIC 流程
```
RTL → Lint → Simulation → Synthesis → STA → DFT(scan) → Floorplan → Placement → CTS → Routing → Signoff(DRC/LVS/IR/EM) → Tapeout
```

| 階段 | Synopsys | Cadence | Siemens | 開源 |
|---|---|---|---|---|
| 模擬 | VCS | Xcelium | Questa | Verilator、Icarus |
| 合成 | Design Compiler／Fusion Compiler | Genus | — | Yosys |
| STA | PrimeTime | Tempus | — | OpenSTA |
| APR | ICC2 | Innovus | — | OpenROAD／OpenLane |
| Signoff | IC Validator | Pegasus | Calibre | Magic、KLayout、Netgen |

### (3) 驗證
- SystemVerilog（OOP、constrained random）、**SVA**（assertion）
- UVM 基礎（業界 DV 職位必備）
- Coverage（code／functional）
- Formal 驗證的基本觀念
- **cocotb**：用 Python 寫 testbench，很適合 co-design 背景的人

### (4) 計算機結構
- Pipeline、hazard、branch prediction
- Cache、記憶體階層、coherence 基礎
- GPU（SIMT、warp、shared memory、tensor core）
- **Roofline model**、Amdahl's law
- DRAM／HBM 的基本特性（頻寬、延遲、bank）

### (5) AI 加速器專門知識（你的核心）
- **Systolic array** 與 dataflow 分類：weight／output／input／row stationary
- **Loop nest、tiling、mapping**（Timeloop 的思考方式）
- **稀疏性**：structured（例如 2:4）vs unstructured
- **量化**：INT8／INT4、FP8（E4M3／E5M2）、**microscaling (MX) 格式**
- **Attention**：FlashAttention 式的 tiling 與 online softmax、KV cache、long context
- **非線性函數**的硬體近似：softmax、LayerNorm、GELU
- Mixture-of-Experts、LLM inference 的 prefill 與 decode 特性差異
- **系統層級**：NoC、chiplet（UCIe）、scale-out interconnect、HBM
- **軟體層**：MLIR、TVM、Triton、PyTorch profiling

### (6) 程式與工具
- Python（NumPy、PyTorch、profiler）
- C++（HLS、模擬器）
- **Tcl**（EDA 工具腳本）
- Bash、Makefile、Git、Linux
- 基本的資料視覺化（matplotlib）：論文圖表品質很重要

---

## 8.2 免費的線上課程

| 課程 | 學校 | 內容 |
|---|---|---|
| **Hardware Architecture for Deep Learning** (6.5930/6.5931) | MIT（Sze、Emer） | 加速器 dataflow、Timeloop，**最推薦** |
| **ECE 5545 ML Hardware and Systems** | Cornell（Abdelfattah） | ML 硬體與系統，教材公開 |
| **CS259** | UCLA（Nowatzki） | 從計算機結構的角度看 ML 的 HW/SW co-design |
| **CS217 Hardware Accelerators for ML** | Stanford | ML 加速器 |
| **EECS 151/251A** | UC Berkeley | 數位設計與積體電路（含 ASIC 實驗） |
| **CS152/252A** | UC Berkeley | 計算機結構 |
| **EE290 Hardware for ML** | UC Berkeley（Shao） | ML 加速器 |
| **18-447** | CMU | 計算機結構（Onur Mutlu 的課在 YouTube 上有完整錄影） |
| **18-643 Reconfigurable Logic** | CMU（Hoe） | FPGA |
| **ECE 5745 Complex Digital ASIC Design** | Cornell（Batten） | ASIC 設計流程 |
| Onur Mutlu 的 Computer Architecture 課程 | ETH Zürich | YouTube 上有完整錄影，內容深入 |

> 課程編號與開放狀態會變動，以搜尋到的最新課程網站為準。

---

## 8.3 書單

| 書 | 用途 |
|---|---|
| *Computer Architecture: A Quantitative Approach*（Hennessy & Patterson） | 計算機結構聖經 |
| *Digital Design and Computer Architecture*（Harris & Harris） | 數位設計基礎 |
| *CMOS VLSI Design*（Weste & Harris） | VLSI 設計 |
| ***Efficient Processing of Deep Neural Networks***（Sze, Chen, Yang, Emer） | **AI 加速器必讀** |
| *SystemVerilog for Verification*（Spear & Tumbush） | 驗證 |
| Clifford Cummings 的論文（Sunburst Design） | CDC、非同步 FIFO、nonblocking assignment 的經典 |
| *Writing for Computer Science*（Zobel） | 學術寫作 |

---

## 8.4 研究框架與工具（值得熟悉）

| 工具 | 用途 | 和你的關聯 |
|---|---|---|
| **Timeloop／Accelergy** | 加速器 mapping 與能耗建模 | 為你的設計做 ASIC 層級的能耗推估 |
| **Chipyard + Gemmini** | 可生成的 RISC-V SoC 與 systolic array | 業界與學界公認的研究平台 |
| **SCALE-Sim** | Systolic array 模擬器 | 快速做 design space exploration |
| **ASTRA-sim** | 分散式 ML 系統模擬 | 做多晶片 scale-out 研究時會用到 |
| **Allo** | Python／MLIR 加速器設計語言 | 從 HLS 往前走的下一步 |
| **ScaleHLS** | PyTorch 到 FPGA 的 HLS 編譯器 | 延續你的 FPGA 工作 |
| **gem5** | 通用的架構模擬器 | 做 CPU／系統層級研究時會用到 |
| **OpenROAD／OpenLane** | 開源 ASIC flow | 沒有商用工具時的替代方案 |
| **Verilator + cocotb** | 快速模擬與 Python 驗證 | 驗證能力的展示 |

---

## 8.5 出國前的具體專案

每個專案都要能放上履歷和 GitHub，並且能在面試時講 5 分鐘。
**⚠️ P2、P3 需要學校的 EDA 工具，一定要在 2027/06 畢業前完成。**

| # | 專案 | 時間 | 產出 | 對求職的價值 |
|---|---|---|---|---|
| P1 | **FPGA 加速器**（你的主要研究）：加上強 baseline 與完整評估 | 持續 | 論文、面試主題 | 「講一個你做過最複雜的設計」 |
| P2 | **核心運算單元的 ASIC implementation**：synthesis + APR → PPA | 3–4 個月 | 履歷上的 ASIC 經驗 | **RTL／PD 職位一定會問** |
| P3 | **可參數化的 systolic array + 完整驗證**（SVA／cocotb + coverage，進階可以加上 UVM） | 1–2 個月 | GitHub 作品 | **DV 職位的敲門磚**；RTL 面試的好話題 |
| P4 | GPU profiling：OpenFold／Boltz／ESMFold 在不同序列長度下的效能分析 | 2–4 週 | 論文的 motivation、技術文章 | 展現效能分析能力 |
| P5（選做） | 用 Timeloop 替你的 dataflow 做能耗建模 | 1 個月 | 和 ASIC 數字交叉驗證 | 架構類職位加分 |

---

## 8.6 業界面試準備（MS 的核心）

### (1) 美國硬體公司的面試流程
```
投遞履歷（career fair / Handshake / 官網 / 內推）
   ↓
Recruiter 電話（15–30 分鐘：背景、身分、時程）
   ↓
技術電話面試 1–2 輪（45–60 分鐘：RTL、數位邏輯、你的專案）
   ↓
Onsite／virtual onsite（4–6 輪，每輪 45–60 分鐘：技術 + behavioral）
   ↓
Offer
```
- **內推的效果遠大於海投**：台灣同學會、學長姐、LinkedIn 上的校友都是資源
- **身分問題**：申請表上常問「是否需要簽證贊助」，要誠實回答。大部分大型晶片公司會贊助，部分新創和國防相關公司不會

### (2) 依職位準備的重點

| 職位 | 必考 | 加分 |
|---|---|---|
| **RTL Design** | 手寫 RTL（FIFO、arbiter、FSM）、CDC、pipelining、STA、低功耗 | 計算機結構、AI 加速器 dataflow |
| **Design Verification** | SystemVerilog OOP、constrained random、SVA、**UVM**、coverage | Formal、Python 自動化 |
| **Physical Design** | Floorplan、placement、CTS、routing、STA（setup／hold 修正）、IR drop | Tcl 腳本、EDA 工具的實際經驗 |
| **Architecture／Performance** | Roofline、cache、記憶體階層、performance model | 你的研究（這類職位最看重） |
| **ML Compiler／Co-design** | PyTorch、C++、MLIR／TVM 概念、kernel 最佳化 | 你的 co-design 經驗 |

### (3) RTL 面試常見題型
- **手寫 RTL**：同步 FIFO、非同步 FIFO、round-robin arbiter、edge detector、除頻器、序列偵測 FSM
- **CDC**：怎麼安全地把單一 bit 或多 bit 訊號傳到另一個 clock domain？
- **STA**：計算 setup／hold slack，說明怎麼修 violation
- **架構**：設計一個 X TOPS、Y GB/s 頻寬的矩陣乘法單元 → 計算 roofline、決定 SRAM 大小
- **AI 加速器**：比較不同 dataflow；量化對面積與功耗的影響；attention 在硬體上的瓶頸
- **數位邏輯基礎**：K-map、mux 實作任意邏輯、latch vs flip-flop、metastability

### (4) 練習資源
- **HDLBits**：Verilog 線上練習題
- **Verification Academy**（Siemens）：UVM／SVA 教學
- 面試心得：一畝三分地、Glassdoor、PTT 相關版、Reddit r/chipdesign
- **自己練習**：8.1 的每個主題都要能**用英文**在白板上講 5 分鐘（英文面試技巧見 [04 的 4.7 節](04-english.md#47-求職面試的英文ms-的主戰場)）

### (5) 準備時程
| 時間 | 目標 |
|---|---|
| 出國前 6 個月 | 每週 2–3 題 RTL 手寫；把 8.1 的基礎主題複習一輪 |
| 出國前 3 個月 | 模擬面試（找在美國業界的學長姐）；履歷定稿；LinkedIn 完成 |
| 入學第 1 個月 | Career fair；大量投遞；請內推 |
| 入學第 1–3 個月 | 面試高峰，每場面試後記錄題目並檢討 |
