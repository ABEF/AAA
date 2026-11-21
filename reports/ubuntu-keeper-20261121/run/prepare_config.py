"""Build a NEW private normal-keeper candidate for an owned loopback lab only."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re

INSTANCES_SHA = "e94a9dc5d4f3f04211ad77e62612b2284301584c3e363203198311d34d128e56"
CORE = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
STATE = "0xf3334192d15450cdd385c8b70e03f9a6bd9e673b"
CORE_SHA = "0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626"
STATE_SHA = "0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instances", required=True, type=Path)
    p.add_argument("--sender", required=True)
    p.add_argument("--runtime", required=True, type=Path)
    p.add_argument("--cast", required=True, type=Path)
    p.add_argument("--keystore", required=True, type=Path)
    p.add_argument("--password-file", required=True, type=Path)
    args = p.parse_args()
    assert os.name == "posix" and os.getuid() != 0 and re.fullmatch("0x[0-9a-f]{40}", args.sender)
    assert args.runtime.is_absolute() and args.runtime.is_dir()
    st = args.runtime.stat()
    assert st.st_uid == os.getuid() and st.st_mode & 0o077 == 0
    lab = args.runtime.resolve().parent
    assert re.fullmatch(r"/opt/popl-ubuntu-20261121-[0-9a-f]{8}", str(lab))
    assert args.runtime.name in ("runtime", "dryrun")
    for secret in (args.keystore, args.password_file):
        stat = secret.stat()
        assert secret.is_absolute() and secret.is_file() and not secret.is_symlink()
        assert stat.st_uid == os.getuid() and stat.st_mode & 0o077 == 0
        assert secret.resolve().is_relative_to(lab / "secrets")
    assert args.cast.resolve().is_relative_to(lab / "bin")
    assert hashlib.sha256(args.cast.read_bytes()).hexdigest() == "d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970"
    assert args.instances.resolve().is_relative_to(lab / "public")
    raw = args.instances.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == INSTANCES_SHA
    rows = json.loads(raw)
    assert len(rows) == 39 and len({r["role"] for r in rows}) == 39
    addresses = {r["role"]: r["address"] for r in rows}
    hashes = {r["role"]: r["runtime_keccak256"] for r in rows}
    assert args.sender not in set(addresses.values()) | {"0x000000000000000000000000000000000000a0a0"}
    roles = ("access", "vault", "strategy", "fees", "compounder", "buyback", "pools", "rewards",
             "liquidity", "balancing_router", "lp_balance_math", "lp_position_executor",
             "portfolio_policy", "protocol_policy", "rebalance_confirmation", "oracle", "contribution_pricing")
    contracts = {name: addresses[name] for name in roles}
    pins = {name: hashes[name] for name in roles}
    contracts.update(principal_exit=addresses["migration"], pool_manager=CORE, state_view=STATE)
    pins.update(principal_exit=hashes["migration"], pool_manager=CORE_SHA, state_view=STATE_SHA,
                idle_compounding_budget=hashes["migration_budget"])
    config = {"chain_id": 4663, "accounting_model": "shared-pools-v2", "accounting_version": 7,
              "custody_version": 5, "protocol_policy_version": 1, "portfolio_version": 2,
              "maintenance_policy_version": 3, "rebalance_confirmation_version": 3,
              "fee_intake_version": 1, "lp_routing_version": 3, "execution_quality_version": 1,
              "execution_price_version": 1, "royalty_settlement_version": 4,
              "rpc_urls": ["http://127.0.0.1:18547", "http://127.0.0.1:18548"], "sender": args.sender,
              "contracts": contracts, "code_hashes": pins,
              "idle_compounding_budget": addresses["migration_budget"],
              "reviewed_for_live_use": True, "cast_binary": str(args.cast),
              "keystore": str(args.keystore), "password_file": str(args.password_file),
              "interval_seconds": 60, "confirmations": 1, "max_gas_limit": 24000000,
              "max_gas_price_wei": "5000000000", "max_transaction_cost_wei": "10000000000000000",
              "max_daily_cost_wei": "50000000000000000", "l1_fee_allowance_wei": "0",
              "receipt_fee_policy": "included", "revert_cooldown_seconds": 3600,
              "state_path": str(args.runtime / "state.json"), "health_path": str(args.runtime / "health.json"),
              "lock_path": str(args.runtime / "keeper.lock"),
              "bucket_discovery": {"maximum_count": 4, "max_per_cycle": 4},
              "maintenance": {"compound": False, "compound_idle": False, "harvest": True,
                              "minimum_liquidity": 1, "harvest_interval_seconds": 3600},
              "bucket_overrides": {}, "adaptive_range": {"enabled": False},
              "royalty_conversion": {"enabled": False}, "lp_conversion": {"enabled": False},
              "metadata_refresh": {"enabled": False}, "principal_distribution": {"enabled": False},
              "buybacks": []}
    path = args.runtime / "config.json"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"schema": 1, "configuration_sha256": hashlib.sha256(json.dumps(
        config, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "sender": args.sender,
        "loopback_only": True, "new_state_required": True, "production_approved": False}))


if __name__ == "__main__":
    main()
