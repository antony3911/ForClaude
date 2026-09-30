# 魔物獵人 Wilds（RE 引擎）mod 研究筆記

整理日期：2026-09-30。都是讀社群文件和開源 mod 原始碼得來的，還沒在遊戲裡實測。

## 參考來源

- RE Engine Modding Wiki（Havens-Night/REEngine-Modding-Documentation 及其 wiki）：打包、解包、模型、貼圖教學
- RE Mesh Editor、RE Chain Editor、RE Asset Library 的 README（NSACloud）
- REFramework 文件（cursey/reframework-book）
- MDF-XL 原始碼（SilverEzredes/MDF-XL）：Wilds 的執行期材質編輯器，裡面有隱藏武器、偵測拔刀的寫法

---

## 1. 檔案類型

| 副檔名 | 內容 |
|---|---|
| `.mesh` | 模型和骨架 |
| `.mdf2` | 材質定義：模型用哪些材質、每個材質用哪些貼圖 |
| `.tex` | 貼圖（包著一個 .dds） |
| `.chain` / `.chain2` | 骨頭的擺動物理（頭髮、衣服）。Wilds 用 chain2 |
| `.pfb` | Prefab：決定一個物件用哪個 mesh、mdf、chain |
| `.clsp` | 碰撞形狀（讓擺動的布料被腿擋住） |

## 2. 解包遊戲檔案（之前筆記裡「待查」的部分）

- **首選：RE Asset Library**（Blender 外掛，Blender 4.3.2 以上）
  - 可以在 Blender 裡搜尋、預覽模型，拖進場景時自動解包需要的檔案
  - **可以只解包需要的類型**：只選「Model Related Files、Prefab Files、User Files」通常就夠了，不用解包整個遊戲 → 省空間
- 備用：RETool（Fluffy 網站）+ 檔名清單，或 ree-pak-gui / REE.PAK.Tool
- 注意：遊戲更新後會多出 `.patch_00X.pak`，**一定要用最新 patch 裡的檔案**，否則開遊戲會黑畫面

## 3. 替換模型的流程（武器最簡單）

1. 用 RE Asset Library 找到要替換的原版武器 `.mesh`，匯入 Blender（會連 `.mdf2` 一起匯入）
2. 匯入我們的模型，**放在跟原版一樣的位置、綁在跟原版一樣的骨頭上**（武器通常只有很簡單的權重）
3. 依材質拆開子模型，每個子模型**命名規則**：`Group_X_Sub_Y__材質名稱`
   - Group 0 = 永遠顯示；Sub 編號隨意（避免重名）；材質名稱要對應 `.mdf2` 裡的材質
   - Blender 裡的材質節點**不會**被匯出，遊戲只看 `.mdf2`
4. 權重：每個頂點最多 8 根骨頭、要正規化、不能有沒權重的頂點
5. 匯出 `.mesh` / `.mdf2` 到 mod 資料夾，路徑要跟原檔在 `natives/STM/...` 下的路徑一模一樣
6. 先進遊戲確認模型正常（貼圖還不對沒關係）；出現棋盤格貼圖或隱形 = `.mesh` 和 `.mdf2` 的材質名稱對不上
7. 做貼圖 → 轉成 `.tex` → 在 `.mdf2` 設定貼圖路徑（相對於 `natives/STM/`，**不能留空**）

## 4. Wilds 特有的限制（重要）

- **Wilds 的貼圖不能用散檔載入，一定要打包成 patch pak**
  - 用 RE Mesh Editor 的「Create Pak Patch」按鈕（需要裝 RE Asset Library 才會出現）
  - 產生的 pak 放在遊戲資料夾的 `pak_mods` 裡
  - 需要 REFramework 才會載入
  - 其他 mod 檔案也可以一起放進這個 pak
- RE Mesh Editor 的「Create Mod Workspace」會自動設好匯出、貼圖轉換、打包的路徑；「Copy Mod Files to Game」可以一鍵複製到遊戲資料夾測試

## 5. 貼圖與材質

RE 引擎的貼圖是**通道打包**的，一張圖的 RGBA 四個通道分別存不同資訊：

| 類型 | 內容 |
|---|---|
| ALBD | RGB = 顏色，A = Dielectric（反向金屬度，黑 = 金屬） |
| ALBM | RGB = 顏色，A = 金屬度 |
| NRRC | R = 粗糙度、G = 法線 Y、B = Cavity、A = 法線 X（新作常用） |
| ATOC / ATOS | 透明度、半透明、AO、Cavity/SSS |
| **EMI** | **發光遮罩** ← 我們的光劍、光環、紋章都要靠這個 |

- 顏色貼圖存 BC7 sRGB，其他存 BC7 Linear
- **透明需要材質開 Base Alpha Test**，或用本來就支援透明的材質 → 能量盾的透明光膜要找遊戲裡現成的半透明發光材質來改（待實測）
- 同一張貼圖有低解析度版（跟 mesh 放一起）和高解析度版（`streaming` 資料夾），建議兩個都做
- **MDF-XL 可以在遊戲執行中即時調整材質參數**（上百個參數、可以存成預設）→ 很適合用來調整發光顏色和強度，不用反覆匯出

## 6. 擺動物理（頭髮、長袍）

- RE Chain Editor：在 Pose Mode 選一條骨鏈的第一根，按「Chain From Bone」建立 Chain Group
  - 一條鏈**不能分岔**
  - 重要設定：Attribute Flags（各遊戲不同，有下拉選單）、角度限制、碰撞半徑、碰撞過濾
- 物理骨頭先從骨架複製出來另外保管，綁完權重再接回去

## 7. 打包成 Fluffy Mod Manager 的格式

```
MyModName/
├── modinfo.ini
├── thumbnail.png
├── natives/            ← 替換檔案，路徑照原檔
└── reframework/
    ├── autorun/        ← Lua 腳本
    └── data/           ← 腳本設定檔（json）
```

`modinfo.ini` 的欄位：name、version、author、description、screenshot，以及 [Options] 下的 category、addonfor、requirement。

## 8. REFramework 腳本（從 MDF-XL 學到的寫法）

| 目的 | 寫法 |
|---|---|
| 取得玩家 | `sdk.get_managed_singleton("app.PlayerManager"):getMasterPlayer()`，再 `:get_Character()` |
| 主武器 / 副武器（盾） | `playerCharacter:get_Weapon()` / `get_SubWeapon()`，再 `:get_GameObject()` |
| 判斷有沒有拔刀 | hook `app.HunterCharacter` 的 `checkWeaponOn()`，讀 `_IsWeaponOn`（只看 ToString 含 `MasterPlayer` 的） |
| 隱藏 / 顯示 | `gameObject:set_DrawSelf(false / true)` |
| 設定檔 | `json.load_file` / `json.dump_file`（路徑相對於 `reframework/data`） |
| 選單 | `re.on_draw_ui` + `imgui.checkbox` / `button` / `tree_node` |

MDF-XL 在某些選單開啟時不隱藏武器（避免裝備畫面預覽看不到武器），我們的腳本之後也要注意這點。

→ 已根據這些寫法起草 `mods/miquella/mhws/MiquellaLight_HideSheathed/`（收刀時隱藏光劍，未實測，Lua 語法檢查通過）。

## 9. 對我們計畫的影響

- **工具清單要補**：RE Asset Library（解包）、RE Toolbox（批次整理權重）、MDF-XL（即時調材質）
- **Blender 版本**：RE Mesh Editor / RE Asset Library 需要 4.3.2 以上，而且 RE Mesh Editor 說 5.1 有匯入匯出很慢的 bug → 魔物獵人用的 Blender 裝 **4.3.2 ~ 5.0**；法環用的 Soulstruct 要 5.1 以上 → 兩個版本並存的結論不變
- RE Mesh Editor、RE Chain Editor、RE Asset Library 的作者都已停止維護 → 遊戲大改版後可能失效
- 武器替換是最容易的一步，**第一個實際 mod 從雙劍開始**的計畫合理
- 發光要靠 EMI 發光遮罩 + 材質參數；能量盾的半透明要另外研究材質

## 10. 回家後要在遊戲裡確認的事

- [ ] 雙劍、片手劍、太刀、重弩、輕弩各選一把「被替換的原版武器」，記下它的 mesh 路徑和 GameObject 名稱
- [ ] 原版武器的 `.mdf2` 有沒有發光相關的參數或 EMI 貼圖槽
- [ ] 有沒有現成的半透明發光材質可以借給能量盾用
- [ ] 收刀隱藏腳本實測：`checkWeaponOn()` 在 Wilds 目前版本還存不存在、隱藏時有沒有影響裝備畫面
