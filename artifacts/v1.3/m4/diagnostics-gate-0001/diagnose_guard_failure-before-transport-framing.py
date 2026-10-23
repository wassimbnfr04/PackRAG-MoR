"""Read-only failed-run custody and exact guard differences, no database repair."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4';ADB=ROOT/'vendor/platform-tools/adb.exe'
target=HERE/'io-device-guard-failure.json';assert not target.exists()
run=M4/'device-diagnostics-0002';log=(run/'instrumentation.txt').read_text(encoding='utf-8')
match=re.search(r'expected:<\{(.*?)\}> but was:<\{(.*?)\}>',log);assert match
def values(text):
    rows=text.split(', ');pairs=[row.rsplit('=',1) for row in rows]
    assert all(len(row)==2 and re.fullmatch('[0-9a-f]{64}',row[1]) for row in pairs)
    return dict(pairs)
before,after=map(values,match.groups())
delta={name:dict(before=before.get(name),after=after.get(name)) for name in before.keys()|after.keys() if before.get(name)!=after.get(name)}
assert delta=={'packs/registry.sqlite':dict(before='3a5bbd80316be558734bb9d6a2f5c2063310dceac25c589dce2ce47db17c5301',after='e967352d73a4d69777f8030e2f4a8578347bd667861ba7b0a0f3775ecaae4a81')},delta
command=[str(ADB),'-s','R3CT908DHHR','exec-out','run-as','org.packrag.product','cat','files/m4-diagnostic-runtime.json']
out=subprocess.run(command,capture_output=True,check=True);p=HERE/'stale-phone-result-after-failed-0002.json';assert not p.exists();p.write_bytes(out.stdout)
original_sha=hashlib.sha256(out.stdout).hexdigest()
previous=json.loads((M4/'device-diagnostics-0001/collected-results.json').read_text())['saved_sha256']['m4-diagnostic-runtime.json']
assert original_sha==previous,'Unexpected phone result, inspect without claiming a new completed result'
commands=[str(ADB),'-s','R3CT908DHHR','shell','logcat','-b','system','-d','-s','ActivityTaskManager:I','*:S']
out=subprocess.run(commands,capture_output=True,check=True)
lines=[line for line in out.stdout.decode('utf-8',errors='replace').splitlines() if 'org.packrag.product' in line]
(HERE/'guard-failure-packrag-activity-log.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
record=dict(status='FAIL_PRESERVED_DEFAULT_REGISTRY_BYTE_CHANGE_CAUSE_NOT_YET_ESTABLISHED',recorded_utc=datetime.now(timezone.utc).isoformat(),
    differences=delta,unchanged=len(before)-len(delta),before_sha256=before,after_sha256=after,
    stale_phone_json_sha256=original_sha,stale_matches_prior_run=True,new_structured_result_written=False,
    instrumentation_sha256=hashlib.sha256((run/'instrumentation.txt').read_bytes()).hexdigest(),
    scope='Only default registry bytes differ; same file list and all pack payload/model hashes unchanged. No logical-state or causal conclusion from this map. Preserve failed JUnit, do not collect stale prior JSON as new success.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);print('Exact differences:',list(delta));print('Prior result remains stale; no new metrics accepted')
