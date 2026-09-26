# 三週計畫：architectural simulation 結果 ＋ 海報

> 校內專題競賽。**三週內（約 10/17 前）交 architectural simulation 結果與海報，再一個月後口頭報告。**
> 目標：不求頂尖，但**不要敷衍**，要有清楚的故事、自己的設計、可信的數據。
> 撰寫日期：2026-09-26。

---

## 1. 「architectural simulation」可以怎麼做（不需要板子）

| 層級 | 我們的工具 | 產出 | 可信度 |
|---|---|---|---|
| 分析模型 | `make model`（`scripts/perf_model.py`） | 任意設定的 cycle、資源、最大 L | 用 HLS 報告校正後誤差 < 幾 % |
| Cycle 級估計 | `make hls` / `hls-all` / `hls-sweep`（Vitis HLS） | 每個迴圈的 latency、II、資源 | 業界標準的合成前估計 |
| RTL 模擬（可選） | `make hls ... COSIM=1` | cycle-accurate 驗證 | 最高（但慢） |

LightNobel 本身也是用模擬器評估架構，不是做出實體晶片。
**「HLS 合成 ＋ 經過驗證的分析模型」就是正統的 architectural simulation。** 上板量測留到第二階段當加分。

---

## 2. 題目與故事（建議）

**標題（暫定）：**
> 突破 Pair Representation 的記憶體牆：以 FPGA 資料流融合與 Token-wise 量化加速蛋白質結構預測
> *Breaking the Pair-Representation Memory Wall: FPGA Dataflow Fusion and Token-wise Quantization for Protein Structure Prediction*

**故事三段：**
1. **問題**：PPM 的 pair representation 隨 L² 成長，Triangle Multiplication 一步就同時需要約 7 份 L×L×128 的資料 → 序列長度受限、而且 memory-bound。
2. **方法**：在 FPGA 上逐步套用 tiling → 寬位元 → double buffering → token-wise INT8，並提出**融合的資料流架構**，讓中間值不寫回 HBM。
3. **結果**：用 HLS ＋ 分析模型量化每一步的效能、資源、精度，以及 U55C 上可處理的最大序列長度。

**和「單純比較常見手法」的差別：**
- 有自己提出的架構（融合資料流），不只是套現成技巧。
- 有經過驗證的分析模型，可以做設計空間探索，而不是只看 5 個點。
- 每一招都對應到明確的瓶頸（roofline、Amdahl），不只是列數字。

---

## 3. 三週時程

### 第 1 週（9/26～10/3）：把現有的東西量完
| 工作 | 指令 / 負責 | 產出 |
|---|---|---|
| v0～v4 合成（進行中） | `make hls-all` | `hls_summary.csv` |
| Tile 大小掃描 | `make hls-sweep` | 4 組 tile 的報告 |
| 校正分析模型 | `make model` → 把誤差大的版本截圖給 Claude 調常數 | 模型誤差表 |
| （可選）真實 activation | Colab 跑 `dump_trimul_inputs.py` | outlier 分布、量化誤差 |

### 第 2 週（10/4～10/10）：自己的設計（方向 A 精簡版）
| 工作 | 產出 |
|---|---|
| 融合架構的設計圖與資料流 | 海報的架構圖 |
| Producer kernel（LayerNorm ＋ 4 個 128×128 投影 ＋ gating ＋ INT8 量化）的 HLS 實作與 C 模擬 | 新 kernel ＋ 正確性驗證 |
| Producer 的 HLS 合成 | cycle 與資源 |
| 把融合架構加進分析模型 | 融合前後的記憶體、cycle 比較 |

> 若第 2 週時間不夠：融合架構只做「設計 ＋ 分析模型評估」，kernel 留到第二階段。故事仍然完整。

### 第 3 週（10/11～10/17）：圖表與海報
| 圖 | 資料來源 | 現在能做嗎 |
|---|---|---|
| 動機：記憶體 vs L | 公式 | ✅ |
| 各版本 cycle / 加速倍數（長條圖） | `hls_summary.csv` | 等 hls-all |
| 時間拆解（載入／計算／其他，堆疊長條） | HLS 報告的迴圈 latency | 等 hls-all |
| Roofline（各版本的位置） | `perf_model.py` ＋ 報告 | ✅（模型值） |
| Tile sweep（cycle 與 BRAM 的 trade-off） | `hls-sweep` ＋ 模型 | 等 hls-sweep |
| 量化誤差：per-token vs per-tensor | `make csim`（＋真實資料） | ✅ |
| 最大序列長度（容量模型） | `perf_model.py` | ✅ |
| 融合架構圖 | 手繪 / 繪圖軟體 | 第 2 週 |

---

## 4. 海報版面（A0 直式，建議）

```
┌──────────────────────────────────────────────┐
│ 標題、作者、指導教授                          │
├──────────────────────┬───────────────────────┤
│ 1. 動機               │ 2. 關鍵觀察            │
│  L² 記憶體成長圖       │  roofline：memory-bound│
│  LightNobel 的啟發     │  outlier 分布          │
├──────────────────────┴───────────────────────┤
│ 3. 架構：融合資料流 ＋ token-wise INT8（大圖）  │
├──────────────────────┬───────────────────────┤
│ 4. 逐步優化 v0→v4     │ 5. 設計空間探索         │
│  加速倍數長條圖        │  tile sweep、Pareto    │
│  時間拆解圖            │  模型 vs HLS 誤差       │
├──────────────────────┼───────────────────────┤
│ 6. 精度               │ 7. 最大序列長度         │
│  per-token vs tensor  │  各配置可處理的 L        │
├──────────────────────┴───────────────────────┤
│ 8. 結論與未來工作（上板、真實資料、完整融合）   │
└──────────────────────────────────────────────┘
```

---

## 5. 第二階段（交海報後一個月，準備口頭報告）
- 完成融合的 epilogue（輸出端 LayerNorm、linear、gating）→ 完整的融合 Triangle Multiplication。
- C/RTL cosim 驗證關鍵 kernel。
- 找到 U55C → 上板量測（v2、v4、多通道對照）。
- 真實 ESMFold activation 上的精度驗證。
- 簡報與 demo。

---

## 6. 目前的模型預測（`make model`，L=256，8×8 tile，300 MHz）

| 版本 | 預測 cycles | GFLOP/s | 備註 |
|---|---|---|---|
| v2 | 177,029,120 | 7.28 | 與 HLS 報告（177,029,185）誤差 < 0.01% |
| v3 | 140,211,200 | 9.19 | 預測比 v2 快約 1.26 倍 |
| v4 | 73,351,168 | 17.6 | 64 路平行（常數為假設值，待校正） |

v0、v1、v4 的常數是假設值，拿到 `hls-all` 的報告後再校正。
