import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from keeper.monitor import Keeper
from keeper.royalties import BATCH, ZERO, encode_batch
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError

HASH='0x'+'ab'*32
CODE='0x6000'
PIN='0x'+keccak256(bytes.fromhex(CODE[2:])).hex()
def addr(n): return '0x'+f'{n:040x}'

class RoyaltyRPC:
    active_url='https://rpc.invalid'
    def __init__(self,contracts):
        self.c=contracts;self.calls=[];self.values={};self.fail=False;self.reorg=False;self.now=100000;self.gas=100
        def add(name,sig,value,*args):self.values[(contracts[name],calldata(sig,*args))]=value
        for name,sig,target in [('royalties','nft()','royalty_nft'),('royalties','canonicalController()','access'),
            ('royalties','converter()','royalty_converter'),('royalty_converter','ledger()','royalties'),
            ('royalty_converter','access()','access'),('royalty_converter','wrapper()','royalty_wrapper'),
            ('royalty_nft','access()','access'),('royalty_nft','royaltyRewards()','royalties')]:add(name,sig,int(contracts[target],16))
        for key,name in [('ZZZNFT','royalty_nft'),('ZZZOracle','oracle')]:add('access','module(bytes32)',int(contracts[name],16),'0x'+keccak256(key.encode()).hex())
        for name,sig,value in [('royalties','MAX_CONVERSION_NFTS()',32),('royalty_converter','MAX_LOSS_BPS()',100),
            ('royalty_converter','enabled()',1),('royalty_nft','mintedCount()',3),('royalties','activationCount()',2)]:add(name,sig,value)
        self.asset=addr(100);self.route='0x'+'cd'*32
        add('royalties','isAsset(address)',1,self.asset);add('royalties','eligibleCount(address)',2,self.asset)
        add('royalty_converter','routeEnabled(bytes32)',1,self.route)
        for n in range(1,4):
            add('royalty_nft','tokenAtOrdinal(uint256)',n,n);add('royalties','weightOf(uint256)',1 if n<3 else 0,n)
            add('royalties','claimable(uint256,address)',100,n,self.asset)
        add('oracle','quote(address,address,uint256)',20000,self.asset,contracts['royalty_wrapper'],200)
        add('access','canonicalState()',0);add('access','preparationActive()',0)
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='eth_getBlockByNumber':
            tag=params[0];return {'number':'0x64' if tag=='latest' else tag,'timestamp':hex(self.now),
                'hash':('0x'+'ef'*32) if self.reorg and len(self.calls)>20 else HASH}
        if method=='eth_getCode':return CODE
        if method=='eth_estimateGas':return hex(self.gas)
        if method=='eth_gasPrice':return '0x1'
        if method=='eth_call':
            tx=params[0];data=tx['data']
            if self.fail and data.startswith(calldata('claimable(uint256,address)',1,self.asset)[:10]):raise RpcError('unavailable')
            if data==calldata('route(bytes32)',self.route):return '0x'+f'{int(self.asset,16):064x}'+'0'*64*9
            if data.startswith(encode_batch(self.asset,[1],self.route,1,1)[:10]):return '0x'+f'{20000:064x}'
            return '0x'+f'{self.values.get((tx["to"],data),0):064x}'
        raise AssertionError(method)
    def eth_call(self,to,data):return self.call('eth_call',[{'to':to,'data':data},'latest'])

class RoyaltyKeeperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        names=['access','vault','strategy','fees','compounder','buyback','pools','royalties','royalty_converter','royalty_nft','royalty_wrapper','oracle']
        self.contracts={n:addr(i+1) for i,n in enumerate(names)};self.rpc=RoyaltyRPC(self.contracts)
        self.cfg={'chain_id':1,'sender':addr(90),'contracts':self.contracts,'confirmations':2,
            'state_path':str(Path(self.tmp.name)/'state.json'),'code_hashes':{n:PIN for n in names},
            'max_gas_limit':100000,'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,'max_daily_cost_wei':10000000,
            'royalty_conversion':{'enabled':True,'max_gas_to_output_bps':100,'assets':[{'asset':self.rpc.asset,'route_id':self.rpc.route,
            'minimum_source_units':1,'minimum_output_wei':1}]}}
        self.k=Keeper(self.cfg,rpc=self.rpc)
        clock=patch('keeper.monitor.time.time',return_value=self.rpc.now);clock.start();self.addCleanup(clock.stop)
    def test_codec_matches_solidity_dynamic_layout(self):
        encoded=encode_batch(addr(100),[1,2],ZERO,99,123)
        words=[encoded[i:i+64] for i in range(10,len(encoded),64)]
        self.assertEqual([int(v,16) for v in words],[100,160,0,99,123,2,1,2])
        self.assertEqual(encoded[:10],'0x'+keccak256(BATCH.encode()).hex()[:8])
    def test_codec_rejects_duplicate_unsorted_empty_or_large_batch(self):
        for ids in ([],[1,1],[2,1],list(range(33)),[True]):
            with self.assertRaises(ValueError):encode_batch(addr(100),ids,ZERO,1,123)
    def test_default_disabled(self):
        cfg=copy.deepcopy(self.cfg);del cfg['royalty_conversion'];k=Keeper(cfg,rpc=self.rpc);self.assertFalse(k.royalties.enabled)
    def test_missing_pins_and_malformed_config_fail(self):
        for mutate in [lambda c:c['code_hashes'].pop('royalties'),lambda c:c['royalty_conversion'].update(max_nfts_per_cycle=33),
            lambda c:c['royalty_conversion'].update(enabled='true')]:
            cfg=copy.deepcopy(self.cfg);mutate(cfg)
            with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)
    def test_pinned_scan_prepares_exact_batch_and_gas_is_separate(self):
        with patch.object(self.k,'submit',return_value=False) as submit:
            self.k.royalties.scan_once()
        name,sig,args,key=submit.call_args.args
        self.assertEqual((name,sig),('royalties',BATCH));self.assertEqual(args,(self.rpc.asset,[1,2],self.rpc.route,19800,100180))
        self.assertEqual(submit.call_args.kwargs,{'maximum_cost':198})
        calls=[p for m,p in self.rpc.calls if m=='eth_call'];self.assertTrue(all(p[1]=={'blockHash':HASH,'requireCanonical':True} for p in calls))
    def test_reorg_or_binding_change_rejects(self):
        self.rpc.reorg=True
        with self.assertRaises(RpcError):self.k.royalties.scan_once()
        self.rpc.reorg=False;self.rpc.values[(self.contracts['royalties'],calldata('converter()'))]=1
        with self.assertRaises(RpcError):self.k.royalties.scan_once()
    def test_currency_failure_rotates_without_destroying_nonce_state(self):
        self.k.royalties.routes.append(dict(self.k.royalties.routes[0],asset=addr(101)))
        self.k.state['next_nonce']=7;self.rpc.fail=True
        with patch('keeper.monitor.log') as log:
            self.assertFalse(self.k._convert_royalties());log.assert_called_once()
        self.assertEqual(self.k.state['royalty_conversion']['asset'],1);self.assertEqual(self.k.state['next_nonce'],7)
    def test_failed_swap_does_not_broadcast_or_erase_rights(self):
        self.rpc.gas=10000
        with patch('subprocess.run') as signer,patch('keeper.monitor.log') as log:
            self.assertFalse(self.k.royalties.scan_once());signer.assert_not_called()
        self.assertTrue(any(c.args[0]=='royalty_conversion_uneconomic' for c in log.call_args_list));self.assertIsNone(self.k.state['pending'])
    def test_dry_run_uses_common_simulation_without_signer(self):
        with patch('subprocess.run') as signer,patch('keeper.monitor.log') as log:
            self.assertFalse(self.k.royalties.scan_once());signer.assert_not_called()
        self.assertTrue(any(c.args[0]=='dry_run' for c in log.call_args_list))
    def test_preparation_blocks_submission(self):
        self.rpc.values[(self.contracts['access'],calldata('preparationActive()'))]=1
        self.assertFalse(self.k.submit('royalties',BATCH,(self.rpc.asset,[1],self.rpc.route,1,100100),'test'))
        self.assertFalse(any(m=='eth_estimateGas' for m,_ in self.rpc.calls))
    def test_small_batch_waits_or_recovers_membership(self):
        self.k.royalties.routes[0]['minimum_source_units']=1000
        with patch.object(self.k,'submit') as submit:self.k.royalties.scan_once();submit.assert_not_called()
        self.rpc.values[(self.contracts['royalties'],calldata('eligibleCount(address)',self.rpc.asset))]=1
        with patch.object(self.k,'submit',return_value=False) as submit:self.k.royalties.scan_once()
        self.assertEqual(submit.call_args.args[:3],('royalties','sync(address)',(self.rpc.asset,)))

if __name__=='__main__': unittest.main()
