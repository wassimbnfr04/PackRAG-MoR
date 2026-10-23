"""Frozen document-backed repair evaluation, not final packs or human/held-out gold."""
import argparse
import hashlib
import json
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone
from nacl.signing import SigningKey
from kpack_builder.core import canonical, sha, write_archive
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.trust import load_trust
from product.packrag.retrieval import Query
from product.packrag.runtime import PackRAG
from scripts.v13_query_identifier_fixtures import make_pack
from scripts.v13_smoke import owned_server, save

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'artifacts/v1.3/m4/chat-and-repair-0001'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--prepared',type=Path)
    args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT/'artifacts/v1.3/m4')
    run.mkdir(parents=True,exist_ok=False)
    documents=FROZEN/'repair-documents-frozen-0001.json';goldfile=FROZEN/'repair-cases-frozen-0001.json'
    corpus=json.loads(documents.read_text());gold=json.loads(goldfile.read_text())
    assert gold['document_sha256']==file_sha(documents)
    rows=corpus['documents'];assert len(rows)==2 and len(gold['cases'])==12
    initial={str(p.relative_to(ROOT)):file_sha(p) for p in [documents,goldfile,Path(__file__)]}
    save(run/'inputs.json',dict(status='FROZEN_INPUTS_BEFORE_INFERENCE',started_utc=datetime.now(timezone.utc).isoformat(),sha256=initial,
        purpose='Document-derived factual test digests and frozen procedural/missing-specification/device-mismatch questions. No thermal74 question, no model/threshold/template/weight tuning.',
        limits='Two compact agent-authored digests of published real guides; not complete raw PDF ingestion, manufacturer attestation, genuine human review/calibration or PackBench held-out accuracy.'))
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
    if args.prepared is None:
        # Only signing code reads this known custody file. Never hash, print or export it.
        signer=SigningKey((ROOT/'product/.private/demo-publisher.seed').read_bytes())
        approved=load_trust(ROOT/'product/config/release-trust.json')
        public=bytes(signer.verify_key);assert public in approved
        draft,ids=make_pack(run,'repair-skills',rows,encoder,signer)
        database=run/'repair-skills/knowledge.sqlite'
        acquisitions=json.loads((FROZEN/'repair-source-acquisition-0001.json').read_text())['sources']
        upstream={row['id']:row for row in acquisitions}
        with closing(sqlite3.connect(database)) as db,db:
            for row,source in zip(rows,['fan','tube'],strict=True):
                note=json.dumps(dict(kind='AGENT_AUTHORED_FACTUAL_TEST_DIGEST_NOT_ORIGINAL_MANUAL',upstream_url=row['upstream_url'],
                    upstream_html_sha256=upstream[source]['html_sha256'],original_redistribution_attested=False,
                    scope='Digest wording is original test material; upstream facts referenced. Not a complete manufacturer guide or release licensing/review claim.'))
                db.execute('UPDATE sources SET publisher=?,canonical_uri=?,retrieved_at=?,license=?,source_type=?,notes=? WHERE source_id=?',
                    (row['publisher'],'urn:packrag:m4:test-digest:'+row['id'],'2026-10-12',row['license'],'manual',note,row['source']))
        with zipfile.ZipFile(draft) as z:manifest=json.loads(z.read('manifest.json'));dense=z.read('dense.kdx')
        manifest.update(pack_id='org.packrag.test.repair-skills',name='DOCUMENT-DERIVED REPAIR TEST — NOT RELEASE CALIBRATION',release_timestamp='2026-10-12T00:00:00Z')
        manifest['publisher']['name']='PackRAG project factual test digest publisher'
        manifest['build'].update(builder_version='1.3.0-repair-skill-test',source_manifest_sha256=file_sha(documents))
        packpath=run/'repair-skills.kpack'
        write_archive(packpath,manifest,{'knowledge.sqlite':database.read_bytes(),'dense.kdx':dense},signer)
        (run/'public-key.raw').write_bytes(public)
        with VerifiedPack(packpath,[public],developer_mode=True) as pack:
            assert pack.manifest['calibration']['status']=='UNCALIBRATED'
        save(run/'prepared.json',dict(status='SIGNED_VERIFIED_DEVELOPMENT_TEST_PACK_NOT_RELEASE_OR_SKILL_ACCEPTANCE',
            pack_sha256=file_sha(packpath),pack_file='repair-skills.kpack',public_key_sha256=file_sha(run/'public-key.raw'),
            document_sha256=file_sha(documents),gold_sha256=file_sha(goldfile),chunk_ids=ids,private_seed='LOCAL_CUSTODY_NOT_HASHED_OR_EXPORTED',
            source_scope=corpus['scope'],production_acceptance=False))
    else:
        prepared=args.prepared.resolve();assert prepared.is_relative_to(ROOT/'artifacts/v1.3/m4')
        identity=json.loads((prepared/'prepared.json').read_text());packpath=prepared/identity['pack_file']
        assert file_sha(packpath)==identity['pack_sha256'] and identity['document_sha256']==file_sha(documents) and identity['gold_sha256']==file_sha(goldfile)
        public=(prepared/'public-key.raw').read_bytes()
        save(run/'reused-prepared.json',dict(path=str(prepared.relative_to(ROOT)),prepared_sha256=file_sha(prepared/'prepared.json'),pack_sha256=file_sha(packpath)))
    if args.prepare_only:
        assert args.prepared is None
        print('SIGNED_VERIFIED_FROZEN_REPAIR_TEST_PACK_READY_NOT_INFERENCE_ACCEPTANCE',flush=True)
        return
    results=[]
    with VerifiedPack(packpath,[public],developer_mode=True) as pack,owned_server(run) as generator:
        registry=SessionRegistry();registry.activate(pack);runtime=PackRAG(registry,encoder,generator)
        for case in gold['cases']:
            result=runtime.answer(Query(case['question'],case['as_of']))
            text=(result['answer'] or '').casefold()
            missing=[term for term in case['required_concepts'] if term.casefold() not in text]
            possible_unsupported=[term for term in case['unsupported_concepts'] if term.casefold() in text]
            record=dict(id=case['id'],expected_state=case['expected_state'],state_matches=result['state']==case['expected_state'],
                missing_lexical_concepts=missing,possible_unsupported_phrases=possible_unsupported,result=result,
                review_status='MANUAL_PROCEDURE_ENTAILMENT_AND_ORDER_REVIEW_REQUIRED' if case['manual_review_required'] else 'STATE_CONTROL_SCREENED')
            save(run/(case['id']+'.json'),record);results.append(record)
            # Collect the complete independent benchmark; failures do not become passes or tune later cases.
            print(case['id'],result['state'],'state_match',record['state_matches'],'missing',len(missing),flush=True)
            save(run/'progress.json',dict(status='RUNNING_FROZEN_BENCHMARK_NOT_SKILL_ACCEPTANCE',completed=[r['id'] for r in results]))
    for name,digest in initial.items():assert file_sha(ROOT/name)==digest
    save(run/'results.json',dict(status='COMPLETE_ORIGINAL_REPAIR_OUTPUTS_MANUAL_REVIEW_REQUIRED',cases=results,
        state_controls_pass=sum(r['state_matches'] for r in results),total=len(results),raw_reasoning_persisted=False,
        limits='Structural acceptance/citation checks and lexical screening are not semantic entailment or repair competence. Record procedure order, omitted prerequisites, unsupported instructions and correct source identity manually. No synthetic development calibration or CPU timings promoted to release/phone performance.'))
    print('COMPLETE_ORIGINAL_REPAIR_OUTPUTS_MANUAL_REVIEW_REQUIRED',flush=True)

if __name__=='__main__':main()
