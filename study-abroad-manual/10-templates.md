# 10. 範本

> 範本只是起點，**一定要改成你自己的內容與口吻**。直接套用會讓人一眼看出來。

---

## 1. 詢問系所第二碩士資格的信

**寄給誰**：系所的研究生辦公室（graduate admissions／graduate program coordinator），信箱通常在系所的 admissions 頁面上。
**什麼時候寄**：T−7 到 T−4（送件前半年左右），**保留書面回覆**。

```
Subject: Eligibility question — applicant with a master's degree from Taiwan (MS ECE, Fall 2029)

Dear [Program name] Graduate Admissions Committee,

I am planning to apply to the MS in [Electrical and Computer Engineering] program
for Fall 2029, and I would like to confirm my eligibility before applying.

I will hold (or currently hold) a Master of Science in [Electrical Engineering]
from [University], Taiwan (expected [Month Year]). My master's research focused on
FPGA-based hardware-software co-design for accelerating long-sequence protein
structure prediction. I am now seeking formal training in ASIC design,
verification, and physical implementation, which my current program does not cover.

Could you please let me know:
1. Whether applicants who already hold a master's degree in a closely related field
   from a non-U.S. institution are eligible for the MS program, and
2. If eligible, whether there are any restrictions (e.g., on repeating coursework)
   I should be aware of?

Thank you very much for your time.

Best regards,
[Full name]
[Current affiliation] | [Email]
```

**寄信前自我檢查**
- [ ] 先把官網的 FAQ 和 admissions 頁面看過一遍（問官網已經寫明的事，會顯得不夠用心）
- [ ] 如果學校同時有 MS 和 MEng，可以一起問兩個學程的資格

---

## 2. 給推薦人的資料包（Brag Sheet）

請推薦人寫信時一併提供，讓老師**有具體事例可以寫**。

```markdown
# 推薦信資料包 — [你的名字]

## 1. 申請資訊
- 申請學位：MS in Electrical/Computer Engineering（另有 2–3 所 PhD）
- 職涯目標：在 AI 晶片團隊從事 digital IC design（RTL／verification），往加速器架構發展
- 為什麼要再讀一個碩士：[一句話，和 SOP 一致]
- 送件截止日清單：（附表，最早的截止日排在最前面）

| 學校 | 學程 | 截止日 | 推薦信提交方式 |
|---|---|---|---|
| ... | MS ECE | 2028/12/15 | 系統會寄連結給老師 |

## 2. 我們共事的經驗（請老師挑選適合的）
- 時間：[起訖]
- 專案：[名稱]
- 我的角色與貢獻：
  - [具體事例 1：工程決策，例如「我發現 X 是瓶頸，改用 Y，讓速度提升 Z 倍」]
  - [具體事例 2：解決困難，例如「FPGA 實測和模擬不一致，我追出是 W 造成的」]
  - [具體事例 3：團隊合作、帶學弟妹、報告表現]
- 量化成果：[加速比、能效、PPA、論文狀態]

## 3. 希望老師能著重的面向（可選）
- 工程實作能力（從演算法一路做到 RTL 和 ASIC）
- 解決問題的能力與獨立性
- 團隊合作與溝通

## 4. 附件
- CV
- SOP 草稿
- 論文或專案報告
```

---

## 3. SOP 骨架

### MS 版（主要）

```
[Paragraph 1 — Career goal + the technical problem behind it]
  e.g., I want to build AI accelerator chips. My research showed me that the hard
  part is data movement, not arithmetic.

[Paragraph 2 — What you've built (master's research)]
  Problem → your design decisions → obstacle → how you solved it → numbers.

[Paragraph 3 — Bridging to silicon (ASIC implementation / verification work)]
  Synthesis + APR results; what you learned; what you still lack.

[Paragraph 4 — Why a second master's (must answer directly)]
  The specific skill gap (ASIC design, verification, physical design, advanced
  architecture) and why your current program cannot fill it. Keep it positive.

[Paragraph 5 — Why THIS program (customize per school!)]
  Specific courses (tapeout course, advanced VLSI, verification), 1–2 faculty
  for thesis/RA if relevant, industry connections, location.

[Paragraph 6 — Closing]
  Career goal in 1–2 sentences (e.g., RTL / micro-architecture on an AI accelerator team).
```

### PhD 備案版

```
[P1] The research problem (not you): long-sequence, memory-bound AI workloads
[P2–3] Research story: your key decisions, obstacles, quantified results
[P4] Second project / ASIC bridge
[P5] What you want to research next (one level broader)
[P6] Why THIS lab: 2–3 faculty, specific papers
[P7] Career goal
```

**寫完後自我檢查**
- [ ] 把學校名稱遮起來之後，還看得出是寫給哪一所學校的嗎？（「Why this program」那段必須看得出來）
- [ ] 「為什麼要再讀一個碩士」的理由具體嗎？有沒有貶低自己的學歷？
- [ ] 有沒有空泛的形容詞（passionate、world-renowned、cutting-edge）？刪掉
- [ ] 找 2–3 位讀者給意見，其中至少一位在美國讀過研究所

---

## 4. 選校追蹤表

建議用 Google Sheets 或 Notion 管理，欄位如下：

| 學校 | 學程 | 第二碩士資格 | 書面確認 | 長度 | 實習必修？ | 總花費（估） | 截止日 | 申請費 | TOEFL 門檻 | GRE | 就業報告重點 | 下線／ASIC 課程 | 地點 | 感興趣的教授 | 送件 | 結果 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Example U | MS ECE | 🟡 SOP 要說明 | ✔ 2027/06 回信 | 3 學期 | 是 | US$12 萬 | 12/15 | $90 | 100 | 不需要 | NVIDIA、Apple… | 有 | TX | Prof. A | ✔ | |

---

## 5. 錄取後聯繫教授的信（RA／thesis）

**什麼時候寄**：錄取後到入學前（3–7 月）。**不要期待一定有回應**，有回應算是紅利。

```
Subject: Incoming MS ECE student (Fall 2029) — interest in RA / thesis in your group

Dear Prof. [Last name],

I am an incoming MS student in [Dept] at [University] (Fall 2029). Before joining,
I completed a master's at [University], Taiwan, where I built an FPGA accelerator
for long-sequence protein structure prediction and took its core engine through
ASIC synthesis and place-and-route in [node].

I read your recent work on [specific paper/project] and I believe my experience in
[specific skill: e.g., HLS-to-RTL design, dataflow tiling, cocotb-based verification]
could contribute to [specific project in their group].

Would you be open to a short conversation about possible RA or MS thesis
opportunities in your group? I have attached my CV and a one-page project summary.

Best regards,
[Full name]
[GitHub] | [LinkedIn]
```

---

## 6. 面試自我準備清單

用英文把每題講一遍，錄音後回放，確認你講得清楚、而且不超時。

### 業界面試（主要）

**自我介紹與專案**
- [ ] Tell me about yourself（60–90 秒）
- [ ] 講一個你做過最複雜的設計（3 分鐘，附一張架構圖）
- [ ] 為什麼要來美國再讀一個碩士？
- [ ] 為什麼想做 AI 晶片？為什麼是這家公司？

**RTL 手寫（每題都要能在 20 分鐘內寫完並說明）**
- [ ] 同步 FIFO（含 full／empty 判斷）
- [ ] 非同步 FIFO（gray code 指標）
- [ ] Round-robin arbiter
- [ ] 序列偵測 FSM（Moore 與 Mealy）
- [ ] 除頻器（奇數除頻）

**觀念題**
- [ ] Setup／hold violation 的成因與修法
- [ ] CDC：單一 bit 與多 bit 的處理
- [ ] Clock gating 的實作與風險
- [ ] Latch vs flip-flop；metastability
- [ ] Cache 的基本觀念
- [ ] 用 roofline 分析一個矩陣乘法單元

**Behavioral（用 STAR 結構）**
- [ ] 最難解的 bug
- [ ] 跟隊友或指導教授意見不同的經驗
- [ ] 快速學會一項新技術的經驗
- [ ] 一次失敗，以及你學到了什麼

**你要問面試官的問題（至少準備 3 題）**
- [ ] 新進工程師的一週通常在做什麼？
- [ ] 團隊目前最大的技術挑戰？
- [ ] 架構、RTL、驗證之間的分工方式？

### PhD 備案面試
- [ ] 1 分鐘與 3 分鐘版本的研究介紹
- [ ] 和 LightNobel 等相關研究的差異
- [ ] 為什麼用 FPGA？換成 ASIC 會有哪些改變？
- [ ] 頻寬加倍或 SRAM 減半時，設計要怎麼調整？
- [ ] 方法怎麼泛化到 LLM 或其他 workload？
- [ ] Why PhD? Why this lab?

---

## 7. 美國格式一頁履歷骨架

```
FIRST LAST
City, State | email | phone | linkedin.com/in/xxx | github.com/xxx
(Work authorization: F-1 student, eligible for CPT/OPT)

EDUCATION
[US University] — M.S. Electrical and Computer Engineering        Expected May 2031
  Relevant: Advanced VLSI, ASIC Verification, Computer Architecture
[Taiwan University] — M.S. Electrical Engineering, GPA x.xx/4.3   Jun 2028

SKILLS
  RTL/HLS: SystemVerilog, Verilog, Vitis HLS | Verification: SVA, UVM, cocotb
  EDA: Design Compiler, PrimeTime, Innovus, VCS, Vivado | Languages: Python, C++, Tcl

EXPERIENCE / RESEARCH
[Lab / Company] — Graduate Researcher                              Sep 2026 – Jun 2028
  • Designed …, achieving … (quantified)
  • Implemented … in 16nm: … MHz, … mm², … mW
  • Verified … with …, reaching …% functional coverage

PROJECTS
  • Parameterized systolic array + UVM/cocotb testbench (GitHub link)

PUBLICATIONS (optional, 1–2 lines)
```

**原則**：嚴格 1 頁；不放照片、年齡、性別；每個 bullet 都是「動作 + 技術 + 量化成果」；關鍵字對齊職缺描述。
