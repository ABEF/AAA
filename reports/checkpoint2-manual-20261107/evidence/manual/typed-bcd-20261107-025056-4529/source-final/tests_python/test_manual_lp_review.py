"""Typed manual B/C/D with actual fresh7 projection/physical code and injected RPC.

No running chain, actual gas qualification, journal, signature or rollout.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_frontend_api import addr,words
from tests_python.test_native_backend_boundary import native_data
from zzz_ops import manual_lp_review as M
from zzz_ops import operator_review as O
from zzz_ops.abi import calldata,decode_words,keccak256
from zzz_ops.errors import RpcError,WorkLimit

H='0x'+'12'*32


class ManualRPC:
    def __init__(self,f):
        self.f=f;self.inner=f.rpc;self.calls=[];self.simulations=[];self.estimates=[]
        self.gas=100000;self.price=2;self.output='0x';self.simulation_error=None
        self.price_failure=False;self.after_estimate=None;self.after_final=None
        self.block_reads=0;self.latest_hash='0x'+'dd'*32;self.chain_override=None
        self.final_stamp=4000;self.final_reorg=False
        self.block_limit=30000000;self.balance=10**18;self.final_simulation_error=None
        self.after_second_estimate=None;self.extra_headers={}
        self.void_selectors={
            '0x'+keccak256((name+M.TUPLE+suffix).encode()).hex()[:8]
            for name,suffix in [('consolidateResidual(', ',bool)'),('emergencyRebalance(',')')]}

    def call(self,method,params):
        self.calls.append((method,copy.deepcopy(params)))
        if method=='eth_chainId' and self.chain_override is not None:return self.chain_override
        if method=='eth_blockNumber':
            self.block_reads+=1
            return hex(self.inner.head)
        if method=='eth_getBlockByNumber':
            result=self.inner.call(method,params)
            number=int(params[0],16)
            result['gasLimit']=hex(self.block_limit)
            if number in self.extra_headers:
                result.update(hash=self.extra_headers[number][0],timestamp=hex(self.extra_headers[number][1]))
            elif number>=110:
                result['hash']=('0x'+'ee'*32) if self.final_reorg and self.block_reads>2 else self.latest_hash
                result['timestamp']=hex(self.final_stamp)
            return result
        if method=='eth_gasPrice':return hex(self.price)
        if method=='eth_getBalance':return hex(self.balance)
        if method=='eth_estimateGas':
            self.estimates.append(copy.deepcopy(params))
            if self.after_estimate:self.after_estimate()
            if len(self.estimates)==2 and self.after_second_estimate:self.after_second_estimate()
            return hex(self.gas)
        if method=='eth_call':
            data=params[0]['data']
            if data[:10] in self.void_selectors:
                self.simulations.append(copy.deepcopy(params))
                if len(self.simulations)%2==0 and self.final_simulation_error:raise self.final_simulation_error
                if self.simulation_error:raise self.simulation_error
                return self.output
            if self.price_failure and data[:10]==native_data('priceBounds(address)',addr(20))[:10]:
                raise RpcError('https://private:credential@rpc.invalid USD outage')
        # Fixture transport internally knows one hash. Preserve distinct actual
        # observed tags above, then translate only inside the injected fixture.
        translated=copy.deepcopy(params)
        if method in ('eth_call','eth_getCode') and params[-1]=={'blockHash':self.latest_hash,'requireCanonical':True}:
            translated[-1]={'blockHash':self.inner.hash,'requireCanonical':True}
        result=self.inner.call(method,translated)
        if self.after_final and method=='eth_call' and params[-1].get('blockHash')==self.latest_hash:
            self.after_final()
        return result


class ManualLPReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=O.Catalog()

    def setUp(self):
        self.f=Fresh7API(self);self.q=self.f.q;self.c=self.f.c;self.config=self.f.config
        self.rpc=ManualRPC(self.f);self.now=4000
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.q.position[2]=1000000;self.q.position[3]=1000000
        self.q.config[6]=1;self.q.tick=0;self.q.secondary=124;self.q.secondary_count=1
        self.extra={}
        for n,role in enumerate(sorted(M.EXTRAS),21000):
            code='0x6001'+f'{n:04x}';target=addr(n)
            self.f.rpc.codes[target]=code
            self.extra[role]={'address':target,'code_hash':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
        self.targets={**self.c,**{role:item['address'] for role,item in self.extra.items()}}
        self.gov=addr(40)
        self.put('access','paused()',1);self.put('access','canConfigure(address)',1,self.gov)
        for role,label in [('oracle','ZZZOracle'),('fees','ZZZFeeController')]:
            self.put('access','module(bytes32)',self.targets[role],'0x'+keccak256(label.encode()).hex())
            self.put(role,'access()',self.c['access'])
        for role,method,target in [('principal_exit','validation()','custody_validation'),
                ('custody_validation','migration()','principal_exit'),('custody_validation','access()','access'),
                ('pools','activationAssets()','activation_assets'),('activation_assets','registry()','pools'),
                ('activation_assets','access()','access'),('oracle','contributionPricing()','contribution_pricing'),
                ('contribution_pricing','oracle()','oracle'),('contribution_pricing','access()','access')]:
            self.put(role,method,self.targets[target])
        for role in ('principal_exit','vault','budget','portfolio_policy','contribution_pricing'):
            self.put(role,'RESIDUAL_REINVEST_VERSION()',1)
        self.put('fees','FEE_INTAKE_VERSION()',1)
        self.put('activation_assets','zzz()',addr(20))
        for method,value in [('consolidationCustodyHash(uint256)',H),('emergencyCustodyHash(uint256)','0x'+'34'*32),
                ('parkingNonce(uint256)',5),('custodyEpoch(uint256)',7)]:self.put('principal_exit',method,value,7)
        self.put('pools','configurationRevision()',8)
        self.put('portfolio_policy','controlFingerprint(bytes32)',H,self.q.pool)
        self.put('budget','maintenanceLossBps()',300);self.put('strategy','additionalLossBps()',100)
        self.put('strategy','executionQualityRevision()',1)
        self.put('balancing_router','executionPoolCount()',1);self.put('balancing_router','executionRevision()',1)
        self.put('balancing_router','executionPoolAt(uint256)',self.q.pool,0)
        for token in (M.ZERO,addr(20)):
            self.put('oracle','priceBounds(address)',[10**18,10**18,H],token)
            self.put('oracle','activePolicy(address)',H,token)
            self.put('fees','compoundBalance(uint256,address)',0,7,token)
        self.put('oracle','activeSequencerPolicy()',0)
        self.policy={'schema':1,'projection_sha256':self.f.p.identity,
            'reference_sha256':self.catalog.reference_sha256,'source_snapshot_sha256':self.catalog.source_snapshot_sha256,
            'governance':self.gov,'extra_contracts':self.extra,
            'fee_policy':{'max_gas_limit':'1000000','max_gas_price_wei':'10','max_network_fee_wei':'10000000',
                'estimate_includes_all_fees':True,'review_hash':H}}
        self.request={'schema':1,'action':'B','bucket':'7','checks':'14','lower':str(self.q.lower),
            'upper':str(self.q.upper),'swapPool':'0x'+'0'*64,'zeroForOne':False,'amountIn':'0','minimumOut':'0',
            'minimumLiquidity':'1','deadline':'4180','review_notes_sha256':'11'*32,'evidence_sha256':['22'*32]}

    def put(self,role,method,value,*args):
        values=value if isinstance(value,list) else [value]
        self.f.rpc.responses[self.targets[role],native_data(method,*args)]=words(*values)

    def prepare(self):
        return M.prepare(self.config,self.policy,self.request,rpc=self.rpc,clock=lambda:self.now,catalog=self.catalog)

    def test_exact_b_c_d_calls_and_floor_meanings(self):
        for action in ('B','C','D'):
            with self.subTest(action=action):
                self.request['action']=action;result=self.prepare();tx=result['transaction']
                self.assertEqual(self.gov,tx['from']);self.assertEqual(self.c['principal_exit'],tx['to'])
                self.assertEqual('0x0',tx['value']);self.assertNotIn('gas',tx)
                self.assertEqual(hex(self.config['chain_id']),tx['chainId'])
                self.assertEqual('125000',result['network_gas']['padded_gas'])
                values=[int(w,16) for w in decode_words('0x'+tx['data'][10:])]
                self.assertEqual(7,values[0]);self.assertEqual(14,values[2]);self.assertEqual(4180,values[10])
                self.assertEqual(int(result['review']['review_hash'],16),values[11])
                self.assertEqual(12 if action=='D' else 13,len(values))
                if action!='D':self.assertEqual(int(action=='C'),values[12])
                self.assertEqual('new_position_liquidity' if action=='D' else 'added_main_liquidity',result['liquidity_floor_kind'])
                self.assertFalse(result['ready_for_submission']);self.assertFalse(result['production_approved'])
                self.assertTrue(self.catalog.check(result['review'])['artifact_matches'])

    def test_forced_zero_mask_has_no_usd_route_or_operations_readiness_dependency(self):
        self.request.update(checks='0');self.rpc.price_failure=True;self.q.config[6]=0
        for action in ('C','D'):
            self.request['action']=action
            result=self.prepare();self.assertEqual('not_retained',result['snapshot']['financial']['state'])
        prohibited={native_data('priceBounds(address)',addr(20))[:10],calldata('executionPoolCount()')[:10],
            calldata('needsRebalance(uint256)',7)[:10],calldata('observations(uint256)',7)[:10],
            native_data('activePolicy(address)',addr(20))[:10],calldata('activeSequencerPolicy()')[:10]}
        self.assertFalse(any(m=='eth_call' and p[0]['data'][:10] in prohibited for m,p in self.rpc.calls))
        self.request['checks']='14'
        with self.assertRaises(RpcError):self.prepare()

    def test_output_chain_and_rpc_configuration_identity_are_bound(self):
        self.rpc.chain_override=1
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual([],self.rpc.simulations)
        self.rpc.chain_override=None;self.config['chain_id']+=1
        with self.assertRaisesRegex(ValueError,'read configuration'):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_full_replacement_can_include_designated_compound_but_same_main_cannot(self):
        self.request.update(action='C',checks='0',swapPool=self.q.pool,zeroForOne=True,
            amountIn='10000000',minimumOut='1')
        self.put('fees','compoundBalance(uint256,address)',10**18,7,M.ZERO)
        with self.assertRaisesRegex(RpcError,'operation principal'):self.prepare()
        self.request['action']='D'
        result=self.prepare()
        self.assertEqual('new_position_liquidity',result['liquidity_floor_kind'])
        self.assertEqual('10000000',result['arguments']['amountIn'])

    def test_d_preharvest_lower_bound_never_replaces_full_source_call_spendability(self):
        self.request.update(action='D',checks='0',swapPool=self.q.pool,zeroForOne=True,
            amountIn='1000000000',minimumOut='1')
        result=self.prepare()
        swap=result['snapshot']['swap']
        self.assertGreater(int(self.request['amountIn']),int(swap['available_principal_raw'][0]))
        self.assertEqual('observed_lower_bound_excludes_future_harvest',swap['availability_scope'])
        self.assertFalse(swap['captured_amount_is_preflight_ceiling'])
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))
        self.assertEqual('1000000000',result['arguments']['amountIn'])
        self.rpc.simulation_error=RpcError('source refuses unavailable post-harvest inventory')
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual(3,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))

    def test_retained_value_bit_requires_usd_even_when_price_agreement_bit_is_off(self):
        self.request.update(action='C',checks='4');self.rpc.price_failure=True
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_all_rpc_contract_reads_use_confirmed_or_final_canonical_hash_without_latest_fallback(self):
        self.prepare()
        read_calls=[p for m,p in self.rpc.calls if m in ('eth_call','eth_getCode','eth_estimateGas')]
        tags={p[-1]['blockHash'] for p in read_calls}
        self.assertEqual({self.f.rpc.hash,self.rpc.latest_hash},tags)
        self.assertTrue(all(p[-1].get('requireCanonical') is True for p in read_calls))
        self.assertEqual([self.f.rpc.hash,self.rpc.latest_hash],[p[-1]['blockHash'] for p in self.rpc.simulations])
        self.assertEqual([self.f.rpc.hash,self.rpc.latest_hash],[p[-1]['blockHash'] for p in self.rpc.estimates])
        self.assertFalse(any('send' in m.lower() or 'TransactionCount' in m for m,_ in self.rpc.calls))

    def test_changed_final_nonce_controls_and_physical_backing_refuse_without_rewriting(self):
        for variant in ('nonce','governance','control','liquidity','price_policy','sequencer_policy'):
            with self.subTest(variant=variant):
                self.setUp()
                original=copy.deepcopy(self.request)
                def change():
                    if variant=='nonce':self.put('principal_exit','parkingNonce(uint256)',6,7)
                    if variant=='governance':self.put('access','governance()',addr(41))
                    if variant=='control':self.put('portfolio_policy','controlFingerprint(bytes32)','0x'+'56'*32,self.q.pool)
                    if variant=='liquidity':self.q.physical_liquidities[123]=700
                    if variant=='price_policy':self.put('oracle','activePolicy(address)','0x'+'56'*32,addr(20))
                    if variant=='sequencer_policy':self.put('oracle','activeSequencerPolicy()','0x'+'56'*32)
                self.rpc.after_estimate=change
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual(original,self.request);self.assertEqual(1,len(self.rpc.simulations))

    def test_healthy_trading_and_new_price_rounds_keep_original_manifest_and_revalidate_twice(self):
        def move():
            self.q.tick=50
            self.put('oracle','priceBounds(address)',[10**18,10**18,'0x'+'56'*32],addr(20))
        self.rpc.after_estimate=move
        result=self.prepare()
        self.assertNotEqual(result['snapshot']['physical']['portfolio_amounts'],
            result['final_market_observations']['physical']['portfolio_amounts'])
        self.assertNotEqual(result['snapshot']['financial']['price_bounds'],
            result['final_market_observations']['financial']['price_bounds'])
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))
        self.assertEqual(self.rpc.simulations[0][0]['data'],self.rpc.simulations[1][0]['data'])
        self.assertEqual('4180',result['arguments']['deadline']);self.assertEqual('1',result['arguments']['minimumLiquidity'])

    def test_latest_retained_guard_failure_refuses_without_fallback_or_third_probe(self):
        self.rpc.after_estimate=lambda:setattr(self.q,'tick',50)
        self.rpc.final_simulation_error=RpcError('opaque minimum/retained guard failure')
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(1,len(self.rpc.estimates))
        self.assertEqual(self.rpc.simulations[0][0]['data'],self.rpc.simulations[1][0]['data'])

    def test_governance_pause_terminal_and_preparation_are_mandatory(self):
        for method,value in [('paused()',0),('governance()',addr(41)),('lpExitStarted()',1),('preparationActive()',1)]:
            with self.subTest(method=method):
                before=self.f.rpc.responses[self.c['access'],calldata(method)]
                self.put('access',method,value)
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.f.rpc.responses[self.c['access'],calldata(method)]=before
        self.assertEqual([],self.rpc.simulations)

    def test_wrong_runtime_current_profile_and_extension_capability_refuse(self):
        for variant in ('runtime','accounting','extension'):
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='runtime':self.f.rpc.codes[self.extra['custody_validation']['address']]='0x6000'
                if variant=='accounting':self.put('vault','ACCOUNTING_VERSION()',6)
                if variant=='extension':self.put('budget','RESIDUAL_REINVEST_VERSION()',0)
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual([],self.rpc.simulations)

    def test_parked_state_is_explicitly_unsupported_even_for_full_emergency(self):
        self.request.update(action='D',checks='0');self.q.position[7]=4;self.q.position[1]=0
        with self.assertRaisesRegex(ValueError,'Parked is unsupported'):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_same_main_cannot_recenter_and_b_cannot_silently_force(self):
        self.request['lower']=str(self.q.lower-10)
        with self.assertRaisesRegex(ValueError,'exact current ticks'):self.prepare()
        self.request['lower']=str(self.q.lower);self.request['checks']='0'
        with self.assertRaisesRegex(ValueError,'checks14'):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_explicit_swap_cannot_spend_main_in_same_main_action(self):
        self.request.update(action='C',checks='0',swapPool=self.q.pool,zeroForOne=True,
            amountIn=str(10**30),minimumOut='1')
        with self.assertRaisesRegex(RpcError,'operation principal'):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_original_deadline_and_snapshot_expiry_are_never_extended(self):
        for deadline in ('3999','4601'):
            self.request['deadline']=deadline
            with self.assertRaises((RpcError,ValueError)):self.prepare()
        self.request['deadline']='4001';self.rpc.after_estimate=lambda:setattr(self,'now',4002)
        with self.assertRaises((RpcError,ValueError)):self.prepare()
        self.assertEqual('4001',self.request['deadline'])

    def test_gas_price_fee_and_headroom_caps_never_widen(self):
        for field,value in [('max_gas_limit','100000'),('max_gas_price_wei','1'),('max_network_fee_wei','1')]:
            with self.subTest(field=field):
                old=self.policy['fee_policy'][field];self.policy['fee_policy'][field]=value
                with self.assertRaisesRegex(RpcError,'original gas/fee'):self.prepare()
                self.assertEqual(value,self.policy['fee_policy'][field]);self.policy['fee_policy'][field]=old

    def test_block_gas_limit_bounds_both_reviews_and_network_envelope_is_separate(self):
        self.rpc.block_limit=200000
        result=self.prepare()
        self.assertEqual(['0x30d40','0x30d40'],[p[0]['gas'] for p in self.rpc.simulations])
        self.assertEqual('200000',result['network_gas']['gas_limit_cap'])
        self.assertNotIn('gas',result['transaction'])
        self.rpc.block_limit=100000
        with self.assertRaisesRegex(RpcError,'original gas/fee'):self.prepare()

    def test_intrinsic_gas_and_governance_funding_are_required(self):
        self.policy['fee_policy']['max_gas_limit']='20999'
        with self.assertRaises(ValueError):self.prepare()
        self.policy['fee_policy']['max_gas_limit']='1000000';self.rpc.gas=20999
        with self.assertRaises(RpcError):self.prepare()
        self.rpc.gas=100000;self.rpc.balance=249999
        with self.assertRaisesRegex(RpcError,'Governance balance'):self.prepare()

    def test_last_head_deadline_after_final_estimate_refuses_without_resimulation(self):
        self.request['deadline']='4010'
        def advance():
            self.f.rpc.head=111;self.rpc.extra_headers[111]=('0x'+'ef'*32,4011)
        self.rpc.after_second_estimate=advance
        with self.assertRaisesRegex(RpcError,'original deadline expired'):self.prepare()
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))

    def test_opaque_simulation_and_malformed_void_return_never_produce_a_draft(self):
        self.rpc.simulation_error=RpcError('https://private:credential@rpc.invalid swap failure')
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual([],self.rpc.estimates)
        self.rpc.simulation_error=None;self.rpc.output='0x'+'0'*64
        with self.assertRaisesRegex(RpcError,'void simulation'):self.prepare()

    def test_reorg_and_lost_depth_refuse(self):
        self.rpc.final_reorg=True
        with self.assertRaises(RpcError):self.prepare()
        self.rpc.final_reorg=False;self.rpc.after_estimate=lambda:setattr(self.f.rpc,'head',90)
        with self.assertRaises(RpcError):self.prepare()

    def test_unknown_duplicate_float_oversized_and_noncanonical_inputs_refuse(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":1.2}',b'['*17+b']'*17,b'x'*(O.MAX_DOCUMENT+1)):
            with self.assertRaises(ValueError):O.decode(raw)
        for change in ({'arbitrary_target':addr(80)},{'minimumLiquidity':'01'},{'checks':True},{'zeroForOne':1}):
            altered={**self.request,**change}
            with self.assertRaises((ValueError,TypeError)):M.selection(altered)
        self.assertEqual([],self.rpc.calls)

    def test_input_mutation_and_work_limits_fail_closed(self):
        self.rpc.after_estimate=lambda:self.request.update(minimumLiquidity='2')
        with self.assertRaises(RpcError):self.prepare()
        self.rpc.after_estimate=None
        with patch.object(M,'MAX_CALLS',1),self.assertRaises(WorkLimit):self.prepare()

    def test_read_only_execution_never_touches_keeper_journals_or_signer(self):
        from keeper.monitor import Keeper
        with patch('subprocess.run',side_effect=AssertionError('signer')),patch.object(Keeper,'save',side_effect=AssertionError('journal')):
            result=self.prepare()
        self.assertTrue(result['read_only']);self.assertEqual([],list(Path(self.tmp.name).iterdir()))

    def test_project_getter_signatures_and_static_return_widths_match_current_catalog(self):
        classes={'access':'ZZZAccessController','vault':'ZZZVault','strategy':'ZZZStrategy',
            'pools':'ZZZPoolRegistry','liquidity':'ZZZLiquidityManager','principal_exit':'ZZZMigration',
            'budget':'ZZZMigrationBudget','portfolio_policy':'ZZZPortfolioPolicy',
            'rebalance_confirmation':'ZZZRebalanceConfirmation','balancing_router':'ZZZLPBalancer',
            'lp_position_executor':'ZZZLPPositionExecutor','lp_balance_math':'ZZZLPBalanceMath',
            'oracle':'ZZZOracle','fees':'ZZZFeeController','activation_assets':'ZZZActivationAssets',
            'custody_validation':'ZZZCustodyValidation','contribution_pricing':'ZZZContributionPricing',
            'protocol_policy':'ZZZProtocolPolicy'}
        by_address={value:key for key,value in self.targets.items()};seen=[];original=M.Reader.read
        def record(reader,role,method,*args,count=1):
            seen.append((by_address.get(role,role),method,count))
            return original(reader,role,method,*args,count=count)
        with patch.object(M.Reader,'read',record):self.prepare()
        def width(output):
            if output['type']=='tuple':return sum(width(child) for child in output['components'])
            self.assertNotIn('[',output['type']);return 1
        matched=set()
        for role,method,count in seen:
            if role not in classes:continue  # Upstream PosM/StateView ABI reused by the physical adapter.
            contracts=[contract for contract in self.catalog.data['contracts'] if contract['name']==classes[role]]
            self.assertEqual(1,len(contracts),role)
            functions=[fn for fn in contracts[0]['functions'] if fn['signature']==method]
            self.assertEqual(1,len(functions),(role,method))
            self.assertEqual(count,sum(width(output) for output in functions[0]['outputs']),(role,method))
            matched.add((role,method))
        self.assertGreater(len(matched),50)

    def test_exclusive_atomic_output_preserves_existing_bytes_and_cleans_temporary(self):
        path=Path(self.tmp.name)/'review.json';M.write_exclusive(path,b'complete')
        with self.assertRaises(FileExistsError):M.write_exclusive(path,b'changed')
        self.assertEqual(b'complete',path.read_bytes())
        self.assertEqual([path],list(path.parent.iterdir()))

    def test_cli_sanitizes_errors_and_never_replaces_output(self):
        paths={key:Path(self.tmp.name)/(key+'.json') for key in ('read-config','policy','selection','output')}
        for key,value in [('read-config',self.config),('policy',self.policy),('selection',self.request)]:
            paths[key].write_bytes(O.render(value))
        args=[item for key,path in paths.items() for item in ('--'+key,str(path))]
        stderr=io.StringIO()
        with patch.object(M,'prepare',side_effect=RpcError('private:credential@rpc.invalid')),contextlib.redirect_stderr(stderr):
            self.assertEqual(1,M.main(args))
        self.assertNotIn('credential',stderr.getvalue());self.assertFalse(paths['output'].exists())
        with contextlib.redirect_stderr(stderr):self.assertEqual(1,M.main(['--unknown','private:credential@rpc.invalid']))
        self.assertNotIn('credential',stderr.getvalue())
        paths['output'].write_bytes(b'preserve')
        with patch.object(M,'prepare') as prepare,contextlib.redirect_stderr(io.StringIO()):self.assertEqual(1,M.main(args))
        prepare.assert_not_called();self.assertEqual(b'preserve',paths['output'].read_bytes())


if __name__=='__main__':unittest.main()
