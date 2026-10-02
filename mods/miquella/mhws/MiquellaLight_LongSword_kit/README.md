# 太刀光劍：遊戲素材包

`build_weapon_kit.py` 從原型一次做完：減面、依材質分槽、照原版擺放、原版骨架、材質。

| 名稱 | 模型 | 原版（骨架、對齊用） | 擺放 |
|---|---|---|---|
| `long_sword` | `wp_miquella_ls.mesh` | `it0300_0000_0` | 握柄 0.34→0.42、×1.9：刀尖 2.13 m（原版 2.17～2.2）、握柄到 -0.78；繞 Z 轉 180°：刃口 -X、刀尖彎向 +X 跟原版一樣。刃紋、刀身各切 8 段（`MiquellaBand1～8`、`MiquellaBlade1～8`，同一段長度從刀根到刀尖），換裝腳本讓練氣光帶從刀根流到刀尖（2026-10-02：只有刃紋太細看不到）。刀鐔的兩個光環磁浮（`MQ_Tsuba0/1`）。**兩條光絲**纏刀身，依出現的時間切成 24 段 `MiquellaGrow1～24`：**氣刃大迴旋斬前的氣刃蓄力**時跟著蓄力時間長出來（2026-10-03 使用者：不是放在練氣段數上），大迴旋斬揮完才淡出（換裝腳本的 `grow`） |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。材質抄雙劍 kit 的 `.mdf2`（現在遊戲的 180 參數排列）。`.blend`（匯出前的場景）不進 repo，用下面的指令重建。

## 共通規則（2026-10-02 第二個帳號做的第一版，還沒進遊戲測）

- 照原版擺放：武器沿 **+Z**、**手在原點**，長度照原版縮放（見上表）；頂點都綁 `Base`，除非表裡另外寫
- **光膜拿掉**：遊戲武器材質只有「鏤空裁切」沒有半透明，淡光膜會變成實心金片 → 盾只留光環和樹紋（之後可做「防禦時才出現光膜」）
- 盾牌是**另一個外觀**（副武器 `_1`）：換裝腳本選單裡 Weapon、SubWeapon 兩個槽各選一個；`KITS` 裡主武器的 `shield` 欄位寫了配對的盾
- 原版盾牌正面朝 **+Y**（窄的握把在 -Y、手臂那側；盾面最寬在 y +0.05～+0.15，逐層量的），我們的盾轉 180° 並放在那個深度，不穿過手臂

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py <名稱> <本資料夾> <原版 .mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\<模型>_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\<模型>_front.png front <間距>
```

打包：本資料夾的 `natives` ＋雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖放進同一個暫存資料夾 → `make_patch_pak.py` → `MiquellaLight_LongSword.pak`（2026-10-02 已裝進遊戲的 `pak_mods`）。
