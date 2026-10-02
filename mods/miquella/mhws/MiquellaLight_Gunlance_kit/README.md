# 銃槍（聖百合）＋能量盾：遊戲素材包

`build_weapon_kit.py` 從原型一次做完：減面、依材質分槽、照原版擺放、原版骨架、材質。

| 名稱 | 模型 | 原版（骨架、對齊用） | 擺放 |
|---|---|---|---|
| `gunlance` | `wp_miquella_gl.mesh` | `it0700_0000_0` | **聖百合**（2026-10-03 使用者選）。×1.3、手在握柄中間（跟第一版一樣）：百合花口 1.92 m、槍尖 2.35 m。`VFX_Fire`（砲擊）移到花口 (0, 0, 1.92)，`VFX_Pile`（龍杭＝金針出現的地方）在軸上 z 0.53，`VFX_Heat` 在軸上 z 1.153 |
| `gunlance_v1` | （同上的檔名） | `it0700_0000_0` | 第一版（三根光肋＋象牙彈簧，2026-10-03 使用者否決：簡陋、不好做特效），留著參考，**不要再匯出蓋掉聖百合** |
| `gunlance_shield` | `wp_miquella_gl_shield.mesh` | `it0700_0000_1` | 0.86 × 1.0 m，中心 (0, 0.10, -0.03)。還是長槍那面樹紋能量盾，配聖百合的盾之後再設計 |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。材質抄雙劍 kit 的 `.mdf2`（現在遊戲的 180 參數排列）。`.blend`（匯出前的場景）不進 repo，用下面的指令重建。

## 聖百合（2026-10-03）

使用者選的組合：本體 B 聖百合（`gunlance_designs.py design_b`）、蓄力時槍尖長出 C 光之百合（`gunlance_lily_charge.py option_c`）、槍身 C1 光葉＋C2 光花（`gunlance_lily_body.py`，不要 C3 光藤）。**原本的元素一個都不能砍，只加**。蓄力要「跟其他武器一樣是動畫，不是分段模型」。

做法（`prototypes/scripts/lily_rig.py`，同一套數學產生模型、骨頭的兩個姿勢和每個頂點的權重）：
- **蓄力才出現的零件全部做成滿蓄力的大小**（綁定姿勢），預設隱藏（`Dissolve` 0），骨頭在「小」和「滿」兩個姿勢之間移動，所以是連續長大，不是換模型：
  - 光之百合（花前用光線畫的大百合，1.2 → 2.6 倍）：每片花瓣兩側邊緣各兩根＋花瓣尖一根（`MQ_LL<瓣>_1L/1R/2L/2R/T`）、六根光花蕊（`MQ_LLS*`）、大光環八根（`MQ_LLH0～7`）
  - 光葉（四片莖葉 1.15 → 2.3 倍、三片鞘葉 1.1 → 1.9 倍，越長越往外張 18°）：每片兩側一半處各一根＋葉尖一根（`MQ_LF<葉>_1L/1R/T`）
  - 花苞的小光百合（0.22 → 0.4 倍，從花苞狀開到全開）：每片花瓣尖一根（`MQ_BL<花苞>_<瓣>`，花瓣寬度不變）
  - 花喉的光：三顆一顆比一顆大的光球（`MiquellaThroat1～3`）依序淡入；龍擊砲的三圈光環（`MiquellaFireHalo`）只在龍擊砲蓄能的最後淡入
- **象牙本體做成平時的樣子**，骨頭把它往後翻：六片花瓣各四根（`MQ_Tepal<瓣>_1～4`，花瓣長度 30／55／80／100 % 處）、六根花蕊尖（`MQ_Stamen*`）、花口光環（`MQ_Mouth`）
- 頂點權重：沿零件的位置（投影到它的中線，0 = 根部，綁 `Base`）在相鄰兩站的骨頭之間線性分配；有兩側骨頭的零件再依橫向位置分左右
- 共 126 根骨頭（加原版 16 根 = 142，上限 256）；三角面約 8.5 萬（象牙 3 萬、金光 1.4 萬、光之百合 9 千、光葉／光花各 6 千…）
- 材質：`MiquellaIvory`、`MiquellaGlow`、`MiquellaBlade`（槍尖＝雌蕊）、`MiquellaTemper`（槍尖中線）、`MiquellaLilyLight`、`MiquellaLeafLight`、`MiquellaBudLight`、`MiquellaThroat1～3`、`MiquellaFireHalo`、`MiquellaGauge1～5`（五個花苞尖的光滴＝彈數，一顆一個材質）
- 匯出時另外寫 **`wp_miquella_gl_bloom.lua`**（貼進換裝腳本的 `LILY_GL`，重建模型後要重貼）和 `.json`（預覽用）：每根骨頭的綁定位置、另一個姿勢（`base`＝小、`alt`＝往後翻）、由哪個進度推動（`open` 象牙、`glow` 光、`wyvern` 龍擊砲光環）、在進度的哪一段移動；淡入的材質和它們的進度區間

預覽（跟遊戲一樣的骨頭算法）：`preview_bloom.py <本資料夾>\wp_miquella_gl_kit.blend <本資料夾>\wp_miquella_gl_bloom.json <輸出前綴> [full|head]` → 一段龍擊砲的 GIF（蓄能 → 發射 → 光在原地淡出、花瓣回位）和 0～100 % 的格子圖，輸出在 `MiquellaTools\work\previews\gunlance\bloom\`。

## 共通規則（2026-10-02 第二個帳號做的第一版）

- 照原版擺放：武器沿 **+Z**、**手在原點**，長度照原版縮放（見上表）；頂點都綁 `Base`，除非表裡另外寫
- **光膜拿掉**：遊戲武器材質只有「鏤空裁切」沒有半透明，淡光膜會變成實心金片 → 盾只留光環和樹紋（之後可做「防禦時才出現光膜」）
- 盾牌是**另一個外觀**（副武器 `_1`）：換裝腳本選單裡 Weapon、SubWeapon 兩個槽各選一個；`KITS` 裡主武器的 `shield` 欄位寫了配對的盾
- 原版盾牌正面朝 **+Y**（窄的握把在 -Y、手臂那側；盾面最寬在 y +0.05～+0.15，逐層量的），我們的盾轉 180° 並放在那個深度，不穿過手臂

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py <名稱> <本資料夾> <原版 .mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\<模型>_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\<模型>_front.png front <間距>
```

打包：本資料夾的 `natives` 複製進 `MiquellaTools\work\stage_Gunlance\`（裡面已有雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖和盾）→ `make_patch_pak.py`（`bpy45` 的 Python）→ `MiquellaLight_Gunlance.pak`。**2026-10-03 聖百合版已裝進遊戲的 `pak_mods`**（遊戲關著直接裝、比對過）。
