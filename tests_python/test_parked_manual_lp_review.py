"""Parked emergency review via the real Projection/Reader and injected wire.

No old test methods, public RPC, signer, journal, live chain or actual gas proof.
Void simulation responses exercise preparation transport, not EVM eligibility.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python import test_manual_lp_review as fixtures
from tests_python.test_frontend_api import addr, words
from zzz_ops import manual_lp_review as M
from zzz_ops.abi import calldata, decode_words, keccak256
from zzz_ops.errors import RpcError


class ParkedManualLPReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = M.offline.Catalog()

    def setUp(self):
        # Fixture setup is reused; no historical test method is executed.
        self.f = fixtures.ManualLPReviewTests('runTest')
        self.f.catalog = self.catalog
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.rpc, self.q, self.c = self.f.rpc, self.f.q, self.f.c
        self.request = self.f.request
        self.request.update(schema=2, action='D', checks='0', expected_position_status='parked')
        self.q.position[1] = 0;self.q.position[7] = 4
        self.q.secondary = 0;self.q.secondary_count = 0
        self.put('vault', 'bucketCount()', 1)
        self.put('vault', 'MAX_BUCKETS()', 4)
        self.put('vault', 'bucketAt(uint256)', 7, 0)
        self.put('liquidity', 'secondaryId(uint256)', 0, 0)
        self.stable = '0x' + keccak256(bytes.fromhex(f'{int(self.c["lp_position_executor"],16):064x}' + '0'*64)).hex()
        self.execution = '0x' + keccak256(bytes.fromhex(self.stable[2:] + '0'*128)).hex()
        self.put('liquidity', 'portfolioFingerprint(uint256)', self.stable, 0)
        self.put('liquidity', 'executionPortfolioFingerprint(uint256)', self.execution, 0)

    def put(self, role, method, value, *args):
        values=value if isinstance(value,list) else [value]
        self.f.f.rpc.responses[self.f.targets.get(role,role),fixtures.native_data(method,*args)]=words(*values)

    def prepare(self):
        self.sync_custody()
        return M.prepare(self.f.config, self.f.policy, self.request, rpc=self.rpc,
            clock=lambda: self.f.now, catalog=self.catalog)

    def sync_custody(self):
        share_response=self.f.f.rpc.responses[self.c['vault'],calldata('bucketTotalShares(uint256)',7)]
        shares=int(decode_words(share_response)[0],16)
        preimage=[self.f.config['chain_id'],int(self.c['vault'],16),7,*self.q.position,shares,int(self.execution,16)]
        custody='0x'+keccak256(bytes.fromhex(''.join(f'{v:064x}' for v in preimage))).hex()
        self.put('principal_exit','emergencyCustodyHash(uint256)',custody,7)

    def calls(self, signature):
        selector = '0x'+keccak256(signature.encode()).hex()[:8]
        return [p for m,p in self.rpc.calls if m=='eth_call' and p[0]['data'][:10]==selector]

    def test_explicit_schema2_parked_d_exact_static_call_and_disclosure(self):
        with patch.object(M, 'physical_portfolio', side_effect=AssertionError('Active physical proof called')):
            result = self.prepare()
        self.assertEqual(2, result['schema'])
        self.assertEqual('parked', result['expected_position_status'])
        self.assertEqual('parked', result['snapshot']['source_position_status'])
        self.assertEqual('parked_no_live_lp', result['snapshot']['physical']['scope'])
        self.assertEqual([], result['snapshot']['physical']['physical_legs'])
        disclosure = result['safeguards']
        self.assertEqual(0, disclosure['checks'])
        self.assertEqual([1,2,4,8,16], [row['bit'] for row in disclosure['bypassed']])
        self.assertEqual([], disclosure['retained'])
        self.assertFalse(disclosure['mask_is_eligibility_proof'])
        self.assertIn('current_governance_only', disclosure['mandatory_controls'])
        self.assertTrue(disclosure['protocol_remains_paused'])
        tx = result['transaction'];values = [int(w,16) for w in decode_words('0x'+tx['data'][10:])]
        self.assertEqual(12, len(values));self.assertEqual(4180, values[10]);self.assertEqual(1, values[9])
        self.assertEqual(int(result['snapshot']['custody_hash'],16), values[1])
        self.assertEqual(int(result['review']['review_hash'],16), values[11])
        self.assertEqual(self.f.gov, tx['from']);self.assertEqual(self.c['principal_exit'],tx['to'])
        self.assertNotIn('gas', tx);self.assertNotIn('nonce', tx)
        self.assertEqual('125000', result['network_gas']['padded_gas'])
        self.assertEqual(2,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))
        self.assertEqual(self.rpc.simulations[0][0],self.rpc.simulations[1][0])
        self.assertFalse(result['ready_for_submission']);self.assertFalse(result['production_approved'])
        self.assertTrue(self.catalog.check(result['review'])['artifact_matches'])

    def test_schema1_remains_active_only_and_unchanged_shape(self):
        self.request.update(schema=1);self.request.pop('expected_position_status')
        with self.assertRaisesRegex(ValueError, 'Parked is unsupported'):self.prepare()
        self.q.position[1]=123;self.q.position[7]=1
        result=self.prepare()
        self.assertEqual(1,result['schema'])
        for field in ('expected_position_status','selection_sha256','safeguards'):
            self.assertNotIn(field,result)
        self.assertNotIn('source_position_status',result['snapshot'])

    def test_schema2_rejects_non_d_missing_wrong_extra_or_implicit_state(self):
        base=copy.deepcopy(self.request)
        variants=[dict(action='B'),dict(action='C'),dict(schema=3),dict(schema=True),
            dict(expected_position_status='active'),dict(expected_position_status='Parked'),dict(unexpected=1)]
        for changes in variants:
            with self.subTest(changes=changes),self.assertRaises(ValueError):M.selection({**base,**changes})
        missing=copy.deepcopy(base);missing.pop('expected_position_status')
        with self.assertRaises(ValueError):M.selection(missing)
        self.q.position[7]=1
        with self.assertRaises((ValueError,RpcError)):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_all_32_masks_report_retained_bits_and_only_relevant_optional_reads(self):
        for mask in range(32):
            with self.subTest(mask=mask):
                self.rpc.calls.clear();self.rpc.simulations.clear();self.rpc.estimates.clear()
                self.request['checks']=str(mask)
                if mask&17:
                    with self.assertRaisesRegex(ValueError, 'Parked.*trigger|Parked.*confirmation'):self.prepare()
                    self.assertEqual([],self.rpc.simulations)
                    self.assertEqual(str(mask),self.request['checks'])
                    continue
                result=self.prepare();disclosure=result['safeguards']
                self.assertEqual([b for b in (1,2,4,8,16) if mask&b], [x['bit'] for x in disclosure['retained']])
                self.assertEqual([b for b in (1,2,4,8,16) if not mask&b], [x['bit'] for x in disclosure['bypassed']])
                self.assertTrue(all(x['status']=='retained_for_exact_simulation' for x in disclosure['retained']))
                self.assertEqual(bool(mask&6), bool(self.calls('priceBounds(address)')))
                self.assertEqual(bool(mask&4), bool(self.calls('maintenanceLossBps()')))
                self.assertEqual(bool(mask&1), bool(self.calls('needsRebalance(uint256)')))
                self.assertEqual(bool(mask&16), bool(self.calls('observations(uint256)')))
                self.assertFalse(disclosure['mask_is_eligibility_proof'])

    def test_no_physical_zero_id_reads_and_other_bucket_residual_is_allowed(self):
        self.q.secondary_count=1
        self.put('vault','bucketCount()',2);self.put('vault','bucketAt(uint256)',8,1)
        result=self.prepare()
        self.assertEqual(1,result['snapshot']['physical']['active_secondary_count'])
        for method in ('ownerOf(uint256)','ticks(uint256)','amounts(uint256)',
                'portfolioAmounts(uint256)','getPoolAndPositionInfo(uint256)','getSlot0(bytes32)'):
            self.assertEqual([], self.calls(method), method)
        self.assertTrue(self.calls('secondaryId(uint256)'))
        self.assertTrue(self.calls('executionPortfolioFingerprint(uint256)'))

    def test_idle_and_designated_compound_are_only_parked_operation_principal(self):
        for kind in ('idle','compound','both'):
            with self.subTest(kind=kind):
                self.q.position[2]=100 if kind!='compound' else 0;self.q.position[3]=0
                self.put('fees','compoundBalance(uint256,address)',200 if kind!='idle' else 0,7,M.ZERO)
                self.prepare()
        self.q.position[2]=self.q.position[3]=0
        self.put('fees','compoundBalance(uint256,address)',0,7,M.ZERO)
        with self.assertRaisesRegex(RpcError, 'principal'):self.prepare()

    def test_zero_main_residual_and_exact_nonzero_fingerprints_are_required(self):
        variants=('main','secondary','stable','execution','count','shares','nonce','epoch')
        for variant in variants:
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='main':self.q.position[1]=123
                if variant=='secondary':self.put('liquidity','secondaryId(uint256)',124,0)
                if variant=='stable':self.put('liquidity','portfolioFingerprint(uint256)',0,0)
                if variant=='execution':self.put('liquidity','executionPortfolioFingerprint(uint256)',1,0)
                if variant=='count':self.q.secondary_count=5
                if variant=='shares':self.put('vault','bucketTotalShares(uint256)',0,7)
                if variant=='nonce':self.put('principal_exit','parkingNonce(uint256)',2**64,7)
                if variant=='epoch':self.put('principal_exit','custodyEpoch(uint256)',2**64,7)
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual([],self.rpc.simulations)

    def test_complete_pool_key_alias_inventory_and_fixed_asset_pins_are_required(self):
        for variant in ('alias','inventory','duplicate','count','maximum','hook','spacing','fee','get','zzz','decimals','runtime'):
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='alias':self.q.overrides[self.c['vault'],'poolBucket(bytes32)']=[f'{8:064x}']
                if variant=='inventory':self.put('vault','bucketAt(uint256)',8,0)
                if variant=='duplicate':
                    self.put('vault','bucketCount()',2);self.put('vault','bucketAt(uint256)',7,1)
                if variant=='count':self.put('vault','bucketCount()',5)
                if variant=='maximum':self.put('vault','MAX_BUCKETS()',5)
                if variant=='hook':self.q.config[4]=1
                if variant=='spacing':self.q.config[3]=0
                if variant=='fee':self.q.config[2]=2**24
                if variant=='get':self.q.overrides[self.c['pools'],'get(bytes32)']=['0'*64]*14
                if variant=='zzz':self.put('activation_assets','zzz()',addr(21))
                if variant=='decimals':self.put(addr(20),'decimals()',17)
                if variant=='runtime':self.f.f.rpc.codes[self.c['liquidity']]='0x6000'
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual([],self.rpc.simulations)

    def test_zero_mask_does_not_need_usd_timing_or_enabled_operations(self):
        self.rpc.price_failure=True;self.q.config[6]=0
        self.prepare()
        for signature in ('priceBounds(address)','needsRebalance(uint256)',
                'observations(uint256)','executionPoolCount()'):
            self.assertEqual([],self.calls(signature))
        self.request['checks']='4'
        with self.assertRaises(RpcError):self.prepare()

    def test_retained_operations_flag_and_source_simulation_failure_never_auto_bypass(self):
        self.request['checks']='8';self.q.config[6]=0
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual('8',self.request['checks']);self.q.config[6]=1
        self.request['checks']='2';self.rpc.simulation_error=RpcError('source rejects retained price guard')
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual('2',self.request['checks']);self.assertEqual([],self.rpc.estimates)

    def test_parked_explicit_swap_floor_and_source_revert_are_preserved(self):
        self.request.update(swapPool=self.q.pool,zeroForOne=True,amountIn='123',minimumOut='17')
        result=self.prepare()
        self.assertEqual('123',result['arguments']['amountIn'])
        self.assertEqual('17',result['arguments']['minimumOut'])
        self.assertEqual('attributed_idle_and_designated_compound_only',result['snapshot']['swap']['availability_scope'])
        self.assertTrue(result['snapshot']['swap']['captured_amount_is_preflight_ceiling'])
        self.rpc.final_simulation_error=RpcError('source cannot spend excessive inventory')
        with self.assertRaises(RpcError):self.prepare()
        self.assertEqual('123',self.request['amountIn'])
        self.rpc.final_simulation_error=None;self.rpc.simulations.clear()
        self.request['amountIn']='1000001'
        with self.assertRaisesRegex(RpcError,'operation principal'):self.prepare()
        self.assertEqual([],self.rpc.simulations)

    def test_both_swap_directions_use_exact_unequal_idle_and_designated_reserves(self):
        self.q.position[2]=100;self.q.position[3]=200
        self.put('fees','compoundBalance(uint256,address)',50,7,M.ZERO)
        self.put('fees','compoundBalance(uint256,address)',70,7,addr(20))
        for direction,available in ((True,150),(False,270)):
            with self.subTest(zeroForOne=direction):
                self.request.update(swapPool=self.q.pool,zeroForOne=direction,
                    amountIn=str(available),minimumOut='1')
                result=self.prepare()
                self.assertEqual(['150','270'],result['snapshot']['swap']['available_principal_raw'])
                self.assertEqual(str(available),result['arguments']['amountIn'])
                self.assertEqual(direction,result['arguments']['zeroForOne'])
                self.assertTrue(result['snapshot']['swap']['captured_amount_is_preflight_ceiling'])
                self.rpc.simulations.clear();self.request['amountIn']=str(available+1)
                with self.assertRaisesRegex(RpcError,'operation principal'):self.prepare()
                self.assertEqual([],self.rpc.simulations)

    def test_explicit_execution1_lp3_profile_and_late_source_controls(self):
        from frontend_api.service import Projection
        from zzz_ops import execution_price as E
        for variant in ('valid','revision','active_context','capability','routing','binding'):
            with self.subTest(variant=variant):
                self.setUp();self.f.config['execution_price_version']=1
                for role in E.ROLES+('lp_balance_math',):self.put(role,'EXECUTION_PRICE_VERSION()',1)
                for role in ('liquidity','balancing_router'):self.put(role,'LP_ROUTING_VERSION()',3)
                self.put('liquidity','executionStrategy()',self.f.targets['lp_balance_math'])
                self.put('oracle','executionActive()',0);self.put('oracle','executionSourceRevision()',1)
                self.f.policy['projection_sha256']=Projection(self.f.config,self.rpc,clock=lambda:4000).identity
                self.rpc.price_failure=True
                if variant=='revision':
                    self.rpc.after_estimate=lambda:self.put('oracle','executionSourceRevision()',2)
                if variant=='active_context':self.put('oracle','executionActive()',1)
                if variant=='capability':self.put('liquidity','EXECUTION_PRICE_VERSION()',0)
                if variant=='routing':self.put('liquidity','LP_ROUTING_VERSION()',2)
                if variant=='binding':self.put('liquidity','executionStrategy()',addr(42))
                if variant=='valid':
                    result=self.prepare()
                    self.assertEqual(1,result['snapshot']['execution_price']['source_revision'])
                    self.assertEqual(1,result['final_market_observations']['execution_price']['source_revision'])
                    self.assertEqual(2,len(self.rpc.simulations))
                else:
                    with self.assertRaises((ValueError,RpcError)):self.prepare()
                    self.assertEqual(1 if variant=='revision' else 0,len(self.rpc.simulations))
                self.assertEqual([],self.calls('priceBounds(address)'))

    def test_every_parked_control_is_rechecked_at_later_canonical_tip(self):
        for variant in ('idle','compound','shares','status','main','custody','nonce','epoch',
                'governance','permission','governance_code','paused','sealed','preparing','canonical','terminal','exit_phase','policy','registry','secondary_count','runtime'):
            with self.subTest(variant=variant):
                self.setUp()
                def change():
                    if variant=='idle':self.q.position[2]+=1
                    if variant=='compound':self.put('fees','compoundBalance(uint256,address)',1,7,M.ZERO)
                    if variant=='shares':self.put('vault','bucketTotalShares(uint256)',2,7)
                    if variant=='status':self.q.position[7]=1
                    if variant=='main':self.q.position[1]=123
                    if variant=='custody':self.put('principal_exit','emergencyCustodyHash(uint256)','0x'+'45'*32,7)
                    if variant=='nonce':self.put('principal_exit','parkingNonce(uint256)',6,7)
                    if variant=='epoch':self.put('principal_exit','custodyEpoch(uint256)',8,7)
                    if variant=='governance':self.put('access','governance()',addr(41))
                    if variant=='permission':self.put('access','canConfigure(address)',0,self.f.gov)
                    if variant=='governance_code':self.rpc.governance_code='0x6000'
                    if variant=='paused':self.put('access','paused()',0)
                    if variant=='sealed':self.put('access','isSealed()',0)
                    if variant=='preparing':self.put('access','preparationActive()',1)
                    if variant=='canonical':self.put('access','canonicalState()',1)
                    if variant=='terminal':self.put('access','lpExitStarted()',1)
                    if variant=='exit_phase':self.put('principal_exit','exitPhase()',1)
                    if variant=='policy':self.put('portfolio_policy','controlFingerprint(bytes32)','0x'+'45'*32,self.q.pool)
                    if variant=='registry':self.put('pools','configurationRevision()',9)
                    if variant=='secondary_count':self.q.secondary_count=1
                    if variant=='runtime':self.f.f.rpc.codes[self.c['liquidity']]='0x6000'
                self.rpc.after_estimate=change
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual(1,len(self.rpc.simulations))

    def test_noncanonical_missing_getters_never_become_zero(self):
        for method in ('secondaryId(uint256)','portfolioFingerprint(uint256)','executionPortfolioFingerprint(uint256)'):
            with self.subTest(method=method):
                self.setUp()
                self.f.f.rpc.responses[self.c['liquidity'],calldata(method,0)]='0x'
                with self.assertRaises((RpcError,ValueError)):self.prepare()
                self.assertEqual([],self.rpc.simulations)

    def test_direct_eoa_only_original_deadline_gas_and_canonical_state(self):
        for variant in ('contract','expired','gas','fee','balance','reorg','final_simulation'):
            with self.subTest(variant=variant):
                self.setUp()
                if variant=='contract':self.rpc.governance_code='0xef0100'+'11'*20
                if variant=='expired':self.request['deadline']='3999'
                if variant=='gas':self.rpc.gas=900000
                if variant=='fee':self.rpc.price=11
                if variant=='balance':self.rpc.balance=1
                if variant=='reorg':self.rpc.final_reorg=True
                if variant=='final_simulation':self.rpc.final_simulation_error=RpcError('changed final market')
                with self.assertRaises((RpcError,ValueError)):self.prepare()

    def test_selection_and_metadata_are_bound_without_mutating_input(self):
        original=copy.deepcopy(self.request);result=self.prepare()
        self.assertEqual(original,self.request)
        self.assertEqual(M.digest(original),result['selection_sha256'])
        self.assertEqual(M.digest(original),result['snapshot']['selection_sha256'])
        self.assertFalse(any('send' in m.lower() or 'TransactionCount' in m for m,_ in self.rpc.calls))
        for m,p in self.rpc.calls:
            if m in ('eth_call','eth_getCode','eth_estimateGas'):
                self.assertTrue(p[-1]['requireCanonical'])

    def test_cli_prepare_real_reader_exclusive_output_and_sanitized_failure(self):
        original_prepare=M.prepare
        def prepare(config,policy,chosen):
            self.sync_custody()
            return original_prepare(config,policy,chosen,rpc=self.rpc,clock=lambda:self.f.now,catalog=self.catalog)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);paths=[]
            for name,value in [('config',self.f.config),('policy',self.f.policy),('selection',self.request)]:
                path=root/(name+'.json');path.write_bytes(M.offline.render(value));paths.append(path)
            output=root/'review.json';args=[]
            for name,path in zip(('read-config','policy','selection'),paths):args.extend(['--'+name,str(path)])
            args.extend(['--output',str(output)])
            with patch.object(M,'prepare',side_effect=prepare),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0,M.main(args))
            raw=output.read_bytes();self.assertEqual(2,json.loads(raw)['schema'])
            with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(1,M.main(args))
            self.assertEqual(raw,output.read_bytes());output.unlink()
            self.rpc.simulation_error=RpcError('https://credential:secret@rpc.invalid')
            stream=io.StringIO()
            with patch.object(M,'prepare',side_effect=prepare),contextlib.redirect_stderr(stream):
                self.assertEqual(1,M.main(args))
            self.assertFalse(output.exists());self.assertNotIn('secret',stream.getvalue())

    def test_cli_incompatible_parked_mask_has_specific_sanitized_reason(self):
        self.request['checks']='17'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);args=[]
            for name,value in [('read-config',self.f.config),('policy',self.f.policy),('selection',self.request)]:
                path=root/(name+'.json');path.write_bytes(M.offline.render(value));args.extend(['--'+name,str(path)])
            output=root/'absent.json';args.extend(['--output',str(output)])
            stream=io.StringIO()
            with contextlib.redirect_stderr(stream):self.assertEqual(1,M.main(args))
            self.assertEqual('parked_active_trigger_or_confirmation_incompatible',json.loads(stream.getvalue())['reason'])
            self.assertFalse(output.exists());self.assertEqual([],self.rpc.simulations)


if __name__=='__main__':unittest.main()
