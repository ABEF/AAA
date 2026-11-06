"""Read-only per-action retry diagnostics; inert RPCs and temporary journals."""
import copy
import json
from unittest.mock import patch
import unittest

from keeper.monitor import Keeper
from tests_python import test_keeper_operation_review as fixtures
from zzz_ops.abi import calldata


class KeeperReviewRetryTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperOperationReviewTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.rpc,self.path=self.f.rpc,self.f.path

    def saved(self,**changes):
        state=json.loads(self.path.read_bytes());state.update(changes)
        self.path.write_text(json.dumps(state),encoding='utf8')

    def ready(self,action):
        if action=='rebalance':
            self.rpc.tick=self.rpc.upper
            self.rpc.record=(1,self.rpc.now-900,self.rpc.now,2)

    def test_future_retry_blocks_only_selected_action_before_simulation(self):
        for action in ('harvest','compound','rebalance'):
            with self.subTest(action=action):
                self.setUp();self.ready(action)
                self.saved(retry_after={action+':7':self.rpc.now+3600})
                before=self.path.read_bytes()
                with patch('keeper.monitor.subprocess.run') as signer:rows=self.f.rows(simulate=True)
                signer.assert_not_called();self.assertEqual(before,self.path.read_bytes())
                row=rows[action]
                self.assertEqual(('not_due',['confirmed_revert_retry']),(row['state'],row['reasons']))
                self.assertEqual('not_requested',row['simulation']['state'])
                retry=row['checks']['local_retry']
                self.assertTrue(retry['available']);self.assertEqual('waiting',retry['state'])
                self.assertEqual(self.rpc.now+3600,retry['retry_after'])
                self.assertEqual(3600,retry['remaining_seconds'])
                self.assertEqual('matching_local_journal',retry['source'])
                if action!='harvest':self.assertEqual('simulated',rows['harvest']['state'])

    def test_expired_retry_and_exact_boundary_allow_existing_review(self):
        for action in ('harvest','compound','rebalance'):
            for offset in (-1,0):
                with self.subTest(action=action,offset=offset):
                    self.setUp();self.ready(action)
                    self.saved(retry_after={action+':7':self.rpc.now+offset})
                    row=self.f.rows(simulate=True)[action]
                    self.assertEqual('simulated',row['state'])
                    self.assertEqual('elapsed',row['checks']['local_retry']['state'])
                    self.assertEqual(0,row['checks']['local_retry']['remaining_seconds'])

    def test_missing_journal_retry_is_unavailable_never_guessed_zero(self):
        self.path.unlink();before=list(self.path.parent.iterdir())
        rows=self.f.rows(simulate=True)
        for row in rows.values():
            retry=row['checks']['local_retry']
            self.assertFalse(retry['available']);self.assertEqual('unavailable',retry['state'])
            self.assertIsNone(retry['retry_after']);self.assertIsNone(retry['remaining_seconds'])
            self.assertEqual('journal_unavailable',retry['source'])
        self.assertEqual(before,list(self.path.parent.iterdir()));self.assertFalse(self.path.exists())

    def test_matching_empty_journal_is_explicitly_no_retry_record(self):
        rows=self.f.rows()
        for action,row in rows.items():
            retry=row['checks']['local_retry']
            self.assertTrue(retry['available']);self.assertEqual('not_recorded',retry['state'])
            self.assertEqual(action+':7',retry['action_key'])
            self.assertIsNone(retry['retry_after']);self.assertIsNone(retry['remaining_seconds'])

    def test_other_bucket_and_action_retry_do_not_leak_into_selected_action(self):
        self.saved(retry_after={'harvest:8':self.rpc.now+3600,'compound:7':self.rpc.now+7200})
        rows=self.f.rows()
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.assertEqual('not_recorded',rows['harvest']['checks']['local_retry']['state'])
        self.assertEqual('not_due',rows['compound']['state'])

    def test_pending_and_lifecycle_blockers_keep_priority_over_retry(self):
        for kind in ('pending','pause','exit','preparation'):
            with self.subTest(kind=kind):
                self.setUp();self.ready('rebalance')
                changes={'retry_after':{a+':7':self.rpc.now+3600 for a in ('harvest','compound','rebalance')}}
                if kind=='pending':
                    changes['pending']={'key':'harvest:7','nonce':0,'to':self.f.cfg['contracts']['vault'],
                        'data':calldata('collectFees(uint256,uint256)',7,self.rpc.now+180),
                        'value':0,'day':'2026-11-06','hash':None}
                elif kind=='pause':self.rpc.paused=1
                elif kind=='exit':self.rpc.exiting=1
                else:self.rpc.preparing=1
                self.saved(**changes)
                rows=self.f.rows(simulate=True)
                expected={'pending':'pending_recovery','pause':'paused','exit':'lp_exit_started','preparation':'preparation_active'}[kind]
                for action,row in rows.items():
                    if kind=='preparation' and action=='harvest':
                        self.assertEqual(['confirmed_revert_retry'],row['reasons'])
                    else:
                        self.assertEqual('blocked',row['state']);self.assertIn(expected,row['reasons'])
                        self.assertNotIn('confirmed_revert_retry',row['reasons'])
                    self.assertEqual('waiting',row['checks']['local_retry']['state'])
                    self.assertEqual('not_requested',row['simulation']['state'])

    def test_malformed_retry_or_mismatched_journal_rejected_before_rpc(self):
        original=self.path.read_bytes()
        variants=({'retry_after':{'harvest:7':True}},{'retry_after':{'harvest:7':-1}},
            {'retry_after':{'harvest:7':'1'}},{'retry_after':[]},
            {'chain_id':999},{'sender':'0x'+'ff'*20})
        for change in variants:
            with self.subTest(change=change):
                self.path.write_bytes(original);self.saved(**change)
                before=self.path.read_bytes();self.rpc.rpc_calls.clear()
                with self.assertRaises(ValueError):self.f.read()
                self.assertEqual([],self.rpc.rpc_calls);self.assertEqual(before,self.path.read_bytes())

    def test_retry_diagnostic_adds_no_rpc_and_never_checks_nonce_or_sends(self):
        self.f.rows();baseline=copy.deepcopy(self.rpc.rpc_calls)
        self.rpc.rpc_calls.clear()
        self.saved(retry_after={'harvest:7':self.rpc.now+3600})
        self.f.rows();self.assertEqual(baseline,self.rpc.rpc_calls)
        self.assertFalse(any('TransactionCount' in method or 'send' in method for method,_ in self.rpc.rpc_calls))


if __name__=='__main__':unittest.main()
