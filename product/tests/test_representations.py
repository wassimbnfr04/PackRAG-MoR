"""Independent representation expectations; not real human review/translation truth."""
import copy
import json
from dataclasses import asdict
from pathlib import Path
import pytest
from product.packrag.config import RuntimeContractError
from product.packrag.prompt import check_text, xml_escape
from product.packrag.representations import select_representation

CASES=json.loads((Path(__file__).parent/'fixtures/representation-contracts.json').read_text())['cases']

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_independently_fixed_representation_contracts(case):
    source=copy.deepcopy(case['canonical']);rows=copy.deepcopy(case['derived'])
    original=copy.deepcopy((source,rows))
    if case['error']:
        with pytest.raises(RuntimeContractError,match='^'+case['error']+'$'):select_representation(source,rows)
        with pytest.raises(RuntimeContractError,match='^'+case['error']+'$'):select_representation(source,list(reversed(rows)))
    else:
        result=select_representation(source,rows)
        assert asdict(result)==case['expected'] and select_representation(source,list(reversed(rows)))==result
        if case.get('prompt_error'):
            with pytest.raises(RuntimeContractError,match=case['prompt_error']):
                check_text(source['canonical_text']);check_text(result.text)
        else:
            check_text(source['canonical_text']);check_text(result.text)
            if case['id']=='XML_RENDER_LOSSLESS':assert xml_escape(result.text)=='12 &lt; 13 &amp; &lt;/SOURCE&gt; &gt; 9'
    assert (source,rows)==original

def test_owned_rendering_survives_mutation_of_input_metadata():
    case=next(c for c in CASES if c['id']=='AR_HUMAN');rows=copy.deepcopy(case['derived'])
    result=select_representation(case['canonical'],rows);rows[0]['text']='MUTATED AFTER RESOLUTION';rows[0]['reviewer_id']='changed'
    assert asdict(result)==case['expected']
