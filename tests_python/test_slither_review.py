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

    def events(self, bundles=None, section="Event emitted after the call(s):", check="reentrancy-events"):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        first = root + "\t\t- first() (src/Core.sol#3)\n"
        second = root + "\t\t- second() (src/Core.sol#4)\n"
        if bundles is None:
            bundles = [second, first]
        return dict(self.finding, check=check, description=
            "Reentrancy in Core.call (src/Core.sol#1-9):\n"
            "\tExternal calls:\n\t- dispatch() (src/Core.sol#2)\n"
            "\t" + section + "\n" + "".join(bundles))

    def test_tied_event_roots_keep_stable_identity_when_bundles_swap(self):
        original = self.events()
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        ordered = self.events([root + "\t\t- first() (src/Core.sol#3)\n",
            root + "\t\t- second() (src/Core.sol#4)\n"])
        self.assertEqual(reviewer.fingerprint(original), reviewer.fingerprint(ordered))

    def test_tied_event_bundles_keep_deeper_descendants_attached(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        first = root + "\t\t- first() (src/Core.sol#3)\n\t\t\t- childA() (src/Core.sol#5)\n"
        second = root + "\t\t- second() (src/Core.sol#4)\n\t\t\t- childB() (src/Core.sol#6)\n"
        original = self.events([second, first])
        self.assertEqual(reviewer.fingerprint(original), reviewer.fingerprint(self.events([first, second])))
        detached = self.events([first.replace("childA()", "childB()"), second.replace("childB()", "childA()")])
        self.assertNotEqual(reviewer.fingerprint(original), reviewer.fingerprint(detached))

    def test_changed_event_expression_or_source_location_requires_review(self):
        original = self.events()
        for old, new in (("Emitted(amount)", "Emitted(other)"), ("#8)", "#9)")):
            changed = dict(original, description=original["description"].replace(old, new, 1))
            self.assertNotEqual(reviewer.fingerprint(original), reviewer.fingerprint(changed))

    def test_changed_event_origin_expression_or_location_requires_review(self):
        original = self.events()
        for old, new in (("first()", "withdraw()"), ("#3)", "#7)")):
            changed = dict(original, description=original["description"].replace(old, new))
            self.assertNotEqual(reviewer.fingerprint(original), reviewer.fingerprint(changed))

    def test_event_bundle_duplicates_additions_and_removal_are_preserved(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        first = root + "\t\t- first() (src/Core.sol#3)\n"
        second = root + "\t\t- second() (src/Core.sol#4)\n"
        original = self.events([first, second])
        for bundles in ([first], [first, second, first], [first, second, root]):
            self.assertNotEqual(reviewer.fingerprint(original), reviewer.fingerprint(self.events(bundles)))

    def test_event_child_partition_cannot_change_between_identical_roots(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        a = "\t\t- first() (src/Core.sol#3)\n"
        b = "\t\t- second() (src/Core.sol#4)\n"
        self.assertNotEqual(reviewer.fingerprint(self.events([root+a, root+b])),
            reviewer.fingerprint(self.events([root+a+b, root])))

    def test_distinct_event_root_order_is_not_normalized(self):
        first = "\t- First(amount) (src/Core.sol#7)\n\t\t- first() (src/Core.sol#3)\n"
        second = "\t- Second(amount) (src/Core.sol#8)\n\t\t- second() (src/Core.sol#4)\n"
        self.assertNotEqual(reviewer.fingerprint(self.events([first, second])),
            reviewer.fingerprint(self.events([second, first])))

    def test_identical_event_roots_do_not_move_across_distinct_event(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        a = root + "\t\t- first() (src/Core.sol#3)\n"
        b = root + "\t\t- second() (src/Core.sol#4)\n"
        middle = "\t- Distinct(amount) (src/Core.sol#9)\n"
        self.assertNotEqual(reviewer.fingerprint(self.events([a, middle, b])),
            reviewer.fingerprint(self.events([b, middle, a])))

    def test_event_origin_cannot_move_to_a_distinct_event_root(self):
        a = "\t- First(amount) (src/Core.sol#7)\n"
        b = "\t- Second(amount) (src/Core.sol#8)\n"
        child = "\t\t- first() (src/Core.sol#3)\n"
        self.assertNotEqual(reviewer.fingerprint(self.events([a+child, b])),
            reviewer.fingerprint(self.events([a, b+child])))

    def test_tied_event_normalization_does_not_apply_to_other_sections(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        a = root + "\t\t- first() (src/Core.sol#3)\n"
        b = root + "\t\t- second() (src/Core.sol#4)\n"
        for section in ("State variables written after the call(s):", "External calls:"):
            self.assertNotEqual(reviewer.fingerprint(self.events([a, b], section=section)),
                reviewer.fingerprint(self.events([b, a], section=section)))

    def test_tied_event_normalization_does_not_apply_to_other_detectors(self):
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        a = root + "\t\t- first() (src/Core.sol#3)\n"
        b = root + "\t\t- second() (src/Core.sol#4)\n"
        for check in ("reentrancy-no-eth", "other-detector"):
            self.assertNotEqual(reviewer.fingerprint(self.events([a, b], check=check)),
                reviewer.fingerprint(self.events([b, a], check=check)))

    def test_event_section_boundary_preserves_following_state_write_order(self):
        original = self.events()
        a = "\t- firstState (src/Core.sol#5)\n"
        b = "\t- secondState (src/Core.sol#6)\n"
        suffix = "\tState variables written after the call(s):\n"
        self.assertNotEqual(reviewer.fingerprint(dict(original, description=original["description"]+suffix+a+b)),
            reviewer.fingerprint(dict(original, description=original["description"]+suffix+b+a)))

    def test_complete_review_accepts_tied_event_reorder_but_rejects_mutation(self):
        original = self.events()
        root = "\t- Emitted(amount) (src/Core.sol#8)\n"
        reordered = self.events([root+"\t\t- first() (src/Core.sol#3)\n",
            root+"\t\t- second() (src/Core.sol#4)\n"])
        self.review["findings"][0]["fingerprint"] = reviewer.fingerprint(original)
        self.report["results"]["detectors"] = [reordered]
        self.assertEqual(reviewer.check(self.report, self.review, self.root), [])
        self.report["results"]["detectors"] = [dict(reordered,
            description=reordered["description"].replace("first()", "withdraw()"))]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))


if __name__ == "__main__":
    unittest.main()
