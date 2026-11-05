"""Confirmed sale-window readiness; no balances, prices or transaction signing."""
import unittest

from frontend_api.service import Projection, ProjectionError
from tests_python import test_mint_sale_end_review as mint_fixtures
from tests_python.test_frontend_api import addr
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError


class MintWindowReadinessTests(unittest.TestCase):
    def fixture(self,end=1200,timestamp=990,*,schema=5,revision=7,minted=1):
        owner=mint_fixtures.MintSaleEndReviewTests('runTest')
        f,_p,*_=owner.fixture(end,revision)
        self.addCleanup(owner.doCleanups)
        f.config['royalty_reporting']={'schema':schema,'converter':None}
        domain=b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8' if schema==5 else b'ZZZ_CANONICAL_SAME_CHAIN_ROYALTY_OPENING_V7'
        f.rpc.put(f.c['handoff'],'SCHEMA()',values=('0x'+keccak256(domain).hex(),))
        f.rpc.put(f.c['royalties'],'ROYALTY_SETTLEMENT_VERSION()',values=(schema-1,))
        f.rpc.header_timestamp=timestamp
        next_ordinal=minted+1
        quotas=(600,299,100) if minted==1 else (0,0,0) if minted==1000 else (600,300,100)
        for sig,value in [('mintedCount()',minted),('nextToFinalize()',next_ordinal),
                          ('remainingToReveal()',sum(quotas)),('randomnessConfigured()',1),
                          ('randomnessCoordinator()',addr(950))]:
            f.rpc.put(f.c['nft'],sig,values=(value,))
        for i,value in enumerate(quotas):f.rpc.put(f.c['nft'],'rarityRemaining(uint256)',(i,),(value,))
        return f,Projection(f.config,f.rpc,clock=lambda:timestamp+1)

    def test_before_at_after_and_unset_sale_end_have_exact_snapshot_status(self):
        for end,timestamp,revision,available,status in [
                (1200,1199,7,True,'open'),(1200,1200,7,True,'open'),
                (1200,1201,7,False,'closed'),(0,990,0,False,'unconfigured')]:
            f,p=self.fixture(end,timestamp,revision=revision)
            ready=p.mint_readiness();mint=p.protocol()['minting']
            with self.subTest(end=end,timestamp=timestamp):
                self.assertEqual(ready['new_minting_stopped_by_sale_window'],not available)
                self.assertEqual(ready['new_minting_stopped'],not available)
                self.assertEqual(ready['sale_window']['status'],status)
                self.assertEqual(ready['sale_window']['mint_end_revision'],revision)
                self.assertTrue(mint['available_by_controls'])
                self.assertEqual(mint['available_by_sale_window'],available)
                self.assertEqual(mint['available'],available)
                self.assertEqual(mint['sale_window'],ready['sale_window'])

    def test_sold_out_or_paused_is_not_reported_available_even_when_window_open(self):
        f,p=self.fixture(minted=1000)
        self.assertTrue(p.mint_readiness()['new_minting_stopped_by_supply'])
        mint=p.protocol()['minting']
        self.assertTrue(mint['available_by_sale_window'])
        self.assertFalse(mint['available_by_supply']);self.assertFalse(mint['available'])
        f,p=self.fixture();f.rpc.put(f.c['nft'],'mintPaused()',values=(1,))
        mint=p.protocol()['minting'];self.assertFalse(mint['available_by_controls'])
        self.assertTrue(mint['available_by_sale_window']);self.assertFalse(mint['available'])

    def test_reporting4_sale_window_does_not_probe_new_revision_getter(self):
        f,p=self.fixture(schema=4);original=f.rpc.call
        def call(method,params):
            if method=='eth_call' and params[0]['data']==calldata('mintEndRevision()'):
                raise AssertionError('Historical royalty3 has no new revision getter')
            return original(method,params)
        f.rpc.call=call
        self.assertTrue(p.protocol()['minting']['available'])
        window=p.mint_readiness()['sale_window']
        self.assertTrue(window['available']);self.assertNotIn('mint_end_revision',window)

    def test_missing_core_window_read_cannot_be_guessed_open_or_unconfigured(self):
        for getter in ('mintEnd()','mintEndRevision()'):
            f,p=self.fixture();original=f.rpc.call
            def call(method,params):
                if method=='eth_call' and params[0]['to']==f.c['royalties'] and params[0]['data']==calldata(getter):
                    raise RpcError('Synthetic unavailable sale control')
                return original(method,params)
            f.rpc.call=call
            for read in (p.protocol,p.mint_readiness):
                with self.subTest(getter=getter),self.assertRaises(RpcError):read()

    def test_wrong_capability_or_invalid_uint64_window_fields_fail_closed(self):
        for getter,value in [('ROYALTY_SETTLEMENT_VERSION()',3),('mintEnd()',2**64),
                             ('mintEndRevision()',2**64),('mintEndRevision()',0)]:
            f,p=self.fixture();f.rpc.put(f.c['royalties'],getter,values=(value,))
            for read in (p.protocol,p.mint_readiness):
                with self.subTest(getter=getter,value=value),self.assertRaises(ProjectionError):read()

    def test_closed_import_can_report_local_zero_revision_without_reopening_sale(self):
        _,p=self.fixture(end=1200,timestamp=1201,revision=0)
        self.assertTrue(p.mint_readiness()['new_minting_stopped_by_sale_window'])
        self.assertFalse(p.protocol()['minting']['available'])

    def test_sale_readiness_never_queries_token_balance_or_price(self):
        f,p=self.fixture();original=f.rpc.call
        forbidden={calldata('claimable(uint256,address)',1,addr(1))[:10],
                   calldata('priceBounds(address)',addr(1))[:10],calldata('price(address)',addr(1))[:10]}
        balance=calldata('balanceOf(address)',addr(1))[:10]
        def call(method,params):
            if method=='eth_call':
                selector=params[0]['data'][:10]
                if selector in forbidden or params[0]['to'] in (addr(20),addr(21)) and selector==balance:
                    raise AssertionError('Sale readiness depended on optional funds or market prices')
            return original(method,params)
        f.rpc.call=call
        self.assertTrue(p.protocol()['minting']['available'])
        self.assertFalse(p.mint_readiness()['new_minting_stopped'])


if __name__=='__main__':unittest.main()
