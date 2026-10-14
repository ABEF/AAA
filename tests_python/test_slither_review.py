import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("slither_review", Path(__file__).resolve().parents[1] / "scripts/check-slither-review.py")
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


class SlitherReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        for name in ("src/Core.sol", "foundry.toml", "package-lock.json", "slither.config.json"):
            (self.root / name).write_text("reviewed\n")
        self.finding = {"check": "example", "impact": "High", "confidence": "High", "description": "Core.call (src/Core.sol#1)\n"}
        self.report = {"success": True, "error": None, "results": {"detectors": [self.finding]}}
        self.review = {
            "independent_audit": False,
            "source_sha256_lf": {p.relative_to(self.root).as_posix(): reviewer.source_hash(p) for p in self.root.rglob("*") if p.is_file()},
            "findings": [{"fingerprint": reviewer.fingerprint(self.finding), "disposition": "accepted_risk", "rationale": "Explicit reviewed trust assumption"}],
        }

    def test_complete_review_accepts_only_unchanged_analysis(self):
        self.assertEqual(reviewer.check(self.report, self.review, self.root), [])
        (self.root / "src/Core.sol").write_bytes(b"reviewed\r\n")
        self.assertEqual(reviewer.check(self.report, self.review, self.root), [])

    def test_analyzer_failure_is_not_an_empty_clean_report(self):
        self.report["success"] = False
        self.assertTrue(reviewer.check(self.report, self.review, self.root))
        self.report["success"] = True
        del self.report["results"]["detectors"]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_source_drift_and_new_source_require_review(self):
        (self.root / "src/Core.sol").write_text("changed\n")
        self.assertTrue(reviewer.check(self.report, self.review, self.root))
        (self.root / "src/Extra.sol").write_text("new\n")
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_new_and_removed_findings_require_review(self):
        self.report["results"]["detectors"].append(dict(self.finding, description="new finding"))
        self.assertTrue(reviewer.check(self.report, self.review, self.root))
        self.report["results"]["detectors"] = []
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_unresolved_missing_or_duplicate_reviews_fail(self):
        self.review["findings"][0]["disposition"] = "open"
        self.assertTrue(reviewer.check(self.report, self.review, self.root))
        self.review["findings"][0]["disposition"] = "accepted_risk"
        self.review["findings"][0]["rationale"] = " "
        self.assertTrue(reviewer.check(self.report, self.review, self.root))
        self.review["findings"].append(self.review["findings"][0])
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_path_normalization_does_not_change_review_identity(self):
        windows = dict(self.finding, description="Core.call (C:\\repo\\src\\Core.sol#1)\n")
        self.assertEqual(reviewer.fingerprint(windows), reviewer.fingerprint(self.finding))


if __name__ == "__main__":
    unittest.main()
