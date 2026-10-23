"""Fix independent approved-fixture policy expectations before adding that test.
Read only public assets; no signing operation or private custody read.
"""
import hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
assets=ROOT/'product/android/app/src/androidTest/assets/release-trust-corpus'
target=HERE/'policy-diagnostics-preparation.json';assert not target.exists()
cases=json.loads((assets/'cases.json').read_text(encoding='utf-8'));positive=[c for c in cases['cases'] if c['accept_production']]
assert len(positive)==1;case=positive[0];pack=assets/case['filename']
assert hashlib.sha256(pack.read_bytes()).hexdigest()==case['sha256']
with zipfile.ZipFile(pack) as z:
    raw=z.read('manifest.json');assert hashlib.sha256(raw).hexdigest()==case['manifest_sha256'];manifest=json.loads(raw)
assert manifest['publisher']['key_id']=='ed25519:97e6f35dd5d63b1f8dfe88273283e283a24fec351f4a0f59ff3da3443d5ad950'
assert manifest['calibration']['status']=='CALIBRATED'
record=dict(status='PREPARED_EXISTING_PUBLIC_APPROVED_SCHEMA_FIXTURE_NOT_EXECUTION_OR_GENUINE_CALIBRATION',recorded_utc=datetime.now(timezone.utc).isoformat(),
    fixture=case,case_manifest_sha256=hashlib.sha256((assets/'cases.json').read_bytes()).hexdigest(),
    publisher_key_id=manifest['publisher']['key_id'],pack_id=manifest['pack_id'],version=manifest['version'],
    independently_retained_question='What is the maximum continuous operating temperature of the Aster-9?',
    independently_retained_answer_value='74 °C',independently_retained_canonical_sha256='266af80f5d4da1dac500acd9a2bcc1fd2317b2caf49141ebb586280b9df49333',
    controls=['Compiled demo ALLOW_DEVELOPMENT_PACKS false and no INTERNET; fresh no-active has no constructor/generation claim',
        'Actual ViewModel import of existing approved schema fixture using build-owned publisher trust',
        'Actual accepted cold/warm LFM answers with captured manifest/candidates/session pins and same selected evidence identity',
        'Read-only inspection retains completed answer/trace/id, while inactive mutation clears live attribution',
        'Jurisdiction-excluded deterministic abstention records no generation and cannot reuse old diagnostic result',
        'Unapproved developer import rejected without a retained old diagnostic trace or caller trust bypass',
        'Owner default registries/models/payloads byte-identical within new isolated run'],
    scope='Plan only. Do not edit frozen0046 Android inputs until current foreground/original/visual result is saved. Existing positive calibration metadata is schema-only. No final content or benchmark acceptance.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status'])
