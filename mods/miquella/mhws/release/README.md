# 可以直接安裝的測試版

`MiquellaLight_v0.1.zip`（也有解開的資料夾 `MiquellaLight_v0.1/`）：

| 檔案 | 內容 |
|---|---|
| `MiquellaLight_DualBlades.pak` | 雙劍光劍的模型、材質、貼圖（patch pak，放在自己的路徑 `Art/Model/MiquellaLight/...`，**不覆蓋任何原版檔案**） |
| `reframework/autorun/MiquellaLight_Weapons.lua` | 換裝腳本：在選單選哪把武器要顯示成光劍，收刀時隱藏 |
| `modinfo.ini`、`preview.png` | Fluffy Mod Manager 用 |

## 安裝

需要先裝好 REFramework。

**用 Fluffy Mod Manager（建議）**：把 `MiquellaLight_v0.1.zip` 拖進 Fluffy 的 Monster Hunter Wilds 分頁，勾選啟用。

**手動**（Fluffy 不行的話）：
1. `MiquellaLight_DualBlades.pak` 放進遊戲資料夾的 `pak_mods`（沒有就建立）
2. `reframework/autorun/MiquellaLight_Weapons.lua` 放進遊戲資料夾的 `reframework/autorun/`

## 第一次測試

1. 進遊戲，裝備任何一把雙劍
2. 按 Insert → Script Generated UI → **MiquellaLight: Light Weapons**
3. 「Weapon」和「SubWeapon」都選 `DualBlades`
4. 選單裡的 **Glow**（發光強度倍率，預設 1）和 **Size**（大小，預設 1）可以直接在遊戲裡拉，滿意的數字告訴 Claude
5. 拔刀看看。回報這幾件事（截圖最好）：
   - 看得到光劍嗎？選單有沒有紅字錯誤？
   - 方向、大小、握的位置對不對（第一次幾乎一定要調）
   - 發光顏色（亮金色）在遊戲裡的樣子
   - 收刀時有沒有消失、拔刀時有沒有出現

不想要了：選回 `(original)` 就會換回原版武器，或在 Fluffy 裡停用。

## 注意

- **還沒在遊戲裡測過**。pak 用 RE Asset Library 的程式產生並讀回驗證過；腳本用模擬 API 測試過流程。遊戲內的方法名稱、模型方向都要實測
- 只改外觀，不改數值和動作
- 重新產生 pak：`python mods/miquella/prototypes/scripts/make_patch_pak.py <素材包資料夾> <輸出.pak> <RE Asset Library 所在的資料夾>`
