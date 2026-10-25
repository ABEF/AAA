"""Reject malformed log provenance before advancing a confirmed history cursor."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from indexer.monitor import Indexer, IndexerSafetyError
import tests_python.test_indexer as fixtures


class IndexerLogSafetyTests(unittest.TestCase):
    def seeded(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        chain = fixtures.Chain()
        chain.transfer(2, fixtures.B)
        config = {'chain_id': 1, 'start_block': 1, 'start_parent_hash': fixtures.h(0),
                  'confirmations': 2, 'block_chunk': 10, 'max_reorg_depth': 5,
                  'contracts': [fixtures.A],
                  'database': str(Path(temporary.name) / 'history.sqlite')}
        index = Indexer(config, chain)
        self.addCleanup(index.close)
        self.assertEqual(index.step(), 5)
        chain.head = 8
        event = {'address': fixtures.A, 'blockNumber': '0x6',
                 'blockHash': chain.blocks[6]['hash'], 'transactionHash': fixtures.h(106),
                 'logIndex': '0x0', 'topics': [fixtures.h(900)], 'data': '0x1234',
                 'removed': False}
        return index, chain, event

    @staticmethod
    def snapshot(index):
        return '\n'.join(index.db.iterdump())

    def rejected(self, modify, code='invalid_log'):
        index, chain, event = self.seeded()
        logs = modify(event)
        before = self.snapshot(index)
        original = chain.call
        def call(method, params):
            return copy.deepcopy(logs) if method == 'eth_getLogs' else original(method, params)
        with patch.object(chain, 'call', side_effect=call):
            try:
                with self.assertRaises(IndexerSafetyError) as caught:
                    index.step()
                self.assertEqual(caught.exception.code, code)
            finally:
                self.assertEqual(self.snapshot(index), before)
                self.assertEqual(index.next_block, 6)
                self.assertEqual(index.nft_owners(fixtures.A), {'7': fixtures.B})

    def test_hashes_require_complete_nonzero_rpc_identities(self):
        for field in ('transactionHash', 'blockHash'):
            for value in ('0x1', '0x' + '00' * 32, None, True, 'not-a-hash'):
                with self.subTest(field=field, value=value):
                    self.rejected(lambda event: [{**event, field: value}])

    def test_block_and_log_quantities_are_canonical_and_database_bounded(self):
        for field in ('blockNumber', 'logIndex'):
            for value in ('0x06', '-0x1', '0x-1', '0x', 6, True, None, hex(1 << 63)):
                with self.subTest(field=field, value=value):
                    self.rejected(lambda event: [{**event, field: value}])

    def test_raw_event_shape_is_strict_even_for_unknown_topics(self):
        cases = [('removed', value) for value in (None, 0, 'false', True)]
        cases += [('topics', value) for value in (None, '0x', [fixtures.h(900)] * 5,
                                                  ['0x1'], [False])]
        cases += [('data', value) for value in (None, '0x1', '0xzz', False)]
        cases += [('address', value) for value in (None, fixtures.C)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.rejected(lambda event: [{**event, field: value}])
        for value in (None, [], 'provider-error'):
            with self.subTest(item=value):
                self.rejected(lambda event: [value])
        self.rejected(lambda event: [{k: v for k, v in event.items() if k != 'removed'}])

    def test_oversized_unknown_raw_log_cannot_poison_history(self):
        self.rejected(lambda event: [{**event, 'provider_metadata': 'x' * 131072}])

    def test_block_log_identity_cannot_be_reused_with_another_transaction(self):
        for same_transaction in (True, False):
            with self.subTest(same_transaction=same_transaction):
                self.rejected(lambda event: [event, {**event, 'transactionHash':
                    event['transactionHash'] if same_transaction else fixtures.h(999)}],
                    'duplicate_log')

    def test_one_transaction_cannot_appear_in_two_blocks_of_one_batch(self):
        self.rejected(lambda event: [event, {**event, 'blockNumber': '0x7',
            'blockHash': fixtures.h(7), 'logIndex': '0x1'}], 'duplicate_log')

    def test_transaction_cannot_move_across_previously_stored_blocks(self):
        self.rejected(lambda event: [{**event, 'transactionHash': fixtures.h(102),
            'logIndex': '0x1'}], 'duplicate_log')

    def test_wellformed_unknown_anonymous_and_multilog_events_remain_available(self):
        index, chain, event = self.seeded()
        anonymous = {**event, 'topics': [], 'data': '0xabcd', 'logIndex': '0x1'}
        chain.logs = [event, anonymous]
        self.assertEqual(index.step(), 2)
        self.assertEqual(index.next_block, 8)
        rows = index.db.execute('SELECT event,decoded,raw FROM logs WHERE block_number=6 ORDER BY log_index').fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual([row[:2] for row in rows], [(None, None), (None, None)])
        self.assertEqual([json.loads(row[2]) for row in rows], [event, anonymous])
        self.assertEqual(index.nft_owners(fixtures.A), {'7': fixtures.B})


if __name__ == '__main__':
    unittest.main()
