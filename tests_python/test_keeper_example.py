"""The shipped current example cannot select retired intake or sign as-is."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from keeper.monitor import Keeper
from zzz_ops.rpc import RpcError


class KeeperExampleTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.cfg = json.loads((root / 'keeper/config.example.json').read_text())
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        for field in ('state_path', 'health_path', 'lock_path'):
            self.cfg[field] = str(Path(temporary.name) / Path(self.cfg[field]).name)
        self.rpc = Mock()
        self.rpc.call.side_effect = AssertionError('Example validation must not contact a chain')

    def test_example_selects_current_intake_without_retired_jobs(self):
        self.assertEqual(self.cfg['accounting_version'], 3)
        self.assertEqual(self.cfg['fee_intake_version'], 1)
        self.assertNotIn('sync_external_rewards', self.cfg['maintenance'])
        self.assertNotIn('reward_routes', self.cfg['maintenance'])
        self.assertFalse(self.cfg['reviewed_for_live_use'])
        self.assertFalse(self.cfg['maintenance']['compound'])
        self.assertFalse(self.cfg['maintenance']['compound_idle'])
        self.assertFalse(self.cfg['royalty_conversion']['enabled'])
        self.assertFalse(self.cfg['lp_conversion']['enabled'])
        self.assertEqual(self.cfg['code_hashes'], {})
        keeper = Keeper(self.cfg, rpc=self.rpc)
        self.assertFalse(keeper.live)
        self.assertEqual(keeper.state['accounting_version'], 3)
        self.assertEqual(keeper.state['fee_intake_version'], 1)
        self.assertFalse(keeper.path.exists())
        self.rpc.call.assert_not_called()

    def test_missing_deployment_review_and_pins_block_example(self):
        keeper = Keeper(self.cfg, rpc=self.rpc)
        with self.assertRaisesRegex(RpcError, 'reviewed Vault runtime pin'):
            keeper._validate_accounting_version()
        keeper.save()
        with self.assertRaisesRegex(ValueError, 'explicit reviewed deployment'):
            Keeper(self.cfg, live=True, rpc=self.rpc)
        self.rpc.call.assert_not_called()

    def test_reintroducing_creator_job_is_rejected_before_rpc(self):
        old = copy.deepcopy(self.cfg)
        old['maintenance']['sync_external_rewards'] = True
        with self.assertRaisesRegex(ValueError, 'creator-payment synchronization'):
            Keeper(old, rpc=self.rpc)
        self.rpc.call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
