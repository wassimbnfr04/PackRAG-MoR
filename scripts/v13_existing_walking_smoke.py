"""Real retained walking smoke reusing the immutable signed pack; no pack authoring.

Use during the owner's knowledge-pack development hold. Corruption is a local
negative-control copy of existing bytes, never a new content/source fixture.
"""
import argparse
import json
from pathlib import Path
import traceback
import zipfile
from datetime import datetime, timezone

from kpack_builder.core import PackError
from product.packrag.config import LOCK, file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack, SessionRegistry
from product.packrag.retrieval import Query
from product.packrag.runtime import PackRAG
from scripts.v13_result_manifest import public_source_files
from scripts.v13_smoke import ROOT, owned_server, save


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True,type=Path);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT/'artifacts/v1.3/m4');run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/'product/android/app/src/androidTest/assets'
    archive=asset/'walking-skeleton.kpack';public=(asset/'developer-public-key.raw').read_bytes()
    expected_pack='19da286b9f0860c312dc8d14ce0ee8681bf12ca092a7b8a12171fd86abe02c7f'
    assert file_sha(archive)==expected_pack
    source={p.relative_to(ROOT).as_posix():file_sha(p) for p in public_source_files(ROOT)}
    save(run/'inputs.json',dict(started_at=datetime.now(timezone.utc).isoformat(),source_sha256=source,
        runtime_lock=LOCK,existing_pack_sha256=expected_pack,public_key_sha256=file_sha(asset/'developer-public-key.raw'),
        content_policy='EXISTING_IMMUTABLE_PACK_NO_AUTHORING',historical_input_sha256=file_sha(ROOT/'gates/g0/g0_v1.jsonl')))
    results=[];status='FAIL'
    try:
        encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
        original=[json.loads(line) for line in (ROOT/'gates/g0/g0_v1.jsonl').read_text(encoding='utf-8').splitlines()][:10]
        with VerifiedPack(archive,[public],developer_mode=True) as pack,owned_server(run) as generator:
            registry=SessionRegistry();runtime=PackRAG(registry,encoder,generator)
            def record(identity,query,state,fact=None):
                answer=runtime.answer(query)
                passed=answer['state']==state and (fact.casefold() in (answer['answer'] or '').casefold() if fact else answer['answer'] is None)
                item=dict(case_id=identity,passed=passed,expected_state=state,expected_fact=fact,result=answer)
                results.append(item);save(run/(identity+'.json'),item)
                print(identity,answer['state'],'PASS' if passed else 'FAIL',flush=True)
                assert passed,identity
            record('NO_PACK',Query('Aster-9 temperature?','2026-10-05'),'NO_ACTIVE_PACK')
            registry.activate(pack)
            for case,fact in zip(original,['74','600','LiFePO4','three','18','20%','8','12','80','99.999%'],strict=True):
                record(case['case_id'],Query(case['question'],'2026-10-05'),'ANSWER_ACCEPTED',fact)
            record('UNRELATED',Query('Who won the most recent football championship?','2026-10-05'),'NO_RELEVANT_EVIDENCE')
            record('EXACT_NOT_SUFFICIENT',Query('What is the Aster-9 controller purchase price?','2026-10-05'),'INSUFFICIENT_EVIDENCE')
            corrupt=run/'corruption-negative-control.kpack'
            with zipfile.ZipFile(archive) as source_zip,zipfile.ZipFile(corrupt,'w') as target:
                for entry in source_zip.infolist():
                    payload=source_zip.read(entry.filename)
                    if entry.filename=='dense.kdx':payload=payload[:-1]+bytes([payload[-1]^1])
                    target.writestr(entry,payload)
            try:
                with VerifiedPack(corrupt,[public],developer_mode=True):pass
            except PackError as error:results.append(dict(case_id='PAYLOAD_CORRUPTION',passed=True,error=str(error)))
            else:raise AssertionError('Corrupt payload activated')
        assert all(file_sha(ROOT/name)==value for name,value in source.items()),'Source changed during smoke'
        assert file_sha(archive)==expected_pack
        status='PASS'
    except Exception:
        (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        save(run/'smoke-results.json',dict(status=status,cases=results,purpose='D3_EXISTING_SYNTHETIC_WALKING_NOT_RELEASE_OR_PACKBENCH',
            pack_created=False,limitations=['Existing uncalibrated exact-alias pack','Structural citations are not semantic sufficiency proof',
                'Desktop WSL CPU, not physical acceptance','No raw reasoning persisted','Corruption copy only; no new knowledge content']))
        save(run/'output-hashes.json',{p.relative_to(run).as_posix():file_sha(p) for p in run.rglob('*') if p.is_file() and p.name!='output-hashes.json'})
    print('Existing signed walking PASS:',len(results),flush=True)


if __name__=='__main__':main()
