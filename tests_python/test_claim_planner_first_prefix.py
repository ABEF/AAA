"""New conservative-prefix checks; reused scaffolding runs no old test method."""
import unittest

from tests_python import test_claim_planner as scaffolding
from tests_python.test_frontend_api import addr, words
from frontend_api.service import ProjectionError
from frontend_api.transactions import TransactionInputError
from zzz_ops.abi import calldata


class ClaimPlannerFirstPrefixTests(unittest.TestCase):
    def fixture(self):
        case = scaffolding.ClaimPlannerTests('runTest')
        case.setUp()
        self.addCleanup(case.doCleanups)
        entries = case.many(32)
        case.rpc.refused = {int(entries[-1]['token_id'])}
        return case, entries

    def test_late_refusal_stops_at_first_success_and_freshly_revalidates_prefix(self):
        case, entries = self.fixture()
        result = case.plan(entries)
        self.assertEqual([len(row['selection_indices']) for row in result['planning']['attempts']], [32, 16])
        self.assertEqual([int(params[0]['data'][74:138], 16) for params in case.rpc.simulations], [32, 16, 16])
        self.assertEqual([row['token_id'] for row in result['next_batch']['claim_operations']],
                         [row['token_id'] for row in entries[:16]])
        self.assertEqual([row['selection_index'] for row in result['remaining_claims']], list(range(16, 32)))
        self.assertTrue(all(row['status'] == 'unassessed' for row in result['remaining_claims']))
        self.assertTrue(result['planning']['final_batch_revalidated'])
        self.assertFalse(result['planning']['batch_optimality_guaranteed'])
        self.assertEqual(result['planning']['maximum_trials'], 10)
        self.assertEqual(result['planning']['maximum_selection'], 32)
        self.assertEqual(result['next_batch']['simulation']['gas_cap'], '12000000')

    def test_final_owner_change_discards_the_first_success(self):
        case, entries = self.fixture()
        original = case.rpc.call
        owner_selector = calldata('ownerOf(uint256)', int(entries[0]['token_id']))[:10]
        def changed_owner(method, params):
            if (method == 'eth_call' and 'from' not in params[0] and
                    params[0]['to'] == addr(2) and params[0]['data'].startswith(owner_selector) and
                    len(case.rpc.simulations) >= 2):
                return words(addr(31))
            return original(method, params)
        case.rpc.call = changed_owner
        with self.assertRaises(TransactionInputError):
            case.plan(entries)
        self.assertEqual([int(params[0]['data'][74:138], 16) for params in case.rpc.simulations], [32, 16])

    def test_final_lifecycle_change_discards_the_first_success(self):
        case, entries = self.fixture()
        original = case.rpc.call
        settling = calldata('canonicalSettling()')
        def changed_lifecycle(method, params):
            if (method == 'eth_call' and params[0] == {'to': addr(1), 'data': settling} and
                    len(case.rpc.simulations) >= 2):
                return words(1)
            return original(method, params)
        case.rpc.call = changed_lifecycle
        with self.assertRaises(ProjectionError):
            case.plan(entries)
        self.assertEqual([int(params[0]['data'][74:138], 16) for params in case.rpc.simulations], [32, 16])
