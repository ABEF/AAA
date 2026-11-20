"""Offline second-reader of the NEW maximum-state conversion/claim evidence.

No nodes, compilation, signing or mutable source are accepted. Recompute
accounting from captured raw words; reconcile receipts to original RPC responses
and submitted transaction envelopes, rather than trusting a reported pass.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from zzz_ops.abi import keccak256

ZERO = "0x" + "00" * 20
CLAIMED = "0x" + keccak256(b"Claimed(uint256,address,address,uint256)").hex()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    path = Path(path)
    raw = path.read_bytes()
    require(len(raw) <= 128 * 1024 * 1024, "Evidence file bound")
    decoded = gzip.decompress(raw) if path.suffix == ".gz" else raw
    require(len(decoded) <= 256 * 1024 * 1024, "Expanded evidence bound")
    return json.loads(decoded)


def linked(ref, root):
    path = Path(ref["path"]).resolve()
    if not path.is_relative_to(root):
        publication = load(root / "PUBLISHED_MANIFEST.json")
        original = Path(publication["original_root"]).resolve()
        require(path.is_relative_to(original), "Evidence pointer outside original captured root")
        path = (root / path.relative_to(original)).resolve()
    require(path.is_relative_to(root), "Evidence pointer escaped campaign directory")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"], "Linked evidence changed")
    return load(path)


def words(raw):
    require(isinstance(raw, str) and raw.startswith("0x") and (len(raw)-2) % 64 == 0,
            "Malformed raw ABI words")
    return [int(raw[i:i+64], 16) for i in range(2, len(raw), 64)]


def state(body):
    values = {row["key"]: words(row["raw"]) for row in body["raw_reads"]}
    require(len(values) == len(body["raw_reads"]) and values == body["values"], "Decoded state differs")
    lp = {key: value for key, value in values.items() if key.startswith("lp:")}
    require(len(lp) == 2000, "Not 1000 NFTs by two LP assets")
    assets = {key.rsplit(":", 1)[1] for key in lp}
    require(len(assets) == 2 and ZERO in assets, "Unexpected LP asset set")
    for asset in assets:
        total = sum(sum(value) for key, value in lp.items() if key.endswith(":" + asset))
        liability = values["reward:liabilities:" + asset][0]
        require(total == liability, "Whole NFT rights do not sum to liability")
        balance = (body["native_balances"]["reward"] if asset == ZERO
                   else values["balance:reward:" + asset][0])
        require(balance == liability + values["reward:orphaned:" + asset][0], "LP reward backing mismatch")
    require(len(body["physical"]) == 2 and all(row["liquidity"] > 0 for row in body["physical"].values()),
            "Maximum-state physical positions missing")
    return values


def verify(root):
    root = root.resolve()
    summary = load(root / "SUMMARY.json")
    completion = summary.get("phase") == "completion"
    require(summary.get("status") != "campaign_failed", "Campaign did not complete its captured matrix")
    failures = summary.get("failures", [])
    if failures:
        failure = load(root / "failures/unsigned-planner.json")
        require(len(failures) == 1 and failures[0] ==
                "unsigned-planner: WorkLimit: Request work limit: deadline" and
                failure["error_type"] == "WorkLimit" and failure["error"] ==
                "Request work limit: deadline", "Unexpected unresolved campaign failure")
    fixture = load(root / "fixture/FIXTURE.json")
    require(fixture["owned_node_stopped"] is True and not fixture.get("exception"), "Owned node not cleanly stopped")
    receipts = load(root / "fixture/SETUP_AND_SCENARIO_RECEIPTS.json")
    raw_rpc = load(root / "fixture/RPC.json.gz")
    # Preserve each individual response from both singleton and batch records.
    # A summarized copy does not count as another observation.
    wire_results, call_outputs = [], set()
    sent = {}
    for row in raw_rpc:
        responses = row.get("response", [])
        responses = responses if isinstance(responses, list) else [responses]
        by_id = {value["id"]: value for value in responses}
        for request in row["requests"]:
            response = by_id[request["id"]]
            if "result" not in response:
                continue
            value = response["result"]
            wire_results.append(value)
            if request["method"] == "eth_call":
                tx = request["params"][0]
                block = json.dumps(request["params"][1], sort_keys=True)
                call_outputs.add((tx.get("to"), tx["data"], block, value))
            if request["method"] == "eth_sendTransaction":
                sent[value] = request["params"][0]
    wire_receipts = {row["transactionHash"]: row for row in wire_results
                     if isinstance(row, dict) and "transactionHash" in row and "gasUsed" in row}
    receipt_by_hash = {row["receipt"]["transactionHash"]: row for row in receipts if row.get("receipt")}
    verified_ops, refusals = [], []
    for row in summary["cases"]:
        op = linked(row["artifact"], root)
        if op["status"] != "mined":
            require(op["status"].startswith("refused"), "Unexpected operation status")
            require("receipt" not in op, "Refused review was submitted")
            refusals.append(op["name"])
            continue
        fixture_prefund = op["name"] in ("prefund-eth-converter", "prefund-eth-executor")
        require(op["cap"] in ((500_000,) if fixture_prefund else (12_000_000, 24_000_000)),
                "Qualification cap changed")
        padding = 2500 if op["cap"] == 24_000_000 else 2000
        require(op["padding_bps"] == padding and
                op["padded"] == (op["estimate"] * (10000 + padding) + 9999) // 10000 <= op["cap"],
                "Full estimate headroom was not preserved")
        receipt = op["receipt"]
        require(receipt == wire_receipts.get(receipt["transactionHash"]), "Receipt missing/different on raw wire")
        submitted = receipt_by_hash[receipt["transactionHash"]]
        tx, review = submitted["transaction"], submitted["review"]
        require(review == sent.get(receipt["transactionHash"]), "Submitted envelope missing/different on raw wire")
        require(tx in wire_results, "Mined transaction missing/different on raw wire")
        require(int(receipt["status"], 16) == 1 and int(receipt["gasUsed"], 16) <= op["padded"] and
                int(tx["gas"], 16) == op["padded"] == int(review["gas"], 16), "Mined gas envelope differs")
        require(tx["input"].lower() == op["data"].lower() and tx["from"].lower() == op["sender"].lower()
                and (tx.get("to").lower() if tx.get("to") else None) ==
                    (op.get("to").lower() if op.get("to") else None), "Receipt transaction identity differs")
        require(receipt["blockHash"] == op["mined_header"]["hash"] and
                receipt["blockNumber"] == op["mined_header"]["number"], "Receipt block identity differs")
        verified_ops.append(op["name"])
    assertions, ownership, continuations = [], [], []
    for path in sorted((root / "assertions").glob("*.json*")):
        assertion = load(path)
        if isinstance(assertion, list):
            require(path.name in ("transfer-before-owner.json", "transfer-after-owner.json") and
                    len(assertion) == 1 and assertion[0]["key"] == "owner" and
                    words(assertion[0]["raw"]) == [int(fixture["discovery"]["newcomer"], 16)] and
                    (assertion[0]["to"], assertion[0]["data"], json.dumps("latest"),
                     assertion[0]["raw"]) in call_outputs, "Ownership observation missing/different")
            ownership.append(path.name)
            continue
        before, after = linked(assertion["before"], root), linked(assertion["after"], root)
        b, a = state(before), state(after)
        for snapshot in (before, after):
            block = json.dumps({"blockHash": snapshot["head"]["hash"], "requireCanonical": True}, sort_keys=True)
            require(all((row["to"], row["data"], block, row["raw"]) in call_outputs
                        for row in snapshot["raw_reads"]), "State contains an unobserved EVM read")
        require(b["group"] == a["group"] and before["physical"] == after["physical"], "Principal changed")
        for key in b:
            if key.startswith("fee:"):
                require(a[key] == b[key], "Designated reserve changed")
        if path.name == "PREFIX_SUFFIX_CONTINUATION.json":
            require(completion and len(assertion["ids"]) == 32 and
                    linked(assertion["prefix"], root)["name"] in verified_ops and
                    linked(assertion["suffix"], root)["name"] in verified_ops,
                    "Prefix/suffix does not reference actual accepted operations")
            source = next(key.rsplit(":", 1)[1] for key in b if key.startswith("lp:") and not key.endswith(ZERO))
            require(sum(sum(b[f"lp:{id_}:{source}"]) for id_ in assertion["ids"]) == assertion["source_total"]
                    and all(a[f"lp:{id_}:{source}"] == [0, 0] for id_ in assertion["ids"]) and
                    after["native_balances"]["reward"] - before["native_balances"]["reward"] == assertion["native_output"],
                    "Conversion continuation lost source units or output")
            continuations.append(path.name)
            continue
        op = linked(assertion["operation"], root)
        require(op["name"] in verified_ops, "Accounting assertion lacks actual admitted receipt")
        if assertion["kind"] == "conversion":
            ids = assertion["ids"]
            require(ids == sorted(set(ids)) and 1 <= len(ids) <= 32, "Conversion IDs not sorted unique")
            source = next(key.rsplit(":", 1)[1] for key in b if key.startswith("lp:") and not key.endswith(ZERO))
            total = sum(sum(b[f"lp:{id_}:{source}"]) for id_ in ids)
            output = after["native_balances"]["reward"] - before["native_balances"]["reward"]
            require(total == assertion["source_total"] and output == assertion["output"] > 0, "Conversion deltas differ")
            guard = assertion["financial_guard"]
            floor = max(guard["caller_minimum"], (guard["quote"] * 9900 + 9999) // 10000)
            require(guard["loss_bps"] == 100 and guard["quote"] > 0 and guard["caller_minimum"] > 0 and
                    floor == guard["minimum_output"] <= output and
                    guard["head"]["hash"] == op["head_before"]["hash"] and
                    int(op["mined_header"]["timestamp"], 16) <= guard["deadline"],
                    "Captured1% quote/caller floor or deadline not preserved")
            cursor = assigned = 0
            expected = {}
            for id_ in ids:
                converted = []
                for amount in b[f"lp:{id_}:{source}"]:
                    cursor += amount
                    cumulative = cursor * output // total
                    converted.append(cumulative - assigned)
                    assigned = cumulative
                expected[id_] = converted
            require(assigned == output and cursor == total, "Indivisible ETH output not conserved")
            for key, value in b.items():
                if not key.startswith("lp:"):
                    continue
                _, id_, asset = key.split(":")
                id_ = int(id_)
                wanted = value
                if id_ in expected:
                    wanted = [0, 0] if asset == source else [value[i] + expected[id_][i] for i in range(2)]
                require(a[key] == wanted, "Same-NFT/component credit or unselected entitlement differs")
            for key in b:
                if key.startswith("royalty:"):
                    require(a[key] == b[key], "Conversion touched royalty accounting")
        elif assertion["kind"] == "claims":
            entries, expected = assertion["entries"], assertion["expected"]
            require(expected == [words(row["raw"])[0] for row in assertion["claim_reads"]], "Claim view/output differs")
            paid = {}
            for (_, asset, _), amount in zip(entries, expected):
                paid[asset] = paid.get(asset, 0) + amount
            require(paid == assertion["paid_by_asset"], "Cross-currency payout was combined")
            for asset, amount in paid.items():
                delta = assertion["recipient_balances_after"][asset] - assertion["recipient_balances_before"][asset]
                require(delta + (assertion["gas_fee"] if asset == ZERO else 0) == amount,
                        "Captured recipient balance delta differs from receipt payout")
            claimed_logs = [log for log in op["receipt"]["logs"]
                            if log.get("topics", [])[:1] == [CLAIMED]]
            require(len(claimed_logs) == len(entries), "Missing exact claim receipt events")
            rewards = fixture["frozen_case"]["pins"]["rewards"]
            royalties = fixture["discovery"]["royalty"]
            for (id_, asset, royalty), amount, log in zip(entries, expected, claimed_logs):
                require(log["address"].lower() == (royalties if royalty else rewards).lower() and
                        len(log["topics"]) == 4 and int(log["topics"][1], 16) == id_ and
                        int(log["topics"][2], 16) == int(asset, 16) and
                        int(log["topics"][3], 16) == int(op["sender"], 16) and
                        words(log["data"]) == [amount], "Claim receipt ledger/owner/asset/amount differs")
            selected = {(str(id_), asset) for id_, asset, royalty in entries if not royalty}
            for key, value in b.items():
                if key.startswith("lp:"):
                    _, id_, asset = key.split(":")
                    require(a[key] == ([0, 0] if (id_, asset) in selected else value), "Claim changed unrelated rights")
        else:
            raise ValueError("Unknown assertion kind")
        assertions.append(path.name)
    require(len(assertions) >= (4 if completion else 8) and verified_ops and (completion or refusals),
            "Missing meaningful scoped accounting evidence")
    baseline = linked(summary["baseline"], root)
    base_values = state(baseline)
    rollback_states = []
    for name in (() if completion else ("convert-32-after", "claim-tree-16-after", "claim-tree-32-after",
                 "faulty-mixed-refused-after", "conversion-refusals-after")):
        paths = list((root / "states").glob(name + ".json*"))
        require(len(paths) == 1, "Missing refused-operation accounting snapshot")
        after = load(paths[0])
        require(state(after) == base_values and after["physical"] == baseline["physical"] and
                after["native_balances"] == baseline["native_balances"], "Refusal changed financial state")
        rollback_states.append(name)
    plans = []
    if completion:
        require(continuations == ["PREFIX_SUFFIX_CONTINUATION.json"], "Missing partial conversion continuation")
        original, paid = None, []
        for index, expected_count in enumerate((24, 8)):
            captured = load(root / f"planner/mixed-next-{index}.json")
            plan = captured["plan"]
            draft, bounds = plan["next_batch"], plan["planning"]
            require(captured["normal_deployment_admission_verified"] is False and
                    sum(captured["rpc_counts"].values()) <= 1024 and
                    bounds["maximum_trials"] == 10 and bounds["trial_count"] <= 10 and
                    bounds["final_batch_revalidated"] is True, "Planner changed its work or admission boundary")
            selected = [row for row in plan["entries"] if row["status"] == "in_next_batch"]
            require(len(selected) == len(draft["claim_operations"]) == expected_count and
                    len(plan["entries"]) == (32 if index == 0 else 8), "Planner selection not retained/split exactly")
            identity = lambda row: (row["token_id"], row["asset"], row["royalty"])
            if original is None:
                original = {identity(row) for row in plan["entries"]}
            paid.extend(identity(row) for row in selected)
            op = load(root / f"operations/planner-execute-next-{index}.json")
            tx, gas = draft["transaction"], draft["network_gas"]
            require(op["name"] in verified_ops and tx["data"] == op["data"] and
                    tx["to"] == op["to"] and tx["from"] == op["sender"] and
                    int(gas["estimated_units"]) == op["estimate"] and
                    int(gas["suggested_limit"]) == op["padded"] <= 12_000_000 and
                    gas["full_twenty_percent_headroom"] is True,
                    "Mined planner transaction differs from final unsigned review")
            plans.append({"selected": expected_count, "estimate": op["estimate"], "padded": op["padded"],
                          "rpc_reads": sum(captured["rpc_counts"].values())})
        zero = load(root / "planner/confirmed-zero-replan.json")["plan"]
        require(len(paid) == len(set(paid)) == 32 and set(paid) == original and
                zero["next_batch"] is None and len(zero["entries"]) == 32 and
                all(row["status"] == "zero" for row in zero["entries"]) and
                zero["planning"]["trial_count"] == 0, "Confirmed replan omitted or double-paid an entry")
    return {"schema": 1, "complete": True, "all_campaign_parts_qualified": not failures,
            "unresolved_campaign_failures": failures, "production_approved": False,
            "actual_mined_scenario_operations": len(verified_ops), "retained_refusals": len(refusals),
            "independent_accounting_assertions": len(assertions), "operation_names": verified_ops,
            "refusal_names": refusals, "assertions": assertions, "ownership_observations": ownership,
            "full_financial_rollback_snapshots": rollback_states,
            "verified_continuations": continuations, "actual_planner_batches": plans,
            "scope": "Offline captured-wire/receipt/unit-accounting check; not another EVM execution or production approval"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.campaign)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if not isinstance(value, list)}))
