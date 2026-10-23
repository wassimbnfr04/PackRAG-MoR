"""Fix duplicate instrumentation stream counting before any phone collection occurred."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;p=HERE/'collect_retained_ui_partial.py';b=p.read_bytes();saved=HERE/'collect_retained_ui_partial-before-terminal-stream.py'
assert not saved.exists();saved.write_bytes(b);text=b.decode('utf-8')
before="text.count('No compose hierarchies found')==2";assert text.count(before)==1
text=text.replace(before,"text.rsplit('INSTRUMENTATION_RESULT: stream=',1)[1].count('No compose hierarchies found')==2");p.write_text(text,encoding='utf-8')
target=HERE/'partial-collector-preparation-failure.json';assert not target.exists();target.write_text(json.dumps(dict(status='FAIL_CHECKER_BEFORE_COLLECTION_REPAIRED_TERMINAL_SCOPE',
    before_sha256=hashlib.sha256(b).hexdigest(),cause='Android repeats each failure in status stack, status stream and final summary. Count only final result summary, while retaining two failed/finished methods. No original files were read or written by the failed collector.',
    scope='No phone test/source/assertion or suite FAIL status changed.'),indent=2)+'\n',encoding='utf-8')
