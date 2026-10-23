"""Exact accepted F1 whitelist: prepare, stage only that delta, verify actual commit."""
import argparse,hashlib,json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
BASE='ac98b4fa6b9fd89b9f0f53023cb1f6115408567f'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
reader=M4/'source-details-gate-0001/checkpoint_git.py'
accepted=read(M4/'source-details-gate-0001/checkpoint-files.json')['files'];assert sha(reader)==accepted[reader.relative_to(ROOT).as_posix()]
spec=spec_from_file_location('f1_binary_git',reader);module=module_from_spec(spec);spec.loader.exec_module(module)
git=module.git;blobs=module.blobs
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','stage','verify']);args=parser.parse_args()
manifest=HERE/'checkpoint-files.json'
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp','pytest-temp'}
forbidden={'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'}
def verify_paths(files):
    for name,value in files.items():
        p=ROOT/name;assert not blocked.intersection(part.lower() for part in Path(name).parts) and p.suffix.lower() not in forbidden,name
        assert not p.is_symlink() and p.resolve().is_relative_to(ROOT) and sha(p)==value,name
if args.mode=='prepare':
    assert not manifest.exists();gate=read(HERE/'gate.json')
    assert gate['status']=='M4F1_LOCAL_ASSET_READINESS_NATIVE_RECOVERY_AND_UI_VERIFIED_NOT_FULL_M4_OR_PRODUCT'
    prior=read(M4/'diagnostics-gate-0001/gate.json')
    baseline={**prior['source_sha256'],**prior['android_source_sha256']}
    current={**gate['source_sha256'],**gate['android_source_sha256']};assert not baseline.keys()-current.keys()
    delta={name:value for name,value in current.items() if baseline.get(name)!=value}
    assert len(delta)==8
    files={**gate['output_sha256'],**delta}
    for name in ['STATUS.md','PLAN.md','DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md',
        'docs/v1.3/M4F1_ASSET_CONTRACT.md','docs/v1.3/M4F1_DEVICE_VALIDATION.md','docs/v1.3/M4F2_IMPORT_ACCEPTANCE_PREPARATION.md']:
        files[name]=sha(ROOT/name)
    for p in HERE.glob('*.json'):files[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in HERE.glob('*.py'):files[p.relative_to(ROOT).as_posix()]=sha(p)
    verify_paths(files);assert git('rev-parse','HEAD').stdout.decode().strip()==BASE
    assert not git('diff','--cached','--name-only').stdout.strip()
    prior_files=read(M4/'diagnostics-gate-0001/checkpoint-files.json')['files']
    original=blobs('HEAD',sorted(prior_files))
    for name,value in prior_files.items():assert original[name] is not None and hashlib.sha256(original[name]).hexdigest()==value,name
    manifest.write_text(json.dumps(dict(purpose='EXACT_ACCEPTED_F1_SOURCE_PUBLIC_EVIDENCE_AND_DURABLE_STATE',prior_head=BASE,
        tested_source_delta=delta,files=dict(sorted(files.items())),scope='Public whitelist only. APKs are separately SHA-bound local artifacts; weights/exports/private custody are excluded from Git. Prior failures stay immutable.'),indent=2)+'\n',encoding='utf-8')
    print('PASS_F1_CHECKPOINT_WHITELIST_PREPARED',len(files))
else:
    record=read(manifest);files=dict(record['files']);files[manifest.relative_to(ROOT).as_posix()]=sha(manifest)
    files[Path(__file__).relative_to(ROOT).as_posix()]=sha(Path(__file__))
    verify_paths(files)
    if args.mode=='stage':
        assert git('rev-parse','HEAD').stdout.decode().strip()==BASE and not git('diff','--cached','--name-only').stdout.strip()
        old=blobs('HEAD',sorted(files));changed={name for name,value in files.items() if old[name] is None or hashlib.sha256(old[name]).hexdigest()!=value}
        pathspec=HERE/'checkpoint-pathspec.utf8.nul';assert not pathspec.exists()
        try:
            pathspec.write_bytes(b''.join(name.encode('utf-8')+b'\0' for name in sorted(files)))
            git('--literal-pathspecs','add','--pathspec-from-file='+str(pathspec),'--pathspec-file-nul')
        finally:pathspec.unlink()
        staged=set(git('diff','--cached','--name-only','-z').stdout.decode().split('\0'))-{''};assert staged==changed
        index=blobs('',sorted(files))
        for name,value in files.items():assert index[name] is not None and hashlib.sha256(index[name]).hexdigest()==value,name
        assert git('branch','--show-current').stdout.decode().strip()=='codex/packrag-v1.3'
        print('PASS_EXACT_F1_WHITELIST_STAGED',len(files),len(changed))
    else:
        head=git('rev-parse','HEAD').stdout.decode().strip();assert head!=BASE and git('rev-parse','HEAD^').stdout.decode().strip()==BASE
        current=blobs('HEAD',sorted(files))
        for name,value in files.items():assert current[name] is not None and hashlib.sha256(current[name]).hexdigest()==value,name
        assert not git('diff','--cached','--name-only').stdout.strip()
        print(json.dumps(dict(status='PASS_EXACT_F1_COMMITTED_CHECKPOINT_BYTES',head=head,whitelist_files=len(files))))
