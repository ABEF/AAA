"""Pack immutable local evidence into a standard, lossless tar.xz archive.

No program, node or API is executed. Repeated runtime wire has its separate
lossless XZ representation. Original captures and failed attempts stay outside
Git as well as the selected published evidence; nothing is rewritten/deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            result.update(data)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    if args.archive.exists() or args.manifest.exists():
        raise ValueError("Use exclusive archive/manifest paths")
    stages = ("attempt02", "late-tax32-03", "late-tax32-04")
    selected, omitted = [], []
    for stage in stages:
        for path in sorted((source / stage).rglob("*")):
            if path.is_symlink():
                raise ValueError("Evidence symlinks are not accepted")
            if not path.is_file():
                continue
            relative = path.relative_to(source).as_posix()
            if ".." in PurePosixPath(relative).parts or ":" in relative:
                raise ValueError("Non-relative archive path")
            row = {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}
            # The whole large wire is separately losslessly published. Duplicate
            # aggregate JSON has the exact selected qualification file as source.
            if relative == "attempt02/node/rpc-records.json.gz" or relative == "attempt02/CAMPAIGN_RESULT.json":
                omitted.append(row)
            else:
                selected.append((path, row))
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.archive, "x:xz", preset=6) as archive:
        for path, row in selected:
            info = tarfile.TarInfo(row["path"])
            info.size, info.mode, info.mtime = row["bytes"], 0o444, 0
            with path.open("rb") as stream:
                archive.addfile(info, stream)
            if digest(path) != row["sha256"]:
                raise ValueError("Source evidence changed during publication")
    # Independently stream every archived member and compare original bytes.
    expected = {row["path"]: row for _, row in selected}
    observed = set()
    with tarfile.open(args.archive, "r|xz") as archive:
        for member in archive:
            if not member.isfile() or member.name not in expected or member.name in observed:
                raise ValueError("Unexpected/nonregular/duplicate archive member")
            row = expected[member.name]
            if member.size != row["bytes"]:
                raise ValueError("Archive member length differs")
            result = hashlib.sha256()
            with archive.extractfile(member) as stream:
                while data := stream.read(1024 * 1024):
                    result.update(data)
            if result.hexdigest() != row["sha256"]:
                raise ValueError("Archive member changed")
            observed.add(member.name)
    if observed != set(expected):
        raise ValueError("Archive omitted a selected original")
    result = {"schema": 1, "format": "standard tar.xz; regular relative files only",
        "original_root": str(source), "archive_sha256": digest(args.archive),
        "archive_bytes": args.archive.stat().st_size, "files": list(expected.values()),
        "selected_original_bytes": sum(row["bytes"] for row in expected.values()),
        "omitted_from_this_archive": omitted, "every_member_roundtrip_verified": True,
        "source_files_modified": False, "evm_executed": False, "production_approved": False}
    with args.manifest.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("archive_bytes", "selected_original_bytes",
        "every_member_roundtrip_verified")}))


if __name__ == "__main__":
    main()
