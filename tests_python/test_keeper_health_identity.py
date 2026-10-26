"""Bind a real emitted keeper heartbeat to its full reviewed configuration.

No network, signer, fixture chain or service is used. Only the cycle body is
replaced so these tests exercise the real health writer and read-only checker.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.ops import health_check


class NoRPC:
    def call(self, *_args, **_kwargs):
        raise AssertionError('Health identity checks must not contact RPC')


class KeeperHealthIdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.config = {
            'chain_id': 31337,
            'sender': '0x' + '11' * 20,
            'contracts': {name: '0x' + '22' * 20 for name in
                          ('access', 'vault', 'strategy', 'fees', 'compounder', 'buyback', 'pools')},
            'accounting_version': 3,
            'fee_intake_version': 1,
            'rpc_urls': ['https://rpc.invalid/PRIVATE-ENDPOINT'],
            'keystore': '/private/KEYSTORE',
            'password_file': '/private/PASSWORD',
            'state_path': str(self.directory / 'state.json'),
            'health_path': str(self.directory / 'health.json'),
        }
        self.keeper = Keeper(self.config, rpc=NoRPC())
        self.keeper.live = True  # Emit the healthy branch; no real live initialization/signing.
        self.keeper.canonical_lifecycle = 0
        self.keeper.preparing = False
        with patch.object(self.keeper, 'cycle'), patch('keeper.monitor.log'), patch('subprocess.run') as signer:
            self.assertTrue(self.keeper.run_cycle())
            signer.assert_not_called()
        self.original_health = Path(self.config['health_path']).read_bytes()

    def test_matching_real_heartbeat_passes_without_exporting_configuration(self):
        self.assertTrue(health_check(self.config)['ok'])
        self.assertEqual(Path(self.config['health_path']).read_bytes(), self.original_health)
        for secret in ('PRIVATE-ENDPOINT', '/private/KEYSTORE', '/private/PASSWORD'):
            self.assertNotIn(secret, self.original_health.decode())

    def test_same_signer_and_chain_cannot_reuse_another_vault_heartbeat(self):
        other = copy.deepcopy(self.config)
        other['contracts']['vault'] = '0x' + '33' * 20
        self.assertFalse(health_check(other)['ok'])

    def test_historical_profile_cannot_reuse_current_profile_heartbeat(self):
        other = copy.deepcopy(self.config)
        other.update(accounting_version=2, fee_intake_version=0)
        self.assertFalse(health_check(other)['ok'])

    def test_changed_reviewed_limits_or_provider_need_fresh_heartbeat(self):
        for field, value in (('max_gas_price_wei', 1), ('rpc_urls', ['https://other.invalid'])):
            other = {**self.config, field: value}
            with self.subTest(field=field):
                self.assertFalse(health_check(other)['ok'])

    def test_legacy_heartbeat_without_configuration_binding_cannot_pass(self):
        data = json.loads(self.original_health)
        data.pop('configuration_sha256', None)
        Path(self.config['health_path']).write_text(json.dumps(data), encoding='utf-8')
        self.assertFalse(health_check(self.config)['ok'])

    def test_malformed_binding_cannot_pass(self):
        for value in (None, True, {}, '0x1234', 'f' * 64):
            data = json.loads(self.original_health)
            data['configuration_sha256'] = value
            Path(self.config['health_path']).write_text(json.dumps(data), encoding='utf-8')
            with self.subTest(value=value):
                self.assertFalse(health_check(self.config)['ok'])


if __name__ == '__main__':
    unittest.main()
