# 交接紀錄：米凱拉風格《魔物獵人 荒野》mod

最後更新：2026-10-03（**雲端 session（武器附加物）：使用者選好了**——輕弩速射彈鼓 A 象牙燈籠、重弩彈匣 C 聖匣、追蹤箭 B 光花綻放、龍穿點火 D 卷草鑽；重弩的盾要重新設計（用槍管上的光環往後拉到盾的位置、擴大成盾，雲端 session 在做提案）；**另外使用者發現輕弩、重弩的槍托人物都沒去抓**，要本機 session 查，見第 0 節）。之前（**本機 session（人物）：頭髮設計定案**——遊戲髮型 512 為底＋細編髮、肩前粗編髮、大編髮加長，見第 9 節「人物」第 4 項）。**武器（第一帳號，2026-10-03 07:45）**：**銃槍打掉重練成聖百合**（蓄力時花前長出光之百合、槍身長出光葉和小光百合，跟著蓄力連續長，已裝進遊戲、等實測）；第七輪修正（螺旋跟著蓄力連續伸長、弓一朵一朵開、太刀氣刃蓄力、操蟲棍精華和三燈蓄力 D、輕弩花苞）全部做完、已裝進遊戲，等實測；HANDOFF 的武器部分整理過，現況在第 9 節「武器」，舊留言和每一輪實測紀錄的原文在 `mods/miquella/WEAPONS_LOG.md`。之前（人物）：第二帳號 2026-10-03 早上：脖子照原版接法重做、已裝進遊戲；本機 session（第一帳號）：脖子接縫重做（身體從外面相切貼上臉的脖子）；身體修正（骨架對齊造成的啤酒肚、腹股溝摺線）；頭冠進遊戲（角色第一步）。分支 `claude/two-account-handoff-plan`。分工：**第一帳號＝武器**（換裝腳本、特效腳本、武器／裝置 kit），**第二帳號＝人物**；兩邊在同一個資料夾工作，commit 只加自己的檔案

> **新的 session 先讀完這份**，再依需要讀第 2 節列的文件。這份是總覽和索引，細節都在各文件裡。
> 做完任何一步，就更新第 9 節「下一步」和第 4 節的進度表，commit 並 push。

---

## 0. 兩個帳號之間的留言

**雲端 session（武器附加物）→ 本機 session（2026-10-03，最新，請處理）**：
- **使用者選好的附加物**（預覽 `prototypes/attachments/*.png`，程式 `attachments.py`，規格 DESIGN.md「武器附加物・提案」）：**輕弩速射彈鼓 A 象牙燈籠**、**重弩彈匣 C 聖匣**、**弓追蹤箭 B 光花綻放**、**重弩龍穿點火 D 卷草鑽** → 要做遊戲版。雲端碰不到遊戲，**每樣是哪個遊戲檔、什麼時候出現都還沒確認**，先在遊戲裡找（做法見第 9 節「武器」→「附加物遊戲版」）
- **重弩的盾**：四個版本都沒選，使用者要「利用光環讓它變形：往後拉到盾的位置、擴展變成盾」→ 雲端 session 在做提案（之後一樣放 `prototypes/attachments/`），挑好之前先不用做
- **槍托問題（使用者 2026-10-03，要本機查）**：「輕弩、重弩的槍托，人物都不會去抓到那個位置」，使用者不確定是①人物抓的位置有問題（我們的模型沒對齊手）、②原版其他設計本來就不把槍托放在那、還是③原版根本沒有槍托。查法和要決定的事在第 9 節「武器」→「槍托問題」；**結論和對照圖給使用者看、讓他決定，不要自己改**
- 雲端也能畫預覽：`pip install bpy==4.5.3`（venv），中文字型用文泉驛

**第一帳號（武器）→ 大家（2026-10-03 06:40，最新）**：使用者 2026-10-02 23:39 實測後的武器要求（弓一朵一朵開、螺旋做成動畫、太刀「氣刃大迴旋斬」的蓄力、操蟲棍光球沒出現、輕弩花苞埋在地下）和之後追加的（螺旋要像動畫連續伸長、操蟲棍三燈蓄力選了 D 三色光旋、操蟲棍攻擊軌跡先紅再金）**全部做完、已裝進遊戲，等實測**。要測什麼、還沒做的、遊戲欄位速查都在第 9 節「武器」。換裝腳本、特效腳本、`arsenal.py`、`build_weapon_kit.py`、`build_device_kit.py`、武器／裝置 kit 在第一帳號手上；人物的檔案第一帳號不碰。HANDOFF 的武器部分這時整理過：10-01～10-03 的武器留言、每一輪實測紀錄的原文搬到 `mods/miquella/WEAPONS_LOG.md`。**下面人物 session 說的雙劍 NRRO 貼圖收到了**：重轉會改變所有武器象牙部分的外觀，先等使用者決定（第 8 節），還沒動
**→ 07:15 使用者：NRRO 先不弄（第二帳號膚質卡關很久，不急）；銃槍打掉重練**（「原本的銃槍很不好做特效，而且看起來挺簡陋的、很沒設計感」，**金針保留**：「金針不賴」）→ 四個方向的設計圖 `prototypes/gunlance/gunlance_redesign.png`（A 金針聖匣／B 聖百合／C 聖樹／D 聖翼，上排平時、中排近看、下排龍擊砲），**等使用者挑**；每個方向的特效做法在 DESIGN.md「銃槍重新設計・提案」
**→ 07:20 使用者選 B 聖百合**（「非常好看」「已經很完美了」）但**蓄力力量感不足，要加；原本的元素一個都不能砍，只加** → 四個加法 `prototypes/gunlance/gunlance_lily_charge.png`（A 金藤螺旋／B 光瓣旋輪／C 光之百合／D 聚光旋渦，各畫一段、二段、滿）
**→ 07:25 使用者選 C 光之百合**（「非常好」），但只有槍尖變化有點空，**槍身也要變**（一樣只加）→ `prototypes/gunlance/gunlance_lily_body.png`：C1 光葉／C2 光花（花苞開成小光百合）／C3 光藤／C4 三者全加
**→ 07:30 使用者定案：聖百合＋光之百合＋光葉＋光花（不要光藤），蓄力要「動畫，不是分段模型」→ 07:45 遊戲版做完、已裝進遊戲（遊戲關著直接裝，`work\install` 也放了一份），等實測**：光的零件做成滿蓄力大小、126 根骨頭從小撐到大，象牙花瓣用骨頭往後翻，跟著蓄力砲擊的計時器／龍擊砲的蓄能時間連續走（龍擊砲第一次發射就記下實際蓄能長度）；五個花苞尖的光滴＝彈數。動畫預覽 `MiquellaTools\work\previews\gunlance\bloom\lily.gif`、`lily_head.gif` 已傳給使用者。測試 234 項全過。盾還是舊的樹紋能量盾

**人物 session → 第一帳號（武器，2026-10-03 清晨，重要）**：**雙劍 kit 的 NRRO 貼圖是壞的**（當初在雲端 Linux 轉檔）：`MiquellaIvory_NRRO.tex` 解碼出來是 (8, 14, 56, 128)，原始 PNG 是 (102, 128, 255, 128)＝RGB 被乘了 alpha 0.5 再轉 sRGB → 遊戲裡粗糙度 0.03（像鏡面金屬）、法線 Y 歪到 -0.9、AO 0.22（整個壓暗）。**所有用雙劍貼圖的象牙／握把部分都受影響**（武器有金光蓋著所以沒發現；身體用了同一張才看出來：陰影處全黑、調色只變明暗）。本機重新轉檔就正確（`build_game_kit.py` 的 `convert_textures`；texconv 讀 PNG 要先 `CoInitializeEx`，bpy 環境裡已初始化）。身體已改用自己的貼圖、沒動武器的；**要不要重轉雙劍貼圖由你／使用者決定**（修好後象牙部分會變亮、變霧面，外觀跟使用者確認過的不同）。其他雲端轉的 kit 貼圖（裝置 `Devices/tex` 等）可能也一樣，用 scratchpad 的解碼法檢查：Tex 讀 mip0 → 包成 DX10 DDS → Pillow 解 BC7

**第二帳號（人物）→ 下一個 session（2026-10-03 早上，最新）**：人物的現況、文件、下一步**整理在第 9 節「人物」**（之前的身體、臀腿、胯下、脖子留言都併進去了）。這次：脖子照原版接法重做（使用者：「這個版本不錯」），已裝進遊戲；匯出時自訂法線被 RE Mesh Editor 弄丟的坑也修了（`prepare_for_export`）

---

## 1. 跟使用者合作的規則（很重要）

**溝通**
- 使用者在台灣，**一律用繁體中文回覆**，連過程中的進度回報也是。使用者明確抱怨過「一直說英文看得很累」
- 回覆精簡、講結論；做出圖就**直接傳圖**給使用者看（他看圖給意見）
- 有幾個方向時，**並排做出來讓他挑**（他很常這樣選：斬擊斧劍模式 A/B、長槍光膜四種濃淡、操蟲棍兩種方案）
- 他會在你做事做到一半時插話補充，照最新的意見調整
- **在意 token 用量**（2026-10-01 提出）：長輸出寫進檔案只印摘要（測試只印失敗和總數、不要整段 hex／範本）；只讀需要的檔案範圍；一個階段 commit 完、HANDOFF 更新後，建議他開新 session 接手

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
| `mods/miquella/WEAPONS_LOG.md` | **武器的舊紀錄**：10-01～10-03 兩個帳號的武器留言、每一輪實測的處理紀錄原文（2026-10-03 從這份搬出去的） |
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

預覽是 Blender 程式產生的概念原型，使用者挑了才做遊戲版；**14 種武器都有遊戲版、已裝進遊戲**，遊戲版的狀態見下面幾張表和第 9 節。

### 角色
| 項目 | 狀態 | 位置 |
|---|---|---|
| 頭冠（光環） | v10：髮帶散成細枝 → 捲成一束 → 三叉往後掃，整個發金光；遊戲版**已裝、還沒實測**（腳本掛到 `Head`） | `prototypes/circlet/`、`mhws/MiquellaLight_Character*/` |
| 角色概念（人台） | 長袍、編髮、頭冠戴在頭髮上；v4 頭髮改成遊戲用的髮片做法 | `prototypes/character_concept/` |
| 身體 | 三款 A／B／C（MakeHuman CC0）掛在獵人骨架上，**已裝、等使用者挑和實測**；脖子照原版接法（2026-10-03 使用者 OK）。細節見第 9 節「人物」 | `prototypes/scripts/miquella_body.py`、`mhws/MiquellaLight_Character_kit/` |
| 頭髮 | **設計定案（2026-10-03）**：遊戲髮型 512 為底＋背後 10 條細編髮、肩前左右各一條粗編髮、大編髮加長；預覽 OK，**還沒做進遊戲**。細節見第 9 節「人物」第 4 項 | `prototypes/scripts/hair512_braids.py` |
| 長袍 | 還沒做（已決定的方向：`notes/two-account-handoff-plan.md`「米凱拉風格角色」、DESIGN.md「服裝」） | — |

### 武器造型（全部定案，除非使用者再改）
| 武器 | 定案的設計（細節見 DESIGN.md 第 5 節） | 位置 |
|---|---|---|
| 雙劍 | v4：葉形光刃、編織柄、護手兩側三叉；**已做成遊戲素材包＋可安裝的測試版** | `prototypes/dual_blades/`、`mhws/` |
| 片手劍 | 光劍＋樹狀紋章能量盾 | `prototypes/sword_shield/` |
| 太刀 | 彎刃＋刃紋、懸浮光環當刀鐔、編織刀柄 | `prototypes/long_sword/` |
| 重弩、輕弩 | 光環隧道、懸浮光環；**槍管上方、靠前的三顆懸浮光點**（使用者很喜歡輕弩）；**輕弩遊戲裡看過，位置正確**；光束上五個環磁浮（使用者說不錯）、光點速射量表（等實測） | `prototypes/heavy_bowgun/`、`light_bowgun/`、`mhws/MiquellaLight_LightBowgun_kit/` |
| 大劍 | **不對稱單刃、光刃懸浮**不碰柄、S 形刃口、卷草托架；**遊戲裡看過，位置正確**；刀背三個環浮動（使用者說不錯）、大環磁浮、蓄力只在刀身（等實測） | `prototypes/great_sword/`、`mhws/MiquellaLight_GreatSword_kit/` |
| 大錘 | 細枝燈籠包光球，比純鏤空多一點遮擋，金色花絲卷草 | `prototypes/hammer/` |
| 狩獵笛 | 光的豎琴，手臂末端是卷草 | `prototypes/hunting_horn/` |
| 長槍、銃槍 | 鏤空雙螺旋槍身、花瓣護手、輕量能量盾；銃槍有象牙彈簧。**銃槍 2026-10-03 使用者否決**（簡陋、不好做特效），**重新設計定案：聖百合**＋蓄力時光之百合、光葉、光花（DESIGN.md「銃槍重新設計・提案」），**遊戲版已裝、等實測**（`mhws/MiquellaLight_Gunlance_kit/`）；龍杭砲金針保留 | `prototypes/lance/`、`gunlance/` |
| 斬擊斧 | 斧：三片懸浮鐮刃排成三叉＋卷草＋金藤＋懸浮光點；**劍模式 A**：長光刃、三片斧刃像羽毛疊在劍背 | `prototypes/switch_axe/` |
| 充能斧 | 劍＋盾；**斧模式盾會變形成長鬍斧**（不是圓盾）；懸浮光點（使用者很喜歡） | `prototypes/charge_blade/` |
| 操蟲棍 | 雙螺旋棍身、**原本的三叉護手**（使用者說不改卷草）；獵蟲是金色燕尾光蝶 | `prototypes/insect_glaive/` |
| 弓 | 反曲弓臂、金藤纏繞、卷草弓尖、光箭穿過 6 圈光環；**箭筒 A（鏤空細枝籠）／B（無筒浮空箭束）、光箭**（2026-10-02） | `prototypes/bow/`、`mhws/MiquellaLight_Bow_kit/`、`MiquellaLight_Arrows_kit/` |

### 動作效果（預覽圖都在 `prototypes/action_states/`，程式 `prototypes/scripts/states.py`）
| 武器 | 定案 |
|---|---|
| 大劍 | **三段**蓄力：亮金 → 更亮的金 → 白光；**只有三段**時刃紋上有金色光帶流過（使用者指定）；**光絲纏繞跟著蓄力時間從護手連續長到刀尖**（2026-10-03），三段時刃口飛火花 |
| 太刀 | 練氣四段：淡金 → 金 → 亮金 → 白光；高段刃紋光流。**光絲纏繞是「氣刃大迴旋斬」前的氣刃蓄力**（不是練氣段數，2026-10-03 使用者）：跟著蓄力時間長、大迴旋斬揮完才淡出 |
| 雙劍 | 鬼人化：一片光刃分裂成三刃苦無（淡入＋滑出）；藍鬼人：亮金 |
| 大錘 | 兩端各一組**由大到小的錐形**光環，每段多 2～3 圈（共 7 圈）；亮金 → 更亮的金 → 白光；**身上不發光**（2026-10-02 使用者） |
| 長槍 | 平時輕裝；**光旋**（2026-10-02 使用者選）：光絲從護手往槍尖**跟著蓄力時間連續長**成錐形光鑽、細光絲從一段加入、越長轉越快（2026-10-03），滿蓄力根部旋轉弧＋槍尖光刃伸長；**身上不發光**。（舊設計：光環一段段長出、光膜） |
| 銃槍 | **聖百合**（2026-10-03 定案，取代第一版的彈簧＋金絲）：蓄力砲擊、龍擊砲時象牙花瓣往後翻、花蕊伸出，花前長出用光線畫的大百合（1.2 → 2.6 倍），槍身的葉子外長出光葉、花苞開成小光百合，花喉的光越來越大，龍擊砲最後再出三圈光環，**全部跟著蓄力連續長**；發射後光在原地淡出、花瓣回位；砲擊、填彈時花瓣輕輕一彈；五個花苞尖的光滴＝彈數 |
| 斬擊斧 | 懸浮光點＝變形量表；強化斧三片光刃亮金；劍模式覺醒亮金；**變形動畫**：光刃從柄頂長出、斧刃翻到劍背變羽翼（`switch_axe_morph.gif`，遊戲版已裝，等實測） |
| 充能斧 | 光點＝瓶子；紅盾、劍強化、斧強化各自亮金；**變形動畫**：盾淡出、劍上浮出盾形橢圓光環再變成長鬍斧輪廓、劍縮成斧柄、光點飛到斧背（`charge_blade_morph.gif`，遊戲版已裝，等實測） |
| 弓 | 拉弓時 6 圈光環往弓身壓緊（彈簧），每段亮兩圈，亮金 → 白金；放箭彈回。弓臂金藤**一朵一朵開光花**（每段的時間開兩朵，花心 → 一半花瓣 → 另一半；三段時剩下的和弓尖大花接連開，2026-10-03） |
| 重弩、輕弩 | 三顆懸浮光點＝點火量表／速射量表 |
| 狩獵笛 | 音符點亮光弦；演奏時聲波環擴大 |
| 能量盾 | 防禦時光膜、樹紋變亮；完美防禦閃亮金＋擴散光環 |
| 操蟲棍三燈蓄力 | **D 三色光旋**（2026-10-03 使用者選）：三朵精華花化成紅白橘三股光絲，蓄力時從上刃光環螺旋編上刀刃（一段 45 %、二段收成刀尖外一點金光），上升螺旋斬揮完才淡出 |
| **操蟲棍精華** | 紅白橘＝法環的**猩紅腐敗、冰凍、癲火**（使用者的點子）。平時只有光刃；**點燈後球才出現、繞著刃轉，不要光環**。**走寫實質感，不要能量感、科技感**：腐敗＝粉紅黴球（像腐敗苔藥）＋寫實小腐敗蝶（深紅、黑翅脈、破翅，夾紫藍和白）；癲火＝捲曲火球（像癲火聖印記，中心暗）；冰凍＝霜面冰塊＋不斷逸散的寒氣（像輝石冰塊）。三燈齊光刃亮金 |

### 武器裝置（`prototypes/devices/`，程式 `devices.py`）
| 武器 | 設計 | 狀態 |
|---|---|---|
| 銃槍龍杭砲 | **米凱拉的未鍛金之針**（金針、絞絲針眼裡一滴光）；刺入裂出金紋、連續爆裂、最後大爆 | 預覽，使用者看過 |
| 重弩龍穿點火 | **D 卷草鑽**（2026-10-03 使用者選）：三股象牙絞成鑽尖、金線、光芯，尾端三個往回捲的卷草；從魔物身上貫穿而出 `prototypes/attachments/piercer.png` | 選好，**遊戲檔還沒確定** |
| 輕弩地雷彈 | 象牙花苞包著光，被打到綻開再爆；遊戲版落地就綻開，**2026-10-03 抬到地面上**（之前八成埋在地下） | 同上 |
| 弓追蹤箭 | **B 光花綻放**（2026-10-03 使用者選）：插箭處象牙花在皮上綻開、金光花緣，打越多開越大，快爆時全開、升起光蕊和光環；箭尾一滴光＋一圈光環 `prototypes/attachments/tracer.png` | 選好，**遊戲檔還沒確定** |
| 輕弩速射彈鼓（新） | **A 象牙燈籠**（2026-10-03 使用者選）：兩圈象牙框、斜的象牙肋骨籠子、兩面金絲卷草＋發光軸心，籠裡一圈光滴＝子彈 `prototypes/attachments/lbg_drum.png` | 選好，**遊戲檔還沒確定** |
| 重弩彈匣（新） | **C 聖匣**（2026-10-03 使用者選）：哥德式小聖物匣，象牙柱、金光尖拱窗、裡面吊一大滴光、底下倒過來的卷草尖塔 `prototypes/attachments/hbg_mag.png` | 選好，**遊戲檔還沒確定** |
| 重弩防禦盾（新） | 第一輪四版（聖樹紋章／光翼／百合／玫瑰窗）都沒選；使用者要**槍管上的光環往後拉到盾的位置、擴大成盾** → 重新提案 | **雲端 session 提案中** |
| 狩獵笛響玉 | 地上光環＋浮空金膜泡泡，攻擊時共鳴 | 同上 |

**遊戲版（2026-10-02）**：龍杭（金針）、起爆龍彈（花苞）已做成遊戲的特效模型並裝進遊戲（`mhws/MiquellaLight_Devices_kit/`），等實測；其他三個的遊戲檔還沒確定

### 遊戲端（`mods/miquella/mhws/`）

- **遊戲**在 `C:\Program Files (x86)\Steam\steamapps\common\MonsterHunterWilds`（不用系統管理員權限就能寫）。REFramework＝`dinput8.dll`（nightly-01424，所有 RE 遊戲共用的 `REFramework.zip`，只放這個檔）；pak 放 `pak_mods/`（REFramework 的 PAK Directory Loading 預設開，不用 Fluffy）。全部移除：刪 `dinput8.dll`、`reframework/`、`pak_mods/`。遊戲資料夾的 `re2_framework_log.txt` 可以直接讀來除錯
- **武器這邊裝在遊戲裡的**：腳本（`reframework/autorun/`）`MiquellaLight_Weapons.lua`（換裝＋武器動作效果）、`MiquellaLight_Effects.lua`（特效改金、藏攻擊／防禦上升閃光），只讀的 `MiquellaLight_Scout.lua`、`MiquellaLight_FxProbe.lua`；pak：每種武器的模型 `MiquellaLight_<武器>.pak`、特效 `MiquellaLight_<武器>FX.pak`（`fx_paks.py` 從使用者的遊戲檔產生，改過的卡普空檔不進 repo）、`Devices`（龍杭金針、起爆龍彈花苞、彈殼金光）、`Arrows`（金針箭）、`HornFX`（響玉金泡泡）。人物的腳本和 pak 見第 9 節「人物」
- **怎麼裝**：Lua 遊戲開著也能複製，請使用者在 REFramework 選單 ScriptRunner → Reset scripts；**pak 遊戲開著會被鎖** → 放進 `C:\Users\anton\MiquellaTools\work\install\pak_mods\`（Lua 放 `install\autorun\`），背景跑 `work\install_when_closed.sh`（每 2 秒檢查，遊戲一關就複製並比對）。背景程序跟著 session，session 關了就沒了：接手時先比對 `work\install\pak_mods` 和遊戲的 `pak_mods`。打包：kit 的 `natives` 複製進 `work\stage_<武器>\`（裡面已有共用貼圖）→ `make_patch_pak.py`（用 `bpy45` 的 Python 跑），讀回比對過才裝
- **離線測試**（`mhws/tests`）：`C:\Users\anton\MiquellaTools\bpy45\Scripts\python run_lua.py weapons_test.lua <換裝腳本>`（再加 `missing` 跑一次）、`effects_test.lua`；改腳本前後都要全過。**換裝腳本的主程式 local 用了 172／200**（Lua 的上限，超過整個腳本在遊戲裡載入失敗；新東西優先放進現有的表）
- **找遊戲欄位不要猜**：換裝腳本的欄位記錄器（選單「Record weapon fields (for Claude)」，預設開）把武器處理器的數值欄位（含子物件一層、陣列）存成遊戲資料夾的 `reframework/data/MiquellaLight/fields_<型別>.json`：`changed`（有變過的）、`all`、`actions`（獵人動作名稱的變化，最近 150 筆）、`events`、`trace`（片手劍完美突進每幀的變化），Claude 在本機直接讀。升段時間這類固定參數在遊戲參數檔 `gamedesign/player/actiondata/wpXX/globalparam/wpXXglobalactionparam.user.3`（`extract_game_files.py` 抽出來，掃「個數＋遞增的浮點數」）
- **在遊戲裡驗證過可行的**：執行中換模型和材質（`setMesh`／`set_Material`）、收刀隱藏、改材質參數（`Emissive_Intensity`、`Emissive_Color`、`Dissolve`、開關材質）、新加的骨頭（`MQ_*`：`getJointByName` → `set_LocalPosition`／`set_LocalRotation`，在 LateUpdateBehavior／PrepareRendering／BeginRendering 都設一次）、執行中改特效顏色。**不行的**：執行中縮放整把武器（被遊戲蓋掉 → 預先做好的大小模型）、材質自己的 `MoveEmit` 流光（沒效果 → 切成分段材質輪流亮）、武器材質半透明（只能鏤空裁切）、改特效檔裡的軌跡顏色（雙劍、操蟲棍的軌跡是遊戲執行時染的 → 特效腳本執行中染金）

| 東西 | 內容 |
|---|---|
| `MiquellaLight_Weapons` | 換裝腳本：依武器種類換成我們的外觀（`config.assignType`；盾、箭筒在副武器那列選）、收刀隱藏、浮動光環、蓄力／型態／量表的動作效果、生長骨頭、欄位記錄器。機制說明在它的 README |
| `MiquellaLight_Effects` | 執行時改特效顏色（雙劍紅 → 金、藍 → 銀；大劍、輕弩、太刀、弓、操蟲棍染金）、藏攻擊／防禦上升閃光。版本紀錄在它的 README |
| `MiquellaLight_FxProbe`、`MiquellaLight_Scout` | 只讀的偵測腳本：播了哪些特效檔和參數（`fx.json`）；武器／防具的模型、材質參數、骨頭（`scout.json`）、Watch（`watch_<型別>.json`） |
| `MiquellaLight_<武器>_kit`（14 種＋獵蟲、裝置、金針箭） | 遊戲素材（`.mesh`、`.mdf2`；貼圖用雙劍 kit 的）。對齊原版的量測、重做指令、骨頭和材質在各自的 README；`.blend` 不進 repo，用指令重建 |
| `release/MiquellaLight_v0.1.zip` | 最早的可安裝測試版（雙劍光劍＋換裝腳本），發布前要重包 |
| `MiquellaLight_HideSheathed` | 舊的收刀隱藏腳本，已被換裝腳本取代，留作備案 |

---

## 5. 設計原則（累積的使用者意見，做任何新東西都要遵守）

- **發光是亮金色，不要白光**；只有使用者指定的地方是白（大劍三段、太刀最高段）。操蟲棍三色是唯一離開金色的例外
- 「亮金」調法：顏色更飽和、強度大幅提高，讓光暈變大變金（只調淡會跟一般一樣，再加就變白）
- **輕盈、鏤空**：米凱拉身形纖細，厚重設計不合格（大劍、長槍、銃槍都因此重做過）
- **奢華卷草**：分支不能三根一樣；用由粗到細、捲成漩渦、帶側枝的卷草；象牙底上要凸顯時用**金色花絲**
- **不要新月**（月亮是菈妮的象徵）
- **懸浮光點**（點亮的水滴套小光環）是使用者很喜歡的元素，可以兼當量表
- 動作效果要有**力量感**，蓄力時變化要明顯（長槍第一版就是太弱被否決）
- 使用者**不想看到一堆不明的特效**：攻擊／防禦上升的閃光已用 `MiquellaLight_Effects` 藏掉；其他雜亂的狀態特效也可以考慮藏
- 寫實優先的場合（操蟲棍精華），**不要用模型硬做火舌之類的特效**，那很醜；火、煙、冷霧在遊戲裡要用**特效**
- 被否決過的方向（不要再提）：大劍對稱寬刃、外框光膜加小葉子（像玩具）；斬擊斧新月、外框光膜、整片光刃（像船槳）；斬擊斧劍模式 B；操蟲棍方案 A（三刃）、操蟲棍護手改卷草；初版的光膜翅膀腐敗蝶（太科技感）；模型做的火舌；凝成一團的冷霧；銃槍第一版（三根光肋＋象牙彈簧：簡陋、沒設計感、不好做特效）

---

## 6. 技術：怎麼產生預覽圖

**環境**（雲端這樣裝；本機一樣做得到）
- Python 3.11 ＋ `pip install bpy==4.2.0`（無介面的 Blender），另外一個 venv 裝 `bpy==4.5.3` 給 RE Mesh Editor 匯出用
- 匯出需要把 RE Mesh Editor 裝成 Blender 外掛（雲端是放在 `~/.config/blender/4.5/scripts/addons/re_mesh_editor`）
- **本機（2026-10-01 裝好）**：全部放在 repo 外的 `C:\Users\anton\MiquellaTools\`：`bpy42\`、`bpy45\`（venv，都有 zstandard；bpy45 另有 lupa）、`addons\re_asset_library\`、`MHWs_STM_Release.list`（REE.PAK.Tool 的檔名清單）、`extracted\`（**從遊戲解出的原版檔案，是卡普空的，絕對不要放進 repo**）、`work\`。RE Mesh Editor 在 `%APPDATA%\Blender Foundation\Blender\4.5\scripts\addons\re_mesh_editor`。執行：`C:\Users\anton\MiquellaTools\bpy45\Scripts\python <腳本>`
- **Windows 無介面的坑**：RE Mesh Editor 的匯入／匯出「運算子」會切換系統主控台，在無介面 Blender 直接當掉（segfault，沒有錯誤訊息）→ 直接呼叫 `importREMeshFile`／`exportREMeshFile`（`fit_dual_blades.py` 有範例）。程式結束時的 segfault 無害（`os._exit` 前先 flush 輸出）
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
| `python extract_game_files.py <遊戲資料夾> <檔名清單> <輸出> <RE Asset Library 所在資料夾> <正規表示式>...` | 從本機遊戲的 pak 解出原版檔案（新 patch 優先）；例：`"art/model/item/it02/00/0024/[^/]*\.(mesh\|mdf2)\."`，15 秒 |
| `python inspect_wilds_mesh.py <.mesh>...` | 印出骨架、材質、每個子模型的範圍和權重（不經 Blender 匯入） |
| `python inspect_wilds_mdf.py [--all-params] <.mdf2>...` | 印出材質的 shader、旗標、貼圖、參數 |
| `python fit_dual_blades.py <kit> <原版 .mesh> <原版 .mdf2>` | 把雙劍光劍對齊原版（方向、握把、骨架）並用原版材質重建 `.mdf2` |
| `python build_weapon_kit.py <名稱> <kit> <原版 .mesh> <雙劍 .mdf2>`（名稱見 `WEAPONS`：14 種武器、各盾牌、獵蟲） | **新武器的素材包一次做完**：原型 → 減面、依材質分槽 → 照原版擺放 → 原版骨架（特效骨頭移到我們的刀尖／槍口）→ `.mesh`＋`.mdf2`（材質抄雙劍 kit）。加武器就在 `WEAPONS` 加一個函式 |
| `python build_device_kit.py <wyrmstake\|wyvernblast> <kit> <原版 .mesh> <stickyshell .mdf2>` | **武器裝置**：原型 → 一個材質 `lambert1`、三色分區貼圖、每個顯示群組放完整模型 → 蓋過遊戲的特效模型路徑 |
| `python preview_kit.py <kit .blend> <原版 .mesh> <out.png> <front\|side\|gun> [間距]` | 素材包和原版並排的預覽（原版灰色）；圖裡有原版，**不進 repo**（放 `MiquellaTools\work\previews\`） |
| `python power_states.py <set> <輸出>`（`lance_power`、`bow_power`、`extract_orbs`、`extract_on_glaive`、`weapons_power [武器名]`、`lance_anim`）／`python power_round2.py <gunlance\|hammer\|hammer3\|sns> <輸出>` | **蓄力力量感的設計提案**（2026-10-02）：每個方向蓄力 1→2→滿並排；`weapon_power.py`（其他武器的加強方向）、`orb_styles.py`（操蟲棍精華的四種造型）是它們用的模組 |
| `python preview_grow.py <kit .blend> <great_sword\|lance\|long_sword\|bow> <輸出> [每秒格數]` | **蓄力生長預覽**：照換裝腳本的算法（生長段＋生長骨頭）和遊戲的時間，輸出一排格子＋GIF；圖裡只有我們的模型，放 `MiquellaTools\work\previews\grow\` |
| `python preview_bloom.py <kit .blend> <_bloom.json> <輸出前綴> [full\|head]` | **銃槍聖百合的蓄力動畫預覽**：照遊戲的骨頭算法，一段龍擊砲（蓄能 → 發射 → 淡出）的 GIF＋0～100 % 格子圖；骨頭和權重來自 `lily_rig.py`（`build_weapon_kit.py gunlance` 用它做模型和 `_bloom.lua`） |
| `bpy45\Scripts\python gunlance_lily_charge.py／gunlance_lily_body.py <輸出> [test]` | 聖百合的蓄力力量感提案（A～D）、槍身變化提案（C1～C4），各畫一段／二段／滿 |
| `bpy45\Scripts\python attachments.py <lbg_drum\|hbg_mag\|hbg_shield\|tracer\|piercer> <輸出> [test] [A B C D]` | **武器附加物提案**（2026-10-03）：每樣四個版本，兩排（裝在槍上／近看、平時／防禦、插上／快爆、彈頭／貫穿），拼成 `<名稱>.png`；只有我們的模型，可以進 repo（`prototypes/attachments/`） |
| `bpy45\Scripts\python gunlance_designs.py <輸出> [test] [A B C D]` | **銃槍重新設計提案**（2026-10-03）：四個方向各畫平時、槍身近看、龍擊砲蓄能三張，拼成 `gunlance_redesign.png`；`test` 是低解析度快速試畫 |
| `python trail_scan.py <解出的遊戲檔根目錄> <MiquellaTools\work> [out.md]` | 列出每種武器特效檔裡的軌跡條目和顏色，標出哪些已在我們的 pak 裡 |
| `bpy45\Scripts\python fx_paks.py <解出的遊戲檔根目錄> <MiquellaTools\work> [it01 ...]` | **全部武器的金色特效 pak**：照檔案裡的規則表用 `recolor_efx.py --layers` 改色、打包、放進 `work\install\pak_mods` |
| `python preview_morph.py <kit .blend> <_morph.json> <輸出前綴> [第二個 kit .blend x y z]` | **變形動畫預覽**（斬擊斧、充能斧）：照遊戲的骨頭算法變形，輸出 `_strip.png`（進度 0～1 六格）和 `.gif`（來回）；第二個 kit（充能斧的盾）擺在旁邊淡出。只有我們的模型，可以進 repo（`prototypes/action_states/`） |

**共用模組**：`common.py`（場景、材質、算圖）、`motifs.py`（光環、編織管、細枝束、卷草、懸浮光點、光刃…）、`status_fx.py`（腐敗黴球、寫實腐敗蝶、冰塊）、`particle_fx.py`（用旋渦氣流描出的火絲、爆炸光絲、體積冷霧）

**已知限制**：pip 版 bpy 的 Mantaflow（火焰模擬）會壞（`LevelsetGrid` 錯誤），所以火和煙是用氣流描線＋體積材質模擬；粒子小球在這個尺寸看起來是一顆顆的，不像火

---

## 7. 研究結論重點（細節在研究筆記）

- **材質可以在遊戲中即時改**：`renderMesh:setMaterialFloat`／`setMaterialFloat4`／`setMaterialsEnable`（MDF-XL 就這樣做）。Weapon Emissive 材質有 `Emissive_Color`、`Emissive_Intensity`、`Dissolve`（淡入淡出）、`Use_MoveEmit`／`MoveEmit`（移動光帶）、`AnimEmit_*`（呼吸燈）等
- 動作效果的做法：會出現的零件放獨立材質槽＋`Dissolve` 淡入；會動的零件綁武器自己的骨頭；光流用 `MoveEmit`
- 遊戲用哪個欄位代表蓄力段數、鬼人化、填彈：用換裝腳本的欄位記錄器在遊戲裡找到了，見第 9 節「武器的遊戲欄位速查」
- **不覆蓋原版的掛載法**：腳本生成物件、`setMesh`／`set_Material`、`set_SameJointsConstraint` 掛到獵人骨架（研究筆記 15）
- **特效**：`.efx` 沒有公開編輯器，只能改顏色。可行的路是 **Armor VFX Manager（Nexus 4908）** 那種做法：執行時生成遊戲現成的特效、掛到任一骨頭、改顏色、依動作觸發；VFX Unleashed（Nexus 4842）可減弱原版蓄力強光、依蓄力段數換特效
- **武器模型的規格（實測＋解出原版確認）**：刀身朝檔案 **+Z**、**手握在原點**（雙劍刀柄約 -0.04～+0.13，柄頭到 -0.10～-0.15）；骨架 `root` → `Base` → `VFX_Attack`（刀尖，例 z=1.285），全部頂點綁 `Base`；原版雙劍長 1.2～1.6 m（我們的光劍 0.81 m）。遊戲裡的路徑長這樣：`Art/Model/Item/it02/00/0024/it0200_0024_0.mesh`
- **材質一定要從遊戲現在的原版 `.mdf2` 複製**：RE Mesh Editor 0.66 的 Wilds 預設是舊版（176 參數），現在 180 個；排列不對，發光等數值會全部讀錯（第一版光劍變黑的原因）
- **大劍**（`it00`）：手在原點、就在護手正下方，握柄往下到 -0.8 m，刀尖約 2.2 m；**單刃武器刃口朝 -X**（單刃原版和太刀的弧度都這樣）。**輕弩**（`it13`）：槍口 +Z、**+Y 朝上**（掛繩、物理鏈往 -Y 垂），原點在機匣頂端，槍膛在下方約 0.19 m（`VFX_Fire`）；原版的 visconGroup 3／4／5 是槍托、長槍管、附件，我們只做 group 0
- 重設場景（`read_factory_settings`）會關掉 RE Mesh Editor 外掛，之後再匯入會無聲當掉 → 建完模型後再啟用外掛（`build_weapon_kit.py` 的 `enable_addon`）
- 武器檔案：雙劍 `it02`（`_0` 左手、`_1` 右手）、大劍 `it00`、太刀 `it03`、片手劍 `it01`（`_1` 是盾）、重弩 `it12`、輕弩 `it13`；其他武器的編號照 MDF-XL 資料庫的 WPType 推測，要用偵察腳本確認
- 資料片《荒野：Ascendance》預定 2027，會給每種武器加 Boost Bracer 新動作，出了再補
- 雲端環境連不上 Nexus 和 Fluffy 官網；GitHub 可以

---

## 8. 待決定的事

- **發布到 Nexus Mods（使用者 2026-10-02：不急，確認做得到而已）**：等**米凱拉人物也做好**再一起包，或兩者都好了再分開上傳。到時要準備：Fluffy／手動都能裝的 zip（pak＋`reframework/autorun` 的換裝、特效腳本，不含偵察腳本、欄位記錄器預設關）、前置 REFramework、英中介紹與安裝說明、致謝（REFramework、RE Mesh Editor、RE Asset Library、REE.PAK.Tool）；改色的特效 pak 是改過的卡普空檔案（灰色地帶，放不放或當選配要使用者決定）；上傳由使用者自己操作。雛形：`release/MiquellaLight_v0.1.zip`
- （已決定 2026-10-03：操蟲棍三燈蓄力選 **D 三色光旋**，遊戲版已做，見第 9 節「武器」）
- **銃槍的盾**：聖百合定案了（2026-10-03），盾還是長槍那面樹紋能量盾，要不要配一面百合風格的盾（之後做提案）
- **雙劍貼圖的 NRRO 要不要重轉（2026-10-03，人物 session 發現，見第 0 節；使用者：先不弄，不急）**：雲端轉檔時壞掉，所有武器的象牙／握把部分在遊戲裡其實是鏡面（粗糙度 0.03）＋壓暗（AO 0.22）；重轉後會變亮、變霧面，跟使用者看慣的不一樣 → 等使用者決定（可以先做對照給他看）
- （已決定 2026-10-03：輕弩速射彈鼓 A、重弩彈匣 C、追蹤箭 B、龍穿點火 D）**重弩防禦盾**：光環變形成盾的提案等使用者挑
- **輕弩、重弩的槍托**（2026-10-03 使用者發現人物都沒抓到槍托的位置）：要不要改位置、縮短或拿掉，等本機 session 查完給使用者看（第 9 節「武器」→「槍托問題」）
- 四個新裝置（重弩、輕弩、弓、狩獵笛）使用者還沒回意見（重弩龍穿點火、弓追蹤箭併進上一項）
- 覆蓋原版檔案，還是用腳本掛上去（建議腳本掛載）
- 頭髮微光的做法（建議：編髮發光、散髮不發光）
- 操蟲棍三顆球繞刃轉的速度、半徑；要不要做綠色精華（荒野有，三燈不需要）
- （已決定 2026-10-02：獵蟲實心金翅；充能斧盾的新月感先不改）
- 特效要直接依賴 Armor VFX Manager，還是學它的寫法放進自己的腳本

---

## 9. 下一步

**武器（第一帳號負責；2026-10-03 整理）**：舊留言和每一輪實測的處理紀錄原文在 `mods/miquella/WEAPONS_LOG.md`
- **等使用者實測：第七輪（2026-10-03 凌晨裝進遊戲，最新）**
  - 大劍：蓄力時三條光絲從護手**連續伸長**到刀尖（不是一格一格冒出來），三段時刃口飛火花；放開後在原地淡出
  - 長槍：光鑽連續伸長、細光絲一段後加入、越長轉越快；三段時根部旋轉弧＋槍尖光刃
  - 太刀：**氣刃蓄力**（`cKijinCharge`）時兩條光絲纏上刀身、氣刃大迴旋斬揮完才淡出；練氣段數只管刀身顏色和流光
  - 弓：拉弓時花**一朵一朵開**（每段的時間開兩朵），三段時剩下的和弓尖大花接連開
  - 銃槍：蓄力砲擊時槍身裡的金絲連續拉長
  - 操蟲棍：點燈後三朵精華花有沒有出現（以前讀錯欄位，從沒出現過）；**三燈蓄力 D 三色光旋**（紅白橘三股光絲連續編上刀刃、花被吸進去、上升螺旋斬後淡出）；攻擊軌跡不再先紅再金
  - 輕弩：起爆龍彈落地後整朵花在地面上
  - **銃槍（2026-10-03 聖百合，新）**：拿銃槍看是不是聖百合（盾還是舊的）；**蓄力砲擊**按住時花前的光之百合、光葉、小光百合連續長大，花瓣往後翻，放開發射後光在原地淡出；**龍擊砲**整段蓄能跟著長，最後出三圈光環（第一次會用 2.5 秒估，發射後就記住實際長度，第二次起應該剛好）；砲擊、填彈時花瓣輕輕一彈；花苞尖的光滴跟彈數一樣多。選單要看 `Gunlance:` 的 `lily:` 和 **`Lily joints found: 126/126`**（0 就是新骨頭沒建立關節）
  - **不對的時候**：光絲一格一格跳或尖端一團光 → 換裝腳本選單 `Growth bones found:` 不是 n/n（0＝新骨頭沒建立關節）；完全沒長 → `Growth:` 的段數、計時器是 `?`（欄位名錯）；長得比升段快／慢 → `Growth:` 的門檻有沒有變 `learned`（`fields_*.json` 的 `events`）；太刀沒長 → `actions` 裡氣刃蓄力的動作名；操蟲棍沒花 → `Extracts:` 寫 `not readable`（陣列讀法）或顏色對不上（`EXTRACT_TYPE` 的順序）；操蟲棍還有紅軌跡 → 特效腳本的 `fastWhile` 少了那個動作的字（`actions` 裡找）
- **之前裝了、使用者還沒回報的**：大錘渾天儀（三道大環像陀螺儀轉）、充能斧斧強化的光齒跑馬燈、片手劍完美突進的時機光環（第一版，時機用猜的）、片手劍盾的光膜 C／D 比較、龍擊砲壓彈簧（改讀動作 `cRyuugeki*`）、太刀練氣流光（刀身切 8 段輪流亮）、響玉金泡泡第四版（細線）、龍杭金針（只放顯示群組 5～9、發光材質）、重弩光環和光點磁浮、獵蟲慢拍翅膀、全部武器的攻擊軌跡改金（狩獵笛音符軌跡變全金，不喜歡就拿掉 `HuntingHornFX`）、雙劍 Size 1.4／B 版三刃／藍鬼人的銀色、輕弩速射量表（要裝填有速射標記的彈才測得到）
- **還沒做／已知問題**：
  - **銃槍聖百合**：遊戲版已裝（見上面 A）；還沒做：配套的盾（第 8 節）；蓄力砲擊滿蓄力的時間 1.8 秒是估的（`LILY_GL.chargeFull`），使用者覺得太快／太慢就改
  - **雙劍 kit 的 NRRO 貼圖是壞的**（人物 session 發現，第 0 節）：所有武器的象牙／握把部分在遊戲裡其實是鏡面＋壓暗；使用者 2026-10-03：先不弄。其他雲端轉的貼圖（裝置 `Devices/tex` 等）也要檢查
  - 片手劍時機光環要校正：使用者打幾次完美突進後讀 `fields_app_cHunterWp01Handling.json` 的 `trace`，找出完美的時間窗（做法在 `WEAPONS_LOG.md` 第 3 節「⑧」）
  - 響玉泡泡常駐（打擊時泡泡留在原地）：先用 FxProbe 錄一次響玉，找出響玉存在期間一直在播的特效
  - 盾的半透明光膜：等使用者比較片手劍 C／D 選一個，再套到長槍、銃槍、充能斧的盾
  - 還沒找到的欄位：雙劍真鬼人化（藍鬼人 → 亮金）、斬擊斧變形量表、充能斧真正的瓶數（現在用 `_ActionEnterBinNum` 代替）
  - 大劍三段的刃紋光帶用的是材質的 `MoveEmit`（太刀證實這個沒效果）→ 使用者沒抱怨就先不動，要的話照太刀切段
  - 操蟲棍三燈蓄力的升段時間是猜的（0.8／1.6 秒），第一次蓄力會自己學到（`Weapons.json` 的 `chargeTimes`）
  - 裝置：重弩龍穿點火、弓追蹤箭、狩獵笛響玉的遊戲檔還沒確定（`MiquellaLight_Devices_kit/README.md` 有候選），這四個新裝置的設計使用者也還沒回意見
  - **附加物遊戲版（2026-10-03 使用者選好：輕弩彈鼓 A、重弩彈匣 C、追蹤箭 B、龍穿點火 D；盾在重新提案）**：模型的做法在 `attachments.py`（`drum_a`、`mag_c`、`tracer_b`、`piercer_d`，原型座標：槍口 +Y、上 +Z，跟 `light_bowgun.py`／`bowgun.py` 同一套）。先找遊戲檔：①**輕弩速射彈鼓**：速射模式（按 ◯）時才裝上去，先用偵察腳本（`scout.json`／Watch）看進速射前後輕弩多了哪個模型或哪個顯示群組，或解 `art/model/item/it13/99/` 看（像箭的 `it1199_*` 那樣）；是武器自己的零件 → 換裝腳本換掉，獨立物件 → patch pak 蓋過；②**重弩彈匣**：同上，`it12/99/`；③**追蹤箭**：射一次追蹤箭用 FxProbe 錄，看是 `11_arrow_03／04` 還是 `it1199_0002_0`；插著時的花是特效模型（跟起爆龍彈花苞一樣做法：`build_device_kit.py`），綻開程度跟著打中次數（要找欄位，或先固定半開）；④**龍穿點火**：候選 `weapon/it12/11_it1299_0001_0`（0.46 m 扁片），用 FxProbe 錄一次點火；⑤**盾**：候選 `Art/Model/Item/it12/99/0001/it1299_0001_0`（有鉸鏈、板子會展開），也可能是原版重弩模型自己的零件（`Hinge` 骨頭）——我們的重弩換掉後盾不見了；等提案選好再做
  - **槍托問題（使用者 2026-10-03）**：「輕弩、重弩的槍托，人物都不會去抓到那個位置」。三種可能：①我們的模型沒對齊手（握把位置錯）；②原版其他設計本來就不把槍托放在那（槍托短、或只抵在手臂下）；③原版根本沒有槍托。查法：
    1. 遊戲裡拿**原版**輕弩、重弩（換裝腳本關掉或選原版）截圖：收刀拔刀、待機、架槍瞄準、開火、裝填、速射／點火、防禦，看兩手和肩膀碰到武器的哪裡；再換**我們的**同樣姿勢截圖對照
    2. 記錄獵人左右手骨頭在武器 `Base` 座標裡的位置（偵察腳本加一段，或 Watch），跟我們模型的握把、前方握持處、槍托範圍比（輕弩 kit：原型 ×1.6、往後挪 0.1，範圍 z -0.74～+0.76，握把在原點後約 0.3；重弩 ×1.3，長 1.7 m）
    3. 解出幾把原版輕弩、重弩（`it1300_00xx`、`it1200_00xx`，各挑 5～6 把不同造型），`inspect_wilds_mesh.py` 量槍托：有沒有、末端到哪、多長、跟握把的距離
    4. 整理成對照圖給使用者決定，可能的改法：手沒對上 → 整把重新對齊；原版槍托普遍短／沒有 → 我們的槍托縮短，或改成懸浮的象牙卷草收尾（更輕盈，也比較不會跟長髮穿模）；**不要自己定**
  - 特效腳本拿雙劍、大劍、輕弩時每幀搜全場特效（約 1.7 ms／幀，使用者沒感覺卡），之後可優化；拿操蟲棍放獵蟲時記憶體升高（使用者說先擱置），長時間測很多武器後建議重開遊戲
  - 使用者把 Glow 拉到 5，之後可寫回 `.mdf2` 預設值
  - 之後的想法：學 Armor VFX Manager 生成特效（火、寒氣、爆炸、光柱）；Ascendance 的新動作

**武器的遊戲欄位速查**（處理器 `app.cHunterWpXXHandling`；都是在遊戲裡記錄到的）

| 武器 | 欄位 | 動作、其他 |
|---|---|---|
| 雙劍 `Wp02` | 鬼人化 `_KijinExtern`（開時 0.13 秒內 0→1）、`_IsKijinOn`；真鬼人化還沒找到 | 特效：軌跡 `11_it02_001` 的參數 `Color`、身體光 `002` 的 `ColorA／B／C`（遊戲執行時才設顏色） |
| 大劍 `Wp00` | 段數 `_ChargeLevel`（0～3）、`_ChargeTimer`、蓄力種類 `_ChargeType` | 一般蓄力 0.8／1.55／2.3 秒升段、3.0 過蓄（其他種類不同） |
| 太刀 `Wp03` | 練氣 `<AuraLevel>k__BackingField`（1 無～4 紅）；氣刃蓄力 `_KijinChargeLv`（0～3）、`_KijinChargeTimer` | 氣刃蓄力 0.8／1.6／2.9 秒；`cKijinCharge*` → 氣刃大迴旋斬 `cKijinSlashRound` |
| 片手劍 `Wp01` | `_IsJustRush`、`_StepSlashCount`（0～4） | 完美突進 `cJustRushStart`、`cJustRushCombo0～2` |
| 大錘 `Wp04` | 段數 `<ChargeLv>k__BackingField`（0～3） | |
| 狩獵笛 `Wp05` | — | 響玉、聲波都是特效（`11_it05_000～042`），泡泡模型是共用的 `Art/VFX/Mesh/Common/Other/bubble/11_bubble_00` |
| 長槍 `Wp06` | `_FinishChargeLevel`（0～3）、`_FinishChargeTimer` | 0.8／2.0／3.6 秒升段 |
| 銃槍 `Wp07` | 填彈 `_IsReload`；蓄力砲擊 `_ChargeShotElapsedTimer`（放開不歸零：還在增加＝蓄力中）；彈數 `_ChargeShotBulletNum`；龍擊砲量表 `_RyuugekiGauge._Value`（1～2，發射那一刻才扣） | 龍擊砲 `cRyuugekiStart`／`Idle`／`AimIdle`／`ToAim`／`Shoot`／`Shot` |
| 斬擊斧 `Wp08` | 型態 `_Mode`（0／1）、覺醒 `_SwordAwakeTimer`；變形量表還沒找到 | |
| 充能斧 `Wp09` | 型態 `_Mode`（0／1）、劍能量 `_SwordEnergyState`（0～3，2＝滿）、`_ShieldEnhancedTimer`／`_SwordEnhancedTimer`／`_AxeEnhancedTimer`；瓶數暫用 `_ActionEnterBinNum` | |
| 操蟲棍 `Wp10` | 蓄力 `<ChargeLv>k__BackingField`（0～2）、`_ChargeTimer`；精華 `ExtractTimer`（`app.cValueHolderF[]`，照 `app.Wp10Def.EXTRACT_TYPE` 排）、三燈 `TrippleUpTimer`；獵蟲＝角色的 `get_Wp10Insect` | 三燈蓄力 `cHoldAttackSuper` → 上升螺旋斬 `cBatonUpSlashSuper` → `cSelfJumpLand`；放獵蟲 `cInsectAttack`、收回 `cInsectBack`；軌跡 `11_it10_001`／`004` 檔案裡是白的、遊戲執行時染紅 |
| 弓 `Wp11` | 段數 `<ChargeLv>k__BackingField`（平時 1，1～3）、`<MaxChargeLv>k__BackingField`、拉弓 `_IsBowStringConstToHand`、`_ChargeTimer`、`_ActionParam._ChargeTimeLv2～4`（1／2／3 秒） | 弦上的箭是 `it1199_0000_0` |
| 重弩 `Wp12` | — | |
| 輕弩 `Wp13` | 速射量表欄位是猜的（沒測到） | 起爆龍彈特效 `11_it13_106`：飛行時顯示模型群組 0＋1、落地後 0＋2；地面在特效原點 |

共通：獵人目前的動作＝角色的 `get_BaseActionController`／`get_SubActionController` → `get_CurrentAction` 的型別名稱（換裝腳本的 `actionNow`）。

**武器的說明在哪**：蓄力零件、生長骨頭、型態變形這些機制 → `mhws/MiquellaLight_Weapons/README.md`；每把武器的模型、骨頭、材質、重做指令 → 各 kit 的 README；特效改色 → `mhws/MiquellaLight_Effects/README.md`、`fx_paks.py`、`trail_scan.py`、`recolor_efx.py`；預覽工具 → `preview_grow.py`（蓄力生長）、`preview_morph.py`（變形）、`glaive_charge.py`／`power_states.py`（設計提案）；舊紀錄 → `mods/miquella/WEAPONS_LOG.md`

**人物（第二帳號負責；2026-10-03 整理）**
- **現況**（都已裝進遊戲，選單「MiquellaLight: Character」）：
  - 頭冠 v10：腳本生成物件掛到獵人 `Head`（不覆蓋遊戲檔）；**還沒實測**：看在不在額頭、跟不跟頭動，位置用選單滑桿調、數值告訴 Claude 寫回模型；戴頭盔會穿模
  - 身體三款 A 纖細中性／B 少年感／C 柔和（選單 `Body shape`），開啟時藏獵人的防具和內衣，臉和頭髮保留；**等使用者挑**。已修：骨架對齊（啤酒肚、胯下）、腹股溝 V 線、錐形大腿、圓潤屁股、收腰＋馬甲線＋背溝、脖子（2026-10-03 照原版接法，使用者：「這個版本不錯」，剩下的小變形頭髮擋得住）
  - 材質暫用雙劍的象牙色（跟臉的膚色不同）
- **文件**：做法、參數、指令、試過不行的 → `mhws/MiquellaLight_Character_kit/README.md`；腳本、選單、測試 → `mhws/MiquellaLight_Character/README.md`；遊戲獵人身體的量測 → 研究筆記第 18 節；已決定的方向（一件長袍蓋全身、身體不刪減、長袍內側要雙面…）→ `notes/two-account-handoff-plan.md`「米凱拉風格角色」
- **下一步**（照順序）：
  0. **2026-10-03 清晨第一次實測（本機 session）**：身體看得到，但**陰影處全黑、亮處灰色像金屬、調色只變明暗** → 兩個原因都修了：①腳本生成的 Mesh 的 `StencilValue` 是 0（獵人自己的是 1，用診斷腳本 `MiquellaLight_Scout/.../MiquellaLight_MeshDiff.lua` 比對臉和身體的 Mesh 設定找到）→ 角色腳本從臉的 Mesh 複製 `StencilValue`、`ShadowCastMode`（選單狀態 `render:`）；②材質抄雙劍的貼圖、NRRO 壞掉（見第 0 節給第一帳號的留言）→ `miquella_body.py` 的 `make_textures` 給身體自己的膚色／布料貼圖（`BODY_TEXTURES`：膚色 sRGB 234,199,172＝使用者要的黃偏白、粗糙度 0.55）；選單 `Skin tone` 五種膚色（`ColorParam` 乘上去）。**腳掌太長**（使用者）：原本把腳轉向遊戲的 Instep、陷地 5 cm 再壓扁到 63 % → 改成保留 MakeHuman 的腳角度、`shorten_feet` 等比例縮到 24.5 cm（`FOOT`）。裝好後膚色 OK，但使用者站在潔瑪旁邊比對：**身體糊、有一塊塊斑**（武器 shader 的雜訊／細節層）→ 皮膚改用**遊戲內衣的 `skin` 材質**（`Base_ATOS_SkinEdit_VFX`，`SKIN_SOURCE`）：中性底色（遊戲身體貼圖的平均 sRGB 152,152,157，不用它的貼圖＝成年男性肌肉、獵人 UV）× 膚色色盤 `SkinMap01` 在 `AddColorUV` 的位置；`BlendNormalMap` 換平坦的。腳本把**臉的 `AddColorUV` 複製到身體**（選單 `Skin tone` 預設 `Match the face`，另外三個在上面再乘 `ColorParam`；狀態列 `face tone x, y`）。裝好後斑塊消失但身體**深棕色**（臉的 `AddColorUV` 有複製成功 (0, 0.627)；測試滑桿：U 往右變深、往左不變＝已在最淺欄；亮度要乘約 4 才接近、而且偏黃）→ **原因：遊戲角色模型的頂點顏色存的是綁定姿勢位置**（raw/255，檔案空間公尺：R = x/2+0.5、G = 高度/2、B = 前後/2+0.5、A = 1；用內衣和臉 100 萬個點擬合，誤差 0.001），shader 拿它算濕身／沾沙的高度線（`Use_VertexColor_Offset`）；我們沒有頂點顏色＝整個身體在地面高度＝又濕又沾沙 → `miquella_body.py` 的 `position_colors` 匯出時寫入（讀回驗證一致），測試滑桿已拿掉。→ 斑塊消失（使用者確認），但 SkinEdit 的皮膚還是比臉深約 3 倍、偏黃（亮度 ×3.3＋分通道校準仍「看得出差別」；臉的底色其實是偏青灰 161,179,181，膚色全來自 SkinMap）→ **改成身體直接用臉的材質**：`SKIN_SOURCE` = 女臉 `ch00_001_0000` 的 `face` 材質（臉的 shader 和貼圖），`face_patch_uvs` 把身體兩組 UV 平面投影到臉貼圖脖子前面一小塊乾淨皮膚 `FACE_PATCH`（u 0.40–0.60、v 0.15–0.22）；角色腳本每 2 秒把獵人臉 `face` 材質的**全部變數**（38 個 float4 依 `FLOAT4_VARS`、其餘 float；跳過 ObjectOffset／BB_Min／BB_Max／Ripple_Emit_Pos）複製到身體，`Skin tone`／`Skin brightness` 乘在臉的 ColorParam 上（config `skinVersion` 2 重設舊值）。→ **失敗、已退回**：更黑，而且模型被扭壞（臉的 vertex shader 依 UV 做捏臉變形，全身 UV 在脖子區就全身套脖子的變形）。**現在**：回到 SkinEdit，底色改成臉貼圖脖子的實際顏色 sRGB 161,179,181（偏青灰；之前的 152,152,157 偏紅才會偏黃），腳本只複製臉的 `AddColorUV`、`ColorParam` = `SKIN_BASE` 2.9（使用者校準 3.3 換算新底色）× 膚色選項 × 亮度。**pak 和腳本在等遊戲關掉才裝**；裝好後請使用者看膚色還沒做：胸口小凸起磨平、脖子底部深色接縫線、內褲顏色跟膚色太近另外：使用者角色是女性，髮型檔是 **`ch01_001_0512`**（女性版），做頭髮要用這個（之前解的是 `ch01_000`）
  1. 使用者在遊戲裡測：身體有沒有出現、原本的衣服有沒有藏起來、關節變形（膝肘肩不好看 → 權重改用遊戲的 `*_HJ_*` 輔助骨頭）、脖子轉頭／低頭、頭冠位置；挑 A／B／C
  2. 膚色材質（抄臉的皮膚材質，接縫看不出色差）
  3. 長袍：上半身和臀部貼身（照身體形狀，腹股溝線不能蓋平）、下擺擺動（學內衣的 `chain2`）
  4. **頭髮（設計定案 2026-10-03，使用者：「這樣蠻好的」）**：以遊戲髮型 **512** 為底（使用者發現它就是左右兩股往後合成大編髮＋中分長波浪到腰；結構見研究筆記第 14 節「遊戲髮型 512／513」）。定案內容（規格寫進 `DESIGN.md`「髮型」）：
     - **512 的長捲髮完全保留**，只加十幾條編髮（使用者：「米凱拉的髮型不是由大量細編髮組成」）
     - **背後 10 條細編髮**，寬約 1.4～1.8 cm（第一版太細很醜，加粗 1.5 倍），長短、間距不規則，約一半夾在散髮裡時隱時現，起點高低錯開（有的從扭轉髮束底下、有的從下面的散髮裡出來）
     - **左右肩前各一條粗編髮**，約 3 cm，跟後腦兩股側編一樣粗；從太陽穴／耳邊起，越過肩膀垂到胸前（比過「全部在背後」，使用者選肩前）
     - **大編髮保持原本粗細（約 5.4 cm）、只加長**到約 z 1.20，原版髮圈和髮尾移到新末端
     - **編髮起點要柔**：三股往上收尖、沉進散髮底下（像從頭髮裡收攏出來），頭 1.2 節從細鬆漸漸收緊；不要變寬的扇形（像紙片三角形）
     - 細編髮末端金色小髮圈＋蓬鬆髮尾（使用者沒反對，進遊戲後再確認）
     - 預覽 `MiquellaTools\work\previews\hair_mq\A_sheet.png`、`close_v4.png`（含卡普空模型，不進 repo）；腳本 `hair512_parts.py` → `hair512_braids.py A`（參數表 `BACK`、`FRONT`、`THIN_SCALE`、`ROOT_LEN`、`SINK`）
     - **下一步（進遊戲）**：①編髮改成遊戲用的髮片：UV 對到 512 的髮絲貼圖（編髮那一塊），起點髮束用貼圖的透明髮梢淡出；減面；②權重：背後細編髮綁到附近的 `back_hair01～05` 鏈，肩前粗編髮綁 `front_hair01／02`（或新增鏈），大編髮延長段延長 `Mituami_hair01` 鏈（要改 `chain2`，RE Chain Editor 或自己寫）；③匯出成 `ch01_000_0512` 的替換檔（改卡普空原檔＝灰色地帶，跟改色特效 pak 一樣，發布時使用者決定）或用腳本掛載；④頭髮微光（研究筆記 14：編髮用 `Base_Equip` 發光材質）
- **備案**：生成物件不行（狀態列寫 could not create）→ 改成覆蓋檔案（頭冠併進某款髮型 `ch01_000_00xx` 或內衣）

**不需要遊戲、隨時可做**：調整任何預覽、做新的設計提案、整理文件

---

## 10. 怎麼把工作搬到本機

**2026-10-01 已搬到本機**：使用者用 Claude 桌面版開了 `C:\Users\anton\ForClaude`。本機有 Python 3.11.9（還沒裝 bpy）、沒有 Blender；C 槽剩約 46 GB。以下是當初的搬家說明，留著備查。

雲端 session 碰不到使用者的電腦。要讓 Claude 直接操作遊戲資料夾、安裝工具、讀遊戲檔案，要在**使用者電腦上**開 Claude Code：
- Claude 桌面版（Claude Code），開這個 repo 的資料夾；或
- 在終端機：`git clone https://github.com/antony3911/ForClaude`，`cd ForClaude`，`git checkout claude/two-account-handoff-plan`，再執行 `claude`（或 `claude remote-control`，就能從手機的 Claude Code app 操作）
- 開好後跟 Claude 說：「讀 HANDOFF.md 接著做」。repo 根目錄的 `CLAUDE.md` 會被自動讀到

本機的注意事項：安裝程式可能跳 UAC，要人在電腦前按；Nexus 下載要登入，由使用者自己載

---

## 11. 其他背景

- 更早討論過：Max 5x 和兩個 Pro 的比較、雙帳號手動換手（用進度檔接手；不做自動換帳號工具）、Remote Control 設定 → 見 `notes/two-account-handoff-plan.md`
- 法環的 mod 工具也在那份清單裡（me3、Soulstruct for Blender 等），目前專案主力是魔物獵人荒野
