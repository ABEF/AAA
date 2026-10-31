"""Price outages isolate valuation, never custody or funded claim reporting.

Actual Projection NFT/wallet bodies and physical inventory adapter execute with
synthetic pinned RPC/history evidence. No network, service, journal or signer.
"""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.service import Projection,ProjectionError,ZERO
from frontend_api.portfolio_v5 import ROLES,read_bucket
from keeper.compound_policy import observe
from tests_python.test_frontend_api import addr,words as encoded
from tests_python.test_frontend_portfolio_v5 import ProfileTranscript,fresh_configuration
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from tests_python.test_keeper_compound_range_policy import words
from zzz_ops.abi import calldata,keccak256
from zzz_ops.rpc import RpcError


class PhysicalResponses(dict):
    def __init__(self,original,physical,selected):
        super().__init__(original);self.physical=physical;self.selected=selected
    def __getitem__(self,key):
        if key in self.selected:
            target,method,args=self.selected[key]
            return '0x'+''.join(self.physical.read(target,method,*args))
        return super().__getitem__(key)


class PortfolioPriceOutageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.config,self.rpc=fresh_configuration()
        self.physical=PortfolioRPC(Path(self.tmp.name)/'inert-state.json')
        c={role:item['address'] for role,item in self.config['contracts'].items()}
        q=self.physical;q.contracts.update({role:c[role] for role in q.contracts if role in c})
        q.budget=c['budget'];q.posm=c['position_manager'];q.zzz=addr(20)
        q.config[1]=int(q.zzz,16);q.pool='0x'+keccak256(bytes.fromhex(''.join(words(*q.config[:5])))).hex()
        q.position[0]=int(q.pool,16);q.position[6]=0;q.now=self.rpc.header_timestamp
        for target in c.values():q.code_overrides[target]=self.rpc.codes[target]
        for target in (c['liquidity'],c['lp_position_executor'],c['position_manager']):
            q.overrides[target,'permit2()']=words(int(c['permit2'],16))
        # Exact fresh profile graph, without stubbing Projection verification.
        graph=ProfileTranscript()
        for role,method,target in graph.bindings:self.rpc.put(c[role],method,values=(c[target],))
        for role in ('pools','liquidity','strategy','budget','portfolio_policy','rebalance_confirmation','balancing_router','lp_position_executor'):
            self.rpc.put(c[role],'access()',values=(c['access'],))
        for role,label in (('pools','ZZZPoolRegistry'),('liquidity','ZZZLiquidityManager'),('strategy','ZZZStrategy')):
            self.rpc.put(c['access'],'module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(c[role],))
        for (role,method,args),value in graph.values.items():
            if method.endswith('VERSION()') or method in ('minimumMainBps()','maximumResidualBps()'):
                self.rpc.put(c[role],method,args,(value,))
        self.rpc.put(c['principal_exit'],'CUSTODY_VERSION()',values=(4,))
        self.rpc.put(c['vault'],'nftBucket(uint256)',(self.rpc.nft_id,),(7,))
        self.rpc.put(c['vault'],'bucketTotalShares(uint256)',(7,),(20*10**36,))
        self.rpc.put(c['nft'],'currentLPValue(uint256)',(self.rpc.nft_id,),(0,0))
        self.rpc.put(c['nft'],'balanceOf(address)',(addr(30),),(1,))
        # Current LP assets; USDC remains an independent optional royalty currency.
        self.rpc.put(c['rewards'],'assetCount()',values=(2,))
        self.rpc.put(c['rewards'],'assets(uint256)',(0,),(ZERO,))
        self.rpc.put(c['rewards'],'assets(uint256)',(1,),(q.zzz,))
        selected={}
        def add(role,method,*args):
            target=c.get(role,role);selected[target,calldata(method,*args)]=(target,method,args)
        for method in ('group(uint256)',):add('vault',method,7)
        for method in ('get(bytes32)','accounting(bytes32)'):add('pools',method,q.pool)
        add('vault','poolBucket(bytes32)',q.pool)
        add('state_view','getSlot0(bytes32)',q.pool)
        for method in ('rangeUpdatePending(uint256)',):add('strategy',method,7)
        for method in ('enabled(bytes32)','geometryRevision(bytes32)','residualSideBps(bytes32)'):
            add('portfolio_policy',method,q.pool)
        add('portfolio_policy','configurationPending(uint256)',7)
        add('portfolio_policy','appliedRevision(uint256)',123)
        add('liquidity','activeSecondaryCount()')
        for method in ('secondaryId(uint256)','portfolioFingerprint(uint256)','portfolioAmounts(uint256)'):
            add('liquidity',method,123)
        for identifier in (123,124):
            add('liquidity','ticks(uint256)',identifier);add('liquidity','amounts(uint256)',identifier)
            for method in ('getPoolAndPositionInfo(uint256)','ownerOf(uint256)','getPositionLiquidity(uint256)'):
                add('position_manager',method,identifier)
        add('rebalance_confirmation','marketSides(uint256)',7)
        add('rebalance_confirmation','requireReferenceExit()')
        self.rpc.responses=PhysicalResponses(self.rpc.responses,q,selected)
        self.p=Projection(self.config,self.rpc,clock=lambda:1000)
        self.block={'blockHash':self.rpc.hash,'requireCanonical':True}
        self.market_call=calldata('marketSides(uint256)',7)
        self.q=q

    def outage(self):
        self.q.overrides[self.q.contracts['rebalance_confirmation'],'marketSides(uint256)']=RpcError('reference USD feed unavailable')

    def test_full_nft_projection_keeps_owner_and_funded_claims_when_prices_fail(self):
        self.outage();self.q.secondary=124;self.q.secondary_count=1;self.q.summed=(130,240)
        result=self.p.nft(self.rpc.nft_id)
        self.assertEqual(addr(30),result['owner'])
        self.assertFalse(result['position']['current_lp_value']['available'])
        self.assertIsNone(result['position']['current_lp_value']['raw'])
        self.assertEqual('124',result['position']['local_custody']['portfolio']['secondary_lp_token_id'])
        self.assertEqual('17',result['claimable']['lp'][0]['raw'])
        self.assertEqual('33333333333333333333',result['claimable']['royalties'][0]['raw'])
        self.assertFalse(any(m=='eth_call' and x[0]['data']==self.market_call for m,x in self.rpc.calls))

    def test_wallet_projection_keeps_eth_total_independent_of_missing_usd(self):
        self.outage();self.p.history=object()
        history=SimpleNamespace(owners={self.rpc.nft_id:addr(30)})
        with patch.object(self.p,'_history_snapshot',return_value=history):
            result=self.p.wallet_summary(addr(30),99)
        self.assertIsNone(result['lp_usd_18'])
        self.assertEqual(str(17+33333333333333333333),result['claimable_eth_wei'])
        self.assertEqual([str(self.rpc.nft_id)],result['token_ids'])

    def test_physical_read_does_not_require_strategy_diagnostics_or_grant_readiness(self):
        self.outage()
        self.q.overrides[self.q.contracts['strategy'],'rangeUpdatePending(uint256)']=RpcError('maintenance diagnostic unavailable')
        result=observe(self.q.read,self.q.code,contracts={k:v['address'] for k,v in self.config['contracts'].items()},
            code_hashes={k:v['code_hash'] for k,v in self.config['contracts'].items()},bucket=7,
            accounting_version=5,physical_only=True)
        self.assertNotIn('allowed',result);self.assertNotIn('status',result)
        self.assertEqual('physical_portfolio_not_maintenance_eligibility',result['scope'])

    def test_default_keeper_observation_still_requires_healthy_reference(self):
        self.outage()
        with self.assertRaisesRegex(RpcError,'reference USD feed unavailable'):
            observe(self.q.read,self.q.code,contracts={k:v['address'] for k,v in self.config['contracts'].items()},
                code_hashes={k:v['code_hash'] for k,v in self.config['contracts'].items()},bucket=7,accounting_version=5)

    def test_price_outage_does_not_hide_invalid_secondary_custody(self):
        self.outage();self.q.secondary=124;self.q.secondary_count=1;self.q.summed=(130,240);self.q.fail_leg_owner=True
        with self.assertRaises(ProjectionError):self.p.nft(self.rpc.nft_id)

    def test_price_outage_does_not_hide_inconsistent_aggregate_principal(self):
        self.outage();self.q.secondary=124;self.q.secondary_count=1;self.q.summed=(100,200)
        with self.assertRaises(ProjectionError):self.p.nft(self.rpc.nft_id)

    def test_price_outage_does_not_hide_runtime_mismatch(self):
        self.outage();self.rpc.codes[self.config['contracts']['state_view']['address']]='0x6001'
        with self.assertRaises(ProjectionError):self.p.nft(self.rpc.nft_id)

    def test_physical_only_read_still_rejects_invalid_main_tick_geometry(self):
        self.outage()
        for lower,upper in ((100,-100),(-887280,100),(-100,887280)):
            with self.subTest(lower=lower,upper=upper):
                self.q.lower,self.q.upper=lower,upper
                with self.assertRaises(ProjectionError):self.p.nft(self.rpc.nft_id)


if __name__=='__main__':unittest.main()
