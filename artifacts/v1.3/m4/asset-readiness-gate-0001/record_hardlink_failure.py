"""Preserve actual failed setup and the single completed negative method before repair."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
run=ROOT/'artifacts/v1.3/m4/device-local-assets-0001';target=HERE/'hardlink-setup-failure.json';assert not target.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(run/'instrumentation-manifest.json')['status']=='FAIL'
text=(run/'instrumentation.txt').read_text(encoding='utf-8')
assert 'Tests run: 3,  Failures: 2' in text and 'java.nio.file.AccessDeniedException' in text and 'UnixFileSystemProvider.createLink' in text
assert 'test=missingCorruptAndSymlinkPathsRejectBeforeAnyNativeInitialization\nINSTRUMENTATION_STATUS_CODE: 0' in text.replace('\r','')
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR'];name='m4-local-assets-negative.json'
argv=adb+['exec-out','run-as','org.packrag.product','cat','files/'+name]
out=subprocess.run(argv,capture_output=True,check=True,timeout=30);data=json.loads(out.stdout)
assert data['status']=='PASS' and len(data['cases'])==5 and data['guards_unchanged']
folder=run/'partial-collected-results';folder.mkdir(exist_ok=False);(folder/name).write_bytes(out.stdout)
dfargv=adb+['shell','df','-k','/data'];df=subprocess.run(dfargv,capture_output=True,text=True,check=True,timeout=30)
record=dict(status='FAIL_TWO_ACTUAL_HARDLINK_SETUP_METHODS_ONE_COMPLETED_NEGATIVE_ORIGINAL_PRESERVED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    instrumentation_manifest_sha256=sha(run/'instrumentation-manifest.json'),instrumentation_sha256=sha(run/'instrumentation.txt'),
    partial_original=dict(argv=argv,returncode=out.returncode,stderr=out.stderr.decode('utf-8',errors='replace'),file=name,sha256=hashlib.sha256(out.stdout).hexdigest(),cases=5),
    storage=dict(argv=dfargv,returncode=df.returncode,stdout=df.stdout,stderr=df.stderr),
    diagnosis='Both failures occur in test-only Files.createLink before actual positive model verification/generation. Android reports AccessDeniedException. The underlying denial mechanism is not inferred. Do not skip controls, alter app permissions/root/device security or claim a product-generation failure.',
    scope='Overall run remains FAIL; only the completed negative method is a partial PASS. Missing-status assertions reached in the failed ViewModel method do not constitute complete method acceptance.')
# Exact independent arithmetic, not a guessed size.
record['copy_required_bytes']=1593894944+5443+25301672+390004608
record['repair']='Use independently owned byte copies guarded by measured private free space >= exact sum '+str(record['copy_required_bytes'])+' bytes plus64MiB. Only copied template is mutated; sessions close before no-follow owned-root cleanup. Fresh APKs/full three-method retry required.'
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note='F1 first device run on0055: three methods/two failures in20.859s. Actual Files.createLink AccessDeniedException blocks both positive setups before generation. One completed negative method/five cases and original JSON preserved separately; overall FAIL unchanged. Repair uses necessary owned copies of all four pinned assets after measured free-space guard; no owner asset mutation or permission/root change. Fresh builds and full retry required. UI guard also rejects symlink directories before traversal; no UI run has occurred.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;heading,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(heading+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'])
