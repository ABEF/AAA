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

    def write_bundles(self):
        positions = ("\tCore.positions (src/Core.sol#1) can be used in cross function reentrancies:\n"
            "\t- Core.confirm(uint256) (src/Core.sol#20-22)\n"
            "\t- Core.group(uint256) (src/Core.sol#23)\n")
        total = ("\tCore.totalIdle (src/Core.sol#2) can be used in cross function reentrancies:\n"
            "\t- Core.totalIdle (src/Core.sol#2)\n")
        return [
            "\t- _compound(bucket) (src/Core.sol#6)\n"
            "\t\t- p.idle0 = new0 (src/Core.sol#10)\n"
            "\t\t- p.idle1 = new1 (src/Core.sol#11)\n" + positions,
            "\t- _idle(bucket,new0,new1) (src/Core.sol#7)\n"
            "\t\t- p.idle0 = new0 (src/Core.sol#10)\n"
            "\t\t- p.idle1 = new1 (src/Core.sol#11)\n" + positions,
            "\t- _idle(bucket,new0,new1) (src/Core.sol#7)\n"
            "\t\t- totalIdle[token0] = new0 (src/Core.sol#8)\n"
            "\t\t- totalIdle[token1] = new1 (src/Core.sol#9)\n" + total,
        ]

    def grouped_finding(self, bundles):
        return dict(self.finding, check="reentrancy-no-eth", description=
            "Reentrancy in Core.join(uint256) (src/Core.sol#3-19):\n"
            "\tExternal calls:\n\t- fees.sync() (src/Core.sol#4)\n"
            "\t- _harvest(bucket) (src/Core.sol#5)\n"
            "\t\t- manager.collect(bucket) (src/Core.sol#15)\n"
            "\t\t- fees.allocate(bucket) (src/Core.sol#16)\n"
            "\tState variables written after the call(s):\n" + "".join(bundles))

    def set_grouped_review(self, findings):
        self.review["findings"] = [dict(finding, fingerprint=reviewer.fingerprint(finding),
            comparison=reviewer.WRITE_BUNDLES, disposition="false_positive",
            rationale="Reviewed guarded calls and each write/cross-function bundle") for finding in findings]

    def test_opted_in_write_bundles_match_split_and_merged_same_build_reports(self):
        a, b, c = self.write_bundles()
        merged = self.grouped_finding([a, b, c])
        split = [self.grouped_finding([b, c]), self.grouped_finding([a])]
        for canonical, incoming in (([merged], split), (split, [merged])):
            with self.subTest(canonical_count=len(canonical)):
                self.set_grouped_review(canonical)
                self.report["results"]["detectors"] = incoming
                self.assertEqual(reviewer.check(self.report, self.review, self.root), [])

    def test_write_regrouping_requires_explicit_per_entry_opt_in(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        del self.review["findings"][0]["comparison"]
        self.report["results"]["detectors"] = [self.grouped_finding([b, c]), self.grouped_finding([a])]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_reviewed_description_must_reconstruct_fingerprint_even_on_exact_hit(self):
        self.review["findings"][0].update(self.finding)
        self.review["findings"][0]["description"] += "unreviewed change\n"
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_unknown_comparison_wrong_detector_and_missing_description_fail(self):
        original = self.grouped_finding(self.write_bundles())
        for mutation in ("unknown", "wrong-detector", "missing-description"):
            with self.subTest(mutation=mutation):
                self.set_grouped_review([original])
                self.report["results"]["detectors"] = [original]
                entry = self.review["findings"][0]
                if mutation == "unknown":
                    entry["comparison"] = "future-unreviewed-normalization"
                elif mutation == "wrong-detector":
                    entry["check"] = "reentrancy-events"
                    entry["fingerprint"] = reviewer.fingerprint(entry)
                    self.report["results"]["detectors"] = [entry]
                else:
                    del entry["description"]
                self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_write_bundle_order_can_change_but_multiplicity_cannot(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        for bundles in ([c, a, b], [a, b], [a, b, c, a], [a, a, c]):
            self.report["results"]["detectors"] = [self.grouped_finding(bundles)]
            errors = reviewer.check(self.report, self.review, self.root)
            self.assertEqual(not errors, bundles == [c, a, b])

    def test_write_regrouping_preserves_all_call_context_expressions_and_locations(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        split = [self.grouped_finding([b, c]), self.grouped_finding([a])]
        replacements = (("fees.sync()", "fees.withdraw()"), ("#4)", "#24)"),
            ("manager.collect(bucket)", "manager.collect(other)"), ("#15)", "#25)"),
            ("Core.join(uint256)", "Core.exit(uint256)"), ("#3-19)", "#3-29)"))
        for old, new in replacements:
            with self.subTest(old=old, new=new):
                self.report["results"]["detectors"] = [split[0], dict(split[1],
                    description=split[1]["description"].replace(old, new))]
                self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_write_regrouping_keeps_external_root_order_and_parentage(self):
        original = self.grouped_finding(self.write_bundles())
        self.set_grouped_review([original])
        description = original["description"]
        first = "\t- fees.sync() (src/Core.sol#4)\n"
        parent = "\t- _harvest(bucket) (src/Core.sol#5)\n"
        children = ("\t\t- manager.collect(bucket) (src/Core.sol#15)\n"
            "\t\t- fees.allocate(bucket) (src/Core.sol#16)\n")
        for changed in (description.replace(first+parent+children, parent+children+first),
                description.replace(first+parent+children, first+children+parent)):
            self.report["results"]["detectors"] = [dict(original, description=changed)]
            self.assertTrue(reviewer.check(self.report, self.review, self.root))
        reordered = children.splitlines(keepends=True)
        self.report["results"]["detectors"] = [dict(original,
            description=description.replace(children, "".join(reversed(reordered))))]
        self.assertEqual(reviewer.check(self.report, self.review, self.root), [])

    def test_write_regrouping_preserves_external_call_multiplicity(self):
        original = self.grouped_finding(self.write_bundles())
        self.set_grouped_review([original])
        root = "\t- fees.sync() (src/Core.sol#4)\n"
        child = "\t\t- manager.collect(bucket) (src/Core.sol#15)\n"
        for description in (original["description"].replace(root, root+root),
                original["description"].replace(child, child+child),
                original["description"].replace(child, "")):
            self.report["results"]["detectors"] = [dict(original, description=description)]
            self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_write_regrouping_preserves_root_child_order_and_deeper_parentage(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        child0 = "\t\t- p.idle0 = new0 (src/Core.sol#10)\n"
        child1 = "\t\t- p.idle1 = new1 (src/Core.sol#11)\n"
        for altered in (a.replace("_compound(bucket)", "_different(bucket)"),
                a.replace("#6)", "#26)"), a.replace("new0", "other0"),
                a.replace("#10)", "#30)"), a.replace(child0+child1, child1+child0),
                a.replace(child1, child1+child1), a.replace(child0, "")):
            with self.subTest(altered=altered):
                self.report["results"]["detectors"] = [self.grouped_finding([altered, b, c])]
                self.assertTrue(reviewer.check(self.report, self.review, self.root))
        a_deep = a.replace(child0, child0+"\t\t\t- inner() (src/Core.sol#12)\n")
        self.set_grouped_review([self.grouped_finding([a_deep, b, c])])
        detached = a.replace(child1, child1+"\t\t\t- inner() (src/Core.sol#12)\n")
        self.report["results"]["detectors"] = [self.grouped_finding([detached, b, c])]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_write_child_partition_cannot_change_between_identical_roots(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        child = "\t\t- p.idle1 = new1 (src/Core.sol#11)\n"
        altered = [a.replace(child, ""), b.replace(child, child+child), c]
        self.report["results"]["detectors"] = [self.grouped_finding(altered)]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_cross_function_paragraph_content_order_locations_and_duplicates_preserved(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        confirm = "\t- Core.confirm(uint256) (src/Core.sol#20-22)\n"
        group = "\t- Core.group(uint256) (src/Core.sol#23)\n"
        for altered in (a.replace("Core.positions", "Core.other"),
                a.replace("#1)", "#31)"), a.replace("Core.confirm", "Core.destroy"),
                a.replace("#20-22)", "#30-32)"),
                a.replace(confirm, ""), a.replace(group, group+group),
                a.replace(confirm+group, group+confirm)):
            self.report["results"]["detectors"] = [self.grouped_finding([altered, b, c])]
            self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_cross_function_paragraph_cannot_move_to_different_write_root(self):
        a, b, c = self.write_bundles()
        self.set_grouped_review([self.grouped_finding([a, b, c])])
        a_root, a_cross = a.split("\tCore.positions", 1)
        c_root, c_cross = c.split("\tCore.totalIdle", 1)
        self.report["results"]["detectors"] = [self.grouped_finding([
            a_root+"\tCore.totalIdle"+c_cross, b, c_root+"\tCore.positions"+a_cross])]
        self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_write_regrouping_rejects_unknown_shape_even_when_exactly_reviewed(self):
        a, b, c = self.write_bundles()
        original = self.grouped_finding([a, b, c])
        descriptions = [original["description"]+"\tFuture section:\n",
            original["description"].replace("\tExternal calls:\n", "\tOther calls:\n"),
            original["description"].replace("\t\t- p.idle0 = new0 (src/Core.sol#10)\n", "").replace(
                "\t\t- p.idle1 = new1 (src/Core.sol#11)\n", ""),
            original["description"].replace(" can be used in cross function reentrancies:", " changed syntax:"),
            original["description"].replace("\t- Core.confirm", "\t\t- Core.confirm"),
            original["description"]+"\n"]
        for description in descriptions:
            with self.subTest(description=description):
                changed = dict(original, description=description)
                self.set_grouped_review([changed])
                self.report["results"]["detectors"] = [changed]
                self.assertTrue(reviewer.check(self.report, self.review, self.root))

    def test_grouped_matches_still_require_source_disposition_rationale_and_severity(self):
        a, b, c = self.write_bundles()
        canonical = self.grouped_finding([a, b, c])
        split = [self.grouped_finding([b, c]), self.grouped_finding([a])]
        for mutation in ("source", "disposition", "rationale", "impact", "confidence"):
            with self.subTest(mutation=mutation):
                self.set_grouped_review([canonical])
                self.report["results"]["detectors"] = [dict(finding) for finding in split]
                if mutation == "source":
                    (self.root / "src/Core.sol").write_text("drift\n")
                elif mutation == "disposition":
                    self.review["findings"][0]["disposition"] = "unresolved"
                elif mutation == "rationale":
                    self.review["findings"][0]["rationale"] = " "
                else:
                    self.report["results"]["detectors"][0][mutation] = "Low"
                self.assertTrue(reviewer.check(self.report, self.review, self.root))
                (self.root / "src/Core.sol").write_text("reviewed\n")

    def test_grouped_matches_cannot_hide_other_new_stale_or_duplicate_findings(self):
        a, b, c = self.write_bundles()
        canonical = self.grouped_finding([a, b, c])
        split = [self.grouped_finding([b, c]), self.grouped_finding([a])]
        for mutation in ("new", "stale", "duplicate-analyzer", "duplicate-review", "mixed-context"):
            with self.subTest(mutation=mutation):
                self.set_grouped_review([canonical])
                self.report["results"]["detectors"] = list(split)
                if mutation == "new":
                    self.report["results"]["detectors"].append(self.finding)
                elif mutation == "stale":
                    self.review["findings"].append(dict(self.finding, fingerprint=reviewer.fingerprint(self.finding),
                        disposition="accepted_risk", rationale="Unchanged exact review"))
                elif mutation == "duplicate-analyzer":
                    self.report["results"]["detectors"].append(split[0])
                elif mutation == "duplicate-review":
                    self.review["findings"].append(dict(self.review["findings"][0]))
                else:
                    self.review["findings"].append(dict(split[0], fingerprint=reviewer.fingerprint(split[0]),
                        disposition="accepted_risk", rationale="Ambiguous exact context"))
                self.assertTrue(reviewer.check(self.report, self.review, self.root))


if __name__ == "__main__":
    unittest.main()
