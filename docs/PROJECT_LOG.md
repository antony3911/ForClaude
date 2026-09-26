# 專題工作紀錄（交接用）

> **給接手的 Claude 對話：** 這份是專題競賽的完整工作紀錄。請先讀完這份，再讀
> `docs/manual/README.md`（教學手冊的大綱與撰寫進度）。使用者是 FPGA 初學者，偏好
> **繁體中文、白話解釋、一步一步來**，每一步都請他截圖回報。
>
> 最後更新：2026-09-26（第一個對話）

---

## 1. 專題基本資料

| 項目 | 內容 |
|---|---|
| 題目方向 | 以 LightNobel (ISCA 2025) 指出的困境為出發點，用**常見的 memory-bound 處理方法**做比較；不要求做出很厲害的新設計 |
| Reference | *LightNobel: Improving Sequence Length Limitation in Protein Structure Prediction Model via Adaptive Activation Quantization*（ISCA 2025，arXiv 上有） |
| 硬體 | AMD Alveo **U55C**（16 GB HBM2，32 個 pseudo-channel × 512 MB） |
| GPU | **沒有** |
| GitHub | `antony3911/ForClaude`，工作分支 `claude/lightnobel-memory-optimization-yhokyc` |
| PR | https://github.com/antony3911/ForClaude/pull/1 （尚未 merge；repo 無 CI） |

## 2. 選定的研究範圍

- 只實作 ESMFold 中 **Triangle Multiplication（outgoing）的 einsum 核心**：
  `z[i][j][c] = Σ_k a[i][k][c] · b[j][k][c]`，a, b, z ∈ R^{L×L×128}
- 不含 LayerNorm / gating / linear projection。
- 已用 HuggingFace `EsmForProteinFolding` 驗證：此算式與 `trunk.blocks[N].tri_mul_out._combine_projections` 的輸出**完全相同（差值 0）**。

## 3. 五個 kernel 版本

| 版本 | 手法 | 每 cycle MAC 數 |
|---|---|---|
| v0 | Baseline：每次 MAC 直接讀 HBM | 1（受 fadd latency 拖累） |
| v1 | Tiling + on-chip buffer（TI×TJ = 8×8） | 1 |
| v2 | v1 + 512-bit 寬位元 AXI | 16 |
| v3 | v2 + double buffering（ping-pong） | 16 |
| v4 | v2 + INT8 per-token 量化 | 64 |

不改 kernel 的額外實驗：tile size sweep（`DEFS="-DTILE_I=.. -DTILE_J=.."`）、HBM 單一 bank 對照（`cfg/trimul_v2_onebank.cfg`）。

## 4. 環境調查結果（使用者的 server：`scd-lab-server63`）

| 項目 | 結果 |
|---|---|
| Vitis / Vivado | **2025.2**，在 `/tools/Xilinx/2025.2/` |
| `v++`、`vitis-run` | 有 |
| `vitis_hls` | **沒有**（2024.2 起移除，改用 `vitis-run --mode hls --tcl`） |
| `xbutil` / XRT | **沒有** |
| `lspci -d 10ee:` | **空的 → 這台沒有插 FPGA 卡** |
| U55C platform（`/opt/xilinx/platforms`） | **沒有** |
| g++、make、git | 有 |
| `/usr/local/tsri-eda` | 存在，推測是 TSRI（國研院半導體中心）的 EDA 環境 |

**結論：** 這台只能做 `make csim` 和 `make hls`。上板（`make xclbin` / `make run`）需要找到有 U55C 的機器。
**待辦：** 使用者要問學長姐／助教「U55C 插在哪台、怎麼登入、有沒有 XRT 和 U55C platform」。

## 5. 時間軸（做了什麼、遇到什麼、怎麼修）

| # | 事件 | 結果 / 產出 |
|---|---|---|
| 1 | 使用者說明題目與困境（不懂 FPGA 工具） | 給出環境調查指令與整體建議 |
| 2 | 使用者確認有 U55C | 建立 `fpga/trimul/`：5 個 kernel、testbench、host、cfg、Makefile、HLS tcl；`docs/getting_started_u55c.md` |
| 3 | g++ C 模擬 | 5 版全部 PASS；隨機資料含 1% outlier：**per-token INT8 rel_l2 ≈ 1%、per-tensor ≈ 11%** |
| 4 | 使用者問如何用真實長鏈蛋白質 | 寫 `python/dump_trimul_inputs.py`（HF ESMFold，跑到指定 block 擷取 a, b）；發現必須用 `model.infer()` 而非 tokenizer id；`docs/real_protein_data.md` |
| 5 | 使用者表示沒有 GPU | 真實資料改為「加分項」（可用 Colab），主線用模擬資料 |
| 6 | 修正文件錯誤 | INT8 版輸出 z 仍是 FP32 → 相同 HBM 下 L 只能多約 **1.4 倍**（不是 2 倍） |
| 7 | 使用者看不懂在做什麼 | 寫 `docs/conversation_notes.md`（廚房比喻、檔案地圖） |
| 8 | 打包 zip 給使用者放到 `C:\ForClaude` | 已傳送（zip 未進 repo） |
| 9 | 環境調查（截圖兩張） | 見第 4 節 |
| 10 | 使用者 clone 時被要求 username | repo 是 private；建議改 public 或用 fine-grained read-only token |
| 11 | `make hls` 失敗 #1：csim 連結找不到 `trimul_v2` | 當時判斷為 2025.2 csim 問題 → 改成預設跳過 in-HLS csim（`CSIM=1` 才跑） |
| 12 | `make hls` 失敗 #2：`Cannot find source file ../kernels/trimul_v2.cpp` | 改用絕對路徑 → 仍失敗 |
| 13 | `make hls` 失敗 #3：同上 | **根因**：專案名稱含 `/`（`hls_prj/trimul_v2`）時，2025.2 把來源路徑改寫成「假設專案只在下一層」的相對路徑。**修法：先 `cd hls_prj` 再 `open_project $kernel`** → 成功 |
| 14 | **v2 合成成功**（見第 6 節） | 第一筆數據 |
| 15 | 新增 `scripts/hls_summary.py`、`make hls-all`、`make summary` | 一次合成全部版本並輸出比較表（`hls_summary.csv`） |
| 16 | 使用者正在跑 `make hls-all` | **等待結果截圖** |
| 17 | 使用者請求撰寫教學手冊 | `docs/manual/` 6 章 + `manual.pdf`（見第 8 節） |

## 6. 已取得的數據

### v2 HLS 合成（L = 256，C = 128，300 MHz）
- Timing：目標 3.33 ns，估計 **2.431 ns** → 達標
- Latency：**177,029,185 cycles ≈ 0.590 s** → 約 **7.3 GFLOP/s**（v2 理論上限 16×2×300M = 9.6 GFLOP/s 的 76%）
- 迴圈：`tile_i` 32 次 × `tile_j` 32 次 × `loop_k` 256 次；每次 `loop_k` = **671 cycles**
  - `load_a` 141、`load_b` 141（兩者在不同 AXI port，**並行**）、`mac` 526（理想 512，II=1 達成）
  - 671 ≈ 141 + 526 + 少量 → **約 21% 時間在等記憶體**
  - 每個 tile 另有 `init` 514 + `store` 586 cycles
- **預測：** v3 把載入藏到計算後面，`loop_k` 應接近 ~530 cycles → 約快 20%。待 `make hls-all` 結果驗證。

### C 模擬（g++，L = 32，隨機資料 1% outlier ×30）
- v0～v3 rel_l2 ≈ 1e-7（浮點誤差）
- v4 per-token rel_l2 ≈ **9.9e-3**，per-tensor ≈ **1.1e-1**

## 7. 下一步（依序）

1. 取得 `make hls-all` 的比較表（v0～v4），分析：
   - v0→v1 資料重用的效果、v1→v2 平行度、v2→v3 是否符合 ~20% 預測、v4 的資源代價
   - 若某版 FAILED：`tail -n 30 hls_trimul_vN.log`
2. Tile sweep（例：`make hls KERNEL=trimul_v2 DEFS="-DTILE_I=16 -DTILE_J=16"`；注意不同 DEFS 會覆蓋同名專案，需要另外記錄）
3. 找到 U55C 機器 → `make xclbin TARGET=hw`、`make run`（檢查 platform 名稱，預設 `xilinx_u55c_gen3x16_xdma_3_202210_1`；也要確認該 platform 支援 Vitis 2025.2）
4. 上板實驗：v2 多通道 vs. onebank、L 掃描、FP32 vs INT8
5. （加分）Colab 跑 `dump_trimul_inputs.py` 取得真實 activation 的量化誤差
6. 報告圖表：roofline、各版本長條圖、tile sweep trade-off、量化誤差、記憶體 vs L 曲線

### 已知風險 / 注意事項
- 程式在 2025.2 上只驗證過 **v2 的 HLS 合成**；v0/v1/v3/v4 的合成、cosim、`v++`、XRT host 都**還沒實際跑過**。
- v0 在 HLS 報告中的 latency 會非常大，屬正常（它就是對照組）。
- `make csim` 用的是系統 g++，與 HLS 無關；功能正確性以它為準。
- HLS 內建 csim 預設關閉；若要開（`CSIM=1`），路徑 bug 已修，應可運作但未驗證。

## 7.5 競賽方向升級（2026-09-26）
使用者覺得原題目偏敷衍，已整理 `docs/competition_directions.md`：
A 融合版 Triangle Multiplication（主推）、B FPGA 簡化版 AAQ、C 分析模型＋DSE、D 真實 activation 分析、E 多 CU。
建議 A＋C＋D。
**使用者回覆：** 校內專題小競賽；**三週內（約 10/17）交 architectural simulation 結果＋海報**，再一個月後口頭報告；
評分偏好不明確，「至少不要太敷衍」。→ 計畫見 `docs/three_week_plan.md`（第 1 週量測＋校正模型、第 2 週融合 producer kernel、第 3 週圖表海報）。
新增工具：`make hls-sweep`（tile 4/8/16/32，專案名 `<kernel>_t<N>`）、`make model`（`scripts/perf_model.py`，
已用 v2 報告校正，誤差 < 0.01%；v0/v1/v3/v4 常數為假設值待校正）。HLS 專案名稱改用 `TAG`（`PRJ` 環境變數）。

## 8. 教學手冊

使用者要求一份鉅細靡遺的教學手冊（為何而做、為何可做、整體流程、工具原理），
放在 `docs/manual/`，進度表在 `docs/manual/README.md`。
**狀態：已依學習順序重排為「導讀＋7 章＋附錄 A/B」（2026-09-26），已輸出 `docs/manual/manual.pdf`（約 58 頁）。**
之後若有新數據（例如 `make hls-all` 的比較表、上板結果），請更新第 4 章 4.11 節、第 2 章 2.6 節、第 6 章 6.8～6.9 節的預測驗證，
並重跑 `build_pdf.py`。

## 9. 檔案索引

| 檔案 | 用途 |
|---|---|
| `docs/PROJECT_LOG.md` | ← 本檔：交接用工作紀錄 |
| `docs/conversation_notes.md` | 給使用者的白話筆記（廚房比喻、下一步） |
| `docs/getting_started_u55c.md` | U55C 環境與開發流程 |
| `docs/real_protein_data.md` | 真實蛋白質資料流程（需 GPU / Colab） |
| `docs/manual/` | 教學手冊 |
| `fpga/trimul/kernels/` | `trimul.h`、`trimul_v0~v4.cpp` |
| `fpga/trimul/tb/tb.cpp` | g++ C 模擬 testbench（`make csim`，可加 `DATA=`） |
| `fpga/trimul/host/` | `host.cpp`（XRT）、`common.h`（資料產生、量化、參考答案、讀 .bin） |
| `fpga/trimul/cfg/` | HBM 連接設定 |
| `fpga/trimul/hls/run_hls.tcl` | HLS 合成腳本（含 2025.2 路徑 bug 的 workaround） |
| `fpga/trimul/scripts/hls_summary.py` | 讀 `csynth.xml`，產生比較表 |
| `fpga/trimul/Makefile` | `csim` / `hls` / `hls-all` / `summary` / `xclbin` / `host` / `run` |
| `python/dump_trimul_inputs.py` | 從 ESMFold 擷取真實 a, b |
