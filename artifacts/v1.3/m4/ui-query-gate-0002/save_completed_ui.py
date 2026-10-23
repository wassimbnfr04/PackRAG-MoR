"""Preserve only the completed new method from an overall failed UI run."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
run=M4/'device-ui-query-0001';text=(run/'instrumentation.txt').read_text()
assert 'Tests run: 2,  Failures: 1' in text
assert 'test=isolatedPackControlsWarningsRemovalAndRestart' in text
assert 'test=capturedControlsSurviveRealGenerationEditsRecreationAndSourceNavigation' in text
target=HERE/'completed-ui-partial.json';assert not target.exists()
command=[str(ROOT/'vendor/platform-tools/adb.exe'),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/m4-ui-query-controls.json']
result=subprocess.run(command,capture_output=True,check=True);parsed=json.loads(result.stdout);assert parsed['status']=='PASS' and parsed['actual_weight_inference']
saved=HERE/'completed-original-adb';saved.mkdir(exist_ok=False);(saved/'m4-ui-query-controls.json').write_bytes(result.stdout)
record=dict(status='COMPLETED_NEW_UI_METHOD_ONLY_OVERALL_TWO_METHOD_RUN_FAILED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    run=run.relative_to(ROOT).as_posix(),command=command,original_sha256=hashlib.sha256(result.stdout).hexdigest(),parsed=parsed,
    failure='Retained management test asserts NO_ACTIVE_PACK displayed without scrolling after submitting; added controls move the status off screen.',
    repair='Change only that assertion to performScrollTo before assertIsDisplayed; preserve original expectation and rerun both UI methods on fresh source-bound APKs.',
    excluded='No m3 management JSON collected from this failed run; any existing phone copy can be from an older run and is not new evidence.')
target.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(record['status'])
