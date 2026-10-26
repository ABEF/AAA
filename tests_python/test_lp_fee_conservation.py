"""Current LP-only earnings conservation, with actual SQLite/API composition.

No public RPC, funds, signing or persistent operator database is accessed.
Legacy replay remains explicit rather than inferring a new event grammar.
"""
import copy
import json
import unittest

import tests_python.test_earnings as fixtures
from frontend_api.earnings_replay import Replay, SCALE
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection
from zzz_ops.abi import keccak256

addr, words = fixtures.addr, fixtures.words


class CurrentFeeConservationAPITests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EarningsAPITests('test_collection_and_nft_reconcile_exact_confirmed_history')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.cfg = copy.deepcopy(self.fixture.cfg)
        self.rpc, self.index = self.fixture.rpc, self.fixture.index
        self.cfg.update(accounting_version=3, fee_intake_version=1)
        self.rpc.put(addr(3), 'ACCOUNTING_VERSION()', values=(3,))
        self.rpc.put(addr(7), 'SCHEMA()', values=(
            '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4').hex(),))
        self.rpc.put(addr(1), 'GOVERNANCE_VERSION()', values=(2,))
        self.rpc.put(addr(1), 'governance()', values=(addr(70),))
        self.rpc.put(addr(40), 'FEE_INTAKE_VERSION()', values=(1,))
        self.rpc.put(addr(40), 'dust(uint256,address)', (5, addr(20)), (0,))
        self.rpc.put(addr(4), 'assetCount()', values=(3,))
        for n, asset in enumerate((ZERO, addr(20), addr(21))):
            self.rpc.put(addr(4), 'assets(uint256)', (n,), (asset,))
        identifier = self.rpc.nft_id
        fixtures.native_put(self.rpc, addr(4), 'ownerIndex(uint256,address)', (5, ZERO), (0,))
        fixtures.native_put(self.rpc, addr(4), 'index(address)', (ZERO,), (0,))
        fixtures.native_put(self.rpc, addr(4), 'claimable(uint256,address)', (identifier, ZERO), (0,))

    def projection(self):
        return Projection(self.cfg, self.rpc, clock=lambda: 1000)

    def read(self, identifier=None):
        return self.projection().earnings(identifier)

    def fee_row(self):
        return self.index.db.execute('SELECT rowid,raw FROM logs WHERE address=? AND block_number=20',
                                     (addr(40),)).fetchone()

    def test_current_collection_rejects_forged_gross_while_chain_indexes_are_unchanged(self):
        original = self.read()
        self.assertEqual(next(r for r in original['all_time'] if r['asset'] == addr(20))['lp_processed_raw'], '100')
        rowid, raw = self.fee_row()
        event = json.loads(raw)
        event['data'] = words(200, 0)
        # Owner/collective indexes and all actual claimable views remain80/10.
        # Only the fee event is corrupted: it must not invent200gross/10+10reserves.
        with self.index.db:
            self.index.db.execute('UPDATE logs SET raw=? WHERE rowid=?', (json.dumps(event), rowid))
        with self.assertRaises(HistoryError):
            self.read()

    def test_current_nft_and_wallet_reject_missing_allocation_even_when_views_match(self):
        identifier = self.rpc.nft_id
        with self.index.db:
            self.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=20', (addr(40),))
        for reader in (lambda: self.read(str(identifier)),
                       lambda: self.projection().wallet_earnings(addr(30), 99, 0)):
            with self.subTest(reader=reader), self.assertRaises(HistoryError):
                reader()

    def test_current_earnings_checks_actual_fee_intake_version_before_replay(self):
        self.rpc.put(addr(40), 'FEE_INTAKE_VERSION()', values=(0,))
        with self.assertRaises(HistoryError):
            self.read()

    def test_current_valid_collection_and_nft_keep_net_rewards_and_gross_separate(self):
        collection = self.read()
        nft = self.read(str(self.rpc.nft_id))
        gross = next(r for r in collection['all_time'] if r['asset'] == addr(20))
        holder = next(r for r in nft['all_time'] if r['asset'] == addr(20))
        self.assertEqual([gross[k] for k in ('lp_processed_raw', 'lp_owner_allocated_raw',
            'lp_collective_allocated_raw', 'lp_compounding_allocated_raw', 'lp_buyback_allocated_raw')],
            ['100', '80', '10', '5', '5'])
        self.assertEqual([holder['lp_individual_raw'], holder['lp_collective_raw']], ['80', '10'])
        self.assertEqual(next(r for r in nft['all_time'] if r['asset'] == ZERO)['royalties_raw'], '100')


class StrictFeeReplayTests(unittest.TestCase):
    def model(self, target=None, *, strict=True, weight=1):
        model = Replay(100000, target)
        model.begin(fixtures.ROLES, [ZERO, addr(20)], [ZERO], fee_intake_version=1 if strict else 0)
        fixtures.consume(model, fixtures.event('royalties', 'AssetAdded', (ZERO,), (0,), 10), 100)
        fixtures.consume(model, fixtures.event('nft', 'Transfer', (ZERO, addr(30), 11), (), 11), 100)
        fixtures.consume(model, fixtures.event('membership', 'MembershipActivated', (11,), (), 12), 100)
        fixtures.consume(model, fixtures.event('royalties', 'Activated', (11,), (weight,), 12, 1), 100)
        fixtures.consume(model, fixtures.event('vault', 'SharesAdded', (11, 5), (100, 100), 12, 2), 100)
        return model

    def feed(self, model, role, name, indexed, data, *, block=20, index=0, tx=None, timestamp=99990):
        event = fixtures.event(role, name, indexed, data, block, index)
        if tx is not None:
            event['transactionHash'] = fixtures.h(tx)
        fixtures.consume(model, event, timestamp)

    def test_strict_matches_multiple_allocations_zero_distribution_and_dust_by_receipt(self):
        model = self.model(11)
        self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (0, 19), index=0)
        # One new raw unit plus19carried dust funds16/2/1/1.
        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (16, 2), index=1)
        # Unrelated royalties may occur between the actual matching pair.
        self.feed(model, 'royalties', 'RoyaltiesReceived', (ZERO,), (7, 1), index=2)
        self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (20, 0), index=3)
        self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (0, 7), index=4)
        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (7, 0), index=5)
        self.feed(model, 'fees', 'MembershipDustSettled', (5, ZERO), (7,), index=6)
        model.finish()
        self.assertEqual([model.totals[k, ZERO] for k in ('lp_processed', 'lp_owner_allocated',
            'lp_collective_allocated', 'lp_compounding_allocated', 'lp_buyback_allocated')], [27, 23, 2, 1, 1])
        self.assertEqual(model.totals['lp_individual', ZERO], 23)
        self.assertEqual(model.totals['lp_collective', ZERO], 2)
        self.assertEqual(model.totals['royalties', ZERO], 7)

    def test_strict_rejects_unmatched_wrong_duplicate_and_cross_transaction_credits(self):
        for fault in ('missing_credit', 'wrong_split', 'duplicate_credit', 'different_transaction',
                      'different_asset', 'unmatched_credit'):
            with self.subTest(fault=fault):
                model = self.model()
                with self.assertRaises(HistoryError):
                    if fault != 'missing_credit':
                        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO),
                                  (79, 11) if fault == 'wrong_split' else (80, 10))
                    if fault == 'duplicate_credit':
                        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (80, 10), index=1)
                    if fault != 'unmatched_credit':
                        self.feed(model, 'fees', 'FeesAllocated', (5, addr(20) if fault == 'different_asset' else ZERO),
                                  (100, 0), index=2, tx=999 if fault == 'different_transaction' else None)
                    model.finish()

    def test_strict_nft_math_keeps_lp_share_collective_and_royalty_rarity_independent(self):
        models = {identifier: self.model(identifier, weight=3) for identifier in (11, 22, 33)}
        for model in models.values():
            for n, (identifier, shares, weight) in enumerate(((22, 300, 1), (33, 200, 2))):
                block = 13 + n
                self.feed(model, 'nft', 'Transfer', (ZERO, addr(30), identifier), (), block=block, timestamp=100)
                self.feed(model, 'membership', 'MembershipActivated', (identifier,), (), block=block, index=1, timestamp=100)
                self.feed(model, 'royalties', 'Activated', (identifier,), (weight,), block=block, index=2, timestamp=100)
                self.feed(model, 'vault', 'SharesAdded', (identifier, 5), (shares, 100), block=block, index=3, timestamp=100)
            self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (480, 60))
            self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (600, 0), index=1)
            self.feed(model, 'royalties', 'RoyaltiesReceived', (ZERO,), (600, 1), index=2)
            model.finish()
        amounts = [[m.totals[k, ZERO] for k in ('lp_individual', 'lp_collective', 'royalties')]
                   for m in models.values()]
        # LP shares1:3:2 and rarity weights3:1:2 deliberately disagree.
        self.assertEqual(amounts, [[80, 20, 300], [240, 20, 100], [160, 20, 200]])
        self.assertEqual(sum(map(sum, amounts)), 1140)  #540netLP+600royalties;60reserved.
        for model in models.values():
            # A top-up only changes future individual LP weight (now4:3:2).
            self.feed(model, 'vault', 'SharesAdded', (11, 5), (300, 100), block=21, timestamp=99995)
            self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (720, 90), block=22, timestamp=99996)
            self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (900, 0), block=22, index=1, timestamp=99996)
            self.feed(model, 'royalties', 'RoyaltiesReceived', (ZERO,), (600, 1), block=22, index=2, timestamp=99996)
            model.finish()
            self.assertEqual(model.weights, {11: 3, 22: 1, 33: 2})
        later = [[m.totals[k, ZERO] for k in ('lp_individual', 'lp_collective', 'royalties')]
                 for m in models.values()]
        self.assertEqual(later, [[400, 50, 600], [480, 50, 200], [320, 50, 400]])
        self.assertEqual(sum(map(sum, later)), 2550)  #1350netLP+1200royalties;150reserved.

    def test_legacy_profile_stays_explicit_and_does_not_invent_new_grammar(self):
        model = self.model(11, strict=False)
        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (80, 10))
        model.finish()
        self.assertEqual(model.totals['lp_individual', ZERO] + model.totals['lp_collective', ZERO], 90)

    def test_strict_canonical_epoch_skips_imports_and_resets_only_observed_fee_keys(self):
        model = self.model(11)
        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (80, 10))
        self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (100, 0), index=1)
        self.feed(model, 'handoff', 'Frozen', (fixtures.h(1), addr(101)), (), block=21)
        self.feed(model, 'handoff', 'Retired', (fixtures.h(1), addr(101)), (fixtures.h(2),), block=22, index=3)
        model.finish()
        self.assertEqual(model.fee_keys, {(5, ZERO)})
        model.begin(fixtures.ROLES, [ZERO, addr(20)], [ZERO],
                    (22, fixtures.h(1022), fixtures.h(1), fixtures.h(2)), fee_intake_version=1)
        self.assertEqual(model.fee_keys, set())
        # Constructor/admission prefunds and imported ownership are not income,
        # new activations or a second mint of the same economic position.
        self.feed(model, 'royalties', 'AssetAdded', (ZERO,), (999,), block=10, timestamp=100)
        self.feed(model, 'nft', 'Transfer', (ZERO, addr(30), 11), (), block=11, timestamp=100)
        self.feed(model, 'handoff', 'Activated', (fixtures.h(1), addr(1)), (fixtures.h(2),), block=22, index=2)
        self.feed(model, 'rewards', 'PoolRewardsCredited', (5, ZERO), (16, 2), block=23, timestamp=99999)
        self.feed(model, 'fees', 'FeesAllocated', (5, ZERO), (20, 3), block=23, index=1, timestamp=99999)
        model.finish()
        self.assertEqual(model.fee_keys, {(5, ZERO)})
        self.assertEqual(model.fee_dust[5, ZERO], 3)
        self.assertEqual((len(model.minted), len(model.members), model.weights), (1, 1, {11: 1}))
        self.assertEqual([model.totals[key, ZERO] for key in
            ('lp_processed', 'lp_individual', 'lp_collective', 'lp_compounding_allocated', 'lp_buyback_allocated', 'royalties')],
            [123, 96, 12, 6, 6, 0])


class CurrentFeeDustAPITests(unittest.TestCase):
    def setUp(self):
        self.case = CurrentFeeConservationAPITests('test_current_valid_collection_and_nft_keep_net_rewards_and_gross_separate')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.case.rpc.put(addr(40), 'dust(uint256,address)', (5, addr(20)), (0,))

    def insert_event(self, event):
        block = int(event['blockNumber'], 16)
        event['blockHash'] = self.case.rpc.header(block)['hash']
        with self.case.index.db:
            self.case.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337, block, event['blockHash'], event['transactionHash'], int(event['logIndex'], 16),
                 event['address'], None, None, json.dumps(event)))

    def test_current_collection_nft_and_wallet_reject_false_carried_dust_with_same_indexes(self):
        rowid, raw = self.case.fee_row()
        event = json.loads(raw)
        event['data'] = words(100, 19)
        with self.case.index.db:
            self.case.index.db.execute('UPDATE logs SET raw=? WHERE rowid=?', (json.dumps(event), rowid))
        readers = (lambda: self.case.read(), lambda: self.case.read(str(self.case.rpc.nft_id)),
                   lambda: self.case.projection().wallet_earnings(addr(30), 99, 0))
        for reader in readers:
            with self.subTest(reader=reader), self.assertRaises(HistoryError):
                reader()

    def test_current_native_dust_is_reconciled_without_calling_untouched_currencies(self):
        self.insert_event(fixtures.event('rewards', 'PoolRewardsCredited', (5, ZERO), (16, 2), 22))
        self.insert_event(fixtures.event('fees', 'FeesAllocated', (5, ZERO), (20, 19), 22, 1))
        fixtures.native_put(self.case.rpc, addr(40), 'dust(uint256,address)', (5, ZERO), (19,))
        fixtures.native_put(self.case.rpc, addr(4), 'ownerIndex(uint256,address)', (5, ZERO), (16*SCALE//100,))
        fixtures.native_put(self.case.rpc, addr(4), 'index(address)', (ZERO,), (2*SCALE,))
        fixtures.native_put(self.case.rpc, addr(4), 'claimable(uint256,address)', (self.case.rpc.nft_id, ZERO), (18,))
        collection = self.case.read()
        nft = self.case.read(str(self.case.rpc.nft_id))
        row = next(row for row in collection['all_time'] if row['asset'] == ZERO)
        self.assertEqual([row[key] for key in ('lp_processed_raw', 'lp_owner_allocated_raw',
            'lp_collective_allocated_raw', 'lp_compounding_allocated_raw', 'lp_buyback_allocated_raw')],
            ['39', '16', '2', '1', '1'])
        holder = next(row for row in nft['all_time'] if row['asset'] == ZERO)
        self.assertEqual([holder[key] for key in ('lp_individual_raw', 'lp_collective_raw', 'royalties_raw')],
                         ['16', '2', '100'])
        # No dust getter is configured for admitted but untouched addr21: an
        # accidental all-bucket/all-currency sweep would fail this exact RPC.

    def test_legacy_profile_needs_no_new_fee_dust_getter(self):
        case = fixtures.EarningsAPITests('test_collection_and_nft_reconcile_exact_confirmed_history')
        case.setUp()
        self.addCleanup(case.tearDown)
        result = case.read()
        self.assertEqual(next(row for row in result['all_time'] if row['asset'] == addr(20))['lp_processed_raw'], '100')

