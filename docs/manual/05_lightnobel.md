# 第 5 章　案例研究（上）：LightNobel 的觀察、演算法與成果

> **本章重點**
> - LightNobel（ISCA 2025）的速讀卡：問題、觀察、解法、評估、結果。
> - 三個關鍵觀察，以及從觀察推出的 **AAQ（token-wise 自適應量化）**：A、B、C 三組各用什麼精度、為什麼。
> - 記憶體到底靠什麼省下來：**量化**（常數倍）與**不存中間值**（消掉 L³ 項）；問題是否真的被解決。
> - 這個領域的其他做法，以及讀原文時要注意什麼。

---

## 5.1 論文速讀卡

| 項目 | 內容 |
|---|---|
| **標題** | LightNobel: Improving Sequence Length Limitation in Protein Structure Prediction Model via Adaptive Activation Quantization |
| **發表** | ISCA 2025（計算機架構領域頂尖會議）；arXiv 2505.05893 |
| **類型** | 硬體與軟體協同設計（HW/SW co-design）的加速器論文 |
| **對象** | PPM（蛋白質結構預測模型），以 **ESMFold** 為基準 |
| **問題** | 長序列時 activation 記憶體爆炸 → 可處理的序列長度受限 |
| **關鍵觀察** | ① 序列一長，執行時間集中在 pair representation，其中 **Triangle Attention** 暴增（Fig. 3）② activation 遠大於權重（Fig. 4）③ **channel 之間差異小、token 之間差異大**，而且 outlier 集中在特定 token（Fig. 5，與 distogram 的模式相關） |
| **軟體解法** | **AAQ**（Token-wise Adaptive Activation Quantization）：把 activation 依「在模型中的位置」分成 **A、B、C 三組**，各用不同的 inlier 精度與 outlier 數量；**每個 token 一個 scale**；**執行時用 top-k 挑出 outlier**（見下表） |
| **硬體解法** | **RMPU**（把資料切成 4-bit 小塊、可依精度重組的矩陣單元）、**VVPU**（128 條 SIMD 的向量單元：LayerNorm、Softmax、residual、**執行時量化**、bitonic top-k 排序）、**Token Aligner**（把不同格式的 token 重新排齊）、crossbar、scratchpad（token 128 KB × 2 做 double buffering）；32 個 RMPU、每個配 4 個 VVPU |
| **評估方法** | 自寫的 **Python cycle-accurate 模擬器**（和 RTL 交叉驗證，平均誤差 3.30%、都在 5% 內）＋ SystemVerilog RTL、Synopsys DC 合成（28 nm、1 GHz）、CACTI 7.0（SRAM）、Ramulator（80 GB HBM2E、2 TB/s） |
| **對象與資料** | ESMFold（ESM-2 3B），Chunk4 設定；CAMEO、CASP14、CASP15、CASP16；和 NVIDIA A100、H100 比較 |
| **結果** | TM-score 變化 < 0.001；速度最多快 **8.44×**（vs A100）／**8.41×**（vs H100）；能效最多高 **37.29×**／**43.35×**；**峰值記憶體最多降 120.05×**（和不分塊的 GPU 比；和分塊比是 1.26～5.05×）；80 GB 內最長可處理 **9,945** 個胺基酸 |
| **硬體成本** | 178.80 mm²、67.80 W；**crossbar 佔 70% 面積、68% 功耗**（資料搬運與排序比運算本身還貴） |

### 一句話總結論文
> **找到「token」這個合適的壓縮單位，並設計能有效率地處理這種格式的硬體，讓長序列放得下、也跑得快。**

---

## 5.2 他們的觀察

### 四個觀察
1. 序列一長，執行時間幾乎都花在 pair representation（91.9%），其中 Triangle Attention 最重（1.4 節）。
2. PPM 的記憶體瓶頸主要來自 **activation**，而不是權重（2.1 節）。
3. **同一個 token 的 128 個 channel 數值差不多，但 token 和 token 之間差很多**，而且 outlier 集中在特定 token（和 distogram 的模式相關）。
   （這裡的 token 指 pair representation 中的一格，也就是一個 (i, j) 位置的 128 個數字。）
   → 所以「每個 token 一把尺」比「每個 channel 一把尺」更合適。
4. **不同位置的 activation 特性也不同**：接 residual 的值很大（平均絕對值約 82）、outlier 多；其他位置的值小（約 4）、outlier 少。

### 我們重現了核心直覺
在模擬資料中放入 1% 的 outlier token：**per-token INT8 的誤差約 1%，per-tensor INT8 約 11%**，相差約 10 倍。
這說明了 LightNobel 為什麼要以 token 為單位量化。

> **模擬資料和論文的差異：** 我們的 outlier 是「整個 token 放大 30 倍」，對應論文觀察 3（token 之間差很多）；
> 論文另外還有「token 內少數幾個值特別大」的 outlier，我們沒有模擬。
> 另外，a、b 是 linear 之後的值，依論文的分法屬於 **C 組**（outlier 很少），所以我們的模擬其實比真實情況更嚴苛。
> 用真實 ESMFold 資料（8.9 節）重跑，可以確認這一點。

---

## 5.3 AAQ：三組、混合精度與 outlier

### AAQ 的三組設定（Sec. 4.2、Fig. 6、Fig. 11）
| 組別 | 是哪些 activation | 數值大小（平均絕對值） | 平均 outlier 數 | 選定的格式 |
|---|---|---|---|---|
| **A** | LayerNorm **之前**、接 residual 的 activation | 82.14（大） | 2.31 | **INT8** inlier ＋ **4 個** INT16 outlier |
| **B** | LayerNorm **之後**、進 linear 之前 | 4.05 | 1.69 | **INT4** inlier ＋ **4 個** INT16 outlier |
| **C** | 其餘（linear 之後的中間值等） | 3.85 | 0.64 | **INT4**，不處理 outlier |

**三組在計算流程中的位置**（以 Triangle Multiplication 為例；和胺基酸的種類無關）：
```
     ┌────── residual：每個 block 算完，把更新量加回 z ───────┐
     ▼                                                        │
  z（pair representation 本身）  ← A 組                       │
     │ LayerNorm                                              │
  z_ln                           ← B 組                       │
     │ linear × 5（乘上權重）                                 │
  a_p、a_g、a、b、g …            ← C 組（本專題的 a、b）      │
     │ einsum … 算出更新量 ───────────────────────────────────┘
```
**為什麼三組的數值差這麼多（白話）：**
- **A 組很大**（平均 82，大部分落在約 ±143 內）：pair representation 每經過一個 block 就加上一筆更新量，
  48 個 block 一直累加、沒有被縮回來，所以數值越滾越大，也容易出現特別大的值。
- **B 組變小**（平均 4，約 ±3.3）：LayerNorm 把每個 token 標準化到大小約 1，但最後乘上的可學習係數 γ 會放大某些 channel，所以仍有一些 outlier。
- **C 組最平滑**（平均 3.9，約 ±2.3）：乘上權重矩陣時，128 個數被混合加總，特別大的值被攤平，outlier 最少，INT4 就夠。

- 量化方式：**對稱量化**，scale = 該 token 的最大絕對值 ÷ (2^(bits−1) − 1)。scale 會和資料一起存下來，用的時候乘回去，數值回到原本的大小（為什麼這不是「標準化」，見 4.1 節；尺的格式與成本見 4.3 節）。
- 為什麼用對稱量化：和非對稱量化相比，對稱量化若不處理 outlier，RMSE 多 27.35%；處理 outlier 後只多 9.76%（實際數值差約 0.0004），所以「對稱 ＋ outlier 處理」就夠了，硬體更簡單（Sec. 4.1）。
- 每組的設定是用**設計空間探索**（精度 × outlier 數，看 TM-score 與資料大小）選出來的（Fig. 11）。
- **權重不量化**，用 INT16（7.90 GB）；比較基準（baseline）的 activation 與權重都是 **FP16**（Table 1）。

### outlier 怎麼存：格式對硬體友善
- 每個 token 裡絕對值最大的 k 個值（A、B 組 k = 4）當作 outlier，**用 INT16 另外存**；其他值（inlier）用 INT4 或 INT8。
- 資料依「inlier → outlier → scale → outlier 位置」的順序排好（Fig. 7），硬體讀取時不用到處跳。
- top-k 是**執行時**才算的（VVPU 用 bitonic 排序），所以每個 token 的 outlier 位置可以不同。
- 白話：大件行李另外托運，其他的壓縮裝箱，箱子依序排好方便拿。

---

## 5.4 記憶體是靠什麼省下來的？

LightNobel 的記憶體節省來自**兩個不同的機制**，論文把它們放在一起報告，所以不容易看出各自的貢獻。

### 兩個機制
| 機制 | 做了什麼 | 效果 | LightNobel 的數字 | 本專題的對應 |
|---|---|---|---|---|
| **① 量化** | 每個數從 16 bit 變成 4～8 bit | 每份資料變小（常數倍） | 資料流程相同時，activation 113.49 → 65.60 GB，總量約 1/1.65（Table 1） | v4（INT8）、v5（INT4）（第 4 章、10.4 節） |
| **② 不存中間值** | 中間值算完馬上用掉，不整份寫回記憶體 | 份數變少；**Triangle Attention 的 L³ 項直接消失** | 和不分塊的 GPU 比，峰值最多 1/120 | 融合設計（約 7 份 → 約 2.5 份，10.3 節） |

機制 ② 為什麼效果大？GPU 不分塊時，Triangle Attention 會存下整個 L×L×L 的 score matrix。
以 ESMFold 的 4 個 head、FP16 粗估：L = 1,410 約 22 GB，L = 2,034 約 67 GB，L = 3,364 約 300 GB。
LightNobel 的 token-wise attention 算一部分、用掉、丟掉，從來不存整個矩陣，立方成長的部分就不見了（原理見 6.6 節）。

### 看懂論文的「120 倍」
- 120.05 倍是和「**不分塊**」的 GPU 比（GPU 會存下整個立方大小的 score matrix）。
- 和「**有分塊**」的 GPU 比只有 **1.26～5.05 倍**。
- 量化本身（AAQ）在同樣資料流下是 121.39 GB → 73.50 GB，約 **1.65 倍**（Table 1）。

所以大部分的節省來自機制 ②。本專題的融合 ＋ INT8 讓最大序列長度提升約 1.52 倍（9.4 節），
和論文中「量化 ＋ 不落地」這部分的量級一致，並不是做得特別差。

### 問題真的被解決了嗎？（誠實版）
**沒有「根本解決」，而是「把上限往後推了很多」。**
- pair representation 仍然隨 **L²** 成長。量化只是乘上一個常數，曲線的形狀不變；而 L 只和記憶體的平方根成正比。
- 真正大幅延長序列的，是把 **L³** 那一項消掉（機制 ②）。
- 論文的成果：80 GB 內最長 **9,945** 個胺基酸；GPU 不分塊時約 **1,410**。GPU 分塊也能跑長序列，但慢很多（LightNobel 在分塊的情況下快 3.67～8.44 倍）。

一句話：**LightNobel 讓長序列「放得下」又「跑得快」，但 L² 的成長仍在。**

---

## 5.5 領域地圖：大家用什麼方法處理這個問題

| 方法類別 | 代表工作 | 解決什麼 | 代價 / 限制 |
|---|---|---|---|
| GPU 系統優化 | FastFold、ScaleFold | 訓練和推論更快（平行化、kernel 優化） | 記憶體仍隨 L² 成長 |
| 分塊（chunking） | AlphaFold 內建、AutoChunk | 峰值記憶體下降 | 變慢，重複讀取資料 |
| 量化 | MEFold（只量化權重）、PTQ4Protein（per-tensor INT8） | 資料變小 | 只量化權重幫助有限；精度降低時 TM-score 下降 |
| 通用 LLM 量化 | SmoothQuant、LLM.int8()、AWQ | outlier 分離 | outlier 以外都用同一精度；GPU 上 activation 量化常常反而變慢（W4A4 比 FP16 慢） |
| 融合 kernel | OpenFold3 的 GPU 融合實作 | 中間值不落地，工作空間約 7U → 4U（分塊後約 2.2U） | 要手寫 kernel，受 GPU 架構限制 |
| **專用加速器** | **LightNobel** | 量化 ＋ 專用硬體 ＋ 管線化資料流，記憶體與速度一起改善 | 以模擬器評估，沒有流片；ASIC 做出來後無法修改 |
| **FPGA 加速** | **本專題** | 逐步拆解各手法的貢獻；可重組、可實際部署的硬體 | 只做一個運算；絕對速度不如 GPU；目前以架構模擬評估 |

> 搜尋「FPGA ＋ AlphaFold／Evoformer／Triangle Multiplication」**沒有找到公開的 FPGA 實作**，這是本專題的切入點之一（建議再用 Google Scholar 確認）。
> 參考：[FastFold](https://arxiv.org/pdf/2203.00854)、[AutoChunk](https://arxiv.org/pdf/2401.10652)、[MEFold](https://ieeexplore.ieee.org/document/10651470/)、[OpenFold3 PR #318](https://github.com/aqlaboratory/openfold-3/pull/318)

---

## 5.6 讀原文時的指引

### 建議閱讀順序
1. 摘要與 Introduction 最後的貢獻列表 → 對照本章 5.1～5.3 節。
2. 動機章節的圖（activation 大小、token-wise 分布）→ 這是「觀察」，最重要。
3. AAQ 的方法章節 → 找出三組的分法、精度、k 值。
4. 硬體架構圖 → 找出 RMPU、VVPU、Token Aligner 的位置和資料流。
5. 評估章節 → 比較對象、資料集、主要圖表。

### 讀完原文後確認的答案
| 問題 | 答案（出處） |
|---|---|
| 三組的分類依據？各用什麼精度？ | 依 activation 在模型中的**位置**：A 組 INT8 ＋ 4 個 outlier、B 組 INT4 ＋ 4 個、C 組 INT4 無 outlier（Sec. 4.2、7.1） |
| top-k 的 k 是多少？ | A、B 組 k = 4，C 組不處理；每個 token 在執行時各自挑選（Sec. 4.2、5.3） |
| 量化套用在哪些 activation？ | PPM block 裡的 activation（Fig. 6 標出每個 activation 屬於哪一組）；**權重不量化**，用 INT16 |
| 硬體怎麼評估？ | Python cycle-accurate 模擬器（和 RTL 交叉驗證）＋ Synopsys DC 28 nm 1 GHz ＋ CACTI ＋ Ramulator（Sec. 6） |
| 最長可處理的序列？ | 80 GB 內 **9,945**（CASP16 最長 6,879 的 1.45 倍）；GPU 不分塊時單卡約 1,410 |
| 比較基準的精度？ | ESMFold **FP16**（activation 113.49 GB、權重 7.90 GB，T1169 3,364 aa；Table 1） |
| 有哪些限制？ | **論文指出：** crossbar 佔 70% 面積、68% 功耗；GPU 上 activation 量化效率差，所以才需要專用硬體（Sec. 8.4、9.3）。**我們的觀察：** 評估以模擬器為主，沒有實體晶片，硬體設計也沒有公開 |

---

## 本章小結

- **問題**：長序列時 activation 以 L²（attention 以 L³）成長，GPU 放不下、也跑不快。
- **觀察**：channel 之間差異小、token 之間差異大；不同位置的 activation 特性不同。
- **演算法**：每個 token 一把尺；A 組 INT8 ＋ 4 個 outlier、B 組 INT4 ＋ 4 個 outlier、C 組 INT4。
- **記憶體**：量化省常數倍（約 1.65×）；不存 L³ 的 score matrix 才讓峰值降到上百倍。
- **下一章**：這些演算法要有效率，需要專門的硬體。

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 C）：

1. LightNobel 的三個創新分別是什麼？各用一句話說明。
2. 為什麼 LightNobel 選擇以「token」為量化單位？
3. Triangle Multiplication 的 a、b 屬於 AAQ 的哪一組？這對我們選 INT8 有什麼意義？
4. LightNobel 的記憶體節省來自哪兩個機制？哪一個讓峰值記憶體降到上百倍？

---

**下一章**從硬體設計者的角度，拆開 LightNobel 的每個硬體單元：它們是什麼、原理是什麼、為什麼這樣設計。
