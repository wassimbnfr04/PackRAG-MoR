"""Restore exact debug APKs in place only after final policy originals pass, then test consent."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=HERE.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
policy=HERE/'device-local-asset-adjacent-demo-0001-execution.json'
assert read(policy)['status']=='PASS_F2_FRESH_ADJACENT_BACKGROUND_VARIANT_NOT_FULL_F2'
assert sum(x['methods'] for x in read(policy)['completed'])==6 and sum(x['controls'] for x in read(policy)['completed'])==26
target=HERE/'debug-restoration-and-final-guards-0001.json';run=M4/'device-local-asset-final-debug-consent-0001'
assert not target.exists() and not run.exists()
sources=read(M4/'build-0076/source-at-build-start.json')['files'];assert len(sources)==599
record=dict(status='RUNNING_RESTORATION_NOT_F2_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),policy_sha256=sha(policy),commands=[])
def unchanged():
    for name,value in sources.items():assert sha(ROOT/name)==value,name
def command(argv,label):
    print('F2_RESTORE',label,'START',flush=True)
    with (HERE/('restore-0001-'+label+'.stdout.txt')).open('xb') as out,(HERE/('restore-0001-'+label+'.stderr.txt')).open('xb') as err:
        result=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['commands'].append(dict(argv=argv,returncode=result.returncode,label=label))
    target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,'Hold restoration/F2/F3; do not retry uncertain installation'
    print('F2_RESTORE',label,'PASS',flush=True)
python=[sys.executable,'-X','utf8']
try:
    unchanged()
    command(python+[str(HERE/'install_pair_serial.py'),'--build','build-0076','--variant','debug','--output','adjacent-debug-restoration-0001.json'],'install')
    assert read(HERE/'adjacent-debug-restoration-0001.json')['status']=='PASS_SERIAL_INSTALLED_EXACT_APK_PAIR_NO_TEST_ACCEPTANCE'
    command(python+[str(HERE/'test_android_installed_0001.py'),'--serial','R3CT908DHHR','--build',str(M4/'build-0076'),'--run',str(run),'--class-name','org.packrag.product.PackImportConsentTest','--result-file','m3-import-consent.json','--timeout','900','--variant','debug'],'consent')
    command(python+['-m','scripts.v13_collect_phone_results','--run',str(run),'--files','m3-import-consent.json'],'collect')
    manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
    assert manifest['status']==collection['status']=='PASS' and manifest['transport']=='VERIFY_EXACT_INSTALLED_APKS_NO_REINSTALL'
    assert re.search(r'OK \(1 test\)',(run/'instrumentation.txt').read_text())
    selected=manifest['selected_test_sources']['org.packrag.product.PackImportConsentTest']
    assert sources[selected['source']]==selected['source_sha256']
    original=run/'original-adb/m3-import-consent.json';value=read(original)
    assert sha(original)==collection['saved_sha256']['m3-import-consent.json']
    assert value['status']=='PASS' and len(value['cases'])==4 and all(x['passed'] is True for x in value['cases'])
    command(python+[str(HERE/'capture_known_guard.py'),'--output','owner-at-f2-closure-0001.json'],'owner50')
    command(python+[str(HERE/'capture_final_owner_no_follow_0001.py')],'owner50-nofollow')
    command(python+[str(HERE/'prepare_full_sources.py'),'--build','build-0076','--output','source4-at-f2-closure-0001.json','--verify-only'],'source4')
    unchanged()
    record.update(status='PASS_F2_EXACT_DEBUG_RESTORATION_CONSENT4_OWNER50_SOURCE4_NOT_CLOSURE',
        installed_proof_sha256=sha(HERE/'adjacent-debug-restoration-0001.json'),manifest_sha256=sha(run/'instrumentation-manifest.json'),
        collection_sha256=sha(run/'collected-results.json'),original_sha256=sha(original),methods=1,controls=4,
        owner_guard_sha256=sha(HERE/'owner-at-f2-closure-0001.json'),source4_guard_sha256=sha(HERE/'source4-at-f2-closure-0001.json'),
        owner_nofollow_guard_sha256=sha(HERE/'owner-at-f2-closure-nofollow-0001.json'),
        scope='Exact prepared debug APKs restored serially in place, no uninstall/clear. Actual four isolated private-copy/older-version-consent controls, no new visual-dialog or native-generation claim. All original reports saved; fixed50 owner public files and retained readonly four full-size test inputs match. Source599 unchanged. Policy fixture/calibration/performance/radio/release limits remain; final custody, gate/index and checkpoint still required.')
except Exception as failure:
    record.update(status='FAIL_HOLD_F2_AND_F3',failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
