"""Signed synthetic D1 global-gate cases with actual pinned Granite vectors.

0/1 thresholds are independently chosen protocol controls, NOT measured release
calibration. Original documents differ in synthetic appendices; identical
canonical excerpts/title/locator intentionally have identical embedding inputs.
Only public ephemeral keys are retained.
"""
import argparse
import json
import shutil
import traceback
import zipfile
from contextlib import ExitStack
from pathlib import Path
import numpy as np
from nacl.signing import SigningKey
from kpack_builder.core import canonical, sha, write_archive
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder, document_input
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query, retrieve
from scripts.v13_query_identifier_fixtures import make_pack

ROOT=Path(__file__).resolve().parents[1]
TEXT='The Aster-9 thermal controller has a maximum continuous operating temperature of 74 °C.'
QUESTION='What is the maximum continuous operating temperature?'

def save(path,value):path.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/relevance-corpus';assert not assets.exists()
    specs=[('a-strict',1,[],None),('b-lenient',0,[],None),('c-uncal',None,[],None),
        ('d-lenient',0,[],None),('e-legacy',0,[],None),('f-exact',1,['EXACTCODE'],None),
        ('g-exact-uncal',None,['EXACTOTHER'],None),('i-duplicate-lenient',0,[],'a-strict')]
    save(run/'source-specifications.json',dict(purpose='SYNTHETIC_PROTOCOL_NOT_MEASURED_CALIBRATION',packs=specs,text=TEXT))
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite');signer=SigningKey.generate();public=bytes(signer.verify_key)
    (run/'public-key.raw').write_bytes(public)
    paths={};records=[];inputs=[]
    for name,threshold,aliases,duplicate in specs:
        original=TEXT+'\nSYNTHETIC original appendix '+(duplicate or name)
        chunks=[dict(id='thermal',title='Aster-9',locator='thermal',text=TEXT,original=original,aliases=aliases)]
        original_path,_=make_pack(run,name,chunks,encoder,signer)
        inputs.append(dict(pack=name,original_sha256=sha(original.encode()),input=document_input('Aster-9','thermal','',TEXT)))
        with zipfile.ZipFile(original_path) as archive:
            manifest=json.loads(archive.read('manifest.json'));payload={item['path']:archive.read(item['path']) for item in manifest['files']}
        if threshold is not None:
            manifest['calibration']=dict(status='CALIBRATED',dataset_sha256=sha(canonical(dict(purpose='SYNTHETIC_FIXED_PROTOCOL_CONTROL',threshold=threshold))),
                method='candidate-relevance-v1.3',min_agreed_dense_cosine=threshold,min_dense_only_cosine=threshold,precision=0,recall=0)
            if name=='e-legacy':del manifest['calibration']['status']
        # Retain original uncalibrated builder transport as provenance, rather than
        # overwriting it. Only this newly signed control transport is activated.
        path=run/(name+'-control.kpack');write_archive(path,manifest,payload,signer);paths[name]=path
        records.append(dict(id=name,filename=path.name,sha256=file_sha(path),threshold=threshold,
            status_field_present=name!='e-legacy',original_builder_transport_sha256=file_sha(original_path)))
    save(run/'embedding-inputs.json',inputs)
    # Expected ordering/flags are fixed from identical excerpt vectors/ranks,
    # pack ID tie-break, exact priority and representative provenance rules.
    scenarios=[
        ('TOP_FAIL_LOWER_PASS',['a-strict','b-lenient'],QUESTION,['a-strict','b-lenient'],[False,False],'NO_RELEVANT_EVIDENCE'),
        ('TOP_UNCAL_LOWER_PASS',['c-uncal','d-lenient'],QUESTION,['c-uncal','d-lenient'],[False,False],'NO_RELEVANT_EVIDENCE'),
        ('TOP_PASS_LOWER_PASS',['b-lenient','d-lenient'],QUESTION,['b-lenient','d-lenient'],[True,False],'ANSWER_ACCEPTED'),
        ('LEGACY_STATUS_DEFAULT',['e-legacy'],QUESTION,['e-legacy'],[True],'ANSWER_ACCEPTED'),
        ('EXACT_THEN_FAIL',['f-exact','a-strict'],'EXACTCODE '+QUESTION,['f-exact','a-strict'],[True,False],'ANSWER_ACCEPTED'),
        ('EXACT_UNCAL_THEN_PASS',['g-exact-uncal','b-lenient'],'EXACTOTHER '+QUESTION,['g-exact-uncal','b-lenient'],[True,True],'ANSWER_ACCEPTED'),
        ('ALL_EXACT',['f-exact','g-exact-uncal'],'EXACTCODE EXACTOTHER '+QUESTION,['f-exact','g-exact-uncal'],[True,True],'ANSWER_ACCEPTED'),
        ('DEDUP_OWN_STRICT',['a-strict','i-duplicate-lenient'],QUESTION,['a-strict'],[False],'NO_RELEVANT_EVIDENCE')]
    save(run/'fixed-expectations.json',[dict(id=i,packs=p,raw=q,expected_order=o,expected_relevant=f,expected_state=s) for i,p,q,o,f,s in scenarios])
    cases=[]
    with ExitStack() as stack:
        packs={name:stack.enter_context(VerifiedPack(path,[public],developer_mode=True)) for name,path in paths.items()}
        assert np.array_equal(packs['a-strict'].vectors,packs['b-lenient'].vectors)
        for identity,names,raw,expected_order,expected_flags,state in scenarios:
            query=Query(raw,'2026-10-09');vector=encoder.encode(query.normalized)
            active=tuple(packs[name] for name in names);actual,ambiguous=retrieve(active,query,vector)
            assert not ambiguous
            assert [c.pack.identity[0].removeprefix('org.packrag.contract.') for c in actual]==expected_order,identity
            assert [c.relevant for c in actual]==expected_flags,identity
            assert all(0<c.dense_cosine<1 for c in actual),identity
            assert retrieve(tuple(reversed(active)),query,vector)==(actual,ambiguous)
            if identity=='DEDUP_OWN_STRICT':assert len(actual[0].origins)==2
            cases.append(dict(id=identity,packs=names,raw=raw,normalized=query.normalized,as_of=query.as_of,query_vector=vector.tolist(),
                expected_order=expected_order,expected_relevant=expected_flags,expected_state=state,expected_ambiguous=False,
                candidates=[dict(pack_id=c.pack.identity[0],chunk_id=c.chunk['chunk_id'],exact=c.exact,relevant=c.relevant,
                    sparse_rank=c.sparse_rank,dense_rank=c.dense_rank,cosine=c.dense_cosine,rrf=c.rrf,origins=[list(o) for o in c.origins]) for c in actual]))
    record=dict(status='FIXED_SIGNED_REFERENCES_NOT_DEVICE_GENERATION_OR_CALIBRATION_ACCEPTANCE',purpose='SYNTHETIC_GLOBAL_GATE_CONTROLS_NOT_MEASURED_CALIBRATION',
        private_seed='EPHEMERAL_NOT_SAVED',script_sha256=file_sha(Path(__file__)),builder_script_sha256=file_sha(ROOT/'scripts/v13_query_identifier_fixtures.py'),
        public_key_sha256=file_sha(run/'public-key.raw'),packs=records,cases=cases,fixed_expectations_sha256=file_sha(run/'fixed-expectations.json'),
        embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),source_specifications_sha256=file_sha(run/'source-specifications.json'),
        fixed_gate_sha256=file_sha(ROOT/'product/tests/fixtures/relevance-contracts.json'))
    save(run/'cases.json',record)
    assets.mkdir()
    for path in [run/'cases.json',run/'public-key.raw',ROOT/'product/tests/fixtures/relevance-contracts.json',*paths.values()]:shutil.copyfile(path,assets/path.name)
    print('Frozen8 signed global-gate scenarios with8 synthetic packs and32 independent gate expectations',flush=True)

if __name__=='__main__':
    try:main()
    except Exception:
        import sys
        if '--run' in sys.argv:
            run=Path(sys.argv[sys.argv.index('--run')+1]).resolve()
            if run.is_relative_to(ROOT) and run.is_dir() and not (run/'failure.txt').exists():(run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
