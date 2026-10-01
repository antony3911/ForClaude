# 輕弩：遊戲素材包

`build_weapon_kit.py light_bowgun` 從原型（`light_bowgun.py`）一次做完：減面、對齊原版、骨架、材質。預覽：`C:\Users\anton\MiquellaTools\work\previews\light_bowgun_vs_original.png`（畫了原版模型，**不進 repo**）（下面灰色是原版 `it1300_0002`）。

| 檔案 | 內容 |
|---|---|
| `natives/STM/Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh.241111606` | 模型，4.1 萬面，全部綁 `Base` |
| `.../wp_miquella_lbg.mdf2.45` | 材質：`MiquellaBlade`（光束）、`MiquellaGlow`、`MiquellaIvory`、`MiquellaGauge1～3`（槍管上的三顆懸浮光點，各自獨立，之後當速射量表） |
| `wp_miquella_lbg_kit.blend` | 匯出前的場景 |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。

## 對齊原版（從解出的原版量的）

- 原版輕弩：槍口朝 **+Z**，**+Y 朝上、-Y 朝下**（原版的掛繩、物理鏈都往 -Y 垂；這樣擺時握把、彈匣朝下，連發弩的彈匣在上面）
- **原點在機匣頂端**（像照門），槍膛在原點下方 0.16～0.23 m（`VFX_Fire` 的 y），握把在原點後方約 0.3 m，槍托到 -0.76～-0.96 m
- 我們的：原型放大 1.6 倍（原型 0.93 m → 1.5 m），槍膛 y = -0.19，往後挪 0.1 讓握把對上原版；範圍 z -0.74～+0.76，y -0.51～+0.02
- 骨架用 `it1300_0001` 的；`VFX_Fire`、`VFX_FireLong`、`VFX_FireSuppressor` 移到我們的槍口 (0, -0.19, 0.75)，開槍火光從最前面的光環出來

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py light_bowgun <本資料夾> <原版 it1300_0001_0.mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\wp_miquella_lbg_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\light_bowgun_vs_original.png gun 0.9
```

打包同大劍（`MiquellaLight_LightBowgun.pak`）。

## 還沒驗證（要進遊戲）

- 手握的位置、槍口火光的位置
- 速射量表（三顆光點）要用 Watch 找欄位
