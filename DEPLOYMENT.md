# GitHub Pages 部署紀錄

Repository：[andy0716NTUT/AI_HW10](https://github.com/andy0716NTUT/AI_HW10)，由使用者本次提供。已查 GitHub metadata：public、push/admin 可用；首次讀 contents 回覆「repository is empty」，沒有覆寫其他專案。

狀態：**已部署且公開網址已驗證**。

Wiki：https://andy0716ntut.github.io/AI_HW10/

簡報：https://andy0716ntut.github.io/AI_HW10/slides.html

Graph：https://andy0716ntut.github.io/AI_HW10/workflow.html

公開站另已實測 78/78 項瀏覽器檢查（不含本機 file:// 兩項）；證據：evidence/public/report.json。

機器紀錄：`deployment.json`。只有成功收到公開站 HTTP 與瀏覽器驗證後才標記 verified；推送 commit 或 Actions 成功本身不等於本機已實際開過公開網址。

## 可重現部署方式

1. 將本專案檔案推送到指定 repo 的 `main`，不包含 `.tools/`、金鑰或憑證。
2. 在 GitHub Settings → Pages 選 GitHub Actions；`.github/workflows/pages.yml` 會重建、跑流程測試、打包 `dist/`，並部署 Pages。此雲端流程只跑靜態 gate；本機 Chrome 證據另保存。
3. 或使用 `python package_site.py` 產生靜態套件，將 dist/ 內容推至專用分支並從該分支發布。套件不包含 Python runtime 或安裝依賴。
4. 開啟實際回傳的 Pages URL，確認 Wiki、slides.html、workflow.html 與相對引用可讀；將觀察寫入 deployment.json，再執行 `python finalize_docs.py` 更新繳交稿。

工作流結構參照 [GitHub 官方 Pages custom workflow 文件](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)，包含 build/deploy 依賴、Pages artifact、pages:write / id-token:write 與 github-pages environment。不在檔案存取 API token。
