"""Close the integrated hardening iteration only; prepare F2 restart/all-slot acceptance."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'hardening-native-complete-0001.json';assert not target.exists()
sequence=read(HERE/'hardening-walking-sequence-0002.json');assert sequence['status']=='PASS_F2_HARDENING_AND_NATIVE_API_REGRESSION_NOT_FULL_F2'
walk=M4/'device-local-asset-import-walking-0003';execution=read(walk/'execution.json');assert execution['status']=='PASS'
actual=read(walk/'original-adb/m4-local-asset-import-walking.json');assert len(actual['cases'])==7
source=read(M4/'build-0063/source-at-build-start.json')['files']
for name,value in source.items():assert sha(ROOT/name)==value,name
raw=(walk/'instrumentation.txt').read_text(encoding='utf-8');seconds=float(re.search(r'Time: ([0-9]+,[0-9]+)',raw).group(1).replace(',','.'))
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 integrated hardening iteration PASS at {time}:0063 host73/frozen{len(source)} inputs, actual fault0002 three methods/28 controls49.491s and fresh native walking0003 seven controls{seconds}s whole-instrumentation. Actual template stream5443/pin/atomic replacement, actual separate-UID one-open/one-close/errors0, foreign warm-model reader exclusion, caller native close and cold answers before/after both74°C[S1] remain working after startup/cleanup/cancel changes. All originals saved before any new build/switch; explicit known50 owner hashes match. These functional observations do not establish M8 performance or arbitrary-provider cancellation. Failed0058 compilation/walking0001/fault0001, unexecuted0061 cleanup review and all partial/scope corrections remain immutable. Next implement actual debug importing-subprocess loss/recovery and full4 real-artifact content-URI imports under prewritten M4F2_RESTART_AND_ALL_SLOT_PREPARATION.md. This is not F2 completion; ViewModel/system-picker/progress/cancel UI, approved-only/retained F1-adjacent regressions/restoration/custody/closure/exact checkpoint still required before F3. F3/F4/later software/release/delivery remain; final packs owner supplied, radio/mobile data unchanged, background PackRAG closed.'
record=dict(status='PASS_INTEGRATED_F2_HARDENING_ITERATION_NOT_FULL_F2',recorded_utc=time,
    sequence_sha256=sha(HERE/'hardening-walking-sequence-0002.json'),native_execution_sha256=sha(walk/'execution.json'),
    native_original_sha256=sha(walk/'original-adb/m4-local-asset-import-walking.json'),native_whole_instrumentation_s=seconds,
    native_answer_before=actual['answer_before'],native_answer_after=actual['answer_after'],note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
