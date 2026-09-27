# 第 1 章　蛋白質結構預測與 pair representation

> **本章重點**
> - 蛋白質結構預測在做什麼，以及貫穿全書的變數 **L**（蛋白質長度）。
> - ESMFold 的架構：sequence representation 與 **pair representation（L × L × 128）**；什麼是 **activation**、什麼是 **token**。
> - 本專題實作的 **Triangle Multiplication** 在算什麼；為什麼長序列時最花時間的是 **Triangle Attention**。

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

### 兩個常被搞混的詞：activation 與 token

**Activation = 模型推論過程中算出來的所有中間資料。** 它是一個總稱，不是某種特定的運算。
| | 是什麼 | 做菜的比喻 | 大小會不會隨輸入改變 |
|---|---|---|---|
| **權重（weight）** | 訓練時學到的參數，例如 128×128 的 linear 矩陣 | 食譜 | 不會，固定（ESMFold 約 7.9 GB） |
| **Activation** | 用這次的輸入一步步算出來的資料 | 做菜過程中的每一盤半成品 | 會，蛋白質越長越大 |

Pair representation 就是**最主要的 activation**，但不只它一份：Triangle Multiplication 一個 block 裡，
LayerNorm 的結果、5 個 linear 的結果、gating 後的 a、b、einsum 的結果……
**每一步算出來的 L×L×128 張量都是 activation**（完整的流程圖見 3.5 節）。

**Token = 資料的「一格」。** 在不同的 representation 裡，一格代表的東西不同：
| | Sequence representation | Pair representation |
|---|---|---|
| 一個 token 代表 | 一個胺基酸 i | **一對**胺基酸 (i, j) |
| 每個 token 有幾個數 | 1024 | 128 |
| token 的數量 | L 個 | **L × L 個**（L = 1000 時是 100 萬個） |

本手冊（以及 LightNobel 的量化）說的 token，**都是指 pair representation 的一格 (i, j)**。
模型裡的 LayerNorm、linear 都是「一個 token 的 128 個數自己算自己的」，所以 token 是很自然的處理單位。

---

## 1.3 Triangle Multiplication 與 Triangle Attention

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
> （詳見第 8 章 8.9 節）。

### Triangle Attention（我們沒有實作，但 LightNobel 有處理）
同一個 block 裡還有 Triangle Attention：對每一列 i，在 (j, k) 之間做 attention。
它的中間值（attention logits）形狀是 **L × L × L × heads**，是**立方**成長，
所以 GPU 上一定要分塊（chunking）計算，否則 L = 1000 時光這個中間值就需要數十 GB。
LightNobel 則改用 token-wise 的 attention（類似 FlashAttention），根本不把整個 score matrix 存下來。

**它才是長序列時最花時間的運算。** LightNobel 在 H100 上量測 ESMFold（不分塊）的執行時間（論文 Fig. 3）：

| 運算 | 77 個胺基酸（R0271） | 1,410 個胺基酸（T1269） |
|---|---|---|
| Triangle Multiplication | **36.1%** | 14.5% |
| Triangle Attention | 29.0% | **75.9%** |
| 整個 pair representation 資料流 | 69.4% | 91.9% |

序列短時，Triangle Multiplication 佔比最高；序列一長，立方成長的 Triangle Attention 就壓過其他所有運算。
所以本專題選 Triangle Multiplication **不是因為它最花時間**，理由見 10.1 節。

---

## 本章小結

| 概念 | 一句話 |
|---|---|
| L | 蛋白質長度，全書的主角；pair representation 的大小隨 L² 成長 |
| Activation | 推論時算出來的所有中間資料；pair representation 是最主要的一份 |
| Token | pair representation 的一格 (i, j)，128 個數 |
| Triangle Multiplication | 對每個 channel 做 `z = a × bᵀ`，本專題的 kernel |
| Triangle Attention | score matrix 是 L³，長序列時佔 75.9% 的執行時間 |

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 C）：

1. Triangle Multiplication（outgoing）對單一 channel 來說，等同於什麼矩陣運算？
2. 序列很長時，ESMFold 最花時間的是哪個運算？既然如此，為什麼本專題還是先做 Triangle Multiplication？
3. 在 pair representation 裡，一個 token 代表什麼？和 sequence representation 的 token 有什麼不同？

---

**下一章**說明這份 L × L × 128 的資料為什麼會造成兩個問題：記憶體放不下、搬資料比計算慢，並介紹分析這類問題的工具（roofline、Amdahl's Law）。
