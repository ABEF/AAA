"""Canonical own-receipt harvest clocks; inert RPCs and temporary journals only."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_fees as fixtures
from tests_python import test_keeper_outside_schedule as schedule_fixtures
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError

TOPIC = '0x' + keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
OTHER = '0x' + 'ab' * 20


class KeeperHarvestCoalescingTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.KeeperSignedFeeTests('runTest')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.rpc = self.f.rpc
        self.cfg = copy.deepcopy(self.f.cfg)
        self.cfg.update(accounting_version=4, fee_intake_version=1,
                        state_path=str(Path(self.f.tmp.name) / 'current.json'))
        self.cfg['contracts']['principal_exit'] = OTHER
        self.k = Keeper(self.cfg, rpc=self.rpc)
        self.k.state.update(next_nonce=7, pending=copy.deepcopy(self.f.k.state['pending']))
        self.k.state['last'] = {'harvest:1': self.rpc.now - 4000,
                               'harvest:2': self.rpc.now - 5000,
                               'rebalance:1': self.rpc.now - 43200,
                               'compound:1': self.rpc.now - 3600}
        self.prepare('compound')

    def prepare(self, action):
        pending = self.k.state['pending']
        signature = action + '(uint256,uint128,uint256)'
        pending.update(key=action + ':1', to=self.k.contracts['compounder' if action == 'compound' else 'vault'],
                       data=calldata(signature, 1, 1, self.rpc.now + 180), value=0)
        pending['fee_review']['maximum_cost_wei'] = 2560
        self.rpc.tx.update(to=pending['to'], input=pending['data'], value='0x0')
        self.rpc.receipt.update(to=pending['to'], logs=[self.event()])
        self.k.save()

    def event(self, bucket=1, *, amount0=0, amount1=0, index=0):
        return {'address': self.k.contracts['vault'], 'topics': [TOPIC, '0x' + f'{bucket:064x}'],
                'data': '0x' + f'{amount0:064x}{amount1:064x}',
                'blockNumber': '0x63', 'blockHash': fixtures.H,
                'transactionHash': fixtures.H, 'transactionIndex': '0x0',
                'logIndex': hex(index), 'removed': False}

    def confirm(self):
        with patch('subprocess.run') as signer:
            self.assertFalse(self.k.poll_pending())
        signer.assert_not_called()
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(8, self.k.state['next_nonce'])
        self.assertEqual(500, sum(self.k.state['spent'].values()))
        self.assertEqual(self.k.state, json.loads(self.k.path.read_bytes()))

    def test_compound_receipt_coalesces_only_its_actual_bucket_harvest(self):
        before = copy.deepcopy(self.k.state['last'])
        self.rpc.receipt['logs'] = [self.event(amount0=7, amount1=11), self.event(index=3)]
        self.confirm()
        self.assertEqual(self.rpc.now, self.k.state['last']['harvest:1'])
        self.assertEqual(self.rpc.now, self.k.state['last']['compound:1'])
        self.assertEqual(before['rebalance:1'], self.k.state['last']['rebalance:1'])
        self.assertEqual(before['harvest:2'], self.k.state['last']['harvest:2'])

    def test_rebalance_receipt_coalesces_harvest_without_advancing_compound(self):
        self.prepare('rebalance')
        old = self.k.state['last']['compound:1']
        self.confirm()
        self.assertEqual(self.rpc.now, self.k.state['last']['harvest:1'])
        self.assertEqual(self.rpc.now, self.k.state['last']['rebalance:1'])
        self.assertEqual(old, self.k.state['last']['compound:1'])

    def test_zero_fees_still_prove_a_collection_and_omitted_removed_is_supported(self):
        self.rpc.receipt['logs'][0].pop('removed')
        self.confirm()
        self.assertEqual(self.rpc.now, self.k.state['last']['harvest:1'])

    def test_historical_accounting_profiles_keep_their_existing_clock(self):
        for version in (1, 2, 3):
            with self.subTest(version=version):
                self.setUp()
                cfg = copy.deepcopy(self.cfg)
                cfg.update(accounting_version=version, fee_intake_version=0 if version==1 else 1,
                           state_path=str(Path(self.f.tmp.name) / 'historical.json'))
                historical = Keeper(cfg, rpc=self.rpc)
                historical.state.update(next_nonce=7, pending=copy.deepcopy(self.k.state['pending']),
                                        last=copy.deepcopy(self.k.state['last']))
                self.k = historical
                self.k.save()
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_absent_empty_or_malformed_log_array_does_not_strand_paid_recovery(self):
        for logs in ('absent', [], None, {}, 'invalid'):
            with self.subTest(logs=logs):
                self.setUp()
                if logs == 'absent': self.rpc.receipt.pop('logs')
                else: self.rpc.receipt['logs'] = logs
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_foreign_emitter_bucket_or_signature_never_proves_our_harvest(self):
        for change in ({'address': OTHER}, {'topics': [TOPIC, '0x' + f'{2:064x}']},
                       {'topics': ['0x' + '23' * 32, '0x' + f'{1:064x}']}):
            with self.subTest(change=change):
                self.setUp(); self.rpc.receipt['logs'][0].update(change)
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_matching_event_must_have_exact_abi_and_inclusion_envelope(self):
        changes = ({'data': '0x'}, {'topics': [TOPIC]}, {'removed': True},
                   {'removed': None}, {'removed': 0}, {'blockNumber': '0x62'},
                   {'blockHash': '0x' + '45' * 32}, {'transactionHash': '0x' + '67' * 32},
                   {'transactionIndex': '0x1'}, {'logIndex': '0x00'})
        for change in changes:
            with self.subTest(change=change):
                self.setUp(); self.rpc.receipt['logs'][0].update(change)
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_duplicate_or_contradictory_matching_event_does_not_partially_advance_clock(self):
        for second in (self.event(), {**self.event(index=1), 'data': '0x'}):
            with self.subTest(second=second):
                self.setUp(); self.rpc.receipt['logs'].append(second)
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_missing_log_inclusion_fields_leave_only_the_harvest_optimization_unverified(self):
        for field in ('blockNumber', 'blockHash', 'transactionHash', 'transactionIndex', 'logIndex'):
            with self.subTest(field=field):
                self.setUp(); self.rpc.receipt['logs'][0].pop(field)
                old = self.k.state['last']['harvest:1']
                self.confirm()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_action_identity_must_match_target_and_static_bucket_calldata(self):
        for change in ({'key': 'compound:01'}, {'key': 'compound:2'}, {'to': OTHER},
                       {'data': calldata('rebalance(uint256,uint128,uint256)', 1, 1, self.rpc.now + 180)},
                       {'data': calldata('compound(uint256,uint128,uint256)', 2, 1, self.rpc.now + 180)},
                       {'value': 10}):
            with self.subTest(change=change):
                self.setUp(); self.k.state['pending'].update(change)
                pending = self.k.state['pending']
                pending['fee_review']['maximum_cost_wei'] = 2560 + pending['value']
                self.rpc.tx.update(to=pending['to'], input=pending['data'], value=hex(pending['value']))
                self.rpc.receipt['to'] = pending['to']
                self.k.save()
                old = self.k.state['last']['harvest:1']
                with patch('subprocess.run') as signer:
                    self.assertFalse(self.k.poll_pending())
                signer.assert_not_called()
                self.assertEqual(old, self.k.state['last']['harvest:1'])

    def test_reverted_or_unmined_or_ambiguous_intent_never_coalesces(self):
        for kind in ('reverted', 'unmined', 'ambiguous'):
            with self.subTest(kind=kind):
                self.setUp()
                old = self.k.state['last']['harvest:1']
                if kind == 'reverted': self.rpc.receipt['status'] = '0x0'
                elif kind == 'unmined': self.rpc.receipt = None
                else: self.k.state['pending']['hash'] = None
                self.k.poll_pending()
                self.assertEqual(old, self.k.state['last']['harvest:1'])
                self.assertEqual(kind != 'reverted', self.k.state['pending'] is not None)

    def test_external_or_manual_activity_without_saved_intent_is_not_adopted(self):
        self.k.state['pending'] = None
        self.k.save(); before = self.k.path.read_bytes()
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(before, self.k.path.read_bytes())

    def test_final_reorg_and_depth_loss_do_not_publish_harvest_candidate(self):
        for depth_loss in (False, True):
            with self.subTest(depth_loss=depth_loss):
                self.setUp(); original = self.rpc.call; reads = 0
                def call(method, params):
                    nonlocal reads
                    result = original(method, params)
                    if method == 'eth_getBlockByNumber' and params[0] == 'latest':
                        reads += 1
                        if depth_loss and reads > 1: return {**result, 'number': '0x63'}
                    if method == 'eth_getBlockByNumber' and params[0] == '0x63' and not depth_loss:
                        reads += 1
                        if reads > 2: return {**result, 'hash': '0x' + 'bb' * 32}
                    return result
                self.rpc.call = call
                before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
                if depth_loss: self.assertTrue(self.k.poll_pending())
                else:
                    with self.assertRaises(RpcError): self.k.poll_pending()
                self.assertEqual(before, self.k.state); self.assertEqual(disk, self.k.path.read_bytes())

    def test_failed_atomic_save_rolls_back_harvest_nonce_and_spend_together(self):
        before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        with patch.object(self.k, 'save', side_effect=OSError('inert failed replace')), self.assertRaises(OSError):
            self.k.poll_pending()
        self.assertEqual(before, self.k.state); self.assertEqual(disk, self.k.path.read_bytes())

    def test_restart_keeps_coalesced_clock_and_recovery_is_idempotent(self):
        self.confirm()
        restored = Keeper(self.cfg, rpc=self.rpc)
        before = restored.path.read_bytes()
        self.assertEqual(self.rpc.now, restored.state['last']['harvest:1'])
        self.assertFalse(restored.poll_pending())
        self.assertEqual(before, restored.path.read_bytes())

    def test_standalone_hourly_harvest_is_due_one_interval_after_proven_collection(self):
        self.confirm()
        f = schedule_fixtures.KeeperOutsideScheduleTests('runTest')
        f.setUp(); self.addCleanup(f.doCleanups)
        f.k.maintenance.update(compound=False, harvest=True)
        stamp = self.k.state['last']['harvest:1']
        f.k.state['last']['harvest:7'] = stamp
        f.base.group_words[6] = stamp - 100
        f.rpc.now = stamp + 3599
        f.cycle().assert_not_called()
        f.rpc.now += 1
        f.cycle().assert_called_once_with('vault', 'collectFees(uint256,uint256)',
                                        (7, f.rpc.now + 180), 'harvest:7')


if __name__ == '__main__': unittest.main()
