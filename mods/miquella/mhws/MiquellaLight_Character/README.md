# MiquellaLight_Character — 米凱拉人物（頭冠、身體、長袍）

REFramework 腳本 `reframework/autorun/MiquellaLight_Character.lua`，**不覆蓋任何遊戲檔**：自己生成一個 GameObject（`via.GameObject.create`＋`createComponent(via.render.Mesh)`，EMV Engine／MDF-XL 的做法），放我們的頭冠模型（`MiquellaLight_Character.pak`），掛到獵人的 `Head` 骨頭上。之後身體、長袍、頭髮也照這個方法掛（研究筆記第 15 節）。

**跟著頭的兩種方法**（選單 `Attach`）：
- `Head joint`：物件的 Transform `set_Parent(獵人)`＋`set_ParentJoint("Head")`，由引擎帶著走
- `Follow every frame`：腳本每幀在算圖前（`PrepareRendering`／`BeginRendering`）把位置、旋轉設成 `Head` 骨頭的
- `Auto`（預設）：先用前者，掛上 1 秒後離 `Head` 超過 30 cm 就改用後者

**身體**（2026-10-02 深夜）：物件 `MiquellaLight_Body`，`set_Parent(獵人)`＋`set_SameJointsConstraint(true)`（MDF-XL 的 MPlayerBase 做法），模型的骨頭名稱跟獵人一樣就會跟著動。選單 `Body shape` 切 A／B／C（同一個物件換模型）。**男女獵人用不同的模型**（2026-10-03）：找到獵人的臉（`character/ch00/`）後看路徑，`ch00_001`（女）用 `mq_body_*_f.mesh`，其他用 `mq_body_*.mesh`；找到臉之前先用男的，狀態列寫 `for a female／male hunter`。勾著「Hide the hunter's armor and innerwear」時，每 0.5 秒找獵人底下（子物件 6 層內）模型路徑含 `character/ch02/`、`character/ch03/` 的物件（防具、內衣）每幀 `set_DrawSelf(false)`；臉 `ch00`、頭髮 `ch01`、武器不動；關掉選項、關掉身體或 Reset scripts 時還原。狀態列顯示藏了幾個物件。

**長袍**（2026-10-04）：物件 `MiquellaLight_Robe`，跟身體一樣掛骨架（SameJointsConstraint），再加 `via.motion.Chain2`（chain2 用遊戲自己的 `Art/Model/Character/ch03/025/001/5/ch03_025_0015.chain2`，每次換模型都重設）和 `via.motion.ChildSecondary`（沒有它腳本生成的鏈不會動，研究筆記第 15 節）。選單 `Outfit`：None／Robe, plain／Robe, body lines／Robe, drape, loose sash／Robe, drape, cinched（`OUTFITS`；垂墜兩款只關 `MiquellaSkinChest`：版型 `fit` 對應 `mq_robe_<fit>_c[_f].mesh`，男女看臉選；都是照 C 款身體做的）。穿著時把身體的 `covers` 材質關掉（`MiquellaSkinChest`、`MiquellaSkinWaist`、`MiquellaClothWaist`：身體被長袍蓋住的部分，`apply_cover`），脫掉就開回來；膚色同時套在 `MiquellaSkin`、`-Chest`、`-Waist` 三個材質上。**診斷**：每 2 秒寫 `reframework/data/MiquellaLight/robe_debug.json`：模型、Chain2／ChildSecondary 有沒有建起來、chain2 有沒有設上、**下擺擺動幅度**（背後下擺末端 `L_B_Skirt_CH_end` 相對獵人 `Hip` 五秒內移動的 mm，~0＝物理沒在跑；選單也顯示）、第一次另外寫 `via.motion.Chain2`、`ChildSecondary`、`app.ChainSetting` 的成員和獵人身上第一個帶 ChainSetting／Chain2 的部位的欄位值（研究腿的碰撞用）。

**選單**（MiquellaLight: Character）：開關、Glow（亮度倍數，使用者要保留可調）、Size（**0.8～0.9，預設 0.85**：模型原本的大小在使用者的獵人上偏大，這個區間使用者都覺得好、還沒決定，2026-10-03；以頭的中心 `SIZE_PIVOT` 縮放，縮小時貼著頭收、不會往下掉）、位置微調（左右／上下／前後，cm，沿頭的方向）、Attach、Reset position；狀態列顯示現在用哪種方法、離 `Head` 幾公分。設定存在 `reframework/data/MiquellaLight/Character.json`。

**頭冠的兩個坑（2026-10-03 修好、遊戲裡確認）**：①**REFramework 的 `Quaternion.new` 參數是 (w, x, y, z)**（glm），寫成 `new(0, 0, 0, 1)` 是繞 Z 轉半圈 → 頭冠上下顛倒掛在 `Head` 上、正面在頭下方 13 cm＝脖子根一圈黑色帶子；現在用 `identity_quat()`（跟換裝腳本一樣先檢查順序）。②頭冠的 `MiquellaHalo` 抄自雙劍象牙，象牙的 **`Emissive_Power` 是 0＝發光整個關掉**（遊戲裡像純金屬）→ 腳本在發光材質上設 `EMIT_ON`（`Emissive_Power` 1、`UseCounterExposureEmit` 1、`CounterExposureEmit_Blend` 0.8，抄雙劍發光材質），`build_weapon_kit.py` 的 `HALO_EMIT_ON` 也改了，下次重建 `.mdf2` 就會帶著。**診斷**：腳本每秒把頭冠和 `Head`／`Neck_0` 骨頭的世界位置、旋轉、頭冠正面在頭骨頭座標的位置寫進 `reframework/data/MiquellaLight/circlet_debug.json`（`frontInHead` 應該約 (0, +0.128×Size, +0.113×Size)），Claude 不用截圖就能確認位置。

**其他**：遊戲換區域把物件刪掉會自動重做；Reset scripts 時先藏起來，新的一輪接手同一個物件（`findGameObject`）；獵人被隱藏時一起藏。

**測試**：`mhws/tests/character_test.lua`（`python run_lua.py character_test.lua <腳本> [female|nojoint|nocreate|missing]`；`female` 是女臉的獵人）。

**狀態**：頭冠 2026-10-03 在遊戲裡確認：戴在額頭、會發金光。身體見 HANDOFF 第 9 節「人物」。以下是當初的測試清單：身體要測：有沒有出現、原本的衣服有沒有藏掉（狀態列的 outfit objects hidden 數字）、走路／翻滾／攻擊時肩膀、手肘、膝蓋、手指變形正不正常、脖子接縫、三種體型。要測：頭冠有沒有出現、在不在額頭、跟不跟頭動（翻滾、攻擊）、狀態列寫哪種方法；戴頭盔時會穿模（先在外觀設定把頭盔關掉）。
