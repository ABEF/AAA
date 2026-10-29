"""A retained anchor cannot hide lost descendants during read-only inventory."""
import copy
import unittest
from unittest.mock import patch

from tests_python import test_production_observer as historical
from tests_python import test_production_v4 as current
from zzz_ops import production_observer as observer
from zzz_ops import production_observer_v4 as observer_v4


def changing_head(rpc, final, initial=None):
    original = rpc.call
    reads = []
    def read(method, params=None):
        if method == 'eth_getBlockByNumber' and params[0] == 'latest':
            reads.append(1)
            if len(reads) > 1:
                return final
            if initial is not None:
                return initial
        return original(method, params)
    rpc.call = read
    return reads


class ObserverFinalDepthTests(unittest.TestCase):
    def legacy(self, final, initial=None):
        config, expected = historical.fixture()
        rpc = historical.FakeRPC(config, expected)
        reads = changing_head(rpc, final, initial)
        return config, expected, rpc, reads

    def observe(self, config, expected, rpc):
        with patch('zzz_ops.production_v2.expected_bindings', return_value=expected):
            return observer.observe(config, rpc)

    def test_historical_profile_lost_depth_discards_whole_result_and_preserves_input(self):
        config, expected, rpc, reads = self.legacy(dict(number='0xb', hash=historical.HASH, timestamp='0x3e9'))
        before = copy.deepcopy(config)
        with self.assertRaisesRegex(ValueError, 'confirmation depth'):
            self.observe(config, expected, rpc)
        self.assertEqual(config, before)
        self.assertEqual(len(reads), 2)

    def test_fresh_schema6_inherits_final_depth_check_without_adopting_pins(self):
        fixture = current.CurrentProductionTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        config = fixture.cfg; before = copy.deepcopy(config)
        rpc = current.F.RPC(config)
        anchor = config['chains'][0]['observed_block']
        changing_head(rpc, dict(number=hex(anchor['number']), hash=anchor['hash'], timestamp=hex(anchor['timestamp'])))
        with self.assertRaisesRegex(ValueError, 'confirmation depth'):
            observer_v4.observe(config, rpc)
        self.assertEqual(config, before)

    def test_missing_malformed_or_contradictory_final_header_is_unavailable(self):
        for final in (None, dict(number='0x00', hash=historical.HASH, timestamp='0x3ea'),
                dict(number='0xc', hash=historical.HASH, timestamp='0x3e7')):
            with self.subTest(final=final):
                config, expected, rpc, _ = self.legacy(final)
                with self.assertRaises(ValueError): self.observe(config, expected, rpc)

    def test_final_head_is_recorded_after_growth(self):
        config, expected, rpc, reads = self.legacy(dict(number='0xd', hash=historical.HASH, timestamp='0x3eb'))
        result = self.observe(config, expected, rpc)
        self.assertTrue(result['chains'][0]['observation']['complete'])
        self.assertEqual(result['chains'][0]['observation']['observed_head'], 13)
        self.assertEqual(len(reads), 2)

    def test_descendant_retreat_with_sufficient_depth_keeps_anchor_and_final_truth(self):
        config, expected, rpc, _ = self.legacy(dict(number='0xc', hash=historical.HASH, timestamp='0x3ea'),
            dict(number='0xe', hash=historical.GENESIS, timestamp='0x3ec'))
        result = self.observe(config, expected, rpc)
        self.assertTrue(result['chains'][0]['observation']['complete'])
        self.assertEqual(result['chains'][0]['observation']['observed_head'], 12)


if __name__ == '__main__':
    unittest.main()
