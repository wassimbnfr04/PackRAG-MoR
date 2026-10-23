"""Actual full-size four-slot API/native acceptance iteration; save originals before switching APKs."""
import argparse,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--run',required=True);parser.add_argument('--source-preparation',required=True);args=parser.parse_args()
build=M4/args.build;run=M4/args.run;target=HERE/(args.run+'-execution.json');assert build.parent==M4 and run.parent==M4 and not run.exists() and not target.exists()
host=read(HERE/(args.build+'-capture.json'));assert host['status']=='PASS_F2_API_ITERATION_HOST_APK_CONTRACTS_NOT_DEVICE_OR_F2_ACCEPTANCE'
source=read(HERE/args.source_preparation);assert source['status']=='PASS_OWNED_FULL_ASSET_SOURCE_SET_VALIDATED_NOT_IMPORT_OR_F2_ACCEPTANCE' and source['source_total_bytes']==2009206667
sources=read(build/'source-at-build-start.json')['files']
for name,value in sources.items():assert sha(ROOT/name)==value,name
files=['m4-local-asset-import-all-slots.json','m4-local-asset-import-all-slots-progress.json']
commands=[
    [sys.executable,'-X','utf8','-m','scripts.v13_test_android','--serial','R3CT908DHHR','--build',str(build),'--run',str(run),'--class-name','org.packrag.product.LocalAssetImportAllSlotsDeviceTest','--result-file',files[0],'--timeout','2400','--variant',host['variant']],
    [sys.executable,'-X','utf8','-m','scripts.v13_collect_phone_results','--run',str(run),'--files',','.join(files)],
    [sys.executable,'-X','utf8',str(HERE/'prepare_full_sources.py'),'--build',args.build,'--output',args.run+'-after-source.json','--verify-only'],
    [sys.executable,'-X','utf8',str(HERE/'capture_known_guard.py'),'--output',args.run+'-after-known-guard.json']]
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,run=args.run,source_preparation_sha256=sha(HERE/args.source_preparation),commands=[])
try:
    for i,command in enumerate(commands):
        print(args.run,'stage',i,'START',flush=True)
        with (HERE/(args.run+f'-stage-{i}.stdout.txt')).open('xb') as out,(HERE/(args.run+f'-stage-{i}.stderr.txt')).open('xb') as err:r=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
        record['commands'].append(dict(argv=command,returncode=r.returncode));target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        assert r.returncode==0,'Hold later F2/UI; preserve actual progress/failure and repair'
        print(args.run,'stage',i,'PASS',flush=True)
    collection=read(run/'collected-results.json');assert set(collection['saved_sha256'])==set(files)
    device=read(run/'original-adb'/files[0]);assert device['status']=='PASS' and device['variant']==host['variant']
    for name in files:
        p=run/'original-adb'/name;assert sha(p)==collection['saved_sha256'][name];value=read(p);assert value['status']=='PASS' and value['cases']==device['cases'] and value['imports']==device['imports']
    expected=read(HERE/'before.json')['owner_public_file_sha256'];assert device['owner_registry_and_model_sha256']==expected and device['guards_unchanged'] is True
    expected_cases=['initially-missing-private-model-root-and-separate-uid-four-narrow-grants']+['actual-full-size-'+slot+'-uri-readback-commit-close' for slot in ['GENERATOR','TEMPLATE','TOKENIZER','ENCODER']]+['all-four-independent-pinned-final-file-verification','actual-cold-native-retrieval-admission-selection-citation-answer','actual-warm-native-retrieval-admission-selection-citation-answer']
    assert [case['id'] for case in device['cases']]==expected_cases and all(case['passed'] is True for case in device['cases'])
    assert [item['slot'] for item in device['imports']]==['GENERATOR','TEMPLATE','TOKENIZER','ENCODER']
    for item in device['imports']:
        key='files/f2-full-assets-0001/full-'+item['slot'].lower()+'.asset'
        assert item['sha256']==source['source_sha256'][key] and item['directory_synced'] is True and item['staging_cleaned'] is True
        assert item['observed_final_bytes']==item['bytes'] and item['progress_callbacks']>0 and item['duration_ms']>0
        assert item['stages']==['COPYING','SYNCING','VERIFYING','COMMITTING','COMMITTED']
        before=item['provider_before'];after=item['provider_after']
        for label in ['opens','closes','typed_cancellable_opens']:assert after[label]==before[label]+1
        for label in ['close_errors','typed_plain_opens']:assert after[label]==before[label]
        assert after['provider_uid']!=device['product_uid']
    assert sum(item['bytes'] for item in device['imports'])==2009206667
    for label in ['cold','warm']:assert '74 °C' in device['answer_'+label] and '[S1]' in device['answer_'+label] and 1<=device['emitted_tokens_'+label]<=512
    assert device['actual_weight_inference'] is True and device['raw_reasoning_persisted'] is False and device['initialization_ms_cold']>0
    assert read(HERE/(args.run+'-after-source.json'))['source_sha256']==source['source_sha256']
    for name,value in sources.items():assert sha(ROOT/name)==value,name
    record.update(status='PASS_F2_ACTUAL_ALL_FOUR_FULL_SIZE_URI_IMPORT_AND_COLD_WARM_NATIVE_NOT_UI_OR_FULL_F2',finished_utc=datetime.now(timezone.utc).isoformat(),original_sha256=collection['saved_sha256'],cases=expected_cases,imports=device['imports'],
        scope='Actual2009206667 bytes/4 separate-UID descriptor imports into initially absent private model root; readback pins/atomic replacement/progress/close and cold/warm real answers; exact owner50 and source4 hashes unchanged. Explicit narrow test receiver grants, not Android system picker or ViewModel/UI. Source set retained deliberately. No full F2/M4/product/release/domain/gold/performance acceptance.')
except Exception as e:
    record.update(status='FAIL',finished_utc=datetime.now(timezone.utc).isoformat(),failure_type=type(e).__name__,failure_message=str(e))
    # Preserve the actual failure progress even when generic instrumentation reports no main PASS envelope.
    if run.exists():
        directory=run/'failure-original-adb';directory.mkdir(exist_ok=False)
        command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','cat','files/'+files[1]]
        r=subprocess.run(command,capture_output=True,timeout=30);record['failure_progress_returncode']=r.returncode
        if r.returncode==0:
            p=directory/files[1];p.write_bytes(r.stdout);record['failure_progress_sha256']=sha(p)
    raise
finally:target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
