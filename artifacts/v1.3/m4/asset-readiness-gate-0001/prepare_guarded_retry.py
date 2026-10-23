"""After the failed suite is terminal, close target app and bind current public guards."""
import hashlib,json,re,sqlite3,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'guarded-retry-preparation.json';assert not target.exists()
failure=json.loads((HERE/'adjacent-terminal-guard-diagnosis.json').read_text());expected=failure['after_sha256']
assert failure['differences']=={'packs/registry.sqlite':dict(before='e967352d73a4d69777f8030e2f4a8578347bd667861ba7b0a0f3775ecaae4a81',after='cf140bbf898aea7eb194406fa440e916cd2d746bb77b222a7c447f3f0e28ed10')}
adb=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR'];commands=[]
def call(argv,binary=False):
    result=subprocess.run(argv,capture_output=True,check=True,timeout=60)
    row=dict(argv=argv,returncode=result.returncode,stderr=result.stderr.decode('utf-8',errors='replace'))
    if not binary:row['stdout']=result.stdout.decode('utf-8',errors='replace')
    commands.append(row);return result.stdout
def guards():
    assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and not {'.private','temp'}.intersection(Path(name).parts) for name in expected)
    raw=call(adb+['shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]])
    parsed={}
    for line in raw.decode('utf-8').splitlines():
        value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/');parsed[name[6:]]=value
    assert parsed==expected,'Current public owner bytes differ from actual terminal after-map; preserve and diagnose'
    return parsed
before=guards()
call(adb+['shell','am','force-stop','org.packrag.product'])
after=guards();assert before==after
caller=call(adb+['shell','pm','list','packages','--uid','10155']).decode('utf-8',errors='replace')
payload=call(adb+['exec-out','run-as','org.packrag.product','cat','files/packs/registry.sqlite'],binary=True)
path=HERE/'default-registry-post-change.sqlite';assert not path.exists();path.write_bytes(payload)
assert hashlib.sha256(payload).hexdigest()==after['packs/registry.sqlite']
connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
try: integrity=connection.execute('PRAGMA integrity_check').fetchall()
finally:connection.close()
assert integrity==[('ok',)]
record=dict(status='PASS_UNCHANGED_TEST_RETRY_PREPARATION_POST_LAUNCH_BASELINE_NOT_TEST_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    owner_quote='Yes, I’ll keep PackRAG closed',owner_reply='Actual human reply to call_ce44e70ec08c4901b92fe60a1203fe3e; other apps/chat/mobile data remain available.',
    target_app_closed_after_all_current_tests_finished=True,commands=commands,owner_public_file_sha256=after,
    current_default_registry_sha256=hashlib.sha256(payload).hexdigest(),current_default_registry_read_only_integrity='ok',observed_launch_caller_uid='10155',observed_uid_package=caller.strip(),
    limits='Only a post-change SQLite snapshot exists; integrity is current-state only, not before/after logical equivalence or human-actor proof. Models and49 other public files unchanged. Failed owner equality remains FAIL. No restore/repair/clearing/uninstall/radio/privilege change. Retry uses identical0056/579 sources/assertions and explicitly post-launch baseline.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'F1 adjacent0001 TERMINAL FAIL at {record["recorded_utc"]}: five methods/one final owner-guard failure907.664s. Only packs/registry.sqlite changes e967352d…→cf140bbf…; all49 other files and all50 filenames match. Four actual completed passing originals saved; failed query-runtime phone JSON is stale and parsed-equal prior E3, never accepted. System ActivityTaskManager records ordinary MAIN/LAUNCHER PackRAG MainActivity start during the failed method from uid10155; caller package resolved separately, human actor/causality and logical-row equivalence not proved. Current post-change DB captured read-only/integrity ok; old bytes unavailable. Owner explicitly agrees to keep PackRAG closed. All tests finished before target-only force-stop; before/after explicit50-file hashes equal post-change cf140 baseline. Same0056/579 source/assertions will retry adjacent0002 without a code repair. The complete F1 session did NOT preserve default-registry bytes; later accepted-run comparisons must explicitly use post-launch baseline. Prior core0002 retains pre-change baseline/evidence. F1/UI/policy/F2 remain held until retry passes.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status']);print('Observed launch caller package:',caller.strip())
