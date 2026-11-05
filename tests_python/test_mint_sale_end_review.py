"""Fresh unsigned mint review binding; synthetic RPC only, no wallet/signing."""
import unittest

from frontend_api.service import Projection, ProjectionError
from frontend_api.transactions import Transactions, TransactionInputError
from tests_python import test_frontend_policy_v6 as historical
from tests_python.test_frontend_api import addr
from tests_python.test_frontend_transactions import transaction_config
from zzz_ops.abi import calldata, keccak256


class MintSaleEndReviewTests(unittest.TestCase):
    def fixture(self, end=1200, revision=7):
        from zzz_ops.mint_policy_v2 import fingerprint
        f=historical.FrontendPolicyV6Tests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        base,price=f.mint_fixture()
        f.config['royalty_reporting']={'schema':5,'converter':None}
        f.rpc.put(f.c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8').hex(),))
        f.rpc.put(f.c['nft'],'royaltyRewards()',values=(f.c['royalties'],))
        f.rpc.put(f.c['royalties'],'mintEnd()',values=(end,))
        f.rpc.put(f.c['royalties'],'mintEndRevision()',values=(revision,))
        combined=fingerprint(base,f.c['nft'],f.c['royalties'],end,revision)
        f.rpc.put(f.c['vault'],'mintPolicyFingerprint()',values=(combined,))
        p=Projection(f.config,f.rpc,clock=lambda:1000)
        return f,p,base,combined,price

    def test_pure_composite_matches_independent_six_static_abi_words(self):
        from zzz_ops.mint_policy_v2 import fingerprint
        base='0x'+'1'*64;end=12345;revision=7
        raw=keccak256(b'ZZZ_MINT_POLICY_WITH_ROYALTY_END_V2').hex()+base[2:]+f'{int(addr(2),16):064x}{int(addr(5),16):064x}{end:064x}{revision:064x}'
        self.assertEqual(len(bytes.fromhex(raw)),192)
        actual=fingerprint(base,addr(2),addr(5),end,revision)
        self.assertEqual(actual,'0x'+keccak256(bytes.fromhex(raw)).hex())
        self.assertNotEqual(actual,base)
        for args in [(base,addr(3),addr(5),end,revision),(base,addr(2),addr(6),end,revision),
                     (base,addr(2),addr(5),end+1,revision),(base,addr(2),addr(5),end,revision+1)]:
            self.assertNotEqual(actual,fingerprint(*args))
        for invalid in (-1,True,2**64):
            with self.assertRaises(ValueError):fingerprint(base,addr(2),addr(5),invalid,revision)
            with self.assertRaises(ValueError):fingerprint(base,addr(2),addr(5),end,invalid)

    def test_current_mint_prepares_composite_calldata_and_inspectable_sale_end(self):
        f,p,base,combined,price=self.fixture()
        result=Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(result['transaction']['data'],calldata('mintDormant(bytes32)',combined))
        self.assertEqual(result['transaction']['value'],hex(price))
        self.assertEqual(result['mint_policy']['policy_fingerprint'],base)
        self.assertEqual(result['mint_policy']['mint_end'],'1200')
        self.assertEqual(result['mint_policy']['mint_end_revision'],'7')
        self.assertEqual(result['mint_policy']['royalty_receiver'],f.c['royalties'])
        self.assertEqual(len(f.sent),1)

    def test_stale_or_unwrapped_mint_policy_is_rejected_before_simulation(self):
        f,p,base,combined,_=self.fixture()
        f.rpc.put(f.c['vault'],'mintPolicyFingerprint()',values=(base,))
        with self.assertRaisesRegex(ProjectionError,'mint terms'):
            Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(f.sent,[])
        f.rpc.put(f.c['vault'],'mintPolicyFingerprint()',values=(combined,))
        f.rpc.put(f.c['royalties'],'mintEnd()',values=(1201,))
        with self.assertRaisesRegex(ProjectionError,'mint terms'):
            Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(f.sent,[])

    def test_restored_end_with_a_new_revision_cannot_revive_a_saved_review(self):
        f,p,*_=self.fixture()
        f.rpc.put(f.c['royalties'],'mintEndRevision()',values=(9,))
        with self.assertRaisesRegex(ProjectionError,'mint terms'):
            Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(f.sent,[])
        f,p,*_=self.fixture(revision=0)
        with self.assertRaises(TransactionInputError):
            Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(f.sent,[])

    def test_unknown_receiver_or_unconfigured_or_closed_sale_does_not_reach_simulation(self):
        for end in (0,989,999):
            f,p,*_=self.fixture(end)
            with self.subTest(end=end),self.assertRaises(TransactionInputError):
                Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
            self.assertEqual(f.sent,[])
        f,p,*_=self.fixture()
        f.rpc.put(f.c['nft'],'royaltyRewards()',values=(addr(999),))
        with self.assertRaisesRegex(ProjectionError,'receiver|binding'):
            Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(f.sent,[])

    def test_review_expiry_cannot_outlive_the_inclusive_mint_end(self):
        f,p,*_=self.fixture(1005)
        result=Transactions(p,transaction_config(p)).prepare({'action':'mint','wallet':addr(30)})
        self.assertEqual(result['prepared_at'],1000)
        self.assertEqual(result['expires_at'],1006)


if __name__=='__main__':unittest.main()
