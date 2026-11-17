"""Offline reconciliation of the finite reservation stages; executes no tests."""
import hashlib
import importlib.util
import json
from pathlib import Path

OWN = Path(__file__).resolve().parent
ROOT = OWN.parents[1]
V = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117")
spec = importlib.util.spec_from_file_location("latest29_proof", OWN / "collect_latest29.py")
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def methods(result):
    return {f"{contract}.{name}": case for contract, values in result.items()
            for name, case in values["test_results"].items()}


def main():
    capacity = methods(load(V / "reservation-final/capacity-final.json"))
    first_pass = {name: row for name, row in capacity.items() if row["status"] == "Success"}
    first_failed = {name for name, row in capacity.items() if row["status"] == "Failure"}
    assert len(capacity) == 12 and len(first_pass) == 8 and len(first_failed) == 4
    selections = (
        ("reservation-final", "capacity-activation-fixed.json", 4),
        ("reservation", "actual-core-new.json", 2),
        ("reservation-final", "pooled-switch-adapted.json", 2),
    )
    combined = dict(first_pass)
    stages = []
    for folder, filename, expected_count in selections:
        path = V / folder / filename
        value = load(path)
        selected = methods(value)
        assert len(selected) == expected_count and all(row["status"] == "Success" for row in selected.values())
        if filename == "capacity-activation-fixed.json":
            assert set(selected) == first_failed
        assert not (set(selected) & set(combined))
        combined.update(selected)
        published = OWN / ("RESERVATION-" + filename)
        published.write_bytes(path.read_bytes())
        source_scopes = []
        for contract in value:
            source, name = contract.split(":")
            artifact_path = V / folder / "out" / Path(source).name / (name + ".json")
            raw = artifact_path.read_bytes()
            artifact = json.loads(raw)
            meta = artifact["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            scope = proof.compiler_source_proof(meta, False)
            assert all(row["scope"] == "current exact bytes" for row in scope["sources"].values()), contract
            source_scopes.append({"contract": contract, "artifact_sha256": sha(raw), "compiler_source_proof": scope})
        stages.append({"log": published.name, "sha256": sha(path.read_bytes()),
                       "passed_methods": sorted(selected), "source_scopes": source_scopes})
    assert len(combined) == 16
    output = {
        "schema": 1,
        "unique_passed_methods": 16,
        "new_methods": 4,
        "adapted_existing_methods": 12,
        "methods": sorted(combined),
        "stages": stages,
        "reused_eight_reservation_only_methods": {
            "log": "RESERVATION-before-fixedZZZ.json",
            "methods": sorted(first_pass),
            "source_stage": "Final four production sources; test-only adapter before fixedZZZ getter.",
            "limit": "Original compiled test artifact was overwritten; exact preceding helper is explicitly reconstructed, not presented as retained original metadata.",
            "source_explanation": "RESERVATION-helper-stage.json",
            "rerun": False,
        },
        "intermediate_failures": [
            {"log": "RESERVATION-provisional-capacity.json", "scope": "Rejected oversized direct-Budget source; eight passes/four activation failures; not final evidence."},
            {"log": "RESERVATION-before-fixedZZZ.json", "scope": "Final production code; eight reservation-only passes/four activation failures from missing test adapter getter."},
            {"log": "RESERVATION-fixedZZZ-failure-trace.log", "scope": "One overlapping diagnostic failure, not an additional method; identifies Oracle.beginExecution -> missing fixedZZZ."},
        ],
        "production_sources_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path.read_bytes())
                                      for path in sorted((ROOT / "src").rglob("*.sol"))},
        "normal_size_gate": "Root full 48-gate report is separate. Rejected Budget/VaultCanonical stages and probes remain explicit.",
        "test_gas_is_production_gas_qualification": False,
        "unchanged_suite_or_public_environment_rerun": False,
    }
    (OWN / "RESERVATION_VERIFICATION.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"unique_passed": 16, "new": 4, "adapted": 12, "current_stage_proved": 8, "earlier_test_helper_stage": 8}))


if __name__ == "__main__":
    main()
