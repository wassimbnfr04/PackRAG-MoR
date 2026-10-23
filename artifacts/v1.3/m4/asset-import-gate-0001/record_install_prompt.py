"""Record observed external installer dialog; no test/product failure attribution."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]; HERE=Path(__file__).parent
target=HERE/'visual-install-prompt-0001.json';assert not target.exists()
image=HERE/'package-install-screen-0001.png'
with image.open('rb') as stream:image_sha=hashlib.file_digest(stream,'sha256').hexdigest()
note=(
    'Separate visual0001 terminal FAIL before instrumentation: ADB product install-r '
    'timed out180s, no selected method ran/no result marker, failure captures are '
    'explicitly invalid JSON/PNG cat-error bytes. Exact original logs/manifests retained. '
    'New identical APK/class/assertion retry visual0002 uses versioned non-streaming '
    'install runner, currently awaiting installer. Actual screenshot package-install-screen-0001.png '
    'shows Google Play Protect PackRAG prompt in French asking whether to send unknown app '
    'to Google for security checking; options Always send/Send this time/Do not send. '
    'This directly observes the second attempt installer dialog; it is compatible with, '
    'but does not directly image/prove, the first attempt timeout cause. '
    'User asked to resolve this per-install choice on phone; no automatic Google upload '
    'or security-setting bypass, no radio change/uninstall/clear. Test is not running '
    'inside PackRAG yet. Preserve active bounded installer until terminal; if timeout '
    'occurs, use a new output location after user resolves dialog. Full F2 visual gate '
    'and subsequent guard/regression/restoration/custody closure remain; F3/F4 held.'
)
target.write_text(json.dumps(dict(status='EXTERNAL_PHONE_INSTALLER_DECISION_PENDING_NOT_TEST_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),screenshot_sha256=image_sha,note=note),indent=2)+'\n',encoding='utf-8')
for name in ['STATUS.md','PLAN.md']:
    path=ROOT/name;header,rest=path.read_text(encoding='utf-8').split('\n',1)
    path.write_text(header+'\n\n'+note+'\n\n'+rest,encoding='utf-8')
for name in ['DECISIONS.md','docs/v1.3/FULL_DOCUMENTATION_WORKING.md','docs/v1.3/M4_IMPLEMENTATION_LOG.md','docs/v1.3/M4F2_SYSTEM_PICKER_METHODS.md']:
    with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write('\n\n'+note+'\n')
print('EXTERNAL_PHONE_INSTALLER_DECISION_PENDING_NOT_TEST_ACCEPTANCE')
