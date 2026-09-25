# 第 3 章　整體流程：從頭到現在具體做了什麼？

> **本章重點**
> - 我們的工作分成十個步驟：**界定範圍 → 資料排列 → 寫 kernel → 驗證 → host → HBM 設定 → Makefile → 真實資料 → 上 server 除錯 → 讀報告**。
> - 每一步都說明：**為什麼做、怎麼做、有什麼效果、產生了什麼檔案**。
> - 最後有一張所有檔案的總表。

---

## 3.1 全景圖

```
 ┌───────────────────────────── 在任何電腦上都能做 ─────────────────────────────┐
 │                                                                              │
 │ [1] 界定範圍 ──► [2] 資料排列與算式 ──► [3] 寫 5 個 kernel（C++）            │
 │                                               │                              │
 │                                               ▼                              │
 │                    [4] C 模擬驗證（g++，make csim）──► ALL PASS              │
 │                                                                              │
 │ [8] 真實資料管線（Python + ESMFold，需要 GPU）── 加分項                      │
 └──────────────────────────────────────────────────────────────────────────────┘
                                        │
 ┌─────────────────── 需要 Vitis（你們的 server63 上可以做） ───────────────────┐
 │                                                                              │
 │ [9] 上 server、修 2025.2 相容問題 ──► [10] HLS 合成（make hls）──► 報告      │
 │                                                                              │
 └──────────────────────────────────────────────────────────────────────────────┘
                                        │
 ┌─────────────── 需要 U55C 卡 + XRT + platform（尚未找到機器） ────────────────┐
 │                                                                              │
 │ [5] host 程式 ＋ [6] HBM 設定 ＋ [7] Makefile ──► v++ 編譯 ──► 上板量測      │
 │     （程式已寫好，尚未實際執行）                                             │
 └──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.2 步驟一：界定範圍

### 為什麼做
LightNobel 處理的是整個 PPM，還設計了專用硬體。專題要求「用常見手法比較」，
所以要從中挑出**一個能代表問題、又做得完**的小範圍。

### 怎麼決定
| 考量 | Triangle Multiplication 的情況 |
|---|---|
| 能代表問題嗎？ | ✅ 直接處理 L×L×128 的 pair representation |
| 算式簡單、容易驗證嗎？ | ✅ 本質是 128 個矩陣乘法 |
| 能展示多種記憶體手法嗎？ | ✅ tiling、寬位元、重疊、多通道、量化都適用 |
| 能呼應 LightNobel 嗎？ | ✅ 可以比較 per-token vs per-tensor 量化 |

### 產出
一句話的題目定義（見第 1 章 1.7 節），以及「只做 einsum 核心，不含 LayerNorm/gating」的範圍界定。

---

## 3.3 步驟二：資料排列（memory layout）與算式

### 為什麼做
資料在記憶體中怎麼排，決定了能不能做 **burst**（連續讀取，見第 2 章 2.5 節）。

### 我們的選擇
```
a、b、z 都是 L × L × C，排成 [row][col][channel]：
index = (row × L + col) × C + c

記憶體中的樣子（C = 128）：
┌───────────────────┬───────────────────┬─────┬─────────────────────┬─────
│ (0,0) 的 128 個數 │ (0,1) 的 128 個數 │ ... │ (0,L-1) 的 128 個數 │ (1,0) ...
└───────────────────┴───────────────────┴─────┴─────────────────────┴─────
  ↑ 同一個 token 的 128 個 channel 是連續的 → 可以一次 burst 讀完
```

### 效果
- 每個 token 的 128 個 float = 512 bytes = **剛好 8 個 512-bit word**，完美對齊寬位元傳輸。
- 這也是 PyTorch 中 ESMFold 的預設排列（最後一維是 channel），所以從 Python 擷取的資料可以**直接使用，不用轉換**。

### 產出
`fpga/trimul/kernels/trimul.h`：定義 `C = 128`、tile 大小、`f16`（16 個 float 的 struct）、`q64`（64 個 int8 的 struct）等共用設定。

---

## 3.4 步驟三：寫 5 個 kernel

以下擷取每個版本最關鍵的部分，完整程式碼在 `fpga/trimul/kernels/`。

### v0：最直白的寫法（`trimul_v0.cpp`）
```cpp
for (int i = 0; i < L; i++)
  for (int j = 0; j < L; j++)
    for (int c = 0; c < C; c++) {
      float acc = 0.0f;
      for (int k = 0; k < L; k++) {
#pragma HLS PIPELINE
        acc += a[(i * L + k) * C + c] * b[(j * L + k) * C + c];   // 每次都讀 HBM
      }
      z[(i * L + j) * C + c] = acc;
    }
```
**問題在哪：**
1. 每次乘加都從 HBM 讀兩個數，完全沒有重用。
2. 最內層的 k 每次跳 C 個位置（stride = 128），無法 burst。
3. `acc += ...` 下一次要等上一次加完（浮點加法需要好幾個 cycle），pipeline 無法每 cycle 開始一次。

### v1：Tiling（`trimul_v1.cpp`）
```cpp
float acc[TI][TJ][C];          // 累加器留在晶片內（BRAM）
float la[TI][C], lb[TJ][C];    // 本輪用到的 a、b

for (i0 ...; i0 += TI)                    // 一次處理 TI 列
  for (j0 ...; j0 += TJ) {                // 和 TJ 行
    acc = 0
    for (int k = 0; k < L; k++) {
      load_a: la[ii][c] = a[((i0 + ii) * L + k) * C + c];    // 搬 TI×C 個（連續）
      load_b: lb[jj][c] = b[((j0 + jj) * L + k) * C + c];    // 搬 TJ×C 個（連續）
      mac:    acc[ii][jj][c] += la[ii][c] * lb[jj][c];       // TI×TJ×C 次乘加
    }
    store: z[...] = acc[ii][jj][c];
  }
```
**改善：** 每個 `la` 用 TJ 次、每個 `lb` 用 TI 次（搬運量減 8 倍）；每次載入 C 個連續的數（可以 burst）。

**一個細節：** `mac` 迴圈裡加了
```cpp
#pragma HLS DEPENDENCE variable = acc inter false
```
意思是告訴 HLS：「同一個 `acc` 位置要隔 TI×TJ×C = 8192 次迭代才會再被更新，不用擔心前後相依」，
這樣 HLS 才敢讓迴圈每個 cycle 開始一次新的迭代（II = 1）。

### v2：寬位元＋16 路平行（`trimul_v2.cpp`）
```cpp
struct f16 { float v[16]; };     // 一個 512-bit word

float acc[TI * TJ * CW][LANES];  // LANES = 16，CW = C/16 = 8
#pragma HLS ARRAY_PARTITION variable = acc dim = 2 complete   // 16 個 lane 拆開成獨立的記憶體

mac:
for (int r = 0; r < TI * TJ * CW; r++) {       // 512 次
#pragma HLS PIPELINE II = 1
  for (int l = 0; l < LANES; l++)              // 這層會被完全展開 → 16 個乘加器同時做
    acc[r][l] += la[...][l] * lb[...][l];
}
```
**改善：**
- 介面從 `float*` 改成 `f16*` → 每次讀 512 bit（16 個 float）。
- `ARRAY_PARTITION` 把 16 個 lane 拆到不同的記憶體區塊，才能**同一個 cycle 讀寫 16 個數**。
- 內層 `for l` 在 PIPELINE 裡會被自動展開成 16 份硬體。

### v3：Double buffering（`trimul_v3.cpp`）
```cpp
float la0[...], lb0[...];   // 第一組 buffer
float la1[...], lb1[...];   // 第二組 buffer

load_ab(k = 0 → la0, lb0);
for (int k = 0; k < L; k++) {
  if (k % 2 == 0) {
    if (k + 1 < L) load_ab(k + 1 → la1, lb1);   // 搬下一批到 buffer 1
    mac(la0, lb0, acc);                          // 同時用 buffer 0 計算
  } else {
    if (k + 1 < L) load_ab(k + 1 → la0, lb0);   // 搬下一批到 buffer 0
    mac(la1, lb1, acc);                          // 同時用 buffer 1 計算
  }
}
```
**關鍵：** `load_ab` 和 `mac` 是兩個獨立的函式（`#pragma HLS INLINE off`），而且使用**不同的 buffer**、
彼此沒有資料相依，所以 HLS 可以讓它們**同時執行**。

### v4：INT8 per-token 量化（`trimul_v4.cpp`）
```cpp
struct q64 { int8_t v[64]; };    // 一個 512-bit word = 64 個 int8

// 每個 token 有自己的 scale：sa[i*L + k]、sb[j*L + k]
mac:
for (int r = 0; r < TI * TJ * QW; r++) {
#pragma HLS PIPELINE II = 1
  float s = lsa[ii] * lsb[jj];                          // 兩個 token 的 scale 相乘
  for (int l = 0; l < 64; l++) {                        // 64 路平行
    int16_t p = (int16_t)la[..][l] * (int16_t)lb[..][l];  // int8 × int8 → int16
    acc[r][l] += (float)p * s;                          // 還原尺度後累加
  }
}
```
**改善：** 每次搬 64 個數（FP32 時只有 16 個），搬運量變 1/4。
**為什麼 scale 不能提到迴圈外：** 每個 k 的 token 不同，scale 也不同，所以每次都要乘。
（如果改成 per-channel 量化，scale 就能提到外面，用純整數累加，但就不是 token-wise 了。）

### 產出
`kernels/trimul_v0.cpp` ～ `trimul_v4.cpp`，以及共用的 `trimul.h`。

---

## 3.5 步驟四：正確性驗證（C 模擬）

### 為什麼做
上板編譯一次要 1～數小時。**先用幾秒鐘確認程式算得對**，才不會浪費時間。

### 怎麼做（`tb/tb.cpp`）
1. 產生隨機資料 `a`、`b`（`host/common.h` 的 `make_activation`）：
   - 一般 token：常態分布 N(0, 1)
   - **1% 的 token 放大 30 倍**：模擬真實 activation 中的 outlier
2. 依序呼叫 v0～v4，把結果和 CPU 用 double 精度算出的正確答案比較。
3. 印出兩種誤差：
   ```
   rel_l2  = ‖z − z_ref‖ ÷ ‖z_ref‖     （整體相對誤差）
   max_abs = max |z − z_ref|             （最大的單點誤差）
   ```
4. v0～v3 要求 rel_l2 < 1e-5（只有浮點誤差）；v4 允許較大誤差（量化本來就有誤差）。

### 結果
```
v0 naive                     rel_l2=1.141e-07   PASS
v1 tiled                     rel_l2=1.141e-07   PASS
v2 tiled+wide                rel_l2=1.141e-07   PASS
v3 tiled+wide+pingpong       rel_l2=1.141e-07   PASS
v4 int8 per-token            rel_l2=9.871e-03   PASS    ← 約 1%
v4 int8 per-tensor           rel_l2=1.126e-01   PASS    ← 約 11%
```
- v0～v3 的誤差完全一樣（1.1e-7），代表**改寫沒有改變計算結果**。
- **per-tensor 誤差約是 per-token 的 11 倍**，這是本專題第一個可以放進報告的結論。

### 為什麼 g++ 能跑 HLS 程式？
因為 kernel 就是**普通的 C++**。`#pragma HLS ...` 對 g++ 來說是不認識的指示，會被忽略
（我們加了 `-Wno-unknown-pragmas` 讓它不要警告）。詳見第 4 章 4.4 節。

### 產出
`tb/tb.cpp`、`host/common.h`；指令 `make csim`。

---

## 3.6 步驟五：host 程式

### 為什麼做
FPGA 不會自己去拿資料。需要一個在 CPU 上執行的程式負責：
**準備資料 → 送進 FPGA 的 HBM → 啟動 kernel → 等它算完 → 取回結果 → 檢查、計時**。

### 流程（`host/host.cpp`，使用 XRT 的 C++ API）
```cpp
xrt::device dev(0);                              // 1. 打開第 0 張 FPGA 卡
auto uuid = dev.load_xclbin("trimul_v2.xclbin"); // 2. 把編譯好的電路燒進去
xrt::kernel krnl(dev, uuid, "trimul_v2");        // 3. 找到 kernel

xrt::bo bo_a(dev, bytes, krnl.group_id(0));      // 4. 在 HBM 上配置記憶體
bo_a.write(a.data());                            //    （group_id 決定放在哪個 PC）
bo_a.sync(XCL_BO_SYNC_BO_TO_DEVICE);             // 5. 從 CPU 記憶體複製到 HBM

run.start(); run.wait();                         // 6. 啟動 kernel 並等待完成（計時）

bo_z.sync(XCL_BO_SYNC_BO_FROM_DEVICE);           // 7. 把結果複製回 CPU
bo_z.read(z.data());
```
最後印出時間、GFLOP/s、估計的搬運量和頻寬、HBM 佔用量、誤差，以及一行 CSV 方便整理。

### 狀態
⚠️ 已寫好，並用假的 XRT header 確認**可以編譯**，但**尚未在真的板子上執行過**。

### 產出
`host/host.cpp`；指令 `make host`、`make run`。

---

## 3.7 步驟六：HBM 連接設定

### 為什麼做
kernel 有好幾個 AXI 連接埠（a、b、z……），每個要接到 HBM 的哪個 pseudo-channel，
是在**連結（link）階段**由設定檔決定的。

### 設定檔（`cfg/trimul_v2.cfg`）
```ini
[connectivity]
sp=trimul_v2_1.a:HBM[0:7]      # a 接到 PC 0～7（共 4 GB）
sp=trimul_v2_1.b:HBM[8:15]     # b 接到 PC 8～15
sp=trimul_v2_1.z:HBM[16:23]    # z 接到 PC 16～23
```
- `trimul_v2_1`：kernel 的第一個實例（instance）。
- `sp`：system port，指定「kernel 的某個參數要接到哪塊記憶體」。
- 對照組 `trimul_v2_onebank.cfg`：全部接到 `HBM[0]`。

### 產出
`cfg/trimul_v0.cfg` ～ `trimul_v4.cfg`、`trimul_v2_onebank.cfg`。

---

## 3.8 步驟七：Makefile

### 為什麼做
完整流程有很多步驟、每個指令都很長。Makefile 把它們包成短指令，參數也集中管理。

### 指令一覽
| 指令 | 做什麼 | 需要什麼 |
|---|---|---|
| `make csim` | g++ 編譯並執行 testbench | 只要 g++ |
| `make hls KERNEL=trimul_v2` | 執行 `hls/run_hls.tcl`，產生合成報告 | Vitis |
| `make hls-all` | 依序合成 v0～v4，最後呼叫 `make summary` | Vitis |
| `make summary` | 執行 `scripts/hls_summary.py`，產生比較表與 `hls_summary.csv` | Python |
| `make xclbin KERNEL=... TARGET=hw` | `v++ -c`（編譯）＋ `v++ -l`（連結）→ `.xclbin` | Vitis ＋ U55C platform |
| `make host` | 編譯 host 程式 | XRT |
| `make run ...` | 執行（emulation 或上板） | XRT（上板還需要卡） |

### 可調參數
`KERNEL`、`TARGET`（sw_emu / hw_emu / hw）、`PLATFORM`、`CFG`、`DEFS`（例如 tile 大小）、`TAG`、`RUN_L`、`DATA`。

### 產出
`Makefile`、`hls/run_hls.tcl`、`scripts/hls_summary.py`、`.gitignore`。

---

## 3.9 步驟八：真實資料管線（加分項）

### 為什麼做
模擬資料的 outlier 是我們「假設」的。要證明結論在**真實蛋白質**上也成立，需要從 ESMFold 取出真正的 activation。

### 怎麼做（`python/dump_trimul_inputs.py`）
1. 下載序列（UniProt / PDB）或讀 FASTA。
2. 載入 HuggingFace 的 ESMFold（`facebook/esmfold_v1`）。
3. **把 `trunk.blocks[N].tri_mul_out._combine_projections` 換成我們的函式**：
   當模型執行到這裡時，把 `a`、`b` 存下來，然後丟出例外讓模型停止（後面的 block 不用跑，省時間）。
4. 計算 outlier 程度、per-token / per-tensor 的量化誤差。
5. 補零到 32 的倍數，存成 `a.bin`、`b.bin`（float32，排列和 kernel 相同）。

### 驗證：「差值 0」是怎麼來的
在隨機初始化的小型 ESMFold 上，擷取 `a`、`b` 後比較：
```python
ref  = tm._combine_projections(a, b)          # ESMFold 自己的計算
ours = torch.einsum("ikc,jkc->ijc", a, b)     # 我們 kernel 的算式
max diff = 0.0
```
**證明我們的 kernel 算的確實是 ESMFold 裡的那個運算。**

### 過程中發現的錯誤
一開始用 tokenizer 產生輸入，結果模型報錯（index out of range）。原因是 ESMFold 的 `forward` 需要的是
**AlphaFold 的胺基酸編號**，不是語言模型 tokenizer 的編號；要用 `model.infer(seq)` 才會正確轉換。

### 狀態
需要 GPU（或 Colab）才能跑正式模型；使用者沒有 GPU，所以目前是**加分項**。
C 模擬、host 程式和 Makefile 都已支援讀取這些檔案（`DATA=...`）。

### 產出
`python/dump_trimul_inputs.py`、`python/requirements.txt`、`docs/real_protein_data.md`。

---

## 3.10 步驟九：在實際 server 上除錯

### 環境調查
| 指令 | 結果 | 結論 |
|---|---|---|
| `which vivado vitis v++` | 都在 `/tools/Xilinx/2025.2/` | 工具齊全，版本很新 |
| `which vitis_hls` | 找不到 | 2025.2 已移除，改用 `vitis-run` |
| `lspci -d 10ee:` | 空的 | **這台沒有 FPGA 卡**（10ee 是 Xilinx 的廠商代號） |
| `xbutil`、`/opt/xilinx/platforms` | 沒有 | 沒有 XRT、沒有 U55C platform |

→ 這台可以做 C 模擬和 HLS 合成，**不能上板**。

### 除錯過程：一次失敗、三次修正
這是一個很好的除錯範例，展示「**從錯誤訊息推理出原因**」的過程。

**第 1 次失敗**
```
ld.lld: error: undefined symbol: trimul_v2
```
- 觀察：編譯清單裡有 tb、v0、v1、v3、v4，**唯獨沒有 v2**。
- 當時的判斷：2025.2 的 C 模擬流程有問題 → 改成預設跳過 HLS 內建的 C 模擬（反正 `make csim` 已經驗證過）。
- （後來發現真正原因和第 2、3 次相同。）

**第 2 次失敗**
```
WARNING: Cannot find source file ../kernels/trimul_v2.cpp; skipping it.
ERROR: Cannot find any design unit to elaborate.
```
- 觀察：工具找不到來源檔。
- 假設：相對路徑的問題 → 改用**絕對路徑**。

**第 3 次失敗（相同錯誤）**
- 關鍵觀察：日誌中 `Adding design file '/home/anthony/.../trimul_v2.cpp'` 已經是絕對路徑，
  但到了合成階段，工具**又自己改寫成 `../kernels/trimul_v2.cpp`**。
- 推理：
  ```
  專案位置：   fpga/trimul/hls_prj/trimul_v2/     （在目前資料夾往下 2 層）
  正確的相對路徑：../../kernels/trimul_v2.cpp
  工具算出來的：  ../kernels/trimul_v2.cpp        （只往上 1 層）
  ```
  → 工具**假設專案只在目前資料夾的下一層**。專案名稱含有 `/`（`hls_prj/trimul_v2`）時就會算錯。
- 修正：先 `cd hls_prj`，再建立名為 `trimul_v2` 的專案（只差一層）。

**第 4 次：成功** ✅

### 學到的除錯方法
1. **仔細看完整的錯誤訊息**，不只看 ERROR，也看前面的 WARNING。
2. **比較「預期」和「實際」**（編譯清單少了一個檔案、路徑少了一層）。
3. 修正後結果不變 → **假設錯了**，回頭找新的線索。
4. 用算的驗證假設（數路徑的層數）。

### 產出
修改過的 `Makefile`（自動選 `vitis_hls` 或 `vitis-run`）與 `hls/run_hls.tcl`。

---

## 3.11 步驟十：讀懂 HLS 報告（以 v2 為例）

報告位置：`hls_prj/trimul_v2/sol/syn/report/trimul_v2_csynth.rpt`

### ① 基本資訊
```
* Version:        2025.2
* Solution:       sol (Vitis Kernel Flow Target)
* Product family: virtexuplusHBM
* Target device:  xcu55c-fsvh2892-2L-e     ← U55C 的晶片型號
```

### ② Timing（時脈）
```
| Clock  | Target  | Estimated | Uncertainty |
| ap_clk | 3.33 ns | 2.431 ns  | 0.90 ns     |
```
| 欄位 | 意義 |
|---|---|
| Target | 我們要求的時脈週期（3.33 ns = 300 MHz） |
| Estimated | HLS 估計電路最慢的路徑需要多久 |
| Uncertainty | 保留給後續繞線的餘裕 |

**判斷：** Estimated + Uncertainty = 3.33 ns，剛好在目標內 → 通過。
（最終能否達到 300 MHz，要等 Vivado 實際繞線後才知道。）

### ③ Latency（總時間）
```
| Latency (cycles) | Latency (absolute) | Interval  |
| 177,029,185      | 0.590 sec          | 177029186 |
```
- **Latency**：從開始到結束的 cycle 數。
- **absolute**：cycle 數 × 時脈週期。
- **Interval**：可以接受下一次呼叫的間隔（這裡和 latency 差不多，因為一次只跑一個）。
- ⚠️ 這是在 **L = 256** 下的估計（由 `trimul.h` 的 `L_TRIP` 決定）。因為 L 是執行時才知道的參數，
  HLS 需要 `LOOP_TRIPCOUNT` 告訴它迴圈大概跑幾次，才能估算。

### ④ Instance（子模組）
```
| Module                     | Latency (cycles) |
| trimul_v2_Pipeline_init    | 514 |   ← 清空累加器（512 次 + 啟動）
| trimul_v2_Pipeline_load_a  | 141 |   ← 載入 a
| trimul_v2_Pipeline_load_b  | 141 |   ← 載入 b
| trimul_v2_Pipeline_store   | 586 |   ← 寫回結果
| trimul_v2_Pipeline_mac     | 526 |   ← 計算（512 次 + pipeline 深度 14）
```
每個 pipeline 化的迴圈會變成一個獨立的硬體模組。

### ⑤ Loop（迴圈）
```
| Loop Name  | Latency     | Iteration Latency | Trip Count |
| tile_i     | 177,029,184 | 5,532,162         | 32 |
|  tile_j    | 5,532,160   | 172,880           | 32 |
|   loop_k   | 171,776     | 671               | 256 |
```
**驗算：**
```
loop_k：256 次 × 671 = 171,776                          ✓
tile_j 每次：171,776（loop_k）+ 514（init）+ 586（store）+ 4 ≈ 172,880   ✓
tile_i 每次：32 × 172,880 + 2 = 5,532,162                ✓
總計：32 × 5,532,162 ≈ 177,029,184                       ✓
```
**`loop_k` 的 671 cycles** 就是第 2 章 2.6 節分析 double buffering 的依據：
`load（141，a、b 並行）+ mac（526）+ 少量 ≈ 671`。

### ⑥ 換算效能
```
運算量 = 2 × 256³ × 128 ≈ 4.29 × 10⁹ FLOP
時間   = 0.590 s
效能   ≈ 7.3 GFLOP/s          （v2 理論上限 9.6 GFLOP/s 的 76%）
```

### ⑦ 資源用量（報告的下一段，尚未截圖）
`Utilization Estimates` 段落會列出 BRAM_18K、DSP、FF、LUT、URAM 的用量和百分比。
`make summary` 會自動把這些數字整理進比較表。

---

## 3.12 所有檔案總表

| 檔案 | 用途 | 狀態 |
|---|---|---|
| `README.md` | repo 目錄 | ✅ |
| `docs/PROJECT_LOG.md` | 專題工作紀錄（交接用） | ✅ |
| `docs/conversation_notes.md` | 白話筆記 | ✅ |
| `docs/getting_started_u55c.md` | U55C 環境與開發流程 | ✅ |
| `docs/real_protein_data.md` | 真實資料流程 | ✅ |
| `docs/manual/` | 本教學手冊（含 `manual.pdf`） | ✅ |
| `fpga/trimul/kernels/trimul.h` | 共用設定 | ✅ |
| `fpga/trimul/kernels/trimul_v0~v4.cpp` | 5 個 kernel | ✅ csim；v2 已合成 |
| `fpga/trimul/tb/tb.cpp` | C 模擬 testbench | ✅ |
| `fpga/trimul/host/common.h` | 資料產生、量化、參考答案、讀檔 | ✅ |
| `fpga/trimul/host/host.cpp` | XRT host 程式 | ⚠️ 未上板 |
| `fpga/trimul/cfg/*.cfg` | HBM 連接 | ⚠️ 未使用 |
| `fpga/trimul/hls/run_hls.tcl` | HLS 腳本 | ✅（2025.2） |
| `fpga/trimul/scripts/hls_summary.py` | 報告整理成表 | ✅（用假報告測過） |
| `fpga/trimul/Makefile` | 指令捷徑 | ✅ csim/hls；⚠️ xclbin/run |
| `python/dump_trimul_inputs.py` | 擷取真實 activation | ✅（小模型測過） |

執行後會產生（不進 git）：`hls_prj/`（HLS 專案與報告）、`hls_*.log`、`hls_summary.csv`、`build/`（v++ 產物）、`*.exe`。

---

## 本章小結

- 流程的核心精神：**從快到慢驗證**（C 模擬 → HLS → emulation → 上板），前一步沒過就不進下一步。
- 每個 kernel 版本只改一件事，才能清楚歸因每一招的效果。
- 除錯時，**比較預期與實際、修正無效就換假設**。
- 目前進度：C 模擬全部通過、v2 合成成功，正在跑 v0～v4 全部合成；上板部分尚待找到有 U55C 的機器。

**下一章**解釋這些工具背後的原理：為什麼 C++ 可以變成電路、每個工具實際做了什麼、這些能力從哪裡來。
