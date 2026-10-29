"""Metadata priority survives a discarded worker, using inert current4 RPC state.

The injected BaseException models loss of the process before another save; it
does not launch/kill a service or qualify actual watchdog timing.
"""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_rebalance_confirmation as fixtures
from zzz_ops.abi import calldata


class StoppedWorker(BaseException):
    pass


class KeeperMetadataRestartTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.KeeperConfirmationTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.cfg, self.rpc = self.f.cfg, self.f.rpc
        self.cfg['metadata_refresh'] = {'enabled': True, 'nft': '0x' + 'a4' * 20}
        self.cfg['code_hashes']['nft'] = self.f.f.pin
        # A due independent harvest, with principal inside its hard cooldown.
        self.cfg['maintenance'] = {'compound': False, 'harvest': True}
        self.f.base.group_words[6] = self.rpc.now
        self.k = Keeper(self.cfg, rpc=self.rpc)
        self.k.save()

    def test_discarded_worker_cannot_restart_metadata_ahead_of_every_due_harvest(self):
        with patch.object(self.k, '_refresh_metadata', side_effect=StoppedWorker), \
                patch.object(self.k, 'submit') as first_submit, \
                self.assertRaises(StoppedWorker):
            self.k.cycle()
        first_submit.assert_not_called()
        # Recreate the worker solely from the durable journal, not old memory.
        restarted = Keeper(self.cfg, rpc=self.rpc)
        with patch.object(restarted, '_refresh_metadata', side_effect=StoppedWorker) as metadata, \
                patch.object(restarted, 'submit', return_value=True) as submit:
            try:
                restarted.cycle()
            except StoppedWorker:
                self.fail('Restart selected the same blocked metadata before the due harvest')
        metadata.assert_not_called()
        self.assertEqual(submit.call_args.args[:2], ('vault', 'collectFees(uint256,uint256)'))
        self.assertEqual(submit.call_args.args[2][0], 7)

    def test_failed_priority_write_rolls_back_before_metadata_or_submission(self):
        save = self.k.save
        last_saved = copy.deepcopy(self.k.state)
        def guarded_save():
            nonlocal last_saved
            if self.k.state['metadata_refresh']['next_first'] is False:
                raise OSError('inert disk failure before optional metadata read')
            save()
            last_saved = copy.deepcopy(self.k.state)
        with patch.object(self.k, 'save', side_effect=guarded_save), \
                patch.object(self.k, '_refresh_metadata') as metadata, \
                patch.object(self.k, 'submit') as submit, self.assertRaises(OSError):
            self.k.cycle()
        metadata.assert_not_called()
        submit.assert_not_called()
        self.assertEqual(self.k.state, last_saved)
        self.assertEqual(json.loads(self.k.path.read_text()), last_saved)

    def test_pending_recovery_does_not_rotate_metadata_or_write_its_journal(self):
        self.k.state['next_nonce'] = 0
        self.k.state['pending'] = {'key': 'harvest:7', 'nonce': 0,
            'to': self.cfg['contracts']['vault'], 'data': calldata('collectFees(uint256,uint256)', 7, self.rpc.now + 180),
            'value': 0, 'day': '2026-10-29', 'hash': '0x' + 'ab' * 32,
            'fee_review': {'schema': 1, 'gas_limit': 100, 'max_fee_per_gas': 1,
                'l1_fee_allowance_wei': 0, 'maximum_cost_wei': 100, 'receipt_fee_policy': 'included'}}
        self.k._validate_state()
        self.k.save()
        before = copy.deepcopy(self.k.state)
        disk = self.k.path.read_bytes()
        with patch.object(self.k, 'save') as save, \
                patch.object(self.k, '_refresh_metadata') as metadata, \
                patch.object(self.k, 'submit') as submit:
            self.k.cycle()
        save.assert_not_called()
        metadata.assert_not_called()
        submit.assert_not_called()
        self.assertEqual(self.k.state, before)
        self.assertEqual(self.k.path.read_bytes(), disk)
