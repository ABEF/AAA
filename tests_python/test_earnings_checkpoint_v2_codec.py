"""Raw checkpoint2 LP codec controls; no provider, service or contract writes."""
import copy
import json
import time
import unittest

from frontend_api.earnings_checkpoint_v2 import capture, validate, restore, SHARED_FIELDS, MAX_NODE
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_replay import Replay, SCALE
from frontend_api.history import HistoryError, ZERO
from tests_python.test_exact_lp_backend import Feed, IDS, ROLES, ZZZ, OWNER
from zzz_ops.exact_lp import Tree, UINT, Q, LEAVES
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget, request_scope


DORMANT = IDS[1]+1
EXACT_ATTRIBUTES = {'owner_trees', 'collective_tree', 'direct', 'ordinals', 'lp_orphaned'}
COLLECTION_MEASUREMENT = {}


class AllFeed(Feed):
    def __init__(self):
        self.roles = dict(ROLES)
        self.model = ExactReplay(200000, track_all=True)
        self.model.begin(self.roles, [ZERO, ZZZ], [ZERO], fee_intake_version=1, royalty_settlement_version=4)
        self.index = 0
        self.tx = 1
        self.emit('royalties', 'AssetAdded(address,uint256)', [ZERO], [0])


def populated():
    feed = AllFeed()
    for identifier in (*IDS, DORMANT):
        feed.mint(identifier)
    feed.activate(IDS[0], 1)
    feed.activate(IDS[1], 2)
    feed.fees(ZERO)
    feed.fees(ZZZ)
    feed.grow(IDS[0], 3)
    feed.fees(ZERO)
    feed.fees(ZZZ)
    feed.emit('royalties', 'RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
              [ZERO], [5, 2, 2, 0, 1])
    feed.emit('royalties', 'RoyaltiesReceived(address,uint256,bool)', [ZERO], [5, 1])
    feed.model.finish()
    return feed


def shared(model):
    return {name: copy.deepcopy(getattr(model, name)) for name in SHARED_FIELDS}


def copied_base(source):
    target = ExactReplay(source.timestamp, track_all=True)
    for name, value in source.__dict__.items():
        if name not in EXACT_ATTRIBUTES:
            setattr(target, name, copy.deepcopy(value))
    return target


def check(state, model, *, base=None, accounts=None):
    validate(state, shared(model) if base is None else base, [ZERO, ZZZ],
             model.accounts if accounts is None else accounts)


class EarningsCheckpointV2CodecTests(unittest.TestCase):
    def test_raw_phase_pending_and_future_credit_growth_claim_roundtrip(self):
        feed = populated()
        state = capture(feed.model)
        self.assertTrue(any(phase != (0, 0) for tree in feed.model.owner_trees.values()
                            for book in tree.carry for phase in book.values()))
        self.assertTrue(any(tree.pending[0] for tree in feed.model.owner_trees.values()))
        before = capture(feed.model)
        target = copied_base(feed.model)
        restore(target, state)
        self.assertEqual(before, capture(feed.model))
        self.assertEqual(state, capture(target))
        other = copy.copy(feed)
        other.model = target
        for current in (feed, other):
            current.grow(IDS[1], 7)
            current.fees(ZERO, units=3)
            current.fees(ZZZ, units=2)
            for identifier in IDS:
                own, collective = current.model.components(identifier, ZZZ)
                current.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
                             [identifier, ZZZ], [own, collective, own, collective])
                amount = sum(current.model.components(identifier, ZERO))
                current.emit('rewards', 'Claimed(uint256,address,address,uint256)',
                             [identifier, ZERO, OWNER], [amount])
        self.assertEqual(capture(feed.model), capture(target))
        self.assertEqual(feed.model.accounts, target.accounts)
        self.assertEqual(feed.model.account_totals, target.account_totals)
        self.assertEqual(feed.model.totals, target.totals)

    def test_dense_zero_nodes_are_preserved_without_settling(self):
        feed = populated()
        tree = feed.model.owner_trees[7]
        for node in range(1, MAX_NODE+1):
            tree.weights.setdefault(node, 0)
            for book in (0, 1):
                tree.pending[book].setdefault(node, 0)
                if node < LEAVES:
                    tree.carry[book].setdefault(node, (0, 0))
        state = capture(feed.model)
        target = copied_base(feed.model)
        restore(target, state)
        self.assertEqual(state, capture(target))
        self.assertEqual(len(target.owner_trees[7].weights), MAX_NODE)

    def test_capture_restore_and_request_copies_do_not_share_mutable_books(self):
        model = populated().model
        state = capture(model)
        first, second = copied_base(model), copied_base(model)
        restore(first, state)
        restore(second, state)
        first.owner_trees[7].take(0, 1)
        first.direct[IDS[0], ZERO][0] = 2
        self.assertEqual(state, capture(second))
        self.assertEqual(state, capture(model))
        state['owner_trees'][7]['outstanding'][0] += 1
        self.assertNotEqual(state, capture(second))

    def test_capture_requires_exact_all_nft_original_profile(self):
        model = populated().model
        for attribute, bad in (('track_all', False), ('lower', (1, 'transaction')),
                               ('fee_intake_version', 0), ('royalty_settlement_version', 3)):
            candidate = copy.deepcopy(model)
            setattr(candidate, attribute, bad)
            with self.subTest(attribute=attribute), self.assertRaises(HistoryError):
                capture(candidate)
        with self.assertRaises(HistoryError):
            capture(Replay(200000, track_all=True))

    def test_capture_rejects_transient_sync_funding_royalty_and_custody_state(self):
        model = populated().model
        for attribute in ('pending_share_sync', 'pending_member_sync', 'pending_lp_credit',
                          'pending_exact_allocations', 'deferred', 'pending_recovery',
                          'royalty_custody', 'custody_ids'):
            candidate = copy.deepcopy(model)
            setattr(candidate, attribute, {1})
            with self.subTest(attribute=attribute), self.assertRaises(HistoryError):
                capture(candidate)
        for attribute, value in (('pending_lp_transaction', 'tx'), ('frozen', True), ('retired', True)):
            candidate = copy.deepcopy(model)
            setattr(candidate, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(HistoryError):
                capture(candidate)

    def test_missing_extra_or_pair_relabel_rejected(self):
        model = populated().model
        state = capture(model)
        for kind in ('missing', 'extra', 'third', 'reverse', 'list', 'uppercase'):
            candidate = copy.deepcopy(state)
            if kind == 'missing': del candidate['ordinals']
            elif kind == 'extra': candidate['owner_index'] = {}
            elif kind == 'third': candidate['pair'] = (ZERO, ZZZ, OWNER)
            elif kind == 'reverse': candidate['pair'] = (ZZZ, ZERO)
            elif kind == 'list': candidate['pair'] = [ZERO, ZZZ]
            else: candidate['pair'] = (ZERO, '0X'+'AB'*20)
            with self.subTest(kind=kind), self.assertRaises(HistoryError):
                check(candidate, model)

    def test_immutable_ordinal_mapping_rejects_swaps_missing_and_boolean(self):
        model = populated().model
        state = capture(model)
        for bad in ({}, {IDS[0]: 2, IDS[1]: 1, DORMANT: 3},
                    {IDS[0]: True, IDS[1]: 2, DORMANT: 3},
                    {IDS[0]: 1, IDS[1]: 2, DORMANT: 1001}):
            candidate = copy.deepcopy(state)
            candidate['ordinals'] = bad
            with self.subTest(bad=bad), self.assertRaises(HistoryError):
                check(candidate, model)

    def test_tree_weight_and_owner_inventory_must_match_shares(self):
        model = populated().model
        state = capture(model)
        for kind in ('root', 'leaf', 'bucket', 'missing', 'spare', 'boolean'):
            candidate = copy.deepcopy(state)
            if kind == 'root': candidate['owner_trees'][7]['weights'][1] += 1
            elif kind == 'leaf': candidate['owner_trees'][7]['weights'][LEAVES] += 1
            elif kind == 'bucket': candidate['owner_trees'][8] = candidate['owner_trees'].pop(7)
            elif kind == 'missing': candidate['owner_trees'] = {}
            elif kind == 'spare': candidate['owner_trees'][7]['weights'][MAX_NODE+1] = 0
            else: candidate['owner_trees'][7]['weights'][LEAVES] = True
            with self.subTest(kind=kind), self.assertRaises(HistoryError):
                check(candidate, model)

    def test_pending_units_and_outstanding_are_conserved(self):
        model = populated().model
        state = capture(model)
        for kind in ('amount', 'outstanding', 'empty_node', 'negative', 'overflow', 'shape'):
            candidate = copy.deepcopy(state)
            tree = candidate['owner_trees'][7]
            if kind == 'amount': tree['pending'][0][1] = tree['pending'][0].get(1, 0)+1
            elif kind == 'outstanding': tree['outstanding'][0] += 1
            elif kind == 'empty_node': tree['pending'][0][MAX_NODE] = 1
            elif kind == 'negative': tree['pending'][0][1] = -1
            elif kind == 'overflow': tree['outstanding'][0] = UINT+1
            else: tree['pending'] = list(tree['pending'])
            with self.subTest(kind=kind), self.assertRaises(HistoryError):
                check(candidate, model)

    def test_high_low_phase_bounds_empty_nodes_and_leaf_domain_are_strict(self):
        model = populated().model
        state = capture(model)
        for node, phase in ((1, (Q, 0)), (1, (0, state['owner_trees'][7]['weights'][1])),
                            (1, (-1, 0)), (1, (0, True)), (LEAVES, (0, 0)),
                            (LEAVES-1, (1, 0)), (1, [0, 0])):
            candidate = copy.deepcopy(state)
            candidate['owner_trees'][7]['carry'][0][node] = phase
            with self.subTest(node=node, phase=phase), self.assertRaises(HistoryError):
                check(candidate, model)

    def test_direct_components_minted_active_currency_and_backing_overflow(self):
        model = populated().model
        state = capture(model)
        for key, amounts in (((DORMANT, ZERO), [1, 0]), ((DORMANT+1, ZERO), [0, 0]),
                             ((IDS[0], OWNER), [1, 0]), ((IDS[0], ZERO), [True, 0]),
                             ((IDS[0], ZERO), [UINT, 0]), ((IDS[0], ZERO), (1, 0))):
            candidate = copy.deepcopy(state)
            candidate['direct'][key] = amounts
            with self.subTest(key=key, amounts=amounts), self.assertRaises(HistoryError):
                check(candidate, model)
        candidate = copy.deepcopy(state)
        candidate['direct'][DORMANT, ZERO] = [0, 0]
        check(candidate, model)

    def test_whole_accounts_reject_old_indices_fractions_and_third_lp_currency(self):
        model = populated().model
        state = capture(model)
        for name in ('owner_index', 'collective_index', 'royalty_index'):
            base = shared(model)
            base[name] = {ZERO: 1}
            with self.subTest(name=name), self.assertRaises(HistoryError):
                check(state, model, base=base)
        for metric, asset, amount in (('lp_individual', ZERO, 1), ('royalties', ZERO, SCALE-1),
                                      ('lp_collective', OWNER, SCALE)):
            accounts = copy.deepcopy(model.accounts)
            accounts[IDS[0]][metric, asset] = amount
            with self.subTest(metric=metric, asset=asset), self.assertRaises(HistoryError):
                check(state, model, accounts=accounts)
        accounts = copy.deepcopy(model.accounts)
        del accounts[DORMANT]
        with self.assertRaises(HistoryError):
            check(state, model, accounts=accounts)

    def test_empty_and_dormant_only_histories_do_not_invent_rights(self):
        for minted in (False, True):
            feed = AllFeed()
            if minted: feed.mint(DORMANT)
            state = capture(feed.model)
            self.assertEqual({}, state['owner_trees'])
            self.assertEqual([0, 0], state['collective_tree']['outstanding'])
            target = copied_base(feed.model)
            restore(target, state)
            self.assertEqual(state, capture(target))

    def test_uintmax_weight_and_pending_are_lossless_but_extra_backing_overflows(self):
        feed = AllFeed()
        feed.mint(IDS[0])
        feed.activate(IDS[0], UINT)
        feed.model.owner_trees[7].credit(0, UINT)
        state = capture(feed.model)
        target = copied_base(feed.model)
        restore(target, state)
        self.assertEqual(UINT, target.owner_trees[7].outstanding[0])
        state['orphaned'][ZERO] = 1
        with self.assertRaisesRegex(HistoryError, 'backing total overflow'):
            check(state, feed.model)

    def test_restore_requires_fresh_exact_books_and_independent_pair(self):
        model = populated().model
        state = capture(model)
        with self.assertRaises(HistoryError): restore(model, state)
        with self.assertRaises(HistoryError): restore(Replay(200000), state)
        target = copied_base(model)
        target.pair = (ZERO, OWNER)
        with self.assertRaises(HistoryError): restore(target, state)

    def test_codec_work_limits_propagate_without_partial_install(self):
        model = populated().model
        state = capture(model)
        target = copied_base(model)
        budget = Budget(clock=lambda: 0)
        budget.clock = lambda: 100
        with self.assertRaises(WorkLimit):
            with request_scope(budget): restore(target, state)
        self.assertEqual({}, target.owner_trees)
        self.assertEqual({}, target.ordinals)

    def test_full_collection_four_buckets_preserve_raw_phase_pending_and_direct(self):
        from frontend_api.earnings_checkpoint import encode, decode, MAX_BYTES, SHARED, Seed
        feed = AllFeed()
        identifiers = tuple(2**200+n for n in range(1, 1001))
        started = time.perf_counter()
        for identifier in identifiers:
            feed.mint(identifier)
        for ordinal, identifier in enumerate(identifiers[:900], 1):
            feed.activate(identifier, (ordinal % 37+1)*10**12+ordinal, 7+ordinal % 4)
        for bucket in range(7, 11):
            for asset in (ZERO, ZZZ):
                feed.fees(asset, bucket, units=12345+bucket)
        for identifier in identifiers[:4]:
            feed.grow(identifier, 7*10**12+1)
        for bucket in range(7, 11):
            for asset in (ZERO, ZZZ):
                feed.fees(asset, bucket, units=345+bucket)
        for identifier in identifiers[:4]:
            own, collective = feed.model.components(identifier, ZZZ)
            feed.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
                      [identifier, ZZZ], [own, collective, own, collective])
        feed.model.finish()
        construction_seconds = time.perf_counter()-started
        started = time.perf_counter()
        with request_scope(Budget()):
            state = capture(feed.model)
            capture_seconds = time.perf_counter()-started
            payload = dict(exact_lp=state, shared={name: copy.deepcopy(getattr(feed.model, name)) for name in SHARED},
                accounts=feed.model.accounts, emitters=feed.roles, lp_assets=[ZERO, ZZZ], royalty_assets=[ZERO],
                collection={k: v for k, v in feed.model.totals.items() if k[0].startswith('lp_') and
                            k[0] not in ('lp_individual', 'lp_collective')})
            phase_started = time.perf_counter()
            wire = json.dumps(encode(payload), separators=(',', ':')).encode('utf-8')
            encode_seconds = time.perf_counter()-phase_started
            self.assertLess(len(wire), MAX_BYTES)
            phase_started = time.perf_counter()
            decoded = decode(json.loads(wire))
            decode_seconds = time.perf_counter()-phase_started
            phase_started = time.perf_counter()
            validate(decoded['exact_lp'], decoded['shared'], [ZERO, ZZZ], decoded['accounts'])
            validate_seconds = time.perf_counter()-phase_started
            target = copied_base(feed.model)
            phase_started = time.perf_counter()
            restore(target, decoded['exact_lp'])
            restore_seconds = time.perf_counter()-phase_started
            self.assertEqual(state, capture(target))
        codec_seconds = time.perf_counter()-started
        selected = ExactReplay(200000, identifiers[0])
        selected.begin(feed.roles, [ZERO, ZZZ], [ZERO], fee_intake_version=1, royalty_settlement_version=4)
        seed = Seed('', dict(timestamp=100), {}, decoded, None, schema=2)
        phase_started = time.perf_counter()
        with request_scope(Budget()):
            seed.restore(selected)
        selected_restore_seconds = time.perf_counter()-phase_started
        self.assertEqual((identifiers[0],), selected.selected)
        self.assertEqual(1, len(selected.accounts))
        self.assertEqual(state['owner_trees'], {k: v.__dict__ for k, v in selected.owner_trees.items()})
        self.assertEqual(1000, len(target.ordinals))
        self.assertEqual(900, len(target.members))
        self.assertEqual(4, len(target.owner_trees))
        self.assertGreater(target.direct_liability(ZERO), 0)
        self.assertTrue(any(tree.pending[0] for tree in target.owner_trees.values()))
        self.assertTrue(any(phase != (0, 0) for tree in target.owner_trees.values()
                            for book in tree.carry for phase in book.values()))
        COLLECTION_MEASUREMENT.update(minted=1000, active=900, buckets=4,
            encoded_state_bytes=len(wire), artifact_limit_bytes=MAX_BYTES,
            construction_seconds=construction_seconds, capture_encode_decode_restore_seconds=codec_seconds,
            capture_seconds=capture_seconds, encode_seconds=encode_seconds, decode_seconds=decode_seconds,
            validate_seconds=validate_seconds, restore_seconds=restore_seconds,
            single_nft_common_seed_restore_seconds=selected_restore_seconds,
            local_request_budget_seconds=25, raw_dict_roundtrip=True,
            boundary='Controlled Python event/tree workload and validated seed restore only; excludes RPC/full HTTP latency/provider/target-gas and actual lifetime qualification.')


if __name__ == '__main__':
    unittest.main()
