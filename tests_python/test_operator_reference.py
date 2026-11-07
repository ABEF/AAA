"""Documentation coverage and ABI boundaries; no compiler, RPC or transactions."""
import copy
import json
from pathlib import Path
import unittest

from zzz_ops.operator_reference import (
    BEGIN, END, ExampleError, check_examples, display, generate, render, validate_value,
)

ROOT = Path(__file__).resolve().parents[1]


class OperatorReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((ROOT/'docs/function-reference.json').read_text())
        cls.examples = json.loads((ROOT/'docs/operator-call-examples.json').read_text())

    def test_current_callables_have_exact_examples_and_no_missing_types(self):
        expected = check_examples(self.reference, self.examples)
        self.assertEqual(len(expected), sum(self.reference['counts'][x] for x in ('functions','constructors','receive_hooks')))
        self.assertEqual(sum(f['kind'] == 'function' for f in expected.values()), self.reference['counts']['functions'])

    def test_table_is_current_without_writing_or_compiling(self):
        self.assertFalse(generate(check=True)['ready_for_submission'])

    def test_every_callable_has_a_row_and_each_explanation_is_at_most_five_words(self):
        text = render(self.reference, self.examples)
        rows = [line for line in text.splitlines() if line.startswith('| `') and 'CONTRACT_FUNCTIONS.md#' in line]
        self.assertEqual(len(rows), len(self.examples['rows']))
        self.assertTrue(all(1 <= len(row.split('|')[-2].strip().split()) <= 5 for row in rows))
        self.assertEqual(text.count(BEGIN), 1); self.assertEqual(text.count(END), 1)

    def test_missing_or_extra_callable_fails_closed(self):
        for missing in (True, False):
            example = copy.deepcopy(self.examples)
            if missing:
                example['rows'].pop(next(iter(example['rows'])))
            else:
                example['rows']['RemovedContract.sweep()'] = next(iter(example['rows'].values()))
            with self.assertRaisesRegex(ExampleError, 'Missing, retired or extra'):
                check_examples(self.reference, example)

    def test_reference_drift_requires_new_example_review(self):
        example = copy.deepcopy(self.examples); example['reference_sha256'] = '0'*64
        with self.assertRaisesRegex(ExampleError, 'current complete function reference'):
            check_examples(self.reference, example)

    def test_overloaded_nft_transfers_are_not_collapsed(self):
        keys = self.examples['rows']
        self.assertIn('ZZZNFT.safeTransferFrom(address,address,uint256)', keys)
        self.assertIn('ZZZNFT.safeTransferFrom(address,address,uint256,bytes)', keys)

    def test_module_and_callback_cannot_be_presented_as_permissionless_actions(self):
        for identity in ['ZZZVault.compound(uint256,uint128,uint256)',
                         'ZZZV4RouteExecutor.unlockCallback(bytes)']:
            example = copy.deepcopy(self.examples); example['rows'][identity]['role'] = 'P'
            with self.assertRaisesRegex(ExampleError, 'Permissionless classification'):
                check_examples(self.reference, example)

    def test_governance_only_terminal_batches_are_not_keeper_or_public(self):
        for identity in ['ZZZMigration.allocatePrincipal(uint256)', 'ZZZMigration.distributePrincipal(uint256[])']:
            self.assertEqual(self.examples['rows'][identity]['role'], 'G')
            example = copy.deepcopy(self.examples); example['rows'][identity]['role'] = 'K'
            with self.assertRaisesRegex(ExampleError, 'Keeper classification'):
                check_examples(self.reference, example)
        self.assertEqual(self.examples['rows']['ZZZMigration.claimPrincipal(uint256,address)']['role'], 'H')

    def test_bootstrap_seal_and_one_time_bindings_remain_distinct(self):
        for identity in ['ZZZAccessController.seal()', 'ZZZRewards.bindConverter(address)',
                         'ZZZNFT.setBaseURI(string)']:
            self.assertEqual(self.examples['rows'][identity]['role'], 'B')

    def test_payable_value_cannot_be_hidden_inside_arguments(self):
        example = copy.deepcopy(self.examples)
        example['rows']['ZZZVault.mintDormant(bytes32)']['value'] = None
        with self.assertRaisesRegex(ExampleError, 'Payable value'):
            check_examples(self.reference, example)
        self.assertEqual(self.examples['rows']['ZZZVault.mintDormant(bytes32)']['value'], '$MINT_PRICE_WEI')

    def test_atomic_entry_keeps_its_complete_seven_field_tuple_and_policy(self):
        identity = 'ZZZActivationEntry.executeReviewed((uint256,bytes32,address,uint256,uint128,uint256,bool),uint16,bytes32)'
        example = copy.deepcopy(self.examples)
        self.assertEqual(len(example['rows'][identity]['arguments'][0]), 7)
        example['rows'][identity]['arguments'][0].pop()
        with self.assertRaisesRegex(ExampleError, 'Tuple fields'):
            check_examples(self.reference, example)
        example = copy.deepcopy(self.examples)
        example['rows'][identity]['arguments'][0] = '$OPAQUE_REQUEST'
        with self.assertRaisesRegex(ExampleError, 'Expand every tuple'):
            check_examples(self.reference, example)

    def test_floats_booleans_as_integers_overflows_and_malformed_bytes_reject(self):
        for parameter, value in [({'type':'uint16'},1.5),({'type':'uint256'},True),
                                 ({'type':'uint8'},256),({'type':'int24'},1<<23),
                                 ({'type':'bytes32'},'0x12'),({'type':'address'},'0x1')]:
            with self.subTest(parameter=parameter,value=value), self.assertRaises(ExampleError):
                validate_value(parameter, value)

    def test_fixed_arrays_cannot_drop_or_add_a_slot(self):
        validate_value({'type':'uint256[4]'}, ['$A','$B','$C','$D'])
        for values in [['$A'],['$A']*5]:
            with self.assertRaisesRegex(ExampleError, 'fixed array'):
                validate_value({'type':'uint256[4]'}, values)

    def test_unresolved_symbol_does_not_hide_an_unknown_abi_type(self):
        with self.assertRaisesRegex(ExampleError, 'Unsupported ABI'):
            validate_value({'type':'function'}, '$UNKNOWN_CALLBACK')

    def test_nested_json_preserves_uint256_precision_and_real_boolean_types(self):
        amount=2**200+123;native='0x'+'00'*20
        rendered=display([amount,native,False,['$NFT_ID',amount]])
        self.assertEqual(json.loads(rendered),[str(amount),native,False,['NFT_ID',str(amount)]])

    def test_dual_sources_have_distinct_reviewed_symbols_and_three_percent_tolerance(self):
        identity = 'ZZZOracle.setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)'
        args = self.examples['rows'][identity]['arguments']
        self.assertNotEqual(args[1][0], args[2][0]); self.assertNotEqual(args[1][2], args[2][2])
        self.assertEqual(args[3], 300)

    def test_snapshot_identifiers_remain_three_distinct_kinds(self):
        text = (ROOT/'docs/OPERATOR_MANUAL.md').read_text()
        self.assertIn('LiquidityManager.portfolioFingerprint(LP_TOKEN_ID)', text)
        self.assertNotIn('LiquidityManager.portfolioFingerprint(BUCKET_ID)', text)
        self.assertIn('ProtocolPolicy.entryFingerprint()', text)
        self.assertIn('Vault.mintPolicyFingerprint()', text)
        self.assertIn('Offline review procedure', text)

    def test_user_explanations_do_not_expand_into_long_warnings(self):
        example = copy.deepcopy(self.examples)
        example['rows'][next(iter(example['rows']))]['short'] = 'This explanation has far too many words'
        with self.assertRaisesRegex(ExampleError, 'one to five words'):
            check_examples(self.reference, example)

    def test_exact_lp_restricted_reads_keep_module_context(self):
        for identity in ('ZZZRewards.canonicalBarrier()', 'ZZZRewards.canonicalSeed(uint256)',
                         'ZZZRewards.canonicalNode(uint256)'):
            with self.subTest(identity=identity):
                self.assertEqual(self.examples['rows'][identity]['role'], 'M')
        check_examples(self.reference, self.examples)

    def test_module_read_exception_does_not_reclassify_public_getters(self):
        example = copy.deepcopy(self.examples)
        example['rows']['ZZZRewards.canonicalModule()']['role'] = 'M'
        with self.assertRaisesRegex(ExampleError, 'A read must not'):
            check_examples(self.reference, example)


if __name__ == '__main__':
    unittest.main()
