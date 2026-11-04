"""Indexer anchor and streaming regressions using disposable SQLite only."""
import json
from pathlib import Path
import tempfile
import unittest

from indexer.monitor import Indexer, IndexerSafetyError
from tests_python.test_indexer import A, B, C, Chain, h
from zzz_ops.errors import RpcError


class IndexerAnchorIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.chain = Chain()
        self.config = dict(chain_id=1, start_block=1, start_parent_hash=h(0),
                           confirmations=2, block_chunk=10, max_reorg_depth=5,
                           contracts=[A], database=str(Path(self.directory.name)/'history.sqlite'))

    def open(self):
        index = Indexer(self.config, self.chain)
        self.addCleanup(index.close)
        return index

    @staticmethod
    def snapshot(index):
        return '\n'.join(index.db.iterdump())

    def test_mutating_callers_anchor_cannot_authorize_full_history_deletion(self):
        index = self.open()
        self.chain.transfer(2, B)
        index.step()
        before = self.snapshot(index)
        self.chain.fork(1)
        self.chain.blocks[1]['parentHash'] = h(999)
        self.config['start_parent_hash'] = h(999)
        with self.assertRaisesRegex(IndexerSafetyError, 'No reviewed common ancestor'):
            index.reconcile()
        self.assertEqual(before, self.snapshot(index))
        self.assertEqual({'7': B}, index.nft_owners(A))

    def test_mutating_callers_anchor_cannot_bypass_first_ingestion_boundary(self):
        index = self.open()
        self.chain.blocks[1]['parentHash'] = h(999)
        self.config['start_parent_hash'] = h(999)
        before = self.snapshot(index)
        with self.assertRaisesRegex(RpcError, 'Non-contiguous block ancestry'):
            index.step()
        self.assertEqual(before, self.snapshot(index))

    def test_unanchored_history_cannot_gain_an_anchor_from_a_later_config_edit(self):
        self.config['start_parent_hash'] = None
        index = self.open()
        index.step()
        before = self.snapshot(index)
        self.chain.fork(1)
        self.config['start_parent_hash'] = h(0)
        with self.assertRaisesRegex(IndexerSafetyError, 'No reviewed common ancestor'):
            index.reconcile()
        self.assertEqual(before, self.snapshot(index))

    def test_malformed_start_anchor_is_rejected_before_creating_a_database(self):
        for invalid in (True, 1, [], {}, '0x1', 'not-a-hash'):
            with self.subTest(anchor=invalid):
                self.config['database'] = str(Path(self.directory.name)/f'invalid-{type(invalid).__name__}.sqlite')
                self.config['start_parent_hash'] = invalid
                with self.assertRaises(ValueError):
                    self.open()
                self.assertFalse(Path(self.config['database']).exists())

    def test_snapshot_preserves_the_existing_database_identity_and_original_anchor(self):
        index = self.open()
        self.config['start_parent_hash'] = h(999)
        self.chain.transfer(2, B)
        self.assertEqual(5, index.step())
        stored = json.loads(index.db.execute('SELECT config FROM cursors').fetchone()[0])
        self.assertEqual(h(0), stored['parent_hash'])
        self.assertEqual({'7': B}, index.nft_owners(A))

    def test_ownership_replay_streams_history_and_preserves_latest_transfer_and_burn(self):
        index = self.open()
        # Real cursor execution, but forbid whole-result materialization. The
        # assertion concerns the resource boundary, not a source-text pattern.
        rows = [(self.chain.head, i, json.dumps(dict(tokenId=str(i % 3), to=B if i < 1998 else C)))
                for i in range(2000)]
        rows.append((self.chain.head, 2000, json.dumps(dict(tokenId='1', to='0x'+'00'*20))))
        index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)', (1, self.chain.head, h(6), h(5), 6))
        index.db.executemany('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
            [(1, block, h(6), h(10000+ordinal), ordinal, A, 'Transfer', decoded, '{}')
             for block, ordinal, decoded in rows])
        class Cursor:
            def __init__(self, inner): self.inner = inner
            def __iter__(self): return iter(self.inner)
            def close(self): self.inner.close()
            def fetchall(self):
                self.close()
                raise AssertionError('Ownership replay materialized the entire transfer history')
        class StreamingDB:
            def execute(self, *args): return Cursor(real.execute(*args))
        real = index.db
        index.db = StreamingDB()
        try:
            self.assertEqual({'0': C, '2': B}, index.nft_owners(A))
            self.assertEqual({}, index.nft_owners(C))
        finally:
            index.db = real
