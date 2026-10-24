#!/usr/bin/env python3
"""Read-only selected ETH/ZZZ pool evidence. Never signs or sends transactions.

Pins all state reads to a hash-checked block. Observations are not release approval
or an independent token/venue audit. RPC credentials are never included in output.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.abi import keccak256

POOL = "0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b"
ZZZ = "0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a"
ADDRESSES = {
    "core": "0x8366a39cc670b4001a1121b8f6a443a643e40951",
    "positions": "0x58daec3116aae6d93017baaea7749052e8a04fa7",
    "state": "0xf3334192d15450cdd385c8b70e03f9a6bd9e673b",
    "permit2": "0x000000000022d473030f116ddee9f6b43ac78ba3",
    "weth": "0x0bd7d308f8e1639fab988df18a8011f41eacad73",
    "zzz": ZZZ,
}


def rpc(url, calls):
    payload = [dict(jsonrpc="2.0", id=i, method=m, params=p) for i, (m, p) in enumerate(calls)]
    req = urllib.request.Request(url, json.dumps(payload).encode(), {
        "Content-Type": "application/json", "User-Agent": "PoPL-readonly-hookless-verification/1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        replies = json.load(response)
    if not isinstance(replies, list) or len(replies) != len(payload):
        raise ValueError("Incomplete RPC batch")
    by_id = {r["id"]: r for r in replies}
    if set(by_id) != set(range(len(payload))):
        raise ValueError("Duplicate or mismatched RPC IDs")
    if any("error" in r or "result" not in r for r in replies):
        raise ValueError("Public read failed; no substituted evidence")
    return [by_id[i]["result"] for i in range(len(payload))]


def selector(signature):
    return "0x" + keccak256(signature.encode())[:4].hex()


def words(encoded):
    if not isinstance(encoded, str) or not encoded.startswith("0x") or (len(encoded)-2) % 64:
        raise ValueError("Malformed static ABI")
    return [int(encoded[i:i+64], 16) for i in range(2, len(encoded), 64)]


def observe(url, block, expected_hash=None):
    chain, header = rpc(url, [("eth_chainId", []), ("eth_getBlockByNumber", [hex(block), False])])
    if int(chain, 16) != 4663 or header is None or int(header["number"], 16) != block:
        raise ValueError("Wrong chain or missing pinned block")
    if expected_hash is not None and header["hash"].lower() != expected_hash.lower():
        raise ValueError("Pinned block hash mismatch")
    tag = hex(block)
    init_sig = "0x" + keccak256(b"Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex()
    reads = [("eth_getLogs", [{"address": ADDRESSES["core"], "fromBlock": hex(65181311),
              "toBlock": hex(65181311), "topics": [init_sig, POOL]}])]
    reads += [("eth_getCode", [a, tag]) for a in ADDRESSES.values()]
    specs = [("slot0", "state", "getSlot0(bytes32)", POOL[2:]),
             ("activeLiquidity", "state", "getLiquidity(bytes32)", POOL[2:]),
             ("positionManagerCore", "positions", "poolManager()", ""),
             ("positionManagerPermit2", "positions", "permit2()", ""),
             ("positionManagerWrapper", "positions", "WETH9()", ""),
             ("stateCore", "state", "poolManager()", ""),
             ("protocolFeeController", "core", "protocolFeeController()", ""),
             ("managerOwner", "core", "owner()", "")]
    reads += [("eth_call", [{"to": ADDRESSES[target], "data": selector(sig)+arg}, tag])
              for _, target, sig, arg in specs]
    result = rpc(url, reads)
    if len(result[0]) != 1:
        raise ValueError("Missing or ambiguous initialization")
    log = result[0][0]
    key = [0, int(ZZZ, 16), 10020, 200, 0]
    if ("0x"+keccak256(b"".join(x.to_bytes(32, "big") for x in key)).hex() != POOL or
        [int(x, 16) for x in log["topics"][2:]] != key[:2] or words(log["data"])[:3] != key[2:]):
        raise ValueError("Unexpected native/static/hookless pool key")
    contracts = {}
    for (name, address), code in zip(ADDRESSES.items(), result[1:7]):
        if code == "0x":
            raise ValueError("Missing deployed dependency")
        contracts[name] = {"address": address, "runtime_keccak": "0x"+keccak256(bytes.fromhex(code[2:])).hex()}
    values = {spec[0]: words(value) for spec, value in zip(specs, result[7:])}
    for field, target in [("positionManagerCore", "core"), ("positionManagerPermit2", "permit2"),
                          ("positionManagerWrapper", "weth"), ("stateCore", "core")]:
        if values[field] != [int(ADDRESSES[target], 16)]:
            raise ValueError("Wrong dependency wiring")
    slot = values["slot0"]
    if len(slot) != 4 or slot[0] == 0 or slot[3] != 10020:
        raise ValueError("Unexpected pool price/static LP fee")
    protocols = [slot[2] & 4095, slot[2] >> 12]
    if any(x > 1000 for x in protocols):
        raise ValueError("Invalid protocol fee")
    ending = rpc(url, [("eth_getBlockByNumber", [tag, False])])[0]
    if ending is None or ending["hash"] != header["hash"]:
        raise ValueError("Canonical block changed during observation")
    return dict(read_only=True, observed_at_utc=datetime.now(timezone.utc).isoformat(), chain_id=4663,
                block=block, block_hash=header["hash"], pool_id=POOL, currencies=["0x"+"0"*40, ZZZ],
                hook="0x"+"0"*40, static_lp_fee_pips=10020, tick_spacing=200,
                protocol_fee_pips=protocols,
                combined_fee_pips=[p+10020-p*10020//1000000 for p in protocols],
                active_liquidity=str(values["activeLiquidity"][0]),
                protocol_fee_controller="0x"+format(values["protocolFeeController"][0], "040x"),
                manager_owner="0x"+format(values["managerOwner"][0], "040x"),
                creation_tx=log["transactionHash"], contracts=contracts,
                release_approved=False, limits="No independent USD feeds, routes, liquidity valuation or audit qualified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", default="https://rpc.mainnet.chain.robinhood.com")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--expected-hash")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.rpc, args.block, args.expected_hash)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
