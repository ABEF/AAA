"""Offline management/recovery consistency; no operating files, RPC or signer."""
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper import ops
from tests_python import test_keeper_ops as ops_fixtures
from tests_python import test_keeper_fees as fee_fixtures
from zzz_ops.rpc import RpcError


class KeeperOpsJSONIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.f = ops_fixtures.OpsTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def test_duplicate_health_counter_cannot_suppress_a_blocked_action(self):
        path = Path(self.f.cfg['health_path'])
        raw = json.dumps(self.f.health).replace('"blocked_actions": 0',
            '"blocked_actions": 1, "blocked_actions": 0')
        path.write_text(raw)
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            ops.health_check(self.f.cfg, now=self.f.now)
        self.assertEqual(before, path.read_bytes())

    def test_escaped_duplicate_health_field_is_also_rejected(self):
        path = Path(self.f.cfg['health_path'])
        raw = json.dumps(self.f.health).replace('"blocked_actions": 0',
            '"blocked_actions": 1, "\\u0062locked_actions": 0')
        path.write_text(raw)
        with self.assertRaises(ValueError):
            ops.health_check(self.f.cfg, now=self.f.now)

    def test_unused_nonfinite_health_numbers_do_not_receive_a_healthy_result(self):
        path = Path(self.f.cfg['health_path'])
        for value in ('NaN', 'Infinity', '-Infinity', '1e400'):
            path.write_text(json.dumps(self.f.health)[:-1] + ', "diagnostic": ' + value + '}')
            with self.subTest(value=value), self.assertRaises(ValueError):
                ops.health_check(self.f.cfg, now=self.f.now)

    def test_conflicting_snapshot_pending_cannot_pass_last_key_wins_integrity(self):
        path = self.f.root / 'ambiguous-snapshot.json'
        ops.create_snapshot(self.f.cfg, path)
        raw = path.read_text()
        self.assertIn('"pending": null', raw)
        # The existing checksum still matches the final duplicate value. The
        # competing intent must be rejected, never selected or silently repaired.
        path.write_text(raw.replace('"pending": null',
            '"pending": {"nonce": 7}, "pending": null'))
        before = path.read_bytes()
        with patch('subprocess.run') as signer, patch('zzz_ops.rpc.Rpc.call') as rpc, \
                self.assertRaises(ValueError):
            ops.verify_snapshot(self.f.cfg, path)
        signer.assert_not_called()
        rpc.assert_not_called()
        self.assertEqual(before, path.read_bytes())

    def test_cli_ambiguous_config_fails_before_running_the_requested_check(self):
        path = self.f.root / 'ambiguous-config.json'
        path.write_text('{"chain_id": 1, "chain_id": 2}')
        output = io.StringIO()
        with patch('sys.argv', ['keeper.ops', '--config', str(path), 'health']), \
                patch('sys.stdout', output), patch.object(ops, 'health_check', return_value={'ok': True}) as check:
            self.assertEqual(1, ops.main())
        check.assert_not_called()
        report = json.loads(output.getvalue())
        self.assertEqual((False, ['check_unavailable'], 'ValueError'),
            (report['ok'], report['reasons'], report['error_type']))

    def test_valid_health_and_snapshot_keep_the_existing_read_only_result(self):
        self.assertTrue(self.f.check_health()['ok'])
        path = self.f.root / 'snapshot.json'
        before = self.f.k.path.read_bytes()
        with patch('subprocess.run') as signer, patch('zzz_ops.rpc.Rpc.call') as rpc:
            ops.create_snapshot(self.f.cfg, path)
            self.assertTrue(ops.verify_snapshot(self.f.cfg, path)['ok'])
        signer.assert_not_called()
        rpc.assert_not_called()
        self.assertEqual(before, self.f.k.path.read_bytes())

    def test_missing_health_and_snapshot_still_raise_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            ops.health_check(self.f.cfg)
        with self.assertRaises(FileNotFoundError):
            ops.verify_snapshot(self.f.cfg, self.f.root / 'missing-snapshot.json')

    def shape_cli(self, config, command):
        output = io.StringIO()
        with patch('sys.argv', ['keeper.ops', '--config', str(config), *command]), \
                patch('sys.stdout', output), patch('subprocess.run') as signer, \
                patch('zzz_ops.rpc.Rpc.call') as rpc:
            self.assertEqual(1, ops.main())
        signer.assert_not_called()
        rpc.assert_not_called()
        report = json.loads(output.getvalue())
        self.assertEqual((False, ['check_unavailable'], 'ValueError'),
            (report['ok'], report['reasons'], report['error_type']))

    def test_nonobject_health_input_has_a_fixed_shape_error_and_keeps_bytes(self):
        config = self.f.root / 'config.json'
        config.write_text(json.dumps(self.f.cfg))
        path = Path(self.f.cfg['health_path'])
        for value in ([], None, 1, True, 'text'):
            path.write_text(json.dumps(value))
            before = path.read_bytes()
            with self.subTest(value=value):
                self.shape_cli(config, ['health'])
                with self.assertRaises(ValueError):
                    ops.health_check(self.f.cfg)
            self.assertEqual(before, path.read_bytes())

    def test_nonobject_snapshot_input_has_a_fixed_shape_error_and_keeps_bytes(self):
        config = self.f.root / 'config.json'
        config.write_text(json.dumps(self.f.cfg))
        path = self.f.root / 'snapshot-shape.json'
        for value in ([], None, 1, True, 'text'):
            path.write_text(json.dumps(value))
            before = path.read_bytes()
            with self.subTest(value=value):
                self.shape_cli(config, ['verify-snapshot', '--input', str(path)])
                with self.assertRaises(ValueError):
                    ops.verify_snapshot(self.f.cfg, path)
            self.assertEqual(before, path.read_bytes())

    def test_nonobject_cli_configuration_is_rejected_before_check_dispatch(self):
        path = self.f.root / 'config-shape.json'
        for value in ([], None, 1, True, 'text'):
            path.write_text(json.dumps(value))
            before = path.read_bytes()
            with self.subTest(value=value), patch.object(ops, 'health_check', return_value={'ok': True}) as check:
                self.shape_cli(path, ['health'])
                check.assert_not_called()
            self.assertEqual(before, path.read_bytes())


class KeeperCheckpointOrderTests(unittest.TestCase):
    def setUp(self):
        self.f = fee_fixtures.KeeperSignedFeeTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.k, self.rpc = self.f.k, self.f.rpc
        self.anchor_hash = '0x' + '98' * 32
        self.receipt_hash = '0x' + '99' * 32
        self.anchor_stamp = self.rpc.now - 1
        self.k.state['receipt_anchor'] = {'number': 98, 'hash': self.anchor_hash,
            'timestamp': self.anchor_stamp, 'nonce': 6}
        self.k.save()
        self.original_call = self.rpc.call
        self.head_stamp = self.rpc.now
        self.receipt_number, self.receipt_stamp = 99, self.rpc.now
        self.same_block = False
        def call(method, params):
            if method == 'eth_getBlockByNumber':
                number = 100 if params[0] == 'latest' else int(params[0], 16)
                stamp = self.head_stamp if params[0] == 'latest' else self.anchor_stamp if number == 98 else self.receipt_stamp
                block_hash = self.anchor_hash if number == 98 else self.receipt_hash
                return {'number': hex(number), 'timestamp': hex(stamp),
                    'hash': block_hash, 'baseFeePerGas': '0x3'}
            return self.original_call(method, params)
        self.rpc.call = call
        self.set_receipt(99, self.rpc.now)

    def set_receipt(self, number, stamp):
        self.receipt_number, self.receipt_stamp = number, stamp
        block_hash = self.anchor_hash if number == 98 else self.receipt_hash
        self.rpc.receipt.update(blockNumber=hex(number), blockHash=block_hash, transactionIndex='0x1')
        self.rpc.tx.update(blockNumber=hex(number), blockHash=block_hash, transactionIndex='0x1')

    def reject_without_mutating_paid_truth(self, body):
        before, disk = copy.deepcopy(self.k.state), self.k.path.read_bytes()
        with patch('subprocess.run') as signer, self.assertRaises(RpcError):
            body()
        signer.assert_not_called()
        self.assertEqual(before, self.k.state)
        self.assertEqual(disk, self.k.path.read_bytes())

    def test_higher_head_with_timestamp_before_checkpoint_is_rejected(self):
        self.head_stamp = self.anchor_stamp - 1
        self.reject_without_mutating_paid_truth(self.k._validate_checkpoint)

    def test_bad_checkpoint_clock_cannot_refresh_health_success(self):
        self.k.state['pending'] = None
        self.k.save()
        self.k.last_success_at = '2000-01-01T00:00:00+00:00'
        self.head_stamp = self.anchor_stamp - 1
        before = self.k.path.read_bytes()
        with patch.object(self.k, 'cycle', side_effect=self.k._validate_checkpoint):
            self.assertFalse(self.k.run_cycle())
        self.assertEqual('2000-01-01T00:00:00+00:00', self.k.last_success_at)
        self.assertEqual(before, self.k.path.read_bytes())

    def test_successor_nonce_receipt_cannot_precede_the_confirmed_anchor_height(self):
        self.set_receipt(97, self.anchor_stamp - 1)
        self.reject_without_mutating_paid_truth(self.k.poll_pending)

    def test_successor_nonce_receipt_cannot_retreat_the_confirmed_anchor_timestamp(self):
        self.set_receipt(99, self.anchor_stamp - 1)
        self.reject_without_mutating_paid_truth(self.k.poll_pending)

    def same_height_header_after_checkpoint(self, block_hash, stamp):
        self.set_receipt(98, self.anchor_stamp)
        self.rpc.receipt['blockHash'] = block_hash
        self.rpc.tx['blockHash'] = block_hash
        original_call = self.rpc.call
        checkpoint_reads = []
        def call(method, params):
            header = original_call(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == hex(98):
                checkpoint_reads.append(header)
                # The initial saved-checkpoint read succeeds. Only subsequent
                # canonical inclusion reads switch, as during RPC failover.
                if len(checkpoint_reads) > 1:
                    return {**header, 'hash': block_hash, 'timestamp': hex(stamp)}
            return header
        self.rpc.call = call
        return checkpoint_reads

    def test_same_height_successor_cannot_replace_the_confirmed_checkpoint_hash(self):
        reads = self.same_height_header_after_checkpoint(self.receipt_hash, self.anchor_stamp)
        self.reject_without_mutating_paid_truth(self.k.poll_pending)
        self.assertGreaterEqual(len(reads), 2)

    def test_same_height_successor_cannot_replace_the_confirmed_checkpoint_timestamp(self):
        reads = self.same_height_header_after_checkpoint(self.anchor_hash, self.anchor_stamp + 1)
        self.reject_without_mutating_paid_truth(self.k.poll_pending)
        self.assertGreaterEqual(len(reads), 2)

    def test_same_block_successor_remains_valid_with_equal_hash_and_timestamp(self):
        reads = self.same_height_header_after_checkpoint(self.anchor_hash, self.anchor_stamp)
        self.assertFalse(self.k.poll_pending())
        self.assertGreaterEqual(len(reads), 3)
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(8, self.k.state['next_nonce'])
        self.assertEqual(510, sum(self.k.state['spent'].values()))
        self.assertEqual({'number': 98, 'hash': self.anchor_hash,
            'timestamp': self.anchor_stamp, 'nonce': 7}, self.k.state['receipt_anchor'])

    def test_inspection_without_old_checkpoint_does_not_invent_one_before_recovery(self):
        self.k.state['receipt_anchor'] = None
        self.k.save()
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(8, self.k.state['next_nonce'])
        self.assertEqual(510, sum(self.k.state['spent'].values()))


if __name__ == '__main__':
    unittest.main()
