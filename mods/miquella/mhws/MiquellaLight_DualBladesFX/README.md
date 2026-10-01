# 雙劍鬼人化的特效改色：紅 → 金、藍 → 銀

使用者要求（2026-10-01）：
- 鬼人化的全身紅光 → **全身金光**；真鬼人化的紅色攻擊軌跡 → **金色**
- 鬼人化中完美閃避進入的**藍色狀態**（使用者叫「藍鬼人」）：全身藍光 → **銀光**，藍色攻擊軌跡 → **銀色**

## 雙劍的特效檔（`natives/STM/Art/VFX/EffectEditor/Weapon/it02/`）

| 檔案 | 內容（從特效名稱、顏色判斷） | 改了幾個顏色 |
|---|---|---|
| `11_it02_000.efx` | 開鬼人化的爆發：全身閃光（`PLE_*` = 玩家發光控制）、火焰 | 紅 → 金 29 |
| `11_it02_001.efx` | 攻擊軌跡：`R_trail`（紅，真鬼人化）、`R_trail0`（藍，藍色狀態）；外部參數 `Color` | 紅 → 金、藍 → 銀，46 |
| `11_it02_002.efx` | 鬼人化期間：全身發光（`PLE`）、前臂火焰；參數 `ColorA` 紅、`ColorB` 藍、`ColorC` 淺紅、`IsKijin`、`IsBuff` | 13 |
| `11_it02_003.efx` | 火焰／光、火花（參數 `Color` 粉紅） | 紅 → 金 10 |
| `11_it02_004.efx` | **藍色狀態**：全身發光（`PLE_Body`、`PLE_Leg`）、電光軌跡、煙 | 藍 → 銀 16 |
| `11_it02_901.efx` | 電光 | 紅 → 金 3 |
| `11_it02_900.efx` | 碎石、火花 | 紅 → 金 1 |

全身發光是 `app.EffectPlEmissiveControl`（在 `PtBehavior` 裡，只有邊緣光寬度、強度這些，**沒有顏色**）；顏色來自同一個特效的 `TypeNoDraw.color`，有的再經過運算式用 `ColorA`／`ColorB` 切換。

## 工具

- `prototypes/scripts/efx_walk.py`：照 kagenocookie 的 REE-EFX-Unified 010 範本讀到每個屬性（Wilds 每個屬性都有自己的大小，未知的可以跳過）
- `prototypes/scripts/recolor_efx.py`：只改已知是顏色的欄位（`TypeRibbonParticle`、`TypeNoDraw`、`RgbCommon`；第二版加上 `TypeBillboard3D`、`TypeRibbonLength`、`TypeRibbonFollow`、`TypeGpuBillboard`、`TypeGpuRibbonLength` 的 color／colorRange；顏色型的外部參數預設值）。紅（色相 <25° 或 >320°）→ 金（色相 38°，偏深避免泛白，保留飽和度、亮度、透明度）；藍（190～265°）→ 銀（幾乎無彩度、亮度 ×0.9）；同一個特效項目裡只要有藍色，紅色也改成銀（那個項目屬於藍色狀態）

## 這是改過的遊戲檔案：不放進 repo

從使用者自己的遊戲檔案產生，打成獨立的 `MiquellaLight_DualBladesFX.pak`，不要了直接刪：

```
python extract_game_files.py <遊戲資料夾> <檔名清單> <解出資料夾> <RE Asset Library 資料夾> "art/vfx/effecteditor/weapon/it02/"
for n in 000 001 002 003 004 900 901:
    python recolor_efx.py <解出>/natives/stm/art/vfx/effecteditor/weapon/it02/11_it02_$n.efx.5571972 <工作>/dbfx/natives/STM/Art/VFX/EffectEditor/Weapon/it02/11_it02_$n.efx.5571972
python make_patch_pak.py <工作>/dbfx MiquellaLight_DualBladesFX.pak <RE Asset Library 資料夾>
```

**遊戲更新改到這些特效檔時要重做**。

## 第一次實測（2026-10-01）

- **有效**：一般型態的真鬼人攻擊軌跡變金
- **還是紅**：鬼人化中的真鬼人軌跡、鬼人化中手上的紅光氣；真鬼人一般型態身體在金紅之間閃爍
- 第一版漏了 5 種特效格式（光暈、火花、GPU 粒子），第二版補上（`000`、`003`、`900`、`901` 的紅光暈和火花，`004` 的藍光暈）
- 顏色運算式（解出來的）：`002` 的 `PLE` 和前臂火焰＝`lerp(lerp(ColorC, ColorA, IsKijin), ColorB, IsBuff)`（`PLE` 的 ColorA 先跟白色混 0.9）；`001` 的 `R_trail`＝`Color`。檔案的預設值都改了，所以還是紅的那些多半是**遊戲執行時設了顏色**，或是別的特效檔 → 用 `MiquellaLight_FxProbe` 錄下來確認

## 還不確定（要實測）

- 遊戲可能在執行時用外部參數（`Color`、`ColorA`…）指定顏色，那樣檔案裡的預設值會被蓋掉 → 如果還是紅／藍，改用腳本在執行時設定特效顏色
- 銀色在強光下可能看起來接近白光；太白的話把 `SILVER_VALUE` 調低
