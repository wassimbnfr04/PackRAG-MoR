"""Hash-bound interpretation correction; originals unchanged, not a new experiment."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];M4=ROOT/'artifacts/v1.3/m4'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',type=Path,required=True);a=p.parse_args()
    run=a.run.resolve();target=a.target.resolve();assert run.is_relative_to(M4) and target.is_relative_to(M4) and not target.exists()
    manifest=read(run/'instrumentation-manifest.json');assert manifest['status']=='PASS'
    collection=read(run/'collected-results.json');assert collection['status']=='PASS'
    source=run/'original-adb/m4-selection-runtime.json';assert digest(source)==collection['saved_sha256']['m4-selection-runtime.json']
    original=read(source);assert original['status']=='PASS' and len(original['cases'])==8
    old='total_ms_including_initialization_not_benchmark';new='runtime_call_ms_excluding_encoder_generator_construction'
    rows=[]
    for case in original['cases']:
        assert old in case and new not in case
        row=dict(case);row[new]=row.pop(old);rows.append(row)
        assert {k:v for k,v in case.items() if k!=old}=={k:v for k,v in row.items() if k!=new}
    target.write_text(json.dumps(dict(status='INTERPRETATION_CORRECTION_NOT_NEW_EXPERIMENT_OR_BENCHMARK',recorded_utc=datetime.now(timezone.utc).isoformat(),
        original_source=str(source.relative_to(ROOT)),original_bytes_sha256=digest(source),normalizer_sha256=digest(Path(__file__)),apk_sha256=manifest['apk_sha256'],
        only_renamed_field=dict(before=old,after=new),scope='Direct PackRag.ask elapsed time excludes externally constructed encoder/backend/model verification/load; includes per-call retrieval/tokenizer/generation/validation. Whole JUnit duration includes all test work.',
        cases=rows),indent=2)+'\n');assert digest(source)==collection['saved_sha256']['m4-selection-runtime.json']
    print('TIMING_INTERPRETATION_CORRECTION_SAVED_ORIGINAL_UNCHANGED')
if __name__=='__main__':main()
