"""Create lossless transport carriers for actual browser screenshots."""
import base64, hashlib
from project_utils import ROOT, write_json
def encode():
    images=[]
    for path in sorted((ROOT/'evidence').rglob('*.png')):
        data=path.read_bytes(); carrier=path.with_suffix('.png.b64')
        carrier.write_text(base64.b64encode(data).decode('ascii'),encoding='ascii')
        images.append({'path':path.relative_to(ROOT).as_posix(),'encoded_path':carrier.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    write_json(ROOT/'evidence/encoded-images.json',{'method':'Lossless base64 transport of actual Chrome PNG evidence. Decode and verify SHA-256 before publication.','images':images})
    print(f'Original PNGs losslessly encoded: {len(images)}')
if __name__=='__main__': encode()
