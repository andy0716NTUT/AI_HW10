# Codex 連續任務：完成 LLM Wiki 教學 HTML 簡報

## 背景
作業要求：至少 ingest 5 篇資料、以「先討論後生成」規劃 Wiki、用 Wiki 製作可實際瀏覽的教學型 HTML 簡報，解釋 loop / graph 的資訊取得、整理、檢查、重試及生成，以及一次實際執行、檢查紀錄和反思。9–10 分強調資料來源對應與真實驗證。

## 執行原則
從本資料夾進行。不要只寫計畫：修改程式、生成檔案、執行測試、留下證據。每階段結束即更新 `RUN_LOG.md`，失敗先修復再進下一階段。避免引入需付費的服務；可優先使用 Python 標準函式庫。若無 LLM API，實作可重現的「檢索＋規則化內容組合＋檢查重試」流程，清楚區分非 LLM 自動生成與 LLM 生成。

### Phase 1 — 稽核現有成果
- 讀完 `wiki.json`、`build.py`、3 個 HTML、`validation.json`、`SUBMISSION.md`。
- 確認 5 個資料來源真的可取得，核查來源的標題、發行方、核心觀點；若無網路，註記 URL 未即時檢查，不要假裝已 ingest 原文。
- 補 `sources/`：每篇至少整理來源 metadata、主題摘要、3–5 個可回溯重點、取得時間與取用方法；能取得原文時可另外保存適量摘要或轉錄，但避免大量搬運受版權保護內容。
- 建立 `INGEST_LOG.md`，記錄每篇的 ingestion 狀態；明確標示摘要取自哪些文件，與僅列出 URL 的差別。
- 撰寫「先討論後生成」的真正討論記錄／設計決策：可寫目前的規劃推演，但不得假稱發生過不存在的對話。

驗收：至少 5 篇各自有整理檔與處理紀錄，Wiki 條目均有有效來源引用，無錯誤聲稱。

### Phase 2 — 可執行的 loop / graph
- 建立 `workflow.py`，明確節點：load_sources → ingest → build_wiki → retrieve → draft_slides → validate_claims → validate_html → export。
- 加入條件分支：資料不完整→回 ingest；缺引用→回 retrieve/draft；HTML 渲染或導覽失敗→回 export；設定最大重試次數避免無限循環。
- 使用 `wiki.json` 作為實際檢索來源，讓簡報內容是**查詢 Wiki 後生成**，而不是把無關的簡報文字直接硬編。
- 可將 `build.py` 重構為可 import 的產生器，維持原本頁面效果。
- 將每次節點耗時（可取得時）、輸入輸出、檢查、重試理由及結果記錄到 machine-readable `execution_log.json` 和 `RUN_LOG.md`。
- 如果無 API 且只能 deterministic pipeline，須在頁面與繳交稿誠實揭露。

驗收：`python workflow.py` 可從本地 Wiki 重新產生 HTML、JSON 報告，並且能測試缺引用的故障路徑確實觸發重試或拒絕發布。

### Phase 3 — 教學品質與 UI
- 保持 10 頁左右，教學順序：問題情境→定義→與一般 LLM/Workflow 差異→組件→Tool Calling→Agent Loop→Graph/狀態→安全與失敗→案例→回顧。
- 新手可理解，每頁主概念一個、有具體例子、不要文字牆。
- 來源引用可點選，Wiki 條目與投影片雙向索引。
- 簡報支援左右鍵、前後按鈕、進度、手機版；全部不依賴 CDN 也可開啟。
- `workflow.html` 明確區分架構設計與「實際運行紀錄」。

驗收：Chrome/Chromium 或 Playwright 可開啟 `index.html`、`slides.html`、`workflow.html`；導覽無 console errors；手機與桌面可讀；來源網址合理。

### Phase 4 — 真實測試、反思
- 寫 `tests/` 測試基本 schema、來源完整性、Wiki→簡報引用一致、投影片數量、導航與失敗重試。
- 執行實際 pipeline 一次，紀錄**真實輸出**；至少刻意製造一個可恢復錯誤來測試前移檢查。
- 更新 `VALIDATION_REPORT.md`：操作、預期、實際、通過／未通過、任何未驗證項目。
- `workflow.html`、`SUBMISSION.md` 的反思需以執行數據為據；「哪個節點最常出錯」若僅測一次，標明只是本次觀察，不能誇稱統計顯著。

驗收：可重現測試，執行紀錄可核查，失敗案例與流程調整一致。

### Phase 5 — 發布與繳交
- 加 `README.md`：快速開啟 HTML、重建命令、架構、來源、測試、部署方式。
- 加 GitHub Pages 部署檔（例如 `.nojekyll`、適當 index）與相對路徑；如果可使用已授權的 GitHub repo，部署至 Pages 並實際檢查公開 URL；若沒有 repo/權限，不要自行選另一個現有 repo 覆寫，把 URL 欄標記為待填。
- 編輯 `SUBMISSION.md`，遵守「學校 學號 系級 姓名 主題」標題格式。已知：北科大、資工四；**學號未知，保留 placeholder**；姓名由使用者核對後填寫。
- 繳交內容：主題、簡介、Wiki URL/成果、簡報 URL、loop/graph、實跑驗證、反思，附完整來源和檔案清單。
- 確認無硬編的公開 URL、測試紀錄或個資。

驗收：可直接展示 Wiki 與簡報，所有資料相互對應；剩餘人工事項清單不超過必要的「學號」、「帳戶授權／部署」、「課堂指定 Wiki 平台（如有）」。

## 最終交付回覆格式
1. 已完成的修改摘要
2. 真正執行的命令及 pass/fail
3. 生成的檔案與示範位置
4. 部署連結（若確實部署）
5. 仍需使用者自行操作的事項（不要冒稱完成）
