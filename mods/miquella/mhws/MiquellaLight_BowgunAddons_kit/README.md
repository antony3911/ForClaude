# 輕弩、重弩附加物：遊戲素材包

使用者 2026-10-03 選的附加物（提案 `prototypes/attachments/`，程式 `attachments.py`），用 `build_weapon_kit.py` 做成遊戲模型，**直接蓋過遊戲的原檔路徑**：每把輕弩／重弩的 prefab 都指向同一個共用零件（`GameDesign/Equip/_Prefab/Weapon/Wp13/99/it1399_0000_0_common_mpi.user`），所以不用腳本，拿掉 pak 就恢復原版。原版就算換裝腳本關掉也會變成我們的（跟裝置一樣）。

| 附加物 | 蓋過的遊戲檔 | 原版（從解出的檔案量的，武器檔案空間：+Z 槍口、+Y 上） | 我們的 |
|---|---|---|---|
| 輕弩速射彈鼓 **A 象牙燈籠**（`lbg_drum`） | `Art/Model/Item/it13/99/0000/it1399_0000_0` | 槍身 **-X 側**一個直徑 0.30 的鼓，**軸跟槍管平行**，穿過 (-0.25, -0.219)；組 1 是接到槍中線的進彈管。骨頭：`Base`（外殼）、`center`（子彈那圈、輻條）、`axis`（中間的軸心，在 center 後面 0.136） | 原型的鼓（軸 X、脖子往 +Z 接槍）轉成軸沿槍管、脖子往槍身伸進去，×2.3（直徑 0.29），中心 (-0.25, -0.219, 0.035)。外框、金邊、脖子綁 `Base`；肋骨籠、光滴子彈、腰帶、卷草綁 `center`；軸心光滴綁 `axis`（遊戲轉鼓時跟著轉） |
| 重弩彈匣 **C 聖匣**（`hbg_mag`，`attachments.py` 的 `mag_c_lantern`） | `Art/Model/Item/it12/99/0000/it1299_0000_0` | 槍身 -X 側一個粗 0.2 的罐子，**往槍口方向斜下**（沿 (0.22, -0.78, 0.59)，就是 `Piston` 骨頭的 -Y），中段約 (-0.20, -0.16, 0.02)；上後端有 `Piston`、`EnergyStick`（特效 `11_it12_030`／`032`／`199` 在這兩根骨頭上播，`199` 畫一根能量棒 `it1299_0000_0_vfx`，沒換） | 第一版照原版斜掛在側面，使用者：「放在旁邊的方形很醜」→ **吊在槍身下面、握把前面**（跟提案圖一樣，用重弩 kit 同一個轉換，×1.15），形狀改成往下收窄的**六角燈籠**（六根微彎的象牙柱、每面金光尖拱窗、裡面一大滴光、底下長短交錯的卷草尖塔）。全部綁 `Base`；`Piston` 骨頭搬進燈籠裡、轉正（`unrotate`），讓特效的能量棒直立在燈籠裡（模型放哪是我們決定的，只有骨頭是遊戲的；如果遊戲的動畫會設 `Piston` 的位置，能量棒會回到側面） |

- 材質抄雙劍 kit（`MiquellaIvory`、`MiquellaGlow`），貼圖用雙劍的（pak 裡也放一份）
- **還沒在遊戲裡看過**：彈鼓是速射模式才裝上去（使用者看過原版彈鼓出現在我們的輕弩上）；彈匣什麼時候出現還不知道（可能是點火模式）。要看：位置對不對、轉鼓時籠子有沒有跟著轉、有沒有東西飛走（骨頭的動畫跟我們的擺法不合）
- 原版另外有重弩 `it1299_0001_0`（24 根骨頭、四片會掀開的板子、前端 `Crow`）：特效 `11_it12_030`（有 `Charge`）會在它的板子上發光，`11_it12_031`（`IsCancel`）把 `11_it1299_0001_0` 的零件炸飛 → 是某一種點火模式裝在槍上的裝置，不是龍穿點火的彈頭。**龍穿點火的彈頭、弓追蹤箭的遊戲檔都還沒確定**（見 HANDOFF 第 9 節）

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py lbg_drum <本資料夾> <it1399_0000_0.mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py hbg_mag <本資料夾> <it1299_0000_0.mesh.241111606> <同上>
```

原版從遊戲解出：`extract_game_files.py ... "art/model/item/it1[23]/99/.*\.(mesh|mdf2)\."`。打包：`work\stage_LBGDrum`、`stage_HBGMag`（各放自己的 natives＋雙劍貼圖）→ `make_patch_pak.py` → `MiquellaLight_LBGDrum.pak`、`MiquellaLight_HBGMag.pak`（2026-10-03 已裝進遊戲）。預覽：`preview_addons.py <out.png> <標題> <槍的 .mesh> <附加物 .mesh> [ghost:<原版 .mesh>]`（有 ghost 的圖含原版模型，不進 repo）。`.blend` 不進 repo。
