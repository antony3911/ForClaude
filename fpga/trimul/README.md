# Triangle Multiplication on U55C：常見 memory-bound 優化比較

## 算的是什麼

AlphaFold2 / ESMFold 的 Triangle Multiplication（outgoing）核心：

```
z[i][j][c] = Σ_k a[i][k][c] · b[j][k][c]        a, b, z ∈ R^{L×L×C}, C = 128
```

- 計算量：`2·L³·C` FLOPs
- 每個 pair tensor 大小：`L²·C·4` bytes（FP32）→ L = 1024 時單一 tensor 就有 512 MB

這裡只實作 einsum 本身（最耗記憶體的部分），LayerNorm、gating、linear projection 不含在內。

## 各版本：每一版多加一種手法

| 版本 | 檔案 | 加入的手法 | 平行度 | 算術強度（FLOP/byte，TI=TJ=8） |
|---|---|---|---|---|
| v0 | `trimul_v0.cpp` | baseline：每次 MAC 都直接讀 HBM | 1 MAC/cycle（實際受 fadd latency 拖累） | 0.25 |
| v1 | `trimul_v1.cpp` | **Tiling + on-chip buffer**（資料重用） | 1 MAC/cycle | 2 |
| v2 | `trimul_v2.cpp` | + **512-bit 寬位元 burst** | 16 MAC/cycle | 2 |
| v3 | `trimul_v3.cpp` | + **Double buffering**（載入與計算重疊） | 16 MAC/cycle | 2 |
| v4 | `trimul_v4.cpp` | v2 + **INT8 token-wise 量化**（呼應 LightNobel） | 64 MAC/cycle | ≈ 7 |

另外有兩種不用改 kernel 的實驗：
- **Tile size sweep**：用 `DEFS="-DTILE_I=16 -DTILE_J=16"` 改變 tile 大小
- **HBM 通道配置**：`cfg/trimul_v2.cfg`（a/b/z 各自分散在 8 個 PC）與
  `cfg/trimul_v2_onebank.cfg`（全部擠在 HBM[0]）比較

## 怎麼跑

```bash
cd fpga/trimul

# ① 功能驗證（不需 Vitis，任何電腦都可以跑）
make csim

# ② HLS 合成報告（不需板子）
make hls KERNEL=trimul_v2
#    報告：hls_prj/trimul_v2/sol/syn/report/trimul_v2_csynth.rpt
#    要看的：Latency（cycles）、各 loop 的 II、BRAM/DSP/LUT/FF 用量

# ③ 硬體模擬（不需板子，L 請用小的，例如 16）
make run KERNEL=trimul_v2 TARGET=hw_emu RUN_L=16

# ④ 上板（編譯很久，請用 tmux）
make xclbin KERNEL=trimul_v2 TARGET=hw
make run    KERNEL=trimul_v2 TARGET=hw RUN_L=512

# v4 可以指定量化方式（per-token 或 per-tensor）
make run KERNEL=trimul_v4 TARGET=hw RUN_L=512 RUN_ARGS="3 tensor"

# HBM 單一 bank 對照組（用 TAG 避免覆蓋上面的 xclbin）
make run KERNEL=trimul_v2 CFG=cfg/trimul_v2_onebank.cfg TAG=trimul_v2_onebank TARGET=hw RUN_L=256

# Tile sweep（host 也會用同一組 DEFS 重新編譯，記得先 rm host.exe）
rm -f host.exe && make run KERNEL=trimul_v2 DEFS="-DTILE_I=16 -DTILE_J=16" TAG=v2_t16 TARGET=hw RUN_L=512
```

### 使用真實蛋白質資料

以上預設使用隨機資料（1% 的 token 被放大，模擬 outlier）。要改用真實 ESMFold 的
activation，請先依照 [docs/real_protein_data.md](../../docs/real_protein_data.md) 產生資料，
再加上 `DATA=`：

```bash
make run KERNEL=trimul_v2 TARGET=hw DATA=../../data/spike
```

host 程式最後一行會印出 CSV：

```
CSV,kernel,L,time_ms,gflops,est_traffic_GB,est_GBps,hbm_footprint_MB,rel_l2,max_abs
```

可以用 `make run ... | grep ^CSV >> results.csv` 收集所有結果。

## 建議的實驗與圖表

| 實驗 | 比較對象 | 圖表 |
|---|---|---|
| A. 手法逐步疊加 | v0 → v1 → v2 → v3（固定 L，例如 256） | 長條圖：時間、GFLOP/s |
| B. Tile size | TI×TJ = 4×4, 8×8, 16×16, 32×32 | 時間與 BRAM 用量的 trade-off |
| C. HBM 通道 | v2 多通道 vs. 單一 bank | 達到的頻寬 |
| D. 量化 | v2 (FP32) vs. v4 per-token vs. v4 per-tensor | 時間 + 誤差（rel_l2）+ HBM 占用 |
| E. 序列長度 | L = 128, 256, 512, 1024, 2048 | 時間隨 L 的成長；FP32 vs. INT8 能支援的最大 L |
| F. Roofline | 所有版本 | x：算術強度，y：GFLOP/s，並畫出 HBM 頻寬上限和計算上限 |

實驗 D、E 最能呼應 LightNobel 的主題：
- 已知 C-sim 結果（L=32、1% outlier token）：**per-token rel_l2 ≈ 1%，per-tensor ≈ 11%**，
  說明 outlier 存在時需要 token-wise 量化。
- 容量：FP32 單一 tensor `L²·512 B`，INT8 只需 `L²·128 B`（加上 scale `L²·4 B`）。
  v4 的輸出 z 仍是 FP32，所以總占用量約為 FP32 版本的一半，相同 HBM 預算下 L 約可多 1.4 倍；
  若輸出也量化，才會接近 2 倍（可以當延伸題目）。

## 預期結果與誠實的限制

- v0 在 L 大時會**非常慢**（甚至超過一小時），上板請只用小的 L（例如 64、128）。
- v2/v3 理論峰值只有 `16 × 2 × 300 MHz ≈ 9.6 GFLOP/s`，v4 約 38 GFLOP/s，
  **絕對速度不會贏 GPU**。專題重點在於**比較各手法帶來的相對改善**，以及讓 kernel
  在 roofline 上的位置如何移動。
- v3 相對於 v2 的改善有限（每個 k 的載入約 128 cycles、計算約 512 cycles，最多省約 20%），
  這是正常的，也可以在報告中分析原因：tile 越大，計算越占主導，overlap 的效益越小。
- 量化的時間（host 端做）沒有計入 kernel 時間；報告中要說明這一點。

## 延伸方向（有餘力再做）

1. **提高平行度**：在 v2 的 `mac` 迴圈把 `jj` 也 unroll，讓每 cycle 做 16×TJ 個 MAC，
   觀察 kernel 從 compute-bound 變回 memory-bound。
2. **多個 compute unit**：`[connectivity] nk=trimul_v2:4`，讓 4 份 kernel 各算一部分的 i，
   分別接到不同 HBM PC。
3. **FP16 / BF16**：介於 FP32 和 INT8 之間的精度選項。
4. **Chunking**：只保留部分的 z 在 HBM 中，模擬 AlphaFold 的 chunk 機制，比較 peak memory。
5. **軟體對照組**：用 PyTorch 在 GPU 上跑同樣的 einsum（`torch.einsum('ikc,jkc->ijc', a, b)`），
   以及 ESMFold 在不同 L 下的 peak memory，作為問題背景的佐證。
