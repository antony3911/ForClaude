# 教學手冊：從 LightNobel 到 FPGA 上的記憶體優化

> **這是什麼：** 使用者的專題以 LightNobel (ISCA 2025) 為 reference。這份手冊要讓完全沒有 FPGA 經驗的人，
> 鉅細靡遺地理解「我們為何做、為何可做、做了什麼、工具怎麼運作」。之後的研究也會從這裡延伸，
> 所以每個知識點都要講清楚，並附上**具體例子**。
>
> **給接手的 Claude 對話：** 請先讀 `docs/PROJECT_LOG.md`（專題工作紀錄），再看下面的**撰寫進度表**，
> 從第一個「⬜ 未開始」或「🟡 撰寫中」的章節接著寫。風格要求見本檔最後一節。

---

## 撰寫進度表

| 章 | 檔案 | 狀態 | 備註 |
|---|---|---|---|
| 0 | `README.md`（本檔：大綱與進度） | ✅ 完成 | |
| 1 | `01_why.md` 為何而做：問題具體是什麼 | ⬜ 未開始 | |
| 2 | `02_why_it_works.md` 為何可做：各解法的原理 | ⬜ 未開始 | |
| 3 | `03_workflow.md` 整體流程：做了什麼、產生什麼 | ⬜ 未開始 | |
| 4 | `04_tools.md` 工具原理：C++ 怎麼變電路 | ⬜ 未開始 | |
| 5 | `05_research_method.md` 研究方法：之後讀 paper 可重複使用的步驟 | ⬜ 未開始 | |
| 6 | `06_glossary.md` 術語表 | ⬜ 未開始 | |
| — | `build_pdf.py` → `manual.pdf` | ⬜ 未開始 | 所有章節完成後輸出 PDF |

狀態：⬜ 未開始　🟡 撰寫中　✅ 完成

---

## 詳細大綱

### 第 1 章　為何而做：問題具體發生了什麼？
1.1 蛋白質結構預測在做什麼（序列 → 3D 結構；為什麼重要）
1.2 AlphaFold2 / ESMFold 的架構全貌
　　- ESM-2 語言模型 → Folding trunk（48 個 block）→ Structure module
　　- Sequence representation（L×C）與 **Pair representation（L×L×C）**
1.3 Triangle Multiplication / Triangle Attention 在做什麼（「三角形」的直覺）
1.4 問題的具體樣貌：**記憶體隨 L² 成長**
　　- 例：L = 500 / 1000 / 2000 / 4000 時 pair tensor 與中間值的大小
　　- 權重 vs. activation：為什麼瓶頸是 activation 而不是模型大小
1.5 第二個問題：**搬資料比計算慢**（memory-bound）
　　- 計算量 O(L³·C)、資料量 O(L²·C)，但實作上反覆讀取
　　- 例：v0 每做 2 次運算要讀 8 bytes
1.6 LightNobel 的觀察與解法（高層次，細節以原文為準）
1.7 我們的定位：只取最關鍵的一個運算，比較常見手法

### 第 2 章　為何可做：這些解法從什麼概念上解決問題？
2.1 核心概念：記憶體階層（register / on-chip / off-chip）與搬運成本
2.2 **算術強度（Arithmetic Intensity）與 Roofline 模型**（整章的主軸）
2.3 解法一　Tiling / 資料重用 → 降低總搬運量（附公式推導與 v0 vs v1 的數字）
2.4 解法二　寬位元 / Burst → 提高每次搬運的效率（頻寬 vs 延遲、Little's Law）
2.5 解法三　Double buffering / 重疊 → 把等待時間藏起來（以 v2 報告 141 vs 526 為例，為何上限約 20%）
2.6 解法四　多通道（HBM pseudo-channel）→ 同時使用多條路
2.7 解法五　量化 → 讓每筆資料變小（INT8 原理、scale、誤差來源、per-token vs per-tensor、outlier）
2.8 其他常見手法（本專題未實作，但報告可提）：chunking、recomputation、operator fusion、稀疏化
2.9 為什麼「效益可能不大」仍然算解法：瓶頸轉移、Amdahl's Law

### 第 3 章　整體流程：從頭到現在具體做了什麼？
3.1 全景圖（流程圖）
3.2 步驟一　界定範圍：為什麼只挑 Triangle Multiplication
3.3 步驟二　資料排列（memory layout）與算式
3.4 步驟三　寫 5 個 kernel（逐版逐段解說程式碼）
3.5 步驟四　正確性驗證：testbench、C 模擬、誤差指標（rel_l2）
3.6 步驟五　host 程式：怎麼把資料送進 FPGA
3.7 步驟六　HBM 連接設定（.cfg）
3.8 步驟七　Makefile：把流程串起來
3.9 步驟八　真實資料管線（Python + ESMFold）與「差值 0」驗證
3.10 步驟九　在實際 server 上遇到的問題與除錯過程（2025.2 路徑 bug 的推理）
3.11 步驟十　讀懂 HLS 報告（逐欄解說 v2 報告）
3.12 產生的所有檔案總表

### 第 4 章　工具原理：為何 C++ 可以變成電路？
4.1 FPGA 是什麼：LUT、FF、DSP、BRAM/URAM、繞線、bitstream
4.2 FPGA vs CPU vs GPU：為什麼能「客製化」
4.3 HLS（High-Level Synthesis）如何運作
　　- 前端：clang/LLVM 解析 C++
　　- 排程（scheduling）、資源配置（allocation）、綁定（binding）
　　- 產生 RTL（Verilog/VHDL）
　　- 每個 pragma 的意義（PIPELINE、II、ARRAY_PARTITION、DEPENDENCE、INTERFACE、INLINE、LOOP_TRIPCOUNT）
4.4 為什麼 C++ 可以直接模擬：C 語意 = 功能規格；csim / cosim / hw_emu 的差別
4.5 Vivado：synthesis → place & route → bitstream
4.6 Vitis 與 `v++`：.xo、.xclbin、platform（shell）的角色
4.7 XRT：host 程式怎麼控制 FPGA（device、xclbin、buffer object、kernel run）
4.8 Python 端：PyTorch、HuggingFace、ESMFold 權重從哪來
4.9 **誰提供了什麼能力？**（AMD 工具、開源工具、下載的模型、Claude 寫的程式碼：清楚劃分）
4.10 Claude 在這個對話中呼叫的工具與它們做了什麼

### 第 5 章　研究方法：之後可以重複使用的步驟
5.1 讀一篇架構 paper 的方法（問題 → 觀察 → 解法 → 評估）
5.2 找出瓶頸的 checklist（算量、資料量、算術強度、roofline）
5.3 從 paper 縮小成可實作的題目
5.4 實驗設計：對照組、一次只改一個變數、要量哪些指標
5.5 除錯的思路（以本專題的 2025.2 bug 為例）
5.6 報告要畫的圖

### 第 6 章　術語表
所有出現過的專有名詞，依主題分類，每個附一句白話解釋與「在本專題哪裡出現」。

---

## 撰寫風格（給接手的對話）
- **繁體中文**，台灣用語（記憶體、軟體、程式碼、硬體）。
- 每個概念：**白話直覺 → 正式定義 → 本專題的具體例子（附數字）**。
- 多用表格和 ASCII 圖；公式用 code block 或行內 code 呈現（PDF 轉換不支援 LaTeX）。
- 對 LightNobel 的具體數字不確定時，寫「細節以原文為準」，不要編造。
- 誠實標示哪些已驗證、哪些尚未在實機上驗證。
- 每章開頭放「本章重點」，結尾放「本章小結」。
- 每章寫完：更新上面的進度表 → commit → push。
