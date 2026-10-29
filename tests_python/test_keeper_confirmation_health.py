"""Policy-only keeper admission/health with inert RPC; no signer or network."""
import copy
import datetime as dt
import json
import unittest
from unittest.mock import patch

from keeper.health import HEALTH_SCHEMA, execution_reasons, observe_confirmation_health, summary
from keeper.monitor import Keeper
from keeper.ops import digest, health_check, preflight
from tests_python import test_keeper_rebalance_confirmation as fixtures
from tests_python import test_keeper as basic
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


class KeeperConfirmationHealthTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.KeeperConfirmationTests('runTest')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.cfg, self.rpc = self.f.cfg, self.f.rpc
        self.cfg.update(reviewed_for_live_use=True,receipt_fee_policy='included')
        for role in self.cfg['contracts']:
            self.cfg['code_hashes'].setdefault(role,self.f.f.pin)
        self.k = Keeper(self.cfg,rpc=self.rpc)
        self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':basic.H,'timestamp':self.rpc.now,'nonce':6}
        self.k.save()
        # All buckets remain inside the hard cooldown and idle compounding is off.
        self.f.base.group_words[6]=self.rpc.now-1
        self.assertNotEqual(1,self.cfg.get('execution_quality_version',0))

    def observe(self, previous=None):
        before=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            report=observe_confirmation_health(self.k,previous)
        signer.assert_not_called(); self.assertEqual(before,self.k.path.read_bytes())
        return report

    def data(self, report):
        return {'health_schema':HEALTH_SCHEMA,'rebalance_confirmation_health':{
            'version':1,'check_interval_seconds':240,'policy':report}}

    def reasons(self, data):
        return execution_reasons(data,self.cfg,now=self.rpc.now,max_age=1800)

    def ready_health(self,report):
        stamp=dt.datetime.fromtimestamp(self.rpc.now,dt.timezone.utc).isoformat()
        return {**self.data(report),'time':stamp,'last_success_at':stamp,'chain_id':self.k.chain,
            'sender':self.k.sender,'status':'dry_run_v2','live':False,'configuration_sha256':digest(self.cfg),
            'pending':False,'strategy_paused':False,'preparation_active':False,'canonical_state':0,
            'confirmed_reverts':0,'active_revert_cooldowns':0,'next_revert_retry_after':None,
            'skipped_buckets':0,'blocked_actions':0,'consecutive_failures':0}

    def test_schema_alone_cannot_approve_confirmation_with_quality_zero(self):
        self.assertIn('confirmation_observation_unknown',self.reasons({'health_schema':HEALTH_SCHEMA}))

    def test_fresh_policy_binds_latest_anchor_runtime_and_helpers_without_candidate_or_oracle_reads(self):
        report=self.observe(); observation=report['last_observed']
        self.assertEqual('observed_this_cycle',report['state'])
        self.assertEqual('latest_canonical_policy_only_not_continuous_evidence',observation['anchor_scope'])
        self.assertEqual(100,observation['block_number']);self.assertEqual(basic.H,observation['block_hash'])
        self.assertEqual(self.f.budget,observation['validated_bindings']['vault_budget'])
        self.assertIn('idle_compounding_budget',observation['runtime_code_hashes'])
        self.assertEqual([],self.reasons(self.data(report)))
        calls=[params[0]['data'] for method,params in self.rpc.calls if method=='eth_call']
        for signature in ('condition(uint256)','observations(uint256)','rebalanceReady(uint256)'):
            self.assertNotIn(calldata(signature,7),calls)

    def test_preflight_checks_budget_capability_under_cooldown_with_compounding_off(self):
        before=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            result=preflight(self.cfg,rpc=self.rpc)
        signer.assert_not_called();self.assertTrue(result['ok'],result['reasons'])
        self.f.bad[self.f.budget,calldata('REBALANCE_CONFIRMATION_VERSION()')]=fixtures.words(0)
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('subprocess.run') as signer:
            result=preflight(self.cfg,rpc=self.rpc)
        signer.assert_not_called();self.assertFalse(result['ok'])
        self.assertIn('rebalance_confirmation_unavailable',result['reasons'])
        self.assertEqual(before,self.k.path.read_bytes())

    def test_wrong_budget_binding_and_runtime_refuse_fresh_health(self):
        self.f.bad[self.f.budget,calldata('vault()')]=fixtures.words(basic.A)
        self.assertEqual('unavailable',self.observe()['state'])
        self.f.bad.clear(); original=self.rpc.call
        def wrong(method,params):
            if method=='eth_getCode' and params[0]==self.f.budget:return '0x6001'
            return original(method,params)
        self.rpc.call=wrong
        self.assertEqual('unavailable',self.observe()['state'])

    def test_failed_read_retains_old_policy_explicitly_stale_without_secret_text(self):
        good=self.observe()
        self.f.bad[self.f.budget,calldata('vault()')]=RpcError('https://secret.invalid/DO-NOT-EXPORT')
        report=self.observe(good)
        self.assertEqual('unavailable',report['state'])
        self.assertEqual(good['last_observed'],report['last_observed'])
        self.assertNotIn('DO-NOT-EXPORT',json.dumps(report))
        self.assertIn('confirmation_observation_not_current',self.reasons(self.data(report)))

    def test_canonical_anchor_change_refuses_policy_record(self):
        original=self.rpc.call
        def reorg(method,params):
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]=='0x64':
                return {**result,'hash':'0x'+'cd'*32}
            return result
        self.rpc.call=reorg
        self.assertEqual('unavailable',self.observe()['state'])

    def test_loaded_config_mutation_is_not_relabelled_as_fresh_policy(self):
        self.cfg['max_transaction_cost_wei']+=1
        self.assertEqual('unavailable',self.observe()['state'])

    def test_policy_future_timestamp_cannot_pass_preflight_observation(self):
        original=self.rpc.call
        def future(method,params):
            result=original(method,params)
            if method=='eth_getBlockByNumber':return {**result,'timestamp':hex(self.rpc.now+31)}
            return result
        self.rpc.call=future
        self.assertEqual('unavailable',self.observe()['state'])

    def test_health_rejects_stale_future_and_malformed_policy_fields(self):
        good=self.data(self.observe())
        for field,value,reason in (
                ('block_timestamp',self.rpc.now-601,'confirmation_observation_stale_or_future'),
                ('observed_at_unix',self.rpc.now+31,'confirmation_observation_read_stale_or_future'),
                ('block_number',True,'confirmation_observation_anchor_invalid'),
                ('policy_revision',True,'confirmation_observation_policy_invalid'),
                ('duration_seconds',True,'confirmation_observation_policy_invalid'),
                ('maximum_gap_seconds',True,'confirmation_observation_policy_invalid'),
                ('version',True,'confirmation_observation_policy_invalid'),
                ('review_hash','0x'+'0'*64,'confirmation_observation_policy_invalid'),
                ('configuration_sha256','bad','confirmation_observation_configuration_mismatch'),
                ('source_files_sha256',{},'confirmation_observation_source_mismatch')):
            bad=copy.deepcopy(good);bad['rebalance_confirmation_health']['policy']['last_observed'][field]=value
            with self.subTest(field=field):self.assertIn(reason,self.reasons(bad))

    def test_health_requires_budget_pin_binding_and_nonboolean_capability(self):
        good=self.data(self.observe())
        for field,value,reason in (
                ('runtime_code_hashes',{},'confirmation_observation_runtime_mismatch'),
                ('validated_bindings',{},'confirmation_observation_bindings_invalid'),
                ('validated_capabilities',{'strategy':True,'rebalance_confirmation':1,'idle_compounding_budget':1},
                    'confirmation_observation_bindings_invalid')):
            bad=copy.deepcopy(good);bad['rebalance_confirmation_health']['policy']['last_observed'][field]=value
            with self.subTest(field=field):self.assertIn(reason,self.reasons(bad))

    def test_gap_zero_is_truthful_stop_in_health_and_preflight(self):
        self.f.gap=0;report=self.observe()
        self.assertEqual('stopped',report['state'])
        self.assertIn('rebalance_confirmation_stopped',self.reasons(self.data(report)))
        self.assertEqual('stopped',summary(self.data(report))['confirmation_policy_state'])
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):result=preflight(self.cfg,rpc=self.rpc)
        self.assertIn('rebalance_confirmation_stopped',result['reasons'])

    def test_terminal_exit_suppresses_only_stop_or_cadence_reason_with_explicit_boolean(self):
        for gap,reason in ((0,'rebalance_confirmation_stopped'),(239,'rebalance_confirmation_cadence_incompatible')):
            self.f.gap=gap;data=self.data(self.observe())
            for flag in (False,None,1):
                with self.subTest(gap=gap,flag=flag):
                    self.assertIn(reason,self.reasons({**data,'lp_exit_started':flag}))
            terminal={**data,'lp_exit_started':True}
            self.assertEqual([],self.reasons(terminal))
            terminal['rebalance_confirmation_health']['policy']['last_observed']['validated_bindings']={}
            self.assertIn('confirmation_observation_bindings_invalid',self.reasons(terminal))

    def test_health_check_cannot_approve_only_schema_and_success_status(self):
        good=self.ready_health(self.observe());self.k.health_path.write_text(json.dumps(good))
        self.assertTrue(health_check(self.cfg,allow_dry_run=True,now=self.rpc.now)['ok'])
        good['rebalance_confirmation_health'].pop('policy');self.k.health_path.write_text(json.dumps(good))
        report=health_check(self.cfg,allow_dry_run=True,now=self.rpc.now)
        self.assertFalse(report['ok']);self.assertIn('confirmation_observation_unknown',report['reasons'])

    def test_subcadence_gap_is_degraded_before_bucket_cooldown_elapses(self):
        self.f.gap=239;report=self.observe()
        self.assertEqual('incompatible_cadence',report['state'])
        self.assertIn('rebalance_confirmation_cadence_incompatible',self.reasons(self.data(report)))
        with patch('keeper.monitor.time.time',return_value=self.rpc.now):result=preflight(self.cfg,rpc=self.rpc)
        self.assertIn('rebalance_confirmation_cadence_incompatible',result['reasons'])

    def test_preflight_pending_does_not_read_new_confirmation_dependencies(self):
        self.k.state['pending']={'key':'harvest:7','nonce':7,'to':self.cfg['contracts']['vault'],
            'data':calldata('collectFees(uint256,uint256)',7,self.rpc.now+100),'value':0,
            'day':'2026-10-28','hash':basic.H};self.k.save();before=self.k.path.read_bytes()
        with patch('keeper.monitor.time.time',return_value=self.rpc.now), \
                patch('keeper.rebalance_confirmation.RebalanceConfirmation.validate',side_effect=AssertionError('Recovery first')) as read:
            result=preflight(self.cfg,rpc=self.rpc)
        read.assert_not_called();self.assertEqual(before,self.k.path.read_bytes())
        self.assertEqual('pending_recovery',result['rebalance_confirmation_policy']['state'])
        self.assertIn('pending_intent_requires_reconciliation',result['reasons'])

    def test_summary_cannot_echo_arbitrary_confirmation_state(self):
        self.assertEqual('unknown',summary({'rebalance_confirmation_health':
            {'policy':{'state':'https://secret.invalid/DO-NOT-EXPORT'}}})['confirmation_policy_state'])


if __name__=='__main__':unittest.main()
