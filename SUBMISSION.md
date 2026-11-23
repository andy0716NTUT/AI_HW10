# 北科大 112590011 資工四 林維信 AI Agent LLM Wiki 與教學簡報

## 主題與簡介

以「如何把五篇文件整理成可信的學習簡報」為情境，介紹 AI Agent 的定義、LLM／Workflow 差異、元件、Tool Calling、Agent Loop、Graph／狀態、安全與設計模式。先寫真實設計推演，再整理五份發行方資料成六個本機 Wiki 條目，依查詢檢索 Wiki 生成十頁響應式 HTML 簡報。

## 成果與網址

Wiki：https://andy0716ntut.github.io/AI_HW10/

簡報：https://andy0716ntut.github.io/AI_HW10/slides.html

Graph：https://andy0716ntut.github.io/AI_HW10/workflow.html

公開站另已實測 78/78 項瀏覽器檢查（不含本機 file:// 兩項）；證據：evidence/public/report.json。

本機展示：`index.html`（Wiki）、`slides.html`（10 頁簡報）、`workflow.html`（Graph、實跑與反思）。原始資料：`wiki.json`、`sources/`；逐頁查詢：`retrieval_log.json`；23 個內容區塊的欄位與來源引用：`slides_data.json`。

## Loop／Graph 實作

Python 實際執行 load_sources → ingest → build_wiki → retrieve → draft_slides → validate_claims → export（暫存）→ validate_html → publish（本機）。來源不足回 ingest；缺引用回 retrieve/draft；HTML 失敗回 export。每處最多重試兩次，持續失敗拒絕發布；通過後才輸出正式 HTML。

## 實跑與檢查

本次 `python workflow.py --fault citation-once --browser` 的 run ID 為 `2026-11-23T231153879896+0800`，共 12 個節點事件。刻意刪掉一筆來源引用，在 validate_claims 攔截一次，重新檢索與起草後通過。14 個流程測試通過；Chrome 157.0.8103.79 在桌面、手機與窄螢幕完成 80/80 項 UI 檢查，console error／page error／failed request 均為 0。永久缺引用測試到第三次失敗後拒絕匯出，既有成果保留。

證據：`execution_log.json`、`evidence/tests/`、`evidence/browser-pipeline/report.json`、`VALIDATION_REPORT.md`。所有結果來自實際執行；靜態 schema、瀏覽器驗證與公開部署分別記錄。

## 反思

本次觀察的引用錯誤是刻意注入，不能聲稱它是最常出錯的節點。實際稽核也找到原稿 S01 對 W03 的反向索引遺漏，已修正並加檢查。把來源映射與 Wiki 欄位比對前移到渲染之前，可避免完成 HTML 才發現引用遺失；暫存與最大重試上限則避免壞草稿覆蓋成果。下一步需要人工標註更多查詢、檢查檢索召回率及語義支持性，而非只依賴 ID 有效就認定內容正確。

## 誠實揭露

本作是 Codex 輔助編輯的本機結構化 Wiki；執行器為 deterministic 檢索與規則組合，未呼叫 LLM API，也未使用 LangGraph 套件或上傳第三方 LLM Wiki 平台。來源已取得並整理，不只列出 URL。若老師指定某個 Wiki 平台，仍需將本作上傳該平台；不宣稱此項已完成。

## 完整來源

- S01 · OpenAI：[ A Practical Guide to Building AI Agents ](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)；整理檔 `sources/S01.md`。
- S02 · Anthropic：[ Building Effective Agents ](https://www.anthropic.com/research/building-effective-agents)；整理檔 `sources/S02.md`。
- S03 · LangChain / LangGraph：[ Workflows and Agents ](https://docs.langchain.com/oss/python/langgraph/workflows-agents)；整理檔 `sources/S03.md`。
- S04 · Microsoft Learn：[ AI Agent Orchestration Patterns ](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns/)；整理檔 `sources/S04.md`。
- S05 · Google Cloud：[ Choose Your Agentic AI Architecture Components ](https://docs.cloud.google.com/architecture/choose-agentic-ai-architecture-components)；整理檔 `sources/S05.md`。

## 檔案清單

展示頁、Python 流程與產生器、十頁查詢計畫、五篇來源整理、逐主張引用資料、真實測試與截圖、Graph、README、INGEST_LOG、RUN_LOG、VALIDATION_REPORT、DEPLOYMENT、Pages 設定與原稿備份皆已保留。逐檔 SHA-256 清單見 `FILE_MANIFEST.json`。
