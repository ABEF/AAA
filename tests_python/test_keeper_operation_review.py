"""Offline fixed-action reports: no signer, operating journal or public RPC."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper import ops
from keeper.monitor import Keeper, NATIVE_ASSET
from keeper.operation_review import review
from tests_python import test_keeper_compound_range_policy as physical
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class ReportRPC(physical.PhysicalTranscript):
    def __init__(self, path):
        super().__init__(path)
        self.contracts.update(balancing_router='0x'+'b1'*20, rebalance_confirmation='0x'+'b2'*20)
        self.budget='0x'+'b3'*20
        self.cfg.update(lp_routing_version=1, execution_quality_version=1, rebalance_confirmation_version=2,
            idle_compounding_budget=self.budget, interval_seconds=240, l1_fee_allowance_wei=0,
            rpc_urls=['https://PRIVATE-ENDPOINT.invalid'], reviewed_for_live_use=True)
        self.cfg['code_hashes'].update(balancing_router=self.pin, rebalance_confirmation=self.pin, idle_compounding_budget=self.pin)
        self.cfg['maintenance'].update(compound=True, compound_thresholds={NATIVE_ASSET:1,self.zzz:1})
        self.cfg['lock_path']=str(Path(path).with_suffix('.lock'))
        self.config[8:11]=[100,100,200]
        self.config[12:14]=[5*10**18,1000000*10**18]
        self.position[6]=self.now-50000
        self.gap=300; self.duration=900; self.record=(0,0,0,0); self.reference=2
        self.paused=self.preparing=self.exiting=0; self.authorized=1
        self.reserves=(1,0); self.compound_ready=1; self.estimate=30000; self.price=2
        self.simulation_error=None; self.estimate_error=None; self.fail_raw=False; self.change_journal=None
        self.rpc_calls=[]; self.catalog_count=1
        self.balance=10**18;self.balance_error=None

    def raw(self):
        return int(self.now>=self.position[6]+43200 and (not self.lower<=self.tick<self.upper or self.manual))

    def sample(self):
        side=1 if self.tick<self.lower else 2 if self.tick>=self.upper else 0
        condition=side if self.raw() and not self.manual and side==self.reference else 0
        identity=1 if condition else 0
        old,first,last,prior_side=self.record
        ready=bool(self.manual and self.raw() or self.gap and condition and old==identity and prior_side==condition and first and self.now-last<=self.gap and self.now-first>=self.duration)
        return condition,identity,ready

    def call(self, method, params):
        self.rpc_calls.append((method,copy.deepcopy(params)))
        if method=='eth_chainId':return 1
        if method=='eth_gasPrice':return hex(self.price)
        if method=='eth_getBalance':
            if self.balance_error:raise self.balance_error
            return hex(self.balance)
        if method=='eth_estimateGas':
            if self.estimate_error:raise self.estimate_error
            return hex(self.estimate)
        if method=='eth_call' and 'from' in params[0]:
            if self.simulation_error:raise self.simulation_error
            return '0x'
        if method=='eth_call':
            c=self.contracts;data=params[0]['data'];target=params[0]['to']
            values={calldata('ACCOUNTING_VERSION()'):4,calldata('FEE_INTAKE_VERSION()'):1,
                calldata('CUSTODY_VERSION()'):3,calldata('lpExitStarted()'):self.exiting,
                calldata('exitPhase()'):1 if self.exiting else 0,calldata('paused()'):self.paused,
                calldata('preparationActive()'):self.preparing,calldata('canonicalState()'):0,
                calldata('isSealed()'):1,calldata('keeperAuthorized(address)',self.cfg['sender']):self.authorized,
                calldata('bucketTotalShares(uint256)',7):100,calldata('migrationBudget()'):int(self.budget,16),
                calldata('IDLE_COMPOUNDING_VERSION()'):3,calldata('vault()'):int(c['vault'],16),
                calldata('lastCompound(uint256)',7):self.now-7200,
                calldata('compoundInterval(bytes32)',self.pool):3600,
                calldata('compoundReady(uint256)',7):self.compound_ready,calldata('maintenanceLossBps()'):300,
                calldata('LP_ROUTING_VERSION()'):1,calldata('EXECUTION_QUALITY_VERSION()'):1,
                calldata('balancingRouter()'):int(c['balancing_router'],16),
                calldata('liquidityManager()'):int(c['liquidity'],16),calldata('executionRevision()'):1,
                calldata('configurationRevision()'):1,calldata('searchIterations()'):8,
                calldata('quoteGasLimit()'):200000,calldata('executionPoolCount()'):self.catalog_count,
                calldata('MAX_EXECUTION_POOLS()'):4,calldata('executionPoolAt(uint256)',0):int(self.pool,16),
                calldata('MAX_ADDITIONAL_LOSS_BPS()'):1000,calldata('additionalLossBps()'):100,
                calldata('executionQualityRevision()'):1,calldata('rebalanceConfirmation()'):int(c['rebalance_confirmation'],16),
                calldata('REBALANCE_CONFIRMATION_VERSION()'):2,calldata('strategy()'):int(c['strategy'],16),
                calldata('duration()'):self.duration,calldata('maxObservationGap()'):self.gap,
                calldata('policyRevision()'):1,calldata('reviewHash()'):1,
                calldata('requireReferenceExit()'):1,calldata('referenceReviewHash()'):0}
            for role,label in (('principal_exit','ZZZMigration'),):
                values[calldata('module(bytes32)','0x'+keccak256(label.encode()).hex())]=int(c[role],16)
            if data==calldata('needsRebalance(uint256)',7):
                if self.fail_raw:raise RpcError('PRIVATE-ENDPOINT secret price failure')
                return '0x'+f'{self.raw():064x}'
            side,identity,ready=self.sample()
            arrays={calldata('condition(uint256)',7):(side,identity,int(bool(self.manual and self.raw()))),
                calldata('observations(uint256)',7):self.record,
                calldata('marketSides(uint256)',7):(1 if self.tick<self.lower else 2,self.reference)}
            values[calldata('ready(uint256)',7)]=values[calldata('rebalanceReady(uint256)',7)]=int(ready)
            for token,amount in zip((NATIVE_ASSET,self.zzz),self.reserves):
                native='0x'+keccak256(b'compoundBalance(uint256,address)').hex()[:8]+f'{7:064x}{int(token,16):064x}'
                values[native]=amount
            if data in arrays:return '0x'+''.join(physical.words(*arrays[data]))
            if data in values:return '0x'+f'{values[data]:064x}'
        result=super().call(method,params)
        if method=='eth_getBlockByNumber' and self.change_journal and params[0]=='latest':
            self.change_journal()
        return result


class KeeperOperationReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.json';self.rpc=ReportRPC(self.path);self.cfg=self.rpc.cfg
        Keeper(self.cfg,rpc=self.rpc).save()

    def read(self, *, simulate=False):
        return review(self.cfg,[7],rpc=self.rpc,simulate=simulate,now=lambda:self.rpc.now)

    def rows(self, **kwargs):return {r['operation']:r for r in self.read(**kwargs)['operations']}

    def test_inside_observation_is_not_needed_while_independent_work_is_eligible(self):
        report=self.read();rows={r['operation']:r for r in report['operations']}
        self.assertEqual(2,report['profile']['rebalance_confirmation_version'])
        self.assertEqual(1,report['profile']['fee_intake_version'])
        self.assertEqual('not_needed',rows['rebalance']['state'])
        self.assertEqual('observed_eligible',rows['compound']['state'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])

    def test_report_never_writes_signs_reconciles_or_acquires_lock(self):
        before=self.path.read_bytes()
        with patch('subprocess.run') as signer,patch.object(Keeper,'submit',side_effect=AssertionError),\
                patch.object(Keeper,'poll_pending',side_effect=AssertionError),patch('zzz_ops.state.process_lock',side_effect=AssertionError):
            result=self.read(simulate=True)
        signer.assert_not_called();self.assertEqual(before,self.path.read_bytes())
        self.assertFalse(result['production_approved']);self.assertTrue(result['read_only'])
        self.assertNotIn('PRIVATE-ENDPOINT',json.dumps(result))
        self.assertFalse(Path(self.cfg.get('lock_path','var/keeper.lock')).exists())

    def test_hash_pinning_and_exact_fixed_calls_without_nonce_or_broadcast(self):
        rows=self.rows(simulate=True)
        self.assertEqual('simulated',rows['harvest']['state'])
        simulations=[p for m,p in self.rpc.rpc_calls if m=='eth_call' and 'from' in p[0]]
        self.assertEqual({p[0]['to'] for p in simulations},{self.cfg['contracts']['vault'],self.cfg['contracts']['compounder']})
        self.assertTrue(all(p[-1]=={'blockHash':'0x'+'ab'*32,'requireCanonical':True} for m,p in self.rpc.rpc_calls if m in ('eth_call','eth_getCode','eth_estimateGas','eth_getBalance')))
        self.assertFalse(any('TransactionCount' in m or 'send' in m for m,_ in self.rpc.rpc_calls))

    def test_outside_during_cooldown_is_not_due_not_not_needed_and_blocks_compound(self):
        self.rpc.tick=self.rpc.upper;self.rpc.position[6]=self.rpc.now-3600
        rows=self.rows()
        self.assertEqual(('not_due',['hard_rebalance_interval']),(rows['rebalance']['state'],rows['rebalance']['reasons']))
        self.assertTrue(rows['rebalance']['checks']['raw_market_condition']['needed'])
        self.assertEqual(['waiting_outside_range'],rows['compound']['reasons'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])

    def test_manual_width_change_blocks_compound_before_rebalance_cooldown(self):
        self.rpc.manual=1;self.rpc.position[6]=self.rpc.now-3600
        rows=self.rows();self.assertEqual('not_due',rows['rebalance']['state'])
        self.assertEqual(['waiting_range_change'],rows['compound']['reasons'])

    def test_confirmation_wait_disagreement_stale_and_disabled_are_distinct(self):
        self.rpc.tick=self.rpc.upper
        for first,last,reference,gap,state,reason in (
            (0,0,2,300,'not_due','confirmation_not_started'),
            (self.rpc.now-899,self.rpc.now,2,300,'not_due','confirmation_accumulating'),
            (self.rpc.now-1000,self.rpc.now-301,2,300,'blocked','confirmation_observation_stale'),
            (self.rpc.now-1000,self.rpc.now,1,300,'blocked','reference_disagreement'),
            (0,0,2,0,'unconfigured','confirmation_stopped')):
            with self.subTest(reason=reason):
                self.rpc.record=(1,first,last,2) if first else (0,0,0,0);self.rpc.reference=reference;self.rpc.gap=gap
                row=self.rows()['rebalance'];self.assertEqual(state,row['state']);self.assertEqual([reason],row['reasons'])

    def test_onchain_ready_does_not_invent_worker_jitter_or_next_execution(self):
        self.rpc.tick=self.rpc.upper;self.rpc.record=(1,self.rpc.now-900,self.rpc.now,2)
        row=self.rows()['rebalance'];self.assertEqual('observed_eligible',row['state'])
        self.assertFalse(row['service_schedule']['available']);self.assertIsNone(row['service_schedule']['next_execution_at'])

    def test_oracle_or_compound_guard_failure_does_not_erase_due_harvest(self):
        self.rpc.tick=self.rpc.upper;self.rpc.fail_raw=True
        rows=self.rows();self.assertEqual('unavailable',rows['rebalance']['state'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.assertNotIn('PRIVATE-ENDPOINT',json.dumps(rows))

    def test_generic_simulation_and_estimate_errors_do_not_invent_cause(self):
        self.rpc.simulation_error=RpcError('Slippage private endpoint token price')
        row=self.rows(simulate=True)['harvest']
        self.assertEqual(['simulation_failed_unclassified'],row['reasons'])
        self.assertNotIn('Slippage',json.dumps(row))
        self.rpc.simulation_error=None;self.rpc.estimate_error=RpcError('oracle secret')
        row=self.rows(simulate=True)['harvest']
        self.assertEqual('succeeded',row['simulation']['state'])
        self.assertEqual(['gas_estimate_or_price_unavailable'],row['reasons'])

    def test_numeric_gas_caps_accumulate_exact_known_blockers(self):
        self.rpc.estimate=90000;self.rpc.price=101
        self.cfg['max_transaction_cost_wei']=1;self.cfg['max_daily_cost_wei']=1
        row=self.rows(simulate=True)['harvest']
        self.assertEqual('blocked',row['state'])
        self.assertEqual({'gas_limit_cap','gas_price_cap','transaction_cost_cap','daily_cost_cap'},set(row['reasons']))

    def test_missing_journal_is_unavailable_and_never_created(self):
        self.path.unlink();rows=self.rows(simulate=True)
        self.assertEqual(['journal_unavailable'],rows['harvest']['reasons'])
        self.assertFalse(self.path.exists())

    def test_valid_empty_journal_records_worker_defaults_without_inventing_receipt(self):
        row=self.rows(simulate=True)['harvest'];local=row['checks']['local_interval']
        self.assertIsNone(local['last_success_at']);self.assertEqual(0,local['worker_effective_last'])
        self.assertEqual('no_success_record_worker_default_zero',local['source'])
        self.assertEqual('no_day_entry_worker_default_zero',row['checks']['gas']['value']['journal_spent_source'])

    def test_changed_journal_or_canonical_anchor_invalidates_whole_report(self):
        self.rpc.canonical_changed=True
        with self.assertRaises(RpcError):self.read()
        self.rpc.canonical_changed=False
        self.rpc.change_journal=lambda:self.path.write_bytes(self.path.read_bytes()+b' ')
        with self.assertRaises(RpcError):self.read()

    def test_harvest_contract_permission_and_worker_role_are_distinct(self):
        self.rpc.authorized=0;rows=self.rows();row=rows['harvest']
        self.assertEqual(['worker_sender_not_authorized'],row['reasons'])
        self.assertEqual('permissionless',row['checks']['authority']['contract_permission'])
        self.assertTrue(row['checks']['authority']['contract_authorized'])

    def test_preparation_preserves_harvest_but_blocks_principal_work(self):
        self.rpc.preparing=1;rows=self.rows()
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.assertIn('preparation_active',rows['compound']['reasons'])
        self.rpc.preparing=0;original=self.rpc.call
        def call(method,params):
            if method=='eth_call' and params[0]['data']==calldata('canonicalState()'):
                return '0x'+f'{999:064x}'
            return original(method,params)
        self.rpc.call=call
        self.assertTrue(all(row['state']=='unavailable' for row in self.rows().values()))

    def test_financial_thresholds_are_observed_but_margins_remain_unavailable(self):
        finance=self.rows()['compound']['checks']['financial_limits']['value']
        self.assertEqual(300,finance['maintenance_policy']['value']['maintenance_loss_bps'])
        self.assertEqual(100,finance['execution_quality']['value']['additional_loss_bps'])
        self.assertEqual(500,finance['post_deployment_idle_ceiling']['bps'])
        self.assertFalse(finance['measured_margins']['available']);self.assertIsNone(finance['measured_margins']['retained_usd'])

    def test_empty_execution_catalog_does_not_invent_an_operation_blocker(self):
        self.rpc.catalog_count=0;row=self.rows(simulate=True)['compound']
        self.assertEqual('simulated',row['state'])
        self.assertFalse(row['checks']['lp_execution']['value']['metadata']['swaps_enabled'])

    def test_historical_profile_is_explicitly_unsupported(self):
        cfg=copy.deepcopy(self.cfg);cfg.update(accounting_version=1,fee_intake_version=0,maintenance_policy_version=0,lp_routing_version=0,execution_quality_version=0,rebalance_confirmation_version=0)
        cfg['maintenance']={'compound':False,'harvest':True}
        cfg['state_path']=str(Path(self.tmp.name)/'missing-history.json')
        result=review(cfg,[7],rpc=self.rpc)
        self.assertTrue(all(r['state']=='unsupported' for r in result['operations']))
        self.assertFalse(result['journal']['available'])

    def test_selection_and_cli_are_bounded_and_read_only(self):
        for buckets in ([],[7,7],[0],[True],[1,2,3,4,5]):
            with self.subTest(buckets=buckets),self.assertRaises(ValueError):review(self.cfg,buckets,rpc=self.rpc)
        output=io.StringIO()
        with patch('sys.argv',['ops','--config','unused','review','--bucket','7']),\
                patch.object(ops,'_read_required_json',return_value=self.cfg),patch('keeper.operation_review.review',return_value={'ok':True,'read_only':True}) as call,contextlib.redirect_stdout(output):
            self.assertEqual(0,ops.main())
        call.assert_called_once_with(self.cfg,[7],simulate=False)

    def test_included_fee_policy_preserves_optional_zero_allowance_default(self):
        self.cfg.pop('l1_fee_allowance_wei')
        row=self.rows(simulate=True)['harvest']
        self.assertEqual('simulated',row['state'])
        self.assertEqual(0,row['checks']['gas']['value']['l1_fee_allowance_wei'])

    def test_missing_fee_configuration_is_distinct_from_unavailable_estimate(self):
        self.cfg['receipt_fee_policy']='unverified'
        row=self.rows(simulate=True)['harvest']
        self.assertEqual('unconfigured',row['state'])
        self.assertIn('network_fee_semantics_unverified',row['reasons'])
        self.cfg['receipt_fee_policy']='included';self.cfg.pop('max_gas_limit')
        row=self.rows(simulate=True)['harvest']
        self.assertEqual('unconfigured',row['state'])
        self.assertEqual(['gas_caps_unconfigured'],row['reasons'])

    def test_physical_or_compound_guard_fault_does_not_block_harvest(self):
        self.rpc.code_overrides[self.rpc.contracts['state_view']]='0x6001'
        rows=self.rows();self.assertEqual('unavailable',rows['compound']['state'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.rpc.code_overrides.clear();self.rpc.compound_ready=2
        rows=self.rows();self.assertEqual(['compound_guard_unavailable'],rows['compound']['reasons'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])

    def test_impossible_pool_financial_policy_is_unavailable_not_configured(self):
        for index,value in ((10,0),(9,0),(9,501),(10,1)):
            with self.subTest(index=index,value=value):
                original=list(self.rpc.config);self.rpc.config[index]=value
                try:
                    rows=self.rows()
                    self.assertFalse(rows['compound']['checks']['financial_limits']['available'])
                    self.assertEqual('unavailable',rows['compound']['state'])
                    self.assertEqual('observed_eligible',rows['harvest']['state'])
                finally:self.rpc.config=original

    def test_native_gas_funding_is_pinned_and_never_inferred_from_simulation(self):
        self.rpc.balance=74999
        row=self.rows(simulate=True)['harvest']
        self.assertEqual(['insufficient_native_gas_balance'],row['reasons'])
        self.assertEqual(75000,row['checks']['native_gas_funding']['required_estimated_max_wei'])
        self.rpc.balance=75000
        self.assertEqual('simulated',self.rows(simulate=True)['harvest']['state'])
        self.rpc.balance_error=RpcError('PRIVATE-ENDPOINT gas funding')
        row=self.rows(simulate=True)['harvest']
        self.assertEqual(['native_gas_balance_unavailable'],row['reasons'])
        self.assertEqual('succeeded',row['simulation']['state'])
        self.assertIsNone(row['checks']['native_gas_funding']['balance_wei'])

    def test_cli_bucket_errors_are_bounded_and_never_echo_untrusted_values(self):
        self.assertEqual(7,ops._review_bucket('7'))
        self.assertEqual(2**256-1,ops._review_bucket(str(2**256-1)))
        for raw in ('PRIVATE-CLI-VALUE','9'*10000,'0','+7','-7',' 7','7 ','1e3','0x7','9'*78):
            with self.subTest(size=len(raw)):
                output=io.StringIO()
                with patch('sys.argv',['ops','--config','unused','review','--bucket',raw]),\
                        contextlib.redirect_stderr(output),patch.object(ops,'_read_required_json') as loaded,\
                        self.assertRaises(SystemExit) as exited:
                    ops.main()
                self.assertEqual(exited.exception.code,2);loaded.assert_not_called()
                self.assertLess(len(output.getvalue()),1000)
                self.assertIn('bucket must be a canonical nonzero uint256 decimal',output.getvalue())
                self.assertNotIn('PRIVATE-CLI-VALUE',output.getvalue())

    def test_harvest_requires_custody_but_not_optional_market_readers(self):
        for failure in ('owner','pool','owner_unavailable'):
            with self.subTest(failure=failure):
                self.rpc.overrides.clear()
                if failure=='owner':
                    self.rpc.overrides[self.rpc.posm,'ownerOf(uint256)']=physical.words(123)
                elif failure=='pool':
                    value=self.rpc.read(self.rpc.posm,'getPoolAndPositionInfo(uint256)',123,count=6)
                    value[1]=f'{123:064x}'
                    self.rpc.overrides[self.rpc.posm,'getPoolAndPositionInfo(uint256)']=value
                else:
                    self.rpc.overrides[self.rpc.posm,'ownerOf(uint256)']=RpcError('PRIVATE-ENDPOINT custody')
                row=self.rows()['harvest']
                self.assertEqual('unavailable' if failure=='owner_unavailable' else 'blocked',row['state'])
                self.assertNotIn('PRIVATE-ENDPOINT',json.dumps(row))
        self.rpc.overrides.clear();self.rpc.code_overrides[self.rpc.contracts['state_view']]='0x6001'
        self.assertEqual('observed_eligible',self.rows()['harvest']['state'])

    def test_changed_position_basis_at_same_hash_invalidates_report(self):
        original=self.rpc.call;group_calls=0
        def call(method,params):
            nonlocal group_calls
            if method=='eth_call' and params[0]['data']==calldata('group(uint256)',7):
                group_calls+=1
                if group_calls==2:
                    position=list(self.rpc.position);position[6]+=1
                    return '0x'+''.join(physical.words(*position))
            return original(method,params)
        self.rpc.call=call
        with self.assertRaises(RpcError):self.read()
        self.assertGreaterEqual(group_calls,2)

    def test_mixed_case_abi_hex_keeps_pool_and_currency_threshold_identity(self):
        original=self.rpc.call
        for signatures in (('get(bytes32)',),('get(bytes32)','accounting(bytes32)')):
            with self.subTest(signatures=signatures):
                def call(method,params):
                    result=original(method,params)
                    if (method=='eth_call' and params[0]['to']==self.rpc.contracts['pools'] and
                            any(params[0]['data']==calldata(signature,self.rpc.pool) for signature in signatures)):
                        return result[:2]+result[2:].upper()
                    return result
                self.rpc.call=call
                rows=self.rows()
                self.assertEqual('observed_eligible',rows['compound']['state'])
                self.assertEqual([NATIVE_ASSET,self.rpc.zzz],rows['compound']['checks']['compound_trigger']['tokens'])
        self.rpc.call=original

    def test_local_confirmation_reset_blocks_principal_only_and_clear_ack_is_informational(self):
        state=json.loads(self.path.read_text());state['confirmation_reset_v1']={'7':True}
        self.path.write_text(json.dumps(state));before=self.path.read_bytes()
        rows=self.rows()
        for action in ('rebalance','compound'):
            self.assertEqual('blocked',rows[action]['state'])
            self.assertIn('confirmation_reset_required',rows[action]['reasons'])
            self.assertTrue(rows[action]['checks']['local_confirmation_coordination']['reset_required'])
        self.assertEqual('not_needed',rows['rebalance']['checks']['pre_service_reset']['state'])
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.assertEqual(before,self.path.read_bytes())
        state.pop('confirmation_reset_v1');state['confirmation_clear_v1']={'7':{
            'number':99,'hash':'0x'+'ab'*32,'timestamp':self.rpc.now-60,'nonce':0,'awaiting_healthy_read':True}}
        self.path.write_text(json.dumps(state));before=self.path.read_bytes()
        rows=self.rows();self.assertEqual('observed_eligible',rows['compound']['state'])
        local=rows['compound']['checks']['local_confirmation_coordination']
        self.assertFalse(local['reset_required']);self.assertTrue(local['clear_ack_present'])
        self.assertTrue(local['awaiting_healthy_read']);self.assertEqual(before,self.path.read_bytes())
        self.assertIsNone(rows['compound']['service_schedule']['next_execution_at'])


if __name__=='__main__':unittest.main()
