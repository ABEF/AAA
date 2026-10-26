"""Current fee projections reject impossible ledger/activation combinations.

Real Projection and ABI-encoded read fixtures only; no signing, live RPC or
mutations of the existing local chain. Inactive means validated never activated,
not an active NFT whose principal is parked or externally custodied.
"""
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError, ZERO
from tests_python.test_frontend_api import MockRPC, addr, configuration, words
from tests_python.test_royalty_reporting import profile, native_data
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError


class CurrentFeeRPC(MockRPC):
    def __init__(self, version=3):
        super().__init__()
        self.version=version
        if version in (2,3):
            self.put(addr(3),'ACCOUNTING_VERSION()',values=(version,))
            domain=(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4' if version==3
                    else b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_V2')
            self.put(addr(7),'SCHEMA()',values=('0x'+keccak256(domain).hex(),))
        if version==3:
            self.put(addr(1),'GOVERNANCE_VERSION()',values=(2,))
            self.put(addr(1),'governance()',values=(addr(70),))
            key=addr(3),calldata('group(uint256)',5)
            self.responses[key]=self.responses[key][:2+8*64]
            self.lp_assets([ZERO,addr(20),addr(21)])
            self.put(addr(4),'claimable(uint256,address)',(self.nft_id,ZERO),(7*10**18,))

    def lp_assets(self,assets):
        self.put(addr(4),'assetCount()',values=(len(assets),))
        for i,asset in enumerate(assets):self.put(addr(4),'assets(uint256)',(i,),(asset,))

    def dormant(self):
        identifier=self.nft_id
        for signature,value in (('nftStatus(uint256)',3 if self.version==3 else 5),
                ('nftBucket(uint256)',0),('sharesOf(uint256)',0)):
            self.put(addr(3),signature,(identifier,),(value,))
        self.put(addr(5),'weightOf(uint256)',(identifier,),(0,))
        self.put(addr(2),'currentLPValue(uint256)',(identifier,),(1,0))
        for role,assets in ((4,[ZERO,addr(20),addr(21)]),(5,[ZERO,addr(21)])):
            for asset in assets:self.put(addr(role),'claimable(uint256,address)',(identifier,asset),(0,))
        self.put(addr(5),'activationOrdinal(uint256)',(identifier,),(0,))
        for asset in (ZERO,addr(21)):
            encoded=native_data('eligibleFor(uint256,address)',identifier,asset) if asset==ZERO else calldata('eligibleFor(uint256,address)',identifier,asset)
            self.responses[addr(5),encoded]=words(0)


class CurrentFeeIntegrityTests(unittest.TestCase):
    def service(self,*,version=3,reporting=False,dormant=False):
        rpc=CurrentFeeRPC(version);cfg=configuration()
        cfg['accounting_version']=version
        if version==3:cfg['fee_intake_version']=1
        if reporting:cfg=profile(cfg,rpc,converter=False)
        if dormant:rpc.dormant()
        return rpc,Projection(cfg,rpc,clock=lambda:1000)

    def test_current_lp_inventory_requires_native_first_without_inventing_a_row(self):
        for assets in ([],[addr(20),addr(21)],[addr(20),ZERO,addr(21)]):
            with self.subTest(assets=assets):
                rpc,p=self.service();rpc.lp_assets(assets)
                with self.assertRaisesRegex(ProjectionError,'LP ledger must begin with native ETH'):
                    p.nft(str(rpc.nft_id))

    def test_inactive_native_and_token_lp_credit_is_rejected(self):
        for asset in (ZERO,addr(20),addr(21)):
            with self.subTest(asset=asset):
                rpc,p=self.service(dormant=True)
                rpc.put(addr(4),'claimable(uint256,address)',(rpc.nft_id,asset),(17,))
                with self.assertRaisesRegex(ProjectionError,'Inactive NFT has reward entitlement'):
                    p.nft(str(rpc.nft_id))

    def test_inactive_royalty_credit_without_optional_reporting_is_rejected(self):
        for asset in (ZERO,addr(21)):
            with self.subTest(asset=asset):
                rpc,p=self.service(dormant=True)
                rpc.put(addr(5),'claimable(uint256,address)',(rpc.nft_id,asset),(19,))
                with self.assertRaisesRegex(ProjectionError,'Inactive NFT has reward entitlement'):
                    p.nft(str(rpc.nft_id))

    def test_optional_reporting_does_not_permit_inactive_lp_credit(self):
        for asset in (ZERO,addr(20)):
            with self.subTest(asset=asset):
                rpc,p=self.service(reporting=True,dormant=True)
                rpc.put(addr(4),'claimable(uint256,address)',(rpc.nft_id,asset),(23,))
                with self.assertRaisesRegex(ProjectionError,'Inactive NFT has reward entitlement'):
                    p.nft(str(rpc.nft_id))

    def test_verified_dormant_zero_and_optional_unavailable_remain_distinct(self):
        rpc,p=self.service(dormant=True)
        out=p.nft(str(rpc.nft_id))
        self.assertFalse(out['position']['activated'])
        self.assertEqual(out['position']['status'],'dormant')
        self.assertTrue(all(row['raw']=='0' for role in ('lp','royalties') for row in out['claimable'][role]))
        rpc,p=self.service(reporting=True,dormant=True)
        original=rpc.call
        missing=(addr(4),calldata('claimable(uint256,address)',rpc.nft_id,addr(20)))
        def outage(method,params):
            if method=='eth_call' and (params[0]['to'],params[0]['data'])==missing:
                raise RpcError('Synthetic currency outage')
            return original(method,params)
        with patch.object(rpc,'call',side_effect=outage):out=p.nft(str(rpc.nft_id))
        unavailable=next(row for row in out['claimable']['lp'] if row['asset']==addr(20))
        self.assertFalse(unavailable['available']);self.assertIsNone(unavailable['raw'])
        self.assertFalse(out['position']['activated'])
        self.assertEqual(out['claimable']['royalties'][0]['raw'],'0')

    def test_active_parked_and_outbound_claims_are_not_treated_as_dormant(self):
        for status in (1,2,4):
            with self.subTest(status=status):
                rpc,p=self.service();rpc.put(addr(3),'nftStatus(uint256)',(rpc.nft_id,),(status,))
                if status!=1:rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(0,0))
                if status==4:
                    key=addr(3),calldata('group(uint256)',5)
                    values=[int(v,16) for v in (rpc.responses[key][2+i*64:2+(i+1)*64] for i in range(8))]
                    values[1]=0;values[7]=4;rpc.responses[key]=words(*values)
                out=p.nft(str(rpc.nft_id))
                self.assertTrue(out['position']['activated'])
                self.assertEqual(out['claimable']['lp'][0]['raw'],str(7*10**18))
                self.assertEqual(out['claimable']['royalties'][0]['raw'],'33333333333333333333')

    def test_historical_source_only_lp_inventory_keeps_its_explicit_profile(self):
        for version in (1,2):
            with self.subTest(version=version):
                rpc,p=self.service(version=version)
                out=p.nft(str(rpc.nft_id))
                self.assertEqual(out['provenance']['accounting_version'],version)
                self.assertEqual(out['claimable']['default_settlement'],'source_assets')
                self.assertFalse(any(row['asset']==ZERO for row in out['claimable']['lp']))

    def test_historical_dormant_zero_and_native_token_credit_are_distinguished(self):
        for version in (1,2):
            with self.subTest(version=version,claimable='zero'):
                rpc,p=self.service(version=version,dormant=True)
                self.assertFalse(p.nft(str(rpc.nft_id))['position']['activated'])
            for role,asset in ((4,addr(20)),(4,addr(21)),(5,ZERO),(5,addr(21))):
                with self.subTest(version=version,role=role,asset=asset):
                    rpc,p=self.service(version=version,dormant=True)
                    rpc.put(addr(role),'claimable(uint256,address)',(rpc.nft_id,asset),(1,))
                    with self.assertRaisesRegex(ProjectionError,'Inactive NFT has reward entitlement'):
                        p.nft(str(rpc.nft_id))


if __name__=='__main__':unittest.main()
