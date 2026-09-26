# 05. 學校與實驗室標的

> **PhD 是跟「人」，不是跟「學校」。** 這一章先給你一份起始名單，再教你怎麼自己找、自己評估。

**重要聲明**
- 名單依公開資訊整理。標 ✔ 的教授，已在 **2026/09 透過網路查證**目前任職學校與研究方向；未標記者請自行確認
- 教授會跳槽、休假、去業界或開公司，也可能某年不收學生。**申請前一定要看教授網站的最新消息**
- 名單不可能完整，一定有很好的教授沒列到，請用 5.2 的方法補充

---

## 5.1 起始名單（依研究類型分類）

你的目標是「digital IC + AI 加速器」，從 FPGA co-design 起步。建議從下面 A、B、C 三類混合挑選；D、E 類視興趣補充。

### A 類：AI 加速器架構與 HW/SW Co-design（最貼近你的目標）

| 學校 | 教授 | 關鍵字 | 備註 |
|---|---|---|---|
| MIT | Vivienne Sze | 高能效 DNN 硬體、Eyeriss | 著有 *Efficient Processing of DNNs* |
| MIT | Joel Emer | Timeloop/Accelergy、加速器建模 | 同時在 NVIDIA |
| MIT | Song Han ✔ | 演算法與硬體 co-design、高效 LLM | 同時是 NVIDIA 研究總監 |
| MIT | Daniel Sanchez | 計算機結構、稀疏運算加速器 | |
| Stanford | Priyanka Raina ✔ | Domain-specific 加速器、agile hardware、CGRA | Stanford Accelerate 實驗室 |
| Stanford | Thierry Tambe ✔ | Algorithm-to-silicon co-design，**以記憶體效率為核心** | 新進教授（和你的長序列記憶體題目很貼近） |
| Stanford | Kunle Olukotun | 可重組 dataflow 架構 | SambaNova 共同創辦人 |
| UC Berkeley | Sophia Shao ✔ | 加速器、Gemmini、Chipyard、agile VLSI | |
| UC Berkeley | Christopher Fletcher ✔ | 計算機結構、安全、AI 輔助架構設計 | |
| UC Berkeley | Kurt Keutzer | 高效 ML 演算法 | 偏演算法端 |
| CMU | James Hoe | 計算機結構、FPGA | |
| CMU | Nathan Beckmann | 記憶體系統 | |
| CMU | Tianqi Chen | ML 編譯器（TVM、MLC-LLM） | 偏軟體端的 co-design |
| Georgia Tech | Tushar Krishna ✔ | Dataflow、interconnect、MAESTRO、ASTRA-sim | |
| Georgia Tech | Yingyan (Celine) Lin ✔ | 跨層演算法與硬體 co-design、agentic AI for HW | 同時是 NVIDIA 訪問教授 |
| Georgia Tech | Divya Mahajan ✔ | 大規模 ML 系統與加速器 | 新進教授 |
| Georgia Tech | Hyesoon Kim | GPU 架構 | |
| UIUC | Josep Torrellas | 計算機結構 | |
| UIUC | Nam Sung Kim | 記憶體、near-data processing | |
| UIUC | Charith Mendis | ML 編譯器 | |
| Cornell | Zhiru Zhang ✔ | Allo（加速器設計語言）、HLS、異質運算 | **FPGA 銜接到 ASIC 的完美橋樑** |
| Cornell (Tech) | Mohamed Abdelfattah ✔ | 高效 LLM 的 HW/SW co-design、FPGA | |
| Cornell (Tech) | Jae-sun Seo ✔ | 生成式 AI 的 ASIC 加速器、CIM | 下線經驗豐富 |
| UCLA | Tony Nowatzki ✔ | 架構特化、HW/SW co-design | |
| UCSD | Hadi Esmaeilzadeh | 加速器、co-design | |
| Princeton | Margaret Martonosi | 計算機結構 | |
| Harvard | David Brooks | 架構與電路 co-design、加速器 SoC | |
| Harvard | Vijay Janapa Reddi | ML 系統、MLPerf、TinyML | |
| Purdue | Anand Raghunathan | ML 加速器、approximate computing | |
| Purdue | Tim Rogers | GPU 架構（Accel-Sim） | |
| UT Austin | Lizy John | 效能評估、加速器 | |
| UT Austin | Mattan Erez | 記憶體系統、架構 | |
| Duke | Yiran Chen / Hai (Helen) Li | ML 加速器、neuromorphic、EDA | |
| USC | Murali Annavaram | ML 系統、架構 | |

### B 類：數位 IC 與下線導向（強化「digital IC designer」的身分）

| 學校 | 教授 | 關鍵字 |
|---|---|---|
| Michigan | Zhengya Zhang ✔ | 加速器晶片、chiplet、DSP（2026 IEEE Fellow） |
| Michigan | David Blaauw / Dennis Sylvester | 超低功耗數位與混合訊號電路，下線量非常大 |
| Michigan | Hun-Seok Kim | DSP／ML 硬體 |
| Michigan | Ronald Dreslinski | 架構與晶片 |
| UC Berkeley | Borivoje Nikolić | 數位電路、BWRC、Chipyard 下線 |
| Stanford | Subhasish Mitra | Robust systems、3D 整合 |
| UW | Michael Taylor ✔ | Bespoke Silicon Group：BaseJump、BlackParrot、HammerBlade、ASIC 下線 |
| UW | Visvesh Sathe | 數位電路、時脈與電源 |
| Cornell | Christopher Batten | 架構與 VLSI、PyMTL、課程內就有 ASIC flow |
| Columbia | Mingoo Seok | 數位電路、CIM |
| Columbia | Luca Carloni | ESP（含加速器的 SoC 平台）、HLS |
| Harvard | Gu-Yeon Wei | 電路與架構、加速器 SoC |
| Princeton | Naveen Verma | In-memory computing（EnCharge AI 共同創辦人） |
| Princeton | David Wentzlaff | OpenPiton、manycore |
| Georgia Tech | Arijit Raychowdhury | 電路、ML 硬體 |
| Georgia Tech | Shimeng Yu | CIM、新興記憶體 |
| Purdue | Kaushik Roy | Neuromorphic、CIM |
| UIUC | Naresh Shanbhag | In-memory computing |

### C 類：FPGA／HLS／可重組計算（和你現有技能無縫銜接）

| 學校 | 教授 | 關鍵字 |
|---|---|---|
| UCLA | Jason Cong ✔ | VAST 實驗室、HLS 先驅、FPGA 上的 LLM（FlexLLM）、ASIC HLS |
| Cornell | Zhiru Zhang ✔ | Allo、HLS |
| UIUC | Deming Chen ✔ | ScaleHLS、FPGA AI 加速、AMD 卓越中心主任 |
| Georgia Tech | Callie Hao ✔ | Sharc Lab：FPGA、HLS、GNN、ML 輔助 EDA |
| USC | Viktor Prasanna | FPGA、圖運算與 ML 加速 |
| UW | Scott Hauck | FPGA |
| CMU | James Hoe | FPGA、架構 |
| Minnesota | Kia Bazargan | FPGA |
| Northeastern | Yanzhi Wang | 高效 DNN、FPGA |

### D 類：生物資訊加速（和你的應用領域最契合）

| 學校 | 教授 | 關鍵字 |
|---|---|---|
| UCSD | Yatish Turakhia ✔ | 基因體分析的 GPU/FPGA/ASIC 加速；DP-HLS（HPCA 2026）；RECOMB-Arch workshop 主席 |
| UCSD | Tajana Rosing | PIM、HDC、生物資訊加速 |
| Michigan | Reetuparna Das | 架構、in-memory、基因體加速 |

> 補充：蛋白質結構預測加速這個題目本身還很新，專門做它的實驗室不多。**不需要只找做生物的實驗室**，A 類的加速器實驗室通常都很歡迎「帶著新 workload 來的學生」。D 類教授對你的領域特別有共鳴，是很好的補充選項。

### E 類：EDA／Physical Design（備選方向，業界需求穩定）

| 學校 | 教授 | 關鍵字 |
|---|---|---|
| UCSD | Andrew Kahng | Physical design、OpenROAD |
| UT Austin | David Z. Pan ✔ | EDA、ML for EDA、physical design |
| Georgia Tech | Sung Kyu Lim | 3D IC、physical design |
| Minnesota | Sachin Sapatnekar | EDA、時序分析 |
| UCLA | Puneet Gupta | Design-technology co-optimization |
| USC | Massoud Pedram / Peter Beerel | 低功耗、非同步電路、EDA |
| NC State | W. Rhett Davis | ASIC 設計流程 |

### 其他值得掃過一遍的學校

UW–Madison、Minnesota、NC State、Penn、Northwestern、Rice、UCSB、UC Davis、UC Irvine、Texas A&M、UVA、Yale（Abhishek Bhattacharjee）、NYU（Siddharth Garg、Brandon Reagen）、Northeastern、Stony Brook、Arizona State、Notre Dame（Yiyu Shi）、Pittsburgh。

---

## 5.2 自己找教授的方法

### Step 1：CSRankings
1. 打開 csrankings.org
2. 區域選 USA
3. 領域勾選：**Computer architecture**、**Design automation**，可再加 **Embedded & real-time systems**
4. 點開每所學校，看是哪些教授撐起分數，以及他們近 3–5 年的發表量

### Step 2：從論文反查
- 翻最近 3 年 **ISCA、MICRO、HPCA、ASPLOS、DAC、ICCAD、FPGA、FCCM、ISSCC** 的論文列表
- 搜尋關鍵字：`attention accelerator`、`long context`、`LLM inference`、`memory-bound`、`quantization`、`transformer`、`genomics`、`bioinformatics`、`protein`、`HLS`、`dataflow`
- 記下**最後一位作者**（通常是 PI）
- 也看看引用 LightNobel 的後續論文（Google Scholar →「Cited by」），這些作者就是你的同領域研究者

### Step 3：確認教授近況
- 教授個人網站的 **News** 區塊（有沒有寫 "I'm recruiting PhD students for Fall 20XX"？）
- X（Twitter）、Bluesky、LinkedIn：很多教授會在每年 9–11 月發文徵學生
- 實驗室成員頁：學生人數、今年畢業幾位（剛好有人畢業 = 可能有空缺）
- Google Scholar：近 2 年的發表量
- **新進助理教授**（剛上任 1–3 年）：通常**更積極收學生、指導也更密集**；風險是 tenure 前壓力較大，也可能跳槽

### Step 4：填進追蹤表並評分（見 5.3，範本在 [10](10-templates.md#4-選校追蹤表)）

---

## 5.3 實驗室評估表

| 面向 | 權重（建議） | 怎麼評估 |
|---|---|---|
| 研究契合度 | 30% | 讀 3 篇他們的論文，能不能想到你可以做的延伸？ |
| 你的錄取機會 | 15% | 學校競爭度、教授是否在收人、你的背景是否對口 |
| 下線／ASIC 機會 | 15% | 是否定期下線，或至少會做完整的 ASIC flow |
| 產業連結與出路 | 15% | 畢業生去向、實習機會、和業界合作的專案 |
| 指導風格與實驗室文化 | 15% | 在學學生怎麼說？學生多久畢業？流動率高不高？ |
| 地點與生活 | 10% | 見 [06](06-geography.md) |

---

## 5.4 聯繫在學學生

- 從實驗室成員頁找**台灣學生**，或同為國際學生的成員；禮貌地用 email 或 LinkedIn 詢問
- 可以問的問題：
  - 教授一週 meeting 幾次？回信速度如何？
  - 經費穩定嗎？有沒有學生沒有 RA、只能一直當 TA？
  - 暑假能不能去實習？
  - 平均畢業年限？
  - 實驗室氣氛如何？
- **注意**：學生很難在書面上說教授壞話。**如果回答避重就輕，本身就是一種訊號**

---

## 5.5 學校競爭度（僅供配比參考）

以計算機結構／IC 設計的研究實力，粗略分組：

| 組別 | 學校（不分先後） |
|---|---|
| 極高競爭 | MIT、Stanford、UC Berkeley、CMU、UIUC、Georgia Tech、Michigan、Cornell、Princeton、UW、UCLA、UCSD、UT Austin、Harvard、Columbia、Purdue |
| 高競爭 | USC、Duke、UW–Madison、Minnesota、NC State、Penn、Northwestern、Rice、UCSB、UC Davis、UC Irvine、Texas A&M、UVA、Yale、NYU、Northeastern |
| 其他研究型大學 | 很多學校有 1–2 位非常好的教授，**依教授而定** |

> 學校組別只是參考，**同一所學校裡不同教授的難度差異可能比不同學校之間還大**。明星教授每年收到上百封申請，新進教授可能只收到十幾封。
