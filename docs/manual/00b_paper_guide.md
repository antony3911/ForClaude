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
| **關鍵觀察** | ① 序列一長，執行時間集中在 pair representation，其中 **Triangle Attention** 暴增（Fig. 3）② activation 遠大於權重（Fig. 4）③ **channel 之間差異小、token 之間差異大**，而且 outlier 集中在特定 token（Fig. 5，與 distogram 的模式相關） |
| **軟體解法** | **AAQ**（Token-wise Adaptive Activation Quantization）：把 activation 依「在模型中的位置」分成 **A、B、C 三組**，各用不同的 inlier 精度與 outlier 數量；**每個 token 一個 scale**；**執行時用 top-k 挑出 outlier**（見下表） |
| **硬體解法** | **RMPU**（把資料切成 4-bit 小塊、可依精度重組的矩陣單元）、**VVPU**（128 條 SIMD 的向量單元：LayerNorm、Softmax、residual、**執行時量化**、bitonic top-k 排序）、**Token Aligner**（把不同格式的 token 重新排齊）、crossbar、scratchpad（token 128 KB × 2 做 double buffering）；32 個 RMPU、每個配 4 個 VVPU |
| **評估方法** | 自寫的 **Python cycle-accurate 模擬器**（和 RTL 交叉驗證，平均誤差 3.30%、都在 5% 內）＋ SystemVerilog RTL、Synopsys DC 合成（28 nm、1 GHz）、CACTI 7.0（SRAM）、Ramulator（80 GB HBM2E、2 TB/s） |
| **對象與資料** | ESMFold（ESM-2 3B），Chunk4 設定；CAMEO、CASP14、CASP15、CASP16；和 NVIDIA A100、H100 比較 |
| **結果** | TM-score 變化 < 0.001；速度最多快 **8.44×**（vs A100）／**8.41×**（vs H100）；能效最多高 **37.29×**／**43.35×**；**峰值記憶體最多降 120.05×**（和不分塊的 GPU 比；和分塊比是 1.26～5.05×）；80 GB 內最長可處理 **9,945** 個胺基酸 |
| **硬體成本** | 178.80 mm²、67.80 W；**crossbar 佔 70% 面積、68% 功耗**（資料搬運與排序比運算本身還貴） |

### AAQ 的三組設定（Sec. 4.2、Fig. 6、Fig. 11）
| 組別 | 是哪些 activation | 數值大小（平均絕對值） | 平均 outlier 數 | 選定的格式 |
|---|---|---|---|---|
| **A** | LayerNorm **之前**、接 residual 的 activation | 82.14（大） | 2.31 | **INT8** inlier ＋ **4 個** INT16 outlier |
| **B** | LayerNorm **之後**、進 linear 之前 | 4.05 | 1.69 | **INT4** inlier ＋ **4 個** INT16 outlier |
| **C** | 其餘（linear 之後的中間值等） | 3.85 | 0.64 | **INT4**，不處理 outlier |

- 量化方式：**對稱量化**，scale = 該 token 的最大絕對值 ÷ (2^(bits−1) − 1)。
- 為什麼用對稱量化：和非對稱量化相比，對稱量化若不處理 outlier，RMSE 多 27.35%；處理 outlier 後只多 9.76%（實際數值差約 0.0004），所以「對稱 ＋ outlier 處理」就夠了，硬體更簡單（Sec. 4.1）。
- 每組的設定是用**設計空間探索**（精度 × outlier 數，看 TM-score 與資料大小）選出來的（Fig. 11）。
- **權重不量化**，用 INT16（7.90 GB）；比較基準（baseline）的 activation 與權重都是 **FP16**（Table 1）。

> 詳見 1.6 節。原文：[arXiv 2505.05893](https://arxiv.org/abs/2505.05893)、[ACM DL](https://dl.acm.org/doi/10.1145/3695053.3731006)

---

## 3. LightNobel 的三個創新，白話版

### 創新一：量化的單位是「token」，而且每個 token 的待遇不同
- 一般量化是「整份資料一把尺」（per-tensor），少數特別大的值（outlier）會拖垮其他值的精度。
- LightNobel 讓**每個 token 有自己的尺**（scale），再依 activation **在模型中的位置**分成三組：接 residual 的數值大、outlier 多，給 INT8；其他給 INT4（見上表）。
- 白話：不是全班穿同一個尺寸的制服，而是量身訂做，還依體型分成三種版型。
- 本專題的對應：v4 做了最基本的「每個 token 一把尺」（INT8 per-token），模擬資料上誤差約 1%，per-tensor 約 11%。（詳見 2.8 節）
- 值得注意：Triangle Multiplication 裡的 a、b 是 linear 之後的值，依定義屬於 **C 組**（論文用 INT4、不處理 outlier）。也就是說，我們的 INT8 對 a、b 其實是**保守**的選擇，INT4 是合理的延伸。

### 創新二：outlier 另外存，而且格式對硬體友善
- 每個 token 裡絕對值最大的 k 個值（A、B 組 k = 4）當作 outlier，**用 INT16 另外存**；其他值（inlier）用 INT4 或 INT8。
- 資料依「inlier → outlier → scale → outlier 位置」的順序排好（Fig. 7），硬體讀取時不用到處跳。
- top-k 是**執行時**才算的（VVPU 用 bitonic 排序），所以每個 token 的 outlier 位置可以不同。
- 白話：大件行李另外托運，其他的壓縮裝箱，箱子依序排好方便拿。

### 創新三：專門設計能吃這種格式的硬體
- 因為不同 token 的精度不同，一般的矩陣運算單元處理起來很浪費。
- **RMPU** 把每個數切成 4-bit 小塊，INT4 用 1 塊、INT8 用 2 塊、INT16 用 4 塊，**不用先反量化**就能直接相乘（一次最多處理 20 個 token）。
- **VVPU** 負責向量類的運算：LayerNorm、Softmax、residual，以及**執行時量化**（算 scale、挑 top-k、轉成低精度）。
- **Token Aligner** 把格式不同的 token 重新排齊，讓 RMPU 的運算單元保持忙碌。
- RMPU 的結果**直接以管線方式交給 VVPU**，中間值不寫回外部記憶體；Triangle Attention 用 **token-wise 的 multi-head attention**（和 FlashAttention 類似），不必存下整個立方大小的 score matrix。
- 白話：量身訂做的衣服，也要有會處理不同版型的裁縫機，而且裁好就直接送去縫，不先堆進倉庫。

### 一句話總結論文
> **找到「token」這個合適的壓縮單位，並設計能有效率地處理這種格式的硬體，讓長序列放得下、也跑得快。**

---

## 4. 讀懂這個領域需要的概念地圖

| 概念 | 一句話 | 詳見 |
|---|---|---|
| Pair representation | 每一對胺基酸之間的關係，大小是 L × L × 128 | 1.2 節 |
| Triangle Multiplication | 用「第三個胺基酸」推論兩者的關係，本專題實作的運算 | 1.3 節 |
| Triangle Attention | 同一 block 的另一個運算，score matrix 是 L³；**長序列時最花時間** | 1.3 節 |
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
| 量化 | MEFold（只量化權重）、PTQ4Protein（per-tensor INT8） | 資料變小 | 只量化權重幫助有限；精度降低時 TM-score 下降 |
| 通用 LLM 量化 | SmoothQuant、LLM.int8()、AWQ | outlier 分離 | outlier 以外都用同一精度；GPU 上 activation 量化常常反而變慢（W4A4 比 FP16 慢） |
| 融合 kernel | OpenFold3 的 GPU 融合實作 | 中間值不落地，工作空間約 7U → 4U（分塊後約 2.2U） | 要手寫 kernel，受 GPU 架構限制 |
| **專用加速器** | **LightNobel** | 量化 ＋ 專用硬體 ＋ 管線化資料流，記憶體與速度一起改善 | 以模擬器評估，沒有流片；ASIC 做出來後無法修改 |
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
| | **管線化、執行時量化**（中間值不落地） | LightNobel 的 RMPU → VVPU 管線已經這樣做；我們在 FPGA 上用 HLS 實現同樣的原則（6.4、6.7 節） |
| | **模擬器 ＋ 交叉驗證**的評估方法 | 論文用 cycle-accurate 模擬器，並和 RTL 比對（誤差 < 5%）；我們用分析模型，並和 HLS 報告比對 |
| **簡化** | 三組混合精度 → 單一 INT8 | 三週內做得完；a、b 屬 C 組，INT4 是自然的延伸 |
| | 執行時 top-k outlier → 不另外處理 | a、b 屬 C 組，論文本身也不處理 outlier |
| | 完整模型 → 只做 Triangle Multiplication | **不是最花時間的運算**（長序列時是 Triangle Attention），但它是結構最單純的 pair 運算，適合當第一個目標（1.7 節） |
| | ASIC 模擬 → FPGA 的 HLS 合成 | 評估對象是現成可燒錄的硬體 |
| **新增（我們的）** | **現成 FPGA 平台**（U55C，HBM）上的實作 | 論文沒有公開硬體；我們的設計可以合成、之後可以上板 |
| | **逐步 ablation（v0～v4）** | 把 tiling、寬位元、double buffering、量化**各自**的效果分開量；論文只給整體結果 |
| | **完整 Triangle Multiplication 的融合設計**（含 LayerNorm、gating、**重算 g**） | 把論文的管線化原則具體套到一個運算上，並算出每一步省下多少流量與容量 |
| | **分析模型 ＋ 設計空間探索** | 用 HLS 報告校正，可預測、可找最佳設定 |

### 我們的貢獻（誠實版）
1. **在 FPGA 上實作 PPM 的 Triangle Multiplication**：搜尋範圍內沒有找到公開的類似實作；LightNobel 本身也只有模擬結果。
2. **把各個記憶體優化手法的貢獻分開量化**（ablation）：論文是整套一起評估，看不出每一招各佔多少。
3. **經過驗證的分析模型與設計空間探索**：讓結果不只是幾個數據點。

> **注意：融合（中間值不落地）與執行時量化，LightNobel 都已經做了，不是我們的新概念。**
> 我們的角色是「在現成的 FPGA 上實現並拆解這些想法」，不是提出新的原理。
>
> 也不要宣稱「比 LightNobel 好」：兩者平台不同（ASIC vs FPGA）、範圍不同（整個模型 vs 一個運算）。
> 比較好的說法是：「**以 LightNobel 的原則為基礎，在現成硬體上實作其中一個運算，並量化每一招各自的貢獻。**」

---

## 7. 讀原文時的指引

### 建議閱讀順序
1. 摘要與 Introduction 最後的貢獻列表 → 對照本章第 2、3 節。
2. 動機章節的圖（activation 大小、token-wise 分布）→ 這是「觀察」，最重要。
3. AAQ 的方法章節 → 找出三組的分法、精度、k 值。
4. 硬體架構圖 → 找出 RMPU、VVPU、Token Aligner 的位置和資料流。
5. 評估章節 → 比較對象、資料集、主要圖表。

### 讀完原文後確認的答案
| 問題 | 答案（出處） |
|---|---|
| 三類的分類依據？各用什麼精度？ | 依 activation 在模型中的**位置**：A 組 INT8 ＋ 4 個 outlier、B 組 INT4 ＋ 4 個、C 組 INT4 無 outlier（Sec. 4.2、7.1） |
| top-k 的 k 是多少？ | A、B 組 k = 4，C 組不處理；每個 token 在執行時各自挑選（Sec. 4.2、5.3） |
| 量化套用在哪些 activation？ | PPM block 裡的 activation（Fig. 6 標出每個 activation 屬於哪一組）；**權重不量化**，用 INT16 |
| 硬體怎麼評估？ | Python cycle-accurate 模擬器（和 RTL 交叉驗證）＋ Synopsys DC 28 nm 1 GHz ＋ CACTI ＋ Ramulator（Sec. 6） |
| 最長可處理的序列？ | 80 GB 內 **9,945**（CASP16 最長 6,879 的 1.45 倍）；GPU 不分塊時單卡約 1,410 |
| 比較基準的精度？ | ESMFold **FP16**（activation 113.49 GB、權重 7.90 GB，T1169 3,364 aa；Table 1） |
| 有哪些限制？ | **論文指出：** crossbar 佔 70% 面積、68% 功耗；GPU 上 activation 量化效率差，所以才需要專用硬體（Sec. 8.4、9.3）。**我們的觀察：** 評估以模擬器為主，沒有實體晶片，硬體設計也沒有公開 |

---

## 8. 報告時怎麼講

### 30 秒版
> 蛋白質結構預測模型裡有一份 L×L×128 的資料，序列越長越放不下。LightNobel 用專用晶片加上 token-wise 量化和管線化資料流解決這個問題，但只有模擬結果。我們在現成的 FPGA 上實作其中的 Triangle Multiplication，**逐步拆解每一種記憶體優化手法各自的貢獻**，並用分析模型找出最佳設計。

### 3 分鐘版（投影片順序）
1. **問題**：pair representation 隨 L² 成長，Triangle Multiplication 一步就有約 7 份；長序列時 Triangle Attention 更花時間（第 1 章）
2. **為什麼難**：memory-bound，roofline 圖（第 2 章）
3. **LightNobel 的解法**與我們的定位（本章第 5、6 節）
4. **我們的架構**：融合資料流圖（第 6 章）
5. **結果**：v0～v4 的逐步改善、DSE、可處理的序列長度（第 4、6 章）
6. **結論與未來工作**：上板、真實資料、更激進的量化

---

## 本章小結
- 領域問題：**pair representation 讓記憶體隨 L² 成長**，限制序列長度。
- LightNobel：**token-wise 自適應量化 ＋ 專用硬體**，峰值記憶體最多降約 120 倍。
- 本專題：**繼承**問題、token-wise 量化與管線化的原則，**簡化**成 INT8 與單一運算，**新增** FPGA 實作、逐步 ablation 與分析模型。
- 報告的定位：「以 LightNobel 的原則為基礎，在現成硬體上實作並量化每一招的貢獻」。

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 B）：

1. LightNobel 的三個創新分別是什麼？各用一句話說明。
2. 為什麼 LightNobel 選擇以「token」為量化單位？
3. 本專題哪些部分繼承自論文？哪些是新增的？
4. 為什麼不應該說「我們比 LightNobel 好」？比較好的說法是什麼？
5. Triangle Multiplication 的 a、b 屬於 AAQ 的哪一組？這對我們選 INT8 有什麼意義？

**接下來**從第 1 章開始，完整了解問題的細節。
