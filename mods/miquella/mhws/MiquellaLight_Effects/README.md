# 執行時改特效顏色、藏 buff 閃光

改過顏色的特效檔不夠：遊戲有些特效的顏色是**執行時**才給的（特效偵測腳本 `MiquellaLight_FxProbe` 錄到的）。這個腳本在遊戲裡即時處理：

1. **雙劍特效紅 → 金、藍 → 銀**：攻擊軌跡 `11_it02_001`（參數 `Color`）、真鬼人身體光和前臂火焰 `11_it02_002`（`ColorA`／`ColorB`／`ColorC`）
   - 新特效產生時：掛鉤 `via.effect.EffectPlayer.addExternParameter`（每個新特效都會呼叫）記下這個特效，**下一幀**就看它的名稱，含 `it02` 就立刻換色，紅色最多出現一幀。（第一版想在這裡直接改參數，但傳進來的參數是遊戲的固定原生物件，改不到：實測「0 at spawn」，軌跡先紅 0.25 秒再變金）
   - 播完的軌跡不再追蹤（每次攻擊都是新的特效物件；第一版沒清，追蹤數累積到 75）
   - 正在播的雙劍特效：每幀檢查參數和特效的染色（`EffectPlayer.get_Color`），紅藍就換掉
2. **藏起攻擊上升／防禦上升的閃光**：`pl_state/11_pl_heal`，遊戲把它染成紅 `#FF3333`（攻擊）或橘 `#FF8040`（防禦），約每 2 秒重播一次。把這兩種染色改成透明黑；同一個特效用別的顏色時（喝藥回復）不動

選單：Script Generated UI → **MiquellaLight Effects**，兩個勾選框可以分別關掉，存在 `reframework/data/MiquellaLight/Effects.json`。選單也顯示換了幾次色、藏了幾次，用來確認有沒有作用。

換色的算法跟 `recolor_efx.py` 一樣（金色色相 38°、保留飽和度亮度透明度；銀色幾乎無彩度、亮度 ×0.9）。

## 版本紀錄（實測）

- 第一版：軌跡大多變金但先紅一下（0 at spawn，全靠 0.25 秒掃描）；buff 閃光消失（使用者確認）
- 第二版（下一幀換色）：軌跡還是先紅；buff 閃光反而**每次重播閃一下**。原因：①軌跡是一段段發射的，每段發射時就定色，晚一幀換色時第一段已經是紅的；②遊戲每次重播 buff 都重設染色，第二版看到非 buff 色就不追蹤，要等掃描才抓回來
- 第三版：**攔截遊戲設顏色的那一刻**：掛鉤 `EffectPlayer.getExternParameter(String)`／`getExternParameters(UInt64)` 記下雙劍特效的顏色參數物件，再掛鉤 `via.effect.script.EffectCustomExternParameter.set_Color(via.Color)`，遊戲設紅色時直接把參數換成金色。buff 特效從找到起就一直盯著。每幀的工作改在 `re.on_pre_application_entry("BeginRendering")`（遊戲更新完、算圖前），沒有這個入口就退回每幀一次。選單第二行顯示掛鉤數和時機

離線測試 `tests/effects_test.lua` 通過。不確定的地方：特效的染色是否也作用在玩家身體發光（PLE）上；`ValueType.new(via.Color)` 的 `rgba` 欄位寫法。
