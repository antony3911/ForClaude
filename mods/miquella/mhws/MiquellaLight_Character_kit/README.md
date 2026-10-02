# MiquellaLight_Character_kit — 角色素材包（頭冠、身體）

| kit | 檔案 | 說明 |
|---|---|---|
| `circlet` | `Art/Model/MiquellaLight/Character/mq_circlet.mesh`／`.mdf2` | 頭冠（光環）v10，約 1.5 萬面；材質 `MiquellaHalo`（象牙底、整個發金光）、`MiquellaGlow`（墜飾水滴） |
| 身體 | `mq_body_a／b／c.mesh`＋`mq_body.mdf2` | 三種體型（A 纖細中性／B 少年感／C 柔和），各約 3.8 萬點（細分一次）；材質 `MiquellaSkin`（抄雙劍 `MiquellaIvory`）、`MiquellaCloth`（內褲，抄 `MiquellaGrip`）。`miquella_body.py kit` 產生 |

## 身體（2026-10-02 深夜）

遊戲沒有裸身模型（內衣是整套衣服，研究筆記第 18 節），所以用 **MakeHuman 的基礎人體（CC0，github.com/makehumancommunity/makehuman，可自由修改發布）**：
1. **體型**：MakeHuman 的 macro 調整檔（成人 25 歲；性別、肌肉、體重三個滑桿，`VARIANTS`）＋細節（V 形軀幹減、胸肌減、乳頭磨平、小腹平、髖窄、脖子細，`COMMON_DETAILS`），胸前再局部抹平（`smooth_spots`）
2. **對齊遊戲骨架**：整體先縮放、平移到遊戲的髖和脖子高度；**軀幹（脊椎、骨盆）保持 MakeHuman 自己的形狀**，只有四肢、脖子、手腳用 MakeHuman 自己的骨架和權重把骨頭拉到遊戲關節之間（Copy Location＋Stretch To，`fit_targets`）。遊戲的 `Hip`／`Spine_0` 比髖關節高 11 cm，之前把脊椎、骨盆也拉過去，胯下被拉到髖關節高度、擠出啤酒肚（2026-10-02 修正）→ 綁定姿勢（A 字）、手指、腳踝都對上遊戲的。腳踝以下壓扁讓腳底貼地（遊戲的腳踝比較低）
2c. **線條**：收腰（`measure-waist-circ-decr`）、馬甲線、背溝（`BASE_GROOVES`），比較圖 `python miquella_body.py lines ...`
2b. **臀腿**（2026-10-02，使用者給參考圖修的）：屁股保留體積磨平肌肉起伏（`soften_buttocks`）、臀部體積加大（`buttocks-volume-incr` 0.75）；大腿側面從臀下到膝蓋收成錐形（`taper_thighs`）；細分一次後臀縫從裡面填平（`bridge_cleft`，像布料撐過去），再刻腹股溝摺線（10 mm 寬的細 V 線）和臀下弧線（`BASE_GROOVES`、`carve`）。前後比較圖：`python miquella_body.py hips <MakeHuman data> <ch02_002_0002.mesh> <輸出>`。**之後的長袍、內褲不能把腹股溝線蓋平；長袍在臀部貼身，照這個形狀**。**試過不行的**：腹股溝 6.5 mm 窄線（像刀割、四分之三視角有尖刺）、不細分就刻（尖刺、稜角）、兩條線在正中交會（擠出鼓包）、三角褲款（褲口鋸齒、剪太高，先拿掉，只留四角褲）；臀縫用局部平滑撐平（邊界留下兩條硬豎線）；`flatten_belly` 把正面輪廓壓直（推出怪凸起，`flat` 預設關）。量體型要排除 MakeHuman 沒有面的輔助幾何（褲襪、裙子的散點，`used` 集合），不然會量錯、把腿弄皺
3. **脖子**（2026-10-03，照原版的接法；使用者：「這個版本不錯」）：遊戲的臉往下包到脖子，下緣是一圈 48 個點（前 1.43、後頸 1.53，內側有一圈內襯 Group_7）。原版內衣 `ch02_002_0002` 的皮膚上緣**就是這 48 個點**（位置差 0.000 mm、法線差 0°、權重完全一樣），所以接縫不會裂、沒有光影線，臉的脖子也不會被動到。我們一樣：**臉完全不動，身體的上緣＝臉下緣那 48 個點**（位置照抄、法線抄臉的自訂法線 `match_face_normals`、權重抄臉的含 `*_HJ_*` `blend_face_weights`）。下緣以下：每個下緣點往外下方瞄一個點（`NECK_SLOPE` 正面 30°／側面 50°／背面 -5°，`NECK_DEPTH` 深 5／7／9 cm），取 MakeHuman 身體上離它最近的點當接點（側面落在斜方肌上，肩頸線比 MakeHuman 原本高、脖子看起來比較短；背面落在 MakeHuman 上背隆起的下方），接點到下緣用三次 Hermite 曲線（接點順著身體表面、下緣順著臉的表面，不會摺）。MakeHuman 沿接點那圈精確切開（`contour_cut`：沿等值線切，只刪連到頭的那塊），以上重新長網格（`neck_tube`：每個下緣點兩欄、12 列，最上一列就是下緣）。**試過不行的**：身體蓋在臉的脖子外面（鼓出一大圈）；接點固定在下緣下方 3 cm（MakeHuman 的脖子比臉的細 2 cm，側面被迫往內縮 → 摺痕）；照抄原版內衣下緣以下的形狀（側面是立起來的襯衫領內襯，像兩道牆）。檢查：`CHECK rim` 0.0000 mm、臉（含內襯）沒有穿出
4. **內褲**：0.78～0.99 m 的帶狀區域另一個材質（先水平切出邊緣，邊緣整齊）。長袍之後蓋在上面
5. **權重**：MakeHuman 的骨頭對到遊戲的**主要骨頭**（`bone_map`：脊椎依高度分段、手指一對一、`lowerleg` → `Shin`、腳趾 → `Toe`），每點最多 6 根、正規化；遊戲的 `*_HJ_*` 輔助骨頭（扭轉、膝肘體積）先沒用，**在遊戲裡看關節變形**，不好再加
6. 骨架整副借內衣身體 `ch02_002_0002` 的（709 根，名稱跟獵人一樣），由腳本用 SameJointsConstraint 跟著獵人動

```
python miquella_body.py preview <MakeHuman data> <ch02_002_0002.mesh> <輸出> [<ch00_000_0000.mesh> [其他內衣 .mesh...]]
python miquella_body.py kit <MakeHuman data> <ch02_002_0002.mesh> <ch00_000_0000.mesh> <這個資料夾> <雙劍 wp_miquella_db.mdf2.45>
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
