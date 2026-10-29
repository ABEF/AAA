"""Ambiguous durable JSON must stop before a recovery journal can be reused."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_recovery as recovery_fixtures
from zzz_ops.state import atomic_json, read_json


class StateJSONIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'state.json'

    def rejected_without_replacement(self, raw):
        self.path.write_bytes(raw.encode())
        with self.assertRaises(ValueError) as caught:
            read_json(self.path, {'pending': None, 'spent': {}})
        self.assertEqual(self.path.read_bytes(), raw.encode())
        return str(caught.exception)

    def test_duplicate_pending_spend_and_nested_configuration_keys_fail_closed(self):
        for raw in ('{"pending":{"nonce":7},"pending":null}',
                '{"spent":{"2026-10-29":100,"2026-10-29":0}}',
                '{"contracts":{"vault":"first","vault":"second"}}',
                '{"pending":{},"\\u0070ending":null}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.rejected_without_replacement(raw), 'Duplicate JSON state field')

    def test_duplicate_field_diagnostic_never_echoes_key_or_value_contents(self):
        raw = '{"SYNTHETIC_PRIVATE_FIELD":"SYNTHETIC_VALUE","SYNTHETIC_PRIVATE_FIELD":null}'
        message = self.rejected_without_replacement(raw)
        self.assertNotIn('SYNTHETIC_PRIVATE_FIELD', message)
        self.assertNotIn('SYNTHETIC_VALUE', message)

    def test_nonfinite_constants_are_rejected_at_every_container_depth(self):
        for token in ('NaN', 'Infinity', '-Infinity'):
            for raw in (token, '[0,'+token+']', '{"metadata":{"value":'+token+'}}'):
                with self.subTest(token=token, raw=raw):
                    self.assertEqual(self.rejected_without_replacement(raw), 'Nonfinite JSON state number')

    def test_overflowing_float_literals_cannot_become_infinity(self):
        for token in ('1e999', '-1e999', '9.99E9999'):
            with self.subTest(token=token):
                self.assertEqual(self.rejected_without_replacement('{"metadata":'+token+'}'),
                                 'Nonfinite JSON state number')

    def test_finite_valid_json_retains_values_and_does_not_rewrite_bytes(self):
        raw = '{ "pending":null, "nonce":'+str(2**600)+', "fraction":0.125, "small":1e-10, '+ \
              '"enabled":true, "label":"NaN", "rows":[0,-3,1.5], "Pending":"case-sensitive" }\n'
        self.path.write_text(raw)
        value = read_json(self.path)
        self.assertEqual(value['nonce'], 2**600)
        self.assertEqual(value['fraction'], .125)
        self.assertEqual(value['small'], 1e-10)
        self.assertIs(value['enabled'], True)
        self.assertEqual(value['rows'], [0, -3, 1.5])
        self.assertEqual(value['label'], 'NaN')
        self.assertEqual(self.path.read_text(), raw)

    def test_only_missing_file_returns_the_explicit_default(self):
        default = {'pending': None}
        self.assertIs(read_json(self.path, default), default)
        self.assertIsNone(read_json(self.path))
        self.assertFalse(self.path.exists())
        self.path.write_text('not json')
        with self.assertRaises(json.JSONDecodeError): read_json(self.path, default)
        self.assertEqual(default, {'pending': None})

    def test_nonfinite_atomic_write_preserves_old_truth_and_cleans_private_temporary(self):
        atomic_json(self.path, {'pending': {'nonce': 7}, 'spent': {'day': 100}})
        original = self.path.read_bytes()
        for value in (float('nan'), float('inf'), -float('inf')):
            for candidate in ({'metadata': value}, {'metadata': [0, {'value': value}]}):
                with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                    atomic_json(self.path, candidate)
                self.assertEqual(self.path.read_bytes(), original)
                self.assertFalse(list(self.path.parent.glob('.state.json.*.tmp')))

    def test_finite_atomic_write_keeps_roundtrip_and_replaces_intentionally(self):
        atomic_json(self.path, {'pending': {'nonce': 7}, 'metadata': .125})
        self.assertEqual(read_json(self.path), {'pending': {'nonce': 7}, 'metadata': .125})
        atomic_json(self.path, {'pending': None, 'metadata': -.5})
        self.assertEqual(read_json(self.path), {'pending': None, 'metadata': -.5})


class KeeperStateJSONStartupTests(unittest.TestCase):
    def test_malformed_present_journal_stops_before_runtime_signer_or_rpc(self):
        fixture = recovery_fixtures.RecoveryTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.k.state['next_nonce'] = 7
        valid = json.dumps(fixture.k.state, separators=(',', ':'))
        cases = [valid.replace('"pending":null', '"pending":{"nonce":7},"pending":null'),
            valid.replace('"spent":{}', '"spent":{"day":100,"day":0}'),
            valid.replace('"next_nonce":7', '"next_nonce":8,"next_nonce":7'),
            valid[:-1]+',"metadata":{"value":NaN}}', valid[:-1]+',"metadata":{"value":1e999}}']
        config = {**fixture.cfg, 'reviewed_for_live_use': True, 'receipt_fee_policy': 'included'}
        for raw in cases:
            fixture.k.path.write_text(raw)
            with self.subTest(raw_kind=cases.index(raw)), \
                    patch.object(Keeper, '_validate_runtime_files') as files, \
                    patch.object(Keeper, '_validate_signer') as signer, \
                    patch('keeper.monitor.subprocess.run') as external:
                with self.assertRaises(ValueError): Keeper(config, live=True, rpc=fixture.rpc)
                files.assert_not_called()
                signer.assert_not_called()
                external.assert_not_called()
            self.assertEqual(fixture.k.path.read_text(), raw)
            self.assertEqual(fixture.rpc.calls, [])


if __name__ == '__main__':
    unittest.main()
