"""Original-currency royalty2 boundaries; synthetic data, no signing or RPC."""
import copy,json
from pathlib import Path
from types import SimpleNamespace
import unittest
from frontend_api.earnings_replay import Replay,ZERO
from frontend_api.history import HistoryError
from frontend_api.service import Projection,ProjectionError
from keeper.royalties import RoyaltyAutomation
from tests_python.test_earnings import init,activate,consume,event
from tests_python.test_frontend_api import MockRPC,configuration,addr,words
from tests_python.test_royalty_reporting import profile
from zzz_ops.abi import calldata
from zzz_ops import production_v9 as P, production_observer_v9 as O
from tests_python import production_v7_fixtures as F

class OriginalCurrencyReplayTests(unittest.TestCase):
    def model(self):
        m=Replay(1000,11);init(m);activate(m,11,100,1);activate(m,22,100,2,14);return m
    def test_original_allocation_stays_in_its_currency_and_is_not_a_second_receipt(self):
        m=self.model();a=addr(21)
        consume(m,event('royalties','UnallocatedRoyaltiesAllocated',(a,),(300,3,1),20))
        self.assertEqual(m.totals['royalties',a],100)
        self.assertEqual(m.totals['royalties',ZERO],0)
        self.assertEqual(m.totals['royalties_recovered',a],300)
        self.assertEqual(m.totals['royalties_received',a],0)
    def test_native_and_erc20_allocations_are_independent(self):
        m=self.model()
        for a,n in [(ZERO,600),(addr(21),300)]:
            consume(m,event('royalties','UnallocatedRoyaltiesAllocated',(a,),(n,3,1),20))
        self.assertEqual(m.totals['royalties',ZERO],200)
        self.assertEqual(m.totals['royalties',addr(21)],100)
    def test_wrong_weight_unknown_asset_zero_review_and_frozen_state_reject(self):
        for a,data in [(addr(999),(3,3,1)),(addr(21),(3,2,1)),(addr(21),(0,3,1)),(addr(21),(3,3,0))]:
            with self.subTest(a=a,data=data),self.assertRaises(HistoryError):
                consume(self.model(),event('royalties','UnallocatedRoyaltiesAllocated',(a,),data,20))
        m=self.model();consume(m,event('handoff','Frozen',('0x'+'1'*64,addr(200)),(),19))
        with self.assertRaises(HistoryError):consume(m,event('royalties','UnallocatedRoyaltiesAllocated',(addr(21),),(3,3,1),20))

class OriginalCurrencyReportingTests(unittest.TestCase):
    def fixture(self):
        rpc=MockRPC();cfg=profile(configuration(),rpc,converter=False)
        cfg['royalty_reporting']={'schema':3,'converter':None}
        rpc.responses[addr(5),calldata('ROYALTY_SETTLEMENT_VERSION()')]=words(2)
        return cfg,rpc
    def test_original_balances_are_claimable_and_not_waiting_for_conversion(self):
        c,rpc=self.fixture();result=Projection(c,rpc,clock=lambda:1000).nft(str(rpc.nft_id));v=result['royalty_reporting']
        self.assertEqual(v['schema'],3);self.assertFalse(v['converter']['enabled'])
        self.assertTrue(all(x['settlement_mode']=='original_currency' and not x['conversion_required'] and x['unconverted_raw'] is None for x in result['claimable']['royalties']))
    def test_legacy_converter_or_missing_new_capability_is_not_silently_adopted(self):
        c,rpc=self.fixture();c['royalty_reporting']['converter']={'address':addr(90),'code_hash':'0x'+'1'*64}
        with self.assertRaises(ValueError):Projection(c,rpc,clock=lambda:1000)
        c,rpc=self.fixture();rpc.responses[addr(5),calldata('ROYALTY_SETTLEMENT_VERSION()')]=words(1)
        with self.assertRaises(ProjectionError):Projection(c,rpc,clock=lambda:1000).nft(str(rpc.nft_id))
    def test_raw_claims_need_no_price_or_swap_route_configuration(self):
        c,rpc=self.fixture();p=Projection(c,rpc,clock=lambda:1000)
        result=p.nft(str(rpc.nft_id))
        self.assertTrue(result['royalty_reporting']['balances_complete'])
        self.assertTrue(any(int(x['raw'])>0 for x in result['claimable']['royalties']))
    def test_fresh_native_currency_cannot_fall_into_historical_custody_deferral(self):
        from tests_python.test_royalty_reporting import native_data
        c,rpc=self.fixture()
        rpc.responses[addr(5),native_data('eligibleCount(address)',ZERO)]=words(4)
        with self.assertRaisesRegex(ProjectionError,'native eligibility mismatch'):
            Projection(c,rpc,clock=lambda:1000).nft(str(rpc.nft_id))

class OriginalCurrencyKeeperTests(unittest.TestCase):
    def test_fresh_submission_blocks_swap_before_any_nonce_or_signing_work(self):
        from keeper.monitor import Keeper
        from keeper.royalties import BATCH
        k=SimpleNamespace(state={},royalty_settlement_version=2)
        with self.assertRaisesRegex(ValueError,'cannot be swapped'):
            Keeper.submit(k,'royalties',BATCH,(),'unexpected')
        self.assertEqual(k.state,{})
        k.state['pending']={'original':'evidence'}
        self.assertFalse(Keeper.submit(k,'royalties',BATCH,(),'unexpected'))
        self.assertEqual(k.state['pending'],{'original':'evidence'})
    def test_fresh_worker_refuses_enabled_royalty_swapping_or_hidden_routes(self):
        for cfg in [{'enabled':True},{'enabled':False,'assets':[]}]:
            k=SimpleNamespace(config={'royalty_conversion':cfg},royalty_settlement_version=2)
            with self.assertRaises(ValueError):RoyaltyAutomation(k)
    def test_fresh_profile_needs_no_converter_and_legacy_default_stays_disabled(self):
        for version in (0,2):
            k=SimpleNamespace(config={},royalty_settlement_version=version)
            self.assertFalse(RoyaltyAutomation(k).enabled)

def fresh_inventory():
    c=F.fixture();c.update(P.VERSIONS);chain=c['chains'][0]
    for name in ('royalty_converter','royalty_v4_executor'):del chain['helpers'][name]
    del chain['execution_loss_policy']['royalty_conversion_bps']
    chain['conversion_routes']=[x for x in chain['conversion_routes'] if x['role']=='lp']
    for role,profile_name in P.SERVICE_PROFILES.items():
        chain['services'][role]['profile']=profile_name;chain['services'][role]['evidence']['profile']=profile_name
    for group,records in P.expected_bindings(chain).items():
        for role,b in records.items():
            chain[group][role]['observed_bindings']=copy.deepcopy(b)
            if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(b)
    return c

class OriginalCurrencyInventoryTests(unittest.TestCase):
    def test_admitted_royalty_only_currency_needs_no_swap_route_or_usd_feed(self):
        c=fresh_inventory();chain=c['chains'][0];asset=addr(9001)
        token=copy.deepcopy(next(x for x in chain['tokens'] if x['address']!=ZERO))
        token.update(address=asset,price_policy=None);chain['tokens'].append(token)
        inv=chain['nft_inventory']['royalty_assets'];row=copy.deepcopy(inv['assets'][0])
        row.update(address=asset,observed_asset=asset,strategy='claim_original');inv['assets'].append(row)
        inv['asset_count']=inv['observed_asset_count']=2
        v=P.validate(c,now=F.NOW)
        self.assertEqual([x['code'] for x in v['issues']],['mint.opensea_unsupported'])
        self.assertIn(asset,P.raw_royalty_assets(chain))
        # The exemption cannot leak into financial uses of the same currency.
        chain['conversion_routes'].append({'role':'lp','source_asset':asset})
        self.assertNotIn(asset,P.raw_royalty_assets(chain))
        self.assertTrue(any(x['code']=='pricing.policy' for x in P.validate(c,now=F.NOW)['issues']))
    def test_observer_skips_only_explicit_raw_only_prices_and_keeps_metadata_checks(self):
        asset=addr(9001);o=object.__new__(O.Observer);o.pricing_version=2;o.errors=[]
        o.chain={'modules':{'oracle':{'address':addr(3)}},'tokens':[
            {'address':asset,'decimals':6,'runtime_hash':F.RUNTIME,'price_policy':None}]}
        o.raw_royalty_assets={asset};o.code=lambda a:F.RUNTIME
        o.read=lambda a,sig:[f'{6:064x}'];o.attempt=lambda p,c,f:f()
        calls=[];o.dual_price=lambda *a:calls.append(a)
        o.tokens();self.assertEqual(calls,[]);self.assertEqual(o.chain['tokens'][0]['observed_decimals'],6)
        o.raw_royalty_assets=set();o.tokens();self.assertEqual(len(calls),1)
    def test_current_observer_reads_raw_capability_without_removed_wrapper_roles(self):
        from unittest.mock import patch
        with patch.object(F.H.H.F.old,'HASH',F.RUNTIME),patch.object(P.V,'NATIVE_DEPENDENCIES',{
                role:(a,F.RUNTIME) for role,(a,_h) in P.V.NATIVE_DEPENDENCIES.items()}):
            c=fresh_inventory();rpc=F.RPC(c);rpc.expected=P.expected_bindings(rpc.chain)
            seen=O.observe(c,rpc)
            self.assertTrue(seen['chains'][0]['observation']['complete'],seen['chains'][0]['observation']['errors'])
            self.assertFalse(P.validate(seen,now=F.NOW)['ready'])
    def test_new_inventory_authenticates18_helpers_and_raw_capability(self):
        c=fresh_inventory();v=P.validate(c,expected_commit=F.COMMIT,now=F.NOW)
        self.assertEqual(len(P.HELPERS),18)
        self.assertEqual([x['code'] for x in v['issues']],['mint.opensea_unsupported'])
        self.assertFalse(v['ready']);self.assertFalse(v['deployment_authorized'])
    def test_removed_converter_routes_and_loss_policy_cannot_be_reintroduced(self):
        c=fresh_inventory();c['chains'][0]['execution_loss_policy']['royalty_conversion_bps']=100
        self.assertTrue(any(i['code']=='royalty.original_currency' for i in P.validate(c,now=F.NOW)['issues']))
        c=fresh_inventory();c['chains'][0]['conversion_routes']=[{'role':'royalty'}]
        with self.assertRaises(ValueError):O.observe(c,object())
    def test_old_inventory_is_not_relabelled_by_current_observer(self):
        c=F.fixture()
        with self.assertRaises(ValueError):O.observe(c,object())
    def test_current_template_remains_unapproved_with_no_royalty_converters(self):
        c=json.loads((Path(__file__).resolve().parents[1]/'config/production.example.json').read_text())
        self.assertEqual(c['schema_version'],11);self.assertEqual(set(c['chains'][0]['helpers']),set(P.HELPERS))
        self.assertFalse(P.validate(c,now=F.NOW)['ready'])

if __name__=='__main__':unittest.main()
