"""Opt-in bounded royalty conversion, using the keeper's existing serial sender.

Reads use one confirmed canonical hash. The ledger recomputes earned balances,
and the converter enforces the oracle floor at execution. No signer lives here.
"""
from __future__ import annotations
import re
from zzz_ops.abi import address, calldata, decode_words, keccak256, word
from zzz_ops.rpc import RpcError
from zzz_ops.state import integer

BATCH = 'convertBatch(address,uint256[],bytes32,uint256,uint256)'
ZERO = '0x' + '00'*32
NATIVE = '0x' + '00'*20

def number(value, name, maximum=None):
    value = integer(value, name, minimum=1)
    if maximum is not None and value > maximum: raise ValueError('Royalty setting exceeds bound: '+name)
    return value

def native_quote(asset, amount):
    # Native identity is allowed only in this typed output slot. The shared
    # generic address codec intentionally continues to reject zero addresses.
    signature='quote(address,address,uint256)'
    return '0x'+keccak256(signature.encode()).hex()[:8]+word(asset,'address')+word(0,'uint256')+word(amount,'uint256')

def encode_batch(asset, ids, route, minimum, deadline):
    if not isinstance(ids,(list,tuple)) or not 1 <= len(ids) <= 32:
        raise ValueError('Royalty batch must contain 1-32 NFTs')
    if any(type(n) is not int or n < 0 or n >= 1 << 256 for n in ids) or list(ids) != sorted(set(ids)):
        raise ValueError('Royalty NFT IDs must be sorted and unique')
    return ('0x'+keccak256(BATCH.encode()).hex()[:8]+word(asset,'address')+word(160,'uint256')+
        word(route,'bytes32')+word(number(minimum,'minimum'),'uint256')+word(number(deadline,'deadline'),'uint256')+
        word(len(ids),'uint256')+''.join(word(n,'uint256') for n in ids))

class RoyaltyAutomation:
    def __init__(self, keeper, *, lp=False):
        self.k = keeper
        self.lp = lp
        self.key = 'lp_conversion' if lp else 'royalty_conversion'
        self.ledger = 'rewards' if lp else 'royalties'
        self.converter = 'lp_converter' if lp else 'royalty_converter'
        self.nft = 'lp_nft' if lp else 'royalty_nft'
        self.wrapper = 'lp_wrapper' if lp else 'royalty_wrapper'
        self.executor = 'lp_v4_executor' if lp else 'royalty_v4_executor'
        cfg = keeper.config.get(self.key,{})
        if not isinstance(cfg,dict) or type(cfg.get('enabled',False)) is not bool:
            raise ValueError('royalty_conversion requires an explicit enabled boolean')
        self.enabled = cfg.get('enabled',False)
        if not self.enabled: return
        self.profile = cfg.get('profile','v3_wrapper')
        if self.profile not in ('v3_wrapper','v3_wrapper_configurable','v4_native'):
            raise ValueError('Unsupported royalty conversion profile')
        self.native_v4 = self.profile == 'v4_native'
        self.configurable_loss = self.profile != 'v3_wrapper'
        self.names = (self.ledger,self.converter,self.nft,'oracle',self.executor if self.native_v4 else self.wrapper)
        self.scan = number(cfg.get('max_nfts_per_cycle',32),'max_nfts_per_cycle',32)
        self.gas_bps = number(cfg.get('max_gas_to_output_bps',100),'max_gas_to_output_bps',10000)
        self.routes = cfg.get('assets')
        if not isinstance(self.routes,list) or not 1 <= len(self.routes) <= 16: raise ValueError('Royalty assets require 1-16 entries')
        self.routes = [dict(p) for p in self.routes]
        seen=set()
        for p in self.routes:
            p['asset']=address(p['asset'])
            if p['asset'] in seen: raise ValueError('Duplicate royalty currency')
            seen.add(p['asset'])
            if not re.fullmatch(r'0x[0-9a-fA-F]{64}',p.get('route_id','')): raise ValueError('Malformed royalty route')
            p['route_id']=p['route_id'].lower()
            if self.native_v4 and (p['asset'] == NATIVE or p['route_id'] == ZERO):
                raise ValueError('Native v4 conversion requires an ERC20 source and explicit route')
            p['minimum_source_units']=number(p['minimum_source_units'],'minimum_source_units')
            p['minimum_output_wei']=number(p['minimum_output_wei'],'minimum_output_wei')
        for name in self.names:
            if name not in keeper.contracts: raise ValueError('Missing royalty contract: '+name)
            if not re.fullmatch(r'0x[0-9a-fA-F]{64}',keeper.config.get('code_hashes',{}).get(name,'')):
                raise ValueError('Missing royalty runtime pin: '+name)
        identity={'ledger':keeper.contracts[self.ledger],'nft':keeper.contracts[self.nft],
            'assets':[p['asset'] for p in self.routes]}
        if self.configurable_loss:
            # Old wrapper jobs/journals must not silently adopt new route semantics.
            identity.update(profile=self.profile)
            if self.native_v4: identity.update(executor=keeper.contracts[self.executor])
        state=keeper.state.get(self.key)
        if state is None:
            keeper.state[self.key]={'identity':identity,'asset':0,'ordinal':1,'next_first':True}
        else:
            if not isinstance(state,dict) or state.get('identity') != identity: raise ValueError('Royalty scan identity changed; reconcile state')
            integer(state.get('asset'),'asset cursor',minimum=0)
            if state['asset'] >= len(self.routes): raise ValueError('Invalid royalty asset cursor')
            number(state.get('ordinal'),'ordinal',1000)
            if type(state.get('next_first')) is not bool: raise ValueError('Invalid royalty scheduling state')

    def scan_once(self):
        k=self.k; state=k.state[self.key]; contracts=k.contracts
        latest=k.rpc.call('eth_getBlockByNumber',['latest',False])
        if not isinstance(latest,dict) or not re.fullmatch(r'0x[0-9a-fA-F]+',latest.get('number','')): raise RpcError('Invalid royalty head')
        block=int(latest['number'],16)-k.confirmations
        if block < 0: raise RpcError('Insufficient royalty confirmations')
        header=k.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if not isinstance(header,dict) or header.get('number') != hex(block) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',header.get('hash','')):
            raise RpcError('Invalid royalty anchor')
        selector={'blockHash':header['hash'],'requireCanonical':True}
        def read(name,sig,*args):
            data=native_quote(args[0],args[2]) if self.native_v4 and sig=='quote(address,address,uint256)' and args[1]==NATIVE else calldata(sig,*args)
            words=decode_words(k.rpc.call('eth_call',[{'to':contracts[name],'data':data},selector]))
            if len(words)!=1: raise RpcError('Unexpected royalty getter ABI')
            return int(words[0],16)
        def enabled(name, sig, *args):
            # A malformed core bool is an observation failure, not governance's
            # legitimate off switch. Preserve outer deferred/degraded telemetry.
            value = read(name, sig, *args)
            if value not in (0, 1): raise RpcError('Noncanonical conversion boolean')
            return value == 1
        checks=[(self.ledger,'access()' if self.lp else 'canonicalController()',contracts['access']),
            (self.ledger,'converter()',contracts[self.converter]),(self.converter,'ledger()',contracts[self.ledger]),
            (self.converter,'access()',contracts['access']),
            (self.nft,'access()',contracts['access'])]
        if self.native_v4:
            checks += [(self.converter,'v4Executor()',contracts[self.executor]),
                (self.executor,'parent()',contracts[self.converter])]
        else: checks += [(self.converter,'wrapper()',contracts[self.wrapper])]
        if not self.lp:
            checks += [(self.ledger,'nft()',contracts[self.nft]),(self.nft,'royaltyRewards()',contracts[self.ledger])]
        for name,sig,expected in checks:
            if read(name,sig)!=int(expected,16): raise RpcError('Royalty binding mismatch')
        for name in self.names:
            code=k.rpc.call('eth_getCode',[contracts[name],selector])
            if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                '0x'+keccak256(bytes.fromhex(code[2:])).hex()!=k.config['code_hashes'][name].lower():
                raise RpcError('Royalty code pin mismatch')
        for key,name in [('ZZZNFT',self.nft),('ZZZOracle','oracle')] + ([('ZZZRewards',self.ledger)] if self.lp else []):
            if read('access','module(bytes32)','0x'+keccak256(key.encode()).hex())!=int(contracts[name],16): raise RpcError('Royalty module mismatch')
        ceiling=read(self.converter,'MAX_LOSS_BPS()')
        loss=read(self.converter,'conversionLossBps()') if self.configurable_loss else 100
        if read(self.ledger,'MAX_CONVERSION_NFTS()')!=32 or ceiling!=(1000 if self.configurable_loss else 100) or not 0<=loss<=ceiling:
            raise RpcError('Royalty protocol limit mismatch')
        if not enabled(self.converter,'enabled()'): return False
        count=read(self.nft,'mintedCount()')
        if count>1000: raise RpcError('Invalid royalty inventory')
        if count==0: return False
        first=min(state['ordinal'],count); last=min(first+self.scan-1,count)
        policy=self.routes[state['asset']]
        # Progress even when one currency is unreadable; the outer serial worker
        # logs that failure and keeps other maintenance available on later cycles.
        state['asset']=(state['asset']+1)%len(self.routes)
        if state['asset']==0: state['ordinal']=1 if last==count else last+1
        k.save()
        asset=policy['asset'];route=policy['route_id']
        if read(self.ledger,'isAsset(address)',asset)!=1: raise RpcError('Royalty currency is not admitted')
        unwrap = not self.native_v4 and asset == contracts[self.wrapper]
        if self.native_v4:
            if read(self.converter,'routeKind(bytes32)',route)!=2: raise RpcError('Royalty route kind mismatch')
            if not enabled(self.converter,'routeEnabled(bytes32)',route): return False
            values=decode_words(k.rpc.call('eth_call',[{'to':contracts[self.converter],
                'data':calldata('v4Route(bytes32)',route)},selector]))
            # The fixed helper's validate checks key, static hookless venue,
            # initialization and every runtime pin at this same confirmed block.
            checked=decode_words(k.rpc.call('eth_call',[{'to':contracts[self.executor],
                'data':calldata('validate(bytes32)',route)},selector]))
            if len(values)!=14 or values!=checked or int(values[0],16)!=int(asset,16) or int(values[1],16)!=0:
                raise RpcError('Royalty native v4 policy mismatch')
        elif not unwrap:
            if not enabled(self.converter,'routeEnabled(bytes32)',route): return False
            values=decode_words(k.rpc.call('eth_call',[{'to':contracts[self.converter],'data':calldata('route(bytes32)',route)},selector]))
            if len(values)!=10 or int(values[0],16)!=int(asset,16): raise RpcError('Royalty route currency mismatch')
        elif route!=ZERO: raise RpcError('WETH unwrapping must not select a swap route')
        ids=[];total=0
        for ordinal in range(first,last+1):
            token=read(self.nft,'tokenAtOrdinal(uint256)',ordinal)
            if not self.lp and read(self.ledger,'weightOf(uint256)',token)==0: continue
            amount=read(self.ledger,'claimable(uint256,address)',token,asset)
            if amount: ids.append(token);total+=amount
        if len(ids)!=len(set(ids)): raise RpcError('Duplicate royalty token inventory')
        # A successful balance read can recover the waiting cohort even if no
        # currently payable whole units exist. sync never swaps or pays anyone.
        recover=not self.lp and read(self.ledger,'eligibleCount(address)',asset)<read(self.ledger,'activationCount()')
        _,now=k._head()
        if now-int(header['timestamp'],16)>300: raise RpcError('Stale royalty snapshot')
        if k.rpc.call('eth_getBlockByNumber',[hex(block),False])!=header: raise RpcError('Royalty anchor changed')
        if total<policy['minimum_source_units']:
            if recover: return k.submit(self.ledger,'sync(address)',(asset,),f'royalty_sync:{asset}')
            return False
        quote_output=NATIVE if self.native_v4 else contracts[self.wrapper]
        expected=total if unwrap else read('oracle','quote(address,address,uint256)',asset,quote_output,total)
        if expected<policy['minimum_output_wei']: return False
        minimum=expected if unwrap else (expected*(10000-loss)+9999)//10000
        # Recheck after the last price read; the contract repeats its own floor.
        if k.rpc.call('eth_getBlockByNumber',[hex(block),False])!=header: raise RpcError('Royalty anchor changed')
        return k.submit(self.ledger,BATCH,(asset,sorted(ids),route,minimum,now+180),
            f'{self.key}:{asset}:{first}:{last}',maximum_cost=minimum*self.gas_bps//10000)
