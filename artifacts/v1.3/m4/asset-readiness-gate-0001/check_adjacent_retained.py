"""Compare fresh adjacent coverage with immutable accepted E3 case contracts."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['debug','demo'],required=True);args=parser.parse_args()
current='device-local-assets-adjacent-0002' if args.variant=='debug' else 'device-local-assets-policy-adjacent-0001'
prior='device-diagnostics-full-0001' if args.variant=='debug' else 'device-diagnostics-policy-full-0001'
target=HERE/('adjacent-retained-parity-'+args.variant+'-0001.json');assert not target.exists()
verified_path=HERE/(current+'-verified.json');verified=read(verified_path)
assert verified['status']=='PASS_F1_ADJACENT_INDEPENDENT_ORIGINAL_CONTRACT_CHECK_NOT_CLOSURE' and verified['variant']==args.variant
e3_path=M4/'diagnostics-gate-0001/gate.json';e3=read(e3_path)
assert sha(e3_path)=='683272dc411f8065ea8fc8811475f74348ab741a9b7f0c726524bea14f5ed702'
coverage={}
for name,observation in verified['observations'].items():
    fresh=M4/current/'original-adb'/name;old=M4/prior/'original-adb'/name
    assert sha(fresh)==observation['original_sha256']
    assert sha(old)==e3['output_sha256'][old.relative_to(ROOT).as_posix()]
    before=read(old);after=read(fresh)
    assert before['status']==after['status']=='PASS'
    old_ids=[row['id'] for row in before['cases']];new_ids=[row['id'] for row in after['cases']]
    assert old_ids==new_ids and len(new_ids)==len(set(new_ids))
    assert all(row['passed'] is True for row in before['cases']+after['cases'])
    coverage[name]=dict(case_ids=new_ids,cases=len(new_ids),prior_original_sha256=sha(old),fresh_original_sha256=sha(fresh))
record=dict(status='PASS_F1_FRESH_ADJACENT_CASE_CONTRACTS_MATCH_ACCEPTED_E3_NOT_WHOLE_PHONE_PARITY_OR_CLOSURE',recorded_utc=datetime.now(timezone.utc).isoformat(),
    variant=args.variant,run=current,prior_run=prior,verified_sha256=sha(verified_path),coverage=coverage,
    cases=sum(row['cases'] for row in coverage.values()),
    scope='Exact ordered case IDs and completed passing assertions under unchanged retained test source, saved original binding to accepted E3/current verified run. Does not require exact model wording, timings or pre-/post-launch registry digests to match; those scopes have independent actual checks. Full security/retrieval/parity suite remains mandatory at F4.')
target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(record['status']);print(args.variant,record['cases'],'retained case IDs')
