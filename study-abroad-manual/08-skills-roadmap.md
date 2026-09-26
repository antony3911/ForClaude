# 08. 技術能力路線圖

> 目標：從「FPGA 加速器研究者」變成「懂 ASIC、也懂架構的 AI 加速器設計者」。
> 這些能力同時服務三件事：**你的研究、申請時的說服力，以及之後的實習與求職面試。**

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

## 8.5 未來 12 個月的具體專案

以你的研究為主軸，每個專案都要能放上 CV、GitHub 和 SOP：

| # | 專案 | 時間 | 產出 |
|---|---|---|---|
| P1 | **GPU profiling 研究**：OpenFold／Boltz／ESMFold 在不同 L 下的時間、記憶體與 roofline 分析 | 2–4 週 | 論文 motivation 的圖表、blog 文章 |
| P2 | **FPGA 加速器**（你的主要研究）：加上強 baseline 與完整評估 | 持續 | 論文 |
| P3 | **核心運算單元的 ASIC implementation**：synthesis + APR → PPA | 3–4 個月 | CV 上的 ASIC 經驗、論文中的 ASIC 推估 |
| P4 | **開源 repo**：可重現的腳本、清楚的 README | 與 P2 並行 | GitHub 作品集 |
| P5（選做） | **可參數化的 systolic array + 完整驗證**（SVA／cocotb + coverage） | 1–2 個月 | 驗證能力展示，面試時的好話題 |
| P6（選做） | 用 Timeloop 替你的 dataflow 做能耗建模 | 1 個月 | 和 ASIC 數字交叉驗證 |

---

## 8.6 業界面試準備（實習或 MS 求職）

### RTL 面試常見題型
- **手寫 RTL**：同步 FIFO、非同步 FIFO、round-robin arbiter、edge detector、除頻器、序列偵測 FSM
- **CDC**：怎麼安全地把單一 bit 或多 bit 訊號傳到另一個 clock domain？
- **STA**：計算 setup／hold slack、如何修 violation
- **架構**：設計一個 X TOPS、Y GB/s 頻寬的矩陣乘法單元 → 計算 roofline、決定 SRAM 大小
- **AI 加速器**：比較不同 dataflow；量化對面積與功耗的影響；attention 在硬體上的瓶頸

### 練習資源
- **HDLBits**：Verilog 線上練習題
- **Verification Academy**（Siemens）：UVM／SVA 教學
- 各大公司的面試心得：一畝三分地、Glassdoor、PTT 相關版、Reddit r/chipdesign
- 自己練習：把 8.1 的每個主題都能**用英文**在白板上講 5 分鐘

### PhD 研究實習
- NVIDIA Research、Google（TPU／DeepMind 硬體）、Meta、Microsoft Research、AMD Research、Intel Labs、IBM Research 等
- 多半透過**指導教授人脈、研討會認識的研究員**、或者你的論文被注意到
- **2026/08 的 CPT 新指引可能影響實習**：入學後先向國際學生辦公室確認
