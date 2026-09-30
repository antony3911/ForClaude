# LightNobel 與 FPGA Triangle Multiplication Kernel：技術摘要

本文整理三部分內容：（1）LightNobel（Han、Choi、Kim，ISCA 2025，arXiv 2505.05893）的運作方式，這是一個針對蛋白質結構預測模型（PPM）的軟硬體協同設計加速器；（2）我們在 AMD Alveo U55C 上實作的 Triangle Multiplication einsum，版本 v0～v3；（3）用來評估它們的分析方法。標示 *（我們的解讀）* 的內容，論文中沒有明確寫出。

## 1. 背景：ESMFold 與 Pair Representation

### 1.1 整體流程

LightNobel 的基準模型是 ESMFold。它從長度為 L 的胺基酸序列預測 3D 結構，分為三個階段：

| 階段 | 功能 | 主要資料 |
|---|---|---|
| Input embedding | ESM-2（3B）蛋白質語言模型 | sequence representation `s`：L × 1024 |
| Folding trunk | 48 個 Protein Folding Block，最多 4 次 recycling | `s` 與 pair representation `z`：L × L × 128 |
| Structure module | 預測原子座標；distogram head 由 `z` 產生 | 3D 結構 |

`z` 的每個元素 `z[i][j]`（pair representation 的一個 *token*）是一個 128 channel 的向量，描述胺基酸 i 與 j 之間的關係。每個 block 以 residual 的方式更新狀態（`z ← z + Δz`），依序為：sequence attention、sequence transition、sequence-to-pair projection、Triangle Multiplication（outgoing）、Triangle Multiplication（incoming）、Triangle Attention（starting node）、Triangle Attention（ending node）、pair transition。

### 1.2 Triangle Multiplication

以 outgoing 版本為例，channel 維度 C = 128，更新如下：

```
z_ln  = LayerNorm_in(z)
a     = mask ⊙ sigmoid(W_ag · z_ln) ⊙ (W_ap · z_ln)          （逐 token，128 → 128）
b     = mask ⊙ sigmoid(W_bg · z_ln) ⊙ (W_bp · z_ln)
x[i][j][c] = Σ_k  a[i][k][c] · b[j][k][c]                     （einsum "ikc,jkc->ijc"）
g     = sigmoid(W_g · z_ln)
Δz    = g ⊙ (W_z · LayerNorm_out(x))
```

除了 einsum，所有運算都是 token-local 的：每個 token 只用到自己的 128 個值和權重。einsum 是唯一跨 token 的運算。對每個 channel c，它是一個 L × L 的矩陣乘法 `x_c = a_c · b_cᵀ`；128 個 channel 彼此獨立（batched matrix multiplication）。incoming 版本計算 `x[i][j][c] = Σ_k a[k][i][c] · b[k][j][c]`，即 `a_cᵀ · b_c`。

每個輸出 token 中，einsum 需要 2·L·C 次運算（L = 1,000 時為 256,000 次），六個 128 × 128 的 linear 層需要 6 · 2 · C² = 196,608 次。因此 L 增大時，einsum 會成為 TriMul 運算量的主體。

一次 Triangle Multiplication 中各類運算（以每個輸出 token 計）：

| 運算 | 類型 | 每個 token 的運算量 | 資料相依性 |
|---|---|---|---|
| LayerNorm_in、LayerNorm_out | 正規化（對 128 個 channel 做歸約） | O(C) | token-local |
| 6 個 linear 層（128 × 128） | 矩陣–向量乘法 | 6 · 2C² = 196,608 | token-local，共用權重 |
| sigmoid、gating、mask | 逐元素運算 | O(C) | token-local |
| einsum | batched 矩陣乘法 | 2 · L · C | 讀取 `a` 的第 i 列與 `b` 的第 j 列 |

### 1.3 Triangle Attention 與成長規模

Triangle Attention 沿著 `z` 的列（或欄）做 attention。它的 attention logits 每個 head 的形狀是 L × L × L，因此隨 L 立方成長；其他 pair representation 的張量則是平方成長。以 starting-node 版本為例，H = 4 個 head、每個 head 維度 32：

```
x    = LayerNorm(z)
q, k, v = W_q x, W_k x, W_v x                  （逐 token，分成 H 個 head）
β[h][j][k] = (W_β x)[j][k][h]                   （pair bias）
s[i][h][j][k] = q[i][j][h] · k[i][k][h] / √32 + β[h][j][k]
o[i][j][h] = Σ_k softmax_k(s[i][h][j][·]) · v[i][k][h]
```

ending-node 版本對 `z` 的轉置做相同的計算。

| 張量 | 形狀 | 成長 |
|---|---|---|
| Sequence representation | L × 1024 | O(L) |
| Pair representation 與 TriMul 中間值 | L × L × 128 | O(L²) |
| Triangle Attention logits（每個 head） | L × L × L | O(L³) |

LightNobel 論文指出，L = 2,034 時 activation 已經是權重的 24.15 倍，需要 144 GB，超過單張 GPU 的容量。論文在 H100、不分塊（no chunking）下的執行時間分布（Fig. 3）顯示了瓶頸的轉移：

| 佔總執行時間 | 短蛋白質（R0271） | 長蛋白質（T1269） |
|---|---|---|
| Protein Folding Block | 83.8% | 94.5% |
| Pair representation 資料流 | 69.4% | 91.9% |
| Triangle Multiplication | 36.1% | 14.5% |
| Triangle Attention | 29.0% | 75.9% |

## 2. LightNobel

### 2.1 概述

LightNobel 只加速 Protein Folding Block；ESM-2 與 structure module 不在加速器上執行。設計建立在四個觀察上：

1. 序列很長時，執行時間集中在 pair representation 資料流，其中又以 Triangle Attention 最重。
2. 記憶體用量主要來自 activation，而非權重。
3. 同一個 token 的各 channel 數值差異小，但 token 之間差異大，且 outlier 集中在特定 token（與 distogram 的模式相關）。因此以 token 為單位量化比以 channel 為單位更合適。
4. block 中不同位置的 activation 統計特性不同（例如 residual 路徑上 LayerNorm 之前的平均絕對值約 82，其他位置約 4）。

主要貢獻有三：軟體層面的 Token-wise Adaptive Activation Quantization（AAQ）；硬體層面的 Reconfigurable Matrix Processing Unit（RMPU）、Versatile Vector Processing Unit（VVPU）與 Token Aligner；以及不存放大型中間值（包括 L³ 的 attention logits）的 token-wise 資料流。

### 2.2 Token-wise Adaptive Activation Quantization（AAQ）

每個 token t 以自己的 scale 做對稱量化：

```
s_t   = max_c |x_t[c]| / (2^(b−1) − 1)          （b = 4 或 8）
q_t[c] = round(x_t[c] / s_t)
x̂_t[c] = s_t · q_t[c]
```

outlier 是每個 token 中絕對值最大的 k 個值。它們在執行時以 top-k 運算挑出，以 INT16 保留原始精度；其餘的值（inlier）則被量化。activation 依其在 block 中的位置分為三組：

| 組別 | 對應的 activation | 平均絕對值 | 每個 token 平均 outlier 數 | 格式 |
|---|---|---|---|---|
| A | LayerNorm 之前、residual 路徑上 | 82.14 | 2.31 | INT8 inlier ＋ 4 個 INT16 outlier |
| B | LayerNorm 之後、linear 層之前 | 4.05 | 1.69 | INT4 inlier ＋ 4 個 INT16 outlier |
| C | 其餘 activation（例如 linear 的輸出） | 3.85 | 0.64 | INT4，不處理 outlier |

其他設計要點：

- 權重不量化，以 INT16 儲存。基準（ESMFold）的權重與 activation 皆為 FP16。
- 採用對稱量化，因為在處理 outlier 的前提下，其 RMSE 只比非對稱量化高 9.76%（不處理 outlier 時高 27.35%），而且硬體成本較低。
- 各組設定透過設計空間探索（精度 × outlier 數）選出，以 TM-score 與資料大小評估。未採用的選項包括：A 組用 INT4（需 32 個以上 outlier 才能維持精度）、A 組 outlier 少於 4 個（TM-score 下降）、B 組用 INT8（精度足夠但資料較大），以及 channel-wise 或 tensor-wise 粒度。
- 每個 token 的儲存格式依序為：inlier、outlier、scale、outlier 位置。多個 token 打包成 block，block 大小依記憶體通道頻寬決定；各組壓縮後的 token 長度不同。

在 Triangle Multiplication 中，`z` 屬於 A 組，`z_ln` 屬於 B 組，`a`、`b` 屬於 C 組（INT4）。

### 2.3 架構與執行模型

```
        External memory（80 GB HBM2E，2 TB/s）
               |                         ^
         Token Aligner             Output Scratchpad（128 KB）
               |                         ^
   Token Scratchpad（128 KB × 2）  Weight Scratchpad（64 KB）
               |                         |
   ======== Global Crossbar Network（GCN）================
               |                         |
        RMPU × 32  ------------->  每個 RMPU 配 4 個 VVPU（共 128 個）
        （矩陣運算）               （向量運算、量化）
   Controller：產生所有單元的控制訊號
```

這些單元是分時共用的，而不是針對某一層焊死的固定管線：

- RMPU 執行所有矩陣類運算：linear 層、TriMul 的 einsum、Q·Kᵀ 與 attention·V。
- VVPU 執行逐元素與向量運算：LayerNorm、sigmoid、gating、residual 相加、softmax，以及執行時量化。
- GCN 讓資料以任意順序在單元之間傳遞（例如 VVPU → RMPU → VVPU）。

模型的一層由數趟（pass）計算組成：

1. **讀入**：Token Aligner 從 HBM 讀入一批打包好的 token，解碼後以一個 token 一行的方式寫入 scratchpad。Token Scratchpad 採 double buffering，處理目前這批的同時載入下一批。
2. **權重**：這一趟用到的權重固定放在 Weight Scratchpad。
3. **運算**：VVPU 先做需要的前處理（例如 LayerNorm），RMPU 一次對最多 20 個 token 做矩陣運算，結果直接以管線送進 VVPU，做後處理與執行時量化。
4. **寫回**：量化後的 token 經 Output Scratchpad 寫回。

延遲由最慢的管線階段（RMPU、VVPU 或記憶體）決定。

採用 weight-stationary 資料流，是因為一個 128 × 128 的 INT16 權重矩陣只有 32 KB，卻會被最多 L² 個 token 重複使用。

### 2.4 RMPU：位元拆解的多精度矩陣單元

如果 INT4、INT8、INT16 各配一套專用乘法器，運算元精度混用時，用不到的那幾套就會閒置。RMPU 改為只用一種小乘法器（沿用 Bit Fusion 的做法），把數字拆成 4-bit 的小塊，再組合出較大的乘積：

```
A = Σ_i a_i · 2^(4i),  B = Σ_j b_j · 2^(4j)
A · B = Σ_i Σ_j (a_i · b_j) · 2^(4(i+j))
```

移位不需要乘法器。INT4 × INT16 需要 4 次小塊乘法，INT8 × INT16 需要 8 次，INT16 × INT16 需要 16 次。

在二補數表示中，只有最高位的小塊帶正負號，較低的小塊都是無號數。Reconfigurable Data Aligner（RDA）對最高位小塊做 sign extension、其他小塊補 0，都擴充成 5 bit。擴充後所有小塊都落在同一種 5-bit 有號格式內（−16～15），因此乘法器的輸入為 5-bit 有號數，只需一種乘法器就能處理所有小塊。

階層結構：

| 層級 | 組成 | 乘法器數 |
|---|---|---|
| PE | 16 個乘法器 ＋ 移位器 ＋ 16-to-1 加法樹 | 16 |
| PE Lane | 8 個 PE | 128 |
| PE Cluster | 20 個 PE Lane ＋ Dynamic Accumulation Logic（DAL） | 2,560 |
| RMPU Engine | 4 個 PE Cluster（80 個 lane、640 個 PE） | 10,240 |

一個 C 組 token（128 個 INT4）與 INT16 權重做 128 維內積，需要 128 × 4 = 512 個乘法器（4 個 lane）；B 組 token（124 個 INT4 ＋ 4 個 INT16）需要 124 × 4 ＋ 4 × 16 = 560 個（5 個 lane）。一個 cluster 放 20 個 lane，即 4 與 5 的最小公倍數，兩種情況都能完全用滿（一次 5 個或 4 個 token）。

DAL 負責處理 scale。inlier 的部分和要乘上 token 的 scale，outlier（INT16 原值）的部分和則不乘。4 個 lane 的 token，把各 lane 的和相加後乘一次 scale；5 個 lane 的 token，先把 4 個 inlier lane 相加並乘 scale，再加上 outlier lane。Arbiter 與可重組加法樹在 4-to-1 與 5-to-1 兩種歸約方式之間切換。

加法樹的多個層級都可以取出結果：
- 2 個 PE 的和：attention 中維度 32 的 head
- 4 或 5 個 lane 的和：量化後的 linear 層
- 8 或 16 個 lane 的和：未量化的運算元

### 2.5 VVPU：向量單元與執行時量化

每個 VVPU 包含：

- **128 條 SIMD lane**：每條對應 token 的一個 channel，各有一個 16-bit ALU、本地 scratchpad 與兩級指數查表。
- **Scalar Support Unit（SSU）**：負責歸約與格式處理。
- **Local Crossbar Network（LCN）**：讓 lane 之間交換資料。

top-k 選取使用 bitonic 排序網路。它由固定連線的 compare-and-swap 元件組成，控制與資料無關；128 個值需要 7 · 8 / 2 = 28 級、每級 64 個比較器，求 top-k 時可以提早結束。排序時會追蹤原始位置以記錄 outlier 的位置；k = 1 時得到最大值，用於 softmax 與計算 scale。

執行時量化分四步：（1）以 top-k 挑出 outlier 與 scale；（2）縮放並四捨五入 inlier；（3）由 LCN 重排成儲存格式；（4）由 SSU 做最後的對齊。完整精度的值從不寫回外部記憶體。

論文的設計空間探索（Fig. 12）顯示，延遲在每個 RMPU 配 4 個 VVPU、以及 32 個 RMPU 時達到飽和。超過這兩點後，新增的單元不在關鍵路徑上，或記憶體系統已無法供應更多資料。

### 2.6 Token-wise multi-head attention

為了不存放 L³ 的 logits，LightNobel 以類似 FlashAttention 的方式逐 token 計算 attention。每個 query 的分數分批處理，並維護執行中的統計量：

```
m_new = max(m, max(s))
ℓ     = ℓ · exp(m − m_new) + Σ exp(s − m_new)
o     = o · exp(m − m_new) + Σ exp(s − m_new) · V
m     = m_new
output = o / ℓ
```

硬體上的執行方式：

1. RMPU 對各 head 平行計算 Q·Kᵀ。
2. VVPU 做反量化與累加。
3. 一批的 softmax 與下一批的 Q·Kᵀ 重疊執行。
4. 最後乘上 V，寫回結果。

由於 hidden 維度很小（128），晶片內可同時容納許多 token，使 token-wise 做法在 PPM 上特別有效率。

### 2.7 Triangle Multiplication 的對應方式 *（我們的解讀）*

論文沒有列出每個運算的排程。依照運算間的相依關係與論文描述的硬體能力，TriMul 分三趟執行：

| 趟次 | 範圍 | 運算 |
|---|---|---|
| 1 | token-local，對每個 (i, k) | 讀 `z` → VVPU LayerNorm → RMPU 四個 linear 層 → VVPU sigmoid、gating、mask、INT4 量化 → 寫出 `a`、`b` |
| 2 | 跨 token | 讀 `a`、`b` → RMPU einsum → VVPU 反量化與累加 |
| 3 | token-local，對每個 (i, j) | VVPU LayerNorm_out → RMPU `W_z`、`W_g` → VVPU sigmoid、gating、residual、INT8 ＋ outlier 量化 → 寫出 `z` |

第 1、2 趟之間，`a`、`b` 必須寫回記憶體，因為 einsum 要跨 token 讀取整列資料。

### 2.8 評估方法與結果

論文使用以下工具評估：

- Python cycle-accurate 模擬器，與 RTL 模擬交叉驗證（平均誤差 3.30%，全部在 5% 以內）。
- SystemVerilog RTL，以 Synopsys Design Compiler 在 28 nm、1 GHz 合成。
- CACTI 7.0 與記憶體編譯器估算 SRAM，換算到 28 nm。
- Ramulator 模擬 80 GB HBM2E、2 TB/s。

工作負載為 ESMFold（ESM-2 3B），資料集為 CAMEO、CASP14、CASP15、CASP16，比較對象為 NVIDIA A100 與 H100。

| 指標 | 結果 |
|---|---|
| 精度 | TM-score 變化 < 0.001 |
| 加速 | 最多 8.44×（A100）、8.41×（H100）；與分塊的 GPU 相比為 3.85～8.44× 與 3.67～8.41× |
| 能源效率 | 最多 37.29×（A100）、43.35×（H100） |
| 峰值記憶體 | 比不分塊的 GPU 最多低 120.05×；比分塊的 GPU 低 1.26～5.05× |
| 最長序列 | 80 GB 內可處理 9,945 個胺基酸（CASP16 最長蛋白質 6,879 的 1.45 倍） |
| 面積／功耗 | 178.80 mm²、67.8 W |

面積與功耗（Table 2）以資料搬移為主。crossbar（128 個 LCN ＋ GCN，約 125.7 mm²）佔 70.28% 的面積與 67.95% 的功耗，RMPU Engine 只佔 18.20% 的面積。單一 VVPU 中，LCN（0.785 mm²）約是 128 條 SIMD lane（0.115 mm²）的 7 倍。

記憶體節省來自兩個不同的機制：

- **量化**：資料流不變時，總記憶體從 121.39 GB 降到 73.50 GB（1.65 倍；T1169，3,364 個胺基酸，Table 1）。
- **不存放中間值**：其中又以移除 L³ 的 attention logits 為主，這是相對不分塊的 GPU 能降低 120 倍峰值記憶體的主要原因。

pair representation 仍隨 L² 成長。

### 2.9 相關做法

| 做法 | 代表工作 | 效果 | 限制 |
|---|---|---|---|
| GPU 系統最佳化 | FastFold、ScaleFold | 訓練與推論更快 | 記憶體仍隨 L² 成長 |
| 分塊（chunking） | AlphaFold／ESMFold 的 chunk 選項、AutoChunk | 峰值記憶體降低 | 變慢；資料重複讀取 |
| 模型量化 | MEFold（權重）、PTQ4Protein（per-tensor INT8） | 資料變小 | 只量化權重對 activation 幫助有限；低精度時準確度下降 |
| LLM 量化 | SmoothQuant、LLM.int8()、AWQ | 分離 outlier | inlier 只有單一精度；GPU 上 activation 量化常反而變慢 |
| 融合的 GPU kernel | OpenFold3 融合 TriMul | 中間值不寫回記憶體 | 需手寫 kernel，受限於 GPU 架構 |
| 專用加速器 | LightNobel | 量化、專用單元與 token-wise 資料流 | 以模擬評估，未實際流片 |

## 3. Triangle Multiplication einsum 的 FPGA 實作

### 3.1 平台與 kernel 規格

| 項目 | 內容 |
|---|---|
| 板卡 | AMD Alveo U55C，16 GB HBM2（32 個 pseudo-channel，各約 14 GB/s，總計約 460 GB/s） |
| 工具鏈 | Vitis HLS（C++ → RTL）、Vitis v++ 連結、XRT host |
| Kernel 時脈 | 目標 300 MHz（3.33 ns）；HLS 估計關鍵路徑 2.431 ns |
| 運算 | `z[i][j][c] = Σ_k a[i][k][c] · b[j][k][c]`，C = 128，FP32 |
| 資料排列 | `[row][col][channel]`，索引 `(row · L + col) · C + c`（與 PyTorch 相同） |
| Tile | T_I = T_J = 8 |

在這種排列下，一個 token 的 128 個 channel 是連續的：512 bytes，剛好是 8 個 512-bit word。

U55C 的記憶體階層：

| 層級 | 容量 | 存取延遲 |
|---|---|---|
| Flip-flop | 約 330 KB | 1 cycle |
| BRAM | 4,032 × 18 Kb ≈ 9 MB | 1～2 cycles |
| URAM | 960 × 288 Kb ≈ 35 MB | 1～2 cycles |
| HBM2 | 16 GB（32 × 512 MB） | 數十～上百 cycles |

L = 1,000 時，一份 L × L × 128 的 FP32 張量就佔 512 MB，而晶片內只有約 43 MB，因此 einsum 必須從 HBM 分批串流 tile。

正確性以兩種方式驗證：

- **C 模擬**：testbench 使用隨機 activation，其中 1% 的 token 放大 30 倍，並與 CPU 上的 double 精度參考結果比較。v0～v3 的 rel_l2 皆為 1.141 × 10⁻⁷（結果完全一致）。
- **與 ESMFold 的等價性**：使用 HuggingFace 的 ESMFold 實作，`einsum("ikc,jkc->ijc", a, b)` 與模組內部的計算結果相比，最大絕對誤差為 0。

### 3.2 v0：基準

```c
for i, for j, for c:
    acc = 0
    for k:  acc += a[(i*L + k)*C + c] * b[(j*L + k)*C + c]
    z[(i*L + j)*C + c] = acc
```

每次乘加都從 HBM 讀取兩個運算元，沒有任何晶片內的重用。最內層迴圈遞增 k，每次位址前進 C 個元素，存取模式不連續，HLS 無法推論 burst，每次存取都要付出完整的記憶體延遲。

### 3.3 v1：Loop tiling 與晶片內 buffer

```c
for (i0 = 0; i0 < L; i0 += TI)  for (j0 = 0; j0 < L; j0 += TJ):
    acc[TI][TJ][C] = 0                                   // BRAM，32 KB
    for k:
        load_a: la[ii][c] ← a[((i0+ii)*L + k)*C + c]     // TI 個 token，4 KB
        load_b: lb[jj][c] ← b[((j0+jj)*L + k)*C + c]     // TJ 個 token，4 KB
        mac:    acc[ii][jj][c] += la[ii][c] * lb[jj][c]  // ii、jj、c
    store acc → z
```

- **Tiling 與重用**：把輸出空間切成 T_I × T_J 的 tile，其累加器留在晶片內（output-stationary）。對每個 k，只載入一次 T_I 個 `a` token 與 T_J 個 `b` token，並在 `mac` 迴圈中重複使用：每個 `la` 元素供 T_J 個輸出使用，每個 `lb` 元素供 T_I 個輸出使用。8 × 8 的 tile 讓晶片外讀取量降為 1/8。
- **Burst 推論**：載入迴圈的最內層沿 c 走訪連續位址，使 HLS 能為每個 token 推論出一個 128 拍的 AXI burst；延遲變成每個 token 付一次，而不是每個元素付一次。
- **Pipeline**：所有迴圈都以 II = 1 做 pipeline。`acc` 上的相依性 pragma（`inter false`）告訴 HLS：同一個累加器每 T_I · T_J · C 次迭代才更新一次，因此浮點加法器的延遲不會限制 initiation interval。
- **限制**：仍是 32-bit port，每個 cycle 只有一次乘加。每一輪 k 約需 1,024 ＋ 1,024 ＋ 8,192 個 cycle，以計算為主（估算值）。

### 3.4 v2：寬位元記憶體介面與向量化

v2 把介面、晶片內 buffer 與運算資料路徑同時加寬為 16 lane：

- **介面**：指標型別從 `float*` 改為 16 個 float 組成的 512-bit struct（`f16`），HLS 因此產生 512-bit 的 AXI master port。`a`、`b`、`z` 使用不同的 bundle（gmem0／1／2），形成三個獨立的 port，連接到不同的 HBM pseudo-channel。在 300 MHz 下，每個 port 的頻寬從 1.2 GB/s 提升到 19.2 GB/s。一個 token 變成 8 拍的 burst，多個未完成的請求（outstanding request）讓連續 token 的延遲互相重疊。
- **Buffer**：`la`、`lb`、`acc` 宣告為 `[rows][16]`，並在 lane 維度完全切割（complete partition），每個 cycle 可以讀寫 16 個值。
- **資料路徑**：pipeline 化的 `mac` 迴圈中，lane 迴圈被完全展開成 16 組平行的浮點乘加單元（峰值 16 × 2 × 300 MHz = 9.6 GFLOP/s）。

HLS 報告（L = 256，T_I = T_J = 8）：

| 模組 | 延遲（cycles） | 拆解 |
|---|---|---|
| init | 514 | 512 ＋ 2 |
| load_a／load_b（平行） | 141 | 64 個 word ＋ 77 |
| mac | 526 | 8 · 8 · 8 = 512 ＋ pipeline 深度 14 |
| loop_k 每輪 | 671 | 141 ＋ 526 ＋ 4 |
| store | 586 | 512 ＋ 74 |
| 每個 tile | 172,880 | |
| 總計 | 177,029,185（0.590 秒） | 1,024 個 tile |

### 3.5 v3：Double buffering

v2 中載入與計算輪流進行：每 671 個 cycle 中有 141 個 cycle 乘加單元閒置。v3 讓兩者重疊：

- **Buffer**：兩組 buffer（`la0/lb0`、`la1/lb1`）。
- **模組**：載入與計算拆成兩個函式（`load_ab`、`mac`），並設定 `INLINE off`，使兩者各自成為獨立的硬體模組。
- **排程**：進入 k 迴圈前，先把 `k = 0` 載入第 0 組。k 為偶數時，`load_ab(k+1 → 第 1 組)` 與 `mac(第 0 組)` 同時執行；k 為奇數時角色互換。兩個呼叫存取的陣列互不重疊，HLS 便將它們排成平行執行。
- **為什麼需要兩組**：只用一組 buffer 會產生 write-after-read hazard：下一次載入會覆蓋目前 `mac` 仍在讀取的資料。
- **代價**：`la`／`lb` 的 BRAM 用量加倍；晶片外流量、port 寬度與乘加單元數量不變。

```
v2:  [load k=0][ mac k=0 ][load k=1][ mac k=1 ][load k=2][ mac k=2 ] ...
v3:  [load k=0][ mac k=0 ][ mac k=1 ][ mac k=2 ][ mac k=3 ] ...
               [load k=1] [load k=2] [load k=3]
```

每輪時間從相加變為取最大值：

```
v2: T_iter = T_load + T_mac + 4        = 141 + 526 + 4 = 671 cycles
v3: T_iter = max(T_load, T_mac) + 4    = 530 cycles（模型預測）
每個 tile：v2 = L · 671，v3 = 141 + L · 530   →  L 很大時加速比 → 671 / 530 ≈ 1.27
```

加速的上限取決於載入所佔的比例（21%），符合 Amdahl's law。v3 的數字是模型預測，尚待 HLS 合成確認。

### 3.6 v0～v3 總整理

| 版本 | 手法 | 晶片外讀取量（元素數） | 每 cycle 乘加數 | 算術強度（FLOP/byte） | 狀態 |
|---|---|---|---|---|---|
| v0 | 基準 | 2 L³ C | 1 | 0.25 | C 模擬驗證 |
| v1 | loop tiling、晶片內 buffer、burst 存取 | L³ C (1/T_I + 1/T_J) | 1 | 2 | C 模擬驗證 |
| v2 | 512-bit AXI、array partitioning、16-lane SIMD | 同 v1 | 16 | 2 | C 模擬驗證、HLS 報告 |
| v3 | double buffering | 同 v1 | 16 | 2 | C 模擬驗證、HLS 待跑 |

## 4. 計算方法

### 4.1 執行時間模型

```
不重疊：  T ≈ T_compute + T_memory
重疊：    T ≈ max(T_compute, T_memory)
T_compute = 運算次數 / (每 cycle 運算數 × f_clk)
T_memory  = 搬運量 / 頻寬 + 延遲 × 未被重疊的請求次數
```

每種最佳化作用在其中一項：

| 手法 | 作用的項 | 版本 |
|---|---|---|
| Tiling | 搬運量 ↓ | v1 |
| 寬位元介面、burst | 頻寬 ↑、未被重疊的請求 ↓ | v1、v2 |
| 平行乘加單元 | 每 cycle 運算數 ↑ | v2 |
| Double buffering | 相加 → 取最大值 | v3 |
| 多個 HBM 通道 | 頻寬 ↑ | 設定檔對照實驗 |

### 4.2 晶片外流量

```
v0：  R_0 = 2 · L³ · C
v1：  R_1 = (L/T_I)(L/T_J) · L · (T_I + T_J) · C = L³ · C · (1/T_I + 1/T_J)
R_0 / R_1 = 2 / (1/T_I + 1/T_J)  =  8（8×8）、16（16×16）、32（32×32）
```

### 4.3 算術強度與 roofline

```
AI = FLOPs / bytes = 2 L³ C / (4 · R)
v0：     AI = 2 L³ C / (4 · 2 L³ C) = 0.25 FLOP/byte
v1～v3：  AI = T_I · T_J / (2 (T_I + T_J))  =  2（8×8）、4（16×16）、8（32×32）
可達效能 = min(峰值運算能力, AI × 頻寬)
```

v2 的 16 個乘加單元最多消耗 9.6 GFLOP/s。在 AI = 2 FLOP/byte 下只需 4.8 GB/s，遠低於兩個 512-bit 輸入 port 提供的 38.4 GB/s，因此 tiling 後的 kernel 是 compute-bound。這與 HLS 報告一致：每輪 671 個 cycle 中 `mac` 佔 526 個。v0 則是 memory-bound：每次乘加都要等兩次無法 burst 的存取。

### 4.4 Cycle 模型與校正

```
cycles_total = (L/T_I)(L/T_J) · cycles_tile
cycles_tile  = t_init + L · t_iter + t_store + ε
t_load  = max(T_I, T_J) · C/16 + α        （α：記憶體延遲與迴圈啟動成本）
t_mac   = T_I · T_J · C/16 + δ            （δ：pipeline 深度）
t_iter  = t_load + t_mac + 4               （v2）
t_iter  = max(t_load, t_mac) + 4           （v3）
t_store = T_I · T_J · C/16 + σ
```

常數由 v2 的 HLS 報告校正：

| 報告數值 | 結構項 | 校正出的常數 |
|---|---|---|
| load = 141 | 8 · 8 = 64 | α = 77 |
| mac = 526 | 8 · 8 · 8 = 512 | δ = 14 |
| store = 586 | 512 | σ = 74 |

校正後的模型預測 v2 為 177,029,120 cycles，報告為 177,029,185（誤差 < 0.01%）。由於校正與比較使用同一份報告，這只檢查了一致性，並非預測能力。驗證要使用校正時沒用過的設定：tile 大小 16 × 16 與 32 × 32（`make hls-sweep`），以及 v3、v4 版本（`make hls-all`），目標誤差在 10% 以內。

模型有三項限制：

- HLS 的延遲本身是估計值。
- 沒有模擬共用同一 HBM 通道的 port 之間的競爭。
- 資源數字（DSP、BRAM）只供參考。

### 4.5 晶片內記憶體

```
acc = T_I · T_J · C · 4 B          （8×8：32 KB；16×16：128 KB；32×32：512 KB）
la  = T_I · C · 4 B，lb = T_J · C · 4 B   （8 個 token：各 4 KB；v3 加倍）
```

tile 越大，算術強度越高，但 BRAM 用量以平方成長。設計空間探索在「cycle 數對 BRAM 用量」的 Pareto 前緣上，選擇膝點作為 tile 大小。

### 4.6 容量模型

記憶體需求隨 L² 成長，因此最大序列長度只隨可用記憶體的平方根成長：

```
記憶體 = L² · (每個 pair 位置的 bytes)
L_max  = sqrt(容量 / 每個 pair 位置的 bytes)
```

以 16 GB 的 U55C、FP16 為基準（ESMFold 與 LightNobel 比較時使用的精度）：

| 配置 | 每個 L² 位置的 bytes | L_max | 相對 |
|---|---|---|---|
| 未融合（約 7 份同時存在的 L × L × 128 張量，FP16） | 7 × 256 = 1,792 | ≈ 3,096 | 1.00× |
| 融合 producer／consumer，FP16 `z`，INT8 `a`、`b`（設計估算） | 2 × 256 ＋ 2 × 132 = 776 | ≈ 4,705 | 1.52× |
| 同上，改用 INT4 `a`、`b`（設計估算） | 2 × 256 ＋ 2 × 68 = 648 | ≈ 5,148 | 1.66× |

INT8 token 為 128 B 加 4 bytes 的 scale；INT4 token 為 64 B 加 4 bytes 的 scale。融合的配置是分析估算，尚未實作。由於 L 只隨記憶體減少倍數的平方根成長，每個位置的 bytes 減少 2.3 倍，L 約提升 1.5 倍。
