"""Current offline setup must disclose deliberately stopped LP operations.

Real preparation and current trusted ABIs are used, with synthetic public inputs.
This is not a successful on-chain configuration or readiness qualification.
"""
import copy
from pathlib import Path
import tempfile
import unittest

from tests_python import preseal_fixture as F
from zzz_ops import preseal_plan as P


class PresealOperatingStopTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-preseal-stops-')
        self.addCleanup(temporary.cleanup)
        self.value = F.complete(Path(temporary.name))

    def test_disabled_contribution_pool_operations_are_explicit_without_changing_the_call(self):
        value = copy.deepcopy(self.value)
        main = value['settings']['native_pools']['pools'][0]['config']
        main['operationsEnabled'] = False
        result = P.prepare(value)
        self.assertTrue(result['configuration_inputs_complete'])
        expected = ('Pool '+P.SELECTED_POOL+' has ordinary LP operations disabled; '
                    'contributions, compounding and ordinary rebalancing are stopped for that pool.')
        self.assertIn(expected, result['explicit_operating_stops'])
        pool_step = next(row for row in result['steps'] if row['id']=='configure:native_pools')
        configure = pool_step['calls'][0]
        self.assertEqual('configureNative', configure['function'])
        self.assertIs(configure['arguments'][0]['value']['operationsEnabled'], False)
        self.assertTrue(configure['calldata'].startswith('0x'))
        self.assertIs(main['depositsEnabled'], True)
        self.assertEqual(value, P.validate(value))
        self.assertTrue(all(result[flag] is False for flag in P.FALSE_FLAGS))

    def test_enabled_operations_do_not_report_a_false_pool_stop(self):
        result = P.prepare(self.value)
        self.assertTrue(result['configuration_inputs_complete'])
        self.assertFalse(any('ordinary LP operations disabled' in stop
                             for stop in result['explicit_operating_stops']))
        self.assertEqual([], result['explicit_operating_stops'])
        self.assertTrue(all(result[flag] is False for flag in P.FALSE_FLAGS))


if __name__ == '__main__':
    unittest.main()
