"""Signed extensionless names that resemble admitted extensions, plus valid anchor."""
import argparse,copy,json,shutil,zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical,key_id,sha
from product.packrag.config import file_sha
from scripts.v13_archive_fixtures import archive
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/extension-name-corpus'; assert not assets.exists()
    source=ROOT/'artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack'
    with zipfile.ZipFile(source) as z: payload={n:z.read(n) for n in z.namelist()}
    base=json.loads(payload.pop('manifest.json')); payload.pop('manifest.sig')
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/'public-key.raw').write_bytes(public)
    base['publisher']['key_id']=key_id(public); base['version']='1.3.1+extension-name'; cases=[]
    for name in ['sample.txt','txt','pdf','json','webp']:
        path='sources/'+name; data=dict(payload); data[path]=b'Synthetic extension-name admission fixture.'
        manifest=copy.deepcopy(base); manifest['files']=[dict(path=p,sha256=sha(b),bytes=len(b),required=True,media_type='application/vnd.sqlite3' if p=='knowledge.sqlite' else 'application/octet-stream') for p,b in sorted(data.items())]
        raw=canonical(manifest); out=run/(name+'.kpack'); out.write_bytes(archive(list(sorted(data.items()))+[('manifest.json',raw),('manifest.sig',signer.sign(raw).signature)]))
        cases.append(dict(id=name,filename=out.name,path=path,media_type='application/octet-stream',accept=name=='sample.txt',path_accept=name=='sample.txt',sha256=file_sha(out),manifest_sha256=sha(raw)))
    record=dict(cases=cases,public_key_sha256=file_sha(run/'public-key.raw'),source_pack_sha256=file_sha(source),script_sha256=file_sha(Path(__file__)),private_seed='EPHEMERAL_NOT_SAVED',limits='Synthetic extensionless-name boundary only; no snapshot decoding/source truth/calibration claim.')
    (run/'cases.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8'); shutil.copytree(run,assets); print('Frozen5 signed extension-name cases')
if __name__=='__main__': main()
