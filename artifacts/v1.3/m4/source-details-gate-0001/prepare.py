"""Read-only E2 baseline guard and independent signed-row expectations before reader edits."""
import hashlib,json,sqlite3,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(values):
    for name,value in values.items():assert digest(ROOT/name)==value,name
target=HERE/'preimplementation.json';assert not target.exists()
gate_path=M4/'ui-query-gate-0002/gate.json';gate=read(gate_path)
assert gate['status']=='M4E1_QUERY_CONTROLS_CAPTURED_CONTEXT_VERIFIED_NOT_COMPLETE_M4_OR_PRODUCT'
for key in ['source_sha256','android_source_sha256','output_sha256']:check(gate[key])
history=read(ROOT/'artifacts/v1.3/m0/historical-evidence-guard.json')['files'];check(history)
commit=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert commit=='17d2b5159b9d2d28a1823f8b8102d178abffecc5'
assets=ROOT/'product/android/app/src/androidTest/assets'
inputs=[('walking-skeleton.kpack','developer-public-key.raw'),('source-metadata-corpus/source-metadata.kpack','source-metadata-corpus/public-key.raw')]
rep=read(assets/'representation-corpus/cases.json')
inputs += [('representation-corpus/'+p['filename'],'representation-corpus/public-key.raw') for p in rep['packs'] if p['import_accept']]
records=[]
for name,key in inputs:
    path=assets/name;relative=path.relative_to(ROOT).as_posix();assert digest(path)==gate['android_source_sha256'][relative]
    with zipfile.ZipFile(path) as archive:
        raw=archive.read('manifest.json');manifest=json.loads(raw);payload=archive.read('knowledge.sqlite')
        declared=next(f for f in manifest['files'] if f['path']=='knowledge.sqlite')
        assert sha(payload)==declared['sha256'] and len(payload)==declared['bytes']
        with sqlite3.connect(':memory:') as db:
            db.deserialize(payload);db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('PRAGMA trusted_schema=OFF')
            sources=[dict(row) for row in db.execute('SELECT * FROM sources ORDER BY source_id')]
            chunks=[dict(row) for row in db.execute('SELECT * FROM chunks ORDER BY dense_row')]
        records.append(dict(asset=name,public_key_asset=key,pack_sha256=digest(path),public_key_sha256=digest(assets/key),
            manifest_sha256=sha(raw),pack_id=manifest['pack_id'],version=manifest['version'],sources=sources,chunks=chunks))
corpus=HERE/'signed-row-expectations.json';assert not corpus.exists()
corpus.write_text(json.dumps(dict(status='INDEPENDENT_ORIGINAL_SIGNED_ROWS_NOT_NEW_RUNTIME_ORACLE',packs=records,
    derivation='Direct standard-library SQLite SELECT * on in-memory original hash-bound payloads before editing either product reader.',
    limits='Synthetic signed metadata assertions; no genuine review/license/gold claim.'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
target.write_text(json.dumps(dict(status='PASS_E1_BASELINE_AND_PREIMPLEMENTATION_SOURCE_EXPECTATIONS_NOT_E2_ACCEPTANCE',
    recorded_utc=datetime.now(timezone.utc).isoformat(),commit=commit,e1_gate_sha256=digest(gate_path),
    runtime_inputs=len(gate['source_sha256']),android_inputs=len(gate['android_source_sha256']),
    e1_public_outputs_unchanged=len(gate['output_sha256']),historical_unchanged=len(history),
    corpus_sha256=digest(corpus),packs=len(records),raw_reasoning_persisted=False),indent=2)+'\n',encoding='utf-8')
print(target.read_text())
