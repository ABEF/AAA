"""Confirmed reveal-drain observations, not provider or handoff approval."""
import http.client
import json
import threading
import unittest

from frontend_api.service import Projection, ProjectionError
from frontend_api.server import ReadServer, handler
from tests_python.test_frontend_api import MockRPC, configuration, addr
from zzz_ops.errors import RpcError


class MintReadinessTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.p = Projection(configuration(), self.rpc, clock=lambda: 1000)
        self.inventory(2, 2, (599, 300, 100))

    def inventory(self, minted, next_ordinal, quotas):
        for sig, value in [('mintedCount()', minted), ('nextToFinalize()', next_ordinal),
                           ('remainingToReveal()', sum(quotas)), ('randomnessConfigured()', 1),
                           ('randomnessCoordinator()', addr(40))]:
            self.rpc.put(addr(2), sig, values=(value,))
        for i, count in enumerate(quotas):
            self.rpc.put(addr(2), 'rarityRemaining(uint256)', (i,), (count,))
        token = self.rpc.nft_id
        self.rpc.put(addr(2), 'tokenAtOrdinal(uint256)', (next_ordinal,), (token,))
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (token,), (next_ordinal,))
        self.rpc.put(addr(2), 'traitsReady(uint256)', (token,), (0,))
        self.rpc.put(addr(2), 'requestOf(uint256)', (token,), (70,))
        self.rpc.put(addr(2), 'requestEpochOf(uint256)', (token,), (1,))
        self.rpc.put(addr(2), 'canonicalRandomness(uint256)', (token,), (token, 0, 0, 1, 0))

    def test_pending_request_is_not_reveal_or_provider_approval(self):
        r = self.p.mint_readiness()
        self.assertEqual((r['minted'], r['revealed'], r['unfinished_draws']), (2, 1, 1))
        self.assertEqual(r['oldest_unfinished']['state'], 'awaiting_randomness')
        self.assertEqual(r['oldest_unfinished']['token_id'], str(self.rpc.nft_id))
        for key in ('collection_replacement_reveal_condition_met', 'other_handoff_requirements_verified',
                    'provider_funding_verified', 'provider_liveness_verified'):
            self.assertFalse(r[key])
        self.assertIsNone(r['pending_since'])
        self.assertIn('not ordinary LP pool migration', r['scope'])
        self.assertTrue(all(m in ('eth_call', 'eth_getCode', 'eth_chainId', 'eth_blockNumber',
                                 'eth_getBlockByNumber') for m, _ in self.rpc.calls))

    def test_fulfilled_request_still_requires_ordered_finalization(self):
        token = self.rpc.nft_id
        self.rpc.put(addr(2), 'canonicalRandomness(uint256)', (token,), (token, 44, 55, 1, 1))
        self.assertEqual(self.p.mint_readiness()['oldest_unfinished']['state'], 'awaiting_finalization')

    def test_empty_and_fully_revealed_inventory_only_satisfy_reveal_condition(self):
        for minted, next_ordinal, quotas in ((0, 1, (600, 300, 100)), (1000, 1001, (0, 0, 0))):
            with self.subTest(minted=minted):
                self.inventory(minted, next_ordinal, quotas)
                r = self.p.mint_readiness()
                self.assertTrue(r['collection_replacement_reveal_condition_met'])
                self.assertFalse(r['other_handoff_requirements_verified'])
                self.assertIsNone(r['oldest_unfinished'])

    def test_preparation_stops_new_work_but_keeps_pending_status_visible(self):
        self.rpc.put(addr(1), 'preparationActive()', values=(1,))
        r = self.p.mint_readiness()
        self.assertTrue(r['new_minting_stopped_by_lifecycle'])
        self.assertEqual(r['unfinished_draws'], 1)

    def test_bad_inventory_and_provenance_fail_closed(self):
        cases = [('mintedCount()', (), (1001,)), ('nextToFinalize()', (), (0,)),
                 ('remainingToReveal()', (), (998,)), ('rarityRemaining(uint256)', (0,), (600,)),
                 ('randomnessConfigured()', (), (0,)),
                 ('mintOrdinalOf(uint256)', (self.rpc.nft_id,), (3,)),
                 ('traitsReady(uint256)', (self.rpc.nft_id,), (1,)),
                 ('requestOf(uint256)', (self.rpc.nft_id,), (0,)),
                 ('canonicalRandomness(uint256)', (self.rpc.nft_id,), (5, 0, 0, 1, 0))]
        for sig, args, vals in cases:
            with self.subTest(signature=sig):
                self.inventory(2, 2, (599, 300, 100))
                self.rpc.put(addr(2), sig, args, vals)
                with self.assertRaises(ProjectionError):
                    self.p.mint_readiness()

    def test_hash_reorg_or_unsupported_pinning_never_returns_readiness(self):
        self.rpc.fail_hash_pin = True
        with self.assertRaises(RpcError):
            self.p.mint_readiness()
        self.rpc.fail_hash_pin = False
        self.rpc.reorg_after_calls = True
        with self.assertRaises(ProjectionError):
            self.p.mint_readiness()

    def test_readiness_http_route_returns_observation_or_sanitized_failure(self):
        server = ReadServer(('127.0.0.1', 0), handler(self.p))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for fail in (False, True):
                self.rpc.fail_hash_pin = fail
                conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=5)
                try:
                    conn.request('GET', '/v1/mint-readiness')
                    response = conn.getresponse()
                    payload = json.loads(response.read())
                    self.assertEqual(response.status, 503 if fail else 200)
                    if fail:
                        self.assertEqual(payload, {'error': 'confirmed_projection_unavailable'})
                    else:
                        self.assertEqual(payload['unfinished_draws'], 1)
                finally:
                    conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)
