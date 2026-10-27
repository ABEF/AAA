"""Opt-in holder-return keeper jobs. Local fixtures only, never broadcast."""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.principal import PrincipalDistribution, BATCH, encode_batch
from tests_python import test_holder_exit_profile as H
from tests_python import test_frontend_api as F
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class PrincipalDistributionTests(unittest.TestCase):
    def setUp(self):
        self.f=H.HolderExitKeeperTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.cfg=copy.deepcopy(self.f.cfg);self.rpc=self.f.rpc;self.nft=F.addr(92)
        self.cfg['principal_distribution']={'enabled':True,'batch_size':4,
            'nft':{'address':self.nft,'code_hash':'0x'+keccak256(bytes.fromhex('6000')).hex()}}
        self.f.started=1;self.f.phase=3
        self.count=8;self.allocation_cursor=1;self.paid=set();self.overrides={};self.remaining=(800,1600)
        original=self.rpc.call
        def read(method,args):
            if method=='eth_call' and 'from' not in args[0]:
                target=args[0]['to'];data=args[0]['data']
                if (target,data) in self.overrides:return self.overrides[target,data]
                value=None
                if target==self.nft and data==calldata('access()'):value=int(self.cfg['contracts']['access'],16)
                elif data==calldata('module(bytes32)','0x'+keccak256(b'ZZZNFT').hex()):value=int(self.nft,16)
                elif target==self.f.exit and data==calldata('exitMintedCount()'):value=self.count
                elif target==self.f.exit and data==calldata('allocationCursor()'):value=self.allocation_cursor
                elif target==self.f.exit and data==calldata('remainingETH()'):value=self.remaining[0]
                elif target==self.f.exit and data==calldata('remainingZZZ()'):value=self.remaining[1]
                elif target==self.nft and data.startswith(calldata('tokenAtOrdinal(uint256)',1)[:10]):
                    value=int(data[-64:],16)+10000
                elif target==self.nft and data.startswith(calldata('mintOrdinalOf(uint256)',1)[:10]):
                    value=int(data[-64:],16)-10000
                elif target==self.f.exit and data.startswith(calldata('principalOf(uint256)',1)[:10]):
                    identifier=int(data[-64:],16)
                    self.rpc.calls.append((method,args))
                    return F.words(100,200,1,int(identifier in self.paid))
                if value is not None:
                    self.rpc.calls.append((method,args));return F.words(value)
            return original(method,args)
        self.rpc.call=read
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def test_bounded_array_encoding_is_exact_and_never_generic(self):
        self.assertEqual('0x'+keccak256(BATCH.encode()).hex()[:8]+F.words(32,2,9,12)[2:],encode_batch([9,12]))
        for ids in ([],[1]*2,[True],[0],[-1],[1<<256],list(range(1,34)),['1'],'1'):
            with self.subTest(ids=ids),self.assertRaises(ValueError):encode_batch(ids)

    def test_accounting4_and_explicit_settings_are_required(self):
        for mutate in ('version','batch','boolean','pin','unknown'):
            cfg=copy.deepcopy(self.cfg)
            if mutate=='version':cfg['accounting_version']=3
            elif mutate=='batch':cfg['principal_distribution']['batch_size']=33
            elif mutate=='boolean':cfg['principal_distribution']['enabled']=1
            elif mutate=='pin':cfg['principal_distribution']['nft']['code_hash']='0x'+'0'*64
            else:cfg['principal_distribution']['recipient']=F.addr(93)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_pending_recovery_precedes_worker_and_never_resends(self):
        self.k.state['pending']={'key':'saved'}
        with patch.object(self.k,'poll_pending',return_value=True),patch.object(self.k.principal_distribution,'run') as run:
            self.k.cycle();run.assert_not_called()

    def test_invalid_new_job_config_cannot_block_saved_hash_recovery_on_startup(self):
        self.k.state['next_nonce']=7
        self.k.state['pending']=dict(key='principal_distribute:1',nonce=7,to=self.f.exit,
            data=encode_batch([10001]),value=0,day='2026-10-27',hash='0x'+'a'*64)
        self.k.save();before=self.k.path.read_bytes()
        cfg=copy.deepcopy(self.cfg);cfg['principal_distribution']={'enabled':'invalid'}
        recovered=Keeper(cfg,rpc=self.rpc)
        self.assertFalse(recovered.principal_distribution.configured)
        with patch.object(recovered,'poll_pending',return_value=True),patch.object(recovered,'submit') as submit:
            recovered.cycle();submit.assert_not_called()
        self.assertEqual(before,recovered.path.read_bytes())
        recovered.state['pending']=None
        with self.assertRaises(ValueError):recovered.cycle()

    def test_revoked_keeper_cannot_schedule_permissionless_delivery_with_service_key(self):
        self.overrides[self.cfg['contracts']['access'],calldata('keepers(address)',self.cfg['sender'])]=F.words(0)
        with patch.object(self.k,'submit') as submit:
            with self.assertRaises(RpcError):self.k.cycle()
            submit.assert_not_called()

    def test_paused_allocation_is_scheduled_only_after_governance_closes_all(self):
        self.f.f.base.paused=True;self.f.phase=1
        with patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle();submit.assert_not_called()
            self.f.phase=2
            self.k.cycle()
            submit.assert_called_once_with('principal_exit','allocatePrincipal(uint256)',(4,),'principal_allocate:1')

    def test_direct_distribution_uses_current_ledger_and_persists_scan_cursor_first(self):
        self.f.f.base.paused=True;self.paid={10002}
        def submit(role,signature,args,key):
            disk=json.loads(self.k.path.read_text())
            self.assertEqual(5,disk['principal_distribution_cursor'])
            self.assertEqual(('principal_exit',BATCH,([10001,10003,10004],),'principal_distribute:1'),
                (role,signature,args,key))
            return True
        with patch.object(self.k,'submit',side_effect=submit):self.k.cycle()
        self.assertEqual({10002},self.paid)  # Local scheduling never marks anyone paid.

    def test_one_thousand_ordinals_rotate_without_forgetting_failed_payments(self):
        self.count=1000;self.k.state['principal_distribution_cursor']=997
        with patch.object(self.k,'submit',return_value=False) as submit:
            self.k.principal_distribution.run()
            self.assertEqual([10997,10998,10999,11000],submit.call_args.args[2][0])
            self.assertEqual(1,self.k.state['principal_distribution_cursor'])
            self.k.principal_distribution.run()
            self.assertEqual([10001,10002,10003,10004],submit.call_args.args[2][0])
            self.k.state['principal_distribution_cursor']=997
            self.k.principal_distribution.run()
            self.assertEqual([10997,10998,10999,11000],submit.call_args.args[2][0])
        self.assertEqual(set(),self.paid)

    def test_zero_classified_principal_stops_repeated_paid_inventory_scans(self):
        self.count=1000;self.remaining=(0,0)
        with patch.object(self.k,'submit') as submit:
            self.k.principal_distribution.run();submit.assert_not_called()
        reads=[args[0]['data'][:10] for method,args in self.rpc.calls if method=='eth_call']
        self.assertNotIn(calldata('tokenAtOrdinal(uint256)',1)[:10],reads)
        self.assertNotIn(calldata('principalOf(uint256)',1)[:10],reads)

    def test_failed_runtime_or_ordinal_or_boolean_blocks_delivery(self):
        for mutation in ('runtime','module','ordinal','boolean','allocation'):
            self.overrides={}
            if mutation=='runtime':self.k.principal_distribution.code_hash='0x'+'f'*64
            elif mutation=='module':self.overrides[self.cfg['contracts']['access'],calldata('module(bytes32)',
                '0x'+keccak256(b'ZZZNFT').hex())]=F.words(F.addr(93))
            elif mutation=='ordinal':self.overrides[self.nft,calldata('mintOrdinalOf(uint256)',10001)]=F.words(2)
            elif mutation=='boolean':self.overrides[self.f.exit,calldata('principalOf(uint256)',10001)]=F.words(100,200,1,2)
            else:self.overrides[self.f.exit,calldata('principalOf(uint256)',10001)]=F.words(100,200,0,0)
            with self.subTest(mutation=mutation),patch.object(self.k,'submit') as submit:
                with self.assertRaises(RpcError):self.k.principal_distribution.run()
                submit.assert_not_called()
            self.k.principal_distribution.code_hash=self.cfg['principal_distribution']['nft']['code_hash']

    def test_actual_submit_reuses_simulation_and_gas_cap_without_any_signing(self):
        self.cfg['max_gas_limit']=1
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.k.submit('principal_exit',BATCH,([10001,10002],),'principal_distribute:1'))
            signer.assert_not_called()
        simulated=[args[0] for method,args in self.rpc.calls if method=='eth_call' and 'from' in args[0]]
        self.assertEqual(encode_batch([10001,10002]),simulated[-1]['data'])
        self.assertEqual('0x0',simulated[-1]['value'])
        self.assertIsNone(self.k.state['pending'])


if __name__=='__main__':unittest.main()
