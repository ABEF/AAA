"""Read only hashes/ownership of the explicitly named new Ubuntu lab's source/tools."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import sys


def pin(path):
    assert path.is_file() and not path.is_symlink()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    stat = path.stat()
    return {"sha256": digest.hexdigest(), "bytes": stat.st_size,
            "uid": stat.st_uid, "mode": oct(stat.st_mode & 0o777)}


def main():
    assert os.geteuid() == 0 and len(sys.argv) == 2
    lab = Path(sys.argv[1])
    assert re.fullmatch(r"/opt/popl-ubuntu-20261121-[0-9a-f]{8}", str(lab))
    assert lab.is_dir() and not lab.is_symlink() and lab.stat().st_uid == 0
    path = lab / "INPUT_MANIFEST.json"
    assert 0 < path.stat().st_size <= 2 * 1024 * 1024
    manifest = json.loads(path.read_bytes())
    assert manifest["credential_members"] == 0 and len(manifest["members"]) < 1000
    sources = {}
    for name, expected in manifest["members"].items():
        if not name.startswith("source/"):
            continue
        relative = PurePosixPath(name)
        assert str(relative) == name and ".." not in relative.parts and "\\" not in name and ":" not in name
        target = lab / name
        assert target.resolve().is_relative_to(lab) and expected["bytes"] <= 2 * 1024 * 1024
        sources[name] = pin(target)
    controller = "source/reports/ubuntu-keeper-20261121/run/capsule.py"
    result = {"schema": 1, "lab": str(lab), "input_manifest_sha256": pin(path)["sha256"],
              "controller_sha256": sources[controller]["sha256"], "source_members": sources,
              "tools": {name: pin(lab / "bin" / name) for name in ("anvil", "cast")},
              "source_contents_exported": False, "credentials_read": False}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
