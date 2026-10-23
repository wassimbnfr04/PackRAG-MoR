"""Preserve failed visual evidence and exact two-source safe-window repair."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ui=read(HERE/'ui-execution.json');assert ui['status']=='PASS_FOUR_UI_METHODS_ORIGINALS_AND_SCREENSHOTS_SAVED_NOT_VISUAL_OR_E2_CLOSURE'
visual=HERE/'visual-inspection.json';assert not visual.exists()
visual.write_text(json.dumps(dict(status='FAIL_CANONICAL_CONTENT_OBSCURED_BY_ANDROID_NAVIGATION_NOT_E2_ACCEPTANCE',
    inspected_utc=datetime.now(timezone.utc).isoformat(),image_sha256=ui['original_png_sha256'],
    notes=['Both original screenshots inspected with view_image. Canonical text is at the bottom, partially under navigation buttons/scrim; French last line and Arabic lower line are not clearly unobscured.',
        'Text equality and partial semantic visibility assertions passed. They do not establish full readable viewport placement.',
        'Whole four-method JUnit remains PASS193.412s; visual acceptance fails. Preserve originals and block full phone/later milestones.'],
    scope='Actual signed AR/FR viewer component; no new multilingual inference, real translation review or production custom-key admission.'),indent=2)+'\n',encoding='utf-8')
changes={}
for name in ['product/android/app/src/main/java/org/packrag/product/MainActivity.kt',
    'product/android/app/src/androidTest/java/org/packrag/product/SourceDetailsUiTest.kt']:
    path=ROOT/name;old=path.read_bytes();assert sha(path)==read(M4/'build-0039/source-at-build-start.json')['files'][name]
    saved=HERE/'insets-repair-before'/name;saved.parent.mkdir(parents=True,exist_ok=True);assert not saved.exists();saved.write_bytes(old)
    import_needle=b'import androidx.compose.foundation.layout.padding\r\n' if b'\r\n' in old else b'import androidx.compose.foundation.layout.padding\n'
    newline=b'\r\n' if b'\r\n' in old else b'\n'
    assert old.count(import_needle)==1
    new=old.replace(import_needle,import_needle+b'import androidx.compose.foundation.layout.safeDrawingPadding'+newline)
    needle=b'Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp))'
    assert new.count(needle)==1
    new=new.replace(needle,b'Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp))')
    path.write_bytes(new);changes[name]=dict(old_sha256=hashlib.sha256(old).hexdigest(),new_sha256=sha(path),
        change='Import safeDrawingPadding; apply it outside the vertical scroll viewport in actual app and isolated viewer-component host.')
record=HERE/'insets-repair.json';assert not record.exists()
record.write_text(json.dumps(dict(status='EXACT_TWO_SOURCE_SAFE_WINDOW_REPAIR_REQUIRES_NEW_BUILDS_UI_FULL_GATES',changes=changes,
    visual_failure_sha256=sha(visual),limits='This changes product layout; original product APK is not byte-identical and old Android tests are not promoted to repaired-build acceptance.'),indent=2)+'\n',encoding='utf-8')
print('Visual FAIL preserved; two exact safeDrawingPadding edits applied')
