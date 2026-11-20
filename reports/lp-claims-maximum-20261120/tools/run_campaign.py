"""Finite current-F6 maximum-state accounting campaign on one owned local node.

No compiler, producer, existing chain, public endpoint, key or production source
is used.  FrozenFixture authenticates and materializes the retained population.
Every admitted operation keeps its original cap and full padding; refusals are
evidence, never permission to send with a wider envelope.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from zzz_ops.abi import keccak256

ZERO = "0x" + "00" * 20
CLAIM_CAP, CLAIM_PADDING = 12_000_000, 2000
CONVERSION_CAP, CONVERSION_PADDING = 24_000_000, 2500
MAX_CASES = 64


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "sha256": sha(path)}


def word(value):
    if isinstance(value, str):
        value = int(value, 16) if value.startswith("0x") else int(value)
    require(type(value) in (int, bool) and 0 <= int(value) < 1 << 256, "Invalid ABI word")
    return int(value).to_bytes(32, "big")


def static(signature, *values):
    return "0x" + (keccak256(signature.encode())[:4] + b"".join(word(v) for v in values)).hex()


def decode(data, count=None):
    require(isinstance(data, str) and data.startswith("0x") and (len(data) - 2) % 64 == 0,
            "Malformed ABI output")
    result = [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]
    require(count is None or len(result) == count, "Unexpected ABI word count")
    return result


def address(value):
    return "0x" + f"{int(value):040x}"


def convert_data(f, ids, minimum=1, deadline=None):
    if deadline is None:
        deadline = int(f.head()["timestamp"], 16) + 300
    return "0x" + (keccak256(b"convertBatch(address,uint256[],bytes32,uint256,uint256)")[:4]
        + b"".join(word(v) for v in (f.zzz, 160, f.route_id, minimum, deadline))
        + word(len(ids)) + b"".join(word(i) for i in ids)).hex()


def claim_data(entries):
    return "0x" + (keccak256(b"claimBatch((uint256,address,bool)[])")[:4] + word(32)
        + word(len(entries)) + b"".join(word(v) for entry in entries for v in entry)).hex()


class Campaign:
    def __init__(self, f, out):
        self.f, self.out = f, Path(out)
        self.cases, self.failures = [], []
        self.rewards = f.pins["rewards"]
        self.vault = f.pins["vault"]
        self.fees = f.pins["fees"]
        self.manager = f.pins.get("liquidity", f.pins.get("manager"))
        self.nft = f.pins["nft"]
        self.posm = f.pins["position_manager"]
        self.executor = address(f.read(f.converter, "v4Executor()")[0])
        self.bucket = f.read(self.vault, "nftBucket(uint256)", f.ids[1])[0]
        self.all_ids = sorted(f.ids.values())
        require(len(set(self.all_ids)) == 1000, "Exact 1000-ID population required")
        self._read_index = 0

    def many(self, queries, block="latest"):
        """Bounded local read-only batches; retain exact output bytes per state."""
        require(len(queries) <= 5000, "Snapshot read bound")
        rows = []
        for start in range(0, len(queries), 100):
            part = queries[start:start + 100]
            result = self.f.rpc.batch([("eth_call", [{"from": self.f.governance, "to": target, "data": data}, block])
                                       for _, target, data in part])
            require(len(result) == len(part), "Batch response count")
            for (key, target, data), raw in zip(part, result):
                rows.append({"key": key, "to": target, "data": data, "raw": raw})
        return rows

    def state(self, name):
        head = self.f.head()
        block = {"blockHash": head["hash"], "requireCanonical": True}
        queries = []
        for id_ in self.all_ids:
            queries.append((f"shares:{id_}", self.vault, static("sharesOf(uint256)", id_)))
            for asset in (ZERO, self.f.zzz):
                queries.append((f"lp:{id_}:{asset}", self.rewards,
                    static("claimableComponents(uint256,address)", id_, asset)))
        queries += [("group", self.vault, static("group(uint256)", self.bucket))]
        for asset in (ZERO, self.f.zzz):
            for method in ("liabilities", "orphaned", "directLiabilities"):
                queries.append((f"reward:{method}:{asset}", self.rewards, static(method + "(address)", asset)))
            for method in ("dust", "compoundBalance"):
                queries.append((f"fee:{method}:{asset}", self.fees,
                    static(method + "(uint256,address)", self.bucket, asset)))
            for method in ("buybackBalance", "accounted"):
                queries.append((f"fee:{method}:{asset}", self.fees, static(method + "(address)", asset)))
            if asset != ZERO:
                for label, holder in (("reward", self.rewards), ("fee", self.fees),
                                      ("converter", self.f.converter), ("executor", self.executor)):
                    queries.append((f"balance:{label}:{asset}", asset, static("balanceOf(address)", holder)))
        for asset in self.f.currencies:
            if asset != ZERO:
                queries.append((f"royalty:balance:{asset}", asset, static("balanceOf(address)", self.f.royalty)))
            for method in ("liabilities", "orphaned", "openingPool", "accounted",
                           "eligibleCount", "eligibleWeight", "allocationCursor"):
                queries.append((f"royalty:{method}:{asset}", self.f.royalty, static(method + "(address)", asset)))
        raw = self.many(queries, block)
        parsed = {r["key"]: decode(r["raw"]) for r in raw}
        group = parsed["group"]
        require(len(group) == 8 and group[1] != 0, "Populated eight-word position")
        main = group[1]
        residual = self.f.read(self.manager, "secondaryId(uint256)", main)[0]
        require(residual != 0, "Maximum state must retain two physical LPs")
        physical = {}
        for id_ in (main, residual):
            physical[str(id_)] = {"owner": self.f.read(self.posm, "ownerOf(uint256)", id_)[0],
                "liquidity": self.f.read(self.posm, "getPositionLiquidity(uint256)", id_)[0],
                "ticks": self.f.read(self.manager, "ticks(uint256)", id_, count=2)}
        native = {"reward": int(self.f.rpc.call("eth_getBalance", [self.rewards, "latest"]), 16),
                  "fee": int(self.f.rpc.call("eth_getBalance", [self.fees, "latest"]), 16),
                  "converter": int(self.f.rpc.call("eth_getBalance", [self.f.converter, "latest"]), 16),
                  "executor": int(self.f.rpc.call("eth_getBalance", [self.executor, "latest"]), 16),
                  "royalty": int(self.f.rpc.call("eth_getBalance", [self.f.royalty, "latest"]), 16)}
        closing = self.f.head()
        require(closing["hash"] == head["hash"], "State read crossed a confirmed block")
        state = {"head": head, "closing_head": closing, "raw_reads": raw, "values": parsed,
                 "physical": physical, "native_balances": native}
        for asset in (ZERO, self.f.zzz):
            total = sum(sum(parsed[f"lp:{id_}:{asset}"]) for id_ in self.all_ids)
            require(total == parsed[f"reward:liabilities:{asset}"][0], "All1000 exact LP claims/liability mismatch")
            balance = native["reward"] if asset == ZERO else parsed[f"balance:reward:{asset}"][0]
            require(balance == total + parsed[f"reward:orphaned:{asset}"][0], "Reward backing mismatch")
            reserves = sum(parsed[f"fee:{m}:{asset}"][0] for m in ("dust", "compoundBalance", "buybackBalance"))
            require(reserves == parsed[f"fee:accounted:{asset}"][0], "Fee reserve classifications mismatch")
            fee_balance = native["fee"] if asset == ZERO else parsed[f"balance:fee:{asset}"][0]
            require(reserves == fee_balance, "Fee reserve backing mismatch")
        for asset in self.f.currencies:
            accounted = sum(parsed[f"royalty:{m}:{asset}"][0] for m in ("liabilities", "orphaned", "openingPool"))
            require(accounted == parsed[f"royalty:accounted:{asset}"][0], "Royalty categories mismatch")
            balance = native["royalty"] if asset == ZERO else parsed[f"royalty:balance:{asset}"][0]
            require(balance >= accounted, "Royalty backing deficit")
        state["artifact"] = save(self.out / "states" / (name + ".json.gz"), state)
        return state

    def run(self, name, sender, target, data, cap, padding, expected_refusal=False, value=0):
        require(len(self.cases) < MAX_CASES, "Finite campaign case bound")
        entry = {"name": name, "sender": sender, "to": target, "data": data,
                 "cap": cap, "padding_bps": padding, "value": value, "head_before": self.f.head()}
        try:
            entry["simulation"] = self.f.call(sender, target, data, gas=cap, value=value)
            estimate = self.f.estimate(sender, target, data, gas=cap, value=value)
            padded = estimate + (estimate * padding + 9999) // 10000
            entry.update(estimate=estimate, padded=padded)
            if padded > cap:
                entry["status"] = "refused_padding"
            elif expected_refusal:
                entry["status"] = "unexpectedly_admissible"
                self.failures.append(name + ": expected refusal unexpectedly admissible")
            else:
                entry["receipt"] = self.f.send(sender, target, data, gas=padded, value=value)
                entry["mined_header"] = self.f.rpc.call("eth_getBlockByNumber", [entry["receipt"]["blockNumber"], False])
                entry["status"] = "mined"
        except Exception as exc:
            structured = isinstance(getattr(exc, "error", None), dict) and getattr(exc, "method", None) in ("eth_call", "eth_estimateGas")
            entry["status"] = "refused_simulation_or_estimate" if structured else "unexpected_runner_error"
            entry["error_type"] = type(exc).__name__
            entry["error"] = str(exc)[:2000]
            if structured:
                entry["rpc_error"] = exc.error
            else:
                self.failures.append(name + ": " + type(exc).__name__ + ": " + str(exc)[:500])
        if expected_refusal:
            require(entry["status"].startswith("refused"), "Expected operation refusal")
        entry["artifact"] = save(self.out / "operations" / (name + ".json"), entry)
        self.cases.append(entry)
        return entry

    def control(self, name, sender, target, data):
        entry = self.run(name, sender, target, data, CLAIM_CAP, CLAIM_PADDING)
        require(entry["status"] == "mined", "Fixture control refused: " + name)
        return entry

    def unchanged(self, before, after):
        require(before["values"] == after["values"], "Refusal changed funded accounting")
        require(before["physical"] == after["physical"], "Refusal changed physical custody")
        require(before["native_balances"] == after["native_balances"], "Refusal changed native backing")

    def protected(self, before, after, royalty=True):
        b, a = before["values"], after["values"]
        require(b["group"] == a["group"] and before["physical"] == after["physical"], "Reward operation moved principal")
        for key in b:
            if key.startswith("fee:") or key.startswith("shares:") or (royalty and key.startswith("royalty:")):
                require(b[key] == a[key], "Reward operation altered protected book: " + key)
        require(before["native_balances"]["fee"] == after["native_balances"]["fee"], "Fee native backing changed")
        require(before["native_balances"]["converter"] == after["native_balances"]["converter"], "Converter native prefund spent")
        require(before["native_balances"]["executor"] == after["native_balances"]["executor"], "Executor native prefund spent")
        if royalty:
            require(before["native_balances"]["royalty"] == after["native_balances"]["royalty"], "Royalty native backing changed")
        require(b[f"balance:converter:{self.f.zzz}"] == a[f"balance:converter:{self.f.zzz}"], "Converter token prefund spent")
        require(b[f"balance:executor:{self.f.zzz}"] == a[f"balance:executor:{self.f.zzz}"], "Executor token prefund spent")

    def conversion(self, name, selected, before):
        selected = sorted(selected)
        prior = before["values"]
        components = [prior[f"lp:{id_}:{self.f.zzz}"] for id_ in selected]
        total = sum(sum(pair) for pair in components)
        require(total > 0, "Nonzero conversion funding")
        guard_head = self.f.head()
        quote = self.f.read(self.f.pins["oracle"], "quote(address,address,uint256)", self.f.zzz, ZERO, total)[0]
        loss_bps = self.f.read(self.f.converter, "conversionLossBps()")[0]
        require(loss_bps == 100 and quote > 0, "Original1% conversion guard must remain")
        caller_minimum = 1
        deadline = int(guard_head["timestamp"], 16) + 300
        floor = max(caller_minimum, (quote * (10000 - loss_bps) + 9999) // 10000)
        operation = self.run(name, self.f.keeper, self.rewards, convert_data(self.f, selected, minimum=caller_minimum, deadline=deadline),
                             CONVERSION_CAP, CONVERSION_PADDING)
        after = self.state(name + "-after")
        if operation["status"] != "mined":
            self.unchanged(before, after)
            return operation, after
        simulation_output = decode(operation["simulation"], 1)[0]
        output = after["native_balances"]["reward"] - before["native_balances"]["reward"]
        require(output == simulation_output and output > 0, "Measured conversion output differs")
        require(output >= floor and int(operation["mined_header"]["timestamp"], 16) <= deadline,
                "Actual output/deadline violated captured conversion guard")
        cumulative = assigned = 0
        expected = {}
        for id_, pair in zip(selected, components):
            eth = []
            for source in pair:
                cumulative += source
                nxt = output * cumulative // total
                eth.append(nxt - assigned)
                assigned = nxt
            expected[str(id_)] = {"source": pair, "eth": eth}
        require(assigned == output and cumulative == total, "Whole output apportionment mismatch")
        for id_ in self.all_ids:
            for asset in (ZERO, self.f.zzz):
                old = prior[f"lp:{id_}:{asset}"]
                new = after["values"][f"lp:{id_}:{asset}"]
                if id_ in selected:
                    wanted = [0, 0] if asset == self.f.zzz else [old[i] + expected[str(id_)]["eth"][i] for i in (0, 1)]
                else:
                    wanted = old
                require(new == wanted, "Same-NFT/component conversion mismatch")
        require(after["values"][f"reward:liabilities:{self.f.zzz}"][0] == prior[f"reward:liabilities:{self.f.zzz}"][0] - total,
                "Source liability debit mismatch")
        for method in ("liabilities", "directLiabilities"):
            require(after["values"][f"reward:{method}:{ZERO}"][0] == prior[f"reward:{method}:{ZERO}"][0] + output,
                    "Native liability/direct debit mismatch")
        executor = address(self.f.read(self.f.converter, "v4Executor()")[0])
        require(self.f.read(self.f.zzz, "allowance(address,address)", self.rewards, self.f.converter)[0] == 0,
                "Ledger approval not cleared")
        require(self.f.read(self.f.zzz, "allowance(address,address)", self.f.converter, executor)[0] == 0,
                "Executor approval not cleared")
        self.protected(before, after)
        save(self.out / "assertions" / (name + ".json"), {"kind": "conversion", "ids": selected,
             "source_total": total, "output": output, "components": expected,
             "financial_guard": {"head": guard_head, "quote": quote, "loss_bps": loss_bps,
                                 "caller_minimum": caller_minimum, "minimum_output": floor, "deadline": deadline},
             "before": before["artifact"], "after": after["artifact"], "operation": operation["artifact"]})
        return operation, after

    def claims(self, name, entries, before, sender=None):
        sender = sender or self.f.owner
        queries = [(str(i), self.f.royalty if royalty else self.rewards,
                    static("claimable(uint256,address)", id_, asset))
                   for i, (id_, asset, royalty) in enumerate(entries)]
        reads = self.many(queries)
        expected = [decode(row["raw"], 1)[0] for row in reads]
        balances = {asset: self.balance(sender, asset) for _, asset, _ in entries}
        operation = self.run(name, sender, self.f.claim_router, claim_data(entries), CLAIM_CAP, CLAIM_PADDING)
        after = self.state(name + "-after")
        if operation["status"] != "mined":
            self.unchanged(before, after)
            return operation, after
        returned = decode(operation["simulation"])
        require(returned[:2] == [32, len(entries)] and returned[2:] == expected, "Claim raw output/input order mismatch")
        paid = {}
        for (_, asset, _), amount in zip(entries, expected):
            paid[asset] = paid.get(asset, 0) + amount
        gas_fee = int(operation["receipt"]["gasUsed"], 16) * int(operation["receipt"]["effectiveGasPrice"], 16)
        after_balances = {asset: self.balance(sender, asset) for asset in paid}
        for asset, amount in paid.items():
            delta = after_balances[asset] - balances[asset]
            require(delta + (gas_fee if asset == ZERO else 0) == amount, "Recipient actual payment differs")
        for id_ in self.all_ids:
            for asset in (ZERO, self.f.zzz):
                old = before["values"][f"lp:{id_}:{asset}"]
                claimed = any(item == (id_, asset, False) for item in entries)
                require(after["values"][f"lp:{id_}:{asset}"] == ([0, 0] if claimed else old),
                        "Claim altered another NFT or left selected rights")
        self.protected(before, after, royalty=not any(e[2] for e in entries))
        save(self.out / "assertions" / (name + ".json"), {"kind": "claims", "entries": entries,
             "claim_reads": reads, "expected": expected, "paid_by_asset": paid, "gas_fee": gas_fee,
             "recipient": sender, "recipient_balances_before": balances, "recipient_balances_after": after_balances,
             "before": before["artifact"], "after": after["artifact"], "operation": operation["artifact"]})
        return operation, after

    def balance(self, owner, asset):
        return int(self.f.rpc.call("eth_getBalance", [owner, "latest"]), 16) if asset == ZERO else self.f.read(asset, "balanceOf(address)", owner)[0]

    def branch(self, name, body):
        snapshot = self.f.snapshot()
        try:
            body()
        except Exception as exc:
            self.failures.append(name + ": " + type(exc).__name__ + ": " + str(exc)[:2000])
            save(self.out / "failures" / (name + ".json"), {"name": name, "error_type": type(exc).__name__, "error": str(exc)[:4000]})
        finally:
            self.f.revert(snapshot)

    def execute(self, phase="matrix"):
        # Nonzero external prefunds must survive conversion. Native funding uses
        # a new constructor-only SELFDESTRUCT helper: no compiler, code override,
        # implementation change or new economic claim is introduced.
        prefunds = []
        for label, target, tokens, native in (("converter", self.f.converter, 7, 13),
                                                ("executor", self.executor, 11, 17)):
            self.control("prefund-zzz-" + label, self.f.governance, self.f.zzz,
                         static("mint(address,uint256)", target, tokens))
            force = self.run("prefund-eth-" + label, self.f.owner, None,
                "0x73" + target[2:] + "ff", 500_000, CLAIM_PADDING, value=native)
            require(force["status"] == "mined", "Constructor-only native prefund refused")
            prefunds.append({"target": target, "tokens": tokens, "native": native})
        save(self.out / "NEW_EXTERNAL_PREFUNDS.json", prefunds)
        # Add two explicit new pending original-currency receipts. These are
        # conventional test-token mints, not privileged royalty/LP ledger writes.
        funding = []
        for i in (1, 64):
            asset = self.f.currencies[i]
            before = self.f.read(asset, "balanceOf(address)", self.f.royalty)[0]
            self.control("pending-royalty-receipt-" + str(i), self.f.governance, asset,
                         static("mint(address,uint256)", self.f.royalty, 1500))
            after = self.f.read(asset, "balanceOf(address)", self.f.royalty)[0]
            require(after - before == 1500, "Actual original-currency receipt mismatch")
            funding.append({"asset": asset, "amount": 1500, "balance_before": before, "balance_after": after})
        save(self.out / "NEW_ROYALTY_RECEIPTS.json", funding)
        baseline = self.state("baseline")
        funded = [id_ for id_ in self.all_ids if sum(baseline["values"][f"lp:{id_}:{self.f.zzz}"]) > 0
                  and address(self.f.read(self.nft, "ownerOf(uint256)", id_)[0]) == self.f.owner]
        require(len(funded) >= 32, "At least32 owner-funded NFT IDs required")
        if phase == "completion":
            # Only these new obligations run after the retained matrix. The
            # unchanged1/8/16/32 capacity and ownership/fault cases are reused.
            self.branch("conversion-prefix-suffix", lambda: self.continuation(funded[:32], baseline))
            self.branch("unsigned-planner", lambda: self.planner(funded[:16], baseline))
        else:
            for count in (1, 8, 16, 32):
                self.branch("convert-" + str(count), lambda count=count: self.conversion("convert-" + str(count), funded[:count], baseline))
                self.branch("claim-tree-" + str(count), lambda count=count: self.claims("claim-tree-" + str(count),
                    [(id_, ZERO, False) for id_ in funded[:count]], baseline))
            self.branch("converted-direct", lambda: self.converted_claims(funded[:8], baseline))
            self.branch("pending-royalty-eight", lambda: self.claims("claim-pending-royalty-eight",
                [(i, self.f.currencies[1], True) for i in funded[:8]], baseline))
            self.branch("stored-royalty-eight", lambda: self.stored_royalty(funded[:8], baseline))
            self.branch("unsigned-planner", lambda: self.planner(funded[:16], baseline))
            self.branch("transfer-partial", lambda: self.transfers(funded[:8], baseline))
            self.branch("faulty-royalty", lambda: self.faulty_royalty(funded[0], baseline))
            self.branch("conversion-refusals", lambda: self.refusals(funded[:2], baseline))
        return {"schema": 1, "build": "activation-final-six-20261118", "scope": "finite_frozen_maximum_state_local",
                "phase": phase, "cases": self.cases, "failures": self.failures, "baseline": baseline["artifact"],
                "caps": {"claim": CLAIM_CAP, "claim_padding_bps": CLAIM_PADDING,
                         "conversion": CONVERSION_CAP, "conversion_padding_bps": CONVERSION_PADDING},
                "production_approved": False, "public_submission": False,
                "limitations": ["Synthetic sources/external depth and mocked control graph remain explicit",
                    "Claims/conversion are local qualification, not target provider, market, fees or operating approval",
                    "Finite1000NFT/65currency/twoLP ordering; not universal recipient/token/market coverage",
                    "Each snapshot branch is separately anchored, not a cumulative payment campaign"]}

    def continuation(self, selected, baseline):
        first, state = self.conversion("conversion-prefix-sixteen", selected[:16], baseline)
        require(first["status"] == "mined", "Reviewed conversion prefix must execute")
        second, final = self.conversion("conversion-suffix-sixteen", selected[16:], state)
        require(second["status"] == "mined", "Remaining independent conversion suffix must execute")
        original = baseline["values"]
        expected_source = sum(sum(original[f"lp:{id_}:{self.f.zzz}"]) for id_ in selected)
        output = final["native_balances"]["reward"] - baseline["native_balances"]["reward"]
        for id_ in selected:
            require(final["values"][f"lp:{id_}:{self.f.zzz}"] == [0, 0], "Suffix continuation left selected source rewards")
        require(final["values"][f"reward:liabilities:{self.f.zzz}"][0]
                == original[f"reward:liabilities:{self.f.zzz}"][0] - expected_source,
                "Combined prefix/suffix source debit mismatch")
        require(final["values"][f"reward:liabilities:{ZERO}"][0]
                == original[f"reward:liabilities:{ZERO}"][0] + output,
                "Combined prefix/suffix native credit mismatch")
        for asset in (ZERO, self.f.zzz):
            require(final["values"][f"reward:orphaned:{asset}"] == original[f"reward:orphaned:{asset}"],
                    "Continuation changed orphaned balances")
        save(self.out / "assertions" / "PREFIX_SUFFIX_CONTINUATION.json", {"ids": selected,
            "source_total": expected_source, "native_output": output, "before": baseline["artifact"],
            "after": final["artifact"], "prefix": first["artifact"], "suffix": second["artifact"],
            "not_equal_to_hypothetical_single_swap": True})

    def stored_royalty(self, selected, baseline):
        self.control("stored-royalty-sync", self.f.governance, self.f.royalty,
                     static("sync(address)", self.f.currencies[1]))
        state = self.state("stored-royalty-before")
        self.protected(baseline, state, royalty=False)
        self.claims("claim-stored-royalty-eight", [(i, self.f.currencies[1], True) for i in selected], state)

    def planner_call(self, label, selection, wallet):
        from claims_planner_qualification import build_manifest, qualify_plan
        migration = address(self.f.read(self.f.access, "module(bytes32)", "0x" + keccak256(b"ZZZMigration").hex())[0])
        manifest = build_manifest(self.f.rpc.call, {"nft": self.nft, "rewards": self.rewards,
            "royalties": self.f.royalty, "claim_router": self.f.claim_router,
            "principal_exit": migration, "vault": self.vault},
            max_gas_price_wei="1000000000000", max_network_fee_wei="12000000000000000000")
        manifest_ref = save(self.out / "planner" / (label + "-MANIFEST.json"), manifest)
        result = qualify_plan(self.f.rpc.call, manifest, selection, wallet=wallet)
        result["fixture_manifest"] = manifest_ref
        result["local_fee_limits_not_target_chain_qualification"] = True
        save(self.out / "planner" / (label + ".json"), result)
        return result["plan"]

    def planner(self, selected, baseline):
        selection = [{"token_id": str(id_), "asset": asset, "royalty": royalty}
                     for id_ in selected for asset, royalty in ((ZERO, False), (self.f.currencies[1], True))]
        remaining, state = selection, baseline
        rounds = []
        for step in range(6):
            plan = self.planner_call("mixed-next-" + str(step), remaining, self.f.owner)
            draft = plan["next_batch"]
            if draft is None:
                require(all(e["status"] == "zero" for e in plan["entries"]), "Funded healthy planner selection has no executable batch")
                remaining = []
                break
            entries = [(int(e["token_id"]), e["asset"], e["royalty"]) for e in draft["claim_operations"]]
            require(draft["transaction"]["data"] == claim_data(entries), "Published calldata differs from explicit selected tuples")
            operation, state = self.claims("planner-execute-next-" + str(step), entries, state)
            require(operation["status"] == "mined", "Fresh planned batch refused actual exact preparation")
            rounds.append({"selection": remaining, "entries": entries, "operation": operation["artifact"]})
            remaining = [{k: e[k] for k in ("token_id", "asset", "royalty")} for e in plan["remaining_claims"]]
            if not remaining:
                break
        require(not remaining, "Finite planner continuation remains incomplete")
        zero = self.planner_call("confirmed-zero-replan", selection, self.f.owner)
        require(zero["next_batch"] is None and all(e["status"] == "zero" for e in zero["entries"]), "Confirmed claims must replan as zero")
        save(self.out / "planner" / "CONFIRMED_CONTINUATION.json", {"rounds": rounds, "remaining": remaining,
             "all_original_entries_confirmed_zero": True})

    def converted_claims(self, selected, baseline):
        operation, state = self.claims("direct-seed-clear-old-eth", [(i, ZERO, False) for i in selected], baseline)
        if operation["status"] != "mined":
            # A refusal is retained; smaller prefixes stay freshly prepared.
            for j, id_ in enumerate(selected):
                operation, state = self.claims("direct-seed-single-" + str(j), [(id_, ZERO, False)], state)
                require(operation["status"] == "mined", "Cannot prepare direct-only claim state")
        operation, state = self.conversion("direct-seed-convert-eight", selected, state)
        require(operation["status"] == "mined", "Cannot prepare converted direct claim state")
        self.claims("claim-converted-direct-eight", [(i, ZERO, False) for i in selected], state)

    def transfers(self, selected, baseline):
        a, b, c = selected[:3]
        self.control("transfer-before-convert", self.f.owner, self.nft,
                     static("transferFrom(address,address,uint256)", self.f.owner, self.f.newcomer, a))
        first_owner = self.many([("owner", self.nft, static("ownerOf(uint256)", a))])
        require(address(decode(first_owner[0]["raw"], 1)[0]) == self.f.newcomer, "First NFT transfer not recorded")
        save(self.out / "assertions" / "transfer-before-owner.json", first_owner)
        old_plan = self.planner_call("former-owner-selection", [{"token_id": str(a), "asset": ZERO, "royalty": False}], self.f.owner)
        require(old_plan["next_batch"] is None and all(e["status"] in ("blocked", "unavailable") for e in old_plan["entries"]),
                "Planner admitted former owner's claim")
        self.run("old-owner-claim-rejected-before", self.f.owner, self.rewards, static("claim(uint256,address)", a, ZERO),
                 CLAIM_CAP, CLAIM_PADDING, expected_refusal=True)
        operation, state = self.claims("raw-zzz-recovery-before-convert", [(b, self.f.zzz, False)], baseline)
        require(operation["status"] == "mined", "RawZZZ recovery must execute")
        operation, state = self.conversion("partial-transfer-convert", selected, state)
        require(operation["status"] == "mined", "Selected partial conversion must execute")
        self.control("transfer-after-convert", self.f.owner, self.nft,
                     static("transferFrom(address,address,uint256)", self.f.owner, self.f.newcomer, c))
        second_owner = self.many([("owner", self.nft, static("ownerOf(uint256)", c))])
        require(address(decode(second_owner[0]["raw"], 1)[0]) == self.f.newcomer, "Second NFT transfer not recorded")
        save(self.out / "assertions" / "transfer-after-owner.json", second_owner)
        self.run("old-owner-claim-rejected-after", self.f.owner, self.rewards, static("claim(uint256,address)", c, ZERO),
                 CLAIM_CAP, CLAIM_PADDING, expected_refusal=True)
        operation, state = self.claims("new-owner-claims-converted", [(a, ZERO, False), (c, ZERO, False)], state, self.f.newcomer)
        require(operation["status"] == "mined", "Current owner claim must execute")
        self.claims("new-owner-repeat-zero", [(a, ZERO, False), (c, ZERO, False)], state, self.f.newcomer)

    def faulty_royalty(self, id_, baseline):
        broken, healthy = self.f.currencies[-1], self.f.currencies[1]
        expected_broken = self.f.read(self.f.royalty, "claimable(uint256,address)", id_, broken)[0]
        require(expected_broken > 0, "Fault test needs funded royalty")
        self.control("fault-currency-enable", self.f.governance, broken, static("failFor(address)", self.f.royalty))
        mixed = [(id_, ZERO, False), (id_, healthy, True), (id_, broken, True)]
        selection = [{"token_id": str(i), "asset": asset, "royalty": royalty} for i, asset, royalty in mixed]
        fault_plan = self.planner_call("fault-currency-balance-read-selection", selection, self.f.owner)
        require(fault_plan["entries"][-1]["status"] in ("blocked", "unavailable"), "Faulty currency was mislabeled payable or zero")
        self.run("faulty-mixed-atomic-refusal", self.f.owner, self.f.claim_router, claim_data(mixed),
                 CLAIM_CAP, CLAIM_PADDING, expected_refusal=True)
        failed = self.state("faulty-mixed-refused-after")
        self.unchanged(baseline, failed)
        operation, state = self.claims("healthy-subset-after-fault", mixed[:-1], failed)
        require(operation["status"] == "mined", "Healthy subset must remain payable")
        self.control("fault-currency-repair", self.f.governance, broken, static("failFor(address)", ZERO))
        require(self.f.read(self.f.royalty, "claimable(uint256,address)", id_, broken)[0] == expected_broken,
                "Failed currency lost original entitlement")
        operation, state = self.claims("repaired-original-currency", mixed[-1:], state)
        require(operation["status"] == "mined", "Repaired original currency must pay")
        self.claims("repaired-currency-repeat-zero", mixed[-1:], state)

    def refusals(self, selected, baseline):
        cases = [("conversion-wrong-caller", self.f.owner, convert_data(self.f, selected)),
                 ("conversion-duplicate-id", self.f.keeper, convert_data(self.f, [selected[0], selected[0]])),
                 ("conversion-unsorted", self.f.keeper, convert_data(self.f, list(reversed(selected)))),
                 ("conversion-expired", self.f.keeper, convert_data(self.f, selected,
                     deadline=int(self.f.head()["timestamp"], 16) - 1)),
                 ("conversion-impossible-minimum", self.f.keeper, convert_data(self.f, selected, minimum=10**40))]
        for name, sender, data in cases:
            self.run(name, sender, self.rewards, data, CONVERSION_CAP, CONVERSION_PADDING, expected_refusal=True)
        self.unchanged(baseline, self.state("conversion-refusals-after"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", choices=("matrix", "completion"), default="matrix")
    args = parser.parse_args(argv)
    out = args.output.resolve()
    require(not out.exists(), "Use a new exclusive campaign directory")
    out.mkdir(parents=True)
    initial_source = Path(__file__).read_bytes()
    (out / "RUNNER_SOURCE.py").write_bytes(initial_source)
    # Importing only after argument validation allows syntax/help inspection
    # before the sibling fixture has finished implementation.
    from frozen_fixture import FrozenFixture
    started = time.time()
    result = None
    try:
        with FrozenFixture(out / "fixture") as fixture:
            campaign = Campaign(fixture, out)
            result = campaign.execute(args.phase)
            result["fixture_pins"] = fixture.pins
    except Exception as exc:
        result = {"schema": 1, "status": "campaign_failed", "error_type": type(exc).__name__,
                  "error": str(exc)[:4000], "production_approved": False}
        if "campaign" in locals():
            result.update(cases=campaign.cases, failures=campaign.failures)
    result.update(elapsed_seconds=round(time.time() - started, 3), runner_sha256=hashlib.sha256(initial_source).hexdigest(),
                  runner_source_unchanged=Path(__file__).read_bytes() == initial_source)
    save(out / "SUMMARY.json", result)
    print(json.dumps({"output": str(out), "cases": len(result.get("cases", [])),
                      "failures": result.get("failures", []), "status": result.get("status", "completed")}))
    return 1 if result.get("status") == "campaign_failed" or result.get("failures") else 0


if __name__ == "__main__":
    raise SystemExit(main())
