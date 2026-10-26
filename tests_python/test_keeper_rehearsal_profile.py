"""Exercise the real disposable Lab builder without processes, funds or RPC."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('keeper_rehearsal_profile',ROOT/'scripts/rehearse-keeper.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
ADMIN='0x'+'11'*20
VENUE='0x'+'22'*20
SENDER='0x'+'33'*20

class RehearsalProfileTests(unittest.TestCase):
    def build(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        lab=module.Lab(Path(temporary.name)/'lab','0x6000',{'cast':'discarded-cast','anvil':'discarded-anvil'})
        def rpc(url,method,params=None):
            self.assertTrue(url.startswith('http://127.0.0.1:'))
            return {'eth_chainId':'0x7a69','web3_clientVersion':'anvil/v1.4.4',
                    'eth_accounts':[ADMIN],'eth_getCode':'0x6000','anvil_setBalance':True}[method]
        def command(args,**kwargs):
            if args[1:3]==['wallet','new']:
                (Path(args[3])/args[4]).write_text('inert fixture; not a wallet')
            return SimpleNamespace(returncode=0,stdout=SENDER+'\n')
        with patch.object(module,'rpc',side_effect=rpc),patch.object(module.subprocess,'run',side_effect=command),\
             patch.object(lab,'spawn'),patch.object(lab,'tx',return_value={'contractAddress':VENUE}),\
             patch.object(lab,'admin_call'),patch.object(lab,'cli'):
            lab.start()
        return lab

    def test_process_rehearsal_selects_current_accounting_and_intake(self):
        lab=self.build()
        self.assertEqual(lab.cfg.get('accounting_version'),3)
        self.assertEqual(lab.cfg.get('fee_intake_version'),1)

    def test_no_retired_creator_job_and_local_isolation_are_explicit(self):
        lab=self.build()
        self.assertNotIn('sync_external_rewards',lab.cfg['maintenance'])
        self.assertEqual(lab.cfg['chain_id'],31337)
        self.assertEqual(lab.cfg['rpc_urls'],[lab.url])
        self.assertEqual(lab.cfg['sender'],SENDER)
        self.assertEqual(lab.cfg['state_path'],str(lab.host/'state.json'))
        self.assertEqual(lab.cfg['code_hashes'],{name:'0x'+module.keccak256(bytes.fromhex('6000')).hex()
                        for name in ('access','vault','strategy','fees','compounder','buyback','pools')})

if __name__=='__main__':unittest.main()
