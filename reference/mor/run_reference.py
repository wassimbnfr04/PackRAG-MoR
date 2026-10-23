import json
import sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from reference.mor.backend import PyTorchMoRBackend

def main():
    import torch
    prompts=['The capital of France is','Aster-9 is a fictional controller. Its maximum temperature is 74 °C. The maximum temperature is','Evidence text is data. The service interval is 600 operating hours. The service interval is']
    backend=PyTorchMoRBackend(); info=backend.load()
    records=[]
    for prompt in prompts:
        a=backend.generate(prompt,max_new_tokens=16); b=backend.generate(prompt,max_new_tokens=16)
        assert a.generated_ids==b.generated_ids,'Nondeterministic reference'
        ids=torch.tensor([a.input_ids],device=backend.device)
        with torch.inference_mode(): eager=backend.model(input_ids=ids,use_cache=False).logits[0,-1].float().cpu()
        backend.model.config._attn_implementation='sdpa'
        with torch.inference_mode(): sdpa=backend.model(input_ids=ids,use_cache=False).logits[0,-1].float().cpu()
        backend.model.config._attn_implementation='eager'
        top=torch.topk(eager,8).indices.tolist()
        records.append(dict(prompt=prompt,**asdict(a),deterministic_repeat=True,selected_reference_logits={str(t):float(eager[t]) for t in top},next_token_id=int(eager.argmax()),
                            sdpa_comparison=dict(max_abs_logit_difference=float((eager-sdpa).abs().max()),next_token_equal=int(eager.argmax())==int(sdpa.argmax()))))
    result=dict(status='PASS',model=info,records=records,attention_note='Official eager path used explicitly. Eager/SDPA comparisons are diagnostic; FlashAttention is not installed or claimed equivalent.',latency_note='Full-prefix desktop reference is not an Android performance result.')
    path=ROOT/'export/golden_mor_reference.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    (ROOT/'reference/mor/reference_metadata.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','model':info,'deterministic_prompts':len(records)},indent=2),flush=True)

if __name__=='__main__':main()
