"""New owned test-UID source copies only; model bytes never enter a host subprocess output."""
import argparse,hashlib,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
SLOTS=[('generator','LFM2.5-2.6B-QAD-Q4_0.gguf',1593894944,'a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03'),
('template','chat_template.jinja',5443,'ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'),
('tokenizer','granite/tokenizer.json',25301672,'4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f'),
('encoder','granite/onnx/model.onnx',390004608,'68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70')]
NAMESPACE='files/f2-full-assets-0001';MAGIC='PackRAG F2 full assets v1\n'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate_script():
    names=' '.join('full-'+name+'.asset' for name,_,_,_ in SLOTS)
    checks=[f'set -eu; root={NAMESPACE}; test -d files; test ! -L files; test -d "$root"; test ! -L "$root"',
        'test -f "$root/owner.marker"; test ! -L "$root/owner.marker"',
        f'test "$(wc -c < "$root/owner.marker")" -eq {len(MAGIC.encode())}',
        'test "$(cat "$root/owner.marker")" = "PackRAG F2 full assets v1"',
        f'for entry in "$root"/* "$root"/.[!.]*; do if test -e "$entry" || test -L "$entry"; then case "${{entry##*/}}" in owner.marker|'+ '|'.join('full-'+name+'.asset' for name,_,_,_ in SLOTS)+') ;; *) exit 91 ;; esac; fi; done']
    for name,_,size,_ in SLOTS:
        p=f'$root/full-{name}.asset';checks += [f'test -f "{p}"; test ! -L "{p}"; test "$(wc -c < "{p}")" -eq {size}']
    checks.append('sha256sum '+' '.join(f'"$root/full-{name}.asset"' for name,_,_,_ in SLOTS))
    return '; '.join(checks)
parser=argparse.ArgumentParser();parser.add_argument('--build',required=True);parser.add_argument('--output',required=True);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
target=HERE/args.output;assert target.parent==HERE and not target.exists()
record=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),runner_sha256=sha(Path(__file__)),build=args.build,namespace=NAMESPACE,verify_only=args.verify_only,commands=[])
def adb(command,timeout=180):
    argv=[str(ADB),'-s','R3CT908DHHR',*command];r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    record['commands'].append(dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));assert r.returncode==0,(command,r.stderr);return r.stdout
try:
    assert args.verify_only, 'F3 source guard is read-only; copying and installation are forbidden'
    capture=read(HERE/(args.build+'-capture.json'));assert capture['status']=='PASS_LOCAL_F3F4_BUILD_HOST_APK_CONTRACTS_NOT_DEVICE_OR_INCREMENT_ACCEPTANCE'
    output=adb(['shell','run-as org.packrag.product.test sh -c '+shlex.quote(validate_script())],timeout=300)
    hashes={line.split()[1]:line.split()[0] for line in output.splitlines()}
    expected={NAMESPACE+'/full-'+name+'.asset':digest for name,_,_,digest in SLOTS};assert hashes==expected
    record.update(status='PASS_OWNED_FULL_ASSET_SOURCE_SET_VALIDATED_NOT_IMPORT_OR_F2_ACCEPTANCE',source_sha256=hashes,source_total_bytes=sum(size for _,_,size,_ in SLOTS),
        scope='Exact four retained test-UID source inputs reverified read-only; no copies or installations; no host model export, arbitrary paths, custody traversal or product permissions. Every pipeline return checked with pipefail. Fixed no-follow types/marker/whitelist/size and full source SHA verified. Namespace deliberately retained; verify-only records reuse explicitly. No import/native/UI acceptance implied.')
except Exception as e:record.update(status='FAIL',failure_type=type(e).__name__,failure_message=str(e));raise
finally:record['finished_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],flush=True)
