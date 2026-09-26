# 競賽方向：比「單純比較常見手法」更有亮點、但做得完的選項

> 背景：原本的題目（在 FPGA 上比較 tiling、寬位元、double buffering、多通道、INT8）完整但偏教科書。
> 以下方向都**建立在已經寫好的 `fpga/trimul/` 之上**，不用從頭開始，並依「亮點 × 可行性」排序。
> 撰寫日期：2026-09-26；**同日讀完 LightNobel 原文後修訂**（修訂理由見最後一節）。

---

## 先說結論（讀原文後修訂版）

| 方向 | 一句話 | 亮點 | 需要板子？ | 需要 GPU？ | 估計時間 | 風險 |
|---|---|---|---|---|---|---|
| **B. 論文導向的低位元量化（INT4）** | 依論文分組，a、b 屬 C 組 → 在 FPGA 上實作 **INT4 per-token** 的 einsum（v5），並和 v4 比較 | ★★★ | 否（HLS） | 否（真實資料用 D） | 1～1.5 週 | 中 |
| **C. 分析模型 ＋ 設計空間探索** | 建立能預測 cycle、資源、最大 L 的模型，自動找最佳設定 | ★★★ | 否 | 否 | 已完成大半 | 低 |
| **D. 真實 activation 分析** | 用 ESMFold 真實的 a、b 檢查「屬於 C 組」的假設，並做精度 × 粒度的誤差表 | ★★★ | 否 | Colab，或 server 用 CPU 跑短序列 | 2～3 天 | 低 |
| **A. 融合版 Triangle Multiplication** | LayerNorm、投影、gating、量化串成管線，中間值不落地 | ★★ | 否 | 否 | 設計＋模型 3 天；kernel 2～3 週 | 中 |
| **E. 多 CU ＋ HBM 通道擴展** | 複製多份 kernel，展示頻寬隨通道數擴展 | ★★ | **是** | 否 | 1～2 週（有板子後） | 看板子 |
| **F. Triangle Attention** | 長序列真正的瓶頸（1,410 aa 時佔 75.9%），需要 token-wise attention | ★★★ | 否 | 否 | 超過 3 週 | 高 |

**建議組合：v0～v4 的 ablation（主軸）＋ C（方法論骨架）＋ D（驗證關鍵假設）＋ B（論文導向的延伸，v5）。**
A 保留為「設計 ＋ 分析模型評估」，kernel 當加分；F 列為未來工作。

### 為什麼和第一版的建議不同
| | 第一版 | 修訂後 | 原因（LightNobel 原文） |
|---|---|---|---|
| A 融合 | 主推 ★★★ | ★★，只做設計＋模型 | 論文的 RMPU → VVPU 管線與執行時量化已經做到「中間值不落地」，**不是新概念**；而且 producer kernel 工作量大 |
| B 量化 | 「分類 ＋ 混合精度 ＋ outlier」，★★★、3～4 週 | 只做 **INT4 per-token**（v5），1～1.5 週 | 論文把 a、b 這類 activation（C 組）用 **INT4、不處理 outlier**；top-k 只在 A、B 組需要 |
| D 真實資料 | 動機數據，★★ | ★★★，**驗證關鍵假設** | 「a、b 屬於 C 組」是 B 的前提；我們的模擬資料（1% token ×30）比論文描述的 C 組嚴苛 |
| 定位 | 「從融合這個互補的角度」 | 「**在現成 FPGA 上實作並拆解每一招的貢獻**」 | 論文只給整體結果，沒有 ablation；而且論文指出 GPU 做低位元 activation 量化效率很差 |

---

## 主軸：v0～v4 的 ablation（已完成大半）

把 tiling、寬位元、double buffering、多通道、量化**一次加一招**，量出每一招的效果與代價。
LightNobel 是整套一起評估，看不出每一招各佔多少；這是我們最直接的貢獻。
數據來源：`make hls-all`、`make hls-sweep`、`make model`。

---

## B. 論文導向的低位元量化：INT4 per-token（v5）

### 依據
LightNobel 依 activation 在模型中的**位置**分成三組（Sec. 4.2、Fig. 11）：
| 組別 | 位置 | 選定格式 |
|---|---|---|
| A | LayerNorm 之前、接 residual | INT8 ＋ 4 個 INT16 outlier |
| B | LayerNorm 之後、進 linear 之前 | INT4 ＋ 4 個 INT16 outlier |
| **C** | 其他（**a、b 在這裡**） | **INT4，不處理 outlier** |

我們的 v4 對 a、b 用 INT8，**比論文保守**。v5 用 INT4，和論文的設定一致。

### 做法
1. **先在 Python 確認精度**（D 的誤差表）：INT4 per-token 在真實 a、b 上的 einsum 誤差是否可接受。
2. **v5 kernel**：從 v4 改。一個 512-bit word 放 **128 個 INT4，剛好是一個完整的 token**；
   每個 byte 拆成兩個 4-bit 值再做乘加，scale 的處理和 v4 相同。
3. csim 驗證 → HLS 合成 → 和 v4 比較 cycle、資源、誤差；加進分析模型。

### 預期亮點
- a、b 的資料量再減半：einsum 部分的讀取量、容量都下降（容量模型見手冊 6.10 節）。
- LightNobel 指出 GPU 做低位元 activation 量化效率很差（W4A4 比 FP16 還慢，Sec. 9.3），所以才需要專用硬體；
  **v5 展示 FPGA 可以用客製的資料路徑做到這件事**，而且不用流片。

### 風險
- INT4 的打包與解包在 HLS 要小心（位元操作、sign extension）。
- 如果 D 的結果顯示 INT4 誤差太大，就把結論改成「在這個運算上 INT8 是必要的」，這也是有價值的發現。

### 延伸（不在三週內）
- 處理 z（A 組）：每個 token 保留 4 個 outlier（INT16），其餘 INT8，需要 top-k 硬體。

---

## C. 分析模型 ＋ 設計空間探索（方法論骨架）

### 做法
1. 從 v2 報告寫出公式，例如每個 k 迴圈 ≈ 載入（約 64 ＋ 延遲）＋ 計算（TI·TJ·C/16 ＋ 深度）。
2. 對 tile 大小、平行度、精度建立 **cycle 模型、資源模型、容量模型**（最大 L；以 FP32 與 **FP16** 兩種基準計算）。
3. 用 HLS 報告驗證模型誤差（目標 < 10%）。
4. 用模型掃過上百種組合，畫出 Pareto 前緣，挑出最佳設定並實際合成驗證。

### 為什麼值得做
- **不需要板子**：server63 就能跑完。
- 和 LightNobel 的評估方法對應：論文用 cycle-accurate 模擬器，並和 RTL 交叉驗證（平均誤差 3.30%）；
  我們用分析模型，並和 HLS 報告交叉驗證。
- 把「比較幾個版本」提升成「**可以預測、可以最佳化的設計方法**」。

---

## D. 真實 activation 分析（驗證關鍵假設）

在 Colab（或記憶體夠大的 server，用 CPU 跑短序列）上執行 `python/dump_trimul_inputs.py`，對幾條蛋白質、多個 block：
- **和論文對照**：每個 token 的平均絕對值、每個 token 超過 3σ 的值有幾個
  → 和論文 C 組（3.85、0.64 個）比較，確認 a、b 是否真的屬於 C 組。（輸出的 `paper_group_C_check`）
- **精度 × 粒度的誤差表**：INT8／INT4 × per-token／per-channel／per-tensor 的 einsum 誤差。（輸出的 `rel_l2_grid`）
  per-channel 是 LLM 常用的做法，論文認為 PPM 的特性（channel 之間差異小、token 之間差異大）更適合 per-token。
- 不同 block 深度的差異。

產出 2～3 張圖；**直接決定 B 要用 INT4 還是維持 INT8**。

---

## A. 融合版 Triangle Multiplication（設計 ＋ 分析模型；kernel 為加分）

### 問題
真實的 Triangle Multiplication 一步要產生很多份 L×L×128 的中間值：
```
z ──LayerNorm──► z_ln ──┬─ linear_a_p, linear_a_g ──► a   （L²×128）
                         ├─ linear_b_p, linear_b_g ──► b   （L²×128）
                         └─ linear_g ──────────────► g   （L²×128）
a, b ──einsum──► x ──LayerNorm_out──► linear_z ──► ×g ──► 輸出
```
一般實作會同時存在 **約 7 份** pair 大小的張量（GPU 融合實作的分析也是這個量級）。

### 做法：兩個融合 kernel
```
Kernel 1（producer）：讀 z 一次
    LayerNorm → 4 個 128×128 linear → sigmoid gating → mask → token-wise 量化
    只寫出：a、b（INT8 或 INT4，含 scale）
Kernel 2（consumer）：現有的 v4／v5 ＋ 輸出 epilogue
    einsum → LayerNorm_out → linear_z → 重新從 z 算 g → 相乘 → 寫出結果
```
- 128×128 的權重只有 64 KB（FP32），放得進晶片內。
- `g` 不存，在 epilogue 從 z 重算：多花的計算比例是 128 ÷ L，L 越大越划算。

### 定位
**融合與執行時量化的原則來自 LightNobel**（RMPU → VVPU 管線、VVPU 的執行時量化）。
我們的部分是：把它具體套到完整的 Triangle Multiplication，並用分析模型算出流量與容量各省多少。
三週內只做**設計圖 ＋ 分析模型評估**；producer kernel 列為第二階段。

### 預期數字（容量模型，U55C 16 GB）
| 基準 | 典型實作 | 融合 ＋ INT8 a、b | 融合 ＋ INT4 a、b |
|---|---|---|---|
| FP32 | 約 2,190 | 約 3,650（1.67×） | — |
| **FP16（論文的基準）** | 約 3,100 | 約 4,700（**1.52×**） | 約 5,150（1.66×） |

---

## E. 多 CU ＋ HBM 通道擴展（需要板子）

`[connectivity] nk=trimul_v2:4`，讓 4～8 份 kernel 各自接不同的 HBM 通道、各算一部分的 i，
量測頻寬與效能隨 CU 數量的擴展。有板子後 1～2 週可以完成，是很好的補充實驗。

---

## F. Triangle Attention（未來工作）

LightNobel Fig. 3：1,410 個胺基酸時，Triangle Attention 佔 ESMFold 執行時間的 **75.9%**，Triangle Multiplication 只佔 14.5%。
它的 score matrix 是 L³，需要 FlashAttention 式的 token-wise attention（論文 Sec. 5.4）。
tiling、量化、分析模型的方法都能沿用，但多了 softmax 與線上最大值追蹤，三週內做不完。
**報告的「未來工作」一定要提，評審很可能會問。**

---

## 時程
三週的具體排程見 `docs/three_week_plan.md`。

---

## 需要先確認的事
1. **評分偏好**：偏創新、偏實作完整度，還是偏應用價值？
2. **U55C 在哪一台**：決定 E 和上板量測能不能做。
3. 若是 AMD / Xilinx 相關的競賽（例如 AMD 的開放硬體設計競賽），用 U55C 與 Vitis 流程本身就是加分。

---

## 文獻查找紀錄（2026-09-26）
- LightNobel（已讀原文）：token-wise 自適應量化（三組 activation、token-wise scale、執行時 top-k outlier）＋ RMPU / VVPU；
  比 A100 / H100 快最多約 8.4 倍、peak memory 最多降低約 120 倍（和不分塊的 GPU 比）；以 cycle-accurate 模擬器評估。
  [arXiv 2505.05893](https://arxiv.org/abs/2505.05893)、[ACM DL](https://dl.acm.org/doi/10.1145/3695053.3731006)
- GPU 融合 kernel：OpenFold3 的 PR 把 Triangle Multiplication 的工作空間從約 7U 降到約 4U（分塊後約 2.2U）。
  [openfold-3 PR #318](https://github.com/aqlaboratory/openfold-3/pull/318)
- 長序列推論的記憶體優化：FastFold、AutoChunk（自動分塊）。
  [AutoChunk](https://arxiv.org/pdf/2401.10652)、[FastFold](https://arxiv.org/pdf/2203.00854)
- Triangle Multiplication 在 GPU 上是 memory-bound 的分析：
  [arXiv 2510.18870](https://arxiv.org/pdf/2510.18870v1)
- 搜尋「FPGA ＋ AlphaFold / Evoformer / Triangle Multiplication」**沒有找到相關的 FPGA 實作**，
  代表這是相對空白的區域（仍建議在 Google Scholar 再確認一次）。
