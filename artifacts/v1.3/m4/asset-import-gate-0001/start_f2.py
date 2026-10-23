"""Bind accepted F1/current public custody before any F2 runtime edit."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
BASE='ccc14de708bf2d46d2791875a8cca9344fc25f48'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def check(mapping):
    for name,value in mapping.items():
        p=ROOT/name
        assert not {'.private','temp','stage','runner-temp','host-temp','pytest-temp'}.intersection(Path(name).parts)
        assert p.suffix.lower() not in {'.seed','.seed32','.key','.jks','.pem','.keystore'}
        assert p.resolve().is_relative_to(ROOT) and not p.is_symlink() and sha(p)==value,name
target=HERE/'before.json';assert not target.exists()
argv=['git','--no-optional-locks','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD']
head=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,check=True);assert head.stdout.strip()==BASE
f1_path=M4/'asset-readiness-gate-0001/gate.json';f1=read(f1_path)
assert f1['status']=='M4F1_LOCAL_ASSET_READINESS_NATIVE_RECOVERY_AND_UI_VERIFIED_NOT_FULL_M4_OR_PRODUCT'
assert len(f1['source_sha256'])==188 and len(f1['android_source_sha256'])==579
check(f1['source_sha256']);check(f1['android_source_sha256']);check(f1['output_sha256'])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];assert len(history)==587;check(history)
expected=read(M4/'asset-readiness-gate-0001/owner-at-closure.json')['owner_public_file_sha256'];assert len(expected)==50
assert all(re.fullmatch(r'[A-Za-z0-9_.@/-]+',name) and '.private' not in Path(name).parts for name in expected)
adb_argv=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','shell','run-as','org.packrag.product','sha256sum',*['files/'+name for name in sorted(expected)]]
out=subprocess.run(adb_argv,capture_output=True,check=True,timeout=60);observed={}
for line in out.stdout.decode('utf-8').splitlines():
    value,name=line.split(maxsplit=1);assert re.fullmatch('[0-9a-f]{64}',value) and name.startswith('files/');observed[name[6:]]=value
assert observed==expected
sources={}
for name in ['ProductSession.kt','PackRagViewModel.kt','MainActivity.kt','LocalAssetsScreen.kt']:
    relative='product/android/app/src/main/java/org/packrag/product/'+name;p=ROOT/relative
    destination=HERE/'before-sources'/relative;destination.parent.mkdir(parents=True,exist_ok=True);assert not destination.exists();destination.write_bytes(p.read_bytes());sources[relative]=sha(p)
record=dict(status='PASS_F2_PREIMPLEMENTATION_PUBLIC_CUSTODY_PHONE_GUARD_NOT_F2_IMPLEMENTATION_OR_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    base_head=BASE,prior_f1_gate_sha256=sha(f1_path),prior_f1_outputs_unchanged=len(f1['output_sha256']),historical_unchanged=587,
    prior_android_inputs=579,unchanged_python_runtime_inputs=188,before_sources_sha256=sources,owner_public_file_sha256=observed,
    commands=[dict(argv=argv,returncode=head.returncode,stdout=head.stdout,stderr=head.stderr),dict(argv=adb_argv,returncode=out.returncode,stdout=out.stdout.decode('utf-8'),stderr=out.stderr.decode('utf-8',errors='replace'))],
    scope='F1 committed421-file exact whitelist verified separately. This new step reads exact pre-existing public mappings and known50 owner paths only; no new full phone directory enumeration or private custody access. F1 whole-session registry exception and all failures remain immutable. F2 starts with a minimal actual granted-content-URI template import/atomic private commit/real generation walking path before expansion. Final knowledge content remains owner supplied; radios remain unmodified.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
note=f'Current milestone M4F2 at {record["recorded_utc"]}, following accepted F1 checkpoint {BASE}. F1 passes all required62 host methods per variant,579 Android/188 unchanged Python identities,16 saved final phone originals and two actual inspected PNGs; its exact421-file public whitelist is committed and verified. New F2 preimplementation check confirms all {record["prior_f1_outputs_unchanged"]} F1 output hashes,587 historical identities and known50 phone paths before edits. First implement the smallest correct integrated granted-content-URI template import into its fixed private slot, bounded staging/size/hash/sync/atomic commit and actual post-import LFM2.5 answer. Then harden cancellation/restart/fault/other slots and actual system-picker/progress UI under the prewritten acceptance. F2 is not implemented or accepted yet; do not progress F3 before all F2 gates pass. Preserve F1 registry exception=false whole-session preservation, all old failed outputs and owner models/partials/default registries. Final knowledge packs remain owner supplied, mobile data stays on; F3/F4/later software/release/delivery remain.'
for name in ['STATUS.md','PLAN.md']:
    p=ROOT/name;header,rest=p.read_text(encoding='utf-8').split('\n',1);p.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print(record['status']);print('Accepted F1 output files',record['prior_f1_outputs_unchanged'])
