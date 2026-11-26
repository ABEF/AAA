"""NEW backup reopen regressions; no old test bodies, journals or services.

The FIFO case needs POSIX. Parent reviews/selects these methods before any run.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import tempfile
import time
import unittest
from unittest.mock import patch

from keeper import recovery_bundle as subject


NOW = 1795705352


class KeeperBackupAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-backup-reopen-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.work = self.root / 'working'; self.work.mkdir(mode=0o700)
        self.runtime = self.work / 'runtime'; self.runtime.mkdir(mode=0o700)
        names = ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback',
                 'pools', 'rewards', 'principal_exit', 'liquidity', 'balancing_router',
                 'pool_manager', 'state_view', 'portfolio_policy', 'lp_balance_math',
                 'lp_position_executor', 'protocol_policy', 'rebalance_confirmation')
        contracts = {name: '0x' + format(index, '040x') for index, name in enumerate(names, 1)}
        self.config = {
            'chain_id': 4663, 'sender': '0x' + '35' * 20,
            'contracts': contracts, 'accounting_model': 'shared-pools-v2',
            'accounting_version': 7, 'custody_version': 5, 'fee_intake_version': 1,
            'portfolio_version': 2, 'maintenance_policy_version': 3,
            'rebalance_confirmation_version': 3, 'execution_quality_version': 1,
            'protocol_policy_version': 1, 'execution_price_version': 1,
            'lp_routing_version': 3, 'royalty_settlement_version': 4,
            'state_path': 'runtime/journal.json', 'health_path': 'runtime/health.json',
            'lock_path': 'runtime/keeper.lock',
        }
        pending = {'key': 'harvest:7', 'nonce': 0, 'to': contracts['vault'],
                   'data': '0x' + '12' * 4, 'value': 0, 'day': '2026-11-26',
                   'hash': '0x' + '67' * 32,
                   'fee_review': {'schema': 1, 'gas_limit': 24000000,
                                  'max_fee_per_gas': 5000000000,
                                  'l1_fee_allowance_wei': 0,
                                  'maximum_cost_wei': 120000000000000000,
                                  'receipt_fee_policy': 'included'}}
        state = {'chain_id': 4663, 'sender': self.config['sender'], 'contracts': contracts,
                 'accounting_model': 'shared-pools-v2', 'accounting_version': 7,
                 'fee_intake_version': 1, 'execution_price_version': 1,
                 'bucket_cursor': 0, 'last': {}, 'spent': {'2026-11-25': 2**255 - 1},
                 'pending': pending, 'next_nonce': 0, 'receipt_anchor': None}
        self.journal = self.runtime / 'journal.json'
        self.raw = (json.dumps(state, indent=3, sort_keys=False) + '\n\n').encode()
        self.journal.write_bytes(self.raw); self.journal.chmod(0o600)
        self.config_path = self.root / 'original-config.json'
        self.config_raw = (json.dumps(self.config, indent=1) + '\n').encode()
        self.config_path.write_bytes(self.config_raw); self.config_path.chmod(0o600)
        for target in ('socket.socket.connect', 'socket.create_connection', 'subprocess.Popen'):
            guard = patch(target, side_effect=AssertionError('Forbidden backup side effect'))
            guard.start(); self.addCleanup(guard.stop)

    def test_guarded_regular_reads_preserve_exact_pending_and_restore_bytes(self):
        bundle = self.root / 'new-backup'; restored = self.root / 'new-restore'
        manifest, pin = subject.backup(self.config_path, bundle,
            working_directory=self.work, now=NOW)
        self.assertEqual(hashlib.sha256((bundle / 'manifest.json').read_bytes()).hexdigest(), pin)
        self.assertEqual(self.raw, (bundle / 'journal.json').read_bytes())
        self.assertEqual(manifest, subject.verify(bundle, pin, self.config_path,
            max_age_seconds=60, now=NOW + 30))
        plan, _ = subject.restore(bundle, pin, self.config_path, restored,
            max_age_seconds=60, now=NOW + 30)
        self.assertEqual(self.raw, (restored / 'keeper-state.json').read_bytes())
        self.assertEqual(self.raw, self.journal.read_bytes())
        self.assertEqual(self.config_raw, self.config_path.read_bytes())
        self.assertEqual(2**255 - 1, json.loads((restored / 'keeper-state.json').read_bytes())['spent']['2026-11-25'])
        self.assertFalse(plan['live_ready']); self.assertFalse(plan['service_restarted'])
        self.assertFalse(plan['configuration_installed']); self.assertFalse(plan['old_keeper_fenced'])

    @unittest.skipUnless(os.name == 'posix', 'FIFO reopen needs actual POSIX semantics')
    def test_fifo_substituted_at_open_refuses_without_waiting_or_complete_output(self):
        original_open = os.open; replaced = []
        output = self.root / 'refused-backup'
        def replace_at_open(path, flags, *args, **kwargs):
            if Path(path) == self.journal and not replaced:
                self.journal.unlink(); os.mkfifo(self.journal, mode=0o600)
                replaced.append(True)
            return original_open(path, flags, *args, **kwargs)
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        def timeout(_signum, _frame):
            raise TimeoutError('Disposable FIFO read did not refuse promptly')
        signal.signal(signal.SIGALRM, timeout); signal.setitimer(signal.ITIMER_REAL, 3)
        started = time.monotonic()
        try:
            with patch.object(os, 'open', side_effect=replace_at_open):
                with self.assertRaises(subject.RecoveryRefusal) as caught:
                    subject.backup(self.config_path, output, working_directory=self.work, now=NOW)
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual('source_snapshot_changed', caught.exception.code)
            self.assertEqual([True], replaced)
            self.assertTrue(stat.S_ISFIFO(self.journal.lstat().st_mode))
            self.assertEqual(self.config_raw, self.config_path.read_bytes())
            self.assertFalse(output.exists())
        finally:
            remaining, interval = previous_timer
            if remaining:
                remaining = max(.001, remaining - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, interval)
            signal.signal(signal.SIGALRM, previous_handler)

