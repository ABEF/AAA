"""Terminal adapter checks through the actual fresh7 reader and injected RPC.

No public RPC, transactions, running-chain changes, fee qualification or signer.
"""
import copy
import unittest

from frontend_api.service import Projection
from tests_python.test_frontend_api import addr, words
from tests_python import test_manual_lp_review as manual_fixture
from tests_python.test_native_backend_boundary import native_data
from zzz_ops import management_exit as E
from zzz_ops import operator_review as O
from zzz_ops.abi import calldata, decode_words, keccak256
from zzz_ops.errors import RpcError
from zzz_ops.management_base import ManagementBlocked, ManagementReader

H = '0x' + '12' * 32


class ManagementExitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = O.Catalog()

    def setUp(self):
        fixture = manual_fixture.ManualLPReviewTests('runTest')
        fixture.catalog = self.catalog
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.f, self.q, self.rpc = fixture.f, fixture.q, fixture.rpc
        self.p = Projection(self.f.config, self.rpc, clock=lambda: 4000)
        self.c = {role: item.address for role, item in self.p.contracts.items()}
        self.c.update(fixture.targets)
        self.extra, self.gov = fixture.extra, fixture.gov
        self.block = self.f.block()
        self.reader = ManagementReader(self.p, self.extra, self.block)
        self.ids = [self.f.rpc.nft_id, 2**255 + 19, 2**255 + 37]
        self.put('access', 'preparationNonce()', 0)
        self.put('access', 'preparationHash()', 0)
        self.put('vault', 'MAX_BUCKETS()', 4)
        self.put('vault', 'bucketCount()', 1)
        self.put('vault', 'bucketAt(uint256)', 7, 0)
        self.put('vault', 'bucketTotalShares(uint256)', 100, 7)
        self.put('nft', 'mintedCount()', 3)
        for ordinal, identifier in enumerate(self.ids, 1):
            self.put('nft', 'tokenAtOrdinal(uint256)', identifier, ordinal)
            self.put('nft', 'mintOrdinalOf(uint256)', ordinal, identifier)
            self.put('nft', 'ownerOf(uint256)', addr(30 if ordinal < 3 else 31), identifier)
            self.put('vault', 'sharesOf(uint256)', (25, 75, 0)[ordinal - 1], identifier)
            self.put('vault', 'nftBucket(uint256)', 7 if ordinal < 3 else 0, identifier)
            self.put('principal_exit', 'principalOf(uint256)', [0, 0, 0, 0], identifier)
        self.put('protocol_policy', 'payoutGas()', 180000)
        self.put(addr(20), 'balanceOf(address)', 10**18, self.c['principal_exit'])

    def put(self, role, signature, value, *args):
        target = self.c.get(role, role)
        values = value if isinstance(value, list) else [value]
        self.f.rpc.responses[target, native_data(signature, *args)] = words(*values)

    def selected(self, action, parameters):
        return {'action': action, 'parameters': E.validate(action, parameters), 'expires_at': 4180}

    def observe(self, action, parameters):
        return E.observe(self.reader, self.selected(action, parameters), self.gov)

    def terminal(self, phase):
        self.put('access', 'lpExitStarted()', 1)
        self.put('principal_exit', 'exitPhase()', phase)
        self.put('principal_exit', 'settlementBucketCount()', 1)
        self.put('principal_exit', 'settlementBucketAt(uint256)', 7, 0)
        self.put('principal_exit', 'exitMintedCount()', 3)
        self.put('principal_exit', 'exitReviewHash()', H)
        self.put('principal_exit', 'remainingBuckets()', 1 if phase == 1 else 0)
        self.put('principal_exit', 'allocationCursor()', 0 if phase == 1 else 1 if phase == 2 else 4)
        allocated = phase == 3
        row = [100, 0 if phase == 1 else 1000, 0 if phase == 1 else 2000,
            100 if allocated else 0, 1000 if allocated else 0, 2000 if allocated else 0, phase != 1]
        self.put('principal_exit', 'bucketSettlement(uint256)', row, 7)
        self.put('principal_exit', 'remainingETH()', 0 if phase == 1 else 1000)
        self.put('principal_exit', 'remainingZZZ()', 0 if phase == 1 else 2000)
        if allocated:
            for identifier, eth, zzz in zip(self.ids, (250, 750, 0), (500, 1500, 0)):
                self.put('principal_exit', 'principalOf(uint256)', [eth, zzz, 1, 0], identifier)
                self.put('principal_exit', 'claimablePrincipal(uint256)', [eth, zzz], identifier)

    def test_selection_bounds_and_irreversible_confirmation_are_explicit(self):
        good = {'confirm_terminal_exit': True}
        self.assertEqual(good, E.validate('collective_exit_begin', good))
        for action, parameters in [('collective_exit_begin', {'confirm_terminal_exit': 1}),
                ('collective_exit_begin', {'confirm_terminal_exit': False}),
                ('allocate_principal', {'maximum': '33'}), ('allocate_principal', {'maximum': '0'}),
                ('allocate_principal', {'maximum': 1}), ('close_bucket', {'bucket': '07', 'minimumETH': '0', 'minimumZZZ': '0'}),
                ('close_bucket', {'bucket': '7', 'minimumETH': '-1', 'minimumZZZ': '0'}),
                ('distribute_principal', {'nft_ids': ['1', '1']}),
                ('distribute_principal', {'nft_ids': []}),
                ('distribute_principal', {'nft_ids': [str(i) for i in range(1, 34)]}),
                ('distribute_principal', {'nft_ids': ['1'], 'recipient': addr(50)})]:
            with self.subTest(action=action, parameters=parameters), self.assertRaises((ValueError, TypeError)):
                E.validate(action, parameters)
        self.assertEqual([], self.rpc.simulations)

    def test_exact_selectors_arguments_and_array_order_match_catalog(self):
        cases = [('collective_exit_begin', {'confirm_terminal_exit': True}, 'beginCollectiveExit(bytes32)', ['reviewHash']),
            ('close_bucket', {'bucket': '7', 'minimumETH': '0', 'minimumZZZ': '19'},
                'closeBucket(uint256,uint256,uint256,uint256)', ['bucket', 'minimumETH', 'minimumZZZ', 'deadline']),
            ('allocate_principal', {'maximum': '32'}, 'allocatePrincipal(uint256)', ['maximum']),
            ('distribute_principal', {'nft_ids': ['77', '9']}, 'distributePrincipal(uint256[])', ['ids'])]
        catalog = O.Catalog()
        functions = next(c for c in catalog.data['contracts'] if c['name'] == 'ZZZMigration')['functions']
        for action, parameters, expected, names in cases:
            selected = self.selected(action, parameters)
            signature, args, data = E.call_spec(selected, {}, H)
            self.assertEqual(expected, signature)
            fn = next(fn for fn in functions if fn['signature'] == signature)
            self.assertEqual(names, [item['label'] for item in fn['inputs']])
            self.assertEqual(names, list(args))
            self.assertEqual('0x' + keccak256(signature.encode()).hex()[:8], data[:10])
            if action == 'distribute_principal':
                self.assertEqual([32, 2, 77, 9], [int(w, 16) for w in decode_words('0x' + data[10:])])
            elif action == 'close_bucket':
                self.assertEqual([7, 0, 19, 4180], [int(w, 16) for w in decode_words('0x' + data[10:])])

    def test_begin_authenticates_both_actual_legs_without_usd_or_operation_flags(self):
        self.rpc.price_failure = True
        self.q.config[6] = 0
        result = self.observe('collective_exit_begin', {'confirm_terminal_exit': True})
        self.assertTrue(result['controls']['irreversible'])
        physical = result['controls']['buckets'][0]['physical']
        self.assertEqual(2, len(physical['physical_legs']))
        self.assertEqual(124, physical['secondary_id'])
        self.assertNotIn('portfolio_amounts', physical)
        self.assertIn('physical_amounts', result['market_observations']['7'])
        selectors = {calldata('priceBounds(address)', addr(20))[:10], calldata('price(address)', addr(20))[:10]}
        self.assertFalse(any(m == 'eth_call' and p[0]['data'][:10] in selectors for m, p in self.rpc.calls))

    def test_begin_accepts_parked_principal_but_rejects_missing_funded_inventory(self):
        self.q.position[1] = 0
        self.q.position[7] = 4
        self.q.secondary = 0
        self.q.secondary_count = 0
        result = self.observe('collective_exit_begin', {'confirm_terminal_exit': True})
        self.assertNotIn('physical', result['controls']['buckets'][0])
        self.put('vault', 'bucketTotalShares(uint256)', 0, 7)
        with self.assertRaisesRegex(ValueError, 'Zero-share'):
            self.observe('collective_exit_begin', {'confirm_terminal_exit': True})

    def test_begin_rejects_uninventoried_residual_and_excess_minted_supply(self):
        self.q.secondary_count = 2
        with self.assertRaisesRegex(ValueError, 'omits a registered residual'):
            self.observe('collective_exit_begin', {'confirm_terminal_exit': True})
        self.q.secondary_count = 1
        self.put('nft', 'mintedCount()', 1001)
        with self.assertRaisesRegex(ValueError, 'bounded funded collection'):
            self.observe('collective_exit_begin', {'confirm_terminal_exit': True})

    def test_close_bucket_keeps_both_zero_raw_floors_and_checks_source_shares(self):
        self.terminal(1)
        self.rpc.price_failure = True
        chosen = self.selected('close_bucket', {'bucket': '7', 'minimumETH': '0', 'minimumZZZ': '0'})
        original = copy.deepcopy(chosen)
        result = E.observe(self.reader, chosen, self.gov)
        _, args, _ = E.call_spec(chosen, result, H)
        self.assertEqual('0', args['minimumETH'])
        self.assertEqual('0', args['minimumZZZ'])
        self.assertEqual(original, chosen)
        self.put('vault', 'bucketTotalShares(uint256)', 101, 7)
        with self.assertRaisesRegex(ValueError, 'Captured exit shares changed'):
            E.observe(self.reader, chosen, self.gov)

    def test_allocation_binds_exact_mint_order_and_includes_dormant_ordinal(self):
        self.terminal(2)
        self.put('access', 'paused()', 0)
        result = self.observe('allocate_principal', {'maximum': '32'})
        selected = result['controls']['selected_ordinals']
        self.assertEqual([str(x) for x in self.ids], [row['token_id'] for row in selected])
        self.assertEqual(['25', '75', '0'], [row['shares'] for row in selected])
        self.assertEqual('0', selected[-1]['bucket'])
        self.assertEqual(4, result['controls']['allocation_end_exclusive'])
        before = result['controls']
        self.put('principal_exit', 'allocationCursor()', 2)
        later = self.observe('allocate_principal', {'maximum': '32'})
        self.assertNotEqual(before, later['controls'])

    def test_allocation_rejects_duplicate_id_or_preallocated_ordinal(self):
        self.terminal(2)
        self.put('principal_exit', 'principalOf(uint256)', [0, 0, 1, 0], self.ids[0])
        with self.assertRaisesRegex(ValueError, 'already allocated'):
            self.observe('allocate_principal', {'maximum': '32'})
        self.put('principal_exit', 'principalOf(uint256)', [0, 0, 0, 0], self.ids[0])
        self.put('nft', 'tokenAtOrdinal(uint256)', self.ids[0], 2)
        with self.assertRaisesRegex(ValueError, 'ordinal identity'):
            self.observe('allocate_principal', {'maximum': '32'})

    def test_ready_requires_exact_completed_cumulative_settlement(self):
        self.terminal(3)
        self.put('principal_exit', 'bucketSettlement(uint256)', [100, 1000, 2000, 99, 990, 1980, 1], 7)
        with self.assertRaisesRegex(ValueError, 'not completely allocated'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
        self.terminal(2)
        self.put('principal_exit', 'bucketSettlement(uint256)', [100, 1000, 2000, 25, 249, 500, 1], 7)
        with self.assertRaisesRegex(ValueError, 'settlement'):
            self.observe('allocate_principal', {'maximum': '1'})

    def test_distribution_same_owner_multiple_nfts_preserves_zero_and_paid_classification(self):
        self.terminal(3)
        self.put('access', 'paused()', 0)
        self.put('principal_exit', 'principalOf(uint256)', [250, 500, 1, 1], self.ids[0])
        self.put('principal_exit', 'claimablePrincipal(uint256)', [0, 0], self.ids[0])
        self.put('principal_exit', 'remainingETH()', 750)
        self.put('principal_exit', 'remainingZZZ()', 1500)
        result = self.observe('distribute_principal', {'nft_ids': [str(i) for i in self.ids]})
        payout = result['controls']['payout']
        self.assertEqual(1, payout['eligible_count'])
        self.assertEqual(['already_paid', 'eligible', 'zero'], [r['status'] for r in payout['selected_entries']])
        self.assertEqual(payout['selected_entries'][0]['owner'], payout['selected_entries'][1]['owner'])
        self.assertEqual('current_owner_at_inclusion', payout['beneficiary_rule'])
        self.assertFalse(payout['all_selected_paid_guaranteed'])
        self.assertTrue(payout['rewards_and_royalties_not_included'])

    def test_distribution_transfer_changes_reviewed_controls_without_redirect_argument(self):
        self.terminal(3)
        parameters = {'nft_ids': [str(self.ids[0])]}
        before = self.observe('distribute_principal', parameters)
        self.put('nft', 'ownerOf(uint256)', addr(50), self.ids[0])
        after = self.observe('distribute_principal', parameters)
        self.assertNotEqual(before['controls'], after['controls'])
        _, arguments, _ = E.call_spec(self.selected('distribute_principal', parameters), after, H)
        self.assertEqual({'ids': [str(self.ids[0])]}, arguments)

    def test_distribution_refuses_unfunded_zero_only_bad_owner_and_view_conflicts(self):
        self.terminal(3)
        with self.assertRaisesRegex(ValueError, 'no unpaid nonzero'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[2])]})
        self.put('nft', 'ownerOf(uint256)', 1 << 160, self.ids[0])
        with self.assertRaisesRegex(ValueError, 'current NFT owner'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
        self.put('nft', 'ownerOf(uint256)', addr(30), self.ids[0])
        self.put('principal_exit', 'claimablePrincipal(uint256)', [249, 500], self.ids[0])
        with self.assertRaisesRegex(ValueError, 'claimable view'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
        self.put('principal_exit', 'claimablePrincipal(uint256)', [250, 500], self.ids[0])
        self.put('vault', 'sharesOf(uint256)', 0, self.ids[0])
        with self.assertRaisesRegex(ManagementBlocked, 'captured LP shares'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
        self.put('vault', 'sharesOf(uint256)', 25, self.ids[0])
        self.put(addr(20), 'balanceOf(address)', 1999, self.c['principal_exit'])
        with self.assertRaisesRegex(ManagementBlocked, 'fully backed') as failure:
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
        self.assertEqual('principal_backing_shortfall', failure.exception.code)

    def test_terminal_governance_lifecycle_and_contract_wallet_checks_are_real(self):
        self.terminal(3)
        for method, value in [('governance()', addr(41)), ('preparationActive()', 1), ('lpExitStarted()', 0)]:
            with self.subTest(method=method):
                old = self.f.rpc.responses[self.c['access'], calldata(method)]
                self.put('access', method, value)
                with self.assertRaises((ValueError, RpcError)):
                    self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})
                self.f.rpc.responses[self.c['access'], calldata(method)] = old
        self.rpc.governance_code = '0x6000'
        with self.assertRaisesRegex(ValueError, 'unsupported_contract_wallet_envelope'):
            self.observe('distribute_principal', {'nft_ids': [str(self.ids[0])]})


if __name__ == '__main__':
    unittest.main()
