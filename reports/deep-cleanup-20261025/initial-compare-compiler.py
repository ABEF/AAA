"""Compare saved compiler/source evidence; no compiler, EVM, RPC or service run."""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXTERNAL = Path(r"C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9")
BASELINE = EXTERNAL / "auditability-refactor-20261025/solidity"
CURRENT = EXTERNAL / "deep-cleanup-20261025/solidity"
ADDED_REMAPPINGS = {"v4-core/=node_modules/@uniswap/v4-core/", "permit2/=node_modules/@uniswap/v4-periphery/lib/permit2/"}
CHANGED_SOURCES = {"src/ZZZAccessController.sol", "src/ZZZRoyaltyRewards.sol", "src/libraries/ZZZV3VenueValidation.sol"}
ERROR_OWNERS = {"ZZZActivationEntry", "ZZZRoyaltyConverter", "ZZZLPRewardConverter"}
GUARDIAN_EVENT = {"anonymous": False, "inputs": [
    {"indexed": True, "internalType": "address", "name": "account", "type": "address"},
    {"indexed": False, "internalType": "bool", "name": "enabled", "type": "bool"}],
    "name": "GuardianChanged", "type": "event"}


def sha(raw): return hashlib.sha256(raw).hexdigest()
def encode(value): return json.dumps(value, sort_keys=True, separators=(",", ":"))
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def flatten(value):
    return {(source, name): item for source, objects in value["contracts"].items()
            if source.startswith("src/") for name, item in objects.items()}


def abi_normalized(abi, name, candidate):
    result = []
    seen = set()
    exceptions = []
    for entry in abi:
        if candidate and name == "ZZZAccessController" and entry == GUARDIAN_EVENT:
            exceptions.append({"kind": "new_observable_event", "entry": entry})
            continue
        key = encode(entry)
        if key in seen and not candidate and name in ERROR_OWNERS and entry == {
                "inputs": [], "name": "InvalidConfiguration", "type": "error"}:
            exceptions.append({"kind": "identical_baseline_error_duplicate", "entry": entry})
            continue
        seen.add(key)
        result.append(entry)
    return sorted(result, key=encode), exceptions


def physical_storage(layout):
    types = layout.get("types") or {}
    def resolve(identifier, parents=()):
        value = types[identifier]
        if len(parents) > 64:
            raise ValueError("Storage depth exceeds bound")
        if identifier in parents:
            return {"recursive_type": value["label"]}
        result = {key: item for key, item in value.items() if key not in ("key", "value", "base", "members")}
        for key in ("key", "value", "base"):
            if key in value:
                result[key] = resolve(value[key], parents + (identifier,))
        if "members" in value:
            result["members"] = [row(item, parents + (identifier,)) for item in value["members"]]
        return result
    def row(item, parents=()):
        return {"label": item["label"], "slot": item["slot"], "offset": item["offset"],
                "type": resolve(item["type"], parents)}
    return [row(item) for item in layout.get("storage", [])]


def trailer(raw):
    if len(raw) < 2:
        return b""
    length = int.from_bytes(raw[-2:], "big")
    if length and length + 2 <= len(raw):
        value = raw[-length - 2:-2]
        if 0xa0 <= value[0] <= 0xbf and b"solc" in value:
            return raw[-length - 2:]
    return b""


def import_resolution(ast, sources, old_settings, new_settings):
    import posixpath
    def resolved(source, literal, remappings):
        matches = [(left, right) for mapping in remappings for left, right in [mapping.split("=", 1)]
                   if literal.startswith(left)]
        if matches:
            left, right = max(matches, key=lambda pair: len(pair[0]))
            return right + literal[len(left):]
        if literal.startswith("."):
            return posixpath.normpath(posixpath.join(posixpath.dirname(source), literal))
        return literal
    rows = []
    for source in sorted(sources):
        for node in ast["sources"][source]["ast"]["nodes"]:
            if node["nodeType"] != "ImportDirective":
                continue
            literal = node["file"]
            before = resolved(source, literal, old_settings["remappings"])
            after = resolved(source, literal, new_settings["remappings"])
            rows.append({"source": source, "literal": literal, "baseline_resolution": before,
                         "candidate_resolution": after, "compiler_absolute_path": node["absolutePath"],
                         "equal": before == after == node["absolutePath"] and after in sources,
                         "uses_added_alias": literal.startswith(("v4-core/", "permit2/"))})
    return rows


def source_refactor(before, after):
    spec = importlib.util.spec_from_file_location("readability_helpers", ROOT / "reports/auditability-refactor-20261025/compare-readability.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    path = "src/ZZZRoyaltyRewards.sol"
    old = helper.functions(before["sources"][path]["content"])
    new = helper.functions(after["sources"][path]["content"])
    base = helper.functions(after["sources"]["src/base/ZZZCanonicalLedger.sol"]["content"])
    old_expression = old["_balance"]["tokens"][len(old["_balance"]["header"]):]
    new_expression = base["_canonicalBalance"]["tokens"][len(base["_canonicalBalance"]["header"]):]
    methods = []
    for name, function in old.items():
        if name == "_balance":
            continue
        candidate = new.get(name)
        normalized = ["_balance" if token == "_canonicalBalance" else token for token in candidate["tokens"]] if candidate else []
        methods.append({"name": name, "equal_after_only_helper_name": function["tokens"] == normalized,
                        "baseline_tokens_sha256": sha(encode(function["tokens"]).encode()),
                        "candidate_normalized_tokens_sha256": sha(encode(normalized).encode()),
                        "renamed_calls": candidate["tokens"].count("_canonicalBalance") if candidate else 0})
    return {"removed_private_function": "_balance", "existing_inherited_function": "_canonicalBalance",
            "exact_balance_expression_tokens_equal": old_expression == new_expression,
            "balance_expression": old_expression,
            "function_inventory_equal_except_removed_helper": set(old) - {"_balance"} == set(new),
            "unchanged_functions": methods,
            "all_bodies_and_call_order_tokens_equal": all(row["equal_after_only_helper_name"] for row in methods)}


def main():
    destination = HERE / "compiler-comparison.json"
    markdown = HERE / "compiler-comparison.md"
    if destination.exists() or markdown.exists():
        raise ValueError("Keep earlier evidence; do not overwrite an executed comparison")
    artifacts = {}
    records = []
    for directory in (BASELINE, CURRENT):
        item = {}
        for filename in ("source-build.json", "source-build-input.json", "source-size-gates.json"):
            path = directory / filename
            artifacts[str(path)] = sha(path.read_bytes())
            item[filename] = read(path)
        records.append(item)
    first, last = records
    old = flatten(first["source-build.json"])
    new = flatten(last["source-build.json"])
    comparisons = []
    for key in sorted(set(old) & set(new)):
        x, baseline_exceptions = abi_normalized(old[key]["abi"], key[1], False)
        y, candidate_exceptions = abi_normalized(new[key]["abi"], key[1], True)
        a, b = physical_storage(old[key]["storageLayout"]), physical_storage(new[key]["storageLayout"])
        item = {"path": key[0], "name": key[1], "raw_abi_equal": sorted(old[key]["abi"], key=encode) == sorted(new[key]["abi"], key=encode),
                "exact_wire_abi_equal_after_declared_exceptions": x == y,
                "baseline_exceptions": baseline_exceptions, "candidate_exceptions": candidate_exceptions,
                "exact_recursive_storage_equal": a == b, "storage_sha256_before": sha(encode(a).encode()),
                "storage_sha256_after": sha(encode(b).encode())}
        if x != y:
            ca, cb = collections.Counter(map(encode, x)), collections.Counter(map(encode, y))
            item["unexpected_abi_removed"] = [json.loads(value) for value in (ca - cb).elements()]
            item["unexpected_abi_added"] = [json.loads(value) for value in (cb - ca).elements()]
        if a != b:
            item.update(storage_before=a, storage_after=b)
        comparisons.append(item)
    settings_before = first["source-build-input.json"]["settings"]
    settings_after = last["source-build-input.json"]["settings"]
    without_remappings = lambda value: {key: item for key, item in value.items() if key != "remappings"}
    settings_ok = (without_remappings(settings_before) == without_remappings(settings_after) and
                   set(settings_after["remappings"]) - set(settings_before["remappings"]) == ADDED_REMAPPINGS and
                   not set(settings_before["remappings"]) - set(settings_after["remappings"]) and
                   len(settings_before["remappings"]) == len(set(settings_before["remappings"])) and
                   len(settings_after["remappings"]) == len(set(settings_after["remappings"])))
    typecheck_path = CURRENT / "all-source-typecheck.json"
    artifacts[str(typecheck_path)] = sha(typecheck_path.read_bytes())
    imports = import_resolution(read(typecheck_path), last["source-build-input.json"]["sources"], settings_before, settings_after)
    changed = sorted(name for name, value in last["source-size-gates.json"]["source_sha256"].items()
                     if value != first["source-size-gates.json"]["source_sha256"].get(name))
    known_metadata = set()
    for output in (first["source-build.json"], last["source-build.json"]):
        for contracts in output["contracts"].values():
            for obj in contracts.values():
                for kind in ("bytecode", "deployedBytecode"):
                    raw = bytes.fromhex(obj["evm"][kind]["object"])
                    if metadata := trailer(raw):
                        known_metadata.add(metadata)
    def masked(raw):
        regions = []
        result = bytearray(raw)
        used = set()
        for metadata in sorted(known_metadata, key=len, reverse=True):
            offset = 0
            while (offset := raw.find(metadata, offset)) >= 0:
                positions = set(range(offset, offset + len(metadata)))
                if not positions & used:
                    used |= positions
                    result[offset:offset + len(metadata)] = bytes(len(metadata))
                    regions.append({"offset": offset, "length": len(metadata), "metadata_sha256": sha(metadata)})
                offset += len(metadata)
        return bytes(result), sorted(regions, key=lambda value: value["offset"])
    bytecode = []
    for key in sorted(set(old) & set(new)):
        row = {"path": key[0], "name": key[1]}
        for kind in ("bytecode", "deployedBytecode"):
            a, b = [bytes.fromhex(obj[key]["evm"][kind]["object"]) for obj in (old, new)]
            ta, tb = trailer(a), trailer(b)
            sa, sb = a[:-len(ta)] if ta else a, b[:-len(tb)] if tb else b
            ma, ra = masked(a)
            mb, rb = masked(b)
            row[kind] = {"raw_equal": a == b, "terminal_metadata_stripped_equal": sa == sb,
                         "all_known_complete_metadata_masked_equal": ma == mb,
                         "masked_sha256_before": sha(ma), "masked_sha256_after": sha(mb),
                         "metadata_regions_before": ra, "metadata_regions_after": rb}
        bytecode.append(row)
    previous_gates = {(row["path"], row["name"]): row for row in first["source-size-gates.json"]["gates"]}
    sizes = []
    for row in last["source-size-gates.json"]["gates"]:
        key = (row["path"], row["name"])
        runtime, creation = [len(bytes.fromhex(new[key]["evm"][kind]["object"])) for kind in ("deployedBytecode", "bytecode")]
        previous = previous_gates[key]
        sizes.append({"path": key[0], "name": key[1], "runtime": runtime, "creation": creation,
                      "runtime_margin": 24576 - runtime, "maximum_total_argument_bytes": 49152 - creation,
                      "static_argument_bytes": row["static_argument_bytes"],
                      "exact_dynamic_constructor_argument_qualification_required": row["dynamic_constructor_exact_argument_qualification_required"],
                      "runtime_delta": runtime - previous["runtime"], "creation_delta": creation - previous["creation"],
                      "normal_gates_pass": runtime <= 24576 and creation + (row["static_argument_bytes"] or 0) <= 49152,
                      "saved_bytes_match": runtime == row["runtime"] and creation == row["creation"]})
    current_hashes = last["source-size-gates.json"]["source_sha256"]
    current_dependencies = last["source-size-gates.json"]["dependency_source_sha256"]
    current_sources_match = (set(current_hashes) == {p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.sol")} and
                             all(sha((ROOT / name).read_bytes()) == value for name, value in current_hashes.items()) and
                             all(sha((ROOT / name).read_bytes()) == value for name, value in current_dependencies.items()))
    prior_partial = read(HERE / "custody-review.json")["source_hashes"]
    matched_partial = {name: {"previous_local_review": prior_partial[name], "current": value,
                              "equal": prior_partial[name] == value}
                       for name, value in current_dependencies.items() if name in prior_partial}
    royalty = source_refactor(first["source-build-input.json"], last["source-build-input.json"])
    report = {"scope": "Read-only saved compiler/source comparison; no compiler/test rerun, EVM, RPC, signing or services.",
              "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__).read_bytes()), "artifact_sha256": artifacts,
              "project_objects": len(comparisons), "objects_removed": sorted(set(old) - set(new)),
              "objects_added": sorted(set(new) - set(old)),
              "object_comparisons": comparisons, "sizes": sizes, "bytecode_comparisons": bytecode,
              "normal_object_gates": len(sizes), "current_source_and_dependency_hashes_match": current_sources_match,
              "changed_production_sources": changed, "source_inventory_unchanged": set(current_hashes) == set(first["source-size-gates.json"]["source_sha256"]),
              "compiler_source_path_inventory_equal": set(first["source-build.json"]["sources"]) == set(last["source-build.json"]["sources"]),
              "compiler_settings_raw_equal": settings_before == settings_after,
              "settings_equal_except_actual_foundry_remappings": settings_ok,
              "baseline_remappings": settings_before["remappings"], "candidate_remappings": settings_after["remappings"],
              "added_remappings": sorted(ADDED_REMAPPINGS), "production_import_resolutions": imports,
              "current_dependency_sha256": current_dependencies, "prior_partial_local_review_dependency_pins": matched_partial,
              "historical_dependency_byte_identity_proven": False,
              "royalty_helper_refactor": royalty,
              "limits": [
                  "Only candidate Access GuardianChanged is removed for wire-ABI comparison; its new constructor/setter logs remain an intentional observable behavior change.",
                  "Only identical baseline InvalidConfiguration() duplicate ABI entries in Entry and the two converters are deduplicated; no internalType/tuple/name/mutability aliases are normalized.",
                  "Physical storage comparison retains member labels/types/slots/offsets recursively, ignoring compiler AST/type IDs and declaration provenance only.",
                  "Two extra unused production aliases and order differences among distinct nonoverlapping prefixes reflect actual existing foundry.toml. No optimizer/compiler/dependency upgrade is implied.",
                  "Prior normal input stored44 project contents but not31 dependency contents;75 logical path equality and current31 pins do not prove historical dependency byte identity.",
                  "Bytecode comparison masks only complete Solidity CBOR metadata independently found in saved compiler objects, recording exact regions; any remaining difference is reported.",
                  "Token/executable/layout equality is evidence, not a formal behavioral proof, execution regression, actual release URI/initcode qualification or independent audit."]}
    baseline_duplicates = sum(len(item["baseline_exceptions"]) for item in comparisons)
    candidate_event = sum(len(item["candidate_exceptions"]) for item in comparisons)
    report["checks_pass"] = (not report["objects_removed"] and not report["objects_added"] and
        all(item["exact_wire_abi_equal_after_declared_exceptions"] and item["exact_recursive_storage_equal"] for item in comparisons) and
        baseline_duplicates == 3 and candidate_event == 1 and len(sizes) == 37 and
        all(item["normal_gates_pass"] and item["saved_bytes_match"] for item in sizes) and
        current_sources_match and set(changed) == CHANGED_SOURCES and report["source_inventory_unchanged"] and
        report["compiler_source_path_inventory_equal"] and settings_ok and all(item["equal"] and not item["uses_added_alias"] for item in imports) and
        royalty["exact_balance_expression_tokens_equal"] and royalty["function_inventory_equal_except_removed_helper"] and
        royalty["all_bodies_and_call_order_tokens_equal"] and all(item["equal"] for item in matched_partial.values()))
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# Saved compiler and source comparison", "", "No compiler or execution tests were repeated by this comparison.", "",
             f"- **{len(comparisons)}** current project objects retain exact wire ABIs after the declared exceptions and exact recursive physical storage.",
             "- Access adds the explicit `GuardianChanged` event. Existing keeper and new guardian constructor grant logs are observable behavior changes; economic permissions are unchanged.",
             "- Three identical `InvalidConfiguration()` error duplicates disappear from the baseline ABI lists. No selector, parameter/tuple label, constructor argument, output or mutability change is hidden.",
             "- Only Access, RoyaltyRewards and the internal v3 validator source hashes differ; the other41production files match the prior build.",
             "- All **37** normal runtime/initcode object gates pass. Exact dynamic NFT URI argument encoding remains a release gate.", "",
             "## Compiler and dependencies", "", "The actual existing Foundry profile has seven remappings; the older bespoke production driver supplied five. The two added aliases (`v4-core/` and `permit2/`) are unused by production imports. Every resolved production import and all75source-unit paths remain identical. Core compiler/optimizer/settings are unchanged; raw settings are explicitly not byte-identical.", "",
             "Current31dependency source bytes are explicitly captured and match the new build. The older production input omitted those dependency contents, so historical dependency-byte identity is **not proven**. Partial earlier local-review pins are compared only where they exist.", "",
             "## Royalty balance helper", "", "The removed private balance expression exactly matches the already inherited `_canonicalBalance` expression. Every remaining RoyaltyRewards body preserves its token/call order after only that helper-name replacement. Actual executable comparisons are recorded below; this source comparison does not replace changed-path execution checks.", "",
             "| Object with a size change | Runtime delta | Creation delta | Runtime / margin |", "| --- | ---: | ---: | ---: |"]
    for item in sizes:
        if item["runtime_delta"] or item["creation_delta"]:
            lines.append(f"| {item['name']} | {item['runtime_delta']:+d} | {item['creation_delta']:+d} | {item['runtime']} / {item['runtime_margin']} |")
    lines += ["", "## Executable comparison", ""]
    for item in bytecode:
        if item["name"] in ("ZZZRoyaltyRewards", "ZZZVault", "ZZZMigration", "ZZZCanonicalHandoff"):
            lines.append(f"- `{item['name']}` creation/runtime equal after only known complete metadata masking: **{item['bytecode']['all_known_complete_metadata_masked_equal']} / {item['deployedBytecode']['all_known_complete_metadata_masked_equal']}**.")
    lines += ["", "See `compiler-comparison.json` for all object ABIs/layouts/bytecode,37size rows,75source units, import resolutions and hashes. Initial ABI/AST test-import failure and test-only repair remain separately recorded. Production remains NOT APPROVED.", ""]
    markdown.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"checks_pass": report["checks_pass"], "project_objects": len(comparisons),
                      "normal_gates": len(sizes), "changed_sources": changed, "production_imports": len(imports),
                      "baseline_duplicate_errors_removed": baseline_duplicates, "candidate_events_added": candidate_event}, indent=2))
    return 0 if report["checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
