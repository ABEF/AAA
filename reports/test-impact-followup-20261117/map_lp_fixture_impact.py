"""Offline lexical impact inventory; this does not execute or qualify tests."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEEDS = {
    "test/VaultAccounting.t.sol",
    "test/MigrationBudgetAdversarial.t.sol",
    "test/PortfolioAccounting.t.sol",
    "test/ReservationCapacity.t.sol",
}


def mask(source: str) -> str:
    # Preserve byte positions/newlines while removing non-code braces/keywords.
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m: "".join("\n" if c == "\n" else " " for c in m[0]), source)


def closing(code: str, opening: int) -> int:
    depth = 1
    for i in range(opening + 1, len(code)):
        depth += (code[i] == "{") - (code[i] == "}")
        if depth == 0:
            return i
    raise ValueError("unclosed body")


def main() -> None:
    paths = sorted((ROOT / "test").rglob("*.sol"))
    sources = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8-sig") for p in paths}
    imports: dict[str, list[str]] = {}
    for rel, source in sources.items():
        imported = re.findall(r'^\s*import\b[^;]*?["\']([^"\']+)["\']\s*;', source, re.MULTILINE)
        imports[rel] = sorted({(ROOT / rel).parent.joinpath(p).resolve().relative_to(ROOT).as_posix()
                              for p in imported if p.startswith(".") and (ROOT / rel).parent.joinpath(p).resolve().is_relative_to(ROOT)})
    memo: dict[str, set[str]] = {}

    def closure(rel: str, visiting: frozenset[str] = frozenset()) -> set[str]:
        if rel in memo:
            return memo[rel]
        if rel in visiting:
            return {rel}
        result = {rel}
        for dep in imports.get(rel, []):
            result |= closure(dep, visiting | {rel})
        memo[rel] = result
        return result

    rows = []
    contracts = []
    for rel, source in sources.items():
        seed_hits = sorted(SEEDS & closure(rel))
        if not seed_hits:
            continue
        code = mask(source)
        for cm in re.finditer(r'\b(?:abstract\s+)?contract\s+(\w+)\s*([^{};]*)\{', code):
            end = closing(code, cm.end() - 1)
            declaration = cm[2].strip()
            parents = re.findall(r'\b(\w+)\b(?:\([^)]*\))?', declaration.removeprefix("is").strip()) if declaration.startswith("is") else []
            contract = {"file": rel, "contract": cm[1], "line": code.count("\n", 0, cm.start()) + 1,
                        "parents": parents, "impact_seed_imports": seed_hits, "local_test_methods": []}
            for fm in re.finditer(r'\bfunction\s+((?:test|invariant)\w*)\s*\(([^)]*)\)[^{;]*\{', code[cm.end():end]):
                start = cm.end() + fm.start()
                opening = cm.end() + fm.end() - 1
                finish = closing(code, opening)
                body = source[opening:finish + 1]
                signature = fm[1] + "(" + ",".join(re.sub(r'\s+(?:memory|calldata|storage)\b', "", a.strip()).split()[0] for a in fm[2].split(",") if a.strip()) + ")"
                ident = f"{rel}:{cm[1]}.{signature}"
                row = {"id": ident, "file": rel, "contract": cm[1], "method": fm[1], "signature": signature,
                       "line": code.count("\n", 0, start) + 1, "end_line": code.count("\n", 0, finish) + 1,
                       "impact_seed_imports": seed_hits, "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                       "fuzz_or_invariant": bool(fm[2].strip()) or fm[1].startswith("invariant"),
                       "generic_revert_expectations": len(re.findall(r'\bexpectRevert\s*\(\s*\)', mask(body))),
                       "assertion_calls": len(re.findall(r'\bassert\w*\s*\(', mask(body)))}
                rows.append(row)
                contract["local_test_methods"].append(ident)
            contracts.append(contract)
    by_name = {c["contract"]: c for c in contracts}

    def inherited_methods(c: dict, trail: frozenset[str] = frozenset()) -> set[str]:
        if c["contract"] in trail:
            return set()
        result = set()
        for parent in c["parents"]:
            if parent in by_name:
                p = by_name[parent]
                result |= set(p["local_test_methods"]) | inherited_methods(p, trail | {c["contract"]})
        return result

    for c in contracts:
        c["inherited_test_methods"] = sorted(inherited_methods(c))
        c["effective_method_instances"] = sorted(
            {f'{c["file"]}:{c["contract"]}.{i.rsplit(".", 1)[1]}'
             for i in c["local_test_methods"] + c["inherited_test_methods"]})
    affected_files = sorted({r["file"] for r in rows})
    output = {"schema": 1, "inventory_only_not_execution": True, "seed_files": sorted(SEEDS),
              "distinct_declared_methods": len(rows),
              "inherited_method_instances": sum(len(c["inherited_test_methods"]) for c in contracts),
              "effective_method_instances": sum(len(c["effective_method_instances"]) for c in contracts),
              "method_bodies_with_generic_reverts": sum(r["generic_revert_expectations"] > 0 for r in rows),
              "affected_method_files": affected_files, "contracts": contracts, "methods": rows,
              "test_file_sha256": {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in sorted(set(imports) & set().union(*(closure(f) for f in affected_files)))}}
    target = Path(__file__).with_name("LP_AFFECTED_METHODS.json")
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(affected_files), "contracts": len(contracts), "methods": len(rows), "generic_negative_methods": output["method_bodies_with_generic_reverts"]}))


if __name__ == "__main__":
    main()
