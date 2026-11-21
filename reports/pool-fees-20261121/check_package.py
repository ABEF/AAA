"""Offline evidence/source/doc publication checks, never an EVM or suite rerun."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ast
import collections
import hashlib
import json
import re
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHIVE = "13aa22d3dd99108d06d58a6aa96505a08b6a16c74e633e90b142bde826edb22b"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def source_check(arguments):
    command = [sys.executable, *arguments]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60, check=False)
    assert result.returncode == 0, (arguments, result.stderr.decode(errors="replace"))
    return {"command": command, "exit_code": result.returncode,
            "stdout": result.stdout.decode("utf-8"), "stderr": result.stderr.decode("utf-8"),
            "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr)}


def main():
    output = HERE / "FINAL_CHECKS.json"
    assert not output.exists(), "Retain earlier checks; choose a new reviewed stage"
    baseline = load(HERE / "BASELINE.json")
    original = Path(baseline["original_docs_external"])
    for name, pin in baseline["original_docs"].items():
        raw = (original / name).read_bytes()
        assert len(raw) == pin["bytes"] and sha(raw) == pin["sha256"], name
    for name, expected in baseline["protected_unrelated_dirty_sha256"].items():
        assert sha((ROOT / name).read_bytes()) == expected, name

    folder = HERE / "run"
    manifest = load(folder / "EVIDENCE_MANIFEST.json")
    raw = (folder / "evidence.zip").read_bytes()
    assert sha(raw) == manifest["sha256"] == ARCHIVE
    assert len(raw) == manifest["bytes"] == 10411086
    with zipfile.ZipFile(folder / "evidence.zip") as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == 114
        assert set(names) == set(manifest["members"])
        for name, pin in manifest["members"].items():
            member = archive.read(name)
            assert len(member) == pin["bytes"] and sha(member) == pin["sha256"], name
        for stage in ("attempt1", "attempt2"):
            cleanup = json.loads(archive.read(stage + "/cleanup.json"))
            assert cleanup["owned_node_stopped"] is True and cleanup["pending"] is None
            assert cleanup.get("existing_nodes_contacted") is False

    for name in ("BASELINE_EAGER.json", "EXTENSION_REVIEW.json", "ARCHIVE_REVIEW.json"):
        assert load(HERE / "review" / name)["passed"] is True
    assert load(folder / "VERIFICATION.json")["passed"] is True
    for metadata, script, result, key in (("EXECUTION.json", "verify_baseline_eager.py", "BASELINE_EAGER.json", "output_sha256"),
                                         ("EXTENSION_EXECUTION.json", "verify_extension_saved.py", "EXTENSION_REVIEW.json", "result_sha256")):
        record = load(HERE / "review" / metadata)
        assert sha((HERE / "review" / script).read_bytes()) == record["source_sha256"]
        assert sha((HERE / "review" / result).read_bytes()) == record[key]
    identities = load(HERE / "review/ARCHIVE_REVIEW.json")["current_sources_match_successful_stage"]
    for name, expected in identities.items():
        assert sha((folder / name).read_bytes()) == expected
    reuse = load(folder / "FINAL_SOURCE_REUSE.json")
    assert reuse["archive_sha256"] == ARCHIVE and reuse["Model_AST_equal"] is True
    assert sha((folder / "run_fees.py").read_bytes()) == reuse["final_executed_driver_sha256"]
    assert sha((folder / "eager_oracle.py").read_bytes()) == reuse["eager_oracle_sha256"]
    control = load(folder / "ORACLE_CONTROL.json")
    assert control["passed"] is True and control["source_sha256"] == reuse["eager_oracle_sha256"]

    tasks = [task for area in load(ROOT / "docs/project-todo.json")["areas"] for task in area["tasks"]]
    old = [task for area in load(original / "docs/project-todo.json")["areas"] for task in area["tasks"]]
    assert [task["id"] for task in tasks] == baseline["stable_task_ids"]
    assert [(t["id"], t["status"]) for t in tasks] == [(t["id"], t["status"]) for t in old]

    parsed = []
    for path in sorted(HERE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        ast.parse(path.read_bytes(), filename=str(path))
        parsed.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    links = set()
    documents = list(HERE.rglob("*.md"))
    documents += [ROOT / name for name in baseline["original_docs"] if name.endswith(".md")]
    for path in documents:
        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = match.group(1).strip("<>")
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            if not path.is_relative_to(HERE) and "pool-fees-20261121" not in target:
                continue
            assert (path.parent / target.split("#", 1)[0]).resolve().is_file(), (str(path), target)
            links.add((str(path.relative_to(ROOT)), target))

    commands = [["scripts/build-workload-inventory.py", "--check",
                 "reports/readiness-advance-20261120/FUNCTION_INVENTORY.json"],
                ["scripts/sync-project-todo.py", "--check"]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        checks = list(pool.map(source_check, commands))
    inventory = json.loads(checks[0]["stdout"])
    assert inventory["output_sha256"] == "d0a2de1c507c2540a61f438e9d6aba160919966c52aabaf455ca9f70d3f46e97"
    result = {"schema": 1, "kind": "offline_publication_checks_no_behavioral_rerun",
              "baseline": baseline["baseline"], "archive_sha256": ARCHIVE,
              "archive_members_verified": 114, "archive_bytes": len(raw),
              "original_docs_verified": len(baseline["original_docs"]),
              "protected_unrelated_dirty_sha256": baseline["protected_unrelated_dirty_sha256"],
              "stable_task_ids": len(tasks), "task_status_changes": 0,
              "task_counts": dict(collections.Counter(t["status"] for t in tasks)),
              "report_python_syntax_checked": parsed, "new_local_links_checked": len(links),
              "source_checks": checks, "source_inventory_only": inventory,
              "new_successful_local_transactions": 17, "saved_wire_rows": 1333,
              "saved_eager_checkpoints": 25, "old_behavioral_suites_rerun": False,
              "production_source_changes": False, "existing_environment_changes": False,
              "production_approved": False}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"passed": True, "archive_members": 114, "stable_tasks": len(tasks),
                      "links": len(links), "report_scripts_syntax": len(parsed)}))


if __name__ == "__main__":
    main()
