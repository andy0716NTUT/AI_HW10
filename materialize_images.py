"""Restore exact PNG evidence from base64 transport files, with SHA-256 checks."""
import base64, hashlib, pathlib
from project_utils import ROOT, read_json
def materialize_images():
    manifest=ROOT/'evidence/encoded-images.json'
    if not manifest.exists(): return 0
    count=0
    for record in read_json(manifest)['images']:
        target=(ROOT/record['path']).resolve(); carrier=(ROOT/record['encoded_path']).resolve()
        if not target.is_relative_to((ROOT/'evidence').resolve()) or not carrier.is_relative_to((ROOT/'evidence').resolve()) or target.suffix!='.png': raise ValueError('Invalid evidence path')
        data=base64.b64decode(carrier.read_text(encoding='ascii'),validate=True)
        if hashlib.sha256(data).hexdigest()!=record['sha256'] or len(data)!=record['bytes']: raise ValueError(f'Image integrity failure: {target.name}')
        if not target.exists() or target.read_bytes()!=data: target.write_bytes(data)
        count+=1
    return count
if __name__=='__main__': print(f'PNG evidence verified/restored: {materialize_images()}')
