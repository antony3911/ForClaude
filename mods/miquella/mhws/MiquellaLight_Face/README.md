# MiquellaLight_Face — 用臉自己的骨頭微調神態（2026-10-04，還沒進遊戲測）

REFramework 腳本 `reframework/autorun/MiquellaLight_Face.lua`。**不換臉、不改任何遊戲檔**：每一幀在遊戲設好臉的姿勢（捏臉、表情、說話、眨眼）之後，把幾根臉部骨頭再加一點位移／旋轉，所以臉還是獵人自己的、所有動作照常。方向照 DESIGN.md「臉」（使用者 2026-10-04）：下垂眼、上眼皮半垂、居高臨下又在玩弄人的眼神（單邊嘴角上揚、下眼皮微推）。

| 滑桿（選單 MiquellaLight: Face） | 動哪些骨頭 | 預設 |
|---|---|---|
| Droopy eyes (mm) | 外眼角 `L/R_OuterEyeJ_LOD02` 往下、往後；上眼皮外半 `UpEyeLid_B_LOD00` 跟著往下 | 2.2 |
| Upper lids lowered (deg) | 上眼皮 `L/R_UpEyeLidJ_LOD02`（在眼球中心）繞頭的左右軸轉 | 11 |
| Lower lids raised (deg) | 下眼皮 `L/R_LoEyeLidJ_LOD02` 反方向轉（笑眼） | 5 |
| Smile corner (mm)／Smile side | 一邊嘴角 `cornerLip_LOD02` 往上、往外、往後，另一邊只動 27 % | 2.6、左 |
| Brow lift (mm) | 微笑那邊的外眉 `EyeBrow_C／B_LOD01` 往上、兩邊內眉 `EyeBrow_A` 稍降 | 0 |

- 位移寫在 `Head` 骨頭的空間（x 獵人左、y 上、z 臉的前方），右邊鏡像；換成每根骨頭父骨頭的區域座標再加上去
- **疊加不累積**：記住上一次設的值，骨頭還是那個值＝遊戲這幀沒動它，用記住的底；不一樣＝遊戲設了新姿勢，拿它當底。在 `LateUpdateBehavior`、`PrepareRendering`、`BeginRendering` 各設一次（換裝腳本設武器骨頭的做法）
- 關掉選項、Reset scripts 時還原成遊戲的姿勢；設定存 `reframework/data/MiquellaLight/Face.json`
- **診斷**：每 2 秒寫 `reframework/data/MiquellaLight/face_debug.json`：找到幾根骨頭、過去一秒遊戲重設了幾次（`takenFromGame`，>0＝那些骨頭有動畫在驅動）／我們的值留著幾次（`keptOurs`），每根骨頭的底和設的值。**滑桿拉了臉卻沒變**：可能遊戲在更晚的階段又設了一次（看 `phases` 有沒有三個都在跑），或捏臉的骨頭在別的物件上
- 已知風險：眨眼時上眼皮會被多轉 11°，可能閉過頭、蓋到下眼皮（要的話之後依眼皮的開合比例縮小）；捏臉放大了頭（`HeadAll_SCL`）時位移也會跟著縮放
- 預覽：`prototypes/scripts/face_tune_preview.py <輸出>`（遊戲的女臉預設形狀，四欄：原樣／A 下垂＋半垂眼皮／B＋單邊微笑＋下眼皮微推／C＋單眉微挑；含卡普空模型，不進 repo）
- 測試：`tests/face_test.lua`（`python run_lua.py face_test.lua <腳本>`），12 項
