"""Extend public closure capture only; no product/test acceptance change."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;target=HERE/'verify_and_record_reporting.py';raw=target.read_bytes()
old=b"'demo-apk-inspection-0011','selection-gate-0001','selection-gate-0002']"
new=b"'demo-apk-inspection-0011','selection-running-resources-0001','selection-gate-0001','selection-gate-0002']"
assert raw.count(old)==1;saved=HERE/'verify_and_record_reporting-before-resource-scope.txt';assert not saved.exists();saved.write_bytes(raw)
target.write_bytes(raw.replace(old,new));record=HERE/'resource-scope-amendment.json';assert not record.exists()
record.write_text(json.dumps(dict(status='PREPARED_SCOPE_EXTENSION_NOT_ACCEPTANCE',before_sha256=hashlib.sha256(raw).hexdigest(),
    after_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),before_copy=saved.name,
    change='Add read-only single resource observation root to immutable public output capture; no tests/requirements/expectations removed'),indent=2)+'\n')
print('RESOURCE_CONTEXT_INCLUDED_IN_PREPARED_CLOSURE_SCOPE')
