# 執行時改特效顏色、藏 buff 閃光

改過顏色的特效檔不夠：遊戲有些特效的顏色是**執行時**才給的（特效偵測腳本 `MiquellaLight_FxProbe` 錄到的）。這個腳本在遊戲裡即時處理：

1. **雙劍特效紅 → 金、藍 → 銀**：攻擊軌跡 `11_it02_001`（參數 `Color`）、真鬼人身體光和前臂火焰 `11_it02_002`（`ColorA`／`ColorB`／`ColorC`）
   - 新特效產生時：掛鉤 `via.effect.EffectPlayer.addExternParameter`（每個新特效都會呼叫）記下這個特效，**下一幀**就看它的名稱，含 `it02` 就立刻換色，紅色最多出現一幀。（第一版想在這裡直接改參數，但傳進來的參數是遊戲的固定原生物件，改不到：實測「0 at spawn」，軌跡先紅 0.25 秒再變金）
   - 播完的軌跡不再追蹤（每次攻擊都是新的特效物件；第一版沒清，追蹤數累積到 75）
   - 正在播的雙劍特效：每幀檢查參數和特效的染色（`EffectPlayer.get_Color`），紅藍就換掉
2. **藏起攻擊上升／防禦上升的閃光**：`pl_state/11_pl_heal`，遊戲把它染成紅 `#FF3333`（攻擊）或橘 `#FF8040`（防禦），約每 2 秒重播一次。把這兩種染色改成透明黑；同一個特效用別的顏色時（喝藥回復）不動

選單：Script Generated UI → **MiquellaLight Effects**，兩個勾選框可以分別關掉，存在 `reframework/data/MiquellaLight/Effects.json`。選單也顯示換了幾次色、藏了幾次，用來確認有沒有作用。

換色的算法跟 `recolor_efx.py` 一樣（金色色相 38°、保留飽和度亮度透明度；銀色幾乎無彩度、亮度 ×0.9）。

還沒在遊戲裡測過（離線測試 `tests/effects_test.lua` 通過）。不確定的地方：特效的染色是否也作用在玩家身體發光（PLE）上；`ValueType.new(via.Color)` 的 `rgba` 欄位寫法。
