"""Root supervisor for ONE new, isolated Ubuntu normal-keeper rehearsal.

Not a deployment utility. Only uniquely named /opt lab paths/units are touched.
The worker is the unchanged normal keeper CLI. No credentials leave this lab.
"""
from pathlib import Path
import argparse
import hashlib
import http.client
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import time

UID = GID = 65534
OWNER = "0x000000000000000000000000000000000000a0a0"
POOL = "0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b"
TOOLS = {"anvil": "05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd",
         "cast": "d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970"}
PROPERTIES = ("Id", "LoadState", "ActiveState", "SubState", "MainPID", "NRestarts", "Result", "ExecMainStatus",
              "PrivateNetwork", "JoinsNamespaceOf", "User", "Group", "WatchdogUSec", "InvocationID",
              "ControlGroup", "ExecStart", "KillMode", "NoNewPrivileges", "MemoryMax", "TasksMax")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value, exclusive=True):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def read(path):
    return json.loads(path.read_bytes())


class Lab:
    def __init__(self, path):
        assert os.name == "posix" and os.geteuid() == 0
        assert re.fullmatch(r"/opt/popl-ubuntu-20261121-[0-9a-f]{8}", str(path))
        assert not path.is_symlink()
        self.path = path
        self.name = path.name
        self.source = path / "source"
        self.tools = self.source / "reports/ubuntu-keeper-20261121/run"
        self.public = path / "public"

    def unit(self, name):
        assert name in ("cache", "anvil", "proxy", "keeper")
        return self.name + "-" + name + ".service"

    def command(self, argv, timeout=60, worker=False, env=None, stdin=None):
        def unprivileged():
            os.setgroups([])
            os.setgid(GID)
            os.setuid(UID)
            os.umask(0o077)
        clean = {"PATH": str(self.path / "bin") + ":/usr/bin:/bin", "LANG": "C.UTF-8",
                 "HOME": str(self.path / "secrets"), "PYTHONPATH": str(self.source),
                 "PYTHONDONTWRITEBYTECODE": "1"}
        clean.update(env or {})
        result = subprocess.run(argv, input=stdin, capture_output=True, timeout=timeout,
                                cwd=self.source if self.source.exists() else "/opt", env=clean,
                                preexec_fn=unprivileged if worker else None)
        assert len(result.stdout) <= 8 * 1024 * 1024 and len(result.stderr) <= 1024 * 1024
        return result

    def must(self, argv, **kw):
        result = self.command(argv, **kw)
        # Do not print arbitrary subprocess output; keygen is explicitly separate.
        if result.returncode:
            raise RuntimeError("Owned command refused: " + str(argv[0]) + "; stderr SHA=" + sha(result.stderr))
        return result.stdout

    def props(self, name):
        argv = ["/usr/bin/systemctl", "show", self.unit(name), "--no-pager"]
        for field in PROPERTIES:
            argv += ["-p", field]
        reply = self.command(argv)
        result = dict(line.split("=", 1) for line in reply.stdout.decode().splitlines() if "=" in line)
        if reply.returncode:
            assert result.get("LoadState") == "not-found", "Owned unit inspection failed"
            result.setdefault("MainPID", "0")
        return result

    def cache_pid(self):
        p = self.props("cache")
        assert p["Id"] == self.unit("cache") and p["ActiveState"] == "active"
        pid = int(p["MainPID"])
        assert pid > 1 and self.path.as_posix().encode() in Path(f"/proc/{pid}/cmdline").read_bytes()
        return pid

    def rpc(self, method, params=None, port=18545):
        # Namespace selection is checked against the owned cache MainPID above.
        # Public bootstrap/read data only; no private keys or signed bodies here.
        assert method in {"web3_clientVersion", "eth_chainId", "eth_getBlockByNumber", "eth_getCode",
                          "eth_call", "eth_getTransactionReceipt", "eth_getTransactionCount", "eth_blockNumber",
                          "eth_getTransactionByHash",
                          "eth_getBalance", "anvil_setBalance", "anvil_impersonateAccount",
                          "anvil_stopImpersonatingAccount", "evm_setNextBlockTimestamp", "evm_mine",
                          "evm_setAutomine", "evm_setIntervalMining", "eth_sendTransaction"}
        assert port in (18545, 18547, 18548)
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
        code = ("import http.client,json,sys; b=sys.stdin.buffer.read(); "
                f"c=http.client.HTTPConnection('127.0.0.1',{port},timeout=30); "
                "c.request('POST','/',b,{'Content-Type':'application/json'}); "
                "r=c.getresponse(); d=r.read(8388609); assert r.status==200 and len(d)<=8388608; sys.stdout.buffer.write(d)")
        raw = self.must(["/usr/bin/nsenter", "--target", str(self.cache_pid()), "--net",
                         "--setuid", str(UID), "--setgid", str(GID), "/usr/bin/python3", "-c", code],
                        stdin=body, timeout=40)
        reply = json.loads(raw)
        if "error" in reply:
            raise RuntimeError("Owned RPC " + method + " refused: " + json.dumps(reply["error"])[:700])
        return reply["result"]

    def calldata(self, signature, *values):
        return self.must([str(self.path / "bin/cast"), "calldata", signature, *map(str, values)], worker=True).decode().strip()

    def ethcall(self, to, signature, *values):
        return self.rpc("eth_call", [{"to": to, "data": self.calldata(signature, *values)}, "latest"])

    def private_dir(self, name):
        path = self.path / name
        path.mkdir(mode=0o700)
        os.chown(path, UID, GID)
        return path

    def install(self, bundle, digest):
        assert not self.path.exists() and bundle.is_file() and not bundle.is_symlink()
        data = bundle.read_bytes()
        assert len(data) <= 32 * 1024 * 1024 and sha(data) == digest
        self.path.mkdir(mode=0o755)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            entries = archive.getmembers()
            assert len(entries) <= 1000 and sum(x.size for x in entries) <= 64 * 1024 * 1024
            assert len({entry.name for entry in entries}) == len(entries)
            packed_manifest = json.loads(archive.extractfile("INPUT_MANIFEST.json").read())
            assert set(entry.name for entry in entries) == set(packed_manifest["members"]) | {"INPUT_MANIFEST.json"}
            for entry in entries:
                assert entry.isfile() and not entry.name.startswith("/") and ".." not in Path(entry.name).parts
                assert entry.name == "INPUT_MANIFEST.json" or entry.name.startswith(("source/", "public/"))
                target = self.path / entry.name
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(entry) as handle:
                    target.write_bytes(handle.read())
                target.chmod(0o444)
        manifest = read(self.path / "INPUT_MANIFEST.json")
        assert manifest["baseline"] == "a5570c95bbaba7472ba5370e43494b87246e0ea7"
        assert manifest["credential_members"] == 0
        for name, entry in manifest["members"].items():
            blob = (self.path / name).read_bytes()
            assert len(blob) == entry["bytes"] and sha(blob) == entry["sha256"]
        (self.path / "bin").mkdir()
        for name, digest in TOOLS.items():
            origin = Path("/opt/zzz-keeper-staging/bin") / name
            raw = origin.read_bytes()
            assert sha(raw) == digest
            target = self.path / "bin" / name
            target.write_bytes(raw)
            target.chmod(0o555)
            assert target.stat().st_uid == 0 and sha(target.read_bytes()) == digest
        for tree in (self.source, self.path / "bin"):
            for directory, _dirs, _files in os.walk(tree):
                Path(directory).chmod(0o555)
        for name in ("secrets", "runtime", "dryrun", "logs", "evidence"):
            self.private_dir(name)
        write(self.public / "proxy-control.json", {"primary": "healthy", "secondary": "healthy"})
        (self.public / "proxy-control.json").chmod(0o444)
        write(self.path / "lab.json", {"schema": 1, "bundle_sha256": sha(data),
              "created_utc": time.time(), "phase": "installed", "private_data_exported": False})
        return {"phase": "installed", "lab": str(self.path), "bundle_sha256": sha(data), "credentials_created": False}

    def unit_start(self, name, argv, stage):
        assert stage in ("preflight", "final")
        base = ["User=nobody", "Group=nogroup", "UMask=0077", "NoNewPrivileges=yes",
                "PrivateNetwork=yes", "PrivateTmp=yes", "PrivateDevices=yes", "ProtectSystem=strict", "ProtectHome=yes",
                "ProtectKernelTunables=yes", "ProtectKernelModules=yes", "ProtectControlGroups=yes",
                "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6", "CapabilityBoundingSet=",
                "MemoryDenyWriteExecute=no", "LimitCORE=0", "TasksMax=64", "MemoryMax=512M",
                "CPUQuota=50%", "RuntimeMaxSec=1800", "KillMode=control-group"]
        if name != "keeper":
            base += ["InaccessiblePaths=" + str(self.path / "secrets")]
        if name != "cache":
            base += ["JoinsNamespaceOf=" + self.unit("cache"), "Requires=" + self.unit("cache"),
                     "After=" + self.unit("cache")]
        if name == "keeper":
            base += ["WatchdogSec=120", "NotifyAccess=main", "TimeoutStopSec=120", "Restart=on-failure",
                     "RestartSec=30", "WatchdogSignal=SIGKILL", "MemoryMax=256M", "CPUQuota=25%",
                     "TasksMax=32"]
            writes = [self.path / "runtime", self.path / "logs"]
        elif name == "cache":
            base += ["MemoryMax=128M", "CPUQuota=25%", "TasksMax=32"]
            writes = [self.path / "evidence"]
        elif name == "proxy":
            base += ["MemoryMax=128M", "CPUQuota=25%", "TasksMax=32"]
            writes = [self.path / "evidence"]
        else:
            writes = [self.path / "runtime", self.path / "logs"]
        base += ["ReadWritePaths=" + " ".join(map(str, writes)), "WorkingDirectory=" + str(self.source)]
        # Anvil output is discarded; it must never log signed bodies or key banners.
        if name == "anvil":
            base += ["StandardOutput=null", "StandardError=null"]
        else:
            log = self.path / "logs" / (stage + "-" + name + ".log")
            base += ["StandardOutput=append:" + str(log), "StandardError=append:" + str(log)]
        cmd = ["/usr/bin/systemd-run", "--quiet", "--collect", "--unit", self.unit(name)]
        for prop in base:
            cmd += ["--property", prop]
        cmd += ["--setenv=PYTHONPATH=" + str(self.source), "--setenv=PYTHONDONTWRITEBYTECODE=1",
                "--setenv=PYTHONUNBUFFERED=1", "--", *argv]
        self.must(cmd)

    def start(self, stage):
        meta = read(self.path / "lab.json")
        assert meta["phase"] in ("installed", "preflight_stopped")
        cache = self.public / ("cache.json" if stage == "preflight" else "frozen-cache.json")
        assert cache.is_file() and cache.stat().st_uid == 0 and cache.stat().st_mode & 0o022 == 0
        if stage == "final":
            frozen = read(self.public / "FROZEN_CACHE.json")
            assert sha(cache.read_bytes()) == frozen["sha256"]
            assert not (self.path / "runtime/state.json").exists()
        cacheout = self.path / "evidence" / (stage + "-cache")
        proxyout = self.path / "evidence" / (stage + "-proxy")
        self.unit_start("cache", ["/usr/bin/python3", str(self.tools / "offline_cache.py"), "--cache", str(cache),
                        "--sha256", sha(cache.read_bytes()), "--output", str(cacheout), "--port", "18546"], stage)
        self.wait_file(cacheout / "ready.json", 15)
        self.unit_start("anvil", [str(self.path / "bin/anvil"), "--host", "127.0.0.1", "--port", "18545",
                        "--chain-id", "4663", "--fork-url", "http://127.0.0.1:18546", "--fork-block-number", "119107223",
                        "--load-state", str(self.public / "restore-state.json"), "--block-time", "1",
                        "--gas-limit", "60000000", "--accounts", "0", "--no-storage-caching", "--silent"], stage)
        until = time.monotonic() + 20
        while True:
            try:
                assert int(self.rpc("eth_chainId"), 16) == 4663
                break
            except Exception:
                if time.monotonic() >= until:
                    raise
                time.sleep(0.25)
        self.unit_start("proxy", ["/usr/bin/python3", str(self.tools / "rpc_proxy.py"), "--control",
                        str(self.public / "proxy-control.json"), "--output", str(proxyout)], stage)
        self.wait_file(proxyout / "ready.json", 15)
        meta.update(phase=stage + "_running", stage=stage)
        write(self.path / "lab.json", meta, False)
        return self.snapshot("started_" + stage)

    def freeze(self, cache, digest):
        assert read(self.path / "lab.json")["phase"] == "preflight_stopped"
        assert not (self.path / "runtime/state.json").exists()
        blob = cache.read_bytes()
        assert len(blob) <= 64 * 1024 * 1024 and sha(blob) == digest
        sys.path.insert(0, str(self.source))
        from scripts import source9_rehearsal_fork as F
        supplied, original = F._loads(blob), read(self.public / "cache.json")
        assert supplied["anchor_number"] == original["anchor_number"] == 119107223
        assert supplied["anchor_hash"] == original["anchor_hash"]
        for key, entry in original["entries"].items():
            assert supplied["entries"][key] == entry
        validator = object.__new__(F._ForkCache)
        validator.anchor_number, validator.anchor_hash = supplied["anchor_number"], supplied["anchor_hash"]
        assert len(supplied["entries"]) <= F.MAX_CACHE_ENTRIES
        for key, row in supplied["entries"].items():
            request = {"jsonrpc": "2.0", "id": 1, "method": row["method"], "params": row["params"]}
            assert validator._validate(request) == (row["method"], row["params"])
            assert validator._cacheable(row["method"], row["params"])
            assert validator._valid_result(row["method"], row["result"], row["params"])
            assert key == F._digest({"method": row["method"], "params": row["params"]})
            assert row["result_sha256"] == F._digest(row["result"])
        target = self.public / "frozen-cache.json"
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        with os.fdopen(fd, "wb") as out:
            out.write(blob)
            out.flush()
            os.fsync(out.fileno())
        result = {"sha256": digest, "entries": len(supplied["entries"]), "original_entries_unchanged": True,
                  "no_live_journal_initialized": True, "network_requests_here": 0, "frozen_time": time.time()}
        write(self.public / "FROZEN_CACHE.json", result)
        (self.public / "FROZEN_CACHE.json").chmod(0o444)
        return result

    @staticmethod
    def wait_file(path, seconds):
        end = time.monotonic() + seconds
        while not path.is_file():
            assert time.monotonic() < end, "Owned process readiness marker missing"
            time.sleep(0.1)

    def key(self):
        assert read(self.path / "lab.json")["phase"] == "installed"
        password = self.path / "secrets/password"
        assert not password.exists()
        fd = os.open(password, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as handle:
            handle.write(secrets.token_hex(32) + "\n")
        os.chown(password, UID, GID)
        # Password through env only; all keygen output is discarded, never journalled.
        self.must([str(self.path / "bin/cast"), "wallet", "new", str(self.path / "secrets"), "keeper"],
                  worker=True, env={"CAST_PASSWORD": password.read_text().strip()}, timeout=30)
        keystore = self.path / "secrets/keeper"
        assert keystore.is_file() and keystore.stat().st_uid == UID
        keystore.chmod(0o600)
        sender = self.must([str(self.path / "bin/cast"), "wallet", "address", "--keystore", str(keystore),
                            "--password-file", str(password)], worker=True).decode().strip().lower()
        assert re.fullmatch("0x[0-9a-f]{40}", sender) and sender != OWNER
        write(self.public / "sender.json", {"address": sender, "encrypted": True, "secret_exported": False})
        (self.public / "sender.json").chmod(0o444)
        for runtime in ("dryrun", "runtime"):
            self.must(["/usr/bin/python3", str(self.tools / "prepare_config.py"), "--instances", str(self.public / "instances.json"),
                       "--sender", sender, "--runtime", str(self.path / runtime), "--cast", str(self.path / "bin/cast"),
                       "--keystore", str(keystore), "--password-file", str(password)], worker=True)
        return {"phase": "fresh_wallet_and_configs", "sender": sender, "secret_exported": False,
                "mode": "0600", "uid": UID, "rpc_urls_fixed": [18547, 18548]}

    def tx(self, target, data):
        tx = {"from": OWNER, "to": target, "data": data, "value": "0x0", "gas": hex(4000000)}
        h = self.rpc("eth_sendTransaction", [tx])
        end = time.monotonic() + 15
        while True:
            receipt = self.rpc("eth_getTransactionReceipt", [h])
            if receipt:
                assert int(receipt["status"], 16) == 1
                return {"transaction": tx, "receipt": receipt}
            assert time.monotonic() < end
            time.sleep(0.1)

    def bootstrap(self):
        stage = read(self.path / "lab.json")["stage"]
        before = self.rpc("eth_getBlockByNumber", ["latest", False])
        now = int(time.time())
        if int(before["timestamp"], 16) < now:
            self.rpc("evm_setNextBlockTimestamp", [now])
            self.rpc("evm_mine")
        sender = read(self.public / "sender.json")["address"]
        rows = read(self.public / "instances.json")
        access = next(r["address"] for r in rows if r["role"] == "access")
        self.rpc("anvil_setBalance", [sender, hex(10**18)])
        assert int(self.rpc("eth_getTransactionCount", [sender, "latest"]), 16) == 0
        self.rpc("anvil_impersonateAccount", [OWNER])
        setup = [self.tx(access, self.calldata("setKeeper(address,bool)", sender, "true"))]
        # Keep exact controlled answers; explicitly align only old fixture timestamps.
        receipts = read(self.public / "entry-receipts.json")
        # Original deploy records are discovered by their declared contract label only.
        feeds = []
        def visit(obj):
            if isinstance(obj, dict):
                label = str(obj.get("label", obj.get("name", obj.get("key", ""))))
                if any(role in label for role in ("eth_feed_a", "eth_feed_b", "zzz_feed_a", "zzz_feed_b")):
                    rec = obj.get("receipt", {})
                    if isinstance(rec, dict) and rec.get("contractAddress"):
                        feeds.append(rec["contractAddress"])
                for val in obj.values():
                    visit(val)
            elif isinstance(obj, list):
                for val in obj:
                    visit(val)
        visit(receipts)
        assert len(set(feeds)) == 4, "Expected four explicit controlled feed deployment records"
        feedproof = []
        for feed in sorted(set(feeds)):
            raw = self.ethcall(feed, "latestRoundData()")
            words = [int(raw[i:i+64], 16) for i in range(2, len(raw), 64)]
            assert len(words) == 5 and words[1] > 0
            timestamp = int(self.rpc("eth_getBlockByNumber", ["latest", False])["timestamp"], 16)
            setup.append(self.tx(feed, self.calldata("set(int256,uint256,uint256)", words[1], timestamp, timestamp)))
            after = self.ethcall(feed, "latestRoundData()")
            assert int(after[66:130], 16) == words[1]
            feedproof.append({"address": feed, "before": raw, "after": after, "answers_unchanged": True})
        self.rpc("anvil_stopImpersonatingAccount", [OWNER])
        assert int(self.ethcall(access, "keepers(address)", sender), 16) == 1
        assert int(self.ethcall(access, "guardians(address)", sender), 16) == 0
        assert int(self.ethcall(access, "governance()"), 16) != int(sender, 16)
        result = {"stage": stage, "head_before": before, "head_after": self.rpc("eth_getBlockByNumber", ["latest", False]),
                  "sender": sender, "keeper": True, "guardian": False, "governor": False,
                  "controlled_prices_unchanged": True, "feedproof": feedproof, "setup": setup,
                  "sender_nonce": 0, "local_fixture_funding_wei": str(10**18)}
        write(self.path / "evidence" / (stage + "-bootstrap.json"), result)
        return result

    def cli(self, mode):
        meta = read(self.path / "lab.json")
        assert mode in ("preflight", "initialize", "lock_contender")
        if mode == "preflight":
            assert meta["phase"] in ("preflight_running", "final_running")
            config = self.path / "dryrun/config.json"
            args = ["--once"]
        else:
            assert meta["phase"] == "final_running"
            assert self.cache_counts("final")["misses"] == 0
            config = self.path / "runtime/config.json"
            args = ["--initialize-state"] if mode == "initialize" else ["--live", "--once"]
        argv = ["/usr/bin/nsenter", "--target", str(self.cache_pid()), "--net", "--setuid", str(UID), "--setgid", str(GID),
                "/usr/bin/python3", "-m", "keeper.monitor", "--config", str(config), *args]
        result = self.command(argv, timeout=180)
        # Normal keeper output has no keys; preserve private raw logs and sanitized outcome.
        path = self.path / "logs" / (meta["stage"] + "-" + mode + ".log")
        assert not path.exists()
        path.write_bytes(result.stdout + result.stderr)
        path.chmod(0o600)
        record = {"mode": mode, "stage": meta["stage"], "exit_code": result.returncode,
                  "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
                  "output": result.stdout.decode(errors="replace"), "cache": self.cache_counts(meta["stage"])}
        write(self.path / "evidence" / (meta["stage"] + "-" + mode + ".json"), record)
        if mode == "initialize":
            assert result.returncode == 0
            self.save_journal("initial-journal.json")
        return record

    def save_journal(self, name):
        assert re.fullmatch(r"[a-z-]+-journal\.json", name)
        source = self.path / "runtime/state.json"
        raw = source.read_bytes()
        # Journal schema contains transaction calldata/review, not key material.
        state = json.loads(raw)
        assert state["sender"] == read(self.public / "sender.json")["address"]
        target = self.path / "evidence" / name
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        return {"path": name, "bytes": len(raw), "sha256": sha(raw)}

    def cache_counts(self, stage):
        path = self.path / "evidence" / (stage + "-cache/events.jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        return {"hits": sum(x["event"] == "hit" for x in rows), "misses": sum(x["event"] == "miss" for x in rows),
                "rejected": sum(x["event"] == "rejected" for x in rows)}

    def live(self):
        assert read(self.path / "lab.json")["phase"] == "final_running"
        assert read(self.path / "evidence/final-preflight.json")["exit_code"] == 0
        assert self.cache_counts("final")["misses"] == 0
        state = read(self.path / "runtime/state.json")
        assert state["next_nonce"] == 0 and state["pending"] is None
        self.unit_start("keeper", ["/usr/bin/python3", "-m", "keeper.monitor", "--config",
                        str(self.path / "runtime/config.json"), "--live"], "final")
        return self.snapshot("live_started")

    def mining(self, hold):
        # Anvil-only controls inside the verified owned namespace; no live journal edit.
        assert read(self.path / "lab.json")["phase"] == "final_running"
        if hold:
            assert not (self.path / "runtime/state.json").exists() or read(self.path / "runtime/state.json")["pending"] is None
            self.rpc("evm_setIntervalMining", [0])
            self.rpc("evm_setAutomine", [False])
        else:
            self.rpc("evm_setAutomine", [True])
            self.rpc("evm_mine")
            self.rpc("evm_setIntervalMining", [1])
        return {"owned_Anvil_mining_held": hold, "head": self.rpc("eth_getBlockByNumber", ["latest", False])}

    def pending(self):
        deadline = time.monotonic() + 45
        path = self.path / "runtime/state.json"
        while time.monotonic() < deadline:
            state = read(path)
            pending = state.get("pending")
            if isinstance(pending, dict) and pending.get("hash"):
                result = self.snapshot("durable_pending_hash")
                assert result["pending"]["nonce"] == 0
                assert self.rpc("eth_getTransactionReceipt", [result["pending"]["hash"]]) is None
                write(self.path / "evidence/durable-pending.json", result)
                self.save_journal("durable-pending-journal.json")
                return result
            time.sleep(0.05)
        raise RuntimeError("Normal keeper did not persist a pending hash within the bounded window")

    def proof(self):
        state = read(self.path / "runtime/state.json")
        assert state["pending"] is None and state["next_nonce"] == 1
        original = read(self.path / "evidence/durable-pending-journal.json")
        txhash = original["pending"]["hash"]
        tx = self.rpc("eth_getTransactionByHash", [txhash])
        public = {key: tx[key] for key in ("hash", "from", "to", "input", "value", "nonce", "gas", "gasPrice", "type",
                  "chainId", "maxFeePerGas", "maxPriorityFeePerGas", "blockHash", "blockNumber", "transactionIndex") if key in tx}
        receipt = self.rpc("eth_getTransactionReceipt", [txhash])
        header = self.rpc("eth_getBlockByNumber", [receipt["blockNumber"], False])
        sender = read(self.public / "sender.json")["address"]
        result = {"transaction": public, "receipt": receipt, "header": header,
                  "sender_balance": self.rpc("eth_getBalance", [sender, "latest"]),
                  "latest_nonce": self.rpc("eth_getTransactionCount", [sender, "latest"]),
                  "pending_nonce": self.rpc("eth_getTransactionCount", [sender, "pending"]),
                  "journal": self.save_journal("final-journal.json")}
        write(self.path / "evidence/final-proof.json", result)
        return result

    def snapshot(self, label):
        result = {"schema": 1, "label": label, "time": time.time(), "units": {}, "files": {}, "network": {}}
        for name in ("cache", "anvil", "proxy", "keeper"):
            props = self.props(name)
            result["units"][name] = props
            pid = int(props.get("MainPID", "0"))
            if pid > 1:
                result["network"][name] = os.readlink(f"/proc/{pid}/ns/net")
        result["host_network"] = os.readlink("/proc/1/ns/net")
        nets = list(result["network"].values())
        if nets:
            assert len(set(nets)) == 1 and nets[0] != result["host_network"]
        for name in ("state.json", "health.json", "config.json"):
            path = self.path / "runtime" / name
            if path.exists():
                stat = path.stat()
                result["files"][name] = {"sha256": sha(path.read_bytes()), "bytes": stat.st_size,
                                         "uid": stat.st_uid, "mode": oct(stat.st_mode & 0o777)}
                if name == "state.json":
                    state = read(path)
                    # State has no keystore contents; keep original journal private nonetheless.
                    result["state"] = {k: state.get(k) for k in ("schema", "next_nonce", "last", "spent", "receipt_anchor")}
                    p = state.get("pending")
                    result["pending"] = None if p is None else {k: p.get(k) for k in ("key", "nonce", "hash", "to", "value", "fee_review")}
                if name == "health.json":
                    result["health"] = read(path)
        meta = read(self.path / "lab.json")
        if "stage" in meta:
            result["cache"] = self.cache_counts(meta["stage"])
        return result

    def fault(self, primary, secondary):
        assert primary in ("healthy", "outage", "body_trickle") and secondary in ("healthy", "outage", "body_trickle")
        target = self.public / "proxy-control.json"
        tmp = self.public / ("control-" + secrets.token_hex(4) + ".json")
        write(tmp, {"primary": primary, "secondary": secondary})
        tmp.chmod(0o444)
        os.replace(tmp, target)
        return {"primary": primary, "secondary": secondary, "time": time.time()}

    def stop(self, preflight=False):
        names = ("keeper", "proxy", "anvil", "cache")
        result = {}
        for name in names:
            before = self.props(name)
            self.command(["/usr/bin/systemctl", "stop", self.unit(name)], timeout=140)
            after = self.props(name)
            result[name] = {"before": before, "after": after}
            assert int(after.get("MainPID", "0")) == 0
        if preflight:
            meta = read(self.path / "lab.json")
            assert meta["phase"] == "preflight_running"
            meta["phase"] = "preflight_stopped"
            write(self.path / "lab.json", meta, False)
        return {"stopped": result, "existing_services_modified": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lab", required=True, type=Path)
    p.add_argument("action", choices=("install", "key", "start-preflight", "start-final", "bootstrap", "preflight",
                                     "initialize", "live", "sample", "lock-contender", "kill-keeper", "stop-keeper",
                                     "fault", "freeze", "cache-events", "proof", "hold-mining", "resume-mining", "await-pending", "stop-preflight", "stop"))
    p.add_argument("--bundle", type=Path)
    p.add_argument("--sha256")
    p.add_argument("--primary", default="healthy")
    p.add_argument("--secondary", default="healthy")
    args = p.parse_args()
    lab = Lab(args.lab)
    if args.action == "install":
        result = lab.install(args.bundle, args.sha256)
    elif args.action == "key":
        result = lab.key()
    elif args.action == "freeze":
        result = lab.freeze(args.bundle, args.sha256)
    elif args.action == "cache-events":
        stage = read(lab.path / "lab.json")["stage"]
        path = lab.path / "evidence" / (stage + "-cache/events.jsonl")
        result = {"stage": stage, "events": [json.loads(line) for line in path.read_text().splitlines()]}
    elif args.action.startswith("start-"):
        result = lab.start(args.action.split("-", 1)[1])
    elif args.action == "bootstrap":
        result = lab.bootstrap()
    elif args.action in ("preflight", "initialize", "lock-contender"):
        result = lab.cli(args.action.replace("-", "_"))
    elif args.action == "live":
        result = lab.live()
    elif args.action in ("hold-mining", "resume-mining"):
        result = lab.mining(args.action == "hold-mining")
    elif args.action == "await-pending":
        result = lab.pending()
    elif args.action == "proof":
        result = lab.proof()
    elif args.action == "sample":
        result = lab.snapshot("sample")
    elif args.action in ("kill-keeper", "stop-keeper"):
        if args.action == "kill-keeper":
            assert read(lab.path / "runtime/state.json").get("pending", {}).get("hash") is not None
        command = ["/usr/bin/systemctl", "kill", "--kill-whom=main", "--signal=SIGKILL", lab.unit("keeper")] if args.action == "kill-keeper" else ["/usr/bin/systemctl", "stop", lab.unit("keeper")]
        lab.must(command, timeout=140)
        result = lab.snapshot(args.action)
    elif args.action == "fault":
        result = lab.fault(args.primary, args.secondary)
    else:
        result = lab.stop(args.action == "stop-preflight")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
