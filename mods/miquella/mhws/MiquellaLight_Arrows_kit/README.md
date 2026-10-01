# 弓的光箭：遊戲素材包

**蓋過遊戲原本的箭**（patch pak `MiquellaLight_Arrows.pak`，所有弓都會換；拿掉 pak 就恢復原版）。箭是遊戲自己生的，換裝腳本碰不到。

光箭（`arsenal.light_arrow`）：三片細長後掠的金光羽毛、細光箭身、光環箍、**長葉形光箭頭**（跟雙劍的葉形光刃同系列，中間一條較亮的脈）、象牙箭尾珠。原版的箭頭本來就很長（約半支箭），我們照原版的長度和寬度。

| 檔案 | 是什麼 | 擺放（從原版量的） | 做法 |
|---|---|---|---|
| `Art/Model/Item/it11/99/0000/it1199_0000_0` | **拉弓時手上那支箭** | 箭尾在原點附近（-0.04）、箭尖 +Z 2.69、箭頭從 1.32 開始 | `build_weapon_kit.py arrow`（原版骨架 root／Base，材質抄雙劍 kit，約 3200 面） |
| `Art/VFX/Mesh/common/shell/arrow/11_arrow_00`、`01`、`02` | **射出去的箭**（特效模型） | 同一支箭往後移 1.1：箭尾 -1.14、箭尖 1.588 | `build_device_kit.py arrow_00／01／02`（跟武器裝置一樣：沒有骨架、一個 `lambert1`、裝置的三色貼圖；`02` 有兩個顯示群組，兩組都放整支箭） |

**沒換的**（原版有額外零件，不知道是哪種箭，換了可能少東西）：`11_arrow_03`（後面多一大截）、`11_arrow_04`／`it1199_0005_0`（箭身中段多一個寬的零件，可能是瓶子）、`it1199_0002_0`（兩組、有 `VFX_Spark` 骨頭）、`it1199_0004_0`（0.34 m 的小東西）。實測時如果還看到木頭箭，記下是什麼時候（哪種瓶、哪個招式）

## 重做

```
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_weapon_kit.py arrow <本資料夾> <it1199_0000_0.mesh.241111606> <雙劍 kit 的 wp_miquella_db.mdf2.45>
C:\Users\anton\MiquellaTools\bpy45\Scripts\python build_device_kit.py arrow_00 <本資料夾> <11_arrow_00.mesh.241111606> <11_stickyshell_000.mdf2.45>
```

原版從遊戲解出：`extract_game_files.py ... "art/model/item/it11/99/.*\.(mesh|mdf2|chain2)\."`。打包：本資料夾的 `natives` ＋雙劍的 `MiquellaBlade/Glow/Ivory` 貼圖＋裝置 kit 的 `Devices/tex` → `make_patch_pak.py` → `MiquellaLight_Arrows.pak`。`.blend` 不進 repo；`build_device_kit.py` 會在這裡另外產生一份裝置貼圖（`texture_sources/`、`dds/`、`natives/.../Devices/tex`），跟裝置 kit 的一樣，刪掉即可。
