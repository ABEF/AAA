"""Report-only real-EVM claim planning with an explicit full-admission seam.

The parent campaign supplies an already verified, owned local RPC callable.
This module has no endpoint, node, signing, send, impersonation or file-writing
interface. It runs the production Transactions/ClaimPlanner directly. Its one
intentional seam replaces COMPLETE deployment/profile/lifecycle admission: the
historical maximum-state fixture has typed Access/Registry doubles, not the
normal sealed construction graph. Runtime and selected ledger/helper bindings,
all admitted currency identities, current ownership, claim views, simulations,
estimates, fee/balance bounds and canonical snapshot checks remain real reads.
This evidence must never be described as full production API admission.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from frontend_api.service import (Asset, Contract, Projection, ProjectionError,
                                 ZERO, _quantity)
from frontend_api.transactions import Transactions, MAX_CLAIMS
from frontend_api.claim_planner import MAX_TRIALS
from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.errors import RemoteRPCError, RpcError
from zzz_ops.work_budget import BudgetedRPC

CAP = 12_000_000
REQUIRED = frozenset(("nft", "rewards", "royalties", "claim_router", "principal_exit"))
ALLOWED = frozenset(("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber",
                     "eth_getBlockByHash", "eth_getCode", "eth_getBalance",
                     "eth_call", "eth_estimateGas", "eth_gasPrice"))


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


class ObservedRPC:
    """Normalize only chain ID; retain sanitized error categories and public logs."""
    def __init__(self, call):
        if not callable(call):
            raise TypeError("An owned parent RPC callable is required")
        self.transport, self.records = call, []

    def call(self, method, params=None):
        if method not in ALLOWED:
            raise AssertionError("Report-only planner attempted a forbidden RPC method")
        params = params or []
        row = {"method": method, "parameters_sha256": _digest(params)}
        if method in ("eth_call", "eth_estimateGas") and params and "from" in params[0]:
            row["execution"] = copy.deepcopy(params[0])
        self.records.append(row)
        try:
            result = self.transport(method, params)
        except RpcError as error:
            row["error"] = type(error).__name__
            raise
        except Exception as error:
            # The owned campaign transports expose structured RPCError/RPCFailure.
            # Never parse its message or reinterpret transport failures as EVM.
            wire = getattr(error, "error", None)
            if (type(error).__name__ in ("RPCFailure", "RPCError") and
                    getattr(error, "method", None) == method and isinstance(wire, dict) and
                    type(wire.get("code")) is int):
                code = wire["code"]
                reason = {-32602: "invalid_params", -32005: "rate_limited"}.get(code, "unclassified")
                row["error"] = {"code": code, "reason": reason}
                raise RemoteRPCError(method, code, reason) from None
            row["error"] = type(error).__name__
            raise
        if method == "eth_chainId":
            result = _quantity(result) if isinstance(result, str) else result
            if type(result) is not int or result <= 0:
                raise ProjectionError("Invalid owned fixture chain identity")
        row.update(response_sha256=_digest(result),
                   response_json_bytes=len(json.dumps(result, separators=(",", ":")).encode()))
        if method in ("eth_estimateGas", "eth_gasPrice", "eth_getBalance"):
            row["quantity"] = result
        return result


def build_manifest(rpc_call, contracts, *,
                   max_gas_price_wei="1000000000000",
                   max_network_fee_wei="12000000000000000000"):
    """Capture the fixture, not independently approve its deployment/source graph."""
    if not REQUIRED <= set(contracts) or set(contracts) - REQUIRED - {"vault"}:
        raise ValueError("Exact required fixture contracts and optional vault are required")
    rpc = ObservedRPC(rpc_call)
    pins = {key: address(value) for key, value in contracts.items()}
    if len(set(pins.values())) != len(pins):
        raise ValueError("Fixture contract identities must be distinct")
    chain = rpc.call("eth_chainId", [])
    head = rpc.call("eth_getBlockByNumber", ["latest", False])
    number, timestamp = _quantity(head["number"]), _quantity(head["timestamp"])
    block = {"blockHash": head["hash"], "requireCanonical": True}
    def words(target, signature, *args):
        return decode_words(rpc.call("eth_call", [{"to": target,
                            "data": calldata(signature, *args)}, block]))
    def runtime(target):
        raw = rpc.call("eth_getCode", [target, block])
        if not isinstance(raw, str) or len(raw) <= 2:
            raise ValueError("Fixture runtime is missing")
        return "0x" + keccak256(bytes.fromhex(raw[2:])).hex()
    objects = {key: {"address": target, "code_hash": runtime(target)}
               for key, target in pins.items()}
    assets = set()
    for role, maximum in (("rewards", 2), ("royalties", 65)):
        count = int(words(pins[role], "assetCount()")[0], 16)
        if not 1 <= count <= maximum:
            raise ValueError("Fixture asset count differs from current profile")
        for index in range(count):
            value = words(pins[role], "assets(uint256)", index)[0]
            if int(value[:24], 16):
                raise ValueError("Noncanonical fixture asset identity")
            assets.add("0x" + value[-40:])
    descriptors = []
    for index, target in enumerate(sorted(assets)):
        descriptors.append({"address": target,
            "decimals": 18 if target == ZERO else int(words(target, "decimals()")[0], 16),
            "symbol": "ETH" if target == ZERO else "FIXTURE" + str(index),
            "code_hash": None if target == ZERO else runtime(target)})
    return {"schema": 1, "fixture_only": True,
        "admission_seam": "Full normal deployment/profile/lifecycle admission is NOT exercised",
        "chain_id": chain, "deployment_block": number,
        "deployment_block_hash": head["hash"], "clock_timestamp": timestamp,
        "contracts": objects, "assets": descriptors,
        "max_gas_price_wei": max_gas_price_wei,
        "max_network_fee_wei": max_network_fee_wei,
        "capture_rpc_counts": dict(Counter(row["method"] for row in rpc.records))}


class FixtureProjection(Projection):
    def __init__(self, rpc, manifest):
        if manifest.get("schema") != 1 or manifest.get("fixture_only") is not True:
            raise ValueError("Explicit fixture-only manifest required")
        if not REQUIRED <= set(manifest["contracts"]):
            raise ValueError("Fixture manifest lacks selected ledger identities")
        self.rpc = BudgetedRPC(rpc)
        self.chain = manifest["chain_id"]
        self.start, self.start_hash = manifest["deployment_block"], manifest["deployment_block_hash"]
        self.clock = lambda: manifest["clock_timestamp"]
        self.confirmations, self.max_age = 1, 120
        self.accounting_version, self.custody_version = 7, 5
        self.mint_integration_version, self.execution_price_version = 2, 1
        self.contracts = {key: Contract(**value) for key, value in manifest["contracts"].items()}
        self.assets = {item["address"]: Asset(**item) for item in manifest["assets"]}
        self.royalty_reporting = SimpleNamespace(schema=5)
        self.identity = _digest(manifest)

    def _verify_deployment(self, block, *, allow_locked=False):
        # Explicit fixture seam, NEVER a replacement production admission path.
        for item in self.contracts.values():
            self._code(item.address, item.code_hash, block)
        for role, method, expected in (
                ("nft", "royaltyRewards()", "royalties"),
                ("nft", "claimRouter()", "claim_router"),
                ("royalties", "nft()", "nft"),
                ("claim_router", "nft()", "nft"),
                ("claim_router", "royalties()", "royalties")):
            if self._addr(role, method, block=block) != self.contracts[expected].address:
                raise ProjectionError("Real fixture ledger/helper binding differs")
        if self._uint("rewards", "LP_ALLOCATION_VERSION()", block=block) != 1:
            raise ProjectionError("Real fixture does not expose exact LP allocation1")
        if self._uint("royalties", "ROYALTY_SETTLEMENT_VERSION()", block=block) != 4:
            raise ProjectionError("Real fixture does not expose original-currency royalty4")
        if "vault" in self.contracts and self._uint("vault", "ACCOUNTING_VERSION()", block=block) != 7:
            raise ProjectionError("Real fixture Vault is not accounting7")
        return {"state": "operating", "fixture_admission_seam": True,
                "new_economic_work_available_by_lifecycle": None,
                "normal_deployment_admission_verified": False}


def qualify_plan(rpc_call, manifest, selection, *, wallet):
    """Return all classifications plus the actual fresh12M/full20% unsigned plan."""
    root = Path(__file__).resolve().parents[3]
    paths = ('frontend_api/claim_planner.py', 'frontend_api/service.py',
             'frontend_api/transactions.py', 'frontend_api/transaction_gas.py')
    source_pins = {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}
    rpc = ObservedRPC(rpc_call)
    p = FixtureProjection(rpc, manifest)
    config = {"schema": 2, "chain_id": p.chain, "projection_sha256": p.identity,
        "fee_policy": {"estimate_includes_all_fees": True,
            "review_hash": "0x" + _digest({"fixture": p.identity, "policy": "12M-full20-local-only"}),
            "max_gas_price_wei": manifest["max_gas_price_wei"],
            "max_network_fee_wei": manifest["max_network_fee_wei"],
            "max_gas_limit": str(CAP)}}
    result = Transactions(p, config).plan_claims({"action": "claim", "wallet": address(wallet),
                                                "claims": copy.deepcopy(selection)})
    entries = result["entries"]
    if len(entries) != len(selection) or [row["selection_index"] for row in entries] != list(range(len(selection))):
        raise AssertionError("Planner lost or reordered an explicit selection")
    for row, original in zip(entries, selection):
        if any(row[key] != original[key] for key in ("token_id", "asset", "royalty")):
            raise AssertionError("Planner changed an explicit claim identity")
    remaining = [row["selection_index"] for row in entries if row["status"] not in ("zero", "in_next_batch")]
    if remaining != [row["selection_index"] for row in result["remaining_claims"]]:
        raise AssertionError("Planner silently discarded an unresolved selection")
    planning = result["planning"]
    if not (planning["maximum_selection"] == MAX_CLAIMS == 32 and
            planning["maximum_trials"] == MAX_TRIALS == 10 and
            planning["trial_count"] <= MAX_TRIALS and
            planning["simulation_gas_cap"] == str(CAP)):
        raise AssertionError("Planner changed the selected work/gas limits")
    draft = result["next_batch"]
    if draft is not None:
        gas = draft["network_gas"]
        estimate, padded = int(gas["estimated_units"]), int(gas["suggested_limit"])
        if not (padded == (estimate * 120 + 99) // 100 <= CAP and estimate <= CAP * 100 // 120 and
                gas["full_twenty_percent_headroom"] is True and
                gas["configured_gas_limit"] == gas["effective_gas_limit"] == str(CAP)):
            raise AssertionError("Published batch lacks unchanged12M/full20% admission")
        if any(key in draft["transaction"] for key in ("gas", "nonce", "signed")):
            raise AssertionError("Unsigned preparer grew a submission envelope")
        published = [row for row in entries if row["status"] == "in_next_batch"]
        actual = draft["claim_operations"]
        if len(actual) != len(published) or any(
                any(a[key] != b[key] for key in ("token_id", "asset", "royalty"))
                for a, b in zip(actual, published)):
            raise AssertionError("Published calldata selection differs from classifications")
        if not planning["final_batch_revalidated"]:
            raise AssertionError("Fresh final preparation was omitted")
    execution = [row for row in rpc.records if "execution" in row]
    if any(row["execution"].get("gas") != hex(CAP) or
           row["execution"].get("to") != p.contracts["claim_router"].address for row in execution):
        raise AssertionError("Real simulations/estimates escaped the exact router12M envelope")
    if source_pins != {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}:
        raise AssertionError("Production planner/preparation source changed during this call")
    return {"schema": 1, "fixture_only": True, "manifest_sha256": p.identity,
        "normal_deployment_admission_verified": False,
        "seams": ["complete normal deployment/profile/lifecycle admission",
                  "controlled fixture block time and conventional token fixtures",
                  "local complete-fee declaration is not Robinhood fee qualification"],
        "policy": config, "plan": result,
        "rpc_counts": dict(Counter(row["method"] for row in rpc.records)),
        "execution_rpc_count": len(execution), "rpc_records": rpc.records,
        "production_source_sha256": source_pins,
        "production_source_unchanged_during_this_call": True,
        "request_local_runtime_proof_reuse": 1,
        "reused_unchanged_production_modules": ["frontend_api/service.py",
            "frontend_api/transactions.py", "frontend_api/transaction_gas.py"],
        "production_approved": False}
