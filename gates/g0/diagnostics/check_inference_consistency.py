"""NOT_PRIMARY_G0: audit the saved inference path, without changing its results."""
import hashlib
import json
import sys
import traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from reference.mor.backend import PyTorchMoRBackend

def main():
    import torch
    directory=ROOT/'gates/g0'
    raw=(directory/'g0_results.jsonl').read_bytes()
    primary_hash=hashlib.sha256(raw).hexdigest()
    assert primary_hash==(directory/'primary_results.sha256').read_text().strip()
    records=[json.loads(s) for s in raw.decode('utf-8').splitlines()]
    backend=PyTorchMoRBackend();metadata=backend.load()
    assert metadata['checkpoint_sha256']==records[0]['model_hash']
    results=[]
    for case_id in ['G0-D01','G0-D02','G0-A01']:
        saved=next(r for r in records if r['case_id']==case_id)
        ids=torch.tensor([saved['input_ids']],device=backend.device)
        manual=backend.generate(saved['prompt'],max_new_tokens=16)
        assert manual.input_ids==saved['input_ids']
        result={'case_id':case_id,'manual_repeat_matches_primary_first16':manual.generated_ids==saved['generated_ids'][:16],'manual_ids':manual.generated_ids}
        try:
            with torch.inference_mode():
                output=backend.model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False,do_sample=False,max_new_tokens=16,pad_token_id=backend.tokenizer.eos_token_id)
            generated=output[0,ids.shape[1]:].tolist()
            result.update(hf_generate_status='PASS',hf_generate_ids=generated,hf_generate_matches_manual=generated==manual.generated_ids)
        except Exception as error:
            result.update(hf_generate_status='FAIL',hf_generate_error=str(error),traceback=traceback.format_exc())
        backend.model.config._attn_implementation='sdpa'
        sdpa=backend.generate(saved['prompt'],max_new_tokens=16)
        backend.model.config._attn_implementation='eager'
        result.update(sdpa_first16_matches_eager=sdpa.generated_ids==manual.generated_ids,sdpa_ids=sdpa.generated_ids)
        results.append(result)
        print(case_id,{k:v for k,v in result.items() if not k.endswith('_ids') and k!='traceback'},flush=True)
    assert hashlib.sha256((directory/'g0_results.jsonl').read_bytes()).hexdigest()==primary_hash
    result={'label':'NOT_PRIMARY_G0','scope':'Three frozen prompts; first 16 generated tokens only. No FlashAttention comparison and no general correctness proof.','checkpoint_sha256':metadata['checkpoint_sha256'],'primary_results_sha256':primary_hash,'primary_results_unchanged':True,'results':results}
    (Path(__file__).parent/'inference_consistency.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    backend.close()

if __name__=='__main__':main()
