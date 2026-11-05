"""Claim planning uses exact preparer output and never diagnoses opaque RPCs."""
import copy
import unittest

from frontend_api.claim_planner import MAX_TRIALS
from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionInputError, Claim, claim_calldata
from tests_python.test_frontend_api import addr, calldata, configuration, words
from tests_python.test_frontend_transactions import TransactionRPC, transaction_config
from tests_python import test_frontend_policy_v6 as current_fixtures
from zzz_ops.abi import keccak256
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit
from zzz_ops.work_budget import Budget, request_scope


class PlannerRPC(TransactionRPC):
    def __init__(self):
        super().__init__()
        self.maximum_batch = 32
        self.refused = set()
        self.metadata_error = None
        self.view_error = None
        self.gas_per_claim = None
        self.owner_reads = 0
        self.change_owner_on_final = False
        self.estimate_reads = 0
        self.estimate_error_at = None

    def call(self, method, params):
        if method == 'eth_call' and 'from' not in params[0]:
            tx = params[0]
            if tx['to'] == addr(21) and tx['data'] == calldata('decimals()') and self.metadata_error:
                raise self.metadata_error
            if tx['to'] == addr(2) and tx['data'].startswith(calldata('ownerOf(uint256)', self.nft_id)[:10]):
                self.owner_reads += 1
                if self.change_owner_on_final and self.owner_reads >= 3:
                    return words(addr(31))
            if (self.view_error and tx['to'] == addr(4) and
                    tx['data'] == calldata('claimable(uint256,address)', self.nft_id, addr(21))):
                raise self.view_error
        if method == 'eth_call' and 'from' in params[0] and params[0]['to'] == addr(6):
            raw = params[0]['data'][10:]
            count = int(raw[64:128],16)
            identifiers = [int(raw[128+i*192:192+i*192],16) for i in range(count)]
            if count > self.maximum_batch or self.refused.intersection(identifiers):
                self.calls.append((method,copy.deepcopy(params)));self.simulations.append(copy.deepcopy(params))
                raise RemoteRPCError(method,3)
        if method == 'eth_estimateGas':
            self.estimate_reads += 1
            if self.estimate_reads == self.estimate_error_at:
                raise RemoteRPCError(method,-32005,'rate_limited')
            if self.gas_per_claim is not None:
                self.estimate = self.gas_per_claim*int(params[0]['data'][74:138],16)
        return super().call(method,params)


class ClaimPlannerTests(unittest.TestCase):
    def setUp(self):
        self.rpc=PlannerRPC();self.now=1000
        self.p=Projection(configuration(),self.rpc,clock=lambda:self.now)
        self.config=transaction_config(self.p);self.service=Transactions(self.p,self.config)

    def entry(self,identifier=None,asset=None,royalty=False):
        return dict(token_id=str(identifier or self.rpc.nft_id),asset=asset or addr(21),royalty=royalty)

    def many(self,count):
        result=[]
        for i in range(count):
            identifier=10**60+i+1
            for sig,args,value in [('mintOrdinalOf(uint256)',(identifier,),i+1),
                                  ('tokenAtOrdinal(uint256)',(i+1,),identifier),
                                  ('ownerOf(uint256)',(identifier,),addr(30))]:
                self.rpc.put(addr(2),sig,args,(value,))
            self.rpc.put(addr(4),'claimable(uint256,address)',(identifier,addr(21)),(100+i,))
            result.append(self.entry(identifier))
        return result

    def plan(self,entries=None,**overrides):
        return self.service.plan_claims(dict(action='claim',wallet=addr(30),
            claims=entries if entries is not None else [self.entry()],**overrides))

    def test_one_exact_batch_is_freshly_prepared_twice_without_future_transactions(self):
        result=self.plan()
        draft=result['next_batch']
        self.assertEqual(draft['transaction']['data'],claim_calldata((Claim(self.rpc.nft_id,addr(21),False),)))
        self.assertEqual(result['entries'][0]['status'],'in_next_batch')
        self.assertEqual(result['remaining_claims'],[])
        self.assertEqual(len(self.rpc.simulations),2)
        self.assertTrue(result['planning']['final_batch_revalidated'])
        self.assertTrue(result['replan_after_confirmation']);self.assertFalse(result['automatic_submission'])
        self.assertEqual(draft['simulation']['gas_cap'],'12000000')
        self.assertNotIn('nonce',draft['transaction']);self.assertNotIn('signed',draft)
        self.assertTrue(all(m not in ('eth_sendTransaction','eth_sendRawTransaction') for m,_ in self.rpc.calls))

    def test_oversized_execution_is_reduced_with_every_remaining_entry_preserved(self):
        entries=self.many(4);self.rpc.maximum_batch=2
        result=self.plan(entries)
        self.assertEqual([d['token_id'] for d in result['next_batch']['claim_operations']],
                         [c['token_id'] for c in entries[:2]])
        self.assertEqual([r['selection_index'] for r in result['remaining_claims']],[2,3])
        self.assertTrue(all(r['status']=='unassessed' for r in result['remaining_claims']))
        self.assertEqual(result['planning']['trial_count'],3)
        self.assertEqual(len(self.rpc.simulations),4)
        self.assertTrue(all('transaction' not in r for r in result['remaining_claims']))

    def test_successful_estimate_above_reviewed_gas_or_fee_bound_is_sized_down(self):
        entries=self.many(8);self.rpc.gas_per_claim=2_000_000
        result=self.plan(entries)
        self.assertEqual(len(result['next_batch']['claim_operations']),4)
        self.assertLessEqual(int(result['next_batch']['network_gas']['suggested_limit']),12_000_000)
        self.assertLessEqual(int(result['next_batch']['network_gas']['suggested_limit_cost_wei']),int(self.config['fee_policy']['max_network_fee_wei']))
        self.assertTrue(any(t['outcome']=='over_budget' for t in result['planning']['attempts']))
        self.assertEqual(len(result['remaining_claims']),4)

    def test_individual_opaque_refusal_remains_unresolved_without_poisoning_other_currencies(self):
        entries=self.many(3);self.rpc.refused={int(entries[0]['token_id'])}
        result=self.plan(entries)
        self.assertEqual(result['entries'][0]['status'],'unavailable')
        self.assertEqual(result['entries'][0]['reason'],'execution_refused_unclassified')
        self.assertEqual(result['entries'][0]['view_raw'],'100')
        self.assertEqual([c['token_id'] for c in result['next_batch']['claim_operations']],
                         [c['token_id'] for c in entries[1:]])
        self.assertEqual(len(result['remaining_claims']),1)
        self.assertNotIn('bad_token',str(result))

    def test_zero_blocked_and_unavailable_are_distinct_and_not_invented_as_balances(self):
        self.rpc.put(addr(4),'claimable(uint256,address)',(self.rpc.nft_id,addr(20)),(0,))
        self.rpc.metadata_error=RemoteRPCError('eth_call',3)
        entries=[self.entry(asset=addr(20)),self.entry(asset=addr(21)),self.entry(asset=addr(22))]
        result=self.plan(entries)
        self.assertIsNone(result['next_batch'])
        self.assertEqual([r['status'] for r in result['entries']],['zero','unavailable','blocked'])
        self.assertEqual([r['view_raw'] for r in result['entries']],['0',None,None])
        self.assertEqual(len(result['remaining_claims']),2)
        self.assertFalse(self.rpc.simulations)

    def test_all_zero_selection_returns_no_draft_or_gas_request(self):
        self.rpc.put(addr(4),'claimable(uint256,address)',(self.rpc.nft_id,addr(21)),(0,))
        result=self.plan()
        self.assertIsNone(result['next_batch']);self.assertEqual(result['entries'][0]['status'],'zero')
        self.assertEqual(result['remaining_claims'],[]);self.assertFalse(self.rpc.simulations)
        self.assertFalse(any(m in ('eth_estimateGas','eth_gasPrice','eth_getBalance') for m,_ in self.rpc.calls))

    def test_nonowner_and_unminted_rows_are_explicitly_blocked_without_losing_owned_claims(self):
        entries=self.many(2);foreign=int(entries[0]['token_id']);unknown=10**70
        self.rpc.put(addr(2),'ownerOf(uint256)',(foreign,),(addr(31),))
        self.rpc.put(addr(2),'mintOrdinalOf(uint256)',(unknown,),(0,))
        result=self.plan([entries[0],entries[1],self.entry(unknown)])
        self.assertEqual([r['status'] for r in result['entries']],['blocked','in_next_batch','blocked'])
        self.assertEqual([r['reason'] for r in result['remaining_claims']],['wallet_not_current_owner','nft_not_minted'])
        self.assertTrue(all(r['view_raw'] is None for r in result['entries'] if r['status']=='blocked'))

    def test_missing_currency_code_is_unavailable_and_other_verified_entries_can_plan(self):
        self.rpc.codes[addr(21)]='0x'
        result=self.plan([self.entry(),self.entry(asset=addr(20))])
        self.assertEqual(result['entries'][0]['status'],'unavailable')
        self.assertIsNone(result['entries'][0]['view_raw'])
        self.assertEqual(len(result['next_batch']['claim_operations']),1)
        self.assertEqual(result['remaining_claims'][0]['selection_index'],0)

    def test_opaque_currency_metadata_or_claim_view_does_not_remove_the_selection(self):
        for field in ('metadata_error','view_error'):
            with self.subTest(field=field):
                self.setUp();setattr(self.rpc,field,RemoteRPCError('eth_call',3))
                result=self.plan([self.entry(),self.entry(asset=addr(20))])
                self.assertEqual(result['entries'][0]['status'],'unavailable')
                self.assertEqual(len(result['next_batch']['claim_operations']),1)
                self.assertEqual(result['remaining_claims'][0]['selection_index'],0)

    def test_detectable_transport_rate_limit_and_unknown_failures_return_no_draft(self):
        for error in (RpcError('private provider details'),RemoteRPCError('eth_call',-32005,'rate_limited'),
                      RemoteRPCError('eth_call',-32001,'unavailable_block'),RemoteRPCError('eth_call',-32603)):
            with self.subTest(kind=type(error).__name__,code=getattr(error,'code',None)):
                self.setUp();self.rpc.metadata_error=error
                with self.assertRaises(RpcError):self.plan([self.entry(asset=addr(20))])
                self.assertFalse(self.rpc.simulations)

    def test_global_failure_after_a_good_trial_does_not_publish_the_older_good_draft(self):
        self.rpc.maximum_batch=2;self.rpc.estimate_error_at=2
        with self.assertRaises(RpcError):self.plan(self.many(4))
        self.assertGreaterEqual(len(self.rpc.simulations),3)

    def test_final_current_owner_and_fees_are_reread_and_can_stop_publication(self):
        self.rpc.change_owner_on_final=True
        with self.assertRaises(TransactionInputError):self.plan()
        self.assertGreaterEqual(self.rpc.owner_reads,3)
        self.assertEqual(len(self.rpc.simulations),1)
        self.setUp();original=self.rpc.call;reads=[0]
        def price(method,params):
            if method=='eth_gasPrice':
                reads[0]+=1
                if reads[0]==2:return hex(10**20)
            return original(method,params)
        self.rpc.call=price
        with self.assertRaises(ProjectionError):self.plan()
        self.assertEqual(reads[0],2)

    def test_malformed_return_and_estimate_are_not_reinterpreted_as_gas_or_token_faults(self):
        for bad in ('0x',words(0,1,1),words(32,1,0)):
            with self.subTest(result=bad[:20]):
                self.setUp();self.rpc.simulated=bad
                with self.assertRaises(ProjectionError):self.plan()
                self.assertEqual(len(self.rpc.simulations),1)
        for bad in ('0x00','0x1',21000,True):
            self.setUp();original=self.rpc.call
            def malformed(method,params):
                return bad if method=='eth_estimateGas' else original(method,params)
            self.rpc.call=malformed
            with self.subTest(estimate=bad),self.assertRaises(ProjectionError):self.plan()

    def test_only_hash_bound_identity_metadata_is_cached_with_no_cross_request_state(self):
        original_rpc=self.p.rpc
        result=self.plan()
        self.assertIs(self.p.rpc,original_rpc)
        self.assertEqual(self.rpc.owner_reads,3)
        for target in (addr(20),addr(21)):
            calls=[p for m,p in self.rpc.calls if m=='eth_call' and p[0].get('to')==target and p[0].get('data')==calldata('decimals()')]
            self.assertEqual(len(calls),1)
        self.assertEqual(len([1 for m,_ in self.rpc.calls if m=='eth_getBalance']),2)
        self.rpc.put(addr(4),'claimable(uint256,address)',(self.rpc.nft_id,addr(21)),(0,))
        again=self.plan()
        self.assertEqual(again['entries'][0]['status'],'zero');self.assertIsNone(again['next_batch'])
        self.assertEqual(result['entries'][0]['status'],'in_next_batch')

    def test_attempt_and_shared_work_budgets_do_not_reset_or_drop_unassessed_rows(self):
        entries=self.many(32);self.rpc.maximum_batch=0
        result=self.plan(entries)
        self.assertIsNone(result['next_batch'])
        self.assertEqual(result['planning']['trial_count'],MAX_TRIALS)
        self.assertEqual(len(result['entries']),32);self.assertEqual(len(result['remaining_claims']),32)
        self.assertTrue(any(r['status']=='unassessed' for r in result['entries']))
        self.assertFalse(any(r['status']=='zero' for r in result['entries']))
        self.setUp()
        with request_scope(Budget(calls=3)),self.assertRaises(WorkLimit):self.plan()

    def test_reorg_staleness_and_expiry_abort_without_fallback_or_state_override(self):
        for mutate in (lambda:setattr(self.rpc,'fail_hash_pin',True),lambda:setattr(self,'now',2000)):
            self.setUp();self.rpc.after_simulation=mutate
            with self.assertRaises((RpcError,WorkLimit)):self.plan()
        self.assertTrue(all(len(params)<=2 for method,params in self.rpc.calls if method=='eth_call'))

    def test_input_selection_is_explicit_bounded_and_cannot_override_transaction_fields(self):
        invalid=[dict(action='mint',wallet=addr(30)),dict(action='claim',wallet=addr(30),claims=[]),
                 dict(action='claim',wallet=addr(30),claims=[self.entry(),self.entry()]),
                 dict(action='claim',wallet=addr(30),claims=self.many(33)),
                 dict(action='claim',wallet=addr(30),claims=[self.entry()],gas=20_000_000)]
        for payload in invalid:
            with self.subTest(payload=list(payload)),self.assertRaises(TransactionInputError):self.service.plan_claims(payload)
        self.assertFalse(self.rpc.calls)


class CurrentClaimPlannerTests(unittest.TestCase):
    def fixture(self,*,opened=True):
        f=current_fixtures.FrontendPolicyV6Tests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        f.config['royalty_reporting']={'schema':5,'converter':None}
        f.rpc.put(f.c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8').hex(),))
        f.rpc.put(f.c['royalties'],'ROYALTY_SETTLEMENT_VERSION()',values=(4,))
        f.rpc.put(f.c['royalties'],'royaltiesOpen()',values=(int(opened),))
        original=f.rpc.call;sent=[]
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:
                sent.append(copy.deepcopy(params));count=int(params[0]['data'][74:138],16)
                return words(32,count,*([17]*count))
            if method=='eth_estimateGas':return hex(200000)
            if method=='eth_gasPrice':return hex(10**9)
            if method=='eth_getBalance':return hex(10**18)
            return original(method,params)
        f.rpc.call=call;p=Projection(f.config,f.rpc,clock=lambda:1000)
        return f,p,Transactions(p,transaction_config(p)),sent

    def test_exact_current_profile_keeps_royalty_window_separate_from_available_lp(self):
        f,p,service,sent=self.fixture(opened=False)
        request=dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(f.rpc.nft_id),asset=ZERO,royalty=False),
            dict(token_id=str(f.rpc.nft_id),asset=ZERO,royalty=True)])
        result=service.plan_claims(request)
        self.assertEqual([r['status'] for r in result['entries']],['in_next_batch','blocked'])
        self.assertEqual(result['remaining_claims'][0]['reason'],'royalty_window_not_open')
        self.assertEqual(result['provenance']['accounting_version'],6)
        self.assertEqual(len(sent),2)

    def test_exact_current_profile_uses_original_currencies_and_no_oracle_calls(self):
        f,p,service,sent=self.fixture()
        f.base.outage()
        result=service.plan_claims(dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(f.rpc.nft_id),asset=ZERO,royalty=True)]))
        self.assertTrue(result['next_batch']['claim_operations'][0]['royalty'])
        self.assertEqual(result['next_batch']['claim_operations'][0]['asset'],ZERO)
        self.assertEqual(len(sent),2)
        self.assertTrue(all(params[1]=={'blockHash':f.rpc.hash,'requireCanonical':True} for params in sent))
        forbidden={calldata('marketSides(uint256)',7)[:10],calldata('currentLPValue(uint256)',f.rpc.nft_id)[:10]}
        self.assertFalse(any(m=='eth_call' and params[0]['data'][:10] in forbidden for m,params in f.rpc.calls))


if __name__=='__main__':unittest.main()
