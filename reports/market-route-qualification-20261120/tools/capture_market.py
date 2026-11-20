"""Bounded read-only phases; no wallet, signer, write RPC or adoption."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, sys, time
import transport_base as b

ROOT = Path(__file__).resolve().parents[3]
BASELINE = '73658567cb605b58c992698e2103535e782269dd'
STOA = '0x27958279f95225b2a5517e7dd12b6fc0317e5c5d'
WETH = '0x0bd7d308f8e1639fab988df18a8011f41eacad73'
V2 = '0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f'
V3 = '0x1f7d7550b1b028f7571e69a784071f0205fd2efa'


def state_rows(c, pools):
    slots = []
    for p in pools:
        assert '0x'+b.keccak256(b''.join(b.word(x) for x in p['key'])).hex() == p['poolId']
        n = int.from_bytes(b.keccak256(b.word(p['poolId'])+b.word(6)), 'big')
        slots.extend((n,n+3))
    values = []
    for i,start in enumerate(range(0,len(slots),50)):
        chunk=slots[start:start+50]
        data='0x'+(b.keccak256(b'extsload(bytes32[])')[:4]+b.word(32)+b.word(len(chunk))+b''.join(b.word(x) for x in chunk)).hex()
        v=b.vals(c.call(b.CORE,'',data=data,label=f'pool-state-bulk-{i}'))
        assert v[:2]==[32,len(chunk)] and len(v)==len(chunk)+2
        values+=v[2:]
    result=[]
    for i,p in enumerate(pools):
        packed,L=values[2*i:2*i+2]
        tick=(packed>>160)&0xffffff
        if tick&(1<<23):tick-=1<<24
        s=dict(sqrtPriceX96=packed&((1<<160)-1),tick=tick,protocolFee=(packed>>184)&0xffffff,lpFee=(packed>>208)&0xffffff)
        assert packed>>232==0 and 0<=L<1<<128 and s['sqrtPriceX96']>0
        if p['key'][2] < 1_000_000:assert s['lpFee']==p['key'][2]
        result.append(dict(poolId=p['poolId'],key=p['key'],slot0=s,active_liquidity=str(L)))
    return result


def keys(value):
    if isinstance(value,dict):return dict(error=value)
    v=b.vals(value)
    assert len(v)>=2 and v[0]==32 and v[1]<=64 and len(v)==2+5*v[1]
    result=[]
    for i in range(v[1]):
        x=v[2+5*i:7+5*i]
        tick=x[3]-(1<<256) if x[3]>>255 else x[3]
        assert x[0]<1<<160 and x[1]<1<<160 and x[2]<1<<24 and 0<tick<=32767 and x[4]<1<<160
        key=['0x'+f'{x[0]:040x}','0x'+f'{x[1]:040x}',x[2],tick,'0x'+f'{x[4]:040x}']
        result.append(dict(key=key,poolId='0x'+b.keccak256(b''.join(b.word(y) for y in key)).hex(),discovery_only=True))
    return result


def state(c, result):
    assert c.rpc('eth_chainId',[],'chain')=='0x1237'
    assert c.rpc('eth_getBlockByNumber',['0x0',False],'genesis')['hash']==b.GENESIS
    h=c.rpc('eth_getBlockByNumber',['latest',False],'anchor')
    assert abs(time.time()-int(h['timestamp'],16))<=120
    result['anchor']=dict(chain_id=4663,number=int(h['number'],16),hash=h['hash'],timestamp=int(h['timestamp'],16),header=h)
    c.block=dict(blockHash=h['hash'],requireCanonical=True)
    result['runtimes']={name:c.code(target,name,b.PRIOR['runtimes'][name]['keccak256']) for name,target in [('core',b.CORE),('state_view',b.VIEW),('quoter',b.QUOTER),('zzz',b.ZZZ)]}
    result['pools']=state_rows(c,b.POOLS)
    result['feeds']={}
    for name,target in [('chainlink_primary',b.CL),('chainlink_secondary',b.CL2)]:
        prior=b.PRIOR['feeds'][name]
        result['feeds'][name]=dict(address=target,runtime=c.code(target,name,prior['runtime']['keccak256']),aggregator=c.call(target,'aggregator()',label=name+'.aggregator'))
    finish_state(c,result)


def finish_state(c,result):
    agg='0x'+b.word(b.vals(result['feeds']['chainlink_primary']['aggregator'],1)[0]).hex()[-40:]
    assert agg==b.PRIOR['feeds']['chainlink_aggregator']['address']
    result['feeds']['chainlink_aggregator']=c.code(agg,'chainlink_aggregator',b.PRIOR['feeds']['chainlink_aggregator']['runtime']['keccak256'])
    result['feeds']['chainlink_primary'].update(round=c.call(b.CL,'latestRoundData()',label='chainlink.round'),decimals=c.call(b.CL,'decimals()',label='chainlink.decimals'))
    for name,target,signature,args in [('pyth',b.PYTH,'getPriceUnsafe(bytes32)',(b.ETH_ID,)),('api3',b.API3,'read()',())]:
        prior=b.PRIOR['feeds'][name]
        row=dict(address=target,runtime=c.code(target,name,prior['runtime']['keccak256']))
        slot='0x'+b.word(int.from_bytes(b.keccak256(b'eip1967.proxy.implementation'),'big')-1).hex()
        implementation=c.rpc('eth_getStorageAt',[target,slot,c.block],name+'.implementation-slot')
        assert implementation==prior['implementation_slot']
        row.update(implementation_slot=implementation,implementation_runtime=c.code('0x'+implementation[-40:],name+'.implementation',prior['implementation_runtime']['keccak256']),observation=c.call(target,signature,args,label=name+'.observation'))
        result['feeds'][name]=row
    raw=c.call(STOA,'keysFor(address,address)',(WETH,b.ZZZ),label='discovery.stoa.keysFor')
    result['stoa_registry']=dict(address=STOA,raw=raw,decoded=keys(raw),qualified=False)


def quotes(c,result,previous):
    result['anchor']=previous['anchor'];c.block=dict(blockHash=result['anchor']['hash'],requireCanonical=True)
    assert c.rpc('eth_getBlockByNumber',[hex(result['anchor']['number']),False],'anchor-before')==result['anchor']['header']
    pools=previous['pools'];selected=next(p for p in pools if p['poolId']==b.SELECTED)
    main=max((p for p in pools if p['poolId']!=b.SELECTED and p['key'][2]<=100000),key=lambda p:int(p['active_liquidity']))
    rows=b.vals(previous['feeds']['chainlink_primary']['round'],5);dec=b.vals(previous['feeds']['chainlink_primary']['decimals'],1)[0]
    assert 0<rows[1]<1<<255 and 0<rows[2]<=rows[3]<=result['anchor']['timestamp'] and rows[0]<=rows[4] and dec<=18
    eth=Fraction(rows[1],10**dec)
    cheap=[p for p in pools if b.fee(p,False)<10000 and p['key'][2]<100000 and 10**12<p['slot0']['sqrtPriceX96']<10**40]
    result['cheap_pool_count_before_extreme_exclusion']=sum(b.fee(p,False)<10000 for p in pools)
    # Explicit finite diagnostics, not the protocol's assumed swap fraction.
    requests=[]
    for p in cheap:
        for n in (1,100,1000):requests.append((p,False,n*10**18,500000))
        requests.append((p,True,int(Fraction(5*10**18,1)/eth),500000))
    for p in (selected,main):
        requests.extend([(p,True,int(Fraction(50*10**18,1)/eth),500000),(p,False,10**18,500000),(p,False,100*10**18,500000)])
    # One separate high-gas diagnostic for the old opaque low-fee case. This
    # does not change any protocol/service setting or qualify whole-tx gas.
    low=next(p for p in cheap if p['key'][2]==75)
    requests.append((low,False,10**18,1000000))
    result['quotes']=[]
    for p,direction,amount,gas in requests:
        encoded='0x'+(b.keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+b.word(32)+b''.join(b.word(x) for x in p['key'])+b.word(int(direction))+b.word(amount)+b.word(256)+b.word(0)).hex()
        observed=c.call(b.QUOTER,'',data=encoded,label='quote.'+p['poolId']+'.'+('ETH-ZZZ' if direction else 'ZZZ-ETH')+'.'+str(amount)+'.'+str(gas),gas=gas)
        result['quotes'].append(dict(pool_id=p['poolId'],key=p['key'],zero_for_one=direction,input_raw=str(amount),result=observed,gas_ceiling=gas,diagnostic_higher_gas_only=gas!=500000,known_fee_pips=b.fee(p,direction),postspot=None,complete_operation_qualified=False))


def discovery(c,result,previous):
    result['anchor']=previous['anchor'];c.block=dict(blockHash=result['anchor']['hash'],requireCanonical=True)
    assert c.rpc('eth_getBlockByNumber',[hex(result['anchor']['number']),False],'anchor-before')==result['anchor']['header']
    result['factory_leads']=[]
    # Addresses/ABI are documented external discovery leads, not pinned or
    # admitted PoPL executors. Confirm response/code/identities separately.
    for name,address in [('v2',V2),('v3',V3),('stoa',STOA),('weth',WETH)]:
        raw=c.rpc('eth_getCode',[address,c.block],name+'.unqualified-code')
        assert isinstance(raw,str) and raw.startswith('0x') and len(raw)%2==0
        result.setdefault('unqualified_discovery_runtimes',{})[name]=dict(address=address,bytes=(len(raw)-2)//2,keccak256='0x'+b.keccak256(bytes.fromhex(raw[2:])).hex(),qualified=False)
    pair=c.call(V2,'getPair(address,address)',(WETH,b.ZZZ),label='discovery.v2.WETH-ZZZ')
    result['factory_leads'].append(dict(kind='v2',factory=V2,result=pair))
    for fee in (100,500,2500,3000,10000):
        value=c.call(V3,'getPool(address,address,uint24)',(WETH,b.ZZZ,fee),label='discovery.v3.WETH-ZZZ.'+str(fee))
        result['factory_leads'].append(dict(kind='v3',factory=V3,fee=fee,result=value))
    decoded=previous.get('stoa_registry',{}).get('decoded',[])
    extra=[p for p in decoded if p['poolId'] not in {x['poolId'] for x in previous['pools']}] if isinstance(decoded,list) else []
    result['stoa_registry_available']=isinstance(decoded,list)
    result['additional_v4_states']=state_rows(c,extra) if extra else []


def main():
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['state','state-continuation','quotes','discovery']);a.add_argument('output',type=Path);a.add_argument('--previous',type=Path);args=a.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);b.OUT=args.output;c=b.Capture()
    result=dict(schema=1,phase=args.phase,baseline=BASELINE,production_approved=False,configuration_adopted=False,public_transactions=0)
    result['source_pins']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),Path(b.__file__).resolve(),ROOT/'zzz_ops/abi.py',ROOT/'src/ZZZV4SpotPriceFeed.sol',ROOT/'src/ZZZOracle.sol']}
    try:
        if args.phase=='state':state(c,result)
        else:
            assert args.previous is not None
            raw=args.previous.read_bytes();previous=json.loads(raw);assert previous.get('canonical_final_recheck') is True
            result['prior_capture_sha256']=hashlib.sha256(raw).hexdigest()
            if args.phase=='state-continuation':
                assert previous['stopped']['exception_type']=='KeyError' and previous['phase']=='state'
                for k in ('anchor','runtimes','pools','feeds'):result[k]=previous[k]
                c.block=dict(blockHash=result['anchor']['hash'],requireCanonical=True)
                assert c.rpc('eth_getBlockByNumber',[hex(result['anchor']['number']),False],'anchor-before')==result['anchor']['header']
                finish_state(c,result)
            else:(quotes if args.phase=='quotes' else discovery)(c,result,previous)
    except Exception as exc:
        result['stopped']=dict(exception_type=type(exc).__name__,reason=str(exc) if isinstance(exc,(AssertionError,ValueError,b.Stop)) else 'Transport failure; no retry',provider_stopped=c.stopped)
    finally:
        if result.get('anchor') and not c.stopped:
            try:
                h=c.rpc('eth_getBlockByNumber',[hex(result['anchor']['number']),False],'anchor-after',closure=True)
                result['canonical_final_recheck']=h==result['anchor']['header'];result['final_header']=h
            except Exception as exc:result['closure_failure']=type(exc).__name__
        result['request_count']=len(c.rows);result['elapsed_seconds']=None if c.start is None else time.perf_counter()-c.start
        b.save('CAPTURE.json',result)
        print(json.dumps({k:result.get(k) for k in ['phase','request_count','elapsed_seconds','canonical_final_recheck','stopped']}))


if __name__=='__main__':main()
