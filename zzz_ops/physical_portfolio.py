"""Pure physical principal and typed identity calculations; no RPC or USD feeds."""
from zzz_ops.abi import keccak256,word


def physical_amounts(price,ticks,liquidity):
    """Exact floor principal amounts, independent of Manager-reported totals."""
    from zzz_ops.tick_math import sqrt_price_at_tick,MIN_SQRT,MAX_SQRT
    if (type(price) is not int or not MIN_SQRT<=price<MAX_SQRT or type(liquidity) is not int or
            not 0<liquidity<2**128 or not isinstance(ticks,list) or len(ticks)!=2 or
            any(type(t) is not int for t in ticks) or not -887272<=ticks[0]<ticks[1]<=887272):
        raise ValueError('Invalid physical principal inputs')
    a,b=map(sqrt_price_at_tick,ticks)
    first=0 if price>=b else ((liquidity<<96)*(b-max(price,a))//b)//max(price,a)
    second=0 if price<=a else liquidity*(min(price,b)-a)//(1<<96)
    return [first,second]


def portfolio_fingerprints(*,executor,position_manager,vault,pool,main,secondary=None):
    """Mirror the fixed typed-child wire, retaining all packed position bits.

    Each physical leg is (id, complete positionInfo, positive liquidity).
    Stable identity excludes L; the execution manifest includes both actual Ls.
    """
    legs=[main]+([secondary] if secondary is not None else [])
    for leg in legs:
        if (not isinstance(leg,tuple) or len(leg)!=3 or any(type(v) is not int for v in leg) or
                not 0<leg[0]<2**256 or not 0<=leg[1]<2**256 or not 0<leg[2]<2**128):
            raise ValueError('Invalid physical fingerprint leg')
    if secondary is not None and secondary[0]==main[0]:raise ValueError('Aliased physical fingerprint legs')
    aux=secondary if secondary is not None else (0,0,0)
    values=[(executor,'address'),(position_manager,'address'),(vault,'address'),(pool,'bytes32'),
        (main[0],'uint256'),(main[1],'uint256'),(aux[0],'uint256'),(aux[1],'uint256')]
    stable='0x'+keccak256(bytes.fromhex(''.join(word(v,t) for v,t in values))).hex()
    execution='0x'+keccak256(bytes.fromhex(word(stable,'bytes32')+
        word(main[2],'uint128')+word(aux[2],'uint128'))).hex()
    return stable,execution
