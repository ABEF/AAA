"""Paid-revert visibility using inert canonical receipts, never a signer/RPC."""
import copy
import datetime as dt
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.ops import health_check
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError
import tests_python.test_keeper as fixtures


class KeeperRevertHealthTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.KeeperTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.k, self.rpc, self.cfg = self.fixture.k, self.fixture.rpc, self.fixture.cfg
        self.head = 100
        self.headers = {98:{'number':'0x62','timestamp':hex(self.rpc.now),'hash':fixtures.H}}
        self.k.state.update(next_nonce=7,receipt_anchor={'number':98,'hash':fixtures.H,
            'timestamp':self.rpc.now,'nonce':6})
        original = self.rpc.call
        def call(method, params):
            if method == 'eth_getBlockByNumber':
                if params[0] == 'latest':
                    return {'number':hex(self.head),'timestamp':hex(self.rpc.now),'hash':fixtures.H}
                number = int(params[0],16)
                if number in self.headers: return dict(self.headers[number])
            return original(method,params)
        self.rpc.call = call
        self._operating()

    def _operating(self):
        # The live health branch is exercised without live initialization or
        # submission. Each cycle body below is an inert receipt/read operation.
        self.k.live = True
        self.k.canonical_lifecycle = 0
        self.k.preparing = False
        self.k.last_success_at = dt.datetime.now(dt.timezone.utc).isoformat()

    def _receipt(self, success, *, key='rebalance:7', nonce=7, block=99, tx_hash=fixtures.H):
        self.fixture.k = self.k
        self.fixture.receipt(success)
        pending = self.k.state['pending']
        pending.update(key=key,nonce=nonce,hash=tx_hash,value=0)
        pending['data'] = (calldata('rebalance(uint256,uint128,uint256)',7,1,self.rpc.now+180)
            if key.startswith('rebalance:') else calldata('collectFees(uint256,uint256)',7,self.rpc.now+180))
        pending['fee_review']['maximum_cost_wei'] = 517
        self.rpc.receipt.update(transactionHash=tx_hash,blockNumber=hex(block),blockHash=tx_hash)
        self.rpc.tx.update(hash=tx_hash,nonce=hex(nonce),input=pending['data'],value='0x0',
            blockNumber=hex(block),blockHash=tx_hash)
        self.headers[block] = {'number':hex(block),'timestamp':hex(self.rpc.now),'hash':tx_hash}
        self.head = block+1

    def _run(self, body=None, *, desktop_time=None):
        with patch.object(self.k,'cycle',side_effect=body or (lambda:None)), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now if desktop_time is None else desktop_time), \
                patch('keeper.monitor.subprocess.run') as signer:
            result = self.k.run_cycle()
        signer.assert_not_called()
        return result

    def _health(self):
        return json.loads(self.k.health_path.read_text())

    def test_confirmed_paid_revert_is_unhealthy_without_reattempt_or_new_backoff(self):
        self._receipt(False)
        prior_success = self.k.last_success_at
        self.assertTrue(self._run(self.k.poll_pending))
        health = self._health()
        self.assertEqual(health['status'],'revert_cooldown')
        self.assertEqual(health['confirmed_reverts'],1)
        self.assertEqual(health['active_revert_cooldowns'],1)
        self.assertEqual(health['next_revert_retry_after'],self.rpc.now+3600)
        self.assertEqual(health['blocked_actions'],0)
        self.assertEqual(health['consecutive_failures'],0)
        self.assertEqual(health['last_success_at'],prior_success)
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(self.k.state['next_nonce'],8)
        self.assertEqual(sum(self.k.state['spent'].values()),205)
        self.assertNotIn('rebalance:7',self.k.state['last'])
        self.assertIn('reverted_actions_in_cooldown',health_check(self.cfg)['reasons'])

    def test_failure_remains_visible_after_restart_without_rewriting_journal(self):
        self._receipt(False)
        self._run(self.k.poll_pending)
        before = self.k.path.read_bytes()
        self.k = Keeper(self.cfg,rpc=self.rpc)
        self._operating()
        self.assertTrue(self._run())
        self.assertEqual(self._health()['confirmed_reverts'],0)
        self.assertEqual(self._health()['status'],'revert_cooldown')
        self.assertEqual(self._health()['active_revert_cooldowns'],1)
        self.assertEqual(self.k.path.read_bytes(),before)
        self.assertFalse(health_check(self.cfg)['ok'])

    def test_unrelated_successful_harvest_cannot_hide_rebalance_failure(self):
        self._receipt(False)
        self._run(self.k.poll_pending)
        deadline = self.k.state['retry_after']['rebalance:7']
        self._receipt(True,key='harvest:7',nonce=8,block=101,tx_hash='0x'+'cd'*32)
        self.assertTrue(self._run(self.k.poll_pending))
        health = self._health()
        self.assertEqual(health['status'],'revert_cooldown')
        self.assertEqual(health['confirmed_reverts'],0)
        self.assertEqual(health['active_revert_cooldowns'],1)
        self.assertEqual(self.k.state['last']['harvest:7'],self.rpc.now)
        self.assertEqual(self.k.state['retry_after']['rebalance:7'],deadline)
        self.assertEqual(self.k.state['next_nonce'],9)
        self.assertEqual(sum(self.k.state['spent'].values()),410)
        self.assertFalse(health_check(self.cfg)['ok'])

    def test_retry_boundary_uses_chain_clock_and_retains_expired_failure_record(self):
        deadline = self.rpc.now
        self.k.state['retry_after'] = {'rebalance:7':deadline}
        before = copy.deepcopy(self.k.state)
        # A desktop clock within the accepted head-skew bound is behind the
        # canonical head; using it for the retry comparison would be wrong.
        self.assertTrue(self._run(desktop_time=deadline-500))
        self.assertEqual(self._health()['status'],'healthy')
        self.assertEqual(self._health()['active_revert_cooldowns'],0)
        self.assertIsNone(self._health()['next_revert_retry_after'])
        self.assertEqual(self.k.state,before)
        self.assertNotIn('rebalance:7',self.k.state['last'])

    def test_only_future_cooldowns_count_with_bounded_earliest_deadline_summary(self):
        self.k.state['retry_after'] = {'old':self.rpc.now-1,'eligible':self.rpc.now,
            'later':self.rpc.now+100,'earlier':self.rpc.now+50}
        before = copy.deepcopy(self.k.state)
        self.assertTrue(self._run())
        health = self._health()
        self.assertEqual(health['active_revert_cooldowns'],2)
        self.assertEqual(health['next_revert_retry_after'],self.rpc.now+50)
        self.assertNotIn('retry_after',health)
        self.assertEqual(self.k.state,before)

    def test_delayed_confirmation_still_reports_current_paid_revert_after_cooldown_expired(self):
        self._receipt(False)
        self.headers[99]['timestamp'] = hex(self.rpc.now-3601)
        self.assertTrue(self._run(self.k.poll_pending))
        health = self._health()
        self.assertEqual(health['status'],'degraded')
        self.assertEqual(health['confirmed_reverts'],1)
        self.assertEqual(health['active_revert_cooldowns'],0)
        self.assertEqual(health['blocked_actions'],0)
        self.assertEqual(health['consecutive_failures'],0)
        self.assertFalse(health_check(self.cfg)['ok'])
        self.assertTrue(self._run())
        self.assertEqual(self._health()['status'],'healthy')
        self.assertIn('rebalance:7',self.k.state['retry_after'])

    def test_success_for_the_same_action_clears_only_its_existing_restriction(self):
        self._receipt(False)
        self._run(self.k.poll_pending)
        self.rpc.now += 3600
        self._receipt(True,nonce=8,block=101,tx_hash='0x'+'cd'*32)
        self.assertTrue(self._run(self.k.poll_pending))
        self.assertNotIn('rebalance:7',self.k.state['retry_after'])
        self.assertEqual(self.k.state['last']['rebalance:7'],self.rpc.now)
        self.assertEqual(self._health()['status'],'healthy')
        self.assertEqual(self._health()['active_revert_cooldowns'],0)

    def test_independent_submission_keeps_its_existing_simulation_and_gas_path(self):
        self.k.state['retry_after'] = {'rebalance:7':self.rpc.now+3600}
        self.k.live = False
        self.assertTrue(self._run(lambda:self.k.submit('vault','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),'harvest:7')))
        self.assertIn('eth_estimateGas',[method for method,params in self.rpc.calls])
        self.assertEqual(self._health()['status'],'revert_cooldown')
        self.assertIsNone(self.k.state['pending'])

    def test_unavailable_cooldown_clock_cannot_publish_health_or_modify_journal(self):
        self.k.state['retry_after'] = {'rebalance:7':self.rpc.now+3600}
        self.k.save()
        before = self.k.path.read_bytes()
        with patch.object(self.k,'_head',side_effect=RpcError('PRIVATE ENDPOINT')):
            self.assertFalse(self._run())
        health = self._health()
        self.assertEqual(health['status'],'error')
        self.assertIsNone(health['active_revert_cooldowns'])
        self.assertNotIn('PRIVATE ENDPOINT',self.k.health_path.read_text())
        self.assertEqual(self.k.path.read_bytes(),before)
        self.assertIn('revert_cooldown_state_unknown',health_check(self.cfg)['reasons'])

    def test_clock_failure_after_valid_reconciliation_keeps_exact_paid_receipt_state(self):
        self._receipt(False)
        with patch.object(self.k,'_head',side_effect=[(100,self.rpc.now)]*3+[RpcError('clock')]):
            self.assertFalse(self._run(self.k.poll_pending))
        self.assertEqual(self._health()['status'],'error')
        self.assertEqual(self.k.confirmed_reverts,1)
        self.assertIsNone(self.k.state['pending'])
        self.assertEqual(self.k.state['next_nonce'],8)
        self.assertEqual(sum(self.k.state['spent'].values()),205)
        self.assertEqual(json.loads(self.k.path.read_text()),self.k.state)

    def test_failed_receipt_checkpoint_write_preserves_pending_and_never_counts_revert(self):
        self._receipt(False)
        self.k.save()
        before = copy.deepcopy(self.k.state)
        disk = self.k.path.read_bytes()
        with patch.object(self.k,'save',side_effect=OSError('disk full')), self.assertRaises(OSError):
            self._run(self.k.poll_pending)
        self.assertEqual(self.k.state,before)
        self.assertEqual(self.k.path.read_bytes(),disk)
        self.assertEqual(self.k.confirmed_reverts,0)
        self.assertEqual(self._health()['status'],'halted')

    def test_reorged_revert_is_still_pending_without_fee_or_revert_count(self):
        self._receipt(False)
        self.rpc.receipt['blockHash'] = '0x'+'cd'*32
        before = copy.deepcopy(self.k.state)
        self.assertTrue(self._run(self.k.poll_pending))
        self.assertEqual(self.k.state,before)
        self.assertEqual(self.k.confirmed_reverts,0)
        self.assertEqual(self._health()['status'],'awaiting_receipt')
        self.assertEqual(self._health()['active_revert_cooldowns'],0)

    def test_ambiguous_pending_and_canonical_lock_keep_status_precedence_and_cooldown_marker(self):
        self.k.state['retry_after'] = {'rebalance:7':self.rpc.now+3600}
        self._receipt(True,key='harvest:7')
        self.k.state['pending']['hash'] = None
        before = copy.deepcopy(self.k.state['pending'])
        self.assertTrue(self._run(self.k.poll_pending))
        self.assertEqual(self._health()['status'],'recovery_required')
        self.assertEqual(self._health()['active_revert_cooldowns'],1)
        self.assertEqual(self.k.state['pending'],before)
        self.k.state['pending'] = None
        self.k.canonical_lifecycle = 3
        self.assertTrue(self._run())
        self.assertEqual(self._health()['status'],'canonical_locked')
        self.assertEqual(self._health()['active_revert_cooldowns'],1)
        reasons = health_check(self.cfg)['reasons']
        self.assertIn('canonical_lifecycle_locked',reasons)
        self.assertIn('reverted_actions_in_cooldown',reasons)

    def test_historical_journal_without_cooldowns_needs_no_new_rpc_or_journal_fields(self):
        self.k.state.pop('retry_after',None)
        self.k.save()
        before = self.k.path.read_bytes()
        with patch.object(self.k,'_head',side_effect=AssertionError('unexpected RPC')):
            self.assertTrue(self._run())
        self.assertEqual(self._health()['active_revert_cooldowns'],0)
        self.assertIsNone(self._health()['next_revert_retry_after'])
        self.assertEqual(self.k.path.read_bytes(),before)
        self.assertTrue(health_check(self.cfg)['ok'])

    def test_checker_rejects_missing_or_malformed_required_cooldown_fields(self):
        self.assertTrue(self._run())
        baseline = self._health()
        malformed = [dict(baseline,active_revert_cooldowns=value)
            for value in (None,True,-1,0.0,'0',{},[])]
        malformed.extend(dict(baseline,next_revert_retry_after=value)
            for value in (0,True,'0',self.rpc.now))
        malformed.extend(dict(baseline,active_revert_cooldowns=1,next_revert_retry_after=value)
            for value in (None,True,0,-1,'123',0.5))
        for field in ('active_revert_cooldowns','next_revert_retry_after'):
            missing = dict(baseline)
            missing.pop(field)
            malformed.append(missing)
        for data in malformed:
            with self.subTest(data=data):
                self.k.health_path.write_text(json.dumps(data))
                self.assertIn('revert_cooldown_state_unknown',health_check(self.cfg)['reasons'])

    def test_checker_cannot_ignore_active_cooldown_even_with_healthy_status(self):
        self.assertTrue(self._run())
        data = dict(self._health(),active_revert_cooldowns=1,next_revert_retry_after=self.rpc.now+3600)
        self.k.health_path.write_text(json.dumps(data))
        result = health_check(self.cfg)
        self.assertFalse(result['ok'])
        self.assertIn('reverted_actions_in_cooldown',result['reasons'])
        self.assertEqual(result['active_revert_cooldowns'],1)
        self.assertEqual(result['next_revert_retry_after'],self.rpc.now+3600)

    def test_checker_rejects_current_paid_revert_or_unknown_flag_even_after_cooldown_expiry(self):
        self.assertTrue(self._run())
        baseline = self._health()
        for value in (1,None,True,-1,0.0,'0',{},[]):
            with self.subTest(value=value):
                self.k.health_path.write_text(json.dumps(dict(baseline,confirmed_reverts=value)))
                result = health_check(self.cfg)
                self.assertFalse(result['ok'])
                self.assertIn('confirmed_reverts',result['reasons'])
        baseline.pop('confirmed_reverts')
        self.k.health_path.write_text(json.dumps(baseline))
        self.assertIn('confirmed_reverts',health_check(self.cfg)['reasons'])


if __name__ == '__main__': unittest.main()
