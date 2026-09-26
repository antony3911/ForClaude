# 第 5 章　指令手冊：做過的、可以做的、格式與用途

> **本章重點**
> - 先學會看懂**指令的格式**（指令、選項、參數、管線、導向），之後遇到新指令也能自己拆解。
> - 依用途分成九類：Linux 基本操作、環境調查、Git、tmux、**本專案的 make 指令**、Vitis 工具、看結果、host 程式、Python 腳本。
> - 每個指令都標示：✅ **已經做過**、🔜 **下一步會用到**、⬜ **之後可以做**、⚠️ **小心使用**。
> - 本章最後有一張「目前為止實際執行過的指令」時間軸，以及常見錯誤的排查方法。
> - 圖示的狀態以 **2026-09-26** 為準，最新進度見 `docs/PROJECT_LOG.md`。

---

## 5.1 先看懂指令的格式

### 基本結構
```
指令名稱  [選項]          [參數]
│         │               │
▼         ▼               ▼
ls        -la             /opt/xilinx
git       clone -b 分支   網址
make      hls             KERNEL=trimul_v2
```

| 部分 | 意思 | 例子 |
|---|---|---|
| **指令名稱** | 要執行的程式 | `ls`、`git`、`make` |
| **短選項** | 一個 `-` 加一個字母，可以合併 | `-l`、`-a`，合併成 `-la` |
| **長選項** | 兩個 `-` 加單字 | `--help`、`--mode hls` |
| **參數** | 指令要處理的對象 | 檔名、資料夾、網址 |
| **子指令** | 有些指令底下還有功能分類 | `git clone`、`git pull` 的 `clone`、`pull` |

### 組合指令的符號
| 符號 | 意思 | 例子 | 白話 |
|---|---|---|---|
| `\|` | **管線**：前一個的輸出當成後一個的輸入 | `lspci \| grep -i xilinx` | 列出所有裝置，只留下含 xilinx 的行 |
| `>` | 把輸出**寫進**檔案（覆蓋） | `make summary > out.txt` | 結果存檔 |
| `>>` | 把輸出**附加**到檔案結尾 | `... \| grep ^CSV >> results.csv` | 累積多次結果 |
| `2>/dev/null` | 把錯誤訊息丟掉 | `ls /opt/xilinx 2>/dev/null` | 資料夾不存在也不顯示錯誤 |
| `2>&1` | 錯誤訊息也當成一般輸出 | `make hls > log.txt 2>&1` | 錯誤也一起存進檔案 |
| `&&` | 前一個**成功**才執行下一個 | `git pull && make csim` | 更新成功才測試 |
| `\|\|` | 前一個**失敗**才執行下一個 | `make hls \|\| echo 失敗` | |
| `;` | 不管成功與否，依序執行 | `cd ~; ls` | |
| `\` | 行尾的反斜線：指令太長時接到下一行 | | |
| `#` | 後面是註解，不會執行 | `make csim   # 看到 ALL PASS` | 手冊裡的說明文字 |
| `~` | 你的家目錄 | `cd ~` | `/home/anthony` |
| `.` / `..` | 目前資料夾 / 上一層 | `cd ..` | |
| `*` | 萬用字元 | `ls kernels/*.cpp` | 所有 .cpp 檔 |
| `$變數` | 取出變數的值 | `echo $XILINX_XRT` | |

### 變數的兩種用法
```bash
KERNEL=trimul_v2 vitis-run ...     # ① 寫在指令前面：只對這一個指令有效（環境變數）
make hls KERNEL=trimul_v2          # ② 寫在 make 後面：傳給 Makefile 的變數
```

### 常用按鍵
| 按鍵 | 用途 |
|---|---|
| **Tab** | 自動補完檔名或指令（按兩下列出所有可能） |
| **↑ / ↓** | 叫出之前輸入過的指令 |
| **Ctrl + C** | **中斷**正在執行的程式（跑錯了、卡住了都用這個） |
| **Ctrl + R** | 搜尋歷史指令 |
| **Ctrl + L** | 清除畫面 |
| **q** | 離開 `less`、`man` 這類翻頁畫面 |

### 忘記怎麼用時
```bash
指令 --help        # 大部分指令都有簡短說明
man 指令           # 完整手冊（按 q 離開）
make help          # 本專案的指令一覽
```

---

## 5.2 Linux 基本操作

| 指令 | 格式 | 用途 | 例子 | 狀態 |
|---|---|---|---|---|
| `ssh` | `ssh 帳號@主機` | 登入遠端 server | `ssh anthony@scd-lab-server63` | ✅ |
| `pwd` | `pwd` | 顯示目前所在的資料夾 | | ⬜ |
| `ls` | `ls [-la] [路徑]` | 列出檔案；`-l` 詳細、`-a` 含隱藏檔 | `ls /tools/Xilinx` | ✅ |
| `cd` | `cd 路徑` | 切換資料夾 | `cd ForClaude/fpga/trimul` | ✅ |
| `cat` | `cat 檔案` | 印出整個檔案 | `cat cfg/trimul_v2.cfg` | ⬜ |
| `head` | `head -n 行數 檔案` | 印出前幾行 | `head -n 60 xxx.rpt` | ✅ |
| `tail` | `tail -n 行數 檔案` | 印出最後幾行（看錯誤訊息最常用） | `tail -n 30 hls_trimul_v4.log` | 🔜 |
| `tail -f` | `tail -f 檔案` | **持續**顯示檔案新增的內容（看進度） | `tail -f hls_trimul_v3.log` | ⬜ |
| `less` | `less 檔案` | 翻頁閱讀長檔案（↑↓ 翻、`/` 搜尋、`q` 離開） | `less xxx_csynth.rpt` | ⬜ |
| `grep` | `grep [-i] 關鍵字 檔案` | 找出含關鍵字的行；`-i` 不分大小寫；`-n` 顯示行號 | `grep -n ERROR hls_trimul_v4.log` | ✅ |
| `find` | `find 路徑 -name "樣式"` | 找檔案 | `find /tools -iname "*u55c*"` | ✅ |
| `which` | `which 指令` | 這個指令裝在哪裡（找不到代表沒裝或沒載入） | `which v++` | ✅ |
| `echo` | `echo 文字或$變數` | 印出文字或變數 | `echo $PATH` | ⬜ |
| `mkdir` | `mkdir -p 資料夾` | 建立資料夾 | `mkdir -p ~/results` | ⬜ |
| `cp` / `mv` | `cp 來源 目的` | 複製 / 移動（或改名） | `cp hls_summary.csv ~/results/` | ⬜ |
| `rm` | `rm [-r] 檔案` | ⚠️ **刪除，無法復原**；`-r` 刪資料夾 | `rm -f host.exe` | ⚠️ |
| `df -h` | `df -h` | 硬碟剩多少空間 | | ⬜ |
| `du -sh` | `du -sh 資料夾` | 某個資料夾佔多少空間（`hls_prj/` 會越來越大） | `du -sh hls_prj` | ⬜ |
| `top` / `htop` | `top` | 看 CPU、記憶體用量與正在跑的程式（`q` 離開） | 確認合成是否還在跑 | ⬜ |
| `history` | `history` | 列出輸入過的指令 | `history \| grep make` | ⬜ |
| `source` | `source 檔案` | 在目前的終端機執行設定檔（載入環境變數） | 見 5.3 | 🔜 |

> ⚠️ `rm -rf` 會直接刪除整個資料夾，不會經過資源回收筒。刪除前先用 `ls` 確認內容；
> 想清掉本專案產生的檔案，改用 `make clean` 比較安全。

---

## 5.3 環境調查與設定

| 指令 | 用途 | 結果 / 狀態 |
|---|---|---|
| `lspci \| grep -i -E "xilinx\|amd\|altera"` | 列出 PCIe 裝置，找 FPGA 卡 | ✅ 空的 |
| `lspci -d 10ee:` | 只列 Xilinx（廠商代號 10ee）的裝置 | ✅ 空的 → **server63 沒有卡** |
| `which vivado vitis v++ vitis-run` | 確認工具有沒有裝 | ✅ 都在 `/tools/Xilinx/2025.2/` |
| `which vitis_hls` | | ✅ 找不到（2025.2 已移除） |
| `ls /tools/Xilinx` | 看裝了哪些版本 | ✅ `2025.2` |
| `xbutil examine` | 列出 FPGA 卡、shell、狀態（需要 XRT） | ✅ command not found |
| `ls /opt/xilinx/platforms` | 找 U55C platform | ✅ 沒有 |
| `find /opt /tools -maxdepth 4 -iname "*u55c*"` | 找 U55C 相關檔案 | ✅ 沒有 |
| `module avail` | 有些 server 用 module 管理工具版本 | ✅ 沒有相關結果 |
| `nvidia-smi` | 看有沒有 NVIDIA GPU | ✅ 沒有 GPU |
| `find /tools/Xilinx/2025.2 -maxdepth 6 -type d -iname "virtexuplus*"` | 確認 U55C 晶片型號資料有裝 | ⬜（HLS 報告顯示 `virtexuplusHBM`，代表有裝） |

### 載入環境（找到有 U55C 的機器後會用到）
```bash
source /tools/Xilinx/2025.2/Vitis/settings64.sh   # 載入 Vitis（server63 看起來已自動載入）
source /opt/xilinx/xrt/setup.sh                   # 載入 XRT（有卡的機器才有）
```
- 每次登入都要執行，或寫進 `~/.bashrc` 讓它自動執行。
- 載入後 `echo $XILINX_XRT` 會顯示路徑，`make host` 需要這個變數。

### 在有 U55C 的機器上要跑的指令（🔜）
```bash
lspci -d 10ee:                   # 應該看到兩行（U55C 有兩個 PCIe function）
xbutil examine                   # 列出卡片與 BDF（例如 0000:3b:00.1）
xbutil examine -d <BDF>          # 看這張卡目前的 shell（platform）名稱
xbutil validate -d <BDF>         # 板子自我檢測（約數分鐘）
ls /opt/xilinx/platforms         # platform 資料夾名稱 = Makefile 的 PLATFORM
```

---

## 5.4 Git：取得與更新程式碼

| 指令 | 格式 | 用途 | 狀態 |
|---|---|---|---|
| `git clone` | `git clone -b 分支 網址` | 第一次下載整個專案 | ✅ |
| `git pull` | `git pull` | 下載 Claude 推上去的最新修改（**最常用**） | ✅ |
| `git status` | `git status` | 看有沒有被你改過的檔案 | ⬜ |
| `git log --oneline` | `git log --oneline \| head` | 看最近的修改紀錄 | ⬜ |
| `git diff` | `git diff [檔案]` | 看你改了哪些地方 | ⬜ |
| `git branch` | `git branch` | 看目前在哪個分支 | ⬜ |
| `git checkout -- 檔案` | | ⚠️ 放棄你對某個檔案的修改，還原成最新版 | ⚠️ |

本專案的 clone 指令：
```bash
git clone -b claude/lightnobel-memory-optimization-yhokyc https://github.com/antony3911/ForClaude.git
```

### `git pull` 失敗時
如果出現 `Your local changes would be overwritten`，代表你在 server 上改過某個檔案：
```bash
git status                  # 看是哪個檔案
git stash                   # 先把你的修改暫存起來
git pull                    # 再更新
git stash pop               # 需要的話把修改拿回來（可能要手動合併）
```

> ⚠️ **不要在 server 上執行 `git push`。** 程式碼的修改由 Claude 推上 GitHub，server 只負責下載與執行。

---

## 5.5 tmux：斷線也不會中斷的終端機

長時間的工作（`make hls-all`、上板編譯）一定要在 tmux 裡跑。

| 操作 | 指令 / 按鍵 | 狀態 |
|---|---|---|
| 開新的 session | `tmux` 或 `tmux new -s hls`（取名 hls） | ✅ |
| 暫時離開（程式繼續跑） | `Ctrl + B`，放開，再按 `D` | ✅ |
| 列出所有 session | `tmux ls` | ⬜ |
| 回到 session | `tmux attach` 或 `tmux attach -t hls` | 🔜 |
| 在 tmux 裡往上捲動 | `Ctrl + B`，放開，再按 `[`，用方向鍵捲；按 `q` 離開 | ⬜ |
| 結束 session | 在裡面輸入 `exit` | ⬜ |

---

## 5.6 本專案的 make 指令（最重要）

所有 make 指令都要在 **`ForClaude/fpga/trimul`** 資料夾裡執行。

### 格式
```
make  目標  [變數=值 變數=值 ...]
│     │     │
│     │     └─ 調整參數（不給就用預設值）
│     └─ 要做哪件事（csim、hls、run ...）
└─ 讀取目前資料夾的 Makefile
```
加上 `-n` 可以**只顯示會執行哪些指令、但不真的執行**，用來檢查：`make -n hls KERNEL=trimul_v3`

### 目標一覽
| 目標 | 做什麼 | 需要 | 時間 | 產出 | 狀態 |
|---|---|---|---|---|---|
| `make help` | 列出所有指令 | — | 瞬間 | — | ⬜ |
| `make csim` | g++ 編譯 testbench，5 個版本和正確答案比對 | g++ | 秒 | 畫面上的 PASS/FAIL | ✅ |
| `make hls KERNEL=...` | 合成一個版本，產生 cycle 數與資源報告 | Vitis | 數分鐘～數十分鐘 | `hls_prj/<kernel>/sol/syn/report/` | ✅（v2） |
| `make hls-all` | 依序合成 v0～v4，最後自動 `make summary` | Vitis | 數十分鐘以上 | `hls_<kernel>.log`、`hls_summary.csv` | 🟡 進行中 |
| `make summary` | 讀取所有報告，印出比較表 | Python 3 | 秒 | `hls_summary.csv` | 🔜 |
| `make hls-sweep` | v2 的 tile 大小掃描（4/8/16/32），各自存成 `hls_prj/trimul_v2_t<N>` | Vitis | 數十分鐘 | 4 份報告 | 🔜 |
| `make model` | 分析模型：預測 cycle、資源、最大 L，並和 HLS 報告比對誤差 | Python 3 | 秒 | `model_dse.csv` | 🔜 |
| `make xo KERNEL=... TARGET=hw` | `v++ -c`：把 kernel 編成 .xo | Vitis ＋ platform | 數分鐘 | `build/hw/<tag>.xo` | ⬜ |
| `make xclbin KERNEL=... TARGET=hw` | `v++ -l`：接上 platform 產生 bitstream | Vitis ＋ platform | **1～數小時** | `build/hw/<tag>.xclbin` | ⬜ |
| `make host` | 編譯 host 程式 | XRT | 秒 | `host.exe` | ⬜ |
| `make run ...` | 執行（emulation 或上板） | XRT（上板需要卡） | 視 L 而定 | 畫面上的時間、誤差、CSV 行 | ⬜ |
| `make clean` | ⚠️ 刪除所有產生的檔案（`build/`、`hls_prj/`、log、csv） | — | 瞬間 | — | ⚠️ |

> ⚠️ `make clean` 會刪掉 `hls_summary.csv` 和所有 HLS 報告。清之前先把要保留的結果複製到別的地方：
> `mkdir -p ~/results && cp hls_summary.csv ~/results/`

### 可以調整的變數
| 變數 | 預設值 | 用途 | 例子 |
|---|---|---|---|
| `KERNEL` | `trimul_v2` | 選版本 | `KERNEL=trimul_v4` |
| `TARGET` | `hw_emu` | `sw_emu`（軟體模擬）／`hw_emu`（硬體模擬）／`hw`（上板） | `TARGET=hw` |
| `PLATFORM` | `xilinx_u55c_gen3x16_xdma_3_202210_1` | 必須和卡上的 shell 一致 | `PLATFORM=<ls /opt/xilinx/platforms 看到的名稱>` |
| `CFG` | `cfg/$(KERNEL).cfg` | HBM 接線設定 | `CFG=cfg/trimul_v2_onebank.cfg` |
| `DEFS` | 空 | 編譯時定義，目前用來改 tile 大小 | `DEFS="-DTILE_I=16 -DTILE_J=16"` |
| `TAG` | 同 `KERNEL` | 輸出檔名，做不同實驗時避免覆蓋 | `TAG=v2_t16` |
| `RUN_L` | `16` | `make run` 的序列長度 | `RUN_L=512` |
| `RUN_ARGS` | 空 | 傳給 host.exe 的額外參數 | `RUN_ARGS="3 tensor"` |
| `DATA` | 空 | 真實資料的資料夾（設定後忽略 `RUN_L`） | `DATA=../../data/spike` |
| `KERNELS` | v0～v4 | `hls-all` 要跑哪些版本 | `KERNELS="trimul_v3 trimul_v4"` |

### 常用組合（照實驗整理）
```bash
# ── 功能驗證 ──
make csim                                   # ✅ 隨機資料，L=32
make csim DATA=../../data/hba               # ⬜ 真實資料（有 GPU／Colab 產生資料後）

# ── 實驗 A：五個版本比較（HLS 報告） ──
make hls-all                                # 🟡 進行中
make hls-all KERNELS="trimul_v3 trimul_v4"  # ⬜ 只重跑失敗或新增的版本
make summary                                # 🔜 重新整理比較表

# ── 實驗 B：tile 大小 ──
make hls-sweep                                             # 🔜 一次跑 4/8/16/32
make hls-sweep SWEEP_KERNEL=trimul_v4 TILES="8 16"         # ⬜ 換版本或尺寸
make model                                                 # 🔜 模型 vs 報告、設計空間探索

# ── 上板（找到有 U55C 的機器後） ──
make xclbin KERNEL=trimul_v2 TARGET=hw PLATFORM=<實際名稱>    # ⬜ 1～數小時
make run    KERNEL=trimul_v2 TARGET=hw RUN_L=512              # ⬜

# ── 實驗 C：HBM 單一通道對照 ──
make run KERNEL=trimul_v2 CFG=cfg/trimul_v2_onebank.cfg TAG=trimul_v2_onebank TARGET=hw RUN_L=256   # ⬜

# ── 實驗 D：量化方式 ──
make run KERNEL=trimul_v4 TARGET=hw RUN_L=512                       # ⬜ per-token（預設）
make run KERNEL=trimul_v4 TARGET=hw RUN_L=512 RUN_ARGS="3 tensor"   # ⬜ per-tensor

# ── 實驗 E：序列長度掃描（收集成一個 CSV） ──
for L in 128 256 512 1024; do
  make run KERNEL=trimul_v2 TARGET=hw RUN_L=$L | grep ^CSV >> results.csv
done                                                                 # ⬜
```

---

## 5.7 Vitis 工具的原始指令（Makefile 背後在做什麼）

平常用 make 就好。這一節讓你知道 make 實際呼叫了什麼，除錯時會用到。

| make 目標 | 實際執行的指令 | 說明 |
|---|---|---|
| `make csim` | `g++ -std=c++17 -O2 ... tb/tb.cpp kernels/*.cpp -o csim.exe && ./csim.exe 32` | 一般 C++ 編譯 |
| `make hls` | `KERNEL=trimul_v2 DEFS="" vitis-run --mode hls --tcl hls/run_hls.tcl` | ✅ 2025.2 的 HLS 指令 |
| `make xo` | `v++ -c -t hw --platform <P> -k trimul_v2 -I kernels -o build/hw/trimul_v2.xo kernels/trimul_v2.cpp` | 編譯 kernel |
| `make xclbin` | `v++ -l -t hw --platform <P> --config cfg/trimul_v2.cfg -o build/hw/trimul_v2.xclbin build/hw/trimul_v2.xo` | 連結＋擺放繞線 |
| `make host` | `g++ ... host/host.cpp -I$XILINX_XRT/include -L$XILINX_XRT/lib -lxrt_coreutil -pthread -o host.exe` | 編譯 host |
| `make run`（emulation） | `emconfigutil --platform <P> --od .` 然後 `XCL_EMULATION_MODE=hw_emu ./host.exe ...` | 產生模擬設定並執行 |

### `v++` 常用選項
| 選項 | 意思 |
|---|---|
| `-c` / `-l` | compile（產生 .xo）／ link（產生 .xclbin） |
| `-t hw\|hw_emu\|sw_emu` | 目標 |
| `--platform` | platform 名稱 |
| `-k` | kernel 函式名稱 |
| `--config` | 設定檔（HBM 接線等） |
| `--save-temps --temp_dir` | 保留中間檔案，除錯時可以看 Vivado 的報告 |

### `run_hls.tcl` 可用的環境變數
```bash
KERNEL=trimul_v3 CSIM=1 vitis-run --mode hls --tcl hls/run_hls.tcl    # 合成前先在 HLS 裡跑 C 模擬
KERNEL=trimul_v3 COSIM=1 vitis-run --mode hls --tcl hls/run_hls.tcl   # 合成後再跑 C/RTL 協同模擬（較慢）
```
也可以透過 make 傳：`make hls KERNEL=trimul_v3 COSIM=1`（make 會把命令列變數傳給子程式）。

---

## 5.8 看結果

### HLS 報告
```bash
# 報告位置
ls hls_prj/trimul_v2/sol/syn/report/

# 前 60 行：timing 與 latency 摘要                                    ✅
head -n 60 hls_prj/trimul_v2/sol/syn/report/trimul_v2_csynth.rpt

# 資源用量那一段                                                     🔜
grep -n -A 20 "Utilization Estimates" hls_prj/trimul_v2/sol/syn/report/trimul_v2_csynth.rpt

# 只看各迴圈的 latency 與 II                                          ⬜
grep -n -A 15 "\* Loop:" hls_prj/trimul_v3/sol/syn/report/trimul_v3_csynth.rpt
```

### make hls-all 的進度與錯誤
```bash
ls hls_*.log                       # 哪些版本跑過了
tail -n 30 hls_trimul_v4.log       # 看某一版最後的輸出（失敗時截圖這個）   🔜
grep -n "ERROR" hls_trimul_*.log   # 一次找出所有錯誤                      ⬜
tail -f hls_trimul_v3.log          # 即時看正在跑的版本（Ctrl+C 離開）      ⬜
```

### 比較表
```bash
make summary                                   # 印出表格並存成 hls_summary.csv   🔜
column -s, -t < hls_summary.csv                # 在終端機把 CSV 排整齊            ⬜
python3 scripts/hls_summary.py --L 256         # 直接呼叫腳本（--L 要和 L_TRIP 一致）
```

### 把結果帶回自己的電腦
在**你自己的電腦**（Windows 的 PowerShell 或命令提示字元）執行：
```powershell
scp anthony@scd-lab-server63:~/ForClaude/fpga/trimul/hls_summary.csv C:\ForClaude\
```
`scp` 的格式是 `scp 來源 目的`，遠端路徑寫成 `帳號@主機:路徑`。

---

## 5.9 host 程式與 Python 腳本的參數

### `host.exe`（上板用，⬜）
```
./host.exe  <xclbin>  <kernel>  <L>  [reps=3]  [token|tensor]  [samples=2000]  [data_dir]
```
| 參數 | 意思 |
|---|---|
| `xclbin` | 編譯好的電路檔 |
| `kernel` | kernel 名稱（`trimul_v2` 等） |
| `L` | 序列長度，必須是 tile 大小的倍數（給了 `data_dir` 就以檔案為準） |
| `reps` | 重複執行幾次，取最快的一次 |
| `token` / `tensor` | v4 的量化方式 |
| `samples` | 隨機抽幾個點驗證正確性 |
| `data_dir` | 真實資料的資料夾 |

輸出的最後一行是 CSV：
```
CSV,kernel,L,time_ms,gflops,est_traffic_GB,est_GBps,hbm_footprint_MB,rel_l2,max_abs
```

### `python/dump_trimul_inputs.py`（需要 GPU 或 Colab，⬜）
```
python dump_trimul_inputs.py  (--uniprot ID | --pdb ID | --fasta 檔案 | --seq 序列)  --out 資料夾
                              [--block 0~47] [--max-len N] [--pad 32] [--device cuda|cpu]
                              [--chunk-size 64] [--eval-channels 16]
```
例：`python dump_trimul_inputs.py --uniprot P0DTC2 --out ../data/spike`

### `docs/manual/build_pdf.py`（重新產生這份手冊的 PDF）
```bash
pip install markdown
python3 docs/manual/build_pdf.py     # 產生 docs/manual/manual.html 與 manual.pdf
```

---

## 5.10 目前為止實際執行過的指令（時間軸）

| # | 指令 | 在哪裡 | 結果 |
|---|---|---|---|
| 1 | `lspci \| grep -i -E "xilinx\|amd\|altera\|intel.*fpga"` | server63 | 空的 |
| 2 | `which vivado vitis vitis_hls v++ xbutil` | server63 | Vivado/Vitis/v++ 有；vitis_hls、xbutil 沒有 |
| 3 | `ls /tools/Xilinx /opt/Xilinx /opt/xilinx` | server63 | `2025.2 DocNav flexlm xic` |
| 4 | `xbutil examine` | server63 | command not found |
| 5 | `which quartus aoc aocl`、`ls /opt/intelFPGA*` | server63 | 沒有（不是 Intel FPGA） |
| 6 | `module avail \| grep ...` | server63 | 沒有結果 |
| 7 | `lspci -d 10ee:` | server63 | 空的 → 沒有 FPGA 卡 |
| 8 | `ls /opt/xilinx/platforms`、`find ... "*u55c*"` | server63 | 沒有 platform |
| 9 | `which vitis-run g++ make git` | server63 | 都有 |
| 10 | `git clone -b ... ForClaude.git` | server63 | 需要 GitHub 帳號（private repo） |
| 11 | `cd ForClaude/fpga/trimul` | server63 | |
| 12 | `make csim` | server63 | （待確認是否 ALL PASS） |
| 13 | `make hls KERNEL=trimul_v2` | server63 | 失敗 3 次（2025.2 路徑問題）→ 修正後成功 |
| 14 | `git pull` | server63 | 取得修正版 |
| 15 | `head -n 60 .../trimul_v2_csynth.rpt` | server63 | 第一筆數據：177,029,185 cycles |
| 16 | `tmux` → `make hls-all` | server63 | 🟡 進行中 |

---

## 5.11 常見錯誤與排查

| 看到的訊息 | 意思 | 怎麼辦 |
|---|---|---|
| `command not found` | 沒裝，或環境沒載入 | `which 指令`；試 `source .../settings64.sh`；問管理員 |
| `No such file or directory` | 路徑打錯，或不在正確的資料夾 | `pwd` 看自己在哪；`ls` 看檔案在不在；善用 Tab 補完 |
| `Permission denied` | 沒有權限 | 不要用 `sudo` 硬來，先問管理員 |
| `make: *** No rule to make target` | 不在 `fpga/trimul` 裡，或目標名稱打錯 | `cd ~/ForClaude/fpga/trimul`；`make help` |
| `Username for 'https://github.com'` | repo 是 private | 改成 public，或用 fine-grained token |
| `Your local changes would be overwritten` | server 上的檔案被改過 | 見 5.4 節的 `git stash` |
| `ERROR: [HLS ...]` | HLS 失敗 | `tail -n 30 hls_<kernel>.log` 截圖給 Claude |
| `WARNING: [HLS ...]` | 通常可以忽略 | 只有同時出現 ERROR 才需要處理 |
| `No space left on device` | 硬碟滿了 | `du -sh hls_prj build`；確認結果已保存後 `make clean` |
| 畫面卡住很久沒動 | 可能正常（合成很慢），也可能卡住 | 另開一個 tmux 視窗用 `top` 看 CPU 有沒有在跑 |

### 回報問題時請提供
1. 完整的指令
2. 錯誤前後 20～30 行的輸出（`tail -n 30 xxx.log`）
3. 你預期會發生什麼
4. 已經試過什麼

---

## 本章小結

- 指令 = **名稱 ＋ 選項 ＋ 參數**；用 `|`、`>`、`&&` 串接；忘了就 `--help`。
- 本專案的所有操作都可以用 **`make 目標 變數=值`** 完成，`make -n` 可以預覽不執行。
- **現在最常用的四個指令：** `git pull`、`make hls-all`、`tail -n 30 hls_*.log`、`make summary`。
- 長時間工作用 **tmux**；刪除前先確認，**不要在 server 上 `git push`**。

---

## 自我檢測
讀完這一章，試著回答下面的問題（參考答案在附錄 B）：

1. `lspci | grep -i xilinx` 中的 `|` 做了什麼？`-i` 是什麼意思？
2. 想知道 `make hls KERNEL=trimul_v3` 會執行哪些指令、但不要真的執行，要怎麼下？
3. 合成要跑很久，SSH 又可能斷線，該怎麼做？斷線後怎麼回到原本的畫面？
4. 想合成 16×16 tile 的 v4，但不要覆蓋 v4 預設設定的報告，指令怎麼寫？
5. 執行 `make clean` 之前應該先做什麼？

**下一章**介紹新的專題策略：融合資料流架構、分析模型與設計空間探索，以及背後的理論。
