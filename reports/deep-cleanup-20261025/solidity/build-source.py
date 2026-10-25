"""Closed-input production size and all-source ABI/AST checks; no EVM execution."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import tomllib


ROOT = Path(__file__).resolve().parents[3]
EXTERNAL = Path(r"C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9")
BASELINE = EXTERNAL / "auditability-refactor-20261025/solidity"
OUT = EXTERNAL / "deep-cleanup-20261025/solidity"
TRACKED = Path(__file__).resolve().parent
SOLC = EXTERNAL / "toolchain-0.8.26/solc.exe"
BUILD_INPUTS = ("foundry.toml", "package.json", "package-lock.json", "scripts/install-deps.sh")
MAX_RUNTIME = 24_576
MAX_INITCODE = 49_152


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect(names) -> dict[str, bytes]:
    result = {}
    for name in sorted(names):
        if (not isinstance(name, str) or "\\" in name or
                any(part in ("", ".", "..") for part in name.split("/"))):
            raise ValueError("Invalid input source name: " + repr(name))
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file() or path.suffix != ".sol":
            raise ValueError("Input source escaped or is missing: " + name)
        result[name] = path.read_bytes()
    return result


def current_project(directories) -> set[str]:
    return {p.relative_to(ROOT).as_posix() for directory in directories
            for p in (ROOT / directory).rglob("*.sol")}


def digest_map(raw) -> dict:
    return {name: sha(content) for name, content in raw.items()}


def unchanged(raw, directories, project_names, build_raw) -> bool:
    return (current_project(directories) == project_names and
            all((ROOT / name).read_bytes() == content for name, content in raw.items()) and
            all((ROOT / name).read_bytes() == content for name, content in build_raw.items()))


def run_compile(prefix, raw_sources, settings, directories, build_raw) -> tuple[dict, dict]:
    project_names = {name for name in raw_sources if name.split("/", 1)[0] in directories}
    sources = {name: {"content": content.decode("utf-8-sig")} for name, content in raw_sources.items()}
    payload = {"language": "Solidity", "sources": sources, "settings": settings}
    input_file = OUT / (prefix + "-input.json")
    write(input_file, payload)
    before = unchanged(raw_sources, directories, project_names, build_raw)
    if not before:
        raise ValueError("Inputs changed before compiler launch")
    print(json.dumps({"stage": prefix, "status": "compiling", "explicit_inputs": len(sources),
                      "project_inputs": len(project_names)}, separators=(",", ":")), flush=True)
    start = time.monotonic()
    command = [str(SOLC), "--standard-json", "--base-path", str(ROOT)]
    process = subprocess.run(command, input=json.dumps(payload).encode("utf-8"),
                             cwd=ROOT, capture_output=True, timeout=1200)
    elapsed = round(time.monotonic() - start, 2)
    (OUT / (prefix + "-stderr.log")).write_bytes(process.stderr)
    start_json = process.stdout.find(b"{")
    if start_json < 0:
        (OUT / (prefix + "-unparsed.stdout")).write_bytes(process.stdout)
        raise ValueError("Compiler returned no JSON")
    output_raw = process.stdout[start_json:]
    output_file = OUT / (prefix + ".json")
    output_file.write_bytes(output_raw)
    compiled = json.loads(output_raw)
    errors = [entry for entry in compiled.get("errors", []) if entry.get("severity") == "error"]
    compiled_names = set(compiled.get("sources", {}))
    stable = unchanged(raw_sources, directories, project_names, build_raw)
    report = {
        "command": command,
        "solc_exit_code": process.returncode,
        "elapsed_seconds": elapsed,
        "errors": errors,
        "source_count": len(sources),
        "compiled_source_count": len(compiled_names),
        "closed_input_inventory": compiled_names == set(sources),
        "unexpected_implicit_sources": sorted(compiled_names - set(sources)),
        "missing_compiled_sources": sorted(set(sources) - compiled_names),
        "unchanged_before_build": before,
        "unchanged_during_build": stable,
        "source_sha256": digest_map({name: raw_sources[name] for name in sorted(project_names)}),
        "dependency_source_sha256": digest_map({name: content for name, content in raw_sources.items()
                                                  if name not in project_names}),
        "compiler_content_sha256": {name: sha(value["content"].encode("utf-8"))
                                    for name, value in sources.items()},
        "build_input_sha256": digest_map(build_raw),
        "settings": settings,
        "compiler_input_sha256": sha(input_file.read_bytes()),
        "compiler_output_sha256": sha(output_raw),
        "solc_executable_sha256": sha(SOLC.read_bytes()),
        "all_pass": process.returncode == 0 and not errors and stable and compiled_names == set(sources),
    }
    return compiled, report


def size_gates(compiled) -> list[dict]:
    gates = []
    for source, contracts in sorted(compiled.get("contracts", {}).items()):
        if not source.startswith("src/"):
            continue
        for name, obj in sorted(contracts.items()):
            creation_raw = obj["evm"]["bytecode"]["object"]
            runtime_raw = obj["evm"]["deployedBytecode"]["object"]
            # bytes.fromhex rejects unlinked placeholders and malformed output.
            creation = len(bytes.fromhex(creation_raw))
            runtime = len(bytes.fromhex(runtime_raw))
            if not creation:
                continue
            arguments = next((item["inputs"] for item in obj["abi"] if item.get("type") == "constructor"), [])
            dynamic = any(item["type"] in ("string", "bytes", "tuple") or "[" in item["type"]
                          for item in arguments)
            static_size = None if dynamic else 32 * len(arguments)
            gates.append({
                "path": source, "name": name,
                "runtime": runtime, "runtime_margin": MAX_RUNTIME - runtime,
                "creation": creation,
                "constructor_types": [item["type"] for item in arguments],
                "static_argument_bytes": static_size,
                "runtime_ok": runtime <= MAX_RUNTIME,
                "creation_ok": creation + (static_size or 0) <= MAX_INITCODE,
                "maximum_total_argument_bytes": MAX_INITCODE - creation,
                "dynamic_constructor_exact_argument_qualification_required": dynamic,
            })
    return gates


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_raw = {name: (ROOT / name).read_bytes() for name in BUILD_INPUTS}
    profile = tomllib.loads(build_raw["foundry.toml"].decode("utf-8-sig"))["profile"]["default"]
    if (profile["solc_version"] != "0.8.26" or profile["evm_version"] != "cancun" or
            profile["via_ir"] is not True or profile["optimizer"] is not True or
            profile["optimizer_runs"] != 1 or profile["optimizer_details"] != {"yul": False}):
        raise ValueError("Unexpected compiler profile; review rather than weakening normal gates")
    compiler_hash = sha(SOLC.read_bytes())
    version = subprocess.run([str(SOLC), "--version"], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    if "0.8.26+commit.8a97fa7a" not in version:
        raise ValueError("Wrong solc executable version")
    (OUT / "solc-version.txt").write_text(version, encoding="utf-8")
    settings = {"evmVersion": profile["evm_version"], "viaIR": profile["via_ir"],
                "optimizer": {"enabled": profile["optimizer"], "runs": profile["optimizer_runs"],
                              "details": profile["optimizer_details"]},
                "remappings": profile["remappings"]}
    old_normal = load(BASELINE / "source-build.json")
    old_normal_settings = load(BASELINE / "source-size-gates.json")["settings"]
    old_all = load(BASELINE / "final-all-source-typecheck.json")
    project_directories = ("src", "test", "script")
    all_project_names = current_project(project_directories)
    all_names = all_project_names | {
        name for name in old_all["sources"] if name.split("/", 1)[0] not in project_directories}
    # Freeze the complete source/test/script/dependency set before either compile.
    all_raw = collect(all_names)
    normal_names = current_project(("src",)) | {name for name in old_normal["sources"] if not name.startswith("src/")}
    if not normal_names <= set(all_raw):
        raise ValueError("Production closure is absent from complete source closure")
    production_raw = {name: all_raw[name] for name in sorted(normal_names)}
    normal_settings = dict(settings, outputSelection={"*": {"*": ["abi", "storageLayout", "evm.bytecode.object", "evm.deployedBytecode.object"]}})
    compiled, report = run_compile("source-build", production_raw, normal_settings, ("src",), build_raw)
    report["all_source_test_inputs_unchanged_during_build"] = unchanged(
        all_raw, project_directories, all_project_names, build_raw)
    report["solc_executable_unchanged"] = sha(SOLC.read_bytes()) == compiler_hash
    report["baseline_driver_remappings"] = old_normal_settings["remappings"]
    report["actual_foundry_remappings"] = profile["remappings"]
    report["remappings_added_from_actual_foundry_profile"] = sorted(
        set(profile["remappings"]) - set(old_normal_settings["remappings"]))
    report["gates"] = size_gates(compiled) if not report["errors"] else []
    report["all_pass"] = report["all_pass"] and report["all_source_test_inputs_unchanged_during_build"] and \
        report["solc_executable_unchanged"] and len(report["gates"]) == 37 and all(
        entry["runtime_ok"] and entry["creation_ok"] for entry in report["gates"])
    report["qualification"] = ("Normal EIP-170/EIP-3860 object limits. Dynamic release constructor arguments "
                               "still require exact encoding qualification. Closed explicit project/dependency compiler inventory; "
                               "no EVM execution, deployment or service approval.")
    write(OUT / "source-size-gates.json", report)
    write(TRACKED / "production-size-gates.json", report)
    print(json.dumps({"stage": "source-build", "all_pass": report["all_pass"], "elapsed_seconds": report["elapsed_seconds"],
                      "gates": len(report["gates"]), "errors": report["errors"],
                      "implicit_sources": report["unexpected_implicit_sources"]}, separators=(",", ":")), flush=True)
    if not report["all_pass"]:
        return 1
    all_settings = dict(settings, outputSelection={"*": {"": ["ast"], "*": ["abi"]}})
    _, typecheck = run_compile("all-source-typecheck", all_raw, all_settings, project_directories, build_raw)
    # Production input bytes must also match the later complete typecheck.
    typecheck["production_inputs_match_normal_build"] = all(
        all_raw.get(name) == raw for name, raw in production_raw.items())
    typecheck["solc_executable_unchanged"] = sha(SOLC.read_bytes()) == compiler_hash
    typecheck["all_pass"] = typecheck["all_pass"] and typecheck["production_inputs_match_normal_build"] and \
        typecheck["solc_executable_unchanged"]
    write(OUT / "typecheck-summary.json", typecheck)
    write(TRACKED / "typecheck-summary.json", typecheck)
    print(json.dumps({"stage": "all-source-typecheck", "all_pass": typecheck["all_pass"],
                      "elapsed_seconds": typecheck["elapsed_seconds"], "sources": typecheck["source_count"],
                      "errors": typecheck["errors"], "implicit_sources": typecheck["unexpected_implicit_sources"]},
                     separators=(",", ":")), flush=True)
    return 0 if typecheck["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
