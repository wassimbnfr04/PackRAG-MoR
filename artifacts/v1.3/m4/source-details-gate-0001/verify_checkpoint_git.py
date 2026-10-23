"""Read-only real Git checks for the checkpoint's binary-safe batch reader."""
import hashlib,json
from pathlib import Path
from checkpoint_git import git,blobs,ROOT
HERE=Path(__file__).parent;target=HERE/'checkpoint-git-reader-verification.json';assert not target.exists()
prior=json.loads((ROOT/'artifacts/v1.3/m4/ui-query-gate-0002/gate.json').read_text(encoding='utf-8'))
binary=next(name for name in prior['android_source_sha256'] if name.endswith('.kpack'))
existing=['product/android/app/build.gradle.kts','docs/v1.3/M4E1_METHODS.md',binary]
missing='__checkpoint_probe_missing__ with spaces.missing'
assert git('show','HEAD:'+missing,check=False).returncode!=0
names=[existing[0],missing,*existing[1:]]
actual=blobs('HEAD',names);assert actual[missing] is None
rows=[]
for name in existing:
    expected=git('show','HEAD:'+name).stdout;assert actual[name]==expected
    rows.append(dict(path=name,bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest()))
index=blobs('',existing)
for name in existing:assert index[name]==git('show',':'+name).stdout
record=dict(status='PASS_READ_ONLY_REAL_GIT_BINARY_TEXT_MISSING_AND_INDEX_COMPARISON_NOT_STAGING_OR_COMMIT',
    cases=rows,missing_path_with_spaces=True,zero_input=blobs('HEAD',[])=={},
    library_sha256=hashlib.sha256((HERE/'checkpoint_git.py').read_bytes()).hexdigest(),
    scope='Exact byte comparison to independent git show on text/binary/missing and current index; no index or repository mutation.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
