"""New diagnostic parity cases; reuse fixtures without inheriting old tests."""
import copy
import json
import unittest

from keeper.monitor import CONFIRMATION_CLEARS, Keeper
from keeper.operation_review import review
from tests_python import test_keeper_operation_review as original


class KeeperOperationReviewFollowupTests(unittest.TestCase):
    setUp = original.KeeperOperationReviewTests.setUp
    read = original.KeeperOperationReviewTests.read
    rows = original.KeeperOperationReviewTests.rows

    def profile2(self, price):
        self.cfg.update(chain_id=4663, submission_fee_profile=2)
        self.cfg['maintenance']['compound'] = False
        state = json.loads(self.path.read_bytes())
        state['chain_id'] = 4663
        self.path.write_text(json.dumps(state))
        base = self.rpc.call
        events = []

        def call(method, params):
            if method == 'eth_chainId': return 4663
            if method == 'eth_gasPrice':
                events.append(('quote', price))
                # A second quote would change a transaction review's fee bound.
                return hex(price if sum(e[0] == 'quote' for e in events) == 1 else 999)
            if method == 'eth_call' and 'from' in params[0]:
                events.append(('simulate', copy.deepcopy(params[0])))
            if method == 'eth_estimateGas': events.append(('estimate', copy.deepcopy(params[0])))
            return base(method, params)

        self.rpc.call = call
        return events

    def test_profile2_quotes_once_before_same_typed_simulation_and_estimate(self):
        events = self.profile2(7)
        before = self.path.read_bytes()
        row = self.rows(simulate=True)['harvest']
        self.assertEqual('simulated', row['state'])
        self.assertEqual(['quote', 'simulate', 'estimate'], [e[0] for e in events])
        simulated, estimated = events[1][1], events[2][1]
        self.assertEqual(simulated, estimated)
        self.assertEqual(('0x2', '0x7', '0x0'),
                         (simulated.get('type'), simulated.get('maxFeePerGas'), simulated.get('maxPriorityFeePerGas')))
        self.assertEqual(7, row['checks']['gas']['value']['price_wei'])
        self.assertEqual(2, row['checks']['gas']['value']['submission_fee_profile'])
        self.assertEqual(before, self.path.read_bytes())

    def test_profile2_zero_quote_refuses_before_any_operation_simulation(self):
        events = self.profile2(0)
        row = self.rows(simulate=True)['harvest']
        self.assertEqual(['quote'], [e[0] for e in events])
        self.assertEqual('unavailable', row['state'])
        self.assertEqual(['gas_price_quote_unavailable'], row['reasons'])
        self.assertEqual('not_requested', row['simulation']['state'])

    def tracked_clear(self):
        state = json.loads(self.path.read_bytes())
        state[CONFIRMATION_CLEARS] = {'7': {'number': 99, 'hash': '0x'+'ab'*32,
            'timestamp': self.rpc.now-60, 'nonce': 0, 'awaiting_healthy_read': True}}
        self.path.write_text(json.dumps(state))

    def test_in_range_foreign_observation_blocks_compound_without_blocking_harvest(self):
        self.tracked_clear()
        self.rpc.record = (1, self.rpc.now-100, self.rpc.now, 2)
        before = self.path.read_bytes()
        rows = self.rows(simulate=True)
        self.assertEqual('blocked', rows['compound']['state'])
        self.assertEqual(['waiting_confirmation_clear'], rows['compound']['reasons'])
        proof = rows['compound']['checks']['compound_confirmation_coordination']['value']
        self.assertEqual(0, proof['current_side'])
        self.assertTrue(proof['record']['nonempty'])
        self.assertTrue(proof['clear_ack_present'])
        self.assertEqual('not_requested', rows['compound']['simulation']['state'])
        self.assertEqual('simulated', rows['harvest']['state'])
        self.assertEqual(before, self.path.read_bytes())

    def test_tracked_malformed_observation_is_unavailable_and_never_invents_clear(self):
        self.tracked_clear()
        self.rpc.record = (1, 0, self.rpc.now, 2)
        before = self.path.read_bytes()
        rows = self.rows(simulate=True)
        self.assertEqual('unavailable', rows['compound']['state'])
        self.assertEqual(['compound_confirmation_evidence_unavailable'], rows['compound']['reasons'])
        self.assertEqual('simulated', rows['harvest']['state'])
        self.assertEqual(before, self.path.read_bytes())

    def test_confirmation3_threshold_return_reports_existing_clear_requirement(self):
        from tests_python.test_keeper_portfolio_policy import PortfolioRPC
        rpc = PortfolioRPC(self.path.with_name('portfolio.json'))
        rpc.physical_side = rpc.reference = 0
        rpc.record = (1, rpc.now-100, rpc.now, 2)
        keeper = Keeper(rpc.cfg, rpc=rpc)
        keeper.state[CONFIRMATION_CLEARS] = {'7': {'number': 99, 'hash': '0x'+'ab'*32,
            'timestamp': rpc.now-60, 'nonce': 0, 'awaiting_healthy_read': True}}
        keeper.save()
        path = self.path.with_name('portfolio.json')
        before = path.read_bytes()
        rows = {row['operation']: row for row in review(rpc.cfg, [7], rpc=rpc,
                simulate=True, now=lambda: rpc.now)['operations']}
        self.assertEqual(['waiting_confirmation_clear'], rows['compound']['reasons'])
        self.assertEqual(0, rows['compound']['checks']['compound_confirmation_coordination']['value']['current_side'])
        self.assertEqual('simulated', rows['harvest']['state'])
        self.assertEqual(before, path.read_bytes())


if __name__ == '__main__': unittest.main()
