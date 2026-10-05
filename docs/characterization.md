# ESMFold Workload Characterization（第一輪）

> 2026-10-04，筆電 RTX 4070 Laptop（8 GB）；3.9 節為 2026-10-05 學校 server CPU 的完整流程量測。程式與原始數據在 `python/char/`，重現方式見第 7 節。
> 標示說明：**實測**＝這台機器量到的；**計數**＝程式從 HF 實作數出來的（精確）；**推估**＝模型推算的。

## 1. 目的

找出整條 ESMFold 推論流程中，哪個運算最值得優化、在哪個長度範圍、原因是什麼，而且結論不能只對某一台 GPU 成立。

## 2. 方法

**三層：**
1. **計數**（與平台無關）：用 meta tensor（只有形狀、不配置記憶體）執行 HF 的 Folding Block，攔截每個 aten 運算，記錄 FLOPs（矩陣乘法）與讀寫 bytes（每個運算讀輸入、寫輸出；view 類不算；broadcast 只算實際元素）。任何 L 都能算。
2. **實測**：真實權重（trunk block 0）、隨機輸入，用 PyTorch profiler 量每個子模組的 GPU kernel 時間（依 GPU 時間軸歸屬，每個 kernel 只算一次）與峰值記憶體。另量端到端（完整模型、4 次 recycling）。
3. **模型**：每個運算 `t = max(FLOPs ÷ 算力, bytes ÷ 頻寬)`，算力與頻寬用實測值。先在筆電上和實測比對，再換成 H100 參數對照論文 Fig. 3。

**為什麼可以這樣做：**
- 時間與記憶體和數值無關（沒有依資料走的分支、沒有稀疏性），所以量時間可以用隨機輸入。
- trunk 是 48 個結構相同的 block × 4 輪（HF 預設 max_recycles = 4；只有手動指定 num_recycles 時才會再加 1）= 192 次，量 1 個 block 即可代表（端到端驗證見 3.8）。**更正（10-06）**：第一輪寫成 5 輪／240 次是錯的；server 上 `run_cpu.py` 的探針直接數到 192 次，HF 原始碼也是如此。
- 分塊（chunk）只把同樣的工作切開：FLOPs 完全相同、bytes 只多 0.7%（計數），時間也相同（實測，見 3.5）。所以用分塊量測可以代表不分塊、記憶體放不下的長度。
- 換硬體時，受算力限制和受頻寬限制的運算加速倍數不同，所以 GPU 上的時間佔比不能直接搬到別的平台；要用模型換算。

**量測注意事項（踩過的坑）：**
- Windows 驅動在顯示記憶體不足時會借用系統 RAM，不報錯但慢數十倍。已用 `torch.cuda.set_per_process_memory_fraction` 限制在 6.5 GB，放不下就記為 OOM。
- profiler 若沿 CPU 端父子關係歸屬 kernel，長 L 加分塊時會重複計算約 20%。已改用 GPU 時間軸歸屬，kernel 總和與 block 時間一致（差 < 0.2%）。
- 筆電 GPU 溫度 70°C→78°C 時同一點的時間差約 5%，數字有這個程度的波動。
- 短序列時 GPU 大部分時間在等 CPU 下發 kernel（L = 76 端到端：kernel 只佔總時間 25%），所以時間以 kernel 時間為準。

## 3. 結果

### 3.1 每個 block 的運算量（計數；與手推公式一致）

| 運算 | 每個 block |
|---|---|
| TriMul out／in（各） | 2.0×10⁵·L²（6 個 128×128 linear）＋ 256·L³（einsum） |
| TriAttn start／end（各） | 1.6×10⁵·L² ＋ 512·L³（Q·Kᵀ 與 attention·V，4 heads × 32） |
| pair transition | 2.6×10⁵·L² |
| seq↔pair | 4×10⁴·L² |
| sequence track | 2.7×10⁷·L |
| **合計** | **1536·L³ ＋ 1.03×10⁶·L² ＋ 2.7×10⁷·L** |

L³ 項在 L ≈ 670 時超過 L² 項。L = 77、512、1410 時每個 block 分別為 8.9、490、6,393 GFLOP（計數與公式相符）。

### 3.2 運算量 vs 搬運量（計數，FP32，不分塊）

| L | TriMul（FLOP% / bytes%） | TriAttn（FLOP% / bytes%） |
|---|---|---|
| 77 | 28.8 / 25.8 | 27.2 / 46.6 |
| 512 | 35.0 / 14.4 | 45.6 / 74.6 |
| 1410 | 34.6 / 7.2 | 55.2 / 87.4 |

TriAttn 的 logits（4 × L³）約被讀寫 8 次（寫出、加兩個 bias、softmax、乘 V），每 byte 只做約 8 次運算（FP16），與 L 無關，任何 GPU 上都受頻寬限制。TriMul einsum 的輸入輸出只有 L² 大小，每 byte 運算量隨 L 增加，受算力限制。

### 3.3 筆電天花板（實測）

| FP32 矩陣乘法 | FP16 矩陣乘法 | 頻寬 | 最小 kernel |
|---|---|---|---|
| 9.6 TFLOPS | 36.9 TFLOPS | 216 GB/s（規格 256 的 85%） | 約 10 µs |

### 3.4 一個 block 的 GPU 時間分布（實測，FP16，chunk 64）

| L | block 時間 | TriMul | TriAttn | pair transition | seq↔pair | seq track | residual 等 |
|---|---|---|---|---|---|---|---|
| 64 | 0.9 ms | 33.2% | 30.2% | 7.0% | 4.3% | 20.3% | 5.0% |
| 256 | 22.1 ms | 28.7% | 53.7% | 8.0% | 1.8% | 1.6% | 6.2% |
| 512 | 143 ms | 24.7% | 63.3% | 5.0% | 1.6% | 0.7% | 4.6% |
| 1024 | 1,009 ms | 26.1% | 66.7% | 2.8% | 0.9% | 0.8% | 2.6% |
| 1410 | 2,508 ms | 21.5% | 72.9% | 2.1% | 0.8% | 0.6% | 2.0% |

FP32 的比例相近（L = 512：TriMul 24.4%、TriAttn 63.6%），FP16 約快 2 倍。

### 3.5 分塊：時間不變、記憶體大幅下降（實測，FP32）

| L | 不分塊 | chunk 64 |
|---|---|---|
| 384 | 136.9 ms／+2.23 GB | 134.7 ms／+0.72 GB |
| 512 | 294.9 ms／+5.04 GB | 292.3 ms／+1.28 GB |

峰值記憶體（一個 block 比開始時多用的部分，實測）：

| L | FP32 不分塊 | FP32 chunk 64 | FP16 不分塊 | FP16 chunk 64 |
|---|---|---|---|---|
| 256 | 0.73 GB | 0.32 | 0.36 | 0.16 |
| 512 | 5.04 | 1.28 | 2.52 | 0.64 |
| 768 | OOM | 2.88 | OOM | 1.44 |
| 1024 | — | 5.11 | — | 2.56 |
| 1410 | — | OOM | — | 4.85 |

不分塊時峰值隨 L³ 成長（TriAttn logits）；分塊後隨 L² 成長（pair 張量）。

### 3.6 TriMul 內部：einsum 本身很快，慢在資料重排（實測，FP16，chunk 64，單獨跑 tri_mul_out）

| aten 運算 | L = 1024 | L = 1410 |
|---|---|---|
| `copy_`（permute 後轉成連續排列，3 個 kernel） | **57.2%** | **57.1%** |
| `addmm`（6 個 linear） | 12.3% | 12.4% |
| `mul`（gating、mask） | 9.4% | 10.7% |
| `native_layer_norm` | 10.6% | 8.7% |
| **`bmm`（einsum 本身）** | **6.3%** | **6.5%** |
| `sigmoid` | 4.2% | 4.7% |

一次 copy 搬約 536 MB（L = 1024）卻花約 36 ms，等效只有約 15 GB/s（頻寬的 7%）：把 L×L×128 轉成 128×L×L 時，讀或寫至少一邊不連續，無法有效利用 DRAM burst。TriMul 的矩陣乘法（6 個 linear ＋ einsum）合計達到 22.8 TFLOPS（實測峰值的 62%），本身效率正常。

### 3.7 模型準度（V2）與對照論文（V5）

**筆電：roofline 預測 vs 實測（一個 block 的總時間，實測 ÷ 預測）**：L ≥ 512 時 0.82～0.95；L ≤ 128 時約 0.5～0.7（張量小到能放進 32 MB 的 L2 快取，實際比以 DRAM 頻寬算的下限更快）。模型系統性低估 TriMul（漏掉 copy 的低效率）、高估 TriAttn。

**推 H100（不分塊），換算成佔 Folding Block 的比例**（論文 Fig. 3 是佔整個 ESMFold；Folding Block 佔 83.8%／94.5%）：

| | L = 77：TriMul | TriAttn | L = 1410：TriMul | TriAttn |
|---|---|---|---|---|
| 論文 Fig. 3（H100，換算） | 43.1% | 34.6% | 15.3% | 80.3% |
| 純 roofline（FP16，SXM） | 25.9% | 46.5% | 7.5% | 87.1% |
| 用筆電實測效率校正（FP16） | 35.1% | 32.0% | 20.3% | 74.1% |
| 筆電直接實測（FP16，L = 64／1410） | 33.2% | 30.2% | 21.5% | 72.9% |

長序列時，論文值落在純 roofline 與校正值之間（各差 5～8 個百分點），趨勢一致。短序列差距較大：H100 上小 kernel 的固定開銷佔比高，模型沒有納入。論文是 SXM 或 PCIe、FP16 的實際做法（.half() 或 autocast）都未知，PCIe 的結果與 SXM 相差 < 1 個百分點。

### 3.8 端到端（實測，FP32 trunk，chunk 64）

ESM-2 另外放 GPU（FP16）計時；trunk 與 structure module 用 profiler 依 GPU 時間軸分段。百分比的分母是 ESM-2 ＋ trunk 的總時間（含 GPU 閒置）。

| 序列 | L | ESM-2 | 192 個 block | 平均每個 block | structure module（4 次） | 峰值 |
|---|---|---|---|---|---|---|
| 泛素 | 76 | 89 ms（3.9%） | 544 ms（23.7%） | 2.83 ms | 32 ms（1.4%） | +0.04 GB |
| 隨機 | 256 | 94 ms（0.8%） | 11.2 s（94.2%） | 58.3 ms | 125 ms（1.1%） | +0.47 GB |
| 隨機 | 512 | 155 ms（0.2%） | 66.5 s（98.3%） | 346.1 ms | 454 ms（0.7%） | +1.85 GB |

（百分比是 profiler 直接量的時間，不受次數更正影響；「平均每個 block」已改成除以 192。）

**V3（單一 block × 192 是否等於 trunk）：** 單獨量的 block（FP32、chunk 64）為 49.6 ms（L = 256）、292.3 ms（L = 512），端到端平均每個 block 為 58.3、346.1 ms，**端到端慢 17～18%**。第一輪寫的「差 5～6%」是用錯的次數（240）算的，錯的次數剛好抵銷了差距。原因尚未查明，候選：端到端連續跑 1 分鐘以上，筆電 GPU 升溫降頻（單獨量 block 是短時間）；端到端裡 block 之間穿插其他運算，快取與記憶體配置器的狀態不同。這個差距不影響時間佔比的結論，但「量 1 個 block × 192 = trunk」要打 0.82～0.85 的折扣。

**正確性：** 泛素的預測結構與 PDB 1UBQ 的 CA RMSD = **0.84 Å**（pLDDT 0.774），模型載入與推論正確。隨機序列的 pLDDT 約 0.21，符合「沒有穩定結構」的預期。

**短序列的 GPU 閒置：** 泛素的 trunk 總時間約 2.2 s，但 GPU kernel 合計只有約 0.58 s，GPU 約 75% 時間在等 CPU 下發 kernel。

### 3.9 第三個平台：server CPU，完整流程（實測，2026-10-05）

**設定：** 學校 server（2 × Intel Xeon Gold 6526Y，每顆 16 核，共 32 實體核／64 執行緒，支援 AVX-512 與 AMX；125 GB RAM；無 GPU；當時負載 0），`python/char/run_cpu.py`：整個 ESMFold 用 FP32 放 CPU、不分塊、不暖機、跑一次，32 執行緒。CPU 同步執行，所以在每個模組前後掐碼錶（forward hook ＋ `time.perf_counter`）就是它實際花的時間；類別互不重疊，加總等於總時間。環境：Python 3.9（server 只有這版）、torch 2.8.0+cpu、transformers 4.57.6。原始數字：`results/measured_cpu.csv`；分析：`analyze_cpu.py`。

**正確性：** 泛素 CA RMSD = 0.83 Å（筆電 GPU 版 0.84）。

**時間分布（佔完整流程）：**

| L | 總時間 | 三角運算 | TriMul | TriAttn | pair transition | 48 個 block 合計 | 峰值記憶體（整個程式） |
|---|---|---|---|---|---|---|---|
| 76 | 6.7 s | 67.8% | **56.9%** | 10.9% | 4.6% | 89.4% | 19.9 GB |
| 256 | 61.2 s | 82.3% | **51.7%** | 30.6% | 6.3% | 96.9% | 22.2 GB |
| 512 | 354 s | 87.8% | 35.0% | **52.8%** | 4.2% | 98.5% | 27.4 GB |
| 1024 | 1,596 s | **90.3%** | 21.6% | **68.7%** | 3.2% | 99.0% | 60.7 GB |

ESM-2 加 structure module：L = 76 時 10.6%，L ≥ 256 時 < 3%。峰值記憶體中約 19 GB 是權重與 ESM-2；L = 1024 多出的約 40 GB 主要是不分塊的 TriAttn logits（一份 4 × L³ × 4 bytes = 17 GB）。

**每個運算達到的算力與頻寬**（運算量、搬運量用計數，除以實測時間；搬運量是「每個運算都完整讀寫一次」的名目值，短序列時資料在快取裡，名目頻寬會偏高）：

| 運算 | FLOP/byte | 達到 GFLOP/s（L = 76 → 1024） | 名目 GB/s |
|---|---|---|---|
| pair transition（幾乎全是 linear，當作參考） | 22 | 850～1,030 | 38～47 |
| TriMul（out、in 各） | 10.5 → 22.4 | 125 → 537 | 12 → 24 |
| TriAttn（start、end 各） | 5.5 → 3.7 | 630 → 230～280 | 114 → 57～78 |

- **server CPU 的實際天花板（`ceilings_cpu.py`，32 執行緒，10-06 第三版）：**

  | 項目 | 實測 |
  |---|---|
  | FP32 矩陣乘法，n = 1024／2048／4096／8192／16384 | 1,412／2,860／3,827／3,957／**4,314** GFLOP/s（n 加倍仍多 5～10%，未完全平穩；同一點三次量測差約 ±5%） |
  | 和 TriMul einsum 同形狀、資料已排好的 bmm（128 個 1024×1024×1024） | **4,363 GFLOP/s，63 ms** |
  | 連續複製／原地加法，記憶體**分散在兩顆 CPU** | 76～82／**95～100** GB/s |
  | 連續複製／原地加法，記憶體**集中在一顆 CPU** | 38～39／50～52 GB/s（剛好一半） |
  | permute 複製（L = 1024 的 pair 張量轉成 channel 在前） | **9 GB/s**，124 ms（兩種擺放都一樣） |
  | 寫入新配置／已用過的記憶體 | 58／74 GB/s |

  **NUMA 陷阱（已驗證）：** server 有 2 顆 CPU，各接自己的記憶體；Linux 把每一頁放在第一個寫它的執行緒所在那顆 CPU 旁。`torch.randn` 在 CPU 上是單執行緒產生的，用它建立的張量全部集中在一顆 CPU，頻寬只剩一半。第一版量到的 80 GB/s 剛好有一邊是多執行緒寫入的；第二版兩邊都用 randn，掉到 38 GB/s；第三版把兩種擺放分開量，證實差 2 倍。ESMFold 裡的大張量都是多執行緒運算產生的，屬於「分散」，所以頻寬上限取 **約 100 GB/s**（原地加法，和 TriAttn 的 `add_` 同一種運算；diagnose 裡 `add_` 實際約 112 GB/s，一致）。算力上限取 **約 4,300 GFLOP/s**。轉折點約 43 FLOP/byte，三角運算全都在它左邊。
- **對照 roofline（可達上限 = 算術強度 × 100 GB/s）：**

  | 運算 | L = 76 | 256 | 512 | 1024 |
  |---|---|---|---|---|
  | TriAttn start | > 100%（資料在快取裡） | 88% | 58% | 77% |
  | pair transition | 89% | 38% | 40% | 47% |
  | **TriMul out** | **12%** | **16%** | **17%** | **24%** |

  TriAttn 貼近頻寬天花板；TriMul 離得最遠。
- **形狀不是問題，排列才是：** 和 TriMul einsum 同形狀的 bmm，資料排好時只要 63 ms（4,363 GFLOP/s，等於機器上限）；HF 的寫法裡，einsum 本身 149 ms、加上它需要的 copy 436 ms，合計 585 ms，是理想的 **9.3 倍**。TriMul 每次 `copy_` 的 436 ms 約等於 3 次 permute 複製（3 × 124 = 372 ms），與 GPU 上的 3 個 copy kernel 對得上：a、b 各轉一次，輸出再轉回來一次。
- **TriMul 兩頭都沒碰到上限**：算術強度與 pair transition 相近，算力只有它的 15～55%；頻寬只有 TriAttn 的 1/4～1/5。不受算力也不受頻寬限制卻慢，與 GPU 上「copy 佔 57%」的現象一致。`diagnose_cpu.py` 證實 CPU 上同樣是 copy 造成（見下方）。
- **TriAttn 受頻寬限制**：每 byte 只有約 4 次運算，而且 L 越大，達到的頻寬越低（資料掉出快取）。

**隨 L 的成長（時間 ∝ L^p）：**

| 區間 | TriMul 時間 | TriMul FLOPs | TriAttn 時間 | TriAttn FLOPs | TriAttn bytes |
|---|---|---|---|---|---|
| 76 → 256 | 1.74 | 2.16 | 2.67 | 2.31 | 2.47 |
| 256 → 512 | 1.97 | 2.32 | **3.32** | 2.53 | 2.70 |
| 512 → 1024 | **1.47** | 2.49 | 2.55 | 2.69 | 2.82 |

TriMul 的時間成長比運算量慢，是因為**效率隨 L 提高**（125 → 537 GFLOP/s：大矩陣比較能填滿 32 核，固定開銷相對變小），不是工作變少。TriAttn 在 256 → 512 成長得比運算量和搬運量都快。原本推測是資料掉出快取，但 L3 只有數十 MB，L = 256 時一份 logits 就有 268 MB，這個解釋站不住。另一個候選：PyTorch 在 CPU 上每個運算的大輸出都向作業系統要新記憶體，第一次寫入要付分頁的代價，張量越大越明顯。`ceilings_cpu.py` 的第 4 項會量這個代價。

**拆到 aten 運算（`diagnose_cpu.py`，單一 block 0 的子模組、暖機後量 3 次取平均，FP32、不分塊、32 執行緒）：**

| | tri_mul_out L = 512 | tri_mul_out L = 1024 | GPU（3.6，L = 1024） |
|---|---|---|---|
| 每次 | 328 ms | 881 ms | — |
| `copy_`（permute 後轉連續排列） | **57.5%** | **49.5%** | 57.2% |
| `bmm`（einsum 本身） | 14.3% | 16.9% | 6.3% |
| `mul`（gating、mask） | 10.2% | 12.0% | 9.4% |
| `addmm`（6 個 linear） | 8.2% | 10.1% | 12.3% |
| `sigmoid` | 5.5% | 6.4% | 4.2% |
| `native_layer_norm` | 3.9% | 4.9% | 10.6% |

tri_mul_in 的分布幾乎相同。**CPU 上 TriMul 也有一半以上的時間在 copy，einsum 只佔 14～17%，與 GPU 一致**：TriMul 慢在資料重排，不是單一硬體的特例。CPU 上 copy_ 每次呼叫 263 次（其中 256 次是逐 channel 的小複製，次數與 L 無關），GPU 上是 3 個 kernel；meta tensor 的計數看不到這些，所以第 3.2 節的搬運量低估了 TriMul 在實際硬體上的搬運。

| | tri_att_start L = 512 | start L = 1024 | tri_att_end L = 1024 |
|---|---|---|---|
| 每次 | 295 ms | 1,978 ms | 2,561 ms |
| `add_`（logits 加兩個 bias，2 次） | 26.0% | 31.1% | **46.6%** |
| `_softmax` | 23.8% | 28.3% | 21.8% |
| `bmm`（Q·Kᵀ、attention·V） | 23.8% | 27.0% | 20.5% |
| `copy_` | 9.5% | 4.8% | 4.4% |

- TriAttn 有 54～68% 的時間花在對 L³ logits 的逐元素運算（`add_`、`_softmax`），矩陣乘法只佔約 1/4。以計數的搬運量換算：`add_` 約 112 GB/s、`_softmax` 約 61 GB/s，L = 512 和 1024 都一樣 → 受頻寬限制，與 GPU 的結論相同。
- **end 比 start 慢的原因找到了**：L = 1024 時 end 的 `add_` 1,194 ms，是 start 的 2 倍（616 ms），差值 578 ms 幾乎等於兩者總差（583 ms）；L = 512 時兩者的 `add_` 相同。end 先把 pair 張量轉置，算出的 bias 是轉置後的不連續排列，加到 logits 時以跳躍的位址讀取（推測：L = 1024 時 bias 有 16 MB，跳躍讀取不再能被快取吸收）。**又是資料排列的問題。**
- 單獨量的 TriAttn 比 `run_cpu.py` 完整流程裡的同一個運算快 22～39%（L = 1024／512），TriMul 則一致（差 < 2%）。完整流程裡沒有暖機，而且每個運算前後都有其他大張量的配置與釋放，`ceilings_cpu.py` 量到寫入新配置的記憶體比已用過的慢約 22%（58 vs 74 GB/s），方向相符、可以解釋一部分，但不足以解釋 39%，仍未完全查明。佔比結論以完整流程為準。

## 4. 結論：哪裡最值得優化

1. **長序列（L ≳ 300）：Triangle Attention，而且問題在搬運量，不在運算量。** 它佔 block 時間 54%（L = 256）→ 73%（L = 1410），在任何 GPU 上都受頻寬限制，因為 L³ 的 logits 要來回讀寫約 8 次；不分塊時它也決定峰值記憶體。有效的優化是不把 logits 寫回記憶體（FlashAttention 式／LightNobel 的 token-wise attention），把搬運量從 O(L³) 降到 O(L²)。
2. **Triangle Multiplication 是第二大（長序列 20～26%；短序列約 33%，是最大項）。** 但在 GPU 上，它的時間主要不是 einsum（只佔 TriMul 的 6%），而是資料重排（57%）與逐元素運算。所以 TriMul 的優化重點是**資料排列與融合**：直接以原本的 `[i][k][c]` 排列計算、不做轉置複製，並把 LayerNorm、linear、gating 和 einsum 串在一起、不寫回中間值。
3. **短序列（L ≲ 128）：** 運算量太小，GPU 被 kernel 下發的固定開銷限制（筆電上 75% 時間閒置），比例由 kernel 數量主導。這個範圍不是本專題的重點。
4. ESM-2 與 structure module 佔比很小：L = 512 時合計不到 1%，192 個 block 佔 98.3%（見 3.8）。整條流程的優化重點就在 trunk 的 block 裡。
5. **跨平台（3.9）：** server CPU 上同樣是三角運算佔 82～90%（L ≥ 256）、TriAttn 隨 L 上升（L = 1024 達 69%）。三個平台（論文 H100、筆電 GPU、server CPU）的趨勢一致，只有 TriMul 與 TriAttn 的交叉點隨硬體移動（筆電 GPU 在 L < 256，CPU 在 256～512 之間）：CPU 的算力相對頻寬較弱，所以運算量大的 TriMul 被放大。**跨平台成立的是趨勢，交叉點不是。**

**對本專題的意義：** 選 TriMul 不能用「它最花時間」當理由（TriAttn 才是）。但數據支持另一個理由：TriMul 浪費在資料搬移與排列，而這正是空間加速器（以 tiling 讀取原始排列、晶片內串接各運算）能直接改善的部分。這個現象在 GPU（copy 佔 57%）與 CPU（copy 佔 50～58%，einsum 只佔 14～17%）上都看得到，不是單一硬體的特例。

## 5. 限制

- 筆電 GPU 無法鎖時脈（需系統管理員權限），時間有約 5% 波動。
- 筆電單一 block 的實測最長到 L = 1410（FP16、分塊）；更長的序列只有計數與模型推估。
- 模型對單個 kernel 的誤差可達 ±40%（例如 copy 與 softmax），只在加總層級驗證過。
- 論文的 GPU 型號細節與精度設定未知，V5 的對照只能說趨勢一致、差距在 5～8 個百分點。
- 只量了推論、batch = 1、單一 GPU。
- 端到端與單一 block 相差 17～18%（3.8），原因未查明。
- server CPU：每個長度只跑一次、沒有暖機；共用 server，雖然當時負載為 0，仍可能受他人影響；32 個執行緒橫跨 2 顆 CPU，沒有控制執行緒放在哪個核心（可能有兩個執行緒共用一個實體核，也有跨 CPU 存取記憶體的代價）。

## 6. 下一步（建議）

- 若能用外部 A100：同一支 `profile_block.py` 跑不分塊的 L = 1024～2000，直接驗證長序列的推估。
- 加入「融合／不轉置」版本 TriMul 的理論搬運量，量化可省下多少。

## 7. 重現

```
python python/char/count_ops.py --L 64 77 128 256 384 512 768 1024 1410 --dtype fp32 fp16 --chunk none 64
python python/char/ceilings.py
python python/char/profile_block.py
python python/char/compare.py
python python/char/diagnose.py --L 1024 --dtype fp16 --chunk 64
python python/char/profile_e2e.py --L 256 512
```
環境：`C:\Users\anton\venvs\lightnobel`（torch 2.11＋cu128、transformers 5.18），需設 `HF_HUB_OFFLINE=1`。

server CPU（`~/venv-ln`，Python 3.9、CPU 版 torch）：
```
HF_HUB_OFFLINE=1 python python/char/run_cpu.py --L 76 256 512 1024 --threads 32
HF_HUB_OFFLINE=1 python python/char/diagnose_cpu.py --L 512 1024 --threads 32
python python/char/ceilings_cpu.py --threads 32
python python/char/analyze_cpu.py   # 讀 results/measured_cpu.csv，筆電上即可跑
```
注意：舊版 transformers 第一次載入只有 `.bin` 的模型時，會在背景另外下載 safetensors 版（約 8 GB），程式算完也要等它下載完才結束；模型下載好之後一律設 `HF_HUB_OFFLINE=1`。
