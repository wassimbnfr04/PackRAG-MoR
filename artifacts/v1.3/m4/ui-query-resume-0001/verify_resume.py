"""Read-only checkpoint/evidence guard before owner-authorized E1 changes."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
target=HERE/'resume.json';assert not target.exists()
pause_path=ROOT/'artifacts/v1.3/m4/selection-pause-0001/pause.json';pause=read(pause_path)
gate=read(ROOT/pause['gate']);assert digest(ROOT/pause['gate'])==pause['gate_sha256']
for field in ['source_sha256','android_source_sha256','output_sha256']:
    for name,value in gate[field].items():assert digest(ROOT/name)==value,name
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files']
for name,value in history.items():assert digest(ROOT/name)==value,name
for name,value in pause['operational_state_sha256'].items():
    assert digest(pause_path.parent/'state-snapshot'/name)==value,name
head=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head.startswith('725dd98')
devices=subprocess.check_output([str(ROOT/'vendor/platform-tools/adb.exe'),'devices','-l'],cwd=ROOT,text=True)
assert 'R3CT908DHHR            device' in devices
(HERE/'adb-devices.txt').write_text(devices,encoding='utf-8')
record=dict(status='PASS_OWNER_AUTHORIZED_RESUME_BEFORE_E1_EDITS',recorded_utc=datetime.now(timezone.utc).isoformat(),
    head=head,implementation_checkpoint=pause['verified_implementation_checkpoint'],
    unchanged_runtime_inputs=len(gate['source_sha256']),unchanged_android_inputs=len(gate['android_source_sha256']),
    unchanged_d3_public_outputs=len(gate['output_sha256']),unchanged_historical=len(history),
    adb_authorized_serial='R3CT908DHHR',mobile_data_must_remain_on=True,
    next='M4E1 query controls and captured context',scope='RAG/mobile software with test packs; final knowledge content belongs to owner')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
