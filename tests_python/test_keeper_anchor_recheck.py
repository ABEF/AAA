"""Late prior-cost anchor checks using inert RPC and temporary journals.

These cases exercise the real checkpoint, submission and recovery code. Runtime,
lifecycle and LP-policy admission are explicit inert seams in submission tests;
no node, keystore, external signer or existing journal is used. A provider is
still trusted to give coherent headers; this is not an ancestry proof against
malicious per-call fork switching or a guarantee about later inclusion.
"""
import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, ROYALTY_BATCH
from zzz_ops.abi import calldata
from zzz_ops.rpc import RpcError


SENDER = '0x'+'11'*20
TARGET = '0x'+'22'*20
ANCHOR_HASH = '0x'+'aa'*32
SUCCESSOR_HASH = '0x'+'bb'*32
TIP_HASH = '0x'+'cc'*32
CHANGED_HASH = '0x'+'dd'*32
TRANSACTION_HASH = '0x'+'ee'*32


class InertAnchorRPC:
    active_url = 'https://rpc.invalid'

    def __init__(self):
        self.now = 1_795_654_800
        self.calls = []
        self.nonce = 7
        self.headers = {
            98: {'number':'0x62','timestamp':hex(self.now-2),'hash':ANCHOR_HASH},
            99: {'number':'0x63','timestamp':hex(self.now-1),'hash':SUCCESSOR_HASH},
            100: {'number':'0x64','timestamp':hex(self.now),'hash':TIP_HASH},
        }
        self.receipt = None
        self.transaction = None
        self.after = None
        self.conversion = False

    def call(self, method, params):
        self.calls.append((method,copy.deepcopy(params)))
        if method == 'eth_getBlockByNumber':
            number = 100 if params[0] == 'latest' else int(params[0],16)
            result = copy.deepcopy(self.headers[number])
        elif method == 'eth_getTransactionReceipt': result = copy.deepcopy(self.receipt)
        elif method == 'eth_getTransactionByHash': result = copy.deepcopy(self.transaction)
        elif method == 'eth_getTransactionCount': result = hex(self.nonce)
        elif method == 'eth_getBalance': result = hex(10**18)
        elif method == 'eth_estimateGas': result = '0x64'
        elif method == 'eth_gasPrice': result = '0x2'
        elif method == 'eth_call':
            result = '0x'+f'{1:064x}' if self.conversion else '0x'
        else: raise AssertionError('Unexpected inert RPC method: '+method)
        if self.after is not None: self.after(method,params)
        return result

    def eth_call(self, to, data):
        return self.call('eth_call',[{'to':to,'data':data},'latest'])


class KeeperAnchorRecheckTests(unittest.TestCase):
    def fixture(self, *, first_nonce=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        rpc = InertAnchorRPC()
        config = {
            'chain_id':1,'sender':SENDER,
            'contracts':{name:TARGET for name in
                ('access','vault','strategy','fees','compounder','buyback','pools','rewards')},
            'state_path':str(Path(temporary.name)/'state.json'),'confirmations':2,
            'max_gas_limit':100_000,'max_gas_price_wei':100,
            'max_transaction_cost_wei':1_000_000,'max_daily_cost_wei':10_000_000,
        }
        keeper = Keeper(config,rpc=rpc)
        keeper.live = True
        keeper.cast = '/inert/cast'
        keeper.keystore = Path('/inert/keystore')
        keeper.password = Path('/inert/password')
        keeper.fee_policy = 'included'
        # These tests isolate late chain-anchor validity, not deployment/LP
        # admission. No on-chain or financial policy is replaced in production.
        keeper._validate_accounting_version = lambda: None
        keeper._validate_code_hashes = lambda: None
        keeper._validate_lp_routing = lambda **_: None
        keeper._defer_for_lifecycle = lambda *_: False
        keeper._rebalance_submission_ready = lambda _: True
        keeper._compound_submission_ready = lambda _: True
        if first_nonce:
            keeper.state['next_nonce'] = 0
            rpc.nonce = 0
        else:
            keeper.state['next_nonce'] = 7
            keeper.state['receipt_anchor'] = {
                'number':98,'hash':ANCHOR_HASH,'timestamp':rpc.now-2,'nonce':6}
            keeper.state['spent']['2026-11-25'] = 19
        keeper.save()
        clock = patch('keeper.monitor.time.time',side_effect=lambda:rpc.now)
        quiet = patch('keeper.monitor.log')
        clock.start();self.addCleanup(clock.stop)
        quiet.start();self.addCleanup(quiet.stop)
        return keeper,rpc

    def receipt(self, keeper, rpc, *, success=True):
        nonce = keeper.state['next_nonce']
        data = calldata('collectFees(uint256,uint256)',1,rpc.now+180)
        keeper.state['pending'] = {
            'key':'collect:1','nonce':nonce,'to':TARGET,'data':data,'value':10,
            'day':'2026-11-26','hash':TRANSACTION_HASH,
            'fee_review':{'schema':1,'gas_limit':256,'max_fee_per_gas':2,
                'l1_fee_allowance_wei':0,'maximum_cost_wei':522,
                'receipt_fee_policy':'included'},
        }
        rpc.receipt = {
            'transactionHash':TRANSACTION_HASH,'blockNumber':'0x63',
            'blockHash':SUCCESSOR_HASH,'status':hex(int(success)),
            'gasUsed':'0x64','effectiveGasPrice':'0x2','from':SENDER,
            'to':TARGET,'transactionIndex':'0x0',
        }
        rpc.transaction = {
            'hash':TRANSACTION_HASH,'from':SENDER,'to':TARGET,'nonce':hex(nonce),
            'input':data,'value':'0xa','blockNumber':'0x63',
            'blockHash':SUCCESSOR_HASH,'transactionIndex':'0x0','gas':'0x100',
            'type':'0x0','chainId':'0x1','v':'0x25','gasPrice':'0x2',
        }
        keeper.save()

    def unchanged(self, keeper, state, raw):
        self.assertEqual(state,keeper.state)
        self.assertEqual(raw,keeper.path.read_bytes())

    def blocked_recovery(self, *, success):
        keeper,rpc = self.fixture()
        self.receipt(keeper,rpc,success=success)
        before,raw = copy.deepcopy(keeper.state),keeper.path.read_bytes()
        # An honest reorg can follow the initial anchor check. The successor
        # receipt/header/transaction subsequently describe the new branch.
        def reorg(method, _):
            if method == 'eth_getTransactionReceipt':
                rpc.headers[98]['hash'] = CHANGED_HASH
        rpc.after = reorg
        with patch('keeper.monitor.run_cast') as signer:
            with self.assertRaisesRegex(RpcError,'Confirmed receipt checkpoint changed'):
                keeper.poll_pending()
            signer.assert_not_called()
        self.unchanged(keeper,before,raw)
        self.assertEqual(0,keeper.confirmed_reverts)
        self.assertEqual(('eth_getBlockByNumber',['0x62',False]),rpc.calls[-1])

    def test_successor_cannot_replace_a_prior_anchor_changed_during_recovery(self):
        self.blocked_recovery(success=True)

    def test_reverted_successor_cannot_hide_invalidated_prior_spending(self):
        self.blocked_recovery(success=False)

    def test_metadata_read_completes_before_the_late_prior_anchor_check(self):
        keeper,rpc = self.fixture()
        self.receipt(keeper,rpc)
        keeper.state['pending']['metadata_observation'] = {'inert':'not a live payload'}
        keeper.save()
        before,raw = copy.deepcopy(keeper.state),keeper.path.read_bytes()
        def metadata(*_):
            rpc.headers[98]['hash'] = CHANGED_HASH
            return {'inert':'not adopted'}
        with patch.object(keeper,'_confirm_metadata',side_effect=metadata) as confirm, \
                patch('keeper.monitor.run_cast') as signer:
            with self.assertRaisesRegex(RpcError,'Confirmed receipt checkpoint changed'):
                keeper.poll_pending()
            confirm.assert_called_once()
            signer.assert_not_called()
        self.unchanged(keeper,before,raw)

    def test_healthy_success_and_revert_keep_fee_accounting_and_final_proof_order(self):
        for success in (True,False):
            with self.subTest(success=success):
                keeper,rpc = self.fixture()
                self.receipt(keeper,rpc,success=success)
                with patch('keeper.monitor.run_cast') as signer:
                    self.assertFalse(keeper.poll_pending())
                    signer.assert_not_called()
                self.assertIsNone(keeper.state['pending'])
                self.assertEqual(8,keeper.state['next_nonce'])
                self.assertEqual({'number':99,'hash':SUCCESSOR_HASH,
                    'timestamp':rpc.now-1,'nonce':7},keeper.state['receipt_anchor'])
                day = dt.datetime.fromtimestamp(rpc.now-1,dt.timezone.utc).date().isoformat()
                self.assertEqual(200+(10 if success else 0),keeper.state['spent'][day])
                self.assertEqual(19,keeper.state['spent']['2026-11-25'])
                self.assertEqual(int(not success),keeper.confirmed_reverts)
                self.assertEqual(keeper.state,json.loads(keeper.path.read_bytes()))
                self.assertEqual([
                    ('eth_getBlockByNumber',['0x62',False]),
                    ('eth_getBlockByNumber',['latest',False]),
                    ('eth_getBlockByNumber',['0x63',False]),
                ],rpc.calls[-3:])
                self.assertEqual(2,rpc.calls.count(('eth_getBlockByNumber',['0x62',False])))

    def test_first_nonce_recovery_has_no_extra_anchor_rpc(self):
        keeper,rpc = self.fixture(first_nonce=True)
        self.receipt(keeper,rpc)
        with patch('keeper.monitor.run_cast') as signer:
            self.assertFalse(keeper.poll_pending())
            signer.assert_not_called()
        self.assertEqual(1,keeper.state['next_nonce'])
        self.assertNotIn(('eth_getBlockByNumber',['0x62',False]),rpc.calls)
        self.assertEqual(2,rpc.calls.count(('eth_getBlockByNumber',['latest',False])))
        self.assertEqual(2,rpc.calls.count(('eth_getBlockByNumber',['0x63',False])))

    def test_successor_change_after_late_anchor_check_is_still_blocked_by_final_header(self):
        keeper,rpc = self.fixture()
        self.receipt(keeper,rpc)
        before,raw = copy.deepcopy(keeper.state),keeper.path.read_bytes()
        anchors = 0
        def reorg_after_anchor(method, params):
            nonlocal anchors
            if method == 'eth_getBlockByNumber' and params[0] == '0x62':
                anchors += 1
                if anchors == 2: rpc.headers[99]['hash'] = CHANGED_HASH
        rpc.after = reorg_after_anchor
        with patch('keeper.monitor.run_cast') as signer:
            with self.assertRaisesRegex(RpcError,'Receipt block changed before checkpoint'):
                keeper.poll_pending()
            signer.assert_not_called()
        self.unchanged(keeper,before,raw)

    def action(self, keeper, rpc, kind):
        if kind == 'rebalance':
            return 'vault','rebalance(uint256,uint128,uint256)',(1,17,rpc.now+180),'rebalance:1'
        if kind == 'compound':
            return 'compounder','compound(uint256,uint128,uint256)',(1,17,rpc.now+180),'compound:1'
        if kind == 'conversion':
            keeper.accounting_version = 7
            rpc.conversion = True
            return 'rewards',ROYALTY_BATCH,(TARGET,[1],ANCHOR_HASH,1,rpc.now+180),'lp_convert:1'
        return 'vault','collectFees(uint256,uint256)',(1,rpc.now+180),'harvest:1'

    def blocked_submission(self, kind):
        keeper,rpc = self.fixture()
        action = self.action(keeper,rpc,kind)
        before,raw = copy.deepcopy(keeper.state),keeper.path.read_bytes()
        balances = 0
        def reorg_after_funding(method, _):
            nonlocal balances
            if method == 'eth_getBalance':
                balances += 1
                if balances == (2 if kind in ('rebalance','compound') else 1):
                    rpc.headers[98]['hash'] = CHANGED_HASH
        rpc.after = reorg_after_funding
        with patch('keeper.monitor.run_cast') as signer:
            with self.assertRaisesRegex(RpcError,'Confirmed receipt checkpoint changed'):
                keeper.submit(*action)
            signer.assert_not_called()
        self.unchanged(keeper,before,raw)
        self.assertIsNone(keeper.state['pending'])
        self.assertEqual(('eth_getBlockByNumber',['0x62',False]),rpc.calls[-1])

    def test_late_rebalance_review_cannot_sign_against_an_invalidated_cost_anchor(self):
        self.blocked_submission('rebalance')

    def test_late_compound_review_cannot_sign_against_an_invalidated_cost_anchor(self):
        self.blocked_submission('compound')

    def test_late_lp_conversion_review_cannot_sign_against_an_invalidated_cost_anchor(self):
        self.blocked_submission('conversion')

    def test_late_harvest_review_cannot_sign_against_an_invalidated_cost_anchor(self):
        self.blocked_submission('harvest')

    def test_healthy_submission_keeps_exact_intent_and_last_head_after_anchor_for_all_branches(self):
        for kind in ('rebalance','compound','conversion','harvest'):
            with self.subTest(kind=kind):
                keeper,rpc = self.fixture()
                name,signature,args,key = self.action(keeper,rpc,kind)
                before = copy.deepcopy(keeper.state)
                def sign(command, **_):
                    saved = json.loads(keeper.path.read_bytes())
                    pending = saved['pending']
                    self.assertEqual(before['receipt_anchor'],saved['receipt_anchor'])
                    self.assertEqual(before['spent'],saved['spent'])
                    self.assertIsNone(pending['hash'])
                    self.assertEqual(7,pending['nonce'])
                    self.assertEqual(pending['data'],command[3])
                    self.assertEqual({'schema':1,'gas_limit':125,'max_fee_per_gas':2,
                        'l1_fee_allowance_wei':0,'maximum_cost_wei':250,
                        'receipt_fee_policy':'included'},pending['fee_review'])
                    self.assertEqual([
                        ('eth_getBlockByNumber',['0x62',False]),
                        ('eth_getBlockByNumber',['latest',False]),
                    ],rpc.calls[-2:])
                    return subprocess.CompletedProcess(command,0,TRANSACTION_HASH,'')
                with patch('keeper.monitor.run_cast',side_effect=sign) as signer:
                    self.assertTrue(keeper.submit(name,signature,args,key))
                    signer.assert_called_once()
                self.assertEqual(TRANSACTION_HASH,keeper.state['pending']['hash'])
                self.assertEqual(before['spent'],keeper.state['spent'])
                self.assertEqual(2,rpc.calls.count(('eth_getBlockByNumber',['0x62',False])))

    def test_first_nonce_submission_keeps_anchor_checks_rpc_free(self):
        keeper,rpc = self.fixture(first_nonce=True)
        action = self.action(keeper,rpc,'harvest')
        with patch('keeper.monitor.run_cast',return_value=
                subprocess.CompletedProcess([],0,TRANSACTION_HASH,'')) as signer:
            self.assertTrue(keeper.submit(*action))
            signer.assert_called_once()
        self.assertIsNone(keeper.state['receipt_anchor'])
        self.assertNotIn(('eth_getBlockByNumber',['0x62',False]),rpc.calls)
        self.assertEqual(2,rpc.calls.count(('eth_getBlockByNumber',['latest',False])))


if __name__ == '__main__': unittest.main()
