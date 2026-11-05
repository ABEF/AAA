"""Royalty window history/profile boundaries; synthetic, no chain or signing."""
import copy, json
from pathlib import Path
import unittest
from types import SimpleNamespace
from collections import defaultdict
from frontend_api.earnings import Earnings
from frontend_api.earnings_replay import Replay, ZERO
from frontend_api.history import HistoryError
from frontend_api.earnings_checkpoint import SHARED, encode, decode
from frontend_api.service import Projection, ProjectionError
from tests_python.test_earnings import init, activate, consume, event
from tests_python.test_frontend_api import MockRPC, configuration, addr, words
from tests_python.test_royalty_reporting import profile
from zzz_ops.abi import calldata
from zzz_ops import production_v10 as P
from zzz_ops import production_observer_v10 as O

class RoyaltyWindowReplayTests(unittest.TestCase):
    def model(self):
        m=Replay(100000,11);init(m)
        consume(m,event('royalties','MintEndConfigured',(),(1000,4600),15))
        activate(m,11,100,1,16)
        return m
    def test_initial_receipts_are_income_once_at_opening_not_early_claim_or_conversion(self):
        m=self.model();a=addr(21)
        consume(m,event('royalties','RoyaltiesReceived',(a,),(600,0),20))
        self.assertEqual(m.totals['royalties',a],0)
        consume(m,event('royalties','RoyaltyOpeningFinalized',(),(4600,1,1),87000))
        consume(m,event('royalties','InitialRoyaltiesAllocated',(a,),(600,1,1),87001))
        self.assertEqual(m.totals['royalties',a],600)
        self.assertEqual(m.totals['royalties_received',a],600)
        self.assertEqual(m.totals['royalties_recovered',a],0)
        activate(m,22,100,2,88000)
        consume(m,event('royalties','RoyaltiesReceived',(a,),(300,1),89000))
        self.assertEqual(m.totals['royalties',a],700)
    def test_repeated_initial_allocation_and_wrong_cohort_reject(self):
        for data in ((600,2,3),(600,1,2)):
            m=self.model();consume(m,event('royalties','RoyaltyOpeningFinalized',(),(4600,1,1),87000))
            with self.assertRaises(HistoryError):consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),data,87001))
        m=self.model();consume(m,event('royalties','RoyaltyOpeningFinalized',(),(4600,1,1),87000))
        consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),(600,1,1),87001))
        with self.assertRaises(HistoryError):consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),(600,1,1),87002))
    def test_window_fields_survive_checkpoint_encoding(self):
        m=self.model();consume(m,event('royalties','RoyaltyOpeningFinalized',(),(4600,1,1),87000))
        self.assertIn('royalty_opening',SHARED)
        state={k:getattr(m,k) for k in ('royalty_mint_end','royalty_opening','initial_royalty_allocations')}
        self.assertEqual(decode(encode(state)),state)

class RoyaltyWindowReportingTests(unittest.TestCase):
    def test_claim_reconciliation_includes_initial_pool_only_after_opening(self):
        for opened in (False,True):
            amounts={'pending(address)':2,'openingPool(address)':6,'claimable(uint256,address)':8 if opened else 0}
            p=SimpleNamespace(royalty_reporting=SimpleNamespace(schema=4),contracts={'royalties':SimpleNamespace(address=addr(5))},
                _uint=lambda role,sig,*a,**kw:amounts[sig],_call=lambda *a,**kw:[words(int(opened))[2:]])
            model=SimpleNamespace(nft_id=11,weights={11:1,22:2},cohorts={ZERO:{11,22}},activation_order=[11,22],
                royalty_opening=(4600,1,1),initial_royalty_allocations=set(),totals=defaultdict(int),scaled=defaultdict(int))
            financial={'previously_claimed':{'assets':[{'asset':ZERO,'lp_raw':'0','royalties_raw':'0'}]},
                'royalty_conversions':{'assets':[],'total_eth_credited_raw':'0'},
                'lp_conversions':{'assets':[],'total_eth_credited_raw':'0'}}
            Earnings.check_paid(p,model,financial,{},[],[ZERO])
    def fixture(self,opened=False):
        rpc=MockRPC();cfg=profile(configuration(),rpc,converter=False)
        cfg['royalty_reporting']={'schema':4,'converter':None}
        rpc.responses[addr(5),calldata('ROYALTY_SETTLEMENT_VERSION()')]=words(3)
        rpc.responses[addr(5),calldata('mintEnd()')]=words(1200)
        rpc.responses[addr(5),calldata('royaltiesOpenAt()')]=words(4800)
        rpc.responses[addr(5),calldata('royaltiesOpen()')]=words(int(opened))
        for a in (ZERO,addr(21)):
            data=calldata('effectiveEligibleCount(address)',addr(1) if a==ZERO else a)
            if a==ZERO:data=data[:-64]+'0'*64
            rpc.responses[addr(5),data]=words(5)
            claim=calldata('claimable(uint256,address)',rpc.nft_id,addr(1) if a==ZERO else a)
            if a==ZERO:claim=claim[:-64]+'0'*64
            if not opened:rpc.responses[addr(5),claim]=words(0)
        return cfg,rpc
    def test_explicit_window_is_reported_without_converter_or_keeper(self):
        c,rpc=self.fixture();v=Projection(c,rpc,clock=lambda:1000).nft(str(rpc.nft_id))['royalty_reporting']
        self.assertEqual(v['opening'],dict(configured=True,mint_end=1200,claims_open_at=4800,claims_open=False,activation_window_seconds=3600,status='locked'))
        self.assertFalse(v['converter']['enabled'])
    def test_old_runtime_or_inconsistent_deadline_cannot_masquerade_as_current(self):
        for sig,value in [('ROYALTY_SETTLEMENT_VERSION()',2),('royaltiesOpenAt()',87601)]:
            c,rpc=self.fixture();rpc.responses[addr(5),calldata(sig)]=words(value)
            with self.assertRaises(ProjectionError):Projection(c,rpc,clock=lambda:1000).nft(str(rpc.nft_id))
    def test_current_inventory_requires_new_explicit_profile(self):
        c=json.loads(Path('config/production.royalty3.example.json').read_text())
        self.assertEqual(c['schema_version'],12)
        self.assertEqual(P.expected_bindings(c['chains'][0])['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION'],3)
        c['schema_version']=11
        self.assertFalse(P.validate(c)['ready'])
    def test_current_observer_keeps_raw_only_classification_and_explicit_capacity(self):
        c=json.loads(Path('config/production.royalty3.example.json').read_text())
        o=O.Observer(object(),c['chains'][0])
        self.assertEqual(o.royalty_asset_maximum,65)
        self.assertEqual(o.raw_royalty_assets,P.raw_royalty_assets(c['chains'][0]))

if __name__=='__main__':unittest.main()
