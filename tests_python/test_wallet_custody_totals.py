"""Wallet totals must agree with custody, not only accept a numeric quote."""
import unittest

from frontend_api.portfolio import read
from frontend_api.service import ProjectionError
from tests_python.test_wallet_summary import Snapshot, OWNER
from zzz_ops.errors import RpcError


class CustodySnapshot(Snapshot):
    def __init__(self):
        super().__init__(1)
        self.accounting_version=4;self.dormant_status=3
        self.status=1;self.valuation=(True,100);self.exited=False

    def _verify_deployment(self,block):
        return {'state':'operating','lp_exit_started':self.exited}

    def _uint(self,role,method,*args,block):
        if method=='nftStatus(uint256)':
            self.calls.append((method,args,block));self.check(block);return self.status
        if method=='claimable(uint256,address)' and self.weights[args[0]]==0:
            self.calls.append((method,args,block));self.check(block);return 0
        return super()._uint(role,method,*args,block=block)

    def _call(self,target,method,i,*,block,words):
        self.calls.append((method,(i,),block));self.check(block)
        if isinstance(self.valuation,Exception):raise self.valuation
        available,amount=self.valuation
        return [f'{int(available):064x}',f'{amount:064x}']


class WalletCustodyTotalsTests(unittest.TestCase):
    def test_parked_or_outbound_cannot_be_reported_as_known_lp_even_at_zero(self):
        for version in (3,4):
            for status in (2,4):
                for amount in (0,100):
                    with self.subTest(version=version,status=status,amount=amount):
                        p=CustodySnapshot();p.accounting_version=version;p.status=status;p.valuation=(True,amount)
                        with self.assertRaises(ProjectionError):read(p,OWNER,90,0)

    def test_parked_and_outbound_keep_funded_rewards_but_lp_total_unavailable(self):
        for status in (2,4):
            with self.subTest(status=status):
                p=CustodySnapshot();p.status=status;p.valuation=(False,0)
                result=read(p,OWNER,90,0)
                self.assertIsNone(result['lp_usd_18']);self.assertEqual('5',result['claimable_eth_wei'])

    def test_unknown_or_noncanonical_owned_status_cannot_make_a_wallet_total(self):
        for status in (0,6,2**256-1,True):
            with self.subTest(status=status):
                p=CustodySnapshot();p.status=status
                with self.assertRaises(ProjectionError):read(p,OWNER,90,0)

    def test_profile3_cannot_silently_accept_the_profile4_exited_code(self):
        p=CustodySnapshot();p.accounting_version=3;p.status=5;p.exited=True;p.valuation=(True,0)
        with self.assertRaises(ProjectionError):read(p,OWNER,90,0)

    def test_dormant_status_and_permanent_royalty_eligibility_must_agree(self):
        for status,weight in ((3,1),(1,0),(4,0),(5,0)):
            with self.subTest(status=status,weight=weight):
                p=CustodySnapshot();p.status=status;p.weights[1]=weight;p.valuation=(True,0);p.exited=True
                with self.assertRaises(ProjectionError):read(p,OWNER,90,0)

    def test_dormant_explicit_unavailable_response_is_contradictory_not_zero(self):
        p=CustodySnapshot();p.status=3;p.weights[1]=0;p.valuation=(False,0)
        with self.assertRaises(ProjectionError):read(p,OWNER,90,0)

    def test_dormant_known_zero_and_exited_known_zero_keep_distinct_rights(self):
        p=CustodySnapshot();p.status=3;p.weights[1]=0;p.valuation=(True,0)
        self.assertEqual(('0','0'),tuple(read(p,OWNER,90,0)[k] for k in ('lp_usd_18','claimable_eth_wei')))
        p=CustodySnapshot();p.status=5;p.exited=True;p.valuation=(True,0)
        result=read(p,OWNER,90,0)
        self.assertEqual('0',result['lp_usd_18']);self.assertEqual('5',result['claimable_eth_wei'])

    def test_real_valuation_outage_keeps_independent_eth_metric_and_same_block(self):
        p=CustodySnapshot();p.valuation=RpcError('inert LP read unavailable')
        result=read(p,OWNER,90,0)
        self.assertIsNone(result['lp_usd_18']);self.assertEqual('5',result['claimable_eth_wei'])
        self.assertTrue(all(block=={'blockHash':p.header['hash'],'requireCanonical':True} for _,_,block in p.calls))


if __name__=='__main__':unittest.main()
