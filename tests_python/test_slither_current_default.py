"""Current CI static-review admission, without executing old contract suites."""
import copy
import gzip
import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("current_slither_default", ROOT / "scripts/check-slither-review.py")
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


class CurrentSlitherDefaultTests(unittest.TestCase):
    def current_inputs(self):
        review = json.loads(reviewer.DEFAULT_REVIEW.read_text(encoding="utf-8"))
        projection = review["scope"]["strict_input_projection"]
        compressed = (ROOT / projection["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), projection["gzip_sha256"])
        data = gzip.decompress(compressed)
        self.assertEqual(hashlib.sha256(data).hexdigest(), projection["decompressed_sha256"])
        report = json.loads(data)
        self.assertTrue(review["scope"]["actual_analyzer"])
        self.assertFalse(review["scope"]["compiler_invoked_by_analyzer"])
        self.assertEqual(report["projection"]["detector_count"], len(report["results"]["detectors"]))
        self.assertEqual(len(review["findings"]), len(report["results"]["detectors"]))
        return report, review

    def test_ci_uses_current_default_and_complete_actual_projection(self):
        workflow = (ROOT / ".github/workflows/verify.yml").read_text(encoding="utf-8")
        shell = (ROOT / "scripts/verify-slither.sh").read_text(encoding="utf-8")
        self.assertIn("- run: bash scripts/verify-slither.sh", workflow)
        joined = re.sub(r"\\\r?\n\s*", " ", shell)
        self.assertIn('python3 scripts/check-slither-review.py "$evidence_dir/slither-current.json"', joined)
        self.assertNotIn("--review", joined)
        report, review = self.current_inputs()
        self.assertEqual(reviewer.check(report, review), [])
        for finding in review["findings"]:
            self.assertEqual(reviewer.fingerprint(finding), finding["fingerprint"])
            self.assertTrue(finding["description"].strip())

    def test_default_refuses_prior_source_and_detector_drift(self):
        report, review = self.current_inputs()
        prior = json.loads((ROOT / review["scope"]["prior_review"]).read_bytes())
        self.assertTrue(reviewer.check(report, prior))
        added = copy.deepcopy(report)
        extra = copy.deepcopy(added["results"]["detectors"][0])
        extra["description"] += "\nUnreviewed detector context\n"
        added["results"]["detectors"].append(extra)
        self.assertTrue(reviewer.check(added, review))
        missing = copy.deepcopy(report)
        missing["results"]["detectors"].pop()
        self.assertTrue(reviewer.check(missing, review))
        with tempfile.TemporaryDirectory(prefix="popl-static-default-") as temp:
            root = Path(temp)
            for name in review["source_sha256_lf"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            self.assertEqual(reviewer.check(report, review, root), [])
            changed = review["scope"]["changed_since_prior_review"]
            self.assertTrue(changed)
            for name in changed:
                path = root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n// unreviewed source drift\n")
                self.assertIn("Reviewed content changed: " + name, reviewer.check(report, review, root))
                path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
