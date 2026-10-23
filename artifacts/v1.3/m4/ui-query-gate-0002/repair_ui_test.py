"""Exact test scrolling repair; save prior source and diagnostic before changing bytes."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
p=ROOT/'product/android/app/src/androidTest/java/org/packrag/product/PackManagementUiTest.kt'
old=p.read_bytes();source=old.decode('utf-8');needle='compose.onNodeWithText("NO_ACTIVE_PACK").assertIsDisplayed()'
assert source.count(needle)==1
saved=HERE/'PackManagementUiTest-before-status-scroll.kt';assert not saved.exists();saved.write_bytes(old)
new=source.replace(needle,'compose.onNodeWithText("NO_ACTIVE_PACK").performScrollTo().assertIsDisplayed()').encode('utf-8');p.write_bytes(new)
target=HERE/'ui-test-repair.json';assert not target.exists()
target.write_text(json.dumps(dict(status='EXACT_TEST_SCROLL_ONLY_REPAIR_REQUIRES_FRESH_BUILDS_AND_BOTH_UI_METHODS',recorded_utc=datetime.now(timezone.utc).isoformat(),
    source=p.relative_to(ROOT).as_posix(),old_sha256=hashlib.sha256(old).hexdigest(),new_sha256=hashlib.sha256(new).hexdigest(),
    original_run='device-ui-query-0001',original_failure_preserved=True,new_ui_method_partial_original_saved=True,
    product_code_changed=False,expectation_changed=False,
    scope='Move the actual existing status into the viewport before asserting it is displayed; do not relax state/output validation.'),indent=2)+'\n')
print('Exact status scroll repair recorded')
