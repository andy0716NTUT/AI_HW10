# AI Agent LLM Wiki 與教學簡報

五份發行方文件 → 六個 Wiki 條目 → 十頁教學簡報；23 個內容區塊逐一帶有 Wiki 欄位與來源 ID。原稿原樣保留於 `original/`，改善版在專案根目錄。

## 快速展示

直接雙擊 `index.html`、`slides.html`、`workflow.html`；不需 CDN 或後端。簡報支援前後按鈕、左右鍵、Home/End、F 全螢幕及 `#slide-7` 直達頁面。手機可捲動，引用可點回 Wiki 與原始資料。

Wiki：https://andy0716ntut.github.io/AI_HW10/

簡報：https://andy0716ntut.github.io/AI_HW10/slides.html

Graph：https://andy0716ntut.github.io/AI_HW10/workflow.html

公開站另已實測 78/78 項瀏覽器檢查（不含本機 file:// 兩項）；證據：evidence/public/report.json。

## 重建與驗證

基本流程僅使用 Python 3.10+ 標準函式庫（本次使用 Python 3.14.0）：

```console
python workflow.py
python workflow.py --fault citation-once
python -m unittest discover -s tests -v
```

真實瀏覽器 gate 使用已安裝的 Google Chrome 與可選的 Playwright：

```console
python -m pip install --target .tools -r requirements-browser.txt
python workflow.py --fault citation-once --browser
python tests/test_browser.py
```

套件只裝進 `.tools/`，不需 LLM API 或金鑰。若沒有 Chrome，先從官方安裝 Chrome，或自行調整 `browser_check.py` 的 browser channel。本次 headless Chrome 在受限執行環境停滯，允許的執行環境中成功；不把啟動失敗當作 pass。

## 實作架構

`load_sources → ingest → build_wiki → retrieve → draft_slides → validate_claims → export(暫存) → validate_html → publish(本機)`。

`slide_plan.json` 只規劃查詢和 Wiki 欄位；`workflow.py` 依關鍵字實際檢索 `wiki.json`，`build.py` 只渲染檢索結果。來源不足回 ingest；缺引用回 retrieve/draft；HTML 失敗回 export；預設每處最多重試兩次，第三次失敗拒絕發布並保留原檔。例：`python workflow.py --fault citation-always --out evidence/rejected-demo` 預期 exit 1，這是正確的拒絕路徑。其他可恢復模式：`source-once`、`html-once`。

每次執行保留 `evidence/runs/<run_id>.json`；`execution_log.json` 為最新流程，`RUN_LOG.md` 記跨階段進度。`validation.json` 會區分靜態 gate 與真正執行的瀏覽器 gate。`--out` 指定另一個輸出目錄可避免覆寫展示成果。

## 來源與限制

來源：OpenAI、Anthropic、LangChain/LangGraph、Microsoft Learn、Google Cloud。詳見 `INGEST_LOG.md` 與 `sources/S01–S05.md`；每篇有摘要、三個可回溯要點、章節、取得時間、方法、HTTP 狀態與內容雜湊。`python audit_sources.py` 會重新連線檢查並更新 acquisition.json；不會自動改寫已核對摘要。`prepare_sources.py` 是從 original/ 重建本次編輯遷移的輔助程式，會覆寫整理檔，日常重建請用 workflow.py。

大型 PNG 的連接工具傳輸曾停滯，瀏覽器上傳也受擴充功能檔案權限限制；repo 另以 `.png.b64` 保留原始圖片的可逆文字封裝與 SHA-256。執行 `python materialize_images.py` 可核對並還原全部 PNG；package_site.py 在發布前自動還原，公開站使用真正 PNG，沒有改圖或重製證據。

本作有真實 Python 自動流程，但執行器是 deterministic 檢索／規則組合，沒有呼叫 LLM API、沒有執行 LangGraph 套件，也沒有第三方 LLM Wiki 平台上傳紀錄。HTTP 與 schema 檢查不證明語義正確，來源正文由本次 Codex 閱讀核對，並非宣稱另有人類複核。

## 已實測與部署

- 單元／整合測試：14/14；真實 Chrome 157.0.8103.79 UI 檢查：80/80。
- 實跑：`2026-11-23T231153879896+0800`，12 個節點事件，引用錯誤被攔截一次並恢復；原始數據見 execution_log.json。
- 詳細操作、限制、截圖與反思見 `VALIDATION_REPORT.md`、`workflow.html`。
- Pages 設定、部署狀態及打包：見 `DEPLOYMENT.md`；`python package_site.py` 輸出 `dist/` 與 `site-deploy.zip`。
- 交作業用 `SUBMISSION.md`；完整檔案清單與 SHA-256 見 `FILE_MANIFEST.json`。
