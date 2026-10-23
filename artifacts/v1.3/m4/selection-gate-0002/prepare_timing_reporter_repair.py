"""One diagnostic label repair only after the current full gate is complete."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(HERE/'development0002-execution.json')['status']=='PASS_FULL_DEVELOPMENT_NOT_POLICY_RESTORATION_OR_D3_CLOSURE'
assert read(HERE/'development-retained-parity.json')['status']=='PASS_FULL_DEVELOPMENT_NOT_POLICY_RESTORATION_OR_D3_CLOSURE'
run=M4/'device-selection-full-0002';assert read(run/'instrumentation-manifest.json')['status']=='PASS'
assert 'OK (30 tests)' in (run/'instrumentation.txt').read_text()
assert len(read(run/'collected-results.json')['saved_sha256'])==30
path='product/android/app/src/androidTest/java/org/packrag/product/SelectionDeviceTest.kt';source=ROOT/path
before=read(M4/'build-0028/source-at-build-start.json')['files'][path];assert digest(source)==before
old='total_ms_including_initialization_not_benchmark';new='runtime_call_ms_excluding_encoder_generator_construction'
raw=source.read_bytes();assert raw.count(old.encode())==1 and new.encode() not in raw
saved=HERE/'timing-reporter-before.kt';assert not saved.exists();saved.write_bytes(raw)
source.write_bytes(raw.replace(old.encode(),new.encode()))
# Preserve every other source byte, including original newline encoding.
record=dict(status='REPORTER_LABEL_REPAIRED_REQUIRES_NEW_BUILDS_AFFECTED_DEVICE_METHODS_AND_IDENTICAL_PRODUCT_APK_PROOF',
    recorded_utc=datetime.now(timezone.utc).isoformat(),source=path,old_source_sha256=before,new_source_sha256=digest(source),
    old_field=old,new_field=new,old_source_copy_sha256=digest(saved),constructor_scope='Encoder/backend are constructed before direct PackRag.ask; runtime call timer excludes construction and load',
    product_runtime_changed=False,expected_reuse='Only if both product APK bytes are identical and all other Android inputs unchanged; rerun affected3 methods and full compiled-policy gate; otherwise rerun full development')
(HERE/'timing-reporter-repair.json').write_text(json.dumps(record,indent=2)+'\n')
print('REPORTER_LABEL_REPAIRED_NOT_ACCEPTED_NEW_BUILD_DEVICE_PROOF_REQUIRED')
