# 交接紀錄：米凱拉風格《魔物獵人 荒野》mod

最後更新：2026-10-01（雲端 session，分支 `claude/two-account-handoff-plan`）

> **新的 session 先讀完這份**，再依需要讀第 2 節列的文件。這份是總覽和索引，細節都在各文件裡。
> 做完任何一步，就更新第 9 節「下一步」和第 4 節的進度表，commit 並 push。

---

## 1. 跟使用者合作的規則（很重要）

**溝通**
- 使用者在台灣，**一律用繁體中文回覆**，連過程中的進度回報也是。使用者明確抱怨過「一直說英文看得很累」
- 回覆精簡、講結論；做出圖就**直接傳圖**給使用者看（他看圖給意見）
- 有幾個方向時，**並排做出來讓他挑**（他很常這樣選：斬擊斧劍模式 A/B、長槍光膜四種濃淡、操蟲棍兩種方案）
- 他會在你做事做到一半時插話補充，照最新的意見調整

**權限與界線**
- push 到 GitHub 不用問；**沒被要求就不要開 PR**；工作分支是 `claude/two-account-handoff-plan`
- 需要系統管理員同意（UAC）的步驟不要自己做，擱置並告訴他
- 已婉拒：做自動偵測額度、自動換帳號的工具（違反使用條款）
- 米凱拉是孩童形象角色：**不做裸露或暴露版本**；長袍底下是平滑身體加簡單內褲
- 角色是 FromSoftware 的 IP；模型自己重做，不直接搬法環的模型

---

## 2. 文件地圖

| 文件 | 內容 |
|---|---|
| `mods/miquella/DESIGN.md` | **設計規格書**：配色、角色、全部武器設計、動作效果表、武器裝置表、還能補強的動作、被否決的方向。改設計前一定要讀 |
| `mods/research/mhws_modding_notes.md` | **研究筆記** 16 節：工具、檔案格式、打包、材質參數（11）、匯出管線測試（12）、遊戲檔案路徑、頭髮材質（14）、不覆蓋原版的掛載法（15）、動作效果的遊戲做法＋其他模組怎麼用特效（16） |
| `mods/miquella/OVERNIGHT_REPORT.md` | **給使用者的報告**：要下載的東西、回家要做的事（照順序）、要給 Claude 的檔案 |
| `notes/two-account-handoff-plan.md` | 更早的筆記：雙帳號換手計畫、**全部 mod 工具安裝清單和官方網址**、角色的已決定方向（體型、頭髮、長袍、光環） |
| `mods/miquella/tools/README.md` | 已下載好的工具（RE Mesh Editor、RE Asset Library）和雲端載不了的東西 |
| `mods/miquella/mhws/*/README.md` | 各遊戲端腳本、套件的說明 |

---

## 3. 專案目標

把米凱拉（艾爾登法環 DLC）重新設計成《魔物獵人 荒野》的 mod，**以米凱拉為元素重新設計，不是搬運**：
1. **角色**：替換獵人的「內衣身體」→ 米凱拉的身體＋長袍；替換一款捏臉髮型 → 米凱拉的頭髮（含擺動）；發光的頭冠（光環）。也可以不覆蓋任何原版檔案，用腳本把模型掛到獵人骨架上（研究筆記 15）
2. **14 種武器**：全部做成「神力光劍」風格，**收刀時武器消失**（解決長髮和背上武器穿模）
3. **武器專屬動作效果**：武器零件跟著蓄力、鬼人化、填彈等動作反應，不只是換膚
4. **武器裝置**：龍杭、地雷、追蹤箭這類打到魔物身上或放在地上的東西也要改
5. **技能特效**：重弩的「米凱拉的光」（光柱），純視覺，**不改傷害、範圍、次數**（使用者原則）

---

## 4. 進度一覽

所有預覽都是 Blender 程式產生的**概念原型**，還沒有一個放進遊戲測過。

### 角色
| 項目 | 狀態 | 位置 |
|---|---|---|
| 頭冠（光環） | 基礎造型 v10：髮帶散成細枝 → 捲成一束 → 三叉往後掃，整個發亮金光 | `prototypes/circlet/` |
| 角色概念（人台） | 長袍、編髮、頭冠戴在頭髮上；v4 頭髮改成遊戲用的髮片做法 | `prototypes/character_concept/` |
| 正式身體、長袍、頭髮 | **需要遊戲骨架**（`ch02_000_9000.fbxskel`、內衣 `ch02_002` 系列），還沒做 | — |

### 武器造型（全部定案，除非使用者再改）
| 武器 | 定案的設計（細節見 DESIGN.md 第 5 節） | 位置 |
|---|---|---|
| 雙劍 | v4：葉形光刃、編織柄、護手兩側三叉；**已做成遊戲素材包＋可安裝的測試版** | `prototypes/dual_blades/`、`mhws/` |
| 片手劍 | 光劍＋樹狀紋章能量盾 | `prototypes/sword_shield/` |
| 太刀 | 彎刃＋刃紋、懸浮光環當刀鐔、編織刀柄 | `prototypes/long_sword/` |
| 重弩、輕弩 | 光環隧道、懸浮光環；**槍管上方、靠前的三顆懸浮光點**（使用者很喜歡輕弩） | `prototypes/heavy_bowgun/`、`light_bowgun/` |
| 大劍 | **不對稱單刃、光刃懸浮**不碰柄、S 形刃口、卷草托架 | `prototypes/great_sword/` |
| 大錘 | 細枝燈籠包光球，比純鏤空多一點遮擋，金色花絲卷草 | `prototypes/hammer/` |
| 狩獵笛 | 光的豎琴，手臂末端是卷草 | `prototypes/hunting_horn/` |
| 長槍、銃槍 | 鏤空雙螺旋槍身、花瓣護手、輕量能量盾；銃槍有象牙彈簧 | `prototypes/lance/`、`gunlance/` |
| 斬擊斧 | 斧：三片懸浮鐮刃排成三叉＋卷草＋金藤＋懸浮光點；**劍模式 A**：長光刃、三片斧刃像羽毛疊在劍背 | `prototypes/switch_axe/` |
| 充能斧 | 劍＋盾；**斧模式盾會變形成長鬍斧**（不是圓盾）；懸浮光點（使用者很喜歡） | `prototypes/charge_blade/` |
| 操蟲棍 | 雙螺旋棍身、**原本的三叉護手**（使用者說不改卷草）；獵蟲是金色燕尾光蝶 | `prototypes/insect_glaive/` |
| 弓 | 反曲弓臂、金藤纏繞、卷草弓尖、光箭穿過光環 | `prototypes/bow/` |

### 動作效果（預覽圖都在 `prototypes/action_states/`，程式 `prototypes/scripts/states.py`）
| 武器 | 定案 |
|---|---|
| 大劍 | **三段**蓄力：亮金 → 更亮的金 → 白光；**只有三段**時刃紋上有金色光帶流過（使用者指定） |
| 太刀 | 練氣四段：淡金 → 金 → 亮金 → 白光；高段刃紋光流 |
| 雙劍 | 鬼人化：一片光刃分裂成三刃苦無（淡入＋滑出）；藍鬼人：亮金 |
| 大錘 | 每段蓄力在兩端打擊面外各多一圈環，越來越小往外疊；光球越來越亮 |
| 長槍 | 平時輕裝；蓄力時大光環從護手往槍尖一段段長出成錐形，每段更亮；滿蓄力浮出光膜（**根部濃、往槍尖淡出**，使用者從四種選的）＋槍尖伸長 |
| 銃槍 | 填彈：象牙彈簧往槍根壓縮、核心充能，再彈回 |
| 斬擊斧 | 懸浮光點＝變形量表；強化斧三片光刃亮金；劍模式覺醒亮金 |
| 充能斧 | 光點＝瓶子；紅盾、劍強化、斧強化各自亮金 |
| 弓 | 拉弓時光環暗著，每段亮一圈 |
| 重弩、輕弩 | 三顆懸浮光點＝點火量表／速射量表 |
| 狩獵笛 | 音符點亮光弦；演奏時聲波環擴大 |
| 能量盾 | 防禦時光膜、樹紋變亮；完美防禦閃亮金＋擴散光環 |
| **操蟲棍精華** | 紅白橘＝法環的**猩紅腐敗、冰凍、癲火**（使用者的點子）。平時只有光刃；**點燈後球才出現、繞著刃轉，不要光環**。**走寫實質感，不要能量感、科技感**：腐敗＝粉紅黴球（像腐敗苔藥）＋寫實小腐敗蝶（深紅、黑翅脈、破翅，夾紫藍和白）；癲火＝捲曲火球（像癲火聖印記，中心暗）；冰凍＝霜面冰塊＋不斷逸散的寒氣（像輝石冰塊）。三燈齊光刃亮金 |

### 武器裝置（`prototypes/devices/`，程式 `devices.py`）
| 武器 | 設計 | 狀態 |
|---|---|---|
| 銃槍龍杭砲 | **米凱拉的未鍛金之針**（金針、絞絲針眼裡一滴光）；刺入裂出金紋、連續爆裂、最後大爆 | 預覽，使用者看過 |
| 重弩龍穿點火 | 金荊棘彈頭，打進去只露尾端，從體內爆開 | 預覽，**使用者還沒回意見** |
| 輕弩地雷彈 | 象牙花苞包著光，被打到綻開再爆 | 同上 |
| 弓追蹤箭 | 插箭處浮出小樹紋光環，其他光箭追過來 | 同上 |
| 狩獵笛響玉 | 地上光環＋浮空金膜泡泡，攻擊時共鳴 | 同上 |

### 遊戲端（`mods/miquella/mhws/`，全部**還沒在遊戲裡測**）
| 東西 | 內容 |
|---|---|
| `release/MiquellaLight_v0.1.zip` | **可安裝的測試版**：雙劍光劍 patch pak（已讀回驗證）＋換裝腳本，Fluffy 拖進去就能裝，不覆蓋原版 |
| `MiquellaLight_Weapons` | 換裝腳本：選哪把武器換成光劍，收刀隱藏；模擬測試通過 |
| `MiquellaLight_Scout` | 偵察腳本（只讀）：列武器／防具／子物件的模型、材質、**材質參數名稱**、骨頭；**「Watch weapon state」記錄做動作時武器處理器裡變動的欄位**；存成 `scout.json`、`watch.json` |
| `MiquellaLight_HideSheathed` | 舊的收刀隱藏腳本，已被換裝腳本取代，留作備案 |
| `MiquellaLight_DualBlades_kit` | 雙劍遊戲素材（`.mesh`、`.mdf2`、`.tex`、貼圖原檔） |
| `tests/` | Lua 離線測試（模擬 REFramework API）：`lua5.4 scout_test.lua ...`、`weapons_test.lua` |

---

## 5. 設計原則（累積的使用者意見，做任何新東西都要遵守）

- **發光是亮金色，不要白光**；只有使用者指定的地方是白（大劍三段、太刀最高段）。操蟲棍三色是唯一離開金色的例外
- 「亮金」調法：顏色更飽和、強度大幅提高，讓光暈變大變金（只調淡會跟一般一樣，再加就變白）
- **輕盈、鏤空**：米凱拉身形纖細，厚重設計不合格（大劍、長槍、銃槍都因此重做過）
- **奢華卷草**：分支不能三根一樣；用由粗到細、捲成漩渦、帶側枝的卷草；象牙底上要凸顯時用**金色花絲**
- **不要新月**（月亮是菈妮的象徵）
- **懸浮光點**（點亮的水滴套小光環）是使用者很喜歡的元素，可以兼當量表
- 動作效果要有**力量感**，蓄力時變化要明顯（長槍第一版就是太弱被否決）
- 寫實優先的場合（操蟲棍精華），**不要用模型硬做火舌之類的特效**，那很醜；火、煙、冷霧在遊戲裡要用**特效**
- 被否決過的方向（不要再提）：大劍對稱寬刃、外框光膜加小葉子（像玩具）；斬擊斧新月、外框光膜、整片光刃（像船槳）；斬擊斧劍模式 B；操蟲棍方案 A（三刃）、操蟲棍護手改卷草；初版的光膜翅膀腐敗蝶（太科技感）；模型做的火舌；凝成一團的冷霧

---

## 6. 技術：怎麼產生預覽圖

**環境**（雲端這樣裝；本機一樣做得到）
- Python 3.11 ＋ `pip install bpy==4.2.0`（無介面的 Blender），另外一個 venv 裝 `bpy==4.5.3` 給 RE Mesh Editor 匯出用
- 匯出需要把 RE Mesh Editor 裝成 Blender 外掛（雲端是放在 `~/.config/blender/4.5/scripts/addons/re_mesh_editor`）
- 標籤中文字型：`states.py` 會自動找（Linux 文泉驛、Windows 微軟正黑體）；找不到就設環境變數 `MIQUELLA_FONT`
- 算圖：Cycles CPU、Filmic「Medium High Contrast」（AgX 會把金光洗成白）、合成器 Glare（Fog Glow）

**腳本**（都在 `mods/miquella/prototypes/scripts/`，用上面那個 Python 執行）
| 指令 | 產生 |
|---|---|
| `python arsenal.py <武器> <輸出資料夾>` | 九種武器：great_sword、hammer、hunting_horn、lance、gunlance、switch_axe、switch_axe_sword_a／b、charge_blade、charge_blade_axe、insect_glaive、bow |
| `python blades.py／long_sword.py／sword_shield.py／bowgun.py／light_bowgun.py／circlet.py／character_concept.py <輸出>` | 雙劍、太刀、片手劍、重弩、輕弩、頭冠、角色概念 |
| `python states.py <組> <輸出>` | 動作效果：great_sword_charge、dual_blades_demon、hammer_charge、lance_charge、lance_full_variants、gunlance_reload、long_sword_spirit、insect_glaive_extracts、switch_axe_states、charge_blade_states、bow_charge、bowgun_gauges、hunting_horn_notes、shield_guard |
| `python devices.py <組> <輸出>` | 裝置：wyrmstake、wyvernpiercer、wyvernblast、tracer、echo_bubble |
| `python build_game_kit.py <kit 資料夾> <工作資料夾>` | 雙劍遊戲素材包（模型、貼圖、材質） |
| `python make_patch_pak.py <含 natives 的資料夾> <out.pak> <RE Asset Library 所在資料夾>` | 打包 patch pak 並讀回驗證 |
| `python export_wilds_test.py <.blend> <根物件> <輸出>` | 測試把原型匯出成 Wilds `.mesh`（bpy 4.5） |

**共用模組**：`common.py`（場景、材質、算圖）、`motifs.py`（光環、編織管、細枝束、卷草、懸浮光點、光刃…）、`status_fx.py`（腐敗黴球、寫實腐敗蝶、冰塊）、`particle_fx.py`（用旋渦氣流描出的火絲、爆炸光絲、體積冷霧）

**已知限制**：pip 版 bpy 的 Mantaflow（火焰模擬）會壞（`LevelsetGrid` 錯誤），所以火和煙是用氣流描線＋體積材質模擬；粒子小球在這個尺寸看起來是一顆顆的，不像火

---

## 7. 研究結論重點（細節在研究筆記）

- **材質可以在遊戲中即時改**：`renderMesh:setMaterialFloat`／`setMaterialFloat4`／`setMaterialsEnable`（MDF-XL 就這樣做）。Weapon Emissive 材質有 `Emissive_Color`、`Emissive_Intensity`、`Dissolve`（淡入淡出）、`Use_MoveEmit`／`MoveEmit`（移動光帶）、`AnimEmit_*`（呼吸燈）等
- 動作效果的做法：會出現的零件放獨立材質槽＋`Dissolve` 淡入；會動的零件綁武器自己的骨頭；光流用 `MoveEmit`
- **還不知道**：遊戲用哪個欄位代表蓄力段數、鬼人化、填彈 → 偵察腳本的 Watch 模式就是為了找這個
- **不覆蓋原版的掛載法**：腳本生成物件、`setMesh`／`set_Material`、`set_SameJointsConstraint` 掛到獵人骨架（研究筆記 15）
- **特效**：`.efx` 沒有公開編輯器，只能改顏色。可行的路是 **Armor VFX Manager（Nexus 4908）** 那種做法：執行時生成遊戲現成的特效、掛到任一骨頭、改顏色、依動作觸發；VFX Unleashed（Nexus 4842）可減弱原版蓄力強光、依蓄力段數換特效
- 武器檔案：雙劍 `it02`（`_0` 左手、`_1` 右手）、太刀 `it03`、片手劍 `it01`（`_1` 是盾）、重弩 `it12`、輕弩 `it13`；其他武器的編號照 MDF-XL 資料庫的 WPType 推測，要用偵察腳本確認
- 資料片《荒野：Ascendance》預定 2027，會給每種武器加 Boost Bracer 新動作，出了再補
- 雲端環境連不上 Nexus 和 Fluffy 官網；GitHub 可以

---

## 8. 待決定的事

- 四個新裝置（重弩、輕弩、弓、狩獵笛）使用者還沒回意見
- 覆蓋原版檔案，還是用腳本掛上去（建議腳本掛載）
- 頭髮微光的做法（建議：編髮發光、散髮不發光）
- 操蟲棍三顆球繞刃轉的速度、半徑；要不要做綠色精華（荒野有，三燈不需要）
- 特效要直接依賴 Armor VFX Manager，還是學它的寫法放進自己的腳本

---

## 9. 下一步（照順序；第一項就是接手後要做的）

**使用者在自己電腦上做（需要遊戲）**
1. 安裝 REFramework（GitHub `praydog/REFramework-nightly` 最新版的 `MHWILDS.zip`，打開 loose file loader）和 Fluffy Mod Manager
2. 跑偵察腳本：拿各武器掃一次存 `scout.json`；大劍、雙劍、大錘、長槍、銃槍做蓄力／鬼人化／填彈時用 Watch 存 `watch.json`
3. 裝 `release/MiquellaLight_v0.1.zip` 看第一把光劍，回報方向、大小、位置
4. 裝 Armor VFX Manager，翻遊戲特效挑出最像癲火、寒氣、腐敗蝶、爆炸、光柱的；把它的 Lua 腳本給 Claude 研究

**Claude 接著做（拿到上面的檔案之後）**
5. 用 `watch.json` 找出狀態欄位 → 寫「武器狀態視覺」REFramework 腳本（改發光參數、開關材質槽、Dissolve），先做大劍蓄力和雙劍鬼人化
6. 把每把武器整理成遊戲用模型：會變化的零件分材質槽、需要動的綁骨頭；用 RE Asset Library 解出原版武器模型對齊骨頭和大小
7. 學 Armor VFX Manager 生成特效的寫法，做操蟲棍三顆球的特效、裝置的爆炸、重弩「米凱拉的光」光柱
8. 角色正式版：身體＋長袍（貼身上半身、擺動下擺）、頭髮（擺動鏈）、頭冠綁頭骨
9. 之後：Ascendance 的新動作

**不需要遊戲、隨時可做**：調整任何預覽、做新的設計提案、整理文件

---

## 10. 怎麼把工作搬到本機

雲端 session 碰不到使用者的電腦。要讓 Claude 直接操作遊戲資料夾、安裝工具、讀遊戲檔案，要在**使用者電腦上**開 Claude Code：
- Claude 桌面版（Claude Code），開這個 repo 的資料夾；或
- 在終端機：`git clone https://github.com/antony3911/ForClaude`，`cd ForClaude`，`git checkout claude/two-account-handoff-plan`，再執行 `claude`（或 `claude remote-control`，就能從手機的 Claude Code app 操作）
- 開好後跟 Claude 說：「讀 HANDOFF.md 接著做」。repo 根目錄的 `CLAUDE.md` 會被自動讀到

本機的注意事項：安裝程式可能跳 UAC，要人在電腦前按；Nexus 下載要登入，由使用者自己載

---

## 11. 其他背景

- 更早討論過：Max 5x 和兩個 Pro 的比較、雙帳號手動換手（用進度檔接手；不做自動換帳號工具）、Remote Control 設定 → 見 `notes/two-account-handoff-plan.md`
- 法環的 mod 工具也在那份清單裡（me3、Soulstruct for Blender 等），目前專案主力是魔物獵人荒野
