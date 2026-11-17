"""Reconcile only the selected new/strengthened checks; no test/compiler/RPC run."""
import hashlib
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256

OWN = Path(__file__).resolve().parent
BASELINE = "003c8d8dc88b60cbfbcc8caf61fa864c6487b40f"
EXTERNAL = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117/latest29")
SELECTIONS = (
    ("seal-changed.json", "OperatorSealArtwork20261117.t.sol", "OperatorSealArtwork20261117Test", (
        "testConstructorConfiguredArtworkRootStillSealsWithoutMutation()",
        "testNonbootstrapCannotPopulateEmptyRootOrSeal()",
        "testUnconfiguredArtworkRootBlocksSealThenBootstrapCanCompleteSetup()",
    )),
    ("canonical-changed.json", "CanonicalPreparation.t.sol", "CanonicalPreparationTest", (
        "testClaimsTransfersPendingRevealAndLPFeeCollectionStayAvailable()",
        "testGovernanceAnnouncementInFinalTreasuryCallbackCannotBypassVaultEndGuard()",
        "testGovernanceAnnouncementInNFTCallbackRollsBackTheEntireMint()",
        "testHarvestAndGovernanceParkingRemainAvailableWithoutSourcePrice()",
    )),
    ("royalty-new.json", "RoyaltyRecovery.t.sol", "OriginalCurrencyRoyaltyTest", (
        "testRecoveryExactUnitsRotateAcrossSmallTranchesReverseClaimsAndTransfer()",
    )),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def obj(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


@lru_cache(maxsize=400)
def compiler_hash(raw):
    return "0x" + keccak256(raw).hex()


def compiler_source_proof(meta, first_stage):
    assert meta["compiler"]["version"] == "0.8.26+commit.8a97fa7a"
    settings = meta["settings"]
    assert settings["evmVersion"] == "cancun" and settings["viaIR"] is True
    assert settings["optimizer"]["runs"] == 1
    assert settings["optimizer"]["details"]["yul"] is False
    for component in ("peephole", "inliner", "jumpdestRemover", "orderLiterals", "deduplicate", "cse", "constantOptimizer"):
        assert settings["optimizer"]["details"][component] is True
    sources = {}
    for name, record in meta["sources"].items():
        raw = (ROOT / name).read_bytes()
        scope = "current exact bytes"
        expected = record["keccak256"]
        if expected not in (compiler_hash(raw), compiler_hash(raw.replace(b"\r\n", b"\n"))):
            reservation_stage = name in ("src/ZZZMigrationBudget.sol", "src/ZZZCustodyValidation.sol", "test/VaultAccounting.t.sol")
            assert reservation_stage or (first_stage and name in ("src/ZZZVault.sol", "src/ZZZNFTMetadata.sol")), name
            raw = subprocess.run(["git", "show", f"{BASELINE}:{name}"], cwd=ROOT, check=True, capture_output=True).stdout
            scope = ("explicit baseline before separately authorized reservation restriction/fixture adaptation" if reservation_stage
                     else "explicit first-stage baseline before separate constructor/root fixes")
        matched_raw = expected == compiler_hash(raw)
        assert matched_raw or expected == compiler_hash(raw.replace(b"\r\n", b"\n")), name
        sources[name] = {"raw_sha256": sha(raw), "compiler_keccak256": expected,
                         "compiler_line_endings": "exact" if matched_raw else "CRLF normalized to LF only",
                         "scope": scope}
    return {"compiler": meta["compiler"], "settings": settings, "sources": sources}


def main():
    stages = []
    all_methods = []
    for log, file, contract, expected in SELECTIONS:
        path = EXTERNAL / log
        result = obj(path)
        published_log = OWN / ("LATEST29-" + log)
        published_log.write_bytes(path.read_bytes())
        key = f"test/{file}:{contract}"
        assert set(result) == {key}, set(result)
        methods = result[key]["test_results"]
        assert set(methods) == set(expected), set(methods)
        assert all(value["status"] == "Success" for value in methods.values())
        first = log == "seal-changed.json"
        if first:
            artifact = obj(EXTERNAL / "seal-metadata-source-stage.json")
            meta = artifact["metadata"]
            artifact_sha = artifact["compiled_artifact_sha256"]
        else:
            artifact_path = EXTERNAL / "out" / file / f"{contract}.json"
            artifact_raw = artifact_path.read_bytes()
            artifact = json.loads(artifact_raw)
            meta = artifact["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            artifact_sha = sha(artifact_raw)
        names = [f"{key}.{name}" for name in sorted(methods)]
        all_methods.extend(names)
        stages.append({"log": published_log.name, "external_original": str(path), "log_sha256": sha(path.read_bytes()),
                       "selected_methods": names, "status": "all selected passed",
                       "test_body_gas_is_production_transaction_gas": False,
                       "compiled_artifact_sha256": artifact_sha,
                       "compiler_source_proof": compiler_source_proof(meta, first)})
    assert len(all_methods) == len(set(all_methods)) == 8
    timing = obj(OWN / "LATEST29_TIMING_OBSERVATION.json")
    assert timing["exit_code"] == 0 and timing["observed_passed_methods"] == 1
    for name, digest in timing["source_sha256"].items():
        assert sha((ROOT / name).read_bytes()) == digest, name
    matrix = obj(OWN / "LATEST29_METHOD_MATRIX.json")
    assert len(matrix["rows"]) == len({row["method"] for row in matrix["rows"]}) == 29
    result = {"schema": 1, "baseline_commit": BASELINE,
              "original_methods_individually_source_reviewed": 29,
              "new_selected_unique_methods": 9, "strengthened_existing_methods": 8, "new_method": 1,
              "selected_solidity_methods": all_methods, "stages": stages, "timing_observation": timing,
              "optimizer_component_flags_checked": True,
              "collector_source_sha256": sha(Path(__file__).read_bytes()),
              "test_source_and_fixture_changes_only_by_this_portion": True,
              "separate_production_changes": "First seal stage precedes Vault home-chain/metadata fixes. All nine selected stages precede the later authorized Budget reservation restriction.",
              "old_fuzz_1000_inputs_rerun": False, "unchanged_methods_rerun": False,
              "old_zero_selection_attempts": "Retained by original operator-behavior report; zero verification, no new zero-selection attempt here.",
              "public_rpc_signing_deployment_service_environment_changes": False}
    output = OWN / "LATEST29_VERIFICATION.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_reviewed": 29, "selected_passed": 9, "solidity_passed": 8, "python_passed": 1}))


if __name__ == "__main__":
    main()
