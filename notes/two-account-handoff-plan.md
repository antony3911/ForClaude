# 雙帳號手動換手計畫（待回家討論，尚未實作）

記錄日期：2026-09-30

## 背景

- 常撞到**週上限**，考慮升級 Max 5x（約 NT$3,200）或改買兩個 Pro。
- Max 5x 官方只保證「每 5 小時用量是 Pro 的 5 倍」，週上限數字沒公布。
- 最接近官方的數字是 2025/7 公布的每週估計（Sonnet 在 Claude Code 的時數）：

  | 方案 | 月費 | 每週估計 | 約是 Pro 的幾倍 |
  |---|---|---|---|
  | Pro | US$20 | 40–80 小時 | 1x |
  | Max 5x | US$100 | 140–280 小時 | 約 3.5x |
  | Max 20x | US$200 | 240–480 小時 | 約 6x |

- 結論：如果瓶頸是週上限，而且願意手動切換，兩個 Pro（US$40）比 Max 5x 划算。
  Max 的優點是 Fable 含在額度內、尖峰優先、不用切換帳號。

## 設計：手動切換帳號，用進度檔換手

1. 在專案的 `CLAUDE.md` 加規則，讓 Claude 隨時更新 `PROGRESS.md`（草稿在下面）。
2. 帳號 A 撞到上限時：
   - 確認 `PROGRESS.md` 是最新的，並 commit（雲端 session 要 push 到 GitHub 分支）
   - `/logout`，再 `/login` 登入帳號 B
   - 開**新 session**，跟 Claude 說「讀 PROGRESS.md 接著做」
3. 不要換帳號後用 `--resume` 接很長的對話：快取是各帳號分開的，換帳號後整段對話要重讀，會吃掉一大塊額度。
4. 兩個帳號都要連 GitHub，雲端 session 的進度才能互相接手。

### CLAUDE.md 規則草稿

```markdown
## 進度紀錄
- 每完成一個步驟，就更新專案根目錄的 PROGRESS.md。
- 開新 session 時，先讀 PROGRESS.md 再開始工作。
- PROGRESS.md 只寫接手需要的資訊，保持精簡。
```

### PROGRESS.md 格式草稿

```markdown
# 進度
## 目標
## 已完成
## 下一步（第一項就是接手後要做的事）
## 重要決定與相關檔案
## 卡住的地方 / 待確認
```

## 不做的部分

- **自動偵測額度用完就換帳號的工具**：Consumer Terms 禁止用 bot、script 等自動化方式存取服務（API key 或官方明確允許的方式除外），而這種工具的目的是繞過用量限制，可能導致兩個帳號都被停權。

## 同時可以先做的省額度調整

- effort 從 xhigh 降到 high
- 一個階段做完就開新 session，或早點 `/compact`
- 查資料、寫文件改用 Sonnet

## 回家要決定 / 要做的事

- [ ] 用 `/usage` 看一週的用量，再決定買兩個 Pro 還是 Max 5x（在 claude.ai 網頁訂閱，不要在 App Store 買）
- [ ] 要不要套用上面的 CLAUDE.md 規則，套在哪些專案
- [ ] 開 Remote Control 自動連線：`/config` → Enable Remote Control for all sessions
- [ ] 帳號設定打開 Require trusted devices（因為有開 bypass permission）
- [ ] 裝遠端桌面軟體，實際測試能不能從手機點 UAC（管理員權限）視窗
- [ ] 照下面的清單安裝遊戲 mod 工具

---

# 遊戲 mod 工具安裝清單（2026-09-30 查證）

安裝要在家裡的電腦上做。有些安裝檔會跳 UAC，要人在電腦前按。
全部只從下面列的官方來源下載（me3 官方 FAQ 有提到防毒軟體可能誤報）。

## 共用

- **Blender 要裝兩個版本**（兩個外掛的版本需求衝突）：
  - **Blender 5.1 以上** → 法環用。Soulstruct for Blender 要求 5.1 以上
  - **Blender 5.0** → 魔物獵人用。RE Mesh Editor 說 5.1 有 bug，匯入匯出會非常慢
  - 做法：一個用安裝版，另一個用 zip 免安裝版，放在不同資料夾
  - 下載：https://www.blender.org/download/
- Blender MCP（選用，讓 Claude 直接操作 Blender）：https://github.com/ahujasid/blender-mcp
- Paint.NET（選用，修貼圖）

## 艾爾登法環

| 工具 | 用途 | 來源 |
|---|---|---|
| me3 | 載入 mod（取代 Mod Engine 2） | https://github.com/garyttierney/me3/releases → `me3_installer.exe` |
| UXM Selective Unpack | 解包遊戲檔案。**只用解包，不要按 Patch** | https://github.com/Nordgaren/UXM-Selective-Unpack |
| WitchyBND | 拆開、打包遊戲封裝檔，也能把特效檔轉成文字檔 | https://github.com/ividyon/WitchyBND |
| Smithbox | 改參數（數值、戰技設定） | https://github.com/vawser/Smithbox |
| DSAnimStudio | 動作時間軸編輯與預覽（做戰技用） | https://github.com/Meowmaritus/DSAnimStudio |
| Soulstruct for Blender | Blender 讀寫法環模型，裝在 Blender 5.1 以上 | https://github.com/Grimrukh/soulstruct-blender |

me3 設定重點：mod 設定檔要寫 `savefile`（mod 專用存檔），不要開 `start_online`（預設就會擋掉官方連線）。

## 魔物獵人（Rise / Wilds 適用；World 的工具不同）

| 工具 | 用途 | 來源 |
|---|---|---|
| REFramework | mod 的基礎框架。Wilds 要打開 loose file loader | https://github.com/praydog/REFramework |
| Fluffy Mod Manager | 管理、開關 mod | Nexus Mods（要註冊帳號） |
| RE Mesh Editor | Blender 讀寫 RE 引擎模型、轉換貼圖，裝在 Blender 5.0 | https://github.com/NSACloud/RE-Mesh-Editor |
| 解包工具 | 取出遊戲原本的檔案 | 待查 |

注意：RE Mesh Editor 的作者已經宣布停止維護，之後遊戲更新可能會讓它失效。

## 米凱拉搬到魔物獵人（構想）

- 做法：**替換獵人的防具外觀**，動作沿用獵人原本的，不用做動畫
- 流程：Soulstruct 匯入米凱拉模型 → Blender 調整身形、套到獵人骨架、轉移權重 → 貼圖轉成 RE 引擎格式 → RE Mesh Editor 匯出 → Fluffy 載入
- 難點：
  - 體型差很多（米凱拉是孩童身形，獵人是成人）
  - 頭髮、衣服的物理擺動不會跟著搬過來，要另外設定，否則會是硬的
  - 材質格式要轉換
- **只能自己玩，不要公開發佈**：Nexus Mods 等平台禁止上傳從其他遊戲搬過來的素材
