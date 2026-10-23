"""Fresh signed NEL presence cases; no real review/official-source claims."""
import argparse,json,shutil,sqlite3,traceback,zipfile
from contextlib import closing
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical,sha,write_archive,PackError
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder,document_input
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query,retrieve
from product.packrag.prompt import representation
from scripts.v13_query_identifier_fixtures import make_pack
from scripts.v13_representation_fixtures import FR,EN,QUESTION,rendering
ROOT=Path(__file__).resolve().parents[1]
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/source-text-corpus';assert not assets.exists()
    specs=[dict(id='bad-source-nel',text=FR,derived=rendering(derivation_source='\u0085'),accept=False),
        dict(id='bad-reviewer-nel',text=FR,derived=rendering('human_reviewed_translation',reviewer_id='\u0085'),accept=False),
        dict(id='bad-render-nel',text=FR,derived=rendering(text='\u0085'),accept=False),
        dict(id='bad-canonical-nel',text='\u0085',derived=rendering(),accept=False),
        dict(id='good-source-nel',text=FR,derived=rendering(derivation_source='\u0085SYNTHETIC_NOT_ACTUAL_OFFICIAL_SOURCE\u0085'),accept=True),
        dict(id='good-reviewer-nel',text=FR,derived=rendering('human_reviewed_translation',reviewer_id='\u0085SYNTHETIC_NO_REAL_PERSON\u0085'),accept=True)]
    save(run/'source-specifications.json',dict(purpose='SYNTHETIC_NEL_PRESENCE_BOUNDARY_NOT_REAL_REVIEW',cases=specs))
    signer=SigningKey.generate();public=bytes(signer.verify_key);(run/'public-key.raw').write_bytes(public)
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite');query=Query(QUESTION,'2026-10-09');vector=encoder.encode(query.normalized)
    records=[];inputs=[]
    for spec in specs:
        name=spec['id'];draft,ids=make_pack(run,name,[dict(id='thermal',title='Aster-9',locator='thermal',text=spec['text'],aliases=['Aster-9'])],encoder,signer)
        database=run/name/'knowledge.sqlite';row=spec['derived']
        with closing(sqlite3.connect(database)) as db,db:
            db.execute('UPDATE sources SET language=?,notes=?',('fr','SYNTHETIC presence protocol, not real review'))
            db.execute('INSERT INTO derived_texts VALUES(?,?,?,?,?,?,?,?,?)',(ids[0],row['purpose'],row['language'],row['text'],row['text_sha256'],row['derivation_method'],row['derivation_source'],row['reviewer_id'],row['reviewed_at']))
        with zipfile.ZipFile(draft) as archive:manifest=json.loads(archive.read('manifest.json'));dense=archive.read('dense.kdx')
        manifest['languages']=['en','fr'];manifest['build']['source_manifest_sha256']=sha(canonical(spec));manifest['build']['builder_version']='1.3.0-source-presence-contract'
        path=run/(name+'-source-text.kpack');write_archive(path,manifest,{'knowledge.sqlite':database.read_bytes(),'dense.kdx':dense},signer)
        record=dict(id=name,filename=path.name,sha256=file_sha(path),accept=spec['accept'],canonical_text=spec['text'],canonical_text_sha256=sha(spec['text'].encode()),
            chunk_id=ids[0],original_builder_transport_sha256=file_sha(draft),expected_derived=row)
        try:
            with VerifiedPack(path,[public],developer_mode=True) as pack:
                assert spec['accept'],name
                candidates,ambiguous=retrieve((pack,),query,vector);assert not ambiguous and len(candidates)==1
                selected=representation(candidates[0]);assert selected.text==EN and selected.derivation_source==row['derivation_source'] and selected.reviewer_id==row['reviewer_id']
                record['generator_representation']=selected.__dict__
        except PackError as error:
            assert not spec['accept'],name;record['observed_import_error']=type(error).__name__+': '+str(error)
        records.append(record);inputs.append(dict(id=name,chunk_id=ids[0],input=document_input('Aster-9','thermal','',spec['text'])))
    save(run/'embedding-inputs.json',inputs)
    reference=dict(status='SIGNED_SYNTHETIC_PRESENCE_FIXTURES_NOT_DEVICE_OR_REAL_REVIEW_ACCEPTANCE',packs=records,raw=QUESTION,normalized=query.normalized,as_of=query.as_of,query_vector=vector.tolist(),
        script_sha256=file_sha(Path(__file__)),builder_sha256=file_sha(ROOT/'scripts/v13_query_identifier_fixtures.py'),rendering_helper_sha256=file_sha(ROOT/'scripts/v13_representation_fixtures.py'),
        fixed_contract_sha256=file_sha(ROOT/'product/tests/fixtures/source-text-contracts.json'),public_key_sha256=file_sha(run/'public-key.raw'),
        source_specifications_sha256=file_sha(run/'source-specifications.json'),embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),private_seed='EPHEMERAL_NOT_SAVED',
        original_draft_note='Inherited builder initially labels en; intermediates never activated. Final newly signed transports declare fr; actual canonical KDX inputs remain unchanged. Inherited6 October release/retrieval dates are synthetic controls; construction9 October.')
    save(run/'cases.json',reference);assets.mkdir()
    for path in [run/'cases.json',run/'public-key.raw',ROOT/'product/tests/fixtures/source-text-contracts.json',*[run/r['filename'] for r in records]]:shutil.copyfile(path,assets/path.name)
    print('Signed6 NEL presence cases:4 rejected imports/2 byte-preserving accepted controls',flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        import sys
        if '--run' in sys.argv:
            run=Path(sys.argv[sys.argv.index('--run')+1]).resolve()
            if run.is_relative_to(ROOT) and run.is_dir():(run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
