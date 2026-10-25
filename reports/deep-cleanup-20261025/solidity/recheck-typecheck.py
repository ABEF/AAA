"""Only repeat the failed ABI/AST stage after the explicit Vm test import."""
import importlib.util
import json
from pathlib import Path
import sys

driver_path = Path(__file__).with_name("build-source.py")
spec = importlib.util.spec_from_file_location("deep_cleanup_build", driver_path)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

initial = driver.load(driver.OUT / "initial-typecheck-summary.json")
production = driver.load(driver.OUT / "source-size-gates.json")
if production["all_pass"] is not True:
    raise ValueError("Cannot reuse a failed production build")
old_hashes = dict(initial["source_sha256"], **initial["dependency_source_sha256"])
raw = driver.collect(old_hashes)
changed = sorted(name for name, content in raw.items() if driver.sha(content) != old_hashes[name])
if changed != ["test/DirectGovernance.t.sol"]:
    raise ValueError("Unexpected source changes since initial typecheck: " + repr(changed))
before_test = (driver.OUT / "initial-DirectGovernance.t.sol.txt").read_bytes()
after_test = raw["test/DirectGovernance.t.sol"]
if after_test != before_test.replace(b'import {Test} from "forge-std/Test.sol";',
        b'import {Test} from "forge-std/Test.sol";\nimport {Vm} from "forge-std/Vm.sol";'):
    raise ValueError("Test repair differs from the single explicit Vm import")
build_raw = {name: (driver.ROOT / name).read_bytes() for name in driver.BUILD_INPUTS}
if driver.digest_map(build_raw) != production["build_input_sha256"]:
    raise ValueError("Build input drift prevents production-build reuse")
normal_hashes = dict(production["source_sha256"], **production["dependency_source_sha256"])
if any(driver.sha(raw[name]) != value for name, value in normal_hashes.items()):
    raise ValueError("Production source/dependency drift prevents build reuse")
if driver.sha(driver.SOLC.read_bytes()) != production["solc_executable_sha256"]:
    raise ValueError("Compiler binary drift prevents build reuse")
_, report = driver.run_compile("all-source-typecheck", raw, initial["settings"],
                               ("src", "test", "script"), build_raw)
report["production_inputs_match_normal_build"] = all(
    driver.sha(raw[name]) == value for name, value in normal_hashes.items())
report["solc_executable_unchanged"] = driver.sha(driver.SOLC.read_bytes()) == production["solc_executable_sha256"]
report["production_build_reused"] = {
    "size_evidence_sha256": driver.sha((driver.OUT / "source-size-gates.json").read_bytes()),
    "project_sources": len(production["source_sha256"]),
    "dependencies": len(production["dependency_source_sha256"]),
    "unchanged": report["production_inputs_match_normal_build"],
}
report["repair"] = {"changed_files": changed,
                    "only_change": "Explicit forge-std/Vm.sol type import for new role-event tests",
                    "initial_typecheck_summary_sha256": driver.sha((driver.OUT / "initial-typecheck-summary.json").read_bytes())}
report["all_pass"] = report["all_pass"] and report["production_inputs_match_normal_build"] and report["solc_executable_unchanged"]
driver.write(driver.OUT / "typecheck-summary.json", report)
driver.write(driver.TRACKED / "typecheck-summary.json", report)
print(json.dumps({"stage": "all-source-typecheck-recheck", "all_pass": report["all_pass"],
                  "elapsed_seconds": report["elapsed_seconds"], "inputs": report["source_count"],
                  "errors": report["errors"], "implicit_sources": report["unexpected_implicit_sources"],
                  "production_build_reused": report["production_build_reused"]}, separators=(",", ":")), flush=True)
sys.exit(0 if report["all_pass"] else 1)
