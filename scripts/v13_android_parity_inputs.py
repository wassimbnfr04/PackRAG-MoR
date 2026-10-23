"""Freeze actual desktop tokenizer/embedding/retrieval/prompt references for M2."""
import argparse
import json
from pathlib import Path

from product.packrag.config import LOCK, file_sha
from product.packrag.embedding import GraniteEncoder
from product.packrag.packs import VerifiedPack
from product.packrag.prompt import SYSTEM, prepare, user_message
from product.packrag.retrieval import Query, retrieve
from scripts.v13_smoke import ROOT, owned_server, save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    run.mkdir(parents=True, exist_ok=False)
    fixture = ROOT / "artifacts/v1.3/m1/smoke-0001/developer-pack"
    records = [json.loads(line) for line in (ROOT / "gates/g0/g0_v1.jsonl").read_text(encoding="utf-8").splitlines()][:10]
    unicode_cases = ["", " a  b\t c\n\n", "ABCDef don't I'll WE'RE café", "é e\u0301 1234567890",
                     "👩🏽‍🔧 إصلاح، عملٌ ١٢٣", "\u200b\u200d text", "你好 世界", "\r\n / !?!",
                     "<|startoftext|>literal<|return|>", "<|reserved_200020|>",
                     "x<|reserved_200020|>x", "ＦＵＬＬＷＩＤＴＨ Aster-9", "Straße İ Σ σ ς",
                     "ما هي ساعات العمل؟", "ch7al sa3a dyal lkhedma", "Quelle est la durée du congé annuel ?"]
    texts = [case["question"] for case in records] + [case["evidence"][0]["text"] for case in records] + unicode_cases
    encoder = GraniteEncoder(ROOT / "models/v1.3/granite")
    token_cases = [dict(id=f"TOKEN-{index:03}", text=text,
                        ids=encoder.tokenizer.encode(text, add_special_tokens=True).ids)
                   for index, text in enumerate(texts)]
    embedding_cases = [dict(text=text, vector=encoder.encode(text).tolist())
                       for text in (texts[0], unicode_cases[-3], unicode_cases[-2], unicode_cases[-1])]
    prompt_cases = []
    with owned_server(run) as generator:
        with VerifiedPack(fixture / "walking-skeleton.kpack", [(fixture / "developer-public-key.raw").read_bytes()], developer_mode=True) as pack:
            for record in records:
                query = Query(record["question"], "2026-10-05")
                candidates, ambiguous = retrieve((pack,), query, encoder.encode(query.raw))
                assert not ambiguous
                prompt = prepare(query, (pack.identity,), candidates, generator)
                prompt_cases.append(dict(id=record["case_id"], query=query.raw, as_of=query.as_of,
                                         system=SYSTEM, user=user_message(query, (pack.identity,), list(prompt.evidence)),
                                         tokens=list(prompt.tokens), prefill=prompt.prefill_tokens, evidence_tokens=prompt.evidence_tokens,
                                         max_new=prompt.max_new_tokens,
                                         selected=[item.chunk["chunk_id"] for item in prompt.evidence],
                                         candidate_order=[item.chunk["chunk_id"] for item in candidates],
                                         sparse_ranks=[item.sparse_rank for item in candidates],
                                         dense_ranks=[item.dense_rank for item in candidates],
                                         rrf=[item.rrf for item in candidates],
                                         dense_cosines=[item.dense_cosine for item in candidates]))
    save(run / "parity-reference.json", dict(
        status="DESKTOP_REFERENCES_FROZEN_NOT_ANDROID_ACCEPTANCE", purpose="M2_NUMERIC_AND_INTERFACE_PARITY",
        lock=LOCK, developer_pack_sha256=file_sha(fixture / "walking-skeleton.kpack"),
        generator_prompt_contract="hash-pinned official one-turn template, one BOS, assistant think prefill",
        tokenizer_cases=token_cases, embedding_cases=embedding_cases, prompt_cases=prompt_cases,
        tolerances=dict(embedding_max_abs_error=1e-4, embedding_min_cosine=.99999, dense_cosine_max_abs_error=1e-4),
        not_a_claim="These are desktop references; phone parity, generation and language retrieval acceptance require separate executions.",
    ))
    save(run / "output-hashes.json", {path.name:file_sha(path) for path in run.iterdir() if path.is_file()})
    print("Frozen", len(token_cases), "tokenizer cases,", len(embedding_cases), "embeddings,", len(prompt_cases), "retrieval/prompts.", flush=True)


if __name__ == "__main__":
    main()
