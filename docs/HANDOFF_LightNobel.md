# 交接筆記：給接手的助理

> 這份文件是給「另一個 Claude 帳號／對話」看的，讓你不用重讀整段對話，就能接手指導這位使用者。
> 最後更新：2026-10-05。倉庫：`antony3911/ForClaude`，分支 `claude/lightnobel-memory-optimization-yhokyc`（PR #1）。
> 同一個倉庫裡還有一個**不相關的專案**（遊戲 mod，分支 `claude/two-account-handoff-plan`，交接檔叫 `HANDOFF.md`）。不要動那個分支，也不要把兩份交接檔搞混；這份才是 LightNobel 的。

---

## 0. 建議閱讀順序

1. 本文件（全部），**特別是 7.5 節：目前和使用者討論到哪、下一步做什麼**
2. `docs/characterization.md`：2026-10-04 做的 workload characterization（方法、數據、結論、限制）
3. `docs/report/summary_zh.md`（或 `summary_en.md`）：目前最精簡、已核對過的技術摘要，約 12～16 頁
4. `docs/manual/`：教科書式手冊（約 150 頁，`manual.pdf`），需要細節時查
5. `docs/PROJECT_LOG.md`：時間軸、已取得的數據、更正紀錄
6. `docs/three_week_plan.md`、`docs/competition_directions.md`：比賽策略（部分內容已過時，見第 6 節）

---

## 1. 使用者是誰、怎麼跟他溝通

- 台灣的大學生，**硬體設計背景**（學過 Verilog、懂暫存器、FSM、pipeline、時序），程式和 ML 背景較弱。
- **一律用繁體中文回答**。他寫英文時會請你幫忙修改；他的英文其實不差，主要錯在語序和用詞，改的時候要說明原因。
- **偏好的解釋方式：**
  - 由上而下：先講整體在做什麼，再講細節。
  - **一定要有具體例子**，最好有實際數字一步一步走（例如 L = 4 的 tiling 追蹤、3×3 矩陣的轉置驗證）。只講抽象概念他會卡住。
  - 從**硬體角度**解釋（AXI 有哪些線、BRAM 有幾個 port、RAW hazard、FSM ＋ datapath），他聽得懂、也喜歡。
  - 回答要直接，不要繞，也不要灌水。
- **他常卡住的地方**（之前都解釋過，答案見第 4 節）：多維陣列攤平成一維的索引、`a·bᵀ` 為什麼要轉置、v1 的重用發生在哪個迴圈、burst 是怎麼來的、512-bit 加寬到底加寬了什麼、C 為什麼能變成硬體。
- **他很在意誠實**：哪些是實測、哪些是估算、哪些是推測，一定要講清楚。他也意識到「程式是 AI 寫的，但上台答辯的是自己」，所以**幫他理解比幫他多做功能更重要**。
- **目前（2026-10-05 起）只在對話裡討論**：他說 PDF 不方便討論，所以不改手冊、不做 PDF，沒被要求也不寫程式。解釋格式和節奏見 7.5 節。（舊規則「改完手冊主動附 PDF」暫停。）
- **他要的是真正的反駁**，不是附和；他的想法有問題就直說並給理由。
- **電腦**：Windows 11 筆電，RTX 4070 Laptop（8 GB）、16 GB RAM、C 槽剩餘空間有限（另一個繪圖工具也在用，裝東西前先估大小）。

---

## 2. 專題是什麼

- **校內專題競賽**，以 LightNobel（ISCA 2025，arXiv 2505.05893）為參考論文。
- 時程：**約 10/17 交 architectural simulation 結果與海報**，再一個月後口頭報告。
- 已登記的題目：*Exploring Memory-Efficient Execution Strategies for Long-Sequence Protein Structure Prediction*。
- 範圍：ESMFold 裡 **Triangle Multiplication（outgoing）的 einsum** `z[i][j][c] = Σ_k a[i][k][c] · b[j][k][c]`，C = 128，以及周邊的記憶體優化。
- **平台還沒確定。** 原本規劃用 AMD Alveo U55C（HBM），但教授還沒確認，所以給教授的文件**不要提特定平台**，只講想法和計算（見 `docs/report/`）。
- **教授最新的要求（2026-10 初）：先做 characterization study**（workload characterization），也就是在設計之前，先量清楚時間、記憶體和資料特性花在哪。見第 7 節。

---

## 3. 目前的成果與狀態（誠實版）

| 項目 | 狀態 | 位置 |
|---|---|---|
| v0 基準 kernel | ✅ 已寫、C 模擬通過 | `fpga/trimul/kernels/trimul_v0.cpp` |
| v1 tiling（8×8） | ✅ 已寫、C 模擬通過 | `trimul_v1.cpp` |
| v2 512-bit ＋ 16 lane | ✅ 已寫、C 模擬通過、**有 HLS 報告** | `trimul_v2.cpp` |
| v3 double buffering | ✅ 已寫、C 模擬通過；**HLS 待跑**（`make hls-all`） | `trimul_v3.cpp` |
| v4 INT8 per-token | ✅ 已寫、C 模擬通過；HLS 待跑 | `trimul_v4.cpp` |
| 多 HBM 通道 | ⚠️ 只有設定檔，要上板才量得到 | `fpga/trimul/cfg/` |
| 融合 producer／consumer、重算 g | ❌ **只有設計與估算**，沒有實作 | 手冊 3.5、3.6、10.3 |
| v5 INT4 | 📅 已降為延伸項目（時間不夠可以不做） | — |
| 分析模型、DSE | ✅ | `fpga/trimul/scripts/perf_model.py`（`make model`） |
| 真實資料擷取與量化誤差 | ✅ | `python/dump_trimul_inputs.py` |
| 教學手冊 | ✅ 約 150 頁 | `docs/manual/`，`python3 docs/manual/build_pdf.py` |
| 給教授的技術摘要（中英） | ✅ 平台無關版 | `docs/report/`，`python3 docs/report/build_report.py` |
| LightNobel 介紹投影片 | ✅ 10 頁（已報告完） | claude.ai Artifact：https://claude.ai/artifact/DSUxtHzzsSxkWzn6coLe2R |

**已有的實際數字：**
- v2 HLS（L = 256、8×8 tile、300 MHz）：總計 **177,029,185 cycles（0.590 s）**；每輪 k：load 141、mac 526、合計 671；init 514、store 586。
- 分析模型用這份報告校正（α = 77、δ = 14、σ = 74），預測 177,029,120，誤差 < 0.01%。但這是**同一份報告校正又驗證**，只證明一致性；真正的驗證要用沒看過的設定（tile sweep、v3、v4）。
- C 模擬：v0～v3 的 rel_l2 都是 1.141e-7；v4 per-token 約 1%、per-tensor 約 11%。
- `einsum("ikc,jkc->ijc")` 與 HF ESMFold 內部計算比對，差值 0（在隨機初始化的小模型上）。

**只是估算、不能當實測講的：** v3 的 530 cycles／1.27 倍（模型預測）、v1 每輪約 10,240 cycles、容量模型的 1.52 倍（建立在還沒實作的融合設計上）、3.4 節多通道 HBM 的數字。

---

## 4. 已經教過的觀念（答案要點）

需要複習時可以直接用這些例子。

| 主題 | 要點 | 手冊位置 |
|---|---|---|
| 3 維索引 | `a[i][k][c]` 的位置是 `(i·L + k)·C + c` = 先用 2 維公式找第幾格，再乘每格大小、加格內位置。2 維是 `i × 欄數 + j`（他一開始誤寫成 `i×k+j`） | 手冊 8.3 |
| 為什麼是 `a·bᵀ` | outgoing 用 i→k、j→k 兩條邊，所以兩邊都取「列」；3×3 實例：z[0][1] = 5；`a×b` 會得到 2，對應位置相乘得到 0。incoming 是 `aᵀ·b`。每個 channel 獨立，所以是 128 個 batched matmul | 手冊 1.4 |
| 轉置何時發生 | 數學和我們的 kernel 都**沒有真的轉置**。PyTorch（HF ESMFold）會先 `permute`，`matmul` 再複製資料，CPU 實測 L=256 有 256 次 clone | 對話中說明，手冊未收 |
| v0 → v1 | v0：一次算一個 z[i][j][c]，最內層是 k，位址每次跳 C，沒辦法 burst、也沒有重用。v1：i、j 每次跳 8，acc[8][8][128] 放晶片內；每輪 k 分 load_a、load_b、mac 三段；**重用發生在 mac 迴圈**（有 ii、jj、c 三層），la 和 lb 各被用 8 次 | 手冊 3.1 |
| burst | AXI 有 AR（位址 ＋ 長度）和 R（資料）兩個 channel。burst = 一個位址、連續很多拍。C 裡不用寫，是 **HLS 從「pipeline 迴圈 ＋ 連續位址」自動推論**出來的。**v1 就已經有 burst**（128 拍 × 32 bit），v2 是變寬（8 拍 × 512 bit），不是「開始有 burst」 | 手冊 3.2（標題仍寫「v1→v2」，有點誤導，可以考慮修） |
| 512-bit 加寬 | 改的是 kernel 的 AXI master 介面（`RDATA[31:0]` → `RDATA[511:0]`），HBM 沒變。程式上只改指標型別 `float*` → `f16*`（16 個 float 的 struct）。還要搭配 ARRAY_PARTITION（buffer 切 16 塊）和 unroll（16 組乘加器）。a、b、z 各有獨立的 bundle，所以 a、b **各自**一拍 16 個 | 手冊 3.2、8.4 |
| v1→v2 為什麼快 | v1 有 80% 時間在 mac（一拍 1 次乘加），所以**主要收穫是 16 倍運算平行化**，加寬介面是為了餵得上 | — |
| v3 | 兩組 buffer 輪流使用；`load_ab`、`mac` 設 `INLINE off` 變成獨立模組；讀寫不同陣列所以能同時跑；只有一組會有 WAR hazard；上限受 Amdahl 限制（搬運只佔 21%） | 手冊 3.3 |
| C 怎麼變硬體（HLS） | 不是逐行翻譯：DFG → 排程 → 配置／綁定 → FSM ＋ datapath。陣列 → BRAM、迴圈 → 計數器 ＋ FSM、指標 → AXI master。為什麼還要學 Verilog：精確時序、控制邏輯多、ASIC、除錯，以及寫好 HLS 本身就需要硬體觀念 | 手冊 7 |
| float | FP32 = 32 bit，一個 float 就是 `a[i][k][c]` 一個值（第 i、k 對胺基酸的第 c 個特徵） | 手冊 4.1 |
| 英文術語 | v1：loop tiling／blocking、data reuse、on-chip buffering、output-stationary。v2：wide memory interface、vectorization／SIMD、array partitioning、loop unrolling。v3：double buffering／ping-pong、overlapping transfer with computation、latency hiding | — |
| 32 bit 是不是 limitation | **不是硬體限制**，是 v1 寫法（`float*`）造成的；平台支援 512 bit，v1 只用了 1/16 | — |
| 這些手法常見嗎 | 很常見，算是標配（經典：Zhang et al., FPGA 2015 的 tiling ＋ double buffering ＋ roofline）。**不能說成貢獻**；貢獻要放在「應用到 TriMul 的分析」上 | — |

---

## 5. LightNobel 的關鍵事實（已核對原文）

- 只加速 Protein Folding Block；ESM-2 和 structure module 不在加速器上。
- **AAQ**（token-wise 量化）：
  - A 組（LayerNorm 前、residual 上）：INT8 ＋ 4 個 INT16 outlier
  - B 組（LayerNorm 後、linear 前）：INT4 ＋ 4 個
  - C 組（其他，包含 TriMul 的 a、b）：INT4，不處理 outlier
  - 對稱量化；權重 INT16；比較基準是 **FP16**
- **硬體**：
  - RMPU：把數拆成 4-bit 小塊，乘法器輸入是 **5-bit 有號**；PE = 16 個乘法器、Lane = 8 PE、Cluster = 20 Lane（4 和 5 的最小公倍數）、Engine = 4 Cluster = 10,240 個乘法器
  - VVPU：128 條 SIMD lane、exp 查表、bitonic top-k
  - 其他：Token Aligner、crossbar（佔 **70% 面積**）
  - 數量：32 個 RMPU、每個配 4 個 VVPU
- **硬體是分時共用的**，一層模型分好幾趟跑；einsum 在 RMPU 上做，而且一定在 LayerNorm／gating 之後。這點使用者曾經問過，手冊 6.2 已修正。
- **Fig. 3（H100、不分塊）**：Triangle Attention 從 29.0%（R0271）升到 75.9%（T1269）；TriMul 從 36.1% 降到 14.5%。**TriMul 不是長序列的最大瓶頸**，選它是本專題自己的範圍決定。
- **結果**：最多快 8.44×（A100）／8.41×（H100）、能效 37.29×／43.35×、峰值記憶體最多降 **120.05×**（和不分塊的 GPU 比；和分塊比只有 1.26～5.05×）、最長 9,945 aa、178.80 mm²、67.8 W。
- 記憶體節省的兩個來源：量化（約 1.65×）和不存 L³ 的 attention logits（大部分的 120×）。
- **論文 PDF 不要 commit 到倉庫**（倉庫是公開的），也不要大段複製原文。原文的文字版在使用者端。

---

## 6. 曾經犯過、已更正的錯誤（不要再犯）

- 「einsum 的 scale 可以最後乘一次」是**錯的**。per-token 的 scale 在 k 方向每項都不同，v4 每個 k 都要乘 `sa × sb`。只有 linear（沿 channel 加總）才能最後乘一次。
- 容量比較要用 **FP16 基準**（1.52×），不是 FP32（1.67×）。
- 「融合」不是新點子（OpenFold3 有 GPU 融合實作，LightNobel 也用管線串接）。
- 手冊 6.2 曾經把 VVPU 的 LayerNorm 畫在 RMPU 之後，已修正為「VVPU 前處理 → RMPU → VVPU 後處理」。
- `three_week_plan.md` 的標題、故事和「v5 第二週」的安排**已經過時**：v5 已降為延伸，平台也未定。

---

## 7. 下一步：characterization study（教授要求）

**目的**：在設計之前，先用數據回答「時間和記憶體到底花在哪」，就像 LightNobel 的 Fig. 3～5。這一步不依賴 FPGA 平台。

**原本的建議做法**（範圍已在下面定案）：

1. **時間分布**：用 PyTorch profiler（有 GPU 時加 Nsight）跑 HF ESMFold（`facebook/esmfold_v1`），測多個長度（例如 L = 100、300、500、1000……），記錄每種運算（TriMul out／in、TriAttn start／end、seq attention、transition 等）的時間佔比。
2. **記憶體**：記錄峰值記憶體，以及各中間張量的大小（也可以用形狀公式計算後對照）。
3. **運算特性**：每個運算的 FLOPs、bytes、算術強度 → 畫 roofline。
4. **資料特性**：沿用 `python/dump_trimul_inputs.py`，它已經能輸出 outlier 統計、`paper_group_C_check`、`rel_l2_grid`（INT8／INT4 × token／channel／tensor）。
5. **隨 L 的變化**：以上每一項對 L 作圖。

**範圍（2026-10-04 與使用者討論後）：** 教授也不確定範圍。使用者的目標是「推導出整個工作流程裡哪裡最值得優化」。決定的做法分三層：
1. **公式**：每個運算的 FLOPs、bytes、中間張量大小，對所有 L 計算（與平台無關）。
2. **筆電實測**：短～中長度，量 GPU kernel 時間（profiler，不用 wall-clock）與峰值記憶體；chunk 開、關都量（關 = 對照論文 Fig. 3）。用來**驗證第 1 層的 roofline 模型**，不直接當結論。
3. **長序列**：引用論文 Fig. 3 ＋ 用模型外推；之後可以申請外部 4 × A100 server 實測。

**為什麼筆電的時間佔比不能直接當結論**（已向使用者解釋）：受算力限制和受頻寬限制的運算，換硬體後的加速倍數不同（H100 對筆電 4070：算力約 3 倍、頻寬約 13 倍），chunk 和 CPU 負載也不是等比影響。記憶體數字和隨 L 的趨勢則與硬體無關。

**環境（2026-10-04 已建好）：**
- 使用者的筆電：**RTX 4070 Laptop 8 GB ＋ 16 GB RAM**（之前寫的「沒有 GPU」是指學校 server）。
- git worktree：`C:\Users\anton\ForClaude-lightnobel`（mod 專案的 session 在 `ForClaude` 用另一個分支，**不要在那邊切分支**）。
- venv：`C:\Users\anton\venvs\lightnobel`（torch 2.11＋cu128、transformers 5.18）。模型在 HF cache（8.44 GB）。
- 下載要設 `HF_HUB_DISABLE_XET=1`（Xet 下載曾卡在 0 bytes）。
- `python/smoke_esmfold.py`：ESM-2 放 CPU（FP16，檔案本來就是 FP16），trunk 等放 GPU 並從原檔填回 FP32 權重。直接在 CPU 上做 `.float()` 會 access violation。
- 實測 L = 100（隨機序列）：參數 ESM-2 2.83 B／其他 0.69 B；GPU 權重 2.77 GB、峰值 2.86 GB；ESM-2（CPU）26.9 s、trunk＋structure 約 5.6 s。當時另一個 session 在裝套件，**時間不能用**，只證明跑得動。
- 另一個 session 會用同一張 GPU 跑繪圖工具：量測前先看 `nvidia-smi`，電腦閒的時候再量。

**第一輪已完成（2026-10-04）：** 結果、方法、限制都在 `docs/characterization.md`，程式與原始數據在 `python/char/`。重點：
- 長序列時 TriAttn 佔 block 時間 54%→73%（L = 256→1410），受頻寬限制（L³ logits 讀寫約 8 次）；TriMul 20～26%。
- **TriMul 在 GPU 上只有 6% 是 einsum，57% 是 permute 後的轉置複製**（約 15 GB/s，頻寬的 7%）→ 選 TriMul 的新理由：浪費在資料排列與搬移，正是空間加速器能改善的。
- 192 個 block（48 × 4 輪；第一輪誤寫成 240，10-06 已更正）佔端到端 98.3%（L = 512）；ESM-2、structure module 各 < 1%。更正後端到端每個 block 比單獨量的慢 17～18%，原因未查明。
- 分塊：時間不變、記憶體降 4 倍（L = 512）。
- roofline 推 H100 與論文 Fig. 3 趨勢一致，差 5～8 個百分點。
- 泛素與 PDB 1UBQ 的 CA RMSD 0.84 Å（模型正確）。
- 量測坑：Windows 驅動會偷借系統 RAM（要設記憶體上限）；profiler 要用 GPU 時間軸歸屬 kernel。

**下一步：** 見 7.5 節的「明天的計畫」。之後可用外部 A100 跑 `profile_block.py` 驗證長序列；把「不轉置／融合」版 TriMul 的搬運量算出來。

**還要確認：** 實驗室投影片的 TODO 寫的是 gem5 ＋ Ramulator ＋ Garnet/Noxim。10/17 要的「architectural simulation」可能是指這套，跟我們的 HLS ＋ 分析模型路線不同，要找機會問教授。

**可能的結果與意義：**
- 在關心的長度範圍內，如果 TriMul 的佔比夠高 → 選題有數據支撐。
- 如果 TriAttn 遠大於 TriMul（論文的 Fig. 3 是這樣）→ 要準備好解釋為什麼仍然選 TriMul（例如 einsum 是唯一跨 token 的運算、作為記憶體優化的研究載體），或和教授討論是否調整方向。

**其他待辦：**
- 使用者 server 上跑 `make hls-all`、`make hls-sweep`，拿到 v3、v4 和不同 tile 大小的數字，用來驗證分析模型。
- 確認比賽對使用 AI 工具有沒有揭露規定。

## 7.5 論文逐步討論的進度（2026-10-05）

**模式**：使用者要先確認自己真的讀懂論文，**只在對話裡討論**；不改手冊、不做 PDF，沒被要求不寫程式。每個運算都講五件事：吃什麼、吐什麼、**每個數字的來源**（標【定義】【模型設定】【舉例】【推導】）、算得出來的小例子、為什麼有用。每次只講一小段，講完確認再往下；他抱怨過「太急」。論文沒寫的要標明是我們的推論。

**已講完**：步驟 0 前半（FP32／FP16／INT、二補數、浮點欄位）；步驟 1（字母→兩套編號→ESM-2 的 embedding、36 層、LayerNorm、attention、head、rotary、FFN→`s`、`z` 初值）；步驟 2 全部（block 的 9 個運算，TriMul 的 a、b、einsum、GPU 的 3 次轉置 copy，TriAttn 的 L³ logits 與 8 次讀寫、分塊、token-wise attention）。

**他卡過、已釐清的點**：ESMFold（整個流程）≠ ESM-2（第一塊）；ESM-2 的 36 層沒有 `z`，trunk 的 48 個 block 才有；128／64 是「個數」不是 bit，64 是向量維度不是把胺基酸分兩半；`z` 是模型的猜測不是量測，所以要看三角形；計算順序可以自由安排（每個輸出獨立）；容量、搬運量、計算量是三種不同的開銷。

**討論中的結論**：TriAttn 73% 是**重現**論文 Fig. 3，不是新發現，不能說成「我們發現」；我們自己的新東西是「TriMul 在 GPU 上 einsum 只佔 6%、轉置 copy 佔 57%」與 roofline 的解釋。專題要從「einsum 很慢」改成「TriMul 浪費在資料搬移，用專用資料流與融合消除」。他提過「用前幾個 bit 篩掉不重要的 k」（動態稀疏性），已說明在 TriMul 上要先用數據證明夠稀疏，TriAttn 較有希望。他以為「沒有 GPU 的 server 更能反映 FPGA」，已反駁：CPU 跟 GPU 一樣逐運算執行，FPGA 的比例取決於自己的設計。

**還沒講**：步驟 0 後半（量化、scale 何時能最後乘）；步驟 3（recycling、structure module）；步驟 4（LightNobel 硬體逐運算對應，需要他提供原文段落）。

**明天的計畫**（他要求設計簡單、還不到優化階段）：
1. server 先跑 `nvidia-smi; nproc; free -g` 確認硬體（依紀錄沒有 GPU）。
2. FPGA 版 roofline：把 `python/char/results/counts_block.csv` 的運算量／搬運量代入板子規格（PYNQ-Z2 約 220 DSP、512 MB；U55C 約 9,000 DSP、HBM 約 460 GB/s，使用前要查證）。
3. server 跑 `make hls-all`（現成指令）。CPU 版 ESMFold 量測只當第三個驗證點，優先度最低。
4. 教他我們做了什麼：`python/char/` 各檔案的作用與結果檔怎麼讀，讓他自己在筆電上跑一次 `profile_e2e.py`（泛素）；可選：一起寫一個他看得懂的 30 行「每個運算前後掐碼錶」簡化版。

---

## 7.6 server CPU 量測（2026-10-05～06）

- server `scd-lab-server63`：64 核、125 GB RAM、無 GPU、只有 Python 3.9。venv `~/venv-ln`（CPU 版 torch），repo 在 `~/ForClaude`，`st` alias 看進度。模型已下載；**一律設 `HF_HUB_OFFLINE=1`**（舊版 transformers 會在背景多下載 safetensors）。
- `run_cpu.py`（碼錶版，使用者要求「最簡單、只求跑完」）跑完 L = 76／256／512／1024：三角運算 68→90%，TriAttn 11→69%，TriMul 57→22%；泛素 RMSD 0.83 Å。結果與分析在 `characterization.md` 3.9、`analyze_cpu.py`。
- 結論：三平台趨勢一致、交叉點隨硬體移動；TriMul 在 CPU 上算力和頻寬都只用到一小部分（與 GPU 的 copy 57% 一致，CPU 原因待 `diagnose_cpu.py` 確認）。
- 待辦：使用者在 server 跑 `diagnose_cpu.py --L 512 1024 --threads 32`、貼 `lscpu` 與 torch／transformers 版本。
- 使用者已去研討會、目前討論模式仍是「對話為主」，但 10-06 明確要我先做能做的事（寫診斷程式、更新 characterization）。

## 8. 工作慣例

- **分支**：只 push 到 `claude/lightnobel-memory-optimization-yhokyc`。
- **commit 訊息**：結尾加上這個環境規定的 attribution trailer；訊息裡不要寫模型名稱。
- **產生 PDF**：
  - 需要 Python 套件 `markdown` 和 Chromium。
  - 手冊：`python3 docs/manual/build_pdf.py`
  - 技術摘要：`python3 docs/report/build_report.py`
  - 檢查渲染結果可以用 `pypdfium2` 把頁面轉成圖片來看。
  - 已知問題：表格前面要空一行，`build_pdf.py` 已會自動補。
- **手冊修改原則**：使用者要的是**系統性、易讀的教科書**，不要單純把新內容塞成一章；改完要回頭檢查全書前後一致。
- **給教授的文件**（`docs/report/`）：不要教學口吻、不要舉例、不要寫讀論文的方法、不要提特定平台、不要放程式碼，只放想法和計算。
- 使用者的 server：`scd-lab-server63`（共用的學校伺服器）。已提醒他**不要在共用伺服器上存 GitHub 憑證，也不要從那裡 push**。

---

## 9. 檔案索引（最常用）

| 路徑 | 內容 |
|---|---|
| `docs/manual/00_guide.md` ～ `11_research_method.md`、`A`～`C` | 手冊各章（1 問題、2 記憶體牆、3 資料流、4 量化、5～6 LightNobel、7 FPGA 工具、8 實作、9 評估、10 策略、11 研究方法） |
| `docs/report/summary_{en,zh}.md` | 給教授的技術摘要（平台無關） |
| `fpga/trimul/kernels/` | v0～v4 kernel、`trimul.h`（C、tile 大小、`f16`、`q64`） |
| `fpga/trimul/tb/`、`host/` | testbench、XRT host |
| `fpga/trimul/Makefile` | `make csim`、`hls`、`hls-all`、`hls-sweep`、`model` |
| `fpga/trimul/scripts/perf_model.py` | 分析模型、DSE、容量模型 |
| `python/dump_trimul_inputs.py` | 從 HF ESMFold 擷取 a、b 並做統計 |
| `docs/PROJECT_LOG.md` | 時間軸、數據、更正紀錄 |
| `docs/characterization.md` | workload characterization 的結果與方法 |
| `python/char/count_ops.py` | 用 meta tensor 數每個運算的 FLOPs、搬運量（任何 L，不用 GPU） |
| `python/char/ceilings.py` | 量這台 GPU 的實際算力、頻寬 |
| `python/char/profile_block.py` | 一個 block 的逐運算 GPU 時間與峰值記憶體（主要數據） |
| `python/char/profile_e2e.py` | 完整 ESMFold 的時間分布、泛素正確性檢查（RMSD） |
| `python/char/compare.py` | roofline 預測 vs 實測、推 H100 對照論文 Fig. 3，畫圖 |
| `python/char/diagnose.py` | TriMul 內部逐 kernel 的時間（找到 copy 佔 57% 的那支） |
| `python/char/results/` | 上面程式的輸出（csv、log、`share_vs_L.png`） |
| `python/smoke_esmfold.py` | 最簡單的試跑：確認模型載得起來、跑得動 |

筆電環境：git worktree `C:\Users\anton\ForClaude-lightnobel`、venv `C:\Users\anton\venvs\lightnobel`。跑之前設 `HF_HUB_OFFLINE=1`（模型已在快取）；重新下載要設 `HF_HUB_DISABLE_XET=1`。
