"""Verify the exact public pause state before resuming F1; no model/private reads."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'resume-0001.json';assert not target.exists()
pause=read(ROOT/'artifacts/v1.3/m4/asset-readiness-pause-0001/pause.json')
head=subprocess.check_output(['git','--no-optional-locks','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head==pause['accepted_checkpoint']
gate_path=ROOT/'artifacts/v1.3/m4/diagnostics-gate-0001/gate.json'
assert sha(gate_path)==pause['accepted_e3_gate_sha256']
gate=read(gate_path)
maps=[pause['android_source_sha256'],gate['source_sha256'],gate['output_sha256'],pause['documents_at_pause_sha256']]
for mapping in maps:
    for name,expected in mapping.items():
        assert '.private' not in Path(name).parts and 'temp' not in Path(name).parts
        assert sha(ROOT/name)==expected,name
first=HERE/'first-host-iteration.json';assert sha(first)==pause['first_host_iteration_sha256']
build=ROOT/'artifacts/v1.3/m4/build-0054/build-result.json';assert sha(build)==pause['build_result_sha256']
argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'devices','-l']
device=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=30)
assert any(line.split()[:2]==['R3CT908DHHR','device'] for line in device.stdout.splitlines())
now=datetime.now(timezone.utc).isoformat()
record=dict(status='PASS_EXACT_OWNER_PAUSE_STATE_RESUMED_NOT_F1_ACCEPTANCE',recorded_utc=now,head=head,
    checked_android_inputs=len(maps[0]),checked_runtime_inputs=len(maps[1]),checked_e3_outputs=len(maps[2]),
    checked_pause_documents=len(maps[3]),adb=dict(argv=argv,stdout=device.stdout,stderr=device.stderr,returncode=device.returncode),
    owner_authorization='Phone available; pick up from where you left off. Final knowledge content excluded; test packs permitted; mobile data stays on.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'RESUMED at {now}: exact pause verified (577 Android/188 runtime inputs, all {len(maps[2])} prior E3 outputs and five pause documents); E3 checkpoint {head} unchanged. Samsung R3CT908DHHR is authorized. M4F1 remains current: first iteration62 host PASS; phone/native/UI acceptance pending. First preserve missing/corrupt query observations across error-session recovery, then independently validate physical readiness/negative paths/real LFM walking and read-only result ownership before F2. No final knowledge-pack authoring; mobile data stays on. Earlier pause paragraphs are dated history superseded by this owner-authorized resume.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;heading,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(heading+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status'])
