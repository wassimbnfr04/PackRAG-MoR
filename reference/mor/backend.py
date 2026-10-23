"""Official forward implementation with an explicit full-prefix reference loop."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OFFICIAL=ROOT/'reference/mor/official'
sys.path.insert(0,str(OFFICIAL))
EXPERIMENT='250720_pretrain_smollm-360m_rec3_middle_cycle_random_lr3e-3_mor_expert_linear_alpha_0.1_sigmoid_aux_loss_0.001'
CHECKPOINT=ROOT/'reference/mor/checkpoints'/EXPERIMENT

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

class PyTorchMoRBackend:
    def __init__(self,attention_backend='eager',device='cuda',precision='bf16'):
        self.attention_backend=attention_backend; self.device=device; self.precision=precision

    def load(self,model_path=str(CHECKPOINT)):
        import torch
        from omegaconf import OmegaConf
        from transformers import AutoConfig,AutoTokenizer
        from model.mor_model.modeling_llama import MoRLlamaForCausalLM
        from model.sharing_strategy import SHARING_STRATEGY
        from util.config import preprocess_config
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32=False
        torch.backends.cudnn.allow_tf32=False
        path=Path(model_path)
        cfgpath=OFFICIAL/'conf/pretrain'/f'{EXPERIMENT}.yaml'
        cfg=OmegaConf.load(cfgpath); cfg.per_device_train_batch_size=1
        cfg.attn_implementation=self.attention_backend; cfg.precision=self.precision
        cfg=preprocess_config(cfg)
        config=AutoConfig.from_pretrained(path,local_files_only=True)
        config._attn_implementation=self.attention_backend
        dtype={'bf16':torch.bfloat16,'fp32':torch.float32,'fp16':torch.float16}[self.precision]
        model=MoRLlamaForCausalLM._from_config(config,attn_implementation=self.attention_backend,torch_dtype=dtype)
        model,_=SHARING_STRATEGY[cfg.model](cfg,model)
        model.transform_layer_to_mor_expert(cfg)
        checkpoint=path/'pytorch_model.bin'
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        matched=model.load_state_dict(state,strict=True)
        del state
        model.eval().to(self.device)
        self.model=model; self.tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
        assets={p.name:file_hash(p) for p in path.glob('*') if p.is_file() and ('token' in p.name or p.name=='vocab.json')}
        self.info=dict(checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_bytes=checkpoint.stat().st_size,
                       checkpoint_sha256=file_hash(checkpoint),config_sha256=file_hash(path/'config.json'),
                       training_config_sha256=file_hash(cfgpath),resolved_inference_config=OmegaConf.to_container(cfg,resolve=True),
                       tokenizer_hashes=assets,tokenizer_sha256=hashlib.sha256(json.dumps(assets,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                       torch_version=torch.__version__,torch_commit=torch.version.git_version,cuda=torch.version.cuda,
                       attention_backend=self.attention_backend,precision=self.precision,device=self.device,
                       host_environment='WINDOWS_NATIVE',generation_implementation='full_prefix_reference',
                       unique_parameters=sum(p.numel() for p in model.parameters()),strict_state_dict=str(matched))
        return self.info

    def generate(self,prompt,max_new_tokens=128,temperature=0.0,top_p=1.0,stop_strings=()):
        import torch
        from desktop.generator_api import GenerationResult
        if temperature!=0.0 or top_p!=1.0: raise ValueError('Reference decoding is fixed greedy')
        inputs=self.tokenizer(prompt,return_tensors='pt',add_special_tokens=False).input_ids.to(self.device)
        input_ids=inputs[0].tolist(); generated=[]
        if len(input_ids)>1536 or len(input_ids)+max_new_tokens>2048: raise ValueError('INPUT_TOO_LONG')
        if self.device.startswith('cuda'): torch.cuda.synchronize()
        start=time.perf_counter(); first=None
        with torch.inference_mode():
            for step in range(max_new_tokens):
                output=self.model(input_ids=inputs,use_cache=False,return_dict=True)
                next_id=int(output.logits[0,-1].argmax().item())
                if first is None: first=time.perf_counter()
                generated.append(next_id)
                inputs=torch.cat((inputs,torch.tensor([[next_id]],device=inputs.device,dtype=inputs.dtype)),dim=1)
                if next_id==self.tokenizer.eos_token_id: break
                if stop_strings and any(self.tokenizer.decode(generated,skip_special_tokens=True).endswith(s) for s in stop_strings): break
        if self.device.startswith('cuda'): torch.cuda.synchronize()
        end=time.perf_counter(); elapsed=(end-start)*1000
        return GenerationResult(text=self.tokenizer.decode(generated,skip_special_tokens=True),prompt_tokens=len(input_ids),generated_tokens=len(generated),
                                time_to_first_token_ms=(first-start)*1000,total_latency_ms=elapsed,average_tokens_per_second=len(generated)/((end-start) or 1),
                                model_hash=self.info['checkpoint_sha256'],backend_name='PyTorchMoRBackend',quantization=self.precision,input_ids=input_ids,generated_ids=generated)

    def close(self):
        import torch
        self.model=None
        if self.device.startswith('cuda'):torch.cuda.empty_cache()
