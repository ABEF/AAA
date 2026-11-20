"""NEW late-refusal32 selection on an exactly restored owned F6 snapshot.

The caller authenticates the original genesis, exported head, nonce, source and
runtime identities before invoking this finite case. No population is repeated.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("late_tax_normal_admission", HERE / "normal_admission.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
BASELINE_PLANNER = "6d5241d61e5d48a6b2d77f10d09114426ad8a33fc7dddf47d2ec804b48136d5f"


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("Late-tax evidence exceeds its finite byte bound")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def announce(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def _simulated_sizes(record):
    sizes = []
    for row in record["rpc_wire"]:
        request = row["requests"][0]
        if request["method"] != "eth_call" or not request["params"] or "from" not in request["params"][0]:
            continue
        result = row.get("response", {}).get("result")
        if isinstance(result, str) and len(result) >= 130 and int(result[2:66], 16) == 32:
            count = int(result[66:130], 16)
            if len(result) == 130 + 64 * count and count > 0:
                sizes.append(count)
    return sizes


def run_late_tax(fixture, output):
    output = Path(output)
    output.mkdir(exist_ok=True)
    manifest = fixture.manifest
    config = N.build_configuration(manifest["contracts"], manifest["assets"],
        chain_id=manifest["chain_id"], deployment_block=manifest["deployment_block"],
        deployment_block_hash=manifest["deployment_block_hash"],
        expected_runtime_pins=manifest["expected_runtime_pins"])
    original = [dict(token_id=str(identifier), asset=fixture.royalty_tokens[0], royalty=True)
                for identifier in fixture.ids[:31]]
    original.append(dict(token_id=str(fixture.ids[0]), asset=fixture.royalty_tokens[63], royalty=True))
    if len({row["token_id"] for row in original[:31]}) != 31:
        raise ValueError("31 distinct healthy NFTs followed by the explicit taxed currency are required")
    aggregate = {"schema": 1, "fixture_only": True,
        "kind": "new_late_tax32_normal_admission",
        "fixture_manifest_sha256": N.digest(manifest), "projection_config": config,
        "limits": N.LIMITS, "plans": [], "controls": [], "executions": [],
        "production_stages": [], "original_selection": original,
        "no_population_repeat": True, "production_approved": False}
    baseline_source = (ROOT / "frontend_api/claim_planner.py").read_bytes()
    if hashlib.sha256(baseline_source).hexdigest() != BASELINE_PLANNER:
        raise ValueError("Exact unchanged planner baseline required for the new evidence")
    with (output / "claim_planner.baseline.py.txt").open("xb") as stream:
        stream.write(baseline_source)
    def plan(label, claims):
        header = fixture.rpc.call("eth_getBlockByNumber", ["latest", False])
        start = len(fixture.rpc.records)
        result = N.qualify_plan(fixture.rpc.call, config,
            {"action": "claim", "wallet": fixture.owner, "claims": copy.deepcopy(claims)},
            clock_timestamp=int(header["timestamp"], 16), label=label)
        result["fixture_wire_start"], result["fixture_wire_end"] = start, len(fixture.rpc.records)
        result["successful_evm_simulation_sizes"] = _simulated_sizes(result)
        aggregate["plans"].append(result)
        save(output / (label + ".json"), result)
        announce({"stage": label, "error": result.get("error"), "rpc_count": result["rpc_count"],
            "elapsed_seconds": result["elapsed_seconds"],
            "successful_evm_simulation_sizes": result["successful_evm_simulation_sizes"],
            "next_batch_count": len(result.get("result", {}).get("next_batch", {}).get("claim_operations", []))
                if result.get("result", {}).get("next_batch") else 0})
        return result
    baseline = plan("late-tax32-baseline", original)
    chosen = baseline
    if baseline.get("error", {}).get("type") == "WorkLimit":
        if not baseline["successful_evm_simulation_sizes"]:
            raise ValueError("Resource refusal has no prior successful EVM prefix; root decision must be reviewed separately")
        marker = output / "CONTINUE.json"
        announce({"stage": "awaiting_root_resource_decision", "marker": str(marker),
            "maximum_wait_seconds": 180, "baseline_error": baseline["error"],
            "successful_evm_simulation_sizes": baseline["successful_evm_simulation_sizes"]})
        deadline = time.monotonic() + 180
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.25)
        if not marker.exists():
            save(output / "qualification.json", aggregate)
            raise ValueError("Root resource decision unavailable within finite180-second wait; original evidence retained")
        decision = json.loads(marker.read_text())
        if decision.get("action") != "reload_changed_planner":
            save(output / "qualification.json", aggregate)
            raise ValueError("Root-approved changed planner required for this source follow-up")
        before, after = baseline["production_source_sha256"], N.source_pins()
        if after["frontend_api/claim_planner.py"] != decision.get("approved_claim_planner_sha256") or after == before:
            raise ValueError("Root-approved changed planner pin differs")
        if any(after[name] != before[name] for name in before if name != "frontend_api/claim_planner.py"):
            raise ValueError("The finite resource correction may change only claim_planner.py")
        import frontend_api.claim_planner as planner_module
        importlib.invalidate_caches()
        importlib.reload(planner_module)
        aggregate["production_stages"].append({"kind": "root_approved_first_success_followup",
            "decision": decision, "before": before, "after": after,
            "old_request_completed_before_reload": True, "planner_module_reloaded": True})
        chosen = plan("late-tax32-first-success", original)
    if chosen.get("error") or chosen.get("result", {}).get("next_batch") is None:
        raise ValueError("Late-tax32 selection did not produce a fresh admitted healthy prefix")
    result = chosen["result"]
    batch = result["next_batch"]["claim_operations"]
    if any(row["asset"] == fixture.royalty_tokens[63] for row in batch):
        raise AssertionError("Opaque taxed-currency refusal was falsely published as executable")
    if not any(row["asset"] == fixture.royalty_tokens[63] for row in result["remaining_claims"]):
        raise AssertionError("The unresolved last currency disappeared from the explicit selection")
    # One actual admitted prefix plus a fresh remainder is sufficient; do not
    # repeat a financial matrix or execute a queue of hypothetical later batches.
    old = importlib.util.spec_from_file_location("late_tax_snapshot_helpers", HERE / "campaign_checks.py")
    helper = importlib.util.module_from_spec(old)
    old.loader.exec_module(helper)
    claims = [{key: row[key] for key in ("token_id", "asset", "royalty")} for row in batch]
    before = helper._snapshot(fixture, claims)
    tx = result["next_batch"]["transaction"]
    sent = fixture.send("late-tax32-confirmed-healthy-prefix", tx["to"], tx["data"],
        value=int(tx["value"], 16), cap=N.CAP, padding=2000)
    after = helper._snapshot(fixture, claims)
    if any(int(row["raw"]) != 0 for row in after["claims"]):
        raise AssertionError("Confirmed healthy prefix did not drain selected rights")
    execution = {"label": "late-tax32-confirmed-healthy-prefix", "plan_label": chosen["label"],
                 "transaction": sent, "before": before, "after": after}
    aggregate["executions"].append(execution)
    save(output / "late-tax32-confirmed-healthy-prefix.json", execution)
    remainder = [{key: row[key] for key in ("token_id", "asset", "royalty")}
                 for row in result["remaining_claims"]]
    fresh = plan("late-tax32-fresh-remainder", remainder)
    if fresh.get("error") or not any(row["asset"] == fixture.royalty_tokens[63]
            for row in fresh["result"]["remaining_claims"]):
        raise AssertionError("Fresh remainder did not preserve the last unresolved currency")
    aggregate["closing_original_claims"] = helper._snapshot(fixture, original)
    save(output / "qualification.json", aggregate)
    announce({"stage": "late_tax32_complete", "plans": len(aggregate["plans"]),
        "actual_claim_transactions": len(aggregate["executions"]),
        "retained_remainder_count": len(remainder)})
    return aggregate
