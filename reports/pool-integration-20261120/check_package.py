"""Offline publication checks; no EVM, provider, signer or production writes."""
from pathlib import Path
import ast
import collections
import hashlib
import json
import re
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def main():
    baseline = load(HERE / "BASELINE.json")
    original = Path(baseline["original_docs_external"])
    for name, row in baseline["original_docs"].items():
        raw = (original / name).read_bytes()
        assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]
    for name, expected in baseline["protected_unrelated_dirty_sha256"].items():
        assert digest((ROOT / name).read_bytes()) == expected, name

    archives = {}
    expected = {
        "swap": (62, "1bc0e50a93d6734b48351dc98c27c630b4266de738bba4653896c7aeae278b78"),
        "entry": (220, "e56b8d78aba465c673aa0379e6a4214860189e935c133dafc7da8c46aa99d2ff"),
    }
    for part, (count, pinned) in expected.items():
        folder = HERE / part
        manifest = load(folder / "EVIDENCE_MANIFEST.json")
        raw = (folder / "evidence.zip").read_bytes()
        assert len(raw) == manifest["bytes"] and digest(raw) == manifest["sha256"] == pinned
        with zipfile.ZipFile(folder / "evidence.zip") as archive:
            names = archive.namelist()
            assert len(names) == len(set(names)) == count
            assert set(names) == set(manifest["members"])
            for name, row in manifest["members"].items():
                member = archive.read(name)
                assert len(member) == row["bytes"] and digest(member) == row["sha256"], name
        assert load(folder / "VERIFICATION.json")["passed"] is True
        archives[part] = {"sha256": pinned, "bytes": len(raw), "members": count}

    current = load(ROOT / "docs/project-todo.json")
    previous = load(original / "docs/project-todo.json")
    tasks = [task for area in current["areas"] for task in area["tasks"]]
    older = [task for area in previous["areas"] for task in area["tasks"]]
    assert [task["id"] for task in tasks] == baseline["stable_task_ids"]
    assert {t["id"]: t["status"] for t in tasks} == {t["id"]: t["status"] for t in older}

    parsed = []
    for path in sorted(HERE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        ast.parse(path.read_bytes(), filename=str(path))
        parsed.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    docs = list(HERE.rglob("*.md"))
    docs += [ROOT / p for p in baseline["original_docs"] if p.endswith(".md")]
    links = set()
    for path in docs:
        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            value = match.group(1).strip("<>")
            if "://" in value or value.startswith(("#", "mailto:")):
                continue
            if not path.is_relative_to(HERE) and "pool-integration-20261120" not in value:
                continue
            target = (path.parent / value.split("#", 1)[0]).resolve()
            assert target.is_file(), (str(path), value)
            links.add((str(path.relative_to(ROOT)), value))

    result = {
        "schema": 1,
        "baseline": baseline["baseline"],
        "kind": "offline_source_evidence_document_publication_check_not_behavioral_rerun",
        "archives": archives,
        "original_documents_verified": len(baseline["original_docs"]),
        "protected_unrelated_dirty_sha256": baseline["protected_unrelated_dirty_sha256"],
        "stable_task_ids": len(tasks),
        "task_counts": dict(collections.Counter(t["status"] for t in tasks)),
        "task_status_changes": 0,
        "report_python_syntax_checked": parsed,
        "new_local_document_links": len(links),
        "new_direct_swap_behaviors": 2,
        "new_entry_contribution_behaviors": 4,
        "negative_direct_swap_scope": "simulation_only_not_mined_failure",
        "production_source_changes": False,
        "unchanged_tests_rerun": False,
        "public_transactions_or_production_seal": False,
        "existing_environment_changes": False,
        "production_approved": False,
    }
    with (HERE / "FINAL_CHECKS.json").open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps({"passed": True, "archives": len(archives), "members": sum(x["members"] for x in archives.values()), "task_ids": len(tasks), "links": len(links)}))


if __name__ == "__main__":
    main()
