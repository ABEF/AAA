"""Focused native-version keeper checks; no signer, service or Linux lock campaign."""
import copy
import json
import unittest
from unittest.mock import patch
from keeper.monitor import Keeper, NATIVE_ASSET
from zzz_ops.abi import address, calldata, keccak256
from zzz_ops.rpc import RpcError
import tests_python.test_keeper as fixtures

class NativeKeeperTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.PoolKeeperTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        self.f=f;self.rpc=f.rpc;self.cfg=f.cfg
        self.cfg['accounting_version']=2
        self.cfg['code_hashes']={'vault':'0x'+keccak256(bytes.fromhex('6000')).hex()}
        self.k=f.k=Keeper(self.cfg,rpc=self.rpc)
        self.version=2;self.buyback_balance=0
        original=self.rpc.call
        def native_call(method,params):
            if method=='eth_call' and 'from' not in params[0]:
                data=params[0]['data']
                if data==calldata('ACCOUNTING_VERSION()'):
                    self.rpc.calls.append((method,params));return '0x'+f'{self.version:064x}'
                if data[:10]==calldata('buybackBalance(address)',fixtures.B)[:10]:
                    self.rpc.calls.append((method,params));return '0x'+f'{self.buyback_balance:064x}'
            return original(method,params)
        self.rpc.call=native_call
        f.config_words[0]=0
        f.pool='0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in f.config_words[:5]))).hex()
        f.group_words[0]=int(f.pool,16);f.group_words[11]=0
        f.ids=[7];f.rebalance=False;f.reserves[NATIVE_ASSET]=17

    def test_native_pool_compound_reads_zero_currency_without_wrapper(self):
        submit=self.f.invoke()
        submit.assert_called_once_with('compounder','compound(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'compound:7')
        data=[p[0]['data'] for method,p in self.rpc.calls if method=='eth_call']
        self.assertFalse(any(d.startswith(calldata('nativeAsset(bytes32)',self.f.pool)[:10]) for d in data))
        selector=calldata('compoundBalance(uint256,address)',7,fixtures.B)[:10]
        self.assertIn(selector+f'{7:064x}'+'0'*64,data)
        self.assertEqual(self.k._bucket(7)[1],[NATIVE_ASSET,fixtures.C])

    def test_native_profile_rejects_weth_normalized_accounting(self):
        self.f.accounting_words=list(self.f.config_words);self.f.accounting_words[0]=int(fixtures.B,16)
        with self.assertRaisesRegex(RpcError,'currencies differ'):self.k._bucket(7)

    def test_version_mismatch_stops_before_scheduling(self):
        self.version=1
        with patch.object(self.k,'submit') as submit:
            with self.assertRaisesRegex(RpcError,'accounting version differs'):self.k.cycle()
            submit.assert_not_called()
        self.assertIsNone(self.k.state['pending'])

    def test_native_version_requires_exact_reviewed_runtime_pin(self):
        previous=self.cfg['code_hashes']['vault']
        for pin in ('','0x'+'00'*32,'bad'):
            self.cfg['code_hashes']['vault']=pin
            with self.subTest(pin=pin),self.assertRaises(RpcError):self.k.cycle()
        self.cfg['code_hashes']['vault']=previous
        self.k._validate_accounting_version()

    def test_missing_version_getter_fails_closed(self):
        original=self.rpc.eth_call
        def read(to,data):
            if data==calldata('ACCOUNTING_VERSION()'):return '0x'
            return original(to,data)
        with patch.object(self.rpc,'eth_call',side_effect=read):
            with self.assertRaisesRegex(RpcError,'version is unavailable'):self.k.cycle()

    def test_native_buyback_is_a_currency_argument_not_transaction_value(self):
        self.f.ids=[];self.cfg['buybacks']=[{'token':NATIVE_ASSET,'amount':3,'pool_id':self.f.pool}];self.buyback_balance=3
        submit=self.f.invoke()
        submit.assert_called_once_with('buyback','execute(address,uint256,bytes32,uint256)',
            (NATIVE_ASSET,3,self.f.pool,self.rpc.now+180),'buyback:'+NATIVE_ASSET)
        encoded=self.k._calldata('execute(address,uint256,bytes32,uint256)',NATIVE_ASSET,3,self.f.pool,100)
        self.assertEqual(encoded[10:74],'0'*64)
        self.assertEqual(encoded[74:138],f'{3:064x}')

    def test_only_reviewed_asset_argument_positions_accept_zero(self):
        self.assertEqual(self.k._asset(NATIVE_ASSET),NATIVE_ASSET)
        with self.assertRaises(ValueError):address(NATIVE_ASSET)
        for signature,args in [('keepers(address)',(NATIVE_ASSET,)),('ownerOf(uint256)',(NATIVE_ASSET,)),
                ('module(address)',(NATIVE_ASSET,))]:
            with self.subTest(signature=signature),self.assertRaises(ValueError):self.k._calldata(signature,*args)
        with self.assertRaises(ValueError):self.k._calldata('execute(address,uint256,bytes32,uint256)',NATIVE_ASSET,1,self.f.pool)
        self.cfg['sender']=NATIVE_ASSET
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)

    def test_contract_zero_addresses_and_second_currency_remain_invalid(self):
        for index in (9,10,12,14):
            previous=self.f.group_words[index];self.f.group_words[index]=0
            with self.subTest(index=index),self.assertRaises(ValueError):self.k._bucket(7)
            self.f.group_words[index]=previous

    def test_persisted_version_prevents_reinterpreting_old_pending_journal(self):
        self.k.state['next_nonce']=7
        self.k.state['pending']={'key':'harvest:7','nonce':7,'to':fixtures.B,
            'data':calldata('collectFees(uint256,uint256)',7,100),'value':0,'day':'2026-10-24','hash':fixtures.H}
        self.k.save();before=self.k.path.read_bytes();state=copy.deepcopy(self.k.state)
        legacy=copy.deepcopy(self.cfg);legacy.pop('accounting_version')
        with self.assertRaisesRegex(ValueError,'another accounting version'):Keeper(legacy,rpc=self.rpc)
        self.assertEqual(self.k.path.read_bytes(),before);self.assertEqual(self.k.state,state)
        loaded=Keeper(self.cfg,rpc=self.rpc);self.assertEqual(loaded.state['pending'],state['pending'])

    def test_legacy_state_missing_version_is_not_silently_native(self):
        self.k.save();state=json.loads(self.k.path.read_text());state.pop('accounting_version');self.k.path.write_text(json.dumps(state))
        before=self.k.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'another accounting version'):Keeper(self.cfg,rpc=self.rpc)
        self.assertEqual(self.k.path.read_bytes(),before)
        legacy=copy.deepcopy(self.cfg);legacy.pop('accounting_version')
        self.assertEqual(Keeper(legacy,rpc=self.rpc).accounting_version,1)

    def test_unsupported_or_bool_versions_rejected(self):
        for version in (0,3,True,False,'2',None):
            cfg=copy.deepcopy(self.cfg);cfg['accounting_version']=version
            with self.subTest(version=version),self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_pending_reconciliation_precedes_version_gate(self):
        # A profile mismatch must never make a saved transaction disappear.
        self.version=1;pending={'key':'saved'};self.k.state['pending']=pending
        with patch.object(self.k,'poll_pending',return_value=True),patch.object(self.k,'submit') as submit:
            self.k.cycle();submit.assert_not_called()
        self.assertIs(self.k.state['pending'],pending)

if __name__=='__main__':unittest.main()
