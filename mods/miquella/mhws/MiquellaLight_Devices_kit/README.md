# 武器裝置：遊戲素材包

`build_device_kit.py` 把 `devices.py` 的裝置原型做成遊戲的**特效模型**，用 patch pak **蓋過遊戲原本那個路徑**（裝置是特效生出來的，換裝腳本碰不到；拿掉 pak 就恢復原版）。

| 裝置 | 蓋過的遊戲檔 | 擺放（從原版量的） |
|---|---|---|
| 銃槍龍杭：未鍛金之針（`wyrmstake`） | `Art/VFX/Mesh/Weapon/it07/11_it07_000` | 原版杭的尖端朝 **+Z**（z 1.52 收成一點）、尾翼在 -0.8 → 針尖朝 +Z、針眼在尾端，0.5 的原型 ×4.7：長 2.34 m（原版 2.35） |
| 輕弩起爆龍彈：象牙花苞（`wyvernblast`） | `Art/VFX/Mesh/Weapon/it13/11_setbombshell_000` | 原版是對 Y 軸對稱的圓頂（x、z ±0.25，y -0.13～+0.24）→ +Y 朝上、地面在 -0.13；閉合的花苞 ×5：高 0.39 |

## 跟原版一樣的地方（為了讓特效照常驅動）

- **沒有骨架**、**一個材質 `lambert1`**：材質抄黏著彈 `11_stickyshell_000` 的特效材質（`VFX_Standard_Simple_E`，有發光貼圖），貼圖換成我們的；`EmissiveParam`（原版黑色、由特效控制）設成金色
- **顯示群組**：原版分成好幾組重疊的零件（龍杭 10 組、起爆龍彈 3 組），特效挑其中幾組顯示 → 我們**每一組都放完整的模型**，不管顯示哪組都看得到。風險：如果特效把某組當碎片飛出去，會看到好幾根針／花苞
- 貼圖：一張 64×64 分成三條：金（金屬、微光 150）、象牙、發光（`texture_sources/`，`Art/Model/MiquellaLight/Devices/tex/`），每個零件的 UV 指到自己的顏色

## 還沒做的裝置

- **重弩**：`weapon/it12/11_it1299_0001_0`（0.46 m 扁片）和 `Art/Model/Item/it12/99/0001/it1299_0001_0`（有鉸鏈、板子會展開）不確定是哪個技能，要在遊戲裡確認
- **弓追蹤箭**：箭是共用的 `common/shell/arrow/11_arrow_00～04`，不知道哪支是追蹤箭；換掉會影響所有弓的箭
- **狩獵笛響玉**：`common/other/bubble` 可能是魔物的泡沫狀態用的，換掉會影響別的東西
- 爆炸、金紋、光環都是**特效**，不是模型（研究筆記第 16 節的做法）

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_device_kit.py <wyrmstake|wyvernblast> <本資料夾> <原版 .mesh.241111606> <11_stickyshell_000.mdf2.45>
```

原版從遊戲解出：`extract_game_files.py ... "art/vfx/mesh/(weapon/it(07|12|13)|common/shell/arrow|common/other/bubble[^/]*)/[^/]*\.(mesh|mdf2)\."`。打包：本資料夾的 `natives` → `make_patch_pak.py` → `MiquellaLight_Devices.pak`（2026-10-02 已裝進遊戲）。`.blend`、`dds/` 不進 repo。
