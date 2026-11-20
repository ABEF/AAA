"""Finite report-only full-admission claims on the caller's owned fixture."""
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
spec = importlib.util.spec_from_file_location("full_claim_normal_admission", HERE / "normal_admission.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
from zzz_ops.abi import calldata


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("Finite qualification evidence bound exceeded")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def announce(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def _snapshot(fixture, claims):
    header = fixture.rpc.call("eth_getBlockByNumber", ["latest", False])
    block = {"blockHash": header["hash"], "requireCanonical": True}
    native = int(fixture.rpc.call("eth_getBalance", [fixture.owner, block]), 16)
    balances = {N.ZERO: str(native)}
    rows = []
    for claim in claims:
        target = fixture.contracts["royalties" if claim["royalty"] else "rewards"]
        data = calldata("claimable(uint256,address)", int(claim["token_id"]),
                        claim["asset"] if claim["asset"] != N.ZERO else "0x" + "0" * 39 + "1")
        if claim["asset"] == N.ZERO:
            data = data[:-64] + "0" * 64
        raw = fixture.rpc.call("eth_call", [{"to": target, "data": data}, block])
        rows.append({**claim, "raw": str(int(raw, 16)), "read_target": target,
                     "read_data": data, "read_block": block})
        asset = claim["asset"]
        if asset not in balances:
            result = fixture.rpc.call("eth_call", [{"to": asset,
                "data": calldata("balanceOf(address)", fixture.owner)}, block])
            balances[asset] = str(int(result, 16))
    return {"header": header, "owner": fixture.owner, "owner_native_balance": str(native),
            "recipient_balances": balances, "claims": rows}


def run_qualification(fixture, output):
    output = Path(output)
    output.mkdir(exist_ok=True)
    manifest = fixture.manifest
    config = N.build_configuration(manifest["contracts"], manifest["assets"],
        chain_id=manifest["chain_id"], deployment_block=manifest["deployment_block"],
        deployment_block_hash=manifest["deployment_block_hash"],
        expected_runtime_pins=manifest["expected_runtime_pins"])
    aggregate = {"schema": 1, "fixture_only": True,
        "fixture_manifest_sha256": N.digest(manifest), "projection_config": config,
        "limits": N.LIMITS, "plans": [], "controls": [], "executions": [],
        "production_stages": [], "fault_cases": [], "production_approved": False,
        "scope": "32 newly activated NFTs, actual65-currency inventory and unchanged normal F6 admission. "
                 "External native runtime genesis, controlled sources/VRF/depth and local fees remain fixture assumptions."}
    def plan(label, claims, *, changed_config=None, control=None, description=None, negative=False):
        header = fixture.rpc.call("eth_getBlockByNumber", ["latest", False])
        payload = {"action": "claim", "wallet": fixture.owner, "claims": copy.deepcopy(claims)}
        exact_wire_start = len(fixture.rpc.records)
        record = N.qualify_plan(fixture.rpc.call, changed_config or config, payload,
            clock_timestamp=int(header["timestamp"], 16), label=label,
            control=control, control_description=description)
        record["fixture_wire_start"] = exact_wire_start
        record["fixture_wire_end"] = len(fixture.rpc.records)
        aggregate["controls" if negative else "plans"].append(record)
        save(output / (label + ".json"), record)
        announce({"stage": label, "error": record.get("error"),
            "rpc_count": record["rpc_count"], "elapsed_seconds": record["elapsed_seconds"],
            "next_batch_count": len(record.get("result", {}).get("next_batch", {}).get("claim_operations", []))
                if record.get("result", {}).get("next_batch") else 0})
        return record
    def execute(record, label):
        result = record.get("result")
        if result is None or result["next_batch"] is None:
            raise ValueError("An actual fresh normal unsigned draft is required")
        draft = result["next_batch"]
        claims = [{key: row[key] for key in ("token_id", "asset", "royalty")}
                  for row in draft["claim_operations"]]
        before = _snapshot(fixture, claims)
        transaction = draft["transaction"]
        if transaction["from"] != fixture.owner or transaction["to"] != fixture.contracts["claim_router"]:
            raise ValueError("Exact fixture owner and fixed claim router required")
        sent = fixture.send(label, transaction["to"], transaction["data"],
            value=int(transaction["value"], 16), cap=N.CAP, padding=2000)
        after = _snapshot(fixture, claims)
        row = {"label": label, "plan_label": record["label"],
               "transaction": sent, "before": before, "after": after}
        aggregate["executions"].append(row)
        save(output / (label + ".json"), row)
        if any(int(item["raw"]) != 0 for item in after["claims"]):
            raise AssertionError("Confirmed selected rights did not drain exactly once")
        return row
    def start_plan(label, claims, **kwargs):
        nonlocal wire_start
        wire_start = len(fixture.rpc.records)
        return plan(label, claims, **kwargs)
    wire_start = 0
    original = [dict(token_id=str(identifier), asset=N.ZERO, royalty=royalty)
                for identifier in fixture.ids[:16] for royalty in (False, True)]
    if len(original) != 32:
        raise ValueError("Exactly32 explicit mixed claims on16 newly activated NFTs required")
    baseline = start_plan("baseline-full32", original)
    selected = baseline
    if baseline.get("error", {}).get("type") == "WorkLimit":
        before_pins = baseline["production_source_sha256"]
        baseline_source = (ROOT / "frontend_api/claim_planner.py").read_bytes()
        with (output / "claim_planner.baseline.py.txt").open("xb") as stream:
            stream.write(baseline_source)
        announce({"stage": "awaiting_root_resource_decision", "marker": str(output / "CONTINUE.json"),
                  "baseline_error": baseline["error"], "maximum_wait_seconds": 180})
        deadline = time.monotonic() + 180
        marker = output / "CONTINUE.json"
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.25)
        decision = json.loads(marker.read_text()) if marker.exists() else {"action": "continue_current_source", "bounded_wait_elapsed": True}
        action = decision.get("action")
        if action == "reload_changed_planner":
            current = N.source_pins()
            expected = decision.get("approved_claim_planner_sha256")
            if current["frontend_api/claim_planner.py"] != expected or current == before_pins:
                raise ValueError("Root-approved changed planner pin required before reload")
            if any(current[name] != before_pins[name] for name in before_pins if name != "frontend_api/claim_planner.py"):
                raise ValueError("Resource follow-up may change only the reviewed planner")
            import frontend_api.claim_planner as planner_module
            importlib.invalidate_caches()
            importlib.reload(planner_module)
            aggregate["production_stages"].append({"kind": "root_approved_resource_followup",
                "decision": decision, "before": before_pins, "after": current,
                "old_request_completed_before_reload": True, "planner_module_reloaded": True})
            selected = start_plan("optimized-full32", original)
        elif action == "continue_current_source":
            if N.source_pins() != before_pins:
                raise ValueError("Unapproved production source change")
            aggregate["production_stages"].append({"kind": "smaller_explicit_selection", "decision": decision})
            selected = start_plan("bounded-prefix16", original[:16])
        else:
            raise ValueError("Unknown resource follow-up decision")
    if selected.get("error") or selected.get("result", {}).get("next_batch") is None:
        raise ValueError("Full admission did not publish a bounded fresh prefix")
    execute(selected, "claim-confirmed-prefix")
    remainder = start_plan("fresh-original32-after-prefix", original)
    if remainder.get("error"):
        raise ValueError("Fresh original selection did not recover remaining funded entries")
    if remainder["result"]["next_batch"] is not None:
        execute(remainder, "claim-confirmed-remainder")
        drained = start_plan("fresh-original32-after-confirmation", original)
    else:
        drained = remainder
    if drained.get("error") or drained["result"]["next_batch"] is not None or any(
            row["status"] != "zero" for row in drained["result"]["entries"]):
        raise AssertionError("Confirmed original32 claims are not all independently zero")
    # A new still-funded original-currency entry permits actual final preparation
    # controls after native claims have drained, without minting or reallocating.
    healthy = dict(token_id=str(fixture.ids[0]), asset=fixture.royalty_tokens[0], royalty=True)
    healthy_baseline = start_plan("normal-funded-currency-control-baseline", [healthy])
    if healthy_baseline.get("error") or healthy_baseline["result"]["next_batch"] is None:
        raise AssertionError("Still-funded healthy currency must prepare normally")
    wrong_pin = start_plan("normal-only-helper-runtime-refusal", [healthy],
        changed_config=N.runtime_pin_control(config), negative=True)
    if not wrong_pin.get("error"):
        raise AssertionError("Altered normal-only helper runtime pin was admitted")
    control, description = N.scalar_control(config, "access", "isSealed()", 0, occurrence=1)
    unsealed = start_plan("intercepted-unsealed-refusal", [healthy], control=control,
        description=description, negative=True)
    signature = calldata("canonicalSettling()")
    occurrences = sum(row["requests"][0]["method"] == "eth_call" and
        row["requests"][0]["params"][0] == {"to": config["contracts"]["access"]["address"], "data": signature}
        for row in healthy_baseline["rpc_wire"])
    if occurrences < 3:
        raise AssertionError("Expected initial, trial and fresh-final lifecycle reads")
    control, description = N.scalar_control(config, "access", "canonicalSettling()", 1, occurrence=occurrences)
    final = start_plan("intercepted-final-lifecycle-refusal", [healthy], control=control,
        description=description, negative=True)
    if any(not record.get("error") or record["interception_matches"] != 1 for record in (unsealed, final)):
        raise AssertionError("A negative lifecycle observation released a draft")
    # TaxToken is selected LAST so an opaque full-batch refusal must never be
    # described as a successful earlier prefix or an atomically partial payout.
    taxed = dict(token_id=str(fixture.ids[0]), asset=fixture.royalty_tokens[63], royalty=True)
    before_fault = _snapshot(fixture, [healthy, taxed])
    fault_plan = start_plan("tax-last-fresh-healthy-prefix", [healthy, taxed])
    after_fault = _snapshot(fixture, [healthy, taxed])
    if before_fault != after_fault:
        raise AssertionError("Read-only refused mixed selection changed financial state")
    result = fault_plan.get("result")
    if result is None or result["next_batch"] is None or len(result["next_batch"]["claim_operations"]) != 1:
        raise AssertionError("Healthy isolated prefix was not prepared after opaque mixed refusal")
    if result["next_batch"]["claim_operations"][0]["asset"] != healthy["asset"]:
        raise AssertionError("Tax-last selection produced an unexpected next batch")
    if len(result["remaining_claims"]) != 1 or result["remaining_claims"][0]["asset"] != taxed["asset"]:
        raise AssertionError("Unresolved taxed-currency entitlement disappeared")
    aggregate["fault_cases"].append({"label": "taxed-last-atomic-simulation-refusal",
        "plan_label": fault_plan["label"], "before": before_fault, "after": after_fault,
        "classification": "opaque execution refusal; selected TaxToken fixture, not generic token diagnosis"})
    execute(fault_plan, "claim-confirmed-healthy-currency-prefix")
    tax_only = start_plan("tax-only-remains-unavailable", [taxed])
    if tax_only.get("error") or tax_only["result"]["next_batch"] is not None or len(tax_only["result"]["remaining_claims"]) != 1:
        raise AssertionError("Taxed original-currency right was lost or falsely made executable")
    aggregate["closing_claims"] = _snapshot(fixture, [healthy, taxed])
    save(output / "qualification.json", aggregate)
    announce({"stage": "full_normal_claim_qualification_complete", "plans": len(aggregate["plans"]),
              "controls": len(aggregate["controls"]), "actual_claim_transactions": len(aggregate["executions"])})
    return aggregate
