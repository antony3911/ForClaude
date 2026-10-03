# 偵察腳本（只讀取，不改任何東西）

回家第一件事跑這個，就能確認研究筆記裡推測的遊戲路徑和骨頭名稱。

## 用法

1. 需要 REFramework。把 `reframework/autorun/MiquellaLight_Scout.lua` 放進遊戲資料夾的 `reframework/autorun/`（或用 Fluffy Mod Manager 安裝這個資料夾）
2. 進遊戲、操作到獵人出現，按 Insert 開 REFramework 選單 → Script Generated UI → **MiquellaLight Scout**
3. 按「Scan hunter」→ 看得到：
   - 武器（主武器、副武器、備用武器）：`.mesh`、`.mdf2` 路徑，材質名稱，掛在哪個物件上，武器自己的骨頭
   - 防具六個部件：路徑和材質
   - 獵人底下所有帶模型的子物件（臉、頭髮……）
   - 勾選「Show hunter skeleton joints」看獵人骨架的全部骨頭名稱
4. 按「Save report」→ 存到 `reframework/data/MiquellaLight/scout.json`，把這個檔案給我

5. **武器動作效果用（找蓄力段數、鬼人化、填彈的數值）**：拿著那把武器，按「Watch weapon state」→ 做動作（例如大劍蓄力到二段、雙劍開鬼人化再開藍鬼人、銃槍填彈）→ 選單會列出**有變動的欄位**和它的範圍 → 按「Save watch」存到 `reframework/data/MiquellaLight/watch.json` 給我
   - 每把武器各錄一次，做動作前先站著不動幾秒（站著也會變的欄位比較好排除）
   - 掃描時武器的每個材質也會列出**參數名稱**（之後改發光、溶解要用的編號）

建議掃這幾次：雙劍、太刀、片手劍、重弩、輕弩各一次；再穿內衣、不戴頭盔掃一次（看內衣和髮型）。

## 注意

- 還沒在遊戲裡測過。寫法照 MDF-XL 和 REFramework 官方範例，每個讀取都包在 `pcall` 裡，讀不到的欄位會顯示 `nil`，不會讓遊戲當掉
- 只讀取資料，不會修改任何物件

## 其他測試腳本（用完要從遊戲移除）

- `MiquellaLight_MeshDiff.lua`：比對臉和我們物件的 Mesh 設定（2026-10-03，找出 StencilValue）
- `MiquellaLight_ChainProbe.lua`：腳本生成的物件能不能有擺動物理（2026-10-03）。複製獵人的頭髮三份、各加不同的元件，記錄髮尾晃動到 `reframework/data/MiquellaLight/chain_probe.json`。**結論：`Chain2`＋`ChildSecondary` 就會跟真頭髮一樣甩**（研究筆記第 15 節）。**會改場景**（生成物件、可以藏掉真頭髮），不是唯讀的
