# 第 4 章　工具原理：為何 C++ 可以變成電路？

> **本章重點**
> - FPGA 是一塊「**可以重新接線的晶片**」：裡面有大量可設定的小元件（LUT、FF、DSP、BRAM），靠一份設定檔（bitstream）決定它們怎麼連接。
> - **把 C++ 變成電路的是 AMD 的 Vitis HLS**，不是 Claude。它把程式拆成運算、排進時脈週期、對應到硬體元件，最後輸出 Verilog。
> - C++ 可以先模擬，是因為 **C++ 程式本身就是功能規格**；HLS 保證產生的電路和程式算出一樣的結果。
> - 整條工具鏈：**g++（驗證）→ Vitis HLS（C++ → RTL）→ Vivado（RTL → bitstream）→ v++（接上 platform）→ XRT（host 控制板子）**。
> - 最後一節清楚劃分：哪些是下載／安裝的工具、哪些是 Claude 寫的、Claude 在這個對話中實際執行了什麼。

---

## 4.1 FPGA 是什麼？

### 白話直覺
- **CPU** 像一位「什麼都會做的通才」：硬體固定，靠執行不同的指令完成不同工作。
- **GPU** 像「一大群做同樣動作的工人」：硬體固定，擅長大量重複的計算。
- **ASIC**（例如 LightNobel 設計的加速器）像「為一道菜專門打造的生產線」：最快、最省電，但做好就不能改，而且製造非常貴。
- **FPGA** 像「**一大箱樂高**」：可以依需求組成任何生產線，組錯了拆掉重來。速度介於 CPU/GPU 和 ASIC 之間。

### FPGA 裡面有什麼
```
┌────────────────────── FPGA 晶片 ──────────────────────┐
│  ┌───┐ ┌───┐ ┌───┐ ┌─────┐ ┌───┐ ┌───┐ ┌──────┐       │
│  │LUT│ │LUT│ │ FF│ │ DSP │ │LUT│ │ FF│ │ BRAM │ ...   │
│  └─┬─┘ └─┬─┘ └─┬─┘ └──┬──┘ └─┬─┘ └─┬─┘ └──┬───┘       │
│ ═══╪═════╪═════╪══════╪══════╪═════╪══════╪═══  ← 可程式化的繞線 │
│  ┌─┴─┐ ┌─┴─┐ ┌─┴─┐ ┌──┴──┐ ┌─┴─┐ ┌─┴─┐ ┌──┴───┐       │
│  │LUT│ │ FF│ │LUT│ │ DSP │ │ FF│ │LUT│ │ URAM │ ...   │
│  └───┘ └───┘ └───┘ └─────┘ └───┘ └───┘ └──────┘       │
└───────────────────────────────────────────────────────┘
```

| 元件 | 是什麼 | 白話 | U55C 的數量 |
|---|---|---|---|
| **LUT**（Look-Up Table） | 一個 6 輸入的小真值表，可以實現任何 6 個輸入的邏輯函數 | 可以變成任何小邏輯閘組合 | 約 130 萬 |
| **FF**（Flip-Flop） | 1 bit 的記憶元件，每個時脈更新一次 | 暫存器，用來「記住上一步的結果」 | 約 260 萬 |
| **DSP**（DSP48E2） | 一個 27×18 bit 的硬體乘法器＋累加器 | 專門做乘法的小計算機 | 9,024 |
| **BRAM** | 36 Kb 的小記憶體（可拆成兩塊 18 Kb），有 2 個讀寫埠 | 料理台 | 2,016（36 Kb） |
| **URAM** | 288 Kb 的較大記憶體 | 大料理台 | 960 |
| **繞線（routing）** | 可程式化的連線網路 | 決定誰接到誰 | — |

### LUT 為什麼能變成「任何邏輯」
LUT 本質上是一塊 64 格的小記憶體（2⁶ = 64）。6 個輸入當作「地址」，存在裡面的 0/1 就是輸出。
```
例：想做「3 個輸入的多數決」（兩個以上是 1 就輸出 1）
  輸入 abc：000 001 010 011 100 101 110 111
  輸出    ：  0   0   0   1   0   1   1   1     ← 把這 8 個 bit 寫進 LUT 就完成了
```
**改寫 LUT 裡的內容，就改變了電路的功能。** 這就是「可程式化」的本質。

### Bitstream
**Bitstream** 是一個檔案，裡面記錄了：每個 LUT 要存什麼、每條繞線要不要接通、每個 DSP 和 BRAM 怎麼設定。
把 bitstream 寫進 FPGA，它就變成我們設計的電路。在 Vitis 流程中，bitstream 被包在 **`.xclbin`** 檔案裡。

### 一個浮點乘法在 FPGA 上長什麼樣子
```
  float x, y  ──►  [ 拆出正負號、指數、尾數（LUT） ]
                           │
                           ▼
                  [ 尾數相乘（約 2～3 個 DSP） ]
                           │
                           ▼
                  [ 指數相加、正規化、捨入（LUT + FF） ]
                           │
                           ▼
                        x × y
  為了跑到 300 MHz，中間會插入好幾級 FF，所以一個浮點乘法需要好幾個 cycle 才出結果。
```
v2 的 16 路平行，就是**真的放了 16 組這樣的硬體**。

---

## 4.2 為什麼 FPGA 適合做記憶體優化的實驗？

| 特性 | CPU / GPU | FPGA |
|---|---|---|
| 記憶體階層 | 固定（cache 由硬體自動管理） | **自己設計**（要多少 buffer、放在哪、怎麼切都可以決定） |
| 資料怎麼搬 | 由硬體和驅動程式決定 | **自己決定**（位元寬度、burst 長度、哪個通道） |
| 運算單元數量 | 固定 | **自己決定**（16 路、64 路……） |
| 能看到多少細節 | 很多被隱藏 | 報告直接列出每個迴圈、每種資源 |

**這讓我們能「一次只改一件事」，清楚量出每一招的效果。**

---

## 4.3 HLS：C++ 是怎麼變成電路的？

**HLS（High-Level Synthesis，高階合成）**：把 C/C++ 自動翻譯成硬體描述語言（Verilog/VHDL）。
本專題用的是 AMD 的 **Vitis HLS**（2025.2 以 `vitis-run --mode hls` 執行）。

### 整體流程
```
 trimul_v2.cpp
      │
      ▼
 ① 前端解析（clang/LLVM）      把 C++ 轉成中間表示（IR），做一般編譯器最佳化
      │                        （日誌中：「C-Synthesis will use clang-16 as the compiler」）
      ▼
 ② 依 pragma 轉換               展開迴圈、切分陣列、內聯函式……
      │
      ▼
 ③ 排程（Scheduling）           決定每個運算在「第幾個 cycle」執行
      │
      ▼
 ④ 配置與綁定                   決定用幾個乘法器、加法器，每個運算用哪一個
   （Allocation & Binding）
      │
      ▼
 ⑤ 產生 RTL                    狀態機（控制）＋資料路徑（運算）＋介面（AXI）
      │
      ▼
 Verilog / VHDL ＋ 報告（csynth.rpt、csynth.xml）
```

### ① 前端解析：把程式拆成「運算的圖」
例：`acc += a * b;`
```
   a ──┐
       ├──► [乘法] ──┐
   b ──┘             ├──► [加法] ──► acc（下一輪）
   acc（上一輪）─────┘
```
這張圖叫 **資料流圖（data flow graph）**：節點是運算，箭頭是資料相依。

### ③ 排程：把運算放進時脈週期
每種運算在 300 MHz 下需要的 cycle 數不同（例如浮點乘法、浮點加法都要好幾個 cycle）。
HLS 依照資料相依關係，把每個運算排到某個 cycle：
```
cycle:   1    2    3    4    5    6    7    8    9   10
讀 a、b  ███
乘法          ████████████
加法                         ████████████████
寫 acc                                           ███
```
一次迭代從開始到結束需要的 cycle 數叫 **iteration latency**。

### Pipeline 與 II（Initiation Interval）
**沒有 pipeline：** 一次迭代做完才開始下一次。
```
迭代 0：[讀][乘乘乘][加加加加][寫]
迭代 1：                          [讀][乘乘乘][加加加加][寫]
```
**有 pipeline（II = 1）：** 每個 cycle 都開始一個新的迭代，像工廠的流水線。
```
迭代 0：[讀][乘乘乘][加加加加][寫]
迭代 1：    [讀][乘乘乘][加加加加][寫]
迭代 2：        [讀][乘乘乘][加加加加][寫]
迭代 3：            [讀][乘乘乘][加加加加][寫]
```
**II = 連續兩次迭代開始的間隔。** II = 1 代表每個 cycle 都有一個結果產出，是最理想的狀態。

**例：v2 的 mac 迴圈** 跑 512 次，報告顯示 526 cycles：
```
526 ≈ 512（每 cycle 開始一次，II = 1）+ 14（pipeline 的深度，最後一次迭代要走完）
```

### 為什麼 v0 無法達到 II = 1
v0 的 `acc += a * b`：下一次的加法**需要這一次加完的結果**。
```
迭代 0：        [加加加加]
迭代 1：                  [加加加加]   ← 要等迭代 0 加完才能開始
```
假設浮點加法需要 4 個 cycle，II 至少是 4。這叫 **loop-carried dependency**（跨迭代的相依）。
v1～v4 把迴圈順序換掉，讓相鄰的迭代更新**不同的** `acc` 位置，就沒有這個問題（再用 `DEPENDENCE` pragma 告訴 HLS）。

### ④ 配置與綁定：用幾個硬體？
- 一個 pipeline 迴圈裡如果每個 cycle 都要做 16 次乘法，就需要 **16 個乘法器**。
- 如果迴圈沒有 pipeline，HLS 可能讓多個運算**共用**同一個乘法器（省資源，但變慢）。
- **記憶體的限制**：一塊 BRAM 只有 2 個讀寫埠，一個 cycle 最多讀寫 2 次。
  v2 每個 cycle 要讀 16 個 `la`，所以必須用 `ARRAY_PARTITION` 把陣列**切成 16 塊**，每塊各自讀。

### ⑤ 產生 RTL：電路長什麼樣子
```
                  ┌──────────────────────────────────────┐
  AXI4-Lite ────► │ 控制暫存器：start / done / L / 位址    │ ◄── host 從這裡設定參數、啟動
                  ├──────────────────────────────────────┤
                  │ 狀態機（FSM）：現在在跑哪個迴圈        │
                  ├──────────────────────────────────────┤
  AXI4 (m_axi) ◄─►│ 資料路徑：load → mac（16 個乘加器） → store │ ◄─► HBM
                  │ BRAM：acc、la、lb                     │
                  └──────────────────────────────────────┘
```
- `#pragma HLS INTERFACE m_axi` → 產生 **AXI4 master** 介面，kernel 可以主動去 HBM 讀寫。
- 在 Vitis 流程中，純量參數（例如 `L`）和指標的位址會自動經由 **AXI4-Lite** 控制暫存器傳入。

### 本專題用到的 pragma 一覽
| Pragma | 作用 | 在哪裡用 | 不加會怎樣 |
|---|---|---|---|
| `PIPELINE II=1` | 迴圈做成流水線，每 cycle 開始一次迭代 | 幾乎所有內層迴圈 | 迭代一個接一個做，慢很多倍 |
| `ARRAY_PARTITION dim=2 complete` | 把陣列的某一維拆成獨立的記憶體 | v2～v4 的 acc、la、lb | 一個 cycle 只能讀 2 個數，16 路平行做不到 |
| `DEPENDENCE variable=acc inter false` | 告訴 HLS 跨迭代沒有相依 | v1～v4 的 mac | HLS 保守地拉高 II |
| `INTERFACE m_axi port=a bundle=gmem0` | a 走獨立的 AXI 連接埠 | 所有 kernel | 多個指標可能共用同一個埠，互相搶頻寬 |
| `INLINE off` | 函式保留成獨立模組 | v3 的 load_ab、mac | 被併進主函式，可能無法平行執行 |
| `LOOP_TRIPCOUNT` | 告訴 HLS 迴圈大概跑幾次 | 以 L 為上限的迴圈 | 報告中的 latency 顯示為「?」 |

### 可合成的 C++ 有什麼限制
HLS 只能處理「**能對應到固定硬體**」的 C++：
| 不能用 | 原因 |
|---|---|
| `new` / `malloc`（動態記憶體） | 硬體的記憶體大小必須在合成時決定 |
| 遞迴 | 無法事先知道要幾層硬體 |
| 系統呼叫（檔案、`printf` 等） | 硬體沒有作業系統 |
| 大小不固定的陣列 | 同動態記憶體 |

所以 kernel 裡的陣列大小都寫成常數（`TI`、`TJ`、`C`），而讀檔、印結果都放在 testbench 或 host。

---

## 4.4 為什麼 C++ 可以直接模擬？

### 核心觀念：C++ 程式就是「功能規格」
HLS 的承諾是：**產生的電路，對同樣的輸入，會算出和 C++ 程式一樣的結果**（在可合成的範圍內）。
所以：
1. 用一般編譯器（g++）執行 C++ → 得到「應該要算出來的答案」。
2. 如果這個答案是對的，那 HLS 產生的電路**在功能上**也是對的。

`#pragma HLS` 只影響**硬體怎麼實作**（多快、用多少資源），不影響**算出什麼**。
g++ 不認識這些 pragma，直接忽略，所以可以照常編譯執行。

### 四種模擬，一層比一層接近真實
| 模擬 | 在跑什麼 | 驗證什麼 | 速度 | 本專題 |
|---|---|---|---|---|
| **C 模擬（csim）** | C++ 程式本身（g++ 或 HLS 內建的 clang） | 演算法對不對 | 秒 | ✅ `make csim` |
| **C/RTL 協同模擬（cosim）** | HLS 產生的 Verilog，用 RTL 模擬器（Vivado 的 xsim）執行，testbench 仍是 C++ | 產生的電路和 C++ 結果一致嗎？時序正確嗎？ | 分鐘～小時 | 可選（`COSIM=1`） |
| **軟體模擬（sw_emu）** | kernel 編成一般程式，搭配 XRT 模擬 | host 和 kernel 的介面對不對 | 快 | 需要 XRT |
| **硬體模擬（hw_emu）** | kernel 的 RTL ＋ platform 的模型＋ XRT | 整個系統（含記憶體介面）的行為 | 慢 | 需要 XRT |

### 為什麼 C 模擬通過不代表一定沒問題
- C++ 沒有「時間」的概念，無法抓到時序相關的錯誤（例如 `DEPENDENCE` 宣告錯誤導致讀到舊值）。
- 所以正式流程中，cosim 或 hw_emu 是重要的第二道防線。

---

## 4.5 Vivado：從 RTL 到 bitstream

HLS 產生的是 Verilog（描述電路的程式碼），還不是 FPGA 能直接用的檔案。
接下來由 **Vivado** 完成（在 Vitis 流程中由 `v++ -l` 自動呼叫）：

| 步驟 | 做什麼 | 比喻 |
|---|---|---|
| **Synthesis（邏輯合成）** | 把 Verilog 轉成 LUT、FF、DSP、BRAM 組成的網表（netlist） | 把設計圖拆成樂高零件清單 |
| **Optimization** | 刪除多餘的邏輯、合併重複的部分 | 省掉不需要的零件 |
| **Placement（擺放）** | 決定每個零件放在晶片的哪個位置 | 決定每塊樂高放哪 |
| **Routing（繞線）** | 決定零件之間的連線走哪條路 | 接電線 |
| **Timing analysis** | 檢查最慢的路徑能不能在一個 cycle 內跑完 | 確認流水線每一站都來得及 |
| **Bitstream generation** | 把以上結果寫成設定檔 | 產出組裝說明書 |

**為什麼要跑 1～數小時？** 擺放和繞線要在數十萬到數百萬個元件中找出好的配置，這是非常難的最佳化問題，
工具只能用啟發式方法反覆嘗試。

**Timing 沒過會怎樣？** 電路在目標時脈下可能算錯，工具會自動降低時脈，或需要修改設計。
HLS 報告中的 `Estimated 2.431 ns` 只是估計，實際值要等 Vivado 繞線完才知道。

---

## 4.6 Vitis 與 `v++`：把 kernel 接到板子上

### Platform（平台）是什麼
FPGA 卡上除了我們的 kernel，還需要很多「基礎設施」：PCIe 介面（和主機溝通）、DMA（搬資料）、
HBM 控制器、時脈產生、卡片管理。這些由 AMD 預先做好，叫做 **platform** 或 **shell**。

```
┌───────────────────── U55C 上的 FPGA ─────────────────────┐
│ ┌──────────── Static region（platform / shell）─────────┐ │
│ │  PCIe ── DMA ── 時脈 ── 管理 ── HBM 控制器（32 個 PC） │ │
│ └─────────────────────────┬─────────────────────────────┘ │
│ ┌──────────── Dynamic region（我們的設計）───────────────┐ │
│ │    AXI interconnect ── trimul_v2（我們的 kernel）        │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```
比喻：platform 像電腦的主機板＋作業系統，kernel 像我們安裝的應用程式。
**編譯時指定的 platform 必須和卡上實際燒錄的 shell 一致**，這就是為什麼 `PLATFORM=` 很重要。

### `v++` 的兩個階段
```
v++ -c（compile）：trimul_v2.cpp ──(內部呼叫 HLS)──► trimul_v2.xo
                   .xo = RTL ＋ kernel 的描述（有哪些參數、哪些 AXI 埠）

v++ -l（link）：    trimul_v2.xo ＋ platform ＋ cfg ──(內部呼叫 Vivado)──► trimul_v2.xclbin
                   把 kernel 放進 dynamic region、依 cfg 接到 HBM、擺放繞線、產生 bitstream
```

### `.xclbin` 裡有什麼
- Bitstream（dynamic region 的電路）
- Metadata：kernel 名稱、每個參數的位置、每個 AXI 埠接到哪幾個 HBM PC（memory topology）
  → host 程式中的 `krnl.group_id(0)` 就是從這裡查到「參數 0 接在哪塊記憶體」。

---

## 4.7 XRT：host 程式怎麼控制 FPGA

**XRT（Xilinx Runtime）** 是 AMD 提供的軟體：Linux 驅動程式＋使用者層的函式庫＋管理工具（`xbutil`）。

| host 程式的動作 | XRT 實際做的事 |
|---|---|
| `xrt::device dev(0)` | 透過驅動程式打開第 0 張卡 |
| `dev.load_xclbin(...)` | 把 bitstream 寫進 FPGA 的 dynamic region，讀取 metadata |
| `xrt::bo bo(dev, size, group)` | 在指定的 HBM 區域配置一塊記憶體（buffer object） |
| `bo.sync(TO_DEVICE)` | 透過 PCIe DMA 把資料從主機記憶體複製到 HBM |
| `run.set_arg(...)` | 把參數（HBM 位址、L）寫進 kernel 的 AXI4-Lite 控制暫存器 |
| `run.start()` | 寫入 start 位元，kernel 開始執行 |
| `run.wait()` | 等待 kernel 的 done 訊號 |
| `bo.sync(FROM_DEVICE)` | 把結果從 HBM 複製回主機 |

**本專題的狀況：** 你們的 server63 **沒有安裝 XRT、也沒有插卡**，所以這部分要在有 U55C 的機器上執行。

---

## 4.8 Python 端：PyTorch、HuggingFace、ESMFold

| 元件 | 誰做的 | 做什麼 | 怎麼取得 |
|---|---|---|---|
| **PyTorch** | Meta 主導的開源專案 | 張量運算、神經網路框架 | `pip install torch` |
| **transformers** | HuggingFace 開源專案 | 各種預訓練模型的程式碼，包含 `EsmForProteinFolding` | `pip install transformers` |
| **ESMFold 權重**（`facebook/esmfold_v1`） | Meta AI 訓練、發布在 HuggingFace Hub | 模型學到的參數（約 8 GB） | 第一次執行時自動下載 |
| **蛋白質序列** | UniProt、RCSB PDB（公開資料庫） | 輸入資料 | 腳本自動從網路下載 |

`dump_trimul_inputs.py` 的做法是「**攔截**」：把 ESMFold 裡某個函式換成我們自己的版本，
當模型執行到那裡時把資料存下來。模型本身完全沒有修改。

---

## 4.9 誰提供了什麼能力？

這是你特別問的問題，這裡清楚劃分。

### 工具鏈：都是現成的軟體，不是 Claude 做的
| 能力 | 提供者 | 在哪裡 | 怎麼來的 |
|---|---|---|---|
| **C++ → 電路（HLS）** | **AMD Vitis HLS** | 你們的 server（`/tools/Xilinx/2025.2/`） | 實驗室／TSRI 安裝的商用軟體（需要授權，`/tools/Xilinx/flexlm` 是授權管理） |
| RTL → bitstream | AMD Vivado | 同上 | 同上 |
| 把 kernel 接上 platform | AMD Vitis（`v++`） | 同上 | 同上 |
| RTL 模擬（cosim） | AMD Vivado 模擬器（xsim） | 同上 | 同上 |
| 控制板子 | AMD XRT | 需要安裝在有卡的機器上 | AMD 開源（GitHub 上可取得） |
| U55C platform | AMD | 需要安裝在有卡的機器上 | AMD 官網下載 |
| C 模擬 | GCC（g++） | 任何 Linux | 開源 |
| 流程自動化 | GNU Make | 任何 Linux | 開源 |
| 蛋白質模型 | Meta ESMFold ＋ HuggingFace transformers ＋ PyTorch | 需要時用 pip 安裝、自動下載權重 | 開源／公開 |

### Claude 做的事
| Claude 做了 | Claude 沒有做 |
|---|---|
| 寫所有的**原始碼**：5 個 kernel、testbench、host、Makefile、HLS 腳本、cfg、Python 腳本、整理報告的腳本 | **沒有**把 C++ 轉成電路（那是 Vitis HLS 做的，在你們的 server 上執行） |
| 寫所有的**文件**（包含這份手冊） | **沒有**執行過 Vitis／Vivado（Claude 的環境裡沒有安裝） |
| 設計實驗（5 個版本、要比較什麼） | **沒有**連到你們的 server（所有 server 上的指令都是你執行、再截圖給 Claude） |
| 在自己的雲端環境中**驗證**：g++ C 模擬、Python 小模型測試、假 XRT header 編譯檢查 | **沒有**使用什麼特別下載的模型或外掛來產生程式碼 |
| 根據你的截圖**推理錯誤原因並修正**（例如 2025.2 路徑 bug） | |

### Claude 的知識從哪裡來
Claude 是一個大型語言模型，在訓練時讀過大量公開資料，包括 AMD 的官方文件、HLS 的教科書與範例、
開源程式碼、學術論文等。寫程式時使用的是這些**學到的知識**，不是即時查詢某個資料庫。

**這也意味著 Claude 可能出錯：** 例如一開始不知道 2025.2 已經移除 `vitis_hls`、也不知道路徑 bug，
是看到你的截圖後才修正。所以每一步都需要在真實工具上驗證，這也是為什麼流程要「從快到慢」一步步確認。

---

## 4.10 Claude 在這個對話中呼叫的工具

Claude 在一個**與你的 server 完全隔離的雲端 Linux 容器**裡工作。以下是實際用過的工具：

| 工具 | 做了什麼 | 例子 |
|---|---|---|
| **Bash**（在雲端容器中執行指令） | 編譯、執行、測試、git 操作 | `g++ ... tb.cpp` 跑 C 模擬；`git commit`、`git push`；`pip install torch transformers` |
| **Write / Edit / Read**（檔案操作） | 建立與修改檔案 | 寫 `trimul_v2.cpp`、修改 `run_hls.tcl` |
| **GitHub 工具** | 讀取 PR 的狀態 | 檢查 PR #1 有沒有 CI 失敗或審查留言 |
| **排程提醒（send_later）** | 定時提醒自己回來檢查 | 每小時檢查 PR、每 10 分鐘檢查手冊進度 |
| **傳送檔案（SendUserFile）** | 把檔案傳給你 | 傳送 `ForClaude.zip` |

### 容器裡驗證了什麼、沒驗證什麼
| 驗證項目 | 方法 | 結果 |
|---|---|---|
| 5 個 kernel 的功能 | g++ C 模擬（L = 16、32、48、64；多種 tile 大小） | ✅ 全部通過 |
| host 程式能否編譯 | 自己寫一組「假的」XRT header，只檢查語法 | ✅ 可編譯（**未實際執行**） |
| Python 擷取腳本 | 隨機初始化的小型 ESMFold（無法下載正式權重，容器的網路政策擋掉了 HuggingFace） | ✅ 流程正確、算式差值 0 |
| 報告整理腳本 | 自己產生格式相同的假報告 | ✅ 可解析 |
| HLS 合成 | **無法**（容器沒有 Vitis） | 由你在 server63 上執行 |
| 上板 | **無法** | 尚待找到有 U55C 的機器 |

### 安全性
- Claude 的容器**無法存取你的 server**，你的 server 也不會連到 Claude 的容器。
- 雙方唯一的交集是 **GitHub repo**：Claude 推上去，你用 `git clone`／`git pull` 下載。
- 你的 server 只有「**下載**」程式碼，沒有上傳任何東西。

---

## 本章小結

```
          ┌── 你寫的（或 Claude 寫的）C++ ──┐
          │                                 │
          ▼                                 ▼
    g++ 編譯執行                     Vitis HLS（AMD）
    = C 模擬（功能對不對）           = C++ → Verilog（電路）
                                           │
                                           ▼
                                    Vivado（AMD）
                                    = Verilog → bitstream（擺放、繞線）
                                           │
                                           ▼
                                    v++ link（AMD）
                                    = kernel ＋ platform ＋ HBM 設定 → .xclbin
                                           │
                                           ▼
                                    XRT（AMD）＋ host 程式
                                    = 燒進 FPGA、搬資料、啟動、取回結果
```
- **把 C++ 變成電路的能力來自 AMD 的 Vitis HLS**；Claude 負責寫出「適合被轉成好電路」的 C++，以及整個實驗的設計與文件。
- C++ 能先模擬，是因為 HLS 保證電路與 C++ 的功能一致；pragma 只影響實作方式。
- 每一層工具都有對應的驗證方式，**越後面的步驟越慢，所以要先把前面的驗證做好**。

**下一章**整理成可以重複使用的研究方法，讓你之後讀其他 paper 時也能照這個流程進行。
