"""Stricter independent saved-source format check, not new runtime execution."""
import hashlib,json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[3]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'typed-source-results.json';assert not target.exists()
path=HERE/'verify_new_results.py';spec=spec_from_file_location('typed_source_checker',path);module=module_from_spec(spec);spec.loader.exec_module(module)
run=ROOT/'artifacts/v1.3/m4/device-source-details-full-0001';result=module.phone(run)
# Independent negative controls show why ordinary Python numeric equality is insufficient.
controls=[(False,0),(True,1),(1.0,1),(None,False),('1',1)]
for actual,expected in controls:
    try:module.exact_typed(actual,expected)
    except AssertionError:pass
    else:raise AssertionError('Wrong saved value type was accepted')
record=dict(status='PASS_DEVELOPMENT_SOURCE_JSON_TYPES_NOT_POLICY_OR_E2_CLOSURE',
    original_checker_sha256=sha(HERE/'verify_new_results-before-typed-values.py'),current_checker_sha256=sha(path),
    negative_type_controls=len(controls),development=result,
    statement='All original signed expectations and device outputs are unchanged. Source-row comparison now requires identical JSON value types; bool/int/float equality cannot hide a format mismatch. Existing passing outputs are not relabelled or rerun.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
