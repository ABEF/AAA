"""Independent, offline review of curated c813/c814 outputs; stdout only.

No application/private-checker imports, RPC, subprocesses, signer reads, tests or
server actions. Private byte/identity facts are explicitly provenance-bound to
the checker that inspected the actual private files during c814, not recreated
from the deliberately incomplete public projections.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
HEAD = "5662a81ad9c9c5953d3578974e0c5840d626ba97"
PINS = {
    "keeper/monitor.py": "90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f",
    "keeper/recovery_bundle.py": "fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268",
    "scripts/keeper-recovery.py": "450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf",
}
MODEL_SHA = "0b16b4d06a3743a4255e3ca46f583bc6330b72b95d947caae310c46b76aa3a8e"
PRIVATE_CHECKER_SHA = "0116857d1b13b57971ce90bd8c8dc5536e675fb0de93da616adf2e0859b9618b"
PRIVATE_CHECKS = {
    "exact_HEAD_and_thirteen_daemon_sources_with_reviewed_tool_sources",
    "private_actual_configuration_diff_is_exactly_three_runtime_paths_original_preserved",
    "exact_private_pending_backup_restore_bytes_and_unsigned_manifest_plan_provenance",
    "root_fence_acknowledgment_and_two_unsigned_process_results_with_unreadable_signer_directory",
    "independent_canonical_receipt_fee_day_anchor_nonce_once_and_documented_dry_scheduler_delta",
    "actual_unsigned_health_transition_and_all_three_financial_vectors_with_original_source_readback",
}
ARTIFACTS = {}


def need(condition, label):
    if not condition:
        raise ValueError("Saved-evidence review refused: " + label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def enc(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def pairs(rows):
    result = {}
    for key, value in rows:
        need(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def constant(_):
    raise ValueError("Saved-evidence review refused: nonfinite JSON")


def read(relative):
    relative = str(relative).replace("\\", "/")
    need(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "fixed local path")
    path = ROOT / relative
    need(path.is_file() and not path.is_symlink(), "regular curated file")
    raw = path.read_bytes()
    need(0 < len(raw) <= 2 * 1024 * 1024, "bounded saved artifact")
    ARTIFACTS[relative] = {"bytes": len(raw), "sha256": sha(raw)}
    return raw


def load(relative):
    value = json.loads(read(relative).decode("utf8"), object_pairs_hook=pairs, parse_constant=constant)
    need(type(value) is dict, "saved object")
    return value


def quantity(value):
    need(type(value) is str and re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})", value), "hex quantity")
    return int(value, 16)


def same(a, b, label):
    need(enc(a) == enc(b), label)


def main():
    checks = []

    def passed(label):
        checks.append({"check": label, "passed": True})

    for attempt in ("c813", "c814"):
        curation = load("CURATION_" + attempt.upper() + ".json")
        need(curation["original_files_modified"] is False and
             curation["private_configs_journals_signers_included"] is False, "curation scope")
        for relative, descriptor in curation["copied_files"].items():
            raw = read(relative)
            same({"bytes": len(raw), "sha256": sha(raw)},
                 {key: descriptor[key] for key in ("bytes", "sha256")}, "curated raw bytes")
            if "original_sha256" in descriptor:
                need(descriptor["original_sha256"] == sha(raw), "original curated bytes unchanged")
    passed("both_curation_inventories_match_saved_raw_bytes")

    prefix = "evidence/c814/"
    prep = "preparation/c814/"
    build = load(prep + "BUILD_RECEIPT.json")
    pins = load(prep + "PARENT_REVIEW_PINS.json")
    approval = load(prefix + "PARENT_PREEXECUTION_APPROVAL.json")
    same(approval["pins"], pins, "reviewed pre-execution helper pins")
    for name, digest in pins.items():
        if name.endswith(".py"):
            need(sha(read(prep + name)) == digest, "actual helper source pin")
    need(build["source_base"] == HEAD and build["production_source_members"] == 193 and
         build["helpers"]["model_service.py"]["sha256"] == MODEL_SHA and
         build["helpers"]["independent_private.py"]["sha256"] == PRIVATE_CHECKER_SHA,
         "reviewed current source and helper build")
    manifest = load(prep + "SOURCE_MANIFEST.json")
    need(manifest["source_head"] == HEAD and len(manifest["members"]) == 193 and
         sha(read(prep + "SOURCE_MANIFEST.json")) == build["source_manifest_sha256"], "source manifest")
    for name, digest in PINS.items():
        need(sha((REPO / name).read_bytes()) == digest and
             manifest["members"][name]["sha256"] == digest, "production source remains pinned")
    passed("prepared_helpers_manifest_and_actual_current_core_sources_match_reviewed_pins")

    old = load("evidence/c813/model-RESULT.json")
    need(old["success"] is False and old["shared_RPC_requests"] == 2354 and
         "final_financial_error" in old and "independent_review_error" in old,
         "original campaign remains NONPASS")
    need(load("evidence/c813/model-COMPLETE.json")["success"] is True and
         not (ROOT / "evidence/c813/case-FINANCIAL_FINAL.json").exists() and
         not (ROOT / "evidence/c813/model-INDEPENDENT.json").exists(),
         "early COMPLETE is insufficient and original gaps remain visible")
    passed("original_c813_NONPASS_and_missing_final_vectors_preserved")

    ready = load(prefix + "model-READY.json")
    pending = load(prefix + "model-PENDING_READY.json")
    restored = load(prefix + "model-RESTORE_READY.json")
    evidence = load(prefix + "case-EVIDENCE.json")
    source = load(prefix + "case-SOURCE_PRESERVED.json")
    private = load(prefix + "model-INDEPENDENT.json")
    result = load(prefix + "model-RESULT.json")
    complete = load(prefix + "model-COMPLETE.json")
    need(private["success"] is True and private["verifier_sha256"] == PRIVATE_CHECKER_SHA and
         len(private["checks"]) == 6 and
         {row["check"] for row in private["checks"]} == PRIVATE_CHECKS and
         all(row["passed"] is True for row in private["checks"]), "six actual private checker partitions")
    for obj in (result, complete):
        need(obj["success"] is True and obj["final_financial_capture_complete"] is True and
             obj["post_inclusion_financial_unchanged"] is True and obj["independent_private_review_passed"] is True,
             "final capture and review precede successful completion")
    need(result["shared_RPC_requests"] == 2353 <= 6000 and
         result["raw_attempts"] == result["raw_forwarded"] == 1 and
         result["cleanup"]["stopped"] is True, "bounded single-send actual outcome")
    passed("c814_completed_final_capture_and_six_private_check_partitions")

    accepted = evidence["known_hash"]
    for obj in (pending, restored, result, complete):
        need(obj["accepted_hash"] == accepted, "same known transaction identity")
    need(accepted != old["accepted_hash"], "fresh affected fixture, not original transaction replay")
    for obj in (ready, evidence, private, result):
        need(obj["source_head"] == HEAD, "source HEAD consistency")
    original_sha = evidence["configuration_raw_sha256"]
    target_sha = evidence["target_configuration_raw_sha256"]
    original_semantic = evidence["configuration_semantic_sha256"]
    target_semantic = evidence["target_configuration_semantic_sha256"]
    need(ready["configuration_sha256"] == pending["configuration_sha256"] ==
         source["configuration_sha256"] == private["original_configuration_raw_sha256"] == original_sha,
         "original raw configuration provenance")
    need(ready["semantic_configuration_sha256"] == original_semantic and
         restored["target_configuration_sha256"] == private["target_configuration_raw_sha256"] == target_sha and
         restored["target_semantic_configuration_sha256"] == target_semantic, "target configuration provenance")
    same(evidence["changed_configuration_keys"], ["health_path", "lock_path", "state_path"], "only runtime path changes")
    same(private["exact_changed_configuration_keys"], evidence["changed_configuration_keys"], "private config diff proof")
    journal_sha = evidence["pending_journal_sha256"]
    need(evidence["restored_journal_sha256"] == pending["journal_sha256"] == restored["journal_sha256"] ==
         source["journal_sha256"] == private["pending_journal_sha256"] ==
         private["restored_before_load_sha256"] == journal_sha, "raw pending/restored identity")
    same(source["node_nonces"], {"latest": 1, "pending": 1}, "actual nonce readback")
    need(all(type(source[k]) is int and source[k] == 1 for k in
             ("raw_attempts", "raw_forwarded", "raw_gateway_attempts", "raw_validated")), "once-only counters")
    need(source["original_configuration_unchanged"] is True and source["original_journal_unchanged"] is True,
         "original source readback")
    same(evidence["bundle_file_names"], ["journal.json", "manifest.json"], "two-file backup")
    same(evidence["restore_file_names"], ["RESTORE_PLAN.json", "keeper-state.json"], "exclusive restore")
    need([r["action"] for r in evidence["tool_runs"]] == ["backup", "verify", "restore"], "three actual CLI actions")
    for row in evidence["tool_runs"]:
        need(row["returncode"] == 0 and row["configuration_sha256"] == original_sha and
             row["signing_enabled"] is False and row["secret_contents_exported"] is False and
             row["digest"] == evidence["restore_plan_sha256" if row["action"] == "restore" else "backup_manifest_sha256"],
             "unsigned CLI results tied to exact pins")
    public_map = {
        "inputs/SOURCE_MANIFEST.json": prep + "SOURCE_MANIFEST.json",
        "source/helpers/independent_private.py": prep + "independent_private.py",
        "control/FENCED.json": prefix + "native-FENCED.json",
        "control/RECOVERY_COMPLETE.json": prefix + "native-RECOVERY_COMPLETE.json",
        "control/DRY_COMPLETE.json": prefix + "native-DRY_COMPLETE.json",
        "runtime/run-001/model/SETTLED.json": prefix + "model-SETTLED.json",
        "runtime/run-001/model/DRY.json": prefix + "model-DRY.json",
    }
    for name in ("CANONICAL", "EVIDENCE", "SOURCE_PRESERVED", "FINANCIAL_INITIAL", "FINANCIAL_INCLUDED", "FINANCIAL_FINAL"):
        public_map["runtime/run-001/model/supervisor/" + name + ".json"] = prefix + "case-" + name + ".json"
    for original_name, relative in public_map.items():
        raw = read(relative)
        same(private["artifacts"][original_name], {"bytes": len(raw), "sha256": sha(raw)}, "private checker/public copy raw binding")
    for name, digest in {
        "PENDING.json": journal_sha, "RESTORED_BEFORE_LOAD.json": journal_sha,
        "actor/state.json": journal_sha, "bundle-001/journal.json": journal_sha,
        "ORIGINAL_CONFIG.json": original_sha, "actor/config.json": original_sha, "TARGET_CONFIG.json": target_sha,
        "bundle-001/manifest.json": evidence["backup_manifest_sha256"],
        "restore-001/RESTORE_PLAN.json": evidence["restore_plan_sha256"],
    }.items():
        need(private["artifacts"]["runtime/run-001/model/supervisor/" + name]["sha256"] == digest, "private digest equality proof")
    passed("public_identity_chain_binds_raw_private_restore_and_three_unsigned_CLI_results")

    canonical = load(prefix + "case-CANONICAL.json")
    tx, receipt, block, head = (canonical[k] for k in ("transaction_without_signature", "receipt", "receipt_block", "head"))
    need(canonical["accepted_hash"] == tx["hash"] == receipt["transactionHash"] == accepted and
         tx["blockHash"] == receipt["blockHash"] == block["hash"] and
         quantity(tx["blockNumber"]) == quantity(receipt["blockNumber"]) == quantity(block["number"]), "canonical transaction inclusion")
    need(quantity(head["number"]) - quantity(block["number"]) + 1 == canonical["confirmations"] == 12,
         "twelve canonical confirmations")
    need(quantity(tx["type"]) == 2 and quantity(tx["chainId"]) == 4663 and quantity(tx["nonce"]) == 0 and
         quantity(tx["value"]) == 0 and tx["from"] == ready["sender"] and quantity(receipt["status"]) == 1,
         "actual stock transaction identity")
    need(not ({"r", "s", "v", "yParity", "raw"} & set(tx)), "no transaction signature disclosure")
    data = tx["input"]
    need(len(data) == 138 and data.startswith("0x6cae7bf7"), "exact standalone harvest calldata")
    bucket, deadline = int(data[10:74], 16), int(data[74:], 16)
    timestamp = quantity(block["timestamp"])
    need(timestamp <= deadline, "execution occurred before reviewed deadline")
    execution_price = min(quantity(tx["maxFeePerGas"]), quantity(block["baseFeePerGas"]) + quantity(tx["maxPriorityFeePerGas"]))
    gas_used = quantity(receipt["gasUsed"])
    need(receipt.get("l1Fee") in (None, "0x0"), "included-fee fixture, no separate L1 addend")
    paid = gas_used * execution_price
    review = pending["pending_fee_review"]
    need(type(review["schema"]) is int and review["schema"] == 1 and review["receipt_fee_policy"] == "included" and
         review["gas_limit"] == quantity(tx["gas"]) <= 24000000 and
         review["max_fee_per_gas"] == quantity(tx["maxFeePerGas"]) and review["l1_fee_allowance_wei"] == 0 and
         review["maximum_cost_wei"] == review["gas_limit"] * review["max_fee_per_gas"] and
         gas_used <= review["gas_limit"] and paid <= review["maximum_cost_wei"], "captured fee review not reinterpreted")
    settled = load(prefix + "model-SETTLED.json")
    financial_state = settled["recovery_fields"]
    same(financial_state["receipt_anchor"], {"number": quantity(block["number"]), "hash": block["hash"],
         "timestamp": timestamp, "nonce": 0}, "exact canonical nonce/cost anchor")
    day = dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date().isoformat()
    same(financial_state["spent"], {day: paid}, "cost counted once on canonical UTC day")
    same(financial_state["last"], {"harvest:" + str(bucket): timestamp}, "harvest clock uses inclusion")
    need(financial_state["pending"] is None and type(financial_state["next_nonce"]) is int and
         financial_state["next_nonce"] == 1 and settled["paid_wei"] == private["paid_wei"] == paid and
         private["gas_used"] == gas_used and private["canonical_execution_price_wei"] == execution_price,
         "receipt recovery clears pending and accounts exact cost once")
    fee_observation = financial_state["last_fee_observation"]
    need(fee_observation["transaction"] == accepted and fee_observation["cost_wei"] == paid and
         fee_observation["execution_price_wei"] == execution_price and fee_observation["gas_used"] == gas_used,
         "booked observation bound to canonical transaction")
    passed("independent_canonical_type2_fee_nonce_harvest_clock_and_spend_arithmetic")

    dry = load(prefix + "model-DRY.json")
    for obj, expected_status, exit_status in ((settled, "degraded", 1), (dry, "dry_run_v2", 0)):
        health = obj["health"]
        need(obj["actual_exit_status"] == exit_status and health["status"] == expected_status and
             health["pending"] is False and health["live"] is False and
             health["configuration_sha256"] == target_semantic, "actual unsigned phase and target config")
    need(settled["health"]["rebalance_confirmation_health"]["policy"]["state"] == "pending_recovery" and
         dry["health"]["rebalance_confirmation_health"]["policy"]["state"] == "observed_this_cycle",
         "metadata is refreshed by the fresh cycle")
    need(set(dry["changed_scheduler_keys"]) <= {"conversion_turn", "bucket_cursor"} and
         dry["conversion_turn_after"] == (dry["conversion_turn_before"] + 1) % 3 and dry["bucket_cursor_after"] == 1,
         "legitimate scheduler advance, not full journal byte equality")
    need(settled["journal_sha256"] == private["settled_journal_sha256"] and
         dry["journal_sha256"] == private["dry_journal_sha256"], "financial fields preserved across documented scheduling")
    observed = dry["health"]["rebalance_confirmation_health"]["policy"]["last_observed"]
    need(observed["block_hash"] == head["hash"] and observed["block_number"] == quantity(head["number"]) and
         observed["continuous_price_proof"] is False and observed["threshold_bps"] == 8500 and
         observed["duration_seconds"] == 600 and observed["maximum_gap_seconds"] == 300,
         "fresh metadata preserves actual policy without claiming continuous observations")
    need(len(observed["source_files_sha256"]) == 13, "thirteen source identity files")
    for name, digest in observed["source_files_sha256"].items():
        need(manifest["members"][name]["sha256"] == digest and
             private["artifacts"]["source/contracts/" + name]["sha256"] == digest,
             "health and private source digest evidence agrees")
    passed("degraded_receipt_recovery_then_fresh_unsigned_dry_cycle_with_legitimate_scheduler_delta")

    vectors = [load(prefix + "case-FINANCIAL_" + phase + ".json") for phase in ("INITIAL", "INCLUDED", "FINAL")]
    for field in ("rights", "physical"):
        same(vectors[0][field], vectors[1][field], "unchanged initial/included " + field)
        same(vectors[1][field], vectors[2][field], "unchanged included/final " + field)
    same(vectors[1], vectors[2], "all post-inclusion financial and Vault balance outputs unchanged")
    need(len(vectors[2]["rights"]) == 2 and vectors[2]["physical"]["secondary"] == 0,
         "two-NFT, one-main fixture scope")
    need(tx["to"] == "0x" + vectors[2]["physical"]["owner"][-40:], "Vault owns actual main position")
    for phase, vector in zip(("initial", "included", "final"), vectors):
        need(private["financial_" + phase + "_sha256"] == sha(enc(vector)), "semantic financial vector digest")
        for asset in vector["money"].values():
            need(sum(sum(row) for row in asset["claims"]) == asset["liabilities"], "fixture direct and collective liabilities reconcile")
    passed("actual_three_financial_vectors_preserve_rights_principal_and_existing_claim_liabilities")

    lab = "/opt/popl-ubuntu-backup-recovery-20261126-c814"
    argv = ["/usr/bin/python3", "-m", "keeper.monitor", "--config", lab + "/runtime/run-001/model/supervisor/TARGET_CONFIG.json", "--once"]
    fence = load(prefix + "native-SOURCE_FENCE.json")
    need(fence["explicit_systemctl_stop_completed"] is True and fence["keeper_fenced_empty"] is True and
         fence["automatic_restart_inhibited"] is True and fence["accepted_hash"] == accepted and
         fence["journal_sha256"] == journal_sha, "source signer fenced before backup")
    source_unit = lab[5:] + "-keeper.service"
    need(fence["native_snapshot"]["units"][source_unit]["cgroup"]["pids"] == [], "native source group empty")
    invocations = []
    for name, exit_status, health_status, journal_digest in (
            ("RECOVERY", 1, "degraded", settled["journal_sha256"]),
            ("DRY", 0, "dry_run_v2", dry["journal_sha256"])):
        native = load(prefix + "native-" + name + "_RECEIPT.json")
        marker = load(prefix + "native-" + name + "_COMPLETE.json")
        same(native["marker"], marker, "root marker copied exactly")
        same(marker["direct_exec_argv"], argv, "actual unsigned direct process argv")
        same(native["launch"]["direct_exec_argv"], argv, "native launch argv")
        properties = native["native"]["properties"]
        need(marker["actual_exit_status"] == exit_status and marker["signing_enabled"] is False and
             marker["accepted_hash"] == accepted and properties["ExecMainStatus"] == str(exit_status) and
             properties["ExecMainCode"] == "1" and properties["MainPID"] == "0" and
             "argv[]=" + " ".join(argv) + " ;" in properties["ExecStart"], "kernel-reported unsigned process exit")
        need(native["native"]["cgroup"]["pids"] == [] and native["signer_directory_mode"] == "0000" and
             native["target_configuration_sha256"] == target_sha and native["target_journal_sha256"] == journal_digest and
             native["stock_health"]["status"] == health_status, "closed process/signer/readback evidence")
        invocations.append(properties["InvocationID"])
    need(len(set(invocations)) == 2, "two separate unsigned process invocations")
    stopped = load(prefix + "native-FINAL_STOP.json")
    need(stopped["all_owned_units_stopped"] is True and stopped["only_fixed_native_units_controlled"] is True and
         stopped["native_status"]["old_processes"] == [], "actual final cleanup")
    units = stopped["native_status"]["units"]
    need(set(units) == {lab[5:] + "-" + role + ".service" for role in ("keeper", "model", "resolve")}, "fixed three units only")
    for unit in units.values():
        need(unit["cgroup"]["pids"] == [] and unit["cgroup"]["processes"] == [] and
             unit["properties"]["MainPID"] == "0" and unit["properties"]["ActiveState"] in ("inactive", "failed"), "all owned groups empty")
    for attempt in ("C813", "C814"):
        host = load("verification/HOST_" + attempt + ".json")
        need(host["success"] is True and host["existing_units_checked"] == 5 and
             host["non_ambient_difference_count"] == 0 and all(x is True for x in host["checks"].values()),
             "separate authorized original-host comparison")
    passed("native_unsigned_invocations_fencing_final_empty_groups_and_separate_host_comparison")

    continuation = load(prefix + "CONTINUATION_RESULT.json")
    need(continuation["success"] is True and continuation["saved_only_continuation_after_client_interruption"] is True and
         continuation["original_server_scenario_restarted"] is False and continuation["transaction_resubmitted"] is False and
         continuation["original_orchestration_rewritten"] is False and continuation["private_independent_check_rows"] == 6 and
         continuation["new_server_actions_for_count_correction"] == 0,
         "saved-only continuation and offline six-row correction remain explicit")
    passed("interrupted_client_continuation_preserves_originals_without_scenario_or_transaction_replay")

    return {"schema": 1, "success": True, "review": "independent_saved_public_evidence",
            "source_head": HEAD, "checks": checks, "private_checker_rows": 6,
            "private_checker_rerun": False, "application_imports": 0, "tests_run": 0, "server_actions": 0,
            "network_calls": 0, "gas_used": gas_used, "canonical_execution_price_wei": execution_price,
            "paid_wei": paid, "shared_RPC_requests": result["shared_RPC_requests"],
            "original_c813_status": "NONPASS", "c814_status": "finite_same_host_PASS",
            "private_evidence_scope": "Exact config/journal/manifest/plan facts bind to the pinned checker executed once on actual private files; public hashes alone cannot reconstruct these files.",
            "host_preservation_scope": "Native owned-group outputs reviewed directly; original five-service preservation is a separately saved root comparison with raw host details withheld.",
            "limitations": ["same host, not off-host or split-brain fencing", "known-hash pending harvest, not hashless recovery",
                            "two existing NFTs, one main LP; no new constructor, Entry, hybrid, reward-conversion or market qualification",
                            "fee-empty harvest preserves existing financial rights; this does not prove a new 80/10/5/5 receipt split",
                            "no power-loss, sustained-daemon, public-provider, production adoption or release approval"],
            "production_approved": False, "artifacts": dict(sorted(ARTIFACTS.items())),
            "reviewer_sha256": sha(Path(__file__).read_bytes())}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
