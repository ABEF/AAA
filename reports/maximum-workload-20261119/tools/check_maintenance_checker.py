"""NEW offline negative controls for the populated maintenance trace verifier.

Synthetic event/call traces test the verifier itself, not production execution.
No compiler, network, signer, application suite or existing environment runs.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256


def run():
    path = HERE / "verify_maintenance.py"
    spec = importlib.util.spec_from_file_location("new_populated_maintenance_checker", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    zero = "0x" + "0" * 40
    addr = lambda value: "0x" + f"{value:040x}"
    pins = {key: addr(i + 1) for i, key in enumerate(("vault", "fees", "rewards", "liquidity",
        "position_manager", "membership", "oracle", "reference", "independent_reference", "budget", "pool_manager"))}
    base = SimpleNamespace(ZERO=zero, topic=lambda text: "0x" + keccak256(text.encode()).hex(),
                           keccak256=keccak256, quantity=lambda raw: int(raw, 16))
    word = lambda value: f"{(int(value,16) if isinstance(value,str) else value) % (1 << 256):064x}"
    selector = lambda text: base.topic(text)[:10]

    def log(emitter, event, indexes, values):
        return {"address": emitter, "topics": [base.topic(event)] + ["0x" + word(i) for i in indexes],
                "data": "0x" + "".join(word(i) for i in values)}

    bucket = 7
    key = [zero, addr(31), 10020, 200, zero]
    pool_id = "0x" + keccak256(bytes.fromhex("".join(word(i) for i in key))).hex()
    case = {"label": "max1000-lp2-harvest", "pins": pins, "shared_bucket": bucket}
    before = {"royalty": addr(30), "zzz": addr(31), "main": 11, "residual": 12, "pool_id": pool_id,
              "fee_books": {asset: {"dust": 0, "compound": 0, "buyback": 0, "liability": 0}
                            for asset in (zero, addr(31))}}

    def physical(lp_id, amount):
        packed = amount << 128
        return {"from": pins["position_manager"], "to": pins["pool_manager"], "type": "CALL", "value": "0x0",
                "input": selector("modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)") +
                "".join(word(i) for i in key + [-100, 100, 0, lp_id, 320, 0]),
                "output": "0x" + word(packed) + word(packed)}

    credit = {"from": pins["fees"], "to": pins["rewards"], "type": "CALL", "value": hex(18), "output": "0x",
              "input": selector("creditPool(uint256,address,uint256,uint256)") +
              "".join(word(i) for i in (bucket, zero, 16, 2)),
              "logs": [log(pins["rewards"], "PoolRewardsCredited(uint256,address,uint256,uint256)", [bucket, zero], [16, 2])]}
    allocate = {"from": pins["vault"], "to": pins["fees"], "type": "CALL", "value": hex(21), "output": "0x",
                "input": selector("allocate(uint256,address,uint256)") + "".join(word(i) for i in (bucket, zero, 21)),
                "calls": [credit], "logs": [log(pins["fees"], "FeesAllocated(uint256,address,uint256,uint256)",
                                                  [bucket, zero], [20, 1])]}
    trace = {"from": addr(40), "to": pins["vault"], "type": "CALL", "value": "0x0", "output": "0x",
             "input": selector("collectFees(uint256,uint256)") + word(bucket) + word(10100),
             "calls": [physical(11, 10), physical(12, 11), allocate],
             "logs": [log(pins["vault"], "FeesCollected(uint256,uint256,uint256)", [bucket], [21, 0])]}
    results = []

    def check(name, candidate, selected_case=case, refuse=False):
        try:
            result = module.verify_financial(base, candidate, selected_case, lambda *args, **kwargs: None, before)
            assert not refuse, "Mutated trace was incorrectly admitted"
            assert result["verified"]
            results.append({"control": name, "passed": True, "expected": "admit"})
        except ValueError as error:
            assert refuse, (name, str(error))
            results.append({"control": name, "passed": True, "expected": "refuse", "reason": str(error)})

    check("exact-two-leg-funded-80-10-5-5-plus-one-unit-dust", trace)
    changed = copy.deepcopy(trace)
    changed["calls"][2]["calls"][0]["input"] = selector("creditPool(uint256,address,uint256,uint256)") + \
        "".join(word(i) for i in (bucket, zero, 15, 3))
    check("incorrect-owner-collective-split", changed, refuse=True)
    changed = copy.deepcopy(trace); changed["calls"][2]["logs"][0]["data"] = "0x" + word(20) + word(0)
    check("missing-carried-unit", changed, refuse=True)
    changed = copy.deepcopy(trace); changed["calls"].append(copy.deepcopy(credit))
    check("unfunded-credit-outside-allocation", changed, refuse=True)
    changed = copy.deepcopy(trace)
    changed["calls"].append({"from": pins["vault"], "to": before["royalty"], "type": "STATICCALL", "input": "0x", "output": "0x"})
    check("hidden-royalty-dependency", changed, refuse=True)
    changed = copy.deepcopy(trace)
    changed["logs"].append(log(pins["position_manager"], "Transfer(address,address,uint256)", [zero, addr(40), 99], []))
    check("position-nft-minted-to-outsider", changed, refuse=True)
    changed = copy.deepcopy(trace); changed["calls"][2]["value"] = "0x0"
    check("missing-native-fee-funding", changed, refuse=True)
    changed = copy.deepcopy(trace)
    changed["calls"] = [physical(11, 0), physical(12, 0)]
    changed["logs"] = [log(pins["vault"], "FeesCollected(uint256,uint256,uint256)", [bucket], [0, 0])]
    check("repeat-harvest-with-no-new-income", changed, {**case, "label": "max1000-lp2-harvest-no-new-fees"})
    check("repeat-harvest-phantom-income", trace, {**case, "label": "max1000-lp2-harvest-no-new-fees"}, True)
    changed = copy.deepcopy(trace); changed["calls"].pop(1)
    check("missing-physical-residual-collection", changed, refuse=True)
    changed = copy.deepcopy(trace); changed["calls"][1]["output"] = "0x" + word(12 << 128) * 2
    check("per-leg-accrual-does-not-match-funded-receipt", changed, refuse=True)
    changed = copy.deepcopy(trace); changed["calls"][1]["output"] = "0x" + word(12 << 128) + word(11 << 128)
    check("principal-mixed-into-zero-liquidity-collection", changed, refuse=True)
    changed = copy.deepcopy(trace)
    changed["calls"][1]["input"] = changed["calls"][1]["input"][:10] + \
        "".join(word(i) for i in [zero, addr(32), 10020, 200, zero, -100, 100, 0, 12, 320, 0])
    check("physical-collection-from-another-pool", changed, refuse=True)
    for name, action in (("strict-static-input-count", lambda: module.words("0x" + word(1), 2)),
                         ("dirty-address-rejected", lambda: module.address(word(1 << 160)))):
        try:
            action(); raise AssertionError("Malformed input accepted")
        except ValueError as error:
            results.append({"control": name, "passed": True, "expected": "refuse", "reason": str(error)})
    return {"schema": 1, "scope": "NEW synthetic cold financial-checker controls, no EVM/network/compiler/application tests",
            "checker_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "control_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "controls": results, "all_passed": all(row["passed"] for row in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    owned = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/maximum-workload-20261119").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(owned) or output.exists():
        raise ValueError("Use one NEW exclusive owned control output")
    result = run(); output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"controls": len(result["controls"]), "passed": result["all_passed"],
                      "output": str(output), "checker_sha256": result["checker_sha256"]}))


if __name__ == "__main__":
    main()
