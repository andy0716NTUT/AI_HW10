"""Pure HTML renderer. Workflow supplies claims retrieved from wiki.json."""
import collections, html, pathlib, shutil
from project_utils import ROOT, write_json
E=lambda x:html.escape(str(x),quote=True)
DISCLOSURE='本機 Wiki → 檢索 → 規則組合；執行器未呼叫 LLM API。來源摘要曾由 Codex 輔助編輯與核對。'
def page(title,body,script='',classes=''):
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="AI Agent 新手教學：五篇來源、六個 Wiki 條目、十頁簡報與可重現流程。"><title>{E(title)}</title><link rel="stylesheet" href="assets.css"><link rel="icon" href="data:,"></head><body class="{classes}"><a class="skip" href="#main">跳到主要內容</a>{body}{f'<script src="{script}"></script>' if script else ''}</body></html>'''
def nav(): return '<nav aria-label="成果導覽"><a href="index.html">Wiki 知識庫</a><a href="slides.html">教學簡報</a><a href="workflow.html">Graph 與實跑</a></nav>'
def source_links(ids,base='index.html'):
    return ' · '.join(f'<a href="{base}#{E(s)}">{E(s)}</a>' for s in ids)
def reflection(state):
    counts=collections.Counter(e['node'] for e in state['events'] if e['status']=='failed')
    summary='、'.join(f'{k} {v} 次' for k,v in counts.items()) or '沒有觀察到失敗'
    return f'''本次 run <code>{E(state['run_id'])}</code> 的失敗事件：{E(summary)}。故障模式：<code>{E(state.get('fault') or '未注入')}</code>。刻意注入的錯誤只用於測試，不能推論日常最常出錯的節點。將來源映射與主張欄位比對移到匯出前，能在 HTML 發布前攔截缺引用；但逐字一致與 HTTP 200 都不能證明原始主張語義正確，仍需閱讀原文。下一步應以不同題目的人工標註資料測量檢索品質，並記錄語義錯誤。'''
def graph():
    names=['load_sources','ingest','build_wiki','retrieve','draft_slides','validate_claims','export（候選）','validate_html']
    labels=['讀取本地來源','整理完整性檢查','建立／核查 Wiki','依查詢檢索','組合 Wiki 欄位','核對主張與引用','渲染到暫存區','結構／可選瀏覽器檢查']
    pos=[(20,30),(260,30),(500,30),(740,30),(740,170),(500,170),(260,170),(20,170)]
    boxes=''.join(f'<g><rect x="{x}" y="{y}" width="220" height="80" rx="12"/><text x="{x+14}" y="{y+30}">{E(n)}</text><text class="secondary" x="{x+14}" y="{y+57}">{E(l)}</text></g>' for (x,y),n,l in zip(pos,names,labels))
    return f'''<figure><div class="graph-scroll"><svg viewBox="0 0 980 430" role="img" aria-labelledby="graph-title graph-desc"><title id="graph-title">實作 Graph：八節點、條件回路與發布閘門</title><desc id="graph-desc">依序載入、ingest、Wiki、retrieve、draft、claims、export 候選、HTML。資料失敗回 ingest，引用失敗回 retrieve，HTML 失敗回 export；每處最多重試兩次，通過才本機發布。</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#62e3c0"/></marker></defs><g class="edges"><path d="M240 70H260 M480 70H500 M720 70H740 M850 110V170 M740 210H720 M500 210H480 M260 210H240"/><path d="M130 250V370H390"/></g><g class="retry-edges"><path d="M370 110V145H250V70H260"/><path d="M610 170V140H850V110"/><path d="M130 170V130H370V170"/></g>{boxes}<text x="180" y="295">資料缺漏 → ingest</text><text x="510" y="295">缺引用 → retrieve / draft</text><text x="180" y="325">HTML 失敗 → export；每處最多重試 2 次</text><rect x="390" y="340" width="370" height="65" rx="12"/><text x="410" y="369">通過 → export（本機正式檔案）</text><text x="410" y="391" class="secondary">超過上限 → REJECTED，不發布候選</text></svg></div><figcaption>實線為主流程，虛線為條件重試。Graph 是 Python 的真實控制流；不宣稱採用 LangGraph 套件。</figcaption></figure>'''
def render(wiki,slides,records,dest,state,root=ROOT):
    dest=pathlib.Path(dest); dest.mkdir(parents=True,exist_ok=True)
    for name in ('assets.css','slides.js','wiki.js'): shutil.copy2(root/name,dest/name)
    shutil.copytree(root/'sources',dest/'sources',dirs_exist_ok=True)
    for p in root.glob('*.md'): shutil.copy2(p,dest/p.name)
    write_json(dest/'wiki.json',wiki); write_json(dest/'slides_data.json',slides); write_json(dest/'execution_log.json',state)
    backlinks=collections.defaultdict(list)
    for i,s in enumerate(slides,1):
        for eid in {c['entry_id'] for c in s['claims']}: backlinks[eid].append(i)
    entries=''
    for w in wiki['entries']:
        text=(w['title']+w['summary']+' '.join(w['details'])+' '.join(w['sources'])).lower()
        entries+=f'''<article id="{E(w['id'])}" class="card entry" data-key="{E(text)}"><p class="eyebrow">{E(w['id'])} / {E(w['section'])}</p><h2>{E(w['title'])}</h2><p>{E(w['summary'])}</p><ul>{''.join('<li>'+E(d)+'</li>' for d in w['details'])}</ul><details><summary>查看教學示例</summary><p>{E(w['example'])}</p></details><p class="references">來源：{source_links(w['sources'],'')}<br>投影片：{' · '.join(f'<a href="slides.html#slide-{n}">{n:02}</a>' for n in backlinks[w['id']])}</p></article>'''
    sources=''
    for s in wiki['sources']:
        r=records[s['id']]; a=r['acquisition']
        sources+=f'''<article id="{E(s['id'])}" class="card"><p class="eyebrow">{E(s['id'])} / {E(s['publisher'])}</p><h3>{E(s['title'])}</h3><p>{E(s['topic'])}</p><ul>{''.join(f'<li>{E(p["claim"])}<small>原文定位：{E(p["locator"])}</small></li>' for p in r['points'])}</ul><p><a href="{E(s['url'])}" target="_blank" rel="noopener noreferrer">閱讀發行方原文</a> · <a href="sources/{s['id']}.md">整理與取得紀錄</a></p><p class="references">HTTP {a['http_status']} · <time>{E(a['checked_at'])}</time><br>對應：{' · '.join(f'<a href="#{e}">{e}</a>' for e in s['related'])}</p></article>'''
    body=f'''{nav()}<main id="main" class="shell"><header class="hero"><p class="eyebrow">AI AGENT / LEARNING WIKI</p><h1>從回答問題，<br>到完成一項任務。</h1><p class="lead">看懂 AI Agent 的工具、回饋迴圈與 Graph。<br>每個概念都能沿著條目 ID 回到原始來源。</p><div class="stats"><span><b>{len(wiki['sources']):02}</b> 篇來源</span><span><b>{len(wiki['entries']):02}</b> 個條目</span><span><b>{len(slides):02}</b> 張投影片</span></div><a class="primary" href="slides.html">開始 10 頁教學</a></header><aside class="notice">{DISCLOSURE} <a href="DESIGN_DECISIONS.md">生成前設計推演</a> · <a href="INGEST_LOG.md">來源整理紀錄</a></aside><section aria-labelledby="wiki-title"><h2 id="wiki-title" class="section-title">知識條目</h2><label for="q">搜尋概念、英文術語或來源 ID</label><input id="q" class="search" type="search" placeholder="例如：工具、graph、S01" autocomplete="off"><p id="search-status" role="status">顯示 6 個條目</p><div class="grid">{entries}</div></section><section aria-labelledby="sources-title"><h2 class="section-title" id="sources-title">原始資料與整理證據</h2><p>來源摘要為改寫；HTTP 200、標題與雜湊是取得證據，內容支持性另經本次原文閱讀核對。</p><div class="grid sources">{sources}</div></section><footer><a href="wiki.json">結構化 Wiki</a> · <a href="slides_data.json">逐主張引用資料</a> · <a href="workflow.html">執行紀錄與反思</a><p>本機成果；公開部署狀態請見 SUBMISSION.md。</p></footer></main>'''
    (dest/'index.html').write_text(page('AI Agent｜可追溯的學習 Wiki',body,'wiki.js'),encoding='utf-8')
    sections=''
    for i,s in enumerate(slides,1):
        claims=''
        for n,c in enumerate(s['claims']):
            claims+=f'''<div class="claim {'lead-claim' if n==0 else ''}" data-entry="{E(c['entry_id'])}" data-field="{E(c['field'])}"><p>{E(c['text'])}</p><p class="references">{E(c['kind'])} · <a href="index.html#{E(c['entry_id'])}">{E(c['entry_id'])} / {E(c['field'])}</a> · {source_links(c['source_ids'])}</p></div>'''
        sections+=f'''<section id="{s['id']}" class="slide" aria-labelledby="title-{i}" {'hidden' if i>1 else ''}><header><span class="eyebrow">{E(s['label'])}</span><span class="counter">{i:02} / {len(slides):02}</span></header><div class="slide-core"><h1 id="title-{i}">{E(s['title'])}</h1>{claims}</div><footer><span>AI AGENT / BEGINNER GUIDE</span><a href="workflow.html">看實際 Graph 與紀錄</a></footer></section>'''
    body=f'''<main id="main" class="deck">{sections}</main><div class="deck-controls"><a href="index.html">Wiki</a><button id="prev" aria-label="上一頁">上一頁</button><span id="position" role="status" aria-live="polite">1 / 10</span><button id="next" aria-label="下一頁">下一頁</button><button id="fullscreen" aria-label="切換全螢幕">全螢幕</button><small>左右鍵 · Home / End</small></div><div class="progress-track"><div id="progress" role="progressbar" aria-label="簡報進度" aria-valuemin="1" aria-valuemax="10" aria-valuenow="1"></div></div>'''
    (dest/'slides.html').write_text(page('AI Agent 是什麼？｜10 頁教學',body,'slides.js','presentation'),encoding='utf-8')
    rows=''.join(f'''<tr><td>{i}</td><td><code>{E(e['node'])}</code></td><td>{E(e['status'])}</td><td>{e['elapsed_ms']:.3f}</td><td>{E(e.get('error',''))}{(' → '+E(e['retry_target'])) if e.get('retry_target') else ''}</td></tr>''' for i,e in enumerate(state['events'],1))
    body=f'''{nav()}<main class="shell" id="main"><header class="hero compact"><p class="eyebrow">WORKFLOW / EVIDENCE</p><h1>讓每個步驟，<br>留下可核查的路徑。</h1><p class="lead">設計圖、實際事件與驗證限制，分開閱讀。</p></header><aside class="notice">{DISCLOSURE} 本作是本機資料與 HTML 流程，未上傳第三方 LLM Wiki。</aside><section class="card"><h2>生成前：設計與決策</h2><p>對象為初學者；以五篇技術文件建立六個概念條目，讓十頁課程可逐主張追溯。這是本次規劃推演，並非假造的歷史對話。</p><a href="DESIGN_DECISIONS.md">閱讀完整設計推演</a></section><section class="card"><h2>已實作的 Graph</h2>{graph()}<p>狀態包含 query、retrieved_ids、draft、errors 與 retry_count。來源不完整時重新讀取本地整理檔；持續缺失則拒絕匯出，並不自動捏造資料。預設 HTML gate 為靜態結構檢查；加 <code>--browser</code> 才執行瀏覽器 gate。</p></section><section class="card"><h2>本次真實運行事件</h2><p>Run：<code>{E(state['run_id'])}</code>；模式：{E(state['mode'])}；故障注入：<code>{E(state.get('fault') or '無')}</code>。下表為本頁產生時已完成的事件，最後 publish 事件請查完整 JSON。</p><div class="table-scroll"><table><thead><tr><th>序</th><th>節點</th><th>結果</th><th>毫秒</th><th>錯誤／重試去向</th></tr></thead><tbody>{rows}</tbody></table></div><p><a href="execution_log.json">完整 execution log</a> · <a href="slides_data.json">主張來源鏈</a> · <a href="VALIDATION_REPORT.md">實際測試報告</a></p><p>預設 HTML gate 只做靜態檢查；瀏覽器結果另由實際 browser_check 執行記錄，不混為一談。</p></section><section class="card"><h2>依本次數據的反思</h2><p>{reflection(state)}</p><p>串接、路由、平行、主控分工與評估優化見 <a href="index.html#W05">W05</a>；本實作採循序流程與檢查回路，未執行多 Agent 分工。</p></section><footer>完整紀錄：<a href="RUN_LOG.md">跨階段 RUN_LOG</a> · <a href="INGEST_LOG.md">INGEST_LOG</a></footer></main>'''
    if not (dest/'VALIDATION_REPORT.md').exists(): (dest/'VALIDATION_REPORT.md').write_text('瀏覽器與整體測試尚未完成；此為建置中的暫存報告。\n',encoding='utf-8')
    (dest/'workflow.html').write_text(page('Graph、真實執行與反思',body),encoding='utf-8')
if __name__=='__main__':
    from workflow import run
    run()
