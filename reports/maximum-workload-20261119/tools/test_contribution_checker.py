"""NEW offline admission controls only; no node, compiler or application suite.

These controls exercise the exact checker parser and qualification boundaries.
They do not supply positive financial, gas or provider acceptance.
"""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("new_maximum_contribution_checker", HERE / "verify_contributions.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def word(value):
    return f"{value:064x}"


def dynamic(raw):
    return word(len(raw)) + raw.hex().ljust(((len(raw) + 31) // 32) * 64, "0")


def log(kind, data):
    event = next(event for event, name in checker.EVENTS.items() if name == kind)
    return {"address": "0x" + "f" * 40, "topics": [event], "data": "0x" + data}


def bindings():
    count = len(checker.ROLES)
    return log("bindings", word(64) + word(64 + 32 + 32 * count) + word(count) +
               "".join(word(i + 1) for i in range(count)) + word(count) +
               "".join(word(i + 101) for i in range(count)))


def call(label, cap=None, padding=None):
    contribution = label in checker.CASE_POLICY
    cap = (checker.CAP if contribution else 24_000_000) if cap is None else cap
    padding = (2000 if contribution else 2500) if padding is None else padding
    name = dynamic(label.encode())
    return log("call", word(320) + word(11) + word(22) + word(0) + word(320 + len(name) // 2) +
               word(cap) + word(padding) + word(123) + word(1) + word(456) + name + dynamic(b"\x12\x34"))


def complete_logs():
    rows = [bindings()]
    for label in (*checker.CASE_POLICY, *checker.MAINTENANCE_LABELS):
        rows.append(call(label))
        path = dynamic(b"/new/owned/exports/setup.setup.json")
        rows.append(log("baseline", word(64) + word(111) + path))
        rows.append(log("block", word(1) + word(2) + word(31337)))
        name = dynamic(label.encode())
        path = dynamic(("/new/owned/exports/" + label + ".json").encode())
        rows.append(log("state", word(96) + word(96 + len(name) // 2) + word(222) + name + path))
        if label in checker.MAINTENANCE_LABELS:
            expected = checker.MAINTENANCE_LABELS[label]
            output = dynamic(b"" if expected else bytes.fromhex("12345678"))
            rows.append(log("maintenance", word(288) + word(int(expected)) + word(288 + len(name) // 2) +
                            word(24_000_000) + word(2500) + word(1) + word(2) + word(333) + word(444) +
                            name + output))
    return rows


class NewColdContributionAdmissionTests(unittest.TestCase):
    def test_complete_known_export_set_and_maintenance_split(self):
        cases = checker.parse_logs(complete_logs())
        self.assertEqual(len(cases), 20)
        self.assertEqual(sum(case["workload_kind"] == "contribution" for case in cases), 12)
        self.assertEqual(sum(case["workload_kind"] == "maintenance" for case in cases), 8)
        for case in cases:
            if case["label"] in checker.MAINTENANCE_LABELS:
                self.assertEqual(case["expected_success"], checker.MAINTENANCE_LABELS[case["label"]])

    def test_cap_and_padding_forgery_are_refused(self):
        label = next(iter(checker.CASE_POLICY))
        for cap, padding in ((31_999_999, 2000), (96_000_000, 2000), (32_000_000, 1999), (32_000_000, 2500)):
            with self.subTest(cap=cap, padding=padding), self.assertRaises(AssertionError):
                checker.parse_logs([bindings(), call(label, cap, padding)])

    def test_unknown_or_invalid_export_label_is_refused(self):
        for label in ("unknown-positive", "max64-TWOLP-999-opening-eth", "../existing-chain", ""):
            with self.subTest(label=label), self.assertRaises(AssertionError):
                checker.parse_logs([bindings(), call(label)])

    def test_missing_maintenance_outcome_is_refused(self):
        logs = complete_logs()
        kind = next(event for event, name in checker.EVENTS.items() if name == "maintenance")
        with self.assertRaises(AssertionError):
            checker.parse_logs([row for row in logs if row["topics"] != [kind]])

    def exports_fixture(self, parsed, parsed_cases):
        raw = json.dumps(parsed).encode()
        return patch.multiple(checker, F=Path("/new/owned/producer99"), RAW_SHA256=checker.sha(raw), START={"source_before": {}}), \
            patch.object(checker, "load", return_value=(raw, parsed)), \
            patch.object(checker, "parse_logs", return_value=parsed_cases)

    def check_export_refusal(self, parsed, cases):
        context, loader, parser = self.exports_fixture(parsed, cases)
        with context, loader, parser, self.assertRaises(AssertionError):
            checker.exports()

    def test_zero_and_wrong_producer_methods_are_refused(self):
        cases = checker.parse_logs(complete_logs())
        host, method = checker.EXPECTED_METHOD.rsplit(":", 1)
        self.check_export_refusal({}, cases)
        wrong = {host: {"test_results": {"testUnreviewed()": {"status": "Success", "logs": []}}}}
        self.check_export_refusal(wrong, cases)
        failed = {host: {"test_results": {method: {"status": "Failure", "logs": []}}}}
        self.check_export_refusal(failed, cases)

    def test_missing_and_duplicate_cases_are_refused(self):
        cases = checker.parse_logs(complete_logs())
        host, method = checker.EXPECTED_METHOD.rsplit(":", 1)
        parsed = {host: {"test_results": {method: {"status": "Success", "logs": []}}}}
        self.check_export_refusal(parsed, cases[:-1])
        self.check_export_refusal(parsed, [*cases, copy.deepcopy(cases[0])])

    def test_exact_padding_threshold_and_invalid_estimates(self):
        self.assertEqual(checker.contribution_padding(26_666_666), (32_000_000, True))
        self.assertEqual(checker.contribution_padding(26_666_667), (32_000_001, False))
        self.assertEqual(checker.contribution_padding(21_000), (25_200, True))
        self.assertEqual(checker.contribution_padding(None), (None, False))
        for value in (True, 0, 20_999, -1, "26666666", 1 << 256):
            with self.subTest(value=value), self.assertRaises(AssertionError):
                checker.contribution_padding(value)

    def test_65_asset_count_and_distinct_native_first_identity(self):
        assets = [checker.ZERO, *("0x" + f"{i:040x}" for i in range(1, 65))]
        checker.validate_asset_inventory(65, 64, assets)
        for count, capacity, candidate in ((64, 64, assets), (65, 16, assets), (65, 64, assets[:-1]),
                                            (65, 64, [*assets[:-1], assets[1]]),
                                            (65, 64, [assets[1], assets[0], *assets[2:]])):
            with self.subTest(count=count, capacity=capacity), self.assertRaises(AssertionError):
                checker.validate_asset_inventory(count, capacity, candidate)

    def test_current_production_source_drift_refused_before_start_admission(self):
        original = Path.read_bytes
        target = checker.R / "src/ZZZVault.sol"
        def changed(path):
            return original(path) + b"// unreviewed drift\n" if path == target else original(path)
        with patch.object(Path, "read_bytes", changed), self.assertRaisesRegex(AssertionError, "differs from baseline"):
            checker.configure("producer99")

    def test_artifact_digest_drift_refused_without_running_a_node(self):
        baseline_raw, baseline = checker.load(checker.E / "BASELINE.json")
        excluded = {"src/ZZZAccessController.sol", "src/ZZZPoolRegistry.sol", "src/ZZZPythPriceFeed.sol"}
        before = {name: pin for name, pin in baseline["source_sha256"].items() if name not in excluded}
        stage = checker.E / "producer99"
        start = {"normal_build": baseline["normal_build"], "baseline_main": baseline["baseline_main"],
                 "method": checker.EXPECTED_METHOD.split(":")[-1], "source_before": before}
        execution = {"pass": True, "exit_code": 0, "error": None, "compiled_source_metadata_verified": True,
                     "source_bracket_stable": True, "tracked_config_unchanged": True, "source_after": before,
                     "artifact_sha256": "0" * 64}
        def fake_load(path):
            path = Path(path)
            if path == checker.E / "BASELINE.json":
                return baseline_raw, baseline
            data = start if path.name == "START.json" else execution if path.name == "EXECUTION.json" else {"metadata": {}}
            return json.dumps(data).encode(), data
        with patch.object(checker, "load", side_effect=fake_load), self.assertRaisesRegex(AssertionError, "artifact digest drift"):
            checker.configure("producer99")


class NewGrowthRecheckControls(unittest.TestCase):
    def test_growth_accepts_zero_remaining_compound_with_funded_rewards(self):
        row = checker.compound_prestate(0, 123, True)
        self.assertEqual(row["compound_reserve"], 0)
        self.assertEqual(row["funded_lp_reward_liability"], 123)
        self.assertTrue(row["zero_compound_allowed_after_prior_entry"])
        self.assertEqual(checker.compound_prestate(17, 123, True)["compound_reserve"], 17)

    def test_activation_retains_positive_compound_requirement_and_typed_cause(self):
        self.assertEqual(checker.compound_prestate(17, 123, False)["compound_reserve"], 17)
        with self.assertRaises(checker.QualificationError) as error:
            checker.compound_prestate(0, 123, False)
        self.assertEqual(error.exception.stage, "physical_portfolio.fee_prestate")
        self.assertIn("Activation fixture", error.exception.cause)

    def test_growth_still_requires_funded_lp_liability(self):
        for compound in (0, 17):
            with self.subTest(compound=compound), self.assertRaises(checker.QualificationError) as error:
                checker.compound_prestate(compound, 0, True)
            self.assertIn("reward liability", error.exception.cause)

    def test_invalid_fee_categories_are_rejected(self):
        for compound, liability in ((True, 17), (-1, 17), (0, -1), (0, "17")):
            with self.subTest(compound=compound, liability=liability), self.assertRaises(checker.QualificationError):
                checker.compound_prestate(compound, liability, True)

    def test_affected_selection_still_requires_complete_twenty_export_set(self):
        cases = checker.parse_logs(complete_logs())
        chosen, maintenance, skipped, name = checker.select_contribution_cases(
            cases, list(checker.GROWTH_RECHECK_LABELS), "growth-recheck01")
        self.assertEqual({case["label"] for case in chosen}, set(checker.GROWTH_RECHECK_LABELS))
        self.assertEqual(len(chosen), 3)
        self.assertEqual(len(maintenance), 8)
        self.assertEqual(len(skipped), 9)
        self.assertEqual(name, "cold-contributions-growth-recheck01")
        self.assertEqual(len(checker.select_contribution_cases(cases)[0]), 12)
        for broken in (cases[:-1], [*cases, copy.deepcopy(cases[0])]):
            with self.assertRaises(checker.QualificationError):
                checker.select_contribution_cases(broken, list(checker.GROWTH_RECHECK_LABELS), "growth-recheck01")

    def test_recheck_options_reject_paths_duplicates_and_unchanged_activation_cases(self):
        labels = list(checker.GROWTH_RECHECK_LABELS)
        for only, tag in ((labels, None), (labels, "../old"), (labels, "bad/path"),
                          (labels, "bad\\path"), (labels, "UPPER"), (labels, "."),
                          (labels, "a" * 49), (None, "unexpected-tag"),
                          ([labels[0], labels[0]], "new"),
                          ([next(iter(checker.CASE_POLICY))], "new"), ([], "new")):
            with self.subTest(only=only, tag=tag), self.assertRaises(checker.QualificationError):
                checker.validate_selection_options(only, tag)


if __name__ == "__main__":
    unittest.main(verbosity=2)
