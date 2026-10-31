"""Actual fresh Projection/unsigned mint against synthetic pinned RPCs."""
import copy
import unittest
from frontend_api.service import Projection,ProjectionError,Contract
from frontend_api.transactions import Transactions
from tests_python import test_portfolio_price_outage as historical_outage
from tests_python.test_protocol_policy_v6 import PolicyTranscript
from tests_python.test_frontend_api import addr
from tests_python.test_frontend_transactions import transaction_config
from zzz_ops.abi import keccak256,calldata
from zzz_ops.protocol_policy import VRF_FIELDS


class FrontendPolicyV6Tests(unittest.TestCase):
    def setUp(self):
        # Reuse historical fixture setup only, not its test methods/assertions.
        self.base=historical_outage.PortfolioPriceOutageTests();self.base.setUp();self.addCleanup(self.base.doCleanups)
        self.config,self.rpc,self.q=self.base.config,self.base.rpc,self.base.q
        c={role:item['address'] for role,item in self.config['contracts'].items()}
        self.policy=PolicyTranscript();self.policy.access=c['access'];target=self.policy.target
        self.rpc.codes[target]=self.policy.code
        self.config['contracts']['protocol_policy']=dict(address=target,code_hash=self.policy.digest)
        self.config.update(accounting_version=6,protocol_policy_version=1)
        self.rpc.put(c['access'],'protocolPolicy()',values=(target,))
        self.rpc.put(target,'access()',values=(c['access'],));self.rpc.put(target,'PROTOCOL_POLICY_VERSION()',values=(1,))
        self.rpc.put(c['vault'],'ACCOUNTING_VERSION()',values=(6,))
        self.rpc.put(c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_ADAPTABLE_POLICY_V6').hex(),))
        for role in ('liquidity','strategy','portfolio_policy'):
            self.rpc.put(c[role],'PORTFOLIO_VERSION()',values=(2,))
            self.q.overrides[c[role],'PORTFOLIO_VERSION()']=[f'{2:064x}']
        for getter,value in (('minimumMainBps(bytes32)',7000),('maximumResidualBps(bytes32)',3000),('residualGapSpacings(bytes32)',3)):
            self.q.overrides[c['portfolio_policy'],getter]=[f'{value:064x}']
            self.rpc.put(c['portfolio_policy'],getter,(self.q.pool,),(value,))
        self.q.overrides[c['vault'],'ACCOUNTING_VERSION()']=[f'{6:064x}']
        for method,words in self.policy.values.items():self.rpc.put(target,method,values=tuple(int(w,16) for w in words))
        self.p=Projection(self.config,self.rpc,clock=lambda:1000);self.c=c

    def test_nft_policy6_preserves_raw_claims_and_both_physical_legs_during_usd_outage(self):
        self.base.outage();self.q.secondary=124;self.q.secondary_count=1;self.q.summed=(130,240)
        result=self.p.nft(self.rpc.nft_id)
        self.assertEqual(addr(30),result['owner']);self.assertFalse(result['position']['current_lp_value']['available'])
        portfolio=result['position']['local_custody']['portfolio']
        self.assertEqual(2,portfolio['version']);self.assertEqual(7000,portfolio['minimum_main_bps'])
        self.assertEqual(3,portfolio['residual_gap_spacings']);self.assertEqual('124',portfolio['secondary_lp_token_id'])
        self.assertEqual('17',result['claimable']['lp'][0]['raw'])
        self.assertEqual('33333333333333333333',result['claimable']['royalties'][0]['raw'])

    def test_dynamic_evolution_follows_captured_metadata_terms_not_old_constants(self):
        self.rpc.put(self.c['nft'],'currentLPValue(uint256)',(self.rpc.nft_id,),(1,1500*10**18))
        result=self.p.nft(self.rpc.nft_id)
        self.assertEqual('activated',result['position']['evolution'])
        self.policy.set('metadata',(1200*10**18,12000*10**18,5))
        for method in ('metadataPolicy()','metadataFingerprint()'):
            self.rpc.put(self.policy.target,method,values=tuple(int(w,16) for w in self.policy.values[method]))
        result=self.p.nft(self.rpc.nft_id)
        self.assertEqual('enhanced',result['position']['evolution'])

    def mint_fixture(self):
        target=self.policy.target;sale=self.policy.values['salePolicy()'];revision=4
        random=(int(addr(950),16),3,4,5,3,400000,0,2,1,7)
        raw=''.join(f'{v:064x}' for v in random)
        fingerprint='0x'+keccak256(bytes.fromhex(f'{int(target,16):064x}'+''.join(sale)+f'{revision:064x}'+raw)).hex()
        for method,values in (('vrfPolicy()',random),('vrfRevision()',(revision,)),('mintFingerprint()',(fingerprint,))):self.rpc.put(target,method,values=values)
        self.rpc.put(self.c['vault'],'mintPolicyFingerprint()',values=(fingerprint,))
        self.rpc.put(self.c['vault'],'mintPrice()',values=(int(sale[0],16),))
        self.rpc.put(self.c['vault'],'mintProceedsRecipient()',values=(addr(900),))
        self.rpc.put(self.c['nft'],'MAX_SUPPLY()',values=(1000,))
        self.rpc.put(self.c['nft'],'mintedCount()',values=(1,))
        self.sent=[];original=self.rpc.call
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:
                self.assertEqual({'blockHash':self.rpc.hash,'requireCanonical':True},params[1]);self.sent.append(copy.deepcopy(params[0]))
                return '0x'+f'{self.rpc.nft_id:064x}'
            if method=='eth_estimateGas':return hex(150000)
            if method=='eth_gasPrice':return hex(10**9)
            if method=='eth_getBalance':return hex(10**18)
            return original(method,params)
        self.rpc.call=call
        return fingerprint,int(sale[0],16)

    def test_actual_mint_preparation_uses_dynamic_price_recipient_and_combined_fingerprint(self):
        fingerprint,price=self.mint_fixture();service=Transactions(self.p,transaction_config(self.p))
        result=service.prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(calldata('mintDormant(bytes32)',fingerprint),result['transaction']['data'])
        self.assertEqual(hex(price),result['transaction']['value']);self.assertNotEqual(hex(5*10**16),result['transaction']['value'])
        self.assertEqual(1,len(self.sent));self.assertEqual(addr(900),result['mint_policy']['recipient'])
        self.assertEqual([],result['claim_operations'])
        self.assertEqual('4',result['mint_policy']['vrf_revision']);self.assertTrue(result['wallet_revalidation_required'])

    def test_mint_rejects_stale_combined_vrf_fingerprint_before_simulation(self):
        self.mint_fixture();self.rpc.put(self.policy.target,'vrfRevision()',values=(5,))
        with self.assertRaises(ProjectionError):Transactions(self.p,transaction_config(self.p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual([],self.sent)
