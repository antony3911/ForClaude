# MiquellaLight_Character_kit — 角色素材包（目前只有頭冠）

| kit | 檔案 | 說明 |
|---|---|---|
| `circlet` | `Art/Model/MiquellaLight/Character/mq_circlet.mesh`／`.mdf2` | 頭冠（光環）v10，約 1.5 萬面；材質 `MiquellaHalo`（象牙底、整個發金光）、`MiquellaGlow`（墜飾水滴） |

**重建**（bpy45）：

```
python build_weapon_kit.py circlet <這個資料夾> <it0100_0002_0.mesh.241111606> <雙劍 wp_miquella_db.mdf2.45>
python make_patch_pak.py <這個資料夾> MiquellaLight_Character.pak <RE Asset Library 所在資料夾>
```

**座標**：檔案空間＝獵人 `Head` 骨頭的空間（綁定姿勢）：+Y 上、+Z 臉的前方、+X 獵人的左手邊，原點是 `Head`（綁定姿勢在 (0, 1.573, -0.010)，幾乎沒有旋轉）。骨架借片手劍原版的（只當載體，全部頂點在 `Base`），由 `MiquellaLight_Character.lua` 把物件掛到 `Head` 上。

**尺寸**（2026-10-02 量遊戲的頭：臉 `ch00_000_0000`、頭髮 `ch01_000_0001`）：眉上（y 1.69）光頭寬 ±0.074、前後 -0.096～+0.101；加頭髮寬 ±0.09、後 -0.117。原型的頭冠圍在 0.074／0.094／0.112 的頭上（帶寬 ±0.075），放大 (1.22, 1.10, 1.12)（寬、高、深）讓兩側戴在頭髮上；正面在 y 1.70、z +0.103（世界座標）。`build_weapon_kit.py` 的 `CIRCLET_SCALE`、`CIRCLET_AT`。

**材質**：`MiquellaHalo` 抄雙劍的 `MiquellaIvory`，發光貼圖換成 `MiquellaGlow_EMI`、`Emissive_Color` (1.0, 0.72, 0.30)、`Emissive_Intensity` 0.8（`HALO_EMISSIVE`、`HALO_INTENSITY`）。貼圖用雙劍 pak 的，**要裝 `MiquellaLight_DualBlades.pak`**。

預覽（放在遊戲的頭上，含卡普空模型，不進 repo）：`MiquellaTools\work\previews\circlet\circlet_on_game_head.png`。
