"""Fresh manual reinvestment admission; no runtime, service or journal adoption."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import production_v12 as OLD, production_v13 as P
from zzz_ops import production_observer_v12 as OLD_OBSERVER, production_observer_v13 as O
from zzz_ops.production_v2 import Gate, _bindings

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


GATE = load_script('validate-production-config')
OBSERVER_CLI = load_script('observe-production-config')


def config(current=True):
    name = 'production.example.json' if current else 'production.schema14.example.json'
    return json.loads((ROOT / 'config' / name).read_text(encoding='utf8'))


class ResidualReinvestProfileTests(unittest.TestCase):
    def test_archived14_is_exact_published_template_not_a_relabel(self):
        original = (ROOT / 'config/production.schema14.example.json').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
            '32cb99572ad0aee158ca42a6262bd1875777588f3f0baa2209144238f13089a5')
        self.assertEqual(config(False)['schema_version'], 14)
        self.assertEqual(OLD.VERSIONS['schema_version'], 14)
        self.assertNotIn('RESIDUAL_REINVEST_VERSION', OLD.expected_bindings(config(False)['chains'][0])['modules']['migration'])

    def test_current15_preserves_wire_and_remains_unqualified(self):
        current = config()
        self.assertEqual(current['schema_version'], 15)
        for field in ('accounting_version', 'custody_version', 'portfolio_version', 'canonical_schema'):
            self.assertEqual(current[field], config(False)[field])
        self.assertEqual(P.SERVICE_PROFILES, OLD.SERVICE_PROFILES)
        self.assertEqual(len(P.HELPERS), 18)
        report = GATE.validate(current, now=1793970000)
        self.assertEqual(report['schema_version'], 15)
        self.assertFalse(report['ready'])
        self.assertFalse(report['deployment_authorized'])
        self.assertIn('mint.opensea_unsupported', {row['code'] for row in report['issues']})

    def test_explicit_bindings_cover_every_forwarder_and_raw_exit(self):
        wanted = P.expected_bindings(config()['chains'][0])
        for group, role in P.REINVEST_ROLES:
            self.assertEqual(wanted[group][role]['RESIDUAL_REINVEST_VERSION'], 1)
        for group, role in P.RESIDUAL_EXIT_ROLES:
            self.assertEqual(wanted[group][role]['RESIDUAL_EXIT_VERSION'], 1)
        for role in ('migration_budget', 'portfolio_policy', 'lp_position_executor', 'contribution_pricing'):
            self.assertEqual(config()['chains'][0]['helpers'][role]['bindings'], wanted['helpers'][role])
        self.assertEqual(wanted['helpers']['portfolio_policy']['PORTFOLIO_VERSION'], 2)

    def test_missing_wrong_or_boolean_capability_never_matches_observed_binding(self):
        wanted = P.expected_bindings(config()['chains'][0])
        for key, roles in (('RESIDUAL_REINVEST_VERSION', P.REINVEST_ROLES),
                          ('RESIDUAL_EXIT_VERSION', P.RESIDUAL_EXIT_ROLES)):
            for group, role in roles:
                exact = {key: wanted[group][role][key]}
                record = {'bindings': copy.deepcopy(exact), 'observed_bindings': copy.deepcopy(exact)}
                gate = Gate(None)
                _bindings(gate, record, exact, role, helper=group == 'helpers')
                self.assertFalse(gate.issues)
                for value in (None, 0, 2, True, '1', 'missing'):
                    changed = copy.deepcopy(record)
                    if value == 'missing':
                        changed['observed_bindings'].pop(key)
                    else:
                        changed['observed_bindings'][key] = value
                    gate = Gate(None)
                    _bindings(gate, changed, exact, role, helper=group == 'helpers')
                    with self.subTest(group=group, role=role, key=key, value=value):
                        self.assertIn('binding.observed', {row['code'] for row in gate.issues})

    def test_current_gate_rejects14_and_malformed_identity_without_relabel(self):
        for value in (14, True, False, '15', 15.0, None):
            changed = config(False)
            changed['schema_version'] = value
            with self.subTest(value=value):
                result = GATE.validate(changed)
                self.assertEqual(result['schema_version'], 15)
                self.assertEqual(result['issues'][0]['code'], 'holder_exit_qualification_pending')
                self.assertFalse(result['deployment_authorized'])

    def test_observer_rejects14_and_wrong_versions_before_any_rpc(self):
        class NoRpc:
            def call(self, *_):
                raise AssertionError('No RPC permitted')
        for value in (14, True, False, '15', 15.0, None):
            changed = config(False)
            changed['schema_version'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'schema15'):
                O.observe(changed, NoRpc())
        changed = config()
        changed['accounting_version'] = 5
        with self.assertRaisesRegex(ValueError, 'selected inventory'):
            O.observe(changed, NoRpc())

    def test_observer_capabilities_use_code_owned_unsigned_types(self):
        observer = object.__new__(O.Observer)
        calls = []
        observer.read = lambda target, signature: calls.append((target, signature)) or ['0' * 63 + '1']
        target = '0x' + '1' * 40
        for name in ('RESIDUAL_REINVEST_VERSION', 'RESIDUAL_EXIT_VERSION'):
            actual = observer.typed(target, name, None)
            self.assertIs(type(actual), int)
            self.assertEqual(actual, 1)
        self.assertEqual(calls, [(target, 'RESIDUAL_REINVEST_VERSION()'), (target, 'RESIDUAL_EXIT_VERSION()')])

    def test_historical14_cli_requires_explicit_flag_and_keeps_approval_false(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'config.json'
            source.write_text(json.dumps(config(False)), encoding='utf8')
            for historical in (False, True):
                output = io.StringIO()
                args = ['gate', '--config', str(source)] + (['--historical-consistency'] if historical else [])
                with patch.object(sys, 'argv', args), redirect_stdout(output):
                    self.assertEqual(GATE.main(), 1)
                report = json.loads(output.getvalue())
                self.assertEqual(report['schema_version'], 14 if historical else 15)
                self.assertFalse(report['deployment_authorized'])
                self.assertIs(report['current_release_gate'], not historical)
                if historical:
                    self.assertEqual(report['approval_scope'], 'historical_manifest_consistency_only')

    def test_observer_cli_dispatches_only_explicit_current_or_historical(self):
        result = {'chains': [{'observation': {'complete': False}}]}
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.json'
            output = Path(folder) / 'output.json'
            for current, historical in ((True, False), (False, True), (False, False), (True, True)):
                source.write_text(json.dumps(config(current)), encoding='utf8')
                args = ['--config', str(source), '--rpc-env', 'POPL_REVIEW_RPC', '--output', str(output)]
                if historical:
                    args.append('--historical-consistency')
                with patch.dict(os.environ, {'POPL_REVIEW_RPC': 'http://127.0.0.1:1'}), \
                        patch.object(OBSERVER_CLI, 'Rpc', return_value=object()), \
                        patch.object(O, 'observe', return_value=result) as new, \
                        patch.object(OLD_OBSERVER, 'observe', return_value=result) as old, \
                        patch.object(OBSERVER_CLI, 'write_observation') as write, \
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    status = OBSERVER_CLI.main(args)
                    with self.subTest(current=current, historical=historical):
                        self.assertEqual(status, 2 if current != historical else 1)
                        self.assertEqual(new.call_count, int(current and not historical))
                        self.assertEqual(old.call_count, int(not current and historical))
                        self.assertEqual(write.call_count, int(current != historical))


if __name__ == '__main__':
    unittest.main()
