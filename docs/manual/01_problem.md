# 第 1 章　蛋白質結構預測與 pair representation

> **本章重點**
> - 蛋白質結構預測在做什麼，以及貫穿全書的變數 **L**（蛋白質長度）。
> - **全景（top-down）**：一次預測從輸入序列到 3D 座標的完整流程；哪些是狀態、哪些是中間值、各放在哪裡。
> - **pair representation（L × L × 128）**、**activation**、**token** 是什麼。
> - 本專題實作的 **Triangle Multiplication** 在算什麼；為什麼長序列時最花時間的是 **Triangle Attention**。
> - Triangle Multiplication 裡每一個運算：**LayerNorm、linear、sigmoid、gating、mask、einsum、residual**。

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

## 1.2 全景：一次預測從頭到尾在算什麼

這一節先由上往下（top-down）看完整個流程，後面各節再放大細節。

### 第 0 層：輸入與輸出
**ESMFold 不是在預測「下一個胺基酸」**（那是 ChatGPT 這類生成模型的做法）。
- **輸入：** 一條**完整已知**的胺基酸序列（L 個字母全部都知道）。
- **輸出：** 這條蛋白質摺疊後的 3D 結構，也就是每個原子的 (x, y, z) 座標，外加每個位置的可信度。
- **什麼時候算：** 使用者丟一條序列進來，就從頭算一次；每條序列都重新算，沒有「歷史」可以沿用。

比喻：給你一條珠鍊的珠子順序，問它會捲成什麼形狀。

### 第 1 層：三個階段
```
輸入：胺基酸序列（L 個字母，幾 KB）
   │
   ▼
① ESM-2 語言模型：讀整條序列，給每個胺基酸一組特徵
   │   → s：L × 1024          （每個胺基酸的「自我描述」）
   │   → z：L × L × 128       （每一對胺基酸的「關係表」；一開始只有「在序列上相距多遠」）
   ▼
② Folding trunk：48 個 block 依序執行，每個 block 都把 s 和 z 修正得更準
   │   s、z 進去 → s、z 出來（形狀不變，內容更新）
   │   整個 trunk 會把結果送回開頭再跑幾次（recycling，預設最多 4 次）
   ▼
③ Structure module：把最後的 s、z 轉成 3D 座標
   ▼
輸出：每個原子的座標（約 L × 37 × 3 個數，很小）
```
**真正花時間、花記憶體的是 ②**：把 z 這張 L×L 的關係表反覆修正，讓它越來越接近真實的距離關係；③ 再根據這張表排出 3D 形狀。

（AlphaFold2 的對應部分叫 **Evoformer**，也有 48 個 block，同樣有 pair representation。
差別在於 AlphaFold2 用多序列比對（MSA）當輸入，ESMFold 改用語言模型。）

### 第 2 層：一個 block 裡做了什麼
每個 block 都用同一個模式修正資料：**`z ← z ＋ 修正量`**（這叫 **residual**，1.5 節）。依序是：

| 步驟 | 做什麼（白話） |
|---|---|
| Sequence attention、MLP | 先修正每個胺基酸的特徵 s |
| Sequence → pair | 把 s 的資訊加進 z |
| **Triangle Multiplication（outgoing）** | 用「i–k 的關係、j–k 的關係」推論「i–j 的關係」（**本專題的 kernel 在這裡**） |
| Triangle Multiplication（incoming） | 同上，方向反過來 |
| Triangle Attention（starting／ending） | 同樣的推論，但用 attention 決定哪些 k 比較重要（長序列時最花時間，1.4 節） |
| Pair transition（MLP） | 每一格自己再加工一次 |

### 第 3 層：一個 Triangle Multiplication 步驟
```
z（進來的關係表，L×L×128）                         ← 狀態：從上一步傳進來
 ├─ LayerNorm                  → z_ln              ← 中間值
 ├─ 5 個 linear ＋ sigmoid      → 各種投影與閘門    ← 中間值
 ├─ gating（相乘）              → a、b              ← 中間值
 ├─ einsum（跨 k 加總）         → x                 ← 中間值（本專題的 kernel）
 ├─ LayerNorm、linear、× g      → 修正量            ← 中間值
 └─ z ← z ＋ 修正量                                ← 狀態：更新後傳給下一步
```
- **狀態（完成值）：** 更新後的 z，要一直傳給下一步、下一個 block，所以必須保存。
- **中間值：** z_ln、a、b、g、x、修正量。只在這一步有用，加回 z 之後就沒用了。
  但每一個都是 L×L×128，和 z 一樣大；一般寫法會整份寫回記憶體，所以同時存在約 7 份（2.1 節）。
- **「中間值不存、直接處理完」**：不要整份算完 z_ln 再寫回去，而是一次拿一格 (i, j) 的 128 個數，在晶片裡一路做完，只把之後還需要的東西寫出去（這叫**融合**，3.5 節）。

每個運算具體在算什麼，見 1.5 節。

### 第 4 層：本專題的 kernel
只做第 3 層裡的 **einsum**：從 HBM 讀 a、b，算 `x[i][j][c] = Σ_k a[i][k][c] × b[j][k][c]`，把 x 寫回 HBM。
v0～v4 算的是同一件事，差別只在**怎麼搬資料**（第 3、4 章）。

### 東西放在哪裡？
| 東西 | 大小（L = 1000，FP32） | 存活多久 | 放在哪裡 |
|---|---|---|---|
| 輸入序列 | 幾 KB | 整次預測 | CPU 記憶體 |
| 權重（所有 linear 的矩陣） | 約 7.9 GB（FP16） | 整次預測，固定不變 | GPU 記憶體或 HBM（晶片外） |
| **s、z（狀態）** | s 約 4 MB、**z 約 512 MB** | 整個 trunk，每一步被更新 | GPU 記憶體或 HBM |
| **中間值**（z_ln、a、b、g…） | **每份約 512 MB，同時約 7 份** | 只在一個步驟內 | 一般：HBM；融合後：只在晶片內一小塊一小塊存在 |
| Triangle Attention 的 score matrix | L³ 級，數十 GB | 只在一個步驟內 | 一般：HBM（所以放不下）；LightNobel：邊算邊丟 |
| 正在計算的一小塊（tile） | 幾十 KB | 幾微秒 | **晶片內**（FPGA 的 BRAM、GPU 的 shared memory） |
| 輸出座標 | 幾百 KB | 最後 | 傳回 CPU |

---

## 1.3 兩種 representation、activation 與 token

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
**每一步算出來的 L×L×128 張量都是 activation**（流程見 1.2 節第 3 層，每個運算的意義見 1.5 節）。

**Token = 資料的「一格」。** 在不同的 representation 裡，一格代表的東西不同：
| | Sequence representation | Pair representation |
|---|---|---|
| 一個 token 代表 | 一個胺基酸 i | **一對**胺基酸 (i, j) |
| 每個 token 有幾個數 | 1024 | 128 |
| token 的數量 | L 個 | **L × L 個**（L = 1000 時是 100 萬個） |

**為什麼一個胺基酸有 1024 個數，一對胺基酸卻只有 128 個？** 這兩個數字不是由胺基酸決定的，而是**模型設計者選的特徵維度**
（ESMFold 的設定：sequence 1024、pair 128）。每個數字是一個「學出來的特徵」，就像描述一個人可以用 1024 項屬性、描述兩個人之間的關係用 128 項屬性。
設計者刻意讓 pair 的維度小，是因為 pair 的 token 數量是 L²：
```
L = 1000 時
sequence：      1,000 個 token × 1024 =     約 100 萬個數
pair：      1,000,000 個 token ×  128 =  約 1.28 億個數   ← 仍然大了 128 倍
如果 pair 也用 1024： 1,000,000 × 1024 = 約 10 億個數     ← 再大 8 倍，一份就 4 GB（FP32）
```
所以**每個 token 小，不代表總量小**；pair representation 的問題在於 token 的**數量**隨 L² 成長。
（ESM-2 語言模型本身的特徵是 2560 維，進入 folding trunk 前先投影到 1024 維。）

本手冊（以及 LightNobel 的量化）說的 token，**都是指 pair representation 的一格 (i, j)**。
模型裡的 LayerNorm、linear 都是「一個 token 的 128 個數自己算自己的」，所以 token 是很自然的處理單位。

---

## 1.4 Triangle Multiplication 與 Triangle Attention

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

上面的 `a`、`b` 是怎麼來的、einsum 之後又做了什麼，見下一節。

---

## 1.5 Triangle Multiplication 裡的每一個運算

這一節把 1.2 節第 3 層的每個運算拆開：**做什麼、公式、數字例子、在硬體上要什麼**。
這些零件（LayerNorm、linear、sigmoid、gating、residual）幾乎出現在所有深度學習模型裡（包括 ChatGPT 這類 Transformer），值得徹底弄懂。

### 完整的算式（ESMFold 的實作）
```
z_ln = LayerNorm_in(z)                               ①
a    = mask × sigmoid(linear_a_g(z_ln))              ⑤ ③ ②
            × linear_a_p(z_ln)                       ④ ②
b    = mask × sigmoid(linear_b_g(z_ln))
            × linear_b_p(z_ln)
x    = einsum(a, b)                                  ⑥
x    = linear_z(LayerNorm_out(x))                    ② ①
g    = sigmoid(linear_g(z_ln))                       ③ ②
修正量 = x × g                                        ④ 輸出閘門
z    = z + 修正量                                     ⑦（在 block 裡做）

① LayerNorm　② linear　③ sigmoid　④ gating　⑤ mask　⑥ einsum　⑦ residual
```
（為了好讀，以下例子只用 4 個 channel；實際是 128 個。）

### ① LayerNorm：把每個 token 的數字拉回標準範圍
**做什麼：** 對**一個 token 的 128 個數**，先減掉平均、再除以標準差，讓它們變成「平均 0、大小約 1」；
最後再乘上一組學出來的係數 γ、加上 β（每個 channel 各一個）。
```
mean = Σ x_c / 128
var  = Σ (x_c − mean)² / 128
y_c  = (x_c − mean) / sqrt(var + ε) × γ_c + β_c
```
**例子：** x = [2, 4, 6, 8] → mean = 5、標準差 ≈ 2.236 → [−1.34, −0.45, 0.45, 1.34]（γ = 1、β = 0 時）。

**為什麼需要：** z 每經過一步就加上一筆修正量，數值會越滾越大（這就是 LightNobel A 組數值很大的原因，5.3 節），
而且不同 token 的大小差很多。先標準化，後面的 linear 和 sigmoid 才能在穩定的範圍內工作。

**硬體的比喻：自動增益控制（AGC）。** 訊號振幅忽大忽小，進入下一級（放大器、ADC）之前先把振幅調回固定範圍，下一級才不會飽和。
LayerNorm 對每個 token 做同樣的事：減平均（去掉 DC offset）、除以標準差（調振幅），再乘 γ、加 β（每個 channel 一組學出來的增益和偏移）。

**硬體：** 兩次加總（一次算平均、一次算變異數）、一次開根號與倒數（每個 token 一次），再做 128 次減法與乘法。
只需要這個 token 自己的 128 個數，可以整個放在晶片內（10.4 節）。

### ② Linear：把 128 個特徵重新混合
**做什麼：** 一個 128 × 128 的權重矩陣 W 乘上這個 token 的 128 個數，再加上偏移 b：
```
y = W x + b          每個輸出 y_o = Σ_c W[o][c] × x_c + b_o
```
每個輸出都是**所有 128 個輸入的加權總和**，權重是訓練時學到的。模型「學到的知識」大多就存在這些矩陣裡。

**例子（2 個 channel）：** W = [[1, 2], [0, −1]]、x = [3, 1] → y = [1·3 + 2·1, 0·3 − 1·1] = [5, −1]。

**意義：一組「特徵偵測器」。** W 的每一列是一個偵測器：和輸入做內積，算出「這個 token 有多符合我要找的模式」。
硬體的比喻是**相關器（correlator）**或 FIR 濾波器：W 的一列是一組係數，輸入越像這組係數，輸出越大。
（下面假裝特徵有名字，方便理解；實際的特徵是模型自己學的，人看不懂。）
```
token 的特徵 x：[距離近, 有氫鍵, 都疏水, 電荷互斥]
偵測器 w       ：[ 1.0 ,  0.5  ,  1.0  ,  −2.0  ]   ← 「會形成穩定接觸」的偵測器

token A：[0.9, 0.1, 0.8, 0.0] → 0.9 + 0.05 + 0.8 + 0   =  1.75   ← 很符合
token B：[0.1, 0.0, 0.2, 0.9] → 0.1 + 0    + 0.2 − 1.8 = −1.5    ← 不符合
```
128×128 的 linear 就是 **128 個偵測器同時看同一個 token**，輸出 128 個新特徵。

Triangle Multiplication 有 6 個 linear（a_p、a_g、b_p、b_g、g、z），各有不同用途，但計算方式完全一樣。

**硬體：** 矩陣乘向量，每個 token 要 128 × 128 = 16,384 次乘加。權重只有 64 KB（FP32），可以一直放在晶片內（weight-stationary，6.2 節）。

### ③ Sigmoid：把任何數壓到 0～1 之間
**做什麼：**
```
sigmoid(x) = 1 ÷ (1 + e^(−x))
```
| x | −4 | −2 | 0 | 2 | 4 |
|---|---|---|---|---|---|
| sigmoid(x) | 0.018 | 0.119 | 0.5 | 0.881 | 0.982 |

很負 → 接近 0；很正 → 接近 1；0 → 剛好 0.5。它是一條平滑的 S 形曲線。

**用途：** 把 linear 算出來的任意數，變成「**要讓多少通過**」的比例（0 = 全擋、1 = 全開）。
在這裡它當作**閘門（gate）**，和下一個運算 gating 一起用。

**另一個角色：非線性。** 如果模型只有 linear，疊再多層也等於一個 linear（矩陣乘矩陣還是矩陣）。
sigmoid 這類**非線性函數**讓模型能表達複雜的關係，這是深度學習能「深」的原因之一。

**硬體：** 需要指數和除法，完整實作很貴；硬體通常用**查表**或分段直線近似（LightNobel 的 VVPU 就有指數查表，6.5 節）。

### 有了 sigmoid，為什麼還需要 LayerNorm？
兩個做的是完全不同的事：

| | LayerNorm | Sigmoid |
|---|---|---|
| 看幾個數 | **整個 token 的 128 個數一起看**（要算平均、標準差） | **每個數各自處理**，不知道其他 127 個是多少 |
| 保留什麼 | 數字之間的**相對關係**和正負號 | 只輸出 0～1，**正負號不見了** |
| 用在哪裡 | 內容和閘門兩條路都用 | **只用在閘門那條路**；內容（a_p、b_p）不經過 sigmoid |

**關鍵原因：sigmoid 會飽和。** 它只有在輸入大約 −4～4 時才有鑑別力：
```
沒有 LayerNorm：[80, 85, 90]                   → sigmoid → [1.0000, 1.0000, 1.0000]   ← 全部一樣，資訊消失
先做 LayerNorm：[80, 85, 90] → [−1.22, 0, 1.22] → sigmoid → [0.23, 0.50, 0.77]         ← 分得出差異
```
就像放大器飽和之後，輸入怎麼變，輸出都一樣。所以整條路的分工是：
```
LayerNorm（AGC：把振幅調好）→ linear（偵測器組：算出新特徵）→ sigmoid（軟開關：0～1）→ gating（乘法器：決定讓多少通過）
```

### ④ Gating：用閘門決定每個值要保留多少
**做什麼：** 兩個 linear 的結果逐元素相乘，其中一個先經過 sigmoid 當閘門：
```
a = sigmoid(linear_a_g(z_ln)) × linear_a_p(z_ln)
       └── 閘門（0～1）──┘       └─ 內容 ─┘
```
**例子：** 內容 = [3.0, −1.0, 2.0, 0.5]，閘門的原始值 = [2, −4, 0, 4] → sigmoid = [0.88, 0.018, 0.5, 0.98]
→ a = [2.64, −0.018, 1.0, 0.49]。第 2 個 channel 幾乎被關掉，第 4 個幾乎全開。

**為什麼需要：** 讓模型**依照這個 token 的內容**，決定哪些特徵要傳下去、哪些要壓掉。就像每個 channel 都有一個可調的調光器。
最後的 `修正量 = x × g` 也是 gating：決定這一步的修正要套用多少。

**硬體：** 逐元素乘法，每個 token 128 次，很便宜。

### ⑤ Mask：忽略補上去的位置
**做什麼：** 乘上 0 或 1。為了對齊，序列常會補上假的位置（padding，例如我們的程式補到 32 的倍數）；mask 把這些位置的值設成 0，讓它們不影響結果。

### ⑥ Einsum：唯一「跨 token」的運算
**做什麼：** `x[i][j][c] = Σ_k a[i][k][c] × b[j][k][c]`，也就是對每個 channel 做 `a × bᵀ` 的矩陣乘法（1.4 節）。
「einsum」是 Einstein summation 的縮寫：寫成 `"ikc,jkc->ijc"`，**輸入有、輸出沒有的索引（k）就加總起來**。

**為什麼特別：** ①～⑤ 都只用**這個 token 自己的 128 個數**；只有 einsum 要讀**整列 i 和整列 j 的所有 token**。
所以 einsum 是融合的「邊界」：前面的運算可以一個 token 一個 token 在晶片內做完，但 a、b 必須先寫出去，einsum 才能跨 token 讀取（3.5 節）。

**硬體：** 最重的一步。每個輸出 token 要 2 × L × 128 次運算，L = 1000 時約 25.6 萬次；
相比之下，6 個 linear 加起來每個 token 約 19.7 萬次。**L 越長，einsum 越是主角**，這也是本專題選它做 kernel 的原因之一。

### a、b 是什麼？為什麼只有它們要寫出去？
**a、b 是兩種「訊息」。** a[i][k] 是「i–k 這條邊」要提供的訊息，b[j][k] 是「j–k 這條邊」的訊息。
兩者都來自 z_ln，只是用不同的 linear（不同的偵測器）做出來，扮演不同的角色。
einsum 把它們配對：channel c 可以想成一個「問題」（例如「靠得近嗎？」），
i–k 和 j–k 在 c 上都大，乘起來就大，代表第三者 k 提供了「i 和 j 有關係」的證據；把所有 k 的證據加總，就是 (i, j) 的結論。

**為什麼要寫出去？** a[i][k] 會被 x[i][0]～x[i][L−1] 共 **L 個輸出**用到，而且這些輸出分散在整個計算的不同時間點；
a[i][k] 產生時，大部分用得到它的輸出都還沒輪到，只能先存起來（reuse distance 很長，3.5 節）。
相比之下，z_ln、a_p、a_g 只在算同一個 token 時用一次，可以留在晶片內。

**融合後，每個值要不要存：**

| 值 | 誰用它 | 用幾次、多久之後 | 要存到記憶體嗎？ |
|---|---|---|---|
| **z（輸入）** | LayerNorm、最後的 residual、重算 g | 一開始用，最後又要用 | **要**（狀態） |
| z_ln、a_p、a_g、b_p、b_g | linear、gating | 同一個 token 馬上用完 | 不用 |
| **a、b** | einsum | 被 L 個輸出用，分散在整個計算中 | **要**（融合的邊界） |
| g | 最後的 `x × g` | 要等 einsum 做完才用 | 可以存，也可以最後從 z 重算（本專題選重算，3.6 節） |
| x（einsum 的結果） | LayerNorm_out、linear_z、× g | 同一個輸出 token 馬上用完 | 不用 |
| **新的 z** | 下一個步驟 | 要傳下去 | **要**（狀態） |

所以融合後記憶體裡只剩 **z（進、出各一份）＋ a、b（INT8，約半份）≈ 2.5 份**，一般寫法約 7 份（10.3 節）。

### ⑦ Residual：修正量加回原本的值
**做什麼：** `z = z + 修正量`。每一步都不是重算 z，而是在原本的 z 上**加一點修正**。

**為什麼需要：** 讓資訊可以一路傳下去、每一層只要學「還差多少」，模型才能疊到 48 層還訓練得起來。
**副作用：** 48 個 block 不斷累加，z 的數值越來越大（LightNobel 的 A 組，5.3 節），所以每一步開頭都要先做 LayerNorm。

### 總整理
| 運算 | 輸入範圍 | 每個 token 的運算量 | 在硬體上要什麼 |
|---|---|---|---|
| ① LayerNorm | 一個 token | 約 5 × 128 | 加總、開根號、乘法 |
| ② Linear（× 6） | 一個 token ＋ 權重 | 6 × 2 × 128² ≈ 19.7 萬 | 大量乘加器、晶片內存權重 |
| ③ Sigmoid | 一個值 | 128（每個值一次） | 指數查表 |
| ④ Gating、⑤ Mask | 一個 token | 128 | 逐元素乘法 |
| **⑥ Einsum** | **跨 token（整列 i、整列 j）** | **2 × L × 128** | 大量乘加器、**大量搬運**（第 3、4 章） |
| ⑦ Residual | 一個 token | 128 | 加法 |

---

## 本章小結

| 概念 | 一句話 |
|---|---|
| L | 蛋白質長度，全書的主角；pair representation 的大小隨 L² 成長 |
| Activation | 推論時算出來的所有中間資料；pair representation 是最主要的一份 |
| Token | pair representation 的一格 (i, j)，128 個數 |
| Triangle Multiplication | 對每個 channel 做 `z = a × bᵀ`，本專題的 kernel |
| Triangle Attention | score matrix 是 L³，長序列時佔 75.9% 的執行時間 |
| 狀態 vs 中間值 | z 要一直傳下去（狀態）；z_ln、a、b、g、x 只在一步內有用（中間值），卻和 z 一樣大 |
| 基本零件 | LayerNorm（標準化）、linear（混合特徵）、sigmoid（壓到 0～1）、gating（閘門）、einsum（唯一跨 token）、residual（加回去） |

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 C）：

1. Triangle Multiplication（outgoing）對單一 channel 來說，等同於什麼矩陣運算？
2. 序列很長時，ESMFold 最花時間的是哪個運算？既然如此，為什麼本專題還是先做 Triangle Multiplication？
3. 在 pair representation 裡，一個 token 代表什麼？和 sequence representation 的 token 有什麼不同？
4. ESMFold 是在預測「下一個胺基酸」嗎？它的輸入和輸出分別是什麼？
5. 在一個 Triangle Multiplication 步驟裡，哪些是「狀態」、哪些是「中間值」？為什麼中間值會佔很多記憶體？
6. sigmoid 的輸出範圍是多少？它和 gating 一起用時扮演什麼角色？
7. Triangle Multiplication 的運算中，哪一個需要讀取「其他 token」的資料？這為什麼決定了融合的邊界？
8. 既然 sigmoid 會把數字壓到 0～1，為什麼還需要先做 LayerNorm？
9. a 和 b 分別代表什麼？為什麼融合之後它們仍然必須寫回記憶體，而 z_ln 不用？

---

**下一章**說明這份 L × L × 128 的資料為什麼會造成兩個問題：記憶體放不下、搬資料比計算慢，並介紹分析這類問題的工具（roofline、Amdahl's Law）。
