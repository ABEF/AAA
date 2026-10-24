#!/usr/bin/env python3
"""Read-only selected ETH/ZZZ pool evidence. Never signs or sends transactions.

Pins all state reads to a hash-checked block. Observations are not release approval
or an independent token/venue audit. RPC credentials are never included in output.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
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
EXPECTED_RUNTIME_HASHES = {
    "core": "0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626",
    "positions": "0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2",
    "state": "0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6",
    "permit2": "0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca",
    "weth": "0x5706be52f64875fee65a2cec0d80e47a23d8793cbe85d214b48445e2d05f5353",
    "zzz": "0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597",
}
MAX_RESPONSE = 2 * 1024 * 1024
READ_METHODS = frozenset(("eth_chainId", "eth_getBlockByNumber", "eth_getLogs", "eth_getCode", "eth_call"))
INITIALIZATION_BLOCK = 65181311
INITIALIZATION_TX = "0x0752dc07e3eb6007b548ec58acdc273bdd6670762ce8f2789a40e64d1c46cd04"


def rpc(url, calls):
    if not isinstance(calls, list) or not 1 <= len(calls) <= 32 or any(
        m not in READ_METHODS or not isinstance(p, list) for m, p in calls
    ):
        raise ValueError("Invalid read-only RPC batch")
    payload = [dict(jsonrpc="2.0", id=i, method=m, params=p) for i, (m, p) in enumerate(calls)]
    req = urllib.request.Request(url, json.dumps(payload).encode(), {
        "Content-Type": "application/json", "User-Agent": "PoPL-readonly-hookless-verification/1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("RPC response exceeds observation limit")
    replies = json.loads(raw)
    if not isinstance(replies, list) or len(replies) != len(payload):
        raise ValueError("Incomplete RPC batch")
    by_id = {}
    for reply in replies:
        if (not isinstance(reply, dict) or reply.get("jsonrpc") != "2.0" or
            type(reply.get("id")) is not int or not 0 <= reply["id"] < len(payload) or
            set(reply) != {"jsonrpc", "id", "result"} or reply["id"] in by_id):
            raise ValueError("Invalid RPC response identity or failed read")
        by_id[reply["id"]] = reply
    return [by_id[i]["result"] for i in range(len(payload))]


def selector(signature):
    return "0x" + keccak256(signature.encode())[:4].hex()


def words(encoded):
    if (not isinstance(encoded, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", encoded) or
        (len(encoded)-2) % 64):
        raise ValueError("Malformed static ABI")
    return [int(encoded[i:i+64], 16) for i in range(2, len(encoded), 64)]


def observe(url, block, expected_hash=None):
    if type(block) is not int or not INITIALIZATION_BLOCK <= block < 2**64:
        raise ValueError("Invalid observation block")
    if expected_hash is not None and not re.fullmatch(r"0x[0-9a-fA-F]{64}", expected_hash):
        raise ValueError("Invalid expected block hash")
    chain, header = rpc(url, [("eth_chainId", []), ("eth_getBlockByNumber", [hex(block), False])])
    if (not isinstance(chain, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", chain) or
        int(chain, 16) != 4663 or not isinstance(header, dict) or
        header.get("number") != hex(block) or not isinstance(header.get("hash"), str) or
        not re.fullmatch(r"0x[0-9a-fA-F]{64}", header["hash"])):
        raise ValueError("Wrong chain or missing pinned block")
    if expected_hash is not None and header["hash"].lower() != expected_hash.lower():
        raise ValueError("Pinned block hash mismatch")
    tag = hex(block)
    state_tag = {"blockHash": header["hash"], "requireCanonical": True}
    init_sig = "0x" + keccak256(b"Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)").hex()
    reads = [("eth_getLogs", [{"address": ADDRESSES["core"], "fromBlock": hex(INITIALIZATION_BLOCK),
              "toBlock": hex(INITIALIZATION_BLOCK), "topics": [init_sig, POOL]}])]
    reads += [("eth_getCode", [a, state_tag]) for a in ADDRESSES.values()]
    specs = [("slot0", "state", "getSlot0(bytes32)", POOL[2:]),
             ("activeLiquidity", "state", "getLiquidity(bytes32)", POOL[2:]),
             ("positionManagerCore", "positions", "poolManager()", ""),
             ("positionManagerPermit2", "positions", "permit2()", ""),
             ("positionManagerWrapper", "positions", "WETH9()", ""),
             ("stateCore", "state", "poolManager()", ""),
             ("protocolFeeController", "core", "protocolFeeController()", ""),
             ("managerOwner", "core", "owner()", "")]
    reads += [("eth_call", [{"to": ADDRESSES[target], "data": selector(sig)+arg}, state_tag])
              for _, target, sig, arg in specs]
    result = rpc(url, reads)
    if len(result[0]) != 1:
        raise ValueError("Missing or ambiguous initialization")
    log = result[0][0]
    key = [0, int(ZZZ, 16), 10020, 200, 0]
    if (not isinstance(log, dict) or log.get("address", "").lower() != ADDRESSES["core"] or
        log.get("removed") is not False or log.get("blockNumber") != hex(INITIALIZATION_BLOCK) or
        log.get("transactionHash", "").lower() != INITIALIZATION_TX or
        not isinstance(log.get("topics"), list) or len(log["topics"]) != 4 or
        log["topics"][:2] != [init_sig, POOL] or
        "0x"+keccak256(b"".join(x.to_bytes(32, "big") for x in key)).hex() != POOL or
        [int(x, 16) for x in log["topics"][2:]] != key[:2] or words(log["data"])[:3] != key[2:]):
        raise ValueError("Unexpected native/static/hookless pool key")
    contracts = {}
    for (name, address), code in zip(ADDRESSES.items(), result[1:7]):
        if not isinstance(code, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", code):
            raise ValueError("Missing deployed dependency")
        digest = "0x"+keccak256(bytes.fromhex(code[2:])).hex()
        if digest != EXPECTED_RUNTIME_HASHES[name]:
            raise ValueError("Unreviewed dependency runtime")
        contracts[name] = {"address": address, "runtime_keccak": digest}
    values = {spec[0]: words(value) for spec, value in zip(specs, result[7:])}
    for field, target in [("positionManagerCore", "core"), ("positionManagerPermit2", "permit2"),
                          ("positionManagerWrapper", "weth"), ("stateCore", "core")]:
        if values[field] != [int(ADDRESSES[target], 16)]:
            raise ValueError("Wrong dependency wiring")
    slot = values["slot0"]
    if len(slot) != 4 or not 0 < slot[0] < 2**160 or slot[2] >= 2**24 or slot[3] != 10020:
        raise ValueError("Unexpected pool price/static LP fee")
    for field in ("activeLiquidity", "protocolFeeController", "managerOwner"):
        limit = 2**128 if field == "activeLiquidity" else 2**160
        if len(values[field]) != 1 or values[field][0] >= limit:
            raise ValueError("Noncanonical liquidity or authority return")
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


def write_observation(path, result):
    """Preserve the last complete record if serialization or replacement fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
            dir=path.parent, prefix=".popl-observation-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(result, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", default="https://rpc.mainnet.chain.robinhood.com")
    parser.add_argument("--block", type=int, required=True)
    parser.add_argument("--expected-hash")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = observe(args.rpc, args.block, args.expected_hash)
        write_observation(args.output, result)
    except Exception:
        # Transport/provider exceptions can contain URLs, authorization or response bodies.
        print("Observation failed; no qualified evidence written. Review RPC, canonical block and dependencies.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
