"""Actual conversion-worker composition: malformed core flags are not healthy off.

Temporary journals and byte-level injected RPC only; no service, key or chain.
"""
from contextlib import contextmanager
import copy
import unittest
from unittest.mock import patch

import tests_python.test_royalty_keeper as legacy
import tests_python.test_typed_v4_conversion_keeper as native
from keeper.monitor import Keeper
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


PROFILES = ('v3_wrapper', 'v3_wrapper_configurable', 'v4_native')


class ConversionBooleanIntegrityTests(unittest.TestCase):
    @contextmanager
    def lab(self, profile, lp=False):
        fixture_type = native.TypedV4ConversionKeeperTests if profile == 'v4_native' else legacy.RoyaltyKeeperTests
        fixture = fixture_type('runTest')
        fixture.setUp()
        try:
            cfg = copy.deepcopy(fixture.cfg)
            cfg['royalty_conversion']['profile'] = profile
            if profile != 'v3_wrapper':
                cfg.update(accounting_version=3, fee_intake_version=1)
                converter = cfg['contracts']['royalty_converter']
                fixture.rpc.values[converter, calldata('MAX_LOSS_BPS()')] = 1000
                fixture.rpc.values[converter, calldata('conversionLossBps()')] = 100
            if lp:
                cfg['lp_conversion'] = cfg.pop('royalty_conversion')
                mapping = [('rewards', 'royalties'), ('lp_converter', 'royalty_converter'), ('lp_nft', 'royalty_nft')]
                mapping += [('lp_v4_executor', 'royalty_v4_executor')] if profile == 'v4_native' else [('lp_wrapper', 'royalty_wrapper')]
                for key, old in mapping:
                    cfg['contracts'][key] = cfg['contracts'][old]
                    cfg['code_hashes'][key] = legacy.PIN
                ledger = cfg['contracts']['rewards']
                fixture.rpc.values[ledger, calldata('access()')] = int(cfg['contracts']['access'], 16)
                fixture.rpc.values[cfg['contracts']['access'], calldata('module(bytes32)',
                    '0x'+keccak256(b'ZZZRewards').hex())] = int(ledger, 16)
                if profile != 'v4_native':
                    fixture.rpc.values[cfg['contracts']['oracle'], calldata('quote(address,address,uint256)',
                        fixture.rpc.asset, cfg['contracts']['lp_wrapper'], 300)] = 30000
            keeper = Keeper(cfg, rpc=fixture.rpc)
            worker = keeper.lp_rewards if lp else keeper.royalties
            yield keeper, fixture.rpc, worker
        finally:
            fixture.doCleanups()

    def test_noncanonical_converter_enabled_flag_raises_before_quote_or_submission(self):
        for profile in PROFILES:
            for lp in (False, True):
                with self.subTest(profile=profile, lp=lp), self.lab(profile, lp) as (keeper, rpc, worker):
                    rpc.values[keeper.contracts[worker.converter], calldata('enabled()')] = 2
                    with patch.object(keeper, 'submit') as submit, self.assertRaisesRegex(RpcError, 'boolean'):
                        worker.scan_once()
                    submit.assert_not_called()
                    self.assertIsNone(keeper.state['pending'])

    def test_noncanonical_route_flag_is_logged_as_deferred_not_a_healthy_disabled_cycle(self):
        for profile in PROFILES:
            for lp in (False, True):
                for value in (2, 2**256-1):
                    with self.subTest(profile=profile, lp=lp, value=value), self.lab(profile, lp) as (keeper, rpc, worker):
                        rpc.values[keeper.contracts[worker.converter], calldata('routeEnabled(bytes32)', rpc.route)] = value
                        with patch.object(keeper, 'submit') as submit, patch('keeper.monitor.log') as log:
                            self.assertFalse(keeper._convert_rewards(worker))
                        submit.assert_not_called()
                        self.assertEqual(keeper.blocked_actions, 1)
                        self.assertEqual(log.call_args.args[0], worker.key+'_deferred')
                        self.assertIsNone(keeper.state['pending'])

    def test_canonical_zero_stays_a_legitimate_stop_for_every_profile_and_ledger(self):
        for profile in PROFILES:
            for lp in (False, True):
                for getter in ('enabled()', 'routeEnabled(bytes32)'):
                    with self.subTest(profile=profile, lp=lp, getter=getter), self.lab(profile, lp) as (keeper, rpc, worker):
                        args = () if getter == 'enabled()' else (rpc.route,)
                        rpc.values[keeper.contracts[worker.converter], calldata(getter, *args)] = 0
                        with patch.object(keeper, 'submit') as submit, patch('keeper.monitor.log') as log:
                            self.assertFalse(keeper._convert_rewards(worker))
                        submit.assert_not_called()
                        log.assert_not_called()
                        self.assertEqual(keeper.blocked_actions, 0)
                        self.assertIsNone(keeper.state['pending'])

    def test_canonical_true_preserves_exact_batch_floor_and_gas_envelope(self):
        for profile in PROFILES:
            for lp in (False, True):
                with self.subTest(profile=profile, lp=lp), self.lab(profile, lp) as (keeper, rpc, worker):
                    with patch.object(keeper, 'submit', return_value=False) as submit:
                        self.assertFalse(worker.scan_once())
                    args = submit.call_args.args[2]
                    expected = (29701 if lp else 19801) if profile == 'v4_native' else (29700 if lp else 19800)
                    self.assertEqual(args, (rpc.asset, [1, 2, 3] if lp else [1, 2], rpc.route, expected, 100180))
                    self.assertEqual(submit.call_args.kwargs, {'maximum_cost': expected//100})
                    self.assertEqual(keeper.blocked_actions, 0)
                    self.assertIsNone(keeper.state['pending'])

    def test_balance_transport_outage_keeps_the_existing_deferred_path(self):
        with self.lab('v4_native') as (keeper, rpc, worker):
            rpc.fail = True
            with patch.object(keeper, 'submit') as submit, patch('keeper.monitor.log') as log:
                self.assertFalse(keeper._convert_rewards(worker))
            submit.assert_not_called()
            self.assertEqual(keeper.blocked_actions, 1)
            self.assertEqual(log.call_args.args[0], 'royalty_conversion_deferred')
            self.assertIsNone(keeper.state['pending'])
