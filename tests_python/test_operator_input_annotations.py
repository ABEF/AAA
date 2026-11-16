"""New operator-input documentation cases; no compiler, RPC or transactions."""
import json
from pathlib import Path
import re
import unittest

from zzz_ops.function_reference import ReferenceError, _parameters, render_markdown
from zzz_ops.operator_reference import render


class OperatorInputAnnotationTests(unittest.TestCase):
    def test_nested_tuple_and_array_notes_preserve_abi_order_and_units(self):
        fields = [
            {'name': 'request', 'type': 'tuple[]', 'components': [
                {'name': 'tick', 'type': 'int24'},
                {'name': 'key', 'type': 'tuple', 'components': [
                    {'name': 'fee', 'type': 'uint24'}]},
            ]},
        ]
        notes = {'request': {'explanation': 'Reviewed requests.', 'fields': {
            'tick': 'Signed spaced tick, not the moving current tick.',
            'key': {'explanation': 'Exact key.', 'fields': {
                'fee': 'LP fee in millionths, not basis points.'}},
        }}}
        result = _parameters(fields, 'inputs', notes)
        self.assertEqual(result[0]['canonical_type'], '(int24,(uint24))[]')
        tick, key = result[0]['components']
        self.assertEqual(tick['position'], 0)
        self.assertIn('Signed spaced tick', tick['explanation'])
        self.assertEqual(key['position'], 1)
        self.assertIn('millionths', key['components'][0]['explanation'])

    def test_legacy_string_notes_keep_identical_parameter_records(self):
        field = {'name': 'request', 'type': 'tuple', 'components': [
            {'name': 'amount', 'type': 'uint128'}]}
        result = _parameters([field], 'inputs', {'0': 'Legacy top-level explanation.'})
        self.assertEqual(result[0]['explanation'], 'Legacy top-level explanation.')
        self.assertIsNone(result[0]['components'][0]['explanation'])

    def test_unknown_fields_and_scalar_nested_notes_fail_closed(self):
        field = {'name': 'request', 'type': 'tuple', 'components': [
            {'name': 'amount', 'type': 'uint128'}]}
        for note in [
            {'explanation': 'Request.', 'fields': {'ammount': 'Typo.'}},
            {'explanation': 'Request.', 'fields': []},
            {'explanation': 'Request.', 'fields': {}, 'guess': True},
        ]:
            with self.subTest(note=note), self.assertRaises(ReferenceError):
                _parameters([field], 'inputs', {'request': note})
        with self.assertRaisesRegex(ReferenceError, 'nested parameter'):
            _parameters([{'name': 'amount', 'type': 'uint128'}], 'inputs', {
                'amount': {'explanation': 'Amount.', 'fields': {}}})

    def test_every_operator_tuple_leaf_is_explicitly_annotated(self):
        root = Path(__file__).resolve().parents[1]
        reference = json.loads((root/'docs/function-reference.json').read_text(encoding='utf-8'))
        examples = json.loads((root/'docs/operator-call-examples.json').read_text(encoding='utf-8'))
        found = []

        def visit(parameter, identity):
            self.assertTrue(parameter['explanation'], identity + ':' + parameter['label'])
            for child in parameter.get('components', []):
                found.append(child)
                visit(child, identity)

        for contract in reference['contracts']:
            for function in contract['functions']:
                identity = contract['name'] + '.' + function['signature']
                if examples['rows'][identity]['role'] in {'G', 'B', 'K', 'N'}:
                    for parameter in function['inputs']:
                        visit(parameter, identity)
        self.assertGreater(len(found), 90)
        rendered = render_markdown(reference)
        self.assertIn('price bounds', rendered)

    def test_conversion_control_values_are_not_mint_payments(self):
        root = Path(__file__).resolve().parents[1]
        reference = json.loads((root/'docs/function-reference.json').read_text(encoding='utf-8'))
        functions = next(c['functions'] for c in reference['contracts']
                         if c['name'] == 'ZZZLPRewardConverter')
        lookup = {function['signature']: function for function in functions}
        loss = lookup['setConversionLossBps(uint16)']['inputs'][0]['explanation']
        self.assertIn('basis points', loss)
        self.assertIn('1000', loss)
        for signature in ('setEnabled(bool)', 'setRouteEnabled(bytes32,bool)'):
            value = lookup[signature]['inputs'][-1]['explanation']
            self.assertIn('True', value)
            self.assertIn('false', value)
            self.assertNotIn('wei', value)

    def test_shared_struct_keeps_operation_specific_examples_and_meanings(self):
        root = Path(__file__).resolve().parents[1]
        reference = json.loads((root/'docs/function-reference.json').read_text(encoding='utf-8'))
        examples = json.loads((root/'docs/operator-call-examples.json').read_text(encoding='utf-8'))
        rendered = render(reference, examples)
        targets = re.findall(r'\[EmergencyRebalance\]\(#([^)]*)\)', rendered)
        self.assertGreaterEqual(len(set(targets)), 2)
        self.assertIn('Meaning / unit', rendered)
        self.assertIn('not consolidationCustodyHash', rendered)
        self.assertIn('not emergencyCustodyHash', rendered)
        self.assertIn('residual principal only; main remains unchanged', rendered)
        self.assertIn('combined main+residual principal close', rendered)


if __name__ == '__main__':
    unittest.main()
