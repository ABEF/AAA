"""A confirmed chunk must retain its depth and exact database predecessor."""
import unittest
from unittest.mock import patch

from indexer.monitor import Indexer, IndexerSafetyError
from tests_python import test_indexer as fixtures


class IndexerCommitGuardsTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.IndexerTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.index, self.chain = self.f.idx, self.f.chain

    def head_changes(self, final):
        original = self.chain.call
        reads = []
        def call(method, params):
            if method == 'eth_blockNumber':
                reads.append(method)
                return '0x6' if len(reads) == 1 else final
            return original(method, params)
        return call, reads

    def test_retained_tip_without_required_descendants_cannot_advance_cursor(self):
        self.chain.transfer(5, fixtures.B)
        before = self.f.database_snapshot(self.index)
        call, reads = self.head_changes('0x5')
        with patch.object(self.chain, 'call', side_effect=call):
            with self.assertRaises(IndexerSafetyError) as caught:
                self.index.step()
        self.assertEqual(caught.exception.code, 'confirmation_depth')
        self.assertEqual(len(reads), 2)
        self.assertEqual(before, self.f.database_snapshot(self.index))
        self.assertEqual(self.index.next_block, 1)

    def test_malformed_final_head_cannot_commit_prepared_logs(self):
        self.chain.transfer(2, fixtures.B)
        before = self.f.database_snapshot(self.index)
        call, _ = self.head_changes('0x05')
        with patch.object(self.chain, 'call', side_effect=call):
            with self.assertRaises(IndexerSafetyError) as caught:
                self.index.step()
        self.assertEqual(caught.exception.code, 'invalid_header')
        self.assertEqual(before, self.f.database_snapshot(self.index))

    def test_lower_final_head_still_accepts_a_sufficiently_deep_small_chunk(self):
        self.index.chunk = 2
        self.chain.transfer(2, fixtures.B)
        call, _ = self.head_changes('0x4')
        with patch.object(self.chain, 'call', side_effect=call):
            self.assertEqual(self.index.step(), 2)
        self.assertEqual(self.index.next_block, 3)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.B})

    def test_growing_final_head_preserves_original_chunk_and_excludes_pending_logs(self):
        self.chain.transfer(5, fixtures.B)
        self.chain.transfer(6, fixtures.C)
        call, _ = self.head_changes('0x8')
        with patch.object(self.chain, 'call', side_effect=call):
            self.assertEqual(self.index.step(), 5)
        self.assertEqual(self.index.next_block, 6)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.B})

    def test_same_cursor_after_other_writer_reorg_cannot_attach_to_old_parent(self):
        self.chain.transfer(2, fixtures.B)
        self.assertEqual(self.index.step(), 5)
        other_chain = fixtures.Chain()
        other_chain.transfer(2, fixtures.B)
        other_chain.fork(5)
        other = Indexer(self.f.config, other_chain)
        self.addCleanup(other.close)
        self.chain.head = 8
        original = self.chain.call
        end_reads = 0
        committed = []
        def call(method, params):
            nonlocal end_reads
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == '0x7':
                end_reads += 1
                if end_reads == 2:
                    # A second legitimate indexer reorgs/reingests block 5.
                    # Its cursor returns to 6, so a cursor-only CAS misses it.
                    self.assertEqual(other.step(), 1)
                    self.assertEqual(other.next_block, 6)
                    committed.append(self.f.database_snapshot(other))
            return result
        with patch.object(self.chain, 'call', side_effect=call):
            with self.assertRaises(IndexerSafetyError) as caught:
                self.index.step()
        self.assertEqual(caught.exception.code, 'database_changed')
        self.assertEqual(len(committed), 1)
        self.assertEqual(self.f.database_snapshot(self.index), committed[0])
        self.assertEqual(self.index.next_block, 6)
        self.assertEqual(self.index.db.execute('SELECT hash FROM blocks WHERE number=5').fetchone()[0],
                         other_chain.blocks[5]['hash'])

    def test_unchanged_predecessor_accepts_normal_resume(self):
        self.chain.transfer(2, fixtures.B)
        self.assertEqual(self.index.step(), 5)
        self.chain.head = 8
        self.chain.transfer(7, fixtures.C)
        self.assertEqual(self.index.step(), 2)
        self.assertEqual(self.index.next_block, 8)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.C})
        rows = self.index.db.execute('SELECT number,hash,parent FROM blocks ORDER BY number').fetchall()
        for parent, child in zip(rows, rows[1:]):
            self.assertEqual(child[2], parent[1])

    def test_regressing_timestamp_inside_chunk_preserves_all_history(self):
        self.chain.transfer(2, fixtures.B)
        self.chain.blocks[3]['timestamp'] = hex(1001)
        before = self.f.database_snapshot(self.index)
        with self.assertRaises(IndexerSafetyError) as caught:
            self.index.step()
        self.assertEqual(caught.exception.code, 'invalid_timestamp')
        self.assertEqual(self.f.database_snapshot(self.index), before)
        self.assertEqual(self.index.next_block, 1)

    def test_new_chunk_timestamp_cannot_regress_below_retained_predecessor(self):
        self.chain.transfer(2, fixtures.B)
        self.assertEqual(self.index.step(), 5)
        self.chain.head = 8
        self.chain.blocks[6]['timestamp'] = hex(1004)
        before = self.f.database_snapshot(self.index)
        with self.assertRaises(IndexerSafetyError) as caught:
            self.index.step()
        self.assertEqual(caught.exception.code, 'invalid_timestamp')
        self.assertEqual(self.f.database_snapshot(self.index), before)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.B})
        self.assertEqual(self.index.next_block, 6)

    def test_equal_timestamps_within_chunk_and_at_retained_boundary_are_valid(self):
        self.chain.blocks[3]['timestamp'] = self.chain.blocks[2]['timestamp']
        self.chain.transfer(2, fixtures.B)
        self.assertEqual(self.index.step(), 5)
        self.chain.head = 8
        for number in (6, 7):
            self.chain.blocks[number]['timestamp'] = self.chain.blocks[5]['timestamp']
        self.chain.transfer(7, fixtures.C)
        self.assertEqual(self.index.step(), 2)
        self.assertEqual(self.index.next_block, 8)
        self.assertEqual(self.index.nft_owners(fixtures.A), {'7': fixtures.C})

    def test_unindexed_parent_time_is_not_invented_or_fetched(self):
        self.chain.blocks[1]['timestamp'] = '0x0'
        original = self.chain.call
        def call(method, params):
            if method == 'eth_getBlockByNumber' and params[0] == '0x0':
                self.fail('Unindexed parent timestamp must not require another RPC anchor')
            return original(method, params)
        with patch.object(self.chain, 'call', side_effect=call):
            self.assertEqual(self.index.step(), 5)
        self.assertEqual(self.index.db.execute('SELECT timestamp FROM blocks WHERE number=1').fetchone(), (0,))


if __name__ == '__main__':
    unittest.main()
