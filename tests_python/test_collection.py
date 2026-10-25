import copy
import http.client
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from frontend_api.collection import read
from frontend_api.history import HistoryError
from frontend_api.service import Projection, ProjectionError
from frontend_api.server import ReadServer, handler
from frontend_api.worker import _run, WorkerClient, WorkerPool
from zzz_ops.errors import RpcError, WorkLimit
from tests_python.test_wallet_summary import Snapshot, OWNER, OTHER
from tests_python import test_frontend_history as fixtures
from tests_python.test_frontend_api import addr


class CollectionSnapshot(Snapshot):
    def __init__(self, count=33):
        super().__init__(count)
        self.accounting_version = 1
        self.dormant_status = 5
        self.corrupt = None
        self.overrides = {}
    def _uint(self, role, method, *args, block):
        self.check(block); self.calls.append((method, args, block))
        i = args[0] if args else 0
        if (method, i) in self.overrides: return self.overrides[method, i]
        if method == 'mintedCount()': return len(self.ids)
        if method.startswith(('mintOrdinalOf', 'tokenAtOrdinal')): return i
        if method.startswith('rarityOf'): return i % 3
        if method.startswith('paletteOf'): return i % 58
        if method.startswith('patternOf'): return i % 4
        if method.startswith('nftStatus'): return 5 if i % 4 == 0 else 1
        if method.startswith(('sharesOf', 'nftBucket')): return 0 if i % 4 == 0 else 1
        if method.startswith('weightOf'): return 0 if i % 4 == 0 else i % 3 + 1
        raise AssertionError(method)
    def _call(self, target, method, i, block, words=1):
        self.check(block); self.calls.append((method, (i,), block))
        if self.limit: raise WorkLimit('rpc_budget')
        if method.startswith('traitsReady'): return ['0'*63+'1']
        if method.startswith('currentLPValue'):
            if i == self.corrupt: return ['0'*63+'2', '0'*64]
            if i == self.lp_missing: return ['0'*64, '0'*64]
            return ['0'*63+'1', f'{0 if i % 4 == 0 else i * 10**18:064x}']
        raise AssertionError(method)


class CollectionTests(unittest.TestCase):
    def test_complete_chunks_cover_all_nfts_once_and_match_lp(self):
        p = CollectionSnapshot()
        parts = [read(p, 90, offset) for offset in (0, 16, 32)]
        self.assertEqual([r['next_offset'] for r in parts], [16, 32, None])
        self.assertEqual(parts[0]['inventory_token_ids'], list(map(str, p.ids)))
        self.assertTrue(all(r['inventory_token_ids'] is None for r in parts[1:]))
        self.assertEqual(sum(int(r['chunk_lp_usd_18']) for r in parts), sum(i for i in p.ids if i % 4) * 10**18)
        self.assertEqual(sum(r['chunk_activated'] for r in parts), 25)
        self.assertEqual(len({r['inventory_sha256'] for r in parts}), 1)
        self.assertEqual([r['token_id'] for part in parts for r in part['positions']], list(map(str, p.ids)))
    def test_full_cap_has_bounded_page_reads(self):
        p = CollectionSnapshot(1000); out = read(p, 90, 992)
        self.assertEqual(len(out['positions']), 8); self.assertIsNone(out['next_offset'])
        self.assertLessEqual(len(p.calls), 1 + 8 * 12)
    def test_empty_collection_is_confirmed_zero(self):
        out = read(CollectionSnapshot(0), 90, 0)
        self.assertEqual((out['count'], out['positions'], out['chunk_lp_usd_18']), (0, [], '0'))
    def test_missing_one_lp_poison_total_without_erasing_other_positions(self):
        p = CollectionSnapshot(); p.lp_missing = 2
        out = read(p, 90, 0)
        self.assertIsNone(out['chunk_lp_usd_18'])
        self.assertIsNone(out['positions'][1]['position']['current_lp_value']['raw'])
        self.assertEqual(out['positions'][0]['position']['current_lp_value']['raw'], str(10**18))
    def test_current_lp_not_lifetime_contributions_sets_evolution(self):
        p = CollectionSnapshot(1)
        original = p._call
        def call(target, method, i, **kw):
            return ['0'*63+'1', f'{10000 * 10**18:064x}'] if method.startswith('currentLPValue') else original(target, method, i, **kw)
        p._call = call
        self.assertEqual(read(p, 90, 0)['positions'][0]['position']['evolution'], 'singularity')
    def test_wrong_owner_rejected(self):
        p = CollectionSnapshot(); p.bad_owner = 8
        with self.assertRaises(HistoryError): read(p, 90, 0)
    def test_wrong_mint_identity_count_and_traits_rejected(self):
        for method, key, value in [('tokenAtOrdinal(uint256)', 2, 777), ('mintOrdinalOf(uint256)', 2, 0),
                ('mintedCount()', 0, 34), ('rarityOf(uint256)', 2, 3), ('paletteOf(uint256)', 2, 58),
                ('patternOf(uint256)', 2, 4), ('weightOf(uint256)', 2, 1), ('nftStatus(uint256)', 2, 5),
                ('sharesOf(uint256)', 2, 0)]:
            with self.subTest(method=method), self.assertRaises((ProjectionError, HistoryError)):
                p = CollectionSnapshot(); p.overrides[method, key] = value; read(p, 90, 0)
    def test_invalid_cursors_and_blocks(self):
        for block, offset in [(90, -1), (90, 1), (90, 1000), (90, True), (True, 0), ('90', 0), (90, 48)]:
            with self.subTest(block=block, offset=offset), self.assertRaises(ValueError): read(CollectionSnapshot(), block, offset)
        with self.assertRaises(ProjectionError): read(CollectionSnapshot(), 101, 0)
    def test_missing_history_stale_and_reorg_rejected(self):
        p = CollectionSnapshot(); p.history = None
        with self.assertRaises(HistoryError): read(p, 90, 0)
        p = CollectionSnapshot(); p.header['timestamp'] = 1
        with self.assertRaises(ProjectionError): read(p, 90, 0)
        p = CollectionSnapshot(); p.changed = True
        with self.assertRaises(ProjectionError): read(p, 90, 0)
    def test_work_budget_not_masked_as_unavailable(self):
        p = CollectionSnapshot(); p.limit = True
        with self.assertRaises(WorkLimit): read(p, 90, 0)
    def test_malformed_boolean_not_masked_as_outage(self):
        p = CollectionSnapshot(); p.corrupt = 2
        with self.assertRaises(ProjectionError): read(p, 90, 0)
    def test_dormant_cannot_report_unknown_lp(self):
        p = CollectionSnapshot(); p.lp_missing = 4
        with self.assertRaises(ProjectionError): read(p, 90, 0)
    def test_current_dormant_three_cannot_report_unknown_lp(self):
        p=CollectionSnapshot(4);p.accounting_version=3;p.dormant_status=3
        p.overrides['nftStatus(uint256)',4]=3;p.lp_missing=4
        with self.assertRaises(ProjectionError):read(p,90,0)
    def test_remote_eligibility_persists_without_fabricated_local_value(self):
        p = CollectionSnapshot(2); p.lp_missing = 2; p.overrides['nftStatus(uint256)', 2] = 3
        out = read(p, 90, 0)
        self.assertEqual(out['chunk_activated'], 2); self.assertIsNone(out['chunk_lp_usd_18'])
        self.assertEqual(out['positions'][1]['position']['status'], 'remote')
    def test_valuation_read_outage_does_not_become_zero(self):
        p = CollectionSnapshot(1); original = p._call
        def call(target, method, i, **kw):
            if method.startswith('currentLPValue'): raise RpcError('upstream fault')
            return original(target, method, i, **kw)
        p._call = call
        self.assertIsNone(read(p, 90, 0)['chunk_lp_usd_18'])


class CollectionIntegrationTests(unittest.TestCase):
    setUp = fixtures.ConfirmedHistoryTests.setUp
    tearDown = fixtures.ConfirmedHistoryTests.tearDown
    projection = fixtures.ConfirmedHistoryTests.projection
    def configure_other(self):
        i = self.rpc.other
        for method, value in [('mintOrdinalOf(uint256)', 2), ('traitsReady(uint256)', 0), ('nftStatus(uint256)', 5),
                ('nftBucket(uint256)', 0), ('sharesOf(uint256)', 0), ('weightOf(uint256)', 0)]:
            self.rpc.put(addr(3) if method.startswith(('nftStatus','nftBucket','sharesOf')) else addr(5) if method.startswith('weightOf') else addr(2), method, (i,), (value,))
        self.rpc.put(addr(2), 'tokenAtOrdinal(uint256)', (2,), (i,))
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (i,), (1, 0))
    def test_real_sqlite_inventory_uses_exact_contract_owner_and_lp(self):
        self.configure_other(); out = self.projection().collection(99)
        self.assertEqual(out['count'], 2); self.assertEqual(out['chunk_activated'], 1)
        self.assertEqual(out['chunk_lp_usd_18'], str(1432*10**18))
        dormant = next(n for n in out['positions'] if n['token_id'] == str(self.rpc.other))
        self.assertFalse(dormant['traits_ready']); self.assertIsNone(dormant['traits'])
        self.assertEqual(dormant['owner'], addr(31))
    def test_http_and_both_supervised_dispatchers(self):
        self.configure_other(); p = self.projection()
        server = ReadServer(('127.0.0.1', 0), handler(p)); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            for suffix, status in [('99/0', 200), ('99/1', 400), ('99/1000', 404), ('100/0', 503), ('99/00', 404)]:
                c = http.client.HTTPConnection('127.0.0.1', server.server_port)
                c.request('GET', '/v1/collection/'+suffix); r = c.getresponse(); body = r.read(); self.assertEqual(r.status, status); c.close()
                self.assertNotIn(b'rpc_urls', body)
        finally: server.shutdown(); server.server_close(); thread.join()
        output = Path(self.temp.name)/'collection-worker.json'
        with patch('frontend_api.worker.Projection', return_value=p): _run(str(output), {}, None, 'collection', [99, 0])
        self.assertEqual(json.loads(output.read_text())['ok']['count'], 2)
        with patch.object(WorkerClient, '_request', return_value={'ok': True}) as request:
            self.assertEqual(WorkerClient(fixtures.configuration()).collection(99), {'ok': True})
            request.assert_called_once_with('collection', [99, 0])
        pool = object.__new__(WorkerPool)
        with patch.object(pool, '_dispatch', return_value={'ok': True}) as dispatch:
            self.assertEqual(pool.collection(99), {'ok': True}); dispatch.assert_called_once_with('collection', 99, 0)


if __name__ == '__main__': unittest.main()
