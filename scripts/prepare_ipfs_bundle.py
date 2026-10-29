"""Prepare a verified, reproducible artwork upload archive. Never publishes or pins.

The on-chain renderer produces dynamic metadata; the included JSON files are
artwork-state references, not immutable per-token LP/reward snapshots.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "design/nft-metadata/palette-system-v1/packed-catalog.json"
RARITIES = ("commun", "rare", "legendary")
STAGES = ("dormant", "activated", "enhanced", "singularity")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _json(data: bytes) -> object:
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate artwork JSON field")
            result[key] = value
        return result

    def reject(value):
        raise ValueError("Non-finite artwork JSON number")

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            reject(value)
        return number

    return json.loads(data, object_pairs_hook=unique, parse_constant=reject, parse_float=finite)


def expected_ids(catalog: dict) -> list[str]:
    return sorted("-".join(parts) for parts in itertools.product(
        [p["id"] for p in catalog["paletteOrder"]], catalog["patternOrder"], RARITIES, STAGES))


def source_file(source: Path, relative: str) -> bytes:
    path = source / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(source):
        raise ValueError(f"Missing or unsafe source file: {relative}")
    return path.read_bytes()


class _StaticSVGTree(ET.TreeBuilder):
    """Reject resource-changing XML constructs before ElementTree drops them."""
    def pi(self, target: str, text: str | None) -> None:
        raise ValueError("SVG processing instructions are not static artwork")

    def doctype(self, name: str, public_id: str | None, system_id: str | None) -> None:
        # Parser-level rejection also covers UTF-16 DTDs that an ASCII byte
        # screen cannot see. A normal XML declaration is not a PI or a DTD.
        raise ValueError("SVG document types and entities are not allowed")


def validate_svg(data: bytes) -> None:
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("SVG must not contain XML declarations with entities")
    root = ET.fromstring(data, parser=ET.XMLParser(target=_StaticSVGTree()))
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("Artwork is not SVG")
    for element in root.iter():
        if element.tag.split("}")[-1].lower() in {"script", "foreignobject", "style", "animate", "animatetransform", "animatemotion", "animatecolor", "set", "discard", "a"}:
            raise ValueError("Active SVG content")
        for name, value in element.attrib.items():
            if name == "{http://www.w3.org/XML/1998/namespace}base":
                raise ValueError("SVG base URIs may redirect local resources")
            name = name.split("}")[-1].lower()
            # The approved renderer has no inline styles or CSS escapes. Reject
            # these channels instead of treating a URL regex as a CSS parser.
            if name == "style" or "\\" in value:
                raise ValueError("SVG styles and escaped resource syntax are not approved")
            urls = re.findall(r"url\((.*?)\)", value, re.IGNORECASE)
            if name.startswith("on") or any(not re.fullmatch(r"#[A-Za-z0-9_-]+", url) for url in urls):
                raise ValueError("Active/external SVG attribute")
            if name == "href" and not value.startswith(("#", "data:image/webp;base64,")):
                raise ValueError("External SVG resource")


def prepare(source: Path, output: Path, catalog_path: Path = CATALOG) -> dict:
    source = source.resolve(strict=True)
    output = output.resolve()
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("Output and source directories must be separate")
    if output.exists():
        raise ValueError("Output must be a new directory; existing bundles are never overwritten")
    catalog_raw = catalog_path.read_bytes()
    ids = expected_ids(_json(catalog_raw))
    manifest_raw = source_file(source, "manifest.json")
    manifest = _json(manifest_raw)
    variants = {item["id"]: item for item in manifest["variants"]}
    if len(variants) != len(manifest["variants"]) or set(variants) != set(ids):
        raise ValueError("Artwork manifest does not match the complete contract catalogue")
    # Validate all files before creating any output; keep no entire artwork set in RAM.
    files = {}
    for art_id in ids:
        svg_name = art_id + ".svg"
        svg = source_file(source, svg_name)
        validate_svg(svg)
        if digest(svg) != variants[art_id]["image_sha256"]:
            raise ValueError(f"Artwork hash mismatch: {art_id}")
        metadata_name = f"metadata/{art_id}.json"
        metadata = source_file(source, metadata_name)
        if _json(metadata)["image"] != f"../{svg_name}":
            raise ValueError(f"Incorrect reference metadata image: {art_id}")
        files[svg_name] = {"sha256": digest(svg), "bytes": len(svg)}
        files[metadata_name] = {"sha256": digest(metadata), "bytes": len(metadata)}
    files["manifest.json"] = {"sha256": digest(manifest_raw), "bytes": len(manifest_raw)}
    payload = encoded({"schema": 1, "artwork_states": len(ids),
        "catalog_sha256": digest(catalog_raw), "files": files,
        "metadata": "Reference artwork states only; tokenURI metadata is generated dynamically on chain."})
    output.mkdir(parents=True)
    archive_path = output / "popl-artwork-ipfs.tar.gz"
    with archive_path.open("xb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for name in sorted(files):
                    data = source_file(source, name)
                    if digest(data) != files[name]["sha256"]:
                        raise ValueError(f"Source changed during packaging: {name}")
                    entry = tarfile.TarInfo("content/" + name)
                    entry.size = len(data); entry.mode = 0o644; entry.mtime = 0
                    archive.addfile(entry, io.BytesIO(data))
                for name, data in (("packed-catalog.json", catalog_raw), ("SHA256-manifest.json", payload)):
                    entry = tarfile.TarInfo("content/" + name)
                    entry.size = len(data); entry.mode = 0o644; entry.mtime = 0
                    archive.addfile(entry, io.BytesIO(data))
    # Independently stream the produced archive back, checking every path and byte hash.
    expected = {"content/" + name: value["sha256"] for name, value in files.items()}
    expected["content/packed-catalog.json"] = digest(catalog_raw)
    expected["content/SHA256-manifest.json"] = digest(payload)
    seen = set()
    with tarfile.open(archive_path, "r|gz") as archive:
        for entry in archive:
            if not entry.isfile() or entry.name in seen or entry.name not in expected:
                raise ValueError("Unexpected archive entry")
            stream = archive.extractfile(entry)
            if stream is None or digest(stream.read()) != expected[entry.name]:
                raise ValueError(f"Archive integrity failure: {entry.name}")
            seen.add(entry.name)
    if seen != set(expected):
        raise ValueError("Incomplete archive")
    with archive_path.open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    receipt = {"schema": 1, "archive": archive_path.name, "archive_sha256": archive_hash,
        "artwork_states": len(ids), "archive_files_verified": len(seen),
        "source_manifest_sha256": digest(manifest_raw), "catalog_sha256": digest(catalog_raw),
        "uploaded": False, "pinned": False, "root_cid": None,
        "next": "Choose a pinning provider, import the content directory with explicit UnixFS settings, verify its CID and every renderer image path before configuring the immutable NFT base URI."}
    (output / "bundle.json").write_bytes(encoded(receipt))
    (output / "SHA256-manifest.json").write_bytes(payload)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Verified website assets/nfts directory")
    parser.add_argument("--output", required=True, type=Path, help="New output directory outside the source")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))


if __name__ == "__main__":
    main()
