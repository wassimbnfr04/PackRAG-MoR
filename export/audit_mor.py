"""Audit actual official MoR graph; distinguish target-pin status from diagnostics."""
import json
import argparse
import sys
import traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def attempt(fn):
    try: return {'status':'PASS','value':fn()}
    except Exception as e: return {'status':'FAIL','error_type':type(e).__name__,'first_failure':str(e),'traceback':traceback.format_exc()}

def main():
    import torch
    from reference.mor.backend import PyTorchMoRBackend
    args=argparse.ArgumentParser();args.add_argument('--xnn-retry',action='store_true');flags=args.parse_args()
    torch.set_num_threads(4)
    out=Path(__file__).parent;out.mkdir(exist_ok=True)
    pin=(ROOT/'artifacts/week1/environment/executorch_torch_pin.log').read_text().split()[0]
    report=dict(executorch_version='1.5.0',mor_repository_commit='82c97f29cd140efa01f5cc4fe0de73a4c3b6ffd6',host_environment='WINDOWS_NATIVE',
                pinned_pytorch_commit=pin,actual_pytorch_commit=torch.version.git_version,actual_pytorch_version=torch.__version__,
                pin_matches=torch.version.git_version==pin,experiment_label='PINNED_TARGET' if torch.version.git_version==pin else 'NON_PINNED_PYTORCH_DIAGNOSTIC',
                environment_smoke={'passed':False},torch_export={},operators=dict(xnnpack=[],portable=[],decomposed=[],custom_required=[],unsupported=[],unknown=[]),
                routing={},kv_cache={},prefill={},decode={},audit_steps={})
    previous=json.loads((out/'mor_export_report.json').read_text()) if flags.xnn_retry else None
    def save():
        (out/'mor_export_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    class Add(torch.nn.Module):
        def forward(self,x,y):return x+y
    def smoke():
        from executorch.exir import to_edge
        exp=torch.export.export(Add(),(torch.ones(2),torch.ones(2)))
        program=to_edge(exp).to_executorch()
        (out/'add_diagnostic.pte').write_bytes(program.buffer)
        return dict(torch_export=True,edge_lowering=True,serialized_bytes=len(program.buffer))
    e0=attempt(smoke);report['audit_steps']['E0']=e0
    report['environment_smoke']=dict(passed=e0['status']=='PASS' and report['pin_matches'],diagnostic_passed=e0['status']=='PASS',details=e0)
    print('E0',e0['status'],flush=True);save()
    backend=PyTorchMoRBackend(device='cpu',precision='fp32'); info=backend.load()
    report['checkpoint_sha256']=info['checkpoint_sha256'];report['model_config_sha256']=info['config_sha256']
    class Prefill(torch.nn.Module):
        def __init__(self,model):super().__init__();self.model=model
        def forward(self,input_ids):return self.model(input_ids=input_ids,use_cache=False,return_dict=True).logits
    wrapper=Prefill(backend.model).eval(); ids=torch.arange(64).remainder(49152).reshape(1,64)
    exported=None
    def static_capture():
        nonlocal exported
        exported=torch.export.export(wrapper,(ids,),strict=True)
        ops=sorted({str(n.target) for n in exported.graph_module.graph.nodes if n.op=='call_function'})
        (out/'mor_static_graph.txt').write_text(str(exported.graph_module.graph),encoding='utf-8')
        return dict(batch=1,sequence=64,strict=True,operators=ops)
    e2=attempt(static_capture);report['audit_steps']['E1']=e2;report['audit_steps']['E2']=e2
    report['torch_export']=dict(status=e2['status'],first_failure=e2.get('first_failure'),static_shape=e2,dynamic_shape={'status':'NOT_ATTEMPTED'})
    print('E2',e2['status'],flush=True);save()
    if e2['status']=='PASS':
        report['operators']['unknown']=e2['value']['operators']
        def dynamic_capture():
            exp=torch.export.export(wrapper,(ids,),dynamic_shapes=({1:torch.export.Dim('seq_len',min=48,max=96)},),strict=True)
            return dict(min_sequence=48,max_sequence=96,graph_nodes=len(list(exp.graph_module.graph.nodes)))
        e3=previous['audit_steps']['E3'] if previous else attempt(dynamic_capture)
        report['audit_steps']['E3']=e3;report['torch_export']['dynamic_shape']=e3
        print('E3',e3['status'],flush=True);save()
        def edge_capture():
            from executorch.exir import to_edge
            edge=to_edge(exported)
            portable=edge.to_executorch()
            (out/'mor_portable_diagnostic.pte').write_bytes(portable.buffer)
            return dict(serialized_bytes=len(portable.buffer))
        report['audit_steps']['E4']=previous['audit_steps']['E4'] if previous else attempt(edge_capture)
        print('E4',report['audit_steps']['E4']['status'],flush=True);save()
        def xnn_capture():
            from executorch.exir import to_edge_transform_and_lower
            from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
            lowered=to_edge_transform_and_lower(exported,partitioner=[XnnpackPartitioner()])
            program=lowered.to_executorch();(out/'mor_xnnpack_diagnostic.pte').write_bytes(program.buffer)
            delegates=[str(n.target) for n in lowered.exported_program().graph_module.graph.nodes if 'delegate' in str(n.target)]
            delegated=set()
            for module in lowered.exported_program().graph_module.modules():
                original=getattr(module,'original_module',None)
                if original is not None:
                    delegated.update(str(n.target) for n in original.graph_module.graph.nodes if n.op=='call_function')
            remaining=sorted({str(n.target) for n in lowered.exported_program().graph_module.graph.nodes if n.op=='call_function' and 'delegate' not in str(n.target)})
            report['operators']['xnnpack']=sorted(delegated)
            report['operators']['portable']=remaining
            report['operators']['unknown']=[]
            return dict(serialized_bytes=len(program.buffer),delegate_calls=delegates,portable_note='Serialized portable operations; Android linkage/runtime not tested.')
        report['audit_steps']['E5']=attempt(xnn_capture)
        print('E5',report['audit_steps']['E5']['status'],flush=True);save()
    else:
        for step in ['E3','E4','E5']:report['audit_steps'][step]={'status':'BLOCKED_UPSTREAM_CAPTURE'}
    report['routing']=dict(implementation='official expert_choice_router.py',static_capacity='top_k=max(1,int(capacity_factor*seq_len))',
                           operations=['aten.topk','aten.sort','aten.gather','aten.scatter_add'],
                           note='Do not classify an operation as custom-required merely because it is not delegated. See measured capture/lowering results.')
    report['kv_cache']=dict(status='NOT_EXPORTED',structures=['DynamicCache','RecursiveDynamicCache'],note='Official mutable cache updates and selected-token cache positions require a separate explicit-state wrapper. Full-prefix reference disables caching.')
    report['prefill']=dict(status=e2['status'],batch=1,sequence=64,use_cache=False)
    report['decode']=dict(status='NOT_EXPORTED',note='A one-token no-cache forward is not a faithful autoregressive decode-step export. Cache/state decomposition remains an audit task.')
    report['audit_steps']['E6']={'status':'UNKNOWN','note':'Portable Android linkage not executed; no unsupported/custom operator list inferred from source alone.'}
    report['audit_steps']['E7']={'status':'UNKNOWN','note':'No custom C++ kernel was introduced.'}
    report['audit_steps']['E8']={'status':'ANALYZED_NOT_EXPORTED','prefill':report['prefill'],'decode':report['decode']}
    report['preliminary_classification']='BLOCKED' if not report['pin_matches'] else 'HIGH_RISK'
    report['next_actions']=['Build/install PyTorch at the exact pinned source commit and rerun E0 before treating diagnostic results as pinned deployment evidence.','Capture explicit cache/state decode separately and compare with golden logits.','Run exported program on arm64 Android before any runtime claim.']
    save()
    md='# MoR ExecuTorch 1.5 audit\n\n'+f"Target-pin status: {'MATCH' if report['pin_matches'] else '**BLOCKED: PyTorch commit mismatch**'}.\n\nRequested `{pin}`, installed `{torch.version.git_version}` ({torch.__version__}). All wheel-based results are `{report['experiment_label']}`. The official installer expects the source-pinned PyTorch to be installed first; no compiler/source-built PyTorch was present in the baseline. The wheel has not been adopted as an architectural substitute.\n\n"+'\n'.join(f"- {step}: {r['status']}" for step,r in report['audit_steps'].items())+'\n\n'+f"Static capture first failure: `{e2.get('first_failure','none')}`\n\nPrefill tested on the actual loaded official checkpoint. Decode/cache state is not yet exported. Operator statuses remain UNKNOWN where Android kernel/linkage tests were not run. No custom operators were built.\n\nPreliminary target classification: **{report['preliminary_classification']}**. This is not the Week 3 final viability decision.\n"
    (out/'mor_export_report.md').write_text(md,encoding='utf-8');print('Audit saved',flush=True)

if __name__=='__main__':main()
