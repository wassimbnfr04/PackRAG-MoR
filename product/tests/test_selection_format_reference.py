"""Binds the explicitly post-observation format control; not held-out accuracy."""
import json
from pathlib import Path
import numpy as np
from product.packrag.config import file_sha
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query,retrieve
from product.tests.test_conflict_integration import ControlledGenerator

ROOT=Path(__file__).resolve().parents[2]
CORPUS=ROOT/'artifacts/v1.3/m4/selection-fixtures-0002'
REFERENCE=ROOT/'artifacts/v1.3/m4/selection-format-reference-0001/case.json'


def test_format_control_reference_is_explicit_and_original_failure_is_preserved():
    case=json.loads(REFERENCE.read_text())
    assert case['scope']=='POST_OBSERVATION_FORMAT_CONTROL_NOT_HELDOUT_GOLD'
    assert case['script_sha256']==file_sha(ROOT/'scripts/v13_selection_format_reference.py')
    assert case['diagnostic_sha256']==file_sha(ROOT/'artifacts/v1.3/m4/selection-output-diagnostic-0001/observed.json')
    assert case['original_corpus_sha256']==file_sha(CORPUS/'cases.json')
    assert REFERENCE.read_bytes()==(ROOT/'product/android/app/src/androidTest/assets/selection-corpus/format-control.json').read_bytes()
    original=json.loads((ROOT/'artifacts/v1.3/m4/selection-smoke-0001/atomic-last-runtime-observed.json').read_text())
    assert original['expected_state']=='ANSWER_ACCEPTED' and original['result']['state']=='OUTPUT_REJECTED'
    assert original['result']['rejection_reason']=='uncited_paragraph'


def test_format_control_keeps_signed_selection_and_frozen_origin_context():
    case=json.loads(REFERENCE.read_text());corpus=json.loads((CORPUS/'cases.json').read_text())
    record=next(row for row in corpus['packs'] if row['id']=='atomic-last')
    assert case['pack_sha256']==file_sha(CORPUS/record['filename'])
    with VerifiedPack(CORPUS/record['filename'],[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True) as pack:
        query=Query(case['raw'],case['as_of'],case['jurisdiction'])
        candidates,ambiguous=retrieve((pack,),query,np.asarray(case['query_vector'],dtype=np.float32))
        assert not ambiguous and [item.chunk['chunk_id'] for item in candidates]==case['expected_pool']
        prepared=prepare(query,(pack.identity,),candidates,ControlledGenerator())
        assert [item.chunk['chunk_id'] for item in prepared.evidence]==case['expected_selected']
        assert [item.final_rank for item in prepared.evidence]==[1,2,3,5]
        assert all(item.origin_records[0].identity==pack.identity for item in prepared.evidence)
