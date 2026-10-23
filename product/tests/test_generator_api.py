"""Generator boundary/diagnostic contracts; actual inference remains a separate gate."""
from pathlib import Path
import threading
from types import SimpleNamespace
import pytest
from product.packrag.config import RuntimeContractError
from product.packrag.output import validate_output
from product.packrag.generator_api import Generated, GeneratorBackend
from product.packrag.generator import LlamaBackend, Generated as LegacyImport

ROOT=Path(__file__).resolve().parents[2]

def test_raw_reasoning_is_not_exposed_by_result_diagnostics():
    emitted=Generated('<think>PRIVATE_REASONING_SENTINEL</think>final',False,(1,2),{'emitted':2})
    assert 'SENTINEL' not in repr(emitted) and 'final' not in repr(emitted)
    assert LegacyImport is Generated  # Preserve the prior desktop import boundary.

def test_concrete_backend_satisfies_portable_contract_without_model_loading():
    # Structural conformance only; do not call a method on this uninitialized object.
    backend=object.__new__(LlamaBackend); backend.metadata={}
    assert isinstance(backend,GeneratorBackend)
    assert not isinstance(object(),GeneratorBackend)

def test_grounded_runtime_depends_on_generator_api_not_native_backend():
    gradle=(ROOT/'product/android/grounded-runtime/build.gradle.kts').read_text()
    assert 'project(":generator-api")' in gradle and 'project(":generator-llama")' not in gradle
    source=(ROOT/'product/android/grounded-runtime/src/main/java/org/packrag/runtime/PackRag.kt').read_text()
    assert 'private val generator: GeneratorBackend' in source
    assert 'LlamaGenerator' not in source and 'NativeEmission' not in source

@pytest.mark.parametrize('stop,input_truncated,expected',[
    ('limit',False,'GENERATION_UNUSABLE'),
    ('eos',False,'ANSWER_ACCEPTED'),
    ('eos',True,'GENERATION_UNUSABLE'),
])
def test_actual_server_stop_semantics_reject_even_a_cited_partial_final(stop,input_truncated,expected):
    backend=object.__new__(LlamaBackend);backend._mutex=threading.Lock()
    backend.request=lambda endpoint,body:dict(content='private</think>Disconnect it [S1].',tokens=[1,7,2],
        timings={},stop_type=stop,truncated=input_truncated)
    backend.tokenize=lambda text,add_special:[7]
    emitted=backend.generate(SimpleNamespace(tokens=(1,),max_new_tokens=512))
    assert emitted.timings['stop_type']==stop
    assert validate_output(emitted.buffer,{'S1'},truncated=emitted.truncated).state==expected

@pytest.mark.parametrize('stop',[None,'word','unknown'])
def test_absent_or_unexpected_stop_metadata_cannot_admit_an_answer(stop):
    backend=object.__new__(LlamaBackend);backend._mutex=threading.Lock()
    backend.request=lambda endpoint,body:dict(content='private</think>Fact [S1].',tokens=[1,7,2],timings={},stop_type=stop)
    with pytest.raises(RuntimeContractError,match='GENERATION_UNUSABLE'):
        backend.generate(SimpleNamespace(tokens=(1,),max_new_tokens=512))
