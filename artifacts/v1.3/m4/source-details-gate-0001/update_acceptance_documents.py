"""Document E2 only after every required repaired acceptance gate passes."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=HERE/'acceptance-document-update.json';assert not target.exists()
subprocess.run([sys.executable,'-X','utf8',str(HERE/'verify_and_record_repaired.py'),'--check-only'],cwd=ROOT,check=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
durations={}
for name in ['device-ui-source-details-0002','device-source-details-full-0001','device-source-details-policy-full-0001','device-development-restore-0013']:
    text=(M4/name/'instrumentation.txt').read_text(encoding='utf-8')
    match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    durations[name]=float(re.sub(r'\s','',match[1]).replace(',','.'))
stamp=datetime.now(timezone.utc).strftime('%d %B %Y %H:%M UTC')
summary=(f'E2 VERIFIED {stamp}: copied source attribution/location and captured canonical/rendering/origin details, plus freshly verified active/inactive pack inspection, pass. '
    'Python 1034 (run0015), 40 host methods per final variant, 561 Android and 188 public runtime inputs; all six retained actual desktop gates pass. '
    f'Repaired foreground UI: 4 methods/{durations["device-ui-source-details-0002"]}s; full development: 35/{durations["device-source-details-full-0001"]}s; '
    f'compiled policy: 29/{durations["device-source-details-policy-full-0001"]}s; restored debug0041 consent: 1/{durations["device-development-restore-0013"]}s. '
    'All 69 final original JSON results are saved. Each variant independently checks 17 signed fixtures, 34 active/inactive inspections, 43 public source rows/all 19 fields and 11 rejection controls; retained tokenizer/runtime/selection parity passes. '
    'The initial automated UI PASS and visual FAIL remain unchanged. Exactly two layout sources were repaired; fresh debug0041/demo0042 and actual repaired screenshots prove readable canonical AR/FR text in the tested viewport. '
    'No old Android run is promoted to repaired acceptance. Original build, fixture, checker and collection failures remain recorded. '
    'All 412 E1 outputs and 587 historical identities remain unchanged. Owner models/default registries/mobile data are preserved. '
    'This closes E2 only: E3, F, software builder/evaluation, nondebuggable release, physical measurements and final documentation/three archives remain. '
    'Synthetic assertions do not establish genuine licensing, review, calibration or gold accuracy; structural citations do not establish semantic entailment. No test is running.')
updates={}
def prepend(name,paragraph):
    p=ROOT/name;raw=p.read_bytes();text=raw.decode('utf-8-sig');first,rest=text.split('\n',1)
    p.write_text(first+'\n\n'+paragraph+'\n'+rest,encoding='utf-8')
    updates[name]=dict(before_sha256=sha(raw),after_sha256=sha(p.read_bytes()))
prepend('STATUS.md',summary+'\n\nNext action: immutable E2 closure and exact checkpoint, then M4E3 under M4E3_DIAGNOSTICS_PREPARATION.md. Earlier pending and RUNNING paragraphs are dated history.')
prepend('PLAN.md',summary+'\n\nRemaining order: E3 diagnostics/lifecycle/accessibility/navigation → F verified local assets/final M4 audit → M5/M6 software builder/provenance/calibration interfaces with test content → M7 software PackBench → M8 release/physical measurements/documentation/three verified archives. Final knowledge content remains owner supplied.')
prepend('DECISIONS.md',summary+'\n\nRead-only pack inspection returns copied data from a freshly authenticated private staging snapshot and retains captured answer context; mutation uses the existing consent/session controls. URI/path metadata is displayed as signed attribution, not fetched. Unknown redistribution remains distinct from false. Source-viewer is the architecture-specified module. Insets repair changes product layout, so repaired Android gates are newly executed; Python/desktop reuse is explicitly limited to 188 unchanged inputs. Functional times and the separate process sample are not performance or causal bottleneck acceptance.')
prepend('docs/v1.3/M4E2_METHODS.md',summary+'\n\nFinal method counts and whole-instrumentation durations above supersede preparation observations below. UI includes five new product source/inspection controls, two canonical-language display controls, five retained query controls and the retained management method. New ViewModel contains five controls; compiled source-policy contains two controls; restoration contains four consent cases. A JUnit method count is not a case count. Arabic/French screenshots exercise the real shared viewer with copied verified fixture data, not new multilingual inference or production admission of fixture keys. Desktop and Python runs were actually executed before the exact two-file Android-only insets repair; their input equality is verified, not represented as reruns.')
prepend('docs/v1.3/M4E2_EVIDENCE_INDEX.md',summary+'\n\nThis final acceptance supersedes the dated preparation statuses in the table below. Original failed/intermediate run scopes remain unchanged; final repaired development/policy/restoration originals and independent parity now pass. The immutable closure and checkpoint are the next recording steps, not an inferred whole-product completion.')
prepend('docs/v1.3/M4_INCREMENT_PLAN.md',summary)
prepend('docs/v1.3/M4_IMPLEMENTATION_LOG.md',summary)
prepend('docs/architecture-compliance-matrix.md',summary+'\n\nM4 UI remains IMPLEMENTING as a whole: E1 controls and E2 source/pack details are accepted within their recorded scopes. E3 diagnostics/lifecycle/accessibility and F local assets remain unverified. No full architecture row is promoted solely by compilation or synthetic metadata.')
prepend('docs/v1.3/FULL_DOCUMENTATION_WORKING.md',summary+'\n\nThis remains an evolving documentation draft; final full v1.3 documentation and three verified delivery archives are pending.')
target.write_text(json.dumps(dict(status='E2_ACCEPTANCE_DOCUMENTED_AFTER_COMPLETE_CHECK_ONLY',recorded_utc=datetime.now(timezone.utc).isoformat(),whole_instrumentation_seconds=durations,updated=updates),indent=2)+'\n',encoding='utf-8')
print('FINAL_E2_SCOPE_DOCUMENTED_NOT_YET_IMMUTABLE_CLOSURE_OR_COMMIT')
