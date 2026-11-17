"""Collect finite selected EVM results, retaining failed source stages separately."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=None)
def ethereum_hash(data: bytes) -> str:
    return "0x" + keccak256(data).hex()


def load(path: Path) -> dict:
    # Forge JSON stdout can follow non-JSON compiler diagnostics.
    text = path.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        if line.startswith('{"test/'):
            return json.loads(line)
    raise ValueError(f"No nonempty Forge result: {path.name}")


def stage(base: Path, label: str, raw: str, artifacts: list[tuple[str, str]], overrides: dict[str, str] | None = None) -> dict:
    raw_path = base / raw
    suites = load(raw_path)
    rows = []
    for suite, values in suites.items():
        for method, result in values["test_results"].items():
            rows.append({"id": f"{suite}.{method}", "status": result["status"], "reason": result["reason"]})
    if not rows:
        raise ValueError(f"Zero selected methods: {label}")
    proofs = []
    for artifact_name, contract in artifacts:
        artifact_path = base / artifact_name
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        metadata = artifact["metadata"]
        mismatches = []
        sources = []
        for rel, record in metadata["sources"].items():
            override = (overrides or {}).get(rel)
            path = base / override if override else ROOT / rel
            data = path.read_bytes()
            expected = record["keccak256"]
            if ethereum_hash(data) == expected:
                form = "exact raw bytes"
            elif b"\r\n" in data and ethereum_hash(data.replace(b"\r\n", b"\n")) == expected:
                form = "exact CRLF-to-LF compiler input"
            else:
                form = "MISMATCH"
                mismatches.append(rel)
            sources.append({"path": rel, "sha256": sha(path), "compiled_keccak256": expected,
                            "proof": form, "source_override": override})
        if mismatches:
            raise ValueError(f"{label} compiler input drift: {mismatches}")
        proofs.append({"contract": contract, "path": artifact_name, "sha256": sha(artifact_path),
                       "compiler": metadata["compiler"]["version"], "source_count": len(sources), "sources": sources})
    return {"label": label, "raw_result": raw, "raw_sha256": sha(raw_path), "methods": rows,
            "compiled_source_proofs": proofs, "test_body_gas_is_production_gas": False}


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    stages = [
        stage(base,"old default-threshold failure","baseline/pooled-security-result.json",[("baseline/PooledSecurityTest.json","PooledSecurityTest")],{"test/PooledSecurity.t.sol":"baseline/PooledSecurity.t.sol"}),
        stage(base,"old explicit-one-percent failure","baseline/entry-budget-result.json",[("baseline/EntryExecutionBudgetTest.json","EntryExecutionBudgetTest")],{"test/EntryExecutionBudget.t.sol":"baseline/EntryExecutionBudget.t.sol"}),
        stage(base,"old native-dust assertion failure","baseline/lp-only-result.json",[("baseline/LPOnlyEntryBoundaryTest.json","LPOnlyEntryBoundaryTest")],{"test/LPOnlyEntryBoundary.t.sol":"baseline/LPOnlyEntryBoundary.t.sol"}),
        stage(base,"initial cross-actions:3pass+idle-cap discovery","initial-cross-action/result.json",[("initial-cross-action/LPFixtureImpact20261117Test.json","LPFixtureImpact20261117Test")],{"test/LPFixtureImpact20261117.t.sol":"initial-cross-action/LPFixtureImpact20261117.t.sol"}),
        stage(base,"affected portfolio first-current selections","final/portfolio-result.json",[("final/PortfolioAccountingTest.json","PortfolioAccountingTest")]),
        stage(base,"corrected default-threshold case","final/pooled-security-result.json",[("final/PooledSecurityTest.json","PooledSecurityTest")]),
        stage(base,"corrected explicit-one-percent case","final/entry-budget-result.json",[("final/EntryExecutionBudgetTest.json","EntryExecutionBudgetTest")]),
        stage(base,"compound-recovery sequence+three Entry callback phases","final/new-completion-result.json",[("final/LPFixtureImpact20261117Test.json","LPFixtureImpact20261117Test"),("final/EntryFixtureImpact20261117Test.json","EntryFixtureImpact20261117Test")]),
        stage(base,"corrected native-dust callback placements","final/lp-only-result.json",[("final/LPOnlyEntryBoundaryTest.json","LPOnlyEntryBoundaryTest")]),
    ]
    passed = sorted({m["id"] for s in stages for m in s["methods"] if m["status"]=="Success"})
    failed = [dict(stage=s["label"], **m) for s in stages for m in s["methods"] if m["status"]!="Success"]
    assert len(passed)==13, passed
    assert len(failed)==4, failed
    result = {"schema":1,"baseline":"fdb7562bf56b11d8bade612fdaf7f9a54daf118a",
              "distinct_passed_methods":len(passed),"new_methods":5,"corrected_methods":4,"previously_unexecuted_affected_portfolio_methods":4,
              "passed_method_ids":passed,"retained_failed_attempts":failed,"stages":stages,
              "production_code_changed":False,"broad_unchanged_suite_rerun":False,
              "scope":"Actual financial modules with explicitly synthetic venue/authority/feed geometry; current source stages not relabelled as market/gas qualification"}
    Path(__file__).with_name("LP_EXECUTION_RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"distinct_passed_methods":len(passed),"retained_failed_attempts":len(failed),"compiled_source_checks":sum(len(p["sources"]) for s in stages for p in s["compiled_source_proofs"])}))


if __name__ == "__main__":
    main()
