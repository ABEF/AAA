"""Safety boundaries for the isolated local-only build generator."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dollar_rehearsal', ROOT/'scripts/prepare-dollar-rehearsal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DollarRehearsalTests(unittest.TestCase):
    def test_only_two_sources_transform_and_preserve_deployment_budget(self):
        changed = []
        for source in (ROOT/'src').rglob('*.sol'):
            name = source.relative_to(ROOT).as_posix()
            before = source.read_bytes(); after = module.transform(name, before)
            if before != after:
                changed.append(name)
                self.assertIn(b'LOCAL_REHEARSAL_ONLY', after)
                self.assertIn(b'block.chainid == 31337', after)
        self.assertEqual(set(changed), set(module.PATCHES))
        budget = module.transform('src/ZZZMigrationBudget.sol', (ROOT/'src/ZZZMigrationBudget.sol').read_bytes())
        self.assertIn(b'uint256 minimumNet = inputUSD - inputUSD / 100;', budget)

    def test_missing_or_duplicated_anchor_fails_closed(self):
        for name, replacements in module.PATCHES.items():
            source = (ROOT/name).read_bytes()
            for anchor, _ in replacements:
                with self.assertRaises(ValueError):
                    module.transform(name, source.replace(anchor.encode(), b'changed', 1))
                with self.assertRaises(ValueError):
                    module.transform(name, source + anchor.encode())

    def test_repository_and_ancestor_output_are_rejected(self):
        for output in (ROOT, ROOT/'tmp-rehearsal', ROOT.parent):
            with self.assertRaises(ValueError):
                module.validate_destination(ROOT, output)

    def test_existing_external_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                module.validate_destination(ROOT, Path(tmp))
            self.assertEqual(module.validate_destination(ROOT, Path(tmp)/'new'), (Path(tmp)/'new').resolve())


if __name__ == '__main__':
    unittest.main()
