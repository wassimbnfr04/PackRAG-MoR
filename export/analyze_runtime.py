"""Post-export operator audit; Windows diagnostics are never Android results."""
import json
import re
import traceback
from pathlib import Path
from executorch.runtime import Runtime

directory=Path(__file__).parent
report=json.loads((directory/'mor_export_report.json').read_text(encoding='utf-8'))
results={}
for name in ['portable','xnnpack']:
    try:
        program=Runtime.get().load_program(str(directory/f'mor_{name}_diagnostic.pte'))
        method=program.load_method('forward')
        results[name]={'status':'METHOD_LOADED_NOT_EXECUTED'}
    except Exception as error:
        results[name]={'status':'FAIL','error':str(error),'traceback':traceback.format_exc()}
    print(name,results[name]['status'],flush=True)
log=(directory.parent/'artifacts/week1/logs/executorch_portable_runtime.log').read_text(encoding='utf-8',errors='replace')
missing=sorted(set(re.findall(r"kernel '([^']+)' not found",log)))
report['windows_runtime_diagnostic']={'label':'NON_PINNED_PYTORCH_DIAGNOSTIC','programs':results,'missing_registered_operators':missing,'android_tested':False,'log':'artifacts/week1/logs/executorch_portable_runtime.log'}
report['audit_steps']['E6']={'status':'PARTIAL','windows_runtime':results,'missing_registered_operators':missing,'android_linkage':'NOT_TESTED'}
report['audit_steps']['E7']={'status':'ANALYZED','candidate_custom_or_decomposition_ops':missing,'kernels_implemented':0,'note':'sort.values is absent from v1.5 portable functions.yaml and the tested Windows registry; an ATen entry exists. Exact pinned Android runtime still needs a linkage audit.'}
report['operators']['portable_serialized']=report['operators']['portable']
report['operators']['portable']=[op for op in report['operators']['portable'] if op!='aten.sort.values']
report['operators']['custom_candidates']=missing
report['operator_audit']={
    'top-k':{'classification':'PORTABLE_SERIALIZED_RUNTIME_UNPROVEN','operators':['aten.topk.values']},
    'sorting':{'classification':'CUSTOM_CPP_OP_OR_DECOMPOSITION_CANDIDATE','operators':missing},
    'expert_choice_routing':{'classification':'STATIC_CAPTURED_DYNAMIC_SHAPE_BLOCKER','note':'Official capacity uses int(float * seq_len), creating unsatisfied symbolic guards.'},
    'gather':{'classification':'PORTABLE_SERIALIZED_RUNTIME_UNPROVEN','operators':['aten.gather.out']},
    'scatter_add':{'classification':'PORTABLE_SERIALIZED_RUNTIME_UNPROVEN','operators':['aten.scatter_add.out']},
    'index_select_masked_selection_dynamic_token_subsets':{'classification':'STATIC_CAPTURED','note':'The observed graph uses gather/topk/where. Dedicated index_select or masked_select nodes were not observed.'},
    'recursive_shared_layer_invocation':{'classification':'STATIC_CAPTURED','note':'Official shared rec3 layer calls are unrolled in the fixed graph.'},
    'attention_normalization_linear':{'classification':'XNNPACK_PARTIALLY_DELEGATED','note':'See measured delegate and remaining operator lists; runtime numerical parity is not established.'},
    'embedding':{'classification':'PORTABLE_SERIALIZED_RUNTIME_UNPROVEN'},
    'reshape_view':{'classification':'DECOMPOSED_SUCCESSFULLY','note':'Edge graph has view_copy/permute_copy operations; execution not established.'},
    'kv_cache_state':{'classification':'UNKNOWN_NOT_EXPORTED'},
    'dynamic_shapes':{'classification':'SHAPE_BLOCKER','failure_step':'E3'},
    'control_flow':{'classification':'STATIC_CAPTURED','note':'No unresolved control-flow blocker observed for fixed prefill. Dynamic cache path remains untested.'},
}
report['next_actions'].insert(1,'Audit sort.values in the exact pinned Android runtime; evaluate a small portable sort kernel or equivalent routing decomposition against golden outputs before any implementation decision.')
(directory/'mor_export_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
md=(directory/'mor_export_report.md').read_text(encoding='utf-8')
md=md.replace('- E6: UNKNOWN','- E6: PARTIAL (Windows load fails; Android untested)').replace('- E7: UNKNOWN','- E7: ANALYZED (sort kernel/decomposition candidate)')
md+='\n## Post-export runtime audit\n\nThe diagnostic Add program executed correctly on Windows. Loading the serialized portable MoR method fails because `aten::sort.values` is not registered (three routing instructions reference that operator). The v1.5 source has an ATen entry, but no portable functions.yaml entry. This identifies a small custom portable kernel or graph decomposition candidate; no kernel was implemented and no Android linkage was tested. XNNPACK method-load outcome: '+results['xnnpack']['status']+'.\n\nThe bounded dynamic capture failure comes from symbolic `int(capacity_factor * seq_len)` routing guards at capacities 1, 2/3 and 1/3. Fixed prefill is captured at batch 1, sequence 64. Explicit cache/state decode is not exported.\n\nThe JSON includes per-family classifications and the exact delegated/remaining operator lists. “Serialized” does not mean linked, executed, numerically equivalent, or phone validated.\n'
(directory/'mor_export_report.md').write_text(md,encoding='utf-8')
