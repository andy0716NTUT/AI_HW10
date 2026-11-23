"""Prepare an allowlisted deployable static bundle; never includes credentials."""
import hashlib, pathlib, shutil, zipfile
from project_utils import ROOT, timestamp, write_json
from workflow import validate_html
FILES=['index.html','slides.html','workflow.html','assets.css','slides.js','wiki.js','.nojekyll','wiki.json','slides_data.json','retrieval_log.json','execution_log.json','validation.json','README.md','SUBMISSION.md','INGEST_LOG.md','DESIGN_DECISIONS.md','RUN_LOG.md','VALIDATION_REPORT.md','DEPLOYMENT.md','deployment.json','FILE_MANIFEST.json']
def package():
    from materialize_images import materialize_images
    materialize_images()
    dest=ROOT/'dist'; dest.mkdir(exist_ok=True)
    for name in FILES:
        source=ROOT/name
        if source.is_file(): shutil.copy2(source,dest/name)
    for name in ('sources','evidence'):
        shutil.copytree(ROOT/name,dest/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.b64'))
    result=validate_html(dest)
    entries=[{'path':str(p.relative_to(dest)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='package_manifest.json']
    write_json(dest/'package_manifest.json',{'created_at':timestamp(),'files':entries,'validation':result,'deployment_status':'packaged; not evidence of publication'})
    with zipfile.ZipFile(ROOT/'site-deploy.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(dest).as_posix())
    print(f'Package PASS: {len(entries)} files, dist/ and site-deploy.zip; not deployed by this command')
if __name__=='__main__': package()
