"""New metadata2 observation/receipt cases using inert RPC and no real signer.

These extend the historical metadata fixture without rerunning its test suite.
Unrelated financial graph admission is stubbed only in receipt fixture actions;
metadata2 renderer/version/hash admission remains real production reader code.
"""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_metadata_keeper as F
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError

RENDERER = '0x' + '55' * 20
CODE = '0x6002'
PIN = '0x' + keccak256(bytes.fromhex(CODE[2:])).hex()


class LifecycleRPC(F.MetadataRpc):
    def __init__(self):
        super().__init__()
        self.life = {token: 11 for token in F.TOKENS}
        self.lifecycle_overrides = {}
        self.code[RENDERER] = CODE

    def call(self, method, params):
        if method == 'eth_call' and 'from' not in params[0]:
            data, target = params[0]['data'], params[0]['to']
            for signature, value in (
                ('metadataRenderer()', int(RENDERER, 16)),
                ('METADATA_LIFECYCLE_VERSION()', 2),
            ):
                if data == calldata(signature):
                    self.calls.append((method, copy.deepcopy(params)))
                    return self.lifecycle_overrides.get(signature, F.words(value))
            if data[:10] == calldata('metadataLifecycleFingerprint(uint256)', 0)[:10]:
                self.calls.append((method, copy.deepcopy(params)))
                identifier = int(data[10:], 16)
                return self.lifecycle_overrides.get('fingerprint', F.words(self.life[identifier]))
            if data in (calldata('lpExitStarted()'), calldata('exitPhase()')):
                self.calls.append((method, copy.deepcopy(params)))
                return F.words(0)
            if target == RENDERER and data == calldata('access()'):
                self.calls.append((method, copy.deepcopy(params)))
                return self.lifecycle_overrides.get('access()', F.words(int(F.ACCESS, 16)))
        return super().call(method, params)


def configuration(original):
    cfg = copy.deepcopy(original)
    cfg.update(accounting_version=7, custody_version=5, fee_intake_version=1,
        protocol_policy_version=1, maintenance_policy_version=3, lp_routing_version=2,
        execution_quality_version=1, portfolio_version=2, rebalance_confirmation_version=3,
        interval_seconds=240, idle_compounding_budget=F.ACCESS, maintenance={'compound': False})
    for i, role in enumerate(('rewards', 'principal_exit', 'liquidity', 'balancing_router',
            'pool_manager', 'state_view', 'portfolio_policy', 'lp_balance_math',
            'lp_position_executor', 'protocol_policy', 'rebalance_confirmation'), 101):
        cfg['contracts'][role] = '0x' + f'{i:040x}'
        cfg['code_hashes'][role] = '0x' + keccak256(bytes.fromhex('6000')).hex()
    cfg['code_hashes']['idle_compounding_budget'] = cfg['code_hashes']['access']
    cfg['metadata_refresh'].update(lifecycle_version=2, renderer=RENDERER,
        renderer_code_hash=PIN)
    return cfg


class KeeperMetadataLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.f = F.MetadataKeeperTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.rpc = LifecycleRPC()
        self.cfg = configuration(self.f.config)
        self.k = Keeper(self.cfg, rpc=self.rpc)
        self.f.config, self.f.keeper, self.f.rpc = self.cfg, self.k, self.rpc

    def record(self, ordinal=1, block=99):
        return self.k._metadata_record_at(ordinal, block)

    def baseline(self):
        records = [self.record(i) for i in range(1, len(self.rpc.ids) + 1)]
        self.k.state['metadata_refresh']['notified'] = {
            str(r['ordinal']): dict(r, observed_number=99, observed_hash=self.rpc.block_hash(99),
                notification_number=99, notification_hash=self.rpc.block_hash(99)) for r in records}

    def capture(self):
        with patch.object(self.k, 'submit', return_value=False) as submit:
            self.assertFalse(self.k._refresh_metadata())
        return submit

    def test_lifecycle_and_payment_changes_notify_without_tier_change(self):
        first = self.record()
        self.assertIn('lifecycle_fingerprint', first)
        self.baseline()
        for fingerprint in (12, 13, 14):
            with self.subTest(fingerprint=fingerprint):
                self.rpc.life[F.TOKENS[0]] = fingerprint
                submit = self.capture()
                self.assertEqual(submit.call_args.args[2], (1, 1))
                record = submit.call_args.kwargs['metadata_observation']['records'][0]
                self.assertEqual(record['lifecycle_fingerprint'], '0x' + f'{fingerprint:064x}')
                self.assertEqual(record['stage'], first['stage'])

    def test_unknown_or_boolean_lifecycle_versions_reject_before_work(self):
        for version in (True, 1, 3, '2', None):
            with self.subTest(version=version):
                cfg = copy.deepcopy(self.cfg)
                cfg['metadata_refresh']['lifecycle_version'] = version
                with self.assertRaises(ValueError):
                    Keeper(cfg, rpc=self.rpc)

    def test_same_fingerprint_skips_notification_without_numeric_price_reads(self):
        self.baseline()
        self.rpc.calls.clear()
        self.capture().assert_not_called()
        requested = [params[0]['data'][:10] for method, params in self.rpc.calls if method == 'eth_call']
        self.assertNotIn(calldata('currentLPValue(uint256)', 0)[:10], requested)
        self.assertNotIn(calldata('tokenURI(uint256)', 0)[:10], requested)

    def test_renderer_address_version_access_and_runtime_fail_before_submission(self):
        for kind, value in (('metadataRenderer()', F.words(int(F.ACCESS, 16))),
                ('METADATA_LIFECYCLE_VERSION()', F.words(1)),
                ('access()', F.words(int(F.SENDER, 16))), ('runtime', '0x6003')):
            with self.subTest(kind=kind):
                self.rpc.lifecycle_overrides.clear()
                self.rpc.code[RENDERER] = CODE
                if kind == 'runtime': self.rpc.code[RENDERER] = value
                else: self.rpc.lifecycle_overrides[kind] = value
                before = copy.deepcopy(self.k.state)
                with patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
                    self.k._refresh_metadata()
                submit.assert_not_called()
                self.assertEqual(self.k.state, before)

    def test_missing_pins_and_wrong_accounting_never_admit_lifecycle2(self):
        for field, value in (('renderer', None), ('renderer_code_hash', None),
                ('renderer_code_hash', '0x' + '00' * 32)):
            with self.subTest(field=field, value=value):
                cfg = copy.deepcopy(self.cfg)
                cfg['metadata_refresh'][field] = value
                with self.assertRaises(ValueError): Keeper(cfg, rpc=self.rpc)
        cfg = copy.deepcopy(self.f.config)
        self.k.accounting_version = 1
        self.k.config = cfg
        with self.assertRaises(ValueError): self.k._configure_metadata()

    def test_legacy_state_cannot_be_relabelled_as_lifecycle2(self):
        legacy_cfg = copy.deepcopy(self.cfg)
        legacy_cfg['metadata_refresh'] = {'enabled': True, 'nft': F.NFT}
        legacy = Keeper(legacy_cfg, rpc=self.rpc)
        legacy.save()
        before = legacy.path.read_bytes()
        with self.assertRaises(ValueError): Keeper(self.cfg, rpc=self.rpc)
        self.assertEqual(legacy.path.read_bytes(), before)

    def test_lifecycle2_state_rejects_implicit_enabled_downgrade(self):
        self.baseline()
        self.k.save()
        before = self.k.path.read_bytes()
        cfg = copy.deepcopy(self.cfg)
        cfg['metadata_refresh'] = {'enabled': True, 'nft': F.NFT}
        with self.assertRaises(ValueError): Keeper(cfg, rpc=self.rpc)
        self.assertEqual(self.k.path.read_bytes(), before)

    def test_disabled_restart_restores_exact_identity_without_new_notifications(self):
        self.baseline()
        self.k.save()
        cfg = copy.deepcopy(self.cfg)
        cfg['metadata_refresh'] = {'enabled': False}
        restarted = Keeper(cfg, rpc=self.rpc)
        self.assertFalse(restarted.metadata_enabled)
        self.assertEqual(restarted.metadata_lifecycle_version, 2)
        self.assertEqual(restarted.state['metadata_refresh'], self.k.state['metadata_refresh'])
        self.assertFalse(restarted._refresh_metadata())

    def test_malformed_fingerprint_and_incomplete_record_never_become_baseline(self):
        for value in ('0x', F.words(1, 2)):
            with self.subTest(value=value):
                self.rpc.lifecycle_overrides['fingerprint'] = value
                with self.assertRaises(RpcError): self.record()
        self.rpc.lifecycle_overrides.clear()
        record = self.record()
        record.pop('lifecycle_fingerprint')
        with self.assertRaises(ValueError): self.k._validate_metadata_record(record)

    def test_legacy_reader_rejects_lifecycle_record_instead_of_ignoring_it(self):
        record = self.record()
        self.k.metadata_lifecycle_version = 0
        with self.assertRaises(ValueError): self.k._validate_metadata_record(record)

    def test_receipt_recomputes_fingerprint_before_disabled_pending_recovery(self):
        with patch.object(self.k, '_validate_accounting_version'):
            self.f.submit()
        prepared = copy.deepcopy(self.k.state['pending']['metadata_observation']['records'])
        self.rpc.life[F.TOKENS[0]] = 55
        self.f.receipt()
        cfg = copy.deepcopy(self.cfg)
        cfg['metadata_refresh'] = {'enabled': False}
        restarted = Keeper(cfg, rpc=self.rpc)
        with patch.object(restarted, '_validate_accounting_version'):
            self.assertFalse(restarted.poll_pending())
        notified = restarted.state['metadata_refresh']['notified']['1']
        self.assertNotEqual(notified['lifecycle_fingerprint'], prepared[0]['lifecycle_fingerprint'])
        self.assertEqual(notified['lifecycle_fingerprint'], '0x' + f'{55:064x}')
        self.assertIsNone(restarted.state['pending'])
        self.assertFalse(restarted.metadata_enabled)

    def test_old_pending_and_legacy_identity_remain_byte_shaped(self):
        legacy_cfg = copy.deepcopy(self.cfg)
        legacy_cfg['metadata_refresh'] = {'enabled': True, 'nft': F.NFT}
        legacy = Keeper(legacy_cfg, rpc=self.rpc)
        self.f.config, self.f.keeper = legacy_cfg, legacy
        with patch.object(legacy, '_validate_accounting_version'):
            self.f.submit()
        pending = copy.deepcopy(legacy.state['pending'])
        identity = copy.deepcopy(legacy.state['metadata_refresh']['identity'])
        self.assertEqual(set(identity), {'chain_id', 'controller', 'nft'})
        self.f.receipt()
        cfg = copy.deepcopy(legacy_cfg)
        cfg['metadata_refresh'] = {'enabled': False}
        restarted = Keeper(cfg, rpc=self.rpc)
        self.assertEqual(restarted.state['pending'], pending)
        with patch.object(restarted, '_validate_accounting_version'):
            self.assertFalse(restarted.poll_pending())
        self.assertEqual(restarted.state['metadata_refresh']['identity'], identity)
        self.assertTrue(all('lifecycle_fingerprint' not in r for r in
            restarted.state['metadata_refresh']['notified'].values()))

    def test_lifecycle_fingerprint_observation_reorg_fails_without_checkpoint(self):
        original = self.rpc.call
        def call(method, params):
            result = original(method, params)
            if method == 'eth_call' and params[0]['data'][:10] == calldata('metadataLifecycleFingerprint(uint256)', 0)[:10]:
                self.rpc.blocks[99] = '0x' + '88' * 32
            return result
        self.rpc.call = call
        with patch.object(self.k, 'submit') as submit, self.assertRaises(RpcError):
            self.k._refresh_metadata()
        submit.assert_not_called()
        self.assertEqual(self.k.state['metadata_refresh']['notified'], {})

    def test_corrupt_disabled_identity_fails_typed_without_rewriting_journal(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['metadata_refresh'] = {'enabled': False}
        for value in (None, [], 'invalid'):
            with self.subTest(value=value):
                self.k.state['metadata_refresh']['identity'] = value
                self.k.save()
                before = self.k.path.read_bytes()
                with self.assertRaises(ValueError): Keeper(cfg, rpc=self.rpc)
                self.assertEqual(self.k.path.read_bytes(), before)

    def test_stored_lifecycle_version_requires_exact_integer_not_float_alias(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['metadata_refresh'] = {'enabled': False}
        for value in (2.0, '2', True, None, 0):
            with self.subTest(value=value):
                self.k.state['metadata_refresh']['identity']['metadata_lifecycle_version'] = value
                self.k.save()
                before = self.k.path.read_bytes()
                with self.assertRaises(ValueError): Keeper(cfg, rpc=self.rpc)
                self.assertEqual(self.k.path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
