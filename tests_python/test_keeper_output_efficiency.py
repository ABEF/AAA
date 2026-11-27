"""New formatting and publication checks; no old test bodies are inherited.

Only FakeRpc data/setup is reused. The stock pending-wait cycle runs without
network, Cast or a live signer. This does not qualify a new live deployment.
"""
import copy
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from keeper.monitor import CONFIRMATION_CLEARS, CONFIRMATION_RESETS, Keeper, log
from tests_python.test_keeper import A, B, H, FakeRpc
from zzz_ops.abi import calldata
from zzz_ops.state import atomic_json, read_json


def encoded(value, *, compact=False):
    options = {'separators': (',', ':')} if compact else {'indent': 2}
    text = json.dumps(value, sort_keys=True, allow_nan=False, **options) + '\n'
    return text.replace('\n', os.linesep).encode('ascii')


class KeeperOutputEfficiencyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def pending_keeper(self, directory=None):
        directory = self.directory if directory is None else directory
        directory.mkdir(parents=True, exist_ok=True)
        rpc = FakeRpc()
        config = {
            'chain_id': 1, 'sender': A,
            'contracts': {name: B for name in
                          ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools')},
            'state_path': str(directory / 'state.json'),
            'health_path': str(directory / 'health.json'),
            'confirmations': 2, 'receipt_fee_policy': 'included',
            'max_gas_limit': 100000, 'max_gas_price_wei': 100,
            'max_transaction_cost_wei': 1000000, 'max_daily_cost_wei': 10000000,
        }
        keeper = Keeper(config, rpc=rpc)
        keeper.state.update(next_nonce=7, pending={
            'key': 'harvest:1', 'nonce': 7, 'to': B,
            'data': calldata('collectFees(uint256,uint256)', 1, rpc.now + 180),
            'value': 0, 'day': '2026-11-27', 'hash': H,
            'fee_review': {'schema': 1, 'gas_limit': 256, 'max_fee_per_gas': 2,
                           'l1_fee_allowance_wei': 0, 'maximum_cost_wei': 512,
                           'receipt_fee_policy': 'included'},
        })
        keeper.save()
        return keeper, rpc

    def test_default_and_explicit_false_preserve_previous_output_bytes(self):
        value = {'z': [True, None, {'unicode': '\u00e9', 'integer': 2**256 - 1}],
                 'a': {'line': 'first\nsecond', 'fraction': 0.125}}
        expected = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
        expected = expected.replace('\n', os.linesep).encode('ascii')
        for name, options in (('default.json', {}), ('false.json', {'compact': False})):
            with self.subTest(name=name):
                path = self.directory / name
                atomic_json(path, value, **options)
                self.assertEqual(path.read_bytes(), expected)
                self.assertEqual(read_json(path), value)

    def test_compact_output_keeps_all_nested_data_and_reduces_bytes(self):
        value = {'status': 'running', 'observations': [
            {'bucket': str(2**255 + index), 'hash': H, 'optional': None, 'ok': True}
            for index in range(32)]}
        pretty, compact = self.directory / 'pretty.json', self.directory / 'compact.json'
        atomic_json(pretty, value)
        atomic_json(compact, value, compact=True)
        raw = compact.read_bytes()
        self.assertEqual(read_json(pretty), read_json(compact))
        self.assertEqual(read_json(compact), value)
        self.assertEqual(raw, encoded(value, compact=True))
        self.assertLess(len(raw), len(pretty.read_bytes()))
        self.assertEqual(raw.count(os.linesep.encode()), 1)

    def test_nonfinite_write_preserves_old_file_and_removes_private_partial(self):
        real_create = tempfile.mkstemp
        for compact in (False, True):
            with self.subTest(compact=compact):
                path = self.directory / ('compact.json' if compact else 'pretty.json')
                old = encoded({'pending': {'hash': H}, 'next_nonce': 7})
                path.write_bytes(old)
                created = []

                def create(*args, **kwargs):
                    fd, name = real_create(*args, **kwargs)
                    created.append((Path(name), stat.S_IMODE(os.fstat(fd).st_mode)))
                    return fd, name

                with patch('zzz_ops.state.tempfile.mkstemp', side_effect=create), \
                        patch('zzz_ops.state.os.replace') as replace:
                    with self.assertRaises(ValueError):
                        atomic_json(path, {'a_partial': [1, 2], 'z_invalid': float('nan')}, compact=compact)
                replace.assert_not_called()
                self.assertEqual(path.read_bytes(), old)
                self.assertEqual(len(created), 1)
                self.assertFalse(created[0][0].exists())
                self.assertEqual(list(self.directory.glob('.' + path.name + '.*.tmp')), [])
                if os.name == 'posix':
                    self.assertEqual(created[0][1], 0o600)

    def test_failed_replace_preserves_original_and_cleans_synced_temporary(self):
        real_sync = os.fsync
        for compact in (False, True):
            with self.subTest(compact=compact):
                path = self.directory / ('compact.json' if compact else 'pretty.json')
                old = encoded({'pending': {'hash': H}, 'spent': {'2026-11-27': 123}})
                path.write_bytes(old)
                refusal = OSError(errno.EACCES, 'inert replacement refusal')
                with patch('zzz_ops.state.os.replace', side_effect=refusal), \
                        patch('zzz_ops.state.os.fsync', wraps=real_sync) as sync:
                    with self.assertRaises(OSError) as raised:
                        atomic_json(path, {'replacement': True}, compact=compact)
                self.assertIs(raised.exception, refusal)
                self.assertEqual(sync.call_count, 1)  # File sync precedes the refused replacement.
                self.assertEqual(path.read_bytes(), old)
                self.assertEqual(list(self.directory.glob('.' + path.name + '.*.tmp')), [])

    def test_both_formats_keep_file_sync_replace_directory_sync_order(self):
        real_sync, real_replace = os.fsync, os.replace
        for compact in (False, True):
            with self.subTest(compact=compact):
                path = self.directory / ('compact.json' if compact else 'pretty.json')
                events = []

                def sync(fd):
                    events.append('sync')
                    return real_sync(fd)

                def replace(source, destination):
                    self.assertEqual(Path(destination), path)
                    self.assertEqual(json.loads(Path(source).read_bytes()), {'value': 42})
                    if os.name == 'posix':
                        self.assertEqual(stat.S_IMODE(Path(source).stat().st_mode), 0o600)
                    events.append('replace')
                    return real_replace(source, destination)

                with patch('zzz_ops.state.os.fsync', side_effect=sync), \
                        patch('zzz_ops.state.os.replace', side_effect=replace):
                    atomic_json(path, {'value': 42}, compact=compact)
                self.assertEqual(events, ['sync', 'replace'] + (['sync'] if hasattr(os, 'O_DIRECTORY') else []))
                self.assertEqual(path.read_bytes(), encoded({'value': 42}, compact=compact))

    def test_compact_logs_preserve_critical_fields_order_duplicates_and_full_calldata(self):
        stamp = '2026-11-27T15:00:00+00:00'
        data = calldata('collectFees(uint256,uint256)', 1, 180)
        events = [
            ('pending', {'transaction': H}), ('pending', {'transaction': H}),
            ('submitted', {'action': 'harvest:1', 'transaction': H}),
            ('confirmed', {'action': 'harvest:1', 'transaction': H, 'cost_wei': '123'}),
            ('reverted', {'action': 'harvest:1', 'transaction': H, 'cost_wei': '123'}),
            ('submission_requires_reconciliation', {'action': 'harvest:1', 'reported_transaction': H,
                                                   'error_type': 'OSError', 'os_errno': 'ENOSPC'}),
            ('cycle_failed', {'retryable': False, 'consecutive_failures': 1, 'error_type': 'ValueError'}),
            ('keeper_halted', {'error_type': 'OSError', 'os_errno': 'EIO'}),
            ('dry_run', {'action': 'harvest:1', 'to': B, 'calldata': data, 'estimated_cost_wei': '123'}),
        ]
        with patch('keeper.monitor.dt.datetime') as clock, patch('builtins.print') as output:
            clock.now.return_value.isoformat.return_value = stamp
            for event, fields in events:
                log(event, **fields)
        self.assertEqual(output.call_count, len(events))
        for call, (event, fields) in zip(output.call_args_list, events):
            expected = {'time': stamp, 'event': event, **fields}
            self.assertEqual(len(call.args), 1)
            self.assertEqual(call.kwargs, {'flush': True})
            self.assertEqual(json.loads(call.args[0]), expected)
            self.assertEqual(call.args[0], json.dumps(expected, sort_keys=True, separators=(',', ':'), allow_nan=False))

    def test_nonfinite_log_is_refused_before_any_line_is_emitted(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(value=value), patch('builtins.print') as output:
                with self.assertRaises(ValueError):
                    log('inert_invalid_metric', metric=value)
                output.assert_not_called()

    def test_stock_pending_cycle_compacts_both_health_writes_without_touching_journal(self):
        keeper, rpc = self.pending_keeper()
        original = keeper.path.read_bytes()
        identity = keeper.path.stat().st_dev, keeper.path.stat().st_ino
        state = copy.deepcopy(keeper.state)
        with patch('keeper.monitor.atomic_json', wraps=atomic_json) as writer, \
                patch('keeper.monitor.run_cast') as signer, redirect_stdout(io.StringIO()):
            self.assertTrue(keeper.run_cycle())
        signer.assert_not_called()
        self.assertEqual(writer.call_count, 2)
        self.assertEqual([call.args[1]['status'] for call in writer.call_args_list], ['running', 'awaiting_receipt'])
        for call in writer.call_args_list:
            self.assertEqual(Path(call.args[0]), keeper.health_path)
            self.assertEqual(call.kwargs, {'compact': True})
        health = read_json(keeper.health_path)
        self.assertEqual(keeper.health_path.read_bytes(), encoded(health, compact=True))
        self.assertEqual(health['status'], 'awaiting_receipt')
        self.assertTrue(health['pending'])
        self.assertFalse(health['live'])
        self.assertEqual(keeper.state, state)
        self.assertEqual(keeper.path.read_bytes(), original)
        self.assertEqual((keeper.path.stat().st_dev, keeper.path.stat().st_ino), identity)
        self.assertEqual(rpc.calls, [('eth_getTransactionReceipt', [H])])

    def test_initial_compact_health_refusal_preserves_files_and_prevents_cycle_or_signing(self):
        keeper, rpc = self.pending_keeper()
        journal = keeper.path.read_bytes()
        previous_health = encoded({'previous': 'retained'})
        keeper.health_path.write_bytes(previous_health)
        refusal = OSError(errno.ENOSPC, 'inert health replacement refusal')
        with patch('zzz_ops.state.os.replace', side_effect=refusal), \
                patch.object(keeper, 'cycle', wraps=keeper.cycle) as cycle, \
                patch('keeper.monitor.run_cast') as signer:
            with self.assertRaises(OSError) as raised:
                keeper.run_cycle()
        self.assertIs(raised.exception, refusal)
        cycle.assert_not_called()
        signer.assert_not_called()
        self.assertEqual(rpc.calls, [])
        self.assertEqual(keeper.path.read_bytes(), journal)
        self.assertEqual(keeper.health_path.read_bytes(), previous_health)
        self.assertEqual(list(self.directory.glob('.*.tmp')), [])

    def test_health_preview_zero_32_33_boundaries_keep_numeric_order_and_full_identity(self):
        for count in (0, 32, 33):
            with self.subTest(count=count):
                keeper, rpc = self.pending_keeper(self.directory / str(count))
                ids = [str(value) for value in range(count, 0, -1)]
                keeper.state[CONFIRMATION_RESETS] = dict.fromkeys(ids, True)
                keeper.state[CONFIRMATION_CLEARS] = {key: {
                    'number': 99, 'hash': H, 'timestamp': rpc.now,
                    'nonce': 6, 'awaiting_healthy_read': True} for key in ids}
                keeper._validate_state()
                keeper.save()
                journal = keeper.path.read_bytes()
                with patch('keeper.monitor.run_cast') as signer, redirect_stdout(io.StringIO()):
                    self.assertTrue(keeper.run_cycle())
                signer.assert_not_called()
                report = read_json(keeper.health_path)['rebalance_confirmation_health']
                ordered = [str(value) for value in range(1, count + 1)]
                digest = hashlib.sha256(json.dumps(ordered, separators=(',', ':')).encode('ascii')).hexdigest()
                for field in ('pending_reset_buckets', 'awaiting_healthy_read_buckets'):
                    self.assertEqual(report[field], ordered[:32])
                    self.assertEqual(report[field + '_summary'], {
                        'count': count, 'complete': count <= 32, 'all_ids_sha256': digest})
                    if count <= 32:
                        self.assertEqual(report[field], ordered)
                self.assertEqual(keeper.path.read_bytes(), journal)

    def test_accepted_ten_thousand_id_inventories_have_bounded_health_and_exact_journal(self):
        keeper, rpc = self.pending_keeper()
        ids = [str(10**77 + value) for value in range(10000)]  # Legal78-digit uint256 bucket IDs.
        keeper.state[CONFIRMATION_RESETS] = dict.fromkeys(reversed(ids), True)
        keeper.state[CONFIRMATION_CLEARS] = {key: {
            'number': 99, 'hash': H, 'timestamp': rpc.now,
            'nonce': 6, 'awaiting_healthy_read': True} for key in reversed(ids)}
        keeper._validate_state()  # Real admission of both full inventories, before formatting.
        keeper.save()
        journal = keeper.path.read_bytes()
        identity = keeper.path.stat().st_dev, keeper.path.stat().st_ino
        full_state = copy.deepcopy(keeper.state)
        with patch('keeper.monitor.run_cast') as signer, redirect_stdout(io.StringIO()):
            self.assertTrue(keeper.run_cycle())
        signer.assert_not_called()
        health_raw = keeper.health_path.read_bytes()
        self.assertLessEqual(len(health_raw), 1024 * 1024)  # Existing alert-reader cap remains unchanged.
        report = json.loads(health_raw)['rebalance_confirmation_health']
        digest = hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode('ascii')).hexdigest()
        for field in ('pending_reset_buckets', 'awaiting_healthy_read_buckets'):
            self.assertEqual(report[field], ids[:32])
            self.assertEqual(report[field + '_summary'], {
                'count': 10000, 'complete': False, 'all_ids_sha256': digest})
        self.assertEqual(keeper.path.read_bytes(), journal)
        self.assertEqual((keeper.path.stat().st_dev, keeper.path.stat().st_ino), identity)
        self.assertEqual(keeper.state, full_state)
        self.assertEqual(rpc.calls, [('eth_getTransactionReceipt', [H])])


if __name__ == '__main__':
    unittest.main()
