"""Admit a fixed set of historical observations; never execute or adopt them.

The checked-in manifest is an explicitly reviewed baseline, not caller supplied
positive evidence. Integrity does not prove original execution or branch coverage.
"""
from __future__ import annotations
import gzip
import hashlib
import io
import json
import math
import re
import zlib
from pathlib import Path
from .abi import keccak256

MANIFEST = "config/focused-evidence-1c18379.json"
MANIFEST_SHA256 = "96c5aef1946eeec3083a40302125039812616d683816e7233512f1efe900f568"
MAX_STORED = 4 * 1024 * 1024
MAX_EXPANDED = 8 * 1024 * 1024
MAX_DEPTH = 40

class EvidenceError(ValueError):
    """A bounded, non-secret refusal reason."""

def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate_json_key")
        result[key] = value
    return result

def _integer(text):
    if len(text) > 128:
        raise EvidenceError("json_integer_limit")
    return int(text)

def _float(text):
    if len(text) > 128:
        raise EvidenceError("json_number_limit")
    number = float(text)
    if not math.isfinite(number):
        raise EvidenceError("nonfinite_json_number")
    return number

def _reject_number(_):
    raise EvidenceError("nonfinite_json_number")

def _decode(data: bytes):
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique,
                           parse_int=_integer, parse_float=_float, parse_constant=_reject_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise EvidenceError("invalid_json") from error
    stack = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise EvidenceError("json_depth_limit")
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return value

def _bytes(root: Path, spec: dict) -> bytes:
    relative = spec["path"]
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise EvidenceError("invalid_evidence_path")
    try:
        path = (root / relative).resolve(strict=True)
        path.relative_to(root.resolve())
        with path.open("rb") as handle:
            stored = handle.read(MAX_STORED + 1)
    except (OSError, ValueError) as error:
        raise EvidenceError("evidence_unavailable") from error
    if len(stored) > MAX_STORED:
        raise EvidenceError("stored_evidence_limit")
    if _digest(stored) != spec["sha256"]:
        raise EvidenceError("historical_evidence_changed")
    if relative.endswith(".gz"):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(stored)) as handle:
                expanded = handle.read(MAX_EXPANDED + 1)
        except (OSError, EOFError, zlib.error) as error:
            raise EvidenceError("invalid_gzip") from error
        if len(expanded) > MAX_EXPANDED:
            raise EvidenceError("expanded_evidence_limit")
        return expanded
    return stored

def _load(root: Path, spec: dict):
    return _decode(_bytes(root, spec))

def _exact_ids(actual: list, expected: list):
    if (not isinstance(actual, list) or any(not isinstance(x, str) for x in actual)
            or len(actual) != len(set(actual)) or sorted(actual) != sorted(expected)):
        raise EvidenceError("exact_method_ids_differ")

def _forge_methods(raw: dict, expected: list) -> list:
    if not isinstance(raw, dict) or not raw:
        raise EvidenceError("invalid_forge_result")
    ids = []
    for suite, result in raw.items():
        if not isinstance(suite, str) or not isinstance(result, dict):
            raise EvidenceError("invalid_forge_suite")
        methods = result.get("test_results")
        if not isinstance(methods, dict) or not methods:
            raise EvidenceError("empty_forge_selection")
        for method, record in methods.items():
            if not isinstance(record, dict) or record.get("status") != "Success":
                raise EvidenceError("method_not_successful")
            if record.get("reason") is not None or record.get("counterexample") is not None:
                raise EvidenceError("method_failure_detail")
            ids.append(suite + "." + method)
    _exact_ids(ids, expected)
    return ids

def _artifact(artifact: dict, proof: dict, group: dict):
    metadata = artifact.get("metadata")
    if isinstance(metadata, str):
        metadata = _decode(metadata.encode("utf-8"))
    if not isinstance(metadata, dict):
        raise EvidenceError("missing_artifact_metadata")
    targets = metadata.get("settings", {}).get("compilationTarget", {})
    suites = {identifier.rsplit(".", 1)[0] for identifier in group["expected_ids"]}
    # Exact methods contain no dots; contract-qualified suite retains .sol.
    expected_targets = dict(suite.rsplit(":", 1) for suite in suites)
    if targets != expected_targets:
        raise EvidenceError("compiled_target_differs")
    identifiers = artifact.get("methodIdentifiers")
    if not isinstance(identifiers, dict):
        raise EvidenceError("missing_compiled_methods")
    for identifier in group["expected_ids"]:
        signature = identifier.rsplit(".", 1)[1]
        if identifiers.get(signature) != keccak256(signature.encode()).hex()[:8]:
            raise EvidenceError("compiled_method_differs")
    sources = metadata.get("sources")
    recorded = proof.get(group["source_field"])
    if not isinstance(sources, dict) or not isinstance(recorded, dict) or set(sources) != set(recorded):
        raise EvidenceError("compiled_source_set_differs")
    for name, source in sources.items():
        if source.get("keccak256") != recorded[name].get("compiler_keccak256"):
            raise EvidenceError("compiled_source_identity_differs")
    if metadata.get("compiler") != proof.get("compiler"):
        raise EvidenceError("compiler_identity_differs")
    if metadata.get("settings") != proof.get("settings"):
        raise EvidenceError("compiler_settings_differ")

def _python_log(data: bytes, expected: list):
    try:
        text = data.decode("utf-8").replace("\r", "")
    except UnicodeError as error:
        raise EvidenceError("invalid_python_log") from error
    entries = re.findall(r"^(test\w+) \(([^()]+)\) \.\.\. (.*)$", text, re.MULTILINE)
    if any(status != "ok" or identifier.rsplit(".", 1)[-1] != leaf
           for leaf, identifier, status in entries):
        raise EvidenceError("python_result_not_successful")
    _exact_ids([identifier for _, identifier, _ in entries], expected)
    summary = re.findall(r"^Ran ([0-9]+) tests? in [0-9.]+s$", text, re.MULTILINE)
    if summary != [str(len(expected))] or not text.rstrip().endswith("\nOK"):
        raise EvidenceError("python_summary_differs")

def _group(root: Path, group: dict) -> dict:
    kind = group["kind"]
    expected = group["expected_ids"]
    if kind == "forge":
        raw = _load(root, group["raw"])
        _forge_methods(raw, expected)
        proof = _load(root, group["proof"])
        if group["artifact"]:
            _artifact(_load(root, group["artifact"]), proof, group)
            level = "exact_raw_results_and_compiled_artifact_source_identity"
        else:
            checks = proof.get("compiled_source_metadata_checks", [])
            expected_suite = expected[0].rsplit(".", 1)[0]
            matches = [x for x in checks if x.get("suite") == expected_suite]
            if len(matches) != 1 or matches[0].get("current_compiler_text_matches_metadata") is not True:
                raise EvidenceError("recorded_source_stage_missing")
            level = "exact_raw_results_and_recorded_source_stage_no_standalone_artifact"
    elif kind == "reported-python":
        record = _load(root, group["raw"])
        actual = record["new_methods_passed"] + record["adapted_methods_passed"]
        _exact_ids(actual, expected)
        if record.get("unique_passed_count") != len(expected) or not record.get("source_sha256"):
            raise EvidenceError("reported_python_record_differs")
        level = "source_hashed_reported_method_list_no_independent_raw_log"
    else:
        ids = []
        for stage in group["stages"]:
            encoded = _bytes(root, stage["raw"])
            record = _decode(encoded)
            log = _bytes(root, stage["log"])
            _python_log(log, stage["expected_ids"])
            if _digest(log) != record.get("log_sha256"):
                raise EvidenceError("python_log_digest_differs")
            if kind == "python-command":
                if record.get("exit_code") != 0 or record.get("command", [])[1:4] != ["-m", "unittest", "-v"]:
                    raise EvidenceError("python_command_differs")
                selected = record["command"][4:]
            elif kind == "python-record":
                if (record.get("successful") is not True or record.get("failures") != 0
                    or record.get("errors") != 0 or record.get("skips") != 0
                    or record.get("tests_run") != len(stage["expected_ids"])
                    or record.get("source_sha256_before") != record.get("source_sha256_after")):
                    raise EvidenceError("python_stage_not_successful")
                selected = record["methods"]
            else:
                raise EvidenceError("unknown_evidence_kind")
            _exact_ids(selected, stage["expected_ids"])
            ids.extend(selected)
        _exact_ids(ids, expected)
        pins = _load(root, group["source_pins"])
        pin_ids = pins["final_core_methods"] if kind == "python-command" else list(pins["new_method_ast_sha256"])
        _exact_ids(pin_ids, expected)
        level = "exact_unittest_logs_and_recorded_historical_source_pins"
    return {"id": group["id"], "historical_method_records": len(expected),
            "evidence_level": level, "source_stage": group["source_stage"],
            "current_source_adopted": False, "new_executions": 0}

def check(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    manifest = _load(root, {"path": MANIFEST, "sha256": MANIFEST_SHA256})
    if manifest.get("schema") != 1 or len(manifest.get("groups", [])) != 7:
        raise EvidenceError("trusted_manifest_shape_differs")
    groups = [_group(root, group) for group in manifest["groups"]]
    return {"schema": 1, "integrity_admitted": True,
            "trusted_baseline": manifest["trusted_baseline"], "groups": groups,
            "historical_method_records": sum(x["historical_method_records"] for x in groups),
            "new_test_executions": 0, "new_EVM_executions": 0,
            "production_approved": False, "omissions": manifest["omissions"],
            "limit": "Integrity is not proof of original execution, complete behavior, current-source qualification or independent audit."}
