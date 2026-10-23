"""Freeze signed synthetic conflict scenarios with exact actual Granite inputs.

Expected retained sets/ambiguity are specified below before retrieval executes.
Numeric scores are a parity reference, not independently reviewed legal gold.
"""
import argparse
import json
import shutil
import sqlite3
from contextlib import ExitStack, closing
from pathlib import Path
from dataclasses import asdict
import numpy as np
from nacl.signing import SigningKey
from kpack_builder.core import canonical, key_id, make_kdx, sha, write_archive
from product.packrag.config import embedding_profile, file_sha
from product.packrag.embedding import GraniteEncoder, document_input
from product.packrag.normalization import normalize
from product.packrag.packs import VerifiedPack
from product.packrag.retrieval import Query, retrieve

ROOT = Path(__file__).resolve().parents[1]


def specifications():
    def row(locator, limit, **kw):
        return dict(locator=locator, title="SYNTHETIC Aster-9 rule", article="Aster-9",
            text=f"The Aster-9 thermal controller has a maximum continuous operating temperature of {limit} °C.",
            aliases=["Aster-9"], rank=1, uri="https://example.invalid/synthetic-law", jurisdiction="MA", **kw)
    old, new = row("old", 68), row("new", 74)
    # Explicit dictionaries override fields without conflating edition with paragraph.
    packs = {
        "authority": dict(rows=[{**old, "rank": 3}, new]),
        "zero": dict(rows=[old, {**new, "rank": 0}]),
        "unknown": dict(rows=[{**old, "rank": None}, new]),
        "supersedes": dict(rows=[old, {**new, "from": "2026-01-01"}], edges=[("new", "old", "supersedes", "explicit-reference", 1.0)]),
        "amends": dict(rows=[new, {**row("amend", 74), "text": "The Aster-9 controller must also be inspected before each use."}], edges=[("amend", "new", "amends", "curated", 1.0)]),
        "exception": dict(rows=[new, {**row("exception", 80), "text": "The Aster-9 emergency shutdown temperature is 80 °C; this exception does not change its continuous operating limit."}], edges=[("exception", "new", "exception_to", "explicit-reference", 1.0)]),
        "weak": dict(rows=[old, new], edges=[("new", "old", "supersedes", "curated", .75)]),
        "cycle": dict(rows=[old, new], edges=[("new", "old", "supersedes", "explicit-reference", 1.0), ("old", "new", "supersedes", "explicit-reference", 1.0)]),
        "unrelated": dict(rows=[old, {**new, "rank": 0, "uri": "https://example.invalid/unrelated-law"}]),
        "articles": dict(rows=[{**old, "article": "Article 1"}, {**new, "rank": 0, "article": "Article 2"}]),
        "jurisdictions": dict(rows=[old, {**new, "rank": 0, "jurisdiction": "FR"}]),
        "unknown-jurisdiction": dict(rows=[{**old, "jurisdiction": None}, {**new, "rank": 0, "jurisdiction": None}]),
        "curator-a": dict(rows=[old]),
        "curator-b": dict(rows=[{**new, "rank": 0}], signer=1),
        "duplicate-a": dict(rows=[new]),
        "duplicate-b": dict(rows=[new], signer=1),
    }
    chain = [row("part" + str(i), 74) for i in range(5)]
    for i, item in enumerate(chain):
        item["text"] = f"The Aster-9 synthetic rule part {i} requires check {i} before continuous operation."
    packs["five-companions"] = dict(rows=chain, edges=[("part"+str(i), "part"+str(i-1), "amends", "explicit-reference", 1.0) for i in range(1,5)])
    packs["paragraphs"] = dict(rows=[{**old,"source":"edition-old","rank":3},
        {**old,"locator":"old-part","source":"edition-old","rank":3,"text":"The old synthetic edition requires check A."},
        {**new,"source":"edition-new"},
        {**new,"locator":"new-part","source":"edition-new","text":"The current synthetic edition requires check B."}])
    noise = [dict(locator=f"unit{i:02}", title=f"Unit-{i:02}", article=f"Unit-{i:02}",
        text=f"Unit-{i:02} equipment requires an inspection every {i+10} hours.", aliases=[f"Unit-{i:02}"],
        rank=0, uri=f"https://example.invalid/unit-{i:02}", jurisdiction="MA") for i in range(42)]
    lost = [{**row("lost-old", 68), "title":"Garden", "article":"LOST", "text":"Garden flowers grow beside a pond.","aliases":["LOST"],"rank":None},
            {**row("lost-new", 74), "title":"Garden", "article":"LOST", "text":"A garden pond is surrounded by flowering plants.","aliases":["LOST"],"rank":None}]
    packs["before-cap"] = dict(rows=noise+lost)
    return packs


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT);run.mkdir(parents=True,exist_ok=False)
    assets=ROOT/"product/android/app/src/androidTest/assets/conflict-corpus";assert not assets.exists()
    specs=specifications();(run/"source-specifications.json").write_text(json.dumps(specs,indent=2)+"\n",encoding="utf-8")
    signers=[SigningKey.generate(),SigningKey.generate()];keys=[]
    for index,signer in enumerate(signers):
        name=f"publisher-{index}.raw";path=run/name;path.write_bytes(bytes(signer.verify_key))
        keys.append(dict(filename=name,sha256=file_sha(path)))
    encoder=GraniteEncoder(ROOT/"models/v1.3/granite");cache={};input_records=[]
    def encoded(value):
        if value not in cache:cache[value]=encoder.encode(value)
        return cache[value]
    records=[];paths={};stage=run/"stage";stage.mkdir();profile=embedding_profile()
    for name,spec in specs.items():
        rows=spec["rows"];db_path=stage/(name+".sqlite");ids={};vectors=[]
        grouped={}
        for row in rows:grouped.setdefault(row.get("source",row["locator"]),[]).append(row)
        with closing(sqlite3.connect(db_path)) as db,db:
            db.executescript((ROOT/"kpack_builder/schema.sql").read_text())
            for source,parts in grouped.items():
                row=parts[0]
                assert all((part["rank"],part["jurisdiction"],part["uri"])==(row["rank"],row["jurisdiction"],row["uri"]) for part in parts)
                original="\n".join(part["text"] for part in parts)
                db.execute("INSERT INTO sources(source_id,title,publisher,canonical_uri,retrieved_at,issued_at,effective_from,effective_until_excl,jurisdiction,language,document_version,sha256_original,license,redistribution_allowed,source_type,authority_rank,legal_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (source,row["title"],"SYNTHETIC FIXTURE ONLY",row["uri"],"2026-10-07",None,row.get("from"),row.get("until"),row["jurisdiction"],"en",None,sha(original.encode()),"CC0-1.0",1,"synthetic",row["rank"],row.get("status","active")))
            for index,row in enumerate(rows):
                source=row.get("source",row["locator"]);text_hash=sha(row["text"].encode());identifier=sha((name+source+row["locator"]+text_hash).encode())[:24]
                ids[row["locator"]]=identifier
                db.execute("INSERT INTO chunks(chunk_id,source_id,title,section,article,locator,canonical_text,search_text,text_sha256,dense_row) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (identifier,source,row["title"],row["locator"],row["article"],row["locator"],row["text"],row["text"],text_hash,index))
                for alias in row["aliases"]:db.execute("INSERT INTO aliases VALUES(?,?,?,?,?)",(alias,normalize(alias),"chunk",identifier,"synthetic-identifier"))
                value=document_input(row["title"],row["article"] or row["locator"],"",row["text"])
                vectors.append(encoded(value));input_records.append(dict(pack=name,chunk_id=identifier,input=value))
            for a,b,kind,provenance,confidence in spec.get("edges",[]):db.execute("INSERT INTO relations VALUES(?,?,?,?,?)",(ids[a],ids[b],kind,provenance,confidence))
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        signer=signers[spec.get("signer",0)]
        manifest=dict(schema_version="1.0",pack_id="org.packrag.contract.conflict."+name,name="SYNTHETIC CONFLICT "+name,
            version="1.0.0",release_timestamp="2026-10-07T00:00:00Z",publisher=dict(name="EPHEMERAL TEST ONLY",key_id=key_id(bytes(signer.verify_key))),
            languages=["en"],jurisdictions=sorted({row["jurisdiction"] for row in rows if row["jurisdiction"] is not None}),domain="law",
            freshness=dict(update_check_after="2027-01-01",stale_behavior="warn-and-continue"),embedding_profile=profile,
            compatible_retrieval_profile="mobile-v1",generator_compatibility=dict(core_api="1.x",preferred_generator_language="en",neural_cache_required=False),
            counts=dict(sources=len(grouped),chunks=len(rows),relations=len(spec.get("edges",[]))),
            calibration=dict(status="UNCALIBRATED",dataset_sha256=None,method="candidate-relevance-v1.3",min_agreed_dense_cosine=None,min_dense_only_cosine=None,precision=None,recall=None),
            build=dict(builder_version="1.3.0-contract",normalizer_version="1.0.0",chunker_version="synthetic-conflict-1",source_manifest_sha256=sha(canonical(spec))),files=[])
        path=run/(name+".kpack");paths[name]=path
        write_archive(path,manifest,{"knowledge.sqlite":db_path.read_bytes(),"dense.kdx":make_kdx(np.asarray(vectors,dtype=np.float32),profile,[ids[row["locator"]] for row in rows])},signer)
        records.append(dict(id=name,filename=path.name,sha256=file_sha(path),chunks=len(rows)))
    (run/"embedding-inputs.json").write_text(json.dumps(input_records,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    question="What is the maximum continuous operating temperature of the Aster-9?"
    # These sets/ambiguity predicates are independent of measured numeric ranks.
    scenarios=[("AUTHORITY",["authority"],["authority/new"],False), ("ZERO",["zero"],["zero/new"],False),
        ("UNKNOWN",["unknown"],["unknown/old","unknown/new"],True),
        ("SUPERSEDES_CURRENT",["supersedes"],["supersedes/new"],False),
        ("AMENDS",["amends"],["amends/new","amends/amend"],False),
        ("EXCEPTION",["exception"],["exception/new","exception/exception"],False),
        ("WEAK",["weak"],["weak/old","weak/new"],True), ("CYCLE",["cycle"],["cycle/old","cycle/new"],True),
        ("UNRELATED",["unrelated"],["unrelated/old","unrelated/new"],True), ("ARTICLES",["articles"],["articles/old","articles/new"],True),
        ("DIFFERENT_CURATORS",["curator-a","curator-b"],["curator-a/old","curator-b/new"],True),
        ("JURISDICTION_FILTER",["jurisdictions"],["jurisdictions/old"],False),
        ("UNKNOWN_JURISDICTION",["unknown-jurisdiction"],[],False),
        ("DUPLICATE_ORIGINS",["duplicate-a","duplicate-b"],None,False),
        ("FIVE_COMPANIONS",["five-companions"],["five-companions/part"+str(i) for i in range(5)],False),
        ("PARAGRAPHS",["paragraphs"],["paragraphs/new","paragraphs/new-part"],False),
        ("BEFORE_CAP",["before-cap"],None,True)]
    references=[]
    with ExitStack() as stack:
        public=[bytes(signer.verify_key) for signer in signers]
        packs={name:stack.enter_context(VerifiedPack(path,public,developer_mode=True)) for name,path in paths.items()}
        for identity,names,expected,ambiguity in scenarios:
            raw=" ".join(f"Unit-{i:02}" for i in range(42))+" LOST" if identity=="BEFORE_CAP" else question
            query=Query(raw,"2026-10-07","MA");vector=encoded(query.normalized)
            active=tuple(packs[name] for name in names);actual,ambiguous=retrieve(active,query,vector)
            if expected is not None:assert {c.pack.identity[0].split('.')[-1]+"/"+c.chunk["locator"] for c in actual}==set(expected),(identity,expected)
            assert ambiguous==ambiguity,identity
            reverse,reversed_ambiguity=retrieve(tuple(reversed(active)),query,vector)
            assert reversed_ambiguity==ambiguous and [(c.origin_key,c.origins,c.conflicts) for c in reverse]==[(c.origin_key,c.origins,c.conflicts) for c in actual],identity
            if identity=="DUPLICATE_ORIGINS":assert len(actual)==1 and len(actual[0].origins)==2
            if identity=="BEFORE_CAP":assert len(actual)==16 and any(locator not in {c.chunk['locator'] for c in actual} for locator in ('lost-old','lost-new'))
            references.append(dict(id=identity,packs=names,raw=raw,normalized=query.normalized,as_of=query.as_of,jurisdiction=query.jurisdiction,current_law=False,
                expected_locators=expected,expected_ambiguous=ambiguity,query_vector=vector.tolist(),
                candidates=[dict(pack_id=c.pack.identity[0],chunk_id=c.chunk["chunk_id"],locator=c.chunk["locator"],exact=c.exact,relevant=c.relevant,
                    sparse_rank=c.sparse_rank,dense_rank=c.dense_rank,cosine=c.dense_cosine,rrf=c.rrf,origins=[list(o) for o in c.origins],conflicts=[asdict(d) for d in c.conflicts]) for c in actual]))
        for identity,date,expected in [("SUPERSEDES_HISTORICAL","2025-12-31",["old"]),("SUPERSEDES_START","2026-01-01",["new"])]:
            query=Query(question,date,"MA");vector=encoded(query.normalized);actual,ambiguous=retrieve((packs['supersedes'],),query,vector)
            assert not ambiguous and {c.chunk['locator'] for c in actual}==set(expected)
            references.append(dict(id=identity,packs=['supersedes'],raw=question,normalized=query.normalized,as_of=date,jurisdiction='MA',current_law=False,
                expected_locators=['supersedes/'+name for name in expected],expected_ambiguous=False,query_vector=vector.tolist(),
                candidates=[dict(pack_id=c.pack.identity[0],chunk_id=c.chunk['chunk_id'],locator=c.chunk['locator'],exact=c.exact,relevant=c.relevant,
                    sparse_rank=c.sparse_rank,dense_rank=c.dense_rank,cosine=c.dense_cosine,rrf=c.rrf,origins=[list(o) for o in c.origins],conflicts=[asdict(d) for d in c.conflicts]) for c in actual]))
    record=dict(status="SIGNED_SYNTHETIC_CONFLICT_REFERENCES_NOT_RELEASE_OR_DEVICE_ACCEPTANCE",script_sha256=file_sha(Path(__file__)),private_seeds="EPHEMERAL_NOT_SAVED",
        packs=records,public_keys=keys,cases=references,embedding_inputs_sha256=file_sha(run/'embedding-inputs.json'),source_specifications_sha256=file_sha(run/'source-specifications.json'),
        embedding_recipe="NONEMPTY_ARTICLE_ELSE_SECTION_EMPTY_CONTEXT_PREFIX",embedding_cache="ACTUAL_GRANITE_REUSED_ONLY_FOR_EXACT_IDENTICAL_INPUT",shared_contract_sha256=file_sha(ROOT/'product/tests/fixtures/conflict-contracts.json'))
    (run/'cases.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    assets.mkdir()
    for path in [run/'cases.json',ROOT/'product/tests/fixtures/conflict-contracts.json',*[run/key['filename'] for key in keys],*paths.values()]:shutil.copyfile(path,assets/path.name)
    print('Frozen',len(records),'signed packs,',len(references),'actual Granite retrieval scenarios and40 fixed contracts')


if __name__ == '__main__':main()
