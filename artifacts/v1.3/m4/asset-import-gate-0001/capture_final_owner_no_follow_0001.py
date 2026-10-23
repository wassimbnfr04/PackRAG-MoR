"""Closure snapshot of exactly50 public owner files; reject links on all path components."""
import hashlib,json,re,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'owner-at-f2-closure-nofollow-0001.json';assert not target.exists()
expected=json.loads((HERE/'before.json').read_text())['owner_public_file_sha256'];assert len(expected)==50
blocked={'.private','..','temp','stage','runner-temp','host-temp','pytest-temp'}
for name in expected:
    p=PurePosixPath(name)
    assert re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and not p.is_absolute() and not blocked.intersection(p.parts)
    assert p.suffix.lower() not in {'.key','.seed','.seed32','.keystore','.jks','.pem'}
checks=['set -eu','test -d files','test ! -L files','test "$(readlink -f files)" = /data/user/0/org.packrag.product/files']
parents=set()
for name in sorted(expected):
    path='files'
    for part in PurePosixPath(name).parts[:-1]:
        path+='/'+part
        if path not in parents:checks+=['test -d '+path,'test ! -L '+path];parents.add(path)
    leaf='files/'+name
    checks+=['test -f '+leaf,'test ! -L '+leaf,'test "$(readlink -f '+leaf+')" = /data/user/0/org.packrag.product/'+leaf]
checks+=['sha256sum '+' '.join('files/'+name for name in sorted(expected))]
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as org.packrag.product sh -c '+shlex.quote('; '.join(checks))]
started=datetime.now(timezone.utc).isoformat();result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=300)
observed={}
if result.returncode==0:
    for line in result.stdout.splitlines():
        value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/')
        observed[name[6:]]=value
record=dict(status='PASS_EXACT50_PUBLIC_OWNER_CLOSURE_NOFOLLOW_SNAPSHOT' if result.returncode==0 and observed==expected else 'FAIL_OWNER_CLOSURE_HOLD_F2',
    started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),owner_public_file_sha256=observed,
    command=dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),
    scope='Every ancestor and leaf of only50 named public files checked as nonlink and resolved within exact app base before hashing. No unknown-file/private-custody enumeration, writes or radio changes. Snapshot under completed tests/PackRAG closed, not an atomic adversarial-filesystem guarantee or recovery of historical default-registry bytes.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert record['status'].startswith('PASS_');print(record['status'],flush=True)
