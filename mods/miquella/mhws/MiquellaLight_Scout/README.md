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

建議掃這幾次：雙劍、太刀、片手劍、重弩、輕弩各一次；再穿內衣、不戴頭盔掃一次（看內衣和髮型）。

## 注意

- 還沒在遊戲裡測過。寫法照 MDF-XL 和 REFramework 官方範例，每個讀取都包在 `pcall` 裡，讀不到的欄位會顯示 `nil`，不會讓遊戲當掉
- 只讀取資料，不會修改任何物件
