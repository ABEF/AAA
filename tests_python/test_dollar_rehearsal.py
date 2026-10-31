"""Safety boundaries for the isolated local-only build generator."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dollar_rehearsal', ROOT/'scripts/prepare-dollar-rehearsal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DollarRehearsalTests(unittest.TestCase):
    @staticmethod
    def legacy_source(name):
        # Explicit generator-only legacy anchors, not current Solidity/runtime
        # qualification. Missing/duplicate anchors are separately rejected below.
        return ('// TEST ONLY historical generator fixture\n'+
                '\n'.join(before for before,_ in module.PATCHES[name])).encode('utf-8')

    def test_legacy_only_two_sources_transform_and_preserve_deployment_budget(self):
        changed = []
        sources={name:self.legacy_source(name) for name in module.PATCHES}
        sources['src/ZZZMigrationBudget.sol']=(ROOT/'src/ZZZMigrationBudget.sol').read_bytes()
        for name,before in sources.items():
            after = module.transform(name, before)
            if before != after:
                changed.append(name)
                self.assertIn(b'LOCAL_REHEARSAL_ONLY', after)
                self.assertIn(b'block.chainid == 31337', after)
        self.assertEqual(set(changed), set(module.PATCHES))
        self.assertEqual(set(module.PATCHES),{'src/ZZZActivationEntry.sol','src/ZZZVaultCanonical.sol'})
        for name in module.PATCHES:
            source=self.legacy_source(name)
            expected=source.decode('utf-8')
            for before,after in module.PATCHES[name]:expected=expected.replace(before,after,1)
            self.assertEqual(module.transform(name,source),expected.encode('utf-8'))
        source=(ROOT/'src/ZZZMigrationBudget.sol').read_bytes()
        self.assertEqual(module.loss_policy(source),module.loss_policy(module.transform('src/ZZZMigrationBudget.sol',source)))

    def minimal_repository(self, parent, budget):
        # Generator-only fixture: no Solidity compilation/provider qualification.
        root=parent/'repository'
        for name in module.PATCHES:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(self.legacy_source(name))
        (root/'src/ZZZVault.sol').write_text('uint256 public constant ACCOUNTING_VERSION = 5;\n',encoding='utf-8')
        (root/'src/ZZZMigrationBudget.sol').write_bytes(budget)
        for name in ('test/AtomicActivationIntegration.t.sol','rehearsal/one-dollar/DollarActivation.t.sol'):
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('// isolated generator fixture; no imports or execution\n',encoding='utf-8')
        solc=parent/'solc.fixture';solc.write_bytes(b'not executed by generator tests')
        return root,solc

    def test_manifest_uses_actual_source_defaults_without_rewriting_policy(self):
        original=(ROOT/'src/ZZZMigrationBudget.sol').read_bytes()
        default,maximum=module.loss_policy(original)
        changed=original.replace(f'contributionLossBps = {default};'.encode(),b'contributionLossBps = 250;').replace(
            f'MAX_LOSS_BPS = {maximum};'.encode(),b'MAX_LOSS_BPS = 750;')
        for budget,expected in ((original,(default,maximum)),(changed,(250,750))):
            with self.subTest(expected=expected),tempfile.TemporaryDirectory() as tmp:
                parent=Path(tmp);root,solc=self.minimal_repository(parent,budget);output=parent/'generated'
                manifest=module.prepare(root,output,solc)
                self.assertEqual((manifest['execution_loss_bps'],manifest['maximum_execution_loss_bps']),expected)
                generated=(output/'src/ZZZMigrationBudget.sol').read_bytes()
                self.assertEqual(generated,budget)
                self.assertEqual(module.loss_policy(generated),expected)
                self.assertEqual((root/'src/ZZZMigrationBudget.sol').read_bytes(),budget)
                self.assertIn('individual test fixtures',manifest['execution_loss_scope'])

    def test_unknown_duplicate_or_false_policy_is_rejected_before_output(self):
        original=(ROOT/'src/ZZZMigrationBudget.sol').read_bytes()
        default,maximum=module.loss_policy(original)
        anchor=f'uint16 public contributionLossBps = {default};'.encode()
        variants=(original.replace(anchor,b'uint16 public contributionLossBps = uint16(200);'),
            original.replace(anchor,b'uint16 public contributionLossBps = 100 + 100;'),
            original.replace(anchor,b'uint16 public contributionLossBps = 0200;'),
            original.replace(anchor,b'uint256 public contributionLossBps = 200;'),
            original.replace(anchor,b'uint16 public contributionLossBps;'),
            original+b'\nuint16 private contributionLossBps;\n',
            original+b'\nuint16 public constant MAX_LOSS_BPS = 1000;\n',
            original.replace(f'MAX_LOSS_BPS = {maximum};'.encode(),b'MAX_LOSS_BPS = 1001;'),
            original.replace(anchor,b'// uint16 public contributionLossBps = 200;'),
            original.replace(anchor,f'uint16 public contributionLossBps = {maximum+1};'.encode()))
        for index,budget in enumerate(variants):
            with self.subTest(index=index),tempfile.TemporaryDirectory() as tmp:
                parent=Path(tmp);root,solc=self.minimal_repository(parent,budget);output=parent/'generated'
                with self.assertRaises(ValueError):module.prepare(root,output,solc)
                self.assertFalse(output.exists())

    def test_comments_and_string_literals_cannot_supply_or_duplicate_policy(self):
        original=(ROOT/'src/ZZZMigrationBudget.sol').read_bytes()
        expected=module.loss_policy(original)
        misleading=(b'\n// uint16 public contributionLossBps = 1;\n'
            b'/* uint16 public constant MAX_LOSS_BPS = 2; */\n'
            b'string constant ignored = "uint16 public contributionLossBps = 3;";\n')
        self.assertEqual(module.loss_policy(original+misleading),expected)

    def test_missing_or_duplicated_anchor_fails_closed(self):
        for name, replacements in module.PATCHES.items():
            source = self.legacy_source(name)
            for anchor, _ in replacements:
                with self.assertRaises(ValueError):
                    module.transform(name, source.replace(anchor.encode(), b'changed', 1))
                with self.assertRaises(ValueError):
                    module.transform(name, source + anchor.encode())

    def test_fresh_profile_refuses_before_compiler_fixture_walk_or_source_changes(self):
        names=('src/ZZZProtocolPolicy.sol','src/ZZZVault.sol','src/ZZZActivationEntry.sol','src/ZZZMigrationBudget.sol')
        before={name:(ROOT/name).read_bytes() for name in names}
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp);output=parent/'must-not-exist';missing_solc=parent/'missing-solc'
            with (patch.object(module,'transform',side_effect=AssertionError('must not transform')),
                  patch.object(module,'loss_policy',side_effect=AssertionError('must not inspect/copy full inputs'))):
                with self.assertRaisesRegex(ValueError,'ProtocolPolicy.setEntryPolicy'):
                    module.prepare(ROOT,output,missing_solc)
            self.assertFalse(output.exists());self.assertFalse(missing_solc.exists())
            self.assertEqual(list(parent.iterdir()),[])
        self.assertEqual(before,{name:(ROOT/name).read_bytes() for name in names})

    def test_fresh_or_future_accounting_marker_alone_cannot_bypass_refusal(self):
        for version in (6,7):
            with self.subTest(version=version),tempfile.TemporaryDirectory() as tmp:
                parent=Path(tmp);root=parent/'repository';(root/'src').mkdir(parents=True)
                (root/'src/ZZZVault.sol').write_text(
                    f'uint256 public constant ACCOUNTING_VERSION = {version};\n',encoding='utf-8')
                output=parent/'must-not-exist'
                with self.assertRaisesRegex(ValueError,'legacy source patches are disabled'):
                    module.prepare(root,output,parent/'missing-solc')
                self.assertFalse(output.exists())

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
