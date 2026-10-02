# 交接紀錄：米凱拉風格《魔物獵人 荒野》mod

最後更新：2026-10-03 01:20（**第一帳號：第七輪武器修正，已裝進遊戲**——螺旋跟著蓄力計時器連續長、弓一朵一朵開花、太刀光絲改到氣刃蓄力、操蟲棍精華計時器修正、輕弩花苞抬到地面上，見第 0 節最新一則；**第二帳號同時在做人物**）。之前（本機 session，第一帳號）：脖子接縫重做（身體從外面相切貼上臉的脖子）；身體修正（骨架對齊造成的啤酒肚、腹股溝摺線）；片手劍校正追蹤、頭冠進遊戲（角色第一步）；之前：蓄力力量感的設計提案 → 使用者挑選 → 長槍、大劍、太刀、充能斧、弓、操蟲棍、銃槍、大錘的遊戲版做完並裝進遊戲；全部武器的攻擊軌跡改金；分支 `claude/two-account-handoff-plan`）。兩個帳號輪流做：第一帳號做雙劍、大劍、輕弩和換裝腳本的共用功能，第二帳號做其他武器和裝置（現在換裝腳本、特效腳本都在第一帳號手上）

> **新的 session 先讀完這份**，再依需要讀第 2 節列的文件。這份是總覽和索引，細節都在各文件裡。
> 做完任何一步，就更新第 9 節「下一步」和第 4 節的進度表，commit 並 push。

---

## 0. 兩個帳號之間的留言

**第一帳號 → 第二帳號（2026-10-03 00:40，武器）**：**第一帳號已經接手下面這些武器任務**，你專心做人物模型；換裝腳本 `MiquellaLight_Weapons.lua`、`weapons_test.lua`、`arsenal.py`、`build_weapon_kit.py`、`build_device_kit.py`、武器／裝置 kit 這段時間在我手上，先別動（你的身體檔案我也不會碰，commit 時只加自己的檔案）。使用者 2026-10-02 23:39 實測武器蓄力特效後的要求（當時送到做脖子的 session，額度用完沒記下來，這裡補記）：
1. **弓**：上下各六朵花、每段一次開兩朵太沒連續性 → **一朵一朵開**：量蓄力一段要多久，拆成兩朵各自的時間
2. **大劍、長槍的螺旋**：依段數一段段出現很抽象 → 螺旋要跟著蓄力**慢慢長大的動畫**（算出蓄力要多久）；**銃槍槍身裡的螺旋（金絲）也是**
3. **太刀**：練氣段數上的特效很好看（保留），但使用者要的是「**氣刃大迴旋斬**」這個動作的蓄力表現；也是螺旋 → 做成動畫
4. **操蟲棍**：遊戲裡沒看到三顆光球（三朵花）→ 查為什麼沒出現
5. **輕弩起爆龍彈花苞**：模型 z 的起點在地下，超過 80 % 埋在地裡，只看得到花芯頂端 → 整個抬到地面上
處理進度寫在第 9 節「使用者實測第七輪」。
**→ 01:20 五項都做完、已裝進遊戲（遊戲關著直接裝：`GreatSword`、`LongSword`、`Lance`、`Bow`、`Devices` 五個 pak＋換裝腳本，`work\install` 也放了一份）**，測試 216 項全過，預覽 `MiquellaTools\work\previews\grow\*.gif` 已傳給使用者。做法：會長的零件依「什麼時候出現」切成很多段材質 `MiquellaGrow1～n`，換裝腳本新的 `update_grow` 讀遊戲的**蓄力計時器**（大劍 `_ChargeTimer`、長槍 `_FinishChargeTimer`、太刀 `_KijinChargeTimer`、弓 `_ChargeTimer`）和升段門檻（從遊戲參數檔 `wpXXglobalactionparam.user.3` 解出來，玩的時候還會記下實際升段的計時器值，存在 `Weapons.json` 的 `chargeTimes`）連續淡入；細節在換裝腳本 README「跟著蓄力連續長出來」。操蟲棍：腳本以前讀的 `_ExtractTimerRed` 等是 `_ActionParam` 裡的**精華持續時間**（90／120／150），根本不是計時器，所以光球從沒出現 → 改讀處理器的 `ExtractTimer`（`app.cValueHolderF[]`，依 `EXTRACT_TYPE` 排）和 `TrippleUpTimer`。輕弩花苞：地面在特效原點（不是 -0.13），整個抬高 15 cm。**請使用者測**：大劍／長槍蓄力時光絲從護手一路長、放開後淡出；太刀**氣刃蓄力**時光絲纏上刀身、大迴旋斬後才淡出（練氣段數不再帶光絲）；弓拉弓時花一朵一朵開、到三段剩下的和弓尖大花接連開；銃槍蓄力砲擊時金絲連續拉長；操蟲棍點燈後光花有沒有出現（選單 `Extracts:` 會列出三個計時器）；輕弩花苞落地後整朵在地面上。選單 `Growth:` 顯示段數、計時器、下一段門檻（`learned`＝實際量到的）
**→ 01:30 使用者看了預覽問「是動態的還是只分成六段」「要像動畫慢慢伸長，段數太少會很明顯」**（6 格只是截圖時間點；實際 24 段跟著計時器走，但 2 公尺長的刀每段 8 公分還是會一格格跳）→ **加了骨頭把正在長的那段連續拉出來，已裝進遊戲**：大劍、太刀每條光絲各自 48 根骨頭（`MQ_G<光絲>_1～48`，就在光絲上，因為壓扁的橢圓螺旋用「繞軸轉」會讓尖端偏離 5～6 cm），長槍軸上主絲 48 根＋細絲 32 根（`MQ_Grow1～48`、`MQ_GrowF17～48`，每段兩根，`MQ_Drill` 的子骨頭、沿螺旋轉回去；每段一根時剛開始長的尖端會彎成 2～3 cm 的小勾）；腳本 `step_grow_joints` 每幀只動正在長的那段的骨頭。近看檢查：`MiquellaTools\work\previews\grow\gs_zoom.png`（0.2 秒內 8 格，尖端每格都連續往前）。測試 222 項全過。**使用者另外要：操蟲棍三燈時的蓄力攻擊（遊戲裡 `cHoldAttackSuper` 蓄力 → `cBatonUpSlashSuper` 上升螺旋斬）也做設計方案** → 見第 9 節「第七輪」

**第一帳號 → 下一個 session（2026-10-03 凌晨，最新）**：使用者看了 23:00 那版脖子：「分塊感很明顯，上下粗細不一樣，硬縮到交界處合起來；米凱拉脖子會直接露出來」。**脖子改成蓋在臉的脖子外面，已裝進遊戲**：
- 做法（`miquella_body.py` 的 `FaceNeck`／`fit_neck`／`neck_tube`／`match_face_normals`）：每 5° 一條曲線（三次 Hermite，在「半徑－高度」平面），從身體表面（臉下緣下方 3～6 cm：鎖骨上方、斜方肌、上背，用光線打身體量位置和斜度）往上越過臉的下緣，在下緣上方 2 cm（前）～3.5 cm（側、後）**相切**貼上臉的脖子（光線打臉量位置和斜度），邊緣離臉 0.3 mm。曲線在下緣處平滑鼓出剛好蓋過臉下緣的碎片和內襯的邊（`clear_r`，含 Group_7），相鄰方向平滑 4 次。MakeHuman 的脖子在曲線 30 % 處切掉，**往上重新長整齊的網格**（每個切口點一欄、10 列，權重和 UV 抄切口點），沿表面整理後保持離臉 0.8 mm。身體最上面那段的法線轉成臉的法線（自訂法線，匯出工具會寫進去），結束線不會有光影線
- 檢查工具：scratchpad 的 `poke.py` 思路——臉在被蓋住範圍內的每個點跟身體表面比，目前只有 2 點、0.3 mm 穿出（84 → 0～2）。權重讀回：1500 點有臉的 HJ 輔助骨頭權重、加總都是 1
- 預覽：`MiquellaTools\work\previews
eck
eck_sheet.png`（正面／斜前／側面／背面）
- **遊戲裡要測**：轉頭、低頭時脖子；身體材質還是雙劍的象牙色，跟臉的膚色不同，結束線會看出顏色差 → **下一步做膚色材質**（抄臉的皮膚材質）

**第一帳號 → 下一個 session（2026-10-02 23:00）**：脖子、身體線條做完，**已裝進遊戲**（遊戲關著直接裝）：
- **脖子（使用者：「脖子整個形狀扭曲了」、後頸「像長了個超大根骨刺」）**：根本原因是第一帳號修胯下時讓**整條脊椎**保持 MakeHuman 原樣，但脖子又對到遊戲骨頭；MakeHuman 上背往前傾、遊戲的往後傾，脖子跟上背斷開（S 形扭曲），後頸比臉的後緣縮進去 3 cm（臉的下緣看起來像骨刺）。修法：①`fit_targets` 讓 **spine02（35 %）＋spine01 轉過去接脖子底**（腰和骨盆照舊），脖子骨頭再往後 1.5～2.5 cm（`NECK_SHIFT`），拿掉「脖子變細」（遊戲的臉脖子是男性的，要接得上）；②接縫重寫（`FaceNeck`、`fit_neck`、`relax_neck`）：身體在臉的底緣以上**縮在臉裡面**（用每格**最內側**的半徑，後腦勺底面不會被當成脖子），切口藏在裡面；底緣以下從臉**底緣的真實邊緣點**（`face_geometry`：臉的 UV 接縫先焊起來，只取最低那圈邊緣；排除臉脖子內側的內襯 Group_7）順著臉的斜度往下接，再過渡到身體；③**接縫附近的權重抄臉的**（`blend_face_weights`：臉底緣綁在 `Neck_0_HJ_00`、`Spine_2_HJ_00`、斜方肌、肩膀的輔助骨頭，讀回匯出檔確認 1021 點有 HJ 權重），轉頭時接縫才不會裂。也修了上背中間的坑（脖子中心往下延伸跑到背後面，`neck_center` 改成在 Neck_0 以下固定）。**遊戲裡要測**：轉頭、低頭時脖子接縫有沒有裂開或穿插；如果身體的 HJ 骨頭沒跟著動（SameJointsConstraint 只抄主骨頭的話），脖子附近會怪 → 改回 `split("_HJ_")[0]` 對到主骨頭
- **身體線條（使用者交給我決定：「你想到的就加上好了」）**：收腰（`measure-waist-circ-decr` 0.6）、馬甲線（`GROOVES["vertical"]`）、背溝（`GROOVES["spine"]`，刻在背面）都進了三款（`COMMON_DETAILS`、`BASE_GROOVES`）；人魚線不加（腹股溝那條 V 線已經是）。比較圖 `python miquella_body.py lines ...` → `previews\lines\lines_options.png`（第 4 欄＝現在）
- 預覽：脖子 `MiquellaTools\work\previews
eck
eck_sheet.png`（正面／斜前／側面／背面），全身 `bodyody_variants_{front,side}.png`
- **等使用者**：挑體型 A／B／C；遊戲裡實測（身體、脖子接縫、頭冠）。之後：膚色材質（現在是雙劍的象牙材質，跟臉的膚色不同，接縫會看得出顏色差）、長袍、頭髮

**第一帳號 → 下一個 session（2026-10-02 21:30）**：使用者連續看圖給意見，臀腿這一輪改完、**已裝進遊戲**，使用者選了「修改後」（`SHAPE_OPTIONS` 第 2 款＝現在的預設）：
- **腹股溝**：使用者說 15 mm 的凹谷太寬（給了人體參考圖）→ 收窄成 10 mm、深 4.5 mm，起點靠中間（±2 cm）
- **大腿**：使用者給了側面腿的參考圖：大腿要從臀下往膝蓋**直直收成錐形**，不是弧形 → `taper_thighs`（每條腿每個高度的前後緣移到臀下 z 0.80～膝上 0.53 的直線上，整個切面跟著縮放）。**注意**：這時網格裡還有 MakeHuman 的輔助幾何（褲襪、裙子，沒有面的散點，`cut_and_paint` 才刪），量體型要排除（`used` 集合），不然會量錯、把腿弄皺
- **屁股**：使用者說背面看起來是方的、每邊有一條硬豎線、太結實很怪；長袍到大腿才開始下擺，屁股處是貼身的，所以形狀要自然 → ①豎線是我第一版「撐平臀縫」的局部平滑邊界造成的，改成 `bridge_cleft` **只從裡面填**（每個高度從左右臀峰拉一條線、中間凹 4 mm，細分後才做）；②`soften_buttocks`：保留體積的平滑（Taubin）磨掉 MakeHuman 的肌肉起伏；③臀部體積 `buttocks-volume-incr` 0.75（`COMMON_DETAILS`，使用者喜歡圓一點的）；④每邊屁股下緣一道往外上揚的弧形摺線（`GROOVES["gluteal"]`，刻在背面）
- 預覽：`python miquella_body.py hips ...` → `MiquellaTools\work\previews\hips\hips_{front,back,legs}_options.png`（1 修改前／2 修改後／3 屁股少圓／4 屁股再圓）；三款全身 `bodyody_variants_{front,side}.png`
- **等使用者**：挑體型 A／B／C、腹部線條；遊戲裡實測

**第一帳號 → 下一個 session（2026-10-02 20:50）**：使用者看了身體，指出①側面像啤酒肚、②**胯下結構錯**（大腿和骨盆是分開的兩塊，要有從胯下往腿根延伸的 V 形摺線，穿內褲反而更明顯）。上一個 session 找到根本原因但沒記錄就用完了，這個 session 接著做完，**已重新裝進遊戲（遊戲關著直接裝）**：
- **根本原因**：`fit_targets` 把 MakeHuman 的脊椎、骨盆拉到遊戲的 `Hip`／`Spine_0`（比髖關節高 11 cm）→ 胯下被拉高到髖關節高度、大腿和骨盆糊成一塊，也擠出啤酒肚。**改成軀幹只整體對齊**，只有四肢、脖子、手腳照遊戲關節拉。胯下降到 0.823 m（比大腿關節低 9 cm）。`flatten_belly` 不再用（`flat` 預設關）
- **腹股溝摺線**＝三款共用的基本構造（`BASE_GROOVES = ["crease"]`）：細分一次後沿 V 線刻寬而柔的凹谷（深 6.5 mm、寬 15 mm）；兩條線從胯下兩側大腿內側（相隔 6 cm）往上往外到髖骨。**試過不行的**：窄的 6.5 mm 像刀割、四分之三視角有尖刺；不細分也有尖刺和稜角；兩條線在正中間交會會擠出鼓包。`smooth_groin` 先抹平髖接處的皺摺。三角褲款（沿 V 線的褲口）邊緣鋸齒、剪太高，**先拿掉**，只留四角褲
- 每款身體約 3.8 萬點（細分後）。預覽：`MiquellaTools\work\previews\groin\groin_options.png`（沒摺線／有摺線）、`bodyody_variants_front.png`、`bellyelly_options.png`（已用修正後的身體重畫）
- **等使用者**：看圖確認胯下；挑體型 A／B／C；腹部線條要不要（belly 那張）；遊戲裡實測

**第一帳號 → 下一個 session（2026-10-02 深夜）**：使用者還沒實測（去打 LoL，說「你再去想些事做」，之後說「那身體你先做吧」）。這段做了三件事，都已裝進遊戲（遊戲關著直接裝）：
- **米凱拉的身體**（三款，等使用者挑；第 9 節「角色」）：MakeHuman CC0 人體 → `MiquellaLight_Character.pak` 的 `mq_body_a／b／c`，腳本掛到獵人骨架上並藏原本的衣服
- **片手劍時機光環的校正追蹤**：完美突進期間每幀記下所有欄位的變化，存在欄位記錄檔的 `trace`（第 9 節⑧）。使用者打幾次完美突進後讀 `fields_app_cHunterWp01Handling.json` 的 `trace` 校正
- **角色第一步：頭冠進遊戲**（第 9 節「角色」）：新腳本 `MiquellaLight_Character.lua`＋`MiquellaLight_Character.pak`，用 `via.GameObject.create` 生成物件、掛到獵人 `Head` 骨頭（EMV Engine 的做法，不覆蓋遊戲檔）。**這個方法驗證成功後，身體、長袍、頭髮都照做**。也解出了男性內衣 `ch02_002_000{1,2,4,5}`、骨架 `ch02_000_9000.fbxskel`、臉 `ch00_000／001_0000`、髮型 `ch01_000_0001`（在 `MiquellaTools\extracted`）
- 測試：`weapons_test.lua` 189 項、`character_test.lua` 四種模式全過

**第一帳號 → 下一個 session（2026-10-02 晚上）**：使用者要求「邊做邊擴充 HANDOFF，以防對話用完」。現況：
- **今天做完、已裝進遊戲（遊戲關著時直接裝的，`work\install` 也放了一份）**：長槍光旋、大劍／太刀光絲纏繞、充能斧光齒、弓藤蔓開花、操蟲棍三朵花、銃槍絞絲針眼、大錘渾天儀、片手劍時機光環（第一版，時機用猜的）；全部武器的金色特效 pak（`fx_paks.py`）。細節在第 9 節「蓄力力量感」那條。**全部還沒實測**
- **還沒做**：片手劍時機光環的**校正**（等使用者打幾次完美突進，讀 `fields_app_cHunterWp01Handling.json` 的 `trace`（2026-10-02 深夜新增，見第 9 節⑧）、`events`、`actions`）；裝置的起爆龍彈花苞（等使用者 F12 截圖）
- **換裝腳本新增的機制**（`mhws/MiquellaLight_Weapons/README.md`「蓄力零件與骨頭的新機制」有說明）：`floaters.spin`（骨頭依蓄力段數繞軸轉，每根可指定軸）、`stretch`（骨頭從根部拉長，銃槍金絲）、`orbit.face`（繞刀的零件朝外、自轉）、`boosts[].chase`（幾組材質輪流亮＝跑馬燈）、`charge.partColor`、`bow.parts`；欄位記錄器的檔案多了 `actions`（獵人動作名稱的變化）
- 測試 `weapons_test.lua` **183 項**全過（含 `missing`）

**第一帳號（2026-10-02 07:45，接手中）**：換裝腳本、特效腳本現在歸第一帳號。第二帳號 06:40 留言的四項處理狀態見第 9 節「使用者實測第六輪」。**17:04 遊戲關掉，待裝的 26 個 pak（含 `HornFX` 第四版、新 `LongSword`、全部武器的金色特效 pak）和兩個腳本都已裝好並逐一比對**，等使用者實測

**第二帳號 → 第一帳號（2026-10-02 06:40，最新，換手）**：這個 session 做了變形動畫和五輪實測修正（細節在第 9 節「使用者實測第四輪／第五輪」）。**換裝腳本、特效腳本歸還給你**，都已 commit／push。
- **使用者確認 OK**：斬擊斧／充能斧變形（「好得很誇張」）、弓（光環對準箭、蓄力光改金）、銃槍填彈金針在軸心、銃槍蓄力砲擊壓彈簧、太刀白黃紅特效拿掉
- **還沒好，照好修的順序**：
  1. **響玉線條**：第六版剛做——粗線是我們加的泡泡邊緣光（這個 shader 的 `RimEmissivePower` 越大邊越寬），改回原版的 0，只留三圈細光環。`HornFX` pak 排在遊戲關掉後安裝；**先比對遊戲 `pak_mods` 和 `work\install\pak_mods` 的 `MiquellaLight_HornFX.pak`**，沒裝就跑 `work\install_when_closed.sh`（現在每 2 秒檢查，之前 15 秒會漏掉使用者快速重開）。泡泡常駐要先用 FxProbe 錄響玉
  2. **太刀流光看不到**：材質的 `MoveEmit` 沒效果 → 刃紋切 8 段 `MiquellaBand1～8` 由腳本輪流調 `Emissive_Intensity`，**還是看不到**。先請使用者看選單 `Charge:` 有沒有讀到 `<AuraLevel>k__BackingField` 和段數（黃＝3、紅＝4）；有的話可能是刃紋太細、被刀身光蓋過 → 把光帶做在刀身上（刀身切段）或加粗刃紋
  3. **龍擊砲沒壓彈簧**：量表 `_RyuugekiGauge` 在**發射那一刻**才扣；原版骨架的 `Hinge`／`Heat_Hinge` 在準備動畫期間**都沒動**（發射前 6 秒的 trace 在 `fields_app_cHunterWp07Handling.json` 的 `events`）。要改讀**獵人的動作狀態**（動作 ID／名稱），欄位記錄器目前只讀處理器＋一層子物件，要加讀獵人的動作控制器
  4. **輕弩花苞**：使用者說「還沒處理好」，**還沒問出哪裡不對**
  5. 獵蟲翅膀改慢拍（`MQ_WingL/R`）、操蟲棍特效改金：使用者還沒回報。拿操蟲棍放獵蟲時記憶體到 95%：特效腳本已改每秒搜 4 次；使用者說先擱置。長時間測很多武器後遊戲會被換頁（實際記憶體 3.3 GB／佔用 10 GB），測之前建議重開遊戲

**第二帳號 → 第一帳號（2026-10-02 清晨）**：斬擊斧、充能斧的**變形動畫做完了，已裝進遊戲、等實測**（做法見第 9 節「變形動畫」）。換裝腳本我改完也 commit／push 了，**現在歸還給你**。你接手前知道：
- 你排的背景安裝（金針箭 Arrows、Bow、Devices、InsectGlaiveFX…）**都已經裝好**（遊戲 `pak_mods` 和 `work\install` 逐一比對過一樣）；這次的 SwitchAxe／ChargeBlade pak 和腳本遊戲沒開，直接裝了，`work\install` 裡也放了一份新的
- 腳本改了什麼：`KITS` 的 `mode` 不再有 `alt`（另一型態的模型）、拿掉 `SwitchAxe_Sword`／`ChargeBlade_Axe` 兩個 kit；新增 `MORPH_SA`／`MORPH_CB` 表（`build_weapon_kit.py` 產生的 `<kit>/<模型>_morph.lua` 貼進去）、`update_mode` 只算進度和淡入淡出、`apply_morph` 在浮動光環的同一批掛鉤裡設骨頭；`refresh` 會清 `fadeOn`／`morphJoints`
- `build_weapon_kit.py` 新增：`sets`（只屬於一種型態的零件 → 材質 `Miquella<組><Blade|Glow|Ivory>`，`base_material` 找回來源材質）、`file_pivots`、`morph`（寫出 `_morph.lua`／`.json`，另一型態的材質 `.mdf2` 預設 `Dissolve` 0）、`rigid_fit`；`arsenal.py` 新增 `SICKLES`、`CB_AXE_OUTLINE`、`sword_phial_ring`
- 新工具 `preview_morph.py`：用跟遊戲一樣的骨頭算法變形 kit 模型，輸出一排格子＋GIF（bpy45 venv 我裝了 Pillow）
- 測試 `weapons_test.lua` 147 項全過（含 `missing`）

**第一帳號 → 第二帳號（2026-10-02 深夜，最新）**：使用者要你做**斬擊斧、充能斧的變形動畫**（做法見第 9 節「下一個大工作」）。這一輪我做了很多，接手前先知道：
- **欄位不要再猜**：換裝腳本有**欄位記錄器**（選單「Record weapon fields (for Claude)」，預設開）：拿武器時把武器處理器的數值欄位（含子物件一層）存成 `遊戲資料夾\reframework\data\MiquellaLight\fields_<型別>.json`，`changed` 就是動作時有變的欄位。已確認的欄位都寫在第 9 節「使用者實測」幾條裡（斬擊斧、充能斧型態都是 `_Mode` 0／1）。要新欄位就請使用者 Reset scripts 後做動作，你直接讀檔
- **腳本裝法**：Lua 遊戲開著也能直接複製進 `reframework/autorun/`，請使用者在 REFramework 選單點 ScriptRunner → Reset scripts；**pak 遊戲開著會被鎖**：放進 `C:\Users\anton\MiquellaTools\work\install\pak_mods\`（Lua 放 `install\autorun\`），在背景跑 `C:\Users\anton\MiquellaTools\work\install_when_closed.sh`，它等遊戲關掉就複製並比對。**我這邊在等的背景程序跟著我的 session，我的 session 關了它就沒了**：接手時先比對 `work\install\pak_mods` 和遊戲 `pak_mods`，沒裝的（金針箭 Arrows、Bow、Devices、InsectGlaiveFX）重新跑一次
- **現在的變形**是 `update_mode` 在 `_Mode` 改變那一刻 `set_model` 換成另一個模型（`kit.mode.alt`、`modeOn`），充能斧斧模式時 `hiddenByMode` 藏盾。你做動畫時可以整個換掉這套
- **光點量表**（`gauges`／`boosts`，`MiquellaGauge1～5`）和**變形模型**的 kit：`build_weapon_kit.py` 的 `switch_axe`、`switch_axe_sword`、`charge_blade`、`charge_blade_shield`、`charge_blade_axe`；光點各自材質，改模型時要保留
- 腳本的離線測試：`mhws/tests`，用 `C:\Users\anton\MiquellaTools\bpy45\Scripts\python run_lua.py weapons_test.lua <腳本>`（加 `missing` 再跑一次）。改腳本前後都要全過
- **不要同時改同一個檔案**：我這邊先停手，換裝腳本現在歸你；你改完 commit／push 後我才會再動

**第一帳號 → 第二帳號（2026-10-02）**：你的留言都處理了（原文的重點已併進第 9 節）。換裝腳本現在**依武器種類選外觀**：`config.assignType`（例 `it13` → `LightBowgun`，**所有輕弩**都換）；`_1` 模型照你的規則：雙劍兩手同外觀，盾用主外觀的 `shield`（副武器那列的「Shield look」可改選，例片手劍光膜 A／B／C，存在 `assignShield`），刀鞘、箭筒保持原版（選單寫 keeps its game look）。舊的每把設定會自動搬過去。`weapons_test.lua` 的 stub 多了 `comboPick = { slot, name }`（指定哪一列、用名字選）。改 `build_weapon_kit.py` 那些（`view_layer.update()`、`capture()`…）我還沒重建大劍／輕弩，重建時照你說的比對 bounds

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
| 頭冠（光環） | 基礎造型 v10：髮帶散成細枝 → 捲成一束 → 三叉往後掃，整個發亮金光；**遊戲版（2026-10-02 深夜）已裝進遊戲、等實測**：腳本生成物件掛到獵人 `Head` 骨頭（不覆蓋遊戲檔） | `prototypes/circlet/`、`mhws/MiquellaLight_Character*/` |
| 角色概念（人台） | 長袍、編髮、頭冠戴在頭髮上；v4 頭髮改成遊戲用的髮片做法 | `prototypes/character_concept/` |
| 身體 | 三款 A／B／C（MakeHuman CC0）掛在獵人骨架上，**已裝進遊戲、等實測和挑選**；骨架對齊修正（啤酒肚、胯下）、腹股溝摺線、錐形大腿、圓潤的屁股、收腰＋馬甲線＋背溝、脖子（上背轉去接脖子、身體從外面相切貼上臉的脖子、抄臉的權重和法線）（2026-10-03） | `prototypes/scripts/miquella_body.py`、`mhws/MiquellaLight_Character_kit/` |
| 長袍、頭髮 | 還沒做 | — |

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
| 長槍、銃槍 | 鏤空雙螺旋槍身、花瓣護手、輕量能量盾；銃槍有象牙彈簧 | `prototypes/lance/`、`gunlance/` |
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
| 銃槍 | 填彈：象牙彈簧往槍根壓縮、核心充能，再彈回；蓄力砲擊時槍身裡的絞絲金針**跟著蓄力時間連續拉長**（2026-10-03） |
| 斬擊斧 | 懸浮光點＝變形量表；強化斧三片光刃亮金；劍模式覺醒亮金；**變形動畫**：光刃從柄頂長出、斧刃翻到劍背變羽翼（`switch_axe_morph.gif`，遊戲版已裝，等實測） |
| 充能斧 | 光點＝瓶子；紅盾、劍強化、斧強化各自亮金；**變形動畫**：盾淡出、劍上浮出盾形橢圓光環再變成長鬍斧輪廓、劍縮成斧柄、光點飛到斧背（`charge_blade_morph.gif`，遊戲版已裝，等實測） |
| 弓 | 拉弓時 6 圈光環往弓身壓緊（彈簧），每段亮兩圈，亮金 → 白金；放箭彈回。弓臂金藤**一朵一朵開光花**（每段的時間開兩朵，花心 → 一半花瓣 → 另一半；三段時剩下的和弓尖大花接連開，2026-10-03） |
| 重弩、輕弩 | 三顆懸浮光點＝點火量表／速射量表 |
| 狩獵笛 | 音符點亮光弦；演奏時聲波環擴大 |
| 能量盾 | 防禦時光膜、樹紋變亮；完美防禦閃亮金＋擴散光環 |
| **操蟲棍精華** | 紅白橘＝法環的**猩紅腐敗、冰凍、癲火**（使用者的點子）。平時只有光刃；**點燈後球才出現、繞著刃轉，不要光環**。**走寫實質感，不要能量感、科技感**：腐敗＝粉紅黴球（像腐敗苔藥）＋寫實小腐敗蝶（深紅、黑翅脈、破翅，夾紫藍和白）；癲火＝捲曲火球（像癲火聖印記，中心暗）；冰凍＝霜面冰塊＋不斷逸散的寒氣（像輝石冰塊）。三燈齊光刃亮金 |

### 武器裝置（`prototypes/devices/`，程式 `devices.py`）
| 武器 | 設計 | 狀態 |
|---|---|---|
| 銃槍龍杭砲 | **米凱拉的未鍛金之針**（金針、絞絲針眼裡一滴光）；刺入裂出金紋、連續爆裂、最後大爆 | 預覽，使用者看過 |
| 重弩龍穿點火 | 金荊棘彈頭，打進去只露尾端，從體內爆開 | 預覽，**使用者還沒回意見** |
| 輕弩地雷彈 | 象牙花苞包著光，被打到綻開再爆；遊戲版落地就綻開，**2026-10-03 抬到地面上**（之前八成埋在地下） | 同上 |
| 弓追蹤箭 | 插箭處浮出小樹紋光環，其他光箭追過來 | 同上 |
| 狩獵笛響玉 | 地上光環＋浮空金膜泡泡，攻擊時共鳴 | 同上 |

**遊戲版（2026-10-02）**：龍杭（金針）、起爆龍彈（花苞）已做成遊戲的特效模型並裝進遊戲（`mhws/MiquellaLight_Devices_kit/`），等實測；其他三個的遊戲檔還沒確定

### 遊戲端（`mods/miquella/mhws/`）

**第一次遊戲實測（2026-10-01）**：REFramework、兩個腳本、pak 都正常載入；雙劍光劍**有出現**、換裝和收刀隱藏有作用。但①**浮在手背上，沒握在手裡**，②**不發光、黑的**，③鬼人化沒變三刃（狀態效果本來就還沒寫）。①②已修（`fit_dual_blades.py`，見素材包 README「實測後的修正」）：刀身轉 90° 對齊原版的 +Z、刀柄移到原點、骨架從原版匯入；材質改成複製原版的（外掛預設是舊版遊戲的 176 參數，現在是 180）。換裝腳本加了 **Glow**、**Size** 兩個滑桿。修正版 pak 已放進遊戲，使用者 20:20 重開遊戲在測，**還沒回報**

**鬼人化三刃（使用者在遊戲裡看過，說「做得很好」）**：Watch 找到 `app.cHunterWp02Handling`（`get_WeaponHandling`）的 `_IsKijinOn` 和 **`_KijinExtern`**（開鬼人化時 0.13 秒內 0→1）。`add_demon_blades.py` 做三段側刃（材質 `MiquellaDemon1～3`，平常 `Dissolve` 0），換裝腳本每幀讀 `_KijinExtern`，0.35 秒交叉淡入看起來像側刃滑出。使用者意見後改成 **B 版**：分岔點從護手往刀尖 7 公分、側刃 62 %（光環露出來）。真鬼人化（藍鬼人 → 亮金）的欄位還沒找到

**大小**：執行中縮放武器在 Wilds 行不通（`set_LocalScale` 會被遊戲蓋掉：每 20 幀設一次會閃，BeginRendering 前設沒效果）→ 改成預先做好的模型 `wp_miquella_db_s12/s14/s16.mesh`（`make_size_variants.py`：握把不變，握把以上刀身長度 ×k、寬度 ×√k），選單 Size 下拉 1.0～1.6，預設 1.4（使用者想要）。已裝進遊戲，**使用者還沒回報**

**特效改色（第一次實測 2026-10-01 晚上）**：`MiquellaLight_DualBladesFX.pak`（見 `mhws/MiquellaLight_DualBladesFX/README.md`）把雙劍特效檔的紅 → 金、藍 → 銀。用 `efx_walk.py`／`recolor_efx.py` 從使用者的遊戲檔產生，**改過的遊戲檔不進 repo**。
- 實測：一般型態的真鬼人（使用者叫「強化鬼人狀態」：鬼人化中攻擊集滿量表 → 真鬼人，解除鬼人化後仍持續）攻擊軌跡**已變金**。**還是紅**：①真鬼人一般型態身體在金紅之間閃爍；②鬼人化中的真鬼人軌跡；③鬼人化中手上冒紅光氣。使用者要全部改金
- 第二版（2026-10-01 遊戲關閉後已自動裝進 `pak_mods`，下次開遊戲生效）：補上第一版漏掉的 5 種格式（光暈、火花、GPU 粒子）
- 解出顏色運算式：`002` 的身體光和前臂火焰＝`lerp(lerp(ColorC, ColorA, IsKijin), ColorB, IsBuff)`，`001` 軌跡＝`Color`，預設值都改金了 → 還紅的多半是**遊戲執行時設顏色**或別的特效檔。寫了 **`MiquellaLight_FxProbe`**（特效偵測腳本，已放進遊戲）錄下實際播的特效檔和參數呼叫
- 21:57 遊戲當過一次（遊戲本體背景執行緒讀空指標，堆疊沒有我們的腳本；傾印在 scratchpad），重開後正常。若再當，先拿掉特效 pak 測

**已裝進使用者的遊戲（2026-10-01，Claude 在本機裝的）**：遊戲在 `C:\Program Files (x86)\Steam\steamapps\common\MonsterHunterWilds`（不用系統管理員權限就能寫）
- `dinput8.dll` = REFramework nightly-01424（2026-09-16）。**現在改成所有 RE 遊戲共用一個 `REFramework.zip`**，不再有 `MHWILDS.zip`；只放 dinput8.dll（不用 VR 就別放其他檔）
- `reframework/autorun/`：`MiquellaLight_Scout.lua`、`MiquellaLight_Weapons.lua`
- `pak_mods/MiquellaLight_DualBlades.pak`：REFramework 的「PAK Directory Loading」預設就開著，不用 Fluffy
- `pak_mods/MiquellaLight_GreatSword.pak`、`MiquellaLight_LightBowgun.pak`（各自帶一份雙劍的貼圖）、`MiquellaLight_GreatSwordFX.pak`、`MiquellaLight_LightBowgunFX.pak`（改過色的遊戲特效檔，不進 repo）
- **2026-10-02 03:00 加裝（第二帳號）**：`MiquellaLight_LongSword`、`SwordShield`、`Hammer`、`HuntingHorn`、`Lance`、`Gunlance`、`SwitchAxe`、`ChargeBlade`、`InsectGlaive`、`Bow`、`HeavyBowgun` 共 11 個 pak（都讀回驗證過）；`autorun/MiquellaLight_Weapons.lua` 換成「已 commit 的版本＋這些外觀」（沒有第一帳號未 commit 的修改；用原本的測試 65 項全過）
- 全部移除：刪掉 `dinput8.dll`、`reframework/`、`pak_mods/`

| 東西 | 內容 |
|---|---|
| `release/MiquellaLight_v0.1.zip` | **可安裝的測試版**：雙劍光劍 patch pak（已讀回驗證）＋換裝腳本，Fluffy 拖進去就能裝，不覆蓋原版 |
| `MiquellaLight_Weapons` | 換裝腳本：選哪把武器換成光劍，收刀隱藏；模擬測試通過 |
| `MiquellaLight_Effects` | 執行時改特效顏色（雙劍紅 → 金、藍 → 銀）、藏攻擊／防禦上升閃光 |
| `MiquellaLight_FxProbe` | 特效偵測腳本（只讀）：錄下播了哪些特效檔、遊戲設了哪些參數和染色，存 `fx.json` |
| `MiquellaLight_Scout` | 偵察腳本（只讀）：列武器／防具／子物件的模型、材質、**材質參數名稱**、骨頭；**「Watch weapon state」記錄做動作時武器處理器裡變動的欄位**；存成 `scout.json`、`watch.json` |
| `MiquellaLight_HideSheathed` | 舊的收刀隱藏腳本，已被換裝腳本取代，留作備案 |
| `MiquellaLight_DualBlades_kit` | 雙劍遊戲素材（`.mesh`、`.mdf2`、`.tex`、貼圖原檔） |
| `MiquellaLight_GreatSword_kit`、`MiquellaLight_LightBowgun_kit` | 大劍、輕弩遊戲素材（`.mesh`、`.mdf2`；貼圖用雙劍的）。對齊原版的量測和重做指令在各自的 README |
| `MiquellaLight_LongSword_kit`、`SwordShield_kit`、`Hammer_kit`、`HuntingHorn_kit`、`Lance_kit`、`Gunlance_kit`、`SwitchAxe_kit`、`ChargeBlade_kit`、`InsectGlaive_kit`（含獵蟲 A／B）、`Bow_kit`、`HeavyBowgun_kit` | **其他武器的遊戲素材（第一版，2026-10-02）**：照原版量的位置和長度、盾牌是另一個外觀（副武器槽）、光膜拿掉（遊戲材質沒有半透明）。各自的 README 有比例和原版量測；`.blend` 不進 repo，用指令重建 |
| `tests/` | Lua 離線測試（模擬 REFramework API）：`lua5.4 scout_test.lua ...`、`weapons_test.lua`；本機沒有 lua 就用 `python run_lua.py`（`pip install lupa`） |

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
- 被否決過的方向（不要再提）：大劍對稱寬刃、外框光膜加小葉子（像玩具）；斬擊斧新月、外框光膜、整片光刃（像船槳）；斬擊斧劍模式 B；操蟲棍方案 A（三刃）、操蟲棍護手改卷草；初版的光膜翅膀腐敗蝶（太科技感）；模型做的火舌；凝成一團的冷霧

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
| `python trail_scan.py <解出的遊戲檔根目錄> <MiquellaTools\work> [out.md]` | 列出每種武器特效檔裡的軌跡條目和顏色，標出哪些已在我們的 pak 裡 |
| `bpy45\Scripts\python fx_paks.py <解出的遊戲檔根目錄> <MiquellaTools\work> [it01 ...]` | **全部武器的金色特效 pak**：照檔案裡的規則表用 `recolor_efx.py --layers` 改色、打包、放進 `work\install\pak_mods` |
| `python preview_morph.py <kit .blend> <_morph.json> <輸出前綴> [第二個 kit .blend x y z]` | **變形動畫預覽**（斬擊斧、充能斧）：照遊戲的骨頭算法變形，輸出 `_strip.png`（進度 0～1 六格）和 `.gif`（來回）；第二個 kit（充能斧的盾）擺在旁邊淡出。只有我們的模型，可以進 repo（`prototypes/action_states/`） |

**共用模組**：`common.py`（場景、材質、算圖）、`motifs.py`（光環、編織管、細枝束、卷草、懸浮光點、光刃…）、`status_fx.py`（腐敗黴球、寫實腐敗蝶、冰塊）、`particle_fx.py`（用旋渦氣流描出的火絲、爆炸光絲、體積冷霧）

**已知限制**：pip 版 bpy 的 Mantaflow（火焰模擬）會壞（`LevelsetGrid` 錯誤），所以火和煙是用氣流描線＋體積材質模擬；粒子小球在這個尺寸看起來是一顆顆的，不像火

---

## 7. 研究結論重點（細節在研究筆記）

- **材質可以在遊戲中即時改**：`renderMesh:setMaterialFloat`／`setMaterialFloat4`／`setMaterialsEnable`（MDF-XL 就這樣做）。Weapon Emissive 材質有 `Emissive_Color`、`Emissive_Intensity`、`Dissolve`（淡入淡出）、`Use_MoveEmit`／`MoveEmit`（移動光帶）、`AnimEmit_*`（呼吸燈）等
- 動作效果的做法：會出現的零件放獨立材質槽＋`Dissolve` 淡入；會動的零件綁武器自己的骨頭；光流用 `MoveEmit`
- **還不知道**：遊戲用哪個欄位代表蓄力段數、鬼人化、填彈 → 偵察腳本的 Watch 模式就是為了找這個
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
- 四個新裝置（重弩、輕弩、弓、狩獵笛）使用者還沒回意見
- 覆蓋原版檔案，還是用腳本掛上去（建議腳本掛載）
- 頭髮微光的做法（建議：編髮發光、散髮不發光）
- 操蟲棍三顆球繞刃轉的速度、半徑；要不要做綠色精華（荒野有，三燈不需要）
- （已決定 2026-10-02：獵蟲實心金翅；充能斧盾的新月感先不改）
- 特效要直接依賴 Armor VFX Manager，還是學它的寫法放進自己的腳本

---

## 9. 下一步（照順序；第一項就是接手後要做的）

**使用者在自己電腦上做（需要遊戲）**
1. ~~安裝 REFramework 和 Fluffy~~ → **已完成**：Claude 已把 REFramework、偵察腳本、換裝腳本、光劍 pak 手動裝好（見第 4 節「遊戲端」），Fluffy 暫時不需要。**等使用者開遊戲**，確認按 Insert 有 REFramework 選單；開不了就先刪 `pak_mods`，還不行再刪 `dinput8.dll`。遊戲資料夾的 `re2_framework_log.txt` 可以直接讀來除錯
2. ~~雙劍鬼人化的 Watch~~ → 完成（見第 4 節）。**還要**：真鬼人化再錄一次 Watch（鬼人化中攻擊把量表集滿、解除後進真鬼人化），新的 `watch.json` 有 `catalog`（全部欄位名稱和型別）可以找；之後大劍、大錘、長槍、銃槍也各錄一次；各武器掃一次存 `scout.json`（都在遊戲資料夾的 `reframework/data/MiquellaLight/`，**Claude 在本機可以直接讀**）
3. ~~大小~~（做完了，見第 4 節）。舊紀錄：位置、金光已驗證 OK。執行中縮放武器（`set_LocalScale`）在 Wilds 行不通：每 20 幀設一次會在兩個大小之間閃（使用者說「瘋狂伸縮」），改在 BeginRendering 前設則完全沒效果。改成**預先做好的大小模型**：`make_size_variants.py` 已產生 `wp_miquella_db_s12/s14/s16.mesh`（握把不變，握把以上放大，刀身長度 ×k、寬度 ×√k），換裝腳本的 repo 版已改成 Size 下拉選單（1.0／1.2／1.4／1.6，預設 1.4，使用者想要 1.4）。**還沒做**：更新 `weapons_test.lua`（拿掉 scale 測試、加 Size 選單測試）並跑過；重新打包 pak（含三個大小）；裝進遊戲（遊戲開著時 pak 被鎖，要用背景等待關遊戲再複製）；遊戲資料夾裡現在還是舊的 BeginRendering 版腳本。使用者把 Glow 拉到 5（上限已改 10）
4. ~~特效顏色~~ → **完成**：`MiquellaLight_Effects` 軌跡、身上特效都是金色，攻擊／防禦上升閃光已藏（見 `mhws/MiquellaLight_Effects/README.md` 版本紀錄）。競技場實測：**1.72 ms/幀**（拿雙劍時每幀搜尋全部特效）、173 when found、**0 later**（找到時換一次就夠，遊戲不會再改回紅）、0 at spawn（產生時的掛鉤沒作用）。**使用者決定先維持現狀**（沒感覺卡頓）。之後要優化：掛鉤 `EffectPlayer.set_Resource` 抓新軌跡，抓得到就把全場搜尋降回每秒 4 次；或收刀時不每幀搜尋；拿掉對舊軌跡的每幀檢查。只有拿雙劍才每幀搜尋，其他武器每秒 4 次（約 0.1 ms/幀）。還沒驗證：藍鬼人（完美閃避）的銀色、Size 1.4、B 版三刃。Glow 使用者拉到 5（之後寫回 `.mdf2` 預設值）
5. **大劍和輕弩**：換模型、浮動環**使用者看過，說不錯**（2026-10-02）。之後使用者要求「模型和特效一起做完再一次測」，以下**全部已裝進遊戲，等實測**（2026-10-02 00:23）：
   - **大劍的大環**（刀身下段斜套的 `Blade_Halo`）也改磁浮（骨頭 `MQ_BladeHalo`，`hover`，跟輕弩一樣）
   - **大劍蓄力只在刀身表現**（使用者：遊戲的蓄力光出現在獵人身上，不喜歡）：特效檔裡身上發光 `PLE_Body`／`PLE_IMP` 拿掉（`MiquellaLight_GreatSwordFX.pak`）；刀身：一段 ×1.8 飽和亮金、二段 ×2.8、三段 ×3.6 白光，三段時刃紋開 `Use_MoveEmit`，`MoveEmit` 由腳本從刀根掃到刀尖（刃紋 UV 的 V 沿刀身排）。蓄力欄位**從執行檔字串猜的**：`_ChargeLv`、`_ChargeLevel`、`_EffectChargeLevel`、`_ChargeLvEffect`，用第一個存在的；選單 `Charge:` 顯示用了哪個、數值，找不到就列出含 Charge 的欄位
   - **輕弩速射量表**：三顆光點各代表 1/3（空的時候暗到 35 %），速射模式時 ×1.8 更飽和。欄位也是猜的：量表 `_RapidAmmoGauge`、`_RapidFireAmmo_Gauge`、`_RapidFireTimer_Gauge`、`_RapidModeTimer`，模式 `_IsRapidMode`、`_IsRapidShotBoost`；選單 `Gauge:`
   - **特效改金**：大劍、輕弩特效檔暖色 → 金（兩個 FX pak），特效腳本再把它們整個染金；選單可把大劍剩下的蓄力特效全藏（見 Effects README 第六版）
   - **偵察腳本**：Watch 時每 2 秒自動存 `watch_<武器型別>.json`（例 `watch_cHunterWp00Handling.json`），不用按 Save，兩把武器不會互蓋
   **使用者實測（2026-10-02）**：「改的不賴」（大劍蓄力、大環、特效顏色都 OK）。**沒有錄 Watch**（資料夾裡沒有 `watch_*.json`），選單的 `Charge:` 欄位應該有對到（效果有出來）。**輕弩速射**：使用者用的白熾龍輕弩沒有可速射的彈 → 沒測到量表；速射要裝填有「雙箭頭」標記的彈（通常彈、部分屬性彈），進入速射模式後消耗速射量表
   **使用者回報的兩個換裝 bug（2026-10-02 修好、已裝進遊戲，等實測）**：①選了外觀後拔刀**什麼都沒有**，要回武器庫重新裝備才出現（從雙劍就有）→ 原因推測是模型資源在換上的那一幀才建立、還沒載入完；改成腳本一啟動就**預先載入**所有外觀，換上後 1 秒、以及收刀時換上的下一次拔刀，**再設一次模型**；載入失敗的資源 5 秒後重試。②外觀**只對選的那一把生效**（換別把輕弩就沒了）→ 改成**依武器種類**（見第 0 節），選單寫「Look (all light bowguns)」。測：選了外觀直接拔刀就要看得到；換另一把同類武器也要自動是我們的外觀；片手劍的盾、太刀的刀鞘照規則
   - 之後：刃紋光帶如果不動（`MoveEmit` 不是照 UV 走）→ 改用 `AnimEmit` 呼吸或分段材質；特效顏色不對 → FxProbe 錄（使用者擔心其他武器也一起卡）
4. 裝 Armor VFX Manager，翻遊戲特效挑出最像癲火、寒氣、腐敗蝶、爆炸、光柱的；把它的 Lua 腳本給 Claude 研究

**Claude 接著做（拿到上面的檔案之後）**
5. 用 `watch.json` 找出狀態欄位 → 寫「武器狀態視覺」REFramework 腳本（改發光參數、開關材質槽、Dissolve），先做大劍蓄力和雙劍鬼人化
6. 把每把武器整理成遊戲用模型：會變化的零件分材質槽、需要動的綁骨頭；用 RE Asset Library 解出原版武器模型對齊骨頭和大小（**已可以自己解**：`extract_game_files.py`＋`inspect_wilds_mesh.py`／`inspect_wilds_mdf.py`，見第 6 節；不需要 RE Asset Library 那個 336 MB 的目錄，用 REE.PAK.Tool 的檔名清單就夠）
7. 學 Armor VFX Manager 生成特效的寫法，做操蟲棍三顆球的特效、裝置的爆炸、重弩「米凱拉的光」光柱
8. 角色正式版：身體＋長袍（貼身上半身、擺動下擺）、頭髮（擺動鏈）、頭冠綁頭骨
9. 之後：Ascendance 的新動作

**使用者實測回報（2026-10-02 下午，第一帳號處理中）**
- **弓（做完，等實測）**：①箭筒、箭還沒設計 → 箭筒 A／B（副武器那列「Quiver look」切換）＋光箭（`MiquellaLight_Arrows.pak` 蓋過遊戲的箭）；②蓄力亮金 → 白金、每段亮兩圈；③拉弓時 6 圈光環往弓身壓緊像彈簧、放箭彈回；④光環磁浮。蓄力欄位猜 `_ChargeLv` 等、拉弓欄位猜 `_IsCharge`、`_IsChargeStart`、`_IsAim`（選單 `Charge:`、`Draw:` 顯示用了哪個；如果光環晚一段才亮，勾「Bow charge counts from 0」）。**遊戲關掉後背景程序自動安裝**（`MiquellaTools\work\install_when_closed.sh`，待裝的在 `work\install\`）。測：拉弓時光環有沒有壓緊、放箭有沒有彈回、羽毛和箭頭方向、哪些時候還是木頭箭
- **大錘、長槍蓄力（做完，等實測）**：蓄力零件放在材質 `MiquellaCharge1～3`（長槍另有槍尖光刃 `MiquellaChargeTip`），`.mdf2` 裡 `Dissolve` 0 預設隱藏，腳本依段數淡入、改顏色（大劍的 `update_charge` 加了 `parts`／`weights`／`colored`）；**身上的蓄力光**用 `recolor_efx.py --hide` 拿掉：`MiquellaLight_HammerFX.pak`（大錘 13 檔，同大劍 `PLE_Body,PLE_IMP`）、`MiquellaLight_LanceFX.pak`（長槍 14 檔，`PLE_Body,PLE_IMP,PLE_Leg,=PLE,=0_PLE`，不含地面特效 `004_jimen`；`=名稱` 是新加的完全比對）。一樣排在遊戲關掉後自動安裝。長槍的段數欄位沒確認（選單 `Charge:`）
- **操蟲棍（做完，等實測）**：蓄力金 → 亮金 → 白金（`CHARGE_LOOKS.whiteGold`）；**精華三顆球**遊戲版（腐敗黴球、冰塊、餘燼球），點燈時淡入、繞上刃轉，三燈齊光刃亮金（欄位 `_ExtractTimerRed／White／Orange／Tripple`，從執行檔字串猜的，選單 `Extracts:` 顯示）；**獵蟲**接進腳本（`_Insect`，選單 `Kinsect:`）。測：點燈後球有沒有出現、繞的位置、獵蟲有沒有換成光蝶
- **銃槍（做完，等實測）**：象牙彈簧頂端一根骨頭 `MQ_SpringTop`，彈簧頂點依高度綁在它和 `Base` 之間 → 骨頭往槍根移就均勻壓縮（最多到 45 %）。**填彈**（`_IsReload`）壓一下再彈回；**蓄力砲擊**（`_IsChargeShot`／`_ChargeShotTimer`）每 0.45 秒一段、越壓越緊、金 → 亮金 → 白金，發射才彈回（會衝過頭一次）；**龍擊砲**（`_RyuugekiChargeTimer`）壓到底直到發射。能量核心獨立材質 `MiquellaCore`。欄位都是從執行檔字串猜的（選單 `Gunlance:` 顯示數值）。**填彈飛出去的機械零件**＝彈殼特效模型 `11_shellcase_02`（銃槍只有 `_0`、`_1` 兩個模型）→ 換成一滴小金光（`build_device_kit.py shellcase`，在 Devices pak）
- **龍杭砲金針（修了，等實測）**：使用者看到了但①一次好幾根 ②黑金屬色不發光 → 只放在顯示群組 5～9、改用我們的發光材質（見 Devices kit README「實測後的修正」）；射出去的光箭也改用發光材質
- **斬擊斧劍模式、充能斧斧模式＋光點量表（做完，等實測）**：劍模式 A（`wp_miquella_sa_sword`）、充能斧斧（`wp_miquella_cb_axe`，刃口轉向 -X）各是一個模型，腳本讀型態欄位（`_TransformMode` 等，猜的；選單 `Mode:`，讀反了就勾「Swap modes」）換模型，充能斧斧模式時把盾藏起來。光點各自一個材質 `MiquellaGauge1～5`：**斬擊斧**＝變形量表 `_SlashGauge`、覺醒 `_IsAwake`／強化斧 `_IsAxeEnhanced` 刃亮金；**充能斧**盾緣五顆＝瓶數 `_BottleNum`、劍上光點環＝劍能量 `_SwordEnergyPoint`（滿了亮金，上限讀 `_SwordEnergyPoint_Max`）、斧模式斧背五顆＝瓶數、盾強化 `_IsShieldEnhanced` 盾亮金、劍強化／斧強化刃亮金（選單 `Gauges:` 顯示用了哪些欄位）
- **太刀練氣（做完，等實測）**：`_AuraLevel`（猜的，0 無／1 白／2 黃／3 紅）→ 淡金 → 金 → 亮金 → 白光，黃以上刃紋流光（`CHARGE_LOOKS.spirit`、`bandFrom`）
- **響玉（做完，等實測）**：遊戲裡**沒有響玉模型**，狩獵笛的響玉／聲波都是特效，泡泡本體是共用模型 `Art/VFX/Mesh/Common/Other/bubble/11_bubble_00`（特效 `11_it05_000～042` 的 `MESH`，半徑 0.5 的球）。`gold_bubble.py` 換掉它（`MiquellaLight_HornFX.pak`，2026-10-02 已裝）：同大小的球殼用遊戲的泡泡材質改金色、拿掉彩虹，外面三道不同傾斜的細金光環用我們的發光材質（特效調不暗）。聲波攻擊用同一顆，會變成放大的金泡泡。球裡的光滴和地上光環要用腳本生成（使用者同意先這樣，不好看會回報）。改過的遊戲材質不進 repo
- **重弩（做完，等實測）**：導管兩圈、槍口兩圈光環和三顆光點各有骨頭，磁浮（`MQ_Halo0～3`、`MQ_Phial0～2`）
- **輕弩起爆龍彈花苞（做完，等實測）**：特效 `11_it13_106` 的模型元素各有一個群組範圍：**飛行中顯示 0＋1、落地後 0＋2**（原版：0 插地尖刺、1 圓頂、2 地上圓盤）→ 0 放中間的光、1 放閉合花苞、2 放綻開的花＋卷草根，**落地那一刻就綻開**（使用者要約 0.5 秒後打開：特效的時間欄位還沒解出來，之後可以用腳本生成會動的花）。改用發光材質。重弩 `11_it12_008_jimen` 也用同一個模型
- **盾的半透明光膜**：使用者看了片手劍 A／B／C：**A、B 看不出來**、**C 邊界很硬、有時只出現在某一象限**。A、B 已從選單拿掉，新增 **D**（`build_weapon_kit.py sns_shield_film`）：我們的發光材質＋部分 `Dissolve`（細碎像素透明，靠遊戲的抗鋸齒混成半透明，像雙劍側刃淡入那樣），5 圈同心環帶由中心 0.42 往外遞減到 0.08 讓邊緣柔化，兩面都有。等實測；有效的話再套到長槍、銃槍、充能斧的盾和長槍蓄力的光膜
- **使用者實測第二輪（2026-10-02 晚）**：弓光環不縮、大錘蓄力環沒出現、長槍蓄力沒變化、充能斧／斬擊斧沒變形、銃槍只有填彈有反應（砲擊、蓄力砲擊、龍擊砲沒有）→ **欄位猜錯**（大劍、銃槍 `_IsReload` 猜對）。換裝腳本加了**欄位記錄**（`recordFields`）：拿武器時每 0.25 秒讀處理器全部數值欄位，每 5 秒存 `reframework/data/MiquellaLight/fields_<型別>.json`（`changed`＝有變過的欄位：最小、最大、最後值、變了幾次）。**下一步：讀這些檔找出正確欄位，改 `KITS` 的 fields**；普通砲擊也要壓一下彈簧（上次漏了） → **第一次記錄的結果（已改進腳本）**：大錘 `<ChargeLv>k__BackingField`（0～3，屬性的 backing field）；長槍 `_FinishChargeLevel`（0～3）；斬擊斧、充能斧型態 `_Mode`（0／1）；充能斧劍能量 `_SwordEnergyState`（0～3，2＝紅＝滿）、瓶數暫用 `_ActionEnterBinNum`、強化 `_ShieldEnhancedTimer`／`_SwordEnhancedTimer`／`_AxeEnhancedTimer`；斬擊斧覺醒 `_SwordAwakeTimer`；銃槍蓄力砲擊 `_ChargeShotElapsedTimer`（放開後不歸零 → 用「還在增加」判斷蓄力，每 0.6 秒一段）。**還沒找到**：銃槍普通砲擊、龍擊砲，斬擊斧變形量表、充能斧真正的瓶數（處理器的直接欄位裡沒有 → 記錄器改成也讀子物件一層，要再錄一次）；**弓、操蟲棍、太刀還沒錄**
- **使用者實測第三輪（2026-10-02 深夜）**：**大錘 OK（先放過）**。弓：拉弓欄位 `_IsBowStringConstToHand`、段數 `<ChargeLv>k__BackingField`（**平時就是 1**，1～3）→ 已改；金針箭、新龍杭、操蟲棍特效 pak **遊戲沒關所以還沒裝**（`install_when_closed.sh` 在等）。
- **變形動畫（第二帳號 2026-10-02 清晨做完，已裝進遊戲，等實測）**：兩型態合成一個模型，`_Mode` 一變，腳本用 0.45／0.5 秒移動骨頭＋`Dissolve` 淡入淡出，**不再換模型**（換模型的卡頓、閃現都沒了）。細節在兩個 kit 的 README「變形」；預覽 `prototypes/action_states/switch_axe_morph.gif`、`charge_blade_morph.gif`（使用者看過預覽前就裝了）。**請使用者測**：①斧↔劍、劍盾↔斧切換時有沒有變形（選單 `Mode:` 後面的 `morph` 會從 0 走到 1、`Morph joints found: 8/8`／`30/30`）；②動畫時間跟遊戲的變形動作合不合（太快／太慢改 `MORPH_*.seconds`）；③充能斧盾淡出時在哪裡（遊戲會把盾移到劍上，可能剛好像盾變成斧）；④人物「跳幀」還有沒有。**如果骨頭找不到**（`0/8`）就是 `getJointByName` 對新骨頭無效，要回報。之後可調：斬擊斧斧刃翻轉的路徑（現在是 180° 翻面）、充能斧橢圓大小
- **使用者實測第四輪（2026-10-02 清晨，第二帳號處理）**：**變形動畫「設計得非常好，好得很誇張」**；銃槍蓄力砲擊的彈簧壓縮 OK。其他：
  - 太刀流光看不到 → 欄位猜錯：實際是 `<AuraLevel>k__BackingField`（1 無～4 紅，腳本 `offset = -1`），光帶加寬加亮；**練氣的白黃紅特效拿掉**（新 `MiquellaLight_LongSwordFX.pak`：`11_it03_000` 刀身光、`11_it03_004` 身上光）
  - 銃槍龍擊砲沒壓彈簧 → 沒有計時欄位，改看龍擊砲量表 `_RyuugekiGauge._Value`（1～2）掉 1 格 → 壓到底 1.7 秒再彈回（時間是猜的）；**普通砲擊**：`_ChargeShotBulletNum` 減少 → 壓一下
  - 獵蟲翅膀閃爍刺眼 → 翅膀改綁我們的 `MQ_WingL/R`（`Body` 子骨頭），腳本慢慢拍（`flap`）；`build_weapon_kit.add_bones` 可以指定父骨頭（`bone_parents`）
  - 操蟲棍還有紅色蓄力光氣 → 14 個特效檔暖色 → 金（`InsectGlaiveFX` 第二版）＋特效腳本第七版執行中染金
  - 響玉線條太粗 → `gold_bubble.py` 光環細到 1/3、亮度 2.0 → 1.4（`HornFX`）。**泡泡常駐**（打擊時光環擴散、泡泡留在原地）**還沒做**：遊戲的泡泡模型只在打擊特效裡出現；要先用 FxProbe 錄一次響玉（放響玉 → 等 10 秒 → 打一下 → 存），找出響玉存在期間一直在播的特效和它的物件，再用腳本在那個位置生成我們的泡泡（腳本生成物件還沒在遊戲裡試過，見研究筆記 15）
  - 弓的金針箭在中間光環穿出 → 箭的角度來自拉弓動作；腳本拉弓時找遊戲的箭（路徑 `it1199_0000_0`），把光環移到箭的線上（選單 `Arrow:` 顯示偏多少）
  - 輕弩花苞「還沒處理好」→ **問使用者哪裡不對**（黑的？好幾個？沒綻開？）
  - 另外：換武器時 REFramework 記錄了 134 次 `set_DrawSelf`／`getComponent` 例外（舊武器物件被遊戲刪了，腳本最多還用 20 幀）→ 改成每幀先丟掉失效的物件
  - 腳本已裝（遊戲開著，要按 Reset scripts）；`LongSwordFX`、`InsectGlaiveFX`、`InsectGlaive`（新獵蟲）、`HornFX` **05:53 遊戲關掉後已自動安裝並比對**。測試 154 項全過
- **使用者實測第五輪（2026-10-02 清晨，第二帳號處理）**：弓光環對準箭「效果很好」；太刀白黃紅拿掉「很棒」；獵蟲記憶體先擱置（使用者說先換別的；特效腳本已把操蟲棍改成每秒搜 4 次）。處理：
  - 弓蓄力有紅光氣 → `11_it11_030`（蓄力 0～3 段：身上光、火、光暈、粒子）暖色 → 金（新 `MiquellaLight_BowFX.pak`）＋特效腳本只對這個檔執行中染金
  - 太刀還是看不到流光 → 材質自己的 `MoveEmit` 在遊戲裡沒效果；刃紋切成 8 段（`MiquellaBand1～8`，`build_weapon_kit.split_bands`），腳本輪流點亮，從刀根跑到刀尖（大劍的光帶也是 `MoveEmit`，大概一樣沒動，之後可照做）
  - 響玉線條沒變細 → 原版泡泡**沒有邊緣光**（0），是我們加的 3.0／power 2 造成粗線；改 1.5／power 6（只剩細邊），光環再細一半、亮度 0.9。還是粗的話請使用者截圖
  - 龍擊砲：量表是在**發射那一刻**才扣（使用者推測對了）→ 改讀原版骨架的 `Heat_Hinge`（遊戲動畫會帶動）轉超過 6° 或移動超過 1 cm 就壓彈簧，量表扣掉（發射）放開、等骨頭回位才能再壓。`Hinge`／`Heat_Hinge` 的動作和量表、彈數變化都記在 `glEvents`（存在 `fields_app_cHunterWp07Handling.json` 的 `events`），選單 `Gunlance:` 顯示兩根骨頭的角度。**猜錯就看 events 換骨頭**
  - 銃槍填彈的金針在外側 → 原版的 `VFX_Pile`（龍杭出現的位置）在 y +0.109（原版槍管那裡），我們的槍在中軸 → 移到 (0, 0, 0.530)，`VFX_Heat` 也移到軸上
  - 腳本已裝；`Gunlance`、`BowFX`、`HornFX`、`LongSword` pak 排在遊戲關掉後安裝。測試 155 項全過
  - **第五輪實測「完全沒改善」**：四個 pak 根本沒裝上——使用者重開遊戲太快，安裝程序每 15 秒才檢查一次，沒抓到遊戲關掉的空檔（已改成每 2 秒）。龍擊砲：記錄顯示 `Heat_Hinge` 整場沒動、`Hinge` 拔刀時轉 72° 後一直停著 → 改成 `Hinge` 跟「拔刀 1 秒後的姿勢」比，偏超過 15°（不在裝填中）就壓；每次發射把前 6 秒兩根骨頭的角度記進 `events`（`trace`），下一輪看準備動畫到底動了什麼
  - **掏出狩獵笛卡到不能動**：當時遊戲佔 10 GB、實際留在記憶體只有 3.3 GB（其餘被換到硬碟），整台 15.6 GB 剩 2 GB → 多半是長時間測很多把武器累積的記憶體壓力，不一定是狩獵笛本身。請使用者關掉遊戲（等 pak 裝好）、關 Discord／Chrome 再重開，先測狩獵笛；如果單獨測還是卡，先拿掉 `MiquellaLight_HornFX.pak` 比較
- **使用者實測第六輪（2026-10-02 06:40）**：弓修好、銃槍填彈金針修好；太刀流光還是沒有、龍擊砲還是沒壓（trace：準備動畫期間 `Hinge` 一直 18°、`Heat_Hinge` 0°，骨頭讀不到）、響玉線條「變更粗」→ 邊緣光關掉（`gold_bubble.py` 的 `SHELL_RIM`，`HornFX` 第四版，排在遊戲關掉後安裝）。使用者換回第一帳號，留言見第 0 節。**第一帳號處理（07:45）**：
  - **響玉**：07:40 比對，遊戲裡的 `HornFX` 還是 06:25 版（第四版 06:37 沒裝上，遊戲一直開著）→ 重跑 `install_when_closed.sh`（背景等遊戲關掉）。裝好後請使用者看線條有沒有變細
  - **太刀流光**：欄位沒問題（記錄裡 `<AuraLevel>k__BackingField` 1→4）。看不到的原因：刃紋是半徑約 2.7 mm 的細管，而 Glow 5 時刀身本身已經 1.2×5×1.8～3.4 ≈ 11～20，光帶再 ×4 也是「白上加白」→ **刀身也切 8 段**（`MiquellaBlade1～8`，`split_bands` 新增 `span`，跟刃紋用同一段長度），光帶經過的段變白、×5，其他段流光期間壓到 0.6（`bandDim`），測試裡對比 1.08 → 5.2。`LongSword` pak 重做，排在遊戲關掉後安裝；腳本同時相容舊模型（`MiquellaBlade`）
  - **龍擊砲**：從執行檔字串找到 `get_BaseActionController`／`get_SubActionController` → `get_CurrentAction`，龍擊砲的動作類別 `cRyuugekiStart`／`Idle`／`AimIdle`／`ToAim`／`Shoot`／`Shot` → 腳本讀**目前動作的類別名稱**，含 `Ryuugeki` 就壓到底，量表扣掉（發射）放開、等動作結束才能再壓；骨頭那套整個拿掉。選單 `Gunlance:` 最後顯示 `action:`（讀不到會寫 `not readable`）。**欄位記錄器的檔案多了 `actions`**（所有武器的動作名稱變化，最多 150 筆）→ 以後找任何武器的動作（響玉、太刀氣刃…）都可以先看這個
  - 腳本已裝進遊戲（要 Reset scripts）、`installutorun` 也換成新版；測試 159 項全過
  - **攻擊軌跡改金（使用者 07:50）**：太刀紅刃的紅軌跡＝`11_it03_001`（五條緞帶全是 `#FF1A1A`）→ `--warm` 改金；升練氣的橘色火光、身上光 `003`、`007` 也改金 → `LongSwordFX` 第二版（5 檔，含原本藏掉的 `000`、`004`）。特效腳本加太刀規則（`11_it03_`、每秒 4 次、`9xx` 不染），已裝進遊戲。操蟲棍：軌跡 `004`／`049`／`057` 在 `InsectGlaiveFX` 第二版已改金（05:53 才裝上，使用者看到的紅可能是之前的），這次補 `030`（精華色的預設值 RED／YELLOW）→ 第三版。兩個 pak 排在遊戲關掉後安裝。**注意** `make_patch_pak.py` 要用 `bpy45` 的 Python 跑
  - **所有武器的攻擊軌跡（使用者 08:00：「其他武器應該也有軌跡」）**：解出全部 14 種武器的特效檔（388 個，片手劍、斬擊斧、充能斧之前沒解），`trail_scan.py` 列出每個檔的軌跡條目和顏色。還沒改的有色軌跡：片手劍紅、狩獵笛每個音符一色、銃槍龍杭紅、斬擊斧紅藍黃、充能斧紅、弓紅藍、重弩紅；另外長槍之前**只隱藏沒改色**，大劍、大錘的防禦／完美防禦還有淡紅（舊工具只改飽和的紅）。`recolor_efx.py` 新增 **`--layers`**：所有顏色（淡色也算）→ 不同層次的金（紅紫 → 深金、橘黃 → 金、綠 → 黃金、藍青 → 白金，亮度保留，金色不動）、`--skip-entry`。**`fx_paks.py`** 一次產生每種武器的 `MiquellaLight_<武器>FX.pak`（規則表在檔案裡：大劍、大錘、長槍保留身上光的隱藏，太刀保留練氣光隱藏，操蟲棍、弓只補檔，雙劍不動，地面煙塵 `_jimen`／`_land_` 不動，血、煙、彈種顏色參數不動）→ 新 pak：`SwordShieldFX`、`HuntingHornFX`（跟響玉的 `HornFX` 分開）、`GunlanceFX`、`SwitchAxeFX`、`ChargeBladeFX`、`HeavyBowgunFX`；重做：`GreatSwordFX`、`HammerFX`、`LanceFX`、`LongSwordFX`、`InsectGlaiveFX`、`BowFX`、`LightBowgunFX`。全部排在遊戲關掉後安裝。**狩獵笛的音符軌跡顏色也變成金色層次**（不再一個音符一個顏色），使用者不喜歡就移除 `HuntingHornFX`
  - **輕弩花苞**：使用者說「看起來根本沒有花苞樣」，懷疑高度設錯或當時還沒裝上（`Devices` pak 06:25 已確定在遊戲裡）。注意現在的設計是**落地就換成綻開的花**（組 2，原版那組是地上圓盤，特效可能把它壓扁或下沉）→ 請使用者放好後按 **F12** 截圖：Steam 截圖會在 `Steam/userdata/<id>/760/remote/2246340/screenshots`（目前還沒有這個資料夾），Claude 直接讀
- ~~下一個大工作：斬擊斧、充能斧的變形動畫~~（上面那條）。原本的計畫：使用者：現在變形是「直接閃現」成另一個模型很怪，要完整的變形動畫（能量武器，光刃直接形變也可以）；充能斧希望**盾形變成斧模式的那個樣子**。另外斬擊斧有時人物動作像跳幀（上一秒持斧下一秒持劍）：可能是遊戲的快速變形招式，也可能是換模型（`set_model` 的 `set_Enabled` 關開＋`setMesh`）造成卡頓 → 新做法不換模型。做法：
  - **不再換模型**：兩種型態做成**同一個 mesh**，各零件綁自己的骨頭（像浮動光環 `MQ_*`），腳本在 `_Mode` 改變時用 0.3～0.5 秒把骨頭從一個姿勢動到另一個，只屬於一種型態的零件用 `Dissolve` 淡入淡出
  - **斬擊斧**：三片斧刃（`switch_axe_axe_head`）各一根骨頭，從扇形轉、移到劍背疊成羽毛（劍模式 A 的位置，`switch_axe_sword_head`），長光刃綁一根骨頭，從柄裡滑出／長出（骨頭往前移＋`Dissolve`；joint 的 `set_LocalScale` 能不能用要測，武器整體縮放在 Wilds 會被蓋掉）
  - **充能斧**：劍的模型裡直接包含斧頭（劍模式時隱藏），盾（`_1`）在變斧時淡出、斧頭從盾的位置附近長出來／淡入；或讓盾的光環、樹紋零件各自綁骨頭往斧頭輪廓移。兩個 GameObject（劍、盾）之間沒辦法共用骨頭，所以盾是淡出＋劍上的斧頭淡入
  - 兩種原型的零件名稱、位置在 `arsenal.switch_axe_common`／`switch_axe_axe_head`／`switch_axe_sword_head`、`charge_blade`／`charge_blade_axe`；骨頭和姿勢要在 `build_weapon_kit.py` 量（`pivots`、`floaters`），腳本可以沿用 `step_floaters` 的骨頭設定
- **操蟲棍（第二輪）**：蓄力 `<ChargeLv>k__BackingField`（0～2，兩段 → `whiteGold2`）；獵蟲改從角色的 `get_Wp10Insect` 拿（執行檔字串找到的；處理器沒有 `_Insect`）；**精華計時器還沒找到**（處理器的直接欄位沒有，等新的記錄器讀子物件）；**身上的精華顏色拿掉**：`11_it10_020`（`PLE_colorA／B／C`＋身上火光）、`11_it10_021`（`PLE_Body`、頭盔）用 `recolor_efx.py --only-hide` 全部透明 → `MiquellaLight_InsectGlaiveFX.pak`（排在遊戲關掉後安裝）
- **弓的箭改成米凱拉金針**（使用者：光箭太粗跑出光環外、像能量武器）：`arsenal.needle_arrow`（龍杭金針壓細拉長，金屬金色微光，材質 `MiquellaGold`＝裝置貼圖的金色帶、`Emissive_Intensity` 0.6），手上的箭、射出去的箭、箭筒裡的箭都換。排在遊戲關掉後安裝
- **待做（照順序）**：①~~攻擊軌跡改金~~（2026-10-02 夜做了，見「使用者實測第六輪」的「所有武器的攻擊軌跡」）③起爆龍彈花苞如果也黑 → 照金針改發光材質、只放對的顯示群組
- **蓄力力量感・設計提案（2026-10-02 夜，第一帳號，使用者睡前交代，等他挑）**：使用者：長槍蓄力不夠有力量感、要更有特色；弓蓄力多一些裝飾光效；操蟲棍三燈光球還沒設計好（多找設計）；其他武器蓄力也加力量感；「不急著放進遊戲」。預覽（`prototypes/action_states/`）：`lance_power.png`（A 光旋／B 光冠／C 光羽／D 收束，各三段）＋`lance_A_spin.gif`、`lance_D_compress.gif`；`bow_power.png`（A 藤蔓綻放／B 聖樹光陣／C 光點環繞／D 光翼）；`extract_orbs.png`＋`extract_on_glaive.png`（1 聖骸燈籠／2 三朵花／3 寶石／4 紋章）；`power_great_sword.png`、`power_hammer.png`、`power_gunlance.png`、`power_long_sword.png`、`power_charge_blade.png`（現在 vs A／B）。說明在 DESIGN.md「蓄力的力量感・提案」。程式 `power_states.py <set>`（`lance_power`、`bow_power`、`extract_orbs`、`extract_on_glaive`、`weapons_power [武器名]`、`lance_anim`）、`weapon_power.py`、`orb_styles.py`。**使用者挑了之後**：照選的方向做遊戲版（新零件分材質槽、`Dissolve` 依段數淡入；光旋要骨頭繞軸轉、收束要骨頭沿軸滑，跟浮動光環同一套）
  - **使用者選了（2026-10-02 晚）**：長槍 A、弓 A、操蟲棍 2（三朵花）、大劍 A、太刀 B、充能斧 A；銃槍要「槍身裡一條充能金絲逐漸拉伸」、大錘再想、片手劍完美突進／蓄力斬也要刀身變化 → 第二輪提案 `gunlance_filament.png`、`hammer_round3.png`、`sns_perfect.png`（等使用者挑）
  - **遊戲版進度**：①**長槍 A 光旋：做完、已裝進遊戲（遊戲關著直接裝）**：`arsenal.lance_drill_parts`、kit 的 `MQ_Drill` 骨頭（z 1.751）、腳本新的骨頭模式 `spin`（`floaters.spin.dps` 依蓄力段數 0／90／200／420 度每秒），測試 164 項全過。②**大劍 A、太刀 B 光絲纏繞：做完、已裝進遊戲**：`arsenal.wrap_strands`／`great_sword_strands`（三條＋滿蓄力火花）／`long_sword_strands`（兩條），依段數分在 `MiquellaCharge1～3`，腳本 `charge.parts`＋新的 `partColor = PART_GOLD`（刀身白光時光絲還是亮金），測試 167 項。③**充能斧 A 光齒：做完、已裝進遊戲**：`arsenal.charge_blade_saw`（24 齒依序分 A／B／C 三組＋外側弧線每組一份），kit 的 `sets` 新增 `SawA／B／C`（跟斧刃一樣綁輪廓骨頭、`MiquellaSaw*` 預設隱藏），腳本 boosts 的 `chase`：斧強化時三組每秒 15 次輪流亮，像光齒沿刃口跑；變形表不變，測試 170 項。④**弓 A 藤蔓開花：做完、已裝進遊戲**：`arsenal.bow_blossoms`（每邊弓臂一段兩朵、滿蓄力弓尖大花，省面的 `light_blossom`），`MiquellaCharge1～3`，腳本 `bow.parts`（拉弓的段數），測試 173 項。⑤**操蟲棍三朵花：做完、已裝進遊戲**：`arsenal.extract_flower`（`orb_styles` 的花，遊戲版用省面零件，各自轉成在自己位置朝外），精華貼圖改 10 條色帶（每種精華：花瓣／暗心／亮心，加金色光環），kit 新增 `uv_band_of`（每個零件依材質對色帶，存在頂點屬性 `mq_band`，合併後依它設 UV）、`uv_band_count`；腳本 `orbit.face`：繞刀時一直朝外、繞自己的朝向慢轉（25 度每秒），測試 174 項。⑥**銃槍 G3 絞絲針眼：做完、已裝進遊戲**：`arsenal.gunlance_filament`（兩股絞絲從能量核心拉到槍口，頂端金針針眼＋光滴，材質 `MiquellaFilament`，預設隱藏）；kit 的頂點依高度分給 `Base` 和新骨頭 `MQ_FilamentTop`（檔案 z 0.429→2.015），腳本新的骨頭欄位 `stretch`（=根部高度）：`entry.stretch` 跟著段數 0→1/3→2/3→1（最短 15 %），所以金絲越蓄越長、絞紋變鬆，外面彈簧同時往槍根壓；顯示用 `charge.parts`（第一段起）。⑦**大錘 H4 渾天儀：做完、已裝進遊戲**：`arsenal.hammer_armillary`（三道大環＋各 6 顆光珠，材質 `MiquellaArmillary1～3` 依段數出現），各綁 `MQ_Arm0～2`（錘頭中心 z 1.316），腳本 `spin` 每根骨頭自己的軸（Z／-X／(0.3,1,0)，只繞法線轉的話圓環看起來不動），70／140／260 度每秒；錐形光環照舊。測試 177 項
  - ⑧**片手劍 S2 時機光環：第一版做完、已裝進遊戲（時機是猜的，要實測校正）**：`arsenal.sns_timing_parts`（光環綁 `MQ_TimingRing`，建在護手 z 0.15；爆開的三圈光環＋12 道光芒），材質 `MiquellaTiming`／`MiquellaBurst`（預設隱藏）；腳本 `timing` 表＋`update_timing`：動作名稱含 `JustRush` 時光環出現，關節新欄位 `slide`（`entry.slide` 往上抬 0.8 m）：從刀尖花 `fall` 0.45 秒降到護手；`canJustRushCombo0～2` 若能呼叫就以它當「到護手」的時機；`_IsJustRush` 變 true＝完美 → 爆開 0.35 秒淡出。選單 `Perfect Rush:` 顯示狀態，事件記進欄位記錄檔的 `events`。測試 183 項。**校正用的追蹤（2026-10-02 深夜，已裝進遊戲）**：完美突進期間到結束後 1 秒，**每幀**讀獵人、武器處理器（含子物件一層）、目前動作物件（含子物件一層）的全部數值欄位，記下變化（真假值、整數每次變都記，其他數字只記 0↔非 0；新動作開始時記它為 true 的欄位；每欄每次最多 12 行），每行是距離突進開始的秒數，連同 `action`、`window`、`ring at the guard`、`Perfect!` 存成欄位記錄檔的 **`trace`**（最多 1500 行）；`canJustRushCombo0～2` 也改成處理器、獵人兩邊都試。**校正方法**：比對每個 `cJustRushCombo*` 開始的時間、下一個開始的時間（＝使用者按鍵）和 `Perfect!`，找出完美的時間窗、有沒有欄位剛好在窗內變 true，改 `timing.fall` 或改讀那個欄位。測試 189 項。原本的說明：荒野機制：**完美突進**＝後跳接的四連擊，每擊前獵人亮起、亮的時候出手傷害大增；**蓄力斬**命中弱點會追加斬擊。執行檔裡找到：動作類別 `cJustRushStart`、`cJustRushCombo0～2`（`app.Wp01Action`？）、`cShortSwordAttack_JustRushCombo`；欄位 `_IsJustRush`、`_IsLastJustRushFinshSuccess`、`_StepSlashCount`（0～4，有記錄到）；判斷 `canJustRushCombo0～2`、`cCheckWp01CanJustRush`（大概就是「亮起」的時機窗）；特效骨頭名 `VFX_JustRush_Success`。**做法**：①劍上加一圈光環（綁骨頭 `MQ_TimingRing`，在動作 `cJustRush*` 期間從刀尖往護手滑，到護手＝時機）和完美時的爆開零件（三圈光環＋放射光芒，材質一組，0.3 秒淡出）；②腳本：讀 `actionNow`（已有）判斷在不在完美突進中，每幀試 `h:call("canJustRushCombo0/1/2")`（存在就用它決定「到護手」的時刻，記進 `glEvents` 類的事件），`_IsJustRush` 變 true 或下一個 `cJustRushCombo` 開始＝打出完美 → 爆開；③**先請使用者實際打幾次完美突進**（欄位記錄器開著），讀 `fields_app_cHunterWp01Handling.json` 的 `actions` 和 `changed` 確認時機，再調。預覽 `prototypes/action_states/sns_perfect.png`（S2 那列）
  - **請使用者測（遊戲版第一次）**：長槍蓄力光絲有沒有越蓄越長、會不會轉；大劍／太刀光絲每段長出、三段時還是金色；充能斧斧強化（紅斧）時刃口光齒有沒有在跑；弓拉弓時弓臂開花；操蟲棍點燈時花有沒有朝外、繞刀、顏色對不對；銃槍蓄力砲擊時槍身裡金絲有沒有拉長；大錘蓄力時三道大環有沒有出現、轉起來像陀螺儀。另外：所有武器攻擊軌跡變金（狩獵笛音符軌跡變全金，不喜歡就拿掉 `HuntingHornFX`）

**使用者實測第七輪（2026-10-02 23:39，第一帳號 2026-10-03 接手處理）**：要求見第 0 節最新一則（弓一朵一朵開、螺旋做成動畫、太刀氣刃大迴旋斬、操蟲棍光球沒出現、輕弩花苞埋在地下）。**全部做完、2026-10-03 01:10 已裝進遊戲，等實測**：
- **蓄力時間從哪來**：欄位記錄器的檔案裡每把武器都有連續的計時器（大劍 `_ChargeTimer` 最大 3.03、長槍 `_FinishChargeTimer` 3.60、太刀 `_KijinChargeTimer`、弓 `_ChargeTimer`／`_OnceChargeTimer`）；升段的計時器值從遊戲參數檔解出來（`extract_game_files.py` 抽 `gamedesign/player/actiondata/wpXX/globalparam/wpXXglobalactionparam.user.3`，掃「個數＋遞增的浮點數」）：大劍 `[0, 0.8, 1.55, 2.3]`＋過蓄 3.0（七組，依 `_ChargeType` 不同，有 `[0, 0.3, 1.1, 1.9]`、`[0, 0.2, 0.7, 1.2]`、`[0, 0.6, 1.4, 2.0]`）、長槍 `[0.8, 2.0, 3.6]`、太刀氣刃蓄力 `[0, 0.8, 1.6, 2.9]`（緊接在 `_KijinChargePressTime` 0.6 後面）、弓 `_ActionParam._ChargeTimeLv2～4` = 1／2／3（處理器上直接讀得到）。銃槍蓄力砲擊沒有段數欄位、參數檔看不出哪個是門檻 → 金絲照舊用 0.6 秒一段的時間，改成連續拉長（1.2 秒拉滿）
- **模型**：`arsenal.py` 新的「growing with the charge」：`band_spans`／`reach_at`，大劍 `great_sword_strands`、太刀 `long_sword_strands`、長槍 `lance_drill_parts` 的光絲依出現時間切成 24 段（`MiquellaGrow1～24`），弓 `bow_blossoms` 每朵花三段共 21 段；`build_weapon_kit.py` 的 `grow_materials`、`GROW_MAX`。大劍火花、長槍根部旋轉弧仍是 `MiquellaCharge3`。重建四把武器的 kit（三角面數：大劍 6.3 萬、長槍 6.4 萬、太刀 3.2 萬、弓 4.8 萬）
- **腳本**：`update_grow`（說明在換裝腳本 README「跟著蓄力連續長出來」）、`with_grow`、`read_path`、`array_numbers`、`number_of`；長槍轉速 `spin.grow`；銃槍金絲連續；操蟲棍 `extract_indices`（讀 `app.Wp10Def.EXTRACT_TYPE` 的列舉值，讀不到就紅 0、白 1、橘 2）；欄位記錄器也記陣列（`ExtractTimer[0]` 等）。`set_alpha` 移到前面給大家用
- **輕弩花苞**：`build_device_kit.wyvernblast` 的位移 -0.13 → +0.02（原版落地圓盤在 y -0.05～+0.06，地面在特效原點）。對照圖 `MiquellaTools\work\previews\grow\bud_ground.png`
- 預覽工具 `preview_grow.py`（照腳本的算法、照遊戲時間）；`preview_morph.py` 加了 `__main__` 判斷才能被 import
- **骨頭連續拉伸（01:30 加的）**：`arsenal.strand_point`／`strand_chains`（每條光絲在自己身上的骨頭點）、`grow_chain`（長槍軸上）；`build_weapon_kit.grow_chain_setup`（加骨頭、依高度綁權重：一段的頂點綁在它兩端的骨頭之間）、`write_grow`（輸出 `<kit>/<模型>_grow.lua`，貼進腳本的 `GROW_GS／LS／LN`）；腳本 `grow_joints`、`step_grow_joints`（正在長的那段裡還沒到的骨頭移到前緣，長槍再轉回螺旋角度；長過的放回原位設一次）、`GROW_SNAP`。`preview_grow.py` 也照這套算法動骨頭。骨頭數：大劍 154、太刀約 126、長槍 121（RE 網格上限 256）。近看檢查 `gs_zoom.png`、`lance_zoom.png`（`MiquellaTools\work\previews\grow\`）
- **如果遊戲裡不對**：⓪光絲出現但一格一格跳、或尖端附近有一團光 → 骨頭沒動：選單 `Growth bones found:` 是不是 n/n（0 就是新骨頭沒建立關節）；①光絲完全沒出現 → 選單 `Growth:` 看段數和計時器有沒有讀到（`?` 就是欄位名錯）；②長得比升段快／慢 → `Growth:` 的 next level 有沒有變 `learned`，`fields_*.json` 的 `events` 有 `charge ...: level k at ...`；③太刀氣刃蓄力沒長 → `actions` 裡氣刃蓄力的動作名（現在找含 `KijinCharge` 的）；④操蟲棍還是沒光花 → `Extracts:` 寫 `not readable` 就是陣列讀法不對（`array_numbers` 試了 `get_elements`／`get_size`＋`get_element`／`get_Length`＋`GetValue`），三個數字對不上顏色就看 `(red 0, white 1, orange 2: assumed)` 改順序

**其他武器（第二帳號，2026-10-02）— 已裝進遊戲，等實測**
- 換裝腳本選單：拿武器時 Weapon 槽選主武器外觀（`LongSword`、`SwordShield`、`Hammer`、`HuntingHorn`、`Lance`、`Gunlance`、`SwitchAxe`、`ChargeBlade`、`InsectGlaive`、`Bow`、`HeavyBowgun`），**有盾的武器 SubWeapon 槽再選 `*_Shield`**。每把看：握的位置、刃口方向（揮砍的光痕那邊）、長度、盾有沒有穿過手臂、浮動光環
- **半透明光膜測試（2026-10-02，等實測）**：遊戲武器材質只能鏤空裁切，但**有半透明材質可以借**（全遊戲 2157 個材質統計過）：武器自己用的 `BaseAlpha_Emit_FakeLiquid_RoughTransparent`（21 把）、`Simple_VolumeBlend_Emit_ViewOffset`（12 把，柔光），特效的 `VFX_Transparent_Unique_Aura`（玩家裝備光暈）、`VFX_Transparent_Bubble`（泡泡，有邊緣發光）。片手劍盾做了三個外觀 **`SwordShield_ShieldA`（光暈）／`B`（泡泡膜）／`C`（柔光）**，使用者在遊戲裡切換比較；**選好後套到長槍、銃槍、充能斧的盾**（那三面的光膜是單面圓片，要加背面或用雙面旗標）。之後可做「防禦時光膜變亮」
- **武器裝置（2026-10-02 加裝 `MiquellaLight_Devices.pak`，等實測）**：銃槍龍杭＝未鍛金之針、輕弩起爆龍彈＝象牙花苞，**蓋過遊戲的特效模型**（`Art/VFX/Mesh/Weapon/it07/11_it07_000`、`it13/11_setbombshell_000`），見 `mhws/MiquellaLight_Devices_kit/README.md`。測：銃槍打龍杭砲、輕弩放起爆龍彈，看模型有沒有出現、大小方向對不對、有沒有好幾個重疊亂飛（原版分 10／3 個顯示群組，我們每組都放完整模型）。重弩、弓追蹤箭、狩獵笛響玉的遊戲檔還不確定是哪個（README 有候選），要在遊戲裡確認
- 已知限制：~~斬擊斧只有斧模式；充能斧盾在斧模式不會變形~~（2026-10-02 做了變形動畫，見上面）；銃槍、重弩的 `Hinge` 動作不會帶動我們的模型；弓弦中段綁 `String` 骨頭（拉弓應會拉成 V 形，等實測）；狩獵笛聲波環沒放
- **使用者決定（2026-10-02）**：獵蟲用 **A 實心金翅**（pak 裡就是 A）；充能斧盾的斧刃像新月 → **先擱置**，使用者想改會再說；盾沒有光膜、只用光環和樹紋 → 可以
- **第一帳號的「依武器種類選外觀」接上時**：同種類的 `_0`、`_1` 會套同一個外觀 → 有盾的武器要用主武器 `KITS` 的 `shield` 欄位給 `_1` 換盾（→ **2026-10-02 第一帳號接上了**：`_1` 盾用 `shield`、可在副武器那列改選；雙劍兩手同外觀；刀鞘、箭筒保持原版）
- Claude 接著：獵蟲接進換裝腳本（先用偵察腳本找獵蟲的 GameObject）；防禦時才出現的盾光膜（需要防禦狀態欄位＋半透明材質：**特效模型的材質有半透明**——`VFX_Transparent_Bubble`（`common/other/bubble/11_bubble_00`）、`VFX_RoughTransparent_D`，可以試著抄給盾的光膜用；武器材質本身只有鏤空裁切）；斬擊斧劍模式、充能斧斧模式（要找模式欄位）

**角色（2026-10-02 深夜開始，第一帳號）**
- **頭冠遊戲版（做完、已裝進遊戲，等實測）**：`build_weapon_kit.py circlet`（原型 `circlet.py` v10，放大 (1.22, 1.10, 1.12) 戴在遊戲的頭上，檔案空間＝`Head` 骨頭空間，材質 `MiquellaHalo`＝象牙底整個發金光）→ `MiquellaLight_Character_kit`、`MiquellaLight_Character.pak`；腳本 `mhws/MiquellaLight_Character/`（README 有做法和選單）。**請使用者測**：選單「MiquellaLight: Character」，看頭冠有沒有出現、在不在額頭、跟不跟頭動；狀態列寫 `Head joint` 或 `following every frame`、離 `Head` 幾公分；位置不對用選單的上下／前後滑桿調，告訴 Claude 數值寫回模型。戴頭盔會穿模（先關頭盔顯示）。預覽 `MiquellaTools\work\previews\circlet\circlet_on_game_head.png`（含遊戲的頭，不進 repo）
- **如果生成物件不行**（狀態列寫 could not create）：退回覆蓋檔案的做法（把頭冠併進某款髮型 `ch01_000_00xx`，或放進內衣身體）
- **發現（2026-10-02 深夜）**：荒野的內衣是**整套衣服**（襯衫、皮帶、褲子、靴子），皮膚只有手、脖子、臉 → **沒有裸身模型可改，身體要自己做**（研究筆記第 18 節，有骨頭位置和 A 字綁定姿勢）
- **身體（2026-10-02 深夜，使用者：「那身體你先做吧」）做完、已裝進遊戲，等實測**：MakeHuman 基礎人體（CC0）調成纖細中性、對齊遊戲骨架、切掉頭接遊戲的臉、內褲材質；**三款 A 纖細中性／B 少年感／C 柔和**（預覽 `MiquellaTools\work\previews\body\body_variants_sheet.png` 已傳給使用者，**等他挑**），三款都進了 pak，遊戲選單 `Body shape` 可切。做法、指令在 `mhws/MiquellaLight_Character_kit/README.md`，程式 `prototypes/scripts/miquella_body.py`。腳本：身體物件 SameJointsConstraint 跟著獵人、打開時藏獵人的防具和內衣（ch02／ch03），臉和頭髮保留。`character_test.lua` 21 項。**請使用者測**：選單「MiquellaLight: Character」看身體有沒有出現、原本的衣服有沒有消失、動作時關節變形、脖子接縫；三款切換比較。**權重只用主要骨頭**，膝肘肩如果折得難看 → 改用遊戲 `*_HJ_*` 輔助骨頭（例：從內衣用最近表面轉移權重、排除 `_CT`／`_CH_` 擺動骨頭）。膚色現在是雙劍的象牙材質（之後做膚色貼圖或抄遊戲的皮膚材質）
- **小腹（使用者 2026-10-02：「像中年老男人的啤酒肚」，側面下腹凸出）**：真正原因是骨架對齊把脊椎、骨盆拉到遊戲的 `Hip`（見下一條），修正後側面就平了；`flatten_belly`（正面輪廓壓成直線）反而推出怪凸起，**不用了**（`flat` 預設 False）。**腹部線條還等使用者挑**：`belly_options.png`（0 原本／1 收小腹 `stomach-pregnant-decr`／2＋緊實／3＋馬甲線／4＋人魚線／5 兩種，已用修正後的身體重畫），`python miquella_body.py abs ...`；挑好後把選的 `details`／`grooves` 併進 `VARIANTS`（或 `COMMON_DETAILS`）再跑 `kit`
- **胯下（使用者 2026-10-02：大腿和胯下是兩塊分開的結構，要有 V 形摺線，穿內褲反而更明顯）——做完、已裝進遊戲**：①`fit_targets` 不再把 MakeHuman 的 `spine01～05`、`pelvis` 拉到遊戲的 `Hip`／`Spine_0`（它們比髖關節高 11 cm，把胯下拉到髖關節高度、大腿和骨盆糊在一起）；軀幹只整體縮放平移，`obj["fit"]` 改成每根骨頭最後的位置（`bone_map` 用）；②`smooth_groin` 抹平髖接處的線性蒙皮皺摺；③`GROOVES["crease"]` 腹股溝摺線（三款共用 `BASE_GROOVES`，`base_grooves: []` 可關掉）：(0.030,0.815)→(0.048,0.852)→(0.078,0.912)→(0.118,0.985)，深 6.5 mm、寬 15 mm、側面也刻（`facing` 0.35）。比較圖 `python miquella_body.py groin ...` → `previews\groin\groin_options.png`。之後的長袍、內褲都不能把這條線蓋平
- **臀腿（使用者 2026-10-02 晚，給了參考圖；選了「修改後」）——做完、已裝進遊戲**：腹股溝收窄（10 mm）；`taper_thighs` 錐形大腿（`THIGH_TAPER` 0.53～0.80）；`soften_buttocks`（Taubin，`SOFT_BUTT`）；`bridge_cleft` 從裡面填平臀縫（`CLEFT`，細分後）；`buttocks-volume-incr` 0.75；`GROOVES["gluteal"]` 臀下弧線（`carve` 的第 5 個欄位 True＝刻在背面）。`BASE_GROOVES = ["crease", "gluteal"]`。參數 `cleft`／`taper`／`soft`／`base_grooves` 設 0 或空可關掉（`SHAPE_OPTIONS` 的「修改前」就是全關）。之後的長袍在臀部是貼身的，要照這個形狀
- **脖子（使用者 2026-10-02 晚：形狀扭曲、後頸像骨刺、分塊感）——做完、已裝進遊戲**：見第 0 節最新兩則。最後的做法：上背兩節脊椎轉去接脖子（`UPPER_BACK_SHARE`）、`NECK_SHIFT`；身體的脖子**蓋在臉的脖子外面**，沿每 5° 的曲線從身體表面相切貼上臉（`NECK_MERGE`、`NECK_LOW`），MakeHuman 的脖子切掉後重新長網格（`neck_tube`）、最上段法線轉成臉的（`match_face_normals`）、接縫附近抄臉的權重（`NECK_W`）。**試過不行的**：身體在臉裡面、只在下緣接上（臉的直筒脖子像插進身體，分塊感）；身體在臉外面只蓋住下緣（鋸齒線、一圈領子）；整段包到下巴（MakeHuman 的後腦勺擠進後頸）；每格最外側的半徑（後腦勺底面 → 骨刺）；用 MakeHuman 自己的點推上曲線（擠成一團、摺起來，臉從縫裡穿出來 1.3 cm）
- **身體線條（使用者 2026-10-02 晚交給 Claude 決定）——做完**：收腰＋馬甲線＋背溝，三款都有；人魚線不加
- **下一步（頭冠驗證後）**：①~~匯入內衣四件、量體型~~（做了，研究筆記第 18 節）；②~~自己做身體~~（上一條）（纖細、平滑）＋長袍（上半身貼身、下擺擺動）原型，**放在遊戲的身體旁邊並排**給使用者挑體型；③頭髮（擺動鏈）。長袍下擺的擺動要學內衣身體的 `chain2`。內衣身體的模型有「群組」（0～14，穿防具時遊戲藏掉被蓋住的部分），掛上去時要把原本的內衣／防具藏起來（`set_DrawSelf(false)` 或關材質）

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
