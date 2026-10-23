"""After terminal import PASS, preserve three exact public test leaves then remove only those leaves/empty dirs."""
import hashlib,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;ADB=ROOT/'vendor/platform-tools/adb.exe'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
parent=HERE/'device-local-asset-final-import-debug-0002-execution.json'
assert read(parent)['status']=='PASS_FINAL_SOURCE_IMPORT_7_METHODS_54_CONTROLS_NOT_FULL_F2'
proof=HERE/'interrupted-visual-root-inspection-0003.json';assert read(proof)['command']['returncode']==0
target=HERE/'interrupted-visual-root-cleanup-0001.json';directory=HERE/'interrupted-visual-public-leaves-0001'
assert not target.exists() and not directory.exists()
name='f2-visual-ae60e430-f540-4024-aa8f-41fb9bca4353';base='files/'+name
progress=ROOT/'artifacts/v1.3/m4/device-local-asset-import-visual-0002/failure-original-adb/m4-local-asset-import-visual-progress.json'
assert read(progress)['test_id']==name and read(progress)['status']=='RUNNING' and read(progress)['cases']==[]
leaves={
 'models/chat_template.jinja':(5443,'ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'),
 'registry/registry.lock':(0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
 'registry/registry.sqlite':(57344,'4d202e56f4256eb3b4b59d045d19d5a89be946d384edf9cefe27b5bcef3cc70c')}
record=dict(status='RUNNING_KNOWN_TEST_ROOT_CLEANUP_NOT_F2_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),
 parent_sha256=sha(parent),inspection_sha256=sha(proof),failed_progress_sha256=sha(progress),runner_sha256=sha(Path(__file__)),commands=[],saved_public_originals={})
def save():target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def shell(script):
    argv=[str(ADB),'-s','R3CT908DHHR','shell','run-as org.packrag.product sh -c '+shlex.quote(script)]
    out=subprocess.run(argv,capture_output=True,timeout=30)
    record['commands'].append(dict(argv=argv,returncode=out.returncode,stdout=out.stdout.decode('utf-8',errors='replace'),stderr=out.stderr.decode('utf-8',errors='replace')));save()
    assert out.returncode==0,'Do not proceed after preflight/delete failure';return out.stdout
prefix='set -eu; test -d files; test ! -L files; root='+base+'; test -d "$root"; test ! -L "$root"; test "$(readlink -f "$root")" = /data/user/0/org.packrag.product/'+base+'; '
checks=prefix+'test "$(ls -A "$root")" = "models\nregistry"; '
for path in ['models','registry','registry/.staging','registry/packs']:
    checks+='test -d "$root/'+path+'"; test ! -L "$root/'+path+'"; '
checks+='test "$(ls -A "$root/models")" = chat_template.jinja; test "$(ls -A "$root/registry")" = ".staging\npacks\nregistry.lock\nregistry.sqlite"; '
checks+='test -z "$(ls -A "$root/registry/.staging")"; test -z "$(ls -A "$root/registry/packs")"; '
for path,(size,value) in leaves.items():
    checks+='test -f "$root/'+path+'"; test ! -L "$root/'+path+'"; test "$(wc -c < "$root/'+path+'")" -eq '+str(size)+'; test "$(sha256sum "$root/'+path+'" | cut -d " " -f 1)" = '+value+'; '
try:
    shell(checks+'echo EXACT_CLOSED_TEST_ROOT_PREFLIGHT_PASS');directory.mkdir()
    for path,(size,value) in leaves.items():
        # Only the preflighted exact public template and empty synthetic registry/lock;
        # no model weights, original experiment reports or private custody read.
        argv=[str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat',base+'/'+path]
        out=subprocess.run(argv,capture_output=True,timeout=30)
        dest=directory/path.replace('/','__');dest.write_bytes(out.stdout)
        assert out.returncode==0 and len(out.stdout)==size and sha(dest)==value
        record['saved_public_originals'][path]=dict(path=str(dest.relative_to(ROOT)).replace('\\','/'),bytes=size,sha256=value);save()
    # Revalidate the entire closed tree immediately before any deletion. Explicit
    # leaf unlink + rmdir refuses any unexpected child; no recursive delete/glob.
    script=checks+'rm -- "$root/models/chat_template.jinja" "$root/registry/registry.lock" "$root/registry/registry.sqlite"; '
    script+='rmdir -- "$root/models" "$root/registry/.staging" "$root/registry/packs" "$root/registry" "$root"; test ! -e "$root"; test ! -L "$root"; echo EXACT_KNOWN_TEST_ROOT_REMOVED'
    shell(script)
    record.update(status='PASS_EXACT_KNOWN_INTERRUPTED_TEST_ROOT_PUBLIC_BYTES_PRESERVED_AND_REMOVED_NOT_FULL_F2',
      scope='Only exact recorded failed-test UUID after terminal background PASS, full no-follow closed-tree preflight and saved/hash-verified62787 public bytes; three explicit unlinks and empty-directory rmdir, no recursion. Original experiment logs/JSON/PNGs untouched, readonly source4 retained and no owner default files/radios/settings changed. Source4/owner50 post-checks and whole F2 closure remain separate.')
except Exception as failure:
    record.update(status='FAIL_HOLD_F2_CLOSURE_NO_FURTHER_CLEANUP',failure_type=type(failure).__name__,failure_message=str(failure));raise
finally:record['finished_utc']=datetime.now(timezone.utc).isoformat();save()
print(record['status'],flush=True)
