# 競賽方向：比「單純比較常見手法」更有亮點、但做得完的選項

> 背景：原本的題目（在 FPGA 上比較 tiling、寬位元、double buffering、多通道、INT8）完整但偏教科書。
> 以下方向都**建立在已經寫好的 `fpga/trimul/` 之上**，不用從頭開始，並依「亮點 × 可行性」排序。
> 撰寫日期：2026-09-26。文獻查找結果見最後一節。

---

## 先說結論

| 方向 | 一句話 | 亮點 | 需要板子？ | 需要 GPU？ | 估計時間 | 風險 |
|---|---|---|---|---|---|---|
| **A. 融合版 Triangle Multiplication** | 把 LayerNorm、投影、gating、量化、輸出都塞進 FPGA 資料流，中間值不落地 | ★★★ | 否（HLS 即可出主要結果） | 否 | 3～4 週 | 中 |
| **B. FPGA 上的簡化版 AAQ** | 實作 LightNobel 的「分類 ＋ 混合精度 ＋ outlier」量化 | ★★★ | 否（HLS）；上板加分 | 需要 Colab 取真實資料 | 3～4 週 | 中 |
| **C. 分析模型 ＋ 設計空間探索** | 建立能預測 cycle、資源、最大 L 的模型，自動找最佳設定 | ★★ | 否 | 否 | 1～2 週 | 低 |
| **D. 真實 activation 分析** | 用 ESMFold 真實資料量化 outlier 分布，當作動機與佐證 | ★★ | 否 | Colab | 3～5 天 | 低 |
| **E. 多 CU ＋ HBM 通道擴展** | 複製多份 kernel，展示頻寬隨通道數擴展 | ★★ | **是** | 否 | 1～2 週（有板子後） | 看板子 |

**建議組合：A（主軸）＋ C（方法論骨架）＋ D（動機數據）**；時間夠再加 B 的一部分。
目前的 v0～v4 比較不會浪費，會變成 A 的 baseline 和 ablation。

---

## A. 融合版 Triangle Multiplication（主推）

### 問題
目前我們只做 einsum。但真實的 Triangle Multiplication 一步要產生很多份 L×L×128 的中間值：
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
    LayerNorm → 4 個 128×128 linear → sigmoid gating → mask → token-wise INT8 量化
    只寫出：a、b（INT8，含 scale）
Kernel 2（consumer）：現有的 v4 ＋ 輸出 epilogue
    einsum（INT8）→ LayerNorm_out → linear_z → 重新從 z 算 g → 相乘 → 寫出結果
```
- 128×128 的權重只有 64 KB（FP32），放得進晶片內。
- `g` 不存，在 epilogue 從 z 重算：每個輸出多 2·C² 次運算，而 einsum 本身是 2·L·C，L > 256 時占比不到一半，L 越大越划算。

### 預期亮點
| 指標 | 一般實作 | 融合 ＋ INT8 中間值 |
|---|---|---|
| 同時存在的 pair 張量 | 約 7 份 FP32（約 7U） | z 輸入 ＋ 輸出（2U）＋ a、b 的 INT8（約 0.5U）≈ **2.5U** |
| 相同 HBM 下可處理的 L | 1× | 約 √(7/2.5) ≈ **1.7×** |

**故事：** LightNobel 用「量化」解決序列長度問題；我們在 FPGA 上用「**融合 ＋ 量化**」從另一個角度處理同一個問題，並量化兩者各貢獻多少。

### 需要做的事
1. 用 Python 寫參考實作（完整的 TriangleMultiplicationOutgoing，已驗證 einsum 部分與 ESMFold 一致）。
2. 寫 producer kernel（LayerNorm ＋ 小矩陣乘法，HLS 很適合）。
3. 在 v4 加上 epilogue。
4. C 模擬比對 → HLS 合成 → 比較記憶體佔用、cycle、資源。

### 風險
- LayerNorm 需要一個 token 128 個數的平均與變異數，要兩次掃描或 Welford 演算法，HLS 寫法要注意。
- 權重需要真實值：從 HuggingFace 的 ESMFold 取出一個 block 的權重即可（CPU 就能做，不需 GPU）。

---

## B. FPGA 上的簡化版 AAQ

### 問題
LightNobel 的 AAQ：把 token **分成三類**，各用不同精度，並用**動態 top-k 保留 outlier**。論文用自己設計的 ASIC 評估。

### 做法（簡化）
| LightNobel | 我們的簡化版 |
|---|---|
| 三類 token、多種精度 | 兩類：一般 token 用 **INT4**，「難」的 token 用 **INT8** |
| 動態 top-k outlier | 每個 token 保留固定 k 個 outlier（FP16），其餘量化 |
| 專用 RMPU / VVPU | HLS 寫兩條資料路徑（INT4、INT8）＋ outlier 修正 |

1. **先在 Python 做**（快、便宜）：在真實 activation 上試各種設定（k、分類門檻），畫出「記憶體 vs 誤差」的 Pareto 曲線。
2. 挑一個設定做成 FPGA kernel，和 v4（純 INT8 per-token）比較。

### 預期亮點
- 據我們查到的資料，**沒有人在 FPGA 上實作過 PPM 的 token-wise 混合精度量化**。
- 可以直接和 LightNobel 對話：「ASIC 設計的想法，在現成 FPGA 上能實現多少？」

### 風險
- 需要真實 activation（Colab 一天可以取得）。
- INT4 的打包與解包在 HLS 裡要花一些心力。

---

## C. 分析模型 ＋ 設計空間探索（最穩的骨架）

### 做法
1. 從現有的 v2 報告已經能寫出公式，例如每個 k 迴圈 ≈ 載入（約 64 + 延遲）＋ 計算（TI·TJ·C/16 + 深度）。
2. 對 tile 大小、平行度、精度建立**cycle 模型、資源模型、容量模型**（最大 L）。
3. 用 HLS 報告驗證模型誤差（目標 < 10%）。
4. 用模型掃過上百種組合，畫出 Pareto 前緣，挑出最佳設定並實際合成驗證。

### 為什麼值得做
- **不需要板子**：server63 就能跑完。
- 把「比較幾個版本」提升成「**可以預測、可以最佳化的設計方法**」，評審通常很看重方法論。
- A 和 B 都能套用這個模型。

---

## D. 真實 activation 分析（動機數據）

在 Colab 上跑 `python/dump_trimul_inputs.py`，對幾條蛋白質、多個 block：
- outlier 比例、最大值與中位數比的分布
- 不同 block 深度的差異
- per-token vs per-tensor INT8 的誤差

產出 3～4 張圖，當作報告第一章的動機。**低成本、高說服力**，也是 B 的前置工作。

---

## E. 多 CU ＋ HBM 通道擴展（需要板子）

`[connectivity] nk=trimul_v2:4`，讓 4～8 份 kernel 各自接不同的 HBM 通道、各算一部分的 i，
量測頻寬與效能隨 CU 數量的擴展。有板子後 1～2 週可以完成，是很好的補充實驗。

---

## 建議時程（以 A ＋ C ＋ D 為例，約 6～7 週）

| 週 | 工作 |
|---|---|
| 1 | 完成 `make hls-all`；開始 C 的模型；Colab 跑 D |
| 2 | C 的模型驗證；A 的 Python 參考實作與權重擷取 |
| 3～4 | A 的 producer kernel 與 epilogue；C 模擬 |
| 5 | A 的 HLS 合成、記憶體與效能比較；用 C 的模型找最佳設定 |
| 6 | （若找到板子）上板；否則補 B 的 Python 部分 |
| 7 | 圖表與報告 |

---

## 需要先確認的事
1. **競賽名稱與截止日期**：決定要選幾個方向。
2. **評分偏好**：偏創新、偏實作完整度，還是偏應用價值？
3. **U55C 在哪一台**：決定 E 和上板量測能不能做。
4. 若是 AMD / Xilinx 相關的競賽（例如 AMD 的開放硬體設計競賽），用 U55C 與 Vitis 流程本身就是加分。

---

## 文獻查找紀錄（2026-09-26）
- LightNobel：token-wise 自適應量化（三類 token、token-wise scale、動態 top-k outlier）＋ RMPU / VVPU；
  宣稱比 A100 / H100 快最多約 8.4 倍、peak memory 最多降低約 120 倍。
  [arXiv 2505.05893](https://arxiv.org/abs/2505.05893)、[ACM DL](https://dl.acm.org/doi/10.1145/3695053.3731006)
- GPU 融合 kernel：OpenFold3 的 PR 把 Triangle Multiplication 的工作空間從約 7U 降到約 4U（分塊後約 2.2U）。
  [openfold-3 PR #318](https://github.com/aqlaboratory/openfold-3/pull/318)
- 長序列推論的記憶體優化：FastFold、AutoChunk（自動分塊）。
  [AutoChunk](https://arxiv.org/pdf/2401.10652)、[FastFold](https://arxiv.org/pdf/2203.00854)
- Triangle Multiplication 在 GPU 上是 memory-bound 的分析：
  [arXiv 2510.18870](https://arxiv.org/pdf/2510.18870v1)
- 搜尋「FPGA ＋ AlphaFold / Evoformer / Triangle Multiplication」**沒有找到相關的 FPGA 實作**，
  代表這是相對空白的區域（仍建議在 Google Scholar 再確認一次）。
