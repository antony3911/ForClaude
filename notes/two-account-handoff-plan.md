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
