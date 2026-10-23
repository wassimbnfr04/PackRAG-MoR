"""One fresh regression after real generator-stop fix; unchanged input custody."""
import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.v13_result_manifest import public_source_files,digest
RUN=ROOT/'artifacts/v1.3/m4/chat-python-regression-0001';RUN.mkdir(exist_ok=False)
files=public_source_files(ROOT);before={str(p.relative_to(ROOT)):digest(p) for p in files}
(RUN/'inputs.json').write_text(json.dumps(dict(started_utc=datetime.now(timezone.utc).isoformat(),files=before),indent=2)+'\n')
args=[sys.executable,'-X','utf8','-m','pytest','tests','product/tests','-q','--basetemp',str(RUN/'pytest-temp'),'--junitxml',str(RUN/'pytest.xml')]
result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=1200)
(RUN/'stdout.txt').write_bytes(result.stdout);(RUN/'stderr.txt').write_bytes(result.stderr)
after={str(p.relative_to(ROOT)):digest(p) for p in public_source_files(ROOT)}
record=dict(status='PASS' if result.returncode==0 and before==after else 'FAIL',argv=args,returncode=result.returncode,source_count=len(before),inputs_unchanged=before==after)
if (RUN/'pytest.xml').exists():record['suites']=[dict(s.attrib) for s in ET.parse(RUN/'pytest.xml').getroot().iter('testsuite')]
(RUN/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(record['status'],record.get('suites'),flush=True)
assert record['status']=='PASS'
