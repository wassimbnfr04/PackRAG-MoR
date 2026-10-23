"""F2 Android URI/path/cancellation iteration; originals precede any next APK/test phase."""
import argparse,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);args=parser.parse_args()
build=M4/args.build;run=M4/args.run;assert build.parent==M4 and run.parent==M4 and not run.exists()
target=HERE/(args.run+'-execution.json');assert not target.exists()
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
assert host['host_xml_totals']==dict(tests=73,failures=0,errors=0,skipped=0)
variant=host['variant'];sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
files=['m4-local-asset-import-uri-faults.json','m4-local-asset-import-provider-cancel.json','m4-local-asset-import-path-recovery.json']
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(build),'--run',str(run),
     '--class-name','org.packrag.product.LocalAssetImportFaultDeviceTest','--result-file',files[0],'--timeout','1200','--variant',variant],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],
    [sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known-guard.json']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),build=args.build,run=args.run,variant=variant,
    runner_sha256=sha(Path(__file__)),host_capture_sha256=sha(HERE/(args.build+'-capture.json')),commands=[])
try:
    for i,command in enumerate(commands):
        print(args.run,'stage',i,'START',flush=True);start=datetime.now(timezone.utc).isoformat()
        with (HERE/(args.run+f'-stage-{i}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{i}.stderr.txt')).open('xb') as err:
            result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=command,started_utc=start,finished_utc=datetime.now(timezone.utc).isoformat(),returncode=result.returncode))
        target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert result.returncode==0,'Hold F2/later increments; preserve original failure and any completed passing originals'
        print(args.run,'stage',i,'PASS',flush=True)
    expected=read(HERE/'before.json')['owner_public_file_sha256']
    case_ids={files[0]:[
        'actual-ungranted-uri-rejects-without-provider-open-and-preserves-final','actual-revoked-before-open-grant-rejects-and-regrant-is-explicit',
        *['actual-'+kind+'-uri-preserves-existing-pin-with-safe-error' for kind in ['empty','truncated','oversized','corrupt','read-error']],
        'actual-wrong-slot-template-source-cannot-install-generator',*['actual-'+kind+'-uses-observed-stream-bytes-and-fixed-private-pin' for kind in ['metadata-lie','short-pipe']],
        *['actual-cancel-at-'+phase+'-is-precommit-and-preserves-pin' for phase in ['COPYING','VERIFYING','COMMITTING']],
        'actual-late-cancel-does-not-report-committed-file-as-unchanged-failure','file-scheme-cannot-bypass-content-descriptor-interface'],
        files[1]:['actual-blocked-pipe-read-cancel-closes-cooperative-producer-and-preserves-final',
        'actual-descriptor-opening-cancellation-signal-reaches-provider-without-blocking-main','actual-fresh-uri-retry-after-both-cancellations-commits-cleanly'],
        files[2]:['actual-new-session-reconciles-validated-abandoned-stage-without-promotion-or-legacy-deletion',
        'unknown-private-named-entry-blocks-whole-startup-cleanup-without-traversal','actual-final-leaf-symlink-rejects-before-source-open-and-never-follows-target',
        'actual-nested-destination-parent-symlink-rejects-before-source-open','actual-ownership-marker-symlink-rejected-without-reading-target',
        'actual-owned-stage-name-with-symlink-type-cannot-be-deleted-or-promoted','actual-staging-directory-symlink-cannot-trigger-recursive-cleanup',
        'actual-import-model-root-symlink-refuses-before-input-and-finally-does-not-follow-it',
        'controlled-precommit-directory-sync-fault-preserves-real-final-and-reports-unconfirmed-cleanup',
        'normal-new-session-recovers-after-injected-sync-fault-without-native-initialization']}
    collection=read(run/'collected-results.json');assert set(collection['saved_sha256'])==set(files)
    for name in files:
        raw=run/'original-adb'/name;assert sha(raw)==collection['saved_sha256'][name]
        device=read(raw);assert device==read(run/name) and device['status']=='PASS' and device['variant']==variant
        assert [case['id'] for case in device['cases']]==case_ids[name] and all(case['passed'] is True for case in device['cases'])
        assert device['owner_registry_and_model_sha256']==expected and device['guards_unchanged'] is True
        assert device['raw_reasoning_persisted'] is False and device['network_mode']=='MOBILE_DATA_PRESERVED_APP_HAS_NO_INTERNET'
    cancellation=read(run/files[1]);assert all(0<=value<1000 for value in cancellation['timings'].values())
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_URI_PATH_CANCEL_28_CONTROLS_NOT_NATIVE_SYSTEM_PICKER_OR_FULL_F2',finished_utc=datetime.now(timezone.utc).isoformat(),
        original_sha256=collection['saved_sha256'],case_ids=case_ids,case_count=sum(map(len,case_ids.values())),
        scope='Three actual methods/28 controls, original bytes and known50 public owner hashes. Cooperative provider main cancel dispatch<1s/watchdogs are functional bounds, not M8 performance or arbitrary-provider IPC guarantee. Controlled sync exception is injection; new session same-process cleanup is not physical process death/power loss. Real native walking regression must pass before actual restart/all-slot/UI expansion.')
except Exception as failure:
    record.update(status='FAIL',finished_utc=datetime.now(timezone.utc).isoformat(),failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
