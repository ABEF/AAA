"""NEW compact-wallet contract, dispatch and admission checks; no historical test imports."""
import copy
from email.message import Message
import hashlib
import http.client
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from frontend_api.admission import AdmissionRejected, ClientAdmission
from frontend_api.history import HistoryError
from frontend_api.http_runtime import BoundedHTTPServer
from frontend_api.server import handler
from frontend_api.service import Projection, ProjectionError
from frontend_api import wallet_view
from frontend_api.wallet_earnings import asset_page
from frontend_api.worker import WorkerClient, WorkerPool, _run, MAX_RESULT
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import BudgetedRPC, request_scope

OWNER = '0x' + '12' * 20
NFT = '0x' + '34' * 20
CONTROLLER = '0x' + '56' * 20
HASH = '0x' + '78' * 32

def address(number):
    return '0x' + format(number, '040x')

def sections():
    history = dict(available=True, through_block=99, block_hash=HASH, minted_count=1,
        from_block=10, start_block_hash='0x' + '11' * 32, start_parent_hash='0x' + '22' * 32)
    provenance = dict(block_number=99, block_hash=HASH, block_timestamp=1000,
        configuration_sha256='a' * 64, confirmations=2, finality='confirmation_depth_only')
    ownership = dict(schema=1, chain_id=31337, wallet=OWNER, nft_contract=NFT, count=1, offset=0,
        chunk_size=16, token_ids=['1'], next_offset=None, inventory_sha256=hashlib.sha256(b'1').hexdigest(),
        lifecycle=dict(state='operating'), history=history, provenance=provenance,
        lp_usd_18='100', claimable_eth_wei='7')
    earnings = copy.deepcopy(ownership)
    earnings.pop('history')
    earnings['provenance']['epochs'] = [dict(controller=CONTROLLER, history=copy.deepcopy(history))]
    engine = SimpleNamespace(descriptors={address(i): object() for i in (0, 20, 21)}, finish_checkpoint=Mock())
    earnings.update(asset_page(engine, 0))
    projection = SimpleNamespace(accounting_version=7, earnings_history=engine,
        rpc=BudgetedRPC(SimpleNamespace(call=Mock(side_effect=AssertionError('unexpected RPC')))),
        contracts={'access': SimpleNamespace(address=CONTROLLER)}, _header=Mock(return_value=dict(number=99, hash=HASH, timestamp=1000)),
        _finish=Mock())
    return projection, ownership, earnings

class WalletViewContractTests(unittest.TestCase):
    def test_currency_cursor_covers_complete_sorted_union_once_and_partial_tail(self):
        descriptors = {address(i): object() for i in reversed(range(66))}
        pages = [asset_page(SimpleNamespace(descriptors=descriptors), offset) for offset in range(0, 66, 4)]
        self.assertEqual([address(i) for i in range(66)], [asset for page in pages for asset in page['selected_asset_ids']])
        self.assertEqual(2, len(pages[-1]['selected_asset_ids']))
        self.assertIsNone(pages[-1]['next_asset_offset'])
        expected = hashlib.sha256(','.join(sorted(descriptors)).encode('ascii')).hexdigest()
        self.assertTrue(all(page['asset_inventory_sha256'] == expected for page in pages))
        self.assertTrue(all(page['asset_ids'] == sorted(descriptors) for page in pages))

    def test_currency_cursor_rejects_invalid_types_bounds_alignment_and_empty_union(self):
        engine = SimpleNamespace(descriptors={address(i): object() for i in range(6)})
        for offset in (True, False, -4, 1, 3, 8, '0', 0.0, None):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                asset_page(engine, offset)
        for descriptors in ({}, {address(i): None for i in range(2049)}):
            with self.assertRaises(ValueError):
                asset_page(SimpleNamespace(descriptors=descriptors), 0)

    def test_nft_cursor_refuses_before_any_snapshot_or_transport(self):
        projection = SimpleNamespace(accounting_version=7, earnings_history=SimpleNamespace(
            descriptors={address(0): object()}))
        for block, offset in ((True, 0), ('99', 0), (99, True), (99, -16), (99, 1), (99, 1000)):
            with self.subTest(block=block, offset=offset), self.assertRaises(ValueError):
                wallet_view.read(projection, OWNER, block, offset, 0)

    def test_compact_profile_requires_exact_lp_and_configured_earnings(self):
        for version, earnings in ((6, object()), (7, None)):
            with self.subTest(version=version), self.assertRaises(HistoryError):
                wallet_view.read(SimpleNamespace(accounting_version=version, earnings_history=earnings), OWNER, 99)

    def test_complete_section_identity_and_each_cutoff_field_are_authenticated(self):
        _, ownership, earnings = sections()
        wallet_view._same_page(ownership, earnings)
        for key in ('chain_id', 'wallet', 'nft_contract', 'count', 'offset', 'chunk_size', 'token_ids',
                    'next_offset', 'inventory_sha256', 'lifecycle'):
            modified = copy.deepcopy(earnings)
            modified[key] = 'contradiction'
            with self.subTest(key=key), self.assertRaises(HistoryError):
                wallet_view._same_page(ownership, modified)
        for key in ('block_number', 'block_hash', 'block_timestamp', 'configuration_sha256', 'confirmations', 'finality'):
            modified = copy.deepcopy(earnings)
            modified['provenance'][key] = 'contradiction'
            with self.subTest(key=key), self.assertRaises(HistoryError):
                wallet_view._same_page(ownership, modified)

    def test_each_raw_history_origin_and_cutoff_field_are_authenticated(self):
        _, ownership, earnings = sections()
        for key in ('through_block', 'block_hash', 'minted_count', 'from_block', 'start_block_hash', 'start_parent_hash'):
            modified = copy.deepcopy(earnings)
            modified['provenance']['epochs'][-1]['history'][key] = 'contradiction'
            with self.subTest(key=key), self.assertRaises(HistoryError):
                wallet_view._same_page(ownership, modified)

    def test_transport_earnings_failure_keeps_verified_summary_after_live_final_proofs(self):
        projection, ownership, _ = sections()
        original_rpc = projection.rpc
        with patch.object(wallet_view, 'read_summary', return_value=ownership), \
                patch.object(wallet_view, 'read_earnings', side_effect=RpcError('private-upstream-detail')), request_scope():
            result = wallet_view.read(projection, OWNER, 99)
        self.assertIsNone(result['earnings'])
        self.assertEqual('earnings_unavailable', result['earnings_error'])
        self.assertEqual('100', result['summary']['lp_usd_18'])
        self.assertEqual('7', result['summary']['claimable_eth_wei'])
        projection.earnings_history.finish_checkpoint.assert_called_once_with()
        projection._finish.assert_called_once_with(dict(number=99, hash=HASH, timestamp=1000))
        self.assertIs(original_rpc, projection.rpc)
        self.assertNotIn('private-upstream-detail', json.dumps(result))

    def test_core_or_work_refusal_never_becomes_independent_earnings_success(self):
        for refusal in (WorkLimit('rpc_budget'), ProjectionError('identity'), HistoryError('history')):
            projection, ownership, _ = sections()
            with self.subTest(refusal=type(refusal).__name__), \
                    patch.object(wallet_view, 'read_summary', return_value=ownership), \
                    patch.object(wallet_view, 'read_earnings', side_effect=refusal), request_scope():
                with self.assertRaises(type(refusal)):
                    wallet_view.read(projection, OWNER, 99)
            projection._finish.assert_not_called()

    def test_missing_one_summary_metric_does_not_erase_other_metric_or_earnings(self):
        for missing, healthy in (('lp_usd_18', 'claimable_eth_wei'), ('claimable_eth_wei', 'lp_usd_18')):
            projection, ownership, earnings = sections()
            ownership[missing] = None
            with self.subTest(missing=missing), patch.object(wallet_view, 'read_summary', return_value=ownership), \
                    patch.object(wallet_view, 'read_earnings', return_value=earnings), request_scope():
                result = wallet_view.read(projection, OWNER, 99)
            self.assertIsNone(result['summary'][missing])
            self.assertEqual(ownership[healthy], result['summary'][healthy])
            self.assertIsNotNone(result['earnings'])
            self.assertIsNone(result['earnings_error'])

    def test_section_mismatch_or_final_anchor_change_refuses_whole_page(self):
        for variant in ('controller', 'timestamp', 'history', 'selected_assets'):
            projection, ownership, earnings = sections()
            if variant == 'controller':
                earnings['provenance']['epochs'][-1]['controller'] = address(999)
            elif variant == 'timestamp':
                projection._header.return_value['timestamp'] += 1
            elif variant == 'history':
                ownership['history']['through_block'] = 98
            else:
                earnings['selected_asset_ids'] = []
            with self.subTest(variant=variant), patch.object(wallet_view, 'read_summary', return_value=ownership), \
                    patch.object(wallet_view, 'read_earnings', return_value=earnings), request_scope():
                with self.assertRaises(HistoryError):
                    wallet_view.read(projection, OWNER, 99)

class WalletViewWireTests(unittest.TestCase):
    def run_handler(self, path):
        projection = SimpleNamespace(wallet_view=Mock(return_value={'new_wire': True}))
        Handler = handler(projection)
        request = object.__new__(Handler)
        request.server = SimpleNamespace(server_address=('127.0.0.1', 8787))
        request.headers = Message()
        request.headers['Host'] = '127.0.0.1:8787'
        request.path = path
        request.begin_work = Mock()
        request._json = Mock()
        request.do_GET()
        return request, projection

    def test_handler_dispatches_exact_four_part_cursor_once(self):
        request, projection = self.run_handler('/v1/wallets/' + OWNER + '/view/99/992/64')
        projection.wallet_view.assert_called_once_with(OWNER, 99, 992, 64)
        request.begin_work.assert_called_once_with()
        request._json.assert_called_once_with(200, {'new_wire': True})

    def test_handler_rejects_bad_cursor_or_noncanonical_wire_before_admission(self):
        suffixes = ('99/15/0', '99/0/3', '99/0/2048', '099/0/0', '99/00/0', '99/0/00',
            '99/0/-4', '99/0/0?other=1', '99/0/0/', '99/1000/0')
        for suffix in suffixes:
            with self.subTest(suffix=suffix):
                request, projection = self.run_handler('/v1/wallets/' + OWNER + '/view/' + suffix)
                projection.wallet_view.assert_not_called()
                request.begin_work.assert_not_called()
                self.assertIn(request._json.call_args.args[0], (400, 404))

    def test_owned_http_listener_preserves_get_only_and_one_shared_admission_bucket(self):
        projection = SimpleNamespace(wallet_view=Mock(return_value={'new_wire': True}))
        admission = ClientAdmission(clock=lambda: 0)
        server = BoundedHTTPServer(('127.0.0.1', 0), handler(projection), admission=admission)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            path = '/v1/wallets/' + OWNER + '/view/99/0/0'
            for index in range(13):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=3)
                connection.request('GET', path)
                response = connection.getresponse()
                payload = json.loads(response.read())
                self.assertEqual(200 if index < 12 else 429, response.status)
                self.assertEqual({'new_wire': True} if index < 12 else {'error': 'client_rate_limited'}, payload)
                if index == 12:
                    self.assertEqual('1', response.getheader('Retry-After'))
                connection.close()
            self.assertEqual(12, projection.wallet_view.call_count)
            connection = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=3)
            connection.request('POST', path)
            response = connection.getresponse()
            response.read()
            self.assertEqual(405, response.status)
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())

    def test_proxy_allowlist_carries_exact_new_get_route_without_arbitrary_paths(self):
        text = (Path(__file__).resolve().parents[1] / 'config/nginx/popl-api-locations.conf').read_text()
        matched = re.search(r'location ~ "([^"]+)" \{(.*?)\n\}', text, re.S)
        self.assertIsNotNone(matched)
        pattern, body = matched.groups()
        self.assertIsNotNone(re.fullmatch(pattern, '/v1/wallets/' + OWNER + '/view/99/992/64'))
        for suffix in ('099/0/0', '99/00/0', '99/0/00', '99/0/-1', '99/0/0/extra', '99/0/0?x=1'):
            self.assertIsNone(re.fullmatch(pattern, '/v1/wallets/' + OWNER + '/view/' + suffix))
        self.assertIn('if ($request_method != GET) { return 405; }', body)
        self.assertIn('proxy_pass http://127.0.0.1:8787;', body)
        self.assertNotIn('$request_uri', body)

    def test_worker_supervisor_and_pool_forward_only_explicit_wallet_view_payload(self):
        client = object.__new__(WorkerClient)
        client._request = Mock(return_value={'ok': 1})
        self.assertEqual({'ok': 1}, client.wallet_view(OWNER, 99, 992, 64))
        client._request.assert_called_once_with('wallet_view', [OWNER, 99, 992, 64])
        pool = object.__new__(WorkerPool)
        pool._dispatch = Mock(return_value={'ok': 2})
        self.assertEqual({'ok': 2}, pool.wallet_view(OWNER, 99, 992, 64))
        pool._dispatch.assert_called_once_with('wallet_view', OWNER, 99, 992, 64)

    def test_actual_worker_dispatch_serializes_new_result_and_enforces_existing_result_limit(self):
        for payload, expected in (({'new_wire': True}, {'ok': {'new_wire': True}}),
                                  ({'oversized': 'x' * MAX_RESULT}, {'error': 'result_limit'})):
            projection = SimpleNamespace(wallet_view=Mock(return_value=payload))
            with self.subTest(oversized='oversized' in payload), TemporaryDirectory(prefix='new-compact-worker-') as directory, \
                    patch('frontend_api.worker.Projection', return_value=projection):
                output = Path(directory) / 'result.json'
                _run(output, {}, None, 'wallet_view', [OWNER, 99, 0, 0])
                self.assertEqual(expected, json.loads(output.read_bytes()))
                projection.wallet_view.assert_called_once_with(OWNER, 99, 0, 0)

    def test_actual_worker_maps_new_projection_failure_without_upstream_detail(self):
        for error, expected in ((RpcError('private-provider-secret'), 'unavailable'), (WorkLimit('rpc_budget'), 'rpc_budget')):
            projection = SimpleNamespace(wallet_view=Mock(side_effect=error))
            with self.subTest(expected=expected), TemporaryDirectory(prefix='new-compact-worker-') as directory, \
                    patch('frontend_api.worker.Projection', return_value=projection):
                output = Path(directory) / 'result.json'
                _run(output, {}, None, 'wallet_view', [OWNER, 99, 0, 0])
                self.assertEqual({'error': expected}, json.loads(output.read_bytes()))

    def test_default_admission_ideal_clock_covers_complete_compact_refresh_and_visible_cards(self):
        results = []
        for count in (1, 17, 1000):
            requests = 1 + (count + 15) // 16 + 2 * min(count, 8)
            clock = [0.0]
            admission = ClientAdmission(clock=lambda: clock[0])
            admitted = []
            for _ in range(requests):
                while True:
                    try:
                        release = admission.acquire('same-client-ip')
                    except AdmissionRejected as exc:
                        self.assertEqual('client_rate_limited', exc.code)
                        clock[0] += exc.retry_after
                    else:
                        admitted.append(clock[0])
                        release()
                        break
            self.assertEqual(max(0, requests - 12), admitted[-1])
            self.assertLess(admitted[-1], 120)
            results.append(dict(count=count, protocol_requests=1, compact_requests=(count + 15) // 16,
                visible_card_requests=2 * min(count, 8), total_requests=requests, earliest_last_read_seconds=admitted[-1],
                snapshot_maximum_seconds=120, zero_latency_ideal_clock_only=True))
        print('NEW_COMPACT_ADMISSION=' + json.dumps(results, sort_keys=True), flush=True)

class ProxyOwnershipCompatibilityTests(unittest.TestCase):
    def test_legacy_verified_ownership_pages_remain_admitted_by_reviewed_proxy(self):
        source=(Path(__file__).resolve().parents[1]/'config/nginx/popl-api-locations.conf').read_text(encoding='utf-8')
        pattern=re.search(r'location ~ "([^"\n]+)"',source).group(1)
        for offset in (0,16,992):
            self.assertIsNotNone(re.fullmatch(pattern,f'/v1/wallets/{OWNER}/nfts/99/{offset}'))
        for suffix in ('/nfts/099/0','/nfts/99/000','/nfts/99/1000','/nfts/99/0/4','/nfts/99/0?x=1'):
            self.assertIsNone(re.fullmatch(pattern,f'/v1/wallets/{OWNER}'+suffix))

if __name__ == '__main__':
    unittest.main()

