import datetime, hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def timestamp(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def read_json(path): return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
def write_json(path,data):
    path=pathlib.Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def digest(data): return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def log_progress(message, root=ROOT):
    with (root/'RUN_LOG.md').open('a',encoding='utf-8') as f: f.write(f'\n- {timestamp()} — {message}\n')
