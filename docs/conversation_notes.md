# 對話筆記：專題規劃與檔案說明

這份筆記整理和 Claude 討論的重點，方便日後回顧。

## 專題題目

以 LightNobel（ISCA 2025，*Improving Sequence Length Limitation in Protein Structure
Prediction Model via Adaptive Activation Quantization*）遇到的困境為出發點，
嘗試用**常見的 memory-bound 處理方法**並比較成果。不求做出很厲害的新設計。

- 硬體：AMD Alveo **U55C**（16 GB HBM）
- 沒有 GPU → 主線只用 FPGA + 模擬資料；真實蛋白質資料是加分項

## 在算什麼

ESMFold 替每一對胺基酸 (i, j) 存 128 個數字，描述兩者之間的關係 → 資料大小是 **L × L × 128**
（L = 蛋白質長度）。L=1000 約 512 MB，L=2000 約 2 GB：**長度加倍，資料變 4 倍**。

其中 **Triangle Multiplication** 這一步要把這份大資料反覆讀很多遍：

```
z[i][j][c] = Σ_k a[i][k][c] × b[j][k][c]
```

瓶頸在「搬資料」而不是「算」→ **memory-bound**。專題就是把這一步放到 FPGA 上，
試幾種省搬運的方法，比較效果。

## 5 個版本（廚房比喻）

- HBM（板上大記憶體）= 遠處的倉庫：大，但搬運慢
- BRAM（晶片內記憶體）= 手邊的料理台：快，但小

| 版本 | 比喻 | 技術名稱 |
|---|---|---|
| v0 | 每用一樣食材就跑一趟倉庫 | Baseline（對照組） |
| v1 | 一次搬一批到料理台，重複使用 | Tiling（切塊＋資料重用） |
| v2 | 推車變大，一次搬 16 個；16 個廚師同時做 | 512-bit 寬位元傳輸＋平行計算 |
| v3 | 煮這批的同時，助手去搬下一批 | Double buffering（搬運與計算重疊） |
| v4 | 食材壓縮成 1/4 再搬，稍微失真 | INT8 量化（LightNobel 的核心手法） |

量化的兩種方式：
- **per-tensor**：整份資料共用一把尺 → 少數特別大的數字會讓其他數字的精度變很差
- **per-token**：每個位置用自己的尺 → 不受大數字拖累

模擬結果：per-token 誤差約 **1%**，per-tensor 約 **11%**（這就是 LightNobel 選 per-token 的理由）。

## 檔案地圖

```
ForClaude/
├── README.md                       目錄
├── docs/
│   ├── conversation_notes.md       ← 本檔
│   ├── getting_started_u55c.md     U55C 環境設定、開發流程、時程
│   └── real_protein_data.md        用真實蛋白質產生資料（加分項，需 GPU 或 Colab）
├── fpga/trimul/                    ★ 專題主體
│   ├── kernels/trimul_v0~v4.cpp    在 FPGA 上跑的 5 個版本
│   ├── kernels/trimul.h            共用設定（C=128、tile 大小）
│   ├── host/host.cpp               在 CPU 上跑：送資料→啟動 FPGA→取回結果→計時、驗證
│   ├── host/common.h               產生測試資料、INT8 量化、正確答案
│   ├── tb/tb.cpp                   不需板子的測試，確認 5 個版本算得對
│   ├── cfg/*.cfg                   資料放在 HBM 哪些區塊
│   ├── hls/run_hls.tcl             產生 cycle 數、硬體用量報告
│   ├── Makefile                    指令捷徑（make csim / make hls / make run）
│   └── README.md                   各版本說明、建議實驗、要畫的圖
└── python/dump_trimul_inputs.py    從 ESMFold 擷取真實資料（加分項）
```

FPGA 程式分兩半：**kernel**（燒進 FPGA 做計算）＋ **host**（在 CPU 上負責送資料、收結果）。

## 驗證狀態

- ✅ 5 個版本用 g++ 模擬，結果都正確
- ✅ kernel 的算式和 ESMFold 內部計算完全一致（差值 0）
- ❌ 尚未在 Vitis 工具上跑過、尚未上板 → 第一次跑可能要修小錯誤

## 接下來要做的事

1. **登入 FPGA server，查環境**，把輸出貼給 Claude：
   ```bash
   xbutil examine
   ls /opt/xilinx/platforms
   which v++ vitis_hls
   ```
2. **把程式抓到 server**：
   ```bash
   git clone -b claude/lightnobel-memory-optimization-yhokyc https://github.com/antony3911/ForClaude.git
   cd ForClaude/fpga/trimul
   ```
3. **確認程式正確**：`make csim` → 看到 `ALL PASS`
4. **拿第一批比較數據**：`make hls KERNEL=trimul_v0`（再換 v1、v2），把報告貼給 Claude 一起看

後續（上板、真實資料）等前面順利再做。
