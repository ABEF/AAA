"""Interrupt durable intent publication: inert current-profile transport/signer.

The real Keeper validators, simulation, fee bounds and atomic journal writer run.
Only read-only RPC replies and the external signer are fixtures. Unix service,
encrypted-keystore startup and process termination need separate host evidence.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from tests_python import test_keeper_execution_price as execution_profile
from zzz_ops.abi import calldata


class KeeperIntentShutdownTests(unittest.TestCase):
    def setUp(self):
        # Reuse only a typed fresh7/execution1/LP3 transcript, never old methods.
        self.rpc, self.cfg, _ = execution_profile.KeeperExecutionPriceTests.fixture(self)
        self.rpc.active_url = 'https://inert-rpc.invalid'
        original = self.rpc.call
        def call(method, params):
            if method == 'eth_getCode':
                self.rpc.rpc_calls.append((method, copy.deepcopy(params)))
                self.assertIn(params[0], self.cfg['contracts'].values())
                return self.rpc.code(params[0])
            if method == 'eth_getTransactionCount':
                self.rpc.rpc_calls.append((method, copy.deepcopy(params)))
                self.assertEqual(params[0], self.cfg['sender'])
                self.assertIn(params[1], ('latest', 'pending'))
                return '0x7'
            return original(method, params)
        self.rpc.call = call
        self.k = Keeper(self.cfg, rpc=self.rpc)
        self.k.state['next_nonce'] = 7
        self.k.state['receipt_anchor'] = {
            'number':98, 'hash':'0x'+'ab'*32, 'timestamp':self.rpc.now, 'nonce':6}
        # The boundary under test is submit(), after reviewed signer startup.
        # No production validator is replaced to reach it on this Windows host.
        self.k.live = True
        self.k.cast = '/inert/cast'
        self.k.keystore = Path('/inert/key')
        self.k.password = Path('/inert/password')
        self.stopping = False
        self.k.stop_requested = lambda:self.stopping
        self.hash = '0x'+'bc'*32
        self.clock = patch('keeper.monitor.time.time', side_effect=lambda:self.rpc.now)
        self.clock.start(); self.addCleanup(self.clock.stop)
        self.events = patch('keeper.monitor.log')
        self.log = self.events.start(); self.addCleanup(self.events.stop)
        self.boundary_evidence = {}

    def submit(self, keeper=None):
        return (keeper or self.k).submit('vault','collectFees(uint256,uint256)',
            (7,self.rpc.now+180),'harvest:7')

    def signer(self, command, **kwargs):
        saved = json.loads(self.k.path.read_bytes())['pending']
        self.assertIsNone(saved['hash'])
        self.assertEqual(saved['nonce'],7)
        self.assertEqual(saved['data'],calldata('collectFees(uint256,uint256)',7,self.rpc.now+180))
        self.assertEqual(command[3],saved['data'])
        self.assertEqual(command[command.index('--nonce')+1],'7')
        self.assertEqual(command[command.index('--gas-limit')+1],str(saved['fee_review']['gas_limit']))
        self.assertEqual(kwargs['timeout'],90)
        self.assertEqual(kwargs['env']['ETH_RPC_URL'],self.rpc.active_url)
        return subprocess.CompletedProcess(command,0,json.dumps({'hash':self.hash}),'')

    def test_stop_during_durable_save_retains_hashless_intent_and_restart_never_resends(self):
        previous = copy.deepcopy(self.k.state)
        original_save = self.k.save
        published = []
        def save_then_stop():
            original_save()
            published.append(self.k.path.read_bytes())
            self.stopping = True
        with patch.object(self.k,'save',side_effect=save_then_stop), \
                patch('keeper.monitor.subprocess.run',side_effect=self.signer) as signer:
            result = self.submit()
        self.boundary_evidence = {'signer_calls':signer.call_count,
            'submit_result':result,'published_hashless':json.loads(published[0])['pending']['hash'] is None,
            'pending_after_hash':self.k.state['pending']['hash'],
            'published_sha256':hashlib.sha256(published[0]).hexdigest(),
            'after_sha256':hashlib.sha256(self.k.path.read_bytes()).hexdigest()}
        self.assertEqual(signer.call_count,0,'Stop during durable intent save must prevent a later signer launch')
        self.assertFalse(result)
        self.assertEqual(len(published),1)
        self.assertEqual(self.k.path.read_bytes(),published[0])
        self.assertIsNone(self.k.state['pending']['hash'])
        self.assertEqual(self.k.state['spent'],previous['spent'])
        self.assertEqual(self.k.state['last'],previous['last'])
        self.assertEqual(self.k.state['next_nonce'],7)
        self.assertEqual(self.k.state['receipt_anchor'],previous['receipt_anchor'])
        self.log.assert_any_call('shutdown_after_intent_before_signer',action='harvest:7')
        before = self.k.path.read_bytes()
        restored = Keeper(self.cfg,rpc=self.rpc)
        restored.live = True
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.submit(restored))
            restored.cycle()
            signer.assert_not_called()
        self.assertEqual(restored.state,self.k.state)
        self.assertEqual(restored.path.read_bytes(),before)
        self.assertEqual(restored.accounting_version,7)
        self.assertEqual(restored.execution_price_version,1)
        self.assertEqual(restored.lp_routing_version,3)

    def test_uninterrupted_submission_keeps_durable_intent_exact_review_and_hash(self):
        previous = copy.deepcopy(self.k.state)
        with patch('keeper.monitor.subprocess.run',side_effect=self.signer) as signer:
            self.assertTrue(self.submit())
        signer.assert_called_once()
        saved = json.loads(self.k.path.read_bytes())
        self.assertEqual(saved,self.k.state)
        self.assertEqual(saved['pending']['hash'],self.hash)
        self.assertEqual(saved['pending']['nonce'],7)
        self.assertEqual(saved['pending']['value'],0)
        self.assertEqual(saved['pending']['fee_review']['schema'],1)
        self.assertEqual(saved['spent'],previous['spent'])
        self.assertEqual(saved['last'],previous['last'])
        self.assertEqual(saved['next_nonce'],previous['next_nonce'])
        for event in self.log.call_args_list:
            self.assertNotEqual(event.args[0],'shutdown_after_intent_before_signer')

    def test_failed_save_after_atomic_publication_never_signs_or_discards_recovery(self):
        original_save = self.k.save
        published = []
        def publish_then_fail():
            original_save()
            published.append(self.k.path.read_bytes())
            raise OSError('inert post-publication storage fault')
        with patch.object(self.k,'save',side_effect=publish_then_fail), \
                patch('keeper.monitor.subprocess.run') as signer:
            with self.assertRaises(OSError):self.submit()
            signer.assert_not_called()
        self.assertEqual(len(published),1)
        self.assertEqual(self.k.path.read_bytes(),published[0])
        self.assertIsNone(json.loads(published[0])['pending']['hash'])
        restored = Keeper(self.cfg,rpc=self.rpc)
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertTrue(restored.poll_pending())
            self.assertFalse(self.submit(restored))
            signer.assert_not_called()
        self.assertEqual(restored.path.read_bytes(),published[0])


if __name__ == '__main__':
    unittest.main()
