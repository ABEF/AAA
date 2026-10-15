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

    def nested(self, children="\t\t- b() (src/Core.sol#3)\n\t\t- a() (src/Core.sol#2)\n"):
        return dict(self.finding, check="reentrancy-no-eth", description=
            "Reentrancy in Core.call (src/Core.sol#1-9):\n\tExternal calls:\n"
            "\t- parent() (src/Core.sol#4)\n" + children +
            "\tState variables written after the call(s):\n\t- value (src/Core.sol#5)\n")

    def test_unordered_nested_callees_have_stable_identity(self):
        ordered = self.nested("\t\t- a() (src/Core.sol#2)\n\t\t- b() (src/Core.sol#3)\n")
        self.assertEqual(reviewer.fingerprint(self.nested()), reviewer.fingerprint(ordered))

    def test_changed_expression_or_location_still_requires_review(self):
        for old,new in (("a()","withdraw()"),("#2)","#8)")):
            altered = dict(self.nested(),description=self.nested()["description"].replace(old,new))
            self.assertNotEqual(reviewer.fingerprint(self.nested()),reviewer.fingerprint(altered))

    def test_nested_call_duplicates_and_membership_are_preserved(self):
        extra = self.nested("\t\t- a() (src/Core.sol#2)\n\t\t- b() (src/Core.sol#3)\n\t\t- b() (src/Core.sol#3)\n")
        missing = self.nested("\t\t- a() (src/Core.sol#2)\n")
        for altered in (extra,missing):
            self.assertNotEqual(reviewer.fingerprint(self.nested()),reviewer.fingerprint(altered))

    def test_parent_groups_and_root_call_order_are_preserved(self):
        original=self.nested();changed=dict(original,description=original["description"].replace("parent()","otherParent()"))
        self.assertNotEqual(reviewer.fingerprint(original),reviewer.fingerprint(changed))
        a="\t- first() (src/Core.sol#6)\n";b="\t- second() (src/Core.sol#7)\n"
        self.assertNotEqual(reviewer.fingerprint(dict(original,description=original["description"]+a+b)),
            reviewer.fingerprint(dict(original,description=original["description"]+b+a)))

    def test_callee_cannot_move_to_another_parent(self):
        first="\t- first() (src/Core.sol#6)\n";second="\t- second() (src/Core.sol#7)\n"
        child="\t\t- a() (src/Core.sol#2)\n";header="Reentrancy in Core.call (src/Core.sol#1):\n"
        self.assertNotEqual(reviewer.fingerprint(dict(self.nested(),description=header+first+child+second)),
            reviewer.fingerprint(dict(self.nested(),description=header+first+second+child)))

    def test_deeper_nodes_are_not_detached_by_sorting(self):
        original=self.nested("\t\t- b() (src/Core.sol#3)\n\t\t- a() (src/Core.sol#2)\n\t\t\t- child() (src/Core.sol#8)\n")
        altered=dict(original,description=original["description"].replace(
            "\t\t- b() (src/Core.sol#3)\n\t\t- a() (src/Core.sol#2)",
            "\t\t- a() (src/Core.sol#2)\n\t\t- b() (src/Core.sol#3)"))
        self.assertNotEqual(reviewer.fingerprint(original),reviewer.fingerprint(altered))

    def test_other_detectors_keep_exact_description_order(self):
        original=dict(self.nested(),check="other-detector")
        altered=dict(original,description=original["description"].replace(
            "\t\t- b() (src/Core.sol#3)\n\t\t- a() (src/Core.sol#2)",
            "\t\t- a() (src/Core.sol#2)\n\t\t- b() (src/Core.sol#3)"))
        self.assertNotEqual(reviewer.fingerprint(original),reviewer.fingerprint(altered))

    def test_state_write_leaf_order_is_not_normalized(self):
        original=self.nested()
        original=dict(original,description=original["description"].replace("External calls:","State variables written after the call(s):"))
        altered=dict(original,description=original["description"].replace(
            "\t\t- b() (src/Core.sol#3)\n\t\t- a() (src/Core.sol#2)",
            "\t\t- a() (src/Core.sol#2)\n\t\t- b() (src/Core.sol#3)"))
        self.assertNotEqual(reviewer.fingerprint(original),reviewer.fingerprint(altered))

    def test_severity_and_confidence_remain_part_of_identity(self):
        original=self.nested()
        for field in ("impact","confidence"):
            self.assertNotEqual(reviewer.fingerprint(original),reviewer.fingerprint(dict(original,**{field:"Low"})))


if __name__ == "__main__":
    unittest.main()
