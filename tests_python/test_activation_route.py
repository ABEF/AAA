"""Offline route/preflight regressions. Mock responses are not market evidence."""
import unittest
import contextlib
import io
import json
from unittest.mock import patch
from zzz_ops import activation_route as ar
from zzz_ops.abi import calldata, keccak256, word

def words(*values): return '0x'+''.join(f'{v:064x}' for v in values)
def addr(value): return words(int(value,16))

class RouteRpc:
    chain_id=4663
    def __init__(self):
        self.snapshot=ar.Snapshot(1000000,'0x'+'ab'*32,200000)
        self.code={a:'0x60016000' for a in ar.CODE_HASHES}
        self.replies={}; self.calls=[]; self.storage={}
        self.block_hash=self.snapshot.block_hash
        self._set(ar.USDC,'decimals()',6); self._set(ar.USDG,'decimals()',6)
        self._set(ar.WETH,'decimals()',18); self._set(ar.ZZZ,'decimals()',18)
        for target,signature,result in [
            (ar.USDC,'l1Address()',ar.L1_USDC),(ar.USDC,'l2Gateway()',ar.L2_GATEWAY),
            (ar.USDC_BEACON,'implementation()',ar.USDC_IMPLEMENTATION),
            (ar.USDC_BEACON,'owner()',ar.USDC_BEACON_OWNER),
            (ar.USDG,'owner()',ar.USDG_ADMIN),(ar.USDG,'defaultAdmin()',ar.USDG_ADMIN),
            (ar.WETH,'l1Address()',ar.L1_WETH),(ar.WETH,'l2Gateway()',ar.L2_WETH_GATEWAY),
        ]: self.replies[target,calldata(signature)]=addr(result)
        self._set(ar.USDG,'paused()',0)
        self.replies[ar.L2_ROUTER,calldata('calculateL2TokenAddress(address)',ar.L1_USDC)]=addr(ar.USDC)
        self.replies[ar.L2_ROUTER,calldata('getGateway(address)',ar.L1_USDC)]=addr(ar.L2_GATEWAY)
        self.storage[ar.USDC,ar._slot('beacon')]=addr(ar.USDC_BEACON)
        self.storage[ar.USDG,ar._slot('implementation')]=addr(ar.USDG_IMPLEMENTATION)
        self.storage[ar.WETH,ar._slot('implementation')]=addr(ar.WETH_IMPLEMENTATION)
        for symbol,feed in ar.FEEDS.items():
            self._set(feed,'decimals()',8)
            self.replies[feed,calldata('latestRoundData()')]=words(8,2500*10**8 if symbol=='ETH' else 10**8,199000,199005,8)
        for target in (ar.QUOTER,ar.SWAP_ROUTER):
            self.replies[target,calldata('factory()')]=addr(ar.FACTORY)
            self.replies[target,calldata('WETH9()')]=addr(ar.WETH)
        for fee,pool in ar.USDG_POOLS.items():
            self.code[pool]='0x60026000'
            self.replies[ar.FACTORY,calldata('getPool(address,address,uint24)',ar.USDG,ar.WETH,fee)]=addr(pool)
            for signature,result in [('factory()',ar.FACTORY),('token0()',ar.WETH),('token1()',ar.USDG)]:
                self.replies[pool,calldata(signature)]=addr(result)
            self._set(pool,'fee()',fee); self._set(pool,'liquidity()',10**18)
            self.replies[pool,calldata('slot0()')]=words(2**96,0,1,1,1,0,1)
            self.replies[ar.WETH,calldata('balanceOf(address)',pool)]=words(10**18)

    def _set(self,target,signature,value): self.replies[target,calldata(signature)]=words(value)
    def call(self,method,params=None):
        self.calls.append((method,params))
        if method=='eth_chainId': return self.chain_id
        if method=='eth_blockNumber': return hex(self.snapshot.number+12)
        if method=='eth_getBlockByNumber':
            return {'number':hex(self.snapshot.number),'hash':self.block_hash,'timestamp':hex(self.snapshot.timestamp)}
        if method=='eth_getCode': return self.code.get(params[0],'0x')
        if method=='eth_getStorageAt': return self.storage[params[0],params[1]]
        raise AssertionError('Unexpected or non-read-only method: '+method)
    def eth_call(self,to,data,sender=None,block='latest'):
        self.calls.append(('eth_call',[to,data,sender,block]))
        if block!=self.snapshot.tag: raise AssertionError('Unpinned state read')
        selector='0x'+keccak256(b'quoteExactInputSingle((address,address,uint256,uint24,uint160))').hex()[:8]
        if to==ar.QUOTER and data.startswith(selector):
            fields=[int(data[i:i+64],16) for i in range(10,len(data),64)]
            fee=fields[3]; amount=fields[2]
            out={100:39960,500:39980,3000:39800,10000:39000}[fee]*10**12*amount//100_000_000
            return words(out,2**96,1,90000)
        return self.replies[to,data]

class ActivationRouteTests(unittest.TestCase):
    def setUp(self):
        self.rpc=RouteRpc()
        self.pins=patch.dict(ar.CODE_HASHES,{a:'0x'+keccak256(bytes.fromhex(code[2:])).hex() for a,code in self.rpc.code.items() if a in ar.CODE_HASHES})
        self.pins.start();self.addCleanup(self.pins.stop)
        self.reader=ar.ActivationRouteReader(self.rpc,self.rpc.snapshot)

    def test_quote_uses_best_funded_pool_and_preserves_combined_one_percent_budget(self):
        quote=self.reader.quote_usdg_to_weth(100_000_000)
        self.assertEqual(quote['fee'],500); self.assertEqual(quote['amount_out'],39980*10**12)
        self.assertEqual(quote['minimum_output'],39980*10**12*9980//10000)
        self.assertEqual(quote['required_final_lp_usd_18'],99*10**18)
        self.assertGreaterEqual(quote['minimum_output_usd_18'],quote['required_final_lp_usd_18'])
        self.assertEqual(quote['remaining_lp_leg_loss_bps'],75)
        self.assertFalse(quote['activation_ready']);self.assertFalse(quote['gas_included_in_execution_loss'])
        self.assertNotIn('transaction',quote)

    def test_prices_use_actual_stable_price_not_assumed_peg(self):
        feed=ar.FEEDS['USDG'];self.rpc.replies[feed,calldata('latestRoundData()')]=words(8,99_000_000,199000,199005,8)
        with self.assertRaisesRegex(ar.RouteError,'below'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_minimum_input_ceil_handles_slight_depeg_without_rounding_below_100usd(self):
        feed=ar.FEEDS['USDG'];self.rpc.replies[feed,calldata('latestRoundData()')]=words(8,99_999_000,199000,199005,8)
        minimum=self.reader.minimum_input_amount('USDG')
        self.assertEqual(minimum,100_001_001)
        price=self.reader.price_usd_18('USDG')
        self.assertGreaterEqual(minimum*price//10**6,100*10**18)
        self.assertLess((minimum-1)*price//10**6,100*10**18)

    def test_below_minimum_zero_negative_bool_and_overflow_inputs_rejected(self):
        for value in (0,-1,True,2**256):
            with self.subTest(value=value),self.assertRaises(ar.RouteError):self.reader.quote_usdg_to_weth(value)
        with self.assertRaises(ar.RouteError):self.reader.quote_usdg_to_weth(99_000_000)
        for bps in (-1,101,True):
            with self.assertRaises(ar.RouteError):self.reader.quote_usdg_to_weth(100_000_000,bps)

    def test_unsupported_inputs_and_no_zzz_price_do_not_invent_price_or_route(self):
        for symbol in ('USDT','usdg','FAKE'):
            with self.assertRaises(ar.RouteError):self.reader.verify_asset(symbol)
        self.assertEqual(self.reader.verify_asset('ZZZ')['token'],ar.ZZZ)
        with self.assertRaisesRegex(ar.RouteError,'No independently verified'):self.reader.price_usd_18('ZZZ')

    def test_canonical_usdc_is_identified_but_route_stays_disabled(self):
        status=self.reader.usdc_route_status()
        self.assertEqual(status['token'],ar.USDC);self.assertEqual(status['decimals'],6)
        self.assertIn('not Circle-native',status['provenance'])
        self.assertFalse(status['route_enabled']);self.assertFalse(status['activation_ready'])

    def test_usdc_bridge_mapping_mismatch_rejected(self):
        self.rpc.replies[ar.USDC,calldata('l1Address()')]=addr(ar.USDG)
        with self.assertRaisesRegex(ar.RouteError,'provenance'):self.reader.verify_asset('USDC')

    def test_usdc_beacon_implementation_or_authority_change_rejected(self):
        for signature in ('implementation()','owner()'):
            key=ar.USDC_BEACON,calldata(signature);original=self.rpc.replies[key]
            self.rpc.replies[key]=addr(ar.USDG)
            with self.assertRaises(ar.RouteError):self.reader.verify_asset('USDC')
            self.rpc.replies[key]=original

    def test_usdg_proxy_upgrade_and_admin_change_fail_closed(self):
        key=ar.USDG,ar._slot('implementation');original=self.rpc.storage[key]
        self.rpc.storage[key]=addr(ar.USDC_IMPLEMENTATION)
        with self.assertRaisesRegex(ar.RouteError,'implementation'):self.reader.verify_asset('USDG')
        self.rpc.storage[key]=original;self.rpc.replies[ar.USDG,calldata('owner()')]=addr(ar.USDC)
        with self.assertRaisesRegex(ar.RouteError,'authority'):self.reader.verify_asset('USDG')

    def test_paused_or_wrong_decimal_stable_rejected(self):
        self.rpc._set(ar.USDG,'paused()',1)
        with self.assertRaisesRegex(ar.RouteError,'paused'):self.reader.verify_asset('USDG')
        self.rpc._set(ar.USDG,'paused()',0);self.rpc._set(ar.USDG,'decimals()',18)
        with self.assertRaisesRegex(ar.RouteError,'decimals'):self.reader.verify_asset('USDG')

    def test_pinned_code_change_rejected(self):
        self.rpc.code[ar.QUOTER]='0x6000'
        with self.assertRaisesRegex(ar.RouteError,'Runtime code'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_reorg_and_wrong_chain_rejected(self):
        self.rpc.block_hash='0x'+'cd'*32
        with self.assertRaisesRegex(ar.RouteError,'block changed'):self.reader.verify_asset('USDG')
        self.rpc.chain_id=1
        with self.assertRaisesRegex(ar.RouteError,'Wrong chain'):ar.ActivationRouteReader(self.rpc,self.rpc.snapshot)

    def test_feed_stale_negative_future_or_incomplete_round_rejected(self):
        key=ar.FEEDS['ETH'],calldata('latestRoundData()')
        for round_values in [(8,1,100000,100001,8),(8,2**256-1,199000,199001,8),
            (8,1,199000,200001,8),(8,1,199000,199001,7),(0,1,199000,199001,0),(8,1,199005,199000,8)]:
            self.rpc.replies[key]=words(*round_values)
            with self.subTest(values=round_values),self.assertRaises(ar.RouteError):self.reader.price_usd_18('ETH')

    def test_pool_factory_tokens_and_mappings_must_match_reviewed_route(self):
        pool=ar.USDG_POOLS[100];self.rpc.replies[pool,calldata('token1()')]=addr(ar.USDC)
        with self.assertRaisesRegex(ar.RouteError,'Pool identity'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_router_cannot_redirect_to_other_factory(self):
        self.rpc.replies[ar.SWAP_ROUTER,calldata('factory()')]=addr(ar.USDC)
        with self.assertRaisesRegex(ar.RouteError,'binding'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_zero_liquidity_no_routes_and_unfunded_quote_rejected(self):
        for pool in ar.USDG_POOLS.values():self.rpc._set(pool,'liquidity()',0)
        with self.assertRaisesRegex(ar.RouteError,'No funded'):self.reader.quote_usdg_to_weth(100_000_000)
        pool=ar.USDG_POOLS[100];self.rpc._set(pool,'liquidity()',1)
        self.rpc.replies[ar.WETH,calldata('balanceOf(address)',pool)]=words(1)
        with self.assertRaisesRegex(ar.RouteError,'Unfunded'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_excessive_total_execution_budget_rejected(self):
        self.rpc.replies[ar.FEEDS['ETH'],calldata('latestRoundData()')]=words(8,2400*10**8,199000,199005,8)
        with self.assertRaisesRegex(ar.RouteError,'1% execution budget'):self.reader.quote_usdg_to_weth(100_000_000)

    def test_native_wrap_is_unsigned_owner_controlled_without_approval_or_activation(self):
        owner='0x'+'11'*20;step=self.reader.eth_wrap_step(owner,4*10**16)
        self.assertEqual(step['from'],owner);self.assertEqual(step['to'],ar.WETH)
        self.assertEqual(step['value'],hex(4*10**16));self.assertEqual(step['data'],calldata('deposit()'))
        self.assertFalse(step['activation_ready']);self.assertFalse(step['gas_included_in_execution_loss'])
        with self.assertRaises(ValueError):self.reader.eth_wrap_step('0x'+'00'*20,4*10**16)

    def test_weth_upgrade_or_wrong_canonical_gateway_rejected(self):
        self.rpc.storage[ar.WETH,ar._slot('implementation')]=addr(ar.USDC_IMPLEMENTATION)
        with self.assertRaisesRegex(ar.RouteError,'WETH implementation'):self.reader.eth_wrap_step('0x'+'11'*20,4*10**16)

    def test_capture_snapshot_requires_confirmations_and_pins_hash(self):
        snapshot=ar.capture_snapshot(self.rpc)
        self.assertEqual(snapshot,self.rpc.snapshot)
        with self.assertRaises(ar.RouteError):ar.capture_snapshot(self.rpc,0)
        self.assertTrue(all(method in {'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getCode','eth_getStorageAt','eth_call'} for method,_ in self.rpc.calls))

    def test_cli_produces_read_only_disabled_usdc_status(self):
        output=io.StringIO()
        with patch.dict('os.environ',{'ACTIVATION_RPC_URL':'https://example.invalid'}),patch('zzz_ops.rpc.Rpc',return_value=self.rpc),contextlib.redirect_stdout(output):
            self.assertEqual(ar.main(['--symbol','USDC']),0)
        result=json.loads(output.getvalue());self.assertEqual(result['token'],ar.USDC)
        self.assertFalse(result['activation_ready']);self.assertFalse(result['route_enabled'])

    def test_cli_rejects_invalid_raw_amount_before_network(self):
        for amount in ('1.5','-1','0','1e8','0x64'):
            with patch.dict('os.environ',{'ACTIVATION_RPC_URL':'https://example.invalid'}),patch('zzz_ops.rpc.Rpc') as client,contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:ar.main(['--symbol','USDG','--amount',amount])
                self.assertEqual(exc.exception.code,1);client.assert_not_called()

if __name__=='__main__':unittest.main()
