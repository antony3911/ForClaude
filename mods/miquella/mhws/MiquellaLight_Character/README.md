# MiquellaLight_Character — 米凱拉人物（頭冠、身體）

REFramework 腳本 `reframework/autorun/MiquellaLight_Character.lua`，**不覆蓋任何遊戲檔**：自己生成一個 GameObject（`via.GameObject.create`＋`createComponent(via.render.Mesh)`，EMV Engine／MDF-XL 的做法），放我們的頭冠模型（`MiquellaLight_Character.pak`），掛到獵人的 `Head` 骨頭上。之後身體、長袍、頭髮也照這個方法掛（研究筆記第 15 節）。

**跟著頭的兩種方法**（選單 `Attach`）：
- `Head joint`：物件的 Transform `set_Parent(獵人)`＋`set_ParentJoint("Head")`，由引擎帶著走
- `Follow every frame`：腳本每幀在算圖前（`PrepareRendering`／`BeginRendering`）把位置、旋轉設成 `Head` 骨頭的
- `Auto`（預設）：先用前者，掛上 1 秒後離 `Head` 超過 30 cm 就改用後者

**身體**（2026-10-02 深夜）：物件 `MiquellaLight_Body`，`set_Parent(獵人)`＋`set_SameJointsConstraint(true)`（MDF-XL 的 MPlayerBase 做法），模型的骨頭名稱跟獵人一樣就會跟著動。選單 `Body shape` 切 A／B／C（同一個物件換模型）。**男女獵人用不同的模型**（2026-10-03）：找到獵人的臉（`character/ch00/`）後看路徑，`ch00_001`（女）用 `mq_body_*_f.mesh`，其他用 `mq_body_*.mesh`；找到臉之前先用男的，狀態列寫 `for a female／male hunter`。勾著「Hide the hunter's armor and innerwear」時，每 0.5 秒找獵人底下（子物件 6 層內）模型路徑含 `character/ch02/`、`character/ch03/` 的物件（防具、內衣）每幀 `set_DrawSelf(false)`；臉 `ch00`、頭髮 `ch01`、武器不動；關掉選項、關掉身體或 Reset scripts 時還原。狀態列顯示藏了幾個物件。

**選單**（MiquellaLight: Character）：開關、Glow（亮度倍數）、Size、位置微調（左右／上下／前後，cm，沿頭的方向）、Attach、Reset position；狀態列顯示現在用哪種方法、離 `Head` 幾公分。設定存在 `reframework/data/MiquellaLight/Character.json`。

**其他**：遊戲換區域把物件刪掉會自動重做；Reset scripts 時先藏起來，新的一輪接手同一個物件（`findGameObject`）；獵人被隱藏時一起藏。

**測試**：`mhws/tests/character_test.lua`（`python run_lua.py character_test.lua <腳本> [female|nojoint|nocreate|missing]`；`female` 是女臉的獵人）。

**狀態**：頭冠、身體 2026-10-02 做完，都還沒在遊戲裡測。身體要測：有沒有出現、原本的衣服有沒有藏掉（狀態列的 outfit objects hidden 數字）、走路／翻滾／攻擊時肩膀、手肘、膝蓋、手指變形正不正常、脖子接縫、三種體型。要測：頭冠有沒有出現、在不在額頭、跟不跟頭動（翻滾、攻擊）、狀態列寫哪種方法；戴頭盔時會穿模（先在外觀設定把頭盔關掉）。
