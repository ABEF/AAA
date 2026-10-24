"""Maintenance policy boundaries, using decoded contract transcripts, not signing."""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET
from tests_python import test_keeper as fixtures
from tests_python import test_keeper_native as native_fixtures
from zzz_ops.abi import calldata, keccak256


class KeeperMaintenancePolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PoolKeeperTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.k = self.fixture.k
        self.cfg = self.fixture.cfg
        self.fixture.ids = [7]
        self.fixture.rebalance = False
        self.k.maintenance = {'harvest': False}

    def test_configuration_rejects_ambiguous_boolean_and_liquidity_bounds(self):
        cases = [{name: value} for name in ('compound', 'compound_idle', 'harvest', 'sync_external_rewards')
                 for value in ('false', 0, 1, None)]
        cases += [{'minimum_liquidity': 1 << 128}, {'minimum_liquidity': True},
                  {'minimum_compound_units': 1 << 256},
                  {'compound_interval_seconds': 1}, {'compound_interval_seconds': 604801}]
        for settings in cases:
            with self.subTest(settings=settings), patch('keeper.monitor.subprocess.run') as signer:
                self.cfg['maintenance'] = settings
                with self.assertRaises(ValueError): Keeper(self.cfg, rpc=self.fixture.rpc)
                signer.assert_not_called()

    def test_thresholds_are_currency_specific_and_not_added_across_decimals(self):
        self.k.maintenance.update(compound_thresholds={fixtures.B: '1000000', fixtures.C: '1000000000000000000'})
        self.fixture.reserves = {fixtures.B: 999999, fixtures.C: 999999999999999999}
        self.fixture.invoke().assert_not_called()
        self.fixture.reserves[fixtures.B] += 1
        self.fixture.invoke().assert_called_once_with('compounder', 'compound(uint256,uint128,uint256)',
            (7, 1, self.fixture.rpc.now + 180), 'compound:7')

    def test_missing_currency_threshold_fails_closed_without_simulation(self):
        self.k.maintenance['compound_thresholds'] = {fixtures.B: '1000000'}
        self.fixture.reserves[fixtures.C] = 10**30
        self.fixture.invoke().assert_not_called()
        self.assertEqual(self.k.skipped_buckets, 1)

    def test_native_currency_is_explicit_and_versioned(self):
        self.cfg['accounting_version'] = 2
        self.cfg['maintenance'] = {'compound_thresholds': {NATIVE_ASSET: '1000000000000000'}}
        Keeper(self.cfg, rpc=self.fixture.rpc)
        self.cfg['accounting_version'] = 1
        with self.assertRaises(ValueError): Keeper(self.cfg, rpc=self.fixture.rpc)

    def test_bad_threshold_maps_fail_before_work(self):
        cases = ([], {}, {fixtures.B: 0}, {fixtures.B: True}, {fixtures.B: 1 << 256},
                 {'not-a-currency': 1}, {fixtures.B.upper(): 1})
        for value in cases:
            with self.subTest(value=value):
                self.cfg['maintenance'] = {'compound_thresholds': value}
                with self.assertRaises(ValueError): Keeper(self.cfg, rpc=self.fixture.rpc)

    def test_confirmed_compound_checkpoint_controls_optional_interval(self):
        self.k.maintenance.update(compound_interval_seconds=3600)
        self.fixture.reserves[fixtures.B] = 100
        self.k.state['last']['compound:7'] = self.fixture.rpc.now - 3599
        self.fixture.invoke().assert_not_called()
        self.k.state['last']['compound:7'] -= 1
        self.fixture.invoke().assert_called_once()

    def test_rebalance_remains_eligible_during_compound_interval(self):
        self.k.maintenance['compound_interval_seconds'] = 3600
        self.k.state['last']['compound:7'] = self.fixture.rpc.now
        self.fixture.rebalance = True
        self.fixture.invoke().assert_called_once_with('vault', 'rebalance(uint256,uint128,uint256)',
            (7, 1, self.fixture.rpc.now + 180), 'rebalance:7')

    def test_retired_bridge_configuration_and_direct_submission_are_rejected(self):
        self.cfg['maintenance'] = {'reward_routes': [{'token': fixtures.B}]}
        with self.assertRaisesRegex(ValueError, 'retired'): Keeper(self.cfg, rpc=self.fixture.rpc)
        with patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaisesRegex(ValueError, 'retired'):
                self.k.submit('fees', 'bridgeRewards(uint256,address,bytes32)',
                    (7, fixtures.B, fixtures.H), 'bridge:7')
            signer.assert_not_called()
        self.assertIsNone(self.k.state['pending'])

    def test_pending_receipt_recovery_survives_retired_route_configuration(self):
        base = fixtures.KeeperTests('runTest')
        base.setUp()
        self.addCleanup(base.doCleanups)
        base.receipt()
        base.k.state['pending']['key'] = 'bridge_rewards:7:'+fixtures.B
        base.k.state['pending']['data'] = calldata('bridgeRewards(uint256,address,bytes32)',7,fixtures.B,fixtures.H)
        base.rpc.tx['input'] = base.k.state['pending']['data']
        base.k.save()
        original_pending = copy.deepcopy(base.k.state['pending'])
        base.cfg['maintenance'] = {'reward_routes': [{'token': fixtures.B}]}
        recovered = Keeper(base.cfg, rpc=base.rpc)
        self.assertEqual(recovered.state['pending'], original_pending)
        with self.assertRaisesRegex(ValueError, 'retired'): recovered.cycle()
        self.assertIsNone(recovered.state['pending'])
        self.assertEqual(recovered.state['next_nonce'], original_pending['nonce'] + 1)
        with self.assertRaisesRegex(ValueError, 'retired'): recovered.cycle()
        self.assertIsNone(json.loads(recovered.path.read_text())['pending'])

    def test_empty_legacy_route_list_remains_compatible_and_never_reads_bridge(self):
        self.k.maintenance.update(reward_routes=[], compound=False)
        self.fixture.invoke().assert_not_called()
        forbidden = ('remoteIndividual(uint256,address)', 'remoteCollective(uint256,address)')
        selectors = {fixtures.calldata(signature, 7, fixtures.B)[:10] for signature in forbidden}
        self.assertFalse(any(method == 'eth_call' and params[0]['data'][:10] in selectors
                             for method, params in self.fixture.rpc.calls))


class KeeperIdleCompoundingPolicyTests(unittest.TestCase):
    """Opt-in capability reads use full ABI transcripts and ordinary submission."""
    def setUp(self):
        self.native = native_fixtures.NativeKeeperTests('runTest')
        self.native.setUp()
        self.addCleanup(self.native.doCleanups)
        self.fixture = self.native.f
        self.k = self.native.k
        self.rpc = self.native.rpc
        self.cfg = self.native.cfg
        self.budget = fixtures.C
        self.cfg['idle_compounding_budget'] = self.budget
        self.cfg['code_hashes']['idle_compounding_budget'] = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.k.maintenance = self.cfg['maintenance'] = {
            'compound_idle': True, 'compound_interval_seconds': 600, 'harvest': False,
            'compound_thresholds': {NATIVE_ASSET: str(10**15), fixtures.C: '1000000'}}
        self.fixture.reserves = {NATIVE_ASSET: 0, fixtures.C: 0}
        self.fixture.group_words[2] = 10**15
        self.feature = 1
        self.last = 0
        self.bound_budget = int(self.budget,16)
        self.bound_vault = int(self.k.contracts['vault'],16)
        self.code = '0x6000'
        original = self.rpc.call
        def call(method,params):
            if method == 'eth_getCode' and params[0] == self.budget: return self.code
            if method == 'eth_call' and 'from' not in params[0]:
                data = params[0]['data']
                values = {calldata('migrationBudget()'): self.bound_budget}
                if params[0]['to'] == self.budget:
                    values = {calldata('vault()'): self.bound_vault,
                              calldata('IDLE_COMPOUNDING_VERSION()'): self.feature,
                              calldata('lastCompound(uint256)',7): self.last}
                if data in values:
                    self.rpc.calls.append((method,params))
                    return '0x'+f'{values[data]:064x}'
            return original(method,params)
        self.rpc.call = call

    def test_idle_only_schedules_same_compound_without_raw_balance_or_outgoing_value(self):
        self.fixture.invoke().assert_called_once_with('compounder', 'compound(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'compound:7')
        self.assertFalse(any(method == 'eth_getBalance' for method,_ in self.rpc.calls))
        self.assertIsNone(self.k.state['pending'])

    def test_idle_does_not_schedule_by_default_or_below_each_currency_threshold(self):
        self.k.maintenance['compound_idle'] = False
        self.fixture.invoke().assert_not_called()
        self.k.maintenance['compound_idle'] = True
        self.fixture.group_words[2] -= 1
        self.fixture.group_words[3] = 999999
        self.fixture.invoke().assert_not_called()

    def test_idle_and_released_reserve_can_reach_same_currency_threshold_together(self):
        self.fixture.group_words[2] -= 1
        self.fixture.reserves[NATIVE_ASSET] = 1
        self.fixture.invoke().assert_called_once()

    def test_chain_checkpoint_from_another_keeper_and_stronger_pool_cooldown_are_respected(self):
        self.fixture.config_words[11] = 3600
        self.last = self.rpc.now - 3599
        self.fixture.invoke().assert_not_called()
        self.last -= 1
        self.fixture.invoke().assert_called_once()

    def test_wrong_runtime_capability_parent_or_unrepresentable_checkpoint_fails_closed(self):
        for field,value in (('code','0x6001'),('feature',2),('bound_budget',int(fixtures.A,16)),
                            ('bound_vault',int(fixtures.A,16)),('last',1 << 64)):
            with self.subTest(field=field):
                original = getattr(self,field)
                setattr(self,field,value)
                self.fixture.invoke().assert_not_called()
                setattr(self,field,original)
        self.assertIsNone(self.k.state['pending'])

    def test_opt_in_requires_explicit_threshold_interval_and_reviewed_pin(self):
        for field in ('compound_thresholds','compound_interval_seconds'):
            with self.subTest(field=field):
                original = self.k.maintenance.pop(field)
                with self.assertRaises(ValueError): Keeper(self.cfg,rpc=self.rpc)
                self.k.maintenance[field] = original
        original = self.cfg['code_hashes'].pop('idle_compounding_budget')
        with self.assertRaises(ValueError): Keeper(self.cfg,rpc=self.rpc)
        self.cfg['code_hashes']['idle_compounding_budget'] = original

    def test_pause_and_preparation_never_read_idle_capability_or_schedule(self):
        for field in ('paused','preparing'):
            with self.subTest(field=field):
                self.rpc.calls.clear()
                setattr(self.fixture,field,True)
                self.fixture.invoke().assert_not_called()
                self.assertFalse(any(method == 'eth_call' and params[0]['data'] == calldata('IDLE_COMPOUNDING_VERSION()')
                                     for method,params in self.rpc.calls))
                setattr(self.fixture,field,False)


if __name__ == '__main__': unittest.main()
