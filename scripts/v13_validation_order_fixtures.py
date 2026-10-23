"""Frozen signed combined-corruption and double-accumulated KDX norm boundaries."""
import argparse,copy,json,shutil,struct,zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import write_archive,key_id,sha
from product.packrag.config import file_sha
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
    run=args.run.resolve(); assert run.is_relative_to(ROOT); run.mkdir(exist_ok=False,parents=True)
    assets=ROOT/'product/android/app/src/androidTest/assets/validation-order-corpus'; assert not assets.exists()
    source=ROOT/'artifacts/v1.3/m1/smoke-0001/developer-pack/walking-skeleton.kpack'
    with zipfile.ZipFile(source) as z: original={n:z.read(n) for n in z.namelist()}
    base=json.loads(original.pop('manifest.json')); original.pop('manifest.sig')
    signer=SigningKey.generate(); public=bytes(signer.verify_key); (run/'public-key.raw').write_bytes(public)
    base['publisher']['key_id']=key_id(public); base['version']='1.2.0+phase-order'
    records=[]
    def pack(identity,accept,contains=None,changes=None,before_db=False):
        payload={**original,**(changes or {})}; path=run/(identity+'.kpack')
        write_archive(path,copy.deepcopy(base),payload,signer)
        with zipfile.ZipFile(path) as z: raw=z.read('manifest.json')
        records.append(dict(id=identity,filename=path.name,accept=accept,error_contains=contains,before_db=before_db,sha256=file_sha(path),manifest_sha256=sha(raw)))
    pack('valid',True)
    broken=b'NOT_A_SQLITE_DB!!'+original['knowledge.sqlite'][16:]
    magic=bytearray(original['dense.kdx']); magic[0]^=1
    nan=bytearray(original['dense.kdx']); struct.pack_into('<f',nan,84,float('nan'))
    pack('broken-db-and-bad-kdx-magic',False,'Invalid KDX header',{'knowledge.sqlite':broken,'dense.kdx':bytes(magic)},True)
    pack('broken-db-and-nonfinite-kdx',False,'Nonfinite KDX vector',{'knowledge.sqlite':broken,'dense.kdx':bytes(nan)},True)
    mapping=bytearray(original['dense.kdx']); mapping[52]^=1
    pack('mapping-binding-after-validated-db',False,'KDX profile/mapping hash mismatch',{'dense.kdx':bytes(mapping)})
    pack('broken-db-after-valid-kdx',False,changes={'knowledge.sqlite':broken})
    for name,value,accept in [('upper-inside',1.01,True),('upper-outside',1.01000011,False),('lower-inside',.99,True),('lower-outside',.98999989,False)]:
        data=bytearray(original['dense.kdx']); struct.pack_into('<384f',data,84,value,*([0.0]*383))
        pack('norm-'+name,accept,None if accept else 'KDX vector norm mismatch',{'dense.kdx':bytes(data)},not accept)
    record=dict(cases=records,public_key_sha256=file_sha(run/'public-key.raw'),source_pack_sha256=file_sha(source),script_sha256=file_sha(Path(__file__)),private_seed='EPHEMERAL_NOT_SAVED',purpose='SYNTHETIC_VALIDATION_PHASE_ORDER_AND_NORM_BOUNDARIES_NOT_RELEASE_CALIBRATION')
    (run/'cases.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8'); shutil.copytree(run,assets)
    print('Frozen signed ordering/norm cases:',len(records))
if __name__=='__main__': main()
