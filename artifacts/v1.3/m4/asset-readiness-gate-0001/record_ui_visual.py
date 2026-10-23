"""Record actual manual inspection of the two original phone PNGs, with viewport limits."""
import hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;run=ROOT/'artifacts/v1.3/m4/device-local-assets-ui-0001'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
target=HERE/'ui-visual-0001.json';assert not target.exists()
execution=read(HERE/'ui-execution-0001.json');assert execution['status']=='PASS_F1_ACTUAL_UI_ORIGINALS_NOT_VISUAL_OR_CLOSURE'
manifest=read(run/'instrumentation-manifest.json');collection=read(run/'collected-results.json')
assert manifest['status']==collection['status']=='PASS' and manifest['variant']=='debug'
assert manifest['apk_sha256']==collection['apk_sha256']==read(HERE/'corrected-pair-preflight.json')['apk_sha256']['build-0056']
assert set(collection['saved_sha256'])=={'m4-local-assets-ui.json'}
original=run/'original-adb/m4-local-assets-ui.json';assert sha(original)==collection['saved_sha256']['m4-local-assets-ui.json']
value=read(original);assert value==read(run/'m4-local-assets-ui.json') and value['status']=='PASS'
assert len(value['cases'])==5 and all(row['passed'] is True for row in value['cases'])
assert value['owner_registry_and_model_sha256']==read(HERE/'guarded-retry-preparation.json')['owner_public_file_sha256']
identities={};dimensions={}
for name,identity in value['visual_png'].items():
    assert name in {'m4-local-assets-generator.png','m4-local-assets-encoder.png'}
    p=run/'original-adb'/name;assert sha(p)==identity['sha256'] and p.stat().st_size==identity['bytes']
    with p.open('rb') as stream:header=stream.read(24)
    assert header[:8]==b'\x89PNG\r\n\x1a\n';dimensions[name]=list(struct.unpack('>II',header[16:24]));identities[name]=identity['sha256']
assert len(identities)==2 and all(size==[1080,2316] for size in dimensions.values())
record=dict(status='PASS_F1_ORIGINAL_ASSET_SCREEN_TESTED_VIEWPORT',recorded_utc=datetime.now(timezone.utc).isoformat(),
    original_png_sha256=identities,original_png_dimensions=dimensions,original_report_sha256=sha(original),
    inspection='Both exact original-adb PNGs displayed and manually inspected using view_image(detail=original) in this task after actual UI success. No image generation, crop, relayout or substitute screenshot.',
    visible_fields={
        'm4-local-assets-generator.png':'App/local-processing text, asset-page/back/check controls, configured-versus-last-completed guidance, generator label/path, VERIFIED guidance, full expected/observed1593894944-byte sizes, full wrapped generator SHA256 and completed UTC timestamp. The following template label/path also appear.',
        'm4-local-assets-encoder.png':'Scrolled page: full template label/path/status, expected/observed5443-byte sizes, complete wrapped template SHA and timestamp; full tokenizer label/path/status, expected/observed25301672-byte sizes, complete wrapped tokenizer SHA and timestamp; encoder label/path and VERIFIED guidance. Encoder size/hash/timestamp continue below this captured viewport and are not claimed visually inspected.'},
    scope='Visible text and wrapped pins are readable without horizontal ellipsis or system-navigation overlap in these exact two viewports. Normal content extends above/below a vertical-scroll viewport. This is not a full-page capture or proof of every encoder field, all screen/font/rotation configurations or global accessibility. Four-file encoder identity and actual model/answer behavior are independently established by completed core/UI assertions, not by unseen pixels. Five UI controls and real74C/[S1] answer pass; policy/restoration/final guards/closure still required.',
    raw_reasoning_persisted=False,mobile_data_preserved=True)
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);print('Manual visible-field scope explicitly excludes offscreen encoder metadata')
