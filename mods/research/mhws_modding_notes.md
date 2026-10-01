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

**5. 預覽圖**：`mods/miquella/prototypes/action_states/`（`prototypes/scripts/states.py` 產生）。預覽裡的淡入用半透明材質代替 `Dissolve`，銃槍彈簧逐格重建代替骨頭。
