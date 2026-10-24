"""Native accounting profile boundaries. All RPC/venue data are offline fixtures."""
import copy
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api.activation_config import ActivationConfig, NATIVE_ASSET_CODE_HASH
from frontend_api.activation_trace import selector, MINT, INCREASE
from frontend_api.earnings_prices import Prices
from frontend_api.lineage import Lineage
from frontend_api.service import Projection, ProjectionError, ZERO, Asset, Contract
from tests_python.test_frontend_api import MockRPC, configuration, addr, words
from tests_python.test_frontend_activation import ActivationRPC, USD
from tests_python.test_frontend_lineage import LineageRPC
from zzz_ops.abi import calldata, decode_words, keccak256

BLOCK = {'blockHash': '0x' + 'b' * 64, 'requireCanonical': True}


def native_data(signature, *args):
    safe = [addr(1) if x == ZERO else x for x in args]
    value = calldata(signature, *safe)
    for i, arg in enumerate(args):
        if arg == ZERO:
            start = 10 + 64 * i
            value = value[:start] + '0' * 64 + value[start + 64:]
    return value


class NativeActivationRPC(ActivationRPC):
    def __init__(self, **options):
        super().__init__(native=True, current=True, **options)
        self.put(addr(3), 'ACCOUNTING_VERSION()', values=(2,))
        self.put(addr(7), 'SCHEMA()', values=('0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2').hex(),))
        self.put(self.pins['pools'], 'accounting(bytes32)', (self.pool,), self.pool_values)
        self.put(self.pins['pools'], 'isNativePool(bytes32)', (self.pool,), (1,))
        policy = '0x' + 'd' * 64
        self.native_put(self.pins['activation_assets'], 'activePolicy(address)', (ZERO,), (policy,))
        self.put(self.pins['activation_assets'], 'policies(bytes32)', (policy,),
                 (ZERO, 1, NATIVE_ASSET_CODE_HASH, '0x' + 'e' * 64, 18, 1))
        self.native_put(self.pins['activation_assets'], 'value(address,uint256)',
                        (ZERO, self.original_amount), (100 * USD,))
        native_token = self.config['tokens'][0]
        native_token['address'] = ZERO
        native_token['code_hash'] = None
        self.native_put(self.pins['oracle'], 'feeds(address)', (ZERO,),
                        (native_token['feed'], 3600, 8, 18))
        self.native_put(self.pins['oracle'], 'price(address)', (ZERO,), (USD,))
        self.native_put(self.pins['oracle'], 'referenceX96(address,address)', (ZERO, addr(21)), (2**96,))

    def native_put(self, target, signature, args, values):
        self.responses[target, native_data(signature, *args)] = words(*values)

    def trace(self, tx):
        # Parent builds a full byte-level typed Entry trace. Change only the
        # native identity and value edges for the new accounting version.
        mutation = self.trace_mutation
        self.trace_mutation = None
        result = super().trace(tx)
        self.trace_mutation = mutation
        vault = result['calls'][0]
        vault['value'] = tx['value']
        mint = vault['calls'][0]
        args = decode_words('0x' + mint['input'][10:])
        mint['value'] = hex(int(args[3 if self.new_pool else 2], 16))
        event = decode_words(result['logs'][0]['data'])
        event[3] = '0' * 64
        result['logs'][0]['data'] = '0x' + ''.join(event)
        if mutation:
            mutation(result)
        return result


class NativeBackendBoundaryTests(unittest.TestCase):
    def service(self, **options):
        rpc = NativeActivationRPC(**options)
        config = configuration()
        config['accounting_version'] = 2
        p = Projection(config, rpc, clock=lambda: 1000)
        return rpc, p, ActivationTransactions(p, rpc.config)

    def test_accounting_profile_is_explicit_and_legacy_is_not_reinterpreted(self):
        rpc = ActivationRPC(native=True)
        p = Projection(configuration(), rpc, clock=lambda: 1000)
        self.assertEqual(p.accounting_version, 1)
        self.assertTrue(ActivationTransactions(p, rpc.config).prepare(rpc.request)['activation_ready'])
        for version in (True, False, 0, 3, '2', None):
            with self.subTest(version=version):
                cfg = configuration(); cfg['accounting_version'] = version
                with self.assertRaises(ValueError): Projection(cfg, MockRPC(), clock=lambda: 1000)

    def test_native_profile_checks_actual_vault_version_and_canonical_schema(self):
        for field, value in (('version', 1), ('schema', '0x' + 'a' * 64)):
            with self.subTest(field=field):
                rpc, p, svc = self.service()
                if field == 'version': rpc.put(addr(3), 'ACCOUNTING_VERSION()', values=(value,))
                else: rpc.put(addr(7), 'SCHEMA()', values=(value,))
                with self.assertRaises(ProjectionError): svc.prepare(rpc.request)

    def test_zero_is_a_typed_currency_never_a_contract_target_or_owner(self):
        rpc, p, _ = self.service()
        self.assertEqual(int(p._call(rpc.pins['oracle'], 'price(address)', ZERO, block=BLOCK)[0], 16), USD)
        with self.assertRaises(ProjectionError): p._call(ZERO, 'price(address)', ZERO, block=BLOCK)
        with self.assertRaises(ValueError): p._call(addr(2), 'ownerOf(address)', ZERO, block=BLOCK)
        legacy = Projection(configuration(), MockRPC(), clock=lambda: 1000)
        with self.assertRaises(ValueError): legacy._call(rpc.pins['oracle'], 'price(address)', ZERO, block=BLOCK)

    def test_native_activation_growth_and_new_lp_have_exact_value_without_wrapper_reads(self):
        for options in ({}, {'increase': True}, {'new_pool': True}):
            with self.subTest(options=options):
                rpc, p, svc = self.service(**options)
                result = svc.prepare(rpc.request)
                self.assertTrue(result['activation_ready'])
                self.assertEqual(result['transaction']['value'], hex(rpc.original_amount))
                self.assertEqual(result['source']['asset'], ZERO)
                self.assertEqual(result['provenance']['accounting_version'], 2)
                self.assertEqual(result['execution_limit_bps'], 100)
                self.assertFalse(result['network_gas']['included_in_execution_loss'])
                self.assertFalse(any(method == 'eth_getCode' and params[0] == ZERO for method, params in rpc.calls))
                self.assertFalse(any(method == 'eth_call' and params[0]['to'] == ZERO for method, params in rpc.calls))
                wrapper_selector = selector('WETH9()')
                self.assertFalse(any(method == 'eth_call' and params[0]['data'].startswith(wrapper_selector)
                                     for method, params in rpc.calls))

    def test_native_child_calls_cannot_hide_missing_extra_or_unrelated_value(self):
        mutations = [lambda trace: trace['calls'][0].update(value='0x0'),
                     lambda trace: trace['calls'][0].update(value=hex(100 * USD + 1)),
                     lambda trace: trace['calls'][0]['calls'][0].update(value='0x0'),
                     lambda trace: trace['calls'][0]['calls'][0].update(value=hex(1001))]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)):
                rpc, _, svc = self.service(); rpc.trace_mutation = mutation
                with self.assertRaises(ProjectionError): svc.prepare(rpc.request)

    def test_native_preparation_rejects_wrapped_identity_substitution_and_wrong_policy(self):
        for mutation in ('account', 'policy'):
            rpc, _, svc = self.service()
            if mutation == 'account':
                rpc.put(rpc.pins['pools'], 'accounting(bytes32)', (rpc.pool,), [addr(20)] + rpc.pool_values[1:])
            else:
                policy = '0x' + 'd' * 64
                rpc.put(rpc.pins['activation_assets'], 'policies(bytes32)', (policy,),
                        (ZERO, 1, rpc.digest(addr(20)), '0x' + 'e' * 64, 18, 1))
            with self.subTest(mutation=mutation), self.assertRaises(ProjectionError): svc.prepare(rpc.request)

    def test_native_currency_requires_no_runtime_pin_and_18_decimals(self):
        for key, value in (('code_hash', '0x' + 'e' * 64), ('decimals', 6)):
            rpc, p, _ = self.service()
            rpc.config['tokens'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): ActivationConfig(rpc.config, p)

    def test_native_slot_does_not_expand_the_32_erc20_inventory_limit(self):
        rpc, p, _ = self.service()
        template = copy.deepcopy(rpc.config['tokens'][1])
        config = copy.deepcopy(rpc.config)
        config['tokens'] = [copy.deepcopy(rpc.config['tokens'][0])]
        for i in range(32):
            config['tokens'].append(dict(template, address=addr(1000+i)))
        self.assertEqual(len(ActivationConfig(config, p).tokens), 33)
        config['tokens'][0] = dict(template, address=addr(2000))
        with self.assertRaises(ValueError): ActivationConfig(config, p)

    def test_native_earnings_feed_is_direct_eth_and_does_not_check_weth(self):
        rpc, p, _ = self.service()
        oracle = rpc.pins['oracle']; feed = rpc.config['tokens'][0]['feed']
        cfg = {'oracle': {'address': oracle, 'code_hash': rpc.digest(oracle)}, 'sequencer': None,
               'feeds': [{'asset': ZERO, 'priced_token': ZERO, 'token_code_hash': None,
                          'source': feed, 'source_code_hash': rpc.digest(feed), 'max_age': 3600, 'feed_decimals': 8}]}
        descriptors = {ZERO: Asset(ZERO, 18, 'ETH', None)}
        prices = Prices(cfg, p, descriptors).read(BLOCK)
        self.assertTrue(prices[ZERO]['available']); self.assertEqual(prices[ZERO]['priced_token'], ZERO)
        for key, value in (('priced_token', addr(20)), ('token_code_hash', '0x' + 'e' * 64)):
            bad = copy.deepcopy(cfg); bad['feeds'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): Prices(bad, p, descriptors)

    def test_native_lp_and_royalties_share_currency_without_double_counting_claims(self):
        from frontend_api.earnings_replay import Replay
        from tests_python.test_earnings import ROLES, event, consume, activate
        model = Replay(1000, 11)
        model.begin(ROLES, [ZERO, addr(21)], [ZERO])
        consume(model, event('royalties', 'AssetAdded', (ZERO,), (0,), 10))
        consume(model, event('nft', 'Transfer', (ZERO, addr(30), 11), (), 11))
        activate(model, 11, 100, weight=3)
        consume(model, event('fees', 'FeesAllocated', (5, ZERO), (100, 0), 20))
        consume(model, event('rewards', 'PoolRewardsCredited', (5, ZERO), (80, 10), 20, 1))
        consume(model, event('royalties', 'RoyaltiesReceived', (ZERO,), (100, 1), 21))
        model.finish()
        self.assertEqual([model.totals[key, ZERO] for key in ('lp_individual', 'lp_collective', 'royalties')], [80, 10, 99])
        # The 100/3 royalty global-index division leaves one fractional raw unit
        # reserved; claims and source->ETH conversion do not create new income.
        before = dict(model.totals)
        for signature in ('Claimed(uint256,address,address,uint256)',
                          'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)'):
            ignored = event('rewards', 'PoolRewardsCredited', (5, ZERO), (80, 10), 22)
            ignored['topics'][0] = '0x' + keccak256(signature.encode()).hex()
            consume(model, ignored)
        self.assertEqual(dict(model.totals), before)

    def test_native_lineage_requires_own_predecessor_profile_instead_of_inheritance(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = LineageRPC(Path(directory), count=2)
            config = copy.deepcopy(fixture.configs[-1]); config['accounting_version'] = 2
            old = fixture.configs[0]
            item = {key: copy.deepcopy(old[key]) for key in
                    ('deployment_block', 'deployment_block_hash', 'contracts', 'assets', 'history')}
            item['retirement_transaction_hash'] = '0x' + 'a' * 64
            current = Projection(config, fixture, clock=lambda: 1000)
            with self.assertRaises(ValueError): Lineage([item], current, config)
            item['accounting_version'] = 1
            actual = Lineage([item], current, config)
            self.assertEqual(actual.entries[0].projection.accounting_version, 1)
            self.assertIsNone(actual.entries[0].projection.earnings_history)
            self.assertIsNone(actual.entries[0].projection.royalty_reporting)
            item['accounting_version'] = 2
            actual = Lineage([item], current, config)
            self.assertEqual(actual.entries[0].projection.accounting_version, 2)
            fixture.close()


if __name__ == '__main__': unittest.main()
