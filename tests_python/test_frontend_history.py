import copy
import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from frontend_api.history import CLAIMED, TRANSFER, History, HistoryError, ZERO
from frontend_api.service import Projection
from frontend_api.server import ReadServer, handler
from indexer.monitor import Indexer
from tests_python.test_frontend_api import MockRPC, addr, configuration, words
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


def h(number):
    return '0x' + f'{100000 + number:064x}'


def topic(number):
    return words(number)


class HistoryRPC(MockRPC):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.other = int.from_bytes(keccak256(b'second canonical NFT'), 'big')
        self.put(addr(2), 'mintedCount()', values=(2,))
        self.put(addr(2), 'mintOrdinalOf(uint256)', (self.nft_id,), (1,))
        self.put(addr(2), 'tokenAtOrdinal(uint256)', (1,), (self.nft_id,))
        self.put(addr(2), 'ownerOf(uint256)', (self.other,), (addr(31),))
        for wallet, count in ((30, 1), (31, 1), (32, 0)):
            self.put(addr(2), 'balanceOf(address)', (addr(wallet),), (count,))
        self.transfer(11, 0, ZERO, addr(30), self.nft_id)
        self.transfer(12, 0, ZERO, addr(31), self.other)
        self.claim(13, 0, addr(4), self.nft_id, addr(20), addr(30), 10)
        self.claim(14, 0, addr(5), self.nft_id, addr(21), addr(30), 30)
        self.transfer(20, 0, addr(30), addr(31), self.nft_id)
        self.claim(20, 1, addr(4), self.nft_id, addr(20), addr(31), 20)
        self.transfer(21, 0, addr(31), addr(30), self.nft_id)
        # A payout callback transfers before the ledger emits its original
        # recipient. History must not discard this legitimate royalty claim.
        self.transfer(23, 0, addr(30), addr(31), self.nft_id)
        self.claim(23, 1, addr(5), self.nft_id, ZERO, addr(30), 7)
        self.transfer(24, 0, addr(31), addr(30), self.nft_id)
        self.claim(24, 1, addr(5), self.nft_id, addr(21), addr(30), 40)
        self.claim(25, 0, addr(4), self.nft_id, addr(20), addr(30), 0)
        self.claim(26, 0, addr(4), self.other, addr(21), addr(31), 999)
        self.claim(100, 0, addr(4), self.nft_id, addr(20), addr(30), 777)

    def header(self, n):
        return {'number': hex(n), 'hash': self.anchor if n == 10 else self.hash if n == 99 else h(n),
                'parentHash': self.anchor if n == 11 else self.hash if n == 100 else h(n - 1),
                'timestamp': hex(891 + n)}

    def raw(self, block, index, emitter, topics, data):
        return {'address': emitter, 'blockNumber': hex(block), 'blockHash': self.header(block)['hash'],
                'transactionHash': h(1000 + block), 'logIndex': hex(index), 'topics': topics,
                'data': data, 'removed': False}

    def transfer(self, block, index, sender, recipient, nft_id):
        self.logs.append(self.raw(block, index, addr(2), [TRANSFER, topic(sender), topic(recipient), topic(nft_id)], '0x'))

    def claim(self, block, index, emitter, nft_id, asset, owner, amount):
        self.logs.append(self.raw(block, index, emitter, [CLAIMED, topic(nft_id), topic(asset), topic(owner)], words(amount)))

    def call(self, method, params):
        if method == 'eth_getLogs':
            low, high = int(params[0]['fromBlock'], 16), int(params[0]['toBlock'], 16)
            return copy.deepcopy([log for log in self.logs if low <= int(log['blockNumber'], 16) <= high])
        if method == 'eth_getBlockByNumber':
            self.calls.append((method, copy.deepcopy(params)))
            return self.header(int(params[0], 16))
        if method == 'eth_getCode' and params[0] == addr(2) and params[1]['blockHash'] == h(9):
            self.calls.append((method, copy.deepcopy(params)))
            return '0x'
        if method == 'eth_getCode' and params[0] == addr(2) and params[1]['blockHash'] == self.anchor:
            self.calls.append((method, copy.deepcopy(params)))
            return self.codes[addr(2)]
        return super().call(method, params)


class ConfirmedHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'index.sqlite'
        self.rpc = HistoryRPC()
        self.config = {'database': str(self.path), 'start_block': 10, 'start_parent_hash': h(9),
                       'contracts': [addr(2), addr(4), addr(5)], 'max_events': 1000}
        index_config = dict(self.config, chain_id=31337, rpc_urls=['http://127.0.0.1:8545'],
                            confirmations=12, block_chunk=200, max_reorg_depth=100, poll_seconds=1)
        index_config.pop('max_events')
        self.index = Indexer(index_config, self.rpc)
        # Build with the actual indexer. Its DB can run ahead of the API's block;
        # the block100 claim must not leak into block99's lifetime total.
        self.rpc.head = 111
        self.assertEqual(self.index.step(), 91)
        self.rpc.head = 110
        self.history = History(self.config, chain_id=31337, nft=addr(2), rewards=addr(4), royalties=addr(5))

    def tearDown(self):
        self.index.close()
        self.temp.cleanup()

    def read(self):
        return self.history.read(block_number=99, block_hash=self.rpc.hash, block_timestamp=990,
                                 minted_count=2, lp_assets={addr(20), addr(21)}, royalty_assets={ZERO, addr(21)})

    def insert(self, log):
        with self.index.db:
            self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337, int(log['blockNumber'], 16), log['blockHash'], log['transactionHash'],
                 int(log['logIndex'], 16), log['address'], 'UNTRUSTED_LABEL', '{"amount":"FAKE"}', json.dumps(log)))

    def projection(self):
        config = configuration(); config['history'] = self.config
        return Projection(config, self.rpc, clock=lambda: 1000)

    def test_transfer_replay_and_lifetime_claims_across_past_owners(self):
        result = self.read()
        self.assertEqual(dict(result.owners), {self.rpc.nft_id: addr(30), self.rpc.other: addr(31)})
        balances = {x['asset']: x for x in result.claimed(self.rpc.nft_id, {ZERO, addr(20), addr(21)})}
        self.assertEqual(balances[addr(20)]['lp_raw'], '30')
        self.assertEqual(balances[addr(21)]['royalties_raw'], '70')
        self.assertEqual(balances[ZERO]['total_raw'], '7')
        self.assertEqual(result.provenance['through_block'], 99)
        self.assertEqual(result.provenance['indexer_next_block'], 101)
        self.assertEqual(result.provenance['claim_events'], 7)
        self.assertIn('not a cryptographic', result.provenance['completeness'])

    def test_decoded_labels_and_json_caches_are_never_trusted(self):
        with self.index.db:
            self.index.db.execute('UPDATE logs SET event=NULL,decoded=?', ('{"amount":"999999999"}',))
        self.assertEqual(self.read().claims[self.rpc.nft_id, addr(20)], (30, 0))

    def test_lp_and_royalties_same_asset_are_summed_without_cross_currency_sum(self):
        log = self.rpc.raw(50, 0, addr(5), [CLAIMED, topic(self.rpc.nft_id), topic(addr(21)), topic(addr(30))], words(5))
        self.insert(log)
        log2 = self.rpc.raw(51, 0, addr(4), [CLAIMED, topic(self.rpc.nft_id), topic(addr(21)), topic(addr(30))], words(6))
        self.insert(log2)
        item = next(x for x in self.read().claimed(self.rpc.nft_id, {addr(21)}) if x['asset'] == addr(21))
        self.assertEqual(item, {'asset': addr(21), 'lp_raw': '6', 'royalties_raw': '75', 'total_raw': '81'})

    def test_missing_cursor_or_incomplete_target_is_not_zero_history(self):
        with self.index.db:
            self.index.db.execute('UPDATE cursors SET next_block=99')
        with self.assertRaisesRegex(HistoryError, 'processed'):
            self.read()
        with self.index.db:
            self.index.db.execute('DELETE FROM cursors')
        with self.assertRaises(HistoryError):
            self.read()

    def test_wrong_cursor_address_start_or_anchor_identity_rejected(self):
        original = self.index.db.execute('SELECT config FROM cursors').fetchone()[0]
        for fields in ({'start': 11}, {'parent_hash': h(8)}, {'contracts': [addr(2), addr(4), addr(6)]}):
            value = json.loads(original); value.update(fields)
            with self.index.db:
                self.index.db.execute('UPDATE cursors SET config=?', (json.dumps(value),))
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(HistoryError, 'identity'):
                    self.read()
        with self.index.db:
            self.index.db.execute('UPDATE cursors SET config=?', (original,))

    def test_missing_block_wrong_tip_timestamp_and_broken_ancestry_rejected(self):
        for field, value in (('hash', h(999)), ('timestamp', 991)):
            with self.index.db:
                self.index.db.execute(f'UPDATE blocks SET {field}=? WHERE number=99', (value,))
            with self.assertRaisesRegex(HistoryError, 'tip'):
                self.read()
            with self.index.db:
                self.index.db.execute('UPDATE blocks SET hash=?,timestamp=990 WHERE number=99', (self.rpc.hash,))
        with self.index.db:
            self.index.db.execute('UPDATE blocks SET parent=? WHERE number=50', (h(999),))
        with self.assertRaisesRegex(HistoryError, 'ancestry'):
            self.read()
        with self.index.db:
            self.index.db.execute('DELETE FROM blocks WHERE number=50')
        with self.assertRaisesRegex(HistoryError, 'gaps'):
            self.read()

    def test_missing_mint_or_transfer_owner_is_not_accepted(self):
        with self.index.db:
            self.index.db.execute('DELETE FROM logs WHERE block_number=11')
        with self.assertRaisesRegex(HistoryError, 'minted|mint|predecessor'):
            self.read()

    def test_no_hidden_burn_or_duplicate_mint(self):
        for sender, recipient in ((addr(30), ZERO), (ZERO, addr(30))):
            log = self.rpc.raw(50, 0, addr(2), [TRANSFER, topic(sender), topic(recipient), topic(self.rpc.nft_id)], '0x')
            self.insert(log)
            with self.assertRaises(HistoryError):
                self.read()
            with self.index.db:
                self.index.db.execute('DELETE FROM logs WHERE block_number=50')

    def test_fixed_topic_data_layout_asset_and_raw_provenance_checked(self):
        good = self.rpc.raw(50, 0, addr(5), [CLAIMED, topic(self.rpc.nft_id), topic(addr(21)), topic(addr(30))], words(1))
        changes = [dict(data=words(1, 2)), dict(data='0x'), dict(removed=True), dict(blockHash=h(999)),
                   dict(topics=good['topics'][:3]), dict(topics=[CLAIMED, topic(self.rpc.nft_id), topic(addr(44)), topic(addr(30))]),
                   dict(topics=[CLAIMED, topic(123), topic(addr(21)), topic(addr(30))]),
                   dict(topics=[CLAIMED, topic(self.rpc.nft_id), topic(1 << 160), topic(addr(30))])]
        for fields in changes:
            log = dict(good, **fields)
            # Keep SQL provenance canonical so malformed raw provenance cannot
            # be disguised by changing the row to agree with an orphan branch.
            with self.index.db:
                self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                    (31337, 50, self.rpc.header(50)['hash'], good['transactionHash'], 0, addr(5), None, None, json.dumps(log)))
            with self.subTest(fields=fields):
                with self.assertRaises(HistoryError):
                    self.read()
            with self.index.db:
                self.index.db.execute('DELETE FROM logs WHERE block_number=50')

    def test_duplicate_block_log_index_and_event_bound_fail_closed(self):
        log = self.rpc.raw(50, 0, addr(5), [CLAIMED, topic(self.rpc.nft_id), topic(ZERO), topic(addr(30))], words(1))
        self.insert(log)
        log['transactionHash'] = h(8888)
        self.insert(log)
        with self.assertRaisesRegex(HistoryError, 'duplicate'):
            self.read()
        bounded = History(dict(self.config, max_events=1), chain_id=31337, nft=addr(2), rewards=addr(4), royalties=addr(5))
        with self.assertRaisesRegex(HistoryError, 'bound'):
            bounded.read(block_number=99, block_hash=self.rpc.hash, block_timestamp=990, minted_count=2,
                         lp_assets={addr(20), addr(21)}, royalty_assets={ZERO, addr(21)})

    def test_readonly_missing_database_never_creates_one(self):
        missing = Path(self.temp.name) / 'missing.sqlite'
        history = History(dict(self.config, database=str(missing)), chain_id=31337, nft=addr(2), rewards=addr(4), royalties=addr(5))
        with self.assertRaises(HistoryError):
            history.read(block_number=99, block_hash=self.rpc.hash, block_timestamp=990, minted_count=2,
                         lp_assets={addr(20), addr(21)}, royalty_assets={ZERO, addr(21)})
        self.assertFalse(missing.exists())

    def test_consistent_sqlite_transaction_ignores_concurrent_later_commit(self):
        connect = sqlite3.connect
        writer = self.index.db
        good = self.rpc.raw(80, 0, addr(4), [CLAIMED, topic(self.rpc.nft_id), topic(addr(20)), topic(addr(30))], words(100))
        class SnapshotConnection:
            def __init__(self, db): self.db = db; self.changed = False
            def execute(inner, sql, args=()):
                cursor = inner.db.execute(sql, args)
                if sql.startswith('SELECT next_block') and not inner.changed:
                    inner.changed = True
                    with writer:
                        writer.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                            (31337, 80, good['blockHash'], good['transactionHash'], 0, addr(4), None, None, json.dumps(good)))
                return cursor
            def set_progress_handler(inner, callback, count): inner.db.set_progress_handler(callback, count)
            def rollback(inner): inner.db.rollback()
            def close(inner): inner.db.close()
        with patch('frontend_api.history.sqlite3.connect', side_effect=lambda *a, **k: SnapshotConnection(connect(*a, **k))):
            self.assertEqual(self.read().claims[self.rpc.nft_id, addr(20)], (30, 0))
        self.assertEqual(self.read().claims[self.rpc.nft_id, addr(20)], (130, 0))

    def test_nft_api_exposes_all_time_ledger_totals_with_exact_decimals(self):
        result = self.projection().nft(self.rpc.nft_id)
        self.assertTrue(result['previously_claimed']['available'])
        entries = {x['asset']: x for x in result['previously_claimed']['assets']}
        self.assertEqual(entries[addr(21)]['total_raw'], '70')
        self.assertEqual(entries[addr(21)]['decimals'], 6)
        self.assertEqual(entries[ZERO]['total_raw'], '7')
        self.assertNotIn('previously_claimed', result['unavailable_metrics'])
        self.assertIn('fees_last_24h', result['unavailable_metrics'])
        self.assertEqual(result['owner'], addr(30))

    def test_wallet_complete_inventory_rechecked_against_balance_and_owner(self):
        projection = self.projection()
        wallet = projection.wallet(addr(30))
        self.assertEqual(wallet['token_ids'], [str(self.rpc.nft_id)])
        self.assertEqual(wallet['count'], 1)
        self.assertTrue(wallet['available'])
        self.assertEqual(projection.wallet(addr(32))['token_ids'], [])
        self.rpc.put(addr(2), 'balanceOf(address)', (addr(30),), (2,))
        with self.assertRaisesRegex(HistoryError, 'balance'):
            projection.wallet(addr(30))
        self.rpc.put(addr(2), 'balanceOf(address)', (addr(30),), (1,))
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(31),))
        with self.assertRaisesRegex(HistoryError, 'owned'):
            projection.wallet(addr(30))
        with self.assertRaisesRegex(HistoryError, 'owner'):
            projection.nft(self.rpc.nft_id)

    def test_creation_coverage_anchor_and_code_before_creation_are_checked(self):
        projection = self.projection()
        original = self.rpc.call
        def preexisting(method, params):
            if method == 'eth_getCode' and params[0] == addr(2) and params[1]['blockHash'] == h(9):
                return self.rpc.codes[addr(2)]
            return original(method, params)
        with patch.object(self.rpc, 'call', side_effect=preexisting):
            with self.assertRaisesRegex(HistoryError, 'already existed'):
                projection.wallet(addr(30))

    def test_optional_history_never_implies_zero_and_invalid_config_is_rejected(self):
        plain = Projection(configuration(), self.rpc, clock=lambda: 1000)
        item = plain.nft(self.rpc.nft_id)
        self.assertFalse(item['previously_claimed']['available'])
        self.assertIsNone(item['previously_claimed']['assets'])
        with self.assertRaises(HistoryError):
            plain.wallet(addr(30))
        for fields in ({'contracts': [addr(2), addr(4), addr(4)]}, {'max_events': 1000001}, {'start_block': 0}):
            with self.assertRaises(ValueError):
                History(dict(self.config, **fields), chain_id=31337, nft=addr(2), rewards=addr(4), royalties=addr(5))

    def test_reorg_after_history_read_cannot_release_a_successful_nft_snapshot(self):
        projection = self.projection()
        original = projection.history.read
        def reorganize(**kwargs):
            result = original(**kwargs)
            self.rpc.hash = h(999)
            return result
        with patch.object(projection.history, 'read', side_effect=reorganize):
            with self.assertRaisesRegex(RpcError, 'changed'):
                projection.nft(self.rpc.nft_id)

    def test_http_wallet_route_and_stale_history_return_explicit_success_or_503(self):
        server = ReadServer(('127.0.0.1', 0), handler(self.projection()))
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        thread.start()
        def request(wallet):
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            try:
                connection.request('GET', f'/v1/wallets/{wallet}/nfts')
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), json.loads(response.read())
            finally:
                connection.close()
        try:
            status, headers, body = request(addr(30))
            self.assertEqual(status, 200)
            self.assertEqual(body['token_ids'], [str(self.rpc.nft_id)])
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(request(ZERO)[0], 400)
            with self.index.db:
                self.index.db.execute('UPDATE cursors SET next_block=99')
            status, _, body = request(addr(30))
            self.assertEqual(status, 503)
            self.assertEqual(body, {'error': 'confirmed_projection_unavailable'})
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
