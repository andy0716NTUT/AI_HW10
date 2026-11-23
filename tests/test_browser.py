"""Explicit browser suite: python tests/test_browser.py (Chrome + optional Playwright)."""
import pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
if __name__=='__main__':
    from browser_check import check_site
    r=check_site()
    print(f"Browser checks: {sum(c['passed'] for c in r['checks'])}/{len(r['checks'])}")
    for c in r['checks']:
        if not c['passed']: print(c)
    sys.exit(0 if r['passed'] else 1)
