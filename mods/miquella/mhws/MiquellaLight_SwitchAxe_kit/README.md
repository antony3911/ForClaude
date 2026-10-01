# 斬擊斧（斧＋劍模式，會變形）：遊戲素材包

`build_weapon_kit.py` 從原型一次做完：減面、依材質分槽、照原版擺放、原版骨架、材質。

| 名稱 | 模型 | 原版（骨架、對齊用） | 擺放 |
|---|---|---|---|
| `switch_axe` | `wp_miquella_sa.mesh` | `it0800_0000_0` | **斧、劍兩種型態在同一個模型**（2026-10-02，見下面「變形」）。手在柄底上 0.38，×1.9：柄往下 0.72（原版 0.83）、斧頂 1.67（原版 1.96）、劍尖 2.77；繞 Z 轉 180°：斧刃朝 -X 跟原版一樣。`VFX_Attack_A` 移到斧頂 |

貼圖沿用雙劍的（`Art/Model/MiquellaLight/DualBlades/tex/`），pak 裡自帶一份。材質抄雙劍 kit 的 `.mdf2`（現在遊戲的 180 參數排列）。`.blend`（匯出前的場景）不進 repo，用下面的指令重建。

## 共通規則（2026-10-02 第二個帳號做的第一版，還沒進遊戲測）

- 照原版擺放：武器沿 **+Z**、**手在原點**，長度照原版縮放（見上表）；頂點都綁 `Base`，除非表裡另外寫
- **光膜拿掉**：遊戲武器材質只有「鏤空裁切」沒有半透明，淡光膜會變成實心金片 → 盾只留光環和樹紋（之後可做「防禦時才出現光膜」）
- 盾牌是**另一個外觀**（副武器 `_1`）：換裝腳本選單裡 Weapon、SubWeapon 兩個槽各選一個；`KITS` 裡主武器的 `shield` 欄位寫了配對的盾
- 原版盾牌正面朝 **+Y**（窄的握把在 -Y、手臂那側；盾面最寬在 y +0.05～+0.15，逐層量的），我們的盾轉 180° 並放在那個深度，不穿過手臂

## 變形（2026-10-02）

使用者：換模型是「直接閃現」很怪，要變形動畫。現在**不換模型**，腳本在 `_Mode` 改變時用 0.45 秒把骨頭從一個姿勢動到另一個，只屬於一種型態的零件用 `Dissolve` 淡入淡出（預覽：`prototypes/action_states/switch_axe_morph*.gif／png`）。
- 零件分組、各自材質：`MiquellaAxe*`（三片斧刃，斧模式）、`MiquellaSpike*`（頂端尖刺）、`MiquellaSword*`（長光刃）、`MiquellaFin*`（劍背三片羽翼）；共用的（柄、卷草、光點）照舊。劍模式的零件在 `.mdf2` 裡 `Dissolve` 0，腳本沒跑時就是斧
- 骨頭：`MQ_Blade0～2`（斧刃，支點在刃根）、`MQ_Fin0～2`（羽翼）：用最小平方法把每片斧刃剛體對到同名的羽翼（`rigid_fit`），斧刃往上翻到劍背、途中淡成羽翼；`MQ_SwordTip`：長光刃的頂點依高度綁在 `Base` 和它之間，斧模式時它壓到刃根（刃壓扁、看不見），變形時往上長出；`MQ_HeadHalo`：頂端光環滑到劍根
- `build_weapon_kit.py` 寫出 `wp_miquella_sa_morph.lua`（貼進換裝腳本的 `MORPH_SA`）和 `.json`（給 `preview_morph.py`）；重建後兩個都要更新

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py <名稱> <本資料夾> <原版 .mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_kit.py <本資料夾>\<模型>_kit.blend <原版 .mesh> C:\Users\anton\MiquellaTools\work\previews\<模型>_front.png front <間距>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python preview_morph.py <本資料夾>\wp_miquella_sa_kit.blend <本資料夾>\wp_miquella_sa_morph.json C:\Users\anton\MiquellaTools\work\previews\morph\sa
```

打包：本資料夾的 `natives` ＋雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖放進同一個暫存資料夾 → `make_patch_pak.py` → `MiquellaLight_SwitchAxe.pak`（2026-10-02 已裝進遊戲的 `pak_mods`；變形版 05:12 重裝）。舊的劍模式模型 `wp_miquella_sa_sword` 已拿掉。
