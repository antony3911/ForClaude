# 米凱拉光劍換裝腳本（不覆蓋原版檔案）

在遊戲執行中，把你指定的武器的**外觀**換成米凱拉光劍，收刀時隱藏。只換外觀，武器的數值和動作完全不變。做法跟 MDF-XL 的武器換裝一樣：`setMesh` / `set_Material` / `set_ChainAsset`。

## 跟覆蓋檔案的差別

| | 覆蓋原版檔案 | 這個腳本 |
|---|---|---|
| 原版那把武器 | 被取代，再也看不到 | 不受影響，隨時換回來 |
| 選哪一把 | 做 mod 時就要決定 | 遊戲裡用選單選，可以選好幾把 |
| 跟其他 mod 衝突 | 改同一個檔案就會衝突 | 不會 |
| 需要 | patch pak | patch pak（我們的模型放在自己的路徑）＋ 這個腳本 |

## 用法

1. 安裝我們的模型 pak（素材包打包後的 patch pak，路徑是 `Art/Model/MiquellaLight/...`）和這個腳本
2. **不要**同時裝 `MiquellaLight_HideSheathed`（這個腳本已經包含收刀隱藏）
3. 拿著想換的武器，打開 REFramework 選單 → Script Generated UI → **MiquellaLight: Light Weapons**
4. 「Weapon: <原版模型路徑>」（主武器）和「SubWeapon」（副武器，雙劍的另一把）下面的 `Look` 下拉選單選外觀：`DualBlades`、`GreatSword`、`LightBowgun`。**要先進遊戲、手上有武器**，`Look` 才會出現（標題畫面只會顯示 `(none)` 和提示）
5. 設定存在 `reframework/data/MiquellaLight/Weapons.json`，以後拿這把武器就會自動換

## 選單

- `Glow`：全部光劍的發光強度倍率（使用者設 5）
- `Size (dual blades)`：只管雙劍，預先做好的大小模型
- `Floating rings`、`Ring motion`：**浮動環**（2026-10-02）。大劍刀背的三個環、輕弩光束上的五個環各有自己的骨頭（`MQ_Ring0～2`、`MQ_Halo0～4`），腳本每幀用彈簧＋阻尼推動：武器加速時環被甩開、晚一拍回彈（大劍最多 3.5 cm、傾斜 28°），平時慢慢漂；輕弩是「磁浮」：幅度 4 mm 的漂移＋0.4 mm 的細微顫動。`Ring motion` 0～3 調強弱，0 = 不動。參數在腳本的 `FLOAT_MODES`
- `Rings found: n/N (set at ...)`：找到幾個環的骨頭、在遊戲的哪個時機設的（`LateUpdateBehavior`／`PrepareRendering`／`BeginRendering`）

## 狀態

- 雙劍、大劍、輕弩的換模型都在遊戲裡驗證過（位置、收刀隱藏）；鬼人化三刃驗證過
- 加新武器：在 `KITS` 加一項（模型路徑、`glow`、要的話加 `floaters`）
- **浮動環還沒實測**：遊戲換模型時會不會替新骨頭建立關節要進遊戲才知道。`Rings found: 0/N` 就是沒建立 → 環會停在原位或跑掉，回報後改用其他做法
- 如果載入失敗，選單會顯示紅字「Could not load ...」，原版武器保持原樣

## 蓄力零件與骨頭的新機制（2026-10-02 晚，第一帳號）

使用者挑選的「蓄力力量感」設計（DESIGN.md「蓄力的力量感・提案」）用到的設定，都寫在 `KITS` 各武器裡：

| 設定 | 用在 | 作用 |
|---|---|---|
| `charge.parts = { 材質 = 段數 }` | 大劍火花、長槍旋轉弧和槍尖光刃、大錘、銃槍 | 零件材質在那一段淡入（`Dissolve`，消失時關掉材質） |
| `charge.partColor` | 大劍（`PART_GOLD`） | 零件固定這個顏色（刀身三段變白時光絲還是亮金） |
| `grow`（見下一節） | 大劍、長槍、太刀的光絲，弓的花 | 跟著遊戲的蓄力計時器連續長出來 |
| `floaters.spin = { axis, dps = { 0段, 1段, 2段, 3段 }, grow }`＋關節 `spin = true` 或 `{ 軸 }` | 長槍 `MQ_Drill`、大錘 `MQ_Arm0～2` | 骨頭固定在原位、依蓄力段數（`entry.chargeSmooth` 內插；`grow = true` 時用長出來的程度 `entry.growLevel`，連續加速）每秒轉幾度；關節可以給自己的軸 |
| 關節 `stretch = 根部高度` | 銃槍 `MQ_FilamentTop` | 骨頭的 z = 根部 + (原位 − 根部) × `entry.stretch`（最短 15 %），`entry.stretch` 由 `update_gunlance` 跟蓄力時間連續拉長（蓄力砲擊 1.2 秒拉滿、龍擊砲 0.9 秒） |
| `floaters.orbit.face = true`, `spin` | 操蟲棍精華 | 繞刀的零件一直朝外（建模時就朝外放），繞自己的朝向慢轉；不設就是原本的翻滾 |
| `boosts[].chase = { 材質… }`, `chaseHz` | 充能斧斧強化 | 幾組材質輪流只亮一組（跑馬燈），不在那個型態時全部藏起來 |
| 關節 `slide = true`＋`timing` 表 | 片手劍 `MQ_TimingRing` | 骨頭沿武器往上抬 `entry.slide`；`update_timing` 在完美突進動作（`cJustRush*`）時讓光環從刀尖降到護手，`_IsJustRush` 時爆開 |

骨頭和零件在 `build_weapon_kit.py` 做：`floaters`（物件名 → 骨頭）＋`pivots`（骨頭位置）；一個材質分多種顏色用 `uv_band_of`／`uv_band_count`（操蟲棍精華，頂點屬性 `mq_band`）；只屬於一個型態的零件用 `sets`（充能斧 `SawA／B／C`）。預設隱藏的材質前綴在 `HIDDEN_AT_START`。

## 跟著蓄力連續長出來（`grow`，2026-10-03，第一帳號）

使用者：螺旋一段一段出現很抽象，「螺旋就應該是慢慢長大的才會帥」；弓每段同時開兩朵花沒有連續性。做法：

- **模型**：會長的零件依「什麼時候出現」切成很多段，每段一個材質 `MiquellaGrow1～n`（`arsenal.py` 的「growing with the charge」：`band_spans`、`reach_at`；光絲每段到的位置照舊：一段 40 %、二段 75 %、三段到頂；弓每朵花三段：花心、一半花瓣、另一半）。大劍、長槍、太刀各 24 段，弓 21 段（7 朵 × 3）
- **骨頭把正在長的那段拉出來**（2026-10-03 使用者：段數太少還是看得出一格一格，要像動畫慢慢伸長）：大劍、太刀的光絲是壓扁的橢圓螺旋，**每條光絲各自一串骨頭、每段兩根**（`MQ_G<光絲>_1～48`，就在光絲上）；長槍是正圓螺旋，**軸上每段兩根**（主絲 `MQ_Grow1～48`、細絲 `MQ_GrowF17～48`，都是 `MQ_Drill` 的子骨頭，跟著轉）。每段的頂點依高度綁在它兩端的骨頭之間。腳本 `step_grow_joints`：還沒長到的骨頭（只算正在長的那段）全部移到**生長前緣**（長槍再沿螺旋把角度轉回去），那一段就從一個點被連續拉出來；長過的骨頭放回原位（設一次）。骨頭表 `chains` 由 `build_weapon_kit.py` 寫成 `<kit>/<模型>_grow.lua`，貼進腳本的 `GROW_GS`／`GROW_LS`／`GROW_LN`（重建模型後要重貼）。有骨頭時每段一開始就顯示（`GROW_SNAP` 6：前 1/6 淡入），沒骨頭（弓）時整段淡入。選單 `Growth bones found: n/N`
- **腳本** `update_grow`：讀遊戲的蓄力段數＋**蓄力計時器**，算出「段數＋往下一段走了多少」（計時器 ÷ 段數門檻；下一段到之前最多走到 98 %，不會比遊戲早），換成長出來的比例，前緣那段用 `Dissolve` 淡入。放開蓄力，長出來的部分在原地 0.3 秒淡出（`hold` 的動作進行中先不淡出：太刀的大迴旋斬）
- **段數門檻**（計時器到哪個值升段）：優先用**玩的時候實際量到的**（段數一變就記下當時的計時器值，存在 `Weapons.json` 的 `chargeTimes`，像 `it00/0`＝大劍、蓄力種類 0；跟表差太多的不記），其次遊戲自己的參數（弓的 `_ActionParam._ChargeTimeLv2～4`），最後是 `times`（從遊戲參數檔 `wpXXglobalactionparam.user.3` 解出來的）。每次學到新值會記進欄位記錄檔的 `events`（`charge it00: level 1 at _ChargeTimer 0.800`）
- 選單 `Growth:` 顯示段數欄位、計時器、下一段的門檻（`learned`＝量到的）和長出來的百分比

| 武器 | 段數欄位 | 計時器 | 門檻（秒） | 其他 |
|---|---|---|---|---|
| 大劍 | `_ChargeLevel`（`CHARGE_FIELDS`） | `_ChargeTimer` | 0.8／1.55／2.3（一般蓄力；其他蓄力種類不同，依 `_ChargeType` 各自學） | 三段時的火花照舊 `MiquellaCharge3` |
| 長槍 | `_FinishChargeLevel` | `_FinishChargeTimer` | 0.8／2.0／3.6 | 細光絲從一段開始長；光鑽轉速跟著長的程度（`spin.grow`） |
| 太刀 | `_KijinChargeLv`（氣刃蓄力） | `_KijinChargeTimer` | 0.8／1.6／2.9 | 只在 `cKijinCharge*` 動作裡開始長（`action`），大迴旋斬 `cKijinSlashRound` 揮完才淡出（`hold`）；亮金、越長越亮（`mul`） |
| 弓 | `<ChargeLv>`（平時 1） | `_ChargeTimer`（沒有就 `_OnceChargeTimer`） | 遊戲的 `_ActionParam._ChargeTimeLv2～4`（1／2／3） | `flowers = 7`：每段的時間開兩朵（一朵一朵），到最高段剩下的接連開完（`post` 0.6 秒），弓尖大花最後；最高段讀 `<MaxChargeLv>` |

預覽：`prototypes/scripts/preview_grow.py <kit .blend> <great_sword|lance|long_sword|bow> <輸出>`（照遊戲的時間做 GIF 和一排格子），輸出在 `MiquellaTools\work\previews\grow\`。
