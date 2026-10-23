"""Versioned D1 references: unchanged signed packs and stored measured vectors.

This is orchestration, not new encoder inference or release calibration. Old
references and historical outputs are never edited. Only the two all-exact
overflow pools deliberately grow from their old local cap to global32.
"""
import argparse
import copy
import json
import traceback
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

import numpy as np
from product.packrag.config import file_sha
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query, retrieve, retrieve_pack

ROOT=Path(__file__).resolve().parents[1]

def save(path, value):
    path.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();run=args.run.resolve();assert run.is_relative_to(ROOT)
    run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/relevance-reference-corpus'
    assert not assets.exists()
    gate_path=ROOT/'artifacts/v1.3/m4/conflict-gate-0001/gate.json'
    gate=json.loads(gate_path.read_text(encoding='utf-8'))
    identities={**gate['source_sha256'],**gate['output_sha256']}
    changes=[];historical={}
    for kind,directory,old_asset in [('query','query-identifier-fixtures-0001','query-identifier-corpus'),('conflict','conflict-fixtures-0001','conflict-corpus')]:
        corpus=ROOT/'artifacts/v1.3/m4'/directory;path=corpus/'cases.json'
        reference=json.loads(path.read_text(encoding='utf-8'))
        name=path.relative_to(ROOT).as_posix()
        # B2 reference is bound through its unchanged Android copy in C2b.
        bound='product/android/app/src/androidTest/assets/'+old_asset+'/cases.json'
        assert file_sha(path)==identities[bound]
        historical[name]=file_sha(path)
        keys=reference.get('public_keys',[dict(filename='public-key.raw',sha256=reference.get('public_key_sha256'))])
        public=[]
        for row in keys:
            key=corpus/row['filename'];assert file_sha(key)==row['sha256'];public.append(key.read_bytes())
            historical[key.relative_to(ROOT).as_posix()]=file_sha(key)
        new=copy.deepcopy(reference)
        with ExitStack() as stack:
            packs={}
            for row in reference['packs']:
                archive=corpus/row['filename'];assert file_sha(archive)==row['sha256']
                historical[archive.relative_to(ROOT).as_posix()]=file_sha(archive)
                packs[row['id']]=stack.enter_context(VerifiedPack(archive,public,developer_mode=True))
            for case,target in zip(reference['cases'],new['cases'],strict=True):
                query=Query(case['raw'],case['as_of'],case.get('jurisdiction'),case.get('current_law',False))
                vector=np.asarray(case['query_vector'],dtype=np.float32)
                active=tuple(packs[name] for name in case['packs'])
                actual,ambiguous=retrieve(active,query,vector)
                assert ambiguous==case['expected_ambiguous'],case['id']
                reverse,reverse_ambiguity=retrieve(tuple(reversed(active)),query,vector)
                assert reverse==actual and reverse_ambiguity==ambiguous
                overflow=case['id'] in ('AMBIGUITY_BEFORE_LOCAL_CAP','BEFORE_CAP')
                # Independently fixed change: >=43 exact eligible hits, all locally
                # retained, then global32. All other original fixture counts stay.
                assert len(actual)==(32 if overflow else len(case['candidates'])),case['id']
                if case.get('expected_locators') is not None:
                    assert {c.pack.identity[0].split('.')[-1]+'/'+c.chunk['locator'] for c in actual}==set(case['expected_locators'])
                base={c.origin_key:c for pack in active for c in retrieve_pack(pack,query,vector,limit=False)[0]}
                old_rows={(r['pack_id'],r['chunk_id']):r for r in case['candidates']}
                rows=[]
                for item in actual:
                    original=base[item.origin_key]
                    assert (item.sparse_rank,item.dense_rank,item.rrf,item.dense_cosine)==(original.sparse_rank,original.dense_rank,original.rrf,original.dense_cosine)
                    # Original packs are uncalibrated: only exact may be relevant.
                    assert item.relevant==item.exact
                    row=dict(pack_id=item.pack.identity[0],chunk_id=item.chunk['chunk_id'],exact=item.exact,relevant=item.relevant,
                        sparse_rank=item.sparse_rank,dense_rank=item.dense_rank,rrf=item.rrf,origins=[list(o) for o in item.origins])
                    row['cosine' if kind=='conflict' else 'dense_cosine']=item.dense_cosine
                    if kind=='conflict':
                        row['locator']=item.chunk['locator']
                        row['conflicts']=json.loads(json.dumps([asdict(d) for d in item.conflicts]))
                    previous=old_rows.get((row['pack_id'],row['chunk_id']))
                    if previous is not None:
                        assert row==json.loads(json.dumps(previous)),(case['id'],'retained field changed')
                    rows.append(row)
                if not overflow:assert rows==case['candidates'],(case['id'],'unexpected ordering change')
                else:
                    assert ambiguous and all(c.exact for c in actual)
                    local=[c for pack in active for c in retrieve_pack(pack,query,vector)[0]]
                    lost={'lost'} if kind=='query' else {'lost-old','lost-new'}
                    assert len(local)>32 and all(any(c.chunk['locator']==name for c in local) for name in lost)
                    assert not any(c.chunk['locator'] in lost for c in actual)
                    changes.append(dict(kind=kind,id=case['id'],old_count=len(case['candidates']),new_count=32,
                        rationale='All exact hits survive local fused16; global32 still discards lost interpretation, but full eligible alias ambiguity remains true.'))
                target['candidates']=rows
        new['status']='D1_REFERENCES_FROZEN_NOT_PHONE_ENCODER_OR_GENERATION_ACCEPTANCE'
        new['reference_derivation']=dict(previous_reference_sha256=file_sha(path),accepted_c2b_gate_sha256=file_sha(gate_path),
            script_sha256=file_sha(Path(__file__)),query_vectors='UNCHANGED_STORED_ACTUAL_GRANITE_NOT_NEW_DESKTOP_INFERENCE',
            deliberate_change='exact union independently ranked fused16, dedup, global32, then relevance')
        save(run/(kind+'-reference.json'),new)
    for name,expected in historical.items():assert file_sha(ROOT/name)==expected
    save(run/'reference-provenance.json',dict(status='FROZEN_NOT_DEVICE_ACCEPTANCE',history_sha256=historical,
        changes=changes,script_sha256=file_sha(Path(__file__)),gate_sha256=file_sha(gate_path)))
    assets.mkdir()
    for name in ('query-reference.json','conflict-reference.json','reference-provenance.json'):
        (assets/name).write_bytes((run/name).read_bytes())
    print(json.dumps(changes,indent=2))

if __name__=='__main__':
    try:main()
    except Exception:
        import sys
        if '--run' in sys.argv:
            failed=Path(sys.argv[sys.argv.index('--run')+1]).resolve()
            if failed.is_relative_to(ROOT) and failed.is_dir() and not (failed/'failure.txt').exists():
                (failed/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
