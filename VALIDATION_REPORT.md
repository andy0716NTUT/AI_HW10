# 真實驗證報告

產生：2026-11-23T23:24:33.994260+08:00（Asia/Taipei）。本報告由既有 execution log、Chrome report 與 unittest 終端輸出彙整；不是硬編 pass。

## 實際執行命令

| 命令 | 觀察到的結果 |
|---|---|
| `python audit_sources.py` | 首次 DNS 失敗；允許的網路重試取得 5×HTTP 200；終端 cp950 失敗另修為 UTF-8 |
| `python workflow.py --fault citation-once` | PASS；首次實跑 12 事件，引用檢查失敗→檢索→重新起草→通過 |
| `python -m unittest discover -s tests -v` | PASS；14 tests / 0.799 秒（最近一次保留輸出） |
| `python browser_check.py --evidence evidence/browser-authorized` | PASS；80/80；首輪受限啟動停滯取消，允許的環境完成 |
| `python workflow.py --fault citation-once --browser` | PASS；run 2026-11-23T231153879896+0800；12 事件；80/80 UI checks |

## 操作、預期與實際

| 操作 | 預期 | 實際 | 結果 |
|---|---|---|---|
| 五篇原始文件 GET | 取得正文且標題合理 | 5×200；標題／章節核對，S04 授權提示但正文可讀 | PASS |
| 本地來源 ingest | 至少五份，各含 metadata、摘要及 3 點 | 五份整理、15 要點、時間與方法 | PASS |
| Wiki 與投影片引用 | 6 條目有效，10 頁全部回溯 | 23 區塊逐字比對 Wiki 欄位，來源集合一致 | PASS |
| 本次缺引用注入 | 匯出前攔截，回 retrieve | 1 次失敗；validate_claims→retrieve→draft→重新驗證 | PASS |
| 永久缺引用 | 最多 2 次重試後拒絕，原成果不變 | 3 次失敗，rejected，既有 release 未覆寫 | PASS |
| 暫時來源缺漏 | 回 ingest 重讀本地檔 | ingest 1 次失敗後恢復 | PASS |
| HTML 缺導航 ID | 回 export 重新渲染 | validate_html 1 次失敗後恢復 | PASS |
| 瀏覽三頁 | HTTP 200、可讀、無頁面橫向溢出 | 1440×900、390×844、320×640 皆通過 | PASS |
| 簡報全部 10 頁 | 內容、引用、控制列不重疊 | 三個 viewport 逐頁檢查通過 | PASS |
| 左右鍵／按鈕／Home/End／Tab／進度 | 正確切頁與焦點 | 實際互動通過 | PASS |
| hash／瀏覽器上一頁／雙向引用 | 直達正確頁及 Wiki | 實際點擊通過 | PASS |
| Wiki 搜尋與空結果 | 篩選、回饋及重設正常 | tool／不存在關鍵字／清空測試通過 | PASS |
| file:// 離線檔案模式 | 不需 CDN，切頁可用 | 直達第 3 頁、按下一頁至 4 | PASS |
| console／page error／載入失敗 | 0 | 0 / 0 / 0 | PASS |

## 可核查證據

- [最新完整流程](execution_log.json)；[逐頁檢索](retrieval_log.json)；[23 個內容區塊來源鏈](slides_data.json)。
- [單元測試原始輸出](evidence/unit-tests.txt)；[引用恢復](evidence/tests/citation-recovery.json)；[永久失敗拒絕](evidence/tests/citation-rejected.json)；[來源恢復](evidence/tests/source-recovery.json)；[HTML 恢復](evidence/tests/html-recovery.json)。
- [瀏覽器 gate 原始報告](evidence/browser-pipeline/report.json)：80/80，Chrome 157.0.8103.79，開始 2026-11-23T23:11:54.329674+08:00，結束 2026-11-23T23:12:09.653131+08:00。
- [桌面簡報](evidence/browser-pipeline/desktop-slide-4.png)、[手機 Tool Calling](evidence/browser-pipeline/mobile-slide-5.png)、[桌面 Graph](evidence/browser-pipeline/desktop-workflow.png)。本次已開圖目視檢查先前同版內容，後續 gate 再檢查修正後版本。

## 反思與驗證邊界

本次故意刪除一筆引用，在 validate_claims 出現一次可恢復錯誤；這只證明該故障路徑有效，不代表此節點日常錯誤率最高。原稿的 S01 反向關聯漏掉 W03 也已修正，因此加入雙向索引檢查。將來源 ID 與欄位一致性檢查放在渲染前，能提前阻擋引用遺漏。Graph 的調整是讓失敗回到對應節點，並先渲染暫存檔，通過才覆蓋展示檔。

來源正文與摘要的語義支持性是本次 Codex 閱讀核查，未自動驗證每一條外部敘述；未有獨立人類複核。檢索使用關鍵字排序，未測 embedding 或泛用查詢召回率。Chrome 是實際桌面瀏覽器的 viewport 模擬，未在實體手機、Safari、螢幕閱讀器上測試；全螢幕 API 的實體顯示效果與列印分頁未驗證。未呼叫 LLM API；未上傳課堂指定第三方 Wiki 平台。公開部署狀態另見 DEPLOYMENT.md，不從本機測試推論公開站可用。
