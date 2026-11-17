"""Actual offline planner/ABI checks for unqualified launch-workload reads.

Synthetic assignments are not deployed observations, gas measurements or
authority approval. Existing test modules and profiles remain unchanged.
"""
import copy
from pathlib import Path
import tempfile
import unittest

from tests_python import preseal_fixture as F
from zzz_ops import deployment_plan as D, preseal_plan as P


class PresealLaunchWorkloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='popl-preseal-launch-')
        cls.addClassCleanup(temporary.cleanup)
        cls.value = F.complete(Path(temporary.name))
        cls.original = copy.deepcopy(cls.value)
        cls.plan = P.prepare(cls.value)

    def checks(self, plan=None):
        return {row['id']:row for row in (plan or self.plan)['seal_boundary_review']['checks']}

    def test_actual_plan_keeps_capacity_distinct_from_admitted_royalty_workload(self):
        row = self.checks()['royalty_workload']
        self.assertEqual('royalty_rewards', row['target_role'])
        self.assertEqual(self.value['child_addresses']['royalty_rewards'], row['assigned_target'])
        self.assertEqual(['assetCapacity()','MAX_ERC20_ASSETS()','MAX_ASSETS()',
                          'assetCount()','assets(uint256)'], row['required_reads'])
        self.assertIn('16 ERC20 currencies plus native ETH, not17 already-admitted assets', row['requirement'])
        self.assertIn('64 ERC20s plus ETH', row['requirement'])
        self.assertIn('healthy, pending-receipt and gas-consuming fault workloads', row['requirement'])
        self.assertFalse(row['verified']); self.assertEqual('unverified', row['status'])
        self.assertNotIn('observed_asset_count', row)

    def test_parameterized_currency_read_requires_observed_zero_based_uint256_index(self):
        row = self.checks()['royalty_workload']
        index = row['required_read_inputs']['assets(uint256)']['index']
        self.assertEqual('uint256', index['type'])
        self.assertEqual('canonical unsigned decimal string', index['format'])
        self.assertEqual('0', index['first_index'])
        self.assertEqual('0 <= index < observed assetCount()', index['range'])
        self.assertNotIn('value', index)
        # Unknown assignments retain instructions, never invented targets/counts.
        unknown = self.checks(P.prepare(P.example()))['royalty_workload']
        self.assertIsNone(unknown['assigned_target']); self.assertFalse(unknown['verified'])
        self.assertEqual(row['required_read_inputs'], unknown['required_read_inputs'])

    def test_new_required_reads_exist_on_exact_trusted_target_abis(self):
        artifacts = D.Artifacts()
        roles = {row['role']:row['contract'] for row in
                 self.plan['seal_boundary_review']['constructor_boundaries']}
        for key in ('royalty_workload', 'gas_policy'):
            row = self.checks()[key]
            _, obj, _ = artifacts.contract(roles[row['target_role']])
            reads = {item['name']+'('+','.join(i['type'] for i in item['inputs'])+')':item
                     for item in obj['abi'] if item['type']=='function' and
                     item['stateMutability'] in ('view','pure')}
            for signature in row['required_reads']:
                self.assertIn(signature, reads, (key, row['target_role'], signature))
            if key=='royalty_workload':
                self.assertEqual([{'internalType':'uint256','name':'','type':'uint256'}],
                                 reads['assets(uint256)']['inputs'])

    def test_gas_review_remains_unverified_and_cannot_change_setup_calls_or_flags(self):
        row = self.checks()['gas_policy']
        self.assertEqual('protocol_policy', row['target_role'])
        self.assertEqual(self.value['constructor_input']['planned_addresses']['protocol_policy'],
                         row['assigned_target'])
        self.assertEqual(['gasPolicy()','payoutGas()','sourceCallGas()',
                          'royaltySyncGas()','gasFingerprint()'], row['required_reads'])
        self.assertIn('per-currency sync budget is not a whole-transaction guarantee', row['requirement'])
        self.assertIn('full20% activation-policy2 or25% maintenance headroom', row['requirement'])
        self.assertFalse(row['verified']); self.assertEqual('unverified', row['status'])
        self.assertTrue(all(self.plan[flag] is False for flag in P.FALSE_FLAGS))
        self.assertFalse(self.plan['seal_boundary_review']['all_preconditions_verified'])
        self.assertIsNone(self.plan['seal_boundary_review']['seal_calldata'])
        self.assertTrue(self.plan['configuration_inputs_complete'])
        calls = [call for step in self.plan['steps'] for call in step['calls']]
        self.assertEqual(24, len(calls))
        self.assertFalse(any(call['function'] in ('setGasPolicy','increaseRoyaltyAssetCapacity',
                                                'addRoyaltyAsset','seal') for call in calls))
        self.assertEqual(self.original, self.value)


if __name__ == '__main__':
    unittest.main()
