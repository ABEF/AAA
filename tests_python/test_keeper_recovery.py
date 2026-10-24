import copy
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from keeper.monitor import Keeper, error_context
from tests_python.test_keeper import FakeRpc, A, B, H
from zzz_ops.rpc import RpcError

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.cfg={'chain_id':1,'sender':A,'contracts':{k:B for k in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'state_path':str(Path(self.tmp.name)/'state.json'),'confirmations':2,
            'max_gas_limit':100000,'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,'max_daily_cost_wei':10000000}
        self.rpc=FakeRpc();self.k=Keeper(self.cfg,rpc=self.rpc)
        quiet=patch('keeper.monitor.log');quiet.start();self.addCleanup(quiet.stop)

    def test_live_missing_state_fails_before_signer_or_rpc(self):
        with patch.object(Keeper,'_validate_signer') as signer:
            with self.assertRaisesRegex(ValueError,'Live state is missing'):Keeper(self.cfg,live=True,rpc=self.rpc)
            signer.assert_not_called();self.assertEqual(self.rpc.calls,[])

    def test_corrupt_counters_cannot_reset_budget(self):
        baseline=copy.deepcopy(self.k.state)
        for values in ({'spent':{'2026-10-16':-1}},{'last':None},{'pending':{}},{'next_nonce':-1}):
            self.k.state=copy.deepcopy(baseline)
            self.k.state.update(values);self.k.save()
            with self.subTest(values=values),self.assertRaises((ValueError,TypeError,KeyError)):Keeper(self.cfg,rpc=self.rpc)

    def test_health_path_cannot_overwrite_recovery_or_lock(self):
        for path in (self.cfg['state_path'],'var/keeper.lock'):
            with self.subTest(path=path),self.assertRaises(ValueError):Keeper({**self.cfg,'health_path':path},rpc=self.rpc)

    def test_used_signer_cannot_initialize(self):
        self.cfg['reviewed_for_live_use']=True
        with patch.object(self.k,'_validate_code_hashes'):
            with self.assertRaisesRegex(ValueError,'Used keeper'):self.k.initialize_state()
        self.assertFalse(self.k.path.exists())

    def test_unused_signer_explicit_bootstrap_and_no_overwrite(self):
        self.cfg['reviewed_for_live_use']=True
        original=self.rpc.call
        def call(method,params):return '0x0' if method=='eth_getTransactionCount' else original(method,params)
        with patch.object(self.k,'_validate_code_hashes'),patch.object(self.rpc,'call',side_effect=call):
            self.k.initialize_state()
            with self.assertRaises(ValueError):self.k.initialize_state()
        self.assertEqual(json.loads(self.k.path.read_text())['next_nonce'],0)

    def test_legacy_state_without_nonce_blocks_live_start(self):
        self.cfg['reviewed_for_live_use']=True;self.k.save()
        with self.assertRaisesRegex(ValueError,'nonce checkpoint'):Keeper(self.cfg,live=True,rpc=self.rpc)

    def test_nonce_drift_pending_unknown_or_low_balance_never_signs(self):
        self.k.live=True;self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':H,'timestamp':self.rpc.now,'nonce':6}
        self.k._validate_code_hashes=lambda:None
        original=self.rpc.call
        cases=[('eth_getTransactionCount','pending','0x8'),('eth_getTransactionCount','latest','0x8'),('eth_getBalance','latest','0x0')]
        for target,tag,value in cases:
            def call(method,params):return value if method==target and params[-1]==tag else original(method,params)
            with self.subTest(target=target,tag=tag),patch.object(self.rpc,'call',side_effect=call),patch('subprocess.run') as signer:
                with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1')
                signer.assert_not_called();self.assertIsNone(self.k.state['pending'])

    def test_restore_keeps_pending_counters_and_cursor(self):
        self.k.state.update(next_nonce=7,bucket_cursor=2,spent={'2026-10-16':100},last={'harvest:1':99},
            pending={'nonce':7,'value':0,'to':B,'key':'harvest:1','data':'0x12345678','day':'2026-10-16','hash':H})
        self.k.save();restored=Keeper(self.cfg,rpc=self.rpc)
        self.assertEqual(restored.state,self.k.state)
        with patch.object(restored,'submit') as submit:self.assertTrue(restored.poll_pending());submit.assert_not_called()

    def test_rpc_failure_health_and_recovery(self):
        with patch.object(self.k,'cycle',side_effect=RpcError('SECRET https://token@rpc.invalid')):
            self.assertFalse(self.k.run_cycle())
        health=json.loads(self.k.health_path.read_text());self.assertEqual(health['status'],'error')
        self.assertNotIn('SECRET',self.k.health_path.read_text());self.assertEqual(health['consecutive_failures'],1)
        with patch.object(self.k,'cycle'):self.assertTrue(self.k.run_cycle())
        health=json.loads(self.k.health_path.read_text());self.assertEqual(health['status'],'dry_run')
        self.assertEqual(health['consecutive_failures'],0);self.assertIsNotNone(health['last_success_at'])

    def test_skipped_bucket_is_degraded_and_pending_is_not_healthy(self):
        def skipped():self.k.skipped_buckets=1
        with patch.object(self.k,'cycle',side_effect=skipped):self.assertFalse(self.k.run_cycle())
        self.assertEqual(json.loads(self.k.health_path.read_text())['status'],'degraded')
        self.k.state['pending']={'hash':None}
        with patch.object(self.k,'cycle'):self.k.run_cycle()
        self.assertEqual(json.loads(self.k.health_path.read_text())['status'],'recovery_required')
        self.k.state['pending']['hash']=H
        with patch.object(self.k,'cycle'):self.k.run_cycle()
        self.assertEqual(json.loads(self.k.health_path.read_text())['status'],'awaiting_receipt')

    def test_health_storage_failure_stops_before_work(self):
        with patch('keeper.monitor.atomic_json',side_effect=OSError('disk full')),patch.object(self.k,'cycle') as cycle:
            with self.assertRaises(OSError):self.k.run_cycle()
            cycle.assert_not_called()

    def test_unexpected_failure_halts_instead_of_retrying(self):
        with patch.object(self.k,'cycle',side_effect=RuntimeError('SECRET')):
            with self.assertRaises(RuntimeError):self.k.run_cycle()
        self.assertEqual(json.loads(self.k.health_path.read_text())['status'],'halted')

    def test_safe_context_has_no_exception_content(self):
        try:raise ValueError('password SECRET')
        except ValueError as exc:details=error_context(exc)
        self.assertNotIn('SECRET',json.dumps(details));self.assertIn('test_safe_context',details['error_site'])

    def test_confirmed_checkpoint_reorg_blocks_all_work(self):
        self.k.state.update(next_nonce=7,receipt_anchor={'number':98,'hash':'0x'+'cd'*32,'timestamp':self.rpc.now,'nonce':6})
        self.k.save();before=self.k.path.read_bytes()
        with patch.object(self.k,'view') as view,patch('subprocess.run') as signer:
            self.assertFalse(self.k.run_cycle());signer.assert_not_called();view.assert_not_called()
        self.assertEqual(self.k.path.read_bytes(),before)

    def test_receipt_checkpoint_loss_blocks_used_live_signer(self):
        self.k.live=True;self.k.state['next_nonce']=7
        with self.assertRaisesRegex(RpcError,'Missing confirmed checkpoint'):self.k._validate_checkpoint()

    def test_pending_receipt_does_not_erase_a_reorged_prior_checkpoint(self):
        self.k.state.update(next_nonce=7,receipt_anchor={'number':98,'hash':'0x'+'cd'*32,'timestamp':self.rpc.now,'nonce':6},pending={'hash':H})
        before=copy.deepcopy(self.k.state)
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertEqual(before,self.k.state)

    def test_gas_cap_is_visible_as_degraded_health(self):
        self.cfg['max_gas_limit']=1
        with patch.object(self.k,'cycle',side_effect=lambda:self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1')):
            self.assertFalse(self.k.run_cycle())
        h=json.loads(self.k.health_path.read_text());self.assertEqual(h['status'],'degraded');self.assertEqual(h['blocked_actions'],1)

    def test_secret_paths_cannot_be_health_output(self):
        with self.assertRaises(ValueError):Keeper({**self.cfg,'keystore':self.cfg['state_path']},rpc=self.rpc)

    def test_malformed_gas_fields_never_sign(self):
        original=self.rpc.call
        for method in ('eth_estimateGas','eth_gasPrice'):
            for bad in ('-0x1','0x01',None,True,'0x'+'f'*65):
                def call(name,params):return bad if name==method else original(name,params)
                with self.subTest(method=method,bad=bad),patch.object(self.rpc,'call',side_effect=call),patch('subprocess.run') as signer:
                    with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1')
                    signer.assert_not_called()

    @unittest.skipUnless(os.name=='posix','Unix runtime ownership and permissions required')
    def test_runtime_permissions_and_symlinks_fail_closed(self):
        self.k.save();self.k._validate_runtime_files()
        self.k.path.chmod(0o644)
        with self.assertRaises(ValueError):self.k._validate_runtime_files()
        self.k.path.chmod(0o600)
        self.k.health_path.symlink_to(self.k.path)
        with self.assertRaises(ValueError):self.k._validate_runtime_files()
        self.k.health_path.unlink();self.k.path.parent.chmod(0o777)
        with self.assertRaises(ValueError):self.k._validate_runtime_files()
        self.k.path.parent.chmod(0o700)

    def test_invalid_fee_policy_and_cooldown_rejected(self):
        for config in ({'receipt_fee_policy':'unknown'},{'revert_cooldown_seconds':0},{'revert_cooldown_seconds':86401}):
            with self.subTest(config=config),self.assertRaises(ValueError):Keeper({**self.cfg,**config},rpc=self.rpc)

    def test_unqualified_network_fees_block_live_before_signer(self):
        self.k.state['next_nonce']=0;self.k.save();self.cfg['reviewed_for_live_use']=True
        with patch.object(Keeper,'_validate_signer') as signer:
            with self.assertRaisesRegex(ValueError,'fee accounting'):Keeper(self.cfg,live=True,rpc=self.rpc)
            signer.assert_not_called()

    def test_pending_intent_save_failure_never_invokes_signer(self):
        self.k.live=True;self.k.fee_policy='included';self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':H,'timestamp':self.rpc.now,'nonce':6}
        self.k._validate_code_hashes=lambda:None
        with patch.object(self.k,'save',side_effect=OSError('disk full')),patch('subprocess.run') as signer:
            with self.assertRaises(OSError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1')
            signer.assert_not_called();self.assertIsNotNone(self.k.state['pending'])

    def test_shutdown_during_preflight_stops_before_intent_and_signing(self):
        self.k.live=True;self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':H,'timestamp':self.rpc.now,'nonce':6}
        self.k._validate_code_hashes=lambda:None
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_getBalance':self.k.stop_requested=lambda:True
            return result
        with patch.object(self.rpc,'call',side_effect=call),patch('subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'harvest:1'))
            signer.assert_not_called();self.assertIsNone(self.k.state['pending'])
