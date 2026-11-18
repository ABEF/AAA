"""Copy recorded finite evidence; never executes an EVM or changes source state."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
WORK = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118")
DEST = Path(__file__).resolve().parent / "full-flow-baseline"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    entries = []

    def copy(relative, target=None, compress=False):
        source = WORK / relative
        raw = source.read_bytes()
        target = target or relative
        output = DEST / (target + (".gz" if compress else ""))
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = gzip.compress(raw, mtime=0) if compress else raw
        if output.exists():
            assert output.read_bytes() == encoded, ("immutable evidence mismatch", output)
        else:
            output.write_bytes(encoded)
        entries.append({"file": output.relative_to(DEST).as_posix(), "sha256": sha(encoded),
                        "bytes": len(encoded), "original_sha256": sha(raw),
                        "original_bytes": len(raw), "gzip": compress or source.suffix == ".gz"})

    full = json.loads((WORK / "full02/EXECUTION.json").read_bytes())
    summary = json.loads((WORK / "full02/local-rpc02/SUMMARY.json").read_bytes())
    assert full["pass"] and full["compiled_source_metadata_verified"]
    assert len(full["methods"]) == 1 and summary["completed_cases"] == 10
    assert summary["verification_complete"] and len(summary["meets_20m_cases"]) == 2
    assert len(summary["fails_20m_cases"]) == 8
    for name in ["EXECUTION.json", "START.json", "HARNESS_RESOURCES.json", "PID.json",
                 "foundry.toml", "ORIGINAL_foundry.toml", "SOURCE_TEST.sol.txt", "PRODUCER.json",
                 "COMPILED_INPUT_SOURCE_POOL.json.gz", "stderr.log", "INITIAL_INFRASTRUCTURE_FAILURE.json"]:
        copy("full02/" + name)
    for name in ["raw.json", "producer-artifact.json"]:
        copy("full02/" + name, compress=True)
    for source in sorted((WORK / "full02/exports").iterdir()):
        copy(source.relative_to(WORK).as_posix(), compress=True)
    for name in ["CHECKER_START.json", "SUMMARY.json", "CALL_COST_SUMMARY.json"]:
        copy("full02/local-rpc02/" + name)
    for folder in sorted((WORK / "full02/local-rpc02").iterdir()):
        if not folder.is_dir():
            continue
        result = json.loads((folder / "VERIFICATION.json").read_bytes())
        assert result["verification_complete"], folder.name
        assert result["royalty_trace_verification"]["verified"], folder.name
        assert result["owned_node_stopped"], folder.name
        for name in ["VERIFICATION.json", "NODE.json", "rpc-records.json.gz", "anvil.log",
                     "CALL_COSTS.json", "ORACLE_BOUNDARIES.json"]:
            if (folder / name).is_file():
                copy((folder / name).relative_to(WORK).as_posix())
        # Exact alloc is reconstructible from setup/export plus authenticated profile;
        # keep its wire genesis hash rather than duplicate a second full state image.
    for name in ["EXECUTION.json", "START.json", "raw.json", "stderr.log"]:
        copy("full01/" + name)
    for source in sorted((WORK / "full02/local-rpc").glob("*/NODE.json")):
        copy(source.relative_to(WORK).as_posix())
    for name in ["RESULT.json", "START.json", "PROBE_START.json", "PROBE_RESULT.json"]:
        path = WORK / "manager/engineering01" / name
        if path.is_file():
            copy(path.relative_to(WORK).as_posix())
    for name in ["compiler-input.json", "compiler-output.json"]:
        copy("manager/engineering01/" + name, compress=True)
    for name in ["old-getters", "new-runtime"]:
        for leaf in ["NODE.json", "rpc-records.json.gz", "anvil.log"]:
            copy("manager/engineering01/" + name + "/" + leaf)
    # This manifest admits integrity and finite execution scope, not an independent audit.
    manifest = {"schema": 1, "scope": "Original round-engine full02 source stage and Manager-only engineering01; no final-source qualification",
                "source_method_count": 1, "cold_case_count": 10,
                "activation_cases_with_full20pct_under20m": 0,
                "growth_cases_with_full20pct_under20m": 2,
                "unchanged_old_tests_reexecuted": 0, "public_transactions": 0,
                "production_approved": False, "files": entries}
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    path = DEST / "MANIFEST.json"
    if path.exists():
        assert path.read_bytes() == raw, "manifest differs; use a new evidence stage"
    else:
        path.write_bytes(raw)
    print(json.dumps({"files": len(entries), "compressed_evidence_bytes": sum(e["bytes"] for e in entries),
                      "manifest_sha256": sha(raw), "new_executions": 0}))


if __name__ == "__main__":
    main()
