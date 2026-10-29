"""Confirmation incident boundaries and reset gas conservation; inert RPC only."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, CONFIRMATION_CLEARS, CONFIRMATION_RESETS, CONFIRMATION_STATE
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError
from tests_python import test_keeper_rebalance_confirmation as fixtures


class KeeperConfirmationIncidentTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperConfirmationTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.k,self.rpc,self.cfg=self.f.k,self.f.rpc,self.f.cfg
        self.k._confirmation_seen_buckets.add(7)

    def _cycle(self):
        self.f.k=self.k
        return self.f.cycle()

    def _ack(self,awaiting=True):
        record={'number':98,'hash':fixtures.basic.H,'timestamp':self.rpc.now-1800,
            'nonce':6,'awaiting_healthy_read':awaiting}
        self.k.state[CONFIRMATION_CLEARS]={'7':record}
        return copy.deepcopy(record)

    def _jitter(self):
        self.k.state[CONFIRMATION_STATE]={'7':dict(identity=fixtures.basic.H,observed_at=self.rpc.now,
            last_checked_at=self.rpc.now,next_check_at=self.rpc.now+300,execute_after=self.rpc.now+60)}

    def _signer_context(self):
        self.k.live=True;self.k.cast='/inert/cast';self.k.keystore=Path('/inert/key');self.k.password=Path('/inert/pass')
        self.k.fee_policy='included';self.k.state['next_nonce']=7

    def _failed_receipt(self,key,signature,args,to):
        fixture=fixtures.basic.KeeperTests('runTest');fixture.k=self.k;fixture.rpc=self.rpc
        self.k.state['next_nonce']=7;fixture.receipt(False)
        pending=self.k.state['pending'];data=calldata(signature,*args)
        pending.update(key=key,to=to,data=data,value=0)
        pending['fee_review']['maximum_cost_wei']=517
        self.rpc.tx.update(to=to,input=data,value='0x0');self.rpc.receipt['to']=to

    def test_unrelated_compound_reserve_fault_does_not_reset_confirmed_window(self):
        self.k.maintenance.update(compound=True,compound_thresholds={currency:1 for currency in
            self.k._bucket(7)[1]})
        self.f.record=[self.f.identity,self.rpc.now-600,self.rpc.now-100,1]
        original=self.k.view
        def view(name,signature,*args):
            if signature=='compoundBalance(uint256,address)':raise RpcError('inert compound reserve outage')
            return original(name,signature,*args)
        with patch.object(self.k,'view',side_effect=view),patch.object(self.k,'submit',return_value=False), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now):self.k.cycle()
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))

    def test_unrelated_router_metadata_fault_does_not_invalidate_price_observations(self):
        self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now-100,1]
        self.k.maintenance['harvest']=True
        with patch.object(self.k,'_validate_lp_routing',side_effect=RpcError('inert router metadata outage')):
            self._cycle().assert_called_once_with('vault','collectFees(uint256,uint256)',
                (7,self.rpc.now+180),'harvest:7')
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))
        self.assertNotEqual([0,0,0,0],self.f.record)

    def test_postmaintenance_health_read_failure_does_not_clear_a_healthy_jitter(self):
        self._jitter();before=copy.deepcopy(self.k.state)
        with patch.object(self.k,'cycle',return_value=None), \
                patch.object(self.k,'_observe_revert_cooldowns',side_effect=RpcError('inert health clock outage')):
            self.assertFalse(self.k.run_cycle())
        self.assertEqual(before,self.k.state)

    def test_unrelated_pending_receipt_fault_preserves_journal_without_reset(self):
        self.k.state['pending']={'key':'harvest:7','to':self.cfg['contracts']['vault'],
            'data':calldata('collectFees(uint256,uint256)',7,self.rpc.now+180)}
        self.k.save();before=self.k.path.read_bytes()
        with patch.object(self.k,'poll_pending',side_effect=RpcError('inert receipt outage')):
            self.assertFalse(self.k.run_cycle())
        self.assertFalse(self.k._confirmation_recovery_interrupted)
        self.assertEqual(before,self.k.path.read_bytes())

    def test_genuine_raw_clock_retreat_requires_reset_and_discards_old_jitter(self):
        self._jitter();self.rpc.now-=1
        # Priority now detects the shared clock fault before optional queues,
        # so the complete cycle must fail rather than defer only this bucket.
        with patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                patch.object(self.k,'submit') as submit,self.assertRaises(RpcError):
            self.k.cycle()
        submit.assert_not_called()
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))

    def test_same_persistent_fault_after_clear_does_not_pay_for_another_reset(self):
        self._ack();self._jitter()
        self.f.bad[self.f.helper,calldata('condition(uint256)',7)]=RpcError('inert persistent price outage')
        for _ in range(3):
            self._cycle().assert_not_called();self.rpc.now+=60
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))
        self.assertTrue(self.k.state[CONFIRMATION_CLEARS]['7']['awaiting_healthy_read'])
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):self.k.run_cycle()
        health=json.loads(self.k.health_path.read_text())
        self.assertEqual(['7'],health['rebalance_confirmation_health']['awaiting_healthy_read_buckets'])

    def test_recovered_empty_record_allows_new_samples_without_duplicate_clear(self):
        self._ack()
        self._cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        self.assertFalse(self.k.state[CONFIRMATION_CLEARS]['7']['awaiting_healthy_read'])
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))

    def test_foreign_candidate_on_first_recovered_read_requires_another_clear(self):
        self._ack();self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now-100,1]
        self._cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])

    def test_restart_preserves_clear_ack_and_does_not_resend_a_known_empty_clear(self):
        self._ack();self.k.save();self.k=Keeper(self.cfg,rpc=self.rpc)
        self.f.bad[self.f.helper,calldata('condition(uint256)',7)]=RpcError('inert persistent outage')
        self._cycle().assert_not_called()
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}))
        self.assertTrue(self.k.state[CONFIRMATION_CLEARS]['7']['awaiting_healthy_read'])

    def test_ambiguous_new_observe_atomically_invalidates_the_old_clear_ack(self):
        self._ack(False);self._signer_context();self.k.save()
        def signer(*args,**kwargs):
            stored=json.loads(self.k.path.read_text())
            self.assertNotIn('7',stored.get(CONFIRMATION_CLEARS,{}))
            self.assertEqual('rebalance_observation:7',stored['pending']['key'])
            raise subprocess.TimeoutExpired('inert signer',1)
        with patch.object(self.k,'_validate_checkpoint'),patch.object(self.k,'_validate_code_hashes'), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                patch('keeper.monitor.subprocess.run',side_effect=signer),self.assertRaises(subprocess.TimeoutExpired):
            self.k.submit('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_CLEARS,{}))
        self.assertIsNone(self.k.state['pending']['hash'])

    def test_failed_observe_intent_save_preserves_clear_ack_and_never_signs(self):
        self._ack(False);self._signer_context();self.k.save();before=self.k.path.read_bytes();state=copy.deepcopy(self.k.state)
        with patch.object(self.k,'_validate_checkpoint'),patch.object(self.k,'_validate_code_hashes'), \
                patch.object(self.k,'save',side_effect=OSError('inert storage failure')), \
                patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('keeper.monitor.subprocess.run') as signer, \
                self.assertRaises(OSError):
            self.k.submit('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        signer.assert_not_called();self.assertEqual(before,self.k.path.read_bytes());self.assertEqual(state,self.k.state)

    def test_restarted_or_changed_confirmed_window_gets_new_jitter_not_old_expired_timer(self):
        self.f.record=[self.f.identity,self.rpc.now-1800,self.rpc.now-100,1]
        with patch('keeper.monitor.secrets.randbelow',return_value=0):self._cycle().assert_called_once()
        old=self.f.schedule();self.rpc.now+=60
        self.f.identity+=1;self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now-100,1]
        with patch('keeper.monitor.secrets.randbelow',return_value=540):
            self._cycle().assert_called_once_with('rebalance_confirmation','observe(uint256)',(7,),'rebalance_observation:7')
        self.assertNotEqual(old['identity'],self.f.schedule()['identity'])
        self.assertEqual(self.rpc.now+600,self.f.schedule()['execute_after'])

    def test_clear_ack_shape_and_bucket_inventory_are_strict_on_restore(self):
        good=self._ack();self.k.save()
        for value in (dict(good,nonce=True),dict(good,awaiting_healthy_read=1),dict(good,extra=1),
                dict(good,hash='0x00')):
            self.k.state[CONFIRMATION_CLEARS]={'7':value};self.k.save()
            with self.subTest(value=value),self.assertRaises((ValueError,RpcError)):Keeper(self.cfg,rpc=self.rpc)

    def test_fresh_confirmation_requires_an_explicit_compatible_outer_poll(self):
        for value in (None,True,False,'60',59,241,300,301,600):
            config=copy.deepcopy(self.cfg)
            if value is None:config.pop('interval_seconds')
            else:config['interval_seconds']=value
            with self.subTest(value=value),patch.object(self.rpc,'call') as rpc,self.assertRaisesRegex(ValueError,'interval_seconds'):
                Keeper(config,rpc=self.rpc)
            rpc.assert_not_called()
        for value in (60,240):
            config=copy.deepcopy(self.cfg);config['interval_seconds']=value
            with self.subTest(value=value):self.assertEqual(1,Keeper(config,rpc=self.rpc).rebalance_confirmation.version)

    def test_failed_observation_receipt_blocks_a_still_fresh_mature_window(self):
        self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now,1];self._jitter()
        self._failed_receipt('rebalance_observation:7','observe(uint256)',(7,),self.f.helper)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):self.assertFalse(self.k.poll_pending())
        self.assertTrue(self.f.ready());self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7'])
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))
        self.assertEqual(8,self.k.state['next_nonce']);self.assertGreater(sum(self.k.state['spent'].values()),0)
        self._cycle().assert_called_once_with('rebalance_confirmation','resetObservation(uint256)',(7,),'rebalance_reset:7')

    def test_failed_rebalance_receipt_atomically_invalidates_its_old_jitter(self):
        self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now,1];self._jitter()
        self._failed_receipt('rebalance:7','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),self.cfg['contracts']['vault'])
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):self.assertFalse(self.k.poll_pending())
        self.assertTrue(self.k.state[CONFIRMATION_RESETS]['7']);self.assertIsNone(self.k.state['pending'])
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_STATE,{}))

    def test_unrelated_failed_harvest_receipt_preserves_confirmation_and_gas_accounting(self):
        self.f.record=[self.f.identity,self.rpc.now-900,self.rpc.now,1];self._jitter()
        expected=copy.deepcopy(self.k.state[CONFIRMATION_STATE])
        self._failed_receipt('harvest:7','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),self.cfg['contracts']['vault'])
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):self.assertFalse(self.k.poll_pending())
        self.assertNotIn('7',self.k.state.get(CONFIRMATION_RESETS,{}));self.assertEqual(expected,self.k.state[CONFIRMATION_STATE])
        self.assertEqual(8,self.k.state['next_nonce']);self.assertGreater(sum(self.k.state['spent'].values()),0)

    def test_full_reset_inventory_preserves_failed_transaction_for_reconciliation(self):
        self._failed_receipt('rebalance_observation:7','observe(uint256)',(7,),self.f.helper)
        self.k.state[CONFIRMATION_RESETS]={'8':True};self.k.max_buckets=1;self.k.save()
        before=copy.deepcopy(self.k.state);disk=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),self.assertRaisesRegex(RpcError,'reset inventory is full'):
            self.k.poll_pending()
        self.assertEqual(before,self.k.state);self.assertEqual(disk,self.k.path.read_bytes())


if __name__=='__main__':unittest.main()
