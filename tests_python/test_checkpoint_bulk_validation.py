"""NEW differential checks for read-only checkpoint2 allocation traversal."""
import copy
import random
import unittest
from unittest.mock import patch

from frontend_api import earnings_checkpoint_v2 as codec
from frontend_api.earnings_replay import SCALE
from frontend_api.history import HistoryError, ZERO
from zzz_ops.errors import WorkLimit
from zzz_ops.exact_lp import Tree, UINT, Q, LEAVES, MAX_ORDINAL
from zzz_ops.work_budget import Budget, request_scope

ZZZ = '0x' + '12'*20


def original_per_leaf(tree, book, count):
    """The original validator's per-ordinal view calculation, not an old test."""
    return [tree.claimable(book, ordinal) for ordinal in range(1, count + 1)]


def new_tree(count):
    tree = Tree()
    for ordinal in range(1, count + 1):
        tree.set_weight(ordinal, ordinal % 19 + 1)
    if count:
        for book in (0, 1):
            tree.credit(book, 123456789123456789 + book)
            for ordinal in range(1, min(count, 9) + 1):
                tree.take(book, ordinal)
            tree.credit(book, 111111111111111111 + book)
        tree.set_weight(count, tree.weight_of(count) + 7)
    return tree


def new_state(count, buckets=4, *, dormant_every=7):
    identifiers = [(1 << 255) + 19*n + 3 for n in range(count)]
    owners, collective = {}, Tree()
    shares, totals, weights = {}, {}, {}
    for ordinal, identifier in enumerate(identifiers, 1):
        if dormant_every and ordinal % dormant_every == 0:
            continue
        bucket = (ordinal - 1) % buckets + 1
        amount = ordinal % 13 + 1
        shares[identifier] = (bucket, amount)
        totals[bucket] = totals.get(bucket, 0) + amount
        weights[identifier] = ordinal % 3 + 1
        owners.setdefault(bucket, Tree()).set_weight(ordinal, amount)
        collective.set_weight(ordinal, 1)
    for tree in (collective, *owners.values()):
        if not tree.total:
            continue
        active = [n for n in range(1, count + 1) if tree.weight_of(n)]
        for book in (0, 1):
            tree.credit(book, 10**20 + book + len(active))
            for ordinal in active[:3]:
                tree.take(book, ordinal)
            tree.credit(book, 101 + book)
    shared = dict(mints=identifiers, shares=shares, supply=totals,
                  members=set(shares), weights=weights, owner_index={},
                  collective_index={}, royalty_index={}, royalty_settlement_version=4)
    exact = dict(pair=(ZERO, ZZZ), ordinals={i: n for n, i in enumerate(identifiers, 1)},
                 owner_trees={b: copy.deepcopy(t.__dict__) for b, t in owners.items()},
                 collective_tree=copy.deepcopy(collective.__dict__), direct={}, orphaned={})
    accounts = {i: {} for i in identifiers}
    return exact, shared, [ZERO, ZZZ], accounts


class CheckpointBulkValidationTests(unittest.TestCase):
    def equivalent(self, tree, count):
        before = copy.deepcopy(tree.__dict__)
        for book in (0, 1):
            expected = original_per_leaf(tree, book, count)
            actual = codec._claimable_prefix(tree, book, count)
            self.assertEqual(actual, expected)
            self.assertEqual(sum(actual), tree.outstanding[book])
            self.assertEqual(tree.__dict__, before)

    def validate_like_original(self, state):
        before = copy.deepcopy(state)
        try:
            codec.validate(*state)
        except Exception as actual:
            with patch.object(codec, '_claimable_prefix', original_per_leaf):
                with self.assertRaises(type(actual)) as expected:
                    codec.validate(*state)
            self.assertEqual(str(actual), str(expected.exception))
        else:
            with patch.object(codec, '_claimable_prefix', original_per_leaf):
                self.assertIsNone(codec.validate(*state))
        self.assertEqual(state, before)

    def test_new_prefix_boundaries_match_every_original_leaf(self):
        for count in (0, 1, 2, 3, 17, 999, 1000):
            with self.subTest(count=count):
                self.equivalent(new_tree(count), count)

    def test_new_zero_ancestor_still_reads_pending_descendants(self):
        tree = Tree()
        for ordinal in (1, 2, 3):
            tree.set_weight(ordinal, ordinal)
        tree.credit(0, 31)
        tree.take(0, 1)
        self.assertEqual(tree.pending[0].get(1, 0), 0)
        self.assertTrue(any(node > 1 and amount for node, amount in tree.pending[0].items()))
        self.equivalent(tree, 3)
        self.assertGreater(sum(codec._claimable_prefix(tree, 0, 3)), 0)

    def test_new_phase_extremes_and_explicit_zero_entries_remain_valid(self):
        state = new_state(17)
        exact = state[0]
        for raw in (exact['collective_tree'], *exact['owner_trees'].values()):
            for book in (0, 1):
                for node, amount in raw['weights'].items():
                    if node < LEAVES and amount:
                        raw['carry'][book][node] = (Q - 1, amount - 1)
                raw['pending'][book][codec.MAX_NODE] = 0
                raw['carry'][book][LEAVES - 1] = (0, 0)
            raw['weights'][codec.MAX_NODE] = 0
        self.validate_like_original(state)

    def test_new_uint_boundaries_match_views_and_reject_path_overflow(self):
        tree = Tree()
        tree.set_weight(1, UINT - 1)
        tree.set_weight(2, 1)
        tree.credit(0, UINT)
        tree.credit(1, UINT)
        self.equivalent(tree, 2)
        bad = copy.deepcopy(tree)
        bad.pending[0][Tree.leaf(1)] = UINT
        before = copy.deepcopy(bad.__dict__)
        with self.assertRaises(ValueError):
            original_per_leaf(bad, 0, 2)
        with self.assertRaises(ValueError):
            codec._claimable_prefix(bad, 0, 2)
        self.assertEqual(bad.__dict__, before)

    def test_new_bulk_selection_rejects_invalid_books_and_counts(self):
        tree = new_tree(1)
        before = copy.deepcopy(tree.__dict__)
        for book, count in ((-1, 1), (2, 1), (True, 1), (0, -1),
                            (0, True), (0, 1.5), (0, MAX_ORDINAL + 1)):
            with self.subTest(book=book, count=count), self.assertRaises(ValueError):
                codec._claimable_prefix(tree, book, count)
        self.assertEqual(tree.__dict__, before)

    def test_new_thousand_nfts_four_buckets_and_dormant_rights(self):
        state = new_state(1000)
        self.assertEqual(len(state[0]['owner_trees']), 4)
        self.assertLess(len(state[1]['members']), len(state[1]['mints']))
        state[0]['ordinals'] = dict(reversed(list(state[0]['ordinals'].items())))
        self.validate_like_original(state)

    def test_new_varied_credits_claims_and_weight_changes_match_views(self):
        random_source = random.Random(20261123)
        tree = new_tree(17)
        for step in range(90):
            ordinal, book = random_source.randrange(1, 18), random_source.randrange(2)
            if step % 3 == 0:
                tree.set_weight(ordinal, random_source.randrange(1, 10001))
            elif step % 3 == 1:
                tree.credit(book, random_source.randrange(1, 10**24))
            else:
                tree.take(book, ordinal)
        self.equivalent(tree, 17)

    def test_new_malformed_checkpoint_guards_match_original_calculation(self):
        def ordinal_gap(state):
            identifier = state[1]['mints'][0]
            state[0]['ordinals'][identifier] = 1000

        def denominator(state):
            state[1]['supply'][1] += 1

        def wrong_weights(state):
            state[0]['owner_trees'][1]['weights'][1] += 1

        def invalid_pending(state):
            state[0]['collective_tree']['pending'][0][codec.MAX_NODE] = 1

        def invalid_high(state):
            state[0]['collective_tree']['carry'][0][1] = (Q, 0)

        def invalid_low(state):
            raw = state[0]['collective_tree']
            raw['carry'][0][1] = (0, raw['weights'][1])

        def bad_outstanding(state):
            state[0]['collective_tree']['outstanding'][0] += 1

        def overflowing_backing(state):
            state[0]['orphaned'][ZERO] = UINT

        def fractional_account(state):
            state[3][state[1]['mints'][0]][('lp_individual', ZERO)] = SCALE + 1

        def dormant_direct(state):
            state[0]['direct'][state[1]['mints'][6], ZERO] = [1, 0]

        for mutate in (ordinal_gap, denominator, wrong_weights, invalid_pending,
                       invalid_high, invalid_low, bad_outstanding, overflowing_backing,
                       fractional_account, dormant_direct):
            state = new_state(17)
            mutate(state)
            with self.subTest(mutation=mutate.__name__):
                with self.assertRaises(HistoryError):
                    codec.validate(*state)
                self.validate_like_original(state)

    def test_new_full_allocation_conservation_check_remains_required(self):
        state = new_state(3, buckets=1)
        with patch.object(codec, '_claimable_prefix', return_value=[0, 0, 0]):
            with self.assertRaisesRegex(HistoryError, 'assigned units differ'):
                codec.validate(*state)

    def test_new_node_work_checks_stop_without_mutating_any_book(self):
        tree = new_tree(1000)
        before = copy.deepcopy(tree.__dict__)

        class AdvancingClock:
            def __init__(self):
                self.value = 0

            def __call__(self):
                self.value += .1
                return self.value

        budget = Budget(seconds=1, clock=AdvancingClock())
        with self.assertRaises(WorkLimit) as failure:
            with request_scope(budget):
                codec._claimable_prefix(tree, 0, 1000)
        self.assertEqual(failure.exception.reason, 'deadline')
        self.assertEqual((budget.calls, budget.posts), (1024, 2048))
        self.assertEqual(tree.__dict__, before)

    def test_new_returned_lists_never_share_or_change_lp_state(self):
        tree = new_tree(17)
        before = copy.deepcopy(tree.__dict__)
        first = codec._claimable_prefix(tree, 0, 17)
        expected = original_per_leaf(tree, 0, 17)
        first[0] += 1
        second = codec._claimable_prefix(tree, 0, 17)
        self.assertEqual(second, expected)
        self.assertIsNot(first, second)
        self.equivalent(tree, 17)
        self.assertEqual(tree.__dict__, before)

    def test_new_empty_and_all_dormant_artifacts_keep_exact_zero_books(self):
        self.validate_like_original(new_state(0))
        self.validate_like_original(new_state(17, dormant_every=1))


if __name__ == '__main__':
    unittest.main()
