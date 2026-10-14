#!/usr/bin/env python3
"""Read-only, pinned-block evidence for the selected Robinhood market.

Requires Python 3.11+ and the pinned Foundry `cast` executable. No credentials,
signer, approvals, transaction submission or synthetic prices are used here.
This verifies observed dependencies; it does not approve production integration.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BLOCK = 88_544_093
BLOCK_HASH = "0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490"
POOL = "0x6538e2c223ed70228114983afecbe5e69fe627e2fafdf367bdd6bdeff2ad391f"
ADDRESSES = {
    "PoolManager": "0x8366a39cc670b4001a1121b8f6a443a643e40951",
    "PositionManager": "0x58daec3116aae6d93017baaea7749052e8a04fa7",
    "StateView": "0xf3334192d15450cdd385c8b70e03f9a6bd9e673b",
    "Permit2": "0x000000000022d473030f116ddee9f6b43ac78ba3",
    "WETH": "0x0bd7d308f8e1639fab988df18a8011f41eacad73",
    "ZZZ": "0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a",
    "PonsHook": "0xe5e702641ea86f4ae6cc3cdaed2b886f976be044",
    "ETHUSD": "0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9",
    "PonsFactory": "0x7ed598bcef8bd9edd8c97a195c6d13f40801ec7e",
    "PonsFeeEscrow": "0xd3afeb2a57f70ef218aa82451c51b2fb0416ac9e",
}


def rpc(url, requests):
    payload = [dict(jsonrpc="2.0", id=i, method=m, params=p) for i, (m, p) in enumerate(requests)]
    request = urllib.request.Request(url, json.dumps(payload).encode(), {
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "AAA-PoPL-readonly-verification/1.0"
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        replies = json.load(response)
    if not isinstance(replies, list) or len(replies) != len(payload):
        raise ValueError("Invalid batch RPC response")
    by_id = {r["id"]: r for r in replies}
    results = []
    for i in range(len(payload)):
        reply = by_id[i]
        if "error" in reply or "result" not in reply:
            raise ValueError(f"Read-only RPC request {i} failed: {reply.get('error')}")
        results.append(reply["result"])
    return results


def words(encoded):
    if not isinstance(encoded, str) or not encoded.startswith("0x") or (len(encoded) - 2) % 64:
        raise ValueError("Malformed static ABI response")
    return [int(encoded[i:i + 64], 16) for i in range(2, len(encoded), 64)]


def address(word):
    if word < 0 or word >= 1 << 160:
        raise ValueError("Invalid ABI address")
    return f"0x{word:040x}"


def keccak(cast, hex_data):
    # stdin avoids OS argument-size limits for runtime bytecode. No shell evaluation.
    result = subprocess.run([cast, "keccak"], input=hex_data, capture_output=True, text=True, check=True)
    digest = result.stdout.strip()
    if len(digest) != 66 or not digest.startswith("0x"):
        raise ValueError("Invalid Ethereum Keccak-256 result")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc", default=os.environ.get("ROBINHOOD_RPC_URL", "https://robinhood.rpc.pinax.network"))
    parser.add_argument("--cast", default=shutil.which("cast"))
    parser.add_argument("--output", type=Path, help="Optional JSON evidence path; otherwise print to stdout")
    args = parser.parse_args()
    if not args.cast:
        parser.error("Pinned Foundry cast executable is required")
    tag = hex(BLOCK)
    call_specs = [
        ("slot0", "StateView", "0xc815641c" + POOL[2:]),
        ("launch", "PonsHook", "0xad091230" + POOL[2:]),
        ("positionManagerCore", "PositionManager", "0xdc4c90d3"),
        ("positionManagerPermit2", "PositionManager", "0x12261ee7"),
        ("stateViewCore", "StateView", "0xdc4c90d3"),
        ("tokenDecimals", "ZZZ", "0x313ce567"),
        ("tokenSupply", "ZZZ", "0x18160ddd"),
        ("ethUSDDecimals", "ETHUSD", "0x313ce567"),
        ("ethUSDRound", "ETHUSD", "0xfeaf968c"),
        ("hookOwner", "PonsHook", "0x8da5cb5b"),
        ("factoryOwner", "PonsFactory", "0x8da5cb5b"),
        ("pendingCreatorChange", "PonsFactory", "0x9beacf4a" + ADDRESSES["ZZZ"][2:].rjust(64, "0")),
    ]
    requests = [("eth_chainId", []), ("eth_getBlockByNumber", [tag, False])]
    requests += [("eth_getCode", [a, tag]) for a in ADDRESSES.values()]
    requests += [("eth_call", [dict(to=ADDRESSES[target], data=data), tag]) for _, target, data in call_specs]
    results = rpc(args.rpc, requests)
    if int(results[0], 16) != 4663 or results[1] is None or results[1]["hash"].lower() != BLOCK_HASH:
        raise ValueError("Wrong chain or pinned block hash")
    block = results[1]
    contracts = {}
    for (name, deployed_address), code in zip(ADDRESSES.items(), results[2:2 + len(ADDRESSES)]):
        if code == "0x":
            raise ValueError(f"Missing deployed code for {name}")
        contracts[name] = dict(address=deployed_address, runtimeBytes=(len(code) - 2) // 2,
                               runtimeKeccak256=keccak(args.cast, code),
                               runtimeSHA256=hashlib.sha256(bytes.fromhex(code[2:])).hexdigest())
    values = dict((spec[0], words(result)) for spec, result in zip(call_specs, results[2 + len(ADDRESSES):]))
    for key, expected in [("positionManagerCore", "PoolManager"), ("positionManagerPermit2", "Permit2"),
                          ("stateViewCore", "PoolManager")]:
        if address(values[key][0]) != ADDRESSES[expected]:
            raise ValueError(f"Dependency binding mismatch: {key}")
    slot = values["slot0"]
    launch = values["launch"]
    if len(slot) != 4 or len(launch) != 13 or slot[2:] != [0, 0]:
        raise ValueError("Unexpected pool state or conventional fee policy")
    if launch[0] != 1 or address(launch[2]) != ADDRESSES["ZZZ"] or launch[3] != 0:
        raise ValueError("Hook launch does not match native ETH / ZZZ")
    if launch[7] != 0 or launch[8] != 3000 or launch[10] != 100 or launch[12] != 0:
        raise ValueError("Pinned hook policy mismatch")
    round_id, answer, started, updated, answered = values["ethUSDRound"]
    timestamp = int(block["timestamp"], 16)
    if values["ethUSDDecimals"] != [8] or not 0 < answer < (1 << 255) or not round_id or answered < round_id:
        raise ValueError("Invalid real ETH/USD feed round")
    if not 0 < updated <= timestamp or timestamp - updated > 86400:
        raise ValueError("Real ETH/USD feed is stale at pinned block")
    pool_key_words = [0, int(ADDRESSES["ZZZ"], 16), 0, 200, int(ADDRESSES["PonsHook"], 16)]
    encoded_key = "0x" + "".join(f"{value:064x}" for value in pool_key_words)
    if keccak(args.cast, encoded_key) != POOL:
        raise ValueError("PoolKey hash mismatch")
    evidence = {
        "schemaVersion": 1,
        "verifiedAtUTC": datetime.now(timezone.utc).isoformat(),
        "readOnly": True,
        # Do not persist a possibly credential-bearing override RPC URL.
        "rpcSource": args.rpc if args.rpc in {
            "https://robinhood.rpc.pinax.network", "https://robinhood.drpc.org",
            "https://rpc.mainnet.chain.robinhood.com"
        } else "User-supplied archive RPC endpoint (redacted)",
        "chainId": 4663,
        "blockNumber": BLOCK,
        "blockHash": BLOCK_HASH,
        "blockTimestamp": timestamp,
        "contracts": contracts,
        "pool": dict(id=POOL, currency0="0x" + "0" * 40, currency1=ADDRESSES["ZZZ"],
                     fee=0, tickSpacing=200, hooks=ADDRESSES["PonsHook"],
                     sqrtPriceX96=str(slot[0]), tick=slot[1], protocolFee=slot[2], lpFee=slot[3]),
        "hookPolicy": dict(creatorRecipient=address(launch[4]), buybackCreatorRecipient=address(launch[5]),
                           protocolRecipient=address(launch[6]), creatorTaxBps=launch[7],
                           protocolFeeShareBps=launch[8], buybackSliceBps=launch[9], hookFeeBps=launch[10],
                           maxInternalPriceImpactBps=launch[11], buybackEnabled=bool(launch[12]),
                           hookOwner=address(values["hookOwner"][0]), factoryOwner=address(values["factoryOwner"][0]),
                           pendingCreatorRecipient=address(values["pendingCreatorChange"][0]),
                           pendingCreatorChangeEffectiveAt=values["pendingCreatorChange"][1],
                           pendingCreatorChangeExpiresAt=values["pendingCreatorChange"][2]),
        "token": dict(decimals=values["tokenDecimals"][0], totalSupply=str(values["tokenSupply"][0]),
                      sourceContract="PonsV2LauncherToken", verifiedSourceProxy=False,
                      verifiedSourceFeatures=["Standard ERC20 transfers", "Constructor-only fixed supply mint",
                                              "ERC20Burnable burn and burnFrom", "No token owner or privileged transfer override"]),
        "ethUSDFeed": dict(proxy=ADDRESSES["ETHUSD"], decimals=8, heartbeatSeconds=86400,
                           roundId=str(round_id), answer=str(answer), startedAt=started, updatedAt=updated,
                           answeredInRound=str(answered)),
        "boundaries": ["Current candidate rejects native currency and hooks",
                       "Core LP fees are zero; LP ownership does not entitle PoPL to Pons hook revenue",
                       "Revenue source remains undecided: a Pons fee-share integration or a new fee-earning pool; no payout terms are approved",
                       "No ZZZ feed or Robinhood sequencer feed found in checked Chainlink catalogs",
                       "Provider chain support does not establish a backed ZZZ bridge route",
                       "Fork settlement tests use a separate locally initialized hookless pool and synthetic test-only reference feeds"],
        "sources": ["https://docs.robinhood.com/chain/connecting/",
                    "https://developers.uniswap.org/docs/protocols/v4/deployments",
                    "https://docs.ponsfamily.com/v2",
                    "https://docs.chain.link/data-feeds/price-feeds/addresses?network=robinhood-mainnet",
                    "https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json",
                    "https://docs.chain.link/data-feeds/l2-sequencer-feeds",
                    "https://robinhoodchain.blockscout.com/api?module=contract&action=getsourcecode&address=" + ADDRESSES["ZZZ"],
                    "https://robinhoodchain.blockscout.com/api?module=contract&action=getsourcecode&address=" + ADDRESSES["PonsHook"]],
    }
    encoded = json.dumps(evidence, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"Verified chain 4663, block {BLOCK}, zero core LP fees, real ETH/USD round and {len(contracts)} code hashes")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"Read-only integration verification FAILED: {exc}") from exc
