"""Explicit native-output conversion profiles; no RPC/signing/provider qualification."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.royalties import BATCH, NATIVE, ZERO, native_quote
from tests_python.test_royalty_keeper import RoyaltyRPC, PIN, HASH, addr
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


class V4ConversionRPC(RoyaltyRPC):
    def __init__(self, contracts):
        super().__init__(contracts)
        self.policy=[int(self.asset,16),0,0,int(self.asset,16),500,60,0,501,502,1,0,2,3,4]
        self.validated=None
        self.values[contracts['royalty_converter'],calldata('v4Executor()')]=int(contracts['royalty_v4_executor'],16)
        self.values[contracts['royalty_v4_executor'],calldata('parent()')]=int(contracts['royalty_converter'],16)
        self.values[contracts['royalty_converter'],calldata('routeKind(bytes32)',self.route)]=2
        self.values[contracts['royalty_converter'],calldata('MAX_LOSS_BPS()')]=1000
        self.values[contracts['royalty_converter'],calldata('conversionLossBps()')]=100
        self.values[contracts['oracle'],native_quote(self.asset,200)]=20001
        self.values[contracts['oracle'],native_quote(self.asset,300)]=30001

    def call(self, method, params):
        if method=='eth_call':
            tx=params[0]
            if tx['data'] in (calldata('v4Route(bytes32)',self.route),calldata('validate(bytes32)',self.route)):
                self.calls.append((method,params))
                values=self.policy if tx['data']==calldata('v4Route(bytes32)',self.route) or self.validated is None else self.validated
                return '0x'+''.join(f'{n:064x}' for n in values)
        return super().call(method,params)


class TypedV4ConversionKeeperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        names=['access','vault','strategy','fees','compounder','buyback','pools','royalties','royalty_converter',
               'royalty_nft','royalty_wrapper','oracle','royalty_v4_executor']
        self.contracts={name:addr(i+1) for i,name in enumerate(names)}
        self.rpc=V4ConversionRPC(self.contracts)
        self.cfg={'chain_id':1,'sender':addr(90),'contracts':dict(self.contracts),'confirmations':2,
            'state_path':str(Path(self.tmp.name)/'state.json'),'code_hashes':{n:PIN for n in names},
            'max_gas_limit':100000,'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,'max_daily_cost_wei':10000000,
            'royalty_conversion':{'enabled':True,'profile':'v4_native','max_gas_to_output_bps':100,
                'assets':[{'asset':self.rpc.asset,'route_id':self.rpc.route,'minimum_source_units':1,'minimum_output_wei':1}]}}
        # Native-only deployments need neither a configured wrapper nor its pin.
        del self.cfg['contracts']['royalty_wrapper'];del self.cfg['code_hashes']['royalty_wrapper']
        clock=patch('keeper.monitor.time.time',return_value=self.rpc.now);clock.start();self.addCleanup(clock.stop)
        self.k=Keeper(self.cfg,rpc=self.rpc)

    def test_native_profile_uses_exact_route_helper_pins_and_native_quote(self):
        with patch.object(self.k,'submit',return_value=False) as submit:self.k.royalties.scan_once()
        self.assertEqual(submit.call_args.args[:3],('royalties',BATCH,(self.rpc.asset,[1,2],self.rpc.route,19801,100180)))
        self.assertEqual(submit.call_args.kwargs,{'maximum_cost':198})
        calls=[p for m,p in self.rpc.calls if m=='eth_call']
        self.assertTrue(all(p[1]=={'blockHash':HASH,'requireCanonical':True} for p in calls))
        self.assertTrue(any(p[0]['data']==native_quote(self.rpc.asset,200) for p in calls))
        self.assertFalse(any(p[0]['data']==calldata('wrapper()') for p in calls))

    def test_native_profile_pins_helper_and_its_fixed_parent(self):
        self.rpc.values[self.contracts['royalty_v4_executor'],calldata('parent()')]=999
        with self.assertRaisesRegex(RpcError,'binding'):self.k.royalties.scan_once()
        cfg=copy.deepcopy(self.cfg);del cfg['code_hashes']['royalty_v4_executor']
        with self.assertRaisesRegex(ValueError,'runtime pin'):Keeper(cfg,rpc=self.rpc)

    def test_missing_kind_does_not_fallback_to_legacy_route(self):
        self.rpc.values.pop((self.contracts['royalty_converter'],calldata('routeKind(bytes32)',self.rpc.route)))
        with patch.object(self.k,'submit') as submit:
            with self.assertRaisesRegex(RpcError,'kind'):self.k.royalties.scan_once()
            submit.assert_not_called()

    def test_policy_length_source_output_or_validation_mismatch_rejects(self):
        original=list(self.rpc.policy)
        for mutate in (lambda p:p.pop(),lambda p:p.__setitem__(0,999),lambda p:p.__setitem__(1,999)):
            self.rpc.policy=list(original);mutate(self.rpc.policy)
            with self.assertRaisesRegex(RpcError,'policy'):self.k.royalties.scan_once()
        self.rpc.policy=original;self.rpc.validated=list(original);self.rpc.validated[4]=3000
        with self.assertRaisesRegex(RpcError,'policy'):self.k.royalties.scan_once()

    def test_disabled_v4_route_defers_without_native_quote_or_send(self):
        self.rpc.values[self.contracts['royalty_converter'],calldata('routeEnabled(bytes32)',self.rpc.route)]=0
        with patch.object(self.k,'submit') as submit:self.assertFalse(self.k.royalties.scan_once());submit.assert_not_called()
        self.assertFalse(any(m=='eth_call' and p[0]['data']==native_quote(self.rpc.asset,200)
                             for m,p in self.rpc.calls))

    def test_bad_native_source_zero_route_or_unknown_profile_rejects_config(self):
        for mutate in (lambda c:c['royalty_conversion']['assets'][0].update(asset=NATIVE),
                       lambda c:c['royalty_conversion']['assets'][0].update(route_id=ZERO),
                       lambda c:c['royalty_conversion'].update(profile='auto')):
            cfg=copy.deepcopy(self.cfg);mutate(cfg)
            with self.assertRaises(ValueError):Keeper(cfg,rpc=self.rpc)

    def test_switching_profile_cannot_reinterpret_existing_scan_identity(self):
        cfg=copy.deepcopy(self.cfg);cfg['royalty_conversion']['profile']='v3_wrapper'
        cfg['contracts']['royalty_wrapper']=self.contracts['royalty_wrapper'];cfg['code_hashes']['royalty_wrapper']=PIN
        self.k.save()
        with self.assertRaisesRegex(ValueError,'identity changed|another deployment'):Keeper(cfg,rpc=self.rpc)

    def test_weth_source_in_explicit_v4_profile_is_swapped_not_unwrapped(self):
        # A token's equality to some wrapper address never overrides explicit v4.
        self.cfg['contracts']['royalty_wrapper']=self.rpc.asset;self.cfg['code_hashes']['royalty_wrapper']=PIN
        self.k=Keeper(self.cfg,rpc=self.rpc)
        with patch.object(self.k,'submit',return_value=False) as submit:self.k.royalties.scan_once()
        self.assertEqual(submit.call_args.args[2][2],self.rpc.route)

    def test_native_lp_profile_preserves_non_royalty_eligibility_and_gas_budget(self):
        cfg=copy.deepcopy(self.cfg);cfg['lp_conversion']=cfg.pop('royalty_conversion')
        for name,prior in [('rewards','royalties'),('lp_converter','royalty_converter'),('lp_nft','royalty_nft'),
                           ('lp_v4_executor','royalty_v4_executor')]:
            cfg['contracts'][name]=cfg['contracts'][prior];cfg['code_hashes'][name]=PIN
        cfg['state_path']=str(Path(self.tmp.name)/'lp.json')
        ledger=cfg['contracts']['rewards'];self.rpc.values[ledger,calldata('access()')]=int(cfg['contracts']['access'],16)
        self.rpc.values[cfg['contracts']['access'],calldata('module(bytes32)','0x'+keccak256(b'ZZZRewards').hex())]=int(ledger,16)
        k=Keeper(cfg,rpc=self.rpc)
        with patch.object(k,'submit',return_value=False) as submit:k.lp_rewards.scan_once()
        self.assertEqual(submit.call_args.args[:3],('rewards',BATCH,(self.rpc.asset,[1,2,3],self.rpc.route,29701,100180)))
        self.assertEqual(submit.call_args.kwargs,{'maximum_cost':297})

    def test_current_governed_cap_uses_pinned_value_and_zero_is_strict(self):
        for cap,minimum in ((0,20001),(250,19501),(1000,18001)):
            self.rpc.values[self.contracts['royalty_converter'],calldata('conversionLossBps()')]=cap
            with patch.object(self.k,'submit',return_value=False) as submit:self.k.royalties.scan_once()
            self.assertEqual(submit.call_args.args[2][3],minimum)

    def test_wrong_hard_ceiling_or_excess_operating_cap_rejects(self):
        for sig,value in (('MAX_LOSS_BPS()',100),('conversionLossBps()',1001)):
            self.rpc.values[self.contracts['royalty_converter'],calldata(sig)]=value
            with self.assertRaisesRegex(RpcError,'limit mismatch'):self.k.royalties.scan_once()
            self.rpc.values[self.contracts['royalty_converter'],calldata('MAX_LOSS_BPS()')]=1000

    def test_new_v3_profile_explicitly_uses_governed_cap_without_v4_route(self):
        cfg=copy.deepcopy(self.cfg);cfg['royalty_conversion']['profile']='v3_wrapper_configurable'
        cfg['contracts']['royalty_wrapper']=self.contracts['royalty_wrapper'];cfg['code_hashes']['royalty_wrapper']=PIN
        cfg['state_path']=str(Path(self.tmp.name)/'v3.json');k=Keeper(cfg,rpc=self.rpc)
        self.rpc.values[self.contracts['royalty_converter'],calldata('conversionLossBps()')]=250
        with patch.object(k,'submit',return_value=False) as submit:k.royalties.scan_once()
        self.assertEqual(submit.call_args.args[2][3],19500)
        self.assertFalse(any(m=='eth_call' and p[0]['data']==calldata('v4Route(bytes32)',self.rpc.route) for m,p in self.rpc.calls))


if __name__=='__main__':unittest.main()
