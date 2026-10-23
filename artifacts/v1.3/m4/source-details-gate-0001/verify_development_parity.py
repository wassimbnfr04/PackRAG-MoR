"""Development-only observation; never manufacture full-driver or policy acceptance."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
target=HERE/'development-parity.json';assert not target.exists()
execution=read(HERE/'full-device-execution.json')
assert execution['status'] in ['RUNNING','PASS_ALL_DEVELOPMENT_POLICY_AND_RESTORATION_ORIGINALS_NOT_E2_CLOSURE']
assert len(execution['commands'])>=2 and all(r['returncode']==0 for r in execution['commands'][:2])
for row in execution['commands'][:2]:assert str(M4/'device-source-details-full-0001') in row['argv']
assert read(M4/'device-source-details-full-0001/instrumentation-manifest.json')['status']=='PASS'
assert read(M4/'device-source-details-full-0001/collected-results.json')['status']=='PASS'
original=HERE/'verify_retained_repaired.py';source=original.read_text(encoding='utf-8')
replacements=[
    ("    assert read(HERE/'full-device-execution.json')['status']=='PASS_ALL_DEVELOPMENT_POLICY_AND_RESTORATION_ORIGINALS_NOT_E2_CLOSURE'",
     "    assert read(M4/'device-source-details-full-0001/instrumentation-manifest.json')['status']=='PASS'"),
    ('    # Frozen accepted expectations remain unchanged; new desktop gates independently',
     "    env['PHONE']={name:value for name,value in env['PHONE'].items() if name=='device-source-details-full-0001'}\n    # Frozen accepted expectations remain unchanged; new desktop gates independently"),
    ('PASS_E2_ALL_RETAINED_EXACT_PHONE_TOKEN_ADMISSION_RUNTIME_AND_NEW_SIGNED_SOURCE_PARITY_NOT_CLOSURE',
     'PASS_E2_DEVELOPMENT_ONLY_RETAINED_AND_SOURCE_PARITY_NOT_POLICY_RESTORATION_OR_CLOSURE')]
for before,after in replacements:
    assert source.count(before)==1,before
    source=source.replace(before,after)
env={'__file__':str(original),'__name__':'e2_development_only_observation'}
exec(compile(source,str(original)+'#development-only-scoped-comparison','exec'),env)
result=env['verify']()
assert set(result['phone'])==set(result['selection'])==set(result['source_values'])=={'device-source-details-full-0001'}
result['scope_derivation']=dict(original_verifier_sha256=sha(original),derived_comparison_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
    replacements=replacements,full_driver_status_at_observation=execution['status'],
    statement='Only the completed development run is compared. No result, expected oracle, source input or full-driver status is rewritten.')
target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(result['status'])
