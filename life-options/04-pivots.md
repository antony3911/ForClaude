# 04. 用數位 IC 背景轉換跑道

> **核心觀點**：你的背景不只能做 IC 設計。「懂硬體、懂 AI、會做研究」這個組合，在很多看起來不相關的領域都很稀缺。
> 下面依「離你現在的工作有多遠」排列。資料狀態：2026/09。

---

## 1. 地圖：你的背景可以通往哪裡

```
                                離 IC 設計的距離
近 ◄──────────────────────────────────────────────────────────► 遠

 AI 晶片架構   EDA／AI for EDA   HFT 的 FPGA 工程師   半導體產業分析   科技政策研究
 ML 編譯器     驗證／PD          產品經理／FAE        創投（deep tech） 科技寫作／媒體
 其他硬體領域                    專利工程師           創業             教育
```

---

## 2. 一個一個看

### ⚡ 高頻交易（HFT）的 FPGA 工程師：**你的 FPGA 經驗在這裡最值錢**

> 2026-09-30 依佇列 U4 深入補充，**以美國（Chicago、New York）為主**。

**在做什麼**
- 把交易系統的關鍵路徑直接做在 FPGA 上，也就是「**tick-to-trade**」：從網路線收到交易所的行情封包 → 解析 Ethernet／IP／UDP 和交易所的協定（例如 FAST）→ 更新委託簿 → 觸發策略 → 從另一條網路線送出下單封包
- 追求的是**奈秒級**的延遲：學術論文裡的 10G 系統，從收到行情到送出下單約 433 奈秒；軟體通常要數微秒
- 工具：Verilog／SystemVerilog（偶爾用 HLS），AMD（Xilinx）或 Intel（Altera）的 FPGA；有些公司（例如 Hudson River Trading）的硬體團隊也做 ASIC

**誰在招（美國）**
- **Chicago**：Jump Trading、Optiver、IMC、DRW、Citadel Securities 等
- **New York**：Hudson River Trading（HRT）、Jane Street、Tower Research 等
- 其他據點：London、Sydney（新加坡為邊界選項）

**薪資（第三方資料，差異很大，僅供參考）**

| 公司 | 數字 | 來源 |
|---|---|---|
| Jump Trading | 新鮮人 FPGA 工程師總薪酬約 **US$28–45 萬**；5 年以上 US$50–100 萬 | Quantt（2026） |
| Jump Trading | FPGA 工程師平均年薪約 US$25 萬 | Indeed |
| Hudson River Trading | FPGA 工程師平均年薪約 US$17.7 萬（9 筆回報，範圍 US$8.9–27.5 萬） | Indeed |
| Jane Street | 研究類職位（包括 FPGA 工程師）底薪約 US$30 萬 | 第三方整理 |

> 對照：NVIDIA 美國的 ASIC 驗證新鮮人底薪約 US$10–16.7 萬（見 [01](01-work-first.md)）。

**簽證：HFT 對國際生特別友善**
- 自營交易公司高度依賴國際人才，**普遍積極擔保 H-1B 和綠卡**，很多有自己的移民團隊（例如 Citadel Securities、Jane Street 在這方面的口碑很好）
- **2026 年起 H-1B 改成依薪資加權抽籤**：薪資等級 IV 的人在籤池裡有 4 個名額、等級 I 只有 1 個。FY2027 的模型估計：**等級 I 約 15%、等級 IV 約 61%**。HFT 的薪資很可能落在最高等級（我的推論；等級要看職業與地區的標準薪資），**抽中的機率遠高於一般新鮮人**

**面試長什麼樣子**

| 階段 | 內容（依網路上的面試經驗整理） |
|---|---|
| 線上測驗 | Optiver：約 60 分鐘的選擇題加 RTL 除錯，或約 2 小時、30 題左右的底層 FPGA 題目 |
| 技術電話面試 | HRT：數位團隊的人連續快問 RTL、計算機結構、驗證，例如快取階層、hazard、CDC、SRAM 存取 |
| 回家作業 | HRT：約 1 小時的計算機結構與 FPGA 問題之後，給一週做一個設計題 |
| 現場面試 | 較長的 HDL 實作；**基礎觀念被追問到你答不出來為止**（metastability、CDC、timing closure）；網路相關的題目；系統設計題：「從網路線進來到網路線出去，你會怎麼設計 tick-to-trade 的路徑？」 |

**常考的題目**
- **同步 FIFO**（參數化、full／empty 旗標要正確）、**固定優先權的仲裁器**、**解析「長度前綴」訊息的狀態機**
- **CDC**：單一位元怎麼跨時脈（兩級同步器）、整個 word 怎麼跨（非同步 FIFO 或 request-acknowledge 握手）、不做會壞在哪裡
- **靜態時序分析**：setup、hold、slack、skew，以及「為什麼 hold 檢查裡沒有時脈週期」
- **reset 同步器**、valid／ready 握手、pipelining 與延遲和吞吐量的取捨
- 面試官在意的不是語法完美，而是「**你知不知道資料什麼時候有效、用了幾個 cycle、邏輯有沒有暫存到能在真的晶片上收斂時序**」

**給你的準備清單**
1. **基礎觀念**：STA、CDC、metastability、reset，要能講到很深
2. **RTL 手寫練習**：FIFO、仲裁器、封包解析 FSM，每個都要搭配 testbench（HRT 的實習是用 Python 建驗證環境）
3. **網路**：Ethernet／IP／UDP 的封包格式；讀開源的 **verilog-ethernet** 和 **Corundum**（開源的 FPGA 網卡，支援 10G／25G／100G 和 PCIe DMA，發表在 FCCM 2020）
4. **一個作品**：在實驗室的 FPGA 板上做一個 **UDP 封包解析器或簡單的行情處理器**，量測延遲是幾個 cycle。這會是你履歷上最有說服力的一項
5. **你的研究也能用**：蛋白質預測加速器的 pipelining、記憶體頻寬、延遲取捨，都是很好的面試故事
6. C++ 與 Linux 的基本功（部分關卡會考）

**實際的進入方式**
- **從台灣直接應徵美國的職位很難**（要公司願意直接辦簽證）；**最實際的路是先讀美國 MS，在碩士期間拿到暑期實習，再轉正職**
  - HRT 的 2027 年暑期硬體實習：在 New York，要求 2028 年畢業的電機、計算機工程學生，用 SystemVerilog 設計、用 Python 驗證
  - Optiver Chicago 的 2027 年暑期 FPGA 實習：學士、碩士、博士都可以
  - Jump Trading Chicago 的 FPGA 實習：要有 FPGA 或硬體設計經驗，**最好有過實習經驗**
- 也就是說：**如果你讀 1.5–2 年的 MS，第一個暑假就是關鍵**，入學後的第一個秋天就要開始投

**挑戰與風險**
- 錄取門檻很高、工作壓力大、要一點金融直覺
- 技能偏向網路與低延遲 FPGA，**和 AI 加速器的 ASIC 架構職涯有一段距離**；想回晶片業的話，網路晶片、SmartNIC、資料中心硬體是比較順的方向

### 🧠 美國的 AI 晶片新創與大型雲端公司的自研晶片（和你的主線最接近）

> 這其實不算「轉換跑道」，而是**你原本目標在美國的具體雇主地圖**，放在這裡和 HFT 對照。

| 類型 | 例子（2026） | 對你的意義 |
|---|---|---|
| **AI 晶片新創** | Etched（2026/09 在加州有 17 個職缺）、MatX、Tenstorrent、d-Matrix、SambaNova；Cerebras 在 2026/05 於 Nasdaq 上市；Groq 在 2025/12 由 NVIDIA 以授權加收編大部分團隊的方式整合 | 小團隊、一個人碰得到架構到 RTL；**FPGA 原型經驗有用** |
| **大型雲端公司的自研晶片** | Google TPU、AWS（Annapurna Labs）Trainium、Meta MTIA、Microsoft Maia；OpenAI 與 Broadcom 合作的晶片；Anthropic 也在組自研晶片團隊 | 穩定、規模大；和台灣的供應鏈（TSMC、設計服務）關係密切 |

**薪資參考（美國，2026）**
- 半導體工程師平均年薪約 **US$18.9 萬**（25 百分位 US$14.3 萬、75 百分位 US$25.4 萬；Glassdoor，2026/05）
- RTL 驗證工程師平均約 US$14.9 萬（ZipRecruiter，2026/06）
- 懂 **CDC／RDC**（跨時脈、跨 reset 域）的驗證專家，在約聘市場有 20–35% 的溢價

### 📊 半導體產業分析師
- **在做什麼**：分析晶片公司、技術趨勢、供應鏈，寫研究報告給投資人或企業
- **雇主**：
  - 券商研究部（本土券商、外資券商的台灣研究團隊）
  - 投信、投顧、避險基金（buy-side）
  - 產業研究機構：工研院產科國際所、資策會 MIC、TrendForce（集邦）、DIGITIMES Research 等
- **為什麼適合你**：台灣是全球半導體的中心，**懂技術的分析師很稀有**。你能看懂 LightNobel 這種論文，也能看懂 NVIDIA 的架構
- **加分項**：CFA 證照、寫作能力（你的寫作興趣派得上用場）
- **國外的例子**：SemiAnalysis 就是由懂技術的分析師創辦的半導體研究機構，在業界很有影響力

### 🏛️ 科技政策研究
- **在做什麼**：研究半導體、AI 的地緣政治、出口管制、產業政策，寫給政府或決策者看
- **雇主**：
  - 美國：Georgetown 的 **CSET**（Center for Security and Emerging Technology）、CSIS 等智庫；CSET 的 Research Analyst 要能讀技術文獻、分析資料、寫給非專業讀者看
  - 台灣：工研院產科國際所、中華經濟研究院、國家政策相關的研究單位、國科會
- **為什麼適合你**：**台灣背景 + 晶片技術 + 寫作能力**，在國際科技政策圈非常少見
- **可能的學位**：公共政策、國際關係、科技政策的碩士（例如科技政策相關的一年制學位）

### ✍️ 專利工程師
- **在做什麼**：幫企業撰寫專利申請文件、分析專利侵權與布局
- **薪資（台灣）**：碩士新人月薪約 4.2–4.9 萬，7 年以上年資年薪約 83–120 萬；事務所的撰稿費用偏低，是薪資上限的主因
- **加分**：考取專利師證照；進入大公司的智財部門（台積電、聯發科都有）
- **為什麼列出來**：這份工作**每天都在寫作**，而且要非常懂技術，是「工程 × 寫作」的一種結合。但薪資明顯低於 IC 設計

### 🧭 產品經理（PM）、FAE、技術行銷
- **產品經理**：定義晶片產品的規格、和客戶與工程團隊溝通。需要技術深度加上溝通能力
- **FAE（應用工程師）**：協助客戶使用你們的晶片，常常需要出差，**很適合想要「跑來跑去」的人**
- **技術行銷**：寫白皮書、做技術簡報、參加展會
- 在台灣的 IC 設計公司、外商分公司都有這些職位；很多人是先做幾年 RD 再轉過去

### 💰 創投（Deep tech VC）
- 半導體、AI 硬體的投資需要懂技術的人
- 通常要先有幾年業界經驗，或者 MBA 背景
- 台灣與國外都有專注在硬體或半導體的創投

### 🚀 創業
- 台灣的 AI 晶片新創：**創鑫智慧**（Neuchips，約 70 人，專攻 AI 推論晶片）、**耐能**（Kneron）
- 政府的「**晶片驅動臺灣產業創新方案**」規劃在 113–122 年投入 3,000 億元，包括培育 IC 設計人才
- 比較務實的路徑：**先加入新創**，學習怎麼從零做一顆晶片，再決定要不要自己創業

### 🔬 其他「冷門但有趣」的硬體領域
| 領域 | 你的技能怎麼用 |
|---|---|
| **量子電腦的控制電子** | 用 FPGA／ASIC 控制量子位元，需要超低延遲與低溫電路 |
| **太空與衛星電子** | 抗輻射的數位設計；台灣也有太空產業在發展 |
| **醫療與植入式晶片** | 超低功耗數位設計；和你的生醫研究背景也有連結 |
| **車用晶片** | 功能安全（ISO 26262）、自駕晶片 |
| **生物資訊硬體加速** | 基因體、蛋白質的硬體加速，**你的研究題目就在這裡** |

### 📚 教育
- 大學教職（見 [03](03-phd-and-research.md)）
- 業界內訓講師、TSRI 的教育訓練
- **線上課程或 YouTube**：台灣有很多人想學 IC 設計，中文的高品質內容其實不多
- 國外的例子：Asianometry 是住在台北的創作者，用影片講半導體產業史，在全球有大量觀眾

---

## 3. 「組合」比「轉換」更有價值

與其想「我要從 IC 設計轉去做 X」，不如想「**IC 設計 + X**」：

| 組合 | 可能的職業 |
|---|---|
| IC 設計 + 寫作 | 科技媒體記者、產業分析師、技術寫作、專利、科普作家 |
| IC 設計 + 金融 | 半導體分析師、HFT 工程師、創投 |
| IC 設計 + 政策 | 科技政策研究員、政府的產業顧問、國際組織 |
| IC 設計 + 美國、日本或其他英語系國家的學位或工作經驗 | 外商的跨國專案、跨國 FAE、國際產業分析；會日語的話，台日半導體合作的橋樑（例如 TSMC 熊本相關的職位） |
| IC 設計 + 生醫 | 生物資訊加速、醫療晶片 |
| IC 設計 + 教學 | 大學教職、線上課程、企業內訓 |

**好消息是**：這些組合裡的「X」，很多都可以在工作之餘慢慢累積，不一定要重讀一個學位。

---

## 來源
- HFT 面試與工作內容：[techinterview.org：Inside the FPGA interview at a low-latency trading firm](https://www.techinterview.org/post/3233477296/fpga-interview-low-latency-trading-firm/)、[Glassdoor：HRT FPGA Engineer Interview](https://www.glassdoor.com/Interview/Hudson-River-Trading-FPGA-Engineer-Interview-Questions-EI_IE470937.0,20_KO21,34.htm)、[Glassdoor：Optiver FPGA Engineer Interview](https://www.glassdoor.com/Interview/Optiver-FPGA-Engineer-Interview-Questions-EI_IE243355.0,7_KO8,21.htm)、[HDL Factory：FPGA Hardware Interview Guide（2026/07）](https://www.hdlfactory.com/post/2026/07/23/fpga-hardware-interview-guide/)、[IEEE：FPGA-Based HFT System for 10GbE（433 ns）](https://ieeexplore.ieee.org/document/9768065/)、[Corundum（GitHub）](https://github.com/corundum/corundum)、[Corundum 論文（FCCM 2020）](https://cseweb.ucsd.edu/~snoeren/papers/corundum-fccm20.pdf)、[Alex Forencich（verilog-ethernet）](https://github.com/alexforencich)
- HFT 實習：[HRT：Hardware Engineer Internship – Summer 2027](https://www.hudsonrivertrading.com/hrt-job/hardware-engineer-internship-summer-2027/)、[Optiver：FPGA Engineer Intern（Summer 2027 – Chicago）](https://www.optiver.com/join-us/jobs/technology/chicago/fpga-engineer-intern-summer-2027-chicago/)、[LinkedIn：Jump Trading Campus FPGA Engineer（Intern）](https://www.linkedin.com/jobs/view/campus-fpga-engineer-intern-at-jump-trading-group-3688508124)
- HFT 薪資與簽證：[Indeed：HRT FPGA Engineer Salaries](https://www.indeed.com/cmp/Hudson-River-Trading/salaries/FPGA-Engineer)、[Indeed：Jump Trading FPGA Engineer Salaries](https://www.indeed.com/cmp/Jump-Trading/salaries/FPGA-Engineer)、[techinterview.org：Visa Sponsorship at Wall Street Firms in 2026](https://www.techinterview.org/post/3233474736/visa-sponsorship-wall-street-firms/)、[f1jobs：Quant Researcher H-1B Sponsorship at Prop Trading Firms](https://www.f1jobs.io/resources/blog/quant-researcher-prop-trading-firm-visa-sponsorship)、[Citadel Securities：FPGA Engineer](https://www.citadelsecurities.com/careers/details/fpga-engineer/)、[Hodgson Russ：FY27 H-1B Registration](https://www.hodgsonruss.com/immigration-insights/fy27-h-1b-registration-what-employers-need-to-know)、[Visa Pros：H-1B Weighted Lottery odds](https://visa-pros.com/h-1b-weighted-lottery/)、[Ogletree：USCIS Completes FY2027 H-1B Lottery](https://ogletree.com/insights-resources/blog-posts/uscis-completes-fiscal-year-2027-h-1b-lottery/)
- AI 晶片雇主：[Hashrate Index：Independent AI Chip Companies 2026](https://hashrateindex.com/blog/independent-ai-chip-companies-ai-asic-market-part-3/)、[Tom's Hardware：Custom AI ASIC state of play（2026/05）](https://www.tomshardware.com/tech-industry/semiconductors/custom-ai-asics-examined-from-broadcom-to-mtia)、[TechRepublic：Anthropic custom AI chip team](https://www.techrepublic.com/article/news-anthropic-custom-ai-chip-team-confirmed/)、[ZipRecruiter：Etched Jobs](https://www.ziprecruiter.com/co/etched/Jobs/--in-California)、[Glassdoor：RTL Verification Engineer Salary](https://www.glassdoor.com/Salaries/rtl-verification-engineer-salary-SRCH_KO0,25.htm)、[ZipRecruiter：RTL Verification Engineer Salary](https://www.ziprecruiter.com/Salaries/Rtl-Verification-Engineer-Salary)、[HeroHunt：Hardware Talent Recruiting 2026](https://www.herohunt.ai/blog/hardware-talent-recruiting-in-the-ai-age-2026/)
- HFT（第一版）：[Optiver：FPGA Engineer](https://optiver.com/working-at-optiver/career-opportunities/7887188002/)、[Built In：Graduate FPGA Engineer](https://builtin.com/job/graduate-fpga-engineer/7142593)、[Quantt：Jump Trading Salary 2026](https://www.quantt.co.uk/resources/jump-trading-salary)、[Glassdoor：IMC FPGA Engineer](https://www.glassdoor.com/Salary/IMC-Trading-FPGA-Engineer-Salaries-E278100_D_KO12,25.htm)、[KORE1：How to Hire FPGA Engineers in 2026](https://www.kore1.com/hire-fpga-engineers-2026/)
- 政策：[CSET：Research Analysts](https://cset.georgetown.edu/job/research-analysts/)
- 專利：[104 薪資情報：專利工程師](https://guide.104.com.tw/salary/job/2002002009?analyze=workexp&salary=annual)、[北美智權報：全球專利人才荒](https://naipnews.naipo.com/37363/)、[Cake：專利師與專利工程師](https://www.cake.me/resources/industry-job-overview/patent-attorney-salary-jobs-interview?locale=en)
- 產業：[聯合新聞網：台灣半導體業今年最缺哪些人才](https://udn.com/news/story/6839/9305554)、[INSIDE：專訪創鑫智慧](https://www.inside.com.tw/feature/ai-new-chip-war/34813-neuchips-interview)、[行政院：晶創臺灣方案](https://www.ey.gov.tw/Page/5A8A0CB5B41DA11E/6dd41826-ed84-4b92-9f51-e6ebeb8621f8)
