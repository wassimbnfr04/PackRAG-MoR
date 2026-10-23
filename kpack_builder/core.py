from __future__ import annotations
import hashlib
import json
import math
import re
import shutil
import sqlite3
import stat
import struct
import tempfile
import unicodedata
import zipfile
from contextlib import closing
from pathlib import Path

import numpy as np
import rfc8785
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

MAX_ENTRIES = 5000
MAX_ENTRY = 256 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_MANIFEST = 1024 * 1024
CONTROL = {'manifest.json', 'manifest.sig'}
PROFILE_ID = 'granite97m-multi-r2-384-v1'
HEADER = struct.Struct('<8sHBBHHI32s32s')
SEMVER = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$')

class PackError(ValueError): pass

def require(condition, message):
    if not condition: raise PackError(message)

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def canonical(obj) -> bytes: return rfc8785.dumps(obj)
def key_id(pub: bytes) -> str: return 'ed25519:' + sha(pub)

def safe_path(name: str):
    require(bool(name) and '\\' not in name and ':' not in name and not name.startswith('/'), 'Unsafe ZIP path')
    require(unicodedata.normalize('NFC', name) == name, 'Non-normalized path')
    for part in name.split('/'):
        require(part not in ('','.', '..') and not part.endswith((' ', '.')), 'Unsafe path segment')
        require(not any(ord(c) < 32 or c in '<>"|?*' for c in part), 'Windows path hazard')
        require(not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part), 'Windows device name')
    require(name in CONTROL or name in ('knowledge.sqlite','dense.kdx') or name.startswith('sources/'), 'Forbidden payload path')
    require(Path(name).suffix.lower() not in {'.exe','.dll','.so','.py','.js','.sh','.bat','.cmd','.ps1','.jar','.dex','.apk','.sql','.gguf','.onnx','.pt','.safetensors'}, 'Executable-like payload')

def verified_manifest(raw: bytes, signature: bytes, pinned: list[bytes]) -> dict:
    require(0 < len(pinned) <= 8 and len(set(pinned)) == len(pinned), 'Invalid trust store')
    require(len(signature) == 64 and len(raw) <= MAX_MANIFEST, 'Invalid control size')
    matches = []
    for pub in pinned:
        require(len(pub) == 32, 'Public key must have 32 bytes')
        try: VerifyKey(pub).verify(raw, signature); matches.append(pub)
        except BadSignatureError: pass
    require(len(matches) == 1, 'Unknown signer or invalid signature')
    try:
        m = json.loads(raw)
        require(canonical(m) == raw, 'Manifest is not RFC 8785 canonical JSON')
        require(m['publisher']['key_id'] == key_id(matches[0]), 'Signer/key_id mismatch')
        audit_manifest(m)
        return m
    except (KeyError, TypeError, json.JSONDecodeError, rfc8785.CanonicalizationError) as e:
        raise PackError('Invalid manifest: ' + str(e)) from e

def audit_manifest(m):
    fields = {'schema_version','pack_id','name','version','release_timestamp','publisher','languages','jurisdictions','domain','freshness','embedding_profile','compatible_retrieval_profile','generator_compatibility','files','counts','calibration','build'}
    require(isinstance(m,dict) and set(m) == fields, 'Manifest fields mismatch')
    require(m['schema_version']=='1.0' and bool(SEMVER.fullmatch(m['version'])), 'Schema/SemVer mismatch')
    require(bool(re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)+',m['pack_id'])), 'Invalid pack ID')
    require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',m['release_timestamp'])), 'Invalid release timestamp')
    require(m['compatible_retrieval_profile']=='mobile-v1', 'Incompatible retrieval profile')
    p = m['embedding_profile']
    require(p['profile_id']==PROFILE_ID and p['model_id']=='ibm-granite/granite-embedding-97m-multilingual-r2', 'Incompatible embedding profile')
    require(p['dimension']==384 and p['dtype']=='float32' and p['normalized'] is True and p['metric']=='cosine', 'Invalid dense profile')
    require(bool(re.fullmatch('[0-9a-f]{40}',p['model_revision'])), 'Unpinned model revision')
    require(bool(re.fullmatch('[0-9a-f]{64}',p['model_sha256'])), 'Invalid model hash')
    require(m['generator_compatibility']==dict(core_api='1.x',preferred_generator_language='en',neural_cache_required=False), 'Invalid generator contract')
    allowed_cal={'status','dataset_sha256','method','min_agreed_dense_cosine','min_dense_only_cosine','precision','recall'}
    c=m['calibration']; require(set(c)<=allowed_cal,'Pack overrides runtime policy')
    for k in ('min_agreed_dense_cosine','min_dense_only_cosine','precision','recall'):
        v=c.get(k)
        if v is not None:
            require(type(v) in (int,float) and math.isfinite(v) and (-1 if 'cosine' in k else 0)<=v<=1,'Invalid calibration')
    if c.get('status')!='UNCALIBRATED':
        require(all(c.get(k) is not None for k in allowed_cal-{'status'}), 'Missing release calibration')
    files=m['files']; require(isinstance(files,list) and len(files)<=MAX_ENTRIES-2, 'Invalid file list')
    names=[]
    for f in files:
        require(set(f)=={'path','sha256','bytes','media_type','required'},'Invalid file record')
        safe_path(f['path']); require(f['path'] not in CONTROL,'Control file cannot hash itself')
        require(type(f['bytes']) is int and 0<=f['bytes']<=MAX_ENTRY,'Invalid file length')
        require(bool(re.fullmatch('[0-9a-f]{64}',f['sha256'])),'Invalid payload hash')
        require(type(f['required']) is bool,'Invalid required flag')
        names.append(f['path'])
    require(names==sorted(names) and len({n.casefold() for n in names})==len(names), 'Unsorted/duplicate file declaration')
    require({'knowledge.sqlite','dense.kdx'}<=set(names), 'Missing required data')
    require(sum(f['bytes'] for f in files)<=MAX_TOTAL,'Declared archive too large')
    require(set(m['counts'])=={'sources','chunks','relations'} and all(type(v) is int and v>=0 for v in m['counts'].values()),'Invalid counts')

def audit_archive(z):
    infos=z.infolist(); require(len(infos)<=MAX_ENTRIES,'Too many archive entries')
    seen=set(); total=0
    for i in infos:
        safe_path(i.filename)
        require(i.filename.casefold() not in seen,'Duplicate ZIP name'); seen.add(i.filename.casefold())
        require(not i.is_dir() and not i.flag_bits & 1,'Directories/encryption forbidden')
        mode=i.external_attr>>16
        require(stat.S_IFMT(mode) in (0,stat.S_IFREG),'Non-regular ZIP entry')
        require(i.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'Unsupported ZIP compression')
        require(i.file_size<=MAX_ENTRY,'Oversized archive entry')
        total+=i.file_size; require(total<=MAX_TOTAL,'Oversized archive')
    require(CONTROL<={i.filename for i in infos},'Missing control files')
    require(z.getinfo('manifest.json').file_size<=MAX_MANIFEST and z.getinfo('manifest.sig').file_size==64,'Invalid control sizes')

def bounded_read(z,name,limit):
    with z.open(name) as f:
        data=f.read(limit+1)
        require(len(data)<=limit,'Payload exceeded signed size')
        return data

def validate_database(path: Path, m: dict):
    # Never run the FTS integrity command on the hash-verified immutable original.
    before=sha(path.read_bytes())
    with tempfile.TemporaryDirectory() as t:
        copy=Path(t)/'validation.sqlite'; shutil.copyfile(path,copy)
        with closing(sqlite3.connect(copy)) as db, db:
            db.execute('PRAGMA trusted_schema=OFF')
            require(db.execute('PRAGMA integrity_check').fetchall()==[('ok',)], 'SQLite integrity failure')
            require(not db.execute('PRAGMA foreign_key_check').fetchall(),'SQLite foreign-key failure')
            objects=db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            allowed={'sources','chunks','chunks_fts','relations','aliases','derived_texts','aliases_norm_idx',
                     'chunks_fts_data','chunks_fts_idx','chunks_fts_docsize','chunks_fts_config'}
            require(all(name in allowed and typ in ('table','index') for typ,name,sql in objects),'Unexpected SQLite schema object')
            schema=Path(__file__).with_name('schema.sql').read_text(encoding='utf-8')
            with closing(sqlite3.connect(':memory:')) as expected:
                expected.executescript(schema)
                for table in ('sources','chunks','relations','aliases','derived_texts'):
                    require(db.execute(f'PRAGMA table_info({table})').fetchall()==expected.execute(f'PRAGMA table_info({table})').fetchall(), 'Schema mismatch: '+table)
                    require(db.execute(f'PRAGMA foreign_key_list({table})').fetchall()==expected.execute(f'PRAGMA foreign_key_list({table})').fetchall(), 'Foreign-key schema mismatch')
            fts=dict((name,sql) for typ,name,sql in objects)['chunks_fts']
            normalized=re.sub(r'\s+','',fts).lower()
            require("usingfts5(" in normalized and "content='chunks'" in normalized and "content_rowid='rowid'" in normalized and "tokenize='unicode61remove_diacritics2'" in normalized,'Invalid FTS schema')
            db.execute("INSERT INTO chunks_fts(chunks_fts,rank) VALUES('integrity-check',1)")
            for name in ('sources','chunks','relations'):
                require(db.execute(f'SELECT count(*) FROM {name}').fetchone()[0]==m['counts'][name], 'Count mismatch: '+name)
            rows=db.execute('SELECT chunk_id,dense_row,canonical_text,text_sha256 FROM chunks ORDER BY dense_row').fetchall()
            require([r[1] for r in rows]==list(range(len(rows))),'Invalid dense mapping')
            for _,_,text,hash_ in rows: require(sha(text.encode('utf-8'))==hash_,'Canonical text hash mismatch')
            ids=[r[0] for r in rows]
    require(sha(path.read_bytes())==before,'Staged DB mutated during validation')
    return ids

def make_kdx(vectors, profile, ids):
    a=np.asarray(vectors,dtype='<f4')
    require(a.shape==(len(ids),384),'Wrong vector shape')
    require(np.isfinite(a).all() and np.all(np.abs(np.linalg.norm(a,axis=1)-1)<=0.01),'Invalid vector norms')
    return HEADER.pack(b'KDX1\0\0\0\0',1,1,1,384,1,len(ids),bytes.fromhex(sha(canonical(profile))),bytes.fromhex(sha(canonical(ids))))+a.tobytes()

def audit_kdx(data, profile, ids):
    require(len(data)>=84,'Truncated KDX header')
    magic,version,dtype,metric,dim,flags,n,ph,mh=HEADER.unpack_from(data)
    require((magic,version,dtype,metric,dim,flags)==(b'KDX1\0\0\0\0',1,1,1,384,1),'Invalid KDX header')
    require(n==len(ids) and len(data)==84+n*dim*4,'KDX count/size mismatch')
    require(ph==bytes.fromhex(sha(canonical(profile))) and mh==bytes.fromhex(sha(canonical(ids))),'KDX profile/mapping hash mismatch')
    a=np.frombuffer(data, dtype='<f4', offset=84).reshape(n,dim)
    require(np.isfinite(a).all(),'Nonfinite KDX vector')
    require(np.all(np.abs(np.linalg.norm(a,axis=1)-1)<=0.01),'KDX vector norm mismatch')

def validate(path: Path, pinned: list[bytes], *, developer_mode=False) -> dict:
    try:
        with zipfile.ZipFile(path) as z:
            audit_archive(z)
            m=verified_manifest(bounded_read(z,'manifest.json',MAX_MANIFEST),bounded_read(z,'manifest.sig',64),pinned)
            require(developer_mode or m['calibration'].get('status')!='UNCALIBRATED','Uncalibrated pack requires developer mode')
            require({i.filename for i in z.infolist()}==CONTROL|{f['path'] for f in m['files']}, 'Undeclared/missing payload')
            with tempfile.TemporaryDirectory() as t:
                stage=Path(t)
                for f in m['files']:
                    data=bounded_read(z,f['path'],f['bytes'])
                    require(len(data)==f['bytes'] and sha(data)==f['sha256'],'Payload hash/length mismatch: '+f['path'])
                    dest=stage/f['path']; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
                ids=validate_database(stage/'knowledge.sqlite',m)
                audit_kdx((stage/'dense.kdx').read_bytes(),m['embedding_profile'],ids)
            return dict(status='PASS', manifest=m,manifest_sha256=sha(z.read('manifest.json')),archive_transport_sha256=sha(path.read_bytes()))
    except (sqlite3.DatabaseError,zipfile.BadZipFile,KeyError,OSError,struct.error) as e:
        raise PackError(str(e)) from e

def write_archive(out: Path, m: dict, payloads: dict[str, bytes], signing_key: SigningKey):
    m['files']=[dict(path=p,sha256=sha(b),bytes=len(b),media_type='application/vnd.sqlite3' if p.endswith('.sqlite') else 'application/octet-stream',required=True) for p,b in sorted(payloads.items())]
    audit_manifest(m)
    raw=canonical(m)
    files=dict(payloads, **{'manifest.json':raw,'manifest.sig':signing_key.sign(raw).signature})
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w') as z:
        for p,b in sorted(files.items()):
            info=zipfile.ZipInfo(p,date_time=(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3; info.external_attr=(stat.S_IFREG|0o644)<<16
            z.writestr(info,b)
    return out

def query_identifier(path: Path, pinned: list[bytes], identifier: str, *, developer_mode=False):
    validate(path,pinned,developer_mode=developer_mode)
    with tempfile.TemporaryDirectory() as t, zipfile.ZipFile(path) as z:
        dbpath=Path(t)/'knowledge.sqlite'; dbpath.write_bytes(z.read('knowledge.sqlite'))
        with closing(sqlite3.connect(dbpath.as_uri()+'?mode=ro&immutable=1',uri=True)) as db:
            rows=db.execute("SELECT c.chunk_id,c.canonical_text,c.locator FROM aliases a JOIN chunks c ON a.target_id=c.chunk_id WHERE a.normalized_alias=? AND a.target_type='chunk' ORDER BY c.chunk_id",(unicodedata.normalize('NFKC',identifier).casefold().strip(),)).fetchall()
    return dict(status='AMBIGUOUS_IDENTIFIER' if len(rows)>1 else 'FOUND_REQUIRES_EVIDENCE_ADMISSION' if rows else 'INSUFFICIENT_EVIDENCE', chunks=rows, algorithm='week1_identifier_smoke_only')
