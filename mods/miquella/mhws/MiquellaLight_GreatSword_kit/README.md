# 大劍光劍：遊戲素材包

`build_weapon_kit.py great_sword` 從原型（`arsenal.great_sword`）一次做完：減面、對齊原版、骨架、材質。預覽：`C:\Users\anton\MiquellaTools\work\previews\great_sword_vs_original.png`（畫了原版模型，**不進 repo**）（灰色是原版 `it0000_0000`）。

| 檔案 | 內容 |
|---|---|
| `natives/STM/Art/Model/MiquellaLight/GreatSword/wp_miquella_gs.mesh.241111606` | 模型，4.5 萬面，全部綁 `Base` |
| `.../wp_miquella_gs.mdf2.45` | 材質：`MiquellaBlade`、`MiquellaGlow`、`MiquellaIvory`、`MiquellaTemper`（刃紋，獨立出來給三段蓄力的光流用）、`MiquellaGrow1～24`（三條纏繞刀身的光絲，依出現的時間切段：換裝腳本跟著蓄力時間讓它們從護手長到刀尖，一段 40 %、二段 75 %、三段到頂，2026-10-03）、`MiquellaCharge3`（三段時刃口飛出的火花）。光絲另外綁在自己的骨頭上：每條光絲 48 根 `MQ_G0_1～48`、`MQ_G1_*`、`MQ_G2_*`（就在光絲上、每段兩根），換裝腳本把正在長的那段從一個點連續拉出來；骨頭表在 `wp_miquella_gs_grow.lua` |
| `wp_miquella_gs_kit.blend` | 匯出前的場景 |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。

## 對齊原版（從解出的原版量的）

- 原版大劍：刀身朝 **+Z**，**手在原點、就在護手正下方**，握柄往下長到 -0.77～-0.83 m，刀尖 1.9～2.3 m
- **刃口朝 -X**：單刃的原版（例 `it0000_0007` 刀尖在 +X、-X 那邊往刀尖收）和太刀的弧度（凸面在 -X）都這樣。我們的原型刃口在 +X → 繞 Z 轉 180°
- 握柄從 0.36 拉長到 0.48（原型單位），雙手才握得下；整把放大 1.6 倍：刀身約 1.9 m、寬 0.37 m（原版 0.5～0.8，維持纖細）
- 骨架用 `it0000_0000` 的（`root`、`Base`、`Grip`、`CH_00`、`CH_end`、`VFX_Attack`），`VFX_Attack` 移到我們的刀尖 (-0.12, 0, 2.14)

## 浮動環

大劍刀背的三個環各綁一根新骨頭（`MQ_Ring0～2`，`Base` 的子骨頭、沒有旋轉、樞紐在環中心，位置見建置 log 和換裝腳本的 `KITS`），換裝腳本每幀推動（`FLOAT_MODES`）。其他頂點都綁 `Base`。

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py great_sword <本資料夾> <原版 it0000_0000_0.mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\wp_miquella_gs_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\great_sword_vs_original.png front 1.0
```

打包：把本資料夾的 `natives` 和雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖放進同一個暫存資料夾，再 `make_patch_pak.py` → `MiquellaLight_GreatSword.pak`。

## 還沒驗證（要進遊戲）

- 雙手握的位置、刃口方向（揮砍時有光痕的 S 形那一邊要朝前；反了就改成不轉 180°）
- 蓄力三段的視覺（等 Watch 找到蓄力欄位）
