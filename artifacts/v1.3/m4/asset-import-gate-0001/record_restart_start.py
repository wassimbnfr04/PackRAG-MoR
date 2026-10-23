"""Durable actual importing-process recovery gate starting state, no result claimed."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'restart-start-0001.json';assert not target.exists()
assert read(HERE/'hardening-native-complete-0001.json')['status']=='PASS_INTEGRATED_F2_HARDENING_ITERATION_NOT_FULL_F2'
old=read(M4/'build-0064/source-at-build-start.json')['files'];new=read(M4/'build-0065/source-at-build-start.json')['files']
delta={name:dict(before=old.get(name),after=value) for name,value in new.items() if old.get(name)!=value}
assert set(old)==set(new) and set(delta)=={'product/android/app/src/androidTest/java/org/packrag/product/LocalAssetImportProcessDeathDeviceTest.kt'}
assert sha(M4/'build-0064/app-debug.apk')==sha(M4/'build-0065/app-debug.apk')
host=read(HERE/'build-0065-capture.json');assert host['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
time=datetime.now(timezone.utc).isoformat()
note=f'Current M4F2 actual process-recovery iteration START at {time}: corrected hardening/native0063 passes28+7 controls, all originals saved/known50 owner guards match. New debug-only unexported AssetImportCrashProbeService uses a bounded-marker-owned UUID root under asset-import-crash, fixed official-template URI, actual importer and binder-triggered worker. It kills only its own separate importing test process at COPYING>0, verified/pre-rename COMMITTING, and post-rename COMMITTED. Main instrumentation/phone/chat stay alive; no owner model/default registry or radio writes. New device test copies only3 actual non-template models once under space guard, seeds deliberately different old template5bytes/legacy partial and exact signed synthetic pack, proves child disconnect/PID distinctions and owned stage/final state before real startup; then actual pinned cold native74°C[S1] after each recovery. Precommit full-correct-stage must be deleted/never promoted and old final must block native until a fresh real URI repair; postcommit exact template must survive without repair. Build0064 host73 passes but is not run physically; pre-execution report refinement0065 makes abandoned-stage field null/not-applicable after commit and syncs probe marker/directory. Only one test source changes, product APK identical0064/65. Build0065 passes73 host/{len(new)} frozen inputs/APK/pins/no INTERNET. Actual device-process-death0001 is starting, no physical PASS yet. This proves importing subprocess loss in one kernel if it passes, not whole-phone/main restart, physical power loss/cache failure, cross-process warm-model leases, all-slot imports/system picker, full F2/M4/product/performance acceptance. F2 all4 artifact imports/ViewModel/picker UI/approved-policy/retained regressions/restoration/custody/closure/checkpoint remain before F3; F3/F4/later software/release/delivery remain. Owner final packs excluded; mobile data on, PackRAG kept closed.'
record=dict(status='F2_ACTUAL_IMPORTING_PROCESS_RECOVERY_STARTING_NOT_ACCEPTED',recorded_utc=time,host_capture_sha256=sha(HERE/'build-0065-capture.json'),
    preexecution_source_delta_0064_to_0065=delta,unchanged_product_sha256=sha(M4/'build-0065/app-debug.apk'),note=note)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'],flush=True)
