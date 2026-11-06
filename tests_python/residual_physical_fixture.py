"""Real principal/hash replies for explicit current6 synthetic transcripts only."""
from zzz_ops.abi import keccak256
from zzz_ops.production_v6 import physical_amounts


def attach_current_physical(rpc):
    """Keep historical fixture classes intact; scope stronger data to this object.

    Values follow captured PosM info/liquidity and slot0. Negative tests override
    a selected reply independently; neither callers nor production views are
    stubbed out. This utility is fixture setup, not independent audit evidence.
    """
    original_read,original_call=rpc.read,rpc.call
    rpc.physical_liquidities={}
    def words(*values):return [f'{v%(1<<256):064x}' for v in values]
    def uint(target,method,*args):return int(original_read(target,method,*args)[0],16)
    def frame(identifier):
        info=int(original_read(rpc.posm,'getPoolAndPositionInfo(uint256)',identifier,count=6)[5],16)
        ticks=[int(v,16) for v in original_read(rpc.contracts['liquidity'],'ticks(uint256)',identifier,count=2)]
        ticks=[v-(1<<256) if v>=(1<<255) else v for v in ticks]
        liquidity=rpc.physical_liquidities.get(identifier)
        if liquidity is None:liquidity=uint(rpc.posm,'getPositionLiquidity(uint256)',identifier)
        price=int(original_read(rpc.contracts['state_view'],'getSlot0(bytes32)',rpc.pool,count=4)[0],16)
        return info,liquidity,physical_amounts(price,ticks,liquidity)
    def fingerprints():
        main=rpc.position[1];mi,ml,_=frame(main);si=sl=0
        if rpc.secondary:si,sl,_=frame(rpc.secondary)
        values=[int(rpc.contracts['lp_position_executor'],16),int(rpc.posm,16),int(rpc.contracts['vault'],16),
            int(rpc.pool,16),main,mi,rpc.secondary,si]
        stable=int.from_bytes(keccak256(b''.join(v.to_bytes(32,'big') for v in values)),'big')
        execution=int.from_bytes(keccak256(b''.join(v.to_bytes(32,'big') for v in (stable,ml,sl))),'big')
        return stable,execution
    def read(target,signature,*args,count=1):
        if (target,signature) in rpc.overrides:return original_read(target,signature,*args,count=count)
        if target==rpc.posm and signature=='getPositionLiquidity(uint256)' and args[0] in rpc.physical_liquidities:
            return words(rpc.physical_liquidities[args[0]])
        if target==rpc.contracts['liquidity']:
            if signature=='amounts(uint256)':return words(*frame(args[0])[2])
            if signature=='portfolioAmounts(uint256)':
                values=frame(args[0])[2]
                if rpc.secondary:values=[a+b for a,b in zip(values,frame(rpc.secondary)[2])]
                return words(*values)
            if signature=='portfolioFingerprint(uint256)':return words(fingerprints()[0])
            if signature=='executionPortfolioFingerprint(uint256)':return words(fingerprints()[1])
        return original_read(target,signature,*args,count=count)
    def call(method,params):
        from zzz_ops.abi import calldata
        if method=='eth_call' and 'from' not in params[0]:
            for signature in ('portfolioFingerprint(uint256)','executionPortfolioFingerprint(uint256)',
                              'portfolioAmounts(uint256)','amounts(uint256)'):
                for identifier in (rpc.position[1],rpc.secondary):
                    if identifier and params[0]['data']==calldata(signature,identifier):
                        return '0x'+''.join(read(params[0]['to'],signature,identifier))
        return original_call(method,params)
    rpc.read,rpc.call=read,call
    return rpc
