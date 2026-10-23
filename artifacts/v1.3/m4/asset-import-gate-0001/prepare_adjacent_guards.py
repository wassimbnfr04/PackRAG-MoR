"""Prepare eleven bounded guard-only source proposals; do not edit tested Android inputs."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
target=HERE/'adjacent-guard-preparation-0001.json';directory=HERE/'adjacent-guard-proposals-0001'
assert not target.exists() and not directory.exists()
names=['DiagnosticLifecycleDeviceTest','DiagnosticRuntimeDeviceTest','DiagnosticPolicyDeviceTest',
       'DiagnosticNavigationUiTest','SourceDetailsViewModelTest','SourceDetailsUiTest',
       'QueryControlsDeviceTest','QueryControlsUiTest','PackManagementUiTest',
       'LocalAssetReadinessDeviceTest','LocalAssetsUiTest']
identity=json.loads((ROOT/'artifacts/v1.3/m4/build-0075/source-at-build-start.json').read_text())['files']
pattern=re.compile(r'(?ms)^([ \t]*)(private )?fun (guard|guardedFiles)\(\):Map<String,String> = listOf\("packs","production-registry","models"\)\.flatMap \{ name ->\n.*?^\1\}\.toMap\(\)')
proposals={}
def digest(payload):return hashlib.sha256(payload).hexdigest()
for name in names:
    relative='product/android/app/src/androidTest/java/org/packrag/product/'+name+'.kt'
    original=(ROOT/relative).read_bytes();assert digest(original)==identity[relative]
    text=original.decode();normalized=text.replace('\r\n','\n')
    if name=='LocalAssetReadinessDeviceTest':
        start=normalized.index('    private fun guards():Map<String,String> {')
        end=normalized.index('    private fun fixture(root:File):File {',start)
        proposal=normalized[:start]+'    private fun guards():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()\n'+normalized[end:]
    elif name=='PackManagementUiTest':
        old='        val owner = File(context.filesDir,"packs")\n        fun ownerHashes() = if(!owner.exists()) emptyMap<String,String>() else owner.walkTopDown().filter { it.isFile }.associate { it.relativeTo(owner).path to Crypto.fileHash(it) }'
        assert normalized.count(old)==1
        proposal=normalized.replace(old,'        fun ownerHashes():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()',1)
        marker='.put("isolated_registry",true).put("mobile_data_preserved",true)'
        assert proposal.count(marker)==1
        proposal=proposal.replace(marker,marker+'.put("owner_registry_and_model_sha256",JSONObject(before))',1)
    else:
        matches=list(pattern.finditer(normalized));assert len(matches)==1,name
        match=matches[0]
        proposal=pattern.sub(lambda found:found[1]+(found[2] or '')+'fun '+found[3]+'():Map<String,String> = LocalAssetImportTestSupport.ownerGuard()',normalized,count=1)
    marker='.put("owner_registry_and_model_sha256",JSONObject(before))'
    count=proposal.count(marker);assert count==(2 if name=='SourceDetailsUiTest' else 1),(name,count)
    proposal=proposal.replace(marker,marker+'.put("owner_guard_scope","EXPLICIT_50_PUBLIC_BASELINE_FILES_NO_ENUMERATION")')
    old_case_ids=re.findall(r'(?<=passed\(")owner-[^"]+(?="\))',proposal)
    proposal=re.sub(r'(?<=passed\(")owner-[^"]+(?="\))','explicit-fifty-owner-public-files-unchanged',proposal)
    if name=='DiagnosticPolicyDeviceTest':
        assert proposal.count('folder.walkTopDown()')==normalized.count('folder.walkTopDown()')-1==2
    payload=proposal.replace('\n','\r\n').encode() if b'\r\n' in original else proposal.encode()
    assert payload!=original
    proposals[relative]=dict(original_sha256=digest(original),proposed_sha256=digest(payload),old_guard_case_ids=old_case_ids,
        proposed_case_id='explicit-fifty-owner-public-files-unchanged' if old_case_ids else None,original=original,proposed=payload)
# Validate every proposal before creating any output; no Android source mutation.
directory.mkdir()
for relative,value in proposals.items():
    name=Path(relative).name
    (directory/(name+'.before')).write_bytes(value.pop('original'))
    (directory/(name+'.proposed')).write_bytes(value.pop('proposed'))
target.write_text(json.dumps(dict(status='PREPARED_VALIDATED_NOT_APPLIED_OR_ACCEPTED',files=proposals,
    scope='Eleven test-only guard proposals replace owner-directory enumeration with existing no-follow exact50 public baseline. All functional controls remain; only guard output scope/case descriptions updated. DiagnosticPolicy two isolated-owned payload walks retained. Historical source snapshots/results unchanged. Do not apply until separate actual picker visual gate passes independent review, then fresh matched builds/host/contracts/adjacent physical regressions required. No active Android/test input modified.'),indent=2)+'\n',encoding='utf-8')
print('PREPARED_ELEVEN_GUARD_ONLY_PROPOSALS_NO_ACTIVE_ANDROID_CHANGE')
