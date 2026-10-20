"""Actual wallet/ledger boundary with independent disposable sender nonces."""
import tempfile
from pathlib import Path
from unittest.mock import Mock
import unittest
from tests_python import test_local_wallet as fixtures
from tests_python.test_local_stack import lab as module

A,B=fixtures.A,fixtures.B


class ConcurrentWalletTests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.WalletTests();fixture.setUp()
        self.lab,self.wallet=fixture.lab,fixture.wallet
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.lab.receipts=[]
        self.lab.operations=module.OperationLedger(Path(self.temp.name)/'operations.json')
        self.lab.wallet=self.wallet
        self.nonces={A:0,B:0}
        self.lab.rpc.side_effect=lambda method,args:hex(self.nonces[args[0]])
        self.lab.uint.return_value=1
        self.lab.preparer.prepare.side_effect=lambda p:{'transaction':{'from':p['wallet'],'to':'nft','value':'0x1','data':'0xab'},'claim_operations':[]}
        def send(tx,*args,**kwargs):
            self.assertEqual(int(tx['nonce'],16),self.nonces[tx['from']])
            self.nonces[tx['from']]+=1
            self.lab.receipts.append({'receipt':{'transactionHash':'0x'+str(len(self.lab.receipts)+1)*64}})
        self.lab.send.side_effect=send
        self.lab.action.side_effect=self.wallet.execute

    def prepare(self,owner):
        return self.wallet.prepare({'action':'mint','account':owner})

    def envelope(self,draft,key):
        return {'operation_id':key*32,'revision':draft['revision'],'payload':{'action':'execute','account':draft['account'],'draft_id':draft['draft_id']}}

    def test_two_wallets_review_at_same_revision_and_both_execute_once(self):
        a,b=self.prepare(A),self.prepare(B)
        first=self.lab.operations.run(self.envelope(a,'a'),self.lab)
        second=self.lab.operations.run(self.envelope(b,'b'),self.lab)
        self.assertEqual([first['status'],second['status']],['confirmed','confirmed'])
        self.assertEqual(self.lab.operations.revision,2)
        self.assertEqual(self.nonces,{A:1,B:1})
        replay=self.lab.operations.run(self.envelope(b,'b'),self.lab)
        self.assertTrue(replay['replayed']);self.assertEqual(self.lab.send.call_count,2)

    def test_same_wallet_other_transaction_invalidates_review(self):
        a,b=self.prepare(A),self.prepare(A)
        self.lab.operations.run(self.envelope(a,'a'),self.lab)
        outcome=self.lab.operations.run(self.envelope(b,'b'),self.lab)
        self.assertEqual(outcome['status'],'failed')
        self.assertIn('wallet sent another transaction',outcome['error'])
        self.assertEqual(outcome['transactions'],[]);self.assertEqual(self.lab.send.call_count,1)

    def test_changed_envelope_revision_cannot_rebind_server_draft(self):
        a=self.prepare(A);envelope=self.envelope(a,'a');envelope['revision']=1
        with self.assertRaisesRegex(ValueError,'expired'):self.lab.operations.run(envelope,self.lab)
        self.lab.send.assert_not_called();self.assertEqual(self.lab.operations.items,{})

    def test_unknown_draft_cannot_bypass_global_revision(self):
        a=self.prepare(A);envelope=self.envelope(a,'a');envelope['payload']['draft_id']='f'*32
        with self.assertRaisesRegex(ValueError,'missing'):self.lab.operations.run(envelope,self.lab)
        self.lab.send.assert_not_called()

    def test_replay_with_new_identifier_cannot_execute_consumed_draft(self):
        a=self.prepare(A);self.lab.operations.run(self.envelope(a,'a'),self.lab)
        with self.assertRaisesRegex(ValueError,'consumed'):self.lab.operations.run(self.envelope(a,'b'),self.lab)
        self.assertEqual(self.lab.send.call_count,1)

    def test_expiry_and_fixture_supply_cap_still_block(self):
        a=self.prepare(A);self.lab.clock.return_value=1060
        with self.assertRaisesRegex(ValueError,'expired'):self.lab.operations.run(self.envelope(a,'a'),self.lab)
        self.lab.clock.return_value=1000;self.lab.uint.return_value=20
        outcome=self.lab.operations.run(self.envelope(a,'a'),self.lab)
        self.assertEqual(outcome['status'],'failed');self.assertIn('capped',outcome['error'])
        self.lab.send.assert_not_called()

    def test_malformed_nonce_never_prepares(self):
        for value in [None,0,'0x','0x00','0x-1','0x'+'f'*17]:
            self.lab.rpc.side_effect=None;self.lab.rpc.return_value=value
            with self.assertRaisesRegex(ValueError,'nonce'):self.prepare(A)
        self.lab.send.assert_not_called()

    def test_claim_all_rechecks_every_reviewed_nft_owner(self):
        a=self.prepare(A)
        item=self.wallet.drafts[a['draft_id']]
        item['public']['claims']=[{'token_id':'1'},{'token_id':'2'}]
        self.lab.addr.side_effect=lambda role,sig,id:A if id=='1' else B
        outcome=self.lab.operations.run(self.envelope(a,'a'),self.lab)
        self.assertEqual(outcome['status'],'failed');self.assertIn('ownership',outcome['error'])
        self.lab.send.assert_not_called()

    def test_operator_actions_still_require_global_revision(self):
        a=self.prepare(A);self.lab.operations.run(self.envelope(a,'a'),self.lab)
        envelope={'operation_id':'b'*32,'revision':0,'payload':{'action':'mint','account':B}}
        with self.assertRaises(module.LocalConflict):self.lab.operations.run(envelope,self.lab)
        self.assertEqual(self.lab.send.call_count,1)

    def test_approval_rechecks_lifecycle_and_activation_state(self):
        for fault in ('paused','activated'):
            with self.subTest(fault=fault):
                draft=fixtures.WalletTests.contribution(self)
                if fault=='paused':
                    self.lab.api.protocol.return_value={'lifecycle':{'new_economic_work_available_by_lifecycle':False}}
                else:
                    self.lab.api.protocol.return_value={'lifecycle':{'new_economic_work_available_by_lifecycle':True}}
                    self.lab.uint.side_effect=lambda role,sig,*args:1 if sig=='nftBucket(uint256)' else 0
                with self.assertRaisesRegex(ValueError,'lifecycle|activation state'):
                    self.wallet.execute({'account':A,'draft_id':draft['draft_id']})
                self.lab.api.protocol.return_value={'lifecycle':{'new_economic_work_available_by_lifecycle':True}}
        self.lab.send.assert_not_called()

    def test_two_distinct_nft_approvals_accept_other_wallet_revision(self):
        self.lab.ids.return_value=['1','2']
        self.lab.addr.side_effect=lambda role,sig,id:A if id=='1' else B
        a=fixtures.WalletTests.contribution(self)
        b=self.wallet.prepare({'action':'activate','account':B,'id':'2','amount':'100'})
        self.assertEqual(a['action'],'approve');self.assertEqual(b['action'],'approve')
        self.assertEqual(self.lab.operations.run(self.envelope(a,'a'),self.lab)['status'],'confirmed')
        self.assertEqual(self.lab.operations.run(self.envelope(b,'b'),self.lab)['status'],'confirmed')
        self.assertEqual(self.lab.send.call_count,2)


if __name__=='__main__':unittest.main()
