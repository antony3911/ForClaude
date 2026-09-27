# 教學手冊：從 LightNobel 到 FPGA 上的記憶體優化

> **這是什麼：** 使用者的專題以 LightNobel (ISCA 2025) 為 reference。這份手冊要讓完全沒有 FPGA 經驗的人，
> 鉅細靡遺地理解「我們為何做、為何可做、做了什麼、工具怎麼運作」。之後的研究也會從這裡延伸，
> 所以每個知識點都要講清楚，並附上**具體例子**。
>
> **給接手的 Claude 對話：** 請先讀 `docs/PROJECT_LOG.md`（專題工作紀錄），再看下面的**撰寫進度表**，
> 從第一個「⬜ 未開始」或「🟡 撰寫中」的章節接著寫。風格要求見本檔最後一節。

---

## 撰寫進度表

> 2026-09-27 重新編排成教科書結構：問題 → 原理 → 案例（LightNobel）→ 實作 → 專題（舊→新章節對照見 `docs/PROJECT_LOG.md` 8.3 節）。

| 部 | 檔案 | 內容 | 狀態 |
|---|---|---|---|
| 前言 | `00_guide.md` | 導讀：結構、閱讀路線、慣例、最短上手路徑 | ✅ |
| 速覽 | `00b_overview.md` | 來龍去脈、全書地圖、LightNobel 與本專題各一分鐘版、概念地圖 | ✅ |
| 一 問題 | `01_problem.md` | 第 1 章 蛋白質結構預測與 pair representation | ✅ |
| 一 問題 | `02_memory_wall.md` | 第 2 章 記憶體牆：容量、頻寬、roofline、Amdahl、三層框架 | ✅ |
| 二 原理 | `03_dataflow.md` | 第 3 章 資料流優化：tiling、burst、double buffering、多通道、融合、重算、分塊 | ✅ |
| 二 原理 | `04_quantization.md` | 第 4 章 量化：原理、per-token、尺的成本與格式、位元數 | ✅ |
| 三 案例 | `05_lightnobel.md` | 第 5 章 LightNobel 的觀察、演算法與成果 | ✅ |
| 三 案例 | `06_lightnobel_hw.md` | 第 6 章 LightNobel 的硬體架構 | ✅ |
| 四 實作 | `07_fpga_tools.md` | 第 7 章 FPGA 與工具原理 | ✅ |
| 四 實作 | `08_implementation.md` | 第 8 章 v0～v4 從程式碼到報告 | ✅ 有 hls-all 結果後更新 8.11 |
| 四 實作 | `09_evaluation.md` | 第 9 章 評估方法：architectural simulation、分析模型、DSE、容量 | ✅ 有 hls-all 結果後更新 9.2、9.3 |
| 五 專題 | `10_strategy.md` | 第 10 章 專題策略：定位、融合設計、v5、海報與評審問答 | ✅ 有真實資料、v5 結果後更新 10.4 |
| 五 專題 | `11_research_method.md` | 第 11 章 研究方法（含 11.11 誤判案例） | ✅ |
| 附錄 | `A_commands.md` | 附錄 A 指令手冊 | ✅ 新增指令時更新 A.10 時間軸 |
| 附錄 | `B_glossary.md` | 附錄 B 術語表 | ✅ |
| 附錄 | `C_answers.md` | 附錄 C 自我檢測參考答案 | ✅ |
| — | `build_pdf.py` → `manual.pdf` | 合併輸出 | ✅ |

狀態：⬜ 未開始　🟡 撰寫中　✅ 完成

---

## 如何閱讀與更新
- **直接看：** `manual.pdf`（排版版）或在 GitHub 上逐章看 `.md`。
- **更新：** 修改各章 `.md` 後執行 `pip install markdown && python3 docs/manual/build_pdf.py`，
  會重新產生 `manual.html` 與 `manual.pdf`（需要 Chrome/Chromium；找不到時只產生 HTML，可用瀏覽器列印成 PDF）。
- **ASCII 圖：** 中文字在等寬區塊中算 2 格寬；畫方框時請照這個規則對齊。

## 撰寫風格（給接手的對話）
- **繁體中文**，台灣用語（記憶體、軟體、程式碼、硬體）。
- 每個概念：**白話直覺 → 正式定義 → 本專題的具體例子（附數字）**。
- 多用表格和 ASCII 圖；公式用 code block 或行內 code 呈現（PDF 轉換不支援 LaTeX）。
- LightNobel 的數字要標出處（Sec.／Fig.／Table）；不確定時寫「細節以原文為準」，不要編造。論文 PDF 不要 commit（repo 公開）。
- 誠實標示哪些已驗證、哪些尚未在實機上驗證。
- 每章開頭放「本章重點」，結尾放「本章小結」。
- 每章結尾：本章小結 → 自我檢測（答案寫進 `C_answers.md`）→「下一章」銜接。
- 每章寫完：更新上面的進度表 → commit → push。
- 新增或調整章節時，同步修改 `build_pdf.py` 的 `CHAPTERS`。
