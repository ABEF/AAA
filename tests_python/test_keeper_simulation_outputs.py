"""Typed simulation return ABI before intent/signing; inert signer/RPC only."""
import copy
import json
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests_python import test_keeper as basic
from zzz_ops.rpc import RpcError


class KeeperSimulationOutputTests(unittest.TestCase):
    def fixture(self, output):
        case=basic.KeeperTests('runTest');case.setUp();self.addCleanup(case.doCleanups)
        case.enable_test_signer();k,rpc=case.k,case.rpc
        k._validate_accounting_version=lambda:None
        k._validate_checkpoint=lambda:None
        k._defer_for_lifecycle=lambda *_:False
        k._validate_lp_routing=lambda:None
        k._rebalance_submission_ready=lambda _:True
        k._compound_submission_ready=lambda _:True
        k.rebalance_confirmation=SimpleNamespace(version=1,validate=lambda:None)
        k._confirmation_status=lambda _:None
        k.contracts.update(nft=basic.B,rebalance_confirmation=basic.B)
        original=rpc.call
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:
                rpc.calls.append((method,params));return output
            return original(method,params)
        rpc.call=call
        return k,rpc

    @staticmethod
    def jobs(now):
        return (
            ('vault','collectFees(uint256,uint256)',(1,now+180)),
            ('vault','rebalance(uint256,uint128,uint256)',(1,1,now+180)),
            ('compounder','compound(uint256,uint128,uint256)',(1,1,now+180)),
            ('buyback','execute(address,uint256,bytes32,uint256)',(basic.B,1,basic.H,now+180)),
            ('nft','refreshMetadataRange(uint256,uint256)',(1,1)),
            ('rebalance_confirmation','resetObservation(uint256)',(1,)),
        )

    def test_void_jobs_reject_nonempty_malformed_or_nonstring_before_intent(self):
        for output in ('0x00','0x'+'0'*64,None,{'not':'ABI'}):
            for index in range(6):
                with self.subTest(output=output,job=index):
                    k,rpc=self.fixture(output);name,signature,args=self.jobs(rpc.now)[index]
                    before=copy.deepcopy(k.state)
                    with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')) as signer:
                        with self.assertRaises(RpcError):k.submit(name,signature,args,'output:test')
                        signer.assert_not_called()
                    self.assertEqual(before,k.state);self.assertFalse(k.path.exists())

    def test_observation_requires_exact_canonical_boolean_word(self):
        for output in ('0x','0x01','0x'+f'{2:064x}','0x'+'g'*64,None):
            with self.subTest(output=output):
                k,rpc=self.fixture(output);before=copy.deepcopy(k.state)
                with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,basic.H,'')) as signer:
                    with self.assertRaises(RpcError):
                        k.submit('rebalance_confirmation','observe(uint256)',(1,),'output:observe')
                    signer.assert_not_called()
                self.assertEqual(before,k.state);self.assertFalse(k.path.exists())

    def test_valid_void_and_boolean_outputs_preserve_exact_fee_intent(self):
        for index in range(8):
            with self.subTest(job=index):
                output='0x' if index<6 else '0x'+f'{index-6:064x}'
                k,rpc=self.fixture(output)
                name,signature,args=self.jobs(rpc.now)[index] if index<6 else ('rebalance_confirmation','observe(uint256)',(1,))
                before=copy.deepcopy(k.state['spent'])
                def sign(command,**_):
                    pending=json.loads(k.path.read_text())['pending']
                    self.assertIsNone(pending['hash']);self.assertEqual(pending['fee_review']['maximum_cost_wei'],250)
                    return subprocess.CompletedProcess(command,0,basic.H,'')
                with patch('keeper.monitor.subprocess.run',side_effect=sign):
                    self.assertTrue(k.submit(name,signature,args,'output:valid'))
                self.assertEqual(before,k.state['spent']);self.assertEqual(k.state['pending']['hash'],basic.H)
