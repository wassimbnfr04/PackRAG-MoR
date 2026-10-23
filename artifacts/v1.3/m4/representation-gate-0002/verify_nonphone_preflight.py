"""Execute nonphone checks only; never run phone acceptance or write a gate."""
import hashlib,json,textwrap,traceback
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;script=HERE/'verify_and_record.py';text=script.read_text()
namespace={'__file__':str(script)};output=HERE/'nonphone-preflight.json';assert not output.exists()
try:
    prefix=text[:text.index('def main():')];body=text[text.index('    target = HERE / "gate.json"'):text.index('    phone = {}')]
    exec(compile(prefix,str(script),'exec'),namespace);exec(compile(textwrap.dedent(body),str(script)+'::nonphone-prefix','exec'),namespace)
    record=dict(status='PASS_NONPHONE_PREFLIGHT_NOT_PHYSICAL_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),runtime_inputs=len(namespace['runtime']),android_inputs=len(namespace['builds']['build-0020']),historical=len(namespace['historical']),note='Only the acceptance body before phone={} runs; no phone loop, no gate write, no state snapshots.')
except Exception:
    (HERE/'nonphone-preflight-failure.txt').write_text(traceback.format_exc());raise
output.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
