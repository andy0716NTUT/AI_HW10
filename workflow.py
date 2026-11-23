"""Reproducible local retrieval/composition graph. No LLM API calls."""
import argparse, copy, html, json, pathlib, re, shutil, sys, tempfile, time
from html.parser import HTMLParser
from project_utils import ROOT, digest, log_progress, read_json, timestamp, write_json
sys.stdout.reconfigure(encoding='utf-8')

class ValidationError(ValueError): pass

def field(entry,path):
    value=entry
    for key in path.split('.'): value=value[int(key)] if isinstance(value,list) else value[key]
    return value

def validate_schema(wiki):
    sources=wiki['sources']; entries=wiki['entries']
    if len(sources)<5 or len({s['id'] for s in sources})!=len(sources): raise ValidationError('至少五個不重複來源')
    if len({e['id'] for e in entries})!=len(entries): raise ValidationError('Wiki ID 重複')
    ids={s['id'] for s in sources}
    for s in sources:
        if not all(s.get(k) for k in ('id','publisher','title','url','facts')) or len(s['facts'])<3: raise ValidationError('來源欄位不完整')
        if not s['url'].startswith('https://'): raise ValidationError('來源網址需 HTTPS')
    for e in entries:
        if not e.get('sources') or not set(e['sources'])<=ids: raise ValidationError(f"{e['id']} 來源引用無效")
        if not all(e.get(k) for k in ('title','summary','details','example')): raise ValidationError('Wiki 欄位不完整')
    for s in sources:
        expected={e['id'] for e in entries if s['id'] in e['sources']}
        if set(s['related'])!=expected: raise ValidationError(f"{s['id']} 雙向來源關聯不一致")
    return {'sources':len(sources),'entries':len(entries),'schema':'valid'}

def load_sources(root):
    wiki=read_json(root/'wiki.json')
    return wiki, {s['id']:read_json(root/'sources'/f"{s['id']}.json") for s in wiki['sources']}

def ingest(wiki, records):
    for s in wiki['sources']:
        r=records.get(s['id'],{})
        if any(r.get(k)!=s.get(k) for k in ('id','title','url','publisher','facts')): raise ValidationError(f"{s['id']} 整理檔與 Wiki 不一致")
        a=r.get('acquisition',{})
        if a.get('status')!='retrieved' or a.get('http_status')!=200 or not a.get('sha256') or not a.get('checked_at'): raise ValidationError(f"{s['id']} 取得證據不完整")
        if not r.get('summary') or len(r.get('points',[]))<3 or any(not p.get('locator') for p in r['points']): raise ValidationError(f"{s['id']} 摘要或定位不完整")
        if [p['claim'] for p in r['points']]!=s['facts']: raise ValidationError('摘要重點與來源主張不一致')
    return {'ingested':len(records),'mode':'local reviewed summaries; no new network fetch'}

def build_wiki(wiki):
    result=validate_schema(wiki)
    result['wiki_sha256']=digest(wiki)
    return result

def retrieve(wiki,plan):
    results=[]
    for page in plan:
        slots=[]
        for q in page['queries']:
            terms=[q['query'].lower()]+re.findall(r'[a-z]+|[\u4e00-\u9fff]{2,}',q['query'].lower())
            ranked=[]
            for entry in wiki['entries']:
                title=entry['title'].lower(); body=json.dumps(entry,ensure_ascii=False).lower()
                score=sum(10*(t in title)+int(t in body) for t in terms)
                if score: ranked.append((score,entry['id'],entry))
            ranked.sort(key=lambda x:(-x[0],x[1]))
            if not ranked: raise ValidationError(f"檢索無結果：{q['query']}")
            score,_,entry=ranked[0]
            slots.append({'query':q['query'],'score':score,'entry':copy.deepcopy(entry),'fields':q['fields']})
        results.append({'title':page['title'],'label':page['label'],'slots':slots})
    return results

def draft_slides(retrieved):
    slides=[]
    for i,page in enumerate(retrieved,1):
        claims=[]
        for slot in page['slots']:
            entry=slot['entry']
            for path in slot['fields']:
                claims.append({'text':field(entry,path),'entry_id':entry['id'],'field':path,'source_ids':entry['sources'][:], 'kind':'教學示例' if path=='example' else '知識主張'})
        slides.append({'id':f'slide-{i}','title':page['title'],'label':page['label'],'claims':claims})
    return slides

def validate_claims(wiki,slides):
    if len(slides)!=10: raise ValidationError('應有 10 張投影片')
    entries={e['id']:e for e in wiki['entries']}; used=set()
    for slide in slides:
        if not slide['claims']: raise ValidationError('投影片沒有主張')
        for c in slide['claims']:
            entry=entries.get(c.get('entry_id'))
            if not entry or not c.get('source_ids') or set(c['source_ids'])!=set(entry['sources']): raise ValidationError(f"{slide['id']} 缺引用或來源集合不符")
            try: expected=field(entry,c['field'])
            except (KeyError,IndexError,TypeError): raise ValidationError('主張欄位不存在')
            if c['text']!=expected: raise ValidationError('主張文字與 Wiki 不一致')
            used.add(entry['id'])
    if used!=set(entries): raise ValidationError('尚有 Wiki 條目未被簡報引用')
    return {'slides':len(slides),'claims':sum(len(s['claims']) for s in slides),'referenced_entries':sorted(used),'scope':'欄位逐字比對與引用一致性；不等於自動語義事實查核'}

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.ids=[]; self.links=[]; self.assets=[]; self.remote_assets=[]; self.slide_count=0; self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a' and 'href' in a: self.links.append(a['href'])
        if tag=='section' and 'slide' in a.get('class','').split(): self.slide_count+=1
        if tag in ('script','img','link') and a.get('src',a.get('href','')): self.assets.append(a.get('src',a.get('href','')))
        if tag in ('script','img','link') and a.get('src',a.get('href','')).startswith(('http:','https:','//')): self.remote_assets.append(a)

def validate_html(directory):
    docs={}
    for name in ('index.html','slides.html','workflow.html'):
        text=(directory/name).read_text(encoding='utf-8')
        if '<html lang="zh-Hant">' not in text or 'name="viewport"' not in text: raise ValidationError('缺語言或 viewport')
        doc=Document(text); docs[name]=doc
        if len(doc.ids)!=len(set(doc.ids)) or doc.remote_assets: raise ValidationError('重複 ID 或依賴 CDN')
    if docs['slides.html'].slide_count!=10 or not {'prev','next','progress','position'}<=set(docs['slides.html'].ids): raise ValidationError('HTML 投影片或導覽不完整')
    for name,doc in docs.items():
        for asset in doc.assets:
            if not re.match(r'^[a-z]+:',asset) and not (directory/asset).is_file(): raise ValidationError(f'缺少本地資產 {asset}')
        for link in doc.links:
            if re.match(r'^[a-z]+:',link): continue
            path,_,anchor=link.partition('#'); path=path or name
            target=directory/path
            if not target.is_file(): raise ValidationError(f'失效連結 {name}: {link}')
            if anchor and path in docs and anchor not in docs[path].ids: raise ValidationError(f'失效錨點 {link}')
    return {'html_files':3,'slides':10,'local_links':'valid','cdn_dependencies':0,'scope':'static HTML structure and local links; browser QA separately recorded'}

def run(root=ROOT,out=None,fault=None,max_retries=2,browser=False):
    root=pathlib.Path(root); out=pathlib.Path(out or root); out.mkdir(parents=True,exist_ok=True)
    run_id=timestamp().replace(':','').replace('.','')
    events=[]; retries={}; checks={}; state={'run_id':run_id,'started_at':timestamp(),'mode':'deterministic retrieval + rule composition; no LLM API','fault':fault,'events':events,'max_retries':max_retries,'status':'running'}
    stage=pathlib.Path(tempfile.mkdtemp(prefix='wiki-stage-')); node='load_sources'; wiki={}; records={}; slides=[]; retrieved=[]; injected=set(); published=False
    plan=read_json(root/'slide_plan.json')
    def save():
        state['retry_counts']=retries; state['finished_at']=timestamp()
        write_json(out/'execution_log.json',state); write_json(out/'evidence/runs'/f'{run_id}.json',state)
    try:
        while True:
            start=time.perf_counter(); event={'node':node,'started_at':timestamp(),'input':{'wiki_sha256':digest(wiki),'slide_count':len(slides)}}
            try:
                if node=='load_sources':
                    wiki,records=load_sources(root); result={'loaded_sources':len(records),'input_files':['wiki.json','sources/S01–S05.json','slide_plan.json'],'wiki_sha256':digest(wiki),'sources_sha256':digest(records),'plan_sha256':digest(plan)}; next_node='ingest'
                elif node=='ingest':
                    # A transient incomplete in-memory read is recoverable by reloading the local records.
                    wiki,records=load_sources(root)
                    if fault=='source-once' and node not in injected:
                        records[wiki['sources'][0]['id']]['points']=[]; injected.add(node)
                    result=ingest(wiki,records); next_node='build_wiki'
                elif node=='build_wiki': result=build_wiki(wiki); next_node='retrieve'
                elif node=='retrieve':
                    retrieved=retrieve(wiki,plan); result={'queries':[{'query':s['query'],'entry_id':s['entry']['id'],'score':s['score']} for p in retrieved for s in p['slots']]}; next_node='draft_slides'
                elif node=='draft_slides':
                    slides=draft_slides(retrieved)
                    if fault in ('citation-once','citation-always') and (fault=='citation-always' or 'citation' not in injected): slides[0]['claims'][0]['source_ids']=[]; injected.add('citation')
                    result={'slides':len(slides),'draft_sha256':digest(slides)}; next_node='validate_claims'
                elif node=='validate_claims': result=validate_claims(wiki,slides); checks['claims']=result; next_node='export'
                elif node=='export':
                    import build
                    # Validated candidates live in a temporary staging directory until all gates pass.
                    build.render(wiki,slides,records,stage,state,root)
                    if fault=='html-once' and 'html' not in injected:
                        p=stage/'slides.html'; p.write_text(p.read_text(encoding='utf-8').replace('id="next"','id="broken"'),encoding='utf-8'); injected.add('html')
                    result={'destination':'temporary staging','files':['index.html','slides.html','workflow.html']}; next_node='validate_html'
                elif node=='validate_html':
                    result=validate_html(stage); checks['html']=result
                    if browser:
                        from browser_check import check_site
                        checks['browser']=check_site(stage,out/'evidence/browser-pipeline')
                        if not checks['browser']['passed']: raise ValidationError('瀏覽器檢查失敗；見 browser report')
                    next_node='publish'
                elif node=='publish':
                    state['status']='passed'; state['checks']=checks
                    # Refresh the evidence page with completed validation events before final export.
                    import build
                    build.render(wiki,slides,records,stage,state,root)
                    validate_html(stage)
                    for p in stage.iterdir():
                        if p.is_file() and p.name not in ('RUN_LOG.md',): shutil.copy2(p,out/p.name)
                    for folder in ('sources',): shutil.copytree(root/folder,out/folder,dirs_exist_ok=True) if root!=out else None
                    write_json(out/'slides_data.json',slides)
                    write_json(out/'retrieval_log.json',[{'title':p['title'],'slots':[{'query':s['query'],'score':s['score'],'entry_id':s['entry']['id'],'fields':s['fields']} for s in p['slots']]} for p in retrieved])
                    write_json(out/'validation.json',{'run_id':run_id,'checked_at':timestamp(),'passed':True,'checks':checks,'notes':'Static checks plus browser only if requested. Source semantics reviewed separately; not an autonomous LLM run.'})
                    published=True; result={'destination':'local output (not public deployment)','files':['index.html','slides.html','workflow.html','slides_data.json','retrieval_log.json','validation.json']}; next_node=None
                else: raise RuntimeError(node)
                event.update(status='passed',output=result)
            except (ValidationError,KeyError,ValueError,FileNotFoundError) as e:
                target={'ingest':'ingest','build_wiki':'ingest','retrieve':'retrieve','validate_claims':'retrieve','validate_html':'export','export':'export'}.get(node)
                retries[node]=retries.get(node,0)+1
                event.update(status='failed',error=str(e),retry_target=target,retry_number=retries[node])
                if not target or retries[node]>max_retries:
                    event['retry_target']=None; raise ValidationError(f'{node}: {e}; 重試上限／不可恢復，拒絕發布')
                next_node=target
            finally:
                event['elapsed_ms']=round((time.perf_counter()-start)*1000,3); events.append(event); save()
            if next_node is None: break
            node=next_node
    except Exception as e:
        state['status']='rejected'; state['error']=str(e); state['published']=False; save()
        log_progress(f"流程 {run_id}：REJECTED；{e}；紀錄 evidence/runs/{run_id}.json",out)
        raise
    finally:
        shutil.rmtree(stage)
    state['published']=published; save()
    log_progress(f"流程 {run_id}：PASS；{len(events)} 個節點事件；重試 {retries}；本機匯出完成（不代表公開部署）。",out)
    return state

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',type=pathlib.Path); p.add_argument('--fault',choices=['citation-once','citation-always','source-once','html-once']); p.add_argument('--max-retries',type=int,default=2); p.add_argument('--browser',action='store_true'); args=p.parse_args()
    if args.max_retries<0: p.error('max-retries must be >= 0')
    try:
        state=run(out=args.out,fault=args.fault,max_retries=args.max_retries,browser=args.browser)
        print(json.dumps({'status':state['status'],'run_id':state['run_id'],'events':len(state['events']),'retry_counts':state['retry_counts']},ensure_ascii=False))
    except Exception as e: print(str(e),file=sys.stderr); sys.exit(1)
if __name__=='__main__': main()
