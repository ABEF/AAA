import json,tempfile,time,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from keeper.monitor import Keeper
from zzz_ops.rpc import RpcError
from zzz_ops.abi import keccak256,calldata
A='0x'+'11'*20;B='0x'+'22'*20;H='0x'+'ab'*32
class FakeRpc:
    active_url='https://rpc.invalid'
    def __init__(self):self.now=int(time.time());self.gas=100;self.gas_price=2;self.receipt=None;self.tx=None;self.error=False;self.calls=[]
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='eth_getBlockByNumber':return {'number':'0x64','timestamp':hex(self.now),'hash':H}
        if method=='eth_call':
            if self.error:raise RpcError('simulation failed')
            return '0x'+'0'*64
        if method=='eth_estimateGas':return hex(self.gas)
        if method=='eth_gasPrice':return hex(self.gas_price)
        if method=='eth_getTransactionCount':return '0x7'
        if method=='eth_getCode':return '0x6000'
        if method=='eth_getTransactionReceipt':return self.receipt
        if method=='eth_getTransactionByHash':return self.tx
        raise AssertionError(method)
    def eth_call(self,to,data):return self.call('eth_call',[{'to':to,'data':data},'latest'])
class KeeperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.rpc=FakeRpc()
        self.cfg={'chain_id':1,'sender':A,'contracts':{k:B for k in ['access','vault','strategy','fees','compounder','buyback']},
            'state_path':str(Path(self.tmp.name)/'state.json'),'confirmations':2,'max_gas_limit':100000,
            'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,'max_daily_cost_wei':10000000}
        self.k=Keeper(self.cfg,rpc=self.rpc)
        self.quiet=patch('keeper.monitor.log');self.quiet.start();self.addCleanup(self.quiet.stop)
    def enable_test_signer(self):
        self.k.live=True;self.k.cast='/mock/cast';self.k.keystore=Path('/mock/key');self.k.password=Path('/mock/pass')
        self.k._validate_code_hashes=lambda:None
    def pending(self):
        self.k.state['pending']={'key':'collect:1','nonce':7,'to':B,'data':calldata('collectFees(uint256,uint256)',1,123),
            'value':10,'day':'2026-10-14','hash':H}
        return self.k.state['pending']
    def receipt(self,success=True):
        p=self.pending()
        self.rpc.receipt={'blockNumber':'0x63','blockHash':H,'status':hex(int(success)),'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x5'}
        self.rpc.tx={'from':A,'to':B,'nonce':'0x7','input':p['data'],'value':hex(p['value'])}
    def test_default_dry_run_never_signs(self):
        with patch('subprocess.run') as run:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
            run.assert_not_called();self.assertIsNone(self.k.state['pending']);self.assertFalse(self.k.path.exists())
    def test_live_requires_explicit_review(self):
        with self.assertRaises(ValueError):Keeper(self.cfg,live=True,rpc=self.rpc)
    def test_bad_chain_state_rejected(self):
        self.k.state['chain_id']=2;self.k.save()
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_simulation_failure_never_signs(self):
        self.enable_test_signer();self.rpc.error=True
        with patch('subprocess.run') as run:
            with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            run.assert_not_called();self.assertIsNone(self.k.state['pending'])
    def test_gas_cap(self):
        self.rpc.gas=1000000
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_gas_price_cap(self):
        self.rpc.gas_price=101
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_cost_cap(self):
        self.cfg['max_transaction_cost_wei']=1
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_stale_head_rejected(self):
        self.rpc.now-=1000
        with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
    def test_broadcast_state_durable_before_signer(self):
        self.enable_test_signer()
        def run(*args,**kwargs):
            state=json.loads(self.k.path.read_text());self.assertIsNone(state['pending']['hash']);self.assertEqual(state['pending']['nonce'],7)
            return subprocess.CompletedProcess(args[0],0,json.dumps(H),'')
        with patch('subprocess.run',side_effect=run):
            self.assertTrue(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
        self.assertEqual(self.k.state['pending']['hash'],H)
    def test_timeout_preserves_ambiguous_state(self):
        self.enable_test_signer()
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('cast',90)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            self.assertIsNotNone(self.k.state['pending']);self.assertIsNone(self.k.state['pending']['hash'])
            self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            self.assertEqual(run.call_count,1)
    def test_pending_waits(self):
        self.pending();self.assertTrue(self.k.poll_pending());self.assertIsNotNone(self.k.state['pending'])
    def test_success_accounts_actual_cost(self):
        self.receipt();self.assertFalse(self.k.poll_pending())
        self.assertEqual(self.k.state['spent']['2026-10-14'],215)
        self.assertEqual(self.k.state['last']['collect:1'],self.rpc.now)
    def test_failed_tx_not_marked_success(self):
        self.receipt(False);self.k.poll_pending()
        self.assertEqual(self.k.state['spent']['2026-10-14'],205);self.assertNotIn('collect:1',self.k.state['last'])
    def test_wrong_sender_fails_closed(self):
        self.receipt();self.rpc.tx['from']=B
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertIsNotNone(self.k.state['pending'])
    def test_wrong_value_fails_closed(self):
        self.receipt();self.rpc.tx['value']='0xff'
        with self.assertRaises(RpcError):self.k.poll_pending()
    def test_wrong_calldata_fails_closed(self):
        self.receipt();self.rpc.tx['input']='0x'
        with self.assertRaises(RpcError):self.k.poll_pending()
    def test_receipt_reorg_not_confirmed(self):
        self.receipt();self.rpc.receipt['blockHash']='0x'+'00'*32
        self.assertTrue(self.k.poll_pending());self.assertIsNotNone(self.k.state['pending'])
    def test_insufficient_confirmations_waits(self):
        self.receipt();self.rpc.receipt['blockNumber']='0x64'
        self.assertTrue(self.k.poll_pending())
    def test_unknown_resolve_hash_rejected(self):
        with self.assertRaises(ValueError):self.k.resolve_pending('0x123')
    def test_changed_code_rejected(self):
        self.cfg['code_hashes']={k:'0x'+keccak256(b'wrong').hex() for k in self.cfg['contracts']}
        with self.assertRaises(ValueError):self.k._validate_code_hashes()
    def test_valid_code_hash_accepted(self):
        self.cfg['code_hashes']={k:'0x'+keccak256(bytes.fromhex('6000')).hex() for k in self.cfg['contracts']}
        self.k._validate_code_hashes()
