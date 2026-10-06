# 第 6 章　案例研究（下）：LightNobel 的硬體架構

> **本章重點**
> - 第 5 章講了 LightNobel 的演算法；這一章從**硬體設計者的角度**，拆開每個單元的結構、原理與設計理由。
> - 讀法：先看 6.1「需求 → 架構」，知道每個單元是為了解決哪個問題；再逐一看單元內部。
> - 核心技巧有四個：**位元拆解乘法**（RMPU）、**可重組的加法樹**（PE Cluster、DAL）、**SIMD 向量單元 ＋ 排序網路**（VVPU）、**線上 softmax**（token-wise attention）。
> - 最重要的一課：**這顆晶片 70% 的面積花在搬資料的 crossbar，不是運算單元。**
> - 資料來源：論文 Sec. 5（架構）、Sec. 6（評估方法）、Sec. 7.2（硬體設計空間探索）、Table 2（面積與功耗）、Fig. 8～10。
>   論文沒有寫明的細節會標「推測」或「我們的分析」。

---

## 6.1 從需求推導架構：設計者面對的四個問題

好的加速器不是先想「要放什麼單元」，而是先分析**工作負載（workload）的特性**，再讓每個單元對應一個需求。
LightNobel 面對的 PPM 有四個特性：

| # | 工作負載的特性 | 帶來的硬體問題 | LightNobel 的對應單元 |
|---|---|---|---|
| ① | **token 很小（128 個數）但數量極多**（L² 個，動輒數百萬） | 要能同時處理很多 token，而且權重要一直重複使用 | 很多組 **RMPU**（每組同時算 20 個 token）；**weight-stationary** 資料流 |
| ② | **同一份工作裡混著多種精度**（INT4、INT8、INT16 outlier） | 為每種精度各做一套乘法器會很浪費：用不到的那套就閒置 | **RMPU 的位元拆解**：用 4-bit 小乘法器拼出任何精度 |
| ③ | **activation 要在執行時量化**（算尺、挑 top-k） | 需要排序、找最大值、重新排列資料的硬體 | **VVPU**（SIMD ＋ bitonic 排序）、**Token Aligner** |
| ④ | **向量運算很多**（LayerNorm、Softmax、residual，每個 token 都要做） | 矩陣單元做這些很沒效率 | **VVPU** 專門做向量運算，和 RMPU 以管線串接 |

再加上一個全域的限制：**記憶體容量與頻寬**（第 1、2 章），所以還需要 scratchpad、double buffering，以及不存中間值的資料流（6.6 節）。

---

## 6.2 整體架構與資料流

### 方塊圖（依論文 Fig. 8 簡化）
```
          External Memory（80 GB HBM2E, 2 TB/s）
                 |                         ^
                 v                         |
          +--------------+          +--------------+
          | Token Aligner|          |    Output    |
          +--------------+          |  Scratchpad  |
                 |                  +--------------+
                 v                         ^
  +------------------+ +-----------+       |
  | Token Scratchpad | |  Weight   |       |
  |  128 KB x 2      | | Scratchpad|       |
  | (double buffer)  | |  64 KB    |       |
  +------------------+ +-----------+       |
           |                 |             |
  =========v=================v=============|=====  Global Crossbar Network (GCN)
           |                               |
     +-----v------+      +-----------------+---------------+
     |   RMPU x32 | ---> | VVPU x4 per RMPU (128 in total) |
     |  (matrix)  |      |  (vector: LayerNorm, Softmax,   |
     +------------+      |   residual, quantization)       |
                         +---------------------------------+
     Controller: generates control signals for all units
```

### 先釐清：方塊圖是「有哪些單元」，不是「運算的順序」
這顆晶片的硬體是**分時共用**的，比較像一台依指令執行的機器，而不是把某個運算焊死成固定管線：
- **RMPU** 負責所有矩陣乘法類的運算：linear、einsum、Q×K。
- **VVPU** 負責所有逐元素、向量類的運算：LayerNorm、sigmoid、gating、residual、softmax、執行時量化。
- **GCN** 讓資料在兩者之間任意繞送，順序可以是 VVPU → RMPU → VVPU；論文也寫到「RMPU **或** VVPU 從 scratchpad 取 token」（Sec. 5）。
- **Controller** 決定每一趟要做哪些運算。

一個模型的運算要**分好幾趟**跑完；每一趟都是「從記憶體讀 → 在晶片內串接幾個運算 → 寫回記憶體」。

### 一趟計算怎麼流過這顆晶片
1. **Token Aligner** 從 HBM 讀進一批（block）壓縮過的 token，拆解、排整齊後放進 **Token Scratchpad**。
   Token Scratchpad 有兩份（128 KB × 2），一份給運算單元讀，另一份同時從記憶體裝下一批，也就是 **double buffering**（3.3 節），藏住記憶體延遲。
2. 這一趟要用的權重事先載入 **Weight Scratchpad**（64 KB），整趟都不動（weight-stationary）。
3. 需要時，**VVPU 先做前處理**（例如 linear 之前的 LayerNorm）。
4. **RMPU** 做矩陣乘法，一次最多 20 個 token。
5. 結果直接以管線送給 **VVPU**（不回記憶體），做後續的向量運算（例如 sigmoid、gating、residual），最後做**執行時量化**。
6. 量化好的 token 經 **Output Scratchpad** 寫回 HBM。

「RMPU → VVPU」這種「矩陣運算後面接向量運算」的組合在模型裡最常見（例如 linear 後面接 sigmoid 和 gating），所以論文特別強調這條管線。

### Triangle Multiplication 怎麼對應到這顆晶片（推測）
**論文沒有寫出每個運算的排程**；下面是依照運算的相依關係（1.5 節）和論文描述的硬體能力推出來的：
```
第 1 趟（逐 token，對每一格 (i, k)）
  讀 z → VVPU：LayerNorm
        → RMPU：4 個 linear（a_p、a_g、b_p、b_g）
        → VVPU：sigmoid、gating、mask、執行時量化（C 組 → INT4）
        → 寫回 HBM：a、b          ← 必須寫出去（einsum 要跨 token 讀）

第 2 趟（einsum，跨 token）
  讀 a、b（INT4）→ RMPU：x[i][j] = Σ_k a[i][k]·b[j][k]
                → VVPU：反量化、累加

第 3 趟（逐 token，對每一格 (i, j)，可以接在第 2 趟後面做成管線）
  → VVPU：LayerNorm_out
  → RMPU：linear_z、linear_g
  → VVPU：sigmoid、× g、residual 相加、執行時量化（A 組 → INT8 ＋ outlier）
  → 寫回 HBM：新的 z
```
重點：**einsum 是矩陣乘法，在 RMPU 上做；它一定在 LayerNorm、gating 之後；而且中間一定要經過一次 HBM。**
這就是 1.5 節說的「融合的邊界」，在 LightNobel 的硬體上也一樣存在。

### 為什麼是 weight-stationary？
「stationary」是指**哪一種資料留在運算單元旁邊不動**。常見的選擇有三種：

| 資料流 | 固定不動的 | 適合的情況 |
|---|---|---|
| Weight-stationary | 權重 | 權重小、被很多輸入重複使用 |
| Output-stationary | 部分和（累加值） | 輸出要累加很多次 |
| Input-stationary | 輸入 | 輸入被很多權重重複使用 |

PPM 的 linear 權重只有 128 × 128 個 INT16 = **32 KB**，卻要被數百萬個 token 重複使用。
把權重固定在晶片內，每個 token 只需要搬一次，權重的搬運成本幾乎是 0。
這和 10.3 節「權重小、activation 大」是同一個觀察。

### 管線（pipeline）與延遲
論文的延遲模型：**總延遲由每個管線階段中最慢的那一段決定**（RMPU 運算、VVPU 運算、記憶體讀寫）。
這和 2.4 節的 `max(T_compute, T_memory)` 是同一個概念，只是階段更多。

---

## 6.3 Token Aligner：記憶體的格式和運算的格式不一樣

### 問題：兩邊想要的排列方式互相衝突
- **記憶體端**希望資料**大塊、連續**，才能用滿 burst（3.2 節）。所以論文把多個 token 打包成一個 block，block 大小依記憶體通道的頻寬決定（Sec. 4.3）。
  每個 token 裡的排列是：inlier → outlier → 尺 → outlier 的位置（Fig. 7）。由於不同組的精度不同，**每個 token 壓縮後的長度也不同**。
- **運算端**希望**一行 scratchpad 剛好是一個 token**，這樣 RMPU、VVPU 一次讀一行就拿到一個完整的 token。

### 解法：解碼 ＋ 重新排列
Token Aligner 在資料進 scratchpad 之前，把「打包好的 block」**解碼並重新排成一個 token 一行**。
在硬體上，它的角色類似**寬度轉換器（width converter / gearbox）**：輸入是固定寬度的記憶體 word，輸出是長度不一的 token，
中間要有 buffer 和移位邏輯，把跨越 word 邊界的 token 拼回來。

### 學到的設計原則
**「儲存格式」和「運算格式」可以不同，中間用一個專門的轉換單元銜接。** 這樣兩邊都能用最適合自己的格式。
代價是轉換單元本身的面積與延遲；和 RMPU、crossbar 比起來，它只是很小的一塊。

---

## 6.4 RMPU：用 4-bit 小乘法器拼出任何精度

RMPU（Reconfigurable Matrix Processing Unit）是做矩陣乘法的單元，要解決 6.1 節的問題 ②：**同一份工作裡混著 INT4、INT8、INT16。**

### 6.4.1 為什麼不各做一套乘法器？
假設晶片上放了 INT4、INT8、INT16 三種乘法器：
- 算 INT4 的 token 時，INT8、INT16 的乘法器全部閒置；
- 而且三種的比例要事先固定，但 AAQ 的精度組合在**執行時**才知道（依 activation 所屬的組、outlier 的數量）。

結果就是嚴重的**利用率不足（underutilization）**。RMPU 的做法是：**只放一種最小的乘法器（處理 4-bit 資料塊），大的乘法用很多個小的拼起來。**
（用語說明：本章說的「4-bit 小乘法器」是簡稱，指「處理 4-bit 資料塊的乘法器」；硬體上它的輸入是 5 bit，原因見 6.4.3 節。）
這個想法來自 Bit Fusion（ISCA 2018，論文參考文獻 [57]）。

### 6.4.2 原理：位元拆解乘法
任何整數都可以拆成 4-bit 的小塊（chunk）：
```
A = a₀ + a₁·2⁴ + a₂·2⁸ + a₃·2¹²              （16-bit 的數拆成 4 塊）
A × B = Σᵢ Σⱼ aᵢ·bⱼ · 2^(4(i+j))              （每一對小塊相乘，再移位相加）
```
每個 `aᵢ·bⱼ` 是**一對 4-bit 資料塊**的小乘法；`× 2^(4(i+j))` 只是**左移**，不需要乘法器。

**數字例子：INT4 的 activation × INT16 的權重**（linear 裡最常見的情況：論文的權重是 INT16）
```
a = −5（INT4，只有 1 塊）
w = 1234 = 0x04D2 → 從低到高 4 塊：[2, 13, 4, 0]

部分積        值        左移      結果
−5 ×  2  =   −10       << 0   =    −10
−5 × 13  =   −65       << 4   =  −1,040
−5 ×  4  =   −20       << 8   =  −5,120
−5 ×  0  =     0       << 12  =      0
                         合計   = −6,170   ← 正好等於 −5 × 1234
```
所以：
| 乘法 | 需要幾個小乘法器（5-bit 輸入） |
|---|---|
| INT4 × INT4 | 1 |
| INT4 × INT16 | 1 × 4 = 4 |
| INT8 × INT16 | 2 × 4 = 8 |
| INT16 × INT16 | 4 × 4 = 16 |

**同一組硬體，精度低就同時算很多個，精度高就合起來算一個**，所有乘法器都不會閒著。

### 6.4.3 有正負號的數怎麼拆？（sign extension）
二補數（two's complement）的整數，**只有最高位的那一塊帶正負號**，其他塊都是無號數。例如 INT8 的 −93：
```
−93 = 0xA3 → 高 4 位 0xA、低 4 位 0x3
高位塊：0xA 當作有號數 = −6
低位塊：0x3 當作無號數 = 3
驗算：−6 × 16 + 3 = −93 ✓
```
所以 RMPU 的資料對齊器（RDA）在拆塊時：
- **最高位的塊**：用它自己的最高位元做**符號延伸**（sign extension）；
- **其他塊**：前面**補 0**（zero extension）。

有號塊的範圍是 −8～7，無號塊是 0～15，要同時裝得下兩者，**每塊要 5 bit**（−16～15）。
這就是論文 Fig. 9(a) 裡乘法器輸入標成「5bit」的原因。

**所以「5-bit」是乘法器的輸入寬度，「4-bit」是資料塊的寬度：**
```
4-bit 資料塊 → RDA 擴充成 5-bit 有號數 → 5×5 有號乘法器 → 部分積 → 移位 → 加法樹
例：−93 = 0xA3
  高位塊 1010 → 符號延伸 → 11010 = −6
  低位塊 0011 → 補 0     → 00011 =  3
```
- **為什麼不用 4×4 就好？** 4-bit 有號只到 7、4-bit 無號沒有負數，都無法同時表示 −8～15。
  擴充成 5-bit 有號後，**同一種乘法器就能處理所有塊**，不用區分有號、無號；代價是乘法器從 4×4 變成 5×5，面積大一些。
- **輸出有幾 bit？** 兩個 5-bit 有號數相乘最多 10 bit；以實際會出現的值（−8×15 = −120 到 15×15 = 225）也至少要 9 bit。
  之後由移位器移 4(i+j) 位，再由加法樹加總。

### 6.4.4 階層式的結構：PE → PE Lane → PE Cluster → RMPU Engine
```
PE（Processing Element）
  16 個 5-bit 乘法器 ＋ 移位器 ＋ 16-to-1 加法樹
  → 可以算 1 個 INT16×INT16，或 16 個 INT4×INT4，或 4 個 INT4×INT16 …

PE Lane = 8 個 PE（共 128 個小乘法器）
  兩種模式：(1) 每 2 個 PE 加上 bias → 4 個輸出（給 head 維度 32 的 attention）
           (2) 8 個 PE 全部用加法樹加起來 → 1 個輸出（內積）

PE Cluster = 20 個 PE Lane ＋ DAL（動態累加邏輯）

RMPU Engine = 4 個 PE Cluster
  = 80 個 PE Lane = 640 個 PE = 10,240 個小乘法器（5-bit 輸入）
  → 一次最多同時處理 20 個 token
```

### 6.4.5 為什麼一個 Cluster 是 20 個 Lane？（最小公倍數）
算一個 128 維的內積（一個 token × 權重的一行），需要多少個 4-bit 乘法器？

| token 的格式 | 計算 | 需要的小乘法器 | 需要的 PE Lane（每個 128 個） |
|---|---|---|---|
| 128 個 INT4 inlier（C 組） | 128 × 4 = 512 | 512 | **4** |
| 124 個 INT4 inlier ＋ 4 個 INT16 outlier（B 組） | 124 × 4 ＋ 4 × 16 = 560 | 560 | 4.375 → **5** |

PPM 裡大部分的內積需要 **4 或 5** 個 Lane。一個 Cluster 放 **20 個 Lane（4 和 5 的最小公倍數）**：
- 需要 4 個 Lane 時：20 ÷ 4 = **5 個 token** 同時算，Lane 全部用滿；
- 需要 5 個 Lane 時：20 ÷ 5 = **4 個 token** 同時算，也全部用滿。

**這就是「依工作負載決定硬體數量」的典型例子**：先統計工作負載需要的單位（4 或 5），再選一個能被兩者整除的數量，讓利用率在兩種情況都是 100%。

### 6.4.6 DAL：尺要在什麼時候乘？
一個 B 組的 token 有兩種值：
- **inlier**：量化過，要**乘尺**才會回到原本的大小；
- **outlier**：以 INT16 原值存，**不用乘尺**。

所以不能把 5 個 Lane 的結果直接加起來。**DAL（Dynamic Accumulation Logic）** 的做法：
```
需要 4 個 Lane（全是 inlier）：  4 個 Lane 的結果相加 → 最後乘一次尺
需要 5 個 Lane（有 outlier）：   inlier 的部分先相加 → 乘尺
                                 → 再加上 outlier 那個 Lane 的結果
```
4-to-1 和 5-to-1 的加法樹結構不同，DAL 用「關掉其中一個加法樹、把第 5 個 Lane 接到後面」的方式動態切換，
前面再放一個 **Arbiter** 把各 Lane 的輸出排到正確的位置。這就是「**可重組的加法樹**」。

> **對照我們的 v4：** linear 的內積是沿著同一個 token 的 channel 加總，所以尺可以最後乘一次（4.4 節情況一）。
> 我們的 einsum 是沿著 k 跨 token 加總，每一項的尺都不同（4.4 節情況二），所以 v4 每個 k 都要乘尺。

### 6.4.7 RMPU 的輸出有很多種「粒度」
加法樹的每一層都有意義，RMPU Engine 把不同層的結果都拉出來用：
| 取出的位置 | 意義 | 用途 |
|---|---|---|
| 2 個 PE 的和 | head 維度 32 的內積 | multi-head attention |
| 4 或 5 個 Lane 的和 | 一個量化 token 的內積 | 量化的 linear（經過 DAL） |
| 8 或 16 個 Lane 的和 | 沒量化的 token 的內積 | 高精度的運算 |
| 80 個 PE 的和 | 更大的內積 | 多個 RMPU 合作 |

最後一層還有 ReLU。同一組乘法器，靠「從加法樹的哪一層取結果」支援不同的運算。

---

## 6.5 VVPU：向量運算、排序與執行時量化

### 6.5.1 結構
```
VVPU
 ├─ 128 條 SIMD Lane：每條有一個 16-bit ALU、自己的小 scratchpad、兩級的指數查表（exp LUT）
 ├─ SSU（Scalar Support Unit）：處理純量運算，例如求平均、量化資料的格式整理
 └─ LCN（Local Crossbar Network）：讓 128 條 Lane 之間可以任意交換資料
```
- **為什麼是 128 條？** 一個 token 剛好 128 個數，**一條 Lane 負責一個 channel**，一個 cycle 就能對整個 token 做同一個運算（SIMD：single instruction, multiple data）。
- **為什麼要指數查表？** Softmax 和 sigmoid 都要算 `exp(x)`。用查表加少量運算代替完整的指數電路，面積小很多（參考文獻 [26] 的做法）。
- **為什麼要 SSU？** LayerNorm 的平均值、變異數要把 128 個數加起來變成一個數，這種「歸約（reduction）」和格式整理交給純量單元做，SIMD Lane 就能專心做逐元素的運算。
- **為什麼要 LCN？** 量化後的資料要依記憶體格式重新排列（inlier、outlier 分開放），需要資料在 Lane 之間移動。

### 6.5.2 用硬體挑 top-k：bitonic 排序網路
執行時量化要找出每個 token 裡絕對值最大的 k 個（A、B 組 k = 4）。VVPU 用 **bitonic sort（雙調排序）**：

**原理：** 排序網路（sorting network）是一組**固定連線的比較交換器（compare-and-swap）**：
每個比較器接兩個數，大的往一邊、小的往另一邊。連線是固定的，**不管資料是什麼，步驟都一樣**。這點對硬體很重要：
- 沒有「if 分支」，每一步所有比較器**同時動作**，很適合 SIMD Lane 平行做；
- 延遲固定，容易排進管線。

以 8 個數為例，bitonic sort 分 3 個大階段（2、4、8 個一組），共 6 步，每步 4 個比較器同時動作：
```
階段 1：兩兩比較，做出長度 2 的有序片段
階段 2：合併成長度 4 的有序片段（2 步）
階段 3：合併成長度 8 的有序序列（3 步）
總步數 = log₂8 × (log₂8 + 1) ÷ 2 = 3 × 4 ÷ 2 = 6
```
128 個數時：`7 × 8 ÷ 2 = 28` 步，每步 64 個比較器同時動作。只要 top-k，不需要完整排序，還可以提早停止（參考文獻 [56]）。

排序時 VVPU **一路追蹤每個值原本的位置（index）**，最後就知道 outlier 在哪裡（要存進記憶體的「outlier 位置」）。
**k = 1 時就是找最大值**，所以同一套硬體也用在 softmax（要先找最大值）和算尺（最大絕對值）。

### 6.5.3 執行時量化的四個步驟
```
1. top-k：SIMD Lane 找出 outlier 和尺（最大絕對值）
2. 縮放：每個值除以尺、四捨五入成 INT4／INT8
3. 重排：LCN 依記憶體格式重新排列（inlier、outlier、尺、位置）
4. 對齊：SSU 整理成最終的記憶體排列
```
這些都在 VVPU 內完成，**完整精度的值從來不寫回記憶體**（4.3 節「算尺的時候…」、10.4 節「量化在源頭完成」）。

### 6.5.4 為什麼一個 RMPU 配 4 個 VVPU？（硬體設計空間探索）
論文 Fig. 12(a) 改變「每個 RMPU 配幾個 VVPU」，看延遲怎麼變：
- **VVPU 太少**：RMPU 算得很快，但 VVPU 做 LayerNorm、量化來不及，整條管線被 VVPU 拖慢；
- **到 4 個時延遲就不再下降（飽和）**：VVPU 的工作已經能完全藏在 RMPU 的運算底下，再加也沒用。

這和 2.6 節的 Amdahl's Law、3.3 節的 double buffering 是同一個道理：**管線的速度由最慢的那一段決定，把最慢的那段加強到不是瓶頸就夠了，再多只是浪費面積。**

---

## 6.6 Token-wise multi-head attention：不存 L³ 的 score matrix

### 問題
Triangle Attention 的 score matrix 是 L × L × L（每個 head），不分塊時一定放不下（5.4 節）。

### 原理：線上 softmax（online softmax）
論文說他們的做法「類似 FlashAttention，並針對 token-wise 運算最佳化」（參考文獻 [16]），但沒有寫出完整的演算法。
以下說明 FlashAttention 的核心原理，也就是 LightNobel 能做到「不存 score matrix」的原因。

Softmax 需要先知道**所有分數的最大值**（數值穩定）和**總和**：
```
softmax(sᵢ) = exp(sᵢ − m) ÷ Σⱼ exp(sⱼ − m)        m = max(s)
```
看起來必須先算完全部的分數才能開始。**線上 softmax** 的技巧是邊算邊修正：
```
維護三個值：目前的最大值 m、目前的總和 ℓ、目前的輸出累加 o
每來一批新的分數 s（和對應的 V）：
  m_new = max(m, max(s))
  ℓ     = ℓ × exp(m − m_new) + Σ exp(s − m_new)       ← 舊的總和用新的最大值重新縮放
  o     = o × exp(m − m_new) + Σ exp(s − m_new) × V
  m     = m_new
全部算完：輸出 = o ÷ ℓ
```
每一批分數**算完就丟**，只留下 m、ℓ、o 三個小東西。L³ 的 score matrix 從來不需要整份存在記憶體。

### 在 LightNobel 上怎麼跑（Sec. 5.4）
1. RMPU 對每個 head 平行算 Q × K；
2. 同時，VVPU 做反量化和中間結果的累加；
3. VVPU 做 softmax，和下一批 Q × K 以管線重疊，減少找最大值的延遲；
4. 最後載入 V，乘上 softmax 的結果，寫回記憶體。

### 為什麼在 PPM 上特別划算
一般的語言模型 hidden 維度很大（LLaMA 7B 是 4,096），一次放不下很多 token，token-wise 做法的資料重用有限。
**PPM 的 hidden 維度只有 128**，一個 token 很小，晶片內可以同時放很多個，token-wise 的做法就很有效率（論文 Sec. 5.4 的論點）。

---

## 6.7 互連與記憶體：為什麼 crossbar 佔了 70% 的面積

### Crossbar 是什麼
Crossbar 是「**任何輸入都能接到任何輸出**」的交換網路。N 個輸入、N 個輸出、每條 W bit 寬：
```
開關（crosspoint）的數量 ∝ N × N × W
```
**面積與功耗隨埠數的平方成長。** 例如 128 條 Lane、16 bit 的全互連：128 × 128 × 16 ≈ 26 萬個開關。
LightNobel 用 **swizzle switch**（參考文獻 [55]）這種面積、功耗較省的 crossbar 實作，但仍然是最大的一塊。

### 面積與功耗的分配（Table 2，28 nm、1 GHz）
論文的 Table 2 在 PDF 中排版錯亂，下表是我們把各列的數字加總對照後推回來的，總數與論文文字（crossbar 70.28% 面積、67.95% 功耗；RMPU Engine 18.20% 面積、22.36% 功耗）一致：

| 模組 | 面積（mm²） | 功耗（mW） |
|---|---|---|
| 1 個 RMPU Engine | 1.017 | 473.9 |
| 1 個 RDA（資料對齊器） | 0.105 | 112.4 |
| 1 個 RMPU 合計 | 1.127 | 589.1 |
| **32 個 RMPU** | **36.07** | **18,853** |
| 1 個 VVPU 的 128 條 SIMD Lane | 0.115 | 21.1 |
| 1 個 VVPU 的 LCN（crossbar） | **0.785** | **288.0** |
| 1 個 VVPU 合計 | 0.902 | 309.9 |
| **128 個 VVPU** | **115.43** | **39,668** |
| **GCN（全域 crossbar）** | **25.13** | **9,216** |
| Scratchpad（Token 128 KB × 2、Weight 64 KB、Output 128 KB） | 約 2.0 | — |
| **整顆晶片** | **178.80** | **67,805（67.8 W）** |

### 這張表教我們什麼
- **一個 VVPU 裡，crossbar（0.785）是 128 條運算 Lane（0.115）的將近 7 倍大。** 搬資料的硬體比算資料的硬體貴得多。
- 全晶片的 crossbar（128 個 LCN ＋ GCN）約 125.7 mm²，**佔 70%**；真正做乘法的 RMPU Engine 只佔 18%。
- 這對應第 2 章的主題：**在這類問題裡，瓶頸是資料移動，不是運算。** 連晶片內部都是如此。
- 對設計者的啟示：想省面積，先檢討**是否真的需要全互連**。如果資料的移動模式是固定的（例如只需要相鄰交換），用簡單的網路就能大幅縮小面積。

### Scratchpad 為什麼叫 scratchpad，不叫 cache？
兩者都是晶片內的小記憶體，差別在**誰決定放什麼**：
| | Cache | Scratchpad |
|---|---|---|
| 放什麼由誰決定 | 硬體自動（依位址、替換策略） | **設計者／程式明確指定** |
| 命中率 | 不確定 | 確定（事先規劃好） |
| 需要的額外硬體 | tag、比較器、替換邏輯 | 幾乎沒有 |

加速器的資料流是事先規劃好的（哪個 token 什麼時候用），不需要 cache 的猜測機制，用 scratchpad 更省面積也更可預測。
我們 FPGA kernel 裡的 BRAM 陣列（`acc`、`la`、`lb`）也是 scratchpad。

---

## 6.8 決定要放幾個：硬體設計空間探索

論文 Fig. 12(b) 固定每個 RMPU 配 4 個 VVPU，改變 RMPU 的數量：**到 32 個時效能就飽和了。**

原因（Sec. 7.2）：32 個 RMPU 已經有足夠的運算能力，**處理從記憶體讀進來的所有資料**；再加更多 RMPU，資料供應跟不上，只會閒置。

這就是 **roofline 的平衡點**（2.5 節）：
```
運算能力 < 記憶體能供應的量 → 加運算單元有用（compute-bound）
運算能力 ≥ 記憶體能供應的量 → 加運算單元沒用（memory-bound）
32 個 RMPU ≈ 剛好在平衡點上
```
**好的硬體設計會把運算資源放到「剛好到平衡點」**，再多就是浪費面積和功耗。
我們的 9.3 節 DSE（tile 大小 vs BRAM）是同一種思考：找「膝點」。

---

## 6.9 硬體怎麼評估：每個工具在做什麼

論文沒有做出實體晶片，而是用以下工具組合評估（Sec. 6）。這也是學術界 ASIC 加速器論文的標準流程：

| 工具 | 做什麼 | 產出 | 對應我們的專題 |
|---|---|---|---|
| **SystemVerilog RTL** | 用硬體描述語言寫出每個模組的電路 | 可模擬、可合成的設計 | HLS 從 C++ 自動產生 RTL |
| **Synopsys Design Compiler**（28 nm、1 GHz） | 邏輯合成：把 RTL 對應到製程的標準元件（standard cell） | 面積、功耗、能不能跑到 1 GHz | Vivado 合成、HLS 的資源與時序報告 |
| **記憶體編譯器、CACTI 7.0** | 估計 SRAM（scratchpad）的面積與功耗 | 記憶體的面積、功耗 | BRAM／URAM 的用量 |
| **Ramulator** | cycle 級的 DRAM／HBM 模擬 | 真實的記憶體延遲與頻寬 | （我們沒有；HLS 假設固定延遲） |
| **Python cycle-accurate 模擬器** | 依每個模組的延遲，模擬整個 PPM 的執行 | 總延遲 | 我們的分析模型（`perf_model.py`） |
| **RTL 交叉驗證** | 比較模擬器和 RTL 模擬的結果 | 誤差平均 3.30%、都在 5% 內 | 分析模型 vs HLS 報告 |

CACTI 只支援到 32 nm，論文用常見的縮放係數換算到 28 nm。這種「工具不完全符合時，用文獻中的方法換算」在架構論文很常見，報告時要說明。

---

## 6.10 如果要在 FPGA 上實作這些設計（我們的分析）

這一節是我們自己的分析，不是論文的內容。目的是把 ASIC 的設計對應到 U55C 上的資源，思考哪些能搬、代價是什麼。

| LightNobel 的元件 | 在 FPGA 上的對應 | 需要注意的地方 |
|---|---|---|
| 4-bit 小乘法器（RMPU） | 用 **LUT** 做（小的乘法器用 LUT 比用 DSP 划算） | U55C 有約 130 萬個 LUT，但每個小乘法器要數個到十幾個 LUT，數量有限 |
| INT8 × INT8 乘法 | **DSP48E2**（27 × 18 的乘法器） | 已知的技巧：共用一個運算元時，一個 DSP 可以同時算兩個 INT8 乘法（AMD 白皮書 WP486） |
| 可重組的加法樹（DAL） | LUT ＋ 多工器 | 可重組的彈性要用多工器換，會吃 LUT 和繞線 |
| SIMD Lane | 展開的迴圈（`#pragma HLS UNROLL`）＋ 切開的陣列（ARRAY_PARTITION） | 和我們的 v2 16 路、v4 64 路是同一個手法 |
| Crossbar | 大量多工器 ＋ 繞線 | **在 FPGA 上一樣昂貴**，而且繞線擁擠會讓時脈跑不高；應盡量用固定的資料移動模式 |
| Scratchpad | BRAM／URAM | U55C 約 43 MB，比 LightNobel 在 Table 2 列出的共用 scratchpad（約 0.45 MB）大得多，這是 FPGA 的優勢 |
| double buffering | 兩組 BRAM ＋ `DATAFLOW` | 就是我們的 v3 |
| exp 查表 | BRAM 或 LUT 裡的查表 | HLS 的 `hls::exp` 也可以，但比較耗資源 |
| bitonic 排序 | 展開的比較交換網路 | 128 個數要 28 步、每步 64 個比較器，LUT 用量可觀 |

**我們的 v0～v5 對應到其中的哪些部分：**
- v1～v3：scratchpad、weight／input 的重用、double buffering（6.2 節的資料流基礎）；
- v4：INT8 乘法 ＋ 浮點尺（RMPU ＋ DAL 的簡化版，但我們的 einsum 每個 k 都要乘尺，6.4.6 節）；
- v5（規劃中）：INT4 的解包與乘法，接近 RMPU 的「拆成 4-bit」想法，但只支援單一精度，不需要可重組。

---

## 本章小結

| 單元 | 解決的問題 | 核心技巧 | 設計數量的理由 |
|---|---|---|---|
| Token Aligner | 記憶體格式 ≠ 運算格式 | 解碼 ＋ 重新排列（寬度轉換） | — |
| RMPU | 多種精度混在一起 | **位元拆解乘法**、可重組加法樹、DAL | 一個 Cluster 20 個 Lane（4 和 5 的最小公倍數）；32 個 RMPU（到平衡點就飽和） |
| VVPU | 大量向量運算、執行時量化 | 128 條 SIMD Lane、exp 查表、**bitonic 排序** | 每個 RMPU 配 4 個（再多就飽和） |
| Token-wise attention | L³ 的 score matrix | **線上 softmax** | — |
| Crossbar、scratchpad | 資料要在單元之間移動 | swizzle switch、double buffering、weight-stationary | crossbar 佔 70% 面積：資料移動才是最貴的 |

**三個可以帶走的設計原則：**
1. **先分析工作負載，再決定硬體**：每個單元都對應一個工作負載的特性（6.1 節）。
2. **數量由利用率和平衡點決定**：20 個 Lane 讓 4、5 兩種情況都用滿；32 個 RMPU、4 個 VVPU 都是「剛好不是瓶頸」的點。
3. **資料移動比運算貴**：不只晶片外（HBM），晶片內（crossbar）也是如此。

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 C）：

1. 用 4-bit 乘法器算 INT8 × INT16，需要幾個乘法器？寫出拆解的公式。
2. 把 INT8 的 −93 拆成兩個 4-bit 塊，高位塊和低位塊各當作有號還是無號？為什麼乘法器的輸入是 5 bit？
3. 為什麼一個 PE Cluster 放 20 個 PE Lane？
4. DAL 為什麼要區分「4 個 Lane」和「5 個 Lane」兩種累加方式？
5. bitonic 排序網路為什麼適合硬體？128 個數要幾步？
6. 線上 softmax 為什麼不需要存整個 score matrix？
7. 為什麼 LightNobel 的 crossbar 佔了 70% 的面積？這對設計者有什麼啟示？
8. 論文的 RMPU 數量為什麼停在 32 個？這和 roofline 有什麼關係？

---

**下一章**進入我們自己的實作：先介紹 FPGA 與 AMD 工具鏈的原理，看 C++ 是怎麼變成電路的。
