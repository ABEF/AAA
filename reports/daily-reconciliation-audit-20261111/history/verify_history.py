"""Read-only provenance checks for this frozen reconciliation, not security tests."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pointer(value, path):
    for item in path.strip("/").split("/"):
        item = item.replace("~1", "/").replace("~0", "~")
        value = value[int(item)] if isinstance(value, list) else value[item]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-directory", type=Path,
                        help="Optional directory holding the external bulk extracts.")
    args = parser.parse_args()
    manifest = load(HERE / "ARTIFACTS.json")
    for row in manifest["files"]:
        data = (HERE / row["path"]).read_bytes()
        assert len(data) == row["bytes"] and digest(data) == row["sha256"], row["path"]
    rows = load(HERE / "inherited-310-findings.json")["rows"]
    assert len(rows) == 310 and len({row["id"] for row in rows}) == 310
    for row in rows:
        raw = (ROOT / row["original_matrix"]).read_bytes()
        assert digest(raw) == row["original_matrix_sha256"], row["id"]
        assert pointer(json.loads(raw.decode("utf-8-sig")), row["json_pointer"]) == row["original_record"], row["id"]
        assert row["fresh_global_closure"] is False
    selected = [row for row in rows if row["current_reassessment_ids"]]
    assert len(selected) == 39
    inventory = load(HERE / "corpus-inventory.json")
    assert inventory["counts"]["main_narrative_ledger_blobs"] == 3948
    assert inventory["counts"]["prior_oids_not_seen_first_parent_raw_log"] == 0
    extracts = load(HERE / "EXTERNAL_EXTRACTION.json")["files"]
    assert {row["name"]: row["contexts"] for row in extracts} == {
        "open-contexts.json.gz": 13119, "structured-contexts.json.gz": 4669}
    if args.external_directory is not None:
        for row in extracts:
            raw = (args.external_directory / row["name"]).read_bytes()
            assert len(raw) == row["bytes"] and digest(raw) == row["sha256"], row["name"]
            assert len(json.loads(gzip.decompress(raw))["contexts"]) == row["contexts"], row["name"]
    baseline = load(HERE / "preservation-baseline.json")
    checked = 0
    for row in baseline["files"]:
        name = row["path"]
        if not name.startswith("reports/") or name in {"reports/README.md", "reports/source-checks.json"}:
            continue
        assert digest((ROOT / name).read_bytes()) == row["working_sha256"], name
        checked += 1
    assert checked == 5517
    cache = {}
    for row in load(HERE / "CURRENT_REASSESSMENTS.json")["rows"]:
        for evidence in row["current_evidence"]:
            key = (evidence["source_revision"], evidence["path"])
            if key not in cache:
                cache[key] = subprocess.check_output(["git", "show", ":".join(key)], cwd=ROOT)
            raw = cache[key]
            assert digest(raw) == evidence["git_blob_bytes_sha256"], key
            lines = raw.decode("utf-8-sig").splitlines()
            assert all(evidence["term"].lower() in lines[n - 1].lower() for n in evidence["matching_lines"]), key
    print(json.dumps({"artifact_integrity": True, "original_pointers": 310,
                      "individually_reassessed_original_rows": 39,
                      "original_rows_not_newly_source_reviewed": 271,
                      "unchanged_old_report_artifacts": checked,
                      "external_extracts_checked": args.external_directory is not None,
                      "new_contract_tests": 0, "security_or_production_approval": False}))


if __name__ == "__main__":
    main()
