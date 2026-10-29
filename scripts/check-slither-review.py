"""Fail closed on analyzer errors, source drift, or findings without a recorded review.

This checks review coverage, not exploit absence or independent audit approval.
"""
import argparse
from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.state import read_json


def source_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def normalized_description(finding):
    description = finding["description"].replace("\\", "/").replace("\r\n", "\n")
    description = re.sub(r"(?:[A-Za-z]:)?/[^\n()]*?/(?=src/)", "", description)
    if finding["check"].startswith("reentrancy-"):
        # Slither emits these nested callee leaves from a Python set. Their
        # presentation order varies across processes/platforms, not call order.
        # Preserve parent groups, expressions, locations, duplicates and every
        # other line; do not reorder a node that itself has deeper children.
        lines = description.splitlines(keepends=True)
        cursor = 0
        external_calls = False
        while cursor < len(lines):
            line = lines[cursor]
            if line.startswith("\t") and not line.startswith(("\t\t", "\t- ")):
                external_calls = line.strip() == "External calls:"
            if not external_calls or not line.startswith("\t\t- "):
                cursor += 1
                continue
            start = cursor
            while cursor < len(lines) and lines[cursor].startswith("\t\t- "):
                cursor += 1
            if cursor == len(lines) or not lines[cursor].startswith("\t\t\t"):
                lines[start:cursor] = sorted(lines[start:cursor])
        if finding["check"] == "reentrancy-events":
            # Slither sorts a set of event findings by event name/node only.
            # Identical event roots reached through different call sites tie;
            # their presentation order is process-dependent. Sort ONLY adjacent
            # byte-identical event roots, keeping each descendant bundle intact.
            # Distinct roots, child edges, duplicates and other sections retain
            # their exact content/order; this is not execution-order inference.
            cursor = 0
            while cursor < len(lines):
                if lines[cursor].rstrip("\n") != "\tEvent emitted after the call(s):":
                    cursor += 1
                    continue
                cursor += 1
                while cursor < len(lines) and lines[cursor].startswith("\t- "):
                    start = cursor
                    event_root = lines[cursor]
                    bundles = []
                    while cursor < len(lines) and lines[cursor] == event_root:
                        block_start = cursor
                        cursor += 1
                        while cursor < len(lines) and lines[cursor].startswith("\t\t"):
                            cursor += 1
                        bundles.append(lines[block_start:cursor])
                    if len(bundles) > 1:
                        lines[start:cursor] = [line for bundle in sorted(bundles) for line in bundle]
        description = "".join(lines)
    return description


def fingerprint(finding):
    payload = [finding[key] for key in ("check", "impact", "confidence")] + [normalized_description(finding)]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=True).encode()).hexdigest()


WRITE_BUNDLES = "reentrancy-no-eth-write-bundles-v1"
LOCATION = r" \(src/[^()\n]+#\d+(?:-\d+)?\)"


def write_bundle_atoms(finding):
    """Parse only the reviewed Slither no-eth grouping shape, without dropping text.

    Slither keys these records by a set-derived call collection, so one identical
    call context can be split across records on a second run of the same build.
    Each atom retains its write root, ordered descendant lines, and entire
    cross-function paragraph. The caller compares a multiset, not a set. This
    narrow parser deliberately rejects direct writes/unknown future syntax;
    they remain eligible for the ordinary exact-fingerprint comparison only.
    """
    if finding["check"] != "reentrancy-no-eth":
        raise ValueError("Write-bundle comparison requires reentrancy-no-eth")
    lines = normalized_description(finding).splitlines(keepends=True)
    marker = "\tState variables written after the call(s):\n"
    if (len(lines) < 5 or not re.fullmatch(r"Reentrancy in .+" + LOCATION + r":\n", lines[0])
            or lines[1] != "\tExternal calls:\n" or lines.count(marker) != 1):
        raise ValueError("Unsupported write-bundle finding header/sections")
    boundary = lines.index(marker)
    roots = 0
    for line in lines[2:boundary]:
        if re.fullmatch(r"\t- .+" + LOCATION + r"\n", line):
            roots += 1
        elif not roots or not re.fullmatch(r"\t{2,}- .+" + LOCATION + r"\n", line):
            raise ValueError("Unsupported write-bundle call tree")
    if not roots:
        raise ValueError("Write-bundle call context is empty")
    context = tuple(finding[key] for key in ("check", "impact", "confidence")) + ("".join(lines[:boundary + 1]),)
    atoms = Counter()
    cursor = boundary + 1
    while cursor < len(lines):
        start = cursor
        if not re.fullmatch(r"\t- .+" + LOCATION + r"\n", lines[cursor]):
            raise ValueError("Unsupported state-write root")
        cursor += 1
        children = cursor
        while cursor < len(lines) and re.fullmatch(r"\t{2,}- .+" + LOCATION + r"\n", lines[cursor]):
            cursor += 1
        if cursor == children:
            raise ValueError("Write-bundle root has no descendants")
        if cursor == len(lines) or not re.fullmatch(
                r"\t[^\n]+" + LOCATION + r" can be used in cross function reentrancies:\n", lines[cursor]):
            raise ValueError("Write-bundle cross-function paragraph is missing")
        cursor += 1
        cross_functions = cursor
        while cursor < len(lines) and re.fullmatch(r"\t- .+" + LOCATION + r"\n", lines[cursor]):
            # A root with descendants begins the next atom. Cross-function
            # entries are qualified function/getter names, never call-tree roots.
            if cursor + 1 < len(lines) and lines[cursor + 1].startswith("\t\t"):
                break
            if not re.fullmatch(r"\t- [A-Za-z_$][\w$]*\.[A-Za-z_$][\w$]*(?:\([^\n]*\))?" + LOCATION + r"\n", lines[cursor]):
                raise ValueError("Unsupported cross-function entry")
            cursor += 1
        if cursor == cross_functions:
            raise ValueError("Write-bundle cross-function list is empty")
        atoms["".join(lines[start:cursor])] += 1
    if not atoms:
        raise ValueError("Write-bundle state section is empty")
    return context, atoms


def check(report, review, root=ROOT):
    errors = []
    if report.get("success") is not True or report.get("error"):
        return ["Slither did not complete successfully"]
    detectors = report.get("results", {}).get("detectors")
    if not isinstance(detectors, list):
        return ["Slither detector output is missing"]
    expected_paths = {p.relative_to(root).as_posix() for p in (root / "src").rglob("*.sol")}
    expected_paths.update({"foundry.toml", "package-lock.json", "slither.config.json"})
    sources = review.get("source_sha256_lf", {})
    if set(sources) != expected_paths:
        errors.append("Reviewed source/toolchain inventory changed")
    for name, digest in sources.items():
        if name not in expected_paths:
            errors.append("Reviewed inventory contains an unexpected source name")
            continue
        path = root / name
        if not path.is_file() or source_hash(path) != digest:
            errors.append(f"Reviewed content changed: {name}")
    entries = review.get("findings", [])
    reviewed = {item.get("fingerprint"): item for item in entries}
    if len(reviewed) != len(entries):
        errors.append("Duplicate review fingerprints")
    current = {fingerprint(item) for item in detectors}
    if len(current) != len(detectors):
        errors.append("Duplicate analyzer fingerprints")
    unreviewed = current - reviewed.keys()
    stale = reviewed.keys() - current
    matched = current & reviewed.keys()
    groups = {}
    for key, item in reviewed.items():
        # Descriptions are optional for legacy exact reviews. When recorded,
        # they must reconstruct the reviewed fingerprint, even for exact hits.
        if "description" in item:
            try:
                if fingerprint(item) != key:
                    raise ValueError("description/fingerprint mismatch")
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"Invalid reviewed description: {key}: {exc}")
                continue
        comparison = item.get("comparison")
        if comparison is None:
            continue
        if comparison != WRITE_BUNDLES:
            errors.append(f"Unsupported review comparison: {key}")
            continue
        try:
            context, atoms = write_bundle_atoms(item)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"Invalid reviewed write bundles: {key}: {exc}")
            continue
        group = groups.setdefault(context, {"keys": set(), "atoms": Counter()})
        group["keys"].add(key)
        group["atoms"].update(atoms)
    for context, group in groups.items():
        incoming_keys = set()
        incoming_atoms = Counter()
        for finding in detectors:
            try:
                finding_context, atoms = write_bundle_atoms(finding)
            except (KeyError, TypeError, ValueError):
                continue  # Unsupported shapes still require an exact review.
            if finding_context == context:
                incoming_keys.add(fingerprint(finding))
                incoming_atoms.update(atoms)
        if incoming_keys & (reviewed.keys() - group["keys"]):
            errors.append("Write-bundle context mixes exact and regrouped reviews")
        elif incoming_atoms != group["atoms"]:
            errors.append("Reviewed write-bundle multiplicity/content changed")
        else:
            unreviewed.difference_update(incoming_keys)
            stale.difference_update(group["keys"])
            matched.update(group["keys"])
    for key in sorted(unreviewed):
        errors.append(f"Unreviewed finding: {key}")
    for key in sorted(stale):
        errors.append(f"Stale review entry: {key}")
    for key in matched:
        item = reviewed[key]
        if item.get("disposition") not in {"false_positive", "accepted_risk", "informational"}:
            errors.append(f"Unresolved finding: {key}")
        if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            errors.append(f"Missing rationale: {key}")
    if review.get("independent_audit") is not False:
        errors.append("Review must identify its non-independent scope")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--review", type=Path, default=ROOT / "reports/production/slither-review.json")
    args = parser.parse_args()
    try:
        report = read_json(args.report,encoding="utf-8")
        review = read_json(args.review,encoding="utf-8")
        if not isinstance(report,dict) or not isinstance(review,dict):
            raise ValueError("Analyzer and review inputs must be objects")
        entries=review.get("findings",[])
        if not isinstance(entries,list) or any(not isinstance(item,dict) or
                not isinstance(item.get("fingerprint"),str) or
                not re.fullmatch(r"[0-9a-f]{64}",item["fingerprint"]) for item in entries):
            raise ValueError("Invalid reviewed finding identity")
        errors = check(report, review)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        errors = ["Invalid analyzer/review input; inspect the reviewed files and source bindings privately"]
    print(json.dumps({"review_coverage_pass": not errors, "independent_audit": False, "errors": errors}))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
