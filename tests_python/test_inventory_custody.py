"""Full current6 projections reject contradictory custody without price guesses."""
from unittest.mock import patch
import unittest

from frontend_api.service import ProjectionError
from frontend_api.history import HistorySnapshot
from tests_python.test_frontend_api import addr
from tests_python.test_frontend_policy_v6 import FrontendPolicyV6Tests
from tests_python.test_wallet_summary import Snapshot, OWNER
from frontend_api.portfolio import read as wallet_read


class InventoryCustodyTests(unittest.TestCase):
    def setUp(self):
        self.fixture=FrontendPolicyV6Tests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f=self.fixture;self.p=f.p;self.identifier=f.rpc.nft_id
        for method,args,values in (('mintedCount()',(),(1,)),
                ('mintOrdinalOf(uint256)',(self.identifier,),(1,)),
                ('tokenAtOrdinal(uint256)',(1,),(self.identifier,))):
            f.rpc.put(f.c['nft'],method,args,values)
        self.p.history=object()
        history=HistorySnapshot(owners={self.identifier:addr(30)},claims={},
            provenance={},conversions={})
        self.history=patch.object(self.p,'_history_snapshot',return_value=history)
        self.history.start();self.addCleanup(self.history.stop)

    def test_active_share_numerator_above_bucket_denominator_rejects_every_projection(self):
        f=self.fixture
        f.rpc.put(f.c['vault'],'sharesOf(uint256)',(self.identifier,),(20*10**36+1,))
        for name,call in self.projections():
            with self.subTest(endpoint=name),self.assertRaisesRegex(ProjectionError,'canonical custody'):
                call()

    def test_parked_nft_cannot_reuse_an_active_bucket_even_when_lp_value_unavailable(self):
        f=self.fixture
        f.rpc.put(f.c['vault'],'nftStatus(uint256)',(self.identifier,),(4,))
        for name,call in self.projections():
            with self.subTest(endpoint=name),self.assertRaisesRegex(ProjectionError,'canonical custody'):
                call()

    def test_price_outage_keeps_exact_funded_balances_and_collection_ownership(self):
        self.fixture.base.outage()
        detail=self.p.nft(self.identifier)
        collection=self.p.collection(99)
        wallet=self.p.wallet_summary(addr(30),99)
        self.assertFalse(detail['position']['current_lp_value']['available'])
        self.assertEqual('17',detail['claimable']['lp'][0]['raw'])
        self.assertEqual(addr(30),collection['positions'][0]['owner'])
        self.assertIsNone(collection['chunk_lp_usd_18'])
        self.assertIsNone(wallet['lp_usd_18'])
        self.assertEqual(str(17+33333333333333333333),wallet['claimable_eth_wei'])

    def test_bucket_reads_are_cached_but_each_nft_share_is_checked(self):
        p=Snapshot(16)
        wallet_read(p,OWNER,90,0)
        self.assertEqual(1,sum(name=='group(uint256)' for name,_,_ in p.calls))
        self.assertEqual(1,sum(name=='bucketTotalShares(uint256)' for name,_,_ in p.calls))
        self.assertEqual(16,sum(name=='sharesOf(uint256)' for name,_,_ in p.calls))
        original=p._uint
        def bad(role,method,*args,**kwargs):
            if method=='sharesOf(uint256)' and args==(16,):return 17
            return original(role,method,*args,**kwargs)
        p._uint=bad
        with self.assertRaisesRegex(ProjectionError,'canonical custody'):
            wallet_read(p,OWNER,90,0)

    def test_terminal_return_remains_separate_from_rewards_and_has_no_stale_idle(self):
        f=self.fixture;c=f.c
        f.rpc.put(c['access'],'lpExitStarted()',values=(1,))
        f.rpc.put(c['principal_exit'],'exitPhase()',values=(3,))
        f.rpc.put(c['vault'],'nftStatus(uint256)',(self.identifier,),(5,))
        f.q.position[1]=0;f.q.position[2]=0;f.q.position[3]=0;f.q.position[7]=5
        f.rpc.put(c['nft'],'currentLPValue(uint256)',(self.identifier,),(1,0))
        f.rpc.put(c['principal_exit'],'principalOf(uint256)',(self.identifier,),(123,456,1,0))
        f.rpc.put(c['principal_exit'],'claimablePrincipal(uint256)',(self.identifier,),(123,456))
        detail=self.p.nft(self.identifier)
        collection=self.p.collection(99)
        wallet=self.p.wallet_summary(addr(30),99)
        self.assertEqual('lp_exited',detail['position']['evolution'])
        self.assertEqual('123',collection['positions'][0]['principal_return']['assets'][0]['claimable_raw'])
        self.assertEqual('0',collection['chunk_lp_usd_18'])
        self.assertEqual('0',wallet['lp_usd_18'])
        self.assertEqual(str(17+33333333333333333333),wallet['claimable_eth_wei'])
        f.q.position[2]=1
        for name,call in self.projections():
            with self.subTest(endpoint=name),self.assertRaisesRegex(ProjectionError,'canonical custody'):
                call()

    def test_distinct_partial_shares_cannot_exceed_bucket_total_in_any_local_state(self):
        f=self.fixture;c=f.c;rpc=f.rpc;first=self.identifier;second=first+1
        for method,args,values in (('mintedCount()',(),(2,)),
                ('mintOrdinalOf(uint256)',(second,),(2,)),('tokenAtOrdinal(uint256)',(2,),(second,)),
                ('ownerOf(uint256)',(second,),(addr(30),)),('traitsReady(uint256)',(second,),(1,)),
                ('rarityOf(uint256)',(second,),(1,)),('paletteOf(uint256)',(second,),(24,)),
                ('patternOf(uint256)',(second,),(2,)),('balanceOf(address)',(addr(30),),(2,))):
            rpc.put(c['nft'],method,args,values)
        rpc.put(c['vault'],'nftBucket(uint256)',(second,),(7,))
        rpc.put(c['royalties'],'weightOf(uint256)',(second,),(2,))
        zero='0x'+'0'*40
        for role in ('rewards','royalties'):
            rpc.put(c[role],'claimable(uint256,address)',(second,zero),(0,))
        history=HistorySnapshot(owners={first:addr(30),second:addr(30)},claims={},
            provenance={},conversions={})
        with patch.object(self.p,'_history_snapshot',return_value=history):
            for status in (1,4,5):
                f.q.position[1]=123 if status==1 else 0;f.q.position[7]=status
                rpc.put(c['access'],'lpExitStarted()',values=(int(status==5),))
                rpc.put(c['principal_exit'],'exitPhase()',values=(3 if status==5 else 0,))
                for identifier in (first,second):
                    rpc.put(c['vault'],'sharesOf(uint256)',(identifier,),(11*10**36,))
                    rpc.put(c['vault'],'nftStatus(uint256)',(identifier,),(status,))
                    rpc.put(c['nft'],'currentLPValue(uint256)',(identifier,),(int(status==5),0))
                    rpc.put(c['principal_exit'],'principalOf(uint256)',(identifier,),(0,0,int(status==5),0))
                    if status==5:
                        rpc.put(c['principal_exit'],'claimablePrincipal(uint256)',(identifier,),(0,0))
                for name,call in (('collection',lambda:self.p.collection(99)),
                        ('wallet',lambda:self.p.wallet_summary(addr(30),99))):
                    with self.subTest(status=status,endpoint=name),self.assertRaisesRegex(ProjectionError,'Inventory shares exceed'):
                        call()
                # 9+11 exactly equals the admitted20e36 denominator: valid partial
                # inventories are accepted, without needing every collection NFT.
                rpc.put(c['vault'],'sharesOf(uint256)',(first,),(9*10**36,))
                self.assertEqual(2,len(self.p.collection(99)['positions']))
                self.assertEqual(2,self.p.wallet_summary(addr(30),99)['count'])

    def projections(self):
        return (('nft',lambda:self.p.nft(self.identifier)),
                ('collection',lambda:self.p.collection(99)),
                ('wallet',lambda:self.p.wallet_summary(addr(30),99)))


if __name__=='__main__':unittest.main()
