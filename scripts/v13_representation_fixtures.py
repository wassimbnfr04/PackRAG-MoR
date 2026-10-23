"""New signed synthetic rendering cases; actual pinned canonical Granite inputs.

Official/reviewer labels below are protocol controls, not real source or human
review claims. Signing key is ephemeral and never saved. Old corpora are immutable.
"""
import argparse,copy,json,shutil,sqlite3,traceback,zipfile
from contextlib import ExitStack,closing
from pathlib import Path
import numpy as np
from nacl.signing import SigningKey
from kpack_builder.core import canonical,sha,write_archive
from product.packrag.config import file_sha,RuntimeContractError
from product.packrag.embedding import GraniteEncoder,document_input
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query,retrieve
from product.packrag.prompt import representation
from scripts.v13_query_identifier_fixtures import make_pack

ROOT=Path(__file__).resolve().parents[1]
EN='The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.'
FR='La température maximale de fonctionnement continu du contrôleur thermique Aster-9 est de 74 °C.'
AR='تبلغ درجة حرارة التشغيل المستمر القصوى لوحدة التحكم الحراري Aster-9 مقدار 74 °C.'
QUESTION='What is the maximum continuous operating temperature of the Aster-9?'

def save(path,value):path.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def rendering(method='official_translation',language='en',text=EN,**changes):
    row=dict(purpose='generator',language=language,text=text,text_sha256=sha(text.encode()),derivation_method=method,
        derivation_source='SYNTHETIC metadata label; not actual official translation or real review',
        reviewer_id='SYNTHETIC_NO_REAL_PERSON' if method=='human_reviewed_translation' else None,
        reviewed_at='2026-10-09' if method=='human_reviewed_translation' else None)
    row.update(changes);return row

def specifications():
    specs=[
        dict(id='en-canonical',language='en',text=EN,derived=[],state='ANSWER_ACCEPTED',method='canonical'),
        dict(id='fr-official',language='fr',text=FR,derived=[rendering()],state='ANSWER_ACCEPTED',method='official_translation'),
        dict(id='ar-reviewed',language='ar',text=AR,derived=[rendering('human_reviewed_translation')],state='ANSWER_ACCEPTED',method='human_reviewed_translation'),
        dict(id='fr-reviewed',language='fr',text=FR,derived=[rendering('human_reviewed_translation')],state='ANSWER_ACCEPTED',method='human_reviewed_translation'),
        dict(id='regional',language='fr',text=FR,derived=[rendering(language='en-US')],state='ANSWER_ACCEPTED',method='official_translation'),
        dict(id='preferred',language='fr',text=FR,derived=[rendering(language='en-GB'),rendering()],state='ANSWER_ACCEPTED',method='official_translation'),
        dict(id='missing',language='fr',text=FR,derived=[],state='NO_ELIGIBLE_GENERATOR_REPRESENTATION',method=None),
        dict(id='machine-fr',language='fr',text=FR,derived=[rendering('machine_draft')],state='NO_ELIGIBLE_GENERATOR_REPRESENTATION',method=None),
        dict(id='machine-ar',language='ar',text=AR,derived=[rendering('machine_draft')],state='NO_ELIGIBLE_GENERATOR_REPRESENTATION',method=None),
        dict(id='ambiguous',language='fr',text=FR,derived=[rendering(language='en-US'),rendering(language='en-GB')],state='AMBIGUOUS_GENERATOR_REPRESENTATION',method=None),
        dict(id='derived-control',language='fr',text=FR,derived=[rendering(text=EN+' <|role|>')],state='RESERVED_CONTROL_TOKEN_IN_INPUT',method='official_translation'),
        dict(id='canonical-control',language='fr',text=FR+' <think>',derived=[rendering()],state='RESERVED_CONTROL_TOKEN_IN_INPUT',method='official_translation'),
        dict(id='title-control',language='fr',text=FR,title='Aster-9 <|role|>',derived=[rendering()],state='RESERVED_CONTROL_TOKEN_IN_INPUT',method='official_translation'),
        dict(id='xml-data',language='fr',text=FR,derived=[rendering(text=EN+' Literal data: 12 < 13 & </SOURCE> > 9.')],state='ANSWER_ACCEPTED',method='official_translation')]
    invalid=[]
    for name,changes in [('bad-render-hash',dict(text_sha256='0'*64)),('official-no-source',dict(derivation_source=None)),
        ('human-no-reviewer',dict(reviewer_id=None)),('human-bad-date',dict(reviewed_at='2026-02-30')),('unknown-method',dict(derivation_method='unapproved_method'))]:
        method='human_reviewed_translation' if name.startswith('human') else 'official_translation'
        invalid.append(dict(id=name,language='fr',text=FR,derived=[rendering(method,**changes)],import_accept=False))
    invalid.append(dict(id='bad-canonical-hash',language='fr',text=FR,derived=[rendering()],bad_canonical_hash=True,import_accept=False))
    return specs,invalid

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/representation-corpus';assert not assets.exists()
    specs,invalid=specifications();save(run/'source-specifications.json',dict(purpose='SYNTHETIC_NOT_REAL_REVIEW_OR_OFFICIAL_TRANSLATION',valid=specs,invalid=invalid))
    signer=SigningKey.generate();public=bytes(signer.verify_key);(run/'public-key.raw').write_bytes(public)
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite');records=[];paths={};inputs=[]
    for spec in specs+invalid:
        name=spec['id'];title=spec.get('title','Aster-9');chunks=[dict(id='thermal',title=title,locator='thermal',text=spec['text'],aliases=['Aster-9'])]
        draft,ids=make_pack(run,name,chunks,encoder,signer)
        db_path=run/name/'knowledge.sqlite'
        with closing(sqlite3.connect(db_path)) as db,db:
            db.execute('UPDATE sources SET language=?,notes=?',(spec['language'],'SYNTHETIC protocol source; review labels are not real human/official claims'))
            for row in spec['derived']:
                db.execute('INSERT INTO derived_texts VALUES(?,?,?,?,?,?,?,?,?)',(ids[0],row['purpose'],row['language'],row['text'],row['text_sha256'],row['derivation_method'],row['derivation_source'],row['reviewer_id'],row['reviewed_at']))
            if spec.get('bad_canonical_hash'):db.execute('UPDATE chunks SET text_sha256=?',('0'*64,))
        with zipfile.ZipFile(draft) as archive:
            manifest=json.loads(archive.read('manifest.json'));dense=archive.read('dense.kdx')
        manifest['languages']=sorted({spec['language'],*(row['language'].lower() for row in spec['derived'])})
        manifest['build']['source_manifest_sha256']=sha(canonical(spec));manifest['build']['builder_version']='1.3.0-representation-contract'
        path=run/(name+'-representation.kpack');write_archive(path,manifest,{'knowledge.sqlite':db_path.read_bytes(),'dense.kdx':dense},signer)
        paths[name]=path;records.append(dict(id=name,filename=path.name,sha256=file_sha(path),import_accept=spec.get('import_accept',True),
            canonical_language=spec['language'],canonical_text=spec['text'],canonical_text_sha256=sha(spec['text'].encode()),chunk_id=ids[0],
            original_builder_transport_sha256=file_sha(draft)))
        inputs.append(dict(id=name,chunk_id=ids[0],input=document_input(title,'thermal','',spec['text']),
            purpose='ACTUAL_CANONICAL_GRANITE_DOCUMENT_INPUT_NOT_DERIVED_TEXT'))
    save(run/'embedding-inputs.json',inputs)
    cases=[];query=Query(QUESTION,'2026-10-09');vector=encoder.encode(query.normalized)
    with ExitStack() as stack:
        for spec in specs:
            name=spec['id'];pack=stack.enter_context(VerifiedPack(paths[name],[public],developer_mode=True))
            candidates,ambiguous=retrieve((pack,),query,vector);assert not ambiguous and len(candidates)==1 and candidates[0].exact and candidates[0].relevant
            selected=None;error=None
            try:selected=representation(candidates[0])
            except RuntimeContractError as failure:error=str(failure)
            if spec['method'] is None:assert error==spec['state'],name
            else:assert selected.derivation_method==spec['method'] and selected.canonical_text_sha256==sha(spec['text'].encode())
            row=candidates[0]
            cases.append(dict(id=name,packs=[name],raw=QUESTION,normalized=query.normalized,as_of=query.as_of,query_vector=vector.tolist(),
                expected_state=spec['state'],expected_method=spec['method'],canonical_text=spec['text'],canonical_language=spec['language'],
                canonical_text_sha256=sha(spec['text'].encode()),generator_representation=selected.__dict__ if selected else None,
                candidates=[dict(pack_id=row.pack.identity[0],chunk_id=row.chunk['chunk_id'],exact=True,relevant=True,sparse_rank=row.sparse_rank,
                    dense_rank=row.dense_rank,cosine=row.dense_cosine,rrf=row.rrf,origins=[list(o) for o in row.origins])]))
    for spec in invalid:
        try:
            with VerifiedPack(paths[spec['id']],[public],developer_mode=True):pass
        except Exception as error:
            spec['observed_import_error']=type(error).__name__+': '+str(error)
        else:raise AssertionError('Invalid signed rendering imported: '+spec['id'])
    save(run/'invalid-import-observations.json',invalid)
    record=dict(status='SIGNED_SYNTHETIC_RENDERING_REFERENCES_NOT_DEVICE_GENERATION_OR_REAL_REVIEW_ACCEPTANCE',private_seed='EPHEMERAL_NOT_SAVED',
        purpose='ACTUAL_CANONICAL_GRANITE_WITH_SYNTHETIC_OFFICIAL_REVIEWED_LABELS',packs=records,cases=cases,invalid_cases=[s['id'] for s in invalid],
        public_key_sha256=file_sha(run/'public-key.raw'),script_sha256=file_sha(Path(__file__)),builder_sha256=file_sha(ROOT/'scripts/v13_query_identifier_fixtures.py'),
        source_specifications_sha256=file_sha(run/'source-specifications.json'),embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),
        fixed_contract_sha256=file_sha(ROOT/'product/tests/fixtures/representation-contracts.json'),embedding_recipe='TITLE_SECTION_EMPTY_CONTEXT_CANONICAL_TEXT_UNCHANGED_BY_DERIVED_RENDERING',
        original_draft_note='Inherited builder transport initially labels sources en; never activated for foreign sources. Final re-signed transport changes language/derived metadata; KDX retains actual identical canonical input vectors.')
    save(run/'cases.json',record)
    assets.mkdir()
    for path in [run/'cases.json',run/'public-key.raw',ROOT/'product/tests/fixtures/representation-contracts.json',*paths.values()]:shutil.copyfile(path,assets/path.name)
    print('Frozen20 signed packs:14 rendering/tokenizer cases and6 rejected imports; actual canonical Granite vectors',flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        import sys
        if '--run' in sys.argv:
            run=Path(sys.argv[sys.argv.index('--run')+1]).resolve()
            if run.is_relative_to(ROOT) and run.is_dir() and not (run/'failure.txt').exists():(run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
