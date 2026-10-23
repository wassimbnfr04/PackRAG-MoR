"""Generate complete paragraph-level requirements traceability and preserve prior evidence."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / 'artifacts/v1.3/architecture'
OUT = ROOT / 'artifacts/v1.3/m0'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def planned(section):
    major = section.split('.')[0]
    modules = {
        '7': ('product/packrag/generation', 'product/tests/test_generation.py', 'M1'),
        '8': ('product/packrag/kpack', 'product/tests/test_kpack_security.py', 'M3'),
        '9': ('product/packrag/kpack/schema.sql', 'product/tests/test_database.py', 'M3'),
        '10': ('product/packrag/kpack/kdx.py', 'product/tests/test_kdx.py', 'M1'),
        '11': ('product/packrag/embedding', 'product/tests/test_embedding.py', 'M1'),
        '12': ('product/packrag/builder', 'product/tests/test_builder.py', 'M5'),
        '13': ('product/packrag/retrieval', 'product/tests/test_retrieval.py', 'M1'),
        '14': ('product/packrag/retrieval/eligibility.py', 'product/tests/test_eligibility.py', 'M4'),
        '15': ('product/packrag/orchestration', 'product/tests/test_e2e.py', 'M1'),
        '16': ('product/android', 'product/android/benchmark', 'M2'),
        '17': ('product/packrag/registry; product/android/kpack-registry', 'product/tests/test_registry.py', 'M3'),
        '18': ('product/packrag/cli', 'product/tests/test_cli.py', 'M4'),
        '19': ('product/android/generator-lfm25-llamacpp', 'product/android/benchmark', 'M2'),
        '20': ('reference/mor (research only)', 'benchmarks/research', 'OPTIONAL_RESEARCH'),
        '21': ('product/packs', 'product/tests/test_demo_packs.py', 'M5/M6'),
        '22': ('product/benchmarks', 'product/tests/test_packbench.py', 'M7'),
        '23': ('product/packrag/kpack; product/android/kpack-security', 'product/tests/test_kpack_security.py', 'M3'),
        '24': ('product/benchmarks/resource', 'product/android/benchmark', 'M8'),
        '25': ('product; docs/v1.3', 'product/tests/test_contracts.py', 'M0'),
        '26': ('product/tests; product/android/benchmark', 'product/tests; product/android/benchmark', 'M1–M8'),
        '27': ('PLAN.md; STATUS.md', 'scripts/v13_milestone.py', 'M0–M8'),
        '28': ('docs/v1.3/risks.md', 'product/benchmarks', 'M8'),
        '29': ('docs/FINAL_IMPLEMENTATION_REPORT.md', 'product/tests; product/android/benchmark', 'M8'),
        '30': ('research only', 'future ADR', 'OPTIONAL_RESEARCH'),
    }
    if section.startswith('Appendix'):
        return ('product/config; product/packrag; docs/adr', 'product/tests/test_contracts.py', 'M0–M8')
    return modules.get(major, ('product; docs/v1.3', 'product/tests/test_contracts.py', 'M0–M8'))


def main():
    paragraphs = json.loads((ARCH/'paragraphs.json').read_text(encoding='utf-8'))
    assert len(paragraphs) == 1071
    section = 'Document control'
    requirements = []
    explicit = []
    schemas = []
    for paragraph in paragraphs:
        text = paragraph['text']
        heading = re.match(r'^(\d+(?:\.\d+)*)\.?\s+[A-Z][^\n]+$', text)
        if heading:
            section = heading.group(1)
        elif text.startswith('Appendix '):
            section = text.split(' — ')[0]
        words = bool(re.search(r'\b(?:MUST(?: NOT)?|SHOULD(?: NOT)?|MAY)\b', text))
        frozen = 'FROZEN DECISION' in text or 'frozen' in text.lower()
        mandatory = text.startswith('•') and section not in ('3.2', '3.3', '3.4', '3.5', '30')
        contract_block = '\n' in text and section.split('.')[0] in {str(i) for i in range(7,20)}
        normative = words or frozen or mandatory or paragraph['in_table'] or contract_block or text.startswith(('FR-', 'NFR-'))
        if 'CREATE TABLE' in text or 'CREATE VIRTUAL TABLE' in text or 'CREATE INDEX' in text:
            schemas.append(dict(paragraph=paragraph['index'], section=section, text=text))
        if normative:
            module, test, milestone = planned(section)
            identifier = 'V13-P' + str(paragraph['index']).zfill(4)
            row = dict(id=identifier, paragraph=paragraph['index'], section=section, requirement=text,
                       normative_basis='explicit modal' if words else 'table/schema/frozen value' if paragraph['in_table'] or frozen else 'mandatory-section clause',
                       planned_module=module, planned_test=test, milestone=milestone,
                       status='OPTIONAL_RESEARCH' if milestone=='OPTIONAL_RESEARCH' else 'NOT_STARTED', evidence=[])
            requirements.append(row)
            if words:
                explicit.append(identifier)
    OUT.mkdir(parents=True, exist_ok=True)
    record=dict(architecture_sha256=digest(ARCH/'architecture-v1.3.docx'), total_paragraphs=len(paragraphs),
                extraction_policy='Every explicit normative-modal paragraph, mandatory bullet, frozen decision and table cell is mapped. Table labels/type/rules are supporting requirements sharing their architecture section; normative sections govern stale pseudocode names.',
                explicit_modal_ids=explicit, requirements=requirements, schemas=schemas)
    (ARCH/'requirements.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    text=['# v1.3 architecture compliance matrix\n',
          'Source: `artifacts/v1.3/architecture/architecture-v1.3.docx`, SHA256 `'+record['architecture_sha256']+'`. All 1,071 body paragraphs were read/extracted in order, including tables and code. Paragraph IDs are stable against this source hash.\n',
          'Status vocabulary: NOT_STARTED, IMPLEMENTING, IMPLEMENTED, VERIFIED, BLOCKED, OPTIONAL_RESEARCH. Writing code is not verification. This matrix is initialized conservatively; prior experiments are historical evidence, not automatic completion of the new product.\n',
          'The machine-readable `requirements.json` contains complete unabridged requirement text and exact schemas. Cells below escape line breaks for review; no requirement text is omitted. Detailed plan/acceptance: PLAN.md. Current results: STATUS.md.\n',
          '| Requirement ID | Architecture section | Requirement / supporting frozen value | Planned module | Planned test | Milestone | Status | Evidence |\n|---|---|---|---|---|---|---|---|\n']
    for r in requirements:
        clause=r['requirement'].replace('|','\\|').replace('\n','<br>')
        text.append(f"| {r['id']} | {r['section']} / paragraph {r['paragraph']} | {clause} | {r['planned_module']} | {r['planned_test']} | {r['milestone']} | {r['status']} | Pending |\n")
    docs=ROOT/'docs';docs.mkdir(exist_ok=True)
    (docs/'architecture-compliance-matrix.md').write_text(''.join(text),encoding='utf-8')
    historical=json.loads((ROOT/'artifacts/full-documentation-2026-10-04/implementation_history.json').read_text(encoding='utf-8'))['protected_evidence_hashes']
    historical['FULL DOCUMENTATION.md']='7c68e26003dc2debfbe4de9ce79467953fec5268c59947b93b2f2c01d612dbca'
    historical['PackRAG_FULL_IMPLEMENTATION_2026-10-04.zip']='7108a4e9a18658aa9684996efc0e675477ad0c810dff9948e16fcb04a4b7398f'
    for name, expected in historical.items():
        assert digest(ROOT/name)==expected, 'Historical identity changed: '+name
    (OUT/'historical-evidence-guard.json').write_text(json.dumps(dict(role='IMMUTABLE_HISTORY_BASELINE',files=historical),indent=2)+'\n',encoding='utf-8')
    result=dict(architecture_paragraphs=1071, matrix_requirements=len(requirements), explicit_modal_paragraphs=len(explicit),
                schema_blocks=len(schemas), protected_historical_identities=len(historical), history_unchanged=True)
    (OUT/'architecture-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
