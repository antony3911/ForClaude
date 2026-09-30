# U55C 從零開始：專題操作手冊

專題主題：以 LightNobel (ISCA 2025) 指出的困境為出發點——PPM（ESMFold / AlphaFold2）的
pair representation 大小是 **L × L × C**，記憶體隨序列長度 L 平方成長，Triangle
Multiplication / Attention 又需要反覆讀寫它 → **memory-bound，且序列太長時放不下**。
我們在 Alveo U55C 上實作其中最關鍵的運算，並比較常見的 memory-bound 處理方法。

---

## 0. 先搞懂 U55C 是什麼

| 項目 | 數值 |
|---|---|
| FPGA | Virtex UltraScale+ `xcu55c-fsvh2892-2L-e` |
| 記憶體 | **16 GB HBM2**，分成 **32 個 pseudo-channel（PC），每個 512 MB** |
| 理論 HBM 頻寬 | 約 460 GB/s（所有 PC 加總；單一 PC 約 14 GB/s） |
| 晶片內記憶體 | BRAM + URAM 約 40 MB 左右（詳見 datasheet） |
| DDR | **沒有**，只有 HBM |

重點：**單一 PC 的頻寬和容量都很小**，要把資料分散到多個 PC 才能用滿頻寬。這本身就是一個
可以拿來比較的 memory 優化手法。

## 1. 需要的軟體（通常 server 已裝好，只要確認）

| 軟體 | 作用 | 確認方式 |
|---|---|---|
| **XRT**（Xilinx Runtime） | host 程式和板子溝通的 driver/runtime | `ls /opt/xilinx/xrt` |
| **U55C platform**（shell） | 板子上的「底座」設計，編譯時要指定 | `ls /opt/xilinx/platforms` |
| **Vitis**（含 `v++`） | 把 kernel 編成 bitstream（`.xclbin`） | `which v++` |
| **Vitis HLS** | C++ → 硬體電路 | `which vitis_hls` |
| Vivado | Vitis 內部會呼叫；你們只需要看它的報告 | `which vivado` |

### 每次登入後要做的設定

```bash
source /opt/xilinx/xrt/setup.sh
source /tools/Xilinx/Vitis/2023.2/settings64.sh     # 路徑和版本依你們 server 而定
# 找不到的話：find / -name settings64.sh 2>/dev/null
```

建議把這兩行寫進 `~/.bashrc`。

### 確認板子與 platform

```bash
xbutil examine                       # 應看到 U55C 卡，記下 BDF（像 0000:3b:00.1）
xbutil examine -d <BDF>              # 看卡上載入的 platform 名稱
ls /opt/xilinx/platforms             # 例如 xilinx_u55c_gen3x16_xdma_3_202210_1
xbutil validate -d <BDF>             # 板子自我檢測（跑一次確認板子正常）
```

**platform 名稱很重要**：本專案的 `Makefile` 預設 `xilinx_u55c_gen3x16_xdma_3_202210_1`，
若不同請用 `make ... PLATFORM=<你們的名稱>` 覆寫。

> 要問學長姐或管理員的事：
> 1. 板子是共用的嗎？燒錄前是否要先登記或排時間？
> 2. Vitis 的 license 是否有限制同時使用的人數？
> 3. 你們的帳號能不能直接執行 `xbutil`？還是需要加進特定 group？

## 2. FPGA 開發流程：一定要從快到慢

```
          時間         需要板子？    用來做什麼
① csim    秒            否           驗證功能是否正確（本專案用一般 g++ 就能跑）
② HLS     數分鐘        否           latency / 資源用量估計 ← 大部分比較數據可從這裡來
③ cosim   數十分鐘      否           cycle-accurate 模擬（可選）
④ hw_emu  數十分鐘      否           整個系統（含 host）一起模擬，抓介面錯誤
⑤ hw      1～數小時     是           真正上板量測 ← 最終數據
```

**原則：前一步沒過，不要進到下一步。** `hw` 編譯很久，務必用 `tmux` 或 `nohup` 跑，
避免 SSH 斷線導致重來。

## 3. 第一週：先把官方 Hello World 跑通

先不要碰本專案，用官方範例確認整個工具鏈是正常的：

```bash
git clone https://github.com/Xilinx/Vitis_Accel_Examples.git
cd Vitis_Accel_Examples/hello_world
make run TARGET=sw_emu PLATFORM=xilinx_u55c_gen3x16_xdma_3_202210_1
make run TARGET=hw     PLATFORM=xilinx_u55c_gen3x16_xdma_3_202210_1   # 約 1～2 小時
```

看到 `TEST PASSED` 就代表環境 OK。（範例 repo 的分支要跟 Vitis 版本對應，例如 2023.2
用 `git checkout 2023.2`。）

這個 repo 裡跟本專題最相關的範例（可以參考寫法）：
- `cpp_kernels/wide_mem_rw`：512-bit 寬位元存取
- `cpp_kernels/burst_rw`：burst 存取
- `cpp_kernels/dataflow_stream`：dataflow
- `performance/hbm_bandwidth`：HBM 多通道頻寬

## 4. 本專案：fpga/trimul

詳見 [`fpga/trimul/README.md`](../fpga/trimul/README.md)。

## 5. 建議時程

| 週次 | 工作 |
|---|---|
| 1 | 確認環境、跑通 hello_world（sw_emu → hw） |
| 2 | 跑本專案 `make csim`、`make hls`，學會看 HLS 報告 |
| 3 | v0 ~ v4 全部跑 HLS，整理 latency / 資源表 |
| 4～5 | v2、v3、v4 跑 hw_emu → hw，實際上板量測 |
| 6 | 實驗 B～D（tile sweep、HBM bank、量化精度、最大 L） |
| 7～8 | 畫 roofline 等圖表、寫報告；有餘力再做延伸（見 trimul README 最後一節） |
