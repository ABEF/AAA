"""Canonical API regressions: no stale spendability or truncated lifetime claims."""
import http.client
import threading
import unittest

from frontend_api.server import ReadServer, handler
from frontend_api.service import Projection, ProjectionError, ZERO
from tests_python.test_frontend_api import MockRPC, addr, configuration, words
from zzz_ops.abi import calldata, keccak256


class CanonicalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.p = Projection(configuration(), self.rpc, clock=lambda: 1000)

    def state(self, state, phase, *, imported=False):
        self.rpc.put(addr(1), 'canonicalState()', values=(state,))
        self.rpc.put(addr(1), 'preparationActive()', values=(int(state in (1, 3)),))
        self.rpc.put(addr(7), 'phase()', values=(phase,))
        self.rpc.put(addr(7), 'incomingSource()', values=(addr(90) if imported else ZERO,))
        self.rpc.put(addr(7), 'destinationController()', values=(addr(91) if state in (1, 3) else ZERO,))
        self.rpc.put(addr(8), 'originVault()', values=(addr(92) if imported else addr(3),))

    def read(self):
        return self.p.nft(str(self.rpc.nft_id))

    def test_original_nft_exposes_exact_origin_and_operating_permissions(self):
        result = self.read()
        life = result['lifecycle']
        self.assertEqual(result['schema'], 2)
        self.assertEqual(life['origin'], {'chain_id': 31337, 'vault': addr(3)})
        self.assertEqual(life['state'], 'operating')
        self.assertIsNone(life['predecessor_controller'])
        self.assertIsNone(life['successor_controller'])
        self.assertTrue(life['claims_available_by_lifecycle'])
        self.assertTrue(life['new_economic_work_available_by_lifecycle'])

    def test_preparation_and_pause_keep_funded_claims_and_transfers(self):
        for prep, paused in ((1, 0), (0, 1), (1, 1)):
            with self.subTest(preparation=prep, paused=paused):
                self.rpc.put(addr(1), 'preparationActive()', values=(prep,))
                self.rpc.put(addr(1), 'paused()', values=(paused,))
                result = self.read()
                life = result['lifecycle']
                self.assertTrue(life['claims_available_by_lifecycle'])
                self.assertTrue(life['transfers_available_by_lifecycle'])
                self.assertFalse(life['new_economic_work_available_by_lifecycle'])
                self.assertGreater(int(result['claimable']['royalties'][0]['raw']), 0)

    def test_every_locked_phase_refuses_positions_before_ownership_or_balance_reads(self):
        for state, phase in ((1, 1), (1, 6), (1, 8), (2, 2), (2, 4), (3, 3), (4, 7)):
            with self.subTest(state=state, phase=phase):
                self.state(state, phase, imported=state in (2, 4))
                self.rpc.calls.clear()
                with self.assertRaisesRegex(ProjectionError, 'locked'):
                    self.read()
                forbidden = (calldata('mintOrdinalOf(uint256)', self.rpc.nft_id)[:10],
                             calldata('claimable(uint256,address)', self.rpc.nft_id, addr(20))[:10],
                             calldata('assetCount()'))
                self.assertFalse(any(m == 'eth_call' and args[0]['data'][:10] in forbidden
                                     for m, args in self.rpc.calls))

    def test_wallet_locked_before_history_replay(self):
        self.state(3, 3)
        self.p.history = object()  # Would fail if reached instead of the lifecycle guard.
        with self.assertRaisesRegex(ProjectionError, 'locked'):
            self.p.wallet(addr(30))

    def test_protocol_remains_readable_for_every_locked_phase_without_balances(self):
        for state, phase in ((1, 1), (1, 6), (1, 8), (2, 2), (2, 4), (3, 3), (4, 7)):
            with self.subTest(state=state, phase=phase):
                self.state(state, phase, imported=state in (2, 4))
                result = self.p.protocol()
                self.assertFalse(result['lifecycle']['claims_available_by_lifecycle'])
                self.assertNotIn('claimable', result)
                self.assertFalse(result['provenance']['protocol_finalized'])
                self.assertEqual(result['lifecycle']['successor_controller'], addr(91) if state == 3 else None)
                self.assertFalse(result['lifecycle']['peer_deployments_verified'])
                self.assertEqual(result['lifecycle']['origin_available'], state not in (2, 4))
                if state in (2, 4):
                    self.assertIsNone(result['lifecycle']['origin'])

    def test_retired_protocol_status_does_not_depend_on_moved_funds_or_prices(self):
        self.state(3, 3)
        for key in list(self.rpc.responses):
            if (key[0] in (addr(20), addr(21)) or key[1][:10] in
                    (calldata('claimable(uint256,address)', self.rpc.nft_id, addr(20))[:10],
                     calldata('assetCount()'), calldata('assets(uint256)', 0)[:10],
                     calldata('currentLPValue(uint256)', self.rpc.nft_id)[:10])):
                del self.rpc.responses[key]
        self.assertEqual(self.p.protocol()['lifecycle']['state'], 'retired')

    def test_restored_abort_never_advertises_stale_destination_as_successor(self):
        self.rpc.put(addr(7), 'destinationController()', values=(addr(91),))
        life = self.p.protocol()['lifecycle']
        self.assertIsNone(life['successor_controller'])
        self.assertIsNone(life['handoff_destination_controller'])
        self.assertTrue(life['claims_available_by_lifecycle'])

    def test_imported_successor_serves_funded_balances_but_not_partial_lifetime_claims(self):
        self.state(0, 5, imported=True)
        # Existing history can cover current ownership, but cannot be relabelled
        # as lifetime claims across predecessors, even when nonzero locally.
        class LocalHistory:
            owners = {self.rpc.nft_id: addr(30)}
        self.p._history_snapshot = lambda *args: LocalHistory()
        self.p._claimed = lambda *args: self.fail('Incomplete history was offered as lifetime claims')
        result = self.read()
        self.assertEqual(result['lifecycle']['predecessor_controller'], addr(90))
        self.assertEqual(result['lifecycle']['origin']['vault'], addr(92))
        self.assertFalse(result['previously_claimed']['available'])
        self.assertIsNone(result['previously_claimed']['assets'])
        self.assertIn('predecessor', result['previously_claimed']['reason'])
        self.assertIn('previously_claimed', result['unavailable_metrics'])
        self.assertGreater(int(result['claimable']['lp'][0]['raw']), 0)

    def test_missing_or_malformed_lifecycle_getters_fail_closed(self):
        for target, signature in ((1, 'canonicalState()'), (1, 'preparationActive()'),
                                  (1, 'paused()'), (1, 'canonicalSettling()'),
                                  (7, 'phase()'), (7, 'incomingSource()'),
                                  (7, 'destinationController()'), (8, 'originChain()'), (8, 'originVault()')):
            for value in ('0x', words(0, 0), '0xzz'):
                with self.subTest(signature=signature, value=value):
                    rpc = MockRPC()
                    rpc.responses[(addr(target), calldata(signature))] = value
                    with self.assertRaises(ProjectionError):
                        Projection(configuration(), rpc, clock=lambda: 1000).protocol()

    def test_unknown_states_phases_and_noncanonical_booleans_fail_closed(self):
        for target, sig, value in ((1, 'canonicalState()', 5), (7, 'phase()', 9), (7, 'phase()', 3),
                                   (1, 'preparationActive()', 2), (1, 'paused()', 2),
                                   (1, 'canonicalSettling()', 1), (1, 'canonicalSettling()', 2)):
            with self.subTest(signature=sig, value=value):
                rpc = MockRPC(); rpc.put(addr(target), sig, values=(value,))
                with self.assertRaises(ProjectionError):
                    Projection(configuration(), rpc, clock=lambda: 1000).protocol()

    def test_inconsistent_origins_and_peer_addresses_fail_closed(self):
        for target, sig, value in ((7, 'incomingSource()', addr(1)),
                                   (7, 'incomingSource()', addr(90)),
                                   (7, 'destinationController()', addr(1)),
                                   (8, 'originChain()', 0), (8, 'originChain()', 4663),
                                   (8, 'originVault()', ZERO), (8, 'originVault()', addr(92))):
            with self.subTest(signature=sig, value=value):
                rpc = MockRPC(); rpc.put(addr(target), sig, values=(value,))
                with self.assertRaises(ProjectionError):
                    Projection(configuration(), rpc, clock=lambda: 1000).protocol()

    def test_missing_required_source_or_destination_is_rejected(self):
        for state, phase, signature in ((2, 4, 'incomingSource()'), (0, 5, 'incomingSource()'),
                                        (3, 3, 'destinationController()'), (1, 8, 'destinationController()')):
            with self.subTest(state=state):
                self.state(state, phase, imported=state in (0, 2))
                self.rpc.put(addr(7), signature, values=(ZERO,))
                with self.assertRaises(ProjectionError):
                    self.p.protocol()

    def test_wrong_code_and_helper_owner_binding_fail_closed(self):
        for target, signature in ((7, 'access()'), (8, 'access()'), (8, 'vault()'),
                                  (1, 'canonicalHandoff()'), (3, 'canonicalModule()')):
            with self.subTest(target=target, signature=signature):
                rpc = MockRPC(); rpc.put(addr(target), signature, values=(addr(99),))
                with self.assertRaises(ProjectionError):
                    Projection(configuration(), rpc, clock=lambda: 1000).protocol()
        for target in (7, 8):
            rpc = MockRPC(); rpc.codes[addr(target)] = '0x6000'
            with self.assertRaises(ProjectionError):
                Projection(configuration(), rpc, clock=lambda: 1000).protocol()

    def test_wrong_sealed_canonical_module_registration_fails_closed(self):
        for label in ('ZZZCanonicalHandoff', 'ZZZVaultCanonical'):
            rpc = MockRPC()
            rpc.put(addr(1), 'module(bytes32)', ('0x' + keccak256(label.encode()).hex(),), (addr(99),))
            with self.assertRaises(ProjectionError):
                Projection(configuration(), rpc, clock=lambda: 1000).protocol()

    def test_legacy_config_and_missing_new_runtime_pins_are_rejected(self):
        for mutation in ('schema', 'handoff', 'vault_canonical'):
            config = configuration()
            if mutation == 'schema': config['schema'] = 1
            else: del config['contracts'][mutation]
            with self.assertRaises(ValueError): Projection(config, self.rpc)

    def test_status_and_nft_all_reads_share_the_confirmed_hash(self):
        self.p.protocol(); self.read()
        for method, args in self.rpc.calls:
            if method in ('eth_call', 'eth_getCode'):
                self.assertEqual(args[-1], {'blockHash': self.rpc.hash, 'requireCanonical': True})
        self.assertFalse(any(method.startswith(('eth_send', 'personal_', 'wallet_')) for method, _ in self.rpc.calls))

    def test_status_reorg_or_lost_depth_is_not_published(self):
        self.rpc.reorg_after_calls = True
        with self.assertRaises(ProjectionError): self.p.protocol()
        self.rpc = MockRPC(); original = self.rpc.call
        def failover(method, args):
            result = original(method, args)
            if method == 'eth_call' and args[0]['data'] == calldata('originVault()'):
                self.rpc.head = 99
            return result
        self.rpc.call = failover
        with self.assertRaises(ProjectionError):
            Projection(configuration(), self.rpc, clock=lambda: 1000).protocol()


class CanonicalHistoryTests(unittest.TestCase):
    def setUp(self):
        # Use the existing real sqlite/indexer fixture, without inheriting and
        # double-counting its other regression methods.
        from tests_python.test_frontend_history import ConfirmedHistoryTests
        self.fixture = ConfirmedHistoryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.p = self.fixture.projection()
        self.rpc = self.fixture.rpc

    def test_real_replayed_claims_are_never_relabelled_as_successor_lifetime_totals(self):
        before = self.p.nft(str(self.rpc.nft_id))
        self.assertTrue(before['previously_claimed']['available'])
        self.assertTrue(any(int(x['total_raw']) > 0 for x in before['previously_claimed']['assets']))
        self.rpc.put(addr(7), 'phase()', values=(5,))
        self.rpc.put(addr(7), 'incomingSource()', values=(addr(90),))
        self.rpc.put(addr(8), 'originVault()', values=(addr(92),))
        after = self.p.nft(str(self.rpc.nft_id))
        self.assertEqual(before['claimable'], after['claimable'])
        self.assertFalse(after['previously_claimed']['available'])
        self.assertIsNone(after['previously_claimed']['assets'])
        wallet = self.p.wallet(addr(30))
        self.assertEqual(wallet['token_ids'], [str(self.rpc.nft_id)])
        self.assertEqual(wallet['lifecycle']['predecessor_controller'], addr(90))

    def test_locked_wallet_does_not_return_stale_indexed_ownership(self):
        self.rpc.put(addr(1), 'canonicalState()', values=(1,))
        self.rpc.put(addr(1), 'preparationActive()', values=(1,))
        self.rpc.put(addr(7), 'phase()', values=(8,))
        self.rpc.put(addr(7), 'destinationController()', values=(addr(91),))
        with self.assertRaisesRegex(ProjectionError, 'locked'):
            self.p.wallet(addr(30))


class CanonicalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.p = Projection(configuration(), self.rpc, clock=lambda: 1000)
        self.server = ReadServer(('127.0.0.1', 0), handler(self.p))
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01})
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()

    def request(self, path):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_address[1], timeout=3)
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            return response.status, response.getheader('Cache-Control'), response.read()
        finally: connection.close()

    def test_retired_status_is_readable_but_positions_are_unavailable(self):
        self.rpc.put(addr(1), 'canonicalState()', values=(3,))
        self.rpc.put(addr(1), 'preparationActive()', values=(1,))
        self.rpc.put(addr(7), 'phase()', values=(3,))
        self.rpc.put(addr(7), 'destinationController()', values=(addr(91),))
        status, cache, body = self.request('/v1/protocol')
        self.assertEqual((status, cache), (200, 'no-store'))
        self.assertIn(b'"state":"retired"', body)
        status, _, body = self.request('/v1/nfts/' + str(self.rpc.nft_id))
        self.assertEqual(status, 503)
        self.assertNotIn(b'claimable', body)

    def test_missing_getter_is_sanitized_not_fallback_to_operating(self):
        del self.rpc.responses[(addr(1), calldata('canonicalState()'))]
        status, _, body = self.request('/v1/protocol')
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"confirmed_projection_unavailable"}\n')

    def test_status_rejects_query_or_trailing_path(self):
        for path in ('/v1/protocol?state=operating', '/v1/protocol/', '/v1/protocol/retired'):
            self.assertEqual(self.request(path)[0], 404)


if __name__ == '__main__':
    unittest.main()
