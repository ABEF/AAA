"""New signer-output regressions using only the existing fresh7 submit fixture.

The normal validators, durable journal and pending-first recovery run. RPC and
Cast output remain inert; these methods do not qualify a Linux daemon or signer.
"""
import copy
import json
import subprocess
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_intent_shutdown as existing


class KeeperBroadcastHashTests(unittest.TestCase):
    def setUp(self):
        # Compose setup/helpers only: no old test method is inherited or run.
        self.fixture = existing.KeeperIntentShutdownTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.k, self.rpc = self.fixture.k, self.fixture.rpc

    def test_zero_signer_hash_preserves_reloadable_intent_and_never_resends(self):
        previous = copy.deepcopy(self.k.state)
        published = []

        def signer(command, **kwargs):
            published.append(self.k.path.read_bytes())
            self.assertIsNone(json.loads(published[-1])['pending']['hash'])
            return subprocess.CompletedProcess(command, 0, json.dumps(
                {'transactionHash': '0x' + '0' * 64}), '')

        with patch('keeper.monitor.subprocess.run', side_effect=signer) as send:
            with self.assertRaisesRegex(RuntimeError, 'Signer did not return a transaction hash'):
                self.fixture.submit()
        send.assert_called_once()
        self.assertEqual(len(published), 1)
        self.assertEqual(self.k.path.read_bytes(), published[0])
        self.assertIsNone(self.k.state['pending']['hash'])
        for field in ('next_nonce', 'spent', 'last', 'receipt_anchor'):
            self.assertEqual(self.k.state[field], previous[field])
        restored = Keeper(self.fixture.cfg, rpc=self.rpc)
        restored.live = True
        with patch('keeper.monitor.subprocess.run') as resend:
            self.assertFalse(self.fixture.submit(restored))
            restored.cycle()
            resend.assert_not_called()
        self.assertEqual(restored.state, self.k.state)
        self.assertEqual(restored.path.read_bytes(), published[0])

    def test_valid_mixed_case_signer_hash_is_normalized_without_changing_review(self):
        previous = copy.deepcopy(self.k.state)
        mixed = '0x' + 'Bc' * 32
        published = []

        def signer(command, **kwargs):
            published.append(json.loads(self.k.path.read_bytes()))
            return subprocess.CompletedProcess(command, 0, json.dumps({'hash': mixed}), '')

        with patch('keeper.monitor.subprocess.run', side_effect=signer) as send:
            self.assertTrue(self.fixture.submit())
        send.assert_called_once()
        final = json.loads(self.k.path.read_bytes())
        self.assertEqual(final, self.k.state)
        self.assertEqual(final['pending']['hash'], mixed.lower())
        for field in ('key', 'nonce', 'to', 'data', 'value', 'day', 'fee_review'):
            self.assertEqual(final['pending'][field], published[0]['pending'][field])
        for field in ('next_nonce', 'spent', 'last', 'receipt_anchor'):
            self.assertEqual(final[field], previous[field])
        restored = Keeper(self.fixture.cfg, rpc=self.rpc)
        self.assertEqual(restored.state, final)


if __name__ == '__main__':
    unittest.main()
