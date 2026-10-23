import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.v13_result_manifest import public_source_files,digest
RUN=ROOT/'artifacts/v1.3/m4/quote-complete-python-regression-0001';RUN.mkdir(exist_ok=False)
inputs={str(p.relative_to(ROOT)):digest(p) for p in public_source_files(ROOT)}
(RUN/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
code="import tempfile,pytest;tempfile.tempdir="+repr(str(RUN/'temporary'))+";raise SystemExit(pytest.main(['tests','product/tests','-q','--tb=short','--basetemp',"+repr(str(RUN/'pytest-temp'))+",'--junitxml',"+repr(str(RUN/'pytest.xml'))+"]))"
(RUN/'temporary').mkdir()
r=subprocess.run([sys.executable,'-X','utf8','-c',code],capture_output=True,cwd=ROOT,timeout=1200)
(RUN/'stdout.txt').write_bytes(r.stdout);(RUN/'stderr.txt').write_bytes(r.stderr)
after={str(p.relative_to(ROOT)):digest(p) for p in public_source_files(ROOT)}
suites=[dict(s.attrib) for s in ET.parse(RUN/'pytest.xml').getroot().iter('testsuite')]
record=dict(status='PASS' if r.returncode==0 and inputs==after else 'FAIL',returncode=r.returncode,source_count=len(inputs),inputs_unchanged=inputs==after,suites=suites)
(RUN/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(record,flush=True);assert record['status']=='PASS'
