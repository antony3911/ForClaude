# 03. 申請材料與策略

> PhD 申請的權重大致是：**研究經驗與成果 ≈ 推薦信 > 研究契合度（SOP） > 學校背景與 GPA > 英文**。MS 則是 GPA、學校背景、專題經驗比重較高。

---

## 3.1 選校配比

### PhD（建議 10–14 所）

| 類型 | 數量 | 定義 |
|---|---|---|
| 夢幻 | 3–4 | 頂尖學校，而且有非常 fit 的教授 |
| 實力相當 | 5–6 | 你的論文和推薦信在這些學校有競爭力 |
| 保底 | 2–4 | 中段研究型大學，但**要有真正想跟的教授**（不要為了保底而申請一所去了也不開心的學校） |

**鐵則**
- **每所學校至少要有 2 位 fit 的教授**：單一教授可能那年剛好不收學生、正在休假，或者要離開
- 不要只看 US News 排名。電腦結構／IC 設計強的學校，不一定是綜合排名最前面的學校
- 名單和評估方法見 [05](05-schools-and-labs.md)

### 錄取機制差異（會影響你聯繫教授的策略）

| 類型 | 說明 | 聯繫教授的效果 |
|---|---|---|
| 委員會制 | 系上委員會統一審核（例如 MIT EECS、Berkeley EECS、CMU ECE） | 仍然有幫助：教授可以在委員會裡替你說話，但無法單獨決定 |
| 教授主導 | 教授有經費就能直接要人（很多公立大學和中段學校） | **非常重要**，常常是決定性因素 |
| 第一年不綁定指導教授 | 第一年由系上資助，入學後再找 advisor（Stanford EE 等學校常見這種模式） | 入學後要主動找教授；錄取時要確認第一年之後的經費保障 |

---

## 3.2 Statement of Purpose (SOP)

### 結構（PhD 版，約 1–2 頁或 ~1,000 字，依各校限制調整）

1. **開頭（1 段）**：直接切入你想解決的研究問題，**不要講童年故事**
   > 例：「Protein structure prediction models such as AlphaFold break down on long sequences not because of compute, but because their pairwise representations grow quadratically in memory…」
2. **研究經驗（2–3 段，這是主體）**：每段講一個研究故事，包含
   - 問題是什麼、為什麼重要
   - **你**做了什麼決定、為什麼這樣決定（展現研究判斷力，而不是只列工作項目）
   - 遇到什麼困難、怎麼解決
   - 量化結果（加速比、能效、記憶體節省）
   - 學到什麼，這件事如何引導你到下一步
3. **未來研究方向（1 段）**：你想在 PhD 期間探索的問題，要比現在的題目更廣一層（例如從蛋白質延伸到長序列、記憶體受限的 AI workload）
4. **Why this school（1 段，每校客製化）**：點名 2–3 位教授，提到他們**具體的論文或專案**，說明你的背景如何銜接
5. **結尾（2–3 句）**：職涯目標

### SOP 常見地雷

- ❌ 「I have been passionate about … since I was a child」
- ❌ 列修課清單（成績單上都有了）
- ❌ 空泛稱讚學校（「world-renowned faculty」）
- ❌ 所有學校都用同一篇，只改校名（教授一看就知道）
- ❌ 找代辦或 AI 生成整篇（見 [07](07-reality-check.md#76-學術誠信)）
- ✅ 具體、量化、有「我」的判斷、有清楚的研究脈絡

### 其他文件

- **Research Statement**：少數學校另外要求，更聚焦在研究本身
- **Personal History／Diversity Statement**：過去 UC 系統等學校會要求。2025 年起有些學校調整了這類文件的要求，以當年申請系統為準
- **短文題**：例如「描述一次失敗」，準備 2–3 個通用故事

---

## 3.3 CV

**原則**：1–2 頁，研究放最前面，每一行都要能在面試時講 3 分鐘。

建議順序：
1. Education（GPA 若不錯就寫；排名若有優勢也可以寫）
2. **Research Experience**（每項 2–4 個 bullet，強動詞開頭，加上量化結果）
   > 「Designed a tiled dataflow for triangle multiplicative updates on an HBM FPGA (Alveo U280), reducing off-chip traffic by 5.2× and achieving 3.1× speedup over an optimized A100 baseline at L = 2,048.」（數字為範例）
3. **Publications**（已接受、審稿中都可以，誠實標示狀態）
4. Projects（ASIC implementation、開源 repo）
5. Skills（分類寫）：
   - HDL/HLS：SystemVerilog, Verilog, Vitis HLS, (Chisel)
   - EDA：Design Compiler/Genus, PrimeTime, ICC2/Innovus, VCS/Xcelium, Vivado
   - Programming：Python (PyTorch), C++, Tcl
   - Verification：SVA, cocotb, (UVM)
6. Honors & Awards、Teaching（助教經驗很加分，表示你能當 TA）

---

## 3.4 推薦信

### 組合（通常要 3 封）

| 優先順序 | 推薦人 | 為什麼 |
|---|---|---|
| 必備 | **研究指導教授** | 最了解你的研究能力 |
| 強烈建議 | 另一位知道你研究的老師（共同作者、合作計畫的老師、口試委員） | 從第二個角度佐證你的研究能力 |
| 加分 | **在美國的合作者**、業界實習主管（例如在台灣的 NVIDIA/Google/MediaTek） | 美國教授熟悉的推薦人，或者業界觀點 |
| 可接受 | 修課表現很突出、而且真的互動過的老師 | 最後的選擇 |

### 怎麼讓推薦信寫得好

- **現在就開始經營**：讓推薦人真正看到你的研究過程（定期報告、主動討論）
- 提供**資料包**（範本在 [10](10-templates.md#2-給推薦人的資料包brag-sheet)）：CV、SOP 草稿、你們共事的具體事例、各校截止日
- **至少提前 6–8 週請託**，截止日前 2 週禮貌提醒
- 送出後，記得寫感謝信並告知結果

### ⚠️ 關於「自己寫推薦信給老師簽」

台灣很常見，但**強烈不建議**：
- 美國審查委員看過大量推薦信，由同一個人寫的三封信，口吻和用詞會很像
- 內容容易流於空泛，缺少只有推薦人才知道的細節
- 這有學術誠信問題

如果老師要求你提供草稿：提供**事實清單與具體事例**（資料包），而不是一封寫好的信。

---

## 3.5 聯繫教授（套磁）

### 什麼時候
- **第一波：9–10 月**（讀完對方近期論文後）
- **第二波：送件後的 11–12 月**（附上 application ID，告知已申請）
- 如果對方的網站寫明「請不要寫信給我詢問招生」→ **尊重對方**，不要寫

### 原則
- **短**：150–250 字，教授一天會收到幾十封這種信
- **具體**：提到他們的 1–2 篇論文，以及你的研究如何接得上
- **有證據**：附上 CV、1 頁研究摘要、論文或 preprint 連結
- **標題清楚**：`Prospective PhD student (Fall 2028) — long-sequence protein structure prediction accelerator, FPGA/ASIC co-design`
- **不要群發**：一眼就看得出來
- 沒回信很正常（回覆率可能只有一到三成），**沒回信不等於拒絕**。2–3 週後可以禮貌地追問一次，之後就不要再寄了

範本在 [10](10-templates.md#1-聯繫教授的信cold-email)。

---

## 3.6 其他加分項

- **個人網站**：一頁式就好，包含研究摘要、論文、CV、GitHub 連結、ASIC layout 圖
- **GitHub**：README 寫清楚、能重現主要實驗、有測試
- **3 分鐘研究影片或投影片**：不是必要的，但準備過程能幫你練好面試
- **海外經驗**：美國的暑期研究或實習（J-1 或遠端合作皆可）；能拿到美國推薦信的價值很高

---

## 3.7 面試

### 形式
- 多為 Zoom，30–60 分鐘，面試官是教授本人，有時會加上他的學生
- 常見流程：自我介紹 → **研究深入追問** → 技術問題 → 你提問

### 常見問題（準備好英文答案）

**研究類**
- Walk me through your research in 3 minutes.
- What was the hardest part? What would you do differently?
- Why FPGA rather than GPU for this workload? What changes if you move to ASIC?
- How does your design compare to LightNobel?
- If off-chip bandwidth doubles, how does your design change? What if on-chip SRAM halves?
- How did you verify correctness? How did you measure energy?

**技術類**
- Roofline model：你的 kernel 落在哪裡？
- Systolic array 的 dataflow（weight/output/row stationary）各有什麼取捨？
- 量化對準確度的影響，你怎麼評估？
- Setup／hold time、CDC 的處理方式
- Cache／記憶體階層的基礎觀念

**動機類**
- Why PhD? Why our lab? What do you want to do after the PhD?

### 你該問的問題（這很重要，會顯示你有想過）
- 實驗室目前的研究方向、下一步有哪些專案？
- 學生通常怎麼選題目？有沒有下線的機會？
- 經費來源（產業、政府）穩不穩定？RA 保障幾年？
- 學生的實習狀況？畢業生都去哪裡？
- 指導風格：多常 one-on-one？

---

## 3.8 費用估算

### 申請階段（約）

| 項目 | 金額（約） |
|---|---|
| 申請費 | 每校 US$75–150 × 12 所 ≈ US$900–1,800 |
| TOEFL | 每次約 US$200 以上 × 1–2 次（以 ETS 台灣報名頁為準） |
| 送分 | 每校約 US$20–30 |
| GRE（如果需要） | 約 US$220 以上，加上送分費 |
| 其他（成績單、郵寄、翻譯） | 數千元新台幣 |
| **合計** | **約 NT$6–9 萬** |

### 就學階段

| | PhD | MS（自費） |
|---|---|---|
| 學費 | 通常全免 | 公立（州外學生）約 US$3.5–6 萬／年；私立約 US$5.5–7.5 萬／年 |
| 生活費 | 由津貼支付（常見約 US$3–5 萬多／年，Bay Area/Boston 等高生活成本地區通常較高） | 約 US$2–4 萬以上／年，視地區而定 |
| 保險 | 通常包含在 package 內 | 約 US$3,000–6,000／年（學校保險） |
| **總計** | 大致收支平衡（取決於地區） | **1.5–2 年約 US$9–20 萬（約 NT$300–650 萬）** |

> 以上是粗估，務必查各校官方的「Cost of Attendance」。

### 獎學金（台灣）
- **教育部與世界百大合作設置獎學金**（PhD 新生）：教育部與 20 多所國外頂尖大學共同出資。2025 年公布的美國合作學校包含 UIUC、UC Berkeley、Cornell、Columbia、USC、Caltech、Northwestern、WashU、Johns Hopkins、UChicago、Harvard GSAS 等（**名單每年會變**），其中不少學校是加速器研究的重鎮。報名期間和申請季重疊
- **教育部留學獎學金**：須已有入學許可或已在學；一般生每年約 US$16,000，最長 2 年（以當年簡章為準）
- **教育部公費留學考試**：考試制；請詳讀簡章中的權利義務（例如是否有返國服務要求）
- **學術交流基金會（Fulbright Taiwan）**：提供免費的 EducationUSA 留學諮詢，並有赴美研究或進修的獎助項目（每年調整）
- 民間基金會與企業獎學金：每年種類不同，可以到教育部公費留學資訊網和各校國際處查詢

**帶著外部獎學金申請 PhD 是很大的優勢**：教授不用自己出錢，就能多收一位學生。

---

## 3.9 Offer 評估

| 面向 | 要問／要看的 |
|---|---|
| **指導教授 fit** | 研究方向、指導風格、實驗室氛圍（**最重要**） |
| 經費 | 保障幾年？RA 還是 TA？暑假有沒有薪水？教授的經費狀況如何？ |
| 津貼 vs 生活成本 | 扣掉房租之後還剩多少？ |
| 下線／工具資源 | 有沒有定期下線的機會？EDA 工具與機器資源夠不夠？ |
| 畢業時間 | 實驗室平均幾年畢業？ |
| 出路 | 近 5 年畢業生去了哪裡（業界、學界、哪些公司）？ |
| 實習政策 | 學校怎麼處理 CPT？**2026/08 SEVP 收緊 CPT 之後，這一點要特別確認**（見 [07](07-reality-check.md#71-政策變動總表)） |
| 地點 | 產業鄰近度、氣候、生活圈（見 [06](06-geography.md)） |
| 資格考 | 形式、通過率 |

**Visit day 時私下問在學學生**：「如果重來一次，你還會選這個實驗室嗎？」
