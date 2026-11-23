# 真實來源整理紀錄

本次五篇均由 Python urllib GET 取得 HTTP 200，並透過網頁讀取工具核對正文及章節。這與只有 URL 的初稿不同：現在每篇有 metadata、摘要、三個帶章節定位的重點、時間、方法與回應雜湊。摘要為 Codex 改寫與核對，workflow 重跑時讀取本地整理檔，不會假裝重新讀取網路全文。

| ID | 整理檔 | 狀態 | 證據 |
|---|---|---|---|
| S01 | [整理](sources/S01.md) / [JSON](sources/S01.json) | 已取得並整理 | acquisition.json；2026-11-23T22:57:58.914976+08:00 |
| S02 | [整理](sources/S02.md) / [JSON](sources/S02.json) | 已取得並整理 | acquisition.json；2026-11-23T22:57:58.915934+08:00 |
| S03 | [整理](sources/S03.md) / [JSON](sources/S03.json) | 已取得並整理 | acquisition.json；2026-11-23T22:57:58.916410+08:00 |
| S04 | [整理](sources/S04.md) / [JSON](sources/S04.json) | 已取得並整理 | acquisition.json；2026-11-23T22:57:58.916946+08:00 |
| S05 | [整理](sources/S05.md) / [JSON](sources/S05.json) | 已取得並整理 | acquisition.json；2026-11-23T22:57:59.041956+08:00 |

## 已觀察到的失敗與修復

第一次在受限網路執行 audit_sources.py，五篇均 DNS getaddrinfo failed；使用已允許的網路執行後五篇 HTTP 200。該次結果已寫入 acquisition.json，但終端機列印 Google 標題時因 cp950 無法輸出不換行空白而退出 1；現已將 stdout 設為 UTF-8。這是輸出編碼錯誤，不是來源取得失敗。

來源文字未大量複製；Microsoft 頁面顯示授權提示但正文可讀，記於 S04 限制。內容正確性仍需人工閱讀，HTTP 200 與 schema 檢查本身不證明語義正確。
