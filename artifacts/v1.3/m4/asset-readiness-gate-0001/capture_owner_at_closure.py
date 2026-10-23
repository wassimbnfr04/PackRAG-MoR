"""Read the fixed public owner-file set after actual development restoration.

No private custody, unknown files, model exports, row repair or radio changes.
This is a final-state check; the earlier registry-byte failure stays a failure.
"""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

target=HERE/'owner-at-closure.json';assert not target.exists()
restored=M4/'device-local-assets-development-restore-0001'
manifest=read(restored/'instrumentation-manifest.json');collection=read(restored/'collected-results.json')
pair=read(HERE/'corrected-pair-preflight.json')
assert manifest['status']==collection['status']=='PASS' and manifest['variant']=='debug'
assert manifest['apk_sha256']==collection['apk_sha256']==pair['apk_sha256']['build-0056']
assert set(collection['saved_sha256'])=={'m3-import-consent.json'}
assert sha(restored/'original-adb/m3-import-consent.json')==collection['saved_sha256']['m3-import-consent.json']
assert read(restored/'original-adb/m3-import-consent.json')==read(restored/'m3-import-consent.json')
preparation=read(HERE/'guarded-retry-preparation.json');expected=preparation['owner_public_file_sha256'];assert len(expected)==50
assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and not {'.private','temp','stage','pytest-temp'}.intersection(Path(name).parts) for name in expected)
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]]
output=subprocess.run(argv,capture_output=True,timeout=60)
command=dict(argv=argv,returncode=output.returncode,stdout=output.stdout.decode('utf-8',errors='replace'),stderr=output.stderr.decode('utf-8',errors='replace'))
observed={}
if output.returncode==0:
    for line in command['stdout'].splitlines():
        value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/')
        assert name[6:] not in observed;observed[name[6:]]=value
passed=output.returncode==0 and observed==expected
record=dict(status='PASS_KNOWN_PUBLIC_OWNER_FILES_MATCH_POST_LAUNCH_BASELINE_NOT_WHOLE_SESSION_PRESERVATION' if passed else 'FAIL_FINAL_KNOWN_OWNER_FILE_GUARD',
    recorded_utc=datetime.now(timezone.utc).isoformat(),commands=[command],guarded_file_count=len(observed),owner_public_file_sha256=observed,
    whole_f1_session_default_registry_bytes_preserved=False,restored_manifest_sha256=sha(restored/'instrumentation-manifest.json'),
    retry_preparation_sha256=sha(HERE/'guarded-retry-preparation.json'),
    scope='Exactly50 previously enumerated public paths, including model pins and two default registries. No new full directory enumeration claimed here. The accepted method guards independently compare their enumerated sets. Whole-session default-registry bytes changed during failed adjacent0001. Post-launch final equality neither repairs that failure nor proves old/new logical-row equivalence or causal actor. Private custody excluded before any access.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);assert passed,'Preserve failure; diagnose before F1 closure'
