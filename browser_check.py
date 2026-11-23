"""Real Chrome UI checks with Playwright; no synthetic pass results."""
import argparse, functools, http.server, json, pathlib, sys, threading, time
from project_utils import ROOT, timestamp, write_json
sys.path.insert(0,str(ROOT/'.tools'))
def check_site(directory=ROOT,evidence=None):
    from playwright.sync_api import sync_playwright
    directory=pathlib.Path(directory).resolve(); evidence=pathlib.Path(evidence or ROOT/'evidence/browser').resolve(); evidence.mkdir(parents=True,exist_ok=True)
    report={'started_at':timestamp(),'target':'local HTTP and file://','checks':[],'console_errors':[],'page_errors':[],'failed_requests':[],'screenshots':[]}
    def record(name,fn):
        start=time.perf_counter()
        try:
            actual=fn()
            if actual is False: raise AssertionError('observed false')
            report['checks'].append({'name':name,'passed':True,'actual':actual,'elapsed_ms':round((time.perf_counter()-start)*1000,3)})
        except Exception as e: report['checks'].append({'name':name,'passed':False,'error':str(e),'elapsed_ms':round((time.perf_counter()-start)*1000,3)})
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(directory)))
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    url=f'http://127.0.0.1:{server.server_port}/'
    def expect(condition,message):
        if not condition: raise AssertionError(message)
        return message
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            report['browser']='Chrome '+browser.version
            for label,width,height in [('desktop',1440,900),('mobile',390,844),('narrow',320,640)]:
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                pg=context.new_page()
                pg.on('console',lambda m: report['console_errors'].append(m.text) if m.type=='error' else None)
                pg.on('pageerror',lambda e: report['page_errors'].append(str(e)))
                pg.on('requestfailed',lambda r: report['failed_requests'].append({'url':r.url,'failure':r.failure}))
                for name in ('index.html','slides.html','workflow.html'):
                    response=pg.goto(url+name,wait_until='networkidle')
                    record(f'{label} {name}: HTTP 200',lambda r=response:expect(r.status==200,f'HTTP {r.status}'))
                    record(f'{label} {name}: no horizontal page overflow',lambda:expect(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'page fits viewport'))
                    record(f'{label} {name}: main heading readable',lambda:expect(pg.locator('h1:visible').count()==1 and pg.locator('h1:visible').evaluate('e => parseFloat(getComputedStyle(e).fontSize)')>=28,'one visible h1, >=28px'))
                    if label!='narrow':
                        shot=evidence/f'{label}-{name[:-5]}.png'; pg.screenshot(path=str(shot),full_page=True); report['screenshots'].append(shot.name)
                pg.goto(url+'index.html',wait_until='networkidle')
                def search():
                    pg.locator('#q').fill('不存在的關鍵字xyz')
                    expect(pg.locator('.entry:visible').count()==0,'empty search result')
                    expect('沒有' in pg.locator('#search-status').inner_text(),'empty status message')
                    pg.locator('#q').fill('tool')
                    expect(pg.locator('.entry:visible').count()>0,'English search has result')
                    pg.locator('#q').fill('')
                    return expect(pg.locator('.entry:visible').count()==6,'search reset: 6 entries')
                record(f'{label}: Wiki search and reset',search)
                def wiki_backlink():
                    pg.locator('#W03 a[href^="slides.html#"]').first.click(); pg.wait_for_url('**/slides.html#slide-*')
                    expect(pg.locator('.slide:not([hidden])').count()==1,'backlink opens one slide')
                    return pg.url.split('/')[-1]
                record(f'{label}: Wiki → slide backlink',wiki_backlink)
                pg.goto(url+'slides.html',wait_until='networkidle')
                def navigation():
                    expect(pg.locator('#prev').is_disabled(),'first page previous disabled')
                    pg.locator('#next').click(); expect(pg.locator('#position').inner_text()=='2 / 10','next button 2/10')
                    pg.locator('#prev').click(); expect(pg.locator('#position').inner_text()=='1 / 10','previous button 1/10')
                    pg.locator('body').click(position={'x':2,'y':2}); pg.keyboard.press('ArrowRight')
                    expect(pg.locator('#position').inner_text()=='2 / 10','ArrowRight advances')
                    pg.keyboard.press('ArrowLeft'); expect(pg.locator('#position').inner_text()=='1 / 10','ArrowLeft reverses')
                    pg.keyboard.press('End'); expect(pg.locator('#position').inner_text()=='10 / 10','End 10/10')
                    expect(pg.locator('#next').is_disabled(),'last page next disabled')
                    expect(pg.locator('#progress').get_attribute('aria-valuenow')=='10','progress aria 10')
                    pg.keyboard.press('Home'); expect(pg.locator('#position').inner_text()=='1 / 10','Home 1/10')
                    pg.keyboard.press('Tab'); return expect(pg.evaluate('document.activeElement.tagName') in ('A','BUTTON'),'keyboard focus reaches controls')
                record(f'{label}: buttons, arrows, Home/End, progress and Tab',navigation)
                def hash_navigation():
                    pg.goto(url+'slides.html#slide-7'); expect(pg.locator('#slide-7').is_visible(),'deep link page 7')
                    pg.evaluate('location.hash="slide-4"'); pg.wait_for_function('document.querySelector("#position").textContent === "4 / 10"')
                    pg.go_back(); pg.wait_for_function('document.querySelector("#position").textContent === "7 / 10"')
                    return 'deep link, hashchange, browser back passed'
                record(f'{label}: URL/hash navigation',hash_navigation)
                for i in range(1,11):
                    pg.goto(url+f'slides.html#slide-{i}',wait_until='load')
                    def slide_layout():
                        active=pg.locator('.slide:not([hidden])')
                        expect(active.count()==1,'exactly one active slide')
                        expect(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),'no horizontal overflow')
                        claims=active.locator('.claim'); expect(claims.count()>=1,'claims present')
                        for claim in claims.all():
                            expect(claim.locator('a[href^="index.html#W"]').count()==1,'Wiki citation')
                            expect(claim.locator('a[href^="index.html#S"]').count()>=1,'source citation')
                        expect(pg.locator('.deck-controls').bounding_box()['y'] >= active.bounding_box()['y']+active.bounding_box()['height']-1,'controls do not overlay content')
                        return f'{claims.count()} claims; citations; controls below content'
                    record(f'{label}: slide {i} layout and citations',slide_layout)
                    if label!='narrow' and i in (4,5,7,9,10):
                        shot=evidence/f'{label}-slide-{i}.png'; pg.screenshot(path=str(shot),full_page=True); report['screenshots'].append(shot.name)
                pg.goto(url+'slides.html#slide-5'); pg.locator('#slide-5 a[href="index.html#W03"]').first.click()
                record(f'{label}: slide → Wiki citation',lambda:expect(pg.url.endswith('index.html#W03') and pg.locator('#W03').is_visible(),'W03 anchor opened'))
                pg.goto(url+'workflow.html')
                record(f'{label}: Graph and real events visible',lambda:expect(pg.locator('svg[role="img"]').count()==1 and pg.locator('tbody tr').count()>=8,'SVG graph and execution rows present'))
                if label=='desktop':
                    pg.goto((directory/'slides.html').as_uri()+'#slide-3',wait_until='load')
                    record('file:// no CDN, slide deep link',lambda:expect(pg.locator('#slide-3').is_visible(),'file slide 3 visible'))
                    pg.locator('#next').click()
                    record('file:// next button',lambda:expect(pg.locator('#slide-4').is_visible(),'file slide 4 visible'))
                context.close()
            browser.close()
    except Exception as e:
        report['checks'].append({'name':'browser infrastructure','passed':False,'error':str(e)})
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)
    for key in ('console_errors','page_errors','failed_requests'):
        report['checks'].append({'name':key,'passed':not report[key],'actual':report[key]})
    report['finished_at']=timestamp(); report['passed']=bool(report['checks']) and all(c['passed'] for c in report['checks'])
    write_json(evidence/'report.json',report)
    return report
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(); parser.add_argument('--directory',type=pathlib.Path,default=ROOT); parser.add_argument('--evidence',type=pathlib.Path); args=parser.parse_args()
    r=check_site(args.directory,args.evidence)
    print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'failed':[c for c in r['checks'] if not c['passed']]},ensure_ascii=False,indent=2))
    sys.exit(0 if r['passed'] else 1)
