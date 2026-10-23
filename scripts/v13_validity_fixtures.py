"""Freeze new signed synthetic interval fixtures with actual Granite vectors.

Expected eligible sets and interval cases are written independently below.
Numeric retrieval references are desktop parity oracles, not semantic gold.
The signing seed exists only in memory. No source/translation review is claimed.
"""
import argparse
import json
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from nacl.signing import SigningKey
from kpack_builder.core import write_archive
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query, eligible, retrieve
from product.packrag.validity import validity_provenance
from scripts.v13_query_identifier_fixtures import make_pack

ROOT = Path(__file__).resolve().parents[1]


def contracts():
    base = dict(source_from="2020-01-01",source_until="2030-01-01",effective_from=None,
                effective_until_excl=None,jurisdiction="MA",legal_status="active")
    cases=[]
    def add(name,as_of,expected,changes=None,jurisdiction="MA",current=False):
        cases.append(dict(id=name,row={**base,**(changes or {})},as_of=as_of,jurisdiction=jurisdiction,current_law=current,eligible=expected))
    add("SOURCE_START_BEFORE","2019-12-31",False)
    add("SOURCE_START_INCLUSIVE","2020-01-01",True)
    add("SOURCE_END_BEFORE","2029-12-31",True)
    add("SOURCE_END_EXCLUSIVE","2030-01-01",False)
    add("CHUNK_LATER_START_BEFORE","2025-12-31",False,{"effective_from":"2026-01-01"})
    add("CHUNK_LATER_START_INCLUSIVE","2026-01-01",True,{"effective_from":"2026-01-01"})
    add("SOURCE_LATER_START","2019-12-31",False,{"effective_from":"2010-01-01"})
    add("CHUNK_EARLIER_END_BEFORE","2026-12-31",True,{"effective_until_excl":"2027-01-01"})
    add("CHUNK_EARLIER_END_EXCLUSIVE","2027-01-01",False,{"effective_until_excl":"2027-01-01"})
    add("SOURCE_EARLIER_END","2030-01-01",False,{"effective_until_excl":"2040-01-01"})
    add("EMPTY_DISJOINT","2025-01-01",False,{"effective_from":"2031-01-01","effective_until_excl":"2032-01-01"})
    add("EMPTY_TOUCHING","2030-01-01",False,{"effective_from":"2030-01-01","effective_until_excl":"2031-01-01"})
    add("UNKNOWN_BOTH","0001-01-01",True,{"source_from":None,"source_until":None})
    add("UNKNOWN_BOTH_FAR_FUTURE","9999-12-31",True,{"source_from":None,"source_until":None})
    add("UNKNOWN_START","0001-01-01",True,{"source_from":None})
    add("UNKNOWN_END","9999-12-31",True,{"source_until":None})
    add("UNKNOWN_SOURCE_CHUNK_BOUND","2025-12-31",False,{"source_from":None,"source_until":None,"effective_from":"2026-01-01"})
    add("UNKNOWN_SOURCE_CHUNK_BOUND_EDGE","2026-01-01",True,{"source_from":None,"source_until":None,"effective_from":"2026-01-01"})
    add("JURISDICTION_WRONG","2026-01-01",False,jurisdiction="FR")
    add("JURISDICTION_UNREQUESTED","2026-01-01",True,jurisdiction=None)
    add("JURISDICTION_UNKNOWN_REQUESTED","2026-01-01",False,{"jurisdiction":None})
    add("JURISDICTION_UNKNOWN_UNREQUESTED","2026-01-01",True,{"jurisdiction":None},jurisdiction=None)
    add("JURISDICTION_SUBDIVISION_EXACT","2026-01-01",True,{"jurisdiction":"MA-01"},jurisdiction="MA-01")
    add("JURISDICTION_SUBDIVISION_NOT_COUNTRY","2026-01-01",False,{"jurisdiction":"MA-01"})
    for status in ("repealed","superseded"):
        add(status.upper()+"_CURRENT","2026-01-01",False,{"legal_status":status},current=True)
        add(status.upper()+"_HISTORICAL","2026-01-01",True,{"legal_status":status})
    for status in ("active","historical","n/a",None):
        add("CURRENT_"+str(status),"2026-01-01",True,{"legal_status":status},current=True)
    # Fixed expected provenance catches invented source dates even with bounded chunks.
    provenance=[dict(id="UNKNOWN_SOURCE_FINITE_CHUNK",row={**base,"source_from":None,"source_until":None,"effective_from":"2026-01-01","effective_until_excl":"2027-01-01"},expected=dict(source_from=None,source_until_excl=None,chunk_from="2026-01-01",chunk_until_excl="2027-01-01",effective_from="2026-01-01",effective_until_excl="2027-01-01",source_start_unknown=True,source_end_unknown=True,chunk_start_inherits=False,chunk_end_inherits=False,empty_intersection=False,jurisdiction="MA",legal_status="active")),
        dict(id="FULL_SOURCE_INHERITANCE",row=base,expected=dict(source_from="2020-01-01",source_until_excl="2030-01-01",chunk_from=None,chunk_until_excl=None,effective_from="2020-01-01",effective_until_excl="2030-01-01",source_start_unknown=False,source_end_unknown=False,chunk_start_inherits=True,chunk_end_inherits=True,empty_intersection=False,jurisdiction="MA",legal_status="active")),
        dict(id="EMPTY_INTERSECTION",row={**base,"effective_from":"2030-01-01","effective_until_excl":"2031-01-01"},expected=dict(source_from="2020-01-01",source_until_excl="2030-01-01",chunk_from="2030-01-01",chunk_until_excl="2031-01-01",effective_from="2030-01-01",effective_until_excl="2030-01-01",source_start_unknown=False,source_end_unknown=False,chunk_start_inherits=False,chunk_end_inherits=False,empty_intersection=True,jurisdiction="MA",legal_status="active"))]
    return dict(purpose="INDEPENDENT_FIXED_SYNTHETIC_INTERVAL_EXPECTATIONS_NOT_LEGAL_GOLD",cases=cases,provenance_cases=provenance)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/'product/android/app/src/androidTest/assets/validity-corpus';assert not asset.exists()
    contract=contracts()
    for target in [ROOT/'product/tests/validity-cases.json',ROOT/'product/android/core-model/src/test/resources/validity-cases.json',ROOT/'product/android/app/src/androidTest/assets/validity-cases.json']:
        content=json.dumps(contract,indent=2)+'\n'
        if target.exists():
            assert target.read_text(encoding='utf-8')==content,'Existing shared contract content differs'
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8')
    signer=SigningKey.generate();public=bytes(signer.verify_key);(run/'public-key.raw').write_bytes(public)
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
    rows=[('baseline',74,'2020-01-01','2030-01-01',None,None,'MA','active'),
          ('historical',68,'2010-01-01','2020-01-01',None,None,'MA','superseded'),
          ('future',81,'2027-01-01','2030-01-01',None,None,'MA','active'),
          ('narrow',76,'2020-01-01','2030-01-01','2026-01-01','2027-01-01','MA','active'),
          ('disjoint',70,'2020-01-01','2022-01-01','2023-01-01','2024-01-01','MA','active'),
          ('unknown',78,None,None,'2026-01-01','2027-01-01','MA','historical'),
          ('wrong',79,None,None,None,None,'FR','active'),('unscoped',80,None,None,None,None,None,None)]
    chunks=[dict(id=r[0],title='Article-T',locator=r[0],text=f'The synthetic Article-T temperature is {r[1]} °C.',aliases=['Article-T']) for r in rows]
    stage=run/'stage';stage.mkdir();path,ids=make_pack(stage,'validity-boundaries',chunks,encoder,signer)
    directory=stage/'validity-boundaries'
    with closing(sqlite3.connect(directory/'knowledge.sqlite')) as db,db:
        for r,identifier in zip(rows,ids):
            db.execute('UPDATE sources SET effective_from=?,effective_until_excl=?,jurisdiction=?,legal_status=? WHERE source_id=(SELECT source_id FROM chunks WHERE chunk_id=?)',(r[2],r[3],r[6],r[7],identifier))
            db.execute('UPDATE chunks SET effective_from=?,effective_until_excl=? WHERE chunk_id=?',(r[4],r[5],identifier))
    import zipfile
    with zipfile.ZipFile(path) as archive:
        manifest=json.loads(archive.read('manifest.json'));dense=archive.read('dense.kdx')
    manifest['jurisdictions']=['MA','FR'];manifest['freshness']['update_check_after']='2020-01-01'
    final=run/'validity-boundaries.kpack'
    write_archive(final,manifest,{'knowledge.sqlite':(directory/'knowledge.sqlite').read_bytes(),'dense.kdx':dense},signer)
    scenarios=[('HISTORICAL_ONLY','2019-12-31','MA',False,['historical']),('CURRENT_REJECTS_SUPERSEDED','2019-12-31','MA',True,[]),
        ('START_INCLUSIVE_END_EXCLUSIVE','2020-01-01','MA',False,['baseline']),('SOLE_BASELINE','2025-12-31','MA',False,['baseline']),
        ('CHUNK_START_INCLUSIVE','2026-01-01','MA',False,['baseline','narrow','unknown']),('CURRENT_HISTORICAL_STATUS_NOT_REPEALED','2026-01-01','MA',True,['baseline','narrow','unknown']),
        ('CHUNK_END_EXCLUSIVE_FUTURE_START','2027-01-01','MA',False,['baseline','future']),('ALL_KNOWN_EXPIRED','2030-01-01','MA',False,[]),
        ('WRONG_JURISDICTION_SOURCE_ONLY','2026-01-01','FR',False,['wrong']),('UNREQUESTED_JURISDICTION','2026-01-01',None,False,['baseline','narrow','unknown','wrong','unscoped']),
        ('UNKNOWN_EARLY','0001-01-01',None,False,['wrong','unscoped']),('UNKNOWN_LATE','9999-12-31',None,True,['wrong','unscoped'])]
    references=[]
    with VerifiedPack(final,[public],developer_mode=True) as pack:
        vector=encoder.encode('article-t temperature')
        for name,as_of,jurisdiction,current,expected in scenarios:
            query=Query('Article-T temperature',as_of,jurisdiction,current)
            allowed={row['locator'] for row in pack.chunks if eligible(row,query)};assert allowed==set(expected),(name,allowed,expected)
            candidates,ambiguous=retrieve((pack,),query,vector)
            assert {c.chunk['locator'] for c in candidates}==allowed
            assert ambiguous==(len(allowed)>1)
            assert sorted(c.dense_rank for c in candidates)==list(range(1,len(allowed)+1))
            references.append(dict(id=name,as_of=as_of,jurisdiction=jurisdiction,current_law=current,expected_locators=expected,ambiguous=ambiguous,
                candidates=[dict(chunk_id=c.chunk['chunk_id'],locator=c.chunk['locator'],sparse_rank=c.sparse_rank,dense_rank=c.dense_rank,rrf=c.rrf,cosine=c.dense_cosine,validity=validity_provenance(c.chunk)) for c in candidates]))
    record=dict(status='SIGNED_SYNTHETIC_REFERENCES_FROZEN_NOT_ACCEPTANCE',script_sha256=file_sha(Path(__file__)),private_seed='EPHEMERAL_NOT_SAVED',pack_sha256=file_sha(final),public_key_sha256=file_sha(run/'public-key.raw'),query_raw='Article-T temperature',query_vector=vector.tolist(),cases=references,shared_contract_cases=len(contract['cases']),provenance_cases=len(contract['provenance_cases']),freshness_is_advisory=True)
    (run/'cases.json').write_text(json.dumps(record,indent=2)+'\n');asset.mkdir()
    for source in [final,run/'public-key.raw',run/'cases.json']:shutil.copyfile(source,asset/source.name)
    print('Frozen',len(contract['cases']),'interval cases,',len(contract['provenance_cases']),'fixed provenance cases and',len(references),'signed retrieval scenarios')


if __name__=='__main__':main()
