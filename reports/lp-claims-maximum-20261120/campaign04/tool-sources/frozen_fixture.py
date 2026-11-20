"""Report-only owned-chain reuse of authenticated maximum-state F6 exports.

No producer, compiler, existing node, public endpoint, signer key or service is
used. The original maximum-state fixture deliberately uses MockAccess. Its
explicit bootstrap seam is used ONLY in a newly owned local chain to install
the unchanged normal-build LP converter before new accounting scenarios. This
is not evidence that a real sealed controller can be unsealed or rotated.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256

ZERO = "0x" + "0" * 40
CLAIM_CAP = 12_000_000
CONVERSION_CAP = 24_000_000
CLAIM_PADDING_BPS = 2000
CONVERSION_PADDING_BPS = 2500
SETUP_CAP = 24_000_000
FIXTURE_GAS = 96_000_000  # synthetic chain capacity, never scenario admission
MAX_REPLY = 64 * 1024 * 1024
OWNED_WORK = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/lp-claims-maximum-20261120")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def address(value):
    if isinstance(value, int):
        if not 0 <= value < 2**160:
            raise ValueError("Dirty address")
        return f"0x{value:040x}"
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
        raise ValueError("Malformed address")
    return value.lower()


def word(value):
    if isinstance(value, str):
        if re.fullmatch(r"0x[0-9a-fA-F]{1,64}", value):
            value = int(value, 16)
        elif value.isdecimal():
            value = int(value)
        else:
            raise ValueError("Malformed static word")
    if type(value) is bool:
        value = int(value)
    if type(value) is not int or not -(2**255) <= value < 2**256:
        raise ValueError("Invalid static word")
    return f"{value % 2**256:064x}"


def selector(signature):
    return "0x" + keccak256(signature.encode()).hex()[:8]


def encode(signature, *args):
    """Flat ABI words only; callers explicitly encode dynamic tuple arrays."""
    return selector(signature) + "".join(word(value) for value in args)


def decoded(data):
    if not isinstance(data, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{64})*", data):
        raise ValueError("Malformed ABI result")
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


class RPCError(RuntimeError):
    def __init__(self, method, error):
        self.method, self.error = method, error
        super().__init__(f"Owned local {method} refused: {error}")


class OwnedRPC:
    READ = frozenset(("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_getBlockByHash",
        "eth_getCode", "eth_getBalance", "eth_call", "eth_estimateGas", "eth_gasPrice",
        "eth_getTransactionCount", "eth_getTransactionByHash", "eth_getTransactionReceipt",
        "debug_traceCall", "debug_traceTransaction"))
    MUTATE = frozenset(("anvil_impersonateAccount", "anvil_stopImpersonatingAccount",
        "eth_sendTransaction", "evm_mine", "evm_snapshot", "evm_revert"))

    def __init__(self, port, proc):
        self.port, self.proc = port, proc
        self.records, self.started = [], time.monotonic()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.next_id = 1
        self.request_count = 0

    def _request(self, requests, batch):
        if self.proc.poll() is not None:
            raise RuntimeError("Owned node stopped")
        if self.request_count + len(requests) > 200000 or time.monotonic() - self.started > 3600:
            raise RuntimeError("Report-only local workload bound exhausted")
        self.request_count += len(requests)
        raw = json.dumps(requests if batch else requests[0], separators=(",", ":")).encode()
        record = {"requests": requests, "request_sha256": sha(raw)}
        self.records.append(record)
        with self.opener.open(urllib.request.Request(f"http://127.0.0.1:{self.port}", raw,
                {"Content-Type": "application/json"}), timeout=90) as response:
            body = response.read(MAX_REPLY + 1)
        if len(body) > MAX_REPLY:
            raise ValueError("Local reply bound exceeded")
        value = json.loads(body)
        record.update(response=value, response_sha256=sha(body))
        values = value if batch else [value]
        if not isinstance(values, list) or len(values) != len(requests):
            raise ValueError("RPC response cardinality differs")
        by_id = {row.get("id"): row for row in values}
        if len(by_id) != len(values):
            raise ValueError("Duplicate RPC response identity")
        result = []
        for request in requests:
            row = by_id.get(request["id"])
            if not row or row.get("jsonrpc") != "2.0":
                raise ValueError("RPC response identity differs")
            if "error" in row:
                raise RPCError(request["method"], row["error"])
            if "result" not in row:
                raise ValueError("Missing RPC result")
            result.append(row["result"])
        return result

    def call(self, method, params=None):
        if method not in self.READ | self.MUTATE:
            raise ValueError("Unreviewed RPC method")
        request = {"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or []}
        self.next_id += 1
        return self._request([request], False)[0]

    def attempt(self, method, params):
        try:
            return {"ok": True, "result": self.call(method, params)}
        except RPCError as error:
            return {"ok": False, "error": error.error}

    def batch(self, calls):
        if not 1 <= len(calls) <= 100 or any(method not in self.READ for method, _ in calls):
            raise ValueError("Only bounded read-only RPC batches")
        requests = []
        for method, params in calls:
            requests.append({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params})
            self.next_id += 1
        return self._request(requests, True)


class FrozenFixture:
    """Context manager; all owned processes stop even after setup/scenario failure."""
    def __init__(self, output_dir, label="max1000-lp2-harvest-no-new-fees"):
        self.output = Path(output_dir).resolve()
        report = ROOT / "reports/lp-claims-maximum-20261120"
        if not (self.output.is_relative_to(report.resolve()) or self.output.is_relative_to(OWNED_WORK.resolve())):
            raise ValueError("New report directory required")
        self.label, self.proc, self.rpc = label, None, None
        self.receipts, self.proof = [], {"production_approved": False,
            "old_producer_rerun": False, "compiler_run": False, "public_transactions": 0,
            "fixture_seam": "New isolated MockAccess bootstrap, not real sealed rotation"}

    selector = staticmethod(selector)
    encode = staticmethod(encode)

    def __enter__(self):
        self.output.mkdir(parents=True, exist_ok=False)
        try:
            self._start()
            self._discover()
            self._converter()
            return self
        except BaseException:
            self.stop()
            raise

    def _start(self):
        old = ROOT / "reports/maximum-workload-20261119/tools/verify_contributions.py"
        spec = importlib.util.spec_from_file_location("maximum_frozen_20261119", old)
        self.base = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.base)
        self.proof["source_authentication"] = self.base.configure("producer06")
        cases, raw_sha256, source_pins, source_methods = self.base.exports()
        self.proof["export_authentication"] = {"raw_sha256": raw_sha256,
            "source_pins": source_pins, "source_methods": source_methods}
        selected = [row for row in cases if row["label"] == self.label]
        if len(selected) != 1:
            raise ValueError("Exact frozen case required")
        self.case = selected[0]
        alloc, omitted, merge = self.base.source_state(self.case)
        self.omitted = omitted
        self.proof.update(frozen_case=self.case, state_merge=merge, omitted_harness=omitted)
        block = self.case["block"]
        genesis = {"config": {"chainId": block["chain_id"], "homesteadBlock": 0,
            "eip150Block": 0, "eip155Block": 0, "eip158Block": 0, "byzantiumBlock": 0,
            "constantinopleBlock": 0, "petersburgBlock": 0, "istanbulBlock": 0,
            "berlinBlock": 0, "londonBlock": 0, "terminalTotalDifficulty": 0,
            "shanghaiTime": 0, "cancunTime": 0}, "number": hex(block["number"]),
            "nonce": "0x0", "timestamp": hex(block["timestamp"]), "extraData": "0x",
            "gasLimit": hex(FIXTURE_GAS), "difficulty": "0x0", "mixHash": "0x" + "0" * 64,
            "coinbase": ZERO, "baseFeePerGas": "0x0", "alloc": alloc}
        raw = json.dumps(genesis, separators=(",", ":")).encode()
        genesis_path = self.output / "genesis.json"
        genesis_path.write_bytes(raw)
        self.proof["genesis_sha256"] = sha(raw)
        if sha(self.base.ANVIL.read_bytes()) != self.base.ANVIL_SHA256:
            raise ValueError("Anvil executable differs")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port in (8902, 57306):
            raise ValueError("Protected port")
        command = [str(self.base.ANVIL), "--host", "127.0.0.1", "--port", str(port),
            "--accounts", "0", "--silent", "--init", str(genesis_path), "--gas-limit", str(FIXTURE_GAS),
            "--chain-id", str(block["chain_id"]), "--hardfork", "cancun", "--no-mining"]
        env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "SystemDrive", "COMSPEC",
            "PATHEXT", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "PROGRAMDATA") if key in os.environ}
        env["PATH"] = str(self.base.ANVIL.parent) + os.pathsep + str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32")
        self.log = (self.output / "anvil.log").open("xb")
        self.proc = subprocess.Popen(command, env=env, stdout=self.log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.proof.update(owned_command=command, owned_pid=self.proc.pid, owned_port=port,
            anvil_sha256=self.base.ANVIL_SHA256)
        self.proof["listener_ownership"] = self.base.listener_identity(self.proc, port)
        self.rpc = OwnedRPC(port, self.proc)
        head = self.head()
        if int(self.rpc.call("eth_chainId"), 16) != block["chain_id"] or int(head["number"], 16) != block["number"] or int(head["timestamp"], 16) != block["timestamp"]:
            raise ValueError("Frozen chain anchor differs")
        self.proof["initial_head"] = head
        for target, pin in self.case["materialized"].items():
            if target not in omitted and self.codehash(target) != pin["hash"]:
                raise ValueError("Materialized runtime differs: " + target)

    def head(self):
        return self.rpc.call("eth_getBlockByNumber", ["latest", False])

    @property
    def block(self):
        return self.head()

    @property
    def timestamp(self):
        return int(self.head()["timestamp"], 16)

    def codehash(self, target):
        return "0x" + keccak256(bytes.fromhex(self.rpc.call("eth_getCode", [address(target), "latest"])[2:])).hex()

    def read(self, target, signature, *args, count=1):
        result = decoded(self.rpc.call("eth_call", [{"from": getattr(self, "governance", self.case["sender"]),
            "to": address(target), "data": encode(signature, *args)}, "latest"]))
        if count is not None and len(result) != count:
            raise ValueError(f"Unexpected {signature} words: {len(result)}")
        return result

    def _tx(self, sender, to, data, gas, value):
        if type(gas) is not int or not 21000 <= gas <= SETUP_CAP:
            raise ValueError("Explicit <=24M envelope required")
        if type(value) is not int or value < 0 or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", data):
            raise ValueError("Malformed transaction")
        tx = {"from": address(sender), "data": data, "gas": hex(gas), "value": hex(value), "gasPrice": "0x0"}
        if to is not None:
            tx["to"] = address(to)
        return tx

    def call(self, sender, to, data, gas=CLAIM_CAP, value=0):
        return self.rpc.call("eth_call", [self._tx(sender, to, data, gas, value), "latest"])

    def estimate(self, sender, to, data, gas=CLAIM_CAP, value=0):
        return int(self.rpc.call("eth_estimateGas", [self._tx(sender, to, data, gas, value), "latest"]), 16)

    def trace(self, sender, to, data, gas=CLAIM_CAP, value=0):
        return self.rpc.call("debug_traceCall", [self._tx(sender, to, data, gas, value), "latest",
            {"tracer": "callTracer", "tracerConfig": {"withLog": True}, "timeout": "60s"}])

    def send(self, sender, to, data, gas=CLAIM_CAP, value=0):
        sender = address(sender)
        if self.rpc.call("eth_getCode", [sender, "latest"]) != "0x":
            raise ValueError("Fixture sender must be an empty-code local EOA")
        nonce = int(self.rpc.call("eth_getTransactionCount", [sender, "latest"]), 16)
        if int(self.rpc.call("eth_getTransactionCount", [sender, "pending"]), 16) != nonce:
            raise ValueError("Owned fixture unexpectedly contains pending work")
        prior_head = self.head()
        tx = self._tx(sender, to, data, gas, value)
        tx["nonce"] = hex(nonce)
        self.rpc.call("anvil_impersonateAccount", [sender])
        try:
            tx_hash = self.rpc.call("eth_sendTransaction", [tx])
        finally:
            self.rpc.call("anvil_stopImpersonatingAccount", [sender])
        # Captured fixture clocks must not jump to the desktop's wall clock.
        # One synthetic second per local transaction is explicit test setup;
        # actual market timing and operating acceptance remain unqualified.
        next_timestamp = int(prior_head["timestamp"], 16) + 1
        self.rpc.call("evm_mine", [next_timestamp])
        new_head = self.head()
        if int(new_head["timestamp"], 16) != next_timestamp or int(new_head["number"], 16) != int(prior_head["number"], 16) + 1:
            raise ValueError("Controlled local mining clock differs")
        receipt = self.rpc.call("eth_getTransactionReceipt", [tx_hash])
        actual = self.rpc.call("eth_getTransactionByHash", [tx_hash])
        if not receipt or int(receipt["status"], 16) != 1 or int(receipt["gasUsed"], 16) > gas:
            self.receipts.append({"review": tx, "receipt": receipt, "transaction": actual})
            raise RuntimeError("Local transaction reverted or exceeded reviewed gas")
        if actual["from"].lower() != sender or actual.get("to") != tx.get("to") or actual["input"].lower() != data.lower() or int(actual["value"], 16) != value or int(actual["nonce"], 16) != nonce:
            raise ValueError("Mined transaction differs from review")
        self.receipts.append({"review": tx, "receipt": receipt, "transaction": actual})
        return receipt

    def snapshot(self):
        return self.rpc.call("evm_snapshot", [])

    def revert(self, snapshot_id):
        if self.rpc.call("evm_revert", [snapshot_id]) is not True:
            raise RuntimeError("Owned scenario snapshot restore failed")

    def _discover(self):
        self.pins = dict(self.case["pins"])
        self.bucket = self.case["shared_bucket"]
        self.access = address(self.read(self.pins["rewards"], "access()")[0])
        self.governance = address(self.read(self.access, "governance()")[0])
        self.keeper = self.case["sender"]
        self.newcomer = "0x" + "0" * 37 + "b0b"
        self.royalty = address(self.read(self.pins["nft"], "royaltyRewards()")[0])
        self.claim_router = address(self.read(self.pins["nft"], "claimRouter()")[0])
        self.zzz = address(self.read(self.pins["rewards"], "assets(uint256)", 1)[0])
        self.ids = {}
        for start in range(1, 1001, 100):
            calls = [("eth_call", [{"to": self.pins["nft"], "data": encode("tokenAtOrdinal(uint256)", i)}, "latest"])
                for i in range(start, min(1001, start + 100))]
            for ordinal, result in zip(range(start, min(1001, start + 100)), self.rpc.batch(calls)):
                self.ids[ordinal] = decoded(result)[0]
        if len(set(self.ids.values())) != 1000 or 0 in self.ids.values():
            raise ValueError("Frozen NFT population differs")
        self.owner = address(self.read(self.pins["nft"], "ownerOf(uint256)", self.ids[1])[0])
        if self.read(self.royalty, "assetCount()")[0] != 65 or self.read(self.pins["membership"], "totalEligible()")[0] != 1000:
            raise ValueError("Exact maximum state required")
        self.currencies = [address(self.read(self.royalty, "assets(uint256)", i)[0]) for i in range(65)]
        if self.currencies[0] != ZERO or len(set(self.currencies)) != 65:
            raise ValueError("Currency inventory differs")
        self.proof["discovery"] = {"access": self.access, "governance": self.governance,
            "keeper": self.keeper, "owner": self.owner, "newcomer": self.newcomer,
            "royalty": self.royalty, "claim_router": self.claim_router, "zzz": self.zzz,
            "ids": self.ids, "currencies": self.currencies, "bucket": self.bucket}

    def _converter(self):
        binding = self.base.NORMAL_BINDING
        path = Path(binding["compiler_output_path"])
        raw = path.read_bytes()
        if sha(raw) != binding["compiler_output_sha256"]:
            raise ValueError("Normal compiler output differs")
        contracts = json.loads(raw)["contracts"]
        compiled = contracts["src/ZZZLPRewardConverter.sol"]["ZZZLPRewardConverter"]
        creation = compiled["evm"]["bytecode"]["object"]
        if not creation or not re.fullmatch(r"[0-9a-fA-F]+", creation):
            raise ValueError("Converter needs unresolved bytecode links")
        rewards = self.pins["rewards"]
        if self.read(rewards, "converter()")[0] != 0:
            raise ValueError("Do not replace an existing converter")
        # Explicit TEST-ONLY unseal. Real AccessController has no such function.
        self.send(self.governance, self.access, encode("beginBootstrap()"), gas=500000)
        creation_data = "0x" + creation + word(self.access) + word(rewards) + word(ZERO)
        # The omitted original test harness was itself a contract creator.
        # Reusing its now-empty account for CREATE would reset its nonce and
        # could collide with the preserved fixture. This new local empty EOA
        # deploys only the converter; controller governance remains unchanged.
        self.deployer = "0x000000000000000000000000000000000000de10"
        if self.rpc.call("eth_getCode", [self.deployer, "latest"]) != "0x" or int(self.rpc.call("eth_getTransactionCount", [self.deployer, "latest"]), 16) != 0:
            raise ValueError("Fresh fixture deployer is not empty")
        simulated_runtime = self.call(self.deployer, None, creation_data, gas=SETUP_CAP)
        receipt = self.send(self.deployer, None, creation_data, gas=SETUP_CAP)
        self.converter = address(receipt["contractAddress"])
        converter_runtime = self._runtime_equivalence(self.converter, compiled, simulated_runtime)
        if self.read(self.converter, "ledger()")[0] != int(rewards, 16) or self.read(self.converter, "access()")[0] != int(self.access, 16) or self.read(self.converter, "wrapper()")[0] != 0:
            raise ValueError("Converter constructor binding differs")
        executor = address(self.read(self.converter, "v4Executor()")[0])
        deploy_trace = self.rpc.call("debug_traceTransaction", [receipt["transactionHash"],
            {"tracer": "callTracer", "tracerConfig": {"withLog": True}, "timeout": "60s"}])
        if deploy_trace.get("error") or deploy_trace.get("input", "").lower() != creation_data.lower():
            raise ValueError("Actual converter creation trace differs")
        frames, todo = [], [deploy_trace]
        while todo:
            frame = todo.pop()
            frames.append(frame)
            if len(frames) > 1024:
                raise ValueError("Constructor trace work bound")
            todo.extend(frame.get("calls", []))
        children = [frame for frame in frames if frame.get("type") == "CREATE" and
            frame.get("from", "").lower() == self.converter and frame.get("to", "").lower() == executor]
        if len(children) != 1 or children[0].get("error"):
            raise ValueError("Typed V4 child construction not authenticated")
        child_compiled = contracts["src/ZZZV4RouteExecutor.sol"]["ZZZV4RouteExecutor"]
        if children[0].get("input", "").lower() != "0x" + child_compiled["evm"]["bytecode"]["object"].lower():
            raise ValueError("V4 executor creation is not the frozen normal artifact")
        executor_runtime = self._runtime_equivalence(executor, child_compiled, children[0].get("output"))
        (self.output / "CONVERTER_CONSTRUCTION_TRACE.json").write_text(json.dumps(deploy_trace) + "\n", encoding="utf-8")
        if self.read(executor, "parent()")[0] != int(self.converter, 16):
            raise ValueError("Converter executor parent differs")
        self.send(self.governance, rewards, encode("bindConverter(address)", self.converter), gas=1000000)
        self.send(self.governance, self.access, encode("seal()"), gas=500000)
        venue = self.read(self.pins["balancing_router"], "executionPoolAt(uint256)", 0)[0]
        config = self.read(self.pins["pools"], "get(bytes32)", venue, count=None)
        key = config[:5]
        if key[0] != 0 or key[1] != int(self.zzz, 16) or key[4] != 0:
            raise ValueError("Existing native fixed-ZZZ hookless route required")
        review = "0x" + keccak256(b"POPL maximum LP claims local converter review 20261120").hex()
        native_hash = "0x" + keccak256(b"ZZZ_NATIVE_ETH_V1").hex()
        policy = [self.zzz, ZERO, *key, self.pins["pool_manager"], self.pins["state_view"],
            self.codehash(self.zzz), native_hash, self.codehash(self.pins["pool_manager"]),
            self.codehash(self.pins["state_view"]), review]
        data = encode("addV4Route((address,address,(address,address,uint24,int24,address),address,address,bytes32,bytes32,bytes32,bytes32,bytes32))", *policy)
        self.route_id = "0x" + decoded(self.call(self.governance, self.converter, data, gas=2000000))[0].to_bytes(32, "big").hex()
        self.send(self.governance, self.converter, data, gas=2000000)
        self.send(self.governance, self.converter, encode("setEnabled(bool)", True), gas=500000)
        if self.read(self.converter, "conversionLossBps()")[0] != 100:
            raise ValueError("Conversion safeguard changed")
        self.proof["converter_setup"] = {"converter": self.converter, "executor": executor,
            "converter_code_hash": self.codehash(self.converter), "executor_code_hash": self.codehash(executor),
            "converter_runtime_equivalence": converter_runtime, "executor_runtime_equivalence": executor_runtime,
            "normal_artifact_sha256": sha(raw), "route_id": self.route_id, "policy_flat_words": policy,
            "fresh_local_deployer": self.deployer,
            "wrapper": ZERO, "native_v4_only": True, "known_fixture_bootstrap_seam": True,
            "no_actual_sealed_controller_rotation": True}

    def _runtime_equivalence(self, target, compiled, constructor_output):
        """Authenticate exact constructor-produced runtime without inventing immutable offsets.

        The frozen normal output omits immutableReferences. Parent creation is
        byte-identical to that artifact and has exact reviewed arguments; child
        input is independently verified in its actual constructor CREATE trace.
        Both whole runtime outputs must match actual deployed code byte-for-byte.
        """
        section = compiled["evm"]["deployedBytecode"]
        if not isinstance(constructor_output, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})+", constructor_output):
            raise ValueError("Missing authenticated constructor runtime output")
        expected = bytes.fromhex(constructor_output[2:])
        actual_raw = bytes.fromhex(self.rpc.call("eth_getCode", [target, "latest"])[2:])
        if not expected or len(actual_raw) != len(section["object"]) // 2:
            raise ValueError("Normal runtime length differs")
        if actual_raw != expected:
            raise ValueError("Deployed runtime differs from exact constructor output")
        return {"normal_unresolved_runtime_template_sha256": sha(bytes.fromhex(section["object"])),
            "constructor_output_sha256": sha(expected), "actual_runtime_sha256": sha(actual_raw),
            "runtime_bytes": len(actual_raw), "whole_constructor_output_identical": True,
            "immutable_offsets_not_in_frozen_normal_output": True}

    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
            self.proof["owned_node_stopped"] = self.proc.poll() is not None
        if hasattr(self, "log"):
            self.log.close()
        if self.output.is_dir():
            (self.output / "FIXTURE.json").write_text(json.dumps(self.proof, indent=2) + "\n", encoding="utf-8")
            (self.output / "SETUP_AND_SCENARIO_RECEIPTS.json").write_text(json.dumps(self.receipts, indent=2) + "\n", encoding="utf-8")
            if self.rpc is not None:
                (self.output / "RPC.json.gz").write_bytes(gzip.compress(json.dumps(self.rpc.records, separators=(",", ":")).encode(), mtime=0))

    def __exit__(self, kind, error, traceback):
        if error is not None:
            self.proof["exception"] = {"type": type(error).__name__, "message": str(error)}
        self.stop()
        return False
