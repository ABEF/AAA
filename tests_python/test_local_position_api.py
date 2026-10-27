"""Explicit V3 read profile and raw-codec boundaries, using pinned offline RPC."""
import unittest
from frontend_api.service import Projection, ProjectionError, ZERO
from zzz_ops.abi import keccak256
from zzz_ops.position import decode_position, status_name, position_word_count
from tests_python.test_frontend_api import MockRPC, configuration, addr


class LocalPositionAPITests(unittest.TestCase):
    def setUp(self):
        self.rpc=MockRPC();self.config=configuration()
        self.config.update(accounting_version=3,fee_intake_version=1)
        self.rpc.put(addr(3),'ACCOUNTING_VERSION()',values=(3,))
        self.rpc.put(addr(7),'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4').hex(),))
        self.rpc.put(addr(1),'GOVERNANCE_VERSION()',values=(2,))
        self.rpc.put(addr(1),'governance()',values=(addr(40),))
        self.row=[444,9,0,0,2000*10**18,2**96,990,1]
        self.rpc.put(addr(3),'group(uint256)',(5,),self.row)
        # This historical native V3 fixture must admit ETH as the real ledger
        # does; the wrapped V1 base fixture has no native LP index.
        self.rpc.put(addr(4),'assetCount()',values=(3,))
        for ordinal,asset in enumerate((ZERO,addr(20),addr(21))):
            self.rpc.put(addr(4),'assets(uint256)',(ordinal,),(asset,))
        self.rpc.put(addr(4),'claimable(uint256,address)',(self.rpc.nft_id,ZERO),(0,))
    def projection(self):return Projection(self.config,self.rpc,clock=lambda:1000)
    def read(self):return self.projection().nft(self.rpc.nft_id)

    def test_active_eight_word_row_preserves_actual_value_and_both_reward_balances(self):
        value=self.read();self.assertEqual('active',value['position']['status'])
        self.assertEqual(str(1432*10**18),value['position']['current_lp_value']['raw'])
        self.assertEqual('9',value['position']['local_custody']['lp_token_id'])
        self.assertTrue(value['claimable']['lp']);self.assertTrue(value['claimable']['royalties'])
        self.assertFalse(value['position']['principal_redeemable'])
        parsed=decode_position([f'{x:064x}' for x in self.row],3)
        self.assertNotIn('home_chain',parsed);self.assertNotIn('location_vault',parsed)

    def test_dormant_three_has_no_lp_membership_and_parked_four_has_no_active_value(self):
        i=self.rpc.nft_id
        self.rpc.put(addr(3),'nftStatus(uint256)',(i,),(3,))
        self.rpc.put(addr(3),'nftBucket(uint256)',(i,),(0,));self.rpc.put(addr(3),'sharesOf(uint256)',(i,),(0,))
        self.rpc.put(addr(5),'weightOf(uint256)',(i,),(0,));self.rpc.put(addr(2),'currentLPValue(uint256)',(i,),(1,0))
        for role,assets in ((4,(ZERO,addr(20),addr(21))),(5,(ZERO,addr(21)))):
            for asset in assets:self.rpc.put(addr(role),'claimable(uint256,address)',(i,asset),(0,))
        dormant=self.read();self.assertEqual('dormant',dormant['position']['status'])
        self.assertFalse(dormant['position']['activated']);self.assertIsNone(dormant['position']['local_custody'])
        self.rpc.configure();self.setUp()
        self.rpc.put(addr(3),'nftStatus(uint256)',(self.rpc.nft_id,),(4,))
        self.row[1]=0;self.row[7]=4;self.rpc.put(addr(3),'group(uint256)',(5,),self.row)
        self.rpc.put(addr(2),'currentLPValue(uint256)',(self.rpc.nft_id,),(0,0))
        parked=self.read();self.assertEqual('parked',parked['position']['status'])
        self.assertFalse(parked['position']['current_lp_value']['available'])

    def test_old_rows_extra_words_and_removed_statuses_are_never_reinterpreted(self):
        for row in (self.row+[0]*7,self.row+[0],self.row[:7]+[5],self.row[:7]+[6]):
            with self.subTest(row=row):
                self.rpc.put(addr(3),'group(uint256)',(5,),row)
                with self.assertRaises(ProjectionError):self.read()
        for code in (5,6):
            self.rpc.put(addr(3),'nftStatus(uint256)',(self.rpc.nft_id,),(code,))
            with self.assertRaises(ProjectionError):self.read()

    def test_version_schema_and_direct_governance_are_bound_before_serving(self):
        for target,method,value in ((3,'ACCOUNTING_VERSION()',2),(7,'SCHEMA()','0x'+'a'*64),
                                    (1,'GOVERNANCE_VERSION()',1),(1,'governance()',addr(1))):
            with self.subTest(method=method):
                self.setUp();self.rpc.put(addr(target),method,values=(value,))
                with self.assertRaises(ProjectionError):self.read()

    def test_historical_and_local_status_meanings_remain_explicit(self):
        self.assertEqual('remote',status_name(2,3));self.assertEqual('dormant',status_name(3,3))
        self.assertEqual('parked',status_name(2,6));self.assertEqual('parked',status_name(3,4))
        self.assertEqual(15,position_word_count(2));self.assertEqual(8,position_word_count(3))
        for version in (True,0,5,'3'):
            with self.assertRaises(ValueError):position_word_count(version)
        for index,value in ((5,1<<160),(6,1<<64)):
            row=list(self.row);row[index]=value
            with self.assertRaises(ValueError):decode_position([f'{x:064x}' for x in row],3)

