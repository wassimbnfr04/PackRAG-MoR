"""Acquire exact v1.3 Granite assets; hash every byte and reuse only matching old bytes."""
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO='ibm-granite/granite-embedding-97m-multilingual-r2'
REVISION='c61e626a6255c490879d0af885078b61929d51f6'
DEST=ROOT/'models/v1.3/granite'
OUT=ROOT/'artifacts/v1.3/m0/assets'
NAMES=('README.md','config.json','config_sentence_transformers.json','model.safetensors','modules.json',
       'sentence_bert_config.json','special_tokens_map.json','tokenizer.json','tokenizer_config.json',
       '1_Pooling/config.json','onnx/model.onnx')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    DEST.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    uri=f'https://huggingface.co/api/models/{REPO}/revision/{REVISION}?blobs=true'
    with urllib.request.urlopen(uri,timeout=60) as response:
        metadata=json.load(response)
    assert metadata['sha']==REVISION
    (OUT/'granite-repository.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    siblings={entry['rfilename']:entry for entry in metadata['siblings']}
    manifest=[]
    for name in NAMES:
        target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True)
        entry=siblings[name];expected=entry.get('lfs',{}).get('sha256')
        old=ROOT/'models/granite'/name
        method='PINNED_DOWNLOAD'
        if target.exists():
            method='ALREADY_ACQUIRED'
        elif expected and old.exists() and sha(old)==expected:
            shutil.copyfile(old,target);method='IDENTICAL_OLD_BYTES_WITH_NEW_REVISION_MEMBERSHIP_VERIFIED'
        else:
            partial=target.with_name(target.name+'.part')
            url=f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}'
            with urllib.request.urlopen(url,timeout=180) as response,partial.open('wb') as stream:
                shutil.copyfileobj(response,stream,1024*1024)
            if expected:
                assert sha(partial)==expected,name+' download hash mismatch'
            partial.replace(target)
        digest=sha(target)
        if expected:
            assert digest==expected,name+' pinned LFS hash mismatch'
        if entry.get('size') is not None:
            assert target.stat().st_size==entry['size'],name+' size mismatch'
        manifest.append(dict(path=name,bytes=target.stat().st_size,sha256=digest,acquisition=method,official_lfs_sha256=expected))
        print(f"{name}: {target.stat().st_size} bytes {digest} ({method})",flush=True)
    (OUT/'granite-assets.json').write_text(json.dumps(dict(model_id=REPO,revision=REVISION,files=manifest),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
