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
  - 需要 REFramework 才會載入（REFramework 的 IntegrityCheckBypass → 「PAK Directory Loading」，設定名 `IntegrityCheckBypass_LoadPakDirectory`，**預設開啟**；檔名隨意，副檔名要小寫 `.pak`；改了要重開遊戲）
  - 2026-09 起 REFramework nightly 改成單一 `REFramework.zip`（所有 RE 遊戲共用的 dinput8.dll，執行時自己判斷遊戲），不再有 `MHWILDS.zip`
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

## 11. Wilds 材質：發光武器怎麼做（從 RE Mesh Editor 的材質預設查到）

RE Mesh Editor 內建 Wilds 的 MDF 材質預設，其中 **Weapon Emissive**（`WeaponEmissiveMat`）就是發光武器用的材質：

- Master Material：`MaterialShader/Variation/Base_ATOS_FX_SecEmit_VEmit_Detail_ColLayer_VFXwe.mmtr`（跟一般 Weapon 預設同一個，只是參數不同）
- 發光相關參數：
  - `Emissive_Color`：發光顏色（RGBA）→ 設成我們的亮金色
  - `Emissive_Intensity`：預設 1.5（一般武器 1.0）
  - `Emissive_Power`：預設 1.0（一般武器 0.0 = 不發光）
  - `RayTrace_Emissive_Booster`：預設 300（光追模式下的加強）
  - `Use_Basecolor_to_Emissive`：可以直接拿顏色貼圖當發光色
- 貼圖槽 `EmissiveMap`：發光遮罩（EMI），決定哪些部位發光 → 光刃整片白、刀柄黑
- 另有 `AlphaTest_Ref`、`AlphaAdjust`、`TranslucentParam` 等透明相關參數 → 能量盾的光膜可以從這裡下手

另外還有 Character Emissive 預設（`CharacterEmissiveMat_UseSC`，`Base_Equip.mmtr`），可以給頭冠用。

## 12. 管線測試：用腳本把原型匯出成 Wilds 模型檔（已成功）

在這個雲端環境用 Blender 4.5（無介面）+ RE Mesh Editor 0.66 測試，腳本在 `mods/miquella/prototypes/scripts/export_wilds_test.py`。

- **結果**：雙劍原型成功匯出成 `wp_miquella_test.mesh.241111606`（Wilds 格式，1.4 MB），重新匯入也正常讀回 4 個子模型
- **匯出器會先檢查格式**，這次抓到兩個規則：
  - 不能有孤立的頂點（沒有面的點）
  - **每個子模型都要有 UV**
  - → 腳本已自動處理：清除孤立頂點、沒有 UV 就自動展開
- 匯出器會自動三角化、自動計算包圍盒
- 無介面環境的小問題：外掛啟動後會留下背景執行緒，程式不會自己結束 → 腳本最後要強制結束；外掛的自動更新檢查也要關掉

**發現的問題：面數太高**
- 一把雙劍約 4.1 萬頂點、7.3 萬三角面，其中刀柄的編織細股就佔了 3.1 萬頂點
- 遊戲武器應該要低很多（實際標準等拿到遊戲裡的原版武器再比對）
- 做法：降低曲線的解析度、細股改少一點，**細節改用法線貼圖表現**（在 Blender 裡從高模烘焙到低模）
- **烘焙測試已成功**（`scripts/bake_grip_test.py`，結果在 `prototypes/game_ready_tests/`）：
  - 雙劍刀柄的高模 59,416 三角面 → 低模圓柱 32 三角面 + 1024×1024 法線貼圖
  - 編織紋路在低模上依然清楚，只有輪廓變平滑
  - 注意：RE 引擎的法線貼圖是 DirectX 格式、而且跟粗糙度打包在同一張（NRRC：R=粗糙度、G=法線Y、A=法線X），Blender 烘焙出來的是 OpenGL 格式 → 轉換時要翻轉 G 通道並重新打包

**這個測試還沒做的**（需要遊戲檔案）：
- 綁到原版武器的骨頭、對齊位置
- 材質名稱對應原版的 `.mdf2`
- 在遊戲裡實際顯示

## 13. 從 Wilds 完整檔名清單推測的路徑（部分已用 MDF-XL 資料庫確認，其餘未進遊戲確認）

來源：REE.PAK.Tool 的 `MHWs_STM_Release.list`（265,677 個檔案、16,859 個模型）。路徑在清單裡是小寫，例如 `natives/stm/art/model/...`。

### 武器：`art/model/item/it00` ~ `it13`

- 14 個資料夾剛好對應 14 種武器，每個模型有 `_0`、`_1` 兩個檔案（例：`it02/00/0002/it0200_0002_0.mesh`、`..._1.mesh`）
- 編號跟 MH World 同順序，**已由 MDF-XL 的武器資料庫確認**（`WeaponTypes: 0 = Great Sword | 1 = Sword & Shield | 2 = Dual Blades | 3 = Long Sword | ... | 12 = Heavy Bowgun | 13 = Light Bowgun`）：

| 編號 | 武器 | 內部名稱（`gamedesign/common/weapon/*.user`） |
|---|---|---|
| it00 | 大劍 | LongSword |
| it01 | 片手劍 | ShortSword |
| **it02** | **雙劍** | TwinSword |
| **it03** | **太刀** | Tachi |
| it10 | 操蟲棍 | — |
| **it12** | **重弩** | HeavyBowgun |
| **it13** | **輕弩** | LightBowgun |

- `_0` / `_1` 是兩個部件（**MDF-XL 資料庫確認**）：雙劍 `_0` = 左手、`_1` = 右手；片手劍 `_0` = 劍、`_1` = 盾；太刀 `_0` = 刀、`_1` = 刀鞘；弓 `_1` = 箭筒
  - 例：`it0200_0002_0` = Guild Knight Sabers (L)、`it0100_0002_1` = Quematrice Cuchillo (Shield)、`it0300_0000_1` = Dosha Fatecleaver (Scabbard)
  - 重弩、輕弩在資料庫裡**沒有**武器類型和路徑（只有 Hope Cannon、Hope Rifle 兩筆）→ 弩可能是組裝式的，換模型會比較麻煩，要進遊戲確認
- 雙劍約 31 款、太刀 28 款、重弩 13 款、輕弩 13 款左右（以不重複模型數估計）

### 人物

| 路徑 | 推測 | 證據 |
|---|---|---|
| `character/ch02/...` | 男性體型（Type 1）的防具 | 社群防具清單 |
| `character/ch03/...` | 女性體型（Type 2）的防具 | 社群防具清單 |
| ~~`ch02_000_0006` 是男性內衣身體~~ | **錯誤，已更正**：部件編號 `_0006` 是投射器，這是系列 000 的預設投射器 | MDF-XL 資料庫：`ch02_001_0006 = Hope Slinger` |
| `character/ch02/002/000/{1,2,4,5}/` | **男性內衣 a**：`_0001` 手、`_0002` 身體、`_0004` 腿、`_0005` 腰（`_0006` 投射器） | MDF-XL 資料庫：`ch02_002_0002 = Innerwear a Mail` |
| `character/ch02/002/100/...`（`ch02_002_1xxx`） | 男性內衣 b | 同上 |
| `character/ch03/002/...` | 女性內衣 a / b | 同上 |
| `character/ch02/000/900/ch02_000_9000.fbxskel` | **男性骨架定義**（還有 `.jcns` 關節限制、捏體型用的動作檔） | 檔名清單 |
| `character/ch01/000/0/001` ~ | **捏臉髮型**（約 48 款） | 有 `chain2` 物理檔、`alba`（顏色＋透明，髮片用）、`hf_msk`、`fa_msk` 貼圖 |
| `character/ch01/000/1/...` | 臉 / 皮膚 | 貼圖叫 `skin_alba` |
| `character/ch01/000/2/...` | 眉毛或鬍子之類 | `ho_alba` 貼圖 |
| `character/ch01/001/...` | 另一個體型的同樣內容 | 結構跟 000 相同 |

### 防具部件編號（MDF-XL 資料庫）

| 結尾 | 部件 | 備註 |
|---|---|---|
| `_0001` | 手（Vambraces） | |
| `_0002` | 身體（Mail） | |
| `_0003` | 頭（Mask / Helm） | 內衣沒有頭 |
| `_0004` | 腿（Greaves） | |
| `_0005` | 腰（Coil） | |
| `_0006` | 投射器（Slinger） | |
| `_001x` | 同一套的 B 型（Type 1B） | `ch02_001_0011` = Hope Vambraces（1B） |

### 對米凱拉計畫的意義

- 米凱拉是男性骨架 → 用 **ch02（Type 1）**
- 人物本體要替換的大概是：**內衣 a 的四個部件** `ch02_002_000{1,2,4,5}`（→ 身體＋長袍，可以把全部放進身體部件，其他三個換成空模型）、`ch01/000/0/` 其中一款髮型（→ 米凱拉的髮型＋`chain2` 擺動物理）
  - 內衣的身體和腰部件本來就有 `chain2`（擺動）和 `.clsp`（碰撞形狀），長袍下擺可以參考它們的設定
  - 另一條路：不替換任何檔案，用腳本把模型掛到獵人身上（見第 15 節）
- 髮型用的是 `alba`（有透明通道的髮片）→ 散髮要做成**髮片**，不是一根根的管子
- 以上都要回家用 RE Asset Library 實際打開確認

## 14. 頭髮：遊戲的做法和我們的原型

### 一款捏臉髮型包含的檔案（檔名清單，`ch01/000/0/001` 為例）

| 檔案 | 內容 |
|---|---|
| `ch01_000_0001.mesh` / `.mdf2` | 髮片模型和材質 |
| `ch01_000_0001.chain2` | 擺動物理 |
| `_alba` | 髮片顏色 ＋ 透明度（A） |
| `_nrro` | 法線、粗糙度、AO |
| `_atos` | 透明、半透光、AO、SSS |
| `_hf_msk3` | 髮流方向（Hair Flow，控制高光沿著髮絲走） |
| `_hss_msk3` | 高度、高光遮罩、高光偏移（Height / Spec mask / Shift） |
| `_ho_alba` | 捏臉的「挑染／漸層」遮罩（對應材質裡的 HairOverColor A/B） |
| `_scalp_alba` / `_scalp_nrro` | **頭皮上畫的頭髮**（我們原型裡的「頭皮蓋」就是這個） |

另外 `streaming/` 底下有同名的高解析度版本。

### Wilds 頭髮材質（RE Mesh Editor 的 `MHWILDS/Hair.json` 預設）

- 主材質：`MaterialShader/Variation/Base_ATOS_VFX_Hair_NoPDO.mmtr`
- 貼圖欄位：`BaseAlphaMap`（ALBA）、`NormalRoughnessOcclusionMap`（NRRO）、`AlphaTranslucentOcclusionSSSMap`（ATOS）、`HairFlowMap`（HF_MSK3）、`Hair_Height_SpecMask_Shift_Map`（HSS_MSK3）、`HairOverMap`（HO_ALBA）
- 重要參數：
  - `AlphaTest_Ref` 0.1、`UseTempDither` 1 → **透明是「抖動＋TAA」的 alpha test**，不是真的半透明混合
  - `EdgeFade` 0.76、`EdgeWidth` 0.38 → **遊戲自己會淡化髮片邊緣**（原型裡用頂點屬性模擬）
  - `Primaly_Anisotropy`、`Specular_ShiftOffset`、`Secondary_ShiftOffset` → 兩層各向異性高光（頭髮特有的光澤帶）
  - `ColorParam`（顏色倍率）、`HairOverColorA/B`（捏臉髮色）
  - `UseVertexColor_mask` 1 → 頂點顏色有用途（可能是 AO 或擺動遮罩，待確認）

### ⚠ 頭髮材質沒有發光參數

`Base_ATOS_VFX_Hair` 裡**沒有** `Emissive_*`。設計上頭髮要有 15–20% 的微光，可能的做法（要實測）：

1. **提亮代替發光**：`ColorParam` 調高、`PrimalySpecularColor` 偏金 → 看起來像自帶光，但暗處會變暗
2. **VFX 混合**：材質有 `VFX_ColorParam1/2`、`Enable_VFXMaterialBlend`、`VFX_Texture2D` → 遊戲的屬性特效（例如發光狀態）可能就是用這組參數，用 MDF-XL 試試看能不能拿來做常駐微光
3. **改用 `Base_Equip`（Character Emissive 預設）**：有 `Emissive_*`，也支援 alpha test 和抖動，還有 `UseCounterExposureEmit`（發光不受曝光影響）；但會失去頭髮專用的各向異性高光
4. **混搭**：散髮用頭髮材質，編髮（實心、不需要透明）用 `Base_Equip` 加微弱發光 → 發光集中在編髮上，也比較像參考圖裡的光感

### 原型做法（`prototypes/scripts/character_concept.py`）

- **髮絲貼圖**：程式產生 512×1024 的 ALBA（RGB 顏色、A 覆蓋率），約 900 根細絲、18 個髮束，髮根密、髮尾往髮束中心收攏，左右可以無縫重複
- **三層**：頭皮蓋（不透明，髮絲間的空隙畫成暗金色）→ 背後底層（不透明，髮尾用貼圖透明度切出不規則邊）→ 約 140 張髮片（分三層、由內往外）
- 每張髮片：3 個頂點寬、沿路徑 44 段、中間微微拱起；U 取貼圖的隨機一段、V 從髮根到髮尾；邊緣和髮根用透明度淡出
- 髮片路徑：從中分線（或後腦）沿頭皮走到耳後／後腦離開頭部，再沿著背後的弧面往下，髮尾位置中間長、兩側短
- 編髮蓋在髮片上面：側編髮和主編髮都往外推一點，所以不會被散髮蓋掉
- 總共約 1.2 萬個面（遊戲的髮型通常是 1–3 萬個三角面，在合理範圍內）

→ 正式版的流程一樣：髮片模型 + ALBA + 頭皮 scalp_alba，再補 NRRO、ATOS、HF（髮流）貼圖。髮流貼圖可以直接從髮片的 V 方向算出來（每張髮片的髮絲方向都沿著 V）。

### 遊戲髮型 512／513（2026-10-03 解出全部 48 款比對）

- 髮型編號 `001～026`、`500～520`、`999`（999 只有頭皮）。全部解出：`extract_game_files.py ... "art/model/character/ch01/000/0/[0-9]+/[^/]*\.(mesh|mdf2|chain2)\."`（147 個檔）。背面總覽 `MiquellaTools\work\previews\hair\sheet_back.png`（卡普空模型，不進 repo）
- **512 最接近米凱拉**：中分、長波浪到腰（最低 y 1.12）、兩側扭轉的髮束往後在後腦合成一條三股編髮（`Mituami_hair01_CH_00～03`，4 根骨頭），在上背 y 1.45 用髮圈（材質 `acc`）綁住後就散開。材質 `scalp`、`acc`、`hair`。擺動鏈：`front_hair01/02`（4 節）、`back_hair01～05`（5 節）、`Mituami_hair01`，另有 `Hair_EX_01～31`
- 跟規格的差別：①**沒有許多小編髮**；②大編髮短又細（合成後約 15 cm 就綁住散開；規格是粗長的大編髮）；③側邊是扭轉不是編髮（遠看差不多）
- **513** 是貼頭皮的細編髮（玉米辮）＋五條垂下的編髮（`braid00～04_CH`，5 節，到肩膀 y 1.30）、髮尾髮圈 `acce`、另有 `FakeAO` 材質
- 補小編髮的做法（建議）：複製 512 自己的編髮模型縮細（同一張貼圖、同一個材質），夾在散髮裡；權重綁到附近的 `back_hair0x` 鏈跟散髮一起擺（規格本來就說相鄰幾條綁成一組），不用改 chain2

## 15. 不替換原版檔案的做法：用腳本把模型掛到獵人身上（從 MDF-XL 學到的）

MDF-XL 有兩個功能用的就是這個技巧，完全不需要覆蓋遊戲原本的檔案：

**1. 自帶的「基本身體」**（`MDFXL_MPlayerBase`）

```lua
-- 在場景裡生成一個新的物件，只帶 via.render.Mesh 元件
func.spawn_gameobj("MDFXL_MPlayerBase", Vector3f.new(0,0,0), Vector4f.new(0,0,0,1), 0, {"via.render.Mesh"})
-- 指定模型和材質（檔案放在 natives/STM/MDF-XL/MaleBase/ 底下，是 mod 自己的檔案）
local mesh = func.create_resource("via.render.MeshResource", "MDF-XL/MaleBase/MDFXL_MPlayerBase.mesh")
local mdf  = func.create_resource("via.render.MeshMaterialResource", "MDF-XL/MaleBase/MDFXL_MPlayerBase.mdf2")
renderMesh:setMesh(mesh)
renderMesh:set_Material(mdf)
-- 掛到獵人身上，並讓同名骨頭跟著獵人的骨架動
xf:setParent(masterPlayer:get_Object():get_Transform(), true)
xf:set_SameJointsConstraint(true)
```

→ **米凱拉的身體＋長袍、頭髮都可以這樣掛上去**：模型裡的骨頭名稱跟獵人骨架一樣，就會自動跟著動。好處：
- 不用決定要犧牲哪一件內衣或哪一款髮型
- 可以用選單開關，也不會跟其他替換同一個檔案的 mod 衝突
- 缺點：要同時把原本的防具／內衣／髮型隱藏（`set_DrawSelf(false)` 或關閉材質），而且擺動物理（chain2）要另外處理（MDF-XL 的武器換裝會一起換 `chain2`：`chain2:set_ChainAsset(...)`）
- **腳本生成的物件也能有擺動物理（2026-10-03 實測，`MiquellaLight_Scout/.../MiquellaLight_ChainProbe.lua`）**：複製獵人的 512 頭髮（同樣的 mesh、mdf2、`ch01_001_0512.chain2`），`SameJointsConstraint` 掛到獵人上，自己 `createComponent`：**只加 `via.motion.Chain2` → 完全不動（0 mm）**；**再加 `via.motion.ChildSecondary` → 跟真頭髮一樣甩**（髮尾 5 秒內最大 1171 mm，真頭髮 1184 mm）；再加 `via.motion.JointConstraints` 沒差別（1151 mm）。建立元件不會當掉。→ 長袍下擺、頭髮編髮都可以用腳本掛＋自己的 `.chain2`，元件要 `Chain2`＋`ChildSecondary`
- 遊戲自己的零件長這樣（同一次記錄）：會擺動的防具／髮型帶 `app.ChainSetting`、`via.motion.Chain2`、`via.motion.ChildSecondary`、`via.motion.JointConstraints`、`app.UnderWaterChain`；**有一件腿部防具（`ch03_042_0015`）的裙子是 `via.dynamics.GpuCloth`＋`app.ClothSetting`＋`app.SkirtBatchProcessing`（GPU 布料模擬）**，是另一條路，還沒研究。女獵人的眉毛也在 `ch01` 底下（`ch01_001_1003`，沒有 chain），找頭髮要挑有 chain2 的那個

**2. 武器換裝（Transmog）**

```lua
renderMesh:setMesh(meshResource)          -- 換模型
renderMesh:set_Material(mdfResource)      -- 換材質
chain2:set_ChainAsset(chain2Resource)     -- 換擺動（沒有的話用一個空的 chain2）
```

→ 光劍可以**只在拿特定一把武器時**換成我們的模型，不用覆蓋原版武器檔。收刀隱藏腳本也可以合併進同一個腳本。

→ **已寫成草稿**：`mods/miquella/mhws/MiquellaLight_Weapons/`（含收刀隱藏），並用模擬 API 的測試跑過完整流程（`mods/miquella/mhws/tests/`）。

**`create_resource` / `spawn_gameobj`**：MDF-XL 用的是 `_SharedCore/Functions.lua`（另一個 mod 的共用函式庫），這次沒有抓到原始碼。REFramework 的常見寫法是 `sdk.create_resource(型別, 路徑):add_ref()`，再 `:create_holder(型別 .. "Holder"):add_ref()` 取得可以傳給 `setMesh` 的 holder → 回家時直接看 `_SharedCore` 的實作最保險。

**偵察腳本**：`mods/miquella/mhws/MiquellaLight_Scout/`（只讀取、不改任何東西）會列出獵人目前的武器、防具、所有帶模型的子物件的 `.mesh` / `.mdf2` 路徑、材質名稱和骨頭名稱，還能存成 `reframework/data/MiquellaLight/scout.json`。回家第一件事跑它，就能確認上面所有推測。

## 16. 武器動作效果：遊戲裡怎麼做（設計見 `mods/miquella/DESIGN.md`「武器專屬動作效果」）

目標：武器零件跟著動作反應（大劍蓄力變色、雙劍鬼人化分裂成三刃、大錘／長槍蓄力多出光環、銃槍填彈彈簧伸縮），不是單純換膚。

**1. 材質參數可以在遊戲中即時改**（MDF-XL 就是這樣調顏色的）

```lua
renderMesh:setMaterialFloat(材質編號, 參數編號, 數值)
renderMesh:setMaterialFloat4(材質編號, 參數編號, Vector4f)   -- 顏色
renderMesh:setMaterialsEnable(材質編號, true / false)       -- 整個材質槽顯示／隱藏
```

Weapon Emissive 預設（`Base_ATOS_FX_SecEmit_VEmit_Detail_ColLayer_VFXwe.mmtr`）裡跟動作效果有關的參數（從 RE Mesh Editor 的 `MHWILDS/Weapon Emissive.json` 列出）：

| 參數 | 用途 |
|---|---|
| `Emissive_Color`、`Emissive_Intensity`、`Emissive_Power` | 發光顏色與強度 → 大劍金／亮金／白光、藍鬼人亮金 |
| `Dissolve` | 溶解（淡入淡出）→ 側刃、新光環出現時用 |
| `AnimEmit_Min`、`AnimEmit_Speed`、`AnimEmitWave`、`UseWaveEmit` | 發光自己一閃一閃（呼吸燈），不用腳本 |
| `Use_MoveEmit`、`MoveEmit`、`MoveEmit_Width` | 一條光帶沿著模型移動 → 長槍蓄力時光從槍根跑到槍尖、銃槍填彈時光往核心收 |
| `SecondaryEmitColor`、`SecEmit_Anim_*` | 第二層發光顏色與動畫 |
| `VFX_Param1`～`10`、`VFX_ColorParam1/2`、`Enable_VFXMaterialBlend` | 特效混合用，用途要實測 |

→ 參數**編號**要在遊戲裡從材質讀出來（偵察腳本加列參數名稱）。

**2. 會出現／消失的零件 = 獨立材質槽**
- 雙劍側刃、大錘每一段的環、長槍每一個新環，各自放在**自己的材質槽**
- 平常 `setMaterialsEnable(槽, false)`；到那一段就打開，`Dissolve` 從 1 降到 0 做淡入

**3. 會移動的零件**
- 首選：零件綁在**武器模型自己的骨頭**上，腳本改骨頭位置（銃槍彈簧每一圈一根骨頭，壓縮時往根部移，不會把彈簧壓扁；雙劍側刃繞刀根轉）
- 退路：做幾個不同姿勢的零件（逐格），依時間輪流打開材質槽

**4. 還不知道的：遊戲狀態從哪裡讀**
- 大劍蓄力段數、雙劍鬼人化／藍鬼人（鬼人量表）、大錘蓄力段數、長槍蓄力、銃槍填彈動作 → 都要找到對應的類別和欄位（例如獵人的武器處理器 `app.cHunterWp??Handling` 之類，名稱待確認）
- 做法：偵察腳本加一個「監看」模式，做動作時把武器處理器裡變動的欄位記下來

**5. 粒子特效（火、寒氣、腐敗蝶）**
- 《荒野》的特效檔是 `.efx`（例如 `natives/STM/Art/VFX/EffectEditor/...`），用 `ree-pak` 加檔名清單解出來
- **目前沒有公開的 EFX 編輯器**（只有開發團隊有）；社群做得到的是**改顏色**（十六進位修改或專用腳本，例如會心特效改色的 CritColorTool）
- 所以操蟲棍的癲火、寒氣這類效果：**找遊戲裡現成、形狀接近的特效（火屬性、冰屬性、怪物的火焰／寒氣），改成需要的顏色，再掛在繞刃的球上**；從零做一個新特效目前做不到
- 掛特效的方法（腳本生成、綁到骨頭）還要研究；預覽圖裡的火和寒氣是用「沿著漩渦氣流描出很多細光絲／體積霧」模擬特效的樣子，不是遊戲做法

**6. 其他模組怎麼處理特效（2026-10 查）**

| 模組 | 做什麼 | 對我們的用處 |
|---|---|---|
| **Armor VFX Manager**（Nexus 4908） | REFramework 腳本：把**遊戲裡任何特效**掛到獵人的任一骨頭（脊椎、手、武器骨頭、擺動骨…），可調位置、旋轉、大小、**RGBA 顏色**；可以設定**只在特定招式（Action ID）、拔刀時、翻滾時**出現；可延遲出現、提早淡出；內建記錄器，做動作時會顯示動作 ID；設定存成 `.json` 預設檔，可以打包分享 | **最關鍵**：操蟲棍的癲火球、寒氣、腐敗蝶，直接挑遊戲裡的火、冰、蟲類特效，改色後掛到球的骨頭上；米凱拉的光柱、頭冠微光也能這樣掛。它的動作 ID 記錄器可以跟我們偵察腳本的監看模式互補 |
| **VFX Unleashed**（Nexus 4842） | REFramework 腳本：針對**武器的狀態和招式**替換或疊加特效，**依蓄力段數調整大小**；可以**減弱原版蓄力時的強光**；支援大劍、大錘、弓、充能斧，內建 30 多種特效（雷、龍、冰、火…） | 大劍、大錘蓄力時，原版獵人身上的蓄力光會跟我們的金光打架 → 用它的做法減弱；每段蓄力換成我們要的特效 |
| CritColorTool（Nexus 2863） | 用 Python 工具改 `natives/STM/Art/VFX/EffectEditor/Common/hit/11_hit_critical_000.efx.5571972` 的顏色，匯出成 Fluffy 模組 | 證明 `.efx` 的顏色可以直接改檔；適合改「整個遊戲都一樣」的特效 |
| 特效合集（Elemental Weapon FX、Street Fighter FX、Shattering Mirror FX…） | 別人做好的特效組合 | 可以參考怎麼搭配 |

- **EFX 編輯器**：NSACloud 的 010 Editor 範本只支援《崛起》（可改顏色、把特效掛到骨頭），龍族教義 2 有另一個範本；《荒野》目前沒有公開的完整編輯器
- **結論：不用自己做特效檔**。走 Armor VFX Manager 那條路（腳本在執行時生成遊戲現成的特效、掛到骨頭、改顏色、依動作觸發）。我們可以把它當前置模組，或回家下載後讀它的 Lua 原始碼，把生成特效的寫法學進我們自己的腳本
- 回家要做：安裝 Armor VFX Manager，在選單裡翻遊戲的特效清單，挑出最像癲火、寒氣、腐敗蝶、光柱的幾個（記下名稱或路徑）；Nexus 在這個環境連不上，所以要你下載

**7. 預覽圖**：`mods/miquella/prototypes/action_states/`（`prototypes/scripts/states.py` 產生）。預覽裡的淡入用半透明材質代替 `Dissolve`，銃槍彈簧逐格重建代替骨頭。

## 17. 第一次遊戲實測和解出原版檔案後確認的事（2026-10-01，本機）

**載入**
- REFramework（nightly-01424，單一 `REFramework.zip`）在 Wilds 正常；紀錄檔 `re2_framework_log.txt` 在遊戲資料夾，會列出 `pak_mods` 讀到的 pak（`Cached custom pak with name: ...`）。一堆 `Scan.cpp ... Failed to find function start` 和 `for DD2` 的錯誤是正常的
- 遊戲開著時 `pak_mods` 裡的 pak 被鎖住，要關遊戲才能換
- 換裝腳本的寫法（`setMesh`／`set_Material`、收刀時 `set_DrawSelf`）在遊戲裡有效
- 遊戲裡的武器路徑長這樣（換裝腳本的設定檔記到的）：`Art/Model/Item/it02/00/0024/it0200_0024_0.mesh`

**從遊戲 pak 解原版檔案**：`prototypes/scripts/extract_game_files.py`（用 RE Asset Library 的讀檔程式，新 patch 優先；模型主檔在 `patch_014`，`.mdf2` 在 `patch_015`）。模型的高精度頂點在 `natives/stm/streaming/...` 同名檔，要一起解出來

**原版雙劍的模型規格**（`it0200_0024`、`it0200_0002`）
- 檔案座標 Y 上、單位公尺；**刀身朝 +Z、手握在原點**；寬度在 X、厚度在 Y
- 刀柄約 z = -0.04～+0.13，柄頭到 -0.10～-0.15，護手從 0.14～0.18 開始；全長 1.2～1.6 m
- 骨架只有 `root` → `Base` → `VFX_Attack`（刀尖位置），全部頂點 100% 綁 `Base`
- 原版有 group 0、1、3 三組子模型（用途待查，可能是不同狀態顯示的部分）；我們只用 group 0

**材質（`.mdf2.45`）**
- 原版雙劍用 `MaterialShader/Variation/Base_ATOS_FX_SecEmit_VEmit_Detail_ColLayer_VFXwe.mmtr`，23 張貼圖、**180 個參數**，原版的發光：`Emissive_Intensity` 0.5、`Emissive_Power` 0.5、`UseCounterExposureEmit` 1（亮處也看得到）
- RE Mesh Editor 0.66 的 Wilds 預設（Weapon／Weapon Emissive）只有 176 個參數，少了 `AnimEmit_Blend`、`Use_Basecolor_Mask`、`Basecolor_Mask_Min`、`Basecolor_Mask_Max`。**遊戲照位置讀參數**，排列不對時發光等數值全錯 → 第一版光劍變黑
- 做法：每個材質都從遊戲現在的原版 `.mdf2` 複製一份，再照**參數名稱**填回我們的值（`fit_dual_blades.py` 的 `rebuild_mdf`）。遊戲更新後如果又變黑，先比對參數數量

**Windows 無介面 Blender 的坑**：RE Mesh Editor 的匯入／匯出運算子會切換系統主控台，無介面時直接 segfault；改成直接呼叫 `importREMeshFile`／`exportREMeshFile`

**武器狀態欄位（Watch 實測）**
- 雙劍：`hunterCharacter:call("get_WeaponHandling")` → `app.cHunterWp02Handling`（37 個數值／布林欄位）
  - `_IsKijinOn`、`_IsKijinOnEffect`：鬼人化開關
  - `_KijinExtern`：開鬼人化時約 0.13 秒內 0 → 1（每幀 +0.11），解除時 1 → 0 → **直接拿來驅動淡入**
  - `_IsHitAttackToEnemy`：打中魔物時 true
  - 真鬼人化（量表）：那次沒錄到；可能在下一層物件裡（偵察腳本已改成看下一層）

**特效檔（`.efx.5571972`）可以讀到屬性層級了**（2026-10-01）
- 格式照 kagenocookie 的 REE-EFX-Unified 010 範本（`EfxVersion_MHWilds = 12`）：表頭 12 個 uint → 名稱區（`entryLength`）→ 外部參數值（每個 24 bytes：兩個雜湊、型別、12 bytes 值；型別 1 = RGBA 顏色）→ 骨頭 → 動作 → 欄位參數 → 特效項目（每個有多個屬性）
- **Wilds 每個屬性開頭是 `itemType, itemSize`**，所以不認識的屬性可以直接跳過 → `prototypes/scripts/efx_walk.py`
- 已知的顏色欄位（相對 `itemSize` 之後）：`TypeRibbonParticle`(38) color1 +8、color2 +12、+92/+96/+100；`TypeNoDraw`(78) color +8、colorRange +12；`RgbCommon`(242) greenChColor +8、redChColor +28（貼圖綠／紅通道的染色）
- **玩家全身發光** = 特效項目 `PLE*`：`TypeNoDraw`（顏色）＋`PtBehavior` 裡的 `app.EffectPlEmissiveControl`（只有邊緣光寬度、強度、部位，沒有顏色）
- 型別 ID ↔ 名稱：範本的 `getStructNameMHWilds`（282 種）

## 18. 角色：遊戲的獵人身體（2026-10-02 深夜，本機解出來看）

- **荒野的「內衣」是一整套衣服**（襯衫、皮帶、腰包、褲子、靴子），**皮膚只露出手、前臂、脖子、臉**（材質 `skin`，在手 `ch02_002_0001` 的群組 10／20、身體 `0002` 的群組 10）。**沒有可以拿來改的裸身模型** → 米凱拉的身體要自己做：長袍外露的手、脖子，加上長袍掀起時看得到的腿和腳；權重從遊戲的內衣用「最近表面」轉移（Blender Data Transfer），骨頭名稱照遊戲的
- 內衣四件：`0001` 手臂（袖子＋手）、`0002` 上身（群組 0～14，穿防具時遊戲藏掉被蓋住的群組）、`0004` 腿（褲子＋靴子，5.3 萬點）、`0005` 腰（皮帶、小刀、腰包，有 `cage` 材質）。臉 `ch00_000_0000`（男）／`ch00_001_0000`（女）、髮型 `ch01/000/0/<編號>`
- **綁定姿勢是 A 字**（手臂往下約 42°），身高到頭頂 1.751（不含頭髮）。骨頭（世界座標）：`Hip` y 1.020、`Spine_2` 1.261、`Neck_0` 1.461、`Head` (0, 1.573, -0.010)；`L_UpperArm` (0.189, 1.405, -0.036)、`L_Forearm` (0.383, 1.231)、`L_Hand` (0.560, 1.070, 0.055)；`L_Thigh` (0.100, 0.910)、`L_Knee` (0.157, 0.504)、`L_Foot` (0.216, 0.088)、`L_Toe` (0.211, 0.028, 0.135)。骨架 709 根（大量 `*_HJ_*` 輔助骨頭、`*_CT` 衣服擺動骨頭）
- 頭部（眉上 y 1.69）：光頭寬 ±0.074、前後 -0.096～+0.101；髮型 001 寬 ±0.09、後 -0.117
- 預覽（含卡普空模型，不進 repo）：`MiquellaTools\work\previews\body\hunter_base_body.png`、`.blend`；腳本在 session 暫存區，要重做照這節的路徑匯入即可（`importREMeshFile`，見第 6 節的坑）
