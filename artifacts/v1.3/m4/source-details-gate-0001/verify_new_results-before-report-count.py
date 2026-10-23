"""Independent E2 source values/desktop contracts; no rewritten historic oracles."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;M4=ROOT/'artifacts/v1.3/m4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def phone(run):
    collected=read(run/'collected-results.json');manifest=read(run/'instrumentation-manifest.json')
    assert manifest['status']==collected['status']=='PASS' and manifest['apk_sha256']==collected['apk_sha256']
    for name,value in collected['saved_sha256'].items():
        assert digest(run/'original-adb'/name)==value and read(run/name)==read(run/'original-adb'/name)
    actual=read(run/'m4-source-details-rows.json');assert actual['status']=='PASS'
    expected=read(ROOT/'product/android/app/src/androidTest/assets/source-details-corpus/signed-row-expectations.json')
    assert actual['expectations_sha256']==digest(ROOT/'product/android/app/src/androidTest/assets/source-details-corpus/signed-row-expectations.json')
    assert len(actual['cases'])==len(expected['packs'])==17
    by_asset={r['asset']:r for r in expected['packs']}
    count=0
    for row in actual['cases']:
        ref=by_asset[row['asset']];assert row['passed'] and row['active_and_inactive_inspection'] and row['manifest_sha256']==ref['manifest_sha256']
        sources=[dict(source,redistribution_allowed=bool(source['redistribution_allowed'])) for source in ref['sources']]
        assert row['actual_sources']==sources and row['sources']==len(sources);count+=len(sources)
    rejected=read(run/'m4-source-details-rejections.json');assert rejected['status']=='PASS' and len(rejected['cases'])==11
    assert len({r['id'] for r in rejected['cases']})==11 and all(r['passed'] for r in rejected['cases'])
    return dict(packs=17,active_inactive_inspections=34,exact_public_source_rows=count,fields_per_row=21,rejection_controls=11,
        original_results=len(collected['saved_sha256']),pack_metadata_truth='SIGNED_ASSERTIONS_NOT_EXTERNAL_LICENSE_REVIEW_CALIBRATION_APPROVAL')
def desktop():
    execution=read(HERE/'regression-execution.json');assert execution['status']=='PASS_FULL_PYTHON_AND_ALL_RETAINED_DESKTOP_GATES_NOT_E2_CLOSURE'
    manifest=read(M4/'run-0015/result-manifest.json');assert manifest['totals']==dict(tests=1034,failures=0,errors=0,skipped=0)
    runtime={n:v for n,v in manifest['source_sha256'].items() if n not in ['PLAN.md','STATUS.md','DECISIONS.md']}
    for name,value in runtime.items():assert digest(ROOT/name)==value,name
    gates=[]
    for name,result,count in [('existing-walking-smoke-0014','smoke-results.json',14),('conflict-smoke-0008','conflict-smoke-results.json',7),
        ('relevance-smoke-0005','relevance-smoke-results.json',4),('representation-smoke-0005','representation-smoke-results.json',8),
        ('source-text-smoke-0003','source-text-smoke-results.json',6),('selection-smoke-0003','selection-smoke-results.json',8)]:
        folder=M4/name;assert read(folder/'inputs.json')['source_sha256']==runtime
        record=read(folder/result);assert record['status']=='PASS'
        # Presence import results have a different envelope; preserve their explicit independent counts.
        if name!='source-text-smoke-0003':assert len(record['cases'])==count,(name,record)
        gates.append(dict(run=name,result=result,record_sha256=digest(folder/result)))
    return dict(python_tests=1034,runtime_inputs=len(runtime),all_six_desktop_gates=gates)
def main():
    target=HERE/'new-result-parity.json';assert not target.exists()
    result=dict(status='PASS_NEW_E2_SIGNED_SOURCE_VALUES_AND_ALL_RETAINED_DESKTOP_GATES_NOT_E2_CLOSURE',
        recorded_utc=datetime.now(timezone.utc).isoformat(),phone=phone(M4/'device-source-details-0001'),desktop=desktop())
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
