"""Contradictory transaction provenance cannot advance or serve history."""
import copy
import json
import unittest

from frontend_api.history import HistoryError
from tests_python import test_frontend_history as history_fixtures
from tests_python import test_indexer_log_safety as log_fixtures
from tests_python import test_indexer as index_fixtures

h = history_fixtures.h


class TransactionIngressTests(unittest.TestCase):
    def rejected(self, modify, code='invalid_transaction_order'):
        fixture = log_fixtures.IndexerLogSafetyTests('runTest')
        try:
            fixture.rejected(modify, code)
        finally:
            fixture.doCleanups()

    def test_distinct_transactions_cannot_reuse_a_supplied_index(self):
        self.rejected(lambda e: [{**e, 'transactionIndex': '0x4'},
            {**e, 'transactionHash': h(999), 'logIndex': '0x1', 'transactionIndex': '0x4'}])

    def test_one_transaction_cannot_change_its_supplied_index(self):
        self.rejected(lambda e: [{**e, 'transactionIndex': '0x4'},
            {**e, 'logIndex': '0x1', 'transactionIndex': '0x5'}])

    def test_known_indices_cannot_decline_across_transactions(self):
        self.rejected(lambda e: [{**e, 'transactionIndex': '0x4'},
            {**e, 'transactionHash': h(999), 'logIndex': '0x1', 'transactionIndex': '0x3'}])

    def test_omitted_indices_still_occupy_a_distinct_transaction(self):
        self.rejected(lambda e: [{**e, 'transactionIndex': '0x4'},
            {**e, 'transactionHash': h(999), 'logIndex': '0x2'},
            {**e, 'transactionHash': h(998), 'logIndex': '0x4', 'transactionIndex': '0x5'}])

    def test_transaction_hash_cannot_reenter_after_another_transaction(self):
        self.rejected(lambda e: [e, {**e, 'transactionHash': h(999), 'logIndex': '0x2'},
            {**e, 'logIndex': '0x4', 'topics': []}])

    def test_optional_index_is_validated_even_on_anonymous_logs(self):
        for value in (None, True, 1, '0x00', '0x-1', hex(1 << 63)):
            with self.subTest(value=value):
                self.rejected(lambda e: [{**e, 'topics': [], 'transactionIndex': value}], 'invalid_log')

    def test_unordered_sparse_filtered_and_legacy_logs_remain_valid(self):
        fixture = log_fixtures.IndexerLogSafetyTests('runTest')
        try:
            index, chain, e = fixture.seeded()
            logs = [{**e, 'logIndex': '0x2', 'transactionIndex': '0x3'},
                {**e, 'logIndex': '0x4', 'transactionIndex': '0x3', 'topics': []},
                {**e, 'transactionHash': h(999), 'logIndex': '0x6'},
                {**e, 'transactionHash': h(998), 'logIndex': '0x9', 'transactionIndex': '0x7'},
                {**e, 'blockNumber': '0x7', 'blockHash': chain.blocks[7]['hash'],
                 'transactionHash': h(997), 'logIndex': '0x0', 'transactionIndex': '0x0'}]
            chain.logs = list(reversed(copy.deepcopy(logs)))
            self.assertEqual(index.step(), 2)
            self.assertEqual(index.next_block, 8)
            self.assertEqual(index.db.execute('SELECT count(*) FROM logs WHERE block_number>=6').fetchone()[0], 5)
            self.assertEqual(index.nft_owners(index_fixtures.A), {'7': index_fixtures.B})
        finally:
            fixture.doCleanups()


class TransactionStoredHistoryTests(unittest.TestCase):
    def fixture(self):
        fixture = history_fixtures.ConfirmedHistoryTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        return fixture

    @staticmethod
    def alter(fixture, rows):
        with fixture.index.db:
            fixture.index.db.execute('DELETE FROM logs WHERE block_number=20')
            for row in rows:
                fixture.insert(row)

    def block_logs(self, fixture):
        return [json.loads(row[0]) for row in fixture.index.db.execute(
            'SELECT raw FROM logs WHERE block_number=20 ORDER BY log_index')]

    def test_raw_rows_cannot_change_one_transactions_index(self):
        f = self.fixture(); rows = self.block_logs(f)
        for index, row in enumerate(rows): row['transactionIndex'] = hex(index)
        self.alter(f, rows)
        with self.assertRaisesRegex(HistoryError, 'transaction provenance'): f.read()

    def test_raw_rows_cannot_reuse_or_reverse_transaction_indices(self):
        for indices in ((4, 4), (4, 3)):
            with self.subTest(indices=indices):
                f = self.fixture(); rows = self.block_logs(f)
                for row, value in zip(rows, indices): row['transactionIndex'] = hex(value)
                rows[1]['transactionHash'] = h(999)
                self.alter(f, rows)
                with self.assertRaisesRegex(HistoryError, 'transaction provenance'): f.read()

    def test_raw_anonymous_rows_cannot_hide_hash_reentry_or_missing_index_conflicts(self):
        for mixed in (False, True):
            with self.subTest(mixed=mixed):
                f = self.fixture(); rows = self.block_logs(f)
                rows[1]['transactionHash'] = h(999)
                extra = {**rows[0], 'logIndex': '0x2', 'topics': [], 'data': '0x'}
                if mixed:
                    rows[0]['transactionIndex'] = '0x4'
                    extra.update(transactionHash=h(998), transactionIndex='0x5')
                self.alter(f, rows + [extra])
                with self.assertRaisesRegex(HistoryError, 'transaction provenance'): f.read()

    def test_raw_optional_index_is_strict_and_legacy_omission_remains_valid(self):
        f = self.fixture()
        before = dict(f.read().claims)
        rows = self.block_logs(f)
        rows[0]['transactionIndex'] = None
        self.alter(f, rows)
        with self.assertRaises(HistoryError): f.read()
        del rows[0]['transactionIndex']
        self.alter(f, rows)
        self.assertEqual(dict(f.read().claims), before)

    def test_callback_transfers_and_sparse_supplied_indices_preserve_claims(self):
        f = self.fixture(); before = f.read()
        rows = [json.loads(row[0]) for row in f.index.db.execute('SELECT raw FROM logs')]
        with f.index.db:
            for row in rows:
                row['transactionIndex'] = '0x7'
                f.index.db.execute('UPDATE logs SET raw=? WHERE transaction_hash=? AND log_index=?',
                    (json.dumps(row), row['transactionHash'], int(row['logIndex'], 16)))
        after = f.read()
        self.assertEqual(dict(after.claims), dict(before.claims))
        self.assertEqual(dict(after.owners), dict(before.owners))
        self.assertEqual(after.claims[f.rpc.nft_id, '0x'+'0'*40], (0, 7))


if __name__ == '__main__':
    unittest.main()
