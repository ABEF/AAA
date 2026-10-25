"""Explicitly authorized dated candidate reads; cannot sign or submit anything.

This bounded report driver does not admit assets, routes, feeds or a provider.
It deliberately reuses the repository's transport/ABI/budget boundaries.
"""
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import json
from pathlib import Path
import re
import sys
import urllib.error

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256, calldata
from zzz_ops.rpc import Rpc
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, request_scope
from zzz_ops.state import atomic_json

OUT=Path(__file__).resolve().parent
PYTH='0x8250f4af4b972684f7b336503e2d6dfedeb1487a'
ZERO='0x'+'0'*40
# Exact previously reviewed identities, also present in the official deployment
# extract. Do not import the unrelated local activation-route draft into evidence.
FACTORY='0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
QUOTER='0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
WETH='0x0bd7d308f8e1639fab988df18a8011f41eacad73'
ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
USDG='0x5fc5360d0400a0fd4f2af552add042d716f1d168'
USDC='0x80e0e24718dbfcad49ecaa6f1e6c89a190586ca8'
CODE_HASHES={FACTORY:'0xec72b1abd1f2faee020cfea9c646bd8994f9fb389054f6e574f103a895091739',
             QUOTER:'0x3db0868d945e9304c9bc6a8b2181948109ea617647142f3c4083e14393496a28'}

def words(raw, count):
    if not isinstance(raw,str) or not re.fullmatch('0x[0-9a-fA-F]{'+str(count*64)+'}',raw):
        raise ValueError('noncanonical_abi')
    return [int(raw[i:i+64],16) for i in range(2,len(raw),64)]

def digest(raw):
    if not isinstance(raw,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',raw):
        raise ValueError('missing_runtime')
    return '0x'+keccak256(bytes.fromhex(raw[2:])).hex()

def bounded_error(exc):
    result={'type':type(exc).__name__}
    cursor=exc
    for _ in range(8):
        if isinstance(cursor,urllib.error.HTTPError): result['http_status']=cursor.code
        if hasattr(cursor,'reason') and getattr(cursor,'reason') in ('unavailable_block','rate_limited','invalid_params','unclassified'):
            result['remote_reason']=cursor.reason
        if hasattr(cursor,'code') and type(getattr(cursor,'code')) is int: result['remote_code']=cursor.code
        cursor=getattr(cursor,'__cause__',None)
        if cursor is None: break
    return result

def run(mode,provider='pinax'):
    result={'read_only':True,'release_approved':False,'qualification':False,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
            'provider_label':'public_'+provider+'_candidate','scope':mode,'chain_id':4663,'observations':[]}
    endpoints={'pinax':'https://robinhood.rpc.pinax.network','official':'https://rpc.mainnet.chain.robinhood.com'}
    rpc=Rpc([endpoints[provider]],4663,timeout=8,retries=1)
    with request_scope(Budget(seconds=60,calls=64,posts=128)) as budget:
        def read(method,params=None):
            budget.consume('calls')
            return rpc.call(method,params)
        if read('eth_chainId')!=4663: raise ValueError('chain_mismatch')
        head=int(read('eth_blockNumber'),16)
        number=head-12
        header=read('eth_getBlockByNumber',[hex(number),False])
        if not isinstance(header,dict) or int(header.get('number','0x0'),16)!=number or not re.fullmatch(r'0x[0-9a-fA-F]{64}',header.get('hash','')):
            raise ValueError('canonical_header_missing')
        timestamp=int(header['timestamp'],16)
        now=int(datetime.now(timezone.utc).timestamp())
        if not now-120<=timestamp<=now+30: raise ValueError('stale_or_future_snapshot')
        result['snapshot']={'number':number,'hash':header['hash'],'timestamp':timestamp,'head':head,'confirmations':12}
        tag={'blockHash':header['hash'],'requireCanonical':True}
        def call(target,signature,*args):
            return read('eth_call',[{'to':target,'data':calldata(signature,*args)},tag])
        def observe(label,fn):
            try: value=fn(); item={'label':label,'available':True,**value}
            except WorkLimit: raise
            except (RpcError,ValueError,TypeError,KeyError) as exc: item={'label':label,'available':False,'error':bounded_error(exc)}
            result['observations'].append(item)
            return item
        if mode=='feeds':
            catalog=json.loads((OUT/'chainlink-selected.json').read_text())
            for feed in catalog:
                def read(feed=feed):
                    address=feed['proxyAddress'].lower()
                    code=digest(read('eth_getCode',[address,tag]))
                    decimals=words(call(address,'decimals()'),1)[0]
                    raw=call(address,'latestRoundData()'); values=words(raw,5)
                    round_id,answer,started,updated,answered=values
                    if decimals>18 or not 0<answer<2**255 or not 0<round_id<2**80 or answered<round_id or not 0<started<=updated<=timestamp:
                        raise ValueError('invalid_round')
                    return {'address':address,'runtime_keccak':code,'decimals':decimals,'raw_latest_round':raw,
                        'round_id':str(round_id),'answer':str(answer),'started_at':started,'updated_at':updated,'answered_in_round':str(answered),
                        'snapshot_age_seconds':timestamp-updated,'usd':str(Decimal(answer)/(10**decimals)),
                        'catalog_heartbeat_seconds':feed['heartbeat'],'within_catalog_heartbeat':timestamp-updated<=feed['heartbeat'],
                        'independence_qualified':False,'product':feed.get('svrDisplayLabel')}
                observe('Chainlink '+feed['name'],read)
            observe('Pyth Core runtime',lambda:{'address':PYTH,'runtime_keccak':digest(read('eth_getCode',[PYTH,tag]))})
            # Observe, do not approve, the implementation behind the public proxy.
            slot=hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)
            observe('Pyth Core ERC1967 implementation slot',lambda:{'slot':slot,'raw':read('eth_getStorageAt',[PYTH,slot,tag])})
            for feed in json.loads((OUT/'pyth-selected.json').read_text()):
                def read(feed=feed):
                    raw=call(PYTH,'getPriceUnsafe(bytes32)','0x'+feed['hermes_id'])
                    price,confidence,expo,published=words(raw,4)
                    price=price-(1<<256) if price>=1<<255 else price
                    expo=expo-(1<<256) if expo>=1<<255 else expo
                    if not 0<price<2**63 or not 0<=confidence<2**64 or not -18<=expo<=0 or not 0<published<=timestamp:
                        raise ValueError('invalid_pyth_price')
                    return {'contract':PYTH,'feed_id':'0x'+feed['hermes_id'],'raw_price':raw,'price':str(price),'confidence':str(confidence),
                        'exponent':expo,'publish_time':published,'snapshot_age_seconds':timestamp-published,
                        'confidence_fraction':str(Decimal(confidence)/price),'usd':str(Decimal(price)*(Decimal(10)**expo)),
                        'within_60_seconds':timestamp-published<=60,'independence_qualified':False}
                observe('Pyth '+feed['symbol'],read)
        elif mode=='routes':
            code=digest(read('eth_getCode',[FACTORY,tag]))
            if code!=CODE_HASHES[FACTORY]: raise ValueError('unreviewed_factory_runtime')
            quoter_code=digest(read('eth_getCode',[QUOTER,tag]))
            if quoter_code!=CODE_HASHES[QUOTER]: raise ValueError('unreviewed_quoter_runtime')
            result['venue']={'factory':FACTORY,'factory_runtime_keccak':code,'quoter':QUOTER,'quoter_runtime_keccak':quoter_code}
            candidates=[]
            for left,right,name in [(ZZZ,WETH,'ZZZ/WETH'),(ZZZ,USDG,'ZZZ/USDG'),(USDG,WETH,'USDG/WETH'),(USDC,WETH,'USDC/WETH')]:
                for fee in (500,3000):
                    record=observe(f'{name} fee {fee}',lambda left=left,right=right,fee=fee:{
                        'factory_pool_word':call(FACTORY,'getPool(address,address,uint24)',left,right,fee)})
                    if record['available']:
                        value=words(record['factory_pool_word'],1)[0]
                        if value>=2**160: raise ValueError('noncanonical_pool_address')
                        record['pool']='0x'+format(value,'040x')
                        record['exists']=value!=0
                        if value: candidates.append((record,left,right,fee))
            # A present address is discovery only. Verify key metadata before any quote.
            for record,left,right,fee in candidates:
                def metadata(record=record,left=left,right=right,fee=fee):
                    pool=record['pool']; runtime=digest(read('eth_getCode',[pool,tag]))
                    factory=words(call(pool,'factory()'),1)[0]
                    token0=words(call(pool,'token0()'),1)[0]; token1=words(call(pool,'token1()'),1)[0]
                    actual_fee=words(call(pool,'fee()'),1)[0]
                    liquidity=words(call(pool,'liquidity()'),1)[0]
                    if factory!=int(FACTORY,16) or (token0,token1)!=tuple(sorted((int(left,16),int(right,16)))) or actual_fee!=fee or liquidity>=2**128:
                        raise ValueError('pool_identity_mismatch')
                    return {'pool':pool,'runtime_keccak':runtime,'factory':FACTORY,'token0':'0x'+format(token0,'040x'),
                            'token1':'0x'+format(token1,'040x'),'fee_pips':fee,'active_liquidity':str(liquidity),
                            'quote_qualified':False,'native_eth_route':False}
                observe(record['label']+' metadata',metadata)
        ending=read('eth_getBlockByNumber',[hex(number),False])
        if any(ending.get(key)!=header.get(key) for key in ('number','hash','timestamp')):
            raise ValueError('canonical_snapshot_changed')
        result['snapshot_rechecked']=True
        result['logical_read_budget_remaining']=budget.calls
        result['http_post_budget_remaining']=budget.posts
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=('feeds','routes'))
    parser.add_argument('--provider',choices=('pinax','official'),default='pinax'); args=parser.parse_args()
    try: report=run(args.mode,args.provider)
    except Exception as exc:
        report={'read_only':True,'qualification':False,'release_approved':False,'scope':args.mode,
                'observed_at_utc':datetime.now(timezone.utc).isoformat(),'available':False,'error':bounded_error(exc)}
    atomic_json(OUT/(args.mode+'-'+args.provider+'-observation.json'),report)
    print(json.dumps({'scope':args.mode,'snapshot':report.get('snapshot'),'observations':len(report.get('observations',[])),
                      'available':report.get('available',True),'error':report.get('error'),
                      'failures':[x['label'] for x in report.get('observations',[]) if not x['available']]}))
