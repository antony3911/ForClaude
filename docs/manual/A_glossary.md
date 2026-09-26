# 附錄 A　術語表

> 依主題分類。每個詞附上：**白話解釋**、**正式說明**、**在本專題哪裡出現**。
> 忘記某個詞的意思時，回來這裡查。

---

## A.1 蛋白質與模型

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **胺基酸（amino acid）** | 珠鍊上的一顆珠子 | 蛋白質的基本單位，共 20 種，用一個英文字母表示 | 序列中的每個字母 |
| **序列長度 L** | 珠子的數量 | 蛋白質中胺基酸的個數 | 整份手冊的核心變數 |
| **PPM** | 蛋白質結構預測模型 | Protein structure Prediction Model，例如 AlphaFold2、ESMFold | LightNobel 的研究對象 |
| **AlphaFold2** | DeepMind 的蛋白質結構預測模型 | 2021 年發表，使用 MSA 與 Evoformer | 第 1 章 |
| **ESMFold** | Meta 的蛋白質結構預測模型 | 用 ESM-2 語言模型代替 MSA，結構較簡單 | 我們驗證算式的對象 |
| **ESM-2** | 蛋白質的「語言模型」 | 像讀文字一樣讀胺基酸序列，產生特徵 | ESMFold 的第一部分 |
| **MSA** | 多序列比對 | Multiple Sequence Alignment，把相似的蛋白質序列排在一起 | AlphaFold2 的輸入，ESMFold 不需要 |
| **Evoformer / Folding trunk** | 模型的主體 | 由 48 個 block 組成，反覆更新兩種 representation | 第 1 章 1.2 節 |
| **Structure module** | 輸出座標的部分 | 把特徵轉成 3D 原子座標 | 第 1 章 1.2 節 |
| **Sequence representation** | 每個胺基酸的特徵 | 形狀 L × 1024（ESMFold） | 第 1 章 |
| **Pair representation** | 每一對胺基酸之間的關係 | 形狀 **L × L × 128**，隨 L² 成長 | **本專題處理的資料** |
| **Triangle Multiplication** | 用「第三者」推論兩者關係 | `z[i][j][c] = Σ_k a[i][k][c]·b[j][k][c]`（outgoing） | **本專題實作的運算** |
| **Outgoing / Incoming** | 兩種三角形方向 | outgoing 用 (i,k)、(j,k)；incoming 用 (k,i)、(k,j) | 我們做 outgoing |
| **Triangle Attention** | 三角形版本的 attention | 中間值隨 L³ 成長，實作上需分塊 | 第 1 章 1.3 節（未實作） |
| **Token** | 一格資料 | 在 pair representation 中指一個 (i, j) 位置的 128 個數字 | per-token 量化的單位 |
| **Channel（C）** | 每格的數字個數 | 特徵維度，ESMFold 的 pair 為 128 | `trimul.h` 的 `C = 128` |
| **LayerNorm / Linear / Gating** | 模型中的標準運算 | 正規化、線性轉換、用 sigmoid 控制資訊流 | 產生 a、b 的步驟（未實作） |
| **Chunking** | 分批計算 | 一次只算一部分以降低記憶體峰值，代價是時間 | 第 2 章 2.9 節 |
| **HuggingFace** | 公開模型的平台 | 提供模型程式碼（transformers）與權重下載（Hub） | `dump_trimul_inputs.py` |
| **UniProt / PDB** | 公開的蛋白質資料庫 | UniProt 存序列、PDB 存實驗測定的結構 | 下載測試序列 |

## A.2 效能與記憶體概念

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **Memory-bound** | 等搬資料 | 效能受限於記憶體頻寬或延遲，而非運算能力 | v0、v2 的載入部分 |
| **Compute-bound** | 廚師忙不過來 | 效能受限於運算單元數量 | v2 的 mac 部分 |
| **Weights（權重）** | 模型學到的參數 | 大小固定，與 L 無關 | 第 1 章 1.4 節 |
| **Activation** | 計算中產生的中間資料 | 隨輸入大小（L）成長 | LightNobel 要壓縮的對象 |
| **OOM** | 記憶體不夠 | Out of Memory | 長序列在 GPU 上的問題 |
| **FLOP** | 一次浮點運算 | 一次乘法或一次加法 | 一次乘加 = 2 FLOP |
| **GFLOP/s** | 每秒十億次運算 | 效能單位 | v2 約 7.3 GFLOP/s |
| **頻寬（bandwidth）** | 每秒能搬多少 | GB/s | 單一 512-bit 埠 19.2 GB/s；U55C HBM 約 460 GB/s |
| **延遲（latency）** | 等多久才開始有資料 | 從請求到第一筆資料的時間 | v2 載入的 141 cycles 大多是延遲 |
| **算術強度（AI）** | 每搬 1 byte 做幾次運算 | FLOP ÷ byte | v0 0.25、v2 2、v4 約 7.8 |
| **Roofline 模型** | 判斷瓶頸的圖 | `可達效能 = min(運算上限, AI × 頻寬)` | 第 2 章 2.3 節 |
| **Ridge point（平衡點）** | roofline 的轉折點 | 峰值運算 ÷ 頻寬 | 判斷 memory/compute-bound |
| **Tiling** | 分批搬、重複用 | 把計算切成小塊，讓搬進來的資料被重用多次 | v1 |
| **資料重用（data reuse）** | 同一個食材做多道菜 | 同一份資料被多次運算使用 | tile 中每個 a 用 TJ 次 |
| **Burst** | 一次請求連續拿很多筆 | 只付一次延遲 | 連續的 128 個 channel |
| **Double buffering（ping-pong）** | 兩個料理台輪流用 | 一個 buffer 計算時，另一個載入下一批 | v3 |
| **Little's Law** | 要多少資料在路上 | 在途資料量 = 頻寬 × 延遲 | 第 2 章 2.5 節 |
| **Amdahl's Law** | 改善的上限 | `加速 = 1 ÷ [(1−p) + p/s]` | v3 最多約 1.27 倍 |
| **Memory layout** | 資料在記憶體中的排列 | 決定能否連續讀取 | `[row][col][channel]` |
| **Stride** | 連續兩次存取的間距 | stride 大 → 無法 burst | v0 的 stride = 128 |
| **Operator fusion（融合）** | 運算合併 | 中間值不寫回記憶體 | 2.9 節、**第 6 章 6.4 節（本專題主策略）** |
| **Recomputation（重算）** | 用計算換記憶體 | 不存中間值，需要時重算 | 2.9 節、6.5 節（重算 g） |

## A.3 量化

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **量化（quantization）** | 把數字壓縮成較少的 bit | 例如 FP32（4 bytes）→ INT8（1 byte） | v4 |
| **FP32 / FP16 / BF16** | 浮點格式 | 32 / 16 / 16 bit 的浮點數 | kernel 用 FP32 |
| **INT8** | 8 bit 整數 | -128～127（對稱量化用 -127～127） | v4 |
| **Scale（s）** | 量化的尺 | `s = max|x| ÷ 127`，`x ≈ s × q` | 每個 token 一個 |
| **對稱量化** | 以 0 為中心 | 正負範圍相同，不需要 zero point | v4 的做法 |
| **Per-tensor** | 整份共用一把尺 | 一個 scale 給整個張量 | 誤差約 11% |
| **Per-token** | 每格一把尺 | 每個 token 一個 scale | 誤差約 1% |
| **Per-channel** | 每個 channel 一把尺 | 每個 c 一個 scale（本專題未實作） | 第 4 章 4.4 節提到 |
| **Outlier** | 特別大的值 | 少數數值遠大於其他值 | 模擬資料中 1% 的 token ×30 |
| **Fake quantization** | 量化再還原 | 用浮點數模擬量化誤差 | Python 腳本評估誤差 |
| **rel_l2** | 整體相對誤差 | `‖z − z_ref‖ ÷ ‖z_ref‖` | testbench、host |
| **max_abs** | 最大單點誤差 | `max |z − z_ref|` | testbench、host |
| **AAQ** | LightNobel 的量化方法 | Token-wise Adaptive Activation Quantization | 第 1 章 1.6 節 |

## A.4 FPGA 硬體

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **FPGA** | 可以重新接線的晶片 | Field-Programmable Gate Array | U55C |
| **ASIC** | 專用晶片 | 做好就不能改，最快最省電 | LightNobel 的加速器 |
| **U55C** | 我們的 FPGA 卡 | AMD Alveo U55C，晶片 xcu55c-fsvh2892-2L-e | 整個專題 |
| **Alveo** | AMD 資料中心 FPGA 卡系列 | 插在伺服器的 PCIe 插槽 | U55C 屬於此系列 |
| **LUT** | 小真值表 | 6 輸入，可實現任意邏輯 | 報告的 LUT 用量 |
| **FF（Flip-Flop）** | 1 bit 暫存器 | 每個時脈更新 | 報告的 FF 用量 |
| **DSP** | 硬體乘法器 | DSP48E2，27×18 bit 乘法＋累加 | 浮點乘法用 |
| **BRAM** | 小塊晶片內記憶體 | 36 Kb（可拆成兩個 18 Kb），2 個讀寫埠 | acc、la、lb |
| **URAM** | 大塊晶片內記憶體 | 288 Kb | 大 tile 時可能用到 |
| **HBM** | 高頻寬記憶體 | High Bandwidth Memory，堆疊在晶片旁 | U55C 有 16 GB |
| **Pseudo-channel（PC）** | HBM 的一條通道 | U55C 有 32 個，每個 512 MB | cfg 中的 `HBM[0:7]` |
| **PCIe** | 主機和卡之間的連線 | 資料從 CPU 記憶體搬到 HBM 走這裡 | XRT 的 sync |
| **時脈（clock）** | 電路的節拍 | 300 MHz = 每 3.33 ns 一拍 | `create_clock -period 3.33` |
| **Cycle** | 一拍 | 一個時脈週期 | 報告的 latency 單位 |
| **Bitstream** | FPGA 的設定檔 | 決定每個元件和連線的設定 | 包在 .xclbin 中 |
| **廠商代號 10ee** | Xilinx 的 PCI ID | `lspci -d 10ee:` 可列出 Xilinx 裝置 | 確認 server63 沒有卡 |

## A.5 HLS 與硬體設計

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **HLS** | C++ 轉電路 | High-Level Synthesis | Vitis HLS |
| **RTL** | 電路的描述 | Register Transfer Level，用 Verilog/VHDL 撰寫 | HLS 的輸出 |
| **Verilog / VHDL** | 硬體描述語言 | 描述電路結構與行為 | 我們不需要手寫 |
| **Kernel** | 在 FPGA 上跑的函式 | 加速的核心運算 | `trimul_v0`～`v4` |
| **Pragma** | 給 HLS 的指示 | `#pragma HLS ...`，不影響功能、只影響實作 | 第 3 章 3.3 節 |
| **Pipeline** | 流水線 | 多個迭代重疊執行 | 幾乎所有內層迴圈 |
| **II（Initiation Interval）** | 流水線的節奏 | 連續兩次迭代開始的間隔，1 最好 | mac 迴圈 II = 1 |
| **Iteration latency** | 一次迭代的長度 | 一次迭代從頭到尾的 cycle 數 | loop_k 為 671 |
| **Pipeline depth** | 流水線的長度 | 一次迭代需要走過的級數 | mac 約 14 |
| **Loop-carried dependency** | 下一輪要等這一輪 | 跨迭代的資料相依，會拉高 II | v0 的 acc |
| **Unroll（展開）** | 把迴圈複製成多份硬體 | 平行執行 | v2 的 16 lane |
| **Array partition** | 把陣列拆開 | 讓多個元素能同時存取 | `ARRAY_PARTITION dim=2 complete` |
| **Scheduling（排程）** | 決定何時做 | 把運算分配到 cycle | 第 3 章 3.3 節 |
| **Binding（綁定）** | 決定用誰做 | 把運算分配到硬體單元 | 第 3 章 3.3 節 |
| **FSM** | 狀態機 | 控制電路目前在做哪一步 | HLS 自動產生 |
| **AXI4 / m_axi** | 讀寫記憶體的介面 | kernel 主動讀寫 HBM 的標準介面 | `INTERFACE m_axi` |
| **AXI4-Lite / s_axilite** | 設定參數的介面 | host 寫入參數和 start 訊號 | L、位址 |
| **Bundle** | AXI 埠的名稱 | 相同 bundle 共用一個埠 | gmem0、gmem1、gmem2 |
| **Trip count** | 迴圈次數 | 告訴 HLS 以便估計 latency | `L_TRIP = 256` |
| **Timing（時序）** | 電路能否在一拍內完成 | Estimated 需小於 Target | 2.431 ns < 3.33 ns |
| **Synthesis（合成）** | 把設計轉成元件 | HLS 合成（C++→RTL）或邏輯合成（RTL→netlist） | 兩種都有 |
| **Place & Route** | 擺放與繞線 | 決定元件位置與連線 | Vivado，耗時最久 |
| **Netlist** | 元件清單＋連線 | 邏輯合成的輸出 | Vivado 內部 |

## A.6 AMD 工具鏈

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **Vitis** | AMD 的加速應用開發環境 | 包含 HLS、`v++`、`vitis-run` 等 | 2025.2 |
| **Vitis HLS** | C++ → RTL 工具 | 2024.2 起以 `vitis-run --mode hls` 執行 | `make hls` |
| **Vivado** | RTL → bitstream 工具 | 合成、擺放、繞線、產生 bitstream | `v++ -l` 內部呼叫 |
| **`v++`** | Vitis 的編譯器 | `-c` 產生 .xo；`-l` 產生 .xclbin | `make xclbin` |
| **`vitis-run`** | 執行 Vitis 工具的指令 | `--mode hls --tcl` 執行 HLS 腳本 | `make hls` |
| **.xo** | 編譯好的 kernel | RTL ＋ kernel 描述 | `v++ -c` 輸出 |
| **.xclbin** | 可以燒進 FPGA 的檔案 | bitstream ＋ metadata | `v++ -l` 輸出 |
| **Platform / Shell** | 卡上的基礎設施 | PCIe、DMA、HBM 控制器等，由 AMD 提供 | `xilinx_u55c_gen3x16_xdma_3_202210_1` |
| **Static / Dynamic region** | 固定區／可變區 | shell 在固定區，kernel 在可變區 | 第 3 章 3.6 節 |
| **XRT** | 控制卡片的軟體 | Xilinx Runtime：驅動程式＋函式庫 | `host.cpp` |
| **`xbutil`** | XRT 的管理工具 | 查看卡片狀態、測試 | `xbutil examine` |
| **Buffer object（bo）** | 卡上的一塊記憶體 | XRT 在 HBM 上配置的空間 | `xrt::bo` |
| **Connectivity（.cfg）** | 接線設定 | 指定 kernel 參數接到哪些 HBM PC | `cfg/*.cfg` |
| **sw_emu / hw_emu / hw** | 三種執行目標 | 軟體模擬／硬體模擬／實際上板 | `TARGET=` |
| **csim / cosim** | 兩種 HLS 模擬 | C 模擬／C 與 RTL 協同模擬 | 第 3 章 3.4 節 |
| **xsim** | Vivado 的 RTL 模擬器 | cosim 與 hw_emu 使用 | 未使用 |
| **csynth.rpt / csynth.xml** | HLS 報告 | 文字版／機器可讀版 | `hls_summary.py` 讀 xml |
| **Tcl** | 工具的腳本語言 | AMD 工具用 Tcl 撰寫自動化流程 | `run_hls.tcl` |
| **flexlm** | 授權管理 | 商用軟體的授權伺服器 | `/tools/Xilinx/flexlm` |

## A.7 軟體與開發工具

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **g++** | C++ 編譯器 | GNU 的開源編譯器 | `make csim` |
| **clang / LLVM** | 另一套編譯器 | Vitis HLS 的前端使用 clang | HLS 日誌 |
| **Make / Makefile** | 指令捷徑 | 把多個步驟寫成規則 | `fpga/trimul/Makefile` |
| **Testbench** | 測試程式 | 產生輸入、呼叫 kernel、檢查輸出 | `tb/tb.cpp` |
| **Host 程式** | CPU 端的控制程式 | 準備資料、控制 FPGA | `host/host.cpp` |
| **git clone / pull / push** | 下載／更新／上傳 | Git 版本控制指令 | 取得程式碼 |
| **分支（branch）** | 同一專案的不同版本 | 修改先放在分支，再合併進 main | `claude/lightnobel-...` |
| **PR（Pull Request）** | 合併請求 | 請求把分支合併進 main | PR #1 |
| **Personal Access Token** | GitHub 的鑰匙 | 代替密碼的存取權杖 | clone private repo 時需要 |
| **tmux** | 不會斷線的終端機 | SSH 斷線後程式繼續跑 | 跑 `make hls-all` |
| **PyTorch** | 深度學習框架 | 張量運算 | Python 腳本 |
| **transformers** | 預訓練模型函式庫 | HuggingFace 的開源函式庫 | `EsmForProteinFolding` |
| **Colab** | 免費的雲端 GPU | Google 提供的筆記本環境 | 沒有 GPU 時的替代方案 |

---

## A.8 架構評估與設計方法

| 術語 | 白話 | 說明 | 本專題 |
|---|---|---|---|
| **Architectural simulation** | 用模型預測硬體表現 | 在做出硬體前，用分析模型、cycle 級模擬或合成報告評估設計 | 6.2 節 |
| **分析模型（analytical model）** | 用公式算 cycle | 把迴圈次數、overhead 寫成公式，快速預測 | `make model`、6.8 節 |
| **校正（calibration）** | 用實測數字定常數 | 從 HLS 報告反推公式裡的 overhead、pipeline 深度 | 6.8 節（77、14） |
| **驗證（validation）** | 檢查模型準不準 | 用**沒拿來校正**的資料比對預測誤差 | 6.8 節 |
| **DSE（設計空間探索）** | 試遍所有設定 | 掃過 tile、平行度、精度等組合，找最佳設計 | `make model`、6.9 節 |
| **Pareto 前緣** | 無法同時更好的設計 | 找不到在所有指標都不輸、且至少一項更好的其他設計 | 6.9 節 |
| **Ablation** | 拆掉一招看差多少 | 逐一加入或移除手法，量出每一招的貢獻 | v0～v4 |
| **Producer / Consumer** | 產生者／使用者 | 產生資料的運算與使用資料的運算 | 6.4 節 |
| **Reuse distance** | 產生到使用的距離 | 距離越短，越容易留在晶片內 | 6.4 節 |
| **落地（materialize）** | 中間值寫回記憶體 | 融合的目的就是避免中間值落地 | 6.3 節 |
| **Epilogue** | kernel 的收尾階段 | 主計算之後的處理（LayerNorm、linear、gating） | 6.4 節 |
| **Welford 演算法** | 一次掃完算平均與變異數 | 數值穩定的線上統計方法 | 6.7 節 |
| **Tile sweep** | 掃過不同 tile 大小 | 量測 tile 大小的 trade-off | `make hls-sweep` |
| **容量模型** | 最多能處理多長 | `最大 L = sqrt(記憶體 ÷ 每個 L² 的 bytes)` | 6.10 節 |

---

## 本附錄小結
遇到不懂的詞，先在這裡查白話解釋，再回到「本專題」欄位指出的章節看完整說明。
