"""Copy existing pinned host assets to fresh owned emulator; no phone or download."""
import json,hashlib,subprocess,uuid
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
OUT=HERE/'emulator-assets-0001.json';assert not OUT.exists()
ADB=ROOT/'vendor/platform-tools/adb.exe';SERIAL='emulator-5580'
stage='/data/local/tmp/packrag-m4-assets-'+str(uuid.uuid4())
record=dict(status='PREPARING_NOT_NATIVE_ACCEPTANCE',serial=SERIAL,started_utc=datetime.now(timezone.utc).isoformat(),staging=stage,commands=[],assets=[])
def save():OUT.write_text(json.dumps(record,indent=2)+'\n')
def adb(*args,timeout=180):
    r=subprocess.run([str(ADB),'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    record['commands'].append(dict(args=list(args),returncode=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));save()
    assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode().strip()
def app(*args,timeout=180):return adb('shell','run-as','org.packrag.product',*args,timeout=timeout)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
    assert adb('shell','getprop','ro.kernel.qemu')=='1'
    assert adb('shell','getprop','sys.boot_completed')=='1'
    assert adb('shell','settings','get','system','font_scale')=='1.0'
    for name in ('models','packs','production-registry'):
        app('test','!','-e','files/'+name);app('test','!','-L','files/'+name)
    record['fresh_owner_roots_absent']=True
    adb('shell','test','!','-e',stage);adb('shell','mkdir',stage);adb('shell','chmod','755',stage)
    app('mkdir','-p','files/models/granite/onnx');app('chmod','700','files/models','files/models/granite','files/models/granite/onnx')
    rows=[
        ('LFM2.5-2.6B-QAD-Q4_0.gguf','models/LFM2.5-2.6B-QAD-Q4_0.gguf',1593894944,'a247afd6414918eac8e520a9e6137dc271235461ecbe1180462221d5b8d40b03'),
        ('04_LFM25_26B_Candidate_Evidence/model/chat_template.jinja','models/chat_template.jinja',5443,'ea663864491de7ade391839479860ca95541f892f72665c73251fbd4643b1bef'),
        ('models/v1.3/granite/tokenizer.json','models/granite/tokenizer.json',25301672,'4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f'),
        ('models/v1.3/granite/onnx/model.onnx','models/granite/onnx/model.onnx',390004608,'68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70')]
    pack=ROOT/'artifacts/v1.3/m4/repair-skills-prepared-0001/repair-skills.kpack'
    prepared=json.loads((pack.parent/'prepared.json').read_text())
    rows.append((str(pack.relative_to(ROOT)),'m4-repair-fixture-0001.kpack',pack.stat().st_size,prepared['pack_sha256']))
    for i,(source,target,size,digest) in enumerate(rows):
        p=ROOT/source;assert p.stat().st_size==size and sha(p)==digest
        temporary=stage+'/asset-'+str(i)
        adb('push',str(p),temporary,timeout=600);adb('shell','chmod','644',temporary)
        app('test','!','-e','files/'+target);app('test','!','-L','files/'+target)
        app('cp',temporary,'files/'+target,timeout=600);app('chmod','600','files/'+target)
        assert app('stat','-c','%s','files/'+target)==str(size)
        assert app('sha256sum','files/'+target,timeout=600).split()[0]==digest
        assert app('stat','-c','%a','files/'+target)=='600'
        record['assets'].append(dict(host=source,app_relative=target,bytes=size,sha256=digest));save()
        # Delete only the exact created staging file, never enumerate owner paths.
        assert temporary.startswith(stage+'/asset-');adb('shell','rm',temporary)
        print('PINNED_EMULATOR_ASSET_VERIFIED',target,flush=True)
    adb('shell','test','!','-L',stage);adb('shell','rmdir',stage)
    record.update(status='PASS_PINNED_FRESH_EMULATOR_ASSETS_NOT_NATIVE_ACCEPTANCE',completed_utc=datetime.now(timezone.utc).isoformat(),phone_touched=False)
    save()
except BaseException as error:
    record.update(status='FAILED_NOT_NATIVE_ACCEPTANCE',error_type=type(error).__name__);save();raise
