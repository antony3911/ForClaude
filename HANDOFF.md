# 交接紀錄：米凱拉風格《魔物獵人 荒野》mod

最後更新：2026-10-04（**早上 8 點：第二帳號、使用者在場，Claude 自己操作遊戲：長袍全黑、分節修好，腿穿出裙子還在查（第 0 節）**；**早上 4 點半：使用者的待辦清單寫在第 0 節最上面，換第二帳號接手**；**人物 session（凌晨 2～3 點）：長袍遊戲版第一版（素面 `smooth`，男女各一）做好、已裝進遊戲，等實測；下擺借遊戲防具 `ch03_025_0015` 的 chain2 擺動；身體被長袍蓋住的部分拆成獨立材質、穿長袍時關掉；使用者給了臉的方向（見第 0 節）；垂墜兩款＋金飾、臉的骨頭微調腳本也做了、都已裝進遊戲**；之前（**人物 session（凌晨）：長袍設計定案——四款可切換（貼身、不露線條＝素面；垂墜＋腰帶鬆掛／束緊＝金飾＋全金寬領「丁」），腳本物件的擺動物理實測可行（`Chain2`＋`ChildSecondary`），下一步做遊戲版，見第 9 節「人物」第 3 項**；之前（**人物 session（深夜）：頭冠錯位修好、會發光了（遊戲裡確認），大小 0.8～0.9 可調**）；之前（**人物 session（晚上）：身體改接女獵人的臉和骨架（使用者的獵人是女的；米凱拉本身是男性、體型不變）、脖子根提高 3 cm 讓脖子變短（使用者選 C）、胸口磨平，已裝進遊戲、等實測，見第 9 節「人物」**；之前（**人物 session（早上）：身體第一次實測後修了光照、斑塊、腳掌，膚色最新版待看，斜方肌／胸口／脖子接縫待改，見第 9 節「人物」**；**本機 session（武器附加物，使用者外出中）**：輕弩速射彈鼓 A、重弩彈匣 C（改成吊在槍下的六角燈籠）、**重弩防禦盾 D 光輪**（使用者選的）做成遊戲版、已裝進遊戲；槍托查完（我們的槍托跟原版位置差不多），加了握持記錄器等實測資料；追蹤箭、龍穿點火的遊戲檔還沒確定，見第 0 節）。之前（**雲端 session（武器附加物）：使用者選好了**——輕弩速射彈鼓 A 象牙燈籠、重弩彈匣 C 聖匣、追蹤箭 B 光花綻放、龍穿點火 D 卷草鑽；重弩的盾重新設計成槍管上的光環往後拉、擴大成盾，第二輪四版等使用者挑；**另外使用者發現輕弩、重弩的槍托人物都沒去抓**，要本機 session 查，見第 0 節）。之前（**本機 session（人物）：頭髮設計定案**——遊戲髮型 512 為底＋細編髮、肩前粗編髮、大編髮加長，見第 9 節「人物」第 4 項）。**武器（第一帳號，2026-10-03 07:45）**：**銃槍打掉重練成聖百合**（蓄力時花前長出光之百合、槍身長出光葉和小光百合，跟著蓄力連續長，已裝進遊戲、等實測）；第七輪修正（螺旋跟著蓄力連續伸長、弓一朵一朵開、太刀氣刃蓄力、操蟲棍精華和三燈蓄力 D、輕弩花苞）全部做完、已裝進遊戲，等實測；HANDOFF 的武器部分整理過，現況在第 9 節「武器」，舊留言和每一輪實測紀錄的原文在 `mods/miquella/WEAPONS_LOG.md`。之前（人物）：第二帳號 2026-10-03 早上：脖子照原版接法重做、已裝進遊戲；本機 session（第一帳號）：脖子接縫重做（身體從外面相切貼上臉的脖子）；身體修正（骨架對齊造成的啤酒肚、腹股溝摺線）；頭冠進遊戲（角色第一步）。分支 `claude/two-account-handoff-plan`。分工：**第一帳號＝武器**（換裝腳本、特效腳本、武器／裝置 kit），**第二帳號＝人物**；兩邊在同一個資料夾工作，commit 只加自己的檔案

> **新的 session 先讀完這份**，再依需要讀第 2 節列的文件。這份是總覽和索引，細節都在各文件裡。
> 做完任何一步，就更新第 9 節「下一步」和第 4 節的進度表，commit 並 push。

---

## 0. 兩個帳號之間的留言

**人物 session（第二帳號）→ 下一個 session（2026-10-04 早上 8 點，最新）**：使用者在旁邊，**授權 Claude 操作整台電腦（不碰 LINE 等社群）**，這次 Claude 自己開關遊戲、進存檔、操作選單、截圖（做法見第 9 節「人物」→「自己操作遊戲」）。長袍第一次在遊戲裡看：①素面、透線條**全黑** → 模型只有布一個材質、`mq_robe.mdf2` 加了金飾變兩個，對不上就連不上材質（`get_MaterialLinked` 失敗）→ 改用只有布的 `mq_robe_cloth.mdf2`，**已確認修好**；②**手臂、軀幹一格一格的分節** → 長袍從身體複製時帶著身體的 UV，匯出用的是那層（布紋被身體的 UV 島撐成幾公分寬的方塊）→ `robe_kit.unwrap` 先刪舊 UV 層，八件重建，**已確認修好**；③金飾太暗像咖啡色麻繩 → 發光貼圖改白、腳本塗金色發光，選單 `Gold glow`（**偏白，待跟使用者調**）；④**腿穿出裙子（還沒修）**：遊戲的防具靠 `app.ChainSetting`＋`via.character.CollisionShapePreset`（`.clsp`）接碰撞，我們只有 Chain2；即時加上去（`MiquellaLight_ChainTest.lua`）有一點效果，但**裙擺在遊戲裡被重力拉成直筒、比站姿兩腿窄**，下一步見第 9 節。使用者的新點子：**高衩旗袍款，衩開到內褲下方的臀線**（DESIGN.md「服裝」，之後做、不急）。臉還沒看（鏡頭拉不近，攝影棚腳本 `MiquellaLight_Booth.lua` 設鏡頭沒作用）

**本機 session → 下一個 session（2026-10-03，握把定案，最新）**：**使用者選了一體式槍托 A3**（握把和槍托一整塊、中間拇指孔、條紋繞孔一圈、金絲雙向交叉繞著，`prototypes/bowgun_grip/grip_onepiece_gold.png` 第 5 欄）→ **重弩、輕弩的遊戲版都重做了、已裝進遊戲，等實測**（`bowgun.py` 的 `stock_and_body`，`ONE_PIECE = True`；舊的槍托＋握把設 False 就回來）。要看：拇指孔的位置跟手、手臂有沒有穿模，金絲夠不夠亮。下面是定案前的經過：**使用者更正：不是槍托，是「握把」人物都不會去握**（下面槍托的查法照樣有用）。使用者要先跟原版確認三個問題、**不要急著做方案**。查了（`bowgun_grip_survey.py`，圖 `MiquellaTools\work\previews\grip\zoom_lbg.png`、`zoom_hbg.png`，含原版、不進 repo，已傳給使用者）：③**不是每把原版都有握把**：輕弩 11 把約一半（it1300_0002、0005、0006、it1310_0001、0003）在我們握把的位置有往後斜的握把，另一半（it1300_0001、0003／0004／it1310_0002 那一型、it1310_0000）那裡沒有握把；重弩 5 把都沒有完整握把，頂多一小截；②同一種武器共用同一套動作、手的位置每把都一樣，一半輕弩和全部重弩那裡根本沒握把 → **原版的握把多半也沒被握，是正常的**；①有握把的原版，握把都跟我們的差不多位置 → 我們沒放錯。要百分之百確定，看握持記錄器的資料（下面）。→ 使用者要看「不握也自然」的方案：`grip_options.py` → `prototypes/bowgun_grip/grip_options.png`（A 卷草垂飾／B 光滴垂飾／C 拿掉握把改金絲卷草／D 編髮垂飾，重弩、輕弩各側面＋背後）；使用者又問「繞回去跟槍托合體的握把」→ 第二組 `grip_options.py <out> loop` → `grip_loop_options.png`（握把底部接回槍托下緣、像拇指孔槍托：A 編織環／B 卷草橋／C 三叉回流／D 光弧）；使用者：「別用原本握把為基礎，直接設計一個連回去的」→ 第三組 `grip_options.py <out> frame` → `grip_frame_options.png`（沒有握把，一整個框從機匣下面繞回槍托：A 卷草框／B 枝條框／C 豎琴框／D 編髮框，`frame_line` 是共用的中心線）；使用者：「太沒有合體感，槍托跟握把是兩個不同元素，希望一體式」→ 第四組 `grip_options.py <out> one` → `grip_onepiece_options.png`：**槍托＋握把變成一圈繞著拇指孔的編織環**（`bowgun_onepiece.py`：外輪廓 `OUTER` 和洞 `HOLE` 兩條對應的閉合曲線之間放樣，截面是側面平的超橢圓，條紋順著環走；A 大拇指孔／B 小拇指孔／C 鏤空編織／D 編髮）；**使用者選 A，要在 A 上繞 D 的金絲** → `grip_options.py <out> gold` → `grip_onepiece_gold.png`（A1 留洞邊金線／A2 拿掉洞邊金線／A3 金絲雙向交叉；金絲三股、離編織面 `lift`、用 MiquellaGlow 的金色），**等使用者挑**；做成遊戲版時：`hb.STOCK_END` 縮到握把前、`pistol_grip` 換成環（`grip_options.py` 的 `one_piece` 就是這樣接的）；挑好後在 `bowgun.py` 的 `pistol_grip` 換掉（輕弩共用），重做兩把 kit。槍托版的草稿 `MiquellaTools\work\addons_probe\stock_options.py`（使用者講錯，不用了）

**本機 session（武器附加物）→ 下一個 session（2026-10-03）**：雲端留的附加物和槍托都處理了（使用者外出、沒法確認，做完的都裝進遊戲了，**等實測**）：
- **輕弩速射彈鼓 A 象牙燈籠**、**重弩彈匣 C 聖匣**：蓋過遊戲共用的 `it1399_0000_0`／`it1299_0000_0`（每把輕弩／重弩的 prefab 都指向它們，不用腳本），pak `MiquellaLight_LBGDrum`、`MiquellaLight_HBGMag`。彈鼓照原版放在槍身側面、軸沿槍管；**彈匣第一版照原版斜掛側面，使用者看預覽說「放在旁邊的方形很醜」→ 改成吊在槍身下面（跟提案圖一樣）的六角燈籠**。細節 `mhws/MiquellaLight_BowgunAddons_kit/README.md`
- **重弩防禦盾：使用者選 D 光輪** → 遊戲版做好：防禦時四個光環滑到機匣前撐大、24 道光芒射出、三顆光點飛到盾緣（換裝腳本 `GL.update_guard`／`apply_guard`，重弩 kit 多了 64 根光環骨頭＋24 根光芒骨頭）。**防禦是用動作名稱含「Guard」偵測的（猜的）**；選單有「Hold the guard open (test)」可以強制打開
- **槍托**：解出 11 把原版輕弩、5 把原版重弩疊起來比（`bowgun_stock_overlay.py`，圖 `MiquellaTools\work\previews\addons\stock_overlay.png` 已傳給使用者）：**原版都有槍托，位置、長度跟我們的差不多** → 不是③（原版沒槍托），我們的槍托也沒放錯；要知道手和肩膀實際在哪，換裝腳本加了**握持記錄器**（跟欄位記錄器一起開）：拿輕弩／重弩時把雙手、前臂、上臂、肩膀、頭在武器座標的位置依動作存成 `reframework/data/MiquellaLight/grip_<處理器>.json` → **使用者下次拿輕弩、重弩各玩一分鐘（待機、架槍、開火、裝填、速射／點火、防禦）後讀這個檔**，再決定握把／槍托怎麼改（第 9 節「武器」→「槍托問題」）
- **追蹤箭 B、龍穿點火 D：遊戲檔還沒確定，沒做**（見第 9 節）：`it1299_0001_0`（四片會掀開的板子）是某種點火模式裝在槍上的裝置、不是彈頭；重弩特殊彈的特效 `11_it12_100～105` 大多沒有模型，龍穿點火的彈頭可能是純特效（那就要用腳本生成模型飛出去，新做法）。下次請使用者開 FxProbe 錄一次追蹤箭、一次龍穿點火

**雲端 session（武器附加物）→ 本機 session（2026-10-03；本機已處理，見上面）**：
- **使用者選好的附加物**（預覽 `prototypes/attachments/*.png`，程式 `attachments.py`，規格 DESIGN.md「武器附加物・提案」）：**輕弩速射彈鼓 A 象牙燈籠**、**重弩彈匣 C 聖匣**、**弓追蹤箭 B 光花綻放**、**重弩龍穿點火 D 卷草鑽** → 要做遊戲版。雲端碰不到遊戲，**每樣是哪個遊戲檔、什麼時候出現都還沒確認**，先在遊戲裡找（做法見第 9 節「武器」→「附加物遊戲版」）
- **重弩的盾**：四個版本都沒選，使用者要「利用光環讓它變形：往後拉到盾的位置、擴展變成盾」→ **第二輪四版做好了，等使用者挑**（`prototypes/attachments/hbg_guard.png`、動畫 `hbg_guard.gif`；A 同心光環／B 樹紋光環／C 光環穹頂／D 光輪，DESIGN.md「重弩防禦盾・第二輪」），挑好之前先不用做
- **槍托問題（使用者 2026-10-03，要本機查）**：「輕弩、重弩的槍托，人物都不會去抓到那個位置」，使用者不確定是①人物抓的位置有問題（我們的模型沒對齊手）、②原版其他設計本來就不把槍托放在那、還是③原版根本沒有槍托。查法和要決定的事在第 9 節「武器」→「槍托問題」；**結論和對照圖給使用者看、讓他決定，不要自己改**
- 雲端也能畫預覽：`pip install bpy==4.5.3`（venv），中文字型用文泉驛

**第一帳號（武器）→ 大家（2026-10-03 06:40，最新）**：使用者 2026-10-02 23:39 實測後的武器要求（弓一朵一朵開、螺旋做成動畫、太刀「氣刃大迴旋斬」的蓄力、操蟲棍光球沒出現、輕弩花苞埋在地下）和之後追加的（螺旋要像動畫連續伸長、操蟲棍三燈蓄力選了 D 三色光旋、操蟲棍攻擊軌跡先紅再金）**全部做完、已裝進遊戲，等實測**。要測什麼、還沒做的、遊戲欄位速查都在第 9 節「武器」。換裝腳本、特效腳本、`arsenal.py`、`build_weapon_kit.py`、`build_device_kit.py`、武器／裝置 kit 在第一帳號手上；人物的檔案第一帳號不碰。HANDOFF 的武器部分這時整理過：10-01～10-03 的武器留言、每一輪實測紀錄的原文搬到 `mods/miquella/WEAPONS_LOG.md`。**下面人物 session 說的雙劍 NRRO 貼圖收到了**：重轉會改變所有武器象牙部分的外觀，先等使用者決定（第 8 節），還沒動
**→ 07:15 使用者：NRRO 先不弄（第二帳號膚質卡關很久，不急）；銃槍打掉重練**（「原本的銃槍很不好做特效，而且看起來挺簡陋的、很沒設計感」，**金針保留**：「金針不賴」）→ 四個方向的設計圖 `prototypes/gunlance/gunlance_redesign.png`（A 金針聖匣／B 聖百合／C 聖樹／D 聖翼，上排平時、中排近看、下排龍擊砲），**等使用者挑**；每個方向的特效做法在 DESIGN.md「銃槍重新設計・提案」
**→ 07:20 使用者選 B 聖百合**（「非常好看」「已經很完美了」）但**蓄力力量感不足，要加；原本的元素一個都不能砍，只加** → 四個加法 `prototypes/gunlance/gunlance_lily_charge.png`（A 金藤螺旋／B 光瓣旋輪／C 光之百合／D 聚光旋渦，各畫一段、二段、滿）
**→ 07:25 使用者選 C 光之百合**（「非常好」），但只有槍尖變化有點空，**槍身也要變**（一樣只加）→ `prototypes/gunlance/gunlance_lily_body.png`：C1 光葉／C2 光花（花苞開成小光百合）／C3 光藤／C4 三者全加
**→ 07:30 使用者定案：聖百合＋光之百合＋光葉＋光花（不要光藤），蓄力要「動畫，不是分段模型」→ 07:45 遊戲版做完、已裝進遊戲（遊戲關著直接裝，`work\install` 也放了一份），等實測**：光的零件做成滿蓄力大小、126 根骨頭從小撐到大，象牙花瓣用骨頭往後翻，跟著蓄力砲擊的計時器／龍擊砲的蓄能時間連續走（龍擊砲第一次發射就記下實際蓄能長度）；五個花苞尖的光滴＝彈數。動畫預覽 `MiquellaTools\work\previews\gunlance\bloom\lily.gif`、`lily_head.gif` 已傳給使用者。測試 234 項全過。盾還是舊的樹紋能量盾

**人物 session → 第一帳號（武器，2026-10-03 清晨，重要）**：**雙劍 kit 的 NRRO 貼圖是壞的**（當初在雲端 Linux 轉檔）：`MiquellaIvory_NRRO.tex` 解碼出來是 (8, 14, 56, 128)，原始 PNG 是 (102, 128, 255, 128)＝RGB 被乘了 alpha 0.5 再轉 sRGB → 遊戲裡粗糙度 0.03（像鏡面金屬）、法線 Y 歪到 -0.9、AO 0.22（整個壓暗）。**所有用雙劍貼圖的象牙／握把部分都受影響**（武器有金光蓋著所以沒發現；身體用了同一張才看出來：陰影處全黑、調色只變明暗）。本機重新轉檔就正確（`build_game_kit.py` 的 `convert_textures`；texconv 讀 PNG 要先 `CoInitializeEx`，bpy 環境裡已初始化）。身體已改用自己的貼圖、沒動武器的；**要不要重轉雙劍貼圖由你／使用者決定**（修好後象牙部分會變亮、變霧面，外觀跟使用者確認過的不同）。其他雲端轉的 kit 貼圖（裝置 `Devices/tex` 等）可能也一樣，用 scratchpad 的解碼法檢查：Tex 讀 mip0 → 包成 DX10 DDS → Pillow 解 BC7

**人物 session（第一帳號）→ 第二帳號（2026-10-04 早上 4 點半，最新；使用者去睡了，換第二帳號接手）**：長袍四款、臉的骨頭微調腳本都做完、裝進遊戲了，**全部還沒在遊戲裡實測**（做了什麼見下一則留言和第 9 節「人物」第 3、3b 項）。使用者會照下面的清單提供東西；**接手時先看清單哪些做了**（`MiquellaTools\refs\` 有沒有圖、遊戲資料夾 `reframework/data/MiquellaLight/` 的 `robe_debug.json`、`face_debug.json` 有沒有新的時間），使用者的回答在對話裡。
- **使用者的待辦清單（第一帳號整理給使用者的，照優先順序；能做多少算多少）**：
  - **A. 進遊戲 5～10 分鐘（最有價值，Claude 讀診斷檔，不用截圖）**：①開遊戲進據點／營地；②Insert → Script Generated UI → **MiquellaLight: Character → Outfit** 四款（Robe, plain／body lines／drape, loose sash／drape, cinched）各走、跑、翻滾 20～30 秒，怪的地方記一句（腿穿出裙子、布或金飾怪、太白太黃）；③**MiquellaLight: Face**（預設開著）：看臉、開關比較、眨眼說話時怪不怪；④臉的正面、側面各截一張（Steam F12）放 refs；⑤順便看舊問題：頭冠大小 0.8 還是 0.9、膚色跟臉合不合、大腿內側還有沒有結塊、內褲顏色、身體 A／B／C 選哪款；⑥關遊戲
  - **B. 放檔案到 `C:\Users\anton\MiquellaTools\refs\`**（沒有就新建）：使用者在聊天裡貼的三張畫師米凱拉圖（Claude 存不下來，要使用者存檔）、有的話官方米凱拉臉部圖（正面、側面、近拍）、A④ 的遊戲截圖
  - **C. 決定／授權**：①臉：骨頭微調當底，不夠的話**准不准改女臉模型**（保留網格、UV、骨頭，只改形狀）、現在的捏臉要不要保留當底；②**下載授權**：借來的裙擺物理不行時，下載 **RE Chain Editor**（GitHub NSACloud/RE-Chain-Editor，Blender 外掛，幾 MB）自己寫擺動和碰撞；③**截圖授權**：computer-use 截遊戲畫面（只能截、不能操作，要使用者開著遊戲）；④**使用者睡覺時做什麼**：頭髮遊戲版（設計已定案），或長袍改進（碰撞、垂墜接縫），或都不做省 token；⑤**自動接手**：額度用完要不要排程重置後自動開新 session
- **接手後怎麼做**：
  - 有 A 的資料：讀 `robe_debug.json`（`swingMm` ~0＝物理沒跑；`chain2Type`／`hunterChainSetting` 是研究腿碰撞的線索）、`face_debug.json`（`takenFromGame`／`keptOurs`、`phases`，臉沒變就是遊戲更晚又設一次），照使用者的意見修，**修完要重建的**：長袍 `robe_kit.py <款> female|male`（四款×男女）→ `make_patch_pak.py` 打包 `MiquellaLight_Character.pak` → 遊戲沒開就直接裝（指令見第 4 節「遊戲端」）
  - 有 B 的圖：照圖修 `MiquellaLight_Face.lua` 的預設值（`face_tune_preview.py` 先出預覽給使用者看），或照 C① 的決定開始改女臉模型
  - 都沒有：照 C④ 的回答做；沒回答就**不要自己開大項目**（使用者在意 token），只做不需要使用者的小整理
**人物 session → 下一個人物 session（2026-10-04 凌晨 3 點）**：**長袍遊戲版第一版裝進遊戲了，等使用者實測**（使用者在睡覺）。做了什麼、怎麼測、下一步在第 9 節「人物」第 3 項。重點：①**四款都做了**：素面 `smooth`、貼身透線條 `lines`、垂墜＋腰帶鬆掛 `drape`、垂墜＋腰帶束緊 `cinch`（垂墜兩款帶金飾：全金寬領丁、窄金邊、金環腰帶＋垂繩金墜），男女各一（`mq_robe_<款>_c[_f].mesh`，`robe_kit.py`）；②下擺綁到遊戲女防具 `ch03_025_0015`（到小腿的裙子）的 12 條裙擺骨鏈，骨頭搬到我們的下擺上，腳本給物件加 `Chain2`＋`ChildSecondary`、引用遊戲自己的 `ch03_025_0015.chain2`（不散布卡普空檔案）；**腿的碰撞不確定有沒有**（遊戲的碰撞在各部位的 `.clsp`，腳本物件吃不吃得到不知道；腳本把 Chain2／app.ChainSetting 的成員寫進 `robe_debug.json` 供研究）；③身體重建：被蓋住的部分拆成 `MiquellaSkinChest`／`MiquellaSkinWaist`／`MiquellaClothWaist`，穿長袍時關掉；④選單「Outfit」選 None／Robe, plain／Robe, body lines／Robe, drape, loose sash／Robe, drape, cinched。**臉**：使用者給了三張喜歡的畫師圖（不進 repo），方向寫在 DESIGN.md「臉」：下垂眼、眼皮半垂、居高臨下又在玩弄人的傲氣眼神、一邊嘴角微揚；要有魔性的吸引力（官方魅惑設定），**不要媚眼、不往色情走**（使用者自己說的）。**臉的第三條路做好了、已裝進遊戲（預設開著），等實測**：`MiquellaLight_Face.lua` 用臉自己的骨頭（外眼角、上下眼皮、嘴角、眉）每幀疊加微調，不換臉、不改遊戲檔、表情照常；選單 MiquellaLight: Face 有滑桿；概念預覽 `MiquellaTools\work\previewsaceace_tune_sheet.png` 已傳給使用者（第 9 節「人物」3b）。做臉還缺：參考圖放 `MiquellaTools
efs\`、遊戲裡獵人臉的截圖、要不要再加捏臉／改模型。**排程**：使用者要求額度重置後自動接手（04:40 的 `miquella-robe-handoff`），這個 session 重置後自己接著做完了，排程已刪掉
**人物 session → 下一個人物 session（2026-10-04 凌晨）**：**長袍開工**。①腳本生成的物件**可以有擺動物理**：要加 `via.motion.Chain2`＋`via.motion.ChildSecondary`（只有 Chain2 不會動），實測紀錄在研究筆記第 15 節；②設計提案 `robe_designs.py`：版型三種（貼身透線條／不露線條／垂墜）使用者都要留，飾品全部金屬金飾，使用者提議上衣和下擺交界放金環束帶（D 款）；**等使用者挑裝飾、決定項圈**。細節在第 9 節「人物」第 3 項、DESIGN.md「服裝」
**人物 session → 下一個人物 session（2026-10-03 深夜）**：**頭冠修好了**（使用者在遊戲裡看過）：脖子那圈黑帶就是頭冠——腳本的 `Quaternion.new` 參數順序寫反（REFramework 是 w, x, y, z），頭冠上下顛倒掛在頭骨頭下面；不發光是因為材質抄象牙、`Emissive_Power` 0。現在戴在額頭、會發金光；大小使用者覺得 0.8～0.9 都好、還沒決定 → 選單 Size 只開這個範圍（預設 0.85），Glow 也保留可調。細節見第 9 節「人物」和 `MiquellaLight_Character/README.md`。**另外**：頭冠腳本每秒寫 `circlet_debug.json`，使用者這次**拒絕了截遊戲畫面**的授權，看位置類的問題可以先讀這種診斷檔
**人物 session → 下一個人物 session（2026-10-03 晚上）**：（**後來**：內凹肚臍、三角褲定案、胸部最小、腰部以下用遊戲內衣褲的權重，都已裝進遊戲；使用者看了「基本上已經很好了」；**下一步先修頭冠錯位**，見第 9 節「人物」下一步）**米凱拉是男性**（使用者：「米凱拉是男的，只是要盡可能瘦弱、女性風格的身材」），但**使用者的獵人是女獵人**（臉 `ch00_001_0000`、頭髮 `ch01_001_0512`、防具 `ch03`），這只關係到身體要接哪副骨架和哪張臉，講的時候要先說清楚，不然使用者會以為要把米凱拉改成女的。這次：①身體原本照男獵人的臉、骨架做，女臉脖子低 1～2 cm、細 4 mm、女骨架肩膀窄 2 cm → 改成男女各一套（`_f`），腳本看臉自動選；②使用者：脖子正面「V 字拉太長」、背面「脖子太長有拉伸感」→ 脖子根一圈提高 3 cm、脖子管縮短（四版選 C）；③胸口磨平。**都已裝進遊戲、使用者還沒看**（膚色最新版也還沒看）。細節在**第 9 節「人物」**
**人物 session → 下一個人物 session（2026-10-03 早上）**：身體第一次在遊戲裡實測，修了光照（StencilValue）、斑塊（頂點顏色＝位置）、腳掌；膚色最新版（SkinEdit＋臉脖子底色＋×2.9）裝好但使用者還沒看

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
| 頭冠（光環） | v10：髮帶散成細枝 → 捲成一束 → 三叉往後掃，整個發金光；遊戲版**遊戲裡確認（2026-10-03 深夜）**：戴在額頭、發金光；大小 0.8～0.9 選單可調（使用者還沒決定）、Glow 可調 | `prototypes/circlet/`、`mhws/MiquellaLight_Character*/` |
| 角色概念（人台） | 長袍、編髮、頭冠戴在頭髮上；v4 頭髮改成遊戲用的髮片做法 | `prototypes/character_concept/` |
| 身體 | 三款 A／B／C（MakeHuman CC0）掛在獵人骨架上，**已實測**（2026-10-03）：光照、斑塊、腳掌修好；膚色調整中；**晚上：男女獵人各一套（使用者是女獵人）、脖子變短、胸口磨平，已裝、等實測**。細節見第 9 節「人物」 | `prototypes/scripts/miquella_body.py`、`mhws/MiquellaLight_Character_kit/` |
| 頭髮 | **設計定案（2026-10-03）**：遊戲髮型 512 為底＋背後 10 條細編髮、肩前左右各一條粗編髮、大編髮加長；預覽 OK，**還沒做進遊戲**。細節見第 9 節「人物」第 4 項 | `prototypes/scripts/hair512_braids.py` |
| 臉 | **骨頭微調腳本 `MiquellaLight_Face`（2026-10-04，已裝、預設開著、等實測）**：下垂眼、上眼皮半垂、下眼皮微推、單邊嘴角上揚、單眉微挑，滑桿可調；方向見 DESIGN.md「臉」 | `mhws/MiquellaLight_Face/`、`prototypes/scripts/face_tune_preview.py` |
| 長袍 | **遊戲裡第一次實測（2026-10-04 早上，第二帳號，Claude 自己操作遊戲）**：全黑（材質沒連上）、分節／格子（用了身體的 UV）**都修好、遊戲裡確認**；金飾加了發光（偏白，待調）；**還沒好：腿穿出裙子**（沒有碰撞＋裙擺被重力拉窄，見第 9 節「人物」第 3 項）。四款：素面、貼身透線條、垂墜鬆掛、垂墜束緊（帶金飾），男女各一 | `prototypes/scripts/robe_designs.py`、`robe_kit.py`、`mhws/MiquellaLight_Character_kit/` |

### 武器造型（全部定案，除非使用者再改）
| 武器 | 定案的設計（細節見 DESIGN.md 第 5 節） | 位置 |
|---|---|---|
| 雙劍 | v4：葉形光刃、編織柄、護手兩側三叉；**已做成遊戲素材包＋可安裝的測試版** | `prototypes/dual_blades/`、`mhws/` |
| 片手劍 | 光劍＋樹狀紋章能量盾 | `prototypes/sword_shield/` |
| 太刀 | 彎刃＋刃紋、懸浮光環當刀鐔、編織刀柄 | `prototypes/long_sword/` |
| 重弩、輕弩 | **槍托＋握把一體式 A3**（2026-10-03：一整塊、中間拇指孔、條紋繞孔一圈、金絲雙向交叉，已裝、等實測）；光環隧道、懸浮光環；**槍管上方、靠前的三顆懸浮光點**（使用者很喜歡輕弩）；**輕弩遊戲裡看過，位置正確**；光束上五個環磁浮（使用者說不錯）、光點速射量表（等實測） | `prototypes/heavy_bowgun/`、`light_bowgun/`、`mhws/MiquellaLight_LightBowgun_kit/` |
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
| 重弩龍穿點火 | **D 卷草鑽**（2026-10-03 使用者選）：三股象牙絞成鑽尖、金線、光芯，尾端三個往回捲的卷草；從魔物身上貫穿而出 `prototypes/attachments/piercer.png` | 選好，**遊戲檔還沒確定**（`it1299_0001_0` 不是彈頭；彈頭可能是純特效，要 FxProbe 錄） |
| 輕弩地雷彈 | 象牙花苞包著光，被打到綻開再爆；遊戲版落地就綻開，**2026-10-03 抬到地面上**（之前八成埋在地下） | 同上 |
| 弓追蹤箭 | **B 光花綻放**（2026-10-03 使用者選）：插箭處象牙花在皮上綻開、金光花緣，打越多開越大，快爆時全開、升起光蕊和光環；箭尾一滴光＋一圈光環 `prototypes/attachments/tracer.png` | 選好，**遊戲檔還沒確定**（要 FxProbe 錄一次） |
| 輕弩速射彈鼓（新） | **A 象牙燈籠**（2026-10-03 使用者選）：兩圈象牙框、斜的象牙肋骨籠子、兩面金絲卷草＋發光軸心，籠裡一圈光滴＝子彈 `prototypes/attachments/lbg_drum.png` | **遊戲版已裝、等實測**：蓋過 `it1399_0000_0`，照原版放在槍身側面、軸沿槍管（`MiquellaLight_LBGDrum.pak`） |
| 重弩彈匣（新） | **C 聖匣**（2026-10-03 使用者選）：哥德式小聖物匣，象牙柱、金光尖拱窗、裡面吊一大滴光、底下倒過來的卷草尖塔 `prototypes/attachments/hbg_mag.png` | **遊戲版已裝、等實測**：蓋過 `it1299_0000_0`；側面方盒使用者說醜 → **吊在槍下的六角燈籠**（`MiquellaLight_HBGMag.pak`） |
| 重弩防禦盾（新） | 第一輪四版都沒選；第二輪（槍管上的光環往後拉、擴大成盾）**使用者選 D 光輪**（2026-10-03）：四個光環滑到機匣前收成同心光輪，外圈射出 24 道長短交錯的光芒，三顆光點飛到盾緣 `prototypes/attachments/hbg_guard.png` | **遊戲版已裝、等實測**（重弩 kit＋換裝腳本；防禦偵測用動作名稱含 Guard，選單可強制打開） |
| 狩獵笛響玉 | 地上光環＋浮空金膜泡泡，攻擊時共鳴 | 同上 |

**遊戲版（2026-10-02）**：龍杭（金針）、起爆龍彈（花苞）已做成遊戲的特效模型並裝進遊戲（`mhws/MiquellaLight_Devices_kit/`），等實測；其他三個的遊戲檔還沒確定

### 遊戲端（`mods/miquella/mhws/`）

- **遊戲**在 `C:\Program Files (x86)\Steam\steamapps\common\MonsterHunterWilds`（不用系統管理員權限就能寫）。REFramework＝`dinput8.dll`（nightly-01424，所有 RE 遊戲共用的 `REFramework.zip`，只放這個檔）；pak 放 `pak_mods/`（REFramework 的 PAK Directory Loading 預設開，不用 Fluffy）。全部移除：刪 `dinput8.dll`、`reframework/`、`pak_mods/`。遊戲資料夾的 `re2_framework_log.txt` 可以直接讀來除錯
- **人物這邊裝在遊戲裡的**：`MiquellaLight_Character.lua`（頭冠、身體、長袍）、`MiquellaLight_Face.lua`（臉的骨頭微調，2026-10-04）＋`MiquellaLight_Character.pak`
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
- **附加物不要照原版硬掛在側面**（2026-10-03 重弩彈匣：「放在旁邊的方形很醜」）：模型擺哪是我們決定的（只有骨頭是遊戲的），照使用者看過的提案圖放；形狀避免方盒，用往下收窄、鏤空的造型
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
| `bpy45\Scripts\python build_weapon_kit.py lbg_drum／hbg_mag <kit> <原版 .mesh> <雙劍 .mdf2>` | **附加物遊戲版**：輕弩彈鼓（`it1399_0000_0`）、重弩彈匣（`it1299_0000_0`，`attachments.py` 的 `mag_c_lantern`），蓋過遊戲原檔路徑（kit `mhws/MiquellaLight_BowgunAddons_kit/`） |
| `bpy45\Scripts\python preview_addons.py <out.png> <標題> <.mesh>... [ghost:<原版 .mesh>]` | 幾個遊戲模型放在一起（槍＋附加物）的側面、玩家視角、前方三張；`ghost:` 畫原版的灰色半透明（有原版的圖不進 repo） |
| `bpy45\Scripts\python preview_guard.py <kit .blend> <wp_miquella_hbg_guard.lua> <out.png> [gif]` | **重弩防禦盾 D 光輪的遊戲版預覽**：照換裝腳本的骨頭算法展開 0～100 %，前方＋玩家視角 |
| `bpy45\Scripts\python bowgun_stock_overlay.py <out.png>` | **槍托對照**：解出的原版輕弩／重弩側面疊起來，跟我們的輪廓比（含原版，不進 repo） |
| `bpy45\Scripts\python gunlance_designs.py <輸出> [test] [A B C D]` | **銃槍重新設計提案**（2026-10-03）：四個方向各畫平時、槍身近看、龍擊砲蓄能三張，拼成 `gunlance_redesign.png`；`test` 是低解析度快速試畫 |
| `bpy45\Scripts\python robe_kit.py <smooth\|lines> <female\|male> [preview <輸出>]` | **長袍遊戲版**：在身體 kit 的 C 款上做長袍（`robe_designs.py` 的版型）、上衣袖子抄身體權重、下擺綁 `ch03_025_0015` 的裙擺骨鏈、布紋貼圖、雙面材質 → `mq_robe_<版型>_c[_f].mesh`＋`mq_robe.mdf2`；`preview` 出靜止／下擺擺動／跨步的檢查圖（含身體，不進 repo） |
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
- （已決定 2026-10-03：輕弩速射彈鼓 A、重弩彈匣 C、追蹤箭 B、龍穿點火 D；**重弩防禦盾 D 光輪**，遊戲版已裝）
- **輕弩、重弩的握把**（2026-10-03；使用者先說槍托，後來更正是握把）：原版一半輕弩、全部重弩那裡沒握把，有的也在跟我們差不多的位置 → 沒被握是正常的；要維持現狀還是改成不握也自然的樣子，**等使用者決定**（第 0 節）。原本以為是槍托時查的：查過了，**原版都有槍托、位置跟我們的差不多**（對照圖已傳）；要不要改握把位置、縮短槍托或改成懸浮的象牙卷草收尾，**等握持記錄器的資料**（第 9 節）再給使用者看
- 四個新裝置（重弩、輕弩、弓、狩獵笛）使用者還沒回意見（重弩龍穿點火、弓追蹤箭併進上一項）
- 覆蓋原版檔案，還是用腳本掛上去（建議腳本掛載）
- 頭髮微光的做法（建議：編髮發光、散髮不發光）
- **臉的做法**（使用者 2026-10-03：「臉和頭髮之後也會設計吧」）：捏臉系統自己捏，或換臉部模型；**2026-10-04 加了第三條路：腳本微調臉的骨頭（`MiquellaLight_Face`，已裝、等實測）**，可以跟捏臉疊著用，不夠再考慮改模型。建議要換就**改遊戲的女臉**（保留網格、表情骨頭、脖子下緣那圈 48 點），不要整張重做：眨眼、表情、過場說話都靠它，而且臉的 shader 會依捏臉參數變形網格。這樣身體接脖子的做法不用改
- **高衩旗袍款長袍**（使用者 2026-10-04 看到右腿穿出裙子時想到的，**之後做、不急**）：規格見 DESIGN.md「服裝」
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
  - **附加物遊戲版（2026-10-03 本機 session 做的，等實測）**：
    - **輕弩速射彈鼓 A**（`it1399_0000_0`，pak `MiquellaLight_LBGDrum`）：速射模式時看彈鼓有沒有變成象牙燈籠、位置（槍身側面、軸沿槍管）對不對、遊戲轉鼓時籠子和光滴有沒有跟著轉（綁 `center`）、有沒有東西飛走
    - **重弩彈匣 C**（`it1299_0000_0`，pak `MiquellaLight_HBGMag`）：什麼時候出現（可能是點火模式）、吊在槍下的燈籠位置；`Piston` 骨頭搬進燈籠裡，特效 `11_it12_199` 的能量棒應該直立在燈籠裡（如果遊戲動畫會設 `Piston` 位置，能量棒會跑回側面）
    - **重弩防禦盾 D 光輪**（重弩 kit＋換裝腳本）：被正面打到／手動防禦時光環有沒有往後滑、撐大、射出光芒；選單 `Guard:` 一行會寫進度和當時的動作名稱，**沒反應的話**看那行的動作名稱（偵測條件是動作名稱含 `Guard`，`GL.update_guard`），或勾「Hold the guard open (test)」先看樣子；`joints found` 要是 88/88
    - **弓追蹤箭 B、重弩龍穿點火 D：遊戲檔還沒確定** → 請使用者開 FxProbe（Insert → Script Generated UI → MiquellaLight FX Probe → Start recording）各錄一次：弓射追蹤箭、讓它被打到爆；重弩切龍穿點火、射一發 → Stop and save，讀 `fx.json` 的 `effects`/`timeline`，再用 `efx_walk.py` 找特效用的模型。已知：重弩特效 `11_it12_030`（`Charge`，骨頭 `Piston`、`Crow`、`Board_*`）和 `11_it12_032` 是兩種點火的蓄能，`030` 用到 `it1299_0001_0`（四片會掀開的板子＋前端 `Crow`，裝在槍上），`11_it12_031`（`IsCancel`）把 `11_it1299_0001_0` 的零件炸飛；`11_it12_100～105` 大多沒用模型（`11_it12_102`：從 `VFX_Fire` 發射、有 `ChargeRate`／`AfterConst`、`P_head`＋`R_trail`，像貫穿彈，最可能是龍穿點火）→ **龍穿點火的彈頭可能是純特效**，那要用腳本生成我們的模型、跟著彈道飛（新做法，研究筆記 16 的 Armor VFX Manager 思路）。弓：`11_it11_012` 用 `it1199_0004_0`（0.34 m、沒骨架）＋`11_arrow_00`，可能跟追蹤箭有關
    - 重弩 `it1299_0001_0`（點火模式的裝置，四片板子會掀開）還是原版的樣子，要換的話等確認是哪種點火
  - **槍托問題（使用者 2026-10-03）**：「輕弩、重弩的槍托，人物都不會去抓到那個位置」。**查過的**：原版 11 把輕弩、5 把重弩疊起來（`bowgun_stock_overlay.py`）→ 原版都有槍托（visconGroup 3 是槍托，跟組 0 重複），輕弩都到 z -0.72～-1.07、高度跟我們的差不多；**所有原版共有的只有槍身那一段，沒有共同的握把位置**。所以不是③、也不是我們的槍托放錯；比較可能是②（遊戲動作本來就不碰槍托）或手握的地方跟我們的握把不同。**下一步**：使用者拿輕弩、重弩各玩一分鐘（欄位記錄器開著：待機、架槍、開火、裝填、速射／點火、防禦）→ 讀 `reframework/data/MiquellaLight/grip_app_cHunterWp13Handling.json`／`..Wp12..json`：每個動作 `R_Hand`、`L_Hand`、`R_UpperArm`、`R_Shoulder`… 在武器座標的 min／平均（`sum/n`）／max，`parent` 是武器掛的骨頭 → 跟我們的握把（輕弩約 z -0.3、往下）、槍托（到 -0.74）比，做對照圖和幾個改法（握把移到手的位置、槍托縮短、改成懸浮的象牙卷草收尾）給使用者挑，**不要自己定**
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

**人物（2026-10-03 早上本機 session 整理；下一個 session 從這裡接）**
- **現況**（都已裝進遊戲，選單「MiquellaLight: Character」；**使用者的獵人是女獵人**（米凱拉本身是男性、體型不分男女），目前選 C 款）：
  - **男女獵人各一套身體**（2026-10-03 晚上）：`mq_body_*.mesh`（男臉 `ch00_000`、骨架 `ch02_002_0002`）、`mq_body_*_f.mesh`（女臉 `ch00_001`、骨架 `ch03_002_0002`），腳本看獵人臉的路徑選，狀態列寫 `for a female hunter`。之前只有男的：女臉脖子下緣低 1～2 cm、細 4 mm，女骨架肩膀、手臂每邊窄 2 cm → 身體上緣浮在脖子外面（懷疑是接縫線）、肩膀被擠
  - **脖子變短**（2026-10-03 晚上，使用者看預覽：正面「V 字拉太長」、背面「脖子明顯太長、有拉伸感」）：脖子根一圈提高 3 cm（`NECK_LIFT`）、脖子管正面 3.5／側面 4／背面 4 cm（原本 5／7／9）；四版 B 2 cm／C 3 cm／D 4 cm 使用者選 C（D 肩線太平太方）。**胸口**磨平（`flatten_chest`＋`fill_nipples`）。**肚臍**做成內凹（MakeHuman `stomach-navel-in` 1.0，三版選 B）。**遊戲裡看過（2026-10-03 晚上）**：使用者說「基本上已經很好了」，兩個怪的地方 → ①胸口兩塊像乳房的突起：MakeHuman 女性比例帶的胸部，胸部大小設最小（使用者看了「沒差」；量了是胸口下緣的凹痕＋遊戲從上面打光，試過把胸口到肋骨磨成一整片，使用者：「新版變紙盒了，保留原本的」「光線夠的時候其實沒有那麼辣眼」→ **保留現狀**）；②大腿內側像肌肉結塊：只綁主骨頭的變形，腰部以下改用遊戲內衣褲的權重（含它自己驅動的輔助骨頭），**等實測**；③脖子上一圈黑色帶子＝**頭冠錯位**（使用者：「好像是頭冠錯位」），還沒修。**內褲改三角褲**（使用者：四角褲像大叔穿的；身體上的色塊、沿褲口線切開，胯側留 2 cm，**使用者定案**；襠部只有襠底一條、褲口從它兩邊往上，背面斜切過臀部下緣、不包腿根）
  - **之後的貼圖**（使用者：先把形狀做對，以後再畫）：身體現在是單色、平的法線；之後畫凹處陰影（肚臍、鎖骨窩、腹股溝）、膚色層次、細小凹凸。使用者說的「性感」是**體態健康的美感**，不是情色元素。MakeHuman 的 UV 本來就整齊，等膚色跟臉對上再畫
  - **頭冠 v10（2026-10-03 深夜修好，使用者確認）**：腳本掛到 `Head`。之前脖子根的黑色帶子就是頭冠：`Quaternion.new` 參數順序寫反（REFramework 是 w, x, y, z）→ 上下顛倒掛著；不發光＝材質抄象牙、`Emissive_Power` 0（腳本 `EMIT_ON` 打開，`build_weapon_kit.py` 的 `HALO_EMIT_ON` 下次重建就帶著）。**大小**：使用者「0.8 到 0.9 都很好、暫時拿不定主意」→ 選單 Size 範圍 0.8～0.9、預設 0.85（以頭的中心縮放）；**Glow 保留可調**。還是象牙那張壞掉的 NRRO（鏡面），發光蓋過去使用者沒抱怨；要霧面就給頭冠自己轉一張 NRRO（不動武器）
  - 身體三款 A／B／C（`Body shape`），藏獵人防具和內衣。**腳掌已修**：原本對準遊戲 Instep 陷地 5 cm 再壓扁 → 保留 MakeHuman 腳角度、`shorten_feet` 縮到 24.5 cm（`FOOT`）
  - **光照已修**：腳本生成的 Mesh `StencilValue` 是 0（陰影處全黑）→ 從臉的 Mesh 複製 `StencilValue`、`ShadowCastMode`（`MATCH_RENDER`）
  - **斑塊／糊已修**（使用者確認）：遊戲角色模型的**頂點顏色存綁定姿勢位置**（R = x/2+0.5、G = 高度/2、B = 前後/2+0.5、A = 1，raw/255、檔案空間公尺），shader 拿來算濕身／沾沙；我們沒有＝全身又濕又沾沙 → `position_colors` 匯出時寫入
  - **膚色：最新版裝好了、使用者還沒看**：皮膚＝內衣的 `skin` 材質（SkinEdit shader，`SKIN_SOURCE`），底色＝臉貼圖脖子的顏色 sRGB 161,179,181（`BODY_TEXTURES`），`BlendNormalMap` 換平坦；腳本從臉的 `face` 材質複製 `AddColorUV`（膚色色盤位置），`ColorParam` = `SKIN_BASE` 2.9 × 膚色選項 × `Skin brightness`（選單）。SkinEdit 比臉暗約 3 倍的原因不明（shader 內部），2.9 是用使用者校準的 3.3 換算的
  - 內褲（`MiquellaCloth`）：武器 shader＋自己的米白貼圖
- **膚色試過的路（不要重走）**：①抄雙劍象牙材質 → 雙劍 NRRO 壞（見第 0 節給第一帳號的留言），鏡面金屬感、全黑；②自己的膚色貼圖＋武器 shader → 顏色對但糊、有斑（其實是沒頂點顏色＝沾沙）；③SkinEdit＋中性灰 152,152,157 → 深棕，要 ×3.3、偏黃；④**臉的材質直接套身體**（UV 塞進臉貼圖脖子區）→ 更黑而且**模型被扭壞**（臉的 vertex shader 依 UV 做捏臉變形）。如果最新版還是不對：考慮回到②（武器 shader＋自己的膚色貼圖，現在有頂點顏色應該不會斑了），膚色用選單手調
- **使用者提出、還沒改的問題**（照使用者在意的程度）：
  1. **膚色**跟臉還有差（看最新版結果）
  2. **斜方肌太壯**（「練很大才會有的肌肉」）→ **晚上的版本先看**：看起來壯應該是長脖子管的斜坡（已縮短）＋男骨架把肩膀往內擠 2 cm（已改女骨架）；直接把斜方肌往下壓試過，背後會起皺，沒用
  3. ~~胸口小凸起~~：晚上磨平了，等實測
  4. **脖子底部一圈深色接縫線** → 晚上改接女臉（縫隙 0 mm、法線差 0.6°），等實測；脖子根前面在 Blender 裡還有一道淺淺的轉折（脖子管短、要從胸口的斜度轉到臉脖子的直立），遊戲裡太明顯就把 `NECK_DEPTH` 前面再放長一點
  5. 內褲顏色跟膚色太近，要更明顯的米白（款式已改三角褲，顏色還沒改：`BODY_TEXTURES` 的 `MiquellaCloth`）
  6. 小瑕疵：新做的脖子管 UV 是退化的（每直排同一個 UV），換貼圖時會影響切線
  7. 還沒測：關節變形（膝肘肩、手指）、轉頭低頭、使用者還沒挑 A／B／C
- **工具**（這次新增）：`MiquellaLight_Scout/reframework/autorun/MiquellaLight_MeshDiff.lua`（比對臉和我們物件的 Mesh 設定，用完要從遊戲移除）、`prototypes/scripts/decode_wilds_tex.py`（解 .tex 看數值）；用 computer-use 截遊戲畫面（要授權 `monsterhunterwilds.exe`；不能按鍵進遊戲，Reset scripts 請使用者按）。pak 遊戲開著時放 `work\install`、背景跑 `install_when_closed.sh`
- **文件**：做法、參數、指令、試過不行的 → `mhws/MiquellaLight_Character_kit/README.md`；腳本、選單、測試 → `mhws/MiquellaLight_Character/README.md`；遊戲獵人身體的量測 → 研究筆記第 18 節；已決定的方向 → `notes/two-account-handoff-plan.md`「米凱拉風格角色」
- **下一步**（照順序）：
  1. ~~頭冠錯位~~（2026-10-03 深夜修好，見上面「現況」）；頭冠大小等使用者在 0.8～0.9 之間決定，決定了可以把預設值改掉（`SIZE_DEFAULT`）
  2. **大腿內側**：腰部以下改用遊戲內衣褲的權重（含它驅動的輔助骨頭）已裝進遊戲，**使用者還沒確認還會不會結塊**；胸口保留現狀（使用者決定）
  3. 膚色、內褲顏色：使用者在遊戲裡看過最新版後再調（`SKIN_BASE`、`BODY_TEXTURES` 的 `MiquellaCloth`；改完男女各跑一次 `miquella_body.py kit ...`，指令見 kit README）。截圖用 computer-use：要授權的是 `monsterhunterwilds.exe`（不是「Monster Hunter Wilds」捷徑）
  3. **長袍（2026-10-04 設計定案，下一步做遊戲版）**：
     - **擺動物理查過了，可以**：腳本生成的物件只加 `via.motion.Chain2` 不會動，**再加 `via.motion.ChildSecondary` 就跟真頭髮一樣甩**（`MiquellaLight_ChainProbe.lua` 複製 512 頭髮實測，研究筆記第 15 節；測試腳本已從遊戲移除）。另外看到遊戲有裙子用 `via.dynamics.GpuCloth`（`ch03_042_0015`），備用
     - **設計**：`bpy45\Scripts\python robe_designs.py <輸出> [A B C D N] [lines smooth drape cinch] [collar:strands] [full] [test]` → `MiquellaTools\work\previews\robe\robe_<版型>_<裝飾>[_collar_<款>]_{front,front34,side,back,close}.png`（含卡普空的臉、頭髮，不進 repo；總覽 `robe_final.png`）。身體用 `mq_body_c_f`（使用者是女獵人、選 C）。版型三種**使用者都要保留**（貼身透線條＝第一張測試圖、不露線條、垂墜：從肩膀掛下來、只被臀部頂起一點）；**飾品全部金屬金飾**；使用者提議**在上衣和下擺交界放金環束帶**（D 款）。細節、規格在 DESIGN.md「服裝」
     - **使用者已定（2026-10-04）**：D 的腰帶＋下擺金邊**只用在垂墜版**；**領口換成全金寬領「丁」**（頭冠紋放射：金板＋三股纏繞分三叉＋小芽＋金水滴，前 9.5／肩 5.5／背 6.5 cm），參考埃及 usekh 寬領但全金；飾品全部金屬金飾
     - **定案（使用者 2026-10-04）**：四個可切換的款式——①貼身透線條 `lines`、②不露線條 `smooth`：**完全素面，不加任何飾品**（使用者：「其他幾款不用飾品」；理解成連金邊都不要，已跟使用者說，沒更正）；③垂墜 `drape`＋腰帶**鬆掛**在臀部、④垂墜＋腰帶**束緊**在腰部 `cinch`（使用者：「鬆掛跟束緊留成可選項」）——③④戴 D 的金飾（金環腰帶＋兩條垂繩金墜、窄金邊袖口和下擺）＋全金寬領「丁」。指令：`robe_designs.py <輸出> N lines smooth`、`D drape cinch collar:strands full`（Cycles 近拍 `_collar_strands_{front,front34,back34}`＋全身）
     - 還沒仔細看：寬領的背面（算圖被頭髮蓋住）
     - 做法的坑（`robe_designs.py` 註解）：乳頭、肚臍那幾塊網格超密（0.4 mm），平滑以「格數」算等於沒平到 → 布料用的身體副本先用周圍的二次曲面撫平（`flatten_dense`）；平滑後每輪推回 4 mm 會把凸起複製回來 → 不露線條／垂墜只修真的穿進去的（1.5 mm）；下擺每欄要用自己的起點高度算斜率（用平均高度時分母接近 0、爆開）、欄位照角度均勻取（不然會交叉出裂縫）
     - **遊戲版第一版（2026-10-04 凌晨，已裝進遊戲，等實測）**：`robe_kit.py smooth female|male` → `mq_robe_smooth_c_f.mesh`（女）、`mq_robe_smooth_c.mesh`（男），約 2.2 萬點；版型照 `robe_designs.py`（同一套 Fit／build_skirt，做在身體 kit 的 C 款上；**其他體型先穿 C 的**）
       - **權重**：上衣、袖子取身體表面最近點、三角形內插身體的權重（含臉的脖子接縫權重、腿的輔助骨頭）；下擺：按角度取左右兩條骨鏈、按列取上下兩節（最上一節用 s³，大部分留在 CH_00，不然擺動時臀部那圈會往內陷、露出皮膚），最上面 6 cm 從身體權重漸變過去（`TOP_BLEND`）。**坑**：布是從身體的 bmesh 複製的，帶著身體的權重層（用身體物件的群組編號），新增群組時編號對上 → 肩膀、背混進腿的權重，跨步時整片飛走；建網格前要先刪掉那層
       - **擺動**：遊戲沒有現成的長袍 chain2，長裙防具多半用 GPU 布料（骨頭名稱含 `GCJ`，`.gpuc`）；用骨鏈的裡面 `ch03_025_0015`（女，腿部防具，長到小腿）最合適：`HipJiggle_CH_00`（掛 `Hip_HJ_00`）底下 12 條 `*_Skirt*_CH_00～04`＋`_CH_end`，繞一圈。整副骨架併進我們的（`mergeArmature`，711 → 813 根；其他鏈的骨頭也帶著、沒權重），12 條裙擺鏈搬到我們下擺的欄上（CH_00 在下擺最上一列、其餘平均往下到下擺），檔案裡的世界／區域／反矩陣一起改（`move_chain`）。chain2 用骨鏈**末端骨頭名稱的 murmur3**（`*_CH_end`）找鏈，所以名稱、父子關係要一樣。**男版那件防具沒有 chain2** → 男女都用女版的 `Art/Model/Character/ch03/025/001/5/ch03_025_0015.chain2`（執行時引用遊戲檔，不放進我們的 pak）
       - **腿的碰撞（不確定）**：chain2 裡沒有碰撞；遊戲每個部位有 `.clsp`（膠囊：內衣褲 `ch03_002_0004.clsp` 是大腿、小腿、腳、`Hip_HJ_00`），應該是部位自己的 `app.ChainSetting` 登記的。我們的物件只有 Chain2＋ChildSecondary，腿可能會穿過裙子（Blender 預覽跨步就是穿過去的）。腳本把 `via.motion.Chain2`、`ChildSecondary`、`app.ChainSetting` 的成員和獵人身上那件的值寫進 `reframework/data/MiquellaLight/robe_debug.json`，下次讀它研究怎麼接碰撞
       - **身體**：被蓋住的部分拆成獨立材質（`miquella_body.py` 的 `mark_covered`，照長袍的領口、袖口、下擺線往內 1 cm）：`MiquellaSkinChest`（領口到胸口、手臂：每款長袍都蓋）、`MiquellaSkinWaist`／`MiquellaClothWaist`（胸口到臀部：只有貼身款蓋，垂墜款不關）。男女六個身體都重建了
       - **布**：米白 sRGB (230, 221, 199) 平紋布，16 股／2.4 cm 一格（`weave_images`），雙面（`BaseTwoSideEnable`，防具的裙子材質也是）；材質抄雙劍 `MiquellaGrip`（武器 shader，內褲用過、確定能顯示）。UV 是半精度浮點數，數值大會抖 → 每 8 格整數平移一次（`UV_BLOCK`）
       - **`lines` 也做了（同一天）**：`robe_kit.py lines female|male`，選單 Robe, body lines
       - **垂墜兩款（同一天早上 4 點）**：`robe_kit.py drape|cinch female|male`。布從胸口垂下（`robe_designs` 的 drape／cinch 版型），**胸口到臀部那段跟著身體的權重**，臀部線（`SKIRT_TOP`）以下才交給 12 條骨鏈（`chain_top`：每欄骨鏈從最接近臀部高度的那列開始）。金飾是 `robe_designs.gold_work("D", collar="strands")` 的曲線和網格，轉成網格合併成第二個子模型 `MiquellaRobeGold`（約 17 萬面減到 6 萬三角形），**每個點抄最近那個布的點的權重**（寬領跟胸口、垂繩和金墜跟裙擺前面、下擺金邊跟骨鏈末端）；金是金屬（`ALBD` alpha 0，照裝置的金色區：sRGB 226, 176, 74、粗糙度 0.27）。垂墜款只關身體的 `MiquellaSkinChest`（胸口以下的布離開身體）。**Blender 預覽的跨步**：大腿抬起時，臀部那排（跟身體走的段和交給骨鏈的段交界）會裂開一點，遊戲裡看碰撞有沒有把裙子推開，不行就把交界的漸變拉長（`TOP_BLEND`）
       - **腳本**：選單「Outfit」：None／Robe, plain／Robe, body lines／Robe, drape, loose sash／Robe, drape, cinched（`OUTFITS`）；長袍物件 `MiquellaLight_Robe`，SameJointsConstraint＋Chain2（chain2 每次 set_model 都重設）＋ChildSecondary；穿著時關掉身體的 `covers` 材質；選單和 `robe_debug.json` 寫**下擺擺動幅度**（背後下擺末端相對 `Hip` 五秒內移動多少 mm，~0＝物理沒在跑）。測試 `character_test.lua` 39 項全過
       - **要使用者實測**：選單 Outfit 選 Robe, plain → ①長袍有沒有出現、位置對不對、有沒有穿模（胸口、領口、手肘）；②走路、跑、翻滾時下擺有沒有擺動（選單 `hem swing` 是幾 mm）、腿會不會穿出裙子；③布紋、顏色（太白、太黃、太亮）；④內側翻起來看不看得到（雙面）；⑤脫掉（Outfit None）身體有沒有完整回來
       - **下一步**：看實測和 `robe_debug.json`：腿穿出去就研究碰撞（加 `app.ChainSetting`？或把裙子前後的權重混一點大腿）；擺動不夠或太軟就換別件的 chain2 或自己寫（RE Chain Editor 沒裝，要下載先問使用者）；垂墜款的金飾看實測（金屬感、寬領會不會跟著胸口變形太多、垂繩要不要自己的鏈）
       - **遊戲裡實測（2026-10-04 早上，Claude 自己操作）**：全黑、分節都修好（見第 0 節）。**腿穿出裙子還沒修**，查到的：
         - 遊戲有擺動的防具（`ch03_012_0014`、長裙 `ch03_042_0015`…）都掛 `app.ChainSetting`（登記進獵人根物件的 `app.ChainSettingCollection`）＋`via.character.CollisionShapePreset`（`CollisionShapePresetInfo.set_Resource(<.clsp holder>)`，各部位自己的 `.clsp`）；頭髮只有 ChainSetting。我們的長袍只有 Chain2＋ChildSecondary
         - `MiquellaLight_Scout/.../MiquellaLight_ChainTest.lua`（實驗用，命令檔 `data/MiquellaLight/chain_test.json`：`{"n":1,"chainSetting":true,"clsp":"Art/Model/Character/ch03/025/001/5/ch03_025_0015.clsp"}`，改 `n` 重套）：即時加 ChainSetting（自動接上 Chain2 和 Collection）、加 CSP。長裙 `ch03_025_0015.clsp` 只有 2 個形狀，加了之後大腿內側被蓋住；內衣褲 `ch03/002/000/4/ch03_002_0004.clsp` 7 個形狀，站著看不出差別。**還沒走路、跑步測**
         - **更根本的**：裙擺在遊戲裡被重力拉成直筒（Blender 裡是散開的 A 字），站姿兩腿比下擺寬，腿一定在外面 → 要讓骨鏈維持散開（chain2 的硬度／角度限制，或用 RE Chain Editor 自己寫擺動＋碰撞，**使用者已授權下載**），或下擺加寬、裙片前後混一點大腿權重
         - 另外看到：素面款胯部、一邊胸口透出身體形狀（「不露線條」不該有）；領口一圈偏淺（可能看到內側）；布面近看有顆粒（可能是鏡頭太近遊戲讓角色半透明）
       - **自己操作遊戲（2026-10-04 學會的）**：computer-use 要授權 `monsterhunterwilds.exe`；**鍵盤有用、點擊遊戲吃不到**（REFramework 選單吃得到點擊）；Insert、滑鼠右鍵、鏡頭轉動要用系統層級送（`mods/miquella/tools/game_input/` 的 `sendkey.ps1`＝keybd_event、`closemenu.ps1`＝Insert＋系統右鍵；轉鏡頭用 `mouse_event` 相對移動，20×100 約轉半圈），Insert 會連帶打開遊戲的語音聊天視窗、系統層級右鍵關掉；叫遊戲到前面用 `WScript.Shell.AppActivate(pid)`。開遊戲 `steam://rungameid/2246340` → 標題按 F → 存檔 F → 大廳按 S 三次（每次隔 0.9 秒）到「單人線上模式」→ F → 等幾秒再 F（太快會吃掉）→ 約 40 秒進營地。**關遊戲**：Esc → E 按六次到時鐘分頁 →「結束遊戲」F →「儲存並結束」F →「確定要儲存嗎」按 A 選「是」→ F（Alt+F4、關視窗指令都沒用，送關視窗後遊戲還卡住）。pak 換法：背景等遊戲關掉就複製並比對。重開後會回到營地，日夜照當時的時間
  3b. **臉（2026-10-04 開始）**：使用者給了三張喜歡的畫師圖（不進 repo），方向在 DESIGN.md「臉」（下垂眼、眼皮半垂、居高臨下又玩弄人的傲氣眼神、單邊嘴角微揚；要有魔性的吸引力，不要媚眼、不往色情走）。女臉 `ch00_001_0000`：8 千點的臉＋嘴、睫毛、眼睛、眼線、眼影、脖子內襯；393 根骨頭，約 150 根臉部骨頭（LOD00／01／02 三層、`*_Master`、`*_SCL`），表情靠骨頭；材質 `Base_ATOS_CharaEdit_MultiBlend_weight12_VFX`（皺紋混合、彩妝 PaintMap、膚色 SkinMap）。捏臉的資料 `hunterfaceeditvaluekeydefinition.user` 只有數字／雜湊，看不出來；**捏臉到底動骨頭還是 shader 變形，要在遊戲裡看**（`face_debug.json` 的骨頭底值會透露一部分）。**已做：`MiquellaLight_Face.lua`**（README 在 `mhws/MiquellaLight_Face/`）：每幀在遊戲的姿勢上疊加骨頭位移／旋轉（疊加不累積：記住上次設的值），預設值是預覽 B 版，滑桿可調、可關。**要使用者實測**：①臉有沒有變（沒變＝遊戲更晚又設一次，看 `face_debug.json`）；②眨眼、說話、表情時有沒有怪（上眼皮多轉 11°，眨眼可能閉過頭）；③神態對不對，調滑桿找喜歡的值告訴我。**還缺**：參考圖放 `MiquellaTools
efs\`、獵人臉的截圖（或允許 computer-use 截圖）；骨頭微調不夠的話再考慮捏臉建議或改女臉模型（保留網格、UV、權重，只改形狀）
  4. **頭髮（設計定案 2026-10-03，使用者：「這樣蠻好的」）**：以遊戲髮型 **512** 為底（**使用者的獵人是女獵人，遊戲裡用的是 `ch01_001_0512`＝女性版，做進遊戲要用這個**；預覽用的是 `ch01_000_0512`，頭型不同要重新對）（使用者發現它就是左右兩股往後合成大編髮＋中分長波浪到腰；結構見研究筆記第 14 節「遊戲髮型 512／513」）。定案內容（規格寫進 `DESIGN.md`「髮型」）：
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
