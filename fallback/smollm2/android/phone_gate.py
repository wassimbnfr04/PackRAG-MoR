"""Physical-phone gate. No device/no offline proof => blocked, never PASS."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from gates.g0.run_g0 import prompt_for

def main():
    p=argparse.ArgumentParser();p.add_argument('--serial');p.add_argument('--run',action='store_true');a=p.parse_args()
    adb=ROOT/'vendor/platform-tools/adb.exe';directory=ROOT/'fallback/smollm2'
    def command(*args):return subprocess.run([str(adb),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True).stdout.strip()
    devices=command('devices','-l')
    connected=[line.split()[0] for line in devices.splitlines()[1:] if len(line.split())>1 and line.split()[1]=='device' and not line.startswith('emulator-')]
    result=dict(model='HuggingFaceTB/SmolLM2-360M-Instruct',status='BLOCKED_PENDING_PHONE',physical_phone=False,offline_generation=False,
                adb_devices=devices,gguf_sha256=None,quantization='F16',llamacpp_commit=None,model_load_time_ms=None,ttft_ms=None,tokens_per_second=None,peak_memory_bytes=None,evidence_smoke_passed=None,evidence_smoke_total=5,raw_cases=[])
    metadata_path=directory/'conversion/conversion_metadata.json'
    if metadata_path.exists():
        metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
        result.update(gguf_sha256=metadata['gguf_sha256'],gguf_bytes=metadata['gguf_bytes'],model_revision=metadata['model_revision'],llamacpp_candidate_commit=metadata['llamacpp_candidate_commit'])
    result['acceptance_classification']='WEEK1_PRODUCT_GATE_FAIL'
    result['acceptance_note']='Required physical-phone acceptance is unmet; unavailable hardware is not a measured model failure.'
    if connected:
        if len(connected)>1 and not a.serial:raise RuntimeError('Specify target device serial')
        serial=a.serial or connected[0]
        if serial not in connected:raise RuntimeError('Requested physical target not connected')
        def device(*args):return command('-s',serial,*args)
        require_physical=device('shell','getprop','ro.kernel.qemu')!='1'
        if not require_physical:raise RuntimeError('Emulator rejected')
        result.update(physical_phone=True,serial=serial,device={key:device('shell','getprop',prop) for key,prop in [('manufacturer','ro.product.manufacturer'),('model','ro.product.model'),('android','ro.build.version.release'),('abi','ro.product.cpu.abi'),('soc','ro.soc.model')]})
        result['device']['meminfo']=device('shell','cat','/proc/meminfo')
        result['status']='READY_TO_RUN' if not a.run else 'BLOCKED_OFFLINE_PROOF'
        if a.run:
            airplane=device('shell','settings','get','global','airplane_mode_on')=='1'
            wifi=device('shell','settings','get','global','wifi_on')=='0'
            data=device('shell','settings','get','global','mobile_data')=='0'
            result['offline_settings']=dict(airplane_mode=airplane,wifi_disabled=wifi,mobile_data_disabled=data)
            if airplane and wifi and data:
                gguf=directory/'conversion/SmolLM2-360M-Instruct-F16.gguf'
                binary=directory/'android/build-arm64/bin/llama-completion'
                if not binary.exists():raise RuntimeError('Android arm64 llama-completion build missing')
                result['gguf_sha256']=hashlib.sha256(gguf.read_bytes()).hexdigest()
                result['llamacpp_commit']=command_git()
                device('shell','mkdir','-p','/data/local/tmp/packrag-week1')
                for file,name in [(gguf,'model.gguf'),(binary,'llama-completion')]:device('push',str(file),'/data/local/tmp/packrag-week1/'+name)
                device('shell','chmod','700','/data/local/tmp/packrag-week1/llama-completion')
                cases=[json.loads(s) for s in (ROOT/'gates/g0/g0_v1.jsonl').read_text(encoding='utf-8').splitlines()]
                from transformers import AutoTokenizer
                tokenizer=AutoTokenizer.from_pretrained(ROOT/'models/smollm2',local_files_only=True)
                for case in [c for c in cases if c['case_id'] in ['G0-D01','G0-D02','G0-C01','G0-A01','G0-X01']]:
                    contract=prompt_for(case)
                    rendered=tokenizer.apply_chat_template([{'role':'user','content':contract}],tokenize=False,add_generation_prompt=True)
                    path=directory/'android'/f"{case['case_id']}.prompt.txt";path.write_text(rendered,encoding='utf-8')
                    device('push',str(path),'/data/local/tmp/packrag-week1/prompt.txt')
                    start=time.perf_counter()
                    proc=subprocess.run([str(adb),'-s',serial,'shell','/data/local/tmp/packrag-week1/llama-completion','-m','/data/local/tmp/packrag-week1/model.gguf','-f','/data/local/tmp/packrag-week1/prompt.txt','-n','128','--temp','0','--top-p','1','--seed','0','--no-conversation','--no-display-prompt'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
                    result['raw_cases'].append(dict(case_id=case['case_id'],contract=contract,rendered_prompt=rendered,exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr,total_process_ms=(time.perf_counter()-start)*1000))
                result['status']='GENERATED_PENDING_ADJUDICATION' if all(r['exit_code']==0 for r in result['raw_cases']) else 'WEEK1_PRODUCT_GATE_FAIL'
                # Raw CLI process success does not establish generation semantics/performance.
                # Parse per-token timings and manually adjudicate before setting any PASS fields.
    path=directory/'phone_test_results.json';path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    report=f"# SmolLM2 target-phone gate\n\nStatus: **{result['status']}**\n\nPhysical phone detected: {result['physical_phone']}\n\nOffline generation proven: {result['offline_generation']}\n\nGGUF: F16 correctness artifact; conversion alone does not prove phone inference.\n\nTTFT, model load time, tokens/s and memory: not measured on a phone. Five-case evidence score: not measured.\n\nNo emulator or desktop result is substituted for the target-phone result.\n"
    (directory/'phone_test_report.md').write_text(report,encoding='utf-8');print(json.dumps(result,indent=2))

def command_git():
    return subprocess.check_output(['git','-c','safe.directory='+str(ROOT/'vendor/llama.cpp'),'-C',str(ROOT/'vendor/llama.cpp'),'rev-parse','HEAD'],text=True).strip()

if __name__=='__main__':main()
