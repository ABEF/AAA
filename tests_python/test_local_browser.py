"""Independent browser receipt observation, with no holder-side server signing."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.local_browser import LocalBrowser, TRANSFER, ZERO, MAX_RECORDS
from tests_python.test_local_stack import lab as launcher

A, B, ADMIN = ['0x' + x * 40 for x in ('1', '2', '3')]
VAULT, NFT, ENTRY, ROUTER, TOKEN = ['0x' + x * 40 for x in ('4', '5', '6', '7', '8')]
HASH, BLOCK, GENESIS = ['0x' + x * 64 for x in ('a', 'b', 'c')]
KEY = 'd' * 32


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lab = SimpleNamespace(
            home=Path(self.tmp.name), genesis=GENESIS, accounts=[ADMIN, A, B],
            contracts={'vault': VAULT, 'nft': NFT, 'entry': ENTRY, 'claim_router': ROUTER},
            pool='0x' + '9' * 64, tokens=[TOKEN], native_input=True,
            rpc_url='http://127.0.0.1:54321', receipts=[], uncertain=False,
            input_assets=[{'symbol': 'ZZZ', 'address': TOKEN, 'decimals': 18,
                           'route_id': '0x' + '0' * 64, 'enabled': True},
                          {'symbol': 'ETH', 'address': ZERO, 'decimals': 18,
                           'route_id': '0x' + '0' * 64, 'enabled': True}],
            guard=Mock(), sync=Mock(), call=Mock(), uint=Mock(), read=Mock(), clock=Mock(return_value=2000000000),
        )
        self.lab.operations = launcher.OperationLedger(self.lab.home / 'operations.json')
        self.tx = {'from': A, 'to': VAULT, 'data': '0x12345678',
                   'value': '0xb1a2bc2ec50000', 'nonce': '0x0', 'gas': '0x30d40', 'gasPrice': '0x64'}
        self.draft = {'draft_id': KEY, 'account': A, 'action': 'mint', 'requested_action': 'mint',
                      'transaction': self.tx, 'network_gas': {'estimate': '100000'}, 'revision': 0,
                      'chain_id': 31337, 'expires_in_seconds': 60}
        self.lab.wallet = SimpleNamespace(drafts={}, prepare=Mock(side_effect=self.prepare_fixture))
        self.transaction = {**self.tx, 'input': self.tx['data'], 'hash': HASH, 'chainId': '0x7a69',
                            'blockNumber': '0x10', 'blockHash': BLOCK, 'transactionIndex': '0x0'}
        self.receipt = {'transactionHash': HASH, 'from': A, 'to': VAULT, 'blockNumber': '0x10',
                        'blockHash': BLOCK, 'status': '0x1', 'gasUsed': '0x186a0', 'effectiveGasPrice': '0x64', 'transactionIndex': '0x0',
                        'logs': [{'address': NFT, 'topics': [TRANSFER, '0x' + '0' * 64,
                                  '0x' + '0' * 24 + A[2:], '0x' + f'{11:064x}']}]}
        self.lab.rpc = Mock(side_effect=self.rpc)
        self.lab.block = Mock(return_value={'number': '0x10', 'hash': BLOCK})
        self.lab.uint.side_effect = self.uint
        self.lab.read.return_value = [f'{11:064x}', '0', '0', '1', '0']
        self.browser = LocalBrowser(self.lab, launcher.save)

    def prepare_fixture(self, payload):
        draft = copy.deepcopy(self.draft)
        self.lab.wallet.drafts[KEY] = {'public': draft}
        return draft

    def rpc(self, method, args):
        if method == 'eth_getTransactionByHash':
            return self.transaction
        if method == 'eth_getTransactionReceipt':
            return self.receipt
        if method == 'eth_getBlockByNumber':
            return {'hash': BLOCK, 'number': '0x10'}
        if method == 'eth_getCode':
            return '0x60006000'
        raise AssertionError('Unexpected RPC: ' + method)

    def uint(self, role, signature, *args):
        if signature in ('mintOrdinalOf(uint256)', 'nextToFinalize()'):
            return 1
        if signature == 'tokenAtOrdinal(uint256)':
            return 11
        if signature == 'traitsReady(uint256)':
            return 0
        if signature == 'requestOf(uint256)':
            return 100
        raise AssertionError(signature)

    def prepare(self):
        return self.browser.prepare({'action': 'mint', 'account': A})

    def confirm(self):
        return self.browser.confirm({'draft_id': KEY, 'account': A, 'transaction_hash': HASH})

    def test_manifest_pins_only_fixture_targets_and_contains_no_key(self):
        result = self.browser.manifest()
        self.assertEqual(result['policy']['chainId'], '0x7a69')
        self.assertEqual(result['policy']['genesisHash'], GENESIS)
        self.assertEqual(set(result['policy']['allowedTargets']), {VAULT, NFT, ENTRY, ROUTER, TOKEN})
        self.assertNotIn(ZERO, result['policy']['allowedTargets'])
        self.assertEqual(result['contracts']['claim_router']['address'], ROUTER)
        self.assertEqual(result['input_assets'][1]['symbol'], 'ETH')
        self.assertEqual(result['policy']['confirmations'], 1)
        self.assertNotIn('private', json.dumps(result).lower())
        self.assertFalse(self.browser.path.exists())
        self.lab.call.assert_not_called()

    def test_manifest_rejects_missing_and_oversized_code(self):
        for code in ('0x', '0x01' * 24577, 'bad', None):
            with self.subTest(code=str(code)[:20]):
                self.lab.rpc.side_effect = None
                self.lab.rpc.return_value = code
                with self.assertRaises(ValueError):
                    self.browser.manifest()

    def test_prepare_has_exact_unsigned_transaction_but_no_local_signer_draft(self):
        draft = self.prepare()
        self.assertEqual(draft['transaction']['chainId'], '0x7a69')
        self.assertEqual(draft['requested'], {'action': 'mint', 'account': A})
        self.assertEqual(draft['expires_at'] - draft['prepared_at'], 60)
        self.assertEqual(self.lab.wallet.drafts, {})
        self.assertTrue(self.browser.path.exists())
        self.lab.call.assert_not_called()

    def test_unrelated_operator_and_transfer_actions_cannot_enter_browser_path(self):
        for payload in (None, [], {}, {'action': 'fund'}, {'action': 'rebalance'}, {'action': 'execute'}, {'action': 'transfer'}):
            with self.assertRaises(ValueError):
                self.browser.prepare(payload)
        self.lab.wallet.prepare.assert_not_called()

    def test_unbounded_or_injected_transaction_fields_never_return_draft(self):
        for tx in ({**self.tx, 'gas': hex(30_000_001)}, {**self.tx, 'gasPrice': hex(100 * 10**9 + 1)},
                   {**self.tx, 'value': hex(100_000 * 10**18)}, {**self.tx, 'gas': '0x00'},
                   {**self.tx, 'accessList': []}, {**self.tx, 'to': ZERO, 'data': '0x'}):
            self.draft['transaction'] = tx
            with self.assertRaises(ValueError):
                self.prepare()
            self.assertEqual(self.lab.wallet.drafts, {})
        self.lab.call.assert_not_called()

    def test_journal_capacity_never_evicts_possibly_sent_reviews(self):
        self.browser.items = {str(i): {} for i in range(MAX_RECORDS)}
        with self.assertRaisesRegex(ValueError, 'full'):
            self.prepare()
        self.lab.wallet.prepare.assert_not_called()

    def test_persistence_failure_does_not_expose_a_draft(self):
        self.browser.save = Mock(side_effect=OSError('disk full'))
        with self.assertRaises(OSError):
            self.prepare()
        self.assertEqual(self.browser.items, {})
        self.assertEqual(self.lab.wallet.drafts, {})
        self.lab.call.assert_not_called()

    def test_pending_transaction_never_creates_outcome_or_operator_transaction(self):
        self.prepare()
        self.receipt = None
        result = self.confirm()
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(self.lab.operations.revision, 0)
        self.lab.call.assert_not_called()
        self.lab.sync.assert_not_called()

    def test_unknown_hash_stays_pending_and_is_not_submitted(self):
        self.prepare()
        self.transaction = None
        self.assertEqual(self.confirm()['status'], 'pending')
        self.lab.call.assert_not_called()
        self.assertNotIn('eth_sendTransaction', [c.args[0] for c in self.lab.rpc.call_args_list])

    def test_confirmed_receipt_advances_once_and_uses_receipt_nft(self):
        self.prepare()
        self.lab.vrf = 'mock-vrf'
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['minted_token_id'], '11')
        self.assertEqual(result['mock_reveal'], 'complete')
        self.assertEqual(self.lab.operations.revision, 1)
        self.lab.call.assert_any_call('mock-vrf', 'fulfill(uint256,uint256,uint256)', 100, 721, 12345)
        self.lab.call.assert_any_call('nft', 'finalizeTraits(uint256)', 11)
        self.assertNotIn('eth_sendTransaction', [c.args[0] for c in self.lab.rpc.call_args_list])
        # Emulate finalized callback state; observation may repeat but cannot
        # repeat any mint/holder transaction or increment the ledger twice.
        self.lab.uint.side_effect = lambda role, sig, *args: 2 if sig == 'nextToFinalize()' else self.uint(role, sig, *args)
        self.lab.call.reset_mock()
        self.assertTrue(self.confirm()['replayed'])
        self.lab.call.assert_not_called()
        self.assertEqual(self.lab.operations.revision, 1)
        self.assertEqual(len(self.lab.receipts), 1)

    def test_confirmation_after_review_expiry_is_still_receipt_observation(self):
        self.prepare()
        self.browser.items[KEY]['draft']['expires_at'] = 1
        self.assertEqual(self.confirm()['status'], 'confirmed')

    def test_reverted_holder_transaction_is_recorded_without_mock_reveal(self):
        self.prepare()
        self.receipt['status'] = '0x0'
        result = self.confirm()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(self.lab.operations.revision, 1)
        self.lab.call.assert_not_called()

    def test_bad_owner_value_nonce_calldata_target_chain_and_fees_fail_closed(self):
        self.prepare()
        original = self.transaction.copy()
        for field, value in [('from', B), ('to', ENTRY), ('value', '0x0'), ('nonce', '0x1'),
                             ('input', '0x87654321'), ('chainId', '0x1'), ('gas', hex(30_000_001)),
                             ('gasPrice', '0x65'), ('gasPrice', hex(100 * 10**9 + 1)),
                             ('hash', '0x' + 'e' * 64)]:
            self.transaction = {**original, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.confirm()
            self.assertEqual(self.lab.operations.revision, 0)
            self.lab.call.assert_not_called()

    def test_wallet_gas_padding_preserves_review_and_accepts_only_paid_gas_within_it(self):
        self.draft['action'] = 'approve'
        self.draft['transaction'] = {**self.tx, 'gas': '0xdfa9', 'gasPrice': '0x3b9aca07'}
        draft = self.prepare()
        original_review = copy.deepcopy(draft['transaction'])
        self.transaction.update(gas='0x11793', gasPrice='0x3b9aca07')
        self.receipt.update(gasUsed='0xba62', effectiveGasPrice='0x3b9aca07')
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(self.browser.items[KEY]['draft']['transaction'], original_review)
        self.assertEqual(self.lab.operations.revision, 1)
        self.lab.call.assert_not_called()

    def test_padded_limit_never_allows_paid_gas_above_original_review(self):
        self.prepare()
        self.transaction['gas'] = '0x61a80'
        self.receipt['gasUsed'] = '0x30d41'
        with self.assertRaisesRegex(ValueError, 'reviewed network fee'):
            self.confirm()
        self.assertEqual(self.lab.operations.items, {})

    def test_smaller_submitted_gas_and_price_are_the_tighter_paid_ceiling(self):
        self.prepare()
        self.transaction.update(gas='0x1869f')
        with self.assertRaisesRegex(ValueError, 'reviewed network fee'):
            self.confirm()
        self.transaction.update(gas='0x30d40', gasPrice='0x63')
        with self.assertRaisesRegex(ValueError, 'reviewed network fee'):
            self.confirm()
        self.assertEqual(self.lab.operations.items, {})

    def test_padding_cannot_exceed_hard_total_cost_even_with_valid_gas_and_price(self):
        self.draft['transaction'] = {**self.tx, 'gasPrice': hex(100 * 10**9)}
        self.prepare()
        self.transaction.update(gas=hex(30_000_000), gasPrice=hex(100 * 10**9))
        with self.assertRaisesRegex(ValueError, 'hard local gas policy'):
            self.confirm()
        self.lab.call.assert_not_called()

    def test_wrong_receipt_identity_or_failed_canonical_inclusion_never_confirms(self):
        self.prepare()
        original = self.receipt.copy()
        for field, value in [('from', B), ('to', ENTRY), ('transactionHash', '0x' + 'e' * 64),
                             ('blockHash', '0x' + 'e' * 64), ('blockNumber', '0x11'),
                             ('status', None), ('gasUsed', '0x30d41'), ('effectiveGasPrice', '0x65')]:
            self.receipt = {**original, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.confirm()
        self.receipt = original
        self.lab.block.return_value = {'number': '0xf', 'hash': BLOCK}
        with self.assertRaisesRegex(ValueError, 'canonical'):
            self.confirm()
        self.assertEqual(self.lab.operations.items, {})
        self.lab.call.assert_not_called()

    def test_replayed_receipt_is_rechecked_after_a_reorg(self):
        self.prepare()
        self.confirm()
        self.lab.rpc.side_effect = lambda method, args: {'hash': '0x' + 'f' * 64} if method == 'eth_getBlockByNumber' else self.rpc(method, args)
        with self.assertRaisesRegex(ValueError, 'canonical'):
            self.confirm()
        self.assertEqual(self.lab.operations.revision, 1)

    def test_inconsistent_transaction_index_and_header_number_fail_closed(self):
        self.prepare()
        self.receipt['transactionIndex'] = '0x1'
        with self.assertRaisesRegex(ValueError, 'transaction index'):
            self.confirm()
        self.receipt['transactionIndex'] = '0x0'
        self.lab.rpc.side_effect = lambda method, args: {'number': '0x11', 'hash': BLOCK} if method == 'eth_getBlockByNumber' else self.rpc(method, args)
        with self.assertRaisesRegex(ValueError, 'canonical'):
            self.confirm()
        self.assertEqual(self.lab.operations.items, {})
        self.lab.call.assert_not_called()

    def test_reincluded_transaction_never_reuses_old_confirmed_outcome(self):
        self.prepare()
        self.confirm()
        original = copy.deepcopy(self.browser.items[KEY]['receipt'])
        self.receipt = {**self.receipt, 'blockNumber': '0x11', 'blockHash': '0x' + 'f' * 64, 'status': '0x0'}
        self.transaction = {**self.transaction, 'blockNumber': '0x11', 'blockHash': '0x' + 'f' * 64}
        self.lab.block.return_value = {'number': '0x11', 'hash': '0x' + 'f' * 64}
        self.lab.rpc.side_effect = lambda method, args: {'number': '0x11', 'hash': '0x' + 'f' * 64} if method == 'eth_getBlockByNumber' else self.rpc(method, args)
        with self.assertRaisesRegex(ValueError, 'Previously observed receipt changed'):
            self.confirm()
        self.assertEqual(self.browser.items[KEY]['receipt'], original)
        self.assertEqual(self.lab.operations.revision, 1)

    def test_confirm_shape_and_wrong_account_do_not_read_or_mutate(self):
        self.prepare()
        self.lab.rpc.reset_mock()
        base = {'draft_id': KEY, 'account': A, 'transaction_hash': HASH}
        for payload in (None, {}, {**base, 'account': B}, {**base, 'draft_id': 'f' * 32},
                        {**base, 'transaction_hash': '0x123'}, {**base, 'data': '0x'}):
            with self.assertRaises(ValueError):
                self.browser.confirm(payload)
        self.lab.rpc.assert_not_called()

    def test_saved_hash_cannot_be_changed_or_credited_to_another_review(self):
        self.prepare()
        self.browser.items[KEY]['hash'] = '0x' + 'e' * 64
        with self.assertRaisesRegex(ValueError, 'another transaction'):
            self.confirm()
        self.browser.items[KEY]['hash'] = None
        self.browser.items['f' * 32] = {'hash': HASH}
        with self.assertRaisesRegex(ValueError, 'another review'):
            self.confirm()

    def test_existing_operation_identifier_collision_rejected(self):
        self.prepare()
        self.lab.operations.items[KEY] = {'fingerprint': 'legacy signer', 'outcome': {}}
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            self.confirm()
        self.lab.call.assert_not_called()

    def test_reload_keeps_review_and_confirmed_evidence_without_resubmission(self):
        self.prepare()
        self.confirm()
        reloaded = LocalBrowser(self.lab, launcher.save)
        self.assertEqual(reloaded.items[KEY]['hash'], HASH)
        outcome = reloaded.confirm({'draft_id': KEY, 'account': A, 'transaction_hash': HASH})
        self.assertEqual(outcome['status'], 'confirmed')
        self.assertEqual(self.lab.operations.revision, 1)

    def test_foreign_and_malformed_journal_fail_closed(self):
        self.prepare()
        original = json.loads(self.browser.path.read_text())
        for document in ({**original, 'genesis': '0x' + 'e' * 64}, {**original, 'items': []},
                         {'schema': 99}, {**original, 'items': {'bad': {}}}):
            self.browser.path.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                LocalBrowser(self.lab, launcher.save)

    def test_projection_outage_does_not_turn_success_into_another_mint(self):
        self.prepare()
        self.lab.sync.side_effect = RuntimeError('indexer outage')
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['projection_sync'], 'retry_read')
        self.assertEqual(self.lab.operations.revision, 1)

    def test_mock_reveal_outage_keeps_success_and_requests_operator_attention(self):
        self.prepare()
        self.lab.vrf = 'mock-vrf'
        self.lab.call.side_effect = RuntimeError('operator paused')
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['mock_reveal'], 'pending_operator')
        self.assertEqual(self.lab.operations.revision, 1)

    def test_confirmed_mint_with_duplicate_mint_logs_does_not_pick_last_token(self):
        self.prepare()
        self.receipt['logs'] *= 2
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['mock_reveal'], 'pending_operator')
        self.lab.call.assert_not_called()

    def test_original_callback_completed_before_failure_is_not_repeated(self):
        self.prepare()
        self.lab.vrf = 'mock-vrf'
        self.lab.read.return_value = [f'{11:064x}', '1', '1', '1', '1']
        self.confirm()
        self.lab.call.assert_called_once_with('nft', 'finalizeTraits(uint256)', 11)

    def test_different_wallet_receipt_can_be_observed_after_other_revision(self):
        self.prepare()
        self.lab.operations.revision = 9
        result = self.confirm()
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['revision'], 10)


class BrowserHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lab = SimpleNamespace(home=Path(self.tmp.name), args=SimpleNamespace(website=None, port=0),
                                   accounts=[ADMIN, A, B], token='test-only-session', lock=threading.RLock(),
                                   browser=SimpleNamespace(manifest=Mock(return_value={'mode': 'LOCAL ANVIL TEST ONLY'}),
                                                           prepare=Mock(return_value={'origin': 'browser'}),
                                                           confirm=Mock(return_value={'status': 'pending'})),
                                   wallet=SimpleNamespace(prepare=Mock()), operations=SimpleNamespace(run=Mock()))
        self.server = launcher.make_server(self.lab)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, path, payload=None, headers=None, method='POST'):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        base = {'Origin': f'http://127.0.0.1:{self.port}', 'X-Local-Token': self.lab.token,
                'Content-Type': 'application/json'}
        if headers:
            base.update(headers)
        body = payload if isinstance(payload, bytes) else (json.dumps(payload) if payload is not None else None)
        connection.request(method, path, body, base)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_manifest_is_read_only_and_never_calls_holder_signer(self):
        status, result = self.request('/browser/manifest', method='GET')
        self.assertEqual(status, 200)
        self.assertEqual(result['mode'], 'LOCAL ANVIL TEST ONLY')
        self.lab.browser.manifest.assert_called_once_with()
        self.lab.operations.run.assert_not_called()
        self.lab.wallet.prepare.assert_not_called()

    def test_browser_prepare_and_observe_are_separate_from_legacy_action(self):
        payload = {'action': 'mint', 'account': A}
        self.assertEqual(self.request('/browser/prepare', payload)[0], 200)
        self.lab.browser.prepare.assert_called_once_with(payload)
        confirm = {'draft_id': KEY, 'account': A, 'transaction_hash': HASH}
        self.assertEqual(self.request('/browser/confirm', confirm)[1]['status'], 'pending')
        self.lab.browser.confirm.assert_called_once_with(confirm)
        self.lab.operations.run.assert_not_called()
        self.lab.wallet.prepare.assert_not_called()

    def test_bad_origin_session_and_host_never_reach_observer(self):
        payload = {'draft_id': KEY, 'account': A, 'transaction_hash': HASH}
        for headers in ({'Origin': 'https://external.test'}, {'X-Local-Token': 'wrong'},
                        {'Host': 'localhost:' + str(self.port)}):
            self.assertEqual(self.request('/browser/confirm', payload, headers)[0], 403)
        self.lab.browser.confirm.assert_not_called()

    def test_malformed_duplicate_and_oversized_bodies_never_prepare(self):
        for raw in (b'{"action":"mint","action":"activate"}', b'{"v":NaN}', b'x' * 2049):
            self.assertEqual(self.request('/browser/prepare', raw)[0], 400)
        self.lab.browser.prepare.assert_not_called()

    def test_busy_observer_returns_pre_handler_busy_without_signing(self):
        with self.lab.lock:
            status, result = self.request('/browser/confirm', {})
        self.assertEqual(status, 409)
        self.assertEqual(result['error'], 'Local operation in progress; refresh shortly')
        self.lab.browser.confirm.assert_not_called()
        self.lab.operations.run.assert_not_called()

    def test_unknown_browser_routes_never_fall_through_to_legacy_actions(self):
        self.assertEqual(self.request('/browser/send', {'action': 'mint', 'account': A})[0], 404)
        self.lab.operations.run.assert_not_called()
        self.lab.wallet.prepare.assert_not_called()


class BrowserPageTests(unittest.TestCase):
    def test_exact_browser_mode_query_serves_index_but_other_queries_stay_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'index.html').write_text('<html>browser fixture</html>')
            lab = SimpleNamespace(home=root, args=SimpleNamespace(website=directory, port=0))
            server = launcher.make_server(lab)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for path, expected in [('/app/', 200), ('/app/?wallet=browser', 200),
                                       ('/app/?wallet=other', 404), ('/app/?wallet=browser&rpc=evil', 404),
                                       ('/browser/manifest?rpc=evil', 404)]:
                    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                    connection.request('GET', path)
                    response = connection.getresponse()
                    body = response.read()
                    connection.close()
                    self.assertEqual(response.status, expected, path)
                    if expected == 200:
                        self.assertEqual(body, b'<html>browser fixture</html>')
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == '__main__':
    unittest.main()
