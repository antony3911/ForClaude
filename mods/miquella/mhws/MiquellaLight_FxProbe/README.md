# 特效偵測腳本（只讀取，不改任何東西）

改了特效檔的紅色，遊戲裡有些地方還是紅的（鬼人化中的真鬼人軌跡、手上的紅光氣、真鬼人一般型態身體金紅閃爍）。特效的顏色可以由遊戲在**執行時**用外部參數指定（`11_it02_002.efx` 的火焰顏色＝`lerp(lerp(ColorC, ColorA, IsKijin), ColorB, IsBuff)`，軌跡顏色＝`Color`），檔案裡的預設值會被蓋掉。這個腳本找出遊戲實際播了哪些特效、設了哪些參數。

## 用法

1. `reframework/autorun/MiquellaLight_FxProbe.lua` 放進遊戲的 `reframework/autorun/`（遊戲開著的話：Insert → ScriptRunner → **Reset scripts** 重新載入）
2. 拿雙劍，Insert → Script Generated UI → **MiquellaLight FX Probe** → **Start recording**
3. 照順序做（每步之間站著等 2～3 秒）：開鬼人化 → 攻擊到真鬼人量表集滿 → 解除鬼人化（一般型態、身體閃爍）→ 攻擊幾下 → 再開鬼人化攻擊幾下 → 完美閃避（藍鬼人）
4. **Stop and save** → `reframework/data/MiquellaLight/fx.json`（Claude 在本機可以直接讀）

## 記錄內容

- `methods`：`via.effect.EffectPlayer` 的方法和參數型別（之後改顏色要呼叫哪個）
- `hooked`：掛上記錄的參數設定方法（名字含 `xtern`、不是 get 開頭的）
- `effects`：錄影期間場上播過的所有特效檔，第一次／最後看到的秒數
- `params`：遊戲每一種參數呼叫（方法、特效檔、參數值、次數），顏色以 `#RRGGBBAA` 顯示
- `values`：雙劍特效（路徑含 `it02`）的參數讀回值（有對應的 get 方法才有）
- `timeline`：武器、玩家特效開始／結束、武器處理器的 true/false 欄位變化、第一次出現的參數呼叫

## 注意

- 還沒在遊戲裡測過（離線測試 `tests/fxprobe_test.lua` 通過）。每個讀取都包在 `pcall` 裡
- 掛鉤只記錄，不改參數；錄影結束後掛鉤還在但什麼都不做
