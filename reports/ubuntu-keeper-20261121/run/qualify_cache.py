"""Outside-namespace exact-anchor READ-ONLY prefetch, before any signing.

Input rows come only from the strict offline cache's admitted misses or the
explicit fresh local sender's public account reads. Provider refusal stops work.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import source9_rehearsal_fork as F

BLOCK = 119107223
ANCHOR = "0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--events", type=Path)
    p.add_argument("--sender")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    raw = args.cache.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == args.sha256
    cache = F._loads(raw)
    assert cache["anchor_number"] == BLOCK and cache["anchor_hash"] == ANCHOR
    validator = object.__new__(F._ForkCache)
    validator.anchor_number, validator.anchor_hash = BLOCK, ANCHOR
    requests = {}

    def admit(method, params):
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        assert validator._validate(request) == (method, params)
        assert validator._cacheable(method, params)
        key = F._digest({"method": method, "params": params})
        if key not in cache["entries"]:
            requests[key] = request

    if args.events:
        for row in json.loads(args.events.read_bytes())["events"]:
            if row["event"] == "miss":
                admit(row["method"], row["params"])
    if args.sender:
        assert re.fullmatch(r"0x[0-9a-f]{40}", args.sender)
        for method in ("eth_getCode", "eth_getBalance", "eth_getTransactionCount"):
            admit(method, [args.sender, hex(BLOCK)])
    assert len(requests) <= 64
    wire = (args.output / "public-read-wire.jsonl").open("x", encoding="utf-8", newline="\n")
    n = 0

    def fetch(request):
        nonlocal n
        n += 1
        assert n <= 66
        body = F._bytes(request)
        status, response = F._https_post(F.PUBLIC_ENDPOINT, body)
        wire.write(json.dumps({"request": request, "http_status": status,
                   "response_utf8": response.decode(), "response_sha256": hashlib.sha256(response).hexdigest()}) + "\n")
        wire.flush()
        assert status == 200, "Provider refused bounded read-only qualification"
        answer = F._loads(response)
        assert answer.get("jsonrpc") == "2.0" and answer.get("id") == request["id"] and "error" not in answer
        time.sleep(2)
        return answer["result"]

    chain = fetch({"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []})
    assert int(chain, 16) == 4663
    header = fetch({"jsonrpc": "2.0", "id": 2, "method": "eth_getBlockByNumber", "params": [hex(BLOCK), False]})
    assert header["hash"] == ANCHOR and int(header["number"], 16) == BLOCK
    for i, (key, request) in enumerate(requests.items(), 3):
        request["id"] = i
        result = fetch(request)
        assert validator._valid_result(request["method"], result, request["params"])
        cache["entries"][key] = {"method": request["method"], "params": copy.deepcopy(request["params"]),
                                 "result": result, "result_sha256": F._digest(result)}
    wire.close()
    result = (json.dumps(cache, indent=2) + "\n").encode()
    (args.output / "cache.json").write_bytes(result)
    manifest = {"schema": 1, "source_cache_sha256": args.sha256, "sha256": hashlib.sha256(result).hexdigest(),
                "wire_sha256": hashlib.sha256((args.output / "public-read-wire.jsonl").read_bytes()).hexdigest(),
                "new_entries": len(requests), "entries": len(cache["entries"]), "public_read_requests": n,
                "anchor_number": BLOCK, "anchor_hash": ANCHOR, "signing": False,
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
