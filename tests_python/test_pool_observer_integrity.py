"""Selected-pool evidence rejects contradictory RPC JSON and actual slot0."""
import io
import json
import unittest
from unittest.mock import patch

from tests_python import test_hookless_observer as fixtures
from zzz_ops.tick_math import sqrt_price_at_tick


class PoolObserverIntegrityTests(unittest.TestCase):
    def rpc(self, raw, calls=None):
        calls = calls or [('eth_chainId', [])]
        with patch.object(fixtures.OBSERVER.urllib.request, 'urlopen', return_value=io.BytesIO(raw)):
            return fixtures.OBSERVER.rpc('https://rpc.invalid', calls)

    def test_duplicate_envelope_or_nested_result_fields_are_rejected(self):
        for raw in (b'[{"jsonrpc":"2.0","id":99,"id":0,"result":"0x1237"}]',
                b'[{"jsonrpc":"2.0","id":0,"result":"first","result":"last"}]',
                b'[{"jsonrpc":"2.0","id":0,"result":{"number":99,"number":0}}]'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): self.rpc(raw)

    def test_nonfinite_constants_and_overflowing_floats_fail_closed(self):
        for token in (b'NaN', b'Infinity', b'-Infinity', b'1e999', b'-1e999'):
            raw = b'[{"jsonrpc":"2.0","id":0,"result":{"value":'+token+b'}}]'
            with self.subTest(token=token), self.assertRaises(ValueError): self.rpc(raw)

    def test_finite_values_and_exact_reordered_reply_ids_are_preserved(self):
        calls = [('eth_chainId', []), ('eth_getBlockByNumber', ['0x1', False])]
        raw = json.dumps([fixtures.reply(1, {'ratio': .125, 'pending': None}),
                          fixtures.reply(0, '0x1237')]).encode()
        self.assertEqual(self.rpc(raw, calls), ['0x1237', {'ratio': .125, 'pending': None}])

    def test_inconsistent_or_noncanonical_slot0_ticks_cannot_create_an_observation(self):
        fixture = fixtures.HooklessObserverTests('runTest')
        for tick in (100, (1 << 24)-1, 1 << 255):
            with self.subTest(tick=tick), self.assertRaises(ValueError):
                fixture.observe(change=lambda result: result.__setitem__(7,
                    fixtures.encoded(1 << 96, tick, 1000 | (1000 << 12), 10020)))

    def test_exact_downward_boundary_ticks_remain_valid_without_repair(self):
        fixture = fixtures.HooklessObserverTests('runTest')
        for endpoint in (-100, 0, 100):
            tick = endpoint-1
            result, _ = fixture.observe(change=lambda rows: rows.__setitem__(7,
                fixtures.encoded(sqrt_price_at_tick(endpoint), tick % (1 << 256),
                                 1000 | (1000 << 12), 10020)))
            self.assertTrue(result['read_only'])
            self.assertFalse(result['release_approved'])
            self.assertEqual(result['combined_fee_pips'], [11010, 11010])


if __name__ == '__main__':
    unittest.main()
