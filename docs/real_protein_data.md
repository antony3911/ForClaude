# 用真實（長鏈）蛋白質跑實驗

FPGA 上跑的只是 ESMFold 裡**一個運算**（Triangle Multiplication），不是整個 ESMFold。
所以流程分成兩段：

```
 (1) 有 GPU（或大記憶體 CPU）的機器                  (2) U55C server
 ┌──────────────────────────────────────┐          ┌──────────────────────────┐
 │ 蛋白質序列（UniProt / PDB / FASTA）   │          │                          │
 │        ↓ ESMFold 跑到第 N 個 block    │  a.bin   │ host.exe 讀檔 → FPGA 計算 │
 │ 擷取 Triangle Mult. 的輸入 a, b       │ ───────→ │ 比較時間、頻寬、量化誤差  │
 │ python/dump_trimul_inputs.py         │  b.bin   │                          │
 └──────────────────────────────────────┘          └──────────────────────────┘
```

**好處：** FPGA 部分完全不用動 ESMFold。第 (1) 段在 Python 端就能直接得到
「真實資料下 per-token 和 per-tensor 量化的誤差」，這個結果不需要 FPGA 也能放進報告。

## 需要哪些資源

| 資源 | 用途 | 你們有沒有？怎麼確認 |
|---|---|---|
| 蛋白質序列 | 輸入 | **免費公開**：UniProt、RCSB PDB，腳本會自動下載 |
| ESMFold 權重 | 模型 | **免費公開**：HuggingFace `facebook/esmfold_v1`，約 8 GB，第一次執行會自動下載 |
| GPU | 跑 ESMFold | 在 server 上執行 `nvidia-smi` 看看；沒有的話問實驗室有沒有 GPU 機器 |
| 網路 | 下載權重與序列 | server 如果不能對外連線，就在別台電腦下載好 HuggingFace cache 再複製過去 |
| 硬碟 | 存 a.bin、b.bin | 每個檔案 `L² × 512` bytes（見下表） |

### GPU 記憶體大概需要多少

腳本只跑到指定的 trunk block 就停止，比完整預測結構省很多，但 pair tensor 還是平方成長。
下面是**粗估**，實際數字請自己量（腳本會印出 `GPU peak memory`，**這本身就是報告的數據**）：

| 序列長度 L | 一個 pair tensor（FP32） | 大概需要的 GPU |
|---|---|---|
| 500 | 128 MB | 16 GB 就夠（T4、RTX 4080 等） |
| 1000 | 512 MB | 16～24 GB |
| 2000 | 2 GB | 24～48 GB |
| 3000 以上 | 4.6 GB 以上 | 48～80 GB（A100/H100），或調小 `--chunk-size` |

**這張表就是 LightNobel 要解決的問題本身。** 你們可以實際量出「L 增加 → 記憶體平方成長 →
在某個 L 放不下」的曲線，作為專題的動機圖。

沒有 GPU 的替代方案：
- **CPU**：可以跑，但慢（L=1000 可能要幾分鐘到幾十分鐘），RAM 最好 32 GB 以上。
  加上 `--device cpu`。
- **Google Colab**：免費版有 T4（16 GB），大約能處理 L ≈ 1000 以內。產生的 `.bin` 很大，
  建議用 `--max-len` 控制長度，再下載或放到雲端硬碟傳到 server。

### FPGA 端的限制

U55C 有 16 GB HBM。依照 `cfg/*.cfg`，每個 port 接到 8 個 pseudo-channel（4 GB）。
每個 tensor 都要放得進自己那 4 GB，所以：
- v0～v3（全部 FP32）：a、b、z 各 `L²×512` bytes → L 最大約 **2880**
- v4（輸入 INT8，輸出 z 仍是 FP32）：輸入只剩 `L²×132` bytes，但 **z 仍然限制 L ≈ 2880**。
  想要更長的話，要讓 z 的 port 接更多 PC（例如 `HBM[16:31]`，8 GB → L ≈ 4096），
  或把輸出也量化（延伸題目）。

總占用量：FP32 版本是 `L²×1536` bytes，v4 是 `L²×776` bytes，**約省一半**。
換句話說，在相同的 HBM 預算下，v4 能處理的 L 大約是 √2 ≈ 1.4 倍。
這個計算（以及輸出也量化後能多到多少）可以直接寫進報告。

## 建議的測試蛋白質

| UniProt ID | 蛋白質 | 長度 | 用途 |
|---|---|---|---|
| P69905 | Hemoglobin α | 142 | 先用這個確認流程能跑 |
| P04637 | p53 | 393 | 中等長度 |
| P0DTC2 | SARS-CoV-2 Spike | 1273 | 長鏈、很有代表性 |
| P38398 | BRCA1 | 1863 | 長鏈 |
| P11532 | Dystrophin | 3685 | 超長鏈，需要大 GPU 或用 `--max-len` 截斷 |

另外可以參考 LightNobel paper 實驗章節使用的資料集（CASP / CAMEO 等），從裡面挑幾條
和 paper 一致的序列，報告比較有說服力。CASP 的 target 序列可在 predictioncenter.org 下載。

## 操作步驟

```bash
# 在有 GPU 的機器上
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 從短到長，逐步確認 GPU 放得下
python dump_trimul_inputs.py --uniprot P69905 --out ../data/hba
python dump_trimul_inputs.py --uniprot P0DTC2 --out ../data/spike
python dump_trimul_inputs.py --uniprot P11532 --max-len 2048 --out ../data/dmd2048

# 可以選擇擷取第幾個 trunk block（0～47），比較不同深度的 activation 分布
python dump_trimul_inputs.py --uniprot P0DTC2 --block 24 --out ../data/spike_b24
```

每次執行都會印出一段統計，例如：

```json
{
  "outlier_ratio_max_over_median": ...,   // outlier 程度：最大 token 的 absmax / 中位數
  "int8_per_token_rel_l2": ...,           // token-wise INT8 的誤差
  "int8_per_tensor_rel_l2": ...           // per-tensor INT8 的誤差
}
```

這些數字也會存在 `meta.json` 裡。

```bash
# 把 data/ 複製到 U55C server 後
cd fpga/trimul
make csim DATA=../../data/hba                              # 先用 g++ 驗證（L 小的才跑得完）
make run  KERNEL=trimul_v2 TARGET=hw DATA=../../data/spike
make run  KERNEL=trimul_v4 TARGET=hw DATA=../../data/spike
```

> `make csim` 在 CPU 上會跑完整的參考答案，計算量是 `L³`。L 超過 500 左右就會很慢，
> 長序列請直接上板（host 只抽樣 2000 個點驗證）。

## 驗證過的事項

- 擷取點是 HuggingFace `EsmForProteinFolding` 裡 `trunk.blocks[N].tri_mul_out` 的
  `_combine_projections(a, b)`。它的 a、b 已經過 LayerNorm、projection、gating 和 mask。
- 已確認 ESMFold 模組本身的計算結果和 kernel 的算式 `z[i][j][c] = Σ_k a[i][k][c]·b[j][k][c]`
  **完全一致**（差值 0）。
- 序列長度會補零到 `--pad`（預設 32）的倍數。補的部分全是 0，不影響結果。
