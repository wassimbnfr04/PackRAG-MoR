"""Inspect the official conversion artifact without claiming device inference."""
import hashlib
import json
import sys
from pathlib import Path
import gguf

ROOT=Path(__file__).resolve().parents[3]
directory=Path(__file__).parent
path=directory/'SmolLM2-360M-Instruct-F16.gguf'
source=json.loads((ROOT/'models/smollm2/tokenizer_config.json').read_text(encoding='utf-8'))
reader=gguf.GGUFReader(path)
metadata={key:reader.fields[key].contents() for key in ['general.architecture','general.name','general.file_type','tokenizer.ggml.model','tokenizer.chat_template']}
assert metadata['general.architecture']=='llama'
assert metadata['general.file_type']==1
assert metadata['tokenizer.chat_template']==source['chat_template'],'Official chat template changed'
assert len(reader.fields['tokenizer.ggml.tokens'].contents())==49152
with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
result={
    'status':'CONVERSION_INSPECTED_NOT_PHONE_TESTED',
    'model_id':'HuggingFaceTB/SmolLM2-360M-Instruct',
    'model_revision':'a10cc1512eabd3dde888204e902eca88bddb4951',
    'llamacpp_candidate_commit':'19e28a27702117d8f2eb16b825b9a308111f67d9',
    'phone_validated_llamacpp_commit':None,
    'conversion_arguments':['vendor/llama.cpp/convert_hf_to_gguf.py','models/smollm2','--outfile',str(path.relative_to(ROOT)),'--outtype','f16'],
    'quantization':'F16','gguf_bytes':path.stat().st_size,'gguf_sha256':digest,
    'metadata':metadata,'tokenizer_vocabulary_size':49152,
    'chat_template_matches_official_source':True,
    'source_tokenizer_hashes':json.loads((ROOT/'artifacts/week1/environment/smollm2_artifact_hashes.json').read_text(encoding='utf-8')),
    'offline_phone_generation_proven':False,
}
(directory/'conversion_metadata.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('metadata','source_tokenizer_hashes')},indent=2))
