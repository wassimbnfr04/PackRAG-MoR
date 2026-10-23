"""Whitelist-only F2 checkpoint; preserve unrelated working changes and binary bytes."""
import argparse,hashlib,json
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=HERE.parent
BASE='ccc14de708bf2d46d2791875a8cca9344fc25f48'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
reader=M4/'source-details-gate-0001/checkpoint_git.py'
accepted=read(M4/'source-details-gate-0001/checkpoint-files.json')['files']
assert sha(reader)==accepted[reader.relative_to(ROOT).as_posix()]
spec=spec_from_file_location('f2_binary_git',reader);module=module_from_spec(spec);spec.loader.exec_module(module)
git=module.git;blobs=module.blobs
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','stage','verify']);args=parser.parse_args()
manifest=HERE/'checkpoint-files.json'
blocked={'.private','build','.gradle','.cxx','.kotlin','__pycache__','temp','stage','runner-temp','host-temp','pytest-temp'}
forbidden={'.apk','.pyc','.class','.seed','.seed32','.pem','.key','.keystore','.jks','.gguf','.onnx','.safetensors'}
def verify(files):
    for name,value in files.items():
        p=ROOT/name;assert p.is_relative_to(ROOT) and not blocked.intersection(part.lower() for part in Path(name).parts) and p.suffix.lower() not in forbidden,name
        for part in [p,*p.parents]:
            assert not part.is_symlink(),part
            if part==ROOT:break
        assert p.resolve().is_relative_to(ROOT) and sha(p)==value,name
if args.mode=='prepare':
    assert not manifest.exists()
    gate=read(HERE/'gate.json');assert gate['status']=='M4F2_PINNED_PRIVATE_ASSET_IMPORT_ATOMICITY_CANCEL_RESTART_PICKER_AND_REGRESSIONS_VERIFIED_NOT_FULL_M4_OR_PRODUCT'
    prior=read(M4/'asset-readiness-gate-0001/gate.json')
    old={**prior['source_sha256'],**prior['android_source_sha256']};current={**gate['source_sha256'],**gate['android_source_sha256']}
    assert not old.keys()-current.keys()
    delta={name:value for name,value in current.items() if old.get(name)!=value}
    files={**gate['output_sha256'],**delta}
    for name in ['STATUS.md','PLAN.md','DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/v1.3/M4F3_ACCEPTANCE_PREPARATION.md']:
        files[name]=sha(ROOT/name)
    for p in sorted((ROOT/'docs/v1.3').glob('M4F2*.md')):files[p.relative_to(ROOT).as_posix()]=sha(p)
    for name in ['gate.json','checkpoint_f2_0001.py']:files[(HERE/name).relative_to(ROOT).as_posix()]=sha(HERE/name)
    # Capture terminal closure/index records written after gate output collection.
    for pattern in ['*.json','*.py']:
        for p in sorted(HERE.glob(pattern)):files[p.relative_to(ROOT).as_posix()]=sha(p)
    verify(files)
    assert git('rev-parse','HEAD').stdout.decode().strip()==BASE and not git('diff','--cached','--name-only').stdout.strip()
    prior_files=read(M4/'asset-readiness-gate-0001/checkpoint-files.json')['files']
    previous=blobs('HEAD',sorted(prior_files))
    for name,value in prior_files.items():assert previous[name] is not None and hashlib.sha256(previous[name]).hexdigest()==value,name
    manifest.write_text(json.dumps(dict(purpose='EXACT_ACCEPTED_F2_SOURCE_PUBLIC_EVIDENCE_AND_DURABLE_STATE',prior_head=BASE,tested_source_delta=delta,
        files=dict(sorted(files.items())),scope='Only explicit accepted public whitelist staged. APKs bound as local binaries, weights/exports/private custody/cache excluded. Historical failed attempts remain unchanged, unrelated dirty files remain outside checkpoint. F2 checkpoint is not M4 or product completion.'),indent=2)+'\n',encoding='utf-8')
    print('PASS_F2_CHECKPOINT_WHITELIST_PREPARED',len(files),len(delta),flush=True)
else:
    record=read(manifest);files=dict(record['files']);files[manifest.relative_to(ROOT).as_posix()]=sha(manifest)
    verify(files)
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
        print('PASS_EXACT_F2_WHITELIST_STAGED',len(files),len(changed),flush=True)
    else:
        head=git('rev-parse','HEAD').stdout.decode().strip();assert head!=BASE and git('rev-parse','HEAD^').stdout.decode().strip()==BASE
        current=blobs('HEAD',sorted(files))
        for name,value in files.items():assert current[name] is not None and hashlib.sha256(current[name]).hexdigest()==value,name
        assert not git('diff','--cached','--name-only').stdout.strip()
        print(json.dumps(dict(status='PASS_EXACT_F2_COMMITTED_CHECKPOINT_BYTES',head=head,whitelist_files=len(files))),flush=True)
