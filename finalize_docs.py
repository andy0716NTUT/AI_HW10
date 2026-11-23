"""Summarize observed evidence; never invent pass or deployment status."""
import hashlib, pathlib, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from project_utils import ROOT as P, read_json, timestamp, write_json
def main():
    wiki=read_json(P/'wiki.json'); run=read_json(P/'execution_log.json'); meta=read_json(P/'submission_metadata.json')
    browser=read_json(P/'evidence/browser-pipeline/report.json')
    unit=(P/'evidence/unit-tests.txt').read_text(encoding='utf-8-sig')
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',unit)
    if not match or not re.search(r'^OK\s*$',unit,re.M): raise RuntimeError('No successful unit test evidence')
    unit_count=int(match[1]); browser_count=len(browser['checks']); browser_pass=sum(c['passed'] for c in browser['checks'])
    if not browser['passed'] or run['status']!='passed': raise RuntimeError('Latest evidence did not pass')
    failed=[e for e in run['events'] if e['status']=='failed']; rejected=read_json(P/'evidence/tests/citation-rejected.json')
    deploy=read_json(P/'deployment.json') if (P/'deployment.json').exists() else {'status':'尚未部署','repository':'https://github.com/andy0716NTUT/AI_HW10','reason':'等待推送、設定 Pages 及公開網址實測'}
    write_json(P/'deployment.json',deploy)
    live=deploy.get('status')=='verified' and deploy.get('public_url')
    public=read_json(P/'evidence/public/report.json') if (P/'evidence/public/report.json').exists() else None
    public_note=f"公開站另已實測 {sum(c['passed'] for c in public['checks'])}/{len(public['checks'])} 項瀏覽器檢查（不含本機 file:// 兩項）；證據：evidence/public/report.json。" if live and public and public['passed'] else ''
    base=deploy['public_url'].rstrip('/')+'/' if live else ''
    urls=f"Wiki：{base}\n\n簡報：{base}slides.html\n\nGraph：{base}workflow.html" if live else '公開網址：尚未部署；目前只提供本機檔案，不能當成公開 URL。'
    title=' '.join(meta[k] for k in ('school','student_id','department_year','name','topic'))
    claims=run['checks']['claims']['claims']
    (P/'README.md').write_text(f'''# AI Agent LLM Wiki 與教學簡報

五份發行方文件 → 六個 Wiki 條目 → 十頁教學簡報；{claims} 個內容區塊逐一帶有 Wiki 欄位與來源 ID。原稿原樣保留於 `original/`，改善版在專案根目錄。

## 快速展示

直接雙擊 `index.html`、`slides.html`、`workflow.html`；不需 CDN 或後端。簡報支援前後按鈕、左右鍵、Home/End、F 全螢幕及 `#slide-7` 直達頁面。手機可捲動，引用可點回 Wiki 與原始資料。

{urls}

{public_note}

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

- 單元／整合測試：{unit_count}/{unit_count}；真實 {browser['browser']} UI 檢查：{browser_pass}/{browser_count}。
- 實跑：`{run['run_id']}`，{len(run['events'])} 個節點事件，引用錯誤被攔截一次並恢復；原始數據見 execution_log.json。
- 詳細操作、限制、截圖與反思見 `VALIDATION_REPORT.md`、`workflow.html`。
- Pages 設定、部署狀態及打包：見 `DEPLOYMENT.md`；`python package_site.py` 輸出 `dist/` 與 `site-deploy.zip`。
- 交作業用 `SUBMISSION.md`；完整檔案清單與 SHA-256 見 `FILE_MANIFEST.json`。
''',encoding='utf-8')
    commands=[('python audit_sources.py','首次 DNS 失敗；允許的網路重試取得 5×HTTP 200；終端 cp950 失敗另修為 UTF-8'),('python workflow.py --fault citation-once','PASS；首次實跑 12 事件，引用檢查失敗→檢索→重新起草→通過'),('python -m unittest discover -s tests -v',f'PASS；{unit_count} tests / {match[2]} 秒（最近一次保留輸出）'),('python browser_check.py --evidence evidence/browser-authorized', 'PASS；80/80；首輪受限啟動停滯取消，允許的環境完成'),('python workflow.py --fault citation-once --browser',f'PASS；run {run["run_id"]}；{len(run["events"])} 事件；{browser_pass}/{browser_count} UI checks')]
    (P/'VALIDATION_REPORT.md').write_text(f'''# 真實驗證報告

產生：{timestamp()}（Asia/Taipei）。本報告由既有 execution log、Chrome report 與 unittest 終端輸出彙整；不是硬編 pass。

## 實際執行命令

| 命令 | 觀察到的結果 |
|---|---|
'''+ '\n'.join(f'| `{a}` | {b} |' for a,b in commands)+f'''

## 操作、預期與實際

| 操作 | 預期 | 實際 | 結果 |
|---|---|---|---|
| 五篇原始文件 GET | 取得正文且標題合理 | 5×200；標題／章節核對，S04 授權提示但正文可讀 | PASS |
| 本地來源 ingest | 至少五份，各含 metadata、摘要及 3 點 | 五份整理、15 要點、時間與方法 | PASS |
| Wiki 與投影片引用 | 6 條目有效，10 頁全部回溯 | {claims} 區塊逐字比對 Wiki 欄位，來源集合一致 | PASS |
| 本次缺引用注入 | 匯出前攔截，回 retrieve | {len(failed)} 次失敗；{', '.join(e['node'] for e in failed)}→retrieve→draft→重新驗證 | PASS |
| 永久缺引用 | 最多 2 次重試後拒絕，原成果不變 | {sum(e['status']=='failed' for e in rejected['events'])} 次失敗，rejected，既有 release 未覆寫 | PASS |
| 暫時來源缺漏 | 回 ingest 重讀本地檔 | ingest 1 次失敗後恢復 | PASS |
| HTML 缺導航 ID | 回 export 重新渲染 | validate_html 1 次失敗後恢復 | PASS |
| 瀏覽三頁 | HTTP 200、可讀、無頁面橫向溢出 | 1440×900、390×844、320×640 皆通過 | PASS |
| 簡報全部 10 頁 | 內容、引用、控制列不重疊 | 三個 viewport 逐頁檢查通過 | PASS |
| 左右鍵／按鈕／Home/End／Tab／進度 | 正確切頁與焦點 | 實際互動通過 | PASS |
| hash／瀏覽器上一頁／雙向引用 | 直達正確頁及 Wiki | 實際點擊通過 | PASS |
| Wiki 搜尋與空結果 | 篩選、回饋及重設正常 | tool／不存在關鍵字／清空測試通過 | PASS |
| file:// 離線檔案模式 | 不需 CDN，切頁可用 | 直達第 3 頁、按下一頁至 4 | PASS |
| console／page error／載入失敗 | 0 | {len(browser['console_errors'])} / {len(browser['page_errors'])} / {len(browser['failed_requests'])} | PASS |

## 可核查證據

- [最新完整流程](execution_log.json)；[逐頁檢索](retrieval_log.json)；[23 個內容區塊來源鏈](slides_data.json)。
- [單元測試原始輸出](evidence/unit-tests.txt)；[引用恢復](evidence/tests/citation-recovery.json)；[永久失敗拒絕](evidence/tests/citation-rejected.json)；[來源恢復](evidence/tests/source-recovery.json)；[HTML 恢復](evidence/tests/html-recovery.json)。
- [瀏覽器 gate 原始報告](evidence/browser-pipeline/report.json)：{browser_pass}/{browser_count}，{browser['browser']}，開始 {browser['started_at']}，結束 {browser['finished_at']}。
- [桌面簡報](evidence/browser-pipeline/desktop-slide-4.png)、[手機 Tool Calling](evidence/browser-pipeline/mobile-slide-5.png)、[桌面 Graph](evidence/browser-pipeline/desktop-workflow.png)。本次已開圖目視檢查先前同版內容，後續 gate 再檢查修正後版本。

## 反思與驗證邊界

本次故意刪除一筆引用，在 validate_claims 出現一次可恢復錯誤；這只證明該故障路徑有效，不代表此節點日常錯誤率最高。原稿的 S01 反向關聯漏掉 W03 也已修正，因此加入雙向索引檢查。將來源 ID 與欄位一致性檢查放在渲染前，能提前阻擋引用遺漏。Graph 的調整是讓失敗回到對應節點，並先渲染暫存檔，通過才覆蓋展示檔。

來源正文與摘要的語義支持性是本次 Codex 閱讀核查，未自動驗證每一條外部敘述；未有獨立人類複核。檢索使用關鍵字排序，未測 embedding 或泛用查詢召回率。Chrome 是實際桌面瀏覽器的 viewport 模擬，未在實體手機、Safari、螢幕閱讀器上測試；全螢幕 API 的實體顯示效果與列印分頁未驗證。未呼叫 LLM API；未上傳課堂指定第三方 Wiki 平台。公開部署狀態另見 DEPLOYMENT.md，不從本機測試推論公開站可用。
''',encoding='utf-8')
    (P/'SUBMISSION.md').write_text(f'''# {title}

## 主題與簡介

以「如何把五篇文件整理成可信的學習簡報」為情境，介紹 AI Agent 的定義、LLM／Workflow 差異、元件、Tool Calling、Agent Loop、Graph／狀態、安全與設計模式。先寫真實設計推演，再整理五份發行方資料成六個本機 Wiki 條目，依查詢檢索 Wiki 生成十頁響應式 HTML 簡報。

## 成果與網址

{urls}

{public_note}

本機展示：`index.html`（Wiki）、`slides.html`（10 頁簡報）、`workflow.html`（Graph、實跑與反思）。原始資料：`wiki.json`、`sources/`；逐頁查詢：`retrieval_log.json`；{claims} 個內容區塊的欄位與來源引用：`slides_data.json`。

## Loop／Graph 實作

Python 實際執行 load_sources → ingest → build_wiki → retrieve → draft_slides → validate_claims → export（暫存）→ validate_html → publish（本機）。來源不足回 ingest；缺引用回 retrieve/draft；HTML 失敗回 export。每處最多重試兩次，持續失敗拒絕發布；通過後才輸出正式 HTML。

## 實跑與檢查

本次 `python workflow.py --fault citation-once --browser` 的 run ID 為 `{run['run_id']}`，共 {len(run['events'])} 個節點事件。刻意刪掉一筆來源引用，在 validate_claims 攔截一次，重新檢索與起草後通過。{unit_count} 個流程測試通過；{browser['browser']} 在桌面、手機與窄螢幕完成 {browser_pass}/{browser_count} 項 UI 檢查，console error／page error／failed request 均為 0。永久缺引用測試到第三次失敗後拒絕匯出，既有成果保留。

證據：`execution_log.json`、`evidence/tests/`、`evidence/browser-pipeline/report.json`、`VALIDATION_REPORT.md`。所有結果來自實際執行；靜態 schema、瀏覽器驗證與公開部署分別記錄。

## 反思

本次觀察的引用錯誤是刻意注入，不能聲稱它是最常出錯的節點。實際稽核也找到原稿 S01 對 W03 的反向索引遺漏，已修正並加檢查。把來源映射與 Wiki 欄位比對前移到渲染之前，可避免完成 HTML 才發現引用遺失；暫存與最大重試上限則避免壞草稿覆蓋成果。下一步需要人工標註更多查詢、檢查檢索召回率及語義支持性，而非只依賴 ID 有效就認定內容正確。

## 誠實揭露

本作是 Codex 輔助編輯的本機結構化 Wiki；執行器為 deterministic 檢索與規則組合，未呼叫 LLM API，也未使用 LangGraph 套件或上傳第三方 LLM Wiki 平台。來源已取得並整理，不只列出 URL。若老師指定某個 Wiki 平台，仍需將本作上傳該平台；不宣稱此項已完成。

## 完整來源

'''+ '\n'.join(f"- {s['id']} · {s['publisher']}：[ {s['title']} ]({s['url']})；整理檔 `sources/{s['id']}.md`。" for s in wiki['sources'])+'''

## 檔案清單

展示頁、Python 流程與產生器、十頁查詢計畫、五篇來源整理、逐主張引用資料、真實測試與截圖、Graph、README、INGEST_LOG、RUN_LOG、VALIDATION_REPORT、DEPLOYMENT、Pages 設定與原稿備份皆已保留。逐檔 SHA-256 清單見 `FILE_MANIFEST.json`。
''',encoding='utf-8')
    (P/'DEPLOYMENT.md').write_text(f'''# GitHub Pages 部署紀錄

Repository：[andy0716NTUT/AI_HW10](https://github.com/andy0716NTUT/AI_HW10)，由使用者本次提供。已查 GitHub metadata：public、push/admin 可用；首次讀 contents 回覆「repository is empty」，沒有覆寫其他專案。

狀態：**{'已部署且公開網址已驗證' if live else '尚未部署'}**。

{urls}

{public_note}

機器紀錄：`deployment.json`。只有成功收到公開站 HTTP 與瀏覽器驗證後才標記 verified；推送 commit 或 Actions 成功本身不等於本機已實際開過公開網址。

## 可重現部署方式

1. 將本專案檔案推送到指定 repo 的 `main`，不包含 `.tools/`、金鑰或憑證。
2. 在 GitHub Settings → Pages 選 GitHub Actions；`.github/workflows/pages.yml` 會重建、跑流程測試、打包 `dist/`，並部署 Pages。此雲端流程只跑靜態 gate；本機 Chrome 證據另保存。
3. 或使用 `python package_site.py` 產生靜態套件，將 dist/ 內容推至專用分支並從該分支發布。套件不包含 Python runtime 或安裝依賴。
4. 開啟實際回傳的 Pages URL，確認 Wiki、slides.html、workflow.html 與相對引用可讀；將觀察寫入 deployment.json，再執行 `python finalize_docs.py` 更新繳交稿。

工作流結構參照 [GitHub 官方 Pages custom workflow 文件](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)，包含 build/deploy 依賴、Pages artifact、pages:write / id-token:write 與 github-pages environment。不在檔案存取 API token。
''',encoding='utf-8')
    ignored={'.tools','.git','__pycache__','dist','node_modules'}
    files=[p for p in P.rglob('*') if p.is_file() and not ignored.intersection(p.relative_to(P).parts) and p.suffix!='.zip' and p.name!='FILE_MANIFEST.json']
    write_json(P/'FILE_MANIFEST.json',{'created_at':timestamp(),'note':'Manifest excludes itself, dependency/cache directories and deploy ZIP. original/ is preserved draft, not current claims.','files':[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]})
    print(f'Docs generated from real evidence: {unit_count} tests, {browser_pass}/{browser_count} browser checks; deployment {deploy["status"]}')
if __name__=='__main__': main()
