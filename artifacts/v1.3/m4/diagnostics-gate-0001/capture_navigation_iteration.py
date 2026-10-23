"""Bind actual original visual review and freeze tested navigation inputs before further edits."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(HERE/'navigation-ui-repaired-execution.json')['status']=='PASS_E3_NAVIGATION_UI_ORIGINALS_PNGS_NOT_VISUAL_OR_FULL_E3'
run=M4/'device-ui-diagnostic-navigation-0002';data=read(run/'m4-diagnostic-navigation.json');collector=read(run/'collected-results.json')
original=run/'original-adb/m4-diagnostic-navigation.json';assert sha(original)==collector['saved_sha256'][original.name]
assert read(original)==data and data['status']=='PASS' and len(data['cases'])==7 and all(r['passed'] for r in data['cases'])
rows={}
for name,row in data['visual_png'].items():
    p=run/'original-adb'/name;assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'];rows[name]=row
visual=dict(status='PASS_REPAIRED_DIAGNOSTIC_AND_CANONICAL_TESTED_VIEWPORT',recorded_utc=datetime.now(timezone.utc).isoformat(),images=rows,
    review_method='Both exact original PNGs inspected with view_image; not inferred from JUnit or tags.',
    home='No IME. Prefill428, evidence256, emitted153 including terminal, reasoning133, remaining20, first emitted43812.023ms and backend decode21890.422ms are visibly labelled and readable above navigation. Captured functional timing only, not visible answer latency or performance acceptance.',
    source='Complete canonical Aster-9 sentence including74°C and signed assertion/unknown attribution labels readable above navigation. Tested viewport only.',
    initial='Original0001 automated PASS and independent visual FAIL remain immutable; no old screenshot was edited or relabelled.')
target=HERE/'navigation-visual-repaired.json';assert not target.exists();target.write_text(json.dumps(visual,indent=2)+'\n',encoding='utf-8')
source=read(M4/'build-0047/source-at-build-start.json')['files'];old=read(M4/'build-0041/source-at-build-start.json')['files']
assert len(source)==573
delta={n:v for n,v in source.items() if old.get(n)!=v}
assert all(sha(ROOT/n)==v for n,v in source.items())
folder=HERE/'navigation-iteration-sources';folder.mkdir(exist_ok=False)
for n,v in delta.items():
    assert n.startswith('product/android/') and Path(n).suffix=='.kt'
    p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==v
life=M4/'device-diagnostic-lifecycle-0001';lc=read(life/'collected-results.json');lp=life/'original-adb/m4-diagnostic-lifecycle.json'
assert sha(lp)==lc['saved_sha256'][lp.name]
record=dict(status='PASS_E3_LIFECYCLE_AND_VISUAL_ITERATION_NOT_COMPLETE_E3',build='build-0047',host_methods=53,android_inputs=573,
    source_snapshots=delta,original_ui_sha256=sha(original),original_lifecycle_sha256=sha(lp),visual=visual['status'],
    lifecycle_scope='Actual0046 run retained with whole product APK byte equality to0047 and unchanged lifecycle source; not relabelled as a0047 rerun.',
    pending='New compiled-policy diagnostics, full retained regressions/parity/restoration/history/closure and checkpoint.')
target=HERE/'navigation-iteration-acceptance.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
message='E3 current10 October19:40 UTC: repaired foreground diagnostic-navigation0002 passes one method/seven controls; exact originals saved and both PNGs actually inspected PASS (counts/timing labels and complete canonical text readable above navigation, no IME). Build0047 host53/573 inputs; product APK byte-identical0046, with only the capture test changed. Actual lifecycle0001/seven controls retained under this exact proof. Initial UI visual FAIL, device owner-registry byte-change FAIL, build0044 and Python0016 failures remain immutable. No phone test running. Next: compiled-policy actual diagnostics with approved existing schema-only synthetic fixture, then full retained gates/parity/restoration/closure. E3 not complete; F/later held. Owner may use phone with USB/mobile data unchanged; keep PackRAG closed during guarded background tests. Final knowledge content owner supplied.\n\n'
status=ROOT/'STATUS.md';text=status.read_text(encoding='utf-8-sig');status.write_text(text.replace('# PackRAG-MoR v1.3 status\n\n','# PackRAG-MoR v1.3 status\n\n'+message,1),encoding='utf-8')
for name in ['docs/v1.3/M4E3_METHODS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md']:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write('\n\n10 October19:40 UTC — '+message+'New navigation-visual-repaired.json binds both original PNG identities to actual image review; navigation-iteration-acceptance.json and source snapshots freeze all E3 changed Kotlin inputs before further Android edits. Scope remains lifecycle/navigation only, not complete E3.\n')
print(record['status'],len(delta),'frozen Kotlin deltas')
