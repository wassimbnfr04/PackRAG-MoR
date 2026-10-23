"""Week 1 synthetic pack: real Granite embeddings, no invented calibration."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
import numpy as np
from nacl.signing import SigningKey
from .core import canonical, sha, key_id, make_kdx, write_archive, validate

ROOT=Path(__file__).resolve().parents[1]

def test_key() -> SigningKey:
    directory=ROOT/'tests/signature_vector'; directory.mkdir(parents=True,exist_ok=True)
    path=directory/'test_private_key'
    if not path.exists(): path.write_bytes(bytes(SigningKey.generate()))
    key=SigningKey(path.read_bytes()); pub=bytes(key.verify_key)
    (directory/'public_key.raw').write_bytes(pub)
    (directory/'README.md').write_text('TEST KEY ONLY — NEVER USE FOR RELEASE\n\nThe raw 32-byte private seed is an intentionally non-secret Week 1 interoperability fixture. Never ship it to Android. Signatures are RAW 64-byte Ed25519 over exact RFC 8785 manifest bytes. key_id = ed25519: + SHA256(raw public key).\n',encoding='utf-8')
    return key

def build(out: Path):
    spec=json.loads((ROOT/'packs/synthetic-week1/pack.json').read_text())
    cases=[json.loads(line) for line in (ROOT/'gates/g0/g0_v1.jsonl').read_text(encoding='utf-8').splitlines()][:10]
    meta=json.loads((ROOT/'artifacts/week1/environment/granite_model_metadata.json').read_text())
    model_path=ROOT/'models/granite'
    required=['model.safetensors','tokenizer.json','tokenizer_config.json','config.json','1_Pooling/config.json']
    hashes={p:sha((model_path/p).read_bytes()) for p in required}
    profile=dict(profile_id='granite97m-multi-r2-384-v1',model_id=meta['id'],model_revision=meta['sha'],
                 model_sha256=hashes['model.safetensors'],tokenizer_hashes={p:h for p,h in hashes.items() if 'tokenizer' in p},
                 dimension=384,dtype='float32',normalized=True,metric='cosine',runtime='onnxruntime-mobile-cpu',
                 pooling=json.loads((model_path/'1_Pooling/config.json').read_text()),max_input_length=512,
                 input_construction='title + newline + locator + newline + canonical_text')
    key=test_key()
    data_dir=out.parent/'build'; data_dir.mkdir(parents=True,exist_ok=True)
    dbpath=data_dir/'knowledge.sqlite'
    # Rebuild rather than mutate an installed/staged pack database.
    if dbpath.exists(): dbpath.unlink()
    ids=[]; embedding_inputs=[]
    with closing(sqlite3.connect(dbpath)) as db, db:
        db.executescript(Path(__file__).with_name('schema.sql').read_text())
        for idx,case in enumerate(cases):
            text=case['evidence'][0]['text']; source_id='synthetic-'+case['case_id']; locator=case['case_id']
            title=spec['equipment'][idx]; text_hash=sha(text.encode('utf-8'))
            chunk_id=sha((source_id+locator+text_hash).encode('utf-8'))[:24]
            assert chunk_id not in ids; ids.append(chunk_id)
            db.execute('INSERT INTO sources(source_id,title,publisher,retrieved_at,language,sha256_original,license,redistribution_allowed,source_type,legal_status) VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (source_id,title,'PackRAG Capstone','2026-09-29','en',text_hash,'CC0-1.0',1,'synthetic','n/a'))
            db.execute('INSERT INTO chunks(chunk_id,source_id,title,locator,canonical_text,search_text,text_sha256,dense_row) VALUES(?,?,?,?,?,?,?,?)',
                       (chunk_id,source_id,title,locator,text,text,text_hash,idx))
            db.execute('INSERT INTO aliases VALUES(?,?,?,?,?)',(title,title.casefold(),'chunk',chunk_id,'equipment-model'))
            embedding_inputs.append(title+'\n'+locator+'\n'+text)
        db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    cache_key=sha(canonical(dict(profile=profile,texts=embedding_inputs)))
    cache=data_dir/(cache_key+'.npy')
    if cache.exists(): vectors=np.load(cache,allow_pickle=False)
    else:
        from sentence_transformers import SentenceTransformer
        import torch
        model=SentenceTransformer(str(model_path),device='cpu',model_kwargs={'attn_implementation':'sdpa'})
        model.max_seq_length=512
        vectors=model.encode(embedding_inputs,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
        np.save(cache,vectors,allow_pickle=False)
    kdx=make_kdx(vectors,profile,ids)
    m=dict(schema_version='1.0',pack_id=spec['pack_id'],name=spec['name'],version=spec['version'],release_timestamp=spec['release_timestamp'],
           publisher=dict(name='PackRAG Capstone — TEST KEY ONLY',key_id=key_id(bytes(key.verify_key))),
           languages=['en'],jurisdictions=[],domain='repair',freshness=dict(update_check_after='2027-01-01',stale_behavior='warn-and-continue'),
           embedding_profile=profile,compatible_retrieval_profile='mobile-v1',
           generator_compatibility=dict(core_api='1.x',preferred_generator_language='en',neural_cache_required=False),
           counts=dict(sources=10,chunks=10,relations=0),calibration=dict(status='UNCALIBRATED',method='candidate-relevance-v1.2',dataset_sha256=None,min_agreed_dense_cosine=None,min_dense_only_cosine=None,precision=None,recall=None),
           build=dict(builder_version='1.2.0-week1',normalizer_version='1.0.0',chunker_version='1.0.0',source_manifest_sha256=sha(canonical(cases)),build_input_sha256=sha(canonical(spec))),files=[])
    write_archive(out,m,{'knowledge.sqlite':dbpath.read_bytes(),'dense.kdx':kdx},key)
    result=validate(out,[bytes(key.verify_key)],developer_mode=True)
    with __import__('zipfile').ZipFile(out) as z:
        for name in ('manifest.json','manifest.sig'):
            (ROOT/'tests/signature_vector'/name).write_bytes(z.read(name))
    (ROOT/'tests/signature_vector/expected.json').write_text(json.dumps(dict(key_id=key_id(bytes(key.verify_key)),manifest_sha256=result['manifest_sha256'],signature_bytes=64,public_key_bytes=32,positive='PASS',negative=['wrong_key','modified_manifest','modified_signature','truncated_signature','unknown_key']),indent=2),encoding='utf-8')
    provenance=dict(spec=spec,embedding_profile=profile,input_hashes=hashes,embedding_inputs=embedding_inputs,**{k:v for k,v in result.items() if k!='manifest'})
    (out.parent/'build_provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False),encoding='utf-8')
    return result
