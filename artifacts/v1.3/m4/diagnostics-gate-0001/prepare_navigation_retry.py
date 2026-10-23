"""Derive new paths/build plus verified capture-only proof, preserve originals."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=HERE/'run_navigation_ui.py';value=source.read_text();changes={
    'build-0046':'build-0047','device-ui-diagnostic-navigation-0001':'device-ui-diagnostic-navigation-0002',
    'navigation-ui-execution.json':'navigation-ui-repaired-execution.json',
    'navigation-ui-stage-':'navigation-ui-repaired-stage-',
    'foreground-authorization.json':'foreground-retry-readiness.json'}
for before,after in changes.items():assert value.count(before)==(2 if before=='navigation-ui-stage-' else 1);value=value.replace(before,after)
anchor="python=[sys.executable,'-X','utf8'];run=M4/'device-ui-diagnostic-navigation-0002'"
assert value.count(anchor)==1
value=value.replace(anchor,"assert read(HERE/'capture-repair-preflight.json')['status']=='PASS_EXACT_PRODUCT_APK_SINGLE_UI_CAPTURE_REPAIR_NOT_NEW_UI_VISUAL_OR_E3_CLOSURE'\n"+anchor)
target=HERE/'run_navigation_ui_repaired.py';assert not target.exists();target.write_text(value,encoding='utf-8')
ready=HERE/'record_foreground.py';text=ready.read_text();assert text.count('foreground-authorization.json')==1
text=text.replace('foreground-authorization.json','foreground-retry-readiness.json')
new=HERE/'record_foreground_retry.py';assert not new.exists();new.write_text(text,encoding='utf-8')
(HERE/'navigation-retry-preparation.json').write_text(json.dumps(dict(status='PREPARED_SAME_PRODUCT_FRESH_UI_CAPTURE_RETRY_NOT_EXECUTION',
    original_driver_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),new_driver_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    replacements=changes,additional_guard='capture-repair-preflight PASS',scope='Same class/variant/timeout and original+PNG collection; fresh build47/run0002, actual renewed phone readiness. No old gate/result overwritten.'),indent=2)+'\n',encoding='utf-8')
print('Prepared fresh47/0002 UI capture retry')
