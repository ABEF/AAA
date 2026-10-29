"""Sold-out mint controls stay distinct from unfinished VRF/reveal work."""
import http.client
import json
import threading
import unittest

from frontend_api.server import ReadServer, handler
from frontend_api.service import Projection
from tests_python import test_frontend_api as api
from tests_python import test_holder_exit_profile as holder
from tests_python import test_mint_readiness as fixtures
from zzz_ops.abi import keccak256


class MintSupplyReadinessTests(unittest.TestCase):
    def service(self, version=4):
        if version == 1:
            cfg, rpc = api.configuration(), api.MockRPC()
        else:
            cfg, rpc = holder.setup_api()
            if version == 3:
                cfg['accounting_version'] = 3
                del cfg['contracts']['principal_exit']
                rpc.put(api.addr(3), 'ACCOUNTING_VERSION()', values=(3,))
                rpc.put(api.addr(7), 'SCHEMA()', values=(
                    '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4').hex(),))
        f = fixtures.MintReadinessTests('runTest')
        f.rpc = rpc
        f.p = Projection(cfg, rpc, clock=lambda: 1000)
        return f

    def test_sold_out_collection_stops_new_mints_while_unfinished_draw_remains_visible(self):
        for version in (1, 3, 4):
            with self.subTest(accounting_version=version):
                f = self.service(version)
                f.inventory(1000, 1000, (0, 0, 1))
                result = f.p.mint_readiness()
                self.assertTrue(result['new_minting_stopped'])
                self.assertTrue(result['new_minting_stopped_by_supply'])
                self.assertEqual(result['remaining_mint_supply'], 0)
                self.assertFalse(result['mint_paused'])
                self.assertFalse(result['new_minting_stopped_by_lifecycle'])
                self.assertEqual(result['schema'], 2)
                self.assertEqual(result['unfinished_draws'], 1)
                self.assertEqual(result['oldest_unfinished']['state'], 'awaiting_randomness')
                self.assertFalse(result['collection_replacement_reveal_condition_met'])
                self.assertFalse(result['provider_liveness_verified'])

    def test_sold_out_fully_revealed_inventory_remains_readable(self):
        f = self.service()
        f.inventory(1000, 1001, (0, 0, 0))
        result = f.p.mint_readiness()
        self.assertTrue(result['new_minting_stopped'])
        self.assertTrue(result['new_minting_stopped_by_supply'])
        self.assertEqual(result['remaining_mint_supply'], 0)
        self.assertEqual(result['unfinished_draws'], 0)
        self.assertIsNone(result['oldest_unfinished'])
        self.assertTrue(result['collection_replacement_reveal_condition_met'])
        self.assertFalse(result['provider_funding_verified'])
        self.assertFalse(result['provider_liveness_verified'])

    def test_supply_boundary_is_exact_and_independent_of_pause_and_lifecycle(self):
        for version in (1, 3, 4):
            for minted in (0, 999, 1000):
                for global_pause, mint_pause in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    with self.subTest(version=version, minted=minted, controls=(global_pause, mint_pause)):
                        f = self.service(version)
                        quotas = (600, 300, 100) if minted == 0 else (0, 0, 1) if minted == 999 else (0, 0, 0)
                        f.inventory(minted, minted + 1, quotas)
                        f.rpc.put(api.addr(1), 'paused()', values=(global_pause,))
                        f.rpc.put(api.addr(2), 'mintPaused()', values=(mint_pause,))
                        result = f.p.mint_readiness()
                        self.assertEqual(result['remaining_mint_supply'], 1000 - minted)
                        self.assertEqual(result['new_minting_stopped_by_supply'], minted == 1000)
                        self.assertEqual(result['new_minting_stopped_by_lifecycle'], bool(global_pause))
                        self.assertEqual(result['mint_paused'], bool(mint_pause))
                        self.assertEqual(result['new_minting_stopped'], bool(global_pause or mint_pause or minted == 1000))
                        self.assertEqual(result['schema'], 2)

    def test_http_serves_sold_out_paused_observation_and_rejects_inconsistent_supply(self):
        f = self.service()
        f.inventory(1000, 1001, (0, 0, 0))
        f.rpc.put(api.addr(1), 'paused()', values=(1,))
        server = ReadServer(('127.0.0.1', 0), handler(f.p))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for malformed in (False, True):
                if malformed:
                    f.rpc.put(api.addr(2), 'mintedCount()', values=(1001,))
                conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=5)
                try:
                    conn.request('GET', '/v1/mint-readiness')
                    response = conn.getresponse()
                    body = json.loads(response.read())
                    self.assertEqual(response.status, 503 if malformed else 200)
                    if malformed:
                        self.assertEqual(body, {'error': 'confirmed_projection_unavailable'})
                    else:
                        self.assertTrue(body['new_minting_stopped_by_supply'])
                        self.assertTrue(body['new_minting_stopped_by_lifecycle'])
                        self.assertTrue(body['collection_replacement_reveal_condition_met'])
                        self.assertEqual(body['schema'], 2)
                finally:
                    conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


if __name__ == '__main__':
    unittest.main()
