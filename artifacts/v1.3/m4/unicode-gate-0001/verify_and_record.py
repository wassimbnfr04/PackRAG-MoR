"""Fail-closed closure of this bounded Unicode increment, not complete M4."""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
M4 = ROOT / "artifacts/v1.3/m4"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_inputs(values):
    for name, expected in values.items():
        assert digest(ROOT / name) == expected, name


COMMON = ["m4-query-unicode.json", "m2-generator-prompt-parity.json", "m2-pack-retrieval-parity.json",
          "m3-data-types.json", "m3-extension-names.json", "m3-validation-order.json",
          "m3-residual-security.json", "m3-manifest-schema.json", "m3-database-validation.json",
          "m3-archive-validation.json"]
PHONE = {
    "device-query-unicode-0001": ("build-0003", 16, COMMON + ["m2-generator-cancellation.json",
        "product-runtime-smoke.json", "m3-explicit-lifecycle.json", "m3-atomic-registry.json",
        "m3-process-death.json", "m3-import-consent.json"]),
    "device-production-query-unicode-0001": ("build-0004", 12, COMMON + [
        "m3-production-policy.json", "m3-release-trust-core.json"]),
    "device-development-restore-0002": ("build-0003", 1, ["m3-import-consent.json"]),
}


def main():
    target = HERE / "gate.json"
    assert not target.exists(), "Gate outputs are immutable"
    python = read(M4 / "run-0002/result-manifest.json")
    assert python["status"] == "PASS" and python["totals"] == dict(tests=501, failures=0, errors=0, skipped=0)
    # Durable live state is deliberately updated as acceptance proceeds.
    runtime = {k: v for k, v in python["source_sha256"].items() if k not in ("PLAN.md", "STATUS.md", "DECISIONS.md")}
    check_inputs(runtime)
    desktop = read(M4 / "smoke-0002/smoke-results.json")
    assert desktop["status"] == "PASS" and len(desktop["cases"]) == 14
    desktop_inputs = read(M4 / "smoke-0002/inputs.json")["source_sha256"]
    check_inputs(desktop_inputs)
    assert runtime == desktop_inputs
    historical = read(ROOT / "artifacts/v1.3/m0/historical-evidence-guard.json")["files"]
    check_inputs(historical)
    builds, apk_hashes = {}, {}
    native_hash = "361d22ac049f28f48b454c283509d47e6c241405d0cabc7054b59c5cc59d91ef"
    for name, variant in [("build-0003", "debug"), ("build-0004", "demo")]:
        build = M4 / name
        assert read(build / "build-result.json")["exit_code"] == 0
        assert read(build / "host-test-summary.json")["test_methods"] == 21
        xmls = list((build / "host-tests").rglob("TEST-*.xml")); assert xmls
        for path in xmls:
            suite = ET.parse(path).getroot()
            assert int(suite.attrib.get("failures", 0)) == int(suite.attrib.get("errors", 0)) == 0
        inputs = read(build / "source-at-build-start.json")["files"]
        check_inputs(inputs); builds[name] = inputs
        apk = build / f"app-{variant}.apk"
        with zipfile.ZipFile(apk) as archive:
            assert hashlib.sha256(archive.read("lib/arm64-v8a/libpackrag_jni.so")).hexdigest() == native_hash
        apk_hashes[name] = {p.name: digest(p) for p in build.glob("*.apk")}
    assert builds["build-0003"] == builds["build-0004"]
    phone = {}
    for run_name, (build_name, count, names) in PHONE.items():
        run = M4 / run_name
        manifest = read(run / "instrumentation-manifest.json")
        assert manifest["status"] == "PASS" and manifest["apk_sha256"] == apk_hashes[build_name]
        text = (run / "instrumentation.txt").read_text(encoding="utf-8")
        noun = "test" if count == 1 else "tests"
        assert f"OK ({count} {noun})" in text and "FAILURES" not in text
        match = re.search(r"Time:\s*([0-9]+[.,][0-9]+)", text); assert match
        for name in names:
            assert read(run / name)["status"] == "PASS", (run_name, name)
        if "m4-query-unicode.json" in names:
            result = read(run / "m4-query-unicode.json")
            assert result["official_rows"] == 19074 and result["official_comparisons"] == 95370
            assert len(result["query_cases"]) == 1453
            assert result["table_sha256"] == digest(ROOT / "product/config/query-unicode15.json")
        phone[run_name] = dict(methods=count, whole_instrumentation_seconds=float(match[1].replace(",", ".")),
                               saved_results=names, apk_sha256=manifest["apk_sha256"])
    assert read(M4 / "demo-apk-inspection-0003/inspection.json")["status"] == "PASS"
    official_hash = read(M4 / "unicode15-inputs-0001/acquisition.json")["files"]["NormalizationTest.txt"]["sha256"]
    corpus_files = ["product/tests/unicode15/NormalizationTest.txt",
                    "product/android/app/src/androidTest/assets/unicode15/NormalizationTest.txt"]
    for name in corpus_files:
        assert digest(ROOT / name) == official_hash, name
    for build_name, variant in [("build-0003", "debug"), ("build-0004", "demo")]:
        with zipfile.ZipFile(M4 / build_name / f"app-{variant}-androidTest.apk") as archive:
            assert hashlib.sha256(archive.read("assets/unicode15/NormalizationTest.txt")).hexdigest() == official_hash
    if "--check-only" in sys.argv:
        print("ALL_B1_ACCEPTANCE_CHECKS_PASS_NO_CLOSURE_RECORD_WRITTEN")
        return
    roots = [M4 / name for name in ["run-0002", "smoke-0002", "build-0003", "build-0004",
        "demo-apk-inspection-0002", "demo-apk-inspection-0003", "query-audit-0001",
        "query-audit-0002", "unicode15-inputs-0001", *PHONE]]
    blocked = {"temp", "pytest-temp", "__pycache__", ".private", "build", ".gradle", ".cxx", ".kotlin"}
    outputs = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT)
            if blocked.intersection(relative.parts) or path.suffix in (".apk", ".pyc", ".class"):
                continue
            assert path.resolve().is_relative_to(ROOT), relative
            if path.is_file():
                outputs[relative.as_posix()] = digest(path)
    documents = ["PLAN.md", "STATUS.md", "DECISIONS.md", "docs/v1.3/M4_INCREMENT_PLAN.md",
        "docs/v1.3/M4_IMPLEMENTATION_LOG.md", "docs/v1.3/M4B1_UNICODE_METHODS.md", "docs/v1.3/M4B2_PREPARATION.md",
        "product/licenses/Unicode15-LICENSE.txt", "product/licenses/Unicode15-NOTICE.md"]
    documents_at_closure = {}
    for name in documents:
        source = ROOT / name
        snapshot = HERE / "state-snapshot" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        assert not snapshot.exists(), snapshot
        snapshot.write_bytes(source.read_bytes())
        documents_at_closure[name] = digest(source)
        outputs[snapshot.relative_to(ROOT).as_posix()] = digest(snapshot)
    for name in corpus_files:
        outputs[name] = digest(ROOT / name)
    outputs[Path(__file__).relative_to(ROOT).as_posix()] = digest(Path(__file__))
    record = dict(status="M4B1_UNICODE_VERIFIED_NOT_FULL_B_OR_M4_PRODUCT_COMPLETE",
        recorded_utc=datetime.now(timezone.utc).isoformat(), python_tests=501, host_methods_per_variant=21,
        official_rows_per_platform=19074, official_comparisons_per_platform=95370, shared_query_cases=1453,
        scalar_reference_comparisons=1112064, historical_identities_unchanged=len(historical),
        unchanged_public_runtime_inputs=len(runtime), frozen_android_inputs_per_variant=len(builds["build-0003"]),
        unicode_table_sha256=digest(ROOT / "product/config/query-unicode15.json"), native_jni_sha256=native_hash,
        apk_sha256=apk_hashes, phone=phone, source_sha256=runtime, android_source_sha256=builds,
        output_sha256=outputs, documents_at_closure=documents_at_closure,
        limits=["Generated/exhaustive scalar checks share Python15 oracle; official corpus is independent",
        "One OS-normalizer probe is not an exhaustive OS audit or old-APK execution",
        "Live durable-state hashes record closure time; future authorized state updates are expected",
        "Instrumentable demo is Android Debug signed, not final nondebuggable release",
        "Synthetic functional data is not release calibration, held-out accuracy or source/translation review",
        "Intermediate memory/thermal snapshot and functional timings do not establish performance or causal bottleneck",
        "Mobile data remains on; no airplane isolation acceptance; B2 and M4C–F/M5–M8 incomplete"])
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["status", "phone", "unchanged_public_runtime_inputs", "frozen_android_inputs_per_variant"]}, indent=2))


if __name__ == "__main__":
    main()
