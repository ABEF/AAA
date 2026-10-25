"""Recheck only the final Access guard and actual canonical retirement path.

Uses the same byte-preserving AST harness as the 87-method campaign; requires
matching reviewed AST8/normal-size artifacts. No production source is changed.
"""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[3]
driver = ROOT / "reports/simplification-20261025/solidity/run-focused.py"
spec = importlib.util.spec_from_file_location("scoped_runner", driver)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
base = module.EXTERNAL / "simplification-audit-20261025/solidity"
module.SELECTION = {
    "AccessControllerTest": {
        "testCanonicalZZZIdentityMustBeBoundBeforeSeal",
        "testMissingOrMismatchedExitZZZCannotPermanentlySeal",
        "testSealErasesBootstrap",
        "testRetiredBridgeModulesCannotBeBoundEvenBeforeSeal",
        "testFuzzTerminalCanonicalStateCannotReopen",
    },
    "CanonicalHandoffTest": {
        "testRetiredSourceCannotAbortRecommitOrReopenThroughUnpause",
    },
}
sys.argv = [str(driver), "--evidence", str(base / "terminal-guard"),
            "--compiler-input", str(base / "all-source-typecheck-input-8.json"),
            "--compiler-output", str(base / "all-source-typecheck-8.json"),
            "--size-evidence", str(base / "source-size-gates.json"), *sys.argv[1:]]
raise SystemExit(module.main())
