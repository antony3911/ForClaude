# 充能斧（劍＋盾）：遊戲素材包

`build_weapon_kit.py` 從原型一次做完：減面、依材質分槽、照原版擺放、原版骨架、材質。

| 名稱 | 模型 | 原版（骨架、對齊用） | 擺放 |
|---|---|---|---|
| `charge_blade` | `wp_miquella_cb.mesh` | `it0900_0000_0` | **劍和斧模式的斧頭在同一個模型**（2026-10-02，見下面「變形」）。原型的 0.8 刀身改 1.3，×1.4：刀尖 1.93 m（原版 1.92）；繞 Z 轉 180°：斧刃朝 -X。刀上的五顆瓶子光點一起 |
| `charge_blade_shield` | `wp_miquella_cb_shield.mesh` | `it0900_0000_1` | 能量盾＋五顆瓶子＋斧刃，×1.4，中心 (0, 0.12, 0)。原版盾沒有頂點綁 `Base`（都在 `Emblem`／`L_Blade`／`R_Blade`），我們整個綁 `Emblem`。斧模式時淡出（見「變形」）；正面看斧刃有點像新月，使用者決定先擱置 |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。材質抄雙劍 kit 的 `.mdf2`（現在遊戲的 180 參數排列）。`.blend`（匯出前的場景）不進 repo，用下面的指令重建。

## 共通規則（2026-10-02 第二個帳號做的第一版，還沒進遊戲測）

- 照原版擺放：武器沿 **+Z**、**手在原點**，長度照原版縮放（見上表）；頂點都綁 `Base`，除非表裡另外寫
- **光膜拿掉**：遊戲武器材質只有「鏤空裁切」沒有半透明，淡光膜會變成實心金片 → 盾只留光環和樹紋（之後可做「防禦時才出現光膜」）
- 盾牌是**另一個外觀**（副武器 `_1`）：換裝腳本選單裡 Weapon、SubWeapon 兩個槽各選一個；`KITS` 裡主武器的 `shield` 欄位寫了配對的盾
- 原版盾牌正面朝 **+Y**（窄的握把在 -Y、手臂那側；盾面最寬在 y +0.05～+0.15，逐層量的），我們的盾轉 180° 並放在那個深度，不穿過手臂

## 變形（2026-10-02）

使用者：換模型是「直接閃現」很怪，希望**盾形變成斧模式的那個樣子**。現在**不換模型**，腳本在 `_Mode` 改變時用 0.5 秒變形（預覽：`prototypes/action_states/charge_blade_morph*.gif／png`）：
- 盾（副武器 `_1`，另一個 GameObject，沒辦法跟劍共用骨頭）在前 40 % 淡出，淡完才隱藏
- 劍上同時浮出一圈**盾那麼大的橢圓光環**，再變形成斧頭的輪廓：輪廓上 24 根骨頭 `MQ_Rim0～23`（沿輪廓等長分布），光環和斧刃的頂點依輪廓位置綁在相鄰兩根之間；劍模式時骨頭排成盾的橢圓（半徑 0.2835 × 1.18，×1.4），斧模式回到原位
- 劍身從 1.3 縮成 0.8（斧頭的柄和脊；頂點依高度綁 `Base`／`MQ_SwordTip`）
- 劍上的五顆光點（`MQ_Phial0～4`）從護手上的光環飛到斧背排成一列（斧模式的瓶數量表）
- 接著斧刃（`MiquellaEdge*`）、樹紋、卷草、光點的小光環（`MiquellaAxe*`）淡入；橢圓光環是 `MiquellaRimGlow`。斧的零件在 `.mdf2` 裡 `Dissolve` 0
- `build_weapon_kit.py` 寫出 `wp_miquella_cb_morph.lua`（貼進換裝腳本的 `MORPH_CB`）和 `.json`；重建後兩個都要更新

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py <名稱> <本資料夾> <原版 .mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\<模型>_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\<模型>_front.png front <間距>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_morph.py <本資料夾>\wp_miquella_cb_kit.blend <本資料夾>\wp_miquella_cb_morph.json C:\Users\anton\MiquellaTools\work\previews\morph\cb <本資料夾>\wp_miquella_cb_shield_kit.blend 0.6 0 0.9
```

打包：本資料夾的 `natives` ＋雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖放進同一個暫存資料夾 → `make_patch_pak.py` → `MiquellaLight_ChargeBlade.pak`（2026-10-02 已裝進遊戲的 `pak_mods`；變形版 05:12 重裝）。舊的斧模式模型 `wp_miquella_cb_axe` 已拿掉。
