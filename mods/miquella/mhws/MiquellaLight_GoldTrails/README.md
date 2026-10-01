# 真鬼人化的攻擊軌跡改金色（特效改色）

使用者要求（2026-10-01）：雙劍**真鬼人化**時攻擊會拖出紅色流光（攻擊軌跡），改成金色。

## 做法

雙劍的特效檔在 `natives/STM/Art/VFX/EffectEditor/Weapon/it02/`，共 7 個：

| 檔案 | 內容（從特效名稱判斷） | 紅色欄位 |
|---|---|---|
| `11_it02_001.efx` | **`R_trail`：攻擊軌跡**（紅），`R_trail0`（藍，用途待查）；外部參數 `Color` 預設紅 | 28 → **已改金** |
| `11_it02_000.efx` | 開鬼人化時的火焰爆發（`IMP_fire`） | 16，沒改 |
| `11_it02_002.efx` | 鬼人化時前臂的火焰（參數 `IsKijin`、`ColorA` 紅） | 9，沒改 |
| `11_it02_003.efx` | 火焰／光（參數 `Color` 粉紅） | 4，沒改 |
| `11_it02_004.efx` | 電光軌跡、身體發光 | 0 |
| `11_it02_900/901.efx` | 碎石、電光 | 0／2 |

`prototypes/scripts/recolor_efx.py` 只改**已知是顏色**的欄位（`TypeRibbonParticle` 的 color1/2、ukn22～24，`RgbCommon` 的 green/red channel 顏色，型別 1 的外部參數預設值），而且只改**紅色**的：色相換成金色（預設 38°，偏深的金，避免泛白），飽和度、亮度、透明度不變。結構照 kagenocookie 的 REE-EFX-Unified 010 範本（`efx_walk.py`）。

## 這是改過的遊戲檔案

**不放進 repo**。從使用者自己的遊戲檔案產生，打成獨立的 pak，可以單獨關掉：

```
python extract_game_files.py <遊戲資料夾> <檔名清單> <解出資料夾> <RE Asset Library 資料夾> "art/vfx/effecteditor/weapon/it02/"
python recolor_efx.py <解出資料夾>/natives/stm/art/vfx/effecteditor/weapon/it02/11_it02_001.efx.5571972 <工作資料夾>/goldtrail/natives/STM/Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx.5571972
python make_patch_pak.py <工作資料夾>/goldtrail MiquellaLight_GoldTrails.pak <RE Asset Library 資料夾>
```

放進遊戲的 `pak_mods/`。不要了就刪掉 `MiquellaLight_GoldTrails.pak`。**遊戲更新改到這個特效檔時要重做**（不然會用到舊版的特效，可能出錯）。

## 還不確定

- 遊戲可能在執行時用外部參數 `Color` 指定顏色（那樣檔案裡的預設值會被蓋掉）→ 要實測
- 如果實測還是紅的，再看 `004`（電光軌跡）或用腳本在執行時改特效顏色
