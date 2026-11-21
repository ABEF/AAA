"""Owned namespace fixed-anchor cache: never fetches, signs, or guesses misses."""
from pathlib import Path
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import signal
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import source9_rehearsal_fork as F

BLOCK = 119107223
ANCHOR = "0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335"
VALIDATOR_SHA = "6c52f68b6d66cfa28d18c13eee0a1930123dec82d54143446ac76ef9069629b4"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    assert os.name == "posix" and 1024 <= args.port <= 65535
    assert sha((ROOT / "scripts/source9_rehearsal_fork.py").read_bytes()) == VALIDATOR_SHA
    raw = args.cache.read_bytes()
    assert len(raw) <= F.MAX_CACHE_BYTES and sha(raw) == args.sha256
    cache = F._loads(raw)
    assert cache["anchor_number"] == BLOCK and cache["anchor_hash"] == ANCHOR
    entries = cache["entries"]
    assert isinstance(entries, dict) and 1 <= len(entries) <= F.MAX_CACHE_ENTRIES
    validator = object.__new__(F._ForkCache)
    validator.anchor_number, validator.anchor_hash = BLOCK, ANCHOR
    for key, row in entries.items():
        method, params, result = row["method"], row["params"], row["result"]
        request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        assert validator._validate(request) == (method, params)
        assert validator._cacheable(method, params)
        assert validator._valid_result(method, result, params)
        assert key == F._digest({"method": method, "params": params})
        assert F._digest(result) == row["result_sha256"]
    args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
    mutex = threading.Lock()
    counts = {"attempts": 0, "requests": 0, "hits": 0, "misses": 0, "rejected": 0}
    stopped = False

    def event(value):
        with (args.output / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            self.connection.settimeout(10)
            with mutex:
                counts["attempts"] += 1
                over_limit = counts["attempts"] > 10000
            if over_limit:
                self.send_error(503, "Owned rehearsal request budget exhausted")
                return
            request, identifier = None, None
            try:
                length = int(self.headers.get("Content-Length", "0"))
                assert 0 < length <= F.MAX_REQUEST
                wire = self.rfile.read(length)
                request = F._loads(wire)
                identifier = request.get("id") if isinstance(request, dict) else None
                original = None
                if isinstance(request, dict) and set(request) == {"jsonrpc", "id", "method"} and request.get("method") == "eth_chainId":
                    # Confirmed Linux Anvil1.4.4 wire: JSON-RPC permits omitted
                    # params for zero arguments. Keep strict ID/helper validation.
                    original = request
                    request = dict(request, params=[])
                method, params = validator._validate(request)
                assert validator._cacheable(method, params)
                key = F._digest({"method": method, "params": params})
                with mutex:
                    counts["requests"] += 1
                    if original is not None:
                        event({"event": "normalized_omitted_zero_args", "original_envelope": original,
                               "original_wire_sha256": sha(wire), "original_wire_bytes": len(wire),
                               "original_id_type": type(identifier).__name__, "original_params_present": False,
                               "normalized_params": []})
                    if key in entries:
                        counts["hits"] += 1
                        reply = {"jsonrpc": "2.0", "id": identifier, "result": entries[key]["result"]}
                        event({"event": "hit", "method": method, "request_sha256": key})
                    else:
                        counts["misses"] += 1
                        # Only admitted historical read params enter discovery records.
                        event({"event": "miss", "method": method, "params": params, "request_sha256": key})
                        reply = {"jsonrpc": "2.0", "id": identifier,
                                 "error": {"code": -32070, "message": "Unreviewed offline cache miss; stop and qualify exact read"}}
            except Exception:
                with mutex:
                    counts["rejected"] += 1
                    # Never log an unknown method's params/raw transaction payload.
                    value = request.get("method") if isinstance(request, dict) else None
                    method = value if isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value) else "invalid_method"
                    event({"event": "rejected", "method": method})
                reply = {"jsonrpc": "2.0", "id": identifier,
                         "error": {"code": -32600, "message": "Outside fixed-anchor read envelope"}}
            payload = F._bytes(reply)
            assert len(payload) <= F.MAX_RESPONSE
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def halt(*_args):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, halt)
    signal.signal(signal.SIGINT, halt)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    server.timeout = 0.5
    save(args.output / "ready.json", {"schema": 1, "pid": os.getpid(), "port": args.port,
         "cache_sha256": args.sha256, "entries": len(entries), "anchor": ANCHOR,
         "public_network_code_used": False, "cache_misses_fail_closed": True,
         "time": time.time(), "source_sha256": sha(Path(__file__).read_bytes())})
    try:
        while not stopped:
            server.handle_request()
    finally:
        server.server_close()
        save(args.output / "summary.json", {"schema": 1, **counts, "public_requests": 0,
             "cache_sha256": args.sha256, "source_sha256": sha(Path(__file__).read_bytes())})


if __name__ == "__main__":
    main()
