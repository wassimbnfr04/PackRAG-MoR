"""Freeze authenticated data-type admission cases without persisting a signer seed."""
import argparse
import copy
import json
import shutil
import zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, sha
from product.packrag.config import file_sha
from scripts.v13_archive_fixtures import archive

ROOT = Path(__file__).resolve().parents[1]
# Independent frozen expected policy, shared by Python/JVM/device tests.
TYPES = dict(txt="text/plain", md="text/markdown", pdf="application/pdf", csv="text/csv",
             tsv="text/tab-separated-values", json="application/json", xml="application/xml",
             png="image/png", jpg="image/jpeg", jpeg="image/jpeg", webp="image/webp")

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run', type=Path, required=True); args = parser.parse_args()
    run = args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(parents=True, exist_ok=False)
    assets = ROOT/'product/android/app/src/androidTest/assets/data-type-corpus'; assert not assets.exists()
    source = ROOT/'artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack'
    with zipfile.ZipFile(source) as z: payload = {n:z.read(n) for n in z.namelist()}
    base = json.loads(payload.pop('manifest.json')); payload.pop('manifest.sig')
    signer = SigningKey.generate(); public = bytes(signer.verify_key); (run/'public-key.raw').write_bytes(public)
    base['publisher']['key_id'] = key_id(public); base['version'] = '1.3.0+data-type'
    cases = []
    def add(identity, path, mime, accept, path_accept=True):
        data = dict(payload); data[path] = b'Synthetic admission bytes; no document decoding or source truth claim.'
        manifest = copy.deepcopy(base)
        manifest['files'] = [dict(path=p, sha256=sha(b), bytes=len(b), required=True,
            media_type=mime if p==path else ('application/vnd.sqlite3' if p=='knowledge.sqlite' else 'application/octet-stream')) for p,b in sorted(data.items())]
        raw = canonical(manifest); output = run/(identity+'.kpack')
        output.write_bytes(archive(list(sorted(data.items()))+[('manifest.json',raw),('manifest.sig',signer.sign(raw).signature)]))
        cases.append(dict(id=identity, filename=output.name, path=path, media_type=mime, accept=accept,
                          path_accept=path_accept, sha256=file_sha(output), manifest_sha256=sha(raw)))
    for ext,mime in TYPES.items():
        add('allow-'+ext, 'sources/sample.'+ext, mime, True)
        add('opaque-'+ext, 'sources/sample.'+ext, 'application/octet-stream', True)
    add('uppercase-data', 'sources/SAMPLE.PDF', 'Application/PDF', True)
    for ext in ['lua','kt','swift','weirdscript','bin','html','svg','docm','zip','onnx','gguf','exe','py']:
        add('deny-'+ext, 'sources/sample.'+ext, 'application/octet-stream', False, False)
    add('deny-extensionless', 'sources/sample', 'text/plain', False, False)
    for identity,path,mime in [('script-mime','sources/sample.txt','text/x-python'),
            ('model-mime','sources/sample.json','application/x-onnx'),
            ('wrong-data-mime','sources/sample.pdf','image/png'),
            ('sqlite-script-mime','knowledge.sqlite','application/x-executable'),
            ('kdx-script-mime','dense.kdx','application/javascript')]:
        # Core MIME negatives replace only their signed metadata, not the valid core bytes.
        if path in payload:
            # add() creates arbitrary bytes; preserve them afterward by constructing here.
            manifest = copy.deepcopy(base)
            manifest['files'] = [dict(path=p,sha256=sha(b),bytes=len(b),required=True,
                media_type=mime if p==path else ('application/vnd.sqlite3' if p=='knowledge.sqlite' else 'application/octet-stream')) for p,b in sorted(payload.items())]
            raw=canonical(manifest); output=run/(identity+'.kpack')
            output.write_bytes(archive(list(sorted(payload.items()))+[('manifest.json',raw),('manifest.sig',signer.sign(raw).signature)]))
            cases.append(dict(id=identity,filename=output.name,path=path,media_type=mime,accept=False,path_accept=True,sha256=file_sha(output),manifest_sha256=sha(raw)))
        else: add(identity,path,mime,False)
    record = dict(cases=cases, source_types=TYPES, public_key_sha256=file_sha(run/'public-key.raw'),
                  source_pack_sha256=file_sha(source), script_sha256=file_sha(Path(__file__)),
                  private_seed='EPHEMERAL_NOT_SAVED',
                  limits='Synthetic signed path/MIME admission only; snapshots are not decoded, executed or claimed as genuine source documents/calibration.')
    (run/'cases.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8'); shutil.copytree(run,assets)
    print('Frozen signed data-type cases:',len(cases))

if __name__=='__main__': main()
