"""Real SQLite startup failures must not adopt identities or leak connections.

Disposable files and an authorizer exercise real DDL/transaction boundaries.
No RPC, operating database, key or service is used.
"""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from indexer.monitor import Indexer
from tests_python.test_indexer import A, B, C, Chain, h


CONNECT = sqlite3.connect
SQLITE_MAX = (1 << 63) - 1


class TrackedConnection(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.was_closed = False
        self.refuse_wal = False

    def execute(self, sql, *args, **kwargs):
        if self.refuse_wal and sql == 'PRAGMA journal_mode=WAL':
            return super().execute('PRAGMA journal_mode')
        return super().execute(sql, *args, **kwargs)

    def close(self):
        self.was_closed = True
        super().close()


class IndexerStartupAtomicityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'history.sqlite'
        self.chain = Chain()
        self.config = dict(chain_id=1, start_block=1, start_parent_hash=h(0),
                           confirmations=2, block_chunk=10, max_reorg_depth=5,
                           contracts=[A], database=str(self.path))
        self.connections = []

    def connection(self, *args, deny=None, initial_mode=None, refuse_wal=False, **kwargs):
        db = CONNECT(*args, factory=TrackedConnection, **kwargs)
        self.connections.append(db)
        self.addCleanup(db.close)
        if initial_mode is not None:
            assert initial_mode in ('off', 'memory')
            self.assertEqual(initial_mode, db.execute('PRAGMA journal_mode='+initial_mode).fetchone()[0])
        db.refuse_wal = refuse_wal
        if deny is not None:
            db.set_authorizer(lambda action, first, second, _database, _source:
                sqlite3.SQLITE_DENY if deny(action, first, second) else sqlite3.SQLITE_OK)
        return db

    def open(self, config=None, deny=None, initial_mode=None, refuse_wal=False):
        with patch('indexer.monitor.sqlite3.connect',
                   side_effect=lambda *a, **kw: self.connection(*a, deny=deny,
                       initial_mode=initial_mode, refuse_wal=refuse_wal, **kw)):
            return Indexer(self.config if config is None else config, self.chain)

    def seed(self):
        self.chain.transfer(2, B)
        index = self.open()
        try:
            index.step()
        finally:
            index.close()

    def snapshot(self):
        db = CONNECT(self.path)
        try:
            return (db.execute('PRAGMA journal_mode').fetchone()[0],
                    list(db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name')),
                    '\n'.join(db.iterdump()))
        finally:
            db.close()

    def assert_failed_connection_closed(self):
        self.assertTrue(self.connections[-1].was_closed,
                        'A rejected startup retained its SQLite connection')
        with self.assertRaises(sqlite3.ProgrammingError):
            self.connections[-1].execute('SELECT 1')

    def test_wrong_identity_preserves_schema_journal_cursor_and_history(self):
        self.seed()
        db = CONNECT(self.path)
        try:
            db.execute('DROP INDEX event_lookup')
            db.commit()
            self.assertEqual('delete', db.execute('PRAGMA journal_mode=DELETE').fetchone()[0])
        finally:
            db.close()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Indexer identity changed'):
            self.open(dict(self.config, contracts=[C]))
        self.assertEqual(before, self.snapshot(),
                         'Rejected identity changed journal mode or repaired schema')
        self.assert_failed_connection_closed()

    def test_failed_schema_creation_rolls_back_the_entire_initialization(self):
        deny = lambda action, first, _second: action == sqlite3.SQLITE_CREATE_INDEX and first == 'event_lookup'
        with self.assertRaises(sqlite3.DatabaseError):
            self.open(deny=deny)
        self.assertEqual([], self.snapshot()[1], 'Failed DDL left a partial indexer schema')
        self.assert_failed_connection_closed()
        recovered = self.open()
        try:
            self.assertEqual(1, recovered.next_block)
            self.assertEqual(5, recovered.step())
        finally:
            recovered.close()

    def test_failed_identity_insert_leaves_no_partial_schema_and_can_retry(self):
        deny = lambda action, first, _second: action == sqlite3.SQLITE_INSERT and first == 'cursors'
        with self.assertRaises(sqlite3.DatabaseError):
            self.open(deny=deny)
        self.assertEqual([], self.snapshot()[1])
        self.assert_failed_connection_closed()
        recovered = self.open()
        try:
            self.assertEqual(1, recovered.next_block)
        finally:
            recovered.close()

    def test_failed_wal_setup_closes_connection_and_preserves_existing_history(self):
        self.seed()
        before = self.snapshot()
        deny = lambda action, first, second: (
            action == sqlite3.SQLITE_PRAGMA and first == 'journal_mode' and str(second).lower() == 'wal')
        with self.assertRaises(sqlite3.DatabaseError):
            self.open(deny=deny)
        self.assert_failed_connection_closed()
        self.assertEqual(before, self.snapshot())
        recovered = self.open()
        try:
            self.assertEqual(6, recovered.next_block)
            self.assertEqual({'7': B}, recovered.nft_owners(A))
        finally:
            recovered.close()

    def test_database_integer_overflow_is_rejected_before_files_or_connection(self):
        for field, number in (('chain_id', SQLITE_MAX + 1),
                              ('start_block', SQLITE_MAX),
                              ('max_reorg_depth', SQLITE_MAX)):
            with self.subTest(field=field):
                directory = self.path.parent / field
                config = dict(self.config, database=str(directory / 'invalid.sqlite'))
                config[field] = str(number)
                before = len(self.connections)
                with self.assertRaises(ValueError):
                    self.open(config)
                self.assertEqual(before, len(self.connections))
                self.assertFalse(directory.exists())

    def test_supported_sqlite_boundaries_remain_accepted_without_rpc(self):
        index = self.open(dict(self.config, chain_id=SQLITE_MAX,
                               start_block=SQLITE_MAX - 1, max_reorg_depth=SQLITE_MAX - 1))
        try:
            self.assertEqual(SQLITE_MAX - 1, index.next_block)
        finally:
            index.close()

    def test_unsafe_journal_modes_reject_before_schema_creation(self):
        for mode in ('off', 'memory'):
            with self.subTest(mode=mode):
                config = dict(self.config, database=str(self.path.with_name(mode+'.sqlite')))
                with self.assertRaisesRegex(ValueError, 'durable rollback-capable'):
                    self.open(config, initial_mode=mode)
                self.assert_failed_connection_closed()
                db = CONNECT(config['database'])
                try:
                    self.assertEqual([], list(db.execute('SELECT name FROM sqlite_master')))
                finally:
                    db.close()

    def test_silent_wal_refusal_cannot_report_success_and_valid_retry_recovers(self):
        with self.assertRaisesRegex(ValueError, 'required WAL journal mode'):
            self.open(refuse_wal=True)
        self.assert_failed_connection_closed()
        # Identity/schema already committed coherently before WAL negotiation;
        # no history was processed. A normal retry adopts that SAME identity.
        recovered = self.open()
        try:
            self.assertEqual(1, recovered.next_block)
            self.assertEqual(('wal',), recovered.db.execute('PRAGMA journal_mode').fetchone())
        finally:
            recovered.close()

    def test_valid_restart_retains_identity_cursor_and_owner_and_continues_ingestion(self):
        self.seed()
        before = self.snapshot()
        index = self.open()
        try:
            self.assertEqual(before, self.snapshot())
            self.assertEqual(6, index.next_block)
            self.assertEqual({'7': B}, index.nft_owners(A))
            self.chain.head = 7
            self.chain.transfer(6, C)
            self.assertEqual(1, index.step())
            self.assertEqual(7, index.next_block)
            self.assertEqual({'7': C}, index.nft_owners(A))
        finally:
            index.close()


if __name__ == '__main__':
    unittest.main()
