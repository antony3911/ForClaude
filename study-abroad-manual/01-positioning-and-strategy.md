# 01. 定位與策略

> 目標：清楚知道讀第二個碩士「買到的是什麼」、風險在哪，以及怎麼用你的研究背景拉開和其他 MS 申請者的差距。

---

## 1.1 AI 加速器的職涯地圖（MS 的入口在哪）

| 職位 | 在做什麼 | MS 能不能進 | 和你目前背景的距離 |
|---|---|---|---|
| **RTL Design（micro-architecture）** | 把架構寫成可合成的 SystemVerilog，負責 timing、面積、功耗 | ✅ **MS 主要入口** | 中：你會寫 RTL/HLS，要補 ASIC 的時序與功耗觀念 |
| **Design Verification (DV)** | UVM testbench、coverage、formal；**職缺最多** | ✅ **MS 主要入口** | 中遠：需要 SV/UVM |
| **Physical Design (PD)** | Floorplan、P&R、CTS、timing closure、signoff | ✅ MS 主要入口 | 遠：需要完整的 APR 經驗 |
| **DFT** | Scan、BIST、ATPG | ✅ | 遠 |
| **ML Compiler / Kernel / HW-SW Co-design** | 把模型映射到硬體（MLIR/TVM/Triton、kernel、runtime） | ✅ | **近：co-design 經驗很加分** |
| **Performance Modeling / Architecture** | 寫效能模型、做 design space exploration、決定 dataflow | ⚠️ 少數優秀的 MS 可以，多數是 PhD | 近 |
| **Research Scientist** | 發論文、做下一代架構 | ❌ 幾乎都是 PhD | — |

**MS 進 AI 加速器的實際路徑**：
```
新鮮人：RTL / DV / PD / compiler（在 AI 晶片團隊）
   ↓ 3–5 年
資深 RTL／micro-architecture，參與架構討論
   ↓
架構師（很多加速器架構師是 MS 學歷，從 RTL 做上去的）
```
**重點：一開始就挑「做 AI 晶片的團隊」**。職稱就算是 RTL 或 DV，每天接觸的都是加速器設計，之後往架構走比較順。

**雇主類型**（名單只是舉例，新創變動很快）：
- **GPU／CPU／SoC 大廠**：NVIDIA、AMD、Intel、Apple、Qualcomm、Arm
- **雲端業者的自研晶片**：Google（TPU）、Amazon（Annapurna Labs）、Meta（MTIA）、Microsoft（Maia）
- **客製 ASIC／網通**：Broadcom、Marvell
- **AI 晶片新創**：Cerebras、Tenstorrent、Etched、MatX、d-Matrix、SambaNova 等（加入前先評估穩定性）
- **EDA**：Synopsys、Cadence、Siemens EDA
- **記憶體**：Micron、Samsung／SK hynix 的美國據點

> 大廠每年都有招募 new college grad 的 ASIC 設計和驗證職位，例如 NVIDIA 在 2026 年就有這類職缺，而且公開的薪資範圍不低。不過，薪資能不能落在較高的 H-1B 級別，要看職位與地區，不保證。

---

## 1.2 第二個碩士到底「買到」什麼？

| 你付出的 | 你換到的 |
|---|---|
| 約 US$9–20 萬（見 [03](03-application-materials.md#38-費用估算)） | 美國學歷，能直接進入美國的校園招募管道（career fair、Handshake、校友網路） |
| 1.5–2 年的時間 | 通常有一次**暑期實習**機會，實習後常能轉成正職 offer |
| 放棄這段時間在台灣工作的薪水 | **最多 3 年的 OPT 工作許可**（EE/CE 屬於 STEM 科系） |
| 身分與政策的不確定性 | **3 次 H-1B 抽籤機會**，而且持美國碩士學位可以多一輪抽籤（advanced degree cap） |

**說白一點**：第二個碩士的學術價值有限（很多課你可能修過類似的），它的核心價值是**「進入美國就業市場的入場券」**。所以選校時，**就業資源、地點、實習政策、總花費**的權重，要比學術排名高。

---

## 1.3 三條路的比較：美國 MS、PhD、台灣美商轉調

| | 美國 MS（主軸） | 美國 PhD（備案） | 台灣美商 → L-1 轉調 |
|---|---|---|---|
| 花費 | 自費 US$9–20 萬 | 通常全額資助 | **不花錢，還有薪水** |
| 時間 | 1.5–2 年 | 5–6 年 | 台灣工作 1 年以上，之後看公司安排 |
| 到美國工作的簽證 | OPT → H-1B 抽籤（Level I 中籤率約 15%） | OPT → H-1B（薪資級別較高、較有利），也可以走 O-1、NIW | **L-1 不用抽籤**，但要公司願意轉調 |
| 你能掌控的程度 | 中：錄取與求職靠自己，抽籤靠運氣 | 中：錄取門檻高 | **低：轉調要看公司和部門** |
| 起點職位 | RTL/DV/PD 新鮮人 | 架構／研究類 | 視台灣職位而定 |
| 役男 | **必須先處理兵役**（見 [07](07-reality-check.md#74-役男兵役)） | 同左，PhD 的年齡上限較寬 | 在台灣工作，不受出境就學限制 |

**建議**：MS 當主軸，另外申請 2–3 所 PhD 當備案（成本只是申請費）。**同時**把「台灣美商」當成平行選項：如果 MS 沒拿到理想的錄取，或者預算不夠，NVIDIA、Google、Apple、AMD、Intel、Qualcomm、Microsoft 等在台灣的硬體團隊，都是很好的起點。

---

## 1.4 誠實盤點：你的 SWOT（MS 申請與求職角度）

### Strengths（優勢）
- **已經有碩士研究經驗**：大部分 MS 申請者只有大學專題
- 做過**完整的 FPGA 加速器**（從演算法、架構到實作），在面試時是很有深度的話題
- **HW/SW co-design** 的思維，正是 AI 晶片團隊需要的
- 研究題目新穎，故事性強（蛋白質結構預測，2024 年諾貝爾化學獎相關領域）

### Weaknesses（缺口）
- **學校背景與 GPA**：中山電機在台灣是好學校，但美國審查委員對台灣學校的熟悉度有限，MS 審查又偏重這兩項。**這要用 ASIC 實作、研究成果、業界經驗來補**（見 [05 的 5.2 節](05-schools-and-labs.md#52-你的選校名單中山電機所成績中上)）
- **「第二個碩士」本身**：有些學校不收，可以申請的學校也會問你「為什麼要再讀一個碩士」（見 1.6）
- **沒有 ASIC flow 經驗**：MS 求職最看重實作能力，這個缺口的影響比申請 PhD 時更大
- **業界面試能力**：RTL 手寫、STA、驗證方法論
- 英文面試與溝通

### Opportunities（機會）
- AI 硬體人才需求仍然很高，大廠持續招募 new grad
- 台灣有 TSRI 提供學界 EDA 工具與下線資源，能在出國前就補上 ASIC 經驗
- 你有研究背景，比一般 MS 學生更有機會拿到 **RA 或 thesis 機會**，有時可以抵學費

### Threats（威脅）
- **H-1B 加權抽籤**：新鮮人的中籤率大幅下降
- **CPT 收緊**：MS 那一次暑期實習的風險變大
- **OPT 仍在被 DHS 檢討**：這是 MS 路線的命脈
- **兵役**：你是役男，出國前要先服完兵役（見 [07](07-reality-check.md#74-役男兵役)）
- 大量國際 MS 學生搶同一批 new grad 職缺

---

## 1.5 研究經驗怎麼用在 MS 路線

MS 申請不像 PhD 那麼看研究，但**研究是你和其他 MS 申請者最大的差異**。三個用途：

### (1) 申請：放進 SOP 和 CV，證明你「做過真的東西」
MS 版 SOP 的重點不是「我想做研究」，而是**「我做過完整的加速器，現在要補上 ASIC 與業界能力，進入 AI 晶片產業」**（見 [03](03-application-materials.md#32-statement-of-purposems-版)）。

### (2) 求職面試：最好的技術話題
面試官很喜歡問「講一個你做過最複雜的設計」。長序列蛋白質結構預測加速器就是很好的題材：
- **瓶頸**：pair representation 是 L × L × 128 的張量。以 L = 4,000 為例，單一 FP32 張量約 **8.2 GB**；triangle 運算的複雜度是 O(L³)
- **你的解法**：dataflow、tiling、量化、記憶體階層的設計
- **取捨**：為什麼用 FPGA？換成 ASIC 會有哪些改變？
- **驗證**：你怎麼確認正確性？GPU baseline 有多強？

### (3) 保留 PhD 的可能
- 研究照樣做完、**論文照樣投**（DAC、ICCAD、FCCM、FPGA 等等，時程見 [02](02-timeline.md#23-研討會投稿時程參考)）
- 同領域已有 **ISCA 2025 的 LightNobel**（KAIST 團隊，針對長序列蛋白質結構預測模型的軟硬體協同加速器），一定要讀，並說得出你的方法和它的差異
- MS 期間如果選 thesis option 或做 RA，有機會拿到美國教授的推薦信，將來要轉 PhD 就容易得多

---

## 1.6 「為什麼要再讀一個碩士？」要有好答案

可以申請的學校（例如 Stanford EE、CMU ECE）都明確要求你**在 SOP 裡說明理由**，面試官也常問。

**❌ 不好的理由**
- 「為了拿美國工作簽證」（雖然是事實，但不能當主要理由）
- 「台灣的碩士不夠好」（貶低自己的學歷，沒有必要）

**✅ 好的理由（依你的情況調整）**
- **能力轉換**：「我的碩士研究偏重 FPGA 原型與 HW/SW co-design，但要設計 AI 加速器晶片，我需要系統性的 ASIC 設計、驗證與實體設計訓練。這是我目前的學程無法提供的」
- **具體課程與資源**：點名學校的進階 VLSI 課程、下線課程、驗證課程，以及和業界的合作專案
- **產業銜接**：清楚的職涯目標，說明這個學程如何幫你銜接到 AI 晶片產業
- **研究延續**：如果有 thesis option，可以提你想延續的研究方向

**這個理由必須是真的**。它也會引導你選課：**不要重修你已經會的東西**，要去補 ASIC、驗證、進階計結這些真正的缺口。

---

## 1.7 從 FPGA 銜接到 ASIC（出國前最值得投資的事）

這對 MS 求職**極度重要**：面試官會直接問你有沒有做過 synthesis、STA 和 P&R。

### 階段 1：ASIC 綜合（1–2 個月）
- 把加速器的**核心運算單元**整理成乾淨的 SystemVerilog（原本是 HLS 的話，最好手寫關鍵模組）
- 用 Design Compiler 或 Genus 做 synthesis
  - 製程：透過 **TSRI** 取得學界製程，或使用 **ASAP7**（學界常用的 7nm 預測型 PDK）
- 用 PrimeTime/Tempus 做 STA → 報告面積、功耗、頻率

### 階段 2：APR（2–3 個月）
- ICC2 或 Innovus：floorplan → placement → CTS → routing → 修 timing
- 或者走開源流程：**OpenROAD / OpenLane**
- 產出：post-layout 的 PPA、layout 截圖（放在 CV 和 GitHub 上）

### 階段 3：驗證（並行進行）
- 替 RTL 寫一套像樣的 testbench：SystemVerilog + assertion，或 **cocotb**；再學 UVM 基礎
- **DV 是職缺最多的領域**，有驗證經驗能讓你的求職面更廣

### 在台灣可以利用的資源
- **課程**：研究所等級的 VLSI 系統設計、數位 IC 設計（例如陽明交大的積體電路設計實驗 ICLAB 這類高強度課程）
- **競賽**：旺宏金矽獎、大學院校積體電路設計競賽、CAD Contest @ ICCAD
- **TSRI**：EDA 工具、製程資源、下線服務、訓練課程

---

## 1.8 策略總結

```
主軸   ：美國 MS 10–12 所（業界認可、錄取機會合理的學校，見 05 的 5.2）
備案   ：台灣美商（平行選項）；PhD 只在遇到非常對口的教授時考慮
兵役   ：出國前服完 4 個月（優先申請分階段軍事訓練）→ 2029 Fall 入學
研究   ：做完並投稿 → SOP 的差異化、面試話題、保留 PhD 的可能
補強   ：ASIC flow（PPA 數字）+ 驗證 + RTL 面試能力（出國前完成）
選校   ：第二碩士資格 > 就業資源 > 地點 > 實習政策 > 花費 > 學術排名
```
