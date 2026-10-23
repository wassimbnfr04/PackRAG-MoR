"""Preserve pre-device preparation failure and remove redundant ordered replacement."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;p=HERE/'prepare_retained_ui.py';b=p.read_bytes()
saved=HERE/'prepare_retained_ui-before-ordered-replacement.py';assert not saved.exists();saved.write_bytes(b)
record=dict(status='FAIL_PREPARATION_BEFORE_DRIVER_OR_DEVICE_EXECUTION',failed_assertion='E2 UI gate failed',
    cause='Earlier general E2 UI replacement already changed this later redundant string; no derived driver was written.',
    source_sha256=hashlib.sha256(b).hexdigest(),repair='Remove only redundant final string replacement; no Android/test/class change.',
    additional_observation='An attempted inline Python shell repair had a quoting SyntaxError before execution; use this saved repair script instead. No edits from that failed command.')
target=HERE/'retained-ui-preparation-initial-failure.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
source=b.decode('utf-8');before="    ('E2 UI gate failed','E3 retained UI gate failed')]";assert source.count(before)==1
source=source.replace(before,']');p.write_text(source,encoding='utf-8')
print('PASS preparation repair preserved original; execute corrected preparation next')
