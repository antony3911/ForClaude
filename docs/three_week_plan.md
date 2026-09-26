# 三週計畫：architectural simulation 結果 ＋ 海報

> 校內專題競賽。**三週內（約 10/17 前）交 architectural simulation 結果與海報，再一個月後口頭報告。**
> 目標：不求頂尖，但**不要敷衍**，要有清楚的故事、自己的設計、可信的數據。
> 撰寫日期：2026-09-26；同日讀完 LightNobel 原文後修訂（方向的取捨見 `docs/competition_directions.md`）。

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

## 2. 題目與故事（讀 LightNobel 原文後修訂）

**標題（暫定）：**
> 拆解 Pair Representation 的記憶體牆：在 FPGA 上實現並量化蛋白質結構預測的資料流優化與 Token-wise 低位元量化
> *Dissecting the Pair-Representation Memory Wall on FPGA: Ablation of Dataflow Optimizations and Token-wise Low-bit Quantization for Protein Structure Prediction*

**故事三段：**
1. **問題**：PPM 的 pair representation 隨 L² 成長，Triangle Multiplication 一步就同時需要約 7 份 L×L×128 的資料 → 序列長度受限、而且 memory-bound。
   LightNobel 用 ASIC ＋ token-wise 量化解決，但只有模擬結果，也沒有拆開每一招的貢獻。
2. **方法**：在 FPGA 上逐步套用 tiling → 寬位元 → double buffering → token-wise INT8 → **INT4（依論文 C 組的設定）**，
   用真實 ESMFold activation 驗證量化假設，並用經過驗證的分析模型評估融合資料流與各種設定。
3. **結果**：每一招的效能、資源、精度貢獻；Pareto 最佳設定；U55C 上可處理的最大序列長度（以論文的 FP16 為基準）。

**和「單純比較常見手法」的差別：**
- 把每一招的貢獻拆開量化（LightNobel 只給整體結果）。
- 量化設定**有論文依據、也有真實資料驗證**，不是隨便挑一個 bit 數。
- 有經過驗證的分析模型，可以做設計空間探索，而不是只看幾個點。
- 每一招都對應到明確的瓶頸（roofline、Amdahl），不只是列數字。

**要誠實說的事（評審很可能問）：**
- 融合與執行時量化的**原則來自 LightNobel**，不是我們提出的。
- 長序列時最花時間的是 **Triangle Attention**（論文 Fig. 3：75.9%），列為未來工作。
- 容量的提升要**以 FP16 為基準**報告（融合 ＋ INT8 約 1.52 倍），不要用 FP32 基準灌水。

---

## 3. 三週時程

### 第 1 週（9/26～10/3）：量測、校正、驗證假設
| 工作 | 指令 / 負責 | 產出 |
|---|---|---|
| v0～v4 合成（進行中） | `make hls-all` | `hls_summary.csv` |
| Tile 大小掃描 | `make hls-sweep` | 4 組 tile 的報告 |
| 校正分析模型 | `make model` → 把誤差大的版本截圖給 Claude 調常數 | 模型誤差表 |
| **真實 activation（方向 D）** | Colab 或 server（CPU、短序列）跑 `dump_trimul_inputs.py` | `paper_group_C_check`、`rel_l2_grid`（INT8／INT4 × token／channel／tensor） |

### 第 2 週（10/4～10/10）：論文導向的延伸（方向 B ＋ A 的設計）
| 工作 | 產出 |
|---|---|
| **v5：INT4 per-token 的 einsum kernel**（Claude 寫程式，你跑 csim 與 HLS） | 新 kernel ＋ 正確性驗證 ＋ 合成報告 |
| 把 v5 加進分析模型、DSE、容量模型 | v4 vs v5 的 cycle、資源、誤差、最大 L |
| 融合架構的設計圖與分析（方向 A，只做設計 ＋ 模型） | 海報的架構圖、流量與容量估算 |

> 若第 1 週的真實資料顯示 INT4 誤差太大：v5 仍然合成（看硬體代價），結論改成「這個運算需要 INT8」。
> 若第 2 週時間不夠：v5 只做 csim ＋ 模型預測，HLS 留到第二階段。故事仍然完整。

### 第 3 週（10/11～10/17）：圖表與海報
| 圖 | 資料來源 | 現在能做嗎 |
|---|---|---|
| 動機：記憶體 vs L、執行時間分布（引用論文 Fig. 3） | 公式、論文 | ✅ |
| 各版本 cycle / 加速倍數（長條圖，v0～v5） | `hls_summary.csv` | 等 hls-all、v5 |
| 時間拆解（載入／計算／其他，堆疊長條） | HLS 報告的迴圈 latency | 等 hls-all |
| Roofline（各版本的位置） | `perf_model.py` ＋ 報告 | ✅（模型值） |
| Tile sweep（cycle 與 BRAM 的 trade-off）、模型 vs HLS 誤差 | `hls-sweep` ＋ 模型 | 等 hls-sweep |
| 量化：真實 a、b 和論文 C 組的對照；精度 × 粒度誤差表 | `dump_trimul_inputs.py` | 等第 1 週的資料 |
| 最大序列長度（容量模型，FP16 基準） | `perf_model.py` | ✅ |
| 融合架構圖 | 手繪 / 繪圖軟體 | 第 2 週 |

---

## 4. 海報版面（A0 直式，建議）

```
┌──────────────────────────────────────────────────┐
│ 標題、作者、指導教授                             │
├────────────────────────┬─────────────────────────┤
│ 1. 動機                │ 2. 關鍵觀察             │
│   L² 記憶體成長圖      │   roofline：memory-bound│
│   LightNobel 的做法    │   真實 a、b 的分布      │
├────────────────────────┴─────────────────────────┤
│ 3. 架構：逐步優化的 kernel ＋ 融合資料流設計     │
├────────────────────────┬─────────────────────────┤
│ 4. 逐步優化 v0→v5      │ 5. 設計空間探索         │
│   加速倍數長條圖       │   tile sweep、Pareto    │
│   時間拆解圖           │   模型 vs HLS 誤差      │
├────────────────────────┼─────────────────────────┤
│ 6. 精度                │ 7. 最大序列長度         │
│   INT8／INT4 × 粒度    │   各配置（FP16 基準）   │
├────────────────────────┴─────────────────────────┤
│ 8. 結論與未來工作                                │
│   Triangle Attention、上板、完整融合 kernel      │
└──────────────────────────────────────────────────┘
```

---

## 5. 第二階段（交海報後一個月，準備口頭報告）
- 融合 producer kernel（LayerNorm ＋ 投影 ＋ gating ＋ 量化）與 epilogue → 完整的融合 Triangle Multiplication。
- C/RTL cosim 驗證關鍵 kernel。
- 找到 U55C → 上板量測（v2、v4、v5、多通道對照）。
- Triangle Attention 的初步設計（token-wise attention 的資料流與分析模型）。
- 簡報與 demo。

---

## 6. 目前的模型預測（`make model`，L=256，8×8 tile，300 MHz）

| 版本 | 預測 cycles | GFLOP/s | 備註 |
|---|---|---|---|
| v2 | 177,029,120 | 7.28 | 與 HLS 報告（177,029,185）誤差 < 0.01% |
| v3 | 140,211,200 | 9.19 | 預測比 v2 快約 1.26 倍 |
| v4 | 73,351,168 | 17.6 | 64 路平行（常數為假設值，待校正） |

v0、v1、v4 的常數是假設值，拿到 `hls-all` 的報告後再校正。
