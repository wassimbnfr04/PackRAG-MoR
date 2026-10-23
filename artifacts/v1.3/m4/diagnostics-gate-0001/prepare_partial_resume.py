"""Preserve second collector failure; resume one verified prefix without rewriting originals."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;p=HERE/'collect_retained_ui_partial.py';b=p.read_bytes();source=b.decode('utf-8');changes=[
    ('raw.mkdir(exist_ok=False)','assert raw.is_dir() and {p.name for p in raw.iterdir()}=={"m4-source-details-languages-ui.json"}'),
    ("p=run/'completed-test-runner.txt';assert not p.exists();p.write_text(logs,encoding='utf-8')", "p=run/'completed-test-runner.txt';assert p.read_text(encoding='utf-8')==logs"),
    ("assert value['status']=='PASS' and value['raw_reasoning_persisted'] is False", "assert value['status']=='PASS' and all(row['passed'] for row in value['cases'])\n    if name=='m4-source-details-languages-ui.json':assert value['raw_reasoning_persisted'] is False\n    else:assert len(value['cases'])==7 and value['isolated_registry'] and 'raw_reasoning_persisted' not in value"),
    ("(raw/name).write_bytes(data);saved[name]=hashlib.sha256(data).hexdigest()", "original=raw/name\n    if original.exists():assert original.read_bytes()==data\n    else:original.write_bytes(data)\n    saved[name]=hashlib.sha256(data).hexdigest()"),
    ("(run/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\\n',encoding='utf-8')", "primary=run/name\n    if primary.exists():assert read(primary)==value\n    else:primary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\\n',encoding='utf-8')")]
for before,after in changes:
    assert source.count(before)==1,before;source=source.replace(before,after)
target=HERE/'collect_retained_ui_partial_resume.py';assert not target.exists();target.write_text(source,encoding='utf-8')
record=dict(status='COLLECTOR_LEGACY_REPORT_SCHEMA_FAILURE_NOT_DEVICE_TEST_FAILURE',failed_source_sha256=hashlib.sha256(b).hexdigest(),
    failure='PackManagementUiTest legacy report does not have raw_reasoning_persisted; KeyError after first language JSON was saved.',
    preserved_prefix='Original language JSON8218bytes and completed TestRunner log remain byte-exact; resumer verifies equality before reuse, never rewrites them.',
    scope='Validate actual legacy seven-case isolated-registry schema without inventing a missing raw-generation field. Four-method suite remains FAIL, not accepted.',replacements=changes,
    derived_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
target=HERE/'partial-collector-schema-failure.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
