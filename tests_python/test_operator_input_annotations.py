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
        # Independent complete record, not just two explanation fields.
        self.assertEqual(result, [{'position': 0, 'name': 'request', 'label': 'request',
            'type': 'tuple', 'canonical_type': '(uint128)', 'internal_type': 'tuple',
            'explanation': 'Legacy top-level explanation.', 'components': [
                {'position': 0, 'name': 'amount', 'label': 'amount', 'type': 'uint128',
                 'canonical_type': 'uint128', 'internal_type': 'uint128', 'explanation': None}]}])

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
        # Global phrases/anchor counts could pass with the two links swapped.
        # Follow each actual operation's link to its own expanded field table.
        def section(action):
            rows=[line for line in rendered.splitlines()
                  if '[Migration.'+action+']' in line]
            self.assertEqual(1,len(rows),action)
            target=re.search(r'\[EmergencyRebalance\]\(#([^)]*)\)',rows[0])
            self.assertIsNotNone(target,action)
            anchor=target.group(1)
            marker='<a id="'+anchor+'"></a>'
            self.assertEqual(1,rendered.count(marker),action)
            return anchor,rendered.split(marker,1)[1].split('</details>',1)[0]
        consolidate,consolidation=section('consolidateResidual')
        replacement,emergency=section('emergencyRebalance')
        self.assertNotEqual(consolidate,replacement)
        self.assertIn('not emergencyCustodyHash',consolidation)
        self.assertIn('EXACT existing main ticks',consolidation)
        self.assertIn('positive ADDED main liquidity delta',consolidation)
        self.assertIn('no compound-reserve release',consolidation)
        self.assertIn('not consolidationCustodyHash',emergency)
        self.assertIn('lower/upper(raw spaced physical ticks, lower&lt;upper)',emergency)
        self.assertIn('Disabled financial checks can lose almost all principal',emergency)


if __name__ == '__main__':
    unittest.main()
