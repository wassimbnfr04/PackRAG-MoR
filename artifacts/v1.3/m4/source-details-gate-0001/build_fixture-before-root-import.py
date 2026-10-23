"""One new synthetic attribution fixture; reuses unchanged walking vectors/text, no new real content."""
import copy,hashlib,json,shutil,sqlite3,zipfile
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import write_archive,sha
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;RUN=HERE.parent/'source-details-fixtures-0001'
assert not RUN.exists();RUN.mkdir()
base=ROOT/'product/android/app/src/androidTest/assets/walking-skeleton.kpack'
with zipfile.ZipFile(base) as archive:
    manifest=json.loads(archive.read('manifest.json'));database=archive.read('knowledge.sqlite');dense=archive.read('dense.kdx')
db=sqlite3.connect(':memory:');db.deserialize(database);db.row_factory=sqlite3.Row
source=db.execute('SELECT s.* FROM sources s JOIN chunks c USING(source_id) WHERE c.locator=?',('G0-D01',)).fetchone();assert source
text=db.execute('SELECT canonical_text FROM chunks WHERE locator=?',('G0-D01',)).fetchone()[0];snapshot=text.encode('utf-8');assert sha(snapshot)==source['sha256_original']
db.execute('UPDATE sources SET canonical_uri=?,retrieved_at=?,snapshot_path=?,notes=? WHERE source_id=?',
    ('https://example.invalid/synthetic/thermal','2026-10-10','originals/thermal.txt','\nSYNTHETIC signed source metadata; no real licensing/review approval.\n',source['source_id']))
db.execute('UPDATE chunks SET page_start=2,page_end=2,character_start=0,character_end=? WHERE locator=?',(len(text),'G0-D01'))
unused=dict(source);unused.update(source_id='dev-unused',title='Résumé sans fragment',language='fr',canonical_uri=None,
    sha256_original=sha(b'Unused synthetic source'),redistribution_allowed=0,snapshot_path=None,notes='Synthetic source with no chunks')
columns=list(unused);db.execute('INSERT INTO sources ('+','.join(columns)+') VALUES ('+','.join('?' for _ in columns)+')',[unused[k] for k in columns]);db.commit()
sources=[dict(row) for row in db.execute('SELECT * FROM sources ORDER BY source_id')];chunks=[dict(row) for row in db.execute('SELECT * FROM chunks ORDER BY dense_row')]
payload=db.serialize();db.close()
signer=SigningKey.generate();public=bytes(signer.verify_key);(RUN/'public-key.raw').write_bytes(public)
manifest=copy.deepcopy(manifest);manifest.update(pack_id='org.packrag.contract.source-details',name='Synthetic source details control',languages=['en','fr'])
manifest['publisher']=dict(name='SYNTHETIC ONLY',key_id='ed25519:'+sha(public));manifest['counts']['sources']=len(sources)
manifest['build']['builder_version']='1.3.0-source-details-contract'
manifest['build']['source_manifest_sha256']=sha(json.dumps(unused,ensure_ascii=False,sort_keys=True).encode())
path=RUN/'source-details.kpack';write_archive(path,manifest,{'knowledge.sqlite':payload,'dense.kdx':dense,'originals/thermal.txt':snapshot},signer)
with zipfile.ZipFile(path) as archive:manifest_hash=sha(archive.read('manifest.json'))
original=json.loads((HERE/'signed-row-expectations.json').read_text(encoding='utf-8'))
original['packs'].append(dict(asset='source-details-corpus/source-details.kpack',public_key_asset='source-details-corpus/public-key.raw',
    pack_sha256=sha(path.read_bytes()),public_key_sha256=sha(public),manifest_sha256=manifest_hash,
    pack_id=manifest['pack_id'],version=manifest['version'],sources=sources,chunks=chunks))
original['new_fixture_limits']='One synthetic orphan source, false redistribution assertion, nullable URI, exact packaged original snapshot and page/character offsets. Same canonical walking text/vectors; no real content/review/calibration.'
assets=ROOT/'product/android/app/src/androidTest/assets/source-details-corpus';assert not assets.exists();assets.mkdir()
for item in [path,RUN/'public-key.raw']:shutil.copyfile(item,assets/item.name)
expected=RUN/'signed-row-expectations.json';expected.write_text(json.dumps(original,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');shutil.copyfile(expected,assets/expected.name)
record=dict(status='NEW_SIGNED_SYNTHETIC_SOURCE_DETAILS_FIXTURE_NOT_E2_ACCEPTANCE',base_sha256=sha(base.read_bytes()),
    script_sha256=sha(Path(__file__).read_bytes()),pack_sha256=sha(path.read_bytes()),public_key_sha256=sha(public),
    expectations_sha256=sha(expected.read_bytes()),original_expectations_sha256=sha((HERE/'signed-row-expectations.json').read_bytes()),
    dense_payload_unchanged_sha256=sha(dense),sources=len(sources),chunks=len(chunks),private_seed='EPHEMERAL_NOT_SAVED',
    original_and_canonical_text_equal=True,embedding_recipe='UNCHANGED_ORIGINAL_CANONICAL_WALKING_VECTORS_METADATA_ONLY')
(RUN/'fixture.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
