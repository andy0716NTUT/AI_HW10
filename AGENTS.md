# Codex 專案指引

## 專案目標
完成 2026-11-23 23:59 截止之「用 LLM Wiki 做一份教學 HTML 簡報」作業。優先確保可驗證的實作，不得編造 ingest、瀏覽器檢查、平台上傳或部署紀錄。

## 現有檔案
- `wiki.json`：5 個來源、6 個 Wiki 條目，資料來源與條目關聯
- `build.py`：生成網站的 Python 程式
- `index.html`：本機 Wiki 頁面
- `slides.html`：10 頁教學簡報
- `workflow.html`：Graph、反思與檢查說明
- `validation.json`：只代表現有**靜態檢查**，不代表瀏覽器或 Agent 執行測試
- `SUBMISSION.md`：待完善的繳交稿

## 不可違反的要求
1. 原樣保留已有內容並在其上改進；不要將示範流程冒稱為真實自動執行。
2. 每個簡報知識主張至少要能回溯至 `wiki.json` 條目及其來源 ID；資料與簡報內容保持一致。
3. 必須保留**至少 5 篇確實整理的資料**；檢查來源網址、標題與主張合理性，無法取得時清楚標記。
4. 如能實作真實 ingest→retrieve→draft→validate→retry→export 的 Python workflow，應使用可重現的本機流程，留下完整 execution log。
5. 不可硬編 fake pass 或虛構檢查結果；只記錄實際執行與觀察到的輸出。
6. 不得將任何 API 金鑰、token 或憑證寫入 Git 或產物。
7. 使用繁體中文，專業但新手可理解，HTML 需要響應式、鍵盤導覽、可閱讀來源引用。
8. 交付前修正 `SUBMISSION.md` 的未填欄位，但若不知道學號，不要猜。
9. 若無法進行公開部署，保留完整可部署檔案並明確標記「尚未部署」。
10. 盡可能自動推進、自行執行驗證與修正；僅在第三方帳戶操作或必要個資缺失時停下。

## 完成標準
遵照 `CODEX_TASK.md` 的階段與驗收；更新 `RUN_LOG.md`、`VALIDATION_REPORT.md`、`SUBMISSION.md`，提供最後的 Git commit 或檔案清單。
