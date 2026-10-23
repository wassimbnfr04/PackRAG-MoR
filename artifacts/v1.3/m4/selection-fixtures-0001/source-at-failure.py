"""Signed synthetic selection controls, independently fixed before retrieval.

Companion placement uses a separate SQL/vector rank oracle to construct the
test, never product retrieval or selector output. Budget boundaries use an
independent XML oracle and the actual GGUF tokenizer, not additive estimates.
No owner final pack, genuine review, release calibration or gold is authored.
"""
import argparse
import copy
from contextlib import closing
from dataclasses import asdict
import html
import json
from pathlib import Path
import shutil
import sqlite3
import traceback
import zipfile

import numpy as np
from nacl.signing import SigningKey
from kpack_builder.core import canonical, sha, write_archive
from product.packrag.config import file_sha, RuntimeContractError
from product.packrag.embedding import GraniteEncoder, document_input
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare
from product.packrag.query_unicode import word_terms
from product.packrag.retrieval import Query, retrieve
from scripts.v13_query_identifier_fixtures import make_pack
from scripts.v13_smoke import ROOT, owned_server, save

QUESTION='What are the safety requirements for BUNDLE-X9?'
FR='La limite continue du contrôleur synthétique est de 74 °C.'
EN='The synthetic controller has a continuous operating temperature limit of 74 °C.'


def original_rows(count):
    texts=[
        'The BUNDLE-X9 synthetic controller has a continuous operating temperature limit of 74 °C.',
        'A technician must inspect the red cable for physical damage.',
        'The protective enclosure must remain securely closed.',
        'A technician must use dry insulated gloves while servicing the unit.',
        'A technician must disconnect the unit from its power supply prior to service.']
    texts += [f'Synthetic maintenance item {i} requires a visual inspection of component {i}.' for i in range(5,count)]
    original='SYNTHETIC TEST MANUAL ONLY\n'+'\n'.join(texts)
    return [dict(id=f'row{i:02}',locator=f'row{i:02}',title='SYNTHETIC TEST MANUAL',text=text,
        source='manual',original=original,aliases=['BUNDLE-X9'],target_type='source') for i,text in enumerate(texts)]


def rank_oracle(db_path,dense,query,ids):
    matrix=np.frombuffer(dense,dtype='<f4',offset=84).reshape(len(ids),384)
    scores={key:float(np.dot(matrix[index],query)) for index,key in enumerate(ids)}
    dense_order=sorted(ids,key=lambda key:(-scores[key],key));dr={key:i for i,key in enumerate(dense_order,1)}
    terms=word_terms(Query(QUESTION,'2026-10-09').normalized)
    with closing(sqlite3.connect(db_path)) as db:
        expression=' OR '.join('"'+word+'"' for word in terms)
        sparse=[row[0] for row in db.execute('SELECT c.chunk_id,bm25(chunks_fts) FROM chunks_fts JOIN chunks c ON c.rowid=chunks_fts.rowid WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts),c.chunk_id',(expression,))][:24]
    sr={key:i for i,key in enumerate(sparse,1)}
    rrf={key:sum(1/(60+r) for r in (sr.get(key),dr.get(key) if dr[key]<=24 else None) if r is not None) for key in ids}
    order=sorted(ids,key=lambda key:(-rrf[key],-scores[key],key))
    return order,[dict(chunk_id=key,sparse_rank=sr.get(key),dense_rank=dr[key] if dr[key]<=24 else None,
        cosine=scores[key],rrf=rrf[key]) for key in order]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT/'artifacts/v1.3/m4');run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/'product/android/app/src/androidTest/assets/selection-corpus';assert not assets.exists()
    fixed=ROOT/'product/tests/fixtures/selection-contracts.json'
    signer=SigningKey.generate();public=bytes(signer.verify_key);(run/'public-key.raw').write_bytes(public)
    encoder=GraniteEncoder(ROOT/'models/v1.3/granite');vector=encoder.encode(Query(QUESTION,'2026-10-09').normalized)
    records=[];cases=[];specifications=[];inputs=[];independent=[];status='FAIL'
    with owned_server(run) as tokenizer:
        try:
            specs=[('atomic-last',5,'atomic'),('five-mandatory',5,'all'),('missing-global',33,'atomic'),
                   ('mandatory-oversize',5,'oversize'),('optional-oversize',2,'optional'),('all-oversize',1,'optional'),
                   ('boundary1200',1,'boundary1200'),('boundary1201',1,'boundary1201')]
            for name,count,kind in specs:
                rows=original_rows(count)
                if kind in ('optional','boundary1200','boundary1201'):
                    rows=[dict(id='thermal',title='SYNTHETIC BUDGET',locator='thermal',text=FR,aliases=['BUNDLE-X9'])]
                    if count==2:rows.append(dict(id='garden',title='SYNTHETIC GARDEN',locator='garden',text='Garden flowers grow beside a pond.',aliases=[]))
                draft,ids=make_pack(run,name,rows,encoder,signer)
                db_path=run/name/'knowledge.sqlite'
                with zipfile.ZipFile(draft) as archive:manifest=json.loads(archive.read('manifest.json'));dense=archive.read('dense.kdx')
                order,rank_rows=rank_oracle(db_path,dense,vector,ids)
                # All manual rows are exact source-alias hits. Budget controls have
                # exactly one exact hit, which precedes any uncalibrated garden row.
                if kind in ('optional','boundary1200','boundary1201'):order=ids
                first,last=order[0],order[-1];edges=[];derived=[]
                if kind in ('atomic','oversize'):edges=[(first,last,'exception_to','explicit-reference',1.0)]
                if kind=='all':edges=[(order[i],order[i+1],'amends','explicit-reference',1.0) for i in range(len(order)-1)]
                expected_pool=order[:32]
                expected_selected=(order[:3]+[last]) if kind=='atomic' and count==5 else order[:4]
                expected='READY'
                if kind=='all' or count==33 or kind=='oversize':expected='INCOMPLETE_LEGAL_CONFLICT_EVIDENCE';expected_selected=[]
                if kind=='optional':expected='NO_RELEVANT_EVIDENCE' if count==2 else 'INPUT_TOO_LONG';expected_selected=[]
                if kind=='boundary1201':expected='INPUT_TOO_LONG';expected_selected=[]
                if kind=='boundary1200':expected_selected=ids
                if kind in ('optional','oversize','boundary1200','boundary1201'):
                    target=first if kind!='oversize' else last
                    # Long generator text, short canonical embedding input. Labels
                    # explicitly assert synthetic protocol provenance only.
                    text=EN+' pad'*2000
                    if kind.startswith('boundary'):
                        cap=int(kind[len('boundary'):]);pack=f'org.packrag.contract.{name}@1.0.0'
                        def block(value):return f'<SOURCE id="S1" pack="{pack}" title="SYNTHETIC BUDGET" locator="thermal">\n{html.escape(value,quote=False)}\n</SOURCE>'
                        base=len(tokenizer.tokenize(block(EN),add_special=False));text=EN+' pad'*(cap-base)
                        assert len(tokenizer.tokenize(block(text),add_special=False))==cap
                    derived=[dict(chunk_id=target,purpose='generator',language='en',text=text,text_sha256=sha(text.encode()),
                        derivation_method='official_translation',derivation_source='SYNTHETIC protocol label, not an actual official translation',reviewer_id=None,reviewed_at=None)]
                spec=dict(id=name,rows=rows,preconflict_order=order,edges=edges,derived=derived,
                    expected_pool=expected_pool,expected_admission=expected,expected_selected=expected_selected)
                # Persist independent decisions before calling product retrieval.
                specifications.append(spec);independent.append(dict(id=name,oracle='SQL_BM25_AND_ACTUAL_KDX_DOT_PRODUCTS_NO_RETRIEVER',ranks=rank_rows))
                save(run/'fixed-expectations.json',specifications);save(run/'independent-ranks.json',independent)
                with closing(sqlite3.connect(db_path)) as db,db:
                    if edges:
                        db.execute("UPDATE sources SET jurisdiction='MA',authority_rank=1,legal_status='active',canonical_uri='https://example.invalid/synthetic-selection'")
                    for edge in edges:db.execute('INSERT INTO relations VALUES(?,?,?,?,?)',edge)
                    for row in derived:
                        # Language metadata does not change canonical text or actual
                        # Granite input. Manual mandatory control changes all of its
                        # source's language; every chunk therefore needs a rendering.
                        if kind=='oversize':
                            db.execute("UPDATE sources SET language='fr'")
                            for chunk_id in ids:
                                value=row if chunk_id==row['chunk_id'] else {**row,'chunk_id':chunk_id,'text':rows[ids.index(chunk_id)]['text'],'text_sha256':sha(rows[ids.index(chunk_id)]['text'].encode())}
                                db.execute('INSERT INTO derived_texts VALUES(?,?,?,?,?,?,?,?,?)',tuple(value[key] for key in ('chunk_id','purpose','language','text','text_sha256','derivation_method','derivation_source','reviewer_id','reviewed_at')))
                        else:
                            db.execute("UPDATE sources SET language='fr' WHERE source_id=(SELECT source_id FROM chunks WHERE chunk_id=?)",(row['chunk_id'],))
                            db.execute('INSERT INTO derived_texts VALUES(?,?,?,?,?,?,?,?,?)',tuple(row[key] for key in ('chunk_id','purpose','language','text','text_sha256','derivation_method','derivation_source','reviewer_id','reviewed_at')))
                manifest['domain']='law' if edges else 'repair';manifest['jurisdictions']=['MA'] if edges else []
                manifest['languages']=['en','fr'] if derived else ['en'];manifest['counts']['relations']=len(edges)
                manifest['build']['source_manifest_sha256']=sha(canonical(spec));manifest['build']['builder_version']='1.3.0-selection-test'
                path=run/(name+'-selection.kpack');write_archive(path,manifest,{'knowledge.sqlite':db_path.read_bytes(),'dense.kdx':dense},signer)
                records.append(dict(id=name,filename=path.name,sha256=file_sha(path),transport_frame_sha256=file_sha(draft)))
                inputs.extend(dict(pack=name,chunk_id=key,input=document_input(row['title'],row['locator'],'',row['text'])) for key,row in zip(ids,rows,strict=True))
                with VerifiedPack(path,[public],developer_mode=True) as pack:
                    query=Query(QUESTION,'2026-10-09','MA' if edges else None)
                    candidates,ambiguous=retrieve((pack,),query,vector)
                    observed=dict(id=name,ambiguous=ambiguous,pool=[item.chunk['chunk_id'] for item in candidates],admission=None,selected=[])
                    save(run/(name+'-retrieval-observed.json'),observed)
                    assert not ambiguous and observed['pool']==expected_pool,name
                    try:
                        prompt=prepare(query,(pack.identity,),candidates,tokenizer)
                        observed.update(admission='READY',selected=[item.chunk['chunk_id'] for item in prompt.evidence],tokens=list(prompt.tokens),
                            prefill_tokens=prompt.prefill_tokens,evidence_tokens=prompt.evidence_tokens,max_new=prompt.max_new_tokens,
                            representations=[asdict(v) for v in prompt.representations])
                    except RuntimeContractError as error:observed['admission']=str(error)
                    save(run/(name+'-tokenizer-observed.json'),observed)
                    assert observed['admission']==expected and observed['selected']==expected_selected,name
                    if kind=='boundary1200':assert observed['evidence_tokens']==1200
                    reverse=prepare(query,(pack.identity,),list(reversed(candidates)),tokenizer) if expected=='READY' else None
                    if reverse:assert reverse.tokens==prompt.tokens and reverse.selection==prompt.selection
                    cases.append(dict(id=name,raw=QUESTION,normalized=query.normalized,as_of=query.as_of,jurisdiction=query.jurisdiction,
                        query_vector=vector.tolist(),expected_pool=expected_pool,expected_admission=expected,expected_selected=expected_selected,actual_tokenizer=observed))
            save(run/'embedding-inputs.json',inputs)
            record=dict(status='SIGNED_SYNTHETIC_SELECTION_CONTROLS_NOT_RELEASE_OR_DEVICE_ACCEPTANCE',script_sha256=file_sha(Path(__file__)),
                builder_sha256=file_sha(ROOT/'scripts/v13_query_identifier_fixtures.py'),fixed_contract_sha256=file_sha(fixed),
                fixed_expectations_sha256=file_sha(run/'fixed-expectations.json'),independent_ranks_sha256=file_sha(run/'independent-ranks.json'),
                embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),public_key_sha256=file_sha(run/'public-key.raw'),packs=records,cases=cases,
                private_seed='EPHEMERAL_NEVER_SAVED',runtime_weight_inference=False,content='SYNTHETIC_TEST_ONLY_NOT_OWNER_FINAL_PACKS')
            save(run/'cases.json',record)
            assets.mkdir()
            for path in [run/'cases.json',run/'public-key.raw',fixed,*[run/row['filename'] for row in records]]:shutil.copyfile(path,assets/path.name)
            status='PASS';print('Eight signed selection controls PASS; no owner final content',flush=True)
        except Exception:
            (run/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
        finally:save(run/'fixture-status.json',dict(status=status,packs_created=len(records),cases_checked=len(cases),no_private_seed_saved=True))


if __name__=='__main__':main()
