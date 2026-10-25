"""Read-only Robinhood input provenance and route-quote groundwork.

Never signs, submits, approves or builds an activate-on-behalf call. A stable
conversion quote is not an end-to-end LP guarantee: the current owner-only Vault
cannot authenticate an earlier stable input amount from received pair assets.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .abi import address, calldata, decode_words, keccak256, uint_result, word

CHAIN_ID = 4663
WETH = '0x0bd7d308f8e1639fab988df18a8011f41eacad73'
WETH_IMPLEMENTATION = '0xc6b81b429797e0f555440b70cd99e032d7ae947e'
L1_WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
L2_WETH_GATEWAY = '0x1d187c3e2da52d72bc9c41e3aba0fdfa6a7bf055'
ZZZ = '0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
USDC = '0x80e0e24718dbfcad49ecaa6f1e6c89a190586ca8'
USDG = '0x5fc5360d0400a0fd4f2af552add042d716f1d168'
L1_USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
L2_ROUTER = '0x1e324b9316138ca9a73f960213621ad1aaf01b89'
L2_GATEWAY = '0xfd9b17206278c16ddaacf6ac8f05dbf97edcb31e'
USDC_BEACON = '0x883d9f54f50c9d096b6b3823532fdc8fd8dfa293'
USDC_IMPLEMENTATION = '0xef3b461697c6bd38c5458afa31e1250c98fd0f5f'
USDC_BEACON_OWNER = '0x2a153c6a1b66dbc930a8d7017230ab0253005c09'
USDG_IMPLEMENTATION = '0x68184c449e1a8f34fa18d289737129fd27b66f8f'
USDG_ADMIN = '0xcfa0388f5ddf905fdc08c45c716c15dc10a14c6f'
FACTORY = '0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
QUOTER = '0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
SWAP_ROUTER = '0xcaf681a66d020601342297493863e78c959e5cb2'
FEEDS = {
    'ETH': '0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9',
    'USDG': '0x61b7e5650328764b076a108eff5fa7282a1b9ad2',
    'USDC': '0x9e6f4605992a899ee2999999f3ec80c41f452546',
}
# Reviewed address/code observations at block 89,527,712 on 2026-10-15.
# Changes fail closed and require fresh provenance/security review.
CODE_HASHES = {
    WETH: '0x5706be52f64875fee65a2cec0d80e47a23d8793cbe85d214b48445e2d05f5353',
    WETH_IMPLEMENTATION: '0xbe1295f37be34ffe03ad779bda0ef278907e1856b51a3be2f35ee541d75d4650',
    L2_ROUTER: '0x5706be52f64875fee65a2cec0d80e47a23d8793cbe85d214b48445e2d05f5353',
    ZZZ: '0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597',
    USDC: '0x487e3e7ba0f6ef76ccd39c373954f0edcdfe15c8817bdca4ef73f6df3963e694',
    USDG: '0x864cc9ad53b338b82da1f7cab85ab0b3d5c8861acb422b6fec63cf36234f36a6',
    USDC_BEACON: '0xc56839de3666971ce2ca986d3b5b7e43baf1049b79e51d5180bad2ff542afc3c',
    USDC_IMPLEMENTATION: '0x48945cb32b27f60c389cef706cccb74daef5c61d197257a159ddf61f586c0c15',
    USDG_IMPLEMENTATION: '0x3a551ac5c744af57e68a1d1431ac403c0f516ffd7d224a75746aee11fc4f3baf',
    FACTORY: '0xec72b1abd1f2faee020cfea9c646bd8994f9fb389054f6e574f103a895091739',
    QUOTER: '0x3db0868d945e9304c9bc6a8b2181948109ea617647142f3c4083e14393496a28',
    SWAP_ROUTER: '0x6f36c378e272c6324c48f045182bcb54bd8ad654cf9ebd42e8893d52c4cb25dc',
    **{feed: '0xbd6f524cdc4268b6bd1bb6f77a8821faeea9c52ee9e0afa0b6d948ce82c966c2' for feed in FEEDS.values()},
}
USDG_POOLS = {
    100: '0x52e65b17fb6e5ba00ed806f37afcd2daa50271ca',
    500: '0x69bfaf19c9f377bb306a89aed9f6b07e2c1a8d9a',
    3000: '0xa9188730fe85be88ad499d7d52b099e800fb0334',
    10000: '0x5f009e071f07e92b6c624e83f52f17bbda34680d',
}
class RouteError(ValueError): pass

def _integer(value: int, minimum: int = 0, maximum: int = (1 << 256) - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum: raise RouteError('Invalid bounded integer')
    return value

def _address_result(result: str) -> str:
    n = uint_result(result)
    if n >= 1 << 160: raise RouteError('Noncanonical address return')
    return '0x' + f'{n:040x}'

def _slot(name: str) -> str:
    return hex(int.from_bytes(keccak256(('eip1967.proxy.' + name).encode()), 'big') - 1)

def _tuple_call(signature: str, values: list[tuple[int | str, str]]) -> str:
    return '0x' + keccak256(signature.encode()).hex()[:8] + ''.join(word(v,t) for v,t in values)

@dataclass(frozen=True)
class Snapshot:
    number: int
    block_hash: str
    timestamp: int
    def __post_init__(self):
        _integer(self.number, 1); _integer(self.timestamp, 1)
        if not re.fullmatch(r'0x[0-9a-f]{64}', self.block_hash): raise RouteError('Invalid block hash')
    @property
    def tag(self) -> str: return hex(self.number)

def capture_snapshot(rpc, confirmations: int = 12) -> Snapshot:
    if rpc.chain_id != CHAIN_ID or rpc.call('eth_chainId') != CHAIN_ID: raise RouteError('Wrong chain')
    _integer(confirmations, 1, 1000)
    number = int(rpc.call('eth_blockNumber'),16) - confirmations
    block = rpc.call('eth_getBlockByNumber',[hex(number),False])
    if not isinstance(block,dict) or int(block['number'],16) != number: raise RouteError('Missing pinned block')
    return Snapshot(number,block['hash'].lower(),int(block['timestamp'],16))

class ActivationRouteReader:
    def __init__(self, rpc, snapshot: Snapshot):
        if rpc.chain_id != CHAIN_ID or rpc.call('eth_chainId') != CHAIN_ID: raise RouteError('Wrong chain')
        self.rpc, self.snapshot = rpc, snapshot
        self._check_block()

    def _check_block(self):
        block = self.rpc.call('eth_getBlockByNumber',[self.snapshot.tag,False])
        if (not isinstance(block,dict) or block.get('hash') != self.snapshot.block_hash or
            int(block.get('number','0x0'),16) != self.snapshot.number or
            int(block.get('timestamp','0x0'),16) != self.snapshot.timestamp): raise RouteError('Pinned block changed')

    def _call(self, target: str, signature: str, *args):
        return self.rpc.eth_call(target,calldata(signature,*args),block=self.snapshot.tag)

    def _uint(self, target: str, signature: str, *args) -> int:
        return uint_result(self._call(target,signature,*args))

    def _address(self, target: str, signature: str, *args) -> str:
        return _address_result(self._call(target,signature,*args))

    def _code(self, target: str, *, pinned: bool = True) -> str:
        raw = self.rpc.call('eth_getCode',[target,self.snapshot.tag])
        if not isinstance(raw,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',raw): raise RouteError('Missing runtime code')
        digest = '0x' + keccak256(bytes.fromhex(raw[2:])).hex()
        if pinned and CODE_HASHES.get(target) != digest: raise RouteError('Runtime code changed or unreviewed')
        return digest

    def _storage_address(self, target: str, name: str) -> str:
        return _address_result(self.rpc.call('eth_getStorageAt',[target,_slot(name),self.snapshot.tag]))

    def verify_asset(self, symbol: str) -> dict:
        if symbol not in ('USDC','USDG','ETH','ZZZ'): raise RouteError('Unsupported input; ticker is not provenance')
        token = {'USDC':USDC,'USDG':USDG,'ETH':WETH,'ZZZ':ZZZ}[symbol]
        self._code(token)
        decimals = 6 if symbol in ('USDC','USDG') else 18
        if self._uint(token,'decimals()') != decimals: raise RouteError('Unexpected token decimals')
        result = {'symbol':symbol,'token':token,'decimals':decimals}
        if symbol == 'USDC':
            self._code(L2_ROUTER)
            if self._storage_address(token,'beacon') != USDC_BEACON: raise RouteError('USDC beacon changed')
            self._code(USDC_BEACON); self._code(USDC_IMPLEMENTATION)
            if self._address(USDC_BEACON,'implementation()') != USDC_IMPLEMENTATION: raise RouteError('USDC implementation changed')
            if self._address(USDC_BEACON,'owner()') != USDC_BEACON_OWNER: raise RouteError('USDC beacon authority changed')
            if (self._address(token,'l1Address()') != L1_USDC or self._address(token,'l2Gateway()') != L2_GATEWAY or
                self._address(L2_ROUTER,'calculateL2TokenAddress(address)',L1_USDC) != token or
                self._address(L2_ROUTER,'getGateway(address)',L1_USDC) != L2_GATEWAY): raise RouteError('USDC bridge provenance mismatch')
            result.update(provenance='canonical Ethereum-bridged USDC; not Circle-native on Robinhood',l1_token=L1_USDC)
        elif symbol == 'USDG':
            if self._storage_address(token,'implementation') != USDG_IMPLEMENTATION: raise RouteError('USDG implementation changed')
            self._code(USDG_IMPLEMENTATION)
            if self._address(token,'owner()') != USDG_ADMIN or self._address(token,'defaultAdmin()') != USDG_ADMIN:
                raise RouteError('USDG authority changed')
            if self._uint(token,'paused()') != 0: raise RouteError('USDG paused')
            result['provenance'] = 'Paxos/Robinhood official native USDG address'
        elif symbol == 'ETH':
            if self._storage_address(WETH,'implementation') != WETH_IMPLEMENTATION: raise RouteError('WETH implementation changed')
            self._code(WETH_IMPLEMENTATION)
            if self._address(WETH,'l1Address()') != L1_WETH or self._address(WETH,'l2Gateway()') != L2_WETH_GATEWAY:
                raise RouteError('WETH canonical identity changed')
        self._check_block()
        return result

    def price_usd_18(self, symbol: str) -> int:
        if symbol not in FEEDS: raise RouteError('No independently verified feed; do not infer a peg or ZZZ price')
        feed = FEEDS[symbol]; self._code(feed)
        if self._uint(feed,'decimals()') != 8: raise RouteError('Unexpected feed decimals')
        words = decode_words(self._call(feed,'latestRoundData()'))
        if len(words) != 5: raise RouteError('Invalid price round')
        round_id,answer,started,updated,answered = [int(w,16) for w in words]
        if (round_id == 0 or answer == 0 or answer >= 1 << 255 or answered < round_id or
            not 0 < started <= updated <= self.snapshot.timestamp or self.snapshot.timestamp-updated > 86400):
            raise RouteError('Stale, incomplete, future or invalid price round')
        self._check_block()
        return answer * 10**10

    def quote_usdg_to_weth(self, amount_in: int, slippage_bps: int = 20) -> dict:
        """Quote the conversion leg only; never marks activation ready."""
        _integer(amount_in,1); _integer(slippage_bps,0,100)
        self.verify_asset('USDG'); self.verify_asset('ETH')
        for target in (FACTORY,QUOTER,SWAP_ROUTER): self._code(target)
        for target in (QUOTER,SWAP_ROUTER):
            if self._address(target,'factory()') != FACTORY or self._address(target,'WETH9()') != WETH:
                raise RouteError('Router/quoter binding changed')
        gross = amount_in * self.price_usd_18('USDG') // 10**6
        if gross < 100 * 10**18: raise RouteError('Source input below $100 at the independent price')
        eth_price = self.price_usd_18('ETH'); routes = []
        for fee,pool in USDG_POOLS.items():
            if self._address(FACTORY,'getPool(address,address,uint24)',USDG,WETH,fee) != pool:
                raise RouteError('Reviewed pool mapping changed')
            code_hash = self._code(pool,pinned=False)
            if (self._address(pool,'factory()') != FACTORY or self._address(pool,'token0()') != WETH or
                self._address(pool,'token1()') != USDG or self._uint(pool,'fee()') != fee): raise RouteError('Pool identity mismatch')
            if self._uint(pool,'liquidity()') == 0: continue
            slot = decode_words(self._call(pool,'slot0()'))
            if len(slot) != 7 or int(slot[0],16) == 0 or int(slot[6],16) != 1: raise RouteError('Invalid pool state')
            data = _tuple_call('quoteExactInputSingle((address,address,uint256,uint24,uint160))',
                [(USDG,'address'),(WETH,'address'),(amount_in,'uint256'),(fee,'uint24'),(0,'uint160')])
            values = decode_words(self.rpc.eth_call(QUOTER,data,block=self.snapshot.tag))
            if len(values) != 4: raise RouteError('Malformed quoter response')
            amount_out = int(values[0],16)
            if amount_out == 0 or amount_out > self._uint(WETH,'balanceOf(address)',pool): raise RouteError('Unfunded route quote')
            routes.append({'fee':fee,'pool':pool,'pool_runtime_keccak':code_hash,'amount_out':amount_out,
                'quote_gas_estimate':int(values[3],16)})
        if not routes: raise RouteError('No funded reviewed USDG route')
        best = max(routes,key=lambda r:r['amount_out'])
        minimum_out = best['amount_out'] * (10000-slippage_bps) // 10000
        minimum_usd = minimum_out * eth_price // 10**18
        required_lp = (gross * 9900 + 9999) // 10000
        if minimum_usd < required_lp: raise RouteError('Conversion floor consumes more than total 1% execution budget')
        remaining_bps = (minimum_usd-required_lp)*10000//minimum_usd
        self._check_block()
        return {'chain_id':CHAIN_ID,'block_number':self.snapshot.number,'block_hash':self.snapshot.block_hash,
            'block_timestamp':self.snapshot.timestamp,'input_asset':USDG,'input_amount':amount_in,'input_usd_18':gross,
            'output_asset':WETH,**best,'minimum_output':minimum_out,'minimum_output_usd_18':minimum_usd,
            'required_final_lp_usd_18':required_lp,'remaining_lp_leg_loss_bps':remaining_bps,
            'slippage_bps':slippage_bps,'gas_included_in_execution_loss':False,'activation_ready':False,
            'scope':'conversion-leg quote only; not an LP valuation, end-to-end guarantee or signable activation',
            'release_gates':['reviewed atomic original-input accounting','reviewed ZZZ valuation and outage policy',
                'same-owner exact activation simulation and measured LP','fresh gas estimation and wallet approval']}

    def minimum_input_amount(self, symbol: str) -> int:
        identity = self.verify_asset(symbol)
        price = self.price_usd_18(symbol)
        numerator = 100 * 10**18 * 10**identity['decimals']
        return (numerator + price - 1) // price

    def eth_wrap_step(self, owner: str, amount: int) -> dict:
        """Unsigned wrap only. WETH is held by the calling owner, not a zapper."""
        owner = address(owner); _integer(amount,1); self.verify_asset('ETH')
        gross = amount * self.price_usd_18('ETH') // 10**18
        if gross < 100 * 10**18: raise RouteError('Source input below $100 at the independent price')
        return {'chainId':CHAIN_ID,'from':owner,'to':WETH,'value':hex(amount),'data':calldata('deposit()'),
            'input_usd_18':gross,'gas_included_in_execution_loss':False,'activation_ready':False,
            'scope':'unsigned wrap step only; no approval, swap or activation; owner must review and re-simulate'}

    def usdc_route_status(self) -> dict:
        identity = self.verify_asset('USDC')
        # No arbitrary token substitution, unreviewed aggregator or new pool is
        # automatically admitted when a token is identified.
        return {**identity,'route_enabled':False,'activation_ready':False,
            'reason':'No reviewed funded USDC route; canonical identity does not establish swap liquidity'}

def main(argv=None) -> int:
    import argparse
    import json
    import os
    from pathlib import Path
    from .rpc import Rpc, RpcError
    parser = argparse.ArgumentParser(description='Read-only activation input/route preflight; never signs or submits')
    parser.add_argument('--rpc-env',default='ACTIVATION_RPC_URL',help='Environment variable containing the HTTPS RPC URL')
    parser.add_argument('--symbol',required=True,choices=['USDC','USDG','ETH','ZZZ'])
    parser.add_argument('--amount',help='Exact raw token/native units; omitted means the current $100 minimum where a feed exists')
    parser.add_argument('--owner',help='Current owner/caller address for the unsigned ETH wrap step')
    parser.add_argument('--confirmations',type=int,default=12)
    parser.add_argument('--slippage-bps',type=int,default=20)
    parser.add_argument('--output',type=Path,help='Optional JSON evidence output, never a key or signed transaction')
    args = parser.parse_args(argv)
    try:
        url = os.environ.get(args.rpc_env)
        if not url: raise RouteError('Set the selected RPC environment variable first')
        amount = None
        if args.amount is not None:
            if not re.fullmatch(r'[0-9]{1,78}',args.amount): raise RouteError('Amount must be positive raw integer units')
            amount = _integer(int(args.amount),1)
        if args.symbol == 'ETH' and not args.owner: raise RouteError('ETH wrapping requires the current owner address')
        if args.owner: address(args.owner)
        rpc = Rpc([url],CHAIN_ID)
        reader = ActivationRouteReader(rpc,capture_snapshot(rpc,args.confirmations))
        if args.symbol == 'USDG':
            result = reader.quote_usdg_to_weth(amount or reader.minimum_input_amount('USDG'),args.slippage_bps)
        elif args.symbol == 'USDC': result = reader.usdc_route_status()
        elif args.symbol == 'ETH': result = reader.eth_wrap_step(args.owner,amount or reader.minimum_input_amount('ETH'))
        else: result = {**reader.verify_asset('ZZZ'),'activation_ready':False,'reason':'Reviewed ZZZ valuation/final LP simulation required'}
        rendered = json.dumps(result,indent=2)+'\n'
        if args.output: args.output.write_text(rendered,encoding='utf-8')
        print(rendered,end='')
        return 0
    except (ValueError,RpcError,OSError) as exc:
        # The RPC client redacts transport URLs/credentials from its own error.
        parser.exit(1,f'Preflight failed closed: {type(exc).__name__}: {exc}\n')

if __name__ == '__main__': raise SystemExit(main())
