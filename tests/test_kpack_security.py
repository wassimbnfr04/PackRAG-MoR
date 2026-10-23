import json
import sqlite3
import struct
import warnings
import zipfile
from contextlib import closing
from pathlib import Path
import pytest
from nacl.signing import SigningKey
from kpack_builder.core import PackError, canonical, sha, validate, verified_manifest, query_identifier

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'packs/synthetic-week1/org.packrag.synthetic.week1-1.0.0.kpack'

@pytest.fixture
def key(): return SigningKey((ROOT/'tests/signature_vector/test_private_key').read_bytes())

def contents():
    with zipfile.ZipFile(PACK) as z: return {i.filename:z.read(i) for i in z.infolist()}

def repack(path, entries, key=None):
    if key is not None:
        m=json.loads(entries['manifest.json'])
        for f in m['files']:
            if f['path'] in entries:
                b=entries[f['path']]; f.update(bytes=len(b),sha256=sha(b))
        entries['manifest.json']=canonical(m); entries['manifest.sig']=key.sign(entries['manifest.json']).signature
    with zipfile.ZipFile(path,'w') as z:
        for p,b in entries.items(): z.writestr(p,b)
    return path

def reject(path,key):
    with pytest.raises(PackError): validate(path,[bytes(key.verify_key)],developer_mode=True)

def test_valid_pack_and_immutable_query(key):
    original=sha(PACK.read_bytes())
    assert validate(PACK,[bytes(key.verify_key)],developer_mode=True)['status']=='PASS'
    query=query_identifier(PACK,[bytes(key.verify_key)],'Aster-9',developer_mode=True)
    assert len(query['chunks'])==1 and '74 °C' in query['chunks'][0][1]
    assert sha(PACK.read_bytes())==original
    with pytest.raises(PackError,match='developer'): validate(PACK,[bytes(key.verify_key)])

@pytest.mark.parametrize('mutation',['wrong_key','modified_manifest','modified_signature','truncated_signature','unknown_key','publisher_mismatch'])
def test_signature_vector(mutation,key):
    entries=contents(); pub=bytes(key.verify_key); raw=entries['manifest.json']; sig=entries['manifest.sig']
    if mutation in ('wrong_key','unknown_key'): pub=bytes(SigningKey.generate().verify_key)
    elif mutation=='modified_manifest': raw=raw+b' '
    elif mutation=='modified_signature': sig=bytes([sig[0]^1])+sig[1:]
    elif mutation=='truncated_signature': sig=sig[:-1]
    elif mutation=='publisher_mismatch':
        m=json.loads(raw); m['publisher']['key_id']='ed25519:'+'0'*64; raw=canonical(m); sig=key.sign(raw).signature
    with pytest.raises(PackError): verified_manifest(raw,sig,[pub])

@pytest.mark.parametrize('payload',['knowledge.sqlite','dense.kdx'])
def test_payload_tamper(tmp_path,key,payload):
    e=contents(); b=e[payload]; e[payload]=bytes([b[0]^1])+b[1:]
    reject(repack(tmp_path/'tamper.kpack',e),key)

@pytest.mark.parametrize('path',['../evil','/absolute','C:/drive','C:drive','\\\\server\\share','sources/../escape','sources\\bad','sources/NUL.txt','sources/CON','sources/a:stream','sources/a.','sources/a ','sources/a.py','neural/cache.bin'])
def test_zip_paths(tmp_path,key,path):
    e=contents(); e[path]=b'bad'; reject(repack(tmp_path/'path.kpack',e),key)

def test_duplicate_zip(tmp_path,key):
    path=repack(tmp_path/'duplicate.kpack',contents())
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with zipfile.ZipFile(path,'a') as z: z.writestr('knowledge.sqlite',b'duplicate')
    reject(path,key)

@pytest.mark.parametrize('kind',['undeclared','missing','symlink','oversized'])
def test_archive_structure(tmp_path,key,kind):
    e=contents()
    if kind=='undeclared': e['sources/new.txt']=b'undeclared'
    if kind=='missing': del e['dense.kdx']
    path=repack(tmp_path/'archive.kpack',e)
    if kind=='symlink':
        with zipfile.ZipFile(path,'a') as z:
            i=zipfile.ZipInfo('sources/link'); i.create_system=3; i.external_attr=0o120777<<16; z.writestr(i,b'../../target')
    if kind=='oversized':
        raw=bytearray(path.read_bytes()); offset=raw.index(b'PK\x01\x02'); struct.pack_into('<I',raw,offset+24,257*1024*1024); path.write_bytes(raw)
    reject(path,key)

@pytest.mark.parametrize('kind',['magic','truncated','trailing','nan','inf','wrong_dimension','wrong_count','bad_norm','mapping','profile','flags'])
def test_authenticated_kdx_invalid(tmp_path,key,kind):
    e=contents(); b=bytearray(e['dense.kdx'])
    if kind=='magic': b[0]^=1
    elif kind=='truncated': b=b[:-1]
    elif kind=='trailing': b+=b'X'
    elif kind in ('nan','inf','bad_norm'): struct.pack_into('<f',b,84,{'nan':float('nan'),'inf':float('inf'),'bad_norm':100.0}[kind])
    elif kind=='wrong_dimension': struct.pack_into('<H',b,12,383)
    elif kind=='wrong_count': struct.pack_into('<I',b,16,11)
    elif kind=='mapping': b[52]^=1
    elif kind=='profile': b[20]^=1
    elif kind=='flags': struct.pack_into('<H',b,14,3)
    e['dense.kdx']=bytes(b); reject(repack(tmp_path/'kdx.kpack',e,key),key)

@pytest.mark.parametrize('kind',['broken','foreign_key','fts','mapping','schema','count'])
def test_authenticated_database_invalid(tmp_path,key,kind):
    e=contents(); dbpath=tmp_path/'db.sqlite'; dbpath.write_bytes(e['knowledge.sqlite'])
    if kind=='broken': dbpath.write_bytes(b'not sqlite')
    else:
        with closing(sqlite3.connect(dbpath)) as db, db:
            if kind=='foreign_key': db.execute("UPDATE chunks SET source_id='unknown' WHERE dense_row=0")
            elif kind=='fts': db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('delete-all')")
            elif kind=='mapping': db.execute('UPDATE chunks SET dense_row=42 WHERE dense_row=0')
            elif kind=='schema': db.execute('CREATE VIEW malicious AS SELECT * FROM chunks')
            elif kind=='count': db.execute("INSERT INTO relations VALUES('a','b','parent','curated',1)")
    e['knowledge.sqlite']=dbpath.read_bytes(); reject(repack(tmp_path/'db.kpack',e,key),key)

def test_jcs_rejects_reserialized_and_unknown_policy(tmp_path,key):
    e=contents(); m=json.loads(e['manifest.json']); e['manifest.json']=json.dumps(m,indent=2).encode(); e['manifest.sig']=key.sign(e['manifest.json']).signature
    reject(repack(tmp_path/'noncanonical.kpack',e),key)
    m['calibration']['max_evidence_chunks']=999; e['manifest.json']=canonical(m); e['manifest.sig']=key.sign(e['manifest.json']).signature
    reject(repack(tmp_path/'override.kpack',e),key)
