"""New signed metadata corpus; actual Granite vectors follow the changed headers.

No authority preference, legal truth, release calibration or graph expansion.
Hard-coded metadata/edges are the expected values, not a runtime-derived oracle.
"""
import argparse
import copy
import json
import shutil
import sqlite3
import zipfile
import numpy as np
from contextlib import closing
from pathlib import Path
from nacl.signing import SigningKey
from kpack_builder.core import canonical,key_id,sha,write_archive,make_kdx
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder,document_input
from product.packrag.packs import VerifiedPack
from product.packrag.source_metadata import source_metadata

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    asset=ROOT/'product/android/app/src/androidTest/assets/source-metadata-corpus'
    if asset.exists():
        previous=ROOT/'artifacts/v1.3/m4/source-metadata-fixtures-0001'
        assert {p.name for p in asset.iterdir()}=={'source-metadata.kpack','public-key.raw','cases.json'}
        assert all(p.read_bytes()==(previous/p.name).read_bytes() for p in asset.iterdir()),'Only unchanged draft source assets may be replaced'
    prior=ROOT/'artifacts/v1.3/m4/validity-fixtures-0003';old=json.loads((prior/'cases.json').read_text())
    original=prior/'validity-boundaries.kpack';assert file_sha(original)==old['pack_sha256']
    with zipfile.ZipFile(original) as archive:
        manifest=json.loads(archive.read('manifest.json'));dense=archive.read('dense.kdx');db_bytes=archive.read('knowledge.sqlite')
    facts={
        'baseline':dict(authority_rank=None,document_version=None,issued_at=None,article=None),
        'historical':dict(authority_rank=0,document_version='Revision A',issued_at='2010-01-01',article='Article 137'),
        'future':dict(authority_rank=1,document_version='Future edition',issued_at='2027-01-01T00:00:00Z',article='Article 137'),
        'narrow':dict(authority_rank=2,document_version='révision B',issued_at='2026-01-01T00:00:00.125Z',article='12 bis'),
        'disjoint':dict(authority_rank=2147483647,document_version='',issued_at=None,article=''),
        'unknown':dict(authority_rank=None,document_version='نسخة تجريبية',issued_at=None,article='𝟙37'),
        'wrong':dict(authority_rank=4,document_version='not-a-semver',issued_at='2020-01-01',article='Article 137'),
        'unscoped':dict(authority_rank=4,document_version=None,issued_at=None,article=None),
    }
    edges=[('narrow','baseline','amends','explicit-reference',1.0),('future','baseline','supersedes','curated',0.75),
           ('unknown','baseline','exception_to','curated',0.5),('historical','baseline','cites','explicit-reference',0.0),
           ('baseline','narrow','see_also','structure',1.0)]
    stage=run/'stage';stage.mkdir();db_path=stage/'knowledge.sqlite';db_path.write_bytes(db_bytes)
    with closing(sqlite3.connect(db_path)) as db,db:
        ids=dict(db.execute('SELECT locator,chunk_id FROM chunks'))
        for locator,fact in facts.items():
            db.execute('UPDATE sources SET authority_rank=?,document_version=?,issued_at=?,canonical_uri=? WHERE source_id=(SELECT source_id FROM chunks WHERE locator=?)',
                (fact['authority_rank'],fact['document_version'],fact['issued_at'],'https://example.invalid/synthetic/'+locator,locator))
            db.execute('UPDATE chunks SET article=? WHERE locator=?',(fact['article'],locator))
        for a,b,kind,provenance,confidence in edges:
            db.execute('INSERT INTO relations VALUES(?,?,?,?,?)',(ids[a],ids[b],kind,provenance,confidence))
        # Article changed; rebuild required external-content FTS without re-embedding.
        db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite')
    with closing(sqlite3.connect(db_path)) as db:
        db.row_factory=sqlite3.Row
        ordered=[dict(row) for row in db.execute('SELECT * FROM chunks ORDER BY dense_row')]
    # The fixed recipe's second field is section_or_article; third is a string
    # contextual prefix, not a nullable article. This legal fixture prefers a
    # nonempty article identifier, otherwise the section; prefix is empty.
    embedding_inputs=[dict(chunk_id=row['chunk_id'],input=document_input(row['title'],row['article'] or row['section'] or '', '',row['canonical_text'])) for row in ordered]
    (run/'embedding-inputs.json').write_text(json.dumps(embedding_inputs,ensure_ascii=True,indent=2)+'\n')
    vectors=np.asarray([encoder.encode(row['input']) for row in embedding_inputs],dtype=np.float32)
    dense=make_kdx(vectors,manifest['embedding_profile'],[row['chunk_id'] for row in ordered])
    signer=SigningKey.generate();public=bytes(signer.verify_key);(run/'public-key.raw').write_bytes(public)
    manifest.update(pack_id='org.packrag.contract.source-metadata',name='SYNTHETIC SOURCE METADATA — NO AUTHORITY DECISION',domain='law')
    manifest['publisher']=dict(name='EPHEMERAL TEST ONLY',key_id=key_id(public))
    manifest['counts']['relations']=len(edges);manifest['build']['source_manifest_sha256']=sha(canonical(dict(facts=facts,edges=edges)))
    path=run/'source-metadata.kpack';write_archive(path,manifest,{'knowledge.sqlite':db_path.read_bytes(),'dense.kdx':dense},signer)
    expected_relations=sorted([dict(from_chunk_id=ids[a],to_chunk_id=ids[b],relation_type=kind,provenance=provenance,confidence=confidence) for a,b,kind,provenance,confidence in edges],key=lambda r:(r['from_chunk_id'],r['to_chunk_id'],r['relation_type']))
    expected=[dict(locator=locator,chunk_id=ids[locator],metadata={**fact,'publisher_key_id':key_id(public),'relations':[r for r in expected_relations if ids[locator] in (r['from_chunk_id'],r['to_chunk_id'])]}) for locator,fact in facts.items()]
    with VerifiedPack(path,[public],developer_mode=True) as pack:
        assert list(pack.relations)==expected_relations
        for row in expected:assert source_metadata(pack,pack.by_id[row['chunk_id']])==row['metadata'],row['locator']
    # New article text changes sparse matching. Freeze new numeric ranks below,
    # while independent eligible sets and ambiguity stay exactly those of C1.
    from product.packrag.retrieval import Query,retrieve
    cases=[]
    with VerifiedPack(path,[public],developer_mode=True) as pack:
        for case in old['cases']:
            query=Query(old['query_raw'],case['as_of'],case['jurisdiction'],case['current_law'])
            candidates,ambiguous=retrieve((pack,),query,np.asarray(old['query_vector'],dtype=np.float32))
            assert {c.chunk['locator'] for c in candidates}==set(case['expected_locators'])
            assert ambiguous==case['ambiguous'],'Metadata must not secretly resolve ambiguity'
            cases.append({**{k:v for k,v in case.items() if k!='candidates'},'candidates':[dict(chunk_id=c.chunk['chunk_id'],locator=c.chunk['locator'],sparse_rank=c.sparse_rank,dense_rank=c.dense_rank,rrf=c.rrf,cosine=c.dense_cosine) for c in candidates]})
    record=dict(status='SIGNED_SYNTHETIC_METADATA_FROZEN_NOT_AUTHORITY_OR_DEVICE_ACCEPTANCE',script_sha256=file_sha(Path(__file__)),pack_sha256=file_sha(path),public_key_sha256=file_sha(run/'public-key.raw'),prior_validity_pack_sha256=old['pack_sha256'],dense_payload_sha256=sha(dense),dense_vectors='NEW_ACTUAL_GRANITE_DOCUMENT_INPUT_WITH_CHANGED_ARTICLE_HEADERS',document_heading_policy='NONEMPTY_ARTICLE_ELSE_SECTION_EMPTY_CONTEXT_PREFIX',embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),query_vector_origin='PRIOR_ACTUAL_NORMALIZED_QUERY_UNCHANGED',private_seed='EPHEMERAL_NOT_SAVED',query_raw=old['query_raw'],query_vector=old['query_vector'],metadata_cases=expected,relations=expected_relations,retrieval_cases=cases,authority_sort=False,graph_expansion=False)
    (run/'cases.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n');asset.mkdir(exist_ok=True)
    for source in [path,run/'public-key.raw',run/'cases.json']:shutil.copyfile(source,asset/source.name)
    print('Frozen8 signed metadata cases,5 directed edges and12 retrieval references; no authority resolution.')


if __name__=='__main__':main()
