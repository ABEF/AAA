"""Only the missing changed-planner claim/continuation after pending-clock review."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
N = module("late_tax_followup_normal", "normal_admission.py")
C = module("late_tax_followup_snapshots", "campaign_checks.py")
NEW_PLANNER = "7a3e720b97acf38e2ebfc7f4dde7a5912852a3eabd0a39629546aa1097cab810"


def run_late_followup(fixture, output):
    output = Path(output)
    output.mkdir(exist_ok=True)
    if N.source_pins()["frontend_api/claim_planner.py"] != NEW_PLANNER:
        raise ValueError("Exact reviewed first-success planner required")
    manifest = fixture.manifest
    config = N.build_configuration(manifest["contracts"], manifest["assets"],
        chain_id=manifest["chain_id"], deployment_block=manifest["deployment_block"],
        deployment_block_hash=manifest["deployment_block_hash"],
        expected_runtime_pins=manifest["expected_runtime_pins"])
    original = [dict(token_id=str(identifier), asset=fixture.royalty_tokens[0], royalty=True)
                for identifier in fixture.ids[:31]]
    original.append(dict(token_id=str(fixture.ids[0]), asset=fixture.royalty_tokens[63], royalty=True))
    aggregate = {"schema": 1, "kind": "late_tax32_missing_execution_followup",
        "fixture_only": True, "fixture_manifest_sha256": N.digest(manifest),
        "projection_config": config, "limits": N.LIMITS,
        "original_selection": original, "plans": [], "controls": [], "executions": [],
        "production_stages": [], "no_population_repeat": True, "production_approved": False,
        "scope": "Separate exact-state restore; only the missing admitted prefix execution and fresh unsigned remainder. "
                 "Prior old-source resource failure and changed-source normal request remain in the03 records."}
    def plan(label, claims):
        header = fixture.rpc.call("eth_getBlockByNumber", ["latest", False])
        start = len(fixture.rpc.records)
        record = N.qualify_plan(fixture.rpc.call, config,
            {"action": "claim", "wallet": fixture.owner, "claims": copy.deepcopy(claims)},
            clock_timestamp=int(header["timestamp"], 16), label=label)
        record["fixture_wire_start"], record["fixture_wire_end"] = start, len(fixture.rpc.records)
        aggregate["plans"].append(record)
        C.save(output / (label + ".json"), record)
        C.announce({"stage": label, "error": record.get("error"), "rpc_count": record["rpc_count"],
                    "elapsed_seconds": record["elapsed_seconds"]})
        if record.get("error"):
            raise ValueError("Changed-source continuation failed normal request admission")
        return record
    chosen = plan("late-tax32-followup-admitted-prefix", original)
    result = chosen["result"]
    if result["next_batch"] is None:
        raise AssertionError("A fresh healthy prefix must remain executable")
    operations = result["next_batch"]["claim_operations"]
    if len(operations) != 16 or any(row["asset"] != fixture.royalty_tokens[0] for row in operations):
        raise AssertionError("Expected conservative16 healthy original-currency claims")
    if [row["selection_index"] for row in result["remaining_claims"]] != list(range(16, 32)):
        raise AssertionError("Every unselected entry including the last currency must remain explicit")
    claims = [{key: row[key] for key in ("token_id", "asset", "royalty")} for row in operations]
    before = C._snapshot(fixture, claims)
    tx = result["next_batch"]["transaction"]
    sent = fixture.send("late-tax32-confirmed-healthy16", tx["to"], tx["data"],
        value=int(tx["value"], 16), cap=N.CAP, padding=2000)
    after = C._snapshot(fixture, claims)
    if any(int(row["raw"]) != 0 for row in after["claims"]):
        raise AssertionError("Confirmed healthy prefix rights did not drain")
    execution = {"label": "late-tax32-confirmed-healthy16", "plan_label": chosen["label"],
                 "transaction": sent, "before": before, "after": after}
    aggregate["executions"].append(execution)
    C.save(output / "late-tax32-confirmed-healthy16.json", execution)
    remainder = [{key: row[key] for key in ("token_id", "asset", "royalty")}
                 for row in result["remaining_claims"]]
    fresh = plan("late-tax32-followup-fresh-remainder16", remainder)
    if (fresh["result"]["next_batch"] is None or
            not any(row["asset"] == fixture.royalty_tokens[63] for row in fresh["result"]["remaining_claims"])):
        raise AssertionError("Fresh unsigned remainder lost the unresolved last currency")
    aggregate["closing_original_claims"] = C._snapshot(fixture, original)
    closing = aggregate["closing_original_claims"]["claims"]
    if any(int(row["raw"]) != 0 for row in closing[:16]) or any(int(row["raw"]) <= 0 for row in closing[16:]):
        raise AssertionError("The selected16 and retained16 original rights are inconsistent")
    C.save(output / "qualification.json", aggregate)
    C.announce({"stage": "late_tax32_missing_continuation_complete",
                "actual_claim_transactions": 1, "retained_original_entries": 16,
                "fresh_unsigned_next_batch": len(fresh["result"]["next_batch"]["claim_operations"])})
    return aggregate
