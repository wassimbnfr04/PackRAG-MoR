"""Run every retained baseline check for the completed development run only."""
import hashlib,json,textwrap,traceback
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).parent;script=HERE/'retained_checks.py';source=script.read_text();namespace={'__file__':str(script)}
target=HERE/'development-retained-parity.json';assert not target.exists()
try:
    prefix=source[:source.index('def main():')];exec(compile(prefix,str(script),'exec'),namespace)
    name='device-selection-full-0002';namespace['PHONE']={name:namespace['PHONE'][name]}
    # Only the body up to policy inspection. It performs all source/format/host/
    # desktop/history and selected development-original/parity assertions, and
    # cannot enter the obsolete D2 closure-writing branch of the adapter.
    start=source.index('    assert "--check-only" in sys.argv')
    body=source[start:source.index('    inspection=read(')]
    namespace['sys'].argv.append('--check-only')
    exec(compile(textwrap.dedent(body),str(script)+'::development-only','exec'),namespace)
    read=namespace['read'];M4=namespace['M4']
    cancel=read(M4/name/'m2-generator-cancellation.json')
    assert cancel['native_cancel_stop']==2 and cancel['cancel_return_ms']<=1000 and cancel['post_cancel_recovery_state']=='ANSWER_ACCEPTED'
    assert cancel['closed_handle_rejected'] and cancel['idempotent_close_cancel']
    parity=read(HERE/'development-selection-parity-0002.json');assert parity['status']=='PASS_D3_SELECTION_PARITY_NOT_COMPLETE_MILESTONE'
    record=dict(status='PASS_FULL_DEVELOPMENT_NOT_POLICY_RESTORATION_OR_D3_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
        adapter_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        phone=namespace['phone'][name],runtime_inputs=len(namespace['runtime']),android_inputs=len(namespace['builds']['build-0028']),
        retained_exact_tokenizer_admissions=43,retained_runtime_states=19,additional_selection_parity=parity,
        native_cancel_return_ms=cancel['cancel_return_ms'],limits='All30 original results; no policy/restoration/final milestone claim; post-observation format control is not held-out gold.')
except Exception:
    failure=HERE/'development-retained-parity.failure.txt';assert not failure.exists();failure.write_text(traceback.format_exc());raise
target.write_text(json.dumps(record,indent=2)+'\n');print('FULL_DEVELOPMENT_RETAINED_PARITY_PASS_NOT_FINAL_CLOSURE')
