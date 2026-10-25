"""Isolated evidence-consumer probes; no compiler, EVM, network or source edits."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests_python.test_function_reference import FunctionReferenceTests
from zzz_ops.function_reference import build_reference, import_compiler, load_json

HERE = Path(__file__).resolve().parent
OUT = Path(r"C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/day-readiness-20261025/evidence-probes-initial")


def sha(raw): return hashlib.sha256(raw).hexdigest()


def update(case, mutate, hash_override=None):
    supplied, compiled, sizes = [load_json(path) for path in case.paths]
    mutate(supplied, compiled, sizes)
    for path, value in zip(case.paths[:2], (supplied, compiled)):
        path.write_text(json.dumps(value), encoding="utf-8")
    sizes["compiler_input_sha256"] = sha(case.paths[0].read_bytes())
    sizes["compiler_output_sha256"] = sha(case.paths[1].read_bytes())
    if hash_override:
        sizes.update(hash_override)
    case.paths[2].write_text(json.dumps(sizes), encoding="utf-8")


def oversized(case, kind, amount):
    def mutate(supplied, compiled, sizes):
        item = compiled["contracts"]["src/Fixture.sol"]["Fixture"]
        item["evm"]["deployedBytecode" if kind == "runtime" else "bytecode"]["object"] = "00" * amount
        sizes["gates"][0][kind] = amount
        sizes["gates"][0]["runtime_ok" if kind == "runtime" else "creation_ok"] = True
    update(case, mutate)


def run_case(name, change, expected_accept=False, actual_repository=False):
    start = time.monotonic()
    fixture = FunctionReferenceTests("test_canonical_nested_tuple_arrays_and_overloads_are_exact")
    fixture.setUp()
    try:
        if actual_repository:
            base = copy.deepcopy(load_json(ROOT / "docs/function-reference.json"))
            notes = load_json(ROOT / "docs/function-reference-notes.json")
            change(base)
            call = lambda: build_reference(ROOT, base, notes)
        else:
            change(fixture)
            case_dir = OUT / name
            case_dir.mkdir(parents=True, exist_ok=True)
            for path in fixture.paths:
                if path.is_file():
                    (case_dir / path.name).write_bytes(path.read_bytes())
            call = lambda: import_compiler(fixture.root, *fixture.paths)
        try:
            call()
            accepted, error = True, None
        except Exception as exc:
            accepted, error = False, {"type": type(exc).__name__, "message": str(exc)}
        return {"name": name, "expected_accept": expected_accept, "actual_accept": accepted,
                "expectation_met": accepted == expected_accept, "error": error,
                "elapsed_seconds": round(time.monotonic() - start, 4),
                "scope": "Actual stored reference copy; no repository writes" if actual_repository else "Disposable isolated evidence fixture"}
    finally:
        fixture.doCleanups()


def main():
    target = HERE / "evidence-negative-probes-initial.json"
    if target.exists():
        raise ValueError("Preserve initial probe evidence")
    watched = ("zzz_ops/function_reference.py", "tests_python/test_function_reference.py",
               "scripts/generate-function-reference.py", ".github/workflows/verify.yml",
               "scripts/verify.sh", "scripts/source_checks.py", "scripts/check-slither-review.py")
    before = {name: sha((ROOT / name).read_bytes()) for name in watched}
    cases = [
        run_case("valid_control", lambda case: None, expected_accept=True),
        run_case("missing_compiler_output", lambda case: case.paths[1].unlink()),
        run_case("stale_source", lambda case: case.source.write_bytes(case.source.read_bytes() + b"// drift\n")),
        run_case("malformed_boolean_gate", lambda case: update(case, lambda i, o, s: s["gates"][0].update(runtime_ok="false"))),
        run_case("oversize_runtime_truthful_length_false_success", lambda case: oversized(case, "runtime", 24577)),
        run_case("oversize_creation_truthful_length_false_success", lambda case: oversized(case, "creation", 49153)),
        run_case("static_constructor_exceeds_initcode", lambda case: oversized(case, "creation", 49121)),
        run_case("contradictory_declared_input_hash", lambda case: update(case, lambda i, o, s: None, {"compiler_input_sha256": "0" * 64})),
        run_case("contradictory_declared_output_hash", lambda case: update(case, lambda i, o, s: None, {"compiler_output_sha256": "0" * 64})),
        run_case("nonzero_compiler_exit_claimed_pass", lambda case: update(case, lambda i, o, s: s.update(solc_exit_code=1))),
        run_case("failed_freeze_claimed_pass", lambda case: update(case, lambda i, o, s: s.update(unchanged_during_build=False))),
        run_case("open_inventory_claimed_pass", lambda case: update(case, lambda i, o, s: s.update(closed_input_inventory=False))),
        run_case("malformed_settings_null", lambda case: update(case, lambda i, o, s: (i.update(settings=None), s.update(settings=None)))),
        run_case("stored_dependency_binding_omitted", lambda base: base["source_snapshot"]["dependency_source_sha256"].pop(
            sorted(base["source_snapshot"]["dependency_source_sha256"])[0]), actual_repository=True),
        run_case("stored_compiler_settings_omitted", lambda base: base["source_snapshot"].pop("compiler_settings"), actual_repository=True),
    ]
    after = {name: sha((ROOT / name).read_bytes()) for name in watched}
    report = {"scope": "Independent negative probes of evidence parsing/consistency only; no compiler/EVM/security approval.",
              "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "command": "python -X utf8 reports/day-readiness-20261025/evidence-negative-probes.py",
              "script_sha256": sha(Path(__file__).read_bytes()), "source_sha256": before,
              "sources_unchanged": before == after, "cases": cases,
              "case_count": len(cases), "met": sum(case["expectation_met"] for case in cases),
              "unexpected_acceptance": [case["name"] for case in cases if case["actual_accept"] and not case["expected_accept"]]}
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("case_count", "met", "sources_unchanged", "unexpected_acceptance")}, indent=2))
    return 1 if report["unexpected_acceptance"] or not report["sources_unchanged"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
