"""Write accurate F1 completion documents only after the actual complete acceptance check.

The immutable gate and exact Git checkpoint follow; never fabricate missing results.
"""
import hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'completion-documentation-0001.json';assert not target.exists()
index=ROOT/'docs/v1.3/M4F1_EVIDENCE_INDEX.md';assert not index.exists()
sequence=read(HERE/'policy-and-restoration-recovery-0001.json')
assert sequence['status']=='PASS_F1_LEGACY_POLICY_VERIFICATION_RECOVERY_RESTORATION_AND_FINAL_GUARDS_NOT_CLOSURE'
argv=[sys.executable,'-X','utf8',str(HERE/'check_acceptance.py'),'--check-only']
result=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
stdout=HERE/'completion-check-only-0001.stdout.txt';stderr=HERE/'completion-check-only-0001.stderr.txt'
assert not stdout.exists() and not stderr.exists();stdout.write_text(result.stdout,encoding='utf-8');stderr.write_text(result.stderr,encoding='utf-8')
assert result.returncode==0 and 'ALL_F1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_WRITTEN' in result.stdout,'Hold F1; save failure, repair, use a new versioned completion attempt'
runs=[read(HERE/(name+'-verified.json')) for name in ['device-local-assets-0002','device-local-assets-adjacent-0002','device-local-assets-policy-0001','device-local-assets-policy-adjacent-0001']]
visual=read(HERE/'ui-visual-0001.json');failure=read(HERE/'adjacent-terminal-guard-diagnosis.json')
def seconds(folder):
    text=(folder/'instrumentation.txt').read_text(encoding='utf-8');match=re.search(r'Time:\s*([0-9][0-9\s\u00a0\u202f]*[.,][0-9]+)',text);assert match
    return float(re.sub(r'\s','',match[1]).replace(',','.'))
ui_seconds=seconds(M4/'device-local-assets-ui-0001');restore_seconds=seconds(M4/'device-local-assets-development-restore-0001')
record=dict(status='PASS_F1_ACCEPTANCE_CHECK_AND_DOCUMENTATION_GATE_AND_CHECKPOINT_STILL_REQUIRED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    command=dict(argv=argv,returncode=result.returncode,stdout_sha256=sha(stdout),stderr_sha256=sha(stderr)),phone_runs=runs,
    ui_seconds=ui_seconds,restoration_seconds=restore_seconds,whole_session_default_registry_bytes_preserved=False,
    scope='All required actual F1 checks passed before these documents are written. F1 immutable gate and exact public Git checkpoint still follow. No full M4/product, fresh Python, final content, domain expertise, calibration or physical-performance acceptance claimed.')
rows='\n'.join(f'| `{row["run"]}` | {row["variant"]} | {row["methods"]} | {row["whole_instrumentation_seconds"]} | {sum(v["cases"] for v in row["observations"].values())} |' for row in runs)
text=f'''# M4F1 evidence and interpretation

Recorded {record['recorded_utc']} after the complete fail-closed F1 acceptance check passed. Immutable closure and exact Git checkpoint must still be recorded. This increment verifies local-asset readiness and native/UI recovery; it does not complete M4 or the product. Final knowledge-pack content remains owner supplied.

## What changed and what executed

Eight source deltas from accepted E3: five new fixed-slot verifier/screen/host/device/UI files and three modified session/ViewModel/activity files. The four existing public pins and private paths are unchanged. Read-only verification checks regular-file size and bounded streaming SHA256 without following asset symlinks or initializing either model. No-active-pack queries skip asset/model initialization. Active queries with unavailable assets fail before constructors. Cold queries check the four files; model constructors retain independent hash checks. A completed failed-file observation survives session recovery with its original check timestamp. Explicit readiness checks preserve the prior answer, submitted context, trace and completion identity. A bad check releases warm models; restoring the copied template permits real native recovery. The source-at-build and closure inventories bind exactly 579 Android inputs; 188 Python runtime inputs are unchanged.

Matched current debug0056/demo0057 builds each pass the same 62 host unit/interface methods, including nine new independent verifier cases. These are 62 tests per build, not124 distinct tests. Both APK pairs are SHA-bound with approved trust-store identity, no product INTERNET permission and the actual unchanged arm64 JNI library. Demo is instrumentable and is not a final nondebuggable release.

Physical tests use newly owned isolated registries and, when negative asset mutation is needed, independently owned copies of all four actual artifacts. StatFs must permit their exact 2,009,206,667-byte sum plus64MiB. Only a copied template is deliberately corrupted/restored. Native/session readers close before exact owned-root cleanup; leaf, parent and root symlink refusal is exercised on the phone. Owner models, legacy partials and default registries are never intentionally replaced by these test preparations.

| Accepted original-report run | Build policy | JUnit methods | Whole instrumentation seconds | Case rows |
| --- | --- | ---: | ---: | ---: |
{rows}
| `device-local-assets-ui-0001` | debug | 1 | {ui_seconds} | 5 |
| `device-local-assets-development-restore-0001` | debug | 1 | {restore_seconds} | 4 |

All16 final method originals are saved before APK switches and checked against their parsed reports, selected source/APKs and actual terminal JUnit PASS. Case rows overlap across variants and are not independent domain questions. Core methods exercise actual four-file readiness, missing/corrupt/symlink rejection, real cold/warm/recovered LFM2.5 output, zero-generation jurisdiction abstention and ViewModel/result ownership. Adjacent methods rerun retained diagnostics, live native replacement/cancellation/recovery, query controls and source details. Exact adjacent case IDs match accepted E3 contracts. Retained1034 Python tests and earlier desktop/security/retrieval results remain immutable under identical188 Python runtime inputs; they are not new F1 full-suite runs. Fresh full regressions remain required at F4.

The first policy report-checker attempt raises KeyError after all three policy adjacent phone methods and their original collection passed. Its first source, exact stderr and failed sequence remain immutable. Two retained legacy policy reports omit per-method owner hashes; SourceDetailsPolicy also omits network metadata. The corrected checker verifies their exact accepted E3 schemas and unchanged test source instead of inventing missing fields. An independent actual known50-file snapshot after the entire policy phase and before restoration matches the DiagnosticPolicy original and post-launch baseline. That snapshot is not described as a per-method assertion for the two omitted schemas. Compiled product no-INTERNET identity remains required. Successful checker recovery then permits development restoration; no app, test, APK or original report changed for this checker repair.

The real UI question returns “The maximum continuous operating temperature of the Aster-9 is 74 °C [S1].” The five UI assertions cover actual file checking without model initialization, page recreation/system Back, integrated retrieval/generation/output validation, owned answer preservation and canonical-source navigation. Both original1080×2316 PNGs were actually viewed at original detail. The generator pin/sizes/timestamp and template/tokenizer pins/sizes/timestamps are readable in the captured viewports; encoder label/path/status are visible, while its size/hash/timestamp continue below the second frame. No unseen pixels, full-page coverage or every accessibility configuration is claimed. See `ui-visual-0001.json` for exact visible-field scope.

## Failed attempts and the owner-registry exception

First device-local-assets0001 on0055 remains FAIL: three methods/two test-setup Files.createLink AccessDenied failures in20.859s, before positive model verification/generation. Its one completed negative method/five controls and original report are retained. No native-positive result is inferred from the failed methods. Only two test helpers changed: independently owned real-artifact copies with a space guard, and no-follow UI traversal. The entire debug product APK is byte-identical0055→0056. Both current variants were rebuilt and actually rerun.

First adjacent0001 remains FAIL: five methods/one final owner-file guard failure in907.664s. Exactly `packs/registry.sqlite` changes from e967352d73a4d69777f8030e2f4a8578347bd667861ba7b0a0f3775ecaae4a81 to cf140bbf898aea7eb194406fa440e916cd2d746bb77b222a7c447f3f0e28ed10; all49 other guarded public files and the50 path names agree. Four genuinely completed passing originals are retained separately. The failed query-runtime phone JSON is parsed-equal to an older E3 report and is explicitly stale, never promoted to a new PASS.

During the failed method, system activity logs record ordinary MAIN/LAUNCHER PackRAG MainActivity startup from UID10155, separately resolved to Samsung launcher. This does not prove who launched it or what caused the DB change. Only the current post-change SQLite snapshot exists; read-only integrity is ok, while old/new logical equivalence remains unproved. No owner DB was restored, repaired, cleared or uninstalled. After every running test ended, target-only force-stop and explicit50-file guards preserved the post-change state. The owner agreed to keep PackRAG closed. The unchanged source/APKs/assertions then passed adjacent0002.

Consequently whole-F1-session default-registry byte preservation is FALSE. Development core0002 preserves the pre-launch e967 baseline. All later accepted adjacent/policy/UI runs and the final known50-file check preserve the explicit cf140 post-launch baseline. The production default registry and model/partial files remain unchanged. Final known-path checking is not represented as a new full directory enumeration. Earlier E3 exceptions also remain unchanged. Forensics, commands, maps, hashes and scope are in adjacent-terminal-guard-diagnosis.json, guarded-retry-preparation.json and owner-at-closure.json.

The first local record-helper attempt failed before writes because it expected the still-running driver execution manifest too early. Its exact pre-repair source and typed error are retained; the corrected record binds actual saved TestRunner start observation. This is a recording-helper failure, not a phone test. The unexecuted UI readiness power assertion was corrected from a truthy literal to membership in actual observed Awake lines before UI execution. No product assertion was relaxed.

## Interpretation and remaining work

All prior1131 E3 output and587 historical evidence hashes remain unchanged. Test packs are synthetic software fixtures, including approved-key schema-only calibration assertions; this is not real content licensing, reviewed calibration, held-out domain accuracy or general expert capability. Citation structure and one supported fictional answer do not prove semantic entailment on arbitrary questions. No raw discarded reasoning is persisted in these reports. Mobile data stayed on; no-INTERNET application behavior is not radio isolation. Whole instrumentation times include setup/copies/hashes/assertions and are not hardware benchmarks or causal bottleneck measurements.

After exact F1 closure/checkpoint, implement F2 actual system-picker/content-URI bounded staging, verified atomic private commit, serialized reader release and cancellation/restart/fault controls; then F3 normative pack/chip/progress/accessibility presentation and F4 fresh complete M4 regression/parity. Software builder/calibration interfaces, software PackBench, nondebuggable release/physical measurements and final documentation/three archives remain. Owner authors final knowledge packs.
'''
index.write_text(text,encoding='utf-8')
note=f'M4F1 acceptance checks pass at {record["recorded_utc"]}: matched62 host tests per variant/579 Android and188 unchanged Python inputs; development core3/adjacent5, approved-only core3/adjacent3, actual UI1/five controls and restored development consent1/four controls. All16 final original reports and two manually inspected PNGs are saved. Final known50 public file guards match the explicit post-launch baseline. Whole-session default-registry byte preservation remains false and both original setup/guard failures remain immutable. Earlier1131 E3/587 historical files are unchanged. Detailed methods/results/limits are in M4F1_EVIDENCE_INDEX.md. Record immutable gate and exact public checkpoint before F2. This is F1 only; F2/F3/F4/later software/release/delivery remain. Owner supplies final knowledge content; mobile data stays on.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;head,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(head+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n\n'+text+'\n')
record['evidence_index_sha256']=sha(index);target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
