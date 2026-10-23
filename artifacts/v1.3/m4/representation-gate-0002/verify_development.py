"""Full completed development evidence/parity; excludes policy/restore acceptance."""
import hashlib,json,textwrap,traceback
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;script=HERE/'verify_and_record.py';source=script.read_text();namespace={'__file__':str(script)}
target=HERE/'development-parity.json';assert not target.exists()
try:
    exec(compile(source[:source.index('def main():')],str(script),'exec'),namespace)
    name='device-representations-0002';namespace['PHONE']={name:namespace['PHONE'][name]}
    body=source[source.index('    target = HERE / "gate.json"'):source.index('    inspection=read(')]
    exec(compile(textwrap.dedent(body),str(script)+'::development-only','exec'),namespace)
    read=namespace['read'];M4=namespace['M4'];digest=namespace['digest']
    cancel=read(M4/name/'m2-generator-cancellation.json');assert cancel['native_cancel_stop']==2 and cancel['cancel_return_ms']<=1000 and cancel['post_cancel_recovery_state']=='ANSWER_ACCEPTED' and cancel['closed_handle_rejected'] and cancel['idempotent_close_cancel']
    partial=read(M4/'source-text-intermediate-parity-0001/partial-parity.json')
    for filename,expected in partial['original_adb_bytes_sha256'].items():assert digest(M4/'source-text-intermediate-parity-0001'/filename)==expected==digest(M4/name/'original-adb'/filename)
    record=dict(status='PASS_FULL_DEVELOPMENT_PARITY_NOT_POLICY_RESTORATION_OR_MILESTONE_ACCEPTANCE',recorded_utc=datetime.now(timezone.utc).isoformat(),verifier_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),phone=namespace['phone'][name],exact_tokenizer_admission_cases=43,retained_runtime_state_cases=19,presence_scope=dict(fixed=38,valid_scalars=1112064,resolver_checks=116,signed_imports=6,rejected=4),native_cancel_return_ms=cancel['cancel_return_ms'],unchanged_runtime_inputs=len(namespace['runtime']),unchanged_android_inputs=len(namespace['builds']['build-0020']),limits='All27 original final JSON and exact supported token/provenance comparisons; no policy/restore claim; natural-language wording need not match byte for byte.')
except Exception:
    (HERE/'development-parity-failure.txt').write_text(traceback.format_exc());raise
target.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(status=record['status'],methods=record['phone']['methods'],seconds=record['phone']['whole_instrumentation_seconds'],exact_tokens=43,runtime_cases=19)))
