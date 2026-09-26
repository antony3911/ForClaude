# 速覽：LightNobel 論文與本專題，一次看懂

> **這一章給誰看：** 剛接手專題、想在 10 分鐘內抓到全貌的人。
>
> **讀完你會知道：** ① 這個領域在解決什麼問題　② LightNobel 做了什麼、創新在哪　③ 本專題哪些來自論文、哪些是我們自己的　④ 報告時怎麼用幾句話講清楚。
>
> 細節都在後面的章節，這裡每一段都標了「詳見」。

---

## 1. 一張圖看懂來龍去脈

```
 蛋白質結構預測（AlphaFold2、ESMFold；2024 諾貝爾化學獎）
          │  模型內部有 L×L×128 的 pair representation
          ▼
 瓶頸：序列一長，activation 以 L² 成長 → 記憶體不夠、搬資料太慢
          │
          ├─ GPU 系統優化（FastFold、ScaleFold）：更快，但記憶體問題仍在
          ├─ 分塊計算（Chunking、AutoChunk）：省記憶體，但變慢
          ├─ 量化（MEFold、各種 PTQ）：壓縮資料，但 outlier 會傷精度
          ├─ 融合 kernel（OpenFold3 的 GPU 實作）：中間值不落地
          │
          ▼
 LightNobel（ISCA 2025）：token-wise 自適應量化 ＋ 專用加速器（ASIC）
          │  軟硬體協同設計，峰值記憶體最多降約 120 倍
          ▼
 本專題：在現成的 FPGA（U55C）上，用「融合資料流 ＋ token-wise 量化」
         處理同一個瓶頸，並用分析模型做設計空間探索
```

---

## 2. 論文速讀卡

| 項目 | 內容 |
|---|---|
| **標題** | LightNobel: Improving Sequence Length Limitation in Protein Structure Prediction Model via Adaptive Activation Quantization |
| **發表** | ISCA 2025（計算機架構領域頂尖會議）；arXiv 2505.05893 |
| **類型** | 硬體與軟體協同設計（HW/SW co-design）的加速器論文 |
| **對象** | PPM（蛋白質結構預測模型），以 **ESMFold** 為基準 |
| **問題** | 長序列時 activation 記憶體爆炸 → 可處理的序列長度受限 |
| **關鍵觀察** | activation 的數值分布**以 token 為單位**有明顯特徵（論文提到與 distogram 相關的模式），不同 token 適合不同的量化方式 |
| **軟體解法** | **AAQ**（Token-wise Adaptive Activation Quantization）：把 activation 分成**三類**，各用不同的 inlier 精度與 outlier 數量；**每個 token 一個 scale**；**動態 top-k** 挑出 outlier |
| **硬體解法** | Token Aligner、**RMPU**（可重組的多精度矩陣運算單元）、**VVPU**（多功能向量運算單元）、crossbar 資料網路、scratchpad、控制器 |
| **評估** | CAMEO、CASP14、CASP15；和 NVIDIA A100、H100 比較 |
| **結果** | TM-score 變化 < 0.001；速度最多快 **8.44×**（vs A100）／**8.41×**（vs H100）；能效最多高 **37.29×**／**43.35×**；**峰值記憶體最多降 120.05×**；可處理接近萬級長度的序列 |
| **以原文為準** | 三類各自的確切精度、k 值、製程與面積功耗、最長序列的精確數字 |

> 詳見 1.6 節。原文：[arXiv 2505.05893](https://arxiv.org/abs/2505.05893)、[ACM DL](https://dl.acm.org/doi/10.1145/3695053.3731006)

---

## 3. LightNobel 的三個創新，白話版

### 創新一：量化的單位是「token」，而且每個 token 的待遇不同
- 一般量化是「整份資料一把尺」（per-tensor），少數特別大的值（outlier）會拖垮其他值的精度。
- LightNobel 讓**每個 token 有自己的尺**（scale），再依照 token 的特性分成三類，**重要或難處理的類別給比較高的精度**。
- 白話：不是全班穿同一個尺寸的制服，而是量身訂做，還依體型分成三種版型。
- 本專題的對應：v4 做了最基本的「每個 token 一把尺」（INT8 per-token），模擬資料上誤差約 1%，per-tensor 約 11%。（詳見 2.8 節）

### 創新二：outlier 另外存，而且格式對硬體友善
- 每個 token 裡最大的 k 個值（top-k）當作 outlier，**以較高精度另外存**（不需要反量化）；其他值（inlier）用低精度。
- 資料依「inlier → outlier → scale → outlier 位置」的順序排好，硬體讀取時不用到處跳。
- 白話：大件行李另外托運，其他的壓縮裝箱，箱子依序排好方便拿。

### 創新三：專門設計能吃這種格式的硬體
- 因為不同 token 的精度不同，一般的矩陣運算單元處理起來很浪費。
- **RMPU** 可以依精度重組運算單元；**VVPU** 負責向量類的運算；**Token Aligner** 負責整理不同格式的 token。
  （後兩者的具體分工是依名稱推測，細節以原文為準。）
- 白話：量身訂做的衣服，也要有會處理不同版型的裁縫機。

### 一句話總結論文
> **找到「token」這個合適的壓縮單位，並設計能有效率地處理這種格式的硬體，讓長序列放得下、也跑得快。**

---

## 4. 讀懂這個領域需要的概念地圖

| 概念 | 一句話 | 詳見 |
|---|---|---|
| Pair representation | 每一對胺基酸之間的關係，大小是 L × L × 128 | 1.2 節 |
| Triangle Multiplication | 用「第三個胺基酸」推論兩者的關係，本專題實作的運算 | 1.3 節 |
| Activation vs 權重 | 權重大小固定；activation 隨 L² 成長，才是瓶頸 | 1.4 節 |
| Memory-bound | 搬資料比計算慢 | 1.5 節 |
| 算術強度、Roofline | 判斷瓶頸在記憶體還是計算 | 2.3 節 |
| Tiling、burst、double buffering | 減少搬運、提高搬運效率、藏起等待時間 | 2.4～2.6 節 |
| 量化、outlier、per-token | 壓縮資料；outlier 為什麼傷精度 | 2.8 節 |
| HW/SW co-design | 演算法和硬體一起設計，互相配合 | 本章第 3 節 |
| FPGA、HLS | 可重新接線的晶片；把 C++ 變成電路的工具 | 第 3 章 |
| Operator fusion | 中間值不寫回記憶體 | 6.4 節 |
| Architectural simulation | 用模型和合成報告評估尚未做出的硬體 | 6.2 節 |
| TM-score | 評估預測結構和真實結構有多接近的指標（0～1，越高越好） | 附錄 A |

---

## 5. 領域地圖：大家用什麼方法處理這個問題

| 方法類別 | 代表工作 | 解決什麼 | 代價 / 限制 |
|---|---|---|---|
| GPU 系統優化 | FastFold、ScaleFold | 訓練和推論更快（平行化、kernel 優化） | 記憶體仍隨 L² 成長 |
| 分塊（chunking） | AlphaFold 內建、AutoChunk | 峰值記憶體下降 | 變慢，重複讀取資料 |
| 量化 | MEFold、蛋白質語言模型的 PTQ | 資料變小 | outlier 會傷精度；多半針對權重 |
| 融合 kernel | OpenFold3 的 GPU 融合實作 | 中間值不落地，工作空間約 7U → 4U（分塊後約 2.2U） | 要手寫 kernel，受 GPU 架構限制 |
| **專用加速器** | **LightNobel** | 量化 ＋ 專用硬體，記憶體與速度一起改善 | ASIC 要流片，成本高、無法修改 |
| **FPGA 加速** | **本專題** | 融合 ＋ 量化，實際可跑的可重組硬體 | 絕對速度不如 GPU；目前以架構模擬評估 |

> 搜尋「FPGA ＋ AlphaFold／Evoformer／Triangle Multiplication」**沒有找到公開的 FPGA 實作**，這是本專題的切入點之一（建議再用 Google Scholar 確認）。
> 參考：[FastFold](https://arxiv.org/pdf/2203.00854)、[AutoChunk](https://arxiv.org/pdf/2401.10652)、[MEFold](https://ieeexplore.ieee.org/document/10651470/)、[OpenFold3 PR #318](https://github.com/aqlaboratory/openfold-3/pull/318)

---

## 6. 本專題 vs 論文：繼承、簡化、新增

| | 內容 | 說明 |
|---|---|---|
| **繼承自論文** | 問題定義（長序列的 activation 記憶體） | 直接沿用 LightNobel 的動機 |
| | 以 ESMFold 為對象 | 同樣的模型，已驗證本專題的 einsum 與 ESMFold 完全一致 |
| | token-wise 量化的想法 | v4 的 per-token INT8 |
| | 峰值記憶體、可處理的序列長度作為指標 | 容量模型（6.10 節） |
| **簡化** | 三類混合精度 → 單一 INT8 | 三週內做得完；可列為延伸（方向 B） |
| | 動態 top-k outlier → 不另外處理 | 同上 |
| | 完整模型 → 只做 Triangle Multiplication | 最核心、最吃記憶體的運算 |
| **新增（我們的）** | **融合資料流**：LayerNorm、投影、gating、量化串成一條管線 | 論文重點在量化；我們從**融合**這個互補的角度處理記憶體 |
| | **重算 g**、**量化在源頭完成** | 用少量計算換記憶體；不多掃一次資料 |
| | **現成 FPGA 平台**（U55C，HBM） | 可實際部署、可修改；不需要流片 |
| | **逐步 ablation（v0～v4）** | 量出每一招的貢獻 |
| | **分析模型 ＋ 設計空間探索** | 用 HLS 報告校正，可預測、可找最佳設定 |

### 我們的創新點（誠實版）
1. **在 FPGA 上實作 PPM 的 Triangle Multiplication**：搜尋範圍內沒有找到公開的類似實作。
2. **融合資料流 ＋ token-wise INT8 的組合**：分別都有前例（GPU 融合、LightNobel 量化），組合起來並放在 FPGA 上是本專題的設計。
3. **經過驗證的分析模型與設計空間探索**：讓結果不只是幾個數據點。

> 不要宣稱「比 LightNobel 好」：兩者平台不同（ASIC vs FPGA）、範圍不同（整個模型 vs 一個運算）。
> 比較好的說法是：「**在現成硬體上，從互補的角度處理同一個問題，並量化各手法的貢獻。**」

---

## 7. 讀原文時的指引

### 建議閱讀順序
1. 摘要與 Introduction 最後的貢獻列表 → 對照本章第 2、3 節。
2. 動機章節的圖（activation 大小、token-wise 分布）→ 這是「觀察」，最重要。
3. AAQ 的方法章節 → 找出三類的分法、精度、k 值。
4. 硬體架構圖 → 找出 RMPU、VVPU、Token Aligner 的位置和資料流。
5. 評估章節 → 比較對象、資料集、主要圖表。

### 讀完要能補上的「待確認清單」
- [ ] 三類 token 的分類依據是什麼？各用什麼精度？
- [ ] top-k 的 k 是多少？是固定還是依類別不同？
- [ ] 量化套用在哪些 activation（全部，還是只有 pair representation）？
- [ ] 硬體的製程、面積、功耗怎麼評估（用什麼模擬器、合成工具）？
- [ ] 最長可處理的序列精確是多少？和 GPU 的上限差多少？
- [ ] 作者自己提到的限制與未來工作是什麼？

補完後，把答案寫進 1.6 節，並更新本章第 2 節的「以原文為準」欄位。

---

## 8. 報告時怎麼講

### 30 秒版
> 蛋白質結構預測模型裡有一份 L×L×128 的資料，序列越長越放不下。LightNobel 用專用晶片加上 token-wise 量化解決這個問題。我們在現成的 FPGA 上，從**融合資料流**的角度處理同一個瓶頸，再結合 token-wise 量化，並用分析模型找出最佳設計。

### 3 分鐘版（投影片順序）
1. **問題**：pair representation 隨 L² 成長，Triangle Multiplication 一步就有約 7 份（第 1 章）
2. **為什麼難**：memory-bound，roofline 圖（第 2 章）
3. **LightNobel 的解法**與我們的定位（本章第 5、6 節）
4. **我們的架構**：融合資料流圖（第 6 章）
5. **結果**：v0～v4 的逐步改善、DSE、可處理的序列長度（第 4、6 章）
6. **結論與未來工作**：上板、真實資料、更激進的量化

---

## 本章小結
- 領域問題：**pair representation 讓記憶體隨 L² 成長**，限制序列長度。
- LightNobel：**token-wise 自適應量化 ＋ 專用硬體**，峰值記憶體最多降約 120 倍。
- 本專題：**繼承**問題與 token-wise 量化，**簡化**成 INT8，**新增**融合資料流、FPGA 實作與分析模型。
- 報告的定位：「在現成硬體上，從互補的角度處理同一個問題」。

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 B）：

1. LightNobel 的三個創新分別是什麼？各用一句話說明。
2. 為什麼 LightNobel 選擇以「token」為量化單位？
3. 本專題哪些部分繼承自論文？哪些是新增的？
4. 為什麼不應該說「我們比 LightNobel 好」？比較好的說法是什麼？

**接下來**從第 1 章開始，完整了解問題的細節。
