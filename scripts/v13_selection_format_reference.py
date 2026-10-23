"""Post-observation formatting-control reference; not independent held-out gold."""
from dataclasses import asdict
import json
import shutil

import numpy as np
from product.packrag.config import file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import prepare
from product.packrag.retrieval import Query,retrieve
from scripts.v13_selection_smoke import CORPUS
from scripts.v13_smoke import ROOT,owned_server,save


def main():
    run=ROOT/'artifacts/v1.3/m4/selection-format-reference-0001';run.mkdir(exist_ok=False)
    original=json.loads((CORPUS/'cases.json').read_text())
    base=next(row for row in original['cases'] if row['id']=='atomic-last')
    record=next(row for row in original['packs'] if row['id']=='atomic-last')
    diagnostic=ROOT/'artifacts/v1.3/m4/selection-output-diagnostic-0001/observed.json'
    observation=json.loads(diagnostic.read_text())
    raw=base['raw']+' Answer in one factual paragraph; cite the sources used.'
    case=dict(id='atomic-format-control',raw=raw,as_of=base['as_of'],jurisdiction=base['jurisdiction'],
        expected_pool=base['expected_pool'],expected_selected=base['expected_selected'],expected_admission='READY',
        expected_state='ANSWER_ACCEPTED',scope='POST_OBSERVATION_FORMAT_CONTROL_NOT_HELDOUT_GOLD',
        original_corpus_sha256=file_sha(CORPUS/'cases.json'),diagnostic_sha256=file_sha(diagnostic),
        script_sha256=file_sha(ROOT/'scripts/v13_selection_format_reference.py'),pack_sha256=record['sha256'])
    save(run/'fixed-format-control.json',case)
    query=Query(raw,base['as_of'],base['jurisdiction']);vector=GraniteEncoder(ROOT/'models/v1.3/granite').encode(query.normalized)
    assert np.max(np.abs(vector-np.asarray(observation['query_vector'],dtype=np.float32)))<=1e-4
    with VerifiedPack(CORPUS/record['filename'],[(CORPUS/'public-key.raw').read_bytes()],developer_mode=True) as pack,owned_server(run) as backend:
        candidates,ambiguous=retrieve((pack,),query,vector);assert not ambiguous
        assert [item.chunk['chunk_id'] for item in candidates]==case['expected_pool']
        prompt=prepare(query,(pack.identity,),candidates,backend)
        assert [item.chunk['chunk_id'] for item in prompt.evidence]==case['expected_selected']
        case.update(status='PASS',query_vector=vector.tolist(),normalized=query.normalized,
            actual_tokenizer=dict(tokens=list(prompt.tokens),prefill_tokens=prompt.prefill_tokens,evidence_tokens=prompt.evidence_tokens,
                max_new=prompt.max_new_tokens,selected=[item.chunk['chunk_id'] for item in prompt.evidence],
                representations=[asdict(item) for item in prompt.representations]),selection=asdict(prompt.selection))
        save(run/'case.json',case)
    asset=ROOT/'product/android/app/src/androidTest/assets/selection-corpus/format-control.json'
    assert not asset.exists();shutil.copyfile(run/'case.json',asset)
    print('POST_OBSERVATION_FORMAT_REFERENCE_PASS_NOT_HELDOUT',flush=True)


if __name__=='__main__':main()
