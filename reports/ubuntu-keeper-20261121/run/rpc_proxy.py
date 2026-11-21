"""Owned namespace real-Anvil RPC proxy with bounded, explicit HTTP faults.

Signed payload bytes/signature fields are NEVER retained. The normal keeper is
unmodified; this fixture changes only transport availability, not EVM answers.
"""
from pathlib import Path
import argparse
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import signal
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256

ALLOWED = {"eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_getBlockByHash",
           "eth_call", "eth_estimateGas", "eth_getCode", "eth_getBalance", "eth_getTransactionCount",
           "eth_getTransactionReceipt", "eth_getTransactionByHash", "eth_gasPrice",
           "eth_maxPriorityFeePerGas", "eth_feeHistory", "eth_getStorageAt", "eth_getProof",
           "eth_getLogs", "eth_sendRawTransaction", "web3_clientVersion", "net_version"}
TX_PUBLIC = {"hash", "from", "to", "input", "value", "nonce", "gas", "gasPrice", "type", "chainId",
             "maxFeePerGas", "maxPriorityFeePerGas", "blockHash", "blockNumber", "transactionIndex"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--control", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--upstream-port", type=int, default=18545)
    args = p.parse_args()
    assert os.name == "posix" and os.getuid() != 0 and args.upstream_port == 18545
    args.output.mkdir(mode=0o700, exist_ok=False)
    counts = {"attempts": 0, "raw_send_attempts": 0}
    mutex = threading.Lock()
    stopped = False

    def event(row):
        with mutex:
            with (args.output / "events.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            self.connection.settimeout(15)
            with mutex:
                counts["attempts"] += 1
                sequence = counts["attempts"]
            if sequence > 10000:
                self.send_error(503)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 128000:
                self.send_error(413)
                return
            raw = self.rfile.read(length)
            request = json.loads(raw)
            assert isinstance(request, dict) and request.get("jsonrpc") == "2.0"
            method, params = request.get("method"), request.get("params", [])
            assert isinstance(method, str) and method in ALLOWED and isinstance(params, list)
            if method in ("eth_getBlockByNumber", "eth_getBlockByHash"):
                assert len(params) == 2 and params[1] is False
            signed_hash = None
            public_request = request
            if method == "eth_sendRawTransaction":
                assert len(params) == 1 and isinstance(params[0], str) and params[0].startswith("0x")
                signed = bytes.fromhex(params[0][2:])
                assert 0 < len(signed) <= 64000
                signed_hash = "0x" + keccak256(signed).hex()
                public_request = {"jsonrpc": "2.0", "id": request.get("id"), "method": method,
                                  "params_redacted": {"transaction_hash": signed_hash, "raw_bytes": len(signed)}}
                with mutex:
                    counts["raw_send_attempts"] += 1
            control_raw = args.control.read_bytes()
            assert len(control_raw) <= 4096
            control = json.loads(control_raw)
            endpoint = "primary" if self.server.server_port == 18547 else "secondary"
            mode = control[endpoint]
            assert mode in ("healthy", "outage", "body_trickle")
            base = {"sequence": sequence, "endpoint": endpoint, "time": time.time(),
                    "request": public_request, "request_bytes_sha256": sha(raw), "mode": mode}
            if mode == "outage":
                event({**base, "event": "controlled_http_503"})
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if mode == "body_trickle" and method == "eth_getBlockByNumber":
                event({**base, "event": "incomplete_body_started", "maximum_seconds": 300})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "60000")
                self.end_headers()
                try:
                    self.wfile.write(b"{")
                    self.wfile.flush()
                    for _ in range(300):
                        if stopped:
                            break
                        time.sleep(1)
                        self.wfile.write(b" ")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, TimeoutError):
                    pass
                event({"sequence": sequence, "event": "incomplete_body_ended", "time": time.time()})
                return
            connection = http.client.HTTPConnection("127.0.0.1", args.upstream_port, timeout=15)
            try:
                connection.request("POST", "/", raw, {"Content-Type": "application/json"})
                reply = connection.getresponse()
                payload = reply.read(4 * 1024 * 1024 + 1)
                assert reply.status == 200 and len(payload) <= 4 * 1024 * 1024
            finally:
                connection.close()
            response = json.loads(payload)
            assert response.get("id") == request.get("id")
            public_response = response
            if method == "eth_getTransactionByHash" and isinstance(response.get("result"), dict):
                public_response = {**response, "result": {k: v for k, v in response["result"].items() if k in TX_PUBLIC}}
            if "error" in response:
                public_response = {"jsonrpc": "2.0", "id": request.get("id"),
                                   "error": {"code": response["error"].get("code"),
                                             "original_error_sha256": sha(json.dumps(response["error"], sort_keys=True).encode())}}
            event({**base, "event": "forwarded", "response": public_response,
                   "response_bytes_sha256": sha(payload)})
            if signed_hash is not None and "result" in response:
                assert response["result"] == signed_hash
                marker = args.output / "first_broadcast.json"
                if not marker.exists():
                    save(marker, {"transaction_hash": signed_hash, "time": time.time(),
                                  "raw_signed_payload_retained": False})
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
    servers = [ThreadingHTTPServer(("127.0.0.1", port), Handler) for port in (18547, 18548)]
    for server in servers:
        server.daemon_threads = True
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in servers]
    for thread in threads:
        thread.start()
    save(args.output / "ready.json", {"schema": 1, "pid": os.getpid(), "ports": [18547, 18548],
         "upstream": "owned_namespace_Anvil_18545", "source_sha256": sha(Path(__file__).read_bytes()),
         "raw_signed_payloads_or_signature_fields_retained": False})
    try:
        while not stopped:
            time.sleep(0.5)
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        save(args.output / "summary.json", {"schema": 1, **counts, "public_network_requests": 0})


if __name__ == "__main__":
    main()
