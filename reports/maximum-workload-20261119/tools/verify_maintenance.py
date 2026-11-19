"""Cold, read-only verification of the NEW populated maintenance exports.

Only the sibling source-pinned producer/parser may supply cases. Each case gets
an owned loopback node and the generic loader stops it in finally. No endpoint,
key, sender-override, send, impersonation or existing-chain option is accepted.
Actual24M/full25% admission is distinct from finite producer assertions, intended
guard refusals and any bounded diagnostic execution. No running limit changes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "verify_contributions.py"
CASE_POLICY = {
    "max1000-lp2-harvest": ("harvest", True),
    "max1000-lp2-harvest-no-new-fees": ("harvest_noop", True),
    "max1000-lp2-compound": ("compound", True),
    "max1000-lp2-compound-before-interval": ("compound_early", False),
    "max1000-lp2-ordinary-replace": ("replace", True),
    "max1000-lp2-rebalance-replay-before-cooldown": ("rebalance_early", False),
    "max1000-lp2-to-lp1-merge": ("merge", True),
    "max1000-lp2-compound-stale-price": ("compound_stale", False),
}
CAP = 24_000_000
PADDING = 2500


def require(ok, message):
    if not ok:
        raise ValueError(message)


def words(data, count=None):
    require(type(data) is str and re.fullmatch(r"0x(?:[0-9a-fA-F]{64})*", data), "Malformed static ABI words")
    result = [data[i:i + 64].lower() for i in range(2, len(data), 64)]
    if count is not None:
        require(len(result) == count, "Unexpected static ABI word count")
    return result


def uint(word):
    require(type(word) is str and re.fullmatch(r"[0-9a-f]{64}", word), "Malformed uint word")
    return int(word, 16)


def address(word):
    require(uint(word) < 1 << 160, "Dirty ABI address")
    return "0x" + word[-40:]


def ordered_frames(root):
    todo = [root]
    count = 0
    while todo:
        frame = todo.pop()
        count += 1
        require(type(frame) is dict and count <= 16384, "Trace frame/work bound")
        yield frame
        children = frame.get("calls", [])
        require(type(children) is list, "Malformed child frame list")
        todo.extend(reversed(children))


def logs_of(frame, emitter, event_topic, indexed_count=None, data_count=None):
    result = []
    for log in frame.get("logs", []):
        if log.get("address", "").lower() != emitter or log.get("topics", [None])[:1] != [event_topic]:
            continue
        require(log.get("removed", False) is False, "Removed simulation log")
        topics = log["topics"]
        if indexed_count is not None:
            require(len(topics) == indexed_count + 1, "Unexpected indexed event count")
        result.append((topics, words(log.get("data"), data_count)))
    return result


def trace_events(trace, emitter, event_topic, indexed_count=None, data_count=None):
    return [item for frame in ordered_frames(trace)
            for item in logs_of(frame, emitter, event_topic, indexed_count, data_count)]


def success(frame):
    require(not frame.get("error"), "Expected successful financial frame reverted")
    return frame


def output_values(frame, count):
    success(frame)
    return [uint(row) for row in words(frame.get("output"), count)]


def verify_financial(base, trace, case, read, before):
    """Reconcile actual funded harvest and physical transition in the cold trace.

    The producer separately checks every holder's exact book and share invariant.
    Those1000-holder assertions are deliberately not inserted into the measured
    transaction. This verifier does not claim to recover arbitrary storage diffs.
    """
    pins = case["pins"]
    vault, fees, rewards = (pins[key] for key in ("vault", "fees", "rewards"))
    liquidity, posm, royalty = pins["liquidity"], pins["position_manager"], before["royalty"]
    bucket = case["shared_bucket"]
    kind, expected = CASE_POLICY[case["label"]]
    require(expected and not trace.get("error"), "Successful financial trace required")
    sig = lambda value: base.topic(value)[:10]
    all_frames = list(ordered_frames(trace))
    require(not any(frame.get("to", "").lower() == royalty for frame in all_frames),
            "LP maintenance unexpectedly calls the royalty ledger")
    require(not any(frame.get("to", "").lower() in (rewards, pins["membership"]) and
                    frame.get("type") not in ("STATICCALL",) and
                    frame.get("input", "")[:10] in (sig("syncShares(uint256)"), sig("syncMembership(uint256)"),
                                                     sig("claim(uint256,address)")) for frame in all_frames),
            "Maintenance changes holder membership/share or claims rewards")

    # A normal harvest allocates only actual Vault receipts. Each20 raw units
    # credits16 individual+2 collective,1 compound and1 fixed-ZZZ-buyback reserve.
    states = {asset: dict(row) for asset, row in before["fee_books"].items()}
    allocations, released, allowed_credit_frames = [], [], set()
    for frame in all_frames:
        if frame.get("from", "").lower() != vault or frame.get("to", "").lower() != fees:
            continue
        method = frame.get("input", "")[:10]
        if method == sig("allocate(uint256,address,uint256)"):
            require(frame.get("type") == "CALL", "Fee allocation must be a typed CALL")
            success(frame)
            data = words("0x" + frame["input"][10:], 3)
            require(uint(data[0]) == bucket, "Fee receipt assigned to another bucket")
            asset, amount = address(data[1]), uint(data[2])
            require(asset in states and amount > 0, "Unexpected/zero LP fee currency")
            state = states[asset]
            require(base.quantity(frame.get("value", "0x0")) == (amount if asset == base.ZERO else 0),
                    "Fee receipt native value differs")
            units, dust = divmod(state["dust"] + amount, 20)
            events = logs_of(frame, fees, base.topic("FeesAllocated(uint256,address,uint256,uint256)"), 2, 2)
            require(len(events) == 1, "Missing exact FeesAllocated event")
            topics, values = events[0]
            require(int(topics[1], 16) == bucket and address(topics[2][2:].lower()) == asset and
                    list(map(uint, values)) == [units * 20, dust], "Fee split/dust event mismatch")
            credits = [child for child in frame.get("calls", []) if child.get("from", "").lower() == fees and
                       child.get("to", "").lower() == rewards and
                       child.get("input", "")[:10] == sig("creditPool(uint256,address,uint256,uint256)")]
            require(len(credits) == int(units > 0), "Missing/extra funded whole-unit credit")
            if units:
                credit = success(credits[0]); allowed_credit_frames.add(id(credit))
                require(words("0x" + credit["input"][10:], 4) ==
                        [f"{bucket:064x}", f"{int(asset, 16):064x}", f"{units * 16:064x}", f"{units * 2:064x}"],
                        "Individual/collective credit differs from80/10")
                require(base.quantity(credit.get("value", "0x0")) == (units * 18 if asset == base.ZERO else 0),
                        "Funded credit native value differs")
                credited = logs_of(credit, rewards, base.topic("PoolRewardsCredited(uint256,address,uint256,uint256)"), 2, 2)
                require(len(credited) == 1, "Missing exact funded rewards event")
                topics, values = credited[0]
                require(int(topics[1], 16) == bucket and address(topics[2][2:].lower()) == asset and
                        list(map(uint, values)) == [units * 16, units * 2], "Funded reward split mismatch")
            state["dust"] = dust; state["compound"] += units; state["buyback"] += units
            state["liability"] += units * 18
            allocations.append({"asset": asset, "received": amount, "individual": units * 16,
                                "collective": units * 2, "compound": units, "buyback": units, "dust": dust})
        elif method == sig("releaseCompound(uint256,address)"):
            data = words("0x" + frame["input"][10:], 2)
            require(uint(data[0]) == bucket and address(data[1]) in states, "Foreign compound release")
            asset = address(data[1]); amount = output_values(frame, 1)[0]
            require(amount == states[asset]["compound"], "Released compound differs from captured reserve plus receipts")
            states[asset]["compound"] = 0
            if amount:
                if asset == base.ZERO:
                    sends = [child for child in frame.get("calls", []) if child.get("to", "").lower() == vault and
                             child.get("from", "").lower() == fees and child.get("type") == "CALL" and
                             base.quantity(child.get("value", "0x0")) == amount]
                    require(len(sends) == 1, "Compound native reserve did not fund the Vault exactly")
                else:
                    sends = [child for child in frame.get("calls", []) if child.get("to", "").lower() == asset and
                             child.get("from", "").lower() == fees and
                             child.get("input", "").lower() == sig("transfer(address,uint256)") +
                             f"{int(vault, 16):064x}{amount:064x}"]
                    require(len(sends) == 1, "Compound fixed-ZZZ reserve did not fund the Vault exactly")
            released.append({"asset": asset, "amount": amount})
        elif method == sig("releaseBuyback(address,uint256)"):
            raise ValueError("LP maintenance spent the buyback reserve")

    all_credits = [frame for frame in all_frames if frame.get("to", "").lower() == rewards and
                   frame.get("type") == "CALL" and frame.get("input", "")[:10] ==
                   sig("creditPool(uint256,address,uint256,uint256)")]
    require({id(frame) for frame in all_credits} == allowed_credit_frames,
            "Unexpected LP credit outside actual fee allocation")
    harvests = trace_events(trace, vault, base.topic("FeesCollected(uint256,uint256,uint256)"), 1, 2)
    require(harvests, "Missing physical fee receipt observation")
    received = {base.ZERO: 0, before["zzz"]: 0}
    for topics, data in harvests:
        require(int(topics[1], 16) == bucket, "Harvest belongs to another bucket")
        received[base.ZERO] += uint(data[0]); received[before["zzz"]] += uint(data[1])
    require(received == {asset: sum(row["received"] for row in allocations if row["asset"] == asset)
                         for asset in received}, "Actual harvested receipts differ from allocated amounts")
    if kind == "harvest":
        require(sum(received.values()) > 0, "Funded harvest evidence is vacuous")
    if kind == "harvest_noop":
        require(sum(received.values()) == 0 and not allocations, "Repeated harvest creates phantom income")

    # Verify which physical positions supplied those receipts, rather than
    # accepting a funded aggregate that might accidentally omit one leg.
    # PositionManager uses bytes32(tokenId) as the actual v4 position salt.
    physical_collections = []
    for frame in all_frames:
        if (frame.get("from", "").lower() != posm or frame.get("to", "").lower() != pins["pool_manager"] or
                frame.get("input", "")[:10] != sig("modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)")):
            continue
        data = words("0x" + frame["input"][10:])
        require(len(data) >= 11, "Truncated actual-core liquidity call")
        if uint(data[7]) != 0:
            continue
        require("0x" + base.keccak256(bytes.fromhex("".join(data[:5]))).hex() == before["pool_id"],
                "Fee collection uses another actual pool")
        lp_id = uint(data[8]); require(lp_id in (before["main"], before["residual"]), "Untracked physical fee source")
        caller_delta, fees_delta = output_values(frame, 2)
        require(caller_delta == fees_delta, "Zero-liquidity collection contains principal")
        values = [fees_delta >> 128, fees_delta & ((1 << 128) - 1)]
        require(all(value < 1 << 127 for value in values), "Negative actual accrued fee")
        physical_collections.append({"position_id": lp_id, "eth": values[0], "zzz": values[1]})
    require({row["position_id"] for row in physical_collections} == {before["main"], before["residual"]},
            "Both tracked physical legs were not collected")
    require([sum(row[key] for row in physical_collections) for key in ("eth", "zzz")] ==
            [received[base.ZERO], received[before["zzz"]]], "Actual per-leg accrued fees differ from Vault receipts")
    if kind == "harvest":
        require(all(sum(row["eth"] + row["zzz"] for row in physical_collections if row["position_id"] == lp_id) > 0
                    for lp_id in (before["main"], before["residual"])),
                "Funded two-leg harvest did not exercise actual fees from both legs")

    # Observe actual position transitions. Position NFT mints/burns are distinct
    # from the collection NFT; all new principal NFTs must stay Vault-owned.
    transfers = trace_events(trace, posm, base.topic("Transfer(address,address,uint256)"), 3, 0)
    minted, burned = [], []
    for topics, _data in transfers:
        sender, recipient = address(topics[1][2:].lower()), address(topics[2][2:].lower())
        nft_id = int(topics[3], 16)
        if sender == base.ZERO:
            require(recipient == vault, "New principal position NFT escaped Vault custody"); minted.append(nft_id)
        if recipient == base.ZERO:
            require(sender == vault, "Unexpected principal NFT burn source"); burned.append(nft_id)
    rebalances = trace_events(trace, vault, base.topic("Rebalanced(uint256,uint256,uint256,uint160)"), 1, 3)
    compounds = trace_events(trace, vault, base.topic("Compounded(uint256,uint256,uint256)"), 1, 2)
    old_main, old_residual = before["main"], before["residual"]
    transition = {"old_main": old_main, "old_residual": old_residual,
                  "minted_position_ids": minted, "burned_position_ids": burned}
    if kind in ("replace", "merge"):
        require(len(rebalances) == 1 and not compounds, "Replacement operation event mismatch")
        topics, values = rebalances[0]
        old, new, center = map(uint, values)
        require(int(topics[1], 16) == bucket and old == old_main and new != old and center > 0,
                "Replacement changed the wrong principal position")
        require(set(burned) == {old_main, old_residual} and len(burned) == 2,
                "Both old physical legs were not closed exactly once")
        require(new in minted and len(minted) == (2 if kind == "replace" else 1),
                "Replacement physical leg count differs")
        require(len(set(minted)) == len(minted), "Duplicate new principal NFT")
        transition.update(new_main=new, new_center=center,
                          new_residual=next((item for item in minted if item != new), 0))
    else:
        require(not rebalances and not minted and not burned, "Harvest/compound replaces or closes principal")
        if kind == "compound":
            require(len(compounds) == 1 and int(compounds[0][0][1], 16) == bucket and
                    sum(map(uint, compounds[0][1])) > 0, "Compound fails to reinvest actual reserves")
        else:
            require(not compounds and not released, "Harvest unexpectedly compounds reserves")

    value_checks = trace_events(trace, pins["budget"], base.topic("MigrationValueChecked(uint256,uint256,uint256,uint256)"), 1, 3)
    if kind in ("compound", "replace", "merge"):
        require(len(value_checks) == 1, "Missing exact captured maintenance value proof")
        topics, data = value_checks[0]; initial, deployed, idle = map(uint, data)
        require(int(topics[1], 16) == bucket and initial > 0 and deployed > 0,
                "Vacuous/foreign maintenance value proof")
        require(deployed + idle >= initial - initial * 300 // 10000,
                "Cold operation violates retained3% maintenance floor")
        require(idle <= (deployed + idle) * before["maintenance_idle_bps"] // 10000,
                "Cold operation violates separate idle ceiling")
        transition["captured_values"] = {"initial_usd18": initial, "deployed_usd18": deployed, "idle_usd18": idle}
    else:
        require(not value_checks, "Fee-only harvest unexpectedly uses USD maintenance budget")
        require(not any(frame.get("to", "").lower() in
                        (pins["oracle"], pins["reference"], pins["independent_reference"])
                        for frame in all_frames), "Fee-only harvest unexpectedly depends on live prices")

    # Explicitly require the production-wide final value/price scope for any
    # swap-bearing principal operation, never an emergency mask or bypass.
    if kind in ("compound", "replace", "merge"):
        opens = [frame for frame in all_frames if frame.get("to", "").lower() == pins["oracle"] and
                 frame.get("input", "")[:10] == sig("beginExecution(address)")]
        closes = [frame for frame in all_frames if frame.get("to", "").lower() == pins["oracle"] and
                  frame.get("input", "")[:10] == sig("endExecution()")]
        require(len(opens) == len(closes) == 1, "Captured execution price scope missing/duplicated")
        success(opens[0]); success(closes[0])
        require(not any(frame.get("to", "").lower() == pins["budget"] and
                        frame.get("input", "")[:10] == sig("beginEmergency(uint256,uint8)")
                        for frame in all_frames), "Ordinary maintenance used an emergency bypass")

    return {"verified": True, "actual_fee_receipts": received, "allocations": allocations,
            "actual_per_position_collections": physical_collections,
            "compound_releases": released, "derived_post_fee_books": states,
            "physical_transition": transition,
            "royalty_ledger_calls": 0,
            "holder_assertion_scope": "All1000 shares/owners/tickets/LPclaims are independently asserted in the source-pinned producer; not repeated as measured cold transaction work."}


def verify_case(base, rpc, read, case, anchor, alloc, omitted):
    label = case["label"]
    require(label in CASE_POLICY, "Unknown maintenance case")
    kind, expected = CASE_POLICY[label]
    require(case["expected_success"] is expected, "Producer expectation differs from reviewed case")
    require(case["cap"] == CAP and case["padding_bps"] == PADDING and case["value"] == 0,
            "Maintenance cap/padding/value changed")
    pins = case["pins"]
    sig = lambda value: base.topic(value)[:10]
    call_data = words("0x" + case["data"][10:])
    compound = kind.startswith("compound")
    expected_sig = "compound(uint256,uint128,uint256)" if compound else (
        "rebalance(uint256,uint128,uint256)" if kind in ("replace", "merge", "rebalance_early") else "collectFees(uint256,uint256)")
    require(case["data"][:10] == sig(expected_sig), "Wrong production operation selector")
    require(len(call_data) == (2 if kind.startswith("harvest") else 3), "Malformed operation arguments")
    bucket = uint(call_data[0]); require(bucket == case["shared_bucket"] > 0, "Wrong populated bucket")
    require(uint(call_data[-1]) == case["block"]["timestamp"] + 100, "Original100-second expiry differs")
    if len(call_data) == 3:
        require(uint(call_data[1]) == 1, "Caller liquidity floor changed")

    access = "0x" + read(pins["liquidity"], "access()")[0][-40:]
    compounder = "0x" + read(access, "module(bytes32)", "0x" + base.keccak256(b"ZZZCompounder").hex())[0][-40:]
    strategy = "0x" + read(access, "module(bytes32)", "0x" + base.keccak256(b"ZZZStrategy").hex())[0][-40:]
    require(case["destination"] == (compounder if compound else pins["vault"]), "Wrong operation destination")
    require(int(read(access, "keeperAuthorized(address)", case["sender"])[0], 16) == 1,
            "Actual cold sender lacks keeper permission")
    require(int(read(access, "paused()")[0], 16) == 0, "Ordinary operation is paused")
    royalty = "0x" + read(pins["nft"], "royaltyRewards()")[0][-40:]
    zzz = "0x" + read(pins["activation_assets"], "zzz()")[0][-40:]
    require(int(read(royalty, "assetCapacity()")[0], 16) == 64 and
            int(read(royalty, "assetCount()")[0], 16) == 65, "Maximum currency population differs")
    require([int(read(addr, method)[0], 16) for addr, method in
             ((pins["nft"], "mintedCount()"), (royalty, "activationCount()"),
              (pins["membership"], "totalEligible()"), (royalty, "totalWeight()"))] == [1000, 1000, 1000, 1500],
            "Maximum minted/activated/ticket population differs")
    require(int(read(pins["budget"], "maintenanceLossBps()")[0], 16) == 300 and
            int(read(strategy, "additionalLossBps()")[0], 16) == 100, "Financial safeguards differ")
    require(int(read(pins["budget"], "emergencyActive()")[0], 16) == 0 and
            int(read(pins["oracle"], "executionActive()")[0], 16) == 0, "Borrowed/emergency execution context")
    group = [int(row, 16) for row in read(pins["vault"], "group(uint256)", bucket, count=8)]
    main = group[1]
    residual = int(read(pins["liquidity"], "secondaryId(uint256)", main)[0], 16)
    require(main == case["expected_main"] and residual == case["expected_residual"] > 0,
            "Captured two-position identity differs")
    require(int(read(pins["liquidity"], "activeSecondaryCount()")[0], 16) == 1, "Extra physical residual")
    for lp_id in (main, residual):
        require("0x" + read(pins["position_manager"], "ownerOf(uint256)", lp_id)[0][-40:] == pins["vault"],
                "Populated principal NFT not Vault-owned")
        require(int(read(pins["position_manager"], "getPositionLiquidity(uint256)", lp_id)[0], 16) > 0,
                "Populated physical leg is empty")
    before = {"main": main, "residual": residual, "royalty": royalty, "zzz": zzz, "pool_id": "0x" + f"{group[0]:064x}",
              "maintenance_idle_bps": int(read(pins["protocol_policy"], "maintenancePolicy()", count=2)[0], 16),
              "fee_books": {}}
    for asset in (base.ZERO, zzz):
        before["fee_books"][asset] = {
            "dust": int(read(pins["fees"], "dust(uint256,address)", bucket, asset)[0], 16),
            "compound": int(read(pins["fees"], "compoundBalance(uint256,address)", bucket, asset)[0], 16),
            "buyback": int(read(pins["fees"], "buybackBalance(address)", asset)[0], 16),
            "liability": int(read(pins["rewards"], "liabilities(address)", asset)[0], 16)}

    tx = {"from": case["sender"], "to": case["destination"], "value": "0x0", "data": case["data"], "gas": hex(CAP)}
    call = rpc.attempt("eth_call", [tx, anchor])
    estimate = rpc.attempt("eth_estimateGas", [tx, anchor])
    traced = base.checked_trace(rpc, tx, anchor, omitted)
    trace_ok = traced["ok"] and not traced["result"].get("error")
    outcome = {"case_kind": kind, "expected_success": expected, "configured_gas_cap": CAP,
               "padding_bps": PADDING, "actual_profile_call": call, "actual_profile_estimate": estimate,
               "profile_trace_success": trace_ok, "population": {"minted": 1000, "active": 1000,
               "royalty_erc20s": 64, "royalty_assets": 65, "physical_legs": 2},
               "production_approved": False, "financial_guards_unchanged": True}
    if not expected:
        require(not call["ok"] and not estimate["ok"] and traced["ok"] and traced["result"].get("error"),
                "Intended financial/timing guard unexpectedly succeeds or lacks a usable trace")
        actual = traced["result"].get("output", "0x").lower()
        require(actual == case["expected_return"].lower() and len(actual) >= 10,
                "Cold refusal differs from the actual producer reason; OOG is not a guard pass")
        expected_error = sig("InvalidPrice(address)") if kind == "compound_stale" else sig("InvalidState()")
        require(actual.startswith(expected_error), "Unknown refusal cause, not the reviewed guard")
        outcome.update(verification_complete=True, expected_behavior_verified=True,
                       intended_guard_refusal=True, revert_data=actual, profile_qualification_applicable=False,
                       meets_reviewed_execution_profile=False,
                       scope="Confirmed intentional source/timing refusal. Not an executable operation/gas admission.")
        return outcome

    estimated = base.quantity(estimate["result"]) if estimate["ok"] else None
    padded = (estimated * 125 + 99) // 100 if estimated is not None else None
    exact = None
    exact_trace = None
    if call["ok"]:
        require(call["result"] == "0x", "Unexpected production return bytes")
    if call["ok"] and estimated is not None and 21000 <= estimated <= padded <= CAP:
        exact = rpc.attempt("eth_call", [{**tx, "gas": hex(padded)}, anchor])
        if exact["ok"]:
            require(exact["result"] == "0x", "Unexpected exact padded return bytes")
            exact_trace = base.checked_trace(rpc, {**tx, "gas": hex(padded)}, anchor, omitted)
    admitted = bool(call["ok"] and trace_ok and exact and exact["ok"] and
                    exact_trace and exact_trace["ok"] and not exact_trace["result"].get("error"))
    complete_trace = traced["result"] if trace_ok else None
    if complete_trace is None:
        diagnostic_tx = {**tx, "gas": hex(base.DIAGNOSTIC)}
        diagnostic = rpc.attempt("eth_call", [diagnostic_tx, anchor])
        diagnostic_trace = base.checked_trace(rpc, diagnostic_tx, anchor, omitted)
        outcome["diagnostic_only"] = {"cap": base.DIAGNOSTIC, "call": diagnostic,
                                      "trace_success": diagnostic_trace["ok"] and not diagnostic_trace["result"].get("error"),
                                      "operating_budget_adopted": False}
        if diagnostic_trace["ok"] and not diagnostic_trace["result"].get("error"):
            complete_trace = diagnostic_trace["result"]
    require(complete_trace is not None, "No complete cold financial trace; profile is not qualified")
    financial = verify_financial(base, complete_trace, case, read, before)
    exact_financial = None
    if admitted:
        exact_financial = verify_financial(base, exact_trace["result"], case, read, before)
        require(exact_financial == financial,
                "Exact padded cold call differs financially from the full-cap call")
    price = base.quantity(rpc.call("eth_gasPrice", []))
    balance = base.quantity(rpc.call("eth_getBalance", [case["sender"], anchor]))
    if admitted:
        require(balance >= padded * price, "Actual keeper cannot fund padded local execution")
    outcome.update(verification_complete=True, expected_behavior_verified=financial["verified"],
                   profile_qualification_applicable=True, meets_reviewed_execution_profile=admitted and financial["verified"],
                   estimate_gas=estimated, padded_gas=padded, exact_padded_call=exact,
                   exact_padded_financial_trace=exact_financial,
                   trace_gas_used=base.quantity(complete_trace["gasUsed"]),
                   financial_trace_verification=financial, gas_price_wei=price, sender_balance_wei=balance,
                   complete_target_fees_qualified=False,
                   scope="Finite cold controlled F6 maintenance,65currencies/1000active/two legs; local execution gas only. No target provider/fees/operating acceptance.")
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage")
    args = parser.parse_args()
    require(re.fullmatch(r"producer[0-9]{2}", args.stage), "Use one new owned producer stage")
    spec = importlib.util.spec_from_file_location("maximum_workload_contribution_support", BASE_PATH)
    base = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = base; spec.loader.exec_module(base)
    base.configure(args.stage)
    cases, raw_hash, sources, methods = base.exports()
    selected = [case for case in cases if case["label"] in CASE_POLICY]
    require({case["label"] for case in selected} == set(CASE_POLICY) and len(selected) == len(CASE_POLICY),
            "Missing/duplicated maximum maintenance export")
    out = base.F / "maintenance-local-rpc"
    out.mkdir(exist_ok=False)
    results = []
    for case in selected:
        result = base.owned_case(case, out, lambda *items: verify_case(base, *items))
        results.append(result)
        print(json.dumps({"label": case["label"], "verification_complete": result.get("verification_complete"),
                          "profile_pass": result.get("meets_reviewed_execution_profile"),
                          "error": result.get("verification_error")}), flush=True)
    summary = {"schema": 1, "producer_raw_sha256": raw_hash, "producer_methods": methods,
               "checker_sha256": base.sha(Path(__file__).read_bytes()), "support_sha256": base.sha(BASE_PATH.read_bytes()),
               "operating_cap": CAP, "padding_bps": PADDING, "maximum_estimate": 19_200_000,
               "new_export_cases": len(selected), "public_transactions": 0, "production_approved": False,
               "verification_complete": all(row.get("verification_complete") and row.get("owned_node_stopped") for row in results),
               "results": results}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}), flush=True)
    return 0 if summary["verification_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
