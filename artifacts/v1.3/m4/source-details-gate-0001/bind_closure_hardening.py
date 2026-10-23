"""Bind initial derived closure bytes and the added fail-closed repair checks."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
r=json.loads((HERE/'repaired-gate-derivation.json').read_text())['derivations'][-1]
text=(HERE/r['original']).read_text(encoding='utf-8')
for old,new in r['replacements']:text=text.replace(old,new)
text=text.replace("'build-0037','build-0038','build-0041','build-0042'","'build-0037','build-0038','build-0039','build-0040','build-0041','build-0042','device-ui-source-details-0001'")
# Original derivation used Path.write_text on Windows, retaining CRLF on disk.
candidates=[text.encode('utf-8'),text.replace('\n','\r\n').encode('utf-8')]
raw=next(value for value in candidates if hashlib.sha256(value).hexdigest()==r['new_sha256'])
copy=HERE/'verify_and_record_repaired-before-extra-repair-assertions.py';assert not copy.exists();copy.write_bytes(raw)
target=HERE/'closure-verifier-additional-checks.json';assert not target.exists()
target.write_text(json.dumps(dict(status='PREPARED_VERIFIER_HARDENING_NOT_ACCEPTANCE',initial_derivation_sha256=r['new_sha256'],
    current_verifier_sha256=hashlib.sha256((HERE/r['target']).read_bytes()).hexdigest(),original_derived_copy=copy.name,
    additional_checks=['Require exact two-source repair proof','Require original visual FAIL and automated UI PASS remain separate','Bind original visual-failure preservation and repair scope into final record'],
    reconstruction_failure='Initial inline attempt compared LF encoding against original Windows CRLF write_text bytes; hash assertion failed before writing anything. This helper accepts only a byte representation matching the originally recorded SHA, never changes the expected hash.'),indent=2)+'\n',encoding='utf-8')
print('Original derived bytes reconstructed/hash-verified; extra checks separately bound')
