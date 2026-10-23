"""Static syntax/input-shape preparation checks only; never substitutes for actual gates."""
import hashlib,json,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
target=HERE/'closure-preparation-audit.json';assert not target.exists();checked={}
for name in ['verify_and_record.py','create_checkpoint.py','stage_checkpoint.py','verify_checkpoint_git.py','verify_full_parity_dispatch_final.py','run_full_background_dispatch_final.py']:
    p=HERE/name;compile(p.read_text(encoding='utf-8'),str(p),'exec');checked[name]=hashlib.sha256(p.read_bytes()).hexdigest()
nav=json.loads((HERE/'navigation-visual-repaired.json').read_text());assert set(nav['images'])=={'m4-diagnostic-home.png','m4-diagnostic-source.png'}
for name,row in nav['images'].items():
    p=M4/'device-ui-diagnostic-navigation-0002/original-adb'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'] and p.stat().st_size==row['bytes']
failed=ET.parse(M4/'run-0016/combined-junit.xml').getroot();assert failed.tag=='testsuites'
assert sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in failed)==474
assert not (HERE/'gate.json').exists() and not (HERE/'checkpoint-files.json').exists()
target.write_text(json.dumps(dict(status='PREPARED_CLOSURE_SYNTAX_AND_EXISTING_SHAPES_CHECKED_NOT_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),prepared_helpers_sha256=checked,
    existing_visual_custody_checked=True,failed_python474_preserved=True,
    scope='Full actual37/30/restore/UI/visual/parity/current-source/history/check-only still mandatory. Does not execute acceptance or record closure.'),indent=2)+'\n',encoding='utf-8')
print('Prepared syntax and actual existing schema/custody verified, no acceptance inferred')
