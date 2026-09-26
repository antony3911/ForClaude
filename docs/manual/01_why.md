# 第 1 章　為何而做：問題具體發生了什麼？

> **本章重點**
> - 蛋白質結構預測模型（AlphaFold2、ESMFold）內部有一份 **L × L × 128** 的巨大資料（pair representation）。
> - 蛋白質越長（L 越大），這份資料**以平方成長**：長度加倍，資料變 4 倍。
> - 這造成兩個具體問題：**① 記憶體放不下**（序列長度受限），**② 搬資料比計算還慢**（memory-bound）。
> - LightNobel 針對這兩個問題提出解法；我們的專題則是在 FPGA 上，用常見手法處理其中最關鍵的一個運算。

---

## 1.1 蛋白質結構預測在做什麼？

### 白話直覺
蛋白質是一條由胺基酸串成的「珠鍊」。胺基酸共有 20 種，用英文字母表示，所以一條蛋白質可以寫成一串字：

```
MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEK...
```

這條珠鍊在細胞裡會**自動摺疊**成特定的 3D 形狀，而**形狀決定功能**：酵素能不能抓住受質、抗體能不能卡住病毒，都取決於形狀。

**蛋白質結構預測** = 輸入那串字母，輸出每個原子的 3D 座標。

### 為什麼重要
- 用實驗測定結構（X 光繞射、冷凍電顯）要花數月到數年，而且很貴。
- AlphaFold2（DeepMind，2021）讓預測準確度接近實驗水準，相關研究獲得 2024 年諾貝爾化學獎。
  LightNobel 的名字就是在呼應這件事。
- 應用：藥物設計、理解疾病突變、設計新的酵素。

### 本專題的關鍵變數：L
**L = 蛋白質的長度（胺基酸個數）**。整份手冊都圍繞這個數字：

| 蛋白質 | UniProt ID | L |
|---|---|---|
| 血紅素 α 鏈 | P69905 | 142 |
| p53（抑癌蛋白） | P04637 | 393 |
| 新冠病毒棘蛋白（單體） | P0DTC2 | 1,273 |
| BRCA1（乳癌相關） | P38398 | 1,863 |
| Dystrophin（肌肉蛋白） | P11532 | 3,685 |
| Titin（人體最大的蛋白之一） | Q8WZ42 | 約 34,000 |

大部分蛋白質在 1,000 以內，但**很多重要的蛋白質比這長**。另外，預測蛋白質複合體時常把多條鏈接起來一起算，L 會變得更大。

---

## 1.2 AlphaFold2 / ESMFold 的架構全貌

我們的 reference（LightNobel）以這一類模型為對象，統稱 **PPM（Protein structure Prediction Model）**。
我們實際對照的是 **ESMFold**（Meta，2022），因為它的結構比 AlphaFold2 簡單，而且公開在 HuggingFace 上。

```
 輸入：胺基酸序列（長度 L）
          │
          ▼
 ┌───────────────────────────┐
 │ ESM-2 語言模型（3B 參數） │  讀序列，產生每個胺基酸的特徵
 └───────────────────────────┘
          │
          ▼
 ┌───────────────────────────────────────────────┐
 │ Folding trunk（48 個 block，反覆執行）        │
 │                                               │
 │   Sequence representation   s ∈ R^{L×1024}    │  ← 每個胺基酸一組特徵
 │   Pair representation       z ∈ R^{L×L×128}   │  ← 每「一對」胺基酸一組特徵 ★
 │                                               │
 │   每個 block 內：                             │
 │     - Triangle Multiplication（outgoing）     │  ← 我們實作的就是這個
 │     - Triangle Multiplication（incoming）     │
 │     - Triangle Attention（starting / ending） │
 │     - 其他（MLP、sequence ↔ pair 的交流）     │
 └───────────────────────────────────────────────┘
          │
          ▼
 ┌──────────────────┐
 │ Structure module │  把特徵轉成 3D 座標
 └──────────────────┘
          │
          ▼
 輸出：每個原子的 3D 座標
```

（AlphaFold2 的對應部分叫 **Evoformer**，也有 48 個 block，同樣有 pair representation。
差別在於 AlphaFold2 用多序列比對（MSA）當輸入，ESMFold 改用語言模型。）

### 兩種 representation
| 名稱 | 形狀 | 意義 | 大小隨 L |
|---|---|---|---|
| Sequence representation | L × 1024 | 「第 i 個胺基酸」的特徵 | **線性**（L） |
| **Pair representation** | **L × L × 128** | 「第 i 個和第 j 個胺基酸之間的關係」 | **平方**（L²） |

Pair representation 可以想成一張 **L × L 的表格，每一格放 128 個數字**。
第 (i, j) 格記錄模型對「i 和 j 距離多遠、有沒有交互作用」的理解。

---

## 1.3 Triangle Multiplication 在做什麼？

### 「三角形」的直覺
如果知道：
- 胺基酸 **i 離 k 很近**
- 胺基酸 **j 離 k 也很近**

那 **i 和 j 大概也不會太遠**，這就是三角不等式。

```
        k
       / \
  近  /   \  近
     /     \
    i ----- j   ← 可以推論：應該也不遠
```

Triangle Multiplication 就是把這個推理寫成數學：**更新 (i, j) 格時，把所有第三者 k 都看過一遍**。

### 算式（outgoing 版本）
```
z[i][j][c] = Σ_k  a[i][k][c] × b[j][k][c]        （k 從 0 到 L−1，c 從 0 到 127）
```
- `a`、`b`：由 pair representation 經過 LayerNorm、線性轉換、gating 得到，形狀都是 L × L × 128。
- `z`：輸出，形狀也是 L × L × 128。
- 對每個 channel c 來說，這其實是一個 **L × L 的矩陣乘法**，總共做 128 次。

### 具體例子（L = 3，只看一個 channel）
```
a = | a00 a01 a02 |      b = | b00 b01 b02 |
    | a10 a11 a12 |          | b10 b11 b12 |
    | a20 a21 a22 |          | b20 b21 b22 |

z[0][1] = a00·b10 + a01·b11 + a02·b12
        = Σ_k a[0][k] · b[1][k]      ← 用到 a 的第 0 列和 b 的第 1 列
```
也就是 `z = a × bᵀ`（a 乘以 b 的轉置）。

> 我們已經用 HuggingFace 的 ESMFold 驗證：這個算式和 ESMFold 模組內部的計算**完全一致（差值 0）**
> （詳見第 4 章 4.9 節）。

### Triangle Attention（我們沒有實作，但 LightNobel 有處理）
同一個 block 裡還有 Triangle Attention：對每一列 i，在 (j, k) 之間做 attention。
它的中間值（attention logits）形狀是 **L × L × L × heads**，是**立方**成長，
所以實作上一定要分塊（chunking）計算，否則 L = 1000 時光這個中間值就需要數十 GB。

---

## 1.4 問題一：記憶體放不下

### 算一算 pair representation 有多大
每個數字用 FP32（4 bytes），每格 128 個數字 → **每格 512 bytes**。

```
大小 = L × L × 128 × 4 bytes = L² × 512 bytes
```

| L | L² | 一份 pair tensor（FP32） |
|---|---|---|
| 256 | 65,536 | 32 MB |
| 500 | 250,000 | 128 MB |
| 1,000 | 1,000,000 | **512 MB** |
| 2,000 | 4,000,000 | **2 GB** |
| 4,000 | 16,000,000 | **8 GB** |
| 10,000 | 100,000,000 | **51 GB** |

**長度變 2 倍，資料變 4 倍；長度變 10 倍，資料變 100 倍。**

### 實際需要的不只一份
計算一次 Triangle Multiplication 時，同時存在的資料至少有：

| 資料 | 形狀 | 說明 |
|---|---|---|
| 輸入 z | L×L×128 | pair representation 本身 |
| LayerNorm 後的 z | L×L×128 | |
| a、b | 各 L×L×128 | 投影後的兩份 |
| gate（a_g、b_g、g） | 各 L×L×128 | gating 用 |
| 輸出 | L×L×128 | |

粗估**同時有 5～8 份** pair 大小的資料。L = 2000 時，光這一步就可能需要 **10～16 GB**。
再加上 Triangle Attention 的立方級中間值，GPU 記憶體很快就不夠用（Out of Memory, OOM）。

### 為什麼問題出在 activation，不是模型權重
| 類別 | 是什麼 | 大小和 L 的關係 | ESMFold 的量級 |
|---|---|---|---|
| **權重（weights）** | 模型學到的參數 | **固定**，和 L 無關 | 約 3～4B 參數，FP16 約 7～8 GB |
| **Activation** | 計算過程中產生的中間資料 | **隨 L² 甚至 L³ 成長** | L 大時可達數十 GB |

L 小的時候，權重佔大頭；**L 一大，activation 就遠遠超過權重**。
所以「把模型變小」幫助有限，真正要處理的是 activation。這正是 LightNobel 的切入點。

### 現在的解法與代價
常見做法是 **chunking（分塊）**：一次只算一部分，算完就丟。
- 優點：記憶體峰值下降。
- 代價：要重複讀資料、無法完全平行，**時間變長**。

> **小結：** 序列長度被記憶體容量卡住，這就是 LightNobel 標題裡的
> 「*Sequence Length Limitation*」。

---

## 1.5 問題二：搬資料比計算慢（memory-bound）

### 白話直覺：廚房比喻
- **HBM / DRAM（主記憶體）= 遠處的倉庫**：很大，但來回一趟很花時間。
- **晶片內記憶體（cache、BRAM、shared memory）= 手邊的料理台**：拿取很快，但很小。
- **運算單元 = 廚師**：切菜很快。

如果廚師切一刀，就要等助手跑一趟倉庫拿下一個食材，那廚師大部分時間都在**等**。
**這時候瓶頸是「搬運」，不是「廚師的速度」。** 這就叫 **memory-bound**。
反過來，如果食材都在手邊，只是廚師切不完，就叫 **compute-bound**。

### 用數字判斷：算術強度（Arithmetic Intensity）
```
算術強度 = 運算次數（FLOP） ÷ 從主記憶體搬運的資料量（byte）
```
單位是 FLOP/byte，代表「每搬 1 byte 可以做幾次運算」。**越高越好。**

### 例子：最直白的寫法（我們的 v0）
每算一次 `a × b` 並累加（2 次運算：一次乘、一次加），都要從記憶體讀一個 `a`（4 bytes）和一個 `b`（4 bytes）：
```
算術強度 = 2 FLOP ÷ 8 bytes = 0.25 FLOP/byte
```

### 硬體能提供多少？
| 硬體 | 記憶體頻寬 | 峰值運算能力（FP32） | 平衡點（運算 ÷ 頻寬） |
|---|---|---|---|
| U55C（本專題） | 約 460 GB/s（HBM2） | 取決於設計 | — |
| 一般 GPU（例：A100） | 約 1.5～2 TB/s | 約 19.5 TFLOP/s | 約 10 FLOP/byte |

以 GPU 為例，演算法的算術強度要**超過約 10 FLOP/byte**，才能把運算單元餵飽。
v0 只有 0.25，也就是說**運算單元大約 97% 的時間都在等資料**。

### 那 Triangle Multiplication 本質上是 memory-bound 嗎？
不一定，取決於**怎麼寫**：
- 理論上：總運算量是 `2·L³·C`，但資料只有 `3·L²·C` 個數字。如果每個數字只搬一次，算術強度可以非常高（L 越大越高）。
- 實際上：晶片內的空間放不下整個 L×L×128，只能分批搬，而**分批的方式決定要重複搬幾次**。

**這就是優化的空間所在：** 同樣的計算，搬運方式不同，速度可以差幾十倍。
第 2 章會用公式說明每種手法如何減少搬運；第 4 章會看到實際數字（v2 報告中約 21% 的時間在等記憶體）。

---

## 1.6 LightNobel 的觀察與解法（高層次）

> 以下是概念層次的整理。**具體數字、實驗設定與硬體細節請以原文為準。**

### 他們的觀察
1. PPM 的記憶體瓶頸主要來自 **activation**（尤其是 pair representation），而不是權重。
2. Activation 的數值分布**在不同 token 之間差異很大**。少數 token 有特別大的數值（**outlier**）。
   （這裡的 token 指 pair representation 中的一格，也就是一個 (i, j) 位置的 128 個數字。）
3. 如果整份資料共用同一個量化尺度，outlier 會讓其他數值的精度嚴重下降。

### 他們的解法
1. **Token-wise Adaptive Activation Quantization（AAQ）**：**每個 token 各自決定量化方式**（包含尺度，
   以及如何處理 outlier），在大幅壓縮 activation 的同時維持預測準確度。
2. **專用硬體加速器**：設計能有效率地處理這種「每個 token 格式不同」的資料的運算單元
   （原文中有可重組的矩陣運算單元與向量運算單元等設計）。
3. 結果：大幅降低記憶體峰值，讓模型能處理**比 GPU 基準長得多的序列**，同時保持速度。

### 和我們的關係
| LightNobel | 我們的專題 |
|---|---|
| 整個 PPM 的完整解法 | 只取 Triangle Multiplication 的核心 einsum |
| 自己設計 ASIC 加速器（模擬評估） | 用現成的 FPGA（U55C）實際實作 |
| 提出新的量化方法（AAQ） | 實作簡化版：INT8 **per-token**（v4），並與 per-tensor 比較 |
| 新穎的架構設計 | 比較**常見的 memory-bound 手法**（tiling、寬位元、double buffering、多通道、量化） |

我們在模擬資料上已經重現了 LightNobel 的核心直覺：資料中有 1% 的 outlier token 時，
**per-token INT8 的誤差約 1%，per-tensor INT8 約 11%**，相差約 10 倍。

---

## 1.7 我們的定位

### 題目一句話
> 在 FPGA 上實作 PPM 中最吃記憶體的運算（Triangle Multiplication），
> 逐一套用常見的 memory-bound 優化手法，**量化每一招帶來多少改善、付出多少硬體代價**。

### 為什麼選 Triangle Multiplication
1. **它是 pair representation 的核心運算**，直接受 L² 資料量影響。
2. 算式簡單（本質是矩陣乘法），容易驗證正確性。
3. 可以清楚展示「同樣的計算，不同搬運方式」的差異。
4. 量化的效果（per-token vs per-tensor）可以直接呼應 LightNobel。

### 為什麼用 FPGA
- FPGA 可以**自己決定記憶體怎麼接、資料怎麼搬、運算單元擺幾個**，適合展示記憶體優化的每一個細節。
- U55C 有 HBM（多通道高頻寬記憶體），可以做多通道的實驗。
- GPU 上這些細節大多被硬體和驅動程式隱藏，比較難單獨觀察每一招的效果。

---

## 本章小結

| 問題 | 具體表現 | 例子 |
|---|---|---|
| 記憶體容量 | pair representation 隨 L² 成長 | L=2000 時一份就 2 GB，同時存在 5～8 份 |
| 記憶體頻寬 | 搬資料比計算慢 | 最直白的寫法算術強度只有 0.25 FLOP/byte |
| 精度 vs. 壓縮 | outlier 讓量化誤差變大 | per-tensor INT8 誤差是 per-token 的約 10 倍 |

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 B）：

1. L 從 1,000 變成 2,000，一份 pair tensor（FP32）從多大變成多大？為什麼是這個倍數？
2. 為什麼說長序列的瓶頸在 activation，而不是模型權重？
3. v0 的算術強度是多少 FLOP/byte？這個數字代表什麼？
4. Triangle Multiplication（outgoing）對單一 channel 來說，等同於什麼矩陣運算？
5. per-tensor 和 per-token 量化差在哪裡？為什麼有 outlier 時 per-tensor 的誤差特別大？

**下一章**解釋：為什麼 tiling、寬位元、double buffering、多通道、量化這些手法，可以從概念上解決（或緩解）這些問題。
