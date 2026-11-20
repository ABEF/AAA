"""Report-only qualification through the unchanged normal Projection boundary.

The caller supplies a separately authenticated, owned local fixture transport
and constructor/runtime manifest. This module has no node, endpoint selection,
signer, transaction submission, state override or Projection subclass. Fee and
clock declarations remain local fixture assumptions, never provider approval.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import time
from collections import Counter

from frontend_api.service import Projection, ZERO, _quantity
from frontend_api.transactions import Transactions
from zzz_ops.abi import address, calldata
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit


ROOT = Path(__file__).resolve().parents[3]
CAP = 12_000_000
LIMITS = {"request_seconds_limit": 25, "logical_rpc_limit": 1024,
          "http_post_limit": 2048, "maximum_selection": 32,
          "maximum_trials": 10, "claim_gas_limit": CAP,
          "claim_padding_percent": 20}
ROLES = (
    "access", "nft", "vault", "rewards", "royalties", "claim_router",
    "handoff", "vault_canonical", "principal_exit", "rewards_canonical",
    "seadrop_mint", "seadrop", "pools", "liquidity", "strategy", "budget",
    "portfolio_policy", "rebalance_confirmation", "balancing_router",
    "lp_balance_math", "lp_position_executor", "protocol_policy",
    "pool_manager", "state_view", "position_manager", "permit2",
)
SOURCE_PATHS = (
    "frontend_api/service.py", "frontend_api/portfolio_v6.py",
    "frontend_api/portfolio_v7.py", "frontend_api/lifecycle.py",
    "frontend_api/transactions.py", "frontend_api/transaction_gas.py",
    "frontend_api/claim_planner.py", "frontend_api/royalty_reporting.py",
    "zzz_ops/work_budget.py", "zzz_ops/abi.py", "zzz_ops/errors.py",
    "zzz_ops/rpc.py",
)
ALLOWED = frozenset(("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber",
    "eth_getBlockByHash", "eth_getCode", "eth_getBalance", "eth_call",
    "eth_estimateGas", "eth_gasPrice"))
_HASH = re.compile(r"0x[0-9a-f]{64}")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()


def source_pins():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_PATHS}


def build_configuration(contracts, assets, *, chain_id, deployment_block,
                        deployment_block_hash, expected_runtime_pins,
                        rpc_urls=None):
    """Use independently reviewed creation/runtime pins, not observed self-pins.

    Extra manifest roles are retained by the caller's construction evidence;
    the normal API's exact declared role set is selected here. Projection then
    validates all config types and checks every runtime/binding during the plan.
    """
    if not isinstance(contracts, dict) or not set(ROLES) <= set(contracts):
        raise ValueError("Normal fixture manifest lacks the exact26 API roles")
    if not isinstance(expected_runtime_pins, dict) or not set(ROLES) <= set(expected_runtime_pins):
        raise ValueError("Independent constructor/runtime pins required for every role")
    selected = {}
    for role in ROLES:
        value = expected_runtime_pins[role]
        if not isinstance(value, str) or _HASH.fullmatch(value) is None or int(value, 16) == 0:
            raise ValueError("Invalid independently authenticated runtime pin: " + role)
        selected[role] = {"address": address(contracts[role]), "code_hash": value}
    config = {"schema": 2, "chain_id": chain_id,
        "rpc_urls": list(rpc_urls or ["http://127.0.0.1:1"]),
        "deployment_block": deployment_block,
        "deployment_block_hash": deployment_block_hash,
        "confirmations": 1, "max_block_age_seconds": 120,
        "accounting_version": 7, "custody_version": 5,
        "protocol_policy_version": 1, "fee_intake_version": 1,
        "mint_integration_version": 2, "execution_price_version": 1,
        "royalty_reporting": {"schema": 5, "converter": None},
        "contracts": selected, "assets": copy.deepcopy(assets)}
    # Construction performs ordinary config validation, and performs no RPC.
    Projection(config)
    return config


def transaction_configuration(projection, *, max_gas_price_wei="1000000000000",
                              max_network_fee_wei="12000000000000000000"):
    return {"schema": 2, "chain_id": projection.chain,
        "projection_sha256": projection.identity,
        "fee_policy": {"estimate_includes_all_fees": True,
            "review_hash": "0x" + digest({"fixture": projection.identity,
                "policy": "report-only-normal-admission-12M-full20-local-fees"}),
            "max_gas_price_wei": max_gas_price_wei,
            "max_network_fee_wei": max_network_fee_wei,
            "max_gas_limit": str(CAP)}}


class ObservedReads:
    """Capture each logical read; production BudgetedRPC owns all work bounds.

    The owned fixture callable may return raw hex chain IDs, while normal Rpc
    returns integer chain IDs. This is the only positive-result normalization.
    Explicit negative controls retain both real and intercepted responses.
    """
    def __init__(self, call, *, control=None):
        if not callable(call):
            raise TypeError("An owned local read transport is required")
        self.transport, self.control = call, control
        self.records, self.matches = [], 0

    def call(self, method, params=None):
        if method not in ALLOWED:
            raise AssertionError("Normal-admission tool attempted a forbidden RPC method")
        params = [] if params is None else params
        request = {"jsonrpc": "2.0", "id": len(self.records) + 1,
                   "method": method, "params": copy.deepcopy(params)}
        row = {"requests": [request]}
        self.records.append(row)
        try:
            result = self.transport(method, params)
        except Exception as error:
            if isinstance(error, RemoteRPCError):
                wire = {"code": error.code, "reason": error.reason}
                converted = error
            else:
                raw = getattr(error, "error", None)
                if (isinstance(raw, dict) and type(raw.get("code")) is int and
                        getattr(error, "method", method) == method):
                    code = raw["code"]
                    reason = {-32602: "invalid_params", -32005: "rate_limited"}.get(code, "unclassified")
                    wire = {"code": code, "reason": reason}
                    converted = RemoteRPCError(method, code, reason)
                else:
                    # Avoid retaining raw transport text or a credentialed URL.
                    row["exception"] = {"type": type(error).__name__}
                    raise
            row["response"] = {"jsonrpc": "2.0", "id": request["id"], "error": wire}
            raise converted from None
        response = {"jsonrpc": "2.0", "id": request["id"], "result": copy.deepcopy(result)}
        if self.control is not None:
            replacement = self.control(method, copy.deepcopy(params), copy.deepcopy(result))
            if replacement is not None:
                row["upstream_response"] = response
                response = {**response, "result": replacement}
                self.matches += 1
                row["explicit_negative_interception"] = True
                result = replacement
        row["response"] = response
        if method == "eth_chainId":
            result = _quantity(result) if isinstance(result, str) else result
            if type(result) is not int or result <= 0:
                raise RpcError("Invalid owned fixture chain identity")
            row["delivered_result"] = result
        return result


def _validate_success(result, payload):
    rows = result["entries"]
    if (len(rows) != len(payload["claims"]) or
            [row["selection_index"] for row in rows] != list(range(len(rows)))):
        raise AssertionError("A normal plan lost or reordered an explicit selection")
    for row, claim in zip(rows, payload["claims"]):
        if any(row[key] != claim[key] for key in ("token_id", "asset", "royalty")):
            raise AssertionError("A normal plan changed an explicit claim identity")
    expected = [row["selection_index"] for row in rows
                if row["status"] not in ("zero", "in_next_batch")]
    if expected != [row["selection_index"] for row in result["remaining_claims"]]:
        raise AssertionError("A normal plan discarded an unresolved selection")
    if (result["planning"]["maximum_selection"] != LIMITS["maximum_selection"] or
            result["planning"]["maximum_trials"] != LIMITS["maximum_trials"] or
            result["planning"]["trial_count"] > LIMITS["maximum_trials"] or
            result["planning"]["simulation_gas_cap"] != str(CAP)):
        raise AssertionError("A normal plan changed its work/gas limits")
    draft = result["next_batch"]
    if draft is None:
        return
    gas = draft["network_gas"]
    estimate, padded = int(gas["estimated_units"]), int(gas["suggested_limit"])
    if not (padded == (estimate * 120 + 99) // 100 <= CAP and
            gas["configured_gas_limit"] == gas["effective_gas_limit"] == str(CAP) and
            gas["full_twenty_percent_headroom"] is True and
            result["planning"]["final_batch_revalidated"] is True):
        raise AssertionError("A normal plan lacks exact12M/full20% final admission")
    published = [row for row in rows if row["status"] == "in_next_batch"]
    operations = draft["claim_operations"]
    if len(published) != len(operations) or any(any(
            a[key] != b[key] for key in ("token_id", "asset", "royalty"))
            for a, b in zip(published, operations)):
        raise AssertionError("Normal plan classifications differ from draft calldata selection")
    if any(key in draft["transaction"] for key in ("gas", "nonce", "signed")):
        raise AssertionError("A normal plan grew a submission envelope")


def qualify_plan(rpc_call, configuration, payload, *, clock_timestamp, label,
                 control=None, control_description=None):
    """Capture one untouched normal plan; errors are evidence, never a fallback.

    Both real request time and the default logical-call limit remain enforced by
    production decorators. The explicitly fixed fixture wall time is recorded;
    it does not replace the monotonic25-second request deadline.
    """
    if type(clock_timestamp) is not int or clock_timestamp <= 0:
        raise ValueError("An explicit fixture block clock is required")
    if control is not None and not control_description:
        raise ValueError("Every intercepted negative control needs an explicit description")
    pins = source_pins()
    observed = ObservedReads(rpc_call, control=control)
    projection = Projection(copy.deepcopy(configuration), observed,
                            clock=lambda: clock_timestamp)
    policy = transaction_configuration(projection)
    transactions = Transactions(projection, policy)
    record = {"schema": 1, "label": label, "fixture_only": True,
        "projection_class": "frontend_api.service.Projection",
        "deployment_verifier": "frontend_api.service.Projection._verify_deployment",
        "projection_config": copy.deepcopy(configuration),
        "transaction_config": policy, "payload": copy.deepcopy(payload),
        "projection_clock_timestamp": clock_timestamp,
        "production_source_sha256": pins, **LIMITS,
        "normal_deployment_admission_replaced": False,
        "result_normalization": "eth_chainId canonical hex->int only",
        "rpc_wire_scope": "Logical-call envelopes with per-plan IDs; original transport envelopes are retained separately by the owned fixture.",
        "transport_scope": "Owned local injected read transport; normal Projection, Transactions and BudgetedRPC. "
            "Production HTTP Rpc chain-check/retry layer is not exercised by this callable.",
        "fee_scope": "Explicit local complete-fee declaration; not actual provider or Robinhood fee qualification.",
        "clock_scope": "Fixed fixture block wall time; unchanged real monotonic25-second request deadline.",
        "explicit_negative_control": control_description,
        "production_approved": False}
    started = time.monotonic()
    try:
        result = transactions.plan_claims(copy.deepcopy(payload))
    except (RpcError, ValueError) as error:
        record["error"] = {"type": type(error).__name__}
        if isinstance(error, WorkLimit):
            record["error"]["reason"] = error.reason
        elif isinstance(error, RemoteRPCError):
            record["error"].update(method=error.method, code=error.code, reason=error.reason)
    else:
        _validate_success(result, payload)
        record["result"] = result
    record.update(elapsed_seconds=time.monotonic() - started,
        rpc_count=len(observed.records),
        rpc_counts=dict(Counter(row["requests"][0]["method"] for row in observed.records)),
        rpc_wire=observed.records, interception_matches=observed.matches,
        production_source_sha256_after=source_pins())
    if pins != record["production_source_sha256_after"]:
        raise AssertionError("Production admission/planning source changed during the request")
    if record["rpc_count"] > LIMITS["logical_rpc_limit"]:
        raise AssertionError("Observed normal plan exceeded the unchanged logical RPC budget")
    return record


def runtime_pin_control(configuration, role="lp_balance_math"):
    """Change only a normal-only helper's expected pin in a separate config."""
    if role not in ROLES or role in ("nft", "rewards", "royalties", "claim_router", "principal_exit", "vault"):
        raise ValueError("Select a helper absent from the earlier six-contract seam")
    changed = copy.deepcopy(configuration)
    old = changed["contracts"][role]["code_hash"]
    changed["contracts"][role]["code_hash"] = "0x" + ("1" if old[2] != "1" else "2") + old[3:]
    return changed


def scalar_control(configuration, role, signature, replacement, *, occurrence):
    """Explicit captured-wire fault; the real upstream response is preserved.

    occurrence1 can model an unsealed observation. A later selected occurrence
    can prove final control/lifecycle reads do not reuse a prior valid result.
    """
    if role not in ROLES or type(occurrence) is not int or occurrence < 1:
        raise ValueError("Exact role and positive scalar-read occurrence required")
    if type(replacement) is not int or not 0 <= replacement < 1 << 256:
        raise ValueError("Scalar replacement must be a uint256 word")
    target = configuration["contracts"][role]["address"]
    wanted = {"to": target, "data": calldata(signature)}
    seen = 0
    def intercept(method, params, result):
        nonlocal seen
        if method == "eth_call" and len(params) == 2 and params[0] == wanted:
            seen += 1
            if seen == occurrence:
                return "0x" + f"{replacement:064x}"
        return None
    description = {"kind": "explicit_intercepted_scalar_negative",
        "role": role, "target": target, "signature": signature,
        "replacement": "0x" + f"{replacement:064x}", "occurrence": occurrence,
        "upstream_real_response_retained": True}
    return intercept, description
