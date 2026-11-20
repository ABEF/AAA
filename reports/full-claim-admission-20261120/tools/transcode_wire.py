"""Lossless streaming gzip-to-XZ evidence packaging; no RPC or JSON rewriting."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import time

CHUNK = 1024 * 1024
MAX_EXPANDED = 8 * 1024 * 1024 * 1024  # finite report archive, never an API limit


def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(CHUNK):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.destination.exists() or args.manifest.exists():
        raise ValueError("Use exclusive new output paths")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    source_sha = sha_file(args.source)
    expanded, total = hashlib.sha256(), 0
    started = time.monotonic()
    # XZ keeps a larger dictionary than gzip. Repeated runtime observations
    # remain present, in their exact original order, instead of being discarded.
    with gzip.open(args.source, "rb") as source, args.destination.open("xb") as raw:
        with lzma.LZMAFile(raw, "w", preset=6) as target:
            while block := source.read(CHUNK):
                total += len(block)
                if total > MAX_EXPANDED:
                    raise ValueError("Report archive exceeds its explicit expansion bound")
                expanded.update(block)
                target.write(block)
    recovered, recovered_size = hashlib.sha256(), 0
    with lzma.open(args.destination, "rb") as stream:
        while block := stream.read(CHUNK):
            recovered_size += len(block)
            if recovered_size > MAX_EXPANDED:
                raise ValueError("XZ expansion bound")
            recovered.update(block)
    if recovered_size != total or recovered.digest() != expanded.digest() or sha_file(args.source) != source_sha:
        raise ValueError("Transcoded archive did not preserve exact original bytes")
    result = {"schema": 1, "kind": "lossless_rpc_evidence_transcode",
        "original_path": str(args.source.resolve()), "original_compression": "gzip",
        "original_compressed_sha256": source_sha, "original_compressed_bytes": args.source.stat().st_size,
        "published_path": str(args.destination.resolve()), "published_compression": "xz",
        "published_sha256": sha_file(args.destination), "published_bytes": args.destination.stat().st_size,
        "exact_expanded_sha256": expanded.hexdigest(), "exact_expanded_bytes": total,
        "roundtrip_verified": True, "json_or_record_order_changed": False,
        "source_modified": False, "evm_executed": False, "production_approved": False,
        "elapsed_seconds": time.monotonic() - started}
    with args.manifest.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("roundtrip_verified", "original_compressed_bytes",
          "published_bytes", "exact_expanded_bytes", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
