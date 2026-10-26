import copy
import datetime as dt
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from keeper.monitor import Keeper
from keeper.ops import create_snapshot, verify_snapshot, health_check, preflight, digest
from tests_python.test_keeper import FakeRpc, A, B
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class OpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name);self.rpc = FakeRpc()
        self.cfg = {'chain_id':1,'sender':A,'contracts':{k:B for k in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'state_path':str(self.root/'state.json'),'health_path':str(self.root/'health.json'),
            'rpc_urls':['https://rpc.invalid/DO-NOT-EXPORT'],'keystore':'/secret/key','password_file':'/secret/password',
            'confirmations':2,'reviewed_for_live_use':True,'receipt_fee_policy':'included',
            'max_transaction_cost_wei':1000,'max_daily_cost_wei':10000,
            'code_hashes':{k:'0x'+keccak256(bytes.fromhex('6000')).hex() for k in ('access','vault','strategy','fees','compounder','buyback','pools')}}
        self.k = Keeper(self.cfg,rpc=self.rpc);self.k.state['next_nonce'] = 0;self.k.save()
        self.now = int(time.time());stamp = dt.datetime.fromtimestamp(self.now,dt.timezone.utc).isoformat()
        self.health = {'time':stamp,'last_success_at':stamp,'chain_id':1,'sender':A,'status':'healthy','live':True,
            'configuration_sha256':digest(self.cfg),
            'pending':False,'strategy_paused':False,'preparation_active':False,'canonical_state':0,
            'skipped_buckets':0,'blocked_actions':0,'consecutive_failures':0}
        original = self.rpc.call
        def call(method,params):
            if method == 'eth_getTransactionCount': return '0x0'
            if method == 'eth_call':
                value = params[0]['data'] not in (calldata('paused()'),calldata('preparationActive()'),calldata('canonicalState()'))
                return '0x'+f'{int(value):064x}'
            return original(method,params)
        self.rpc.call = call

    def check_health(self):
        Path(self.cfg['health_path']).write_text(json.dumps(self.health))
        return health_check(self.cfg,now=self.now)

    def test_healthy_requires_fresh_live_identity_and_success(self):
        self.assertTrue(self.check_health()['ok'])
        original = copy.deepcopy(self.health)
        for key,value in [('status','running'),('status','degraded'),('live',False),('chain_id',2),('pending',True),
                ('strategy_paused',True),('skipped_buckets',1),('blocked_actions',1),('consecutive_failures',1),
                ('time','2000-01-01T00:00:00+00:00'),('last_success_at','2000-01-01T00:00:00+00:00')]:
            self.health = {**original,key:value}
            with self.subTest(key=key,value=value):self.assertFalse(self.check_health()['ok'])

    def test_future_heartbeat_and_missing_counters_do_not_pass(self):
        self.health['time'] = dt.datetime.fromtimestamp(self.now+60,dt.timezone.utc).isoformat()
        self.assertFalse(self.check_health()['ok'])
        self.health.pop('pending');self.assertFalse(self.check_health()['ok'])

    def test_dry_run_requires_explicit_health_mode(self):
        self.health.update(live=False,status='dry_run');self.assertFalse(self.check_health()['ok'])
        self.assertTrue(health_check(self.cfg,allow_dry_run=True,now=self.now)['ok'])

    def test_missing_or_corrupt_health_never_looks_healthy(self):
        with self.assertRaises(FileNotFoundError):health_check(self.cfg)
        Path(self.cfg['health_path']).write_text('broken')
        with self.assertRaises(ValueError):health_check(self.cfg)

    def test_first_pending_cycle_has_actionable_health_reasons(self):
        self.health.update(status='awaiting_receipt',pending=True,last_success_at=None)
        result=self.check_health()
        self.assertFalse(result['ok']);self.assertIn('pending',result['reasons'])
        self.assertIn('no_successful_cycle_yet',result['reasons'])

    def test_snapshot_preserves_pending_budget_and_omits_secrets(self):
        self.k.state.update(spent={'2026-10-16':42},pending={'nonce':0,'to':B,'data':calldata('collectFees(uint256,uint256)',1,123),
            'value':0,'day':'2026-10-16','key':'harvest:1','hash':None});self.k.save()
        path = self.root/'snapshot.json'
        with patch('subprocess.run') as signer,patch('zzz_ops.rpc.Rpc.call') as rpc:
            create_snapshot(self.cfg,path);signer.assert_not_called();rpc.assert_not_called()
        content = path.read_text();self.assertNotIn('DO-NOT-EXPORT',content);self.assertNotIn('/secret',content)
        self.assertEqual(json.loads(content)['payload']['state'],self.k.state)
        self.assertTrue(verify_snapshot(self.cfg,path)['ok'])

    def test_snapshot_is_exclusive_and_never_overwrites_state(self):
        before = self.k.path.read_bytes()
        with self.assertRaises(FileExistsError):create_snapshot(self.cfg,self.k.path)
        self.assertEqual(before,self.k.path.read_bytes())
        self.assertFalse(list(self.root.glob('.keeper-snapshot-*')))

    def test_snapshot_corruption_age_configuration_and_identity(self):
        path = self.root/'snapshot.json';create_snapshot(self.cfg,path)
        original = json.loads(path.read_text())
        self.assertFalse(verify_snapshot(self.cfg,path,now=self.now+7200)['ok'])
        self.assertFalse(verify_snapshot({**self.cfg,'confirmations':3},path)['ok'])
        with self.assertRaises(ValueError):verify_snapshot({**self.cfg,'chain_id':2},path)
        original['payload']['state']['next_nonce'] = 12;path.write_text(json.dumps(original))
        with self.assertRaises(ValueError):verify_snapshot(self.cfg,path)

    def test_preflight_is_read_only_and_never_calls_signer(self):
        before = self.k.path.read_bytes()
        with patch('subprocess.run') as signer:
            self.assertTrue(preflight(self.cfg,rpc=self.rpc)['ok']);signer.assert_not_called()
        self.assertEqual(before,self.k.path.read_bytes())

    def test_preflight_refuses_missing_state_nonce_drift_or_pending(self):
        self.k.path.unlink()
        with self.assertRaises(ValueError):preflight(self.cfg,rpc=self.rpc)
        self.k.save()
        original = self.rpc.call
        self.rpc.call = lambda method,params: '0x1' if method=='eth_getTransactionCount' else original(method,params)
        self.assertIn('nonce_reconciliation_required',preflight(self.cfg,rpc=self.rpc)['reasons'])
        self.rpc.call = original
        self.k.state['pending'] = {'nonce':0,'to':B,'data':calldata('collectFees(uint256,uint256)',1,123),
            'value':0,'day':'2026-10-16','key':'harvest:1','hash':None};self.k.save()
        self.assertIn('pending_intent_requires_reconciliation',preflight(self.cfg,rpc=self.rpc)['reasons'])

    def test_preflight_unqualified_fee_or_review_cannot_pass(self):
        for change in ({'receipt_fee_policy':'unverified'},{'reviewed_for_live_use':False}):
            self.assertFalse(preflight({**self.cfg,**change},rpc=self.rpc)['ok'])

    def test_preflight_low_balance_or_revoked_role_cannot_pass(self):
        original = self.rpc.call
        def low(method,params):return '0x0' if method == 'eth_getBalance' else original(method,params)
        self.rpc.call = low
        self.assertIn('balance_below_transaction_budget',preflight(self.cfg,rpc=self.rpc)['reasons'])
        def revoked(method,params):
            if method=='eth_call' and params[0]['data']==calldata('keepers(address)',A):return '0x'+'0'*64
            return original(method,params)
        self.rpc.call = revoked
        self.assertIn('keeper_not_authorized',preflight(self.cfg,rpc=self.rpc)['reasons'])

    def test_preflight_cannot_approve_wrong_native_accounting_abi(self):
        self.cfg['accounting_version'] = 2
        self.k.state['accounting_version'] = 2
        self.k.save(); before = self.k.path.read_bytes()
        # Runtime pin is present and matches. The actual version getter is 1,
        # so the native profile must fail just as live startup would.
        with patch('subprocess.run') as signer, self.assertRaisesRegex(RpcError,'accounting version differs'):
            preflight(self.cfg,rpc=self.rpc)
        signer.assert_not_called()
        self.assertEqual(self.k.path.read_bytes(),before)
