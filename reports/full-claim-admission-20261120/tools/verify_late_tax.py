"""Independent offline stage-aware reader for the NEW late-tax32 continuation."""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED_CHECKER = "d03cfdb0bd7adf11127bf5043fbfd494ceda7768c01cb39573e6f1eac84e61e2"
if hashlib.sha256((HERE / "verify_admission.py").read_bytes()).hexdigest() != SHARED_CHECKER:
    raise ValueError("Unreviewed shared independent checker source")
spec = importlib.util.spec_from_file_location("late_tax_shared_checker", HERE / "verify_admission.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

STAGES = {
    "failure": {"wire": "ba64c6cee949ac39867a2a419966a12c838e71a988dc50dabb2c7c07e3c605b9",
        "restorer": "b5e0c66012752303983570c87af2c824734380c0d7bd6eba41a79b5e0e4058e6"},
    "continuation": {"wire": "f4a88b3087a3ba865b0f5632df1b858f958845aa63223b8da7c0ad7253068613",
        "restorer": "0e099603f05a9be13c34ee522289c4c062fa3aaccd441d7fd43d3635a80ee571"},
}
EXPORT_FILE = "033654ac79c40eb7278dce050d43c23cca36cdd3b8761954fdac52e64087c69d"
MANIFEST_FILE = "3cc6bc33b754995e149af837c853a8984b1fe6a8d0f3c621dd2ea4a1652bc69a"
STATE_FILE = "4713b6e99987927b32061fa5c3965e0d403f3c048f9281ddff0826a93eccafda"
GENESIS = "0x828f888a4efcfb571dcc20bbfa24896b388a35c21cfb8847f1623b03c7d1b307"


def frozen_file(path, expected):
    actual, size = V.file_sha(path, V.LIMIT)
    V.require(actual == expected, "Frozen late-tax evidence bytes differ: " + Path(path).name)
    return size


def read_stage(folder, stage, records):
    folder = Path(folder).resolve()
    proof = V.load(folder / "RESTORE_PROVENANCE.json")
    verified = V.load(folder / "RESTORE_VERIFIED.json")
    manifest = V.load(folder / "FIXTURE_MANIFEST.json")
    frozen_file(folder / "restore_case.py", STAGES[stage]["restorer"])
    frozen_file(folder / "FIXTURE_MANIFEST.json", MANIFEST_FILE)
    frozen_file(folder / "exact-anvil-state.json", STATE_FILE)
    V.require(proof["restorer_source_sha256"] == STAGES[stage]["restorer"] and
        proof["source_export_file_sha256"] == EXPORT_FILE and
        proof["source_manifest_sha256"] == MANIFEST_FILE and
        proof["unpacked_state_sha256"] == STATE_FILE and
        proof["source_genesis"] == GENESIS and proof["source_sender_nonce"] == 444 and
        proof["source_best_block_number"] == 445 and
        proof["protocol_storage_edited"] is False and
        proof["protocol_runtime_relabelled"] is False and
        proof["constructors_or_population_rerun"] is False,
        "Exact same-source restoration proof differs")
    wire_path = folder / "node/rpc-records.json.gz"
    wire_size = frozen_file(wire_path, STAGES[stage]["wire"])
    # These restored cases are small. Retain every original method, including
    # nonce/clock observations outside the unsigned API's own read allowlist.
    with gzip.open(wire_path, "rb") as stream:
        wire_raw = stream.read(V.LIMIT + 1)
    V.require(len(wire_raw) <= V.LIMIT, "Restored wire exceeds the existing bounded JSON inventory")
    original = V.flatten_wire([{**row, "original_index": index}
        for index, row in enumerate(V.loads(wire_raw))])
    wire_proof = {"compressed_sha256": STAGES[stage]["wire"], "compressed_bytes": wire_size,
        "expanded_sha256": V.sha(wire_raw), "expanded_bytes": len(wire_raw),
        "original_records": len(original), "all_original_methods_retained": True}
    V.require(verified["exact_anchor"] == proof["source_anchor"] and
        verified["exact_genesis"] == GENESIS and
        verified["exact_deployment_header"] == manifest["deployment_block_hash"] and
        verified["source_nonce"] == 444 and verified["actual_nfts"] == 32 and
        verified["actual_active"] == 32 and verified["actual_currencies"] == 65,
        "Restored header/population identity differs")
    V.wire_result(original, "eth_getBlockByNumber", ["latest", False], verified["exact_anchor"])
    V.require(any(row["request"]["method"] == "eth_getBlockByNumber" and
        row["request"]["params"] == ["0x0", False] and
        row["response"].get("result", {}).get("hash") == GENESIS for row in original),
        "Exact restored genesis not observed")
    V.wire_result(original, "eth_getTransactionCount", [manifest["owner"], "latest"], hex(444))
    for field, method in (("deployment_block_hash", "eth_getBlockByNumber"),):
        V.require(any(row["request"]["method"] == method and
            row["request"]["params"] == [hex(manifest["deployment_block"]), False] and
            row["response"].get("result", {}).get("hash") == manifest[field] for row in original),
            "Original deployment ancestry is missing")
    cleanup = V.load(folder / "node/cleanup.json")
    V.require(cleanup["owned_node_stopped"] is True and cleanup["pending_submission"] is None,
              "Owned restored node is not cleanly stopped")
    forbidden = ("anvil_setStorageAt", "anvil_setCode", "anvil_setBalance", "anvil_loadState", "anvil_reset")
    V.require(not any(row["request"]["method"] in forbidden for row in original),
              "Protocol/runtime/state override appeared in the restored campaign")
    return manifest, original, wire_proof, proof


def check_record(record, manifest, original, *, source, expected):
    V.require(record["explicit_negative_control"] is None and record["interception_matches"] == 0,
              "Late-tax resource proof must use actual unintercepted responses")
    config, policy = record["projection_config"], record["transaction_config"]
    V.check_configuration(config, policy, manifest)
    start, end = record["fixture_wire_start"], record["fixture_wire_end"]
    rows = record["rpc_wire"]
    by_index = {row["original_index"]: row for row in original}
    V.require(end - start == len(V.flatten_wire(rows)), "Late-tax captured request range is incomplete")
    selected = [by_index[index] for index in range(start, end)]
    V.require(V.bind_plan_to_original(rows, selected) == end - start,
              "Late-tax normal request was not tied to exact original wire")
    with V.planner_stage(source, expected):
        return (V.check_plan(record, config, policy, rows) if "result" in record else
                V.check_refusal(record, config, policy, rows))


def selected_identity(rows):
    return [(str(row["token_id"]), row["asset"], row["royalty"]) for row in rows]


def check_clock(folder, manifest, original):
    clock = V.load(Path(folder) / "RESTORE_CLOCK.json")
    before, after, pending = clock["before_latest"], clock["after_latest"], clock["after_pending"]
    V.check_header(before, original)
    V.check_header(after, original)
    V.require(before["stateRoot"] == after["stateRoot"] and
        V.quantity(after["number"]) == V.quantity(before["number"]) + 1 and
        after["parentHash"] == before["hash"] and after["transactions"] == [] and
        V.quantity(after["timestamp"]) == V.quantity(before["timestamp"]) + 1 and
        V.quantity(pending["timestamp"]) >= V.quantity(after["timestamp"]) and
        clock["before_latest_royalties_open"] == 1 and clock["before_pending_royalties_open"] == 0 and
        clock["after_pending_royalties_open"] == 1 and
        clock["explicit_empty_clock_block"] is True and clock["protocol_call_or_storage_edit"] is False,
        "Owned pending-clock correction changed principal state or lacks its finite boundary")
    V.wire_result(original, "eth_getBlockByNumber", ["pending", False], pending)
    V.require(sum(row["request"]["method"] == "evm_setNextBlockTimestamp" and
        row["request"]["params"] == [V.quantity(after["timestamp"])] for row in original) == 1 and
        sum(row["request"]["method"] == "evm_mine" for row in original) == 1,
        "Expected exactly one reviewed empty local clock block")
    for tag, expected in (("latest", 1), ("pending", 0)):
        data = V.calldata("royaltiesOpen()")
        V.wire_result(original, "eth_call", [{"to": manifest["contracts"]["royalties"], "data": data}, tag],
                      "0x" + f"{expected:064x}")
    return {"empty_block_number": V.quantity(after["number"]), "state_root_unchanged": True,
            "source_nonce_unchanged": True, "pending_clock_refusal_retained": True}


def verify(failure, continuation):
    failure, continuation = Path(failure).resolve(), Path(continuation).resolve()
    old_path = failure / "qualification/claim_planner.baseline.py.txt"
    frozen_file(old_path, V.OLD_PLANNER_SHA)
    baseline = V.load(failure / "qualification/late-tax32-baseline.json")
    changed = V.load(failure / "qualification/late-tax32-first-success.json")
    manifest, original, failure_wire, provenance = read_stage(failure, "failure", [baseline, changed])
    V.require(baseline["error"] == {"type": "WorkLimit", "reason": "rpc_budget"} and
        baseline["rpc_count"] == 1024 and baseline["elapsed_seconds"] < 25 and
        "result" not in baseline and baseline["successful_evm_simulation_sizes"] == [16, 24],
        "Original bounded-work failure was altered or relabelled")
    baseline_check = check_record(baseline, manifest, original, source=old_path, expected=V.OLD_PLANNER_SHA)
    current_path = V.ROOT / "frontend_api/claim_planner.py"
    changed_check = check_record(changed, manifest, original, source=current_path, expected=V.NEW_PLANNER_SHA)
    V.require(selected_identity(changed["payload"]["claims"]) == selected_identity(baseline["payload"]["claims"]) and
        changed["rpc_count"] == 885 and changed["successful_evm_simulation_sizes"] == [16, 16] and
        [len(row["selection_indices"]) for row in changed["result"]["planning"]["attempts"]] == [32, 16],
        "Changed source did not retain exact selection and conservative final revalidation")
    V.require(not any(row["request"]["method"] == "eth_sendTransaction" for row in original),
        "Prior pending-clock refusal was relabelled as an actual claim")
    V.require(any(row["request"]["method"] == "eth_estimateGas" and
        row["response"].get("error", {}).get("data") == "0xbaf3f0f7" for row in original),
        "Original actual pending-estimate refusal was lost")
    qualification = V.load(continuation / "qualification/qualification.json")
    records = qualification["plans"]
    later_manifest, later_wire, continuation_wire, later_provenance = read_stage(continuation, "continuation", records)
    V.require(manifest == later_manifest and provenance["source_anchor"] == later_provenance["source_anchor"],
              "Continuation changed source population/anchor/profile")
    V.require(qualification["fixture_manifest_sha256"] == V.sha(V.canonical(manifest).encode()) and
        qualification["production_stages"] == [] and len(records) == 2 and len(qualification["executions"]) == 1,
        "Missing/extra continuation operations or a relabelled production stage")
    clock = check_clock(continuation, manifest, later_wire)
    plan_checks, positive = [], {}
    for record in records:
        plan_checks.append(check_record(record, manifest, later_wire, source=current_path, expected=V.NEW_PLANNER_SHA))
        positive[record["label"]] = record
    first, second = records
    claims = first["payload"]["claims"]
    V.require(len(claims) == 32 and len({row["token_id"] for row in claims[:31]}) == 31 and
        all(row["royalty"] is True and row["asset"] == manifest["contracts"]["currency_0"] for row in claims[:31]) and
        claims[-1] == {"token_id": claims[0]["token_id"], "asset": manifest["contracts"]["currency_63"], "royalty": True} and
        selected_identity(claims) == selected_identity(baseline["payload"]["claims"]),
        "Late-fault32 selection differs from the exact31 healthy + taxed-last case")
    batch = first["result"]["next_batch"]["claim_operations"]
    remaining = first["result"]["remaining_claims"]
    V.require(len(batch) == 16 and selected_identity(batch) == selected_identity(claims[:16]) and
        [row["selection_index"] for row in remaining] == list(range(16, 32)) and
        selected_identity(second["payload"]["claims"]) == selected_identity(remaining) and
        len(second["result"]["next_batch"]["claim_operations"]) == 8 and
        any(row["asset"] == claims[-1]["asset"] for row in second["result"]["remaining_claims"]),
        "Conservative execution or fresh unsigned remainder silently lost a selection")
    execution = V.check_execution(qualification["executions"][0], positive, later_wire)
    V.require(sum(row["request"]["method"] == "eth_sendTransaction" for row in later_wire) == 1,
              "Unexpected additional transaction in finite continuation")
    closing = qualification["closing_original_claims"]
    block = V.check_header(closing["header"], later_wire)
    V.require(selected_identity(closing["claims"]) == selected_identity(claims), "Closing original selection changed")
    amounts = [V.claim_read(first["projection_config"], manifest["owner"], row, block, later_wire)
               for row in closing["claims"]]
    V.require(all(value == 0 for value in amounts[:16]) and all(value > 0 for value in amounts[16:]),
              "Paid and retained original-currency rights do not reconcile")
    return {"schema": 1, "complete": True, "production_approved": False,
        "shared_checker_sha256": SHARED_CHECKER,
        "source_stages": {"old": V.OLD_PLANNER_SHA, "new": V.NEW_PLANNER_SHA},
        "original_resource_failure": baseline_check, "first_changed_source_proof": changed_check,
        "continuation_plans": plan_checks, "execution": execution, "clock": clock,
        "closing_paid_zero": 16, "closing_unselected_positive": 16,
        "taxed_last_right_retained": True, "failure_wire": failure_wire,
        "continuation_wire": continuation_wire, "original_population_rerun": False,
        "scope": "Independent offline exact-stage normal API replay and actual receipt/balance verification; "
                 "finite32-NFT65-currency case, not the1,000-NFT maximum state or actual provider acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("failure", type=Path)
    parser.add_argument("continuation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.failure, args.continuation)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"complete": result["complete"], "output": str(args.output),
        "entries_paid": result["execution"]["entries_paid"], "retained": 16}), flush=True)


if __name__ == "__main__":
    main()
