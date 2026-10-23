"""Freeze initial evidence and prepare explicit operational helpers; no acceptance."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;M4=ROOT/'artifacts/v1.3/m4'
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
roots=['run-0009','build-0016','build-0017','build-0018','build-0019','smoke-0008','smoke-0009','conflict-smoke-0005','relevance-smoke-0002','representation-smoke-0001','representation-smoke-0002','representation-fixtures-0001','representation-unit-0001','representation-adjacent-0001','representation-adjacent-0002','representation-intermediate-parity-0001','representation-development-parity-0001','representation-token-oracle-0001','representation-token-oracle-0002','representation-whitespace-audit-0001','representation-gate-0001','demo-apk-inspection-0009','device-representations-0001','device-production-representations-0001']
blocked={'.private','__pycache__','temp','stage','pytest-temp','.gradle','.cxx','.kotlin'}
files={}
for name in roots:
    root=M4/name;assert root.is_dir(),name
    for path in root.rglob('*'):
        if path.is_file() and not blocked.intersection(path.relative_to(root).parts) and path.suffix not in ('.apk','.class','.pyc'):
            assert path.resolve().is_relative_to(ROOT);files[path.relative_to(ROOT).as_posix()]=digest(path)
target=HERE/'initial-output-guard.json';assert not target.exists();target.write_text(json.dumps(dict(status='FROZEN_INITIAL_BOUNDED_D2_OUTPUTS_NOT_REPAIRED_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),files=files),indent=2)+'\n',encoding='utf-8')
old=M4/'representation-gate-0001'
source=(old/'collect_results.py').read_text()
source=source.replace("prior=json.loads((M4/'relevance-gate-0001/gate.json').read_text())\nold='device-relevance-0001' if variant=='debug' else 'device-production-relevance-0001'\nnames=prior['phone'][old]['saved_results']+['m4-representations.json','m4-representation-runtime.json']", "old='device-representations-0001' if variant=='debug' else 'device-production-representations-0001'\nprior=json.loads((M4/old/'collected-results.json').read_text())\nnames=list(prior['saved_sha256'])+['m4-source-text.json']")
assert "names=list(prior['saved_sha256'])+['m4-source-text.json']" in source
source=source.replace("assert name=='m4-representations.json'", "assert name=='m4-source-text.json'")
(HERE/'collect_results.py').write_text(source,encoding='utf-8')
source=(old/'inspect_demo.py').read_text().replace('demo-apk-inspection-0009','demo-apk-inspection-0010').replace('build-0019','build-0021').replace("'representation-corpus']","'representation-corpus','source-text-corpus']")
(HERE/'inspect_demo.py').write_text(source,encoding='utf-8')
source=(old/'create_checkpoint.py').read_text().replace('build-0018','build-0020')
source=source.replace("assets=ROOT/'product/android/app/src/androidTest/assets/representation-corpus'", "sources += ['product/packrag/representations.py','product/tests/test_source_text.py','product/tests/fixtures/source-text-contracts.json','scripts/v13_source_text_fixtures.py','scripts/v13_source_text_smoke.py','product/android/core-model/src/main/java/org/packrag/model/SourceText.kt','product/android/core-model/src/main/java/org/packrag/model/QueryUnicode.kt','product/android/core-model/src/test/java/org/packrag/model/SourceTextTest.kt','product/android/kpack-registry/src/main/java/org/packrag/packs/DatabaseMetadata.kt','product/android/app/src/androidTest/java/org/packrag/product/SourceTextDeviceTest.kt']\nsources += [p.relative_to(ROOT).as_posix() for p in (ROOT/'product/android/app/src/androidTest/assets/source-text-corpus').iterdir() if p.is_file()]\nassets=ROOT/'product/android/app/src/androidTest/assets/representation-corpus'")
(HERE/'create_checkpoint.py').write_text(source,encoding='utf-8')
audit=M4/'representation-whitespace-audit-0002';assert not audit.exists();audit.mkdir();(audit/'probe.py').write_bytes((M4/'representation-whitespace-audit-0001/probe.py').read_bytes())
for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
print(json.dumps(dict(status='PREPARED_NOT_ACCEPTANCE',initial_public_files=len(files),syntax_checked=True)))
