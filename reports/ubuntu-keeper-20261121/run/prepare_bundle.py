"""Build a public-source/state-only capsule input; never copies credentials."""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
ENTRY = "e56b8d78aba465c673aa0379e6a4214860189e935c133dafc7da8c46aa99d2ff"
FEES = "13aa22d3dd99108d06d58a6aa96505a08b6a16c74e633e90b142bde826edb22b"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def member(folder, pinned, name):
    manifest = json.loads((folder / "EVIDENCE_MANIFEST.json").read_bytes())
    raw = (folder / "evidence.zip").read_bytes()
    assert sha(raw) == manifest["sha256"] == pinned
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        data = archive.read(name)
    assert len(data) == manifest["members"][name]["bytes"] and sha(data) == manifest["members"][name]["sha256"]
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert head == "a5570c95bbaba7472ba5370e43494b87246e0ea7"
    names = subprocess.run(["git", "ls-files", "-z", "keeper", "zzz_ops", "frontend_api", "indexer"],
                           cwd=ROOT, capture_output=True, check=True).stdout.decode().strip("\0").split("\0")
    contents = {}
    for name in names:
        if not (name.endswith(".py") or name == "indexer/event_schema.json"):
            continue
        data = subprocess.run(["git", "cat-file", "blob", "HEAD:" + name], cwd=ROOT, capture_output=True, check=True).stdout
        assert data == (ROOT / name).read_bytes(), "Unpublished production source differs: " + name
        contents["source/" + name] = data
    helper = "scripts/source9_rehearsal_fork.py"
    data = subprocess.run(["git", "cat-file", "blob", "HEAD:" + helper], cwd=ROOT, capture_output=True, check=True).stdout
    assert sha(data) == "6c52f68b6d66cfa28d18c13eee0a1930123dec82d54143446ac76ef9069629b4"
    contents["source/" + helper] = data
    for name in ("offline_cache.py", "prepare_config.py", "rpc_proxy.py", "capsule.py"):
        data = Path(__file__).with_name(name).read_bytes()
        contents["source/reports/ubuntu-keeper-20261121/run/" + name] = data
    entry = ROOT / "reports/pool-integration-20261120/entry"
    state = member(entry, ENTRY, "attempt1/owned-state.dump")
    assert sha(state) == "b4c01efff093fa73d69c837d004c534f456a1776af8fb84dfb6043e69bda238a"
    with gzip.GzipFile(fileobj=io.BytesIO(state)) as compressed:
        restored = compressed.read(16 * 1024 * 1024 + 1)
    assert len(restored) <= 16 * 1024 * 1024
    json.loads(restored)
    contents["public/restore-state.json"] = restored
    contents["public/instances.json"] = member(entry, ENTRY, "attempt1/construction/instances.json")
    contents["public/entry-state-capture.json"] = member(entry, ENTRY, "attempt1/owned-state-capture.json")
    contents["public/entry-helper-reuse.json"] = member(entry, ENTRY, "attempt1/HELPER_REUSE.json")
    contents["public/entry-receipts.json"] = member(entry, ENTRY, "attempt1/ALL_SETUP_SCENARIO_RECEIPTS.json")
    cache = member(ROOT / "reports/pool-fees-20261121/run", FEES, "attempt2/relay/full-cache.json")
    assert len(json.loads(cache)["entries"]) == 307
    contents["public/cache.json"] = cache
    manifest = {"schema": 1, "purpose": "isolated_stock_keeper_ubuntu_inputs_no_credentials",
                "baseline": head, "entry_archive_sha256": ENTRY, "cache_archive_sha256": FEES,
                "restore_state_bytes": len(restored), "cache_sha256": sha(cache),
                "members": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in sorted(contents.items())},
                "credential_members": 0, "production_approved": False}
    contents["INPUT_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output = args.output / "public-capsule-inputs.tar.gz"
    with tarfile.open(output, "x:gz") as archive:
        for name, data in sorted(contents.items()):
            assert not name.startswith("/") and ".." not in Path(name).parts
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime, info.uid, info.gid = len(data), 0o444, 0, 0, 0
            archive.addfile(info, io.BytesIO(data))
    receipt = {"schema": 1, "archive_sha256": sha(output.read_bytes()), "archive_bytes": output.stat().st_size,
               "members": len(contents), "input_manifest_sha256": sha(contents["INPUT_MANIFEST.json"]),
               "manifest": manifest, "private_data_included": False, "source_sha256": sha(Path(__file__).read_bytes())}
    (args.output / "BUNDLE.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: value for key, value in receipt.items() if key != "manifest"}))


if __name__ == "__main__":
    main()
