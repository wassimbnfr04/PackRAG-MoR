"""Fresh full-run names after ADB installation transport failure; no test changes."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
retained=HERE/'retained_checks.py';saved=HERE/'retained_checks-before-adb-retry.py';assert not saved.exists();saved.write_bytes(retained.read_bytes())
source=retained.read_text();assert 'device-selection-full-0001' in source
retained.write_text(source.replace('device-selection-full-0001','device-selection-full-0002'),encoding='utf-8')
driver=HERE/'run_full_development.py';next_driver=HERE/'run_full_development_0002.py';assert not next_driver.exists()
source=driver.read_text().replace('device-selection-full-0001','device-selection-full-0002')
source=source.replace('development-stage-','development0002-stage-').replace('development-execution.json','development0002-execution.json')
source=source.replace('development-selection-parity.json','development-selection-parity-0002.json')
next_driver.write_text(source,encoding='utf-8')
(HERE/'execution-name-repair.json').write_text(json.dumps(dict(status='PREPARATION_REPAIR_NOT_ACCEPTANCE',
    reason='full0001 ADB daemon connection failure installing test APK; instrumentation never started; same source-bound build0028 retry',
    retained_before_sha256=digest(saved),retained_after_sha256=digest(retained),driver_before_sha256=digest(driver),driver_after_sha256=digest(next_driver),
    no_product_test_or_expectation_changed=True),indent=2)+'\n')
print('PREPARED_FRESH_FULL_RETRY_SAME_BUILD')
