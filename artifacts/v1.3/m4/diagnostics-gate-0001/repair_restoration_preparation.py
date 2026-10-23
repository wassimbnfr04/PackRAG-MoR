"""Preserve preparation failure and resume only byte/text-exact derived prefix."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;p=HERE/'prepare_restoration_recovery.py'
saved=HERE/'prepare_restoration_recovery.before-redundant-change.py';assert not saved.exists();saved.write_bytes(p.read_bytes())
source=p.read_text(encoding='utf-8')
before="('verify_and_record.py','verify_and_record_final.py'),('device-development-restore-0014','device-development-restore-0015'),('consent0014','consent0015')"
after="('verify_and_record.py','verify_and_record_final.py'),('device-development-restore-0014','device-development-restore-0015')"
assert source.count(before)==1;source=source.replace(before,after)
before="p=HERE/after_name;assert not p.exists();compile(content,str(p),'exec');p.write_text(content,encoding='utf-8')"
after="p=HERE/after_name;compile(content,str(p),'exec')\n    if p.exists():assert p.read_text(encoding='utf-8')==content,'Existing preparation prefix differs'\n    else:p.write_text(content,encoding='utf-8')"
assert source.count(before)==1;source=source.replace(before,after);compile(source,str(p),'exec');p.write_text(source,encoding='utf-8')
target=HERE/'restoration-preparation-initial-failure.json';assert not target.exists()
target.write_text(json.dumps(dict(status='HELPER_PREPARATION_FAILURE_PRESERVED_NO_DEVICE_MUTATION',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_helper_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),corrected_helper_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
    failure='AssertionError consent0014: document helper uses consent1 and only full directory path needed replacement. First two derived verifiers already exist; they will be reused only if exact expected normalized source text agrees, without rewriting original bytes.',
    partial_derived_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['verify_full_parity_restoration_final.py','verify_and_record_final.py']},
    scope='No Android source/test/class/expected result changes, no active driver interruption. Preparation only; actual future orchestration failure/recovery still pending.'),indent=2)+'\n',encoding='utf-8')
print('Redundant absent replacement removed; exact derived prefix custody preserved')
