"""Explicit fresh conversion intent; no RPC, signer or journal migration."""
import copy
from types import SimpleNamespace
import unittest
from keeper.royalties import RoyaltyAutomation

def configured(lp=False):
    ledger,converter,nft,executor=('rewards','lp_converter','lp_nft','lp_v4_executor') if lp else ('royalties','royalty_converter','royalty_nft','royalty_v4_executor')
    roles=(ledger,converter,nft,'oracle',executor)
    contracts={role:'0x'+f'{i+1:040x}' for i,role in enumerate(roles)}
    job=dict(enabled=True,profile='v4_native',assets=[dict(asset='0x'+f'{100:040x}',route_id='0x'+'1'*64,minimum_source_units=1,minimum_output_wei=1)])
    config={('lp_conversion' if lp else 'royalty_conversion'):job,'code_hashes':{role:'0x'+'2'*64 for role in roles}}
    return SimpleNamespace(accounting_version=6,config=config,contracts=contracts,state={})

class ConversionProfileV6Tests(unittest.TestCase):
    def test_enabled_profile6_has_no_implicit_wrapper_default_and_accepts_reviewed_native(self):
        for lp in (False,True):
            k=configured(lp);worker=RoyaltyAutomation(k,lp=lp)
            self.assertEqual('v4_native',worker.profile);self.assertTrue(worker.native_v4)
            self.assertEqual('v4_native',k.state[worker.key]['identity']['profile'])
            bad=configured(lp);bad.config[worker.key].pop('profile')
            with self.subTest(lp=lp),self.assertRaisesRegex(ValueError,'explicit reviewed profile'):RoyaltyAutomation(bad,lp=lp)
            self.assertEqual({},bad.state)

    def test_invalid_new_profile_does_not_reinterpret_or_block_saved_pending_intent(self):
        k=configured();k.config['royalty_conversion'].pop('profile')
        k.state['pending']={'key':'original','hash':'0x'+'3'*64,'nonce':7}
        before=copy.deepcopy(k.state);worker=RoyaltyAutomation(k)
        self.assertEqual(before,k.state)
        k.state['pending']=None
        with self.assertRaisesRegex(ValueError,'unconfigured'):worker.scan_once()
        self.assertNotIn('royalty_conversion',k.state)
