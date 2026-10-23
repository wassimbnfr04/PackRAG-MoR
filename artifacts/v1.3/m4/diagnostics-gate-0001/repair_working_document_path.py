"""Preserve mistakenly created root note; append it to existing canonical working document."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
source=ROOT/'FULL_DOCUMENTATION_WORKING.md';destination=HERE/'misplaced-working-document-note.md'
assert source.resolve().is_relative_to(ROOT) and destination.resolve().is_relative_to(ROOT) and not destination.exists()
note=source.read_bytes();assert len(note)==1097 and b'retained UI0002 FINISHED' in note
canonical=ROOT/'docs/v1.3/FULL_DOCUMENTATION_WORKING.md';before=hashlib.sha256(canonical.read_bytes()).hexdigest()
with canonical.open('ab') as f:f.write(note)
source.rename(destination)
target=HERE/'working-document-path-repair.json';assert not target.exists()
target.write_text(json.dumps(dict(status='DOCUMENT_NOTE_PATH_CORRECTED_NO_RUNTIME_CHANGE',canonical_path=canonical.relative_to(ROOT).as_posix(),before_sha256=before,after_sha256=hashlib.sha256(canonical.read_bytes()).hexdigest(),preserved_misplaced_note_sha256=hashlib.sha256(note).hexdigest(),reason='Helper appended to root rather than docs/v1.3 working document; preserve exact note, append to canonical document and remove ambiguity by relocating original inside diagnostic evidence.'),indent=2)+'\n',encoding='utf-8')
print('Working documentation note preserved and appended at correct existing path')
