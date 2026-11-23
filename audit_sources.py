"""Fetch primary documents, retain metadata and short evidence, not full copies."""
import concurrent.futures, datetime, hashlib, html, json, pathlib, re, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = pathlib.Path(__file__).resolve().parent
def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def audit(s):
    result = {'id':s['id'], 'requested_url':s['url'], 'checked_at':now(), 'method':'Python urllib GET; title and headings extraction; Codex separately reviewed publisher web document (not a human review)'}
    try:
        req = urllib.request.Request(s['url'], headers={'User-Agent':'Mozilla/5.0 (educational source verification)'})
        with urllib.request.urlopen(req, timeout=35) as r:
            raw=r.read(); result.update(http_status=r.status, final_url=r.url, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        text=raw.decode('utf-8',errors='replace')
        title=re.search(r'<title[^>]*>(.*?)</title>',text,re.S|re.I)
        clean=lambda x:html.unescape(re.sub('<[^>]+>',' ',x)).strip()
        headings=[clean(x) for x in re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>',text,re.S|re.I)]
        result.update(status='retrieved', observed_title=clean(title[1]) if title else '', headings=headings[:30])
    except Exception as e:
        result.update(status='unavailable',error=str(e))
    return result
def main():
    wiki=json.loads((ROOT/'wiki.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(audit,wiki['sources']))
    (ROOT/'sources'/'acquisition.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for x in results: print(x['id'],x['status'],x.get('http_status'),x.get('observed_title',x.get('error')))
if __name__=='__main__': main()
