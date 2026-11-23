"""Verify published package against the actual server-returned artifact manifest."""
import argparse, concurrent.futures, hashlib, urllib.parse, urllib.request
from project_utils import ROOT, timestamp, write_json
def verify(base):
    import json
    base=base.rstrip('/')+'/'
    with urllib.request.urlopen(base+'package_manifest.json',timeout=30) as r:
        manifest=json.load(r)
    def fetch(item):
        path=item['path']; url=urllib.parse.urljoin(base,urllib.parse.quote(path,safe='/'))
        if not url.startswith(base): raise ValueError('Manifest path escapes site')
        result={'path':path}
        try:
            with urllib.request.urlopen(url,timeout=30) as r:
                data=r.read(); result.update(http_status=r.status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            result['passed']=result['http_status']==200 and len(data)==item['bytes'] and result['sha256']==item['sha256']
        except Exception as e: result.update(passed=False,error=str(e))
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(fetch,manifest['files']))
    report={'checked_at':timestamp(),'base_url':base,'manifest_created_at':manifest['created_at'],'checks':results,'passed':bool(results) and all(r['passed'] for r in results)}
    write_json(ROOT/'evidence/public-http.json',report)
    print(f'Public HTTP and SHA-256: {sum(r["passed"] for r in results)}/{len(results)}')
    for r in results:
        if not r['passed']: print(r)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('base_url'); args=p.parse_args()
    raise SystemExit(0 if verify(args.base_url)['passed'] else 1)
