# 10. 範本

> 範本只是起點，**一定要改成你自己的內容與口吻**。直接套用會讓人一眼看出來。

---

## 1. 聯繫教授的信（Cold Email）

**原則**：150–250 字、具體、附上證據、不要群發。

```
Subject: Prospective PhD student (Fall 2028) — long-sequence protein structure
         prediction accelerator, FPGA/ASIC co-design

Dear Prof. [Last name],

I am a master's student at [University] in Taiwan, advised by Prof. [Name],
working on hardware-software co-design for long-sequence protein structure
prediction. I am applying to the [Dept] PhD program for Fall 2028 and am
very interested in joining your group.

Your recent work on [specific paper, e.g., "XXX" (MICRO'26)] resonated with
me because [one concrete connection — e.g., it tackles memory-bound tiling for
attention, which is exactly the bottleneck I hit with triangle attention when
L > 2,000].

In my current project, I [one-sentence summary of what YOU did + key number,
e.g., designed a fused dataflow for triangle multiplicative updates on an HBM
FPGA, reducing off-chip traffic by 5x vs. a chunked GPU baseline]. The work is
[under review at ICCAD'27 / available at arXiv link]. I am now extending it to
an ASIC implementation in [node] to quantify area and energy.

I would love to explore [one direction that fits THEIR lab — e.g., how such
dataflow insights generalize to long-context LLM inference accelerators].
Could I ask whether you expect to recruit PhD students for Fall 2028?

I have attached my CV and a one-page research summary. Thank you for your time.

Best regards,
[Full name]
[Personal website] | [GitHub] | [Google Scholar]
```

**寄信前自我檢查**
- [ ] 提到的論文你真的讀過，而且能講出它的核心貢獻
- [ ] 和你研究的連結是具體的，不是「我也做加速器」這種程度
- [ ] 附件是 PDF，檔名清楚（`Lastname_CV.pdf`、`Lastname_ResearchSummary.pdf`）
- [ ] 教授的名字與頭銜都正確（`Prof.`，不要寫 `Mr.`／`Ms.`）

---

## 2. 給推薦人的資料包（Brag Sheet）

請推薦人寫信時一併提供，讓老師**有具體事例可以寫**。

```markdown
# 推薦信資料包 — [你的名字]

## 1. 申請資訊
- 申請學位：PhD in Electrical/Computer Engineering
- 研究方向：AI accelerator / digital IC design，特別是長序列、記憶體受限的 workload
- 送件截止日清單：（附表，最早的截止日排在最前面）

| 學校 | 系所 | 截止日 | 推薦信提交方式 |
|---|---|---|---|
| ... | ... | 2027/12/01 | 系統會寄連結給老師 |

## 2. 我們共事的經驗（請老師挑選適合的）
- 時間：2026/09 – 2027/11
- 專案：[名稱]
- 我的角色與貢獻：
  - [具體事例 1：例如「我發現 GPU baseline 的 chunking 策略會造成 X，提出改用 Y，後來成為論文的主要貢獻」]
  - [具體事例 2：例如「在 deadline 前兩週，模擬結果和 FPGA 實測不一致，我追出是 Z 造成的」]
  - [具體事例 3：獨立性、主動性、帶學弟妹、報告表現]
- 量化成果：[加速比、能效、論文狀態]

## 3. 我希望老師能著重的面向（可選）
- 研究獨立性（例如：我自己提出了 X 的想法）
- 技術深度（例如：從演算法一路做到 RTL 和 ASIC）
- 溝通能力（例如：在 XX 研討會上報告）

## 4. 附件
- CV
- SOP 草稿
- 論文／preprint
- 成績單（如果老師需要）
```

---

## 3. SOP 骨架（PhD）

```
[Paragraph 1 — The problem, not you]
  Open with the research problem that drives you. One concrete, technical hook.
  (e.g., long proteins break structure prediction models because pairwise
  representations explode in memory — a data-movement problem, not a FLOPs problem.)

[Paragraph 2–3 — Research story #1 (your main project)]
  Context → the key decision YOU made and why → obstacle → how you solved it →
  quantified result → what it taught you about hardware design.

[Paragraph 4 — Research story #2 (ASIC implementation / another project)]
  Show breadth: bridging FPGA prototypes to silicon-level PPA analysis,
  verification rigor, or a different layer of the stack.

[Paragraph 5 — What you want to do next]
  Broaden one level: memory-bound, long-sequence AI workloads; co-design across
  algorithm / dataflow / memory hierarchy / silicon.

[Paragraph 6 — Why THIS program (customize per school!)]
  2–3 faculty, specific papers/projects, and how your background fits.
  Mention resources (tapeout programs, centers, industry collaborations).

[Paragraph 7 — Closing]
  Career goal in 1–2 sentences (e.g., architect next-generation AI accelerators
  in industry or academia).
```

**寫完後自我檢查**
- [ ] 把學校名稱遮起來之後，這篇 SOP 還看得出是寫給哪一所學校的嗎？（第 6 段必須看得出來）
- [ ] 每一段都有「我」做的具體決定嗎？
- [ ] 有沒有空泛的形容詞（passionate、world-renowned、cutting-edge）？刪掉
- [ ] 找 2–3 位讀者給意見，其中至少一位在美國讀博

---

## 4. 選校追蹤表

建議用 Google Sheets 或 Notion 管理，欄位如下：

| 學校 | 系所 | 學位 | 截止日 | 申請費 | TOEFL 門檻 | GRE | 教授 1 | 教授 2 | 教授 3 | Fit (1–5) | 錄取機會 (1–5) | 下線機會 | 地點 | CPT 政策 | 聯繫教授日期 | 回覆 | 送件 | 結果 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Example U | ECE | PhD | 12/01 | $90 | 100 / Band 5.0 | 不需要 | Prof. A | Prof. B | — | 5 | 2 | 有 | CA | 待確認 | 09/20 | 有回覆 | ✔ | |

**每位教授另外一頁筆記**：
```
- 近 2 年代表論文（3 篇）：
- 每篇的一句話摘要：
- 我能做的延伸：
- 是否在招生：（網站、社群媒體上的資訊）
- 實驗室人數、近期畢業生去向：
- 聯繫紀錄：
```

---

## 5. 一頁研究摘要（Research Summary）

附在聯繫教授的信中，或在面試前寄給對方。

```
[Title]  Memory-Efficient Acceleration of Long-Sequence Protein Structure Prediction
[Name, affiliation, advisor, contact]

Motivation (3–4 lines)
  - Why long sequences matter scientifically
  - Why current hardware fails (one key number, e.g., 8 GB per pair tensor at L=4k in FP32)

Key Insight (2–3 lines)

Approach (figure + 4–5 lines)
  - Algorithm / dataflow / hardware co-design; one architecture diagram

Results (3–4 bullets with numbers)
  - Speedup, energy efficiency, memory reduction vs. strong GPU baseline
  - Accuracy (lDDT / TM-score) preserved
  - ASIC PPA (if available)

Next Steps (2–3 lines) — link to the lab you're writing to

Publications / Code
```

---

## 6. 面試自我準備清單

用英文把每題講一遍，錄音後回放，確認你講得清楚、而且不超時。

### 研究
- [ ] 1 分鐘版本的研究介紹
- [ ] 3 分鐘版本的研究介紹（含一張圖）
- [ ] 最難的部分是什麼？如果重做，你會改什麼？
- [ ] 為什麼用 FPGA？換成 ASIC 會有哪些改變？
- [ ] 和 LightNobel（以及其他相關研究）有什麼不同？
- [ ] 頻寬加倍或 SRAM 減半時，設計要怎麼調整？
- [ ] 你怎麼驗證正確性？怎麼量測能耗？GPU baseline 有多強？
- [ ] 方法怎麼泛化到 LLM 或其他 workload？

### 技術基礎
- [ ] 用 roofline 分析你的 kernel
- [ ] 比較三種 systolic array dataflow
- [ ] 量化對準確度、面積、功耗的影響
- [ ] Setup／hold violation 怎麼修
- [ ] 非同步 FIFO 怎麼設計
- [ ] Cache 的基本觀念（associativity、replacement、write policy）

### 動機與規劃
- [ ] Why PhD? Why now?
- [ ] Why this lab? 你讀過我們哪幾篇論文？
- [ ] 5 年後／10 年後想做什麼？

### 你要問教授的問題（至少準備 5 題）
- [ ] 實驗室未來 2–3 年的研究方向？
- [ ] 新生通常怎麼決定題目？
- [ ] 有沒有下線機會？多久一次？
- [ ] 經費狀況與 RA 保障年限？
- [ ] 學生的暑期實習狀況？學校目前怎麼處理 CPT？
- [ ] 指導風格（meeting 頻率、期待）？
- [ ] 近幾年畢業生的去向？
