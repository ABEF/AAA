"""Operational reinvestment telemetry is decodable, never a reward credit."""
import copy
import unittest

from frontend_api.earnings_replay import Replay, TOPICS
from indexer.events import SCHEMA, decode
from zzz_ops.abi import keccak256, word

SIGNATURE = 'ResidualConsolidated(uint256,bool,bytes32,bytes32)'
TOPIC = '0x' + keccak256(SIGNATURE.encode()).hex()
REQUEST = '0x' + 'ab' * 32
REVIEW = '0x' + 'cd' * 32
NATIVE = '0x' + '0' * 40
MIGRATION = '0x' + '1' * 40
VAULT = '0x' + '2' * 40
FEES = '0x' + '3' * 40
FIXED_ZZZ = '0x' + '4' * 40


def event(forced):
    return {'address': MIGRATION,
        'topics': [TOPIC, '0x' + word(7, 'uint256'), REQUEST, REVIEW],
        'data': '0x' + word(forced, 'bool')}


class ResidualReinvestEventTests(unittest.TestCase):
    def test_guarded_and_forced_events_preserve_exact_review_identity(self):
        self.assertEqual(SCHEMA[TOPIC]['signature'], SIGNATURE)
        for forced in (False, True):
            with self.subTest(forced=forced):
                self.assertEqual(decode(event(forced)), ('ResidualConsolidated',
                    {'bucket': '7', 'forced': forced, 'requestHash': REQUEST, 'reviewHash': REVIEW}))

    def test_wrong_boolean_topic_count_or_data_length_is_rejected(self):
        original = event(False)
        for kind in ('boolean', 'missing_topic', 'extra_topic', 'extra_data', 'missing_data'):
            changed = copy.deepcopy(original)
            if kind == 'boolean': changed['data'] = '0x' + word(2, 'uint256')
            elif kind == 'missing_topic': changed['topics'].pop()
            elif kind == 'extra_topic': changed['topics'].append(REQUEST)
            elif kind == 'extra_data': changed['data'] += word(1, 'uint256')
            else: changed['data'] = '0x'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                decode(changed)

    def test_operational_event_cannot_credit_income_even_from_an_earnings_emitter(self):
        model = Replay(1000, 11)
        model.begin({'vault': VAULT, 'fees': FEES}, [NATIVE, FIXED_ZZZ], [])
        model.add('lp_individual', NATIVE, 17, 900)
        before = (dict(model.totals), dict(model.day), model.events, model.last_timestamp)
        for emitter in (MIGRATION, VAULT, FEES):
            for forced in (False, True):
                entry = event(forced)
                model(emitter, entry['topics'], entry['data'], 7, REQUEST, 950, REVIEW, 0)
                self.assertEqual((dict(model.totals), dict(model.day), model.events, model.last_timestamp), before)
        self.assertTrue(model.totals)
        self.assertFalse(any(topic == TOPIC for _, topic in TOPICS))


if __name__ == '__main__':
    unittest.main()
