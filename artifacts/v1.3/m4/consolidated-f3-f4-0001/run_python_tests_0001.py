"""Versioned fresh pytest audit; private test temp is never inventoried or exported."""
import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.v13_result_manifest import public_source_files

parser=argparse.ArgumentParser()
parser.add_argument('--run',required=True)
parser.add_argument('--boundary-only',action='store_true')
args=parser.parse_args()
run=(ROOT/args.run).resolve()
assert run.is_relative_to(ROOT/'artifacts/v1.3/m4/consolidated-f3-f4-0001') and not run.exists()
run.mkdir()

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

sources={p.relative_to(ROOT).as_posix():sha(p) for p in public_source_files(ROOT)}
argv=[sys.executable,'-X','utf8','-m','pytest',
      'product/tests/test_public_evidence_boundary.py' if args.boundary_only else 'product/tests',
      '-q','--basetemp',str(run/'pytest-temp'),'--junitxml',str(run/'tests-junit.xml')]
record=dict(status='RUNNING_FRESH_PYTHON_NOT_ACCEPTED',started_utc=datetime.now(timezone.utc).isoformat(),
            argv=argv,source_at_start_sha256=sources,
            scope='Fresh exact-source tests. Private pytest-temp is excluded before any traversal/hash/export. '
                  'Normal Windows user execution preserves pytest/application ACL semantics; no permission '
                  'assertions, tests, radio/security settings or historical artifacts altered.')
(run/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
try:
    with (run/'stdout.txt').open('xb') as out,(run/'stderr.txt').open('xb') as err:
        completed=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    record['returncode']=completed.returncode
    assert completed.returncode==0,'Preserve failure outputs and repair before further acceptance'
    suites=ET.parse(run/'tests-junit.xml').getroot().findall('testsuite')
    totals={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}
    record['totals']=totals
    assert totals['tests']>0 and totals['failures']==totals['errors']==totals['skipped']==0
    assert all(sha(ROOT/name)==expected for name,expected in sources.items()),'Runtime/source changed during test'
    record.update(status='PASS_FRESH_EXACT_SOURCE_PYTHON_NOT_DEVICE_OR_FULL_M4_ACCEPTANCE',
                  public_output_sha256={name:sha(run/name) for name in ['stdout.txt','stderr.txt','tests-junit.xml']})
except Exception as error:
    record.update(status='FAIL_FRESH_PYTHON_HOLD_ACCEPTANCE',failure_type=type(error).__name__,failure_message=str(error))
    raise
finally:
    record['finished_utc']=datetime.now(timezone.utc).isoformat()
    (run/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(record['status'],record['totals'],flush=True)
