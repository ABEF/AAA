"""Corrupt stored evidence must fail as unavailable, never become clean income.

Real SQLite/writer/reader; deterministic RPC values, no network or signer.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from frontend_api.history import History, HistoryError, TRANSFER, CLAIMED, ZERO
from indexer.monitor import Indexer


def hash_(number):
    return '0x' + f'{number:064x}'


def address_(number):
    return '0x' + f'{number:040x}'


class StoredHistoryIntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'history.sqlite'
        self.contracts = [address_(i) for i in (1, 2, 3)]
        self.logs = []
        for number, emitter, topics, data in (
            (11, self.contracts[0], [TRANSFER, hash_(0), hash_(4), hash_(7)], '0x'),
            (12, self.contracts[2], [CLAIMED, hash_(7), hash_(0), hash_(4)], hash_(20)),
        ):
            self.logs.append(dict(address=emitter, blockNumber=hex(number),
                blockHash=hash_(number), transactionHash=hash_(number + 100),
                logIndex='0x0', removed=False, topics=topics, data=data))
        config = dict(chain_id=1, start_block=10, start_parent_hash=hash_(9),
            confirmations=1, block_chunk=4, contracts=self.contracts, database=str(self.path))
        self.index = Indexer(config, self)
        self.addCleanup(self.index.close)
        self.assertEqual(self.index.step(), 4)
        self.history = History(dict(database=str(self.path), start_block=10,
            start_parent_hash=hash_(9), contracts=self.contracts, max_events=100),
            chain_id=1, nft=self.contracts[0], rewards=self.contracts[1], royalties=self.contracts[2])

    def call(self, method, params):
        if method == 'eth_blockNumber':
            return hex(13)
        if method == 'eth_getLogs':
            return copy.deepcopy(self.logs)
        if method == 'eth_getBlockByNumber':
            number = int(params[0], 16)
            return dict(number=hex(number), hash=hash_(number), parentHash=hash_(number - 1),
                timestamp=hex(100 + number))
        raise AssertionError(method)

    def read(self):
        return self.history.read(block_number=13, block_hash=hash_(13),
            block_timestamp=113, minted_count=1, lp_assets={ZERO}, royalty_assets={ZERO})

    def mutate_raw(self, transform):
        raw = self.index.db.execute('SELECT raw FROM logs WHERE block_number=12').fetchone()[0]
        with self.index.db:
            self.index.db.execute('UPDATE logs SET raw=? WHERE block_number=12', (transform(raw),))

    def test_healthy_claims_and_owner_use_actual_raw_rows(self):
        result = self.read()
        self.assertEqual(result.owners, {7: address_(4)})
        self.assertEqual(result.claims[7, ZERO], (0, 20))

    def test_duplicate_raw_fields_fail_even_when_values_agree(self):
        self.mutate_raw(lambda raw: raw[:-1] + ', "data": ' + json.dumps(hash_(20)) + '}')
        with self.assertRaises(HistoryError):
            self.read()

    def test_duplicate_cursor_identity_is_not_silently_accepted(self):
        identity = self.index.db.execute('SELECT config FROM cursors').fetchone()[0]
        with self.index.db:
            self.index.db.execute('UPDATE cursors SET config=?', (identity[:-1] + ', "start": 10}',))
        with self.assertRaises(HistoryError):
            self.read()

    def test_nonfinite_extra_metadata_is_malformed(self):
        for number in ('NaN', 'Infinity', '-Infinity', '1e999'):
            with self.subTest(number=number):
                self.mutate_raw(lambda raw: json.dumps(self.logs[1])[:-1] + ', "extra": ' + number + '}')
                with self.assertRaises(HistoryError):
                    self.read()

    def test_parser_recursion_becomes_unavailable_and_connection_is_reusable(self):
        # Inject the parser's failure rather than assume a runtime-specific
        # nesting depth always exceeds its native JSON implementation's limit.
        with patch('frontend_api.history.json.loads', side_effect=RecursionError):
            with self.assertRaises(HistoryError):
                self.read()
        self.assertEqual(self.read().claims[7, ZERO], (0, 20))

    def test_missing_explicit_not_removed_marker_is_unavailable(self):
        def remove(raw):
            item = json.loads(raw)
            del item['removed']
            return json.dumps(item)
        self.mutate_raw(remove)
        with self.assertRaises(HistoryError):
            self.read()

    def test_unknown_log_still_requires_well_formed_data(self):
        def corrupt(raw):
            item = json.loads(raw)
            item.update(topics=[hash_(999)], data='0xz')
            return json.dumps(item)
        self.mutate_raw(corrupt)
        with self.assertRaises(HistoryError):
            self.read()
