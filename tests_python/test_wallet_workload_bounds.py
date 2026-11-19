"""New wallet inventory workloads; injected RPC and owned loopback only.

The legacy complete endpoint remains complete-or-failed. New fixed-block pages
verify their own IDs; the last page alone never attests a multi-page inventory.
No historical test classes are imported into collection or rerun.
"""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.history import HistoryError
from frontend_api.service import Projection, ProjectionError
from frontend_api.server import ReadServer, handler
from frontend_api import worker
from tests_python import test_exact_lp_profile7 as fixtures
from tests_python.test_frontend_api import addr
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget


OWNER = addr(30)
OTHER = addr(31)


class WalletWorkloadBoundsTests(unittest.TestCase):
    def fixture(self, count=1000):
        f = fixtures.Fresh7API(self)
        p = f.p
        ids = [(1 << 255) + i + 1 for i in range(count)]
        owners = dict.fromkeys(ids, OWNER)
        p.history = object()
        p._history_snapshot = lambda *_a, **_kw: SimpleNamespace(
            owners=copy.copy(owners), provenance={'controlled_fixture': True})
        f.rpc.put(f.c['nft'], 'balanceOf(address)', (OWNER,), (count,))
        f.rpc.put(f.c['nft'], 'mintedCount()', values=(count,))
        for identifier in ids:
            f.rpc.put(f.c['nft'], 'ownerOf(uint256)', (identifier,), (OWNER,))
        header, _head, _block = p._snapshot()
        f.rpc.calls.clear()
        return f, p, ids, owners, header['number']

    def test_legacy_complete_thousand_owner_request_exposes_default_budget_limit(self):
        f, p, _ids, _owners, _block = self.fixture()
        with self.assertRaisesRegex(WorkLimit, 'rpc_budget'):
            p.wallet(OWNER)
        self.assertEqual(len(f.rpc.calls), Budget().calls)
        # No larger limit or partial successful legacy response is introduced.
        self.assertEqual(Budget().calls, 1024)

    def test_all_thousand_ids_are_verified_once_in_bounded_same_block_pages(self):
        f, p, ids, _owners, block = self.fixture()
        pages = []
        maximum_calls = 0
        owner_selector = calldata('ownerOf(uint256)', 0)[:10]
        for offset in range(0, 1000, 16):
            f.rpc.calls.clear()
            result = p.wallet_page(OWNER, block, offset)
            maximum_calls = max(maximum_calls, len(f.rpc.calls))
            owned = [params for method, params in f.rpc.calls if method == 'eth_call' and
                     params[0]['to'] == f.c['nft'] and params[0]['data'][:10] == owner_selector]
            self.assertEqual(len(owned), len(result['token_ids']))
            self.assertTrue(all(params[1] == f.block() for params in owned))
            self.assertFalse(result['complete'])
            self.assertEqual(result['verified_count'], min(16, 1000-offset))
            self.assertLess(len(json.dumps({'ok': result}).encode()), worker.MAX_RESULT)
            pages.append(result)
        self.assertLessEqual(maximum_calls, 1024)
        self.assertEqual([int(i) for row in pages for i in row['token_ids']], ids)
        self.assertEqual(len({row['inventory_sha256'] for row in pages}), 1)
        self.assertEqual(len({row['provenance']['block_hash'] for row in pages}), 1)
        self.assertEqual([row['offset'] for row in pages], list(range(0, 1000, 16)))
        self.assertIsNone(pages[-1]['next_offset'])
        self.assertEqual(pages[-1]['verified_count'], 8)

    def test_complete_is_only_true_when_the_page_verifies_the_whole_inventory(self):
        for count in (0, 1, 16, 17):
            with self.subTest(count=count):
                _f, p, _ids, _owners, block = self.fixture(count)
                first = p.wallet_page(OWNER, block)
                self.assertEqual(first['complete'], count <= 16)
                self.assertEqual(first['count'], count)
                if count == 17:
                    last = p.wallet_page(OWNER, block, 16)
                    self.assertFalse(last['complete'])
                    self.assertIsNone(last['next_offset'])

    def test_invalid_cursor_types_and_unconfirmed_block_never_return_a_page(self):
        f, p, _ids, _owners, block = self.fixture(17)
        for number, offset in ((True, 0), ('99', 0), (block, True), (block, '16'),
                               (block, -1), (block, 1), (block, 1000)):
            f.rpc.calls.clear()
            with self.subTest(number=number, offset=offset), self.assertRaises(ValueError):
                p.wallet_page(OWNER, number, offset)
            self.assertEqual(f.rpc.calls, [])
        for number in (p.start-1, block+1):
            with self.subTest(block=number), self.assertRaises(ProjectionError):
                p.wallet_page(OWNER, number)
        with self.assertRaises(ValueError):
            p.wallet_page(OWNER, block, 32)

    def test_missing_history_count_mismatch_and_wrong_selected_owner_fail_closed(self):
        f, p, ids, owners, block = self.fixture(17)
        p.history = None
        with self.assertRaises(HistoryError):
            p.wallet_page(OWNER, block)
        p.history = object()
        owners.pop(ids[-1])
        with self.assertRaises(HistoryError):
            p.wallet_page(OWNER, block)
        owners[ids[-1]] = OWNER
        f.rpc.put(f.c['nft'], 'ownerOf(uint256)', (ids[3],), (OTHER,))
        with self.assertRaises(HistoryError):
            p.wallet_page(OWNER, block)

    def test_reorg_and_lost_confirmation_are_not_successful_partial_pages(self):
        _f, p, _ids, _owners, block = self.fixture(17)
        for message in ('Canonical chain changed', 'Lost required confirmation depth'):
            with self.subTest(message=message), patch.object(p, '_finish', side_effect=ProjectionError(message)):
                with self.assertRaises(ProjectionError):
                    p.wallet_page(OWNER, block)

    def test_currency_outage_does_not_hide_confirmed_ownership(self):
        f, p, ids, _owners, block = self.fixture(17)
        f.rpc.codes[addr(21)] = '0x6000'
        result = p.wallet_page(OWNER, block)
        self.assertEqual(result['token_ids'], list(map(str, ids[:16])))
        self.assertFalse(result['complete'])

    def test_first_thousand_holder_page_fits_with_sixteen_or_sixtyfour_currencies(self):
        for count in (16, 64):
            for faulted in (False, True):
                with self.subTest(erc20_currencies=count, metadata_faulted=faulted):
                    f, _old, ids, owners, block = self.fixture()
                    config = copy.deepcopy(f.config)
                    tokens = [addr(21)]
                    for index in range(count-1):
                        token = addr(30000+index)
                        code = '0x60'+f'{index+1:02x}'+'00'
                        f.rpc.codes[token] = code
                        f.rpc.put(token, 'decimals()', values=(18,))
                        config['assets'].append(dict(address=token, decimals=18,
                            symbol='COIN'+str(index),
                            code_hash='0x'+keccak256(bytes.fromhex(code[2:])).hex()))
                        tokens.append(token)
                    f.rpc.put(f.c['royalties'], 'assetCount()', values=(count+1,))
                    for index, token in enumerate([('0x'+'0'*40), *tokens]):
                        f.rpc.put(f.c['royalties'], 'assets(uint256)', (index,), (token,))
                    p = Projection(config, f.rpc, clock=lambda:4000)
                    p.history = object()
                    p._history_snapshot = lambda *_a, **_kw: SimpleNamespace(
                        owners=copy.copy(owners), provenance={'controlled_fixture': True})
                    if faulted:
                        for token in tokens:
                            f.rpc.codes[token] = '0x6000'
                    f.rpc.calls.clear()
                    result = p.wallet_page(OWNER, block)
                    self.assertEqual(result['token_ids'], list(map(str, ids[:16])))
                    self.assertFalse(result['complete'])
                    self.assertLessEqual(len(f.rpc.calls), 1024)
                    self.assertLess(len(json.dumps({'ok':result}).encode()), worker.MAX_RESULT)

    def test_changed_indexed_inventory_has_a_different_digest(self):
        f, p, ids, owners, block = self.fixture(17)
        first = p.wallet_page(OWNER, block)
        replacement = ids[-1]+1
        owners.pop(ids[-1]); owners[replacement] = OWNER
        f.rpc.put(f.c['nft'], 'ownerOf(uint256)', (replacement,), (OWNER,))
        last = p.wallet_page(OWNER, block, 16)
        self.assertNotEqual(first['inventory_sha256'], last['inventory_sha256'])
        self.assertFalse(last['complete'])

    def test_worker_child_client_and_pool_forward_the_explicit_page_action(self):
        result = {'kind': 'fixed_block_wallet_inventory_page', 'complete': False}
        projection = SimpleNamespace(wallet_page=lambda *args: dict(result, arguments=list(args)))
        with tempfile.TemporaryDirectory(prefix='popl-wallet-page-') as directory:
            output = Path(directory)/'result.json'
            with patch.object(worker, 'Projection', return_value=projection):
                worker._run(str(output), {}, None, 'wallet_page', [OWNER, 99, 16])
            self.assertEqual(json.loads(output.read_text())['ok']['arguments'], [OWNER, 99, 16])
        client = object.__new__(worker.WorkerClient)
        with patch.object(client, '_request', return_value=result) as request:
            self.assertEqual(client.wallet_page(OWNER, 99, 16), result)
            request.assert_called_once_with('wallet_page', [OWNER, 99, 16])
        pool = object.__new__(worker.WorkerPool)
        with patch.object(pool, '_dispatch', return_value=result) as dispatch:
            self.assertEqual(pool.wallet_page(OWNER, 99, 16), result)
            dispatch.assert_called_once_with('wallet_page', OWNER, 99, 16)


class WalletPageHTTPTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.p = SimpleNamespace(chain=31337)
        def page(*args):
            self.requests.append(('page', args))
            return {'schema': 1, 'kind': 'fixed_block_wallet_inventory_page', 'complete': False}
        def complete(owner):
            self.requests.append(('legacy', owner)); return {'schema': 2, 'complete': True}
        self.p.wallet_page = page
        self.p.wallet = complete
        self.server = ReadServer(('127.0.0.1', 0), handler(self.p))
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(2)

    def request(self, path):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_address[1], timeout=3)
        try:
            c.request('GET', path); response = c.getresponse()
            return response.status, json.loads(response.read())
        finally:
            c.close()

    def test_explicit_page_route_and_legacy_route_stay_distinct(self):
        status, result = self.request('/v1/wallets/'+OWNER+'/nfts/99/16')
        self.assertEqual(status, 200); self.assertFalse(result['complete'])
        self.assertEqual(self.requests, [('page', (OWNER, 99, 16))])
        status, result = self.request('/v1/wallets/'+OWNER+'/nfts')
        self.assertEqual(status, 200); self.assertEqual(result['schema'], 2)
        self.assertEqual(self.requests[-1], ('legacy', OWNER))

    def test_noncanonical_or_misaligned_route_cursor_does_not_start_work(self):
        for suffix, expected in (('99/1', 400), ('099/0', 404), ('99/1000', 404),
                                  ('99/-16', 404), ('99/16?x=1', 404)):
            status, _ = self.request('/v1/wallets/'+OWNER+'/nfts/'+suffix)
            self.assertEqual(status, expected)
        self.assertEqual(self.requests, [])

    def test_upstream_failure_is_sanitized_and_not_a_partial_inventory(self):
        def fail(*_):
            raise RuntimeError('secret credential must not be printed')
        self.p.wallet_page = fail
        status, result = self.request('/v1/wallets/'+OWNER+'/nfts/99/0')
        self.assertEqual(status, 503)
        self.assertEqual(result, {'error': 'confirmed_projection_unavailable'})


if __name__ == '__main__':
    unittest.main()
