"""One-time editorial migration. Do not run to overwrite later editorial changes."""
import json, pathlib
P=pathlib.Path(__file__).resolve().parent
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
wiki=json.loads((P/'original/wiki.json').read_text(encoding='utf-8'))
for s in wiki['sources']:
    s['related']=[e['id'] for e in wiki['entries'] if s['id'] in e['sources']]
receipts={x['id']:x for x in json.loads((P/'sources/acquisition.json').read_text(encoding='utf-8'))}
locators={
'S01':['Agent design foundations','Defining tools','Guardrails'],
'S02':['What are agents?','What are agents?','Building blocks, workflows, and agents'],
'S03':['Agents','Agents / ToolNode','Routing / conditional edges'],
'S04':['Start with the right level of complexity','Sequential orchestration / Concurrent orchestration / Handoff orchestration','Start with the right level of complexity'],
'S05':['Agent architecture overview / Agent tools','Agent memory / Short-term memory / Long-term memory','Agent security and governance']}
for s in wiki['sources']:
    r=receipts[s['id']]
    record={**s,'summary':'；'.join(s['facts']),'acquisition':r,
      'review_method':'本次 Codex 讀取發行方網頁核對；摘要以繁體中文改寫，不是逐字轉錄。Python GET 保留標題、章節與內容雜湊；不保存整篇原文。',
      'points':[{'id':f"{s['id']}-P{i+1}",'claim':f,'locator':locators[s['id']][i]} for i,f in enumerate(s['facts'])],
      'limitations': '網頁含授權提示，但本次 GET 與網頁讀取可取得正文；未登入帳戶。' if s['id']=='S04' else '取得的是本次頁面版本；未核驗歷史版本或每個外連。'}
    save(P/'sources'/f"{s['id']}.json",record)
    text=f"# {s['id']} · {s['title']}\n\n發行方：{s['publisher']}\n\n原始網址：{s['url']}\n\n本次標題：{r['observed_title']}\n\n取得：{r['checked_at']}；HTTP {r.get('http_status')}；{r['method']}\n\n## 主題摘要\n\n{record['summary']}\n\n## 可回溯要點\n\n"
    text+='\n'.join(f"- {x['id']}：{x['claim']}（原文章節：{x['locator']}）" for x in record['points'])
    text+=f"\n\n對應 Wiki：{', '.join(s['related'])}\n\n{record['review_method']}\n\n限制：{record['limitations']}\n\n原文回應 SHA-256：`{r['sha256']}`；位元組數：{r['bytes']}。未保留整份原文，因此此雜湊用於版本識別，無法離線還原全文。\n"
    (P/'sources'/f"{s['id']}.md").write_text(text,encoding='utf-8')
entries={x['id']:x for x in wiki['entries']}
entries['W01']['details'][0]='一般單次 LLM 呼叫可直接產生回答；聊天介面也可能接上工具，不能只看介面判斷是否為 Agent。'
entries['W02']['title']='Agent 的四個基本元件（教學整理）'
entries['W02']['details'].append('此四項是本教學的整合框架：OpenAI 提出模型、工具、指令，另以 Google Cloud 的狀態／記憶補充。')
examples={
'W01':'教學情境：請幫我把五篇 Agent 文件整理成有來源的學習簡報；系統需要取得資料、整理並檢查。',
'W02':'例：模型選擇查詢；指令要求附來源；工具讀取 Wiki；狀態記住已找到的條目。',
'W03':'工具呼叫示意：模型提出 search_wiki(query="工具迴圈")；執行環境查詢 Wiki，將 W03 回傳給模型。這是教學示意，並非本程式呼叫 LLM 的紀錄。',
'W04':'狀態示例：query、retrieved_ids、draft、errors、retry_count。若引用檢查失敗，就帶著錯誤回到檢索節點。',
'W05':'例：先整理來源，再起草摘要，最後檢查引用；不合格就回到檢索與起草。',
'W06':'練習：若引用不存在，應先回檢索／引用檢查；重試到上限仍失敗，就停止輸出並回報。'}
for e in wiki['entries']:
    e['example']=examples[e['id']]
    e['source_points']={s:[f'{s}-P{i+1}' for i in range(3)] for s in e['sources']}
wiki['method']='本機結構化 Wiki；初稿經本次原始來源核查後補強。先記錄設計推演，再以 Python 檢索與規則組合產生簡報；執行器未呼叫 LLM API，未上傳第三方 Wiki 平台。'
save(P/'wiki.json',wiki)
(P/'INGEST_LOG.md').write_text('# 真實來源整理紀錄\n\n本次五篇均由 Python urllib GET 取得 HTTP 200，並透過網頁讀取工具核對正文及章節。這與只有 URL 的初稿不同：現在每篇有 metadata、摘要、三個帶章節定位的重點、時間、方法與回應雜湊。摘要為 Codex 改寫與核對，workflow 重跑時讀取本地整理檔，不會假裝重新讀取網路全文。\n\n| ID | 整理檔 | 狀態 | 證據 |\n|---|---|---|---|\n'+ '\n'.join(f"| {s['id']} | [整理](sources/{s['id']}.md) / [JSON](sources/{s['id']}.json) | 已取得並整理 | acquisition.json；{receipts[s['id']]['checked_at']} |" for s in wiki['sources'])+'\n\n## 已觀察到的失敗與修復\n\n第一次在受限網路執行 audit_sources.py，五篇均 DNS getaddrinfo failed；使用已允許的網路執行後五篇 HTTP 200。該次結果已寫入 acquisition.json，但終端機列印 Google 標題時因 cp950 無法輸出不換行空白而退出 1；現已將 stdout 設為 UTF-8。這是輸出編碼錯誤，不是來源取得失敗。\n\n來源文字未大量複製；Microsoft 頁面顯示授權提示但正文可讀，記於 S04 限制。內容正確性仍需人工閱讀，HTTP 200 與 schema 檢查本身不證明語義正確。\n',encoding='utf-8')
