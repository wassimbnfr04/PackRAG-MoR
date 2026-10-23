"""Record final E1 scope only after the complete fail-closed acceptance check passes."""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=HERE/'acceptance-document-update.json';assert not target.exists()
subprocess.run([sys.executable,'-X','utf8',str(HERE/'verify_and_record.py'),'--check-only'],cwd=ROOT,check=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
durations={}
for name,count in [('device-ui-query-0003',2),('device-query-controls-0001',2),('device-query-regression-0001',30),('device-query-policy-0001',26),('device-development-restore-0011',1)]:
    text=(M4/name/'instrumentation.txt').read_text(encoding='utf-8')
    match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    durations[name]=float(re.sub(r'\s','',match[1]).replace(',','.'))
stamp=datetime.now(timezone.utc).strftime('%d %B %Y %H:%M UTC')
summary=(f'E1 VERIFIED {stamp}: query/date/jurisdiction/current-law controls and owned submitted context/freshness pass. '
    f'Python1010 (run0014), host37 per final variant,548 Android/185 unchanged runtime inputs, retained real desktop walking14, '
    f'foreground UI2/{durations["device-ui-query-0003"]}s, actual ViewModel2/{durations["device-query-controls-0001"]}s, '
    f'full development30/{durations["device-query-regression-0001"]}s, compiled-policy26/{durations["device-query-policy-0001"]}s '
    f'and restoreddebug0035/consent1/{durations["device-development-restore-0011"]}s pass. '
    'All61 final structured original results are saved; both policy variants match43 retained tokenizer/admission and19 retained runtime-state comparisons, '
    'with D3 selection/origin/identity guards preserved. Every902 prior D3 public output and587 historical identity is unchanged. '
    'Original sandbox/UI/readiness failures remain FAIL with exact test-only scroll repair and byte-identical product-APK proof; no old run is relabeled. '
    'Close immutable ui-query-gate0002 and checkpoint before E2 source/pack details. Full M4/product remains incomplete: E2, E3, F, software evaluation, '
    'nondebuggable release, physical performance and final documentation/three archives remain. Owner authors final knowledge content; synthetic tests '
    'are not genuine licensing/review/calibration/gold or semantic-entailment proof. Phone mobile data/models/default registries preserved; no test is running.')
updates={}
def prepend(name,paragraph):
    p=ROOT/name;raw=p.read_bytes();text=raw.decode('utf-8-sig');first,rest=text.split('\n',1)
    revised=first+'\n\n'+paragraph+'\n'+rest
    p.write_text(revised,encoding='utf-8');updates[name]=dict(before_sha256=sha(raw),after_sha256=sha(p.read_bytes()))
prepend('STATUS.md',summary+'\n\nCurrent next action: immutable E1 closure/checkpoint, then M4E2 under the prewritten acceptance criteria. Earlier RUNNING/PAUSED/partial statements below are dated history, superseded by this acceptance.')
prepend('PLAN.md',summary+'\n\nRemaining dependency order: E2 captured source provenance and verified inactive pack details → E3 diagnostics/lifecycle/accessibility → F verified local assets and final M4 audit → M5/M6 software builder/calibration interfaces with test content → M7 software PackBench → M8 release/physical measurements/documentation/three verified public archives. Never start a later increment while a required gate is failing.')
prepend('DECISIONS.md',summary+'\n\nE1 uses exact validated input bytes and captured verified identities. Empty jurisdiction means no filter; freshness is advisory at the submitted date. Completed RuntimeTrace stays bound to that submission; edits and Activity recreation retain the original result context. Formatting/citation validation is not semantic entailment. The management repair only scrolls before the same assertion; exact product APKs and185 runtime inputs permit bounded reuse of the already executed Python/desktop results, never a claim of rerunning them. Compiled demo policy is independently tested and remains an instrumentable debug-signed test build, not the final release.')
prepend('docs/v1.3/M4E1_METHODS.md',summary+'\n\nFinal original runs above supersede pending observations below. Host37 includes the three new pure QueryPresentation methods. Foreground UI contains five new query-control cases plus seven retained management cases; ViewModel methods contain seven input/no-pack/cancel and four runtime cases; the new production control method contains three cases; restoration contains four consent cases. Functional wall times include separately labeled lazy initialization where reported and do not establish peak memory, throughput, thermal stability or a causal bottleneck.')
prepend('docs/v1.3/M4_INCREMENT_PLAN.md',summary)
prepend('docs/v1.3/M4_IMPLEMENTATION_LOG.md',summary)
prepend('docs/architecture-compliance-matrix.md',summary+'\n\nThe integrated UI clause remains IMPLEMENTING as a whole: E1 now verifies controls/captured context/freshness, while full source/pack details, diagnostics and assets remain unverified. Existing runtime subcontracts retain their original accepted evidence. No whole-product requirement is promoted solely because it compiles.')
target.write_text(json.dumps(dict(status='E1_ACCEPTANCE_DOCUMENTED_AFTER_COMPLETE_CHECK_ONLY',recorded_utc=datetime.now(timezone.utc).isoformat(),
    whole_instrumentation_seconds=durations,updated=updates),indent=2)+'\n',encoding='utf-8')
print('FINAL_E1_SCOPE_DOCUMENTED_NOT_YET_IMMUTABLE_CLOSURE_OR_COMMIT')
