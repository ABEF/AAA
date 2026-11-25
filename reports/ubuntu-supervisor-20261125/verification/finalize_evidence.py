"""Verify new public evidence and write its manifest; no runtime or network work."""
from pathlib import Path
import ast
import hashlib
import json
import re

REPORT = Path(__file__).resolve().parents[1]
ROOT = REPORT.parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    for tag, count in (("c804", 2932), ("c806", 2357)):
        folder = REPORT / "evidence" / tag
        result = json.loads((folder / "model-RESULT.json").read_bytes())
        assert result["success"] is True and result["shared_RPC_requests"] == count
        assert result["raw_attempts"] == result["raw_forwarded"] == 1
        assert result["new_seals"] == result["public_transactions"] == 0
        proof = json.loads((REPORT / "evidence" / ("INDEPENDENT_" + tag.upper() + ".json")).read_bytes())
        assert proof["status"] == "passed"
        assert all(x["status"] == "passed" for x in proof["checks"].values())
        raw = (folder / "FINAL_JOURNAL.raw").read_bytes()
        assert sha(raw) == (folder / "FINAL_JOURNAL.sha256").read_text().strip()
        assert json.loads(raw)["pending"] is None
        stop = json.loads((folder / "control" / "STOP.json").read_bytes())
        assert stop["all_owned_units_stopped"] is True
        final = json.loads((folder / "control" / "FINAL-PUBLIC_RESULT.json").read_bytes())
        assert final["all_fixed_owned_units_stopped"] is True
        assert len(final["units_after"]) == 9
        for unit in final["units_after"].values():
            assert int(unit["properties"]["MainPID"]) == 0 and not unit["cgroup"]["pids"]
        for capture in (folder / "capture").glob("EXECUTION-*.json"):
            execution = json.loads(capture.read_bytes())
            name = capture.name.removeprefix("EXECUTION-").removesuffix(".json")
            assert execution["exit_code"] == 0
            assert sha((folder / name).read_bytes()) == execution["artifact_sha256"]
    host = json.loads((REPORT / "evidence" / "HOST_PRESERVATION.json").read_bytes())
    assert host["success"] is True and host["non_ambient_difference_count"] == 0
    assert host["existing_units_checked"] == 5 and host["ignored_observer_invocation_count"] == 1
    protected = {
        "reports/source-checks.json": "049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4",
        "scripts/run-fork-checks.py": "875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b",
        "tests_python/test_fork_runner.py": "6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9",
        "tests_python/test_frontend_history.py": "361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb",
    }
    for path, digest in protected.items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    checked_links = 0
    required_paths = []
    for path in REPORT.rglob("*"):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if path.suffix == ".py":
            ast.parse(raw, filename=str(path))
        if path.suffix == ".json":
            json.loads(raw)
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", raw.decode()):
                if not target.startswith(("http:", "https:", "#")):
                    required_paths.append(path.parent / target.split("#", 1)[0])
                    checked_links += 1
        assert re.search(rb"(?m)^\s*-----BEGIN (?:OPENSSH )?PRIVATE KEY-----\s*$", raw) is None
    summary = {
        "schema": 1, "status": "passed", "public_capture_hashes_verified": True,
        "both_independent_reviews_passed": True, "all_nine_new_units_stopped": True,
        "five_original_service_states_preserved": True, "protected_dirty_files_unchanged": True,
        "relative_report_links_verified": checked_links, "old_test_bodies_run": 0,
        "runtime_actions": 0, "network_calls": 0, "production_approved": False,
        "private_original_input_archives_required_for_full_source_replay": True,
    }
    (REPORT / "verification" / "PUBLIC_VERIFICATION.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf8")
    paths = sorted(p for p in REPORT.rglob("*") if p.is_file()
                   and p.name != "EVIDENCE_MANIFEST.json" and "__pycache__" not in p.parts)
    manifest = {"schema": 1, "report": REPORT.name, "members": {
        str(p.relative_to(REPORT)).replace("\\", "/"): {
            "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in paths}}
    (REPORT / "verification" / "EVIDENCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf8")
    assert all(path.is_file() for path in required_paths), required_paths
    print(json.dumps({**summary, "manifest_members": len(paths)}, sort_keys=True))


if __name__ == "__main__":
    main()
