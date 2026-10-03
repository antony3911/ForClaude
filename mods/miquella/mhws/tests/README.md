# 腳本的離線測試

沒有遊戲也能跑：用假的 REFramework API（`sdk`、`re`、`imgui`、`json`）模擬獵人和武器，實際執行腳本的流程。能抓到邏輯錯誤，但**不能**證明遊戲的方法名稱正確，那個要進遊戲才知道。

本機（Windows）沒有 lua5.4：用 `pip install lupa`（內含 Lua 5.4），把下面的 `lua5.4` 換成 `python run_lua.py`。

```
lua5.4 weapons_test.lua ../MiquellaLight_Weapons/reframework/autorun/MiquellaLight_Weapons.lua
lua5.4 weapons_test.lua ../MiquellaLight_Weapons/reframework/autorun/MiquellaLight_Weapons.lua missing
lua5.4 scout_test.lua ../MiquellaLight_Scout/reframework/autorun/MiquellaLight_Scout.lua
lua5.4 character_test.lua ../MiquellaLight_Character/reframework/autorun/MiquellaLight_Character.lua [female|nojoint|nocreate|missing]
lua5.4 face_test.lua ../MiquellaLight_Face/reframework/autorun/MiquellaLight_Face.lua
```

換裝腳本測了：選武器 → 換模型／材質／擺動物理 → 收刀隱藏、拔刀出現 → 遊戲自己換回原版時再換一次 → 同一個物件換成別把武器時不動它 → 取消後還原模型、材質、擺動物理 → 模型檔不存在時顯示錯誤、不隱藏原版武器。

寫測試時抓到並修好的 bug：
1. 遊戲自己換回原版模型後再換一次，會把「原本的擺動物理」記成空的，之後還原不了
2. 模型沒載入成功時，收刀還是會把原版武器藏起來
3. 遊戲在同一個物件上換成別把武器時，腳本會誤以為還是舊的那把
