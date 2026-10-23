"""Save bounded connected-gate evidence on explicit owner pause. Never completes C2b."""
import ast,hashlib,json,runpy,textwrap
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
M4=ROOT/'artifacts/v1.3/m4'
FULL=M4/'conflict-gate-0001'
target=HERE/'pause.json'
assert not target.exists(),'Pause record is immutable'
checker=FULL/'verify_and_record.py'
code=checker.read_text()
scope=runpy.run_path(str(checker),run_name='connected_gate_audit_only')
scope['PHONE']=dict(scope['PHONE'])
assert scope['PHONE'].pop('device-development-restore-0007')==('build-0012',1,['m3-import-consent.json'])
begin=code.index('def main():\n')+len('def main():\n')
end=code.index('    if "--check-only" in sys.argv:',begin)
# Execute only read-only acceptance checks for the two completed gates. The
# full checker remains unchanged and still requires restoration for C2b closure.
exec(compile(textwrap.dedent(code[begin:end]),str(checker)+'[connected-gates-only]','exec'),scope)
assert len(scope['phone'])==2 and sum(r['methods'] for r in scope['phone'].values())==39
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
names=['run-0007','smoke-0006','build-0012','build-0013','demo-apk-inspection-0007',
 'conflict-fixtures-0001','conflict-unit-0001','conflict-adjacent-0001','conflict-adjacent-0002',
 'run-0006','build-0011','conflict-smoke-0001','conflict-smoke-0002','conflict-diagnostic-0001',
 'conflict-diagnostic-0002','conflict-smoke-0003','xml-prompt-unit-0001','xml-prompt-fixtures-0001',
 'conflict-source-recovery-0001','xml-prompt-source-recovery-0001','conflict-input-audit-0001',
 *scope['PHONE']]
blocked={'temp','stage','pytest-temp','__pycache__','.private','build','.gradle','.cxx','.kotlin'}
outputs={}
for name in names:
 base=M4/name;assert base.is_dir(),base
 for path in sorted(base.rglob('*')):
  relative=path.relative_to(ROOT)
  if blocked.intersection(relative.parts) or path.suffix.lower() in {'.apk','.pyc','.class'}:continue
  if path.is_file():outputs[relative.as_posix()]=digest(path)
for path in list(FULL.glob('*.py'))+list(HERE.glob('*.py'))+[FULL/'PREPARATION_FAILURE.json',FULL/'prephone-audit.json',M4/'conflict-temp-0001/fixture-execution.txt']:
 outputs[path.relative_to(ROOT).as_posix()]=digest(path)
documents=['PLAN.md','STATUS.md','DECISIONS.md','docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md',
 'docs/v1.3/M4C_VALIDITY_CONFLICT_PLAN.md','docs/v1.3/M4C2a_SOURCE_METADATA_METHODS.md','docs/v1.3/M4C2b_CONFLICT_METHODS.md',
 'docs/v1.3/M4C2_DESIGN_AUDIT.md','docs/v1.3/M4D_EVIDENCE_PREPARATION.md','docs/adr/ADR-002-v13-conflict-scope.md',
 'docs/architecture-compliance-matrix.md']
state={}
for name in documents:
 source=ROOT/name;snapshot=HERE/'state-snapshot'/name
 snapshot.parent.mkdir(parents=True,exist_ok=True);assert not snapshot.exists()
 snapshot.write_bytes(source.read_bytes());state[name]=digest(source)
 outputs[snapshot.relative_to(ROOT).as_posix()]=digest(snapshot)
record=dict(status='OWNER_PAUSED_AFTER_CONNECTED_GATES_C2B_RESTORATION_AND_CLOSURE_PENDING',
 recorded_utc=datetime.now(timezone.utc).isoformat(),phone=scope['phone'],python_tests=691,host_methods_per_variant=26,
 runtime_inputs=143,android_inputs_per_variant=458,historical_identities_unchanged=587,
 fixed_conflict_cases=40,signed_packs=19,tokenizer_cases=19,actual_runtime_cases=7,xml_prompt_cases=10,
 model_or_native_or_decoding_change=False,mobile_data='ON',installed_variant='demo build-0013',
 source_sha256=scope['runtime'],android_source_sha256=scope['builds'],apk_sha256=scope['apk_hashes'],
 prior_saved_output_identities_unchanged={key:len(scope[value]['output_sha256']) for key,value in [('B2','prior_query'),('C1','prior_validity'),('C2a','prior_metadata')]},
 output_sha256=outputs,documents_at_pause=state,
 pending=['Owner resumes with phone available','Restore debug build-0012; run prepared PackImportConsentTest in device-development-restore-0007',
 'Run full conflict-gate-0001/verify_and_record.py --check-only including restoration; update acceptance state and write immutable C2b closure/checkpoint',
 'Only after C2b passes proceed to M4D evidence, E UI, F assets, M5/M6 demonstrator packs, M7 PackBench and M8 final physical release acceptance'],
 limits=['Both completed gate outputs are verified; C2b and product are NOT complete',
 'No new instrumentation, APK installation, foreground UI action or variant restoration after the running gate finishes',
 'Instrumentable Debug-signed demo is not final nondebuggable release',
 'Synthetic functional data is not release calibration, source/translation review, held-out accuracy or causal performance evidence'])
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
# Reuse only the literal source whitelist of the future verified checkpoint,
# never run its acceptance-dependent writer or pretend it has completed.
tree=ast.parse((FULL/'create_checkpoint.py').read_text())
source_names=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sources' for t in node.targets))
asset_root=ROOT/'product/android/app/src/androidTest/assets'
source_names += [p.relative_to(ROOT).as_posix() for d in ['conflict-corpus','prompt-v13-xml-corpus'] for p in (asset_root/d).iterdir() if p.is_file()]
tested={**scope['runtime'],**scope['builds']['build-0012']}
files={**outputs,**state}
for name in source_names:
 assert name in tested and digest(ROOT/name)==tested[name],name
 files[name]=tested[name]
files[target.relative_to(ROOT).as_posix()]=digest(target)
for name,expected in files.items():
 path=ROOT/name
 assert path.resolve().is_relative_to(ROOT) and not blocked.intersection(Path(name).parts),name
 assert path.suffix.lower() not in {'.apk','.pyc','.class','.seed','.pem','.key','.keystore','.jks'},name
 assert digest(path)==expected,name
manifest=HERE/'checkpoint-files.json';assert not manifest.exists()
manifest.write_text(json.dumps(dict(purpose='PUBLIC_WORK_IN_PROGRESS_PAUSE_CHECKPOINT_NOT_C2B_ACCEPTANCE',files=dict(sorted(files.items()))),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=record['status'],phone=record['phone'],saved_output_files=len(outputs),checkpoint_files=len(files)),indent=2))
