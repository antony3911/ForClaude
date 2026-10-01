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
