"""Check generator output only; never invoke the acceptance main function."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
script=HERE/'prepare_closure.py';source=script.read_text(encoding='utf-8');prefix=source[:source.index("target=HERE/'verify_and_record.py'")]
namespace={'__file__':str(script)};exec(compile(prefix,str(script),'exec'),namespace)
target=HERE/'verify_and_record.py';assert namespace['source']==target.read_text(encoding='utf-8')
for path in HERE.glob('*.py'):compile(path.read_text(),str(path),'exec')
output=HERE/'final-preparation-reproduction.json';assert not output.exists();output.write_text(json.dumps(dict(status='PASS_GENERATED_SCRIPT_TEXT_EXACT_NOT_ACCEPTANCE_EXECUTION',preparation_script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),actual_verifier_file_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),description='Execute adaptation prefix only; compare normalized file text exactly; all current helper syntax checks pass. No gate main function is called.'),indent=2)+'\n')
print('PASS repaired acceptance-helper reproduction and syntax; no gate executed')
