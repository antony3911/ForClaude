# MiquellaLight_Character_kit — 角色素材包（頭冠、身體）

| kit | 檔案 | 說明 |
|---|---|---|
| `circlet` | `Art/Model/MiquellaLight/Character/mq_circlet.mesh`／`.mdf2` | 頭冠（光環）v10，約 1.5 萬面；材質 `MiquellaHalo`（象牙底、整個發金光）、`MiquellaGlow`（墜飾水滴） |
| 身體 | `mq_body_a／b／c.mesh`（男獵人）、`mq_body_a／b／c_f.mesh`（女獵人）＋`mq_body.mdf2` | 三種體型（A 纖細中性／B 少年感／C 柔和），各約 3.8 萬點（細分一次）；**米凱拉的體型男女獵人一樣**，`_f` 只是接女獵人的臉和骨架；材質 `MiquellaSkin`（抄雙劍 `MiquellaIvory`）、`MiquellaCloth`（內褲，抄 `MiquellaGrip`）。`miquella_body.py kit` 產生 |

## 身體（2026-10-02 深夜）

遊戲沒有裸身模型（內衣是整套衣服，研究筆記第 18 節），所以用 **MakeHuman 的基礎人體（CC0，github.com/makehumancommunity/makehuman，可自由修改發布）**：
1. **體型**：MakeHuman 的 macro 調整檔（成人 25 歲；性別、肌肉、體重三個滑桿，`VARIANTS`）＋細節（V 形軀幹減、胸肌減、乳頭磨平、小腹平、髖窄、脖子細，`COMMON_DETAILS`），胸前再局部抹平（`smooth_spots`）
2. **對齊遊戲骨架**：整體先縮放、平移到遊戲的髖和脖子高度；**軀幹（脊椎、骨盆）保持 MakeHuman 自己的形狀**，只有四肢、脖子、手腳用 MakeHuman 自己的骨架和權重把骨頭拉到遊戲關節之間（Copy Location＋Stretch To，`fit_targets`）。遊戲的 `Hip`／`Spine_0` 比髖關節高 11 cm，之前把脊椎、骨盆也拉過去，胯下被拉到髖關節高度、擠出啤酒肚（2026-10-02 修正）→ 綁定姿勢（A 字）、手指、腳踝都對上遊戲的。腳踝以下壓扁讓腳底貼地（遊戲的腳踝比較低）
2c. **線條**：收腰（`measure-waist-circ-decr`）、馬甲線、背溝（`BASE_GROOVES`），比較圖 `python miquella_body.py lines ...`
2b. **臀腿**（2026-10-02，使用者給參考圖修的）：屁股保留體積磨平肌肉起伏（`soften_buttocks`）、臀部體積加大（`buttocks-volume-incr` 0.75）；大腿側面從臀下到膝蓋收成錐形（`taper_thighs`）；細分一次後臀縫從裡面填平（`bridge_cleft`，像布料撐過去），再刻腹股溝摺線（10 mm 寬的細 V 線）和臀下弧線（`BASE_GROOVES`、`carve`）。前後比較圖：`python miquella_body.py hips <MakeHuman data> <ch02_002_0002.mesh> <輸出>`。**之後的長袍、內褲不能把腹股溝線蓋平；長袍在臀部貼身，照這個形狀**。**試過不行的**：腹股溝 6.5 mm 窄線（像刀割、四分之三視角有尖刺）、不細分就刻（尖刺、稜角）、兩條線在正中交會（擠出鼓包）、第一版三角褲（整個面塗色→褲口鋸齒、側邊剪到腰，2026-10-03 改成沿線切開重做）；臀縫用局部平滑撐平（邊界留下兩條硬豎線）；`flatten_belly` 把正面輪廓壓直（推出怪凸起，`flat` 預設關）。量體型要排除 MakeHuman 沒有面的輔助幾何（褲襪、裙子的散點，`used` 集合），不然會量錯、把腿弄皺
0. **男女獵人各一套**（2026-10-03 晚上）：使用者的獵人是女的（臉 `ch00_001_0000`、防具 `ch03`），身體之前照男獵人的臉、骨架做。女臉的脖子下緣比男的低 1～2 cm、細 4 mm，女性骨架（內衣 `ch03_002_0002`，711 根）肩膀、手臂每邊窄 2 cm（其他骨頭一樣）→ 身體上緣浮在女臉脖子外面（懷疑就是遊戲裡那圈深色接縫線）。`kit` 看臉的檔名，女臉輸出 `_f`，皮膚材質從同一套內衣的手臂檔抄（男女只差貼圖，共用 `mq_body.mdf2`）；腳本看獵人臉的路徑選（`MiquellaLight_Character` README）
1d. **不要胸部**（2026-10-03 晚上，使用者在遊戲裡：胸口兩塊像乳房的突起）：體型的性別參數 0.62～0.90（偏男但有女性比例，為了柔和），女性那部分會帶 MakeHuman 的一般胸部 → 胸部大小設最小（`macro_targets` 加 `breast/female-young-*-mincup-averagefirmness`，權重＝女性比例×肌肉×體重，跟 MakeHuman 的 BreastSize 滑桿 0 一樣）
1e. **胸口到肋骨磨成一整片：試過、使用者否決**（2026-10-03 晚上）：胸部調最小後使用者「感覺沒差」，量了是胸口下緣有一道凹痕、遊戲從上面打光像乳房下緣 → 胸前擬合成平滑曲面（最多動 1 cm）。使用者：「原版還有一點肋骨型，新版變紙盒了，看起來更怪」，而且「光線夠的時候其實沒有那麼辣眼」→ 保留現狀（胸部最小＋`flatten_chest`）
1c. **肚臍**（2026-10-03 晚上，使用者：「把凹肚臍做出來」）：原本 MakeHuman 的肚臍很淺、像一個小點 → `stomach/stomach-navel-in` 1.0（`COMMON_DETAILS`；0／1／1.5 三版使用者選 1）。之後的細節（凹處陰影、膚色層次）用貼圖畫，使用者要的是「體態健康的美感」
1b. **胸口**（2026-10-03 晚上，使用者：胸口小凸起）：原本只在乳頭點 3.5 cm 內磨平，留下胸肌的小丘 → 乳頭點周圍 8 cm、朝前的面再磨平（`flatten_chest`，`CHEST`），乳頭本身網格比較密、磨完留一個小凹點 → 把胸前當成高度場，用外圈 2～4.5 cm 擬合二次曲面、裡面設到曲面上（`fill_nipples`）
3b. **脖子變短**（2026-10-03 晚上，使用者：「這塊 V 字被拉得太長」「脖子明顯太長、有拉伸感」）：臉的脖子正面本來就包到胸骨上方，MakeHuman 的胸口和上背卻在臉下緣下面 5 cm（正面）～9 cm（背面）才開始，中間全是新長的管子 → **脖子根一圈往上提 3 cm**（`raise_neck_base`，`NECK_LIFT`：靠近脖子、越高提越多，肩關節和胸口以下不動），接點縮到 `NECK_DEPTH` 3.5／4／4.05 cm（四個版本 B 2 cm／C 3 cm／D 4 cm 使用者選 C；C 原本正面 2.3 cm 在脖子根折出一圈線，放長到 3.5 cm）。接點那圈再順著磨平（`smooth_neck_foot`，往臉下緣方向一半以上就不動，磨到下緣附近反而在下緣出線）。斜方肌壓低試過（背後起皺），沒用：看起來壯是長脖子管的斜坡造成的
3. **脖子**（2026-10-03，照原版的接法；使用者：「這個版本不錯」）：遊戲的臉往下包到脖子，下緣是一圈 48 個點（前 1.43、後頸 1.53，內側有一圈內襯 Group_7）。原版內衣 `ch02_002_0002` 的皮膚上緣**就是這 48 個點**（位置差 0.000 mm、法線差 0°、權重完全一樣），所以接縫不會裂、沒有光影線，臉的脖子也不會被動到。我們一樣：**臉完全不動，身體的上緣＝臉下緣那 48 個點**（位置照抄、法線抄臉的自訂法線 `match_face_normals`、權重抄臉的含 `*_HJ_*` `blend_face_weights`）。下緣以下：每個下緣點往外下方瞄一個點（`NECK_SLOPE` 正面 30°／側面 50°／背面 -5°，`NECK_DEPTH` 深 5／7／9 cm），取 MakeHuman 身體上離它最近的點當接點（側面落在斜方肌上，肩頸線比 MakeHuman 原本高、脖子看起來比較短；背面落在 MakeHuman 上背隆起的下方），接點到下緣用三次 Hermite 曲線（接點順著身體表面、下緣順著臉的表面，不會摺）。MakeHuman 沿接點那圈精確切開（`contour_cut`：沿等值線切，只刪連到頭的那塊），以上重新長網格（`neck_tube`：每個下緣點兩欄、12 列，最上一列就是下緣）。**試過不行的**：身體蓋在臉的脖子外面（鼓出一大圈）；接點固定在下緣下方 3 cm（MakeHuman 的脖子比臉的細 2 cm，側面被迫往內縮 → 摺痕）；照抄原版內衣下緣以下的形狀（側面是立起來的襯衫領內襯，像兩道牆）。檢查：`CHECK rim` 0.0000 mm、臉（含內襯）沒有穿出
4. **內褲**：**三角褲**（2026-10-03 晚上，使用者：「四角褲好醜，超像大叔穿的」）：不是另一個物件，是身體上另一個材質的區域（`brief_s` > 0：腰頭 0.975 m 以下、褲口以上）。褲口從兩腿間的襠部沿腹股溝往上、背後從襠部斜切過臀部下緣（第一版沿臀下，使用者：「誰家三角褲會包到腿根」），到胯側 0.955 m。**襠部只有襠底那一條**（|x| < 1.5 cm；襠底在 0.825 m，往外 1.5～2 cm 就往下變成大腿內側），褲口從它兩邊往上（第二版襠部往外包了 3～4 cm，使用者：「很明顯是從腿根開始的」）；胯側留約 2 cm 寬（6 → 3.5 → 2 cm，使用者：「這邊可以細一點」「再細點」）。**使用者定案（2026-10-03）**；褲口線是平滑曲線（`line_z`，單調三次曲線），**網格沿 `brief_s` 的零線切開**（`split_along`，脖子的 `contour_cut` 也用它），邊緣乾淨。之前的四角褲（0.78～0.99 m 水平帶）還在，`underwear: boxer`。長袍之後蓋在上面
5b. **腰部以下用遊戲內衣褲的權重**（2026-10-03 晚上，使用者在遊戲裡：大腿內側像肌肉結塊；Blender 站姿是平的 → 是變形）：遊戲的腿幾乎全綁在它自己驅動的輔助骨頭上（`ThighTwist_HJ_00～02`、`Hip_HJ_00`、`Spine_0_HJ_00`、`Knee_HJ_00`、`KneeRX_HJ_00`，主骨頭 `Thigh` 只有 2 千／2.9 萬），我們只綁主骨頭，大腿根整塊扭在一起擠成一團。現在從同一套內衣的腿 `ch0X_002_0004`（不含 fur）取最近表面、三角形內插權重，0.96 m 以下全用、1.04 m 淡出、離皮膚 3～6 cm 淡出（`blend_leg_weights`，`LEG_W`、`LEG_FAR`）。**只能在遊戲裡驗證**（輔助骨頭是遊戲執行時驅動的，Blender 擺姿勢看不出來）
5. **權重**：MakeHuman 的骨頭對到遊戲的**主要骨頭**（`bone_map`：脊椎依高度分段、手指一對一、`lowerleg` → `Shin`、腳趾 → `Toe`），每點最多 6 根、正規化；遊戲的 `*_HJ_*` 輔助骨頭（扭轉、膝肘體積）先沒用，**在遊戲裡看關節變形**，不好再加
6. 骨架整副借內衣身體 `ch02_002_0002` 的（709 根，名稱跟獵人一樣），由腳本用 SameJointsConstraint 跟著獵人動

```
python miquella_body.py preview <MakeHuman data> <ch02_002_0002.mesh> <輸出> [<ch00_000_0000.mesh> [其他內衣 .mesh...]]
python miquella_body.py kit <MakeHuman data> <ch02_002_0002.mesh> <ch00_000_0000.mesh> <這個資料夾> <雙劍 wp_miquella_db.mdf2.45>   # 男獵人
python miquella_body.py kit <MakeHuman data> <ch03_002_0002.mesh> <ch00_001_0000.mesh> <這個資料夾> <雙劍 wp_miquella_db.mdf2.45>   # 女獵人（_f）
```
MakeHuman 資料放在 repo 外：`C:\Users\anton\MiquellaTools\makehuman`（`git clone --depth 1 --filter=blob:none --sparse`，sparse 只取 `makehuman/data/3dobjs`、`rigs`、`targets/{macrodetails,torso,breast,stomach,hip,neck,...}`）。預覽（含遊戲模型，不進 repo）：`MiquellaTools\work\previews\body\body_variants_sheet.png`、`neck_closeups.png`

**還沒做**：膚色材質（現在是雙劍的象牙材質）、用遊戲的輔助骨頭改善關節、長袍、頭髮

**重建**（bpy45）：

```
python build_weapon_kit.py circlet <這個資料夾> <it0100_0002_0.mesh.241111606> <雙劍 wp_miquella_db.mdf2.45>
python make_patch_pak.py <這個資料夾> MiquellaLight_Character.pak <RE Asset Library 所在資料夾>
```

**座標**：檔案空間＝獵人 `Head` 骨頭的空間（綁定姿勢）：+Y 上、+Z 臉的前方、+X 獵人的左手邊，原點是 `Head`（綁定姿勢在 (0, 1.573, -0.010)，幾乎沒有旋轉）。骨架借片手劍原版的（只當載體，全部頂點在 `Base`），由 `MiquellaLight_Character.lua` 把物件掛到 `Head` 上。

**尺寸**（2026-10-02 量遊戲的頭：臉 `ch00_000_0000`、頭髮 `ch01_000_0001`）：眉上（y 1.69）光頭寬 ±0.074、前後 -0.096～+0.101；加頭髮寬 ±0.09、後 -0.117。原型的頭冠圍在 0.074／0.094／0.112 的頭上（帶寬 ±0.075），放大 (1.22, 1.10, 1.12)（寬、高、深）讓兩側戴在頭髮上；正面在 y 1.70、z +0.103（世界座標）。`build_weapon_kit.py` 的 `CIRCLET_SCALE`、`CIRCLET_AT`。

**材質**：`MiquellaHalo` 抄雙劍的 `MiquellaIvory`，發光貼圖換成 `MiquellaGlow_EMI`、`Emissive_Color` (1.0, 0.72, 0.30)、`Emissive_Intensity` 0.8（`HALO_EMISSIVE`、`HALO_INTENSITY`）。貼圖用雙劍 pak 的，**要裝 `MiquellaLight_DualBlades.pak`**。

預覽（放在遊戲的頭上，含卡普空模型，不進 repo）：`MiquellaTools\work\previews\circlet\circlet_on_game_head.png`。
