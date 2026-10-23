"""Only after full check-only passes: durable E3 acceptance with explicit remaining scope."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=HERE/'acceptance-document-update.json';assert not target.exists() and not (HERE/'gate.json').exists()
command=[sys.executable,'-X','utf8',str(HERE/'verify_and_record.py'),'--check-only']
result=subprocess.run(command,cwd=ROOT,capture_output=True,check=True,text=True,encoding='utf-8')
assert 'ALL_E3_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_WRITTEN' in result.stdout
phone=[]
for name,count in [('device-ui-diagnostics-retained-0004',4),('device-diagnostics-full-0001',37),('device-diagnostics-policy-full-0001',30),('device-development-restore-0014',1)]:
    text=(M4/name/'instrumentation.txt').read_text(encoding='utf-8');match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    seconds=float(re.sub(r'\s','',match[1]).replace(',','.'));phone.append(dict(run=name,methods=count,whole_instrumentation_seconds=seconds))
now=datetime.now(timezone.utc).isoformat();text=(
    f'E3 VERIFIED within diagnostics/execution/lifecycle/UI contracts at {now}. Python1034 and53 host methods per matched0052/53 variant pass;188 runtime/574 Android inputs are bound. '
    f'Actual retained UI4/{phone[0]["whole_instrumentation_seconds"]}s, full development37/{phone[1]["whole_instrumentation_seconds"]}s, '
    f'compiled policy30/{phone[2]["whole_instrumentation_seconds"]}s and restored0052 consent1/{phone[3]["whole_instrumentation_seconds"]}s pass. '
    'All72 final method originals plus the extra edited-query ownership original are saved before APK switches; both new AR/FR PNGs actually inspected. '
    '43 retained tokenizer/admission cases/19 runtime states, selection28/9 tokenizer/8 runtime/2 guards/2 origins and signed source17 packs/34 inspections/43 rows/19 fields/11 negatives per variant pass. '
    'New desktop14 passes; six earlier actual desktop gates are explicitly retained under unchanged188 runtime inputs. '
    'Actual0047 diagnostic navigation/seven controls/viewport is retained through exact selected source and whole product APK equality, not described as a0052 rerun. '
    'Original host/Python/device/visual/three retained UI failures and every partial scope stay unchanged. Two UI dispatch helpers were strengthened; all app/answer expectations and whole product APK bytes remained unchanged. '
    'Owner models are preserved; all accepted later owner guards use the documented post-launch registry baseline. Earlier failed0002 changed default registry bytes and remains an explicit exception, with no causal actor/logical-row equality claim. '
    'All690 E2 public outputs/587 historical identities remain unchanged. Mobile data stays on, app has no INTERNET permission. '
    'E3 closure/exact checkpoint is being recorded; next M4F local assets and final normative UI/product audit under M4F_ASSET_READINESS_PREPARATION.md. '
    'Full M4/product, builder/evaluation software, nondebuggable release/physical metrics, documentation and three archives remain. Owner authors final knowledge content. '
    'Synthetic assertions are not genuine licensing/review/calibration/gold; structural citation checks are not semantic entailment; functional timings are not benchmarks. No phone test is running.'
)
updated={}
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;source=p.read_text(encoding='utf-8-sig');first,rest=source.split('\n',1);p.write_text(first+'\n\n'+text+'\n\n'+rest,encoding='utf-8');updated[name]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['DECISIONS.md','docs/v1.3/M4E3_METHODS.md','docs/v1.3/M4E3_EVIDENCE_INDEX.md','docs/v1.3/M4E3_LIFECYCLE_CONTROLS.md',
    'docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_INCREMENT_PLAN.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/architecture-compliance-matrix.md']:
    p=ROOT/name
    with p.open('a',encoding='utf-8') as f:f.write('\n\n'+text+'\n\nFinal E3 gate and exact checkpoint follow successful check-only; original commands/sources/APK identities/failed attempts/custody are recorded under artifacts/v1.3/m4/diagnostics-gate-0001. F preparation is dependency planning only until E3 checkpoint verification.\n')
    updated[name]=hashlib.sha256(p.read_bytes()).hexdigest()
target.write_text(json.dumps(dict(status='E3_ACCEPTANCE_DURABLE_DOCUMENTS_UPDATED_AFTER_CHECK_ONLY_BEFORE_CLOSURE',recorded_utc=now,check_only_argv=command,check_only_returncode=result.returncode,
    check_only_stdout=result.stdout,phone=phone,updated_document_sha256=updated),indent=2)+'\n',encoding='utf-8')
print('Verified E3 acceptance/current remaining work recorded; closure/checkpoint next')
