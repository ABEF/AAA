"""Offline integrity/reconciliation only; no RPC, EVM, compiler or test rerun."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> object:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def descendants(node: dict):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-root", type=Path)
    args = parser.parse_args()
    manifest = read(HERE / "ARTIFACTS.json")
    for row in manifest["files"]:
        path = HERE / row["path"]
        require(sha(path.read_bytes()) == row["sha256"], f"artifact changed: {row['path']}")
    scope = read(HERE / "TEST_SCOPE.json")
    parent = (ROOT / "test/ReferenceExecutionContext.t.sol").read_bytes()
    restored = parent.replace(b"bytes32 internal exportSetupHash;", b"bytes32 private exportSetupHash;")
    require(sha(parent) == scope["current_parent_sha256"], "parent source changed")
    require(sha(restored) == scope["original_parent_sha256"], "parent change is not visibility-only")
    require(len(re.findall(rb"function\s+test\w+\(", restored)) == 35, "old method count changed")
    require(sha((ROOT / scope["new_test_path"]).read_bytes()) == scope["new_test_sha256"], "profile test changed")
    snapshot = read(HERE / "SOURCE_SNAPSHOT.json")
    sources = {name: digest for name, digest in snapshot["source_sha256"].items() if name.startswith("src/")}
    require(len(sources) == 61, "production source inventory changed")
    for name, digest in sources.items():
        require(sha((ROOT / name).read_bytes()) == digest, f"production source changed: {name}")
    normal_bytes = gzip.decompress((ROOT / "reports/gas-feasibility-20261111/build/compiler-input.json.gz").read_bytes())
    require(sha(normal_bytes) == snapshot["normal_input_sha256"], "accepted normal input changed")
    normal = json.loads(normal_bytes)
    require(len(normal["sources"]) == 100, "normal source inventory changed")
    for name, source in normal["sources"].items():
        require((ROOT / name).read_bytes() == source["content"].encode(), f"normal source differs: {name}")
    execution = read(HERE / "EXECUTION.json")
    require(len(execution["test_methods"]) == 5, "wrong new-method count")
    for i, row in enumerate(execution["test_methods"]):
        compact = read(HERE / "unit" / str(i) / "RESULT.json.gz")
        require(compact["source_forge_sha256"] == row["raw_forge_sha256"], "raw Forge archive identity differs")
        name, result = compact["method"], compact["result"]
        require(name.removesuffix("()") == row["method"] and result["status"] == "Success", "new method did not pass")
        require(row["process_exit_code"] == 0, "Forge process failed")
    gas = read(HERE / "GAS.json")
    require(len(gas["cases"]) == 10, "wrong RPC case count")
    allowed = {"eth_chainId", "eth_getBlockByNumber", "eth_getBlockByHash", "eth_getCode", "eth_call", "eth_estimateGas", "eth_gasPrice", "eth_getBalance", "debug_traceCall"}
    summaries = []
    for row in gas["cases"]:
        fixture_path = HERE / row["fixture"]
        require(sha(fixture_path.read_bytes()) == row["fixture_sha256"], "fixture identity differs")
        fixture = read(fixture_path)
        records = read(fixture_path.parent / "rpc-records.json.gz")
        verification = read(fixture_path.parent / "VERIFICATION.json")
        require(verification["successful"] and verification["owned_node_stopped"], "operation or cleanup failed")
        require(all(record["method"] in allowed for record in records), "non-read-only RPC recorded")

        def response(method: str, params: list):
            matches = [record["response"] for record in records if record["method"] == method and record["params"] == params]
            require(len(matches) == 1, f"missing or ambiguous recorded response: {row['case']} {method}")
            require("error" not in matches[0], f"recorded RPC failed: {method}")
            return matches[0]["result"]

        profile = fixture["profile"]
        cap, padding = profile["cap"], profile["padding_bps"]
        contribution = row["case"].startswith(("eth-", "zzz-"))
        require((cap, padding) == ((20_000_000, 2000) if contribution else (24_000_000, 2500)), "profile or margin changed")
        tx = fixture["transaction"]
        require(tx["from"] == profile["sender"] and tx["to"] == profile["destination"], "actual caller/target differs")
        require(int(tx["gas"], 16) == cap and int(tx["value"], 16) == profile["value"] and tx["data"] == profile["data"], "actual payload differs")
        block = {"blockHash": fixture["confirmed_block"]["hash"], "requireCanonical": True}
        require(int(fixture["confirmed_block"]["gasLimit"], 16) == 32_000_000, "wrong block limit")
        estimate = int(response("eth_estimateGas", [tx, block]), 16)
        padded = (estimate * (10000 + padding) + 9999) // 10000
        require(estimate == fixture["estimate_gas"] and padded == fixture["padded_gas"] <= cap, "estimate margin does not fit")
        require(response("eth_call", [tx, block]) == "0x", "profile cap call failed")
        require(response("eth_call", [{**tx, "gas": hex(padded)}, block]) == "0x", "exact padded call failed")
        require(response("eth_getCode", [profile["sender"], block]) == "0x", "caller is not EOA")
        price = int(response("eth_gasPrice", []), 16)
        balance = int(response("eth_getBalance", [profile["sender"], block]), 16)
        require(price == fixture["gas_price_wei"] and balance == fixture["sender_balance_wei"], "local affordability inputs differ")
        require(balance >= profile["value"] + padded * price, "local sender cannot afford the call")
        require(response("eth_getBlockByHash", [block["blockHash"], False]) == fixture["confirmed_block"], "canonical final header differs")
        for address, expected in fixture["materialized"].items():
            if address in fixture["omitted_harness"]:
                continue
            raw_code = bytes.fromhex(response("eth_getCode", [address, block]).removeprefix("0x"))
            require(len(raw_code) == expected["length"] and "0x" + keccak256(raw_code).hex() == expected["hash"], "runtime differs from actual exported code")
        trace = fixture["actual_trace_call"]
        require(response(trace["method"], trace["params"]) == trace["result"], "trace was not the captured response")
        require(trace["result"]["from"].lower() == profile["sender"] and not trace["result"].get("error"), "actual trace caller/success differs")
        omitted = set(fixture["omitted_harness"])
        require(not any(node.get("to", "").lower() in omitted for node in descendants(trace["result"])), "production trace calls omitted harness")
        require(int(trace["result"]["gasUsed"], 16) == verification["gas_used"] == row["actual_rpc"]["gas_used"], "trace gas differs")
        require(row["actual_rpc"]["remaining_profile_margin"] == cap - padded, "remaining margin differs")
        summaries.append({"case": row["case"], "estimate_gas": estimate, "padded_gas": padded, "remaining_margin": cap - padded})
    external_count = 0
    if args.external_root is not None:
        for row in read(HERE / "EXTERNAL.json")["files"]:
            require(sha((args.external_root / row["path"]).read_bytes()) == row["sha256"], f"external archive changed: {row['path']}")
            external_count += 1
    print(json.dumps({"successful": True, "new_methods": 5, "actual_rpc_states": 10, "all_exact_padded_calls": True, "production_sources": len(sources), "old_methods_rerun": 0, "external_files_checked": external_count, "cases": summaries}, indent=2))


if __name__ == "__main__":
    main()
