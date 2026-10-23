"""Save owner-requested pause after completed tests; no new device execution."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'pause.json';assert not target.exists()
gate_path=M4/'selection-gate-0002/gate.json';gate=read(gate_path)
assert gate['status']=='M4D3_SELECTION_FREEZING_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
assert read(M4/'selection-gate-0002/reporting-acceptance-execution.json')['status']=='PASS_ACCEPTANCE_PREFLIGHT_NOT_CLOSURE_OR_COMPLETE_PRODUCT'
for values in [gate['source_sha256'],gate['android_source_sha256'],gate['output_sha256']]:
    for name,value in values.items():assert digest(ROOT/name)==value,name
commit=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert commit=='19f760e89c9a5dae7a36edf8fe1b02ba248cf700'
snapshots={}
for name in ['PLAN.md','STATUS.md','DECISIONS.md']:
    saved=HERE/'state-snapshot'/name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists()
    saved.write_bytes((ROOT/name).read_bytes());snapshots[name]=digest(saved)
record=dict(status='PAUSED_AT_OWNER_REQUEST_AFTER_COMPLETED_D3_TESTS',recorded_utc=datetime.now(timezone.utc).isoformat(),
    verified_implementation_checkpoint=commit,gate=str(gate_path.relative_to(ROOT)),gate_sha256=digest(gate_path),
    unchanged_runtime_inputs=len(gate['source_sha256']),unchanged_android_inputs=len(gate['android_source_sha256']),
    unchanged_gate_public_outputs=len(gate['output_sha256']),operational_state_sha256=snapshots,
    tests_running=False,tests_killed=False,development_restored_build='build-0030',restoration_run='device-development-restore-0010',
    owner_models_and_registries_preserved=True,mobile_data_preserved=True,phone_may_disconnect=True,
    next_milestone='M4E1 query/date/jurisdiction controls and captured answer context',next_code_started=False,
    resume='Only after explicit owner instruction; verify checkpoint/current source/saved original results/history, then E1 using M4E_UI_PREPARATION.md',
    scope='RAG/mobile software and test packs; final knowledge-pack content belongs to owner',
    limits='D3 correctness/ownership acceptance is not complete M4/product, semantic gold, final content review/calibration, benchmark, final signing or archive acceptance')
target.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(status=record['status'],checkpoint=commit,public_outputs_unchanged=record['unchanged_gate_public_outputs'])))
