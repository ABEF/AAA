"""Confirmation/replay boundaries, with no public RPC or contract rebuild."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest
from scripts.local_wallet import LocalWallet, UNIT

A='0x'+'11'*20
B='0x'+'22'*20

class WalletTests(unittest.TestCase):
    def setUp(self):
        self.lab=Mock()
        self.lab.uncertain=False
        self.lab.accounts=['operator',A,B]
        self.lab.tokens=['token']
        self.lab.input_assets=None
        self.lab.pool='pool'
        self.lab.contracts={'entry':'entry','nft':'nft'}
        self.lab.operations=SimpleNamespace(revision=4)
        self.lab.ids.return_value=['1']
        self.lab.addr.return_value=A
        self.lab.clock.return_value=1000
        self.lab.encode.return_value='0xab'
        self.lab.simulate.side_effect=lambda tx:({**tx,'gas':'0x100','gasPrice':'0x1'},{'max_cost_wei':'256'})
        self.lab.preparer.prepare.return_value={'transaction':{'from':A,'to':'vault','value':'0x0','data':'0xab'},'claim_operations':[]}
        self.lab.api.protocol.return_value={'lifecycle':{'new_economic_work_available_by_lifecycle':True}}
        self.wallet=LocalWallet(self.lab)
    def contribution(self,allowance=0):
        def uint(role,signature,*args):
            return {'nftBucket(uint256)':0,'balanceOf(address)':1000*UNIT,'allowance(address,address)':allowance}[signature]
        self.lab.uint.side_effect=uint
        self.lab.contribution_tx.return_value={'from':A,'to':'entry','data':'0xab','value':'0x0'}
        return self.wallet.prepare({'action':'activate','account':A,'id':'1','amount':'100'})
    def test_approval_and_entry_are_distinct_explicit_confirmations(self):
        draft=self.contribution()
        self.assertEqual(draft['action'],'approve');self.assertEqual(draft['transaction']['to'],'token')
        self.lab.contribution_tx.assert_not_called();self.lab.send.assert_not_called()
        draft=self.contribution(100*UNIT)
        self.assertEqual(draft['action'],'activate');self.assertEqual(draft['minimum_lp_usd_18'],str(99*UNIT))
        self.lab.send.assert_not_called()
    def test_insufficient_balance_does_not_prepare_an_approval(self):
        self.lab.uint.return_value=0
        with self.assertRaisesRegex(ValueError,'Insufficient'):self.wallet.prepare({'action':'activate','account':A,'id':'1','amount':'100'})
        self.lab.simulate.assert_not_called()
    def test_paused_lifecycle_blocks_even_token_approval(self):
        self.lab.api.protocol.return_value={'lifecycle':{'new_economic_work_available_by_lifecycle':False}}
        with self.assertRaisesRegex(ValueError,'lifecycle'):self.contribution()
        self.lab.simulate.assert_not_called()
    def test_wrong_owner_does_not_prepare_any_transaction(self):
        self.lab.addr.return_value=B
        with self.assertRaisesRegex(ValueError,'does not own'):self.wallet.prepare({'action':'claim','account':A,'id':'1'})
        self.lab.preparer.prepare.assert_not_called()
    def test_revision_account_or_expiry_mismatch_rejects(self):
        draft=self.contribution()
        payload={'account':A,'draft_id':draft['draft_id']}
        for kind in ['account','revision','wall','chain']:
            with self.subTest(kind=kind):
                self.lab.operations.revision=5 if kind=='revision' else 4
                self.lab.clock.return_value=1060 if kind=='chain' else 1000
                with patch('scripts.local_wallet.time.monotonic',return_value=10**20 if kind=='wall' else 0):
                    with self.assertRaisesRegex(ValueError,'expired'):self.wallet.execute({**payload,'account':B if kind=='account' else A})
        self.lab.send.assert_not_called()
    def test_approval_checks_ownership_again_at_execution(self):
        draft=self.contribution();self.lab.addr.return_value=B
        with self.assertRaisesRegex(ValueError,'ownership changed'):self.wallet.execute({'account':A,'draft_id':draft['draft_id']})
        self.lab.send.assert_not_called()
    def test_exact_confirmation_is_consumed_once_even_if_send_fails(self):
        draft=self.contribution();payload={'account':A,'draft_id':draft['draft_id']}
        self.lab.send.side_effect=ValueError('gas changed')
        with self.assertRaisesRegex(ValueError,'gas changed'):self.wallet.execute(payload)
        with self.assertRaisesRegex(ValueError,'consumed'):self.wallet.execute(payload)
        self.assertEqual(self.lab.send.call_count,1)
        self.lab.send.assert_called_with(draft['transaction'],'website approve',approved=True)
    def test_draft_storage_is_bounded_without_eviction_of_live_drafts(self):
        for _ in range(32):self.contribution()
        with self.assertRaisesRegex(ValueError,'Too many'):self.contribution()
        self.assertEqual(len(self.wallet.drafts),32)
    def test_operator_and_arbitrary_transaction_actions_are_not_wallet_drafts(self):
        for action in ('fund','rebalance','execute','rpc'):
            with self.assertRaisesRegex(ValueError,'not a holder'):self.wallet.prepare({'action':action,'account':A})
        self.lab.send.assert_not_called()
    def test_bulk_claims_are_bounded_to_ten_owned_nfts(self):
        self.lab.ids.return_value=[str(i) for i in range(1,21)]
        self.lab.api.nft.return_value={'claimable':{'lp':[{'asset':'token','raw':'12'}],'royalties':[{'asset':'eth','raw':'4'}]}}
        result=self.wallet.prepare({'action':'claim_all','account':A})
        claims=self.lab.preparer.prepare.call_args.args[0]['claims']
        self.assertEqual(len(claims),20)
        self.assertEqual(len({c['token_id'] for c in claims}),10)
        self.assertEqual(result['action'],'claim');self.lab.send.assert_not_called()
    def test_native_default_does_not_include_pending_source_balances(self):
        native='0x'+'00'*20
        self.lab.api.nft.return_value={'claimable':{'default_settlement':'native_eth',
            'lp':[{'asset':'token','raw':'100'},{'asset':native,'raw':'12'}],
            'royalties':[{'asset':native,'raw':'4'}]}}
        self.wallet.prepare({'action':'claim','account':A,'id':'1'})
        claims=self.lab.preparer.prepare.call_args.args[0]['claims']
        self.assertEqual(len(claims),2);self.assertEqual({x['asset'] for x in claims},{native})
    def test_approved_gas_cost_increase_does_not_submit(self):
        from tests_python.test_local_stack import lab
        instance=object.__new__(lab.Lab)
        instance.simulate=Mock(return_value=({'gas':'0x101','gasPrice':'0x1'},{}))
        instance.rpc=Mock()
        with self.assertRaisesRegex(ValueError,'Gas requirement increased'):
            instance.send({'from':A,'gas':'0x100','gasPrice':'0x1'},'approved',approved=True)
        instance.rpc.assert_not_called()

class StaticBoundaryTests(unittest.TestCase):
    def test_website_mount_exposes_only_explicit_public_files(self):
        import http.client,tempfile,threading
        from pathlib import Path
        from tests_python.test_local_stack import lab
        from tests_python.test_local_stack_edges import FakeLab
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'index.html').write_text('<main>Website</main>')
            (path/'private.json').write_text('{"not_public":true}')
            fake=FakeLab(directory);fake.args.website=directory
            server=lab.make_server(fake);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                for route,expected in [('/app/',200),('/app/private.json',404),('/app/assets/../private.json',404),('/app/.git/config',404),('/app/assets/%2e%2e/private.json',404)]:
                    with self.subTest(route=route):
                        connection=http.client.HTTPConnection('127.0.0.1',server.server_port)
                        connection.request('GET',route);response=connection.getresponse();body=response.read();connection.close()
                        self.assertEqual(response.status,expected)
                        self.assertNotIn(b'not_public',body)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
