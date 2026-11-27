"""NEW CWR09 fixed-anchor checks; no existing test body is selected.

The composed case reuses exact7 setup/helpers with real SQLite/checkpoint/replay
and controlled ABI/header/clock responses. Its extra block contains a literal
transfer and royalty payout, with explicitly versioned owner/claim getters.
This is not an EVM, normal-F6, provider or maximum-workload qualification.
"""
from copy import deepcopy
import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from frontend_api import canonical_cache
from frontend_api.earnings import Earnings
from frontend_api.history import HistoryError, ZERO
from frontend_api.server import ReadServer, handler
from frontend_api.service import Projection, ProjectionError
from frontend_api.worker import WorkerClient, WorkerPool, _run
from tests_python import test_earnings_checkpoint_v2 as fixture
from zzz_ops.abi import calldata
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import BudgetedRPC, checkpoint, request_scope

HASH = '0x'+'ab'*32
OTHER = '0x'+'cd'*32
START = '0x'+'ef'*32


class AnchorRPC:
    def __init__(self):
        self.head = 111
        self.chain = 31337
        self.calls = []
        self.headers = {
            10: dict(number='0xa', hash=START, timestamp=hex(900)),
            99: dict(number=hex(99), hash=HASH, timestamp=hex(1000)),
            100: dict(number=hex(100), hash=OTHER, timestamp=hex(1001)),
        }

    def call(self, method, params=None):
        self.calls.append((method, deepcopy(params)))
        if method == 'eth_chainId':
            return self.chain
        if method == 'eth_blockNumber':
            return hex(self.head)
        if method == 'eth_getBlockByNumber':
            return deepcopy(self.headers[int(params[0], 16)])
        raise AssertionError('Unexpected financial read in anchor-only fixture')


def anchor_reader():
    wire = AnchorRPC()
    p = Projection.__new__(Projection)
    p.rpc = BudgetedRPC(wire)
    p.chain, p.start, p.start_hash = 31337, 10, START
    p.test_now = [1002]
    p.confirmations, p.max_age, p.clock = 12, 120, lambda:p.test_now[0]
    p.accounting_version, p.history, p.wallet_read_batch = 7, object(), 1
    p.earnings_history = Earnings.__new__(Earnings)
    p.earnings_history.p = p
    return p, wire


class FixedNFTAnchorTests(unittest.TestCase):
    def test_actual_checkpoint_card_and_earnings_keep_old_owner_and_payout_after_new_block(self):
        f = fixture.Checkpoint2APITests('runTest')
        self.addCleanup(f.doCleanups)
        f.setUp()
        f.config['wallet_read_batch'] = 1
        f.put(f.c['royalties'], 'mintEndRevision()', values=(1,))
        saved = f.install()
        saved_bytes = saved.read_bytes()
        # Reuse the existing main's geometry for this event ledger's bucket5.
        q = f.inner.responses.physical
        for role, method in (('vault', 'group(uint256)'),
                             ('portfolio_policy', 'configurationPending(uint256)')):
            target = f.c[role]
            f.inner.responses.selected[target, calldata(method, 5)] = (target, method, (5,))
        q.overrides[f.c['vault'], 'poolBucket(bytes32)'] = [f'{5:064x}']
        p = f.projection()
        self.assertEqual(p.protocol()['fixed_block_nft_view_profile'], 1)
        history = p.history
        p.history = None
        self.assertNotIn('fixed_block_nft_view_profile', p.protocol())
        p.history = history
        baseline_nft, baseline_earned = p.nft(f.i), p.earnings(f.i)
        original = f.rpc
        old_hash = original.hash(99)
        old_header = original.header

        def moving_header(number):
            result = old_header(number)
            if number >= 100:
                result['timestamp'] = hex(1118800+number-99)
            return result

        original.header = moving_header
        original.head = 111  # Confirmation depth now selects100, while99 remains fresh.
        h = original.header(100)
        with f.index.db:
            f.index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                (31337, 100, h['hash'], h['parentHash'], int(h['timestamp'], 16)))
            f.index.db.execute('UPDATE cursors SET next_block=101')
        f.emit('nft', 'Transfer(address,address,uint256)',
               (f.owners[f.i], fixture.addr(32), f.i), (), 100)
        f.emit('royalties', 'Claimed(uint256,address,address,uint256)',
               (f.i, ZERO, fixture.addr(32)), (7,), 100)
        native_claim = calldata('claimable(uint256,address)', f.i, fixture.addr(1))[:-64]+'0'*64

        class VersionedWire:
            def call(self, method, params=None):
                if method == 'eth_call' and params[-1]['blockHash'] == h['hash']:
                    tx = params[0]
                    if tx['to'] == f.c['nft'] and tx['data'] == calldata('ownerOf(uint256)', f.i):
                        return fixture.words(fixture.addr(32))
                    if tx['to'] == f.c['royalties'] and tx['data'] == native_claim:
                        return fixture.words(0)
                return original.call(method, params)

        f.rpc = VersionedWire()
        p = f.projection()
        fixed_nft = p.nft_at(f.i, 99, old_hash)
        fixed_earned = p.earnings_at(f.i, 99, old_hash)
        progress = []
        def advance_indexer_metadata(before, after, path='$'):
            if isinstance(before, dict):
                self.assertEqual(set(before), set(after))
                for key in before:
                    if key == 'indexer_next_block':
                        self.assertEqual((before[key],after[key]), (100,101))
                        before[key] = after[key]
                        progress.append(path+'.'+key)
                    else:
                        advance_indexer_metadata(before[key],after[key],path+'.'+key)
            elif isinstance(before, list):
                self.assertEqual(len(before),len(after))
                for index,(a,b) in enumerate(zip(before,after)):
                    advance_indexer_metadata(a,b,path+f'[{index}]')
        for before, after in ((baseline_nft, fixed_nft), (baseline_earned, fixed_earned)):
            before = deepcopy(before)
            self.assertEqual((before['provenance']['observed_head'],after['provenance']['observed_head']), (110,111))
            before['provenance']['observed_head'] = 111
            # Live ingestion may progress while its requested financial cutoff
            # stays99. Assert that exact metadata change, retaining all else.
            advance_indexer_metadata(before,after)
            self.assertEqual(before, after)
            self.assertEqual(after['provenance']['block_number'], 99)
            self.assertEqual(after['provenance']['block_hash'], old_hash)
        latest_nft, latest_earned = p.nft(f.i), p.earnings(f.i)
        self.assertEqual(latest_nft['owner'], fixture.addr(32))
        self.assertEqual(latest_earned['owner'], fixture.addr(32))
        self.assertEqual(latest_nft['provenance']['block_number'], 100)
        self.assertEqual(latest_earned['provenance']['block_number'], 100)
        native = lambda item: next(r['raw'] for r in item['claimable']['royalties'] if r['asset'] == ZERO)
        self.assertEqual(native(fixed_nft), '7')
        self.assertEqual(native(latest_nft), '0')
        self.assertEqual(fixed_earned['all_time'], latest_earned['all_time'])
        self.assertEqual(latest_earned['provenance']['epochs'][0]['history']['claim_events'], 1)
        self.assertEqual(fixed_earned['provenance']['epochs'][0]['history']['claim_events'], 0)
        self.assertEqual(fixed_earned['window']['through_timestamp_inclusive']-
                         fixed_earned['window']['after_timestamp_exclusive'], 86400)
        self.assertEqual(saved.read_bytes(), saved_bytes)
        self.assertIsNone(canonical_cache._current.get())
        self.assertIsNone(checkpoint())
        self.assertTrue(progress)
        type(self).indexer_progress_metadata_paths = progress

    def test_exact_anchor_inputs_and_live_final_proofs_fail_closed_without_leaks(self):
        invalid = [(True,HASH),(0,HASH),(-1,HASH),(1<<63,HASH),('99',HASH),
                   (99,None),(99,'0x'+'0'*64),(99,HASH.upper()),(99,'0x12')]
        for number, digest in invalid:
            p, wire = anchor_reader()
            with self.subTest(number=number, digest=digest), self.assertRaises(ValueError):
                p._snapshot_at(number, digest)
            self.assertEqual(wire.calls, [])
        for number, digest in ((9,HASH),(101,HASH),(99,OTHER)):
            p, _ = anchor_reader()
            with self.subTest(number=number), request_scope(), self.assertRaises(ProjectionError):
                p._snapshot_at(number, digest)
        for fault in ('wrong_number', 'expired', 'future'):
            p, wire = anchor_reader()
            wire.headers[99][{'wrong_number':'number','expired':'timestamp','future':'timestamp'}[fault]] = (
                '0x62' if fault == 'wrong_number' else hex(800 if fault == 'expired' else 1033))
            with self.subTest(fault=fault), request_scope(), self.assertRaises(ProjectionError):
                p._snapshot_at(99, HASH)
        for route in ('nft_at','earnings_at'):
            for fault in ('reorg','depth','age','age_exact','chain','deployment'):
                p, wire = anchor_reader()
                def body(identifier, *, snapshot):
                    self.assertEqual(snapshot[2], {'blockHash':HASH,'requireCanonical':True})
                    if fault == 'reorg': wire.headers[99]['hash'] = OTHER
                    elif fault == 'depth': wire.head = 109
                    elif fault in ('age','age_exact'): p.test_now[0] = 1120 if fault == 'age_exact' else 1121
                    elif fault == 'chain': wire.chain = 1
                    else: wire.headers[10]['hash'] = OTHER
                    p._finish(snapshot[0])
                    raise AssertionError('Unverified fixed result was released')
                target = p if route == 'nft_at' else p.earnings_history
                name = '_nft' if route == 'nft_at' else '_read'
                with self.subTest(route=route,fault=fault), patch.object(target,name,side_effect=body):
                    with self.assertRaises((ProjectionError,WorkLimit) if fault in ('age','age_exact') else ProjectionError):
                        getattr(p,route)(1,99,HASH)
                self.assertIsNone(canonical_cache._current.get())
                self.assertIsNone(checkpoint())
            for unsupported in ('profile','history','earnings'):
                p, wire = anchor_reader()
                if unsupported == 'profile': p.accounting_version = 6
                elif unsupported == 'history': p.history = None
                else: p.earnings_history = None
                with self.subTest(route=route,unsupported=unsupported), self.assertRaises(HistoryError):
                    getattr(p,route)(1,99,HASH)
                self.assertEqual(wire.calls, [])

    def test_http_and_nginx_routes_accept_only_exact_fixed_anchor_grammar(self):
        proxy = Mock()
        proxy.nft_at.return_value = {'kind':'nft'}
        proxy.earnings_at.return_value = {'kind':'earnings'}
        proxy.nft.return_value = {'kind':'latest'}
        h = handler(proxy)
        h.log_message = lambda *args:None
        server = ReadServer(('127.0.0.1',0),h)
        thread = threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        edge = Path('config/nginx/popl-api-locations.conf').read_text().split('location ~ "',1)[1].split('" {',1)[0]
        def get(path):
            conn = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            try:
                conn.request('GET',path)
                response = conn.getresponse()
                return response.status,json.loads(response.read())
            finally:conn.close()
        for path,method in ((f'/v1/nfts/7/at/99/{HASH}',proxy.nft_at),
                            (f'/v1/nfts/7/earnings/at/99/{HASH}',proxy.earnings_at)):
            self.assertIsNotNone(re.fullmatch(edge,path))
            self.assertEqual(get(path)[0],200)
            method.assert_called_once_with(7,99,HASH)
        for path,status in ((f'/v1/nfts/7/at/0/{HASH}',400),
                            (f'/v1/nfts/7/at/{1<<63}/{HASH}',400),
                            ('/v1/nfts/7/at/99/0x'+'0'*64,400),
                            (f'/v1/nfts/7/at/099/{HASH}',404),
                            (f'/v1/nfts/7/at/99/{HASH.upper()}',404),
                            (f'/v1/nfts/7/at/99/{HASH}?latest=1',404)):
            self.assertEqual(get(path)[0],status,path)
        self.assertEqual(proxy.nft_at.call_count,1)
        self.assertEqual(proxy.earnings_at.call_count,1)
        self.assertEqual(get('/v1/nfts/7'),(200,{'kind':'latest'}))
        proxy.nft.assert_called_once_with(7)

    def test_worker_child_client_and_pool_preserve_exact_fixed_inputs(self):
        payload = [7,99,HASH]
        for action in ('nft_at','earnings_at'):
            client = WorkerClient.__new__(WorkerClient)
            client._request = Mock(return_value={'ok':True})
            self.assertEqual(getattr(client,action)(*payload),{'ok':True})
            client._request.assert_called_once_with(action,payload)
            pool = WorkerPool.__new__(WorkerPool)
            pool._dispatch = Mock(return_value={'ok':True})
            self.assertEqual(getattr(pool,action)(*payload),{'ok':True})
            pool._dispatch.assert_called_once_with(action,*payload)
            proxy = Mock()
            getattr(proxy,action).return_value = {'anchor':HASH,'number':99}
            with tempfile.TemporaryDirectory() as directory, patch('frontend_api.worker.Projection',return_value=proxy):
                out = Path(directory)/'result.json'
                _run(str(out),{},None,action,payload)
                self.assertEqual(json.loads(out.read_bytes()),{'ok':{'anchor':HASH,'number':99}})
            getattr(proxy,action).assert_called_once_with(*payload)
