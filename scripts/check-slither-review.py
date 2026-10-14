"""Fail closed on analyzer errors, source drift, or findings without a recorded review.

This checks review coverage, not exploit absence or independent audit approval.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def fingerprint(finding):
    description = finding["description"].replace("\\", "/").replace("\r\n", "\n")
    description = re.sub(r"(?:[A-Za-z]:)?/[^\n()]*?/(?=src/)", "", description)
    payload = [finding[key] for key in ("check", "impact", "confidence")] + [description]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=True).encode()).hexdigest()


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
        path = root / name
        if name not in expected_paths or not path.is_file() or source_hash(path) != digest:
            errors.append(f"Reviewed content changed: {name}")
    entries = review.get("findings", [])
    reviewed = {item.get("fingerprint"): item for item in entries}
    if len(reviewed) != len(entries):
        errors.append("Duplicate review fingerprints")
    current = {fingerprint(item) for item in detectors}
    if len(current) != len(detectors):
        errors.append("Duplicate analyzer fingerprints")
    for key in sorted(current - reviewed.keys()):
        errors.append(f"Unreviewed finding: {key}")
    for key in sorted(reviewed.keys() - current):
        errors.append(f"Stale review entry: {key}")
    for key in current & reviewed.keys():
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
        report = json.loads(args.report.read_text(encoding="utf-8"))
        review = json.loads(args.review.read_text(encoding="utf-8"))
        errors = check(report, review)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors = [f"Invalid analyzer/review input: {exc}"]
    print(json.dumps({"review_coverage_pass": not errors, "independent_audit": False, "errors": errors}))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
