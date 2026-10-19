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

def number(value, name, maximum=None):
    value = integer(value, name, minimum=1)
    if maximum is not None and value > maximum: raise ValueError('Royalty setting exceeds bound: '+name)
    return value

def encode_batch(asset, ids, route, minimum, deadline):
    if not isinstance(ids,(list,tuple)) or not 1 <= len(ids) <= 32:
        raise ValueError('Royalty batch must contain 1-32 NFTs')
    if any(type(n) is not int or n < 0 or n >= 1 << 256 for n in ids) or list(ids) != sorted(set(ids)):
        raise ValueError('Royalty NFT IDs must be sorted and unique')
    return ('0x'+keccak256(BATCH.encode()).hex()[:8]+word(asset,'address')+word(160,'uint256')+
        word(route,'bytes32')+word(number(minimum,'minimum'),'uint256')+word(number(deadline,'deadline'),'uint256')+
        word(len(ids),'uint256')+''.join(word(n,'uint256') for n in ids))

class RoyaltyAutomation:
    def __init__(self, keeper):
        self.k = keeper
        cfg = keeper.config.get('royalty_conversion',{})
        if not isinstance(cfg,dict) or type(cfg.get('enabled',False)) is not bool:
            raise ValueError('royalty_conversion requires an explicit enabled boolean')
        self.enabled = cfg.get('enabled',False)
        if not self.enabled: return
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
            p['minimum_source_units']=number(p['minimum_source_units'],'minimum_source_units')
            p['minimum_output_wei']=number(p['minimum_output_wei'],'minimum_output_wei')
        for name in ('royalties','royalty_converter','royalty_nft','royalty_wrapper','oracle'):
            if name not in keeper.contracts: raise ValueError('Missing royalty contract: '+name)
            if not re.fullmatch(r'0x[0-9a-fA-F]{64}',keeper.config.get('code_hashes',{}).get(name,'')):
                raise ValueError('Missing royalty runtime pin: '+name)
        identity={'ledger':keeper.contracts['royalties'],'nft':keeper.contracts['royalty_nft'],
            'assets':[p['asset'] for p in self.routes]}
        state=keeper.state.get('royalty_conversion')
        if state is None:
            keeper.state['royalty_conversion']={'identity':identity,'asset':0,'ordinal':1,'next_first':True}
        else:
            if not isinstance(state,dict) or state.get('identity') != identity: raise ValueError('Royalty scan identity changed; reconcile state')
            integer(state.get('asset'),'asset cursor',minimum=0)
            if state['asset'] >= len(self.routes): raise ValueError('Invalid royalty asset cursor')
            number(state.get('ordinal'),'ordinal',1000)
            if type(state.get('next_first')) is not bool: raise ValueError('Invalid royalty scheduling state')

    def scan_once(self):
        k=self.k; state=k.state['royalty_conversion']; contracts=k.contracts
        latest=k.rpc.call('eth_getBlockByNumber',['latest',False])
        if not isinstance(latest,dict) or not re.fullmatch(r'0x[0-9a-fA-F]+',latest.get('number','')): raise RpcError('Invalid royalty head')
        block=int(latest['number'],16)-k.confirmations
        if block < 0: raise RpcError('Insufficient royalty confirmations')
        header=k.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if not isinstance(header,dict) or header.get('number') != hex(block) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',header.get('hash','')):
            raise RpcError('Invalid royalty anchor')
        selector={'blockHash':header['hash'],'requireCanonical':True}
        def read(name,sig,*args):
            words=decode_words(k.rpc.call('eth_call',[{'to':contracts[name],'data':calldata(sig,*args)},selector]))
            if len(words)!=1: raise RpcError('Unexpected royalty getter ABI')
            return int(words[0],16)
        checks=[('royalties','nft()',contracts['royalty_nft']),('royalties','canonicalController()',contracts['access']),
            ('royalties','converter()',contracts['royalty_converter']),('royalty_converter','ledger()',contracts['royalties']),
            ('royalty_converter','access()',contracts['access']),('royalty_converter','wrapper()',contracts['royalty_wrapper']),
            ('royalty_nft','access()',contracts['access']),('royalty_nft','royaltyRewards()',contracts['royalties'])]
        for name,sig,expected in checks:
            if read(name,sig)!=int(expected,16): raise RpcError('Royalty binding mismatch')
        for name in ('royalties','royalty_converter','royalty_nft','royalty_wrapper','oracle'):
            code=k.rpc.call('eth_getCode',[contracts[name],selector])
            if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                '0x'+keccak256(bytes.fromhex(code[2:])).hex()!=k.config['code_hashes'][name].lower():
                raise RpcError('Royalty code pin mismatch')
        for key,name in (('ZZZNFT','royalty_nft'),('ZZZOracle','oracle')):
            if read('access','module(bytes32)','0x'+keccak256(key.encode()).hex())!=int(contracts[name],16): raise RpcError('Royalty module mismatch')
        if read('royalties','MAX_CONVERSION_NFTS()')!=32 or read('royalty_converter','MAX_LOSS_BPS()')!=100:
            raise RpcError('Royalty protocol limit mismatch')
        if read('royalty_converter','enabled()')!=1: return False
        count=read('royalty_nft','mintedCount()')
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
        if read('royalties','isAsset(address)',asset)!=1: raise RpcError('Royalty currency is not admitted')
        if asset!=contracts['royalty_wrapper']:
            if read('royalty_converter','routeEnabled(bytes32)',route)!=1: return False
            values=decode_words(k.rpc.call('eth_call',[{'to':contracts['royalty_converter'],'data':calldata('route(bytes32)',route)},selector]))
            if len(values)!=10 or int(values[0],16)!=int(asset,16): raise RpcError('Royalty route currency mismatch')
        elif route!=ZERO: raise RpcError('WETH unwrapping must not select a swap route')
        ids=[];total=0
        for ordinal in range(first,last+1):
            token=read('royalty_nft','tokenAtOrdinal(uint256)',ordinal)
            if read('royalties','weightOf(uint256)',token)==0: continue
            amount=read('royalties','claimable(uint256,address)',token,asset)
            if amount: ids.append(token);total+=amount
        if len(ids)!=len(set(ids)): raise RpcError('Duplicate royalty token inventory')
        # A successful balance read can recover the waiting cohort even if no
        # currently payable whole units exist. sync never swaps or pays anyone.
        recover=read('royalties','eligibleCount(address)',asset)<read('royalties','activationCount()')
        _,now=k._head()
        if now-int(header['timestamp'],16)>300: raise RpcError('Stale royalty snapshot')
        if k.rpc.call('eth_getBlockByNumber',[hex(block),False])!=header: raise RpcError('Royalty anchor changed')
        if total<policy['minimum_source_units']:
            if recover: return k.submit('royalties','sync(address)',(asset,),f'royalty_sync:{asset}')
            return False
        expected=total if asset==contracts['royalty_wrapper'] else read('oracle','quote(address,address,uint256)',asset,contracts['royalty_wrapper'],total)
        if expected<policy['minimum_output_wei']: return False
        minimum=expected if asset==contracts['royalty_wrapper'] else (expected*9900+9999)//10000
        # Recheck after the last price read; the contract repeats its own floor.
        if k.rpc.call('eth_getBlockByNumber',[hex(block),False])!=header: raise RpcError('Royalty anchor changed')
        return k.submit('royalties',BATCH,(asset,sorted(ids),route,minimum,now+180),
            f'royalty_convert:{asset}:{first}:{last}',maximum_cost=minimum*self.gas_bps//10000)
