import datetime,hashlib,json,pathlib,sys,urllib.request,urllib.error
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
OLD=REPO/'reports/market-qualification-20261109/markets'
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
from zzz_ops.tick_math import decode_slot0,sqrt_price_at_tick
ANCHOR=json.loads((ROOT.parent/'shared/anchor.json').read_text())
PIN=ANCHOR['selector'];N=ANCHOR['block_number'];URL='https://rpc.mainnet.chain.robinhood.com/'
ZERO='0x'+'0'*40;Z='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a';W='0x0bd7d308f8e1639fab988df18a8011f41eacad73'
C='0x8366a39cc670b4001a1121b8f6a443a643e40951';S='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b';F='0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
QV4='0x8dc178efb8111bb0973dd9d722ebeff267c98f94';QV3='0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
SELECTED='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
METHODS={'eth_call','eth_getCode','eth_getLogs','eth_getBlockByNumber'}
class NoRedirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):fp.close();raise ValueError('unreviewed redirect')
opener=urllib.request.build_opener(NoRedirects)
def put(name,obj):
 with(ROOT/name).open('x',encoding='utf-8',newline='\n')as f:json.dump(obj,f,indent=2);f.write('\n')
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def rpc(name,calls):
 assert 0<len(calls)<=32
 assert all(m in METHODS for m,p in calls)
 payload=[{'jsonrpc':'2.0','id':i+1,'method':m,'params':p}for i,(m,p)in enumerate(calls)]
 req={'url':URL,'read_only':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'json':payload};put(name+'-request.json',req)
 result={k:v for k,v in req.items()if k!='json'}
 try:
  with opener.open(urllib.request.Request(URL,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'PoPL-readonly-route-followup/2'}),timeout=35)as r:raw=r.read(8000001);result['http_status']=r.status
 except urllib.error.HTTPError as x:raw=x.read(8000001);result['http_status']=x.code
 except Exception as x:raw=b'';result['transport_error']=type(x).__name__+': '+str(x)
 assert len(raw)<=8000000
 with(ROOT/(name+'-response.raw')).open('xb')as f:f.write(raw)
 result.update(response_bytes=len(raw),response_sha256=hashlib.sha256(raw).hexdigest());put(name+'-result.json',result)
 print(json.dumps({'capture':name,'status':result.get('http_status'),'bytes':len(raw),'error':result.get('transport_error')}),flush=True)
 obj=json.loads(raw)
 assert isinstance(obj,list)and len(obj)==len(payload)and{x['id']for x in obj}=={x['id']for x in payload}
 return sorted(obj,key=lambda x:x['id'])
def batch(name,calls,size=24):
 out=[]
 for i in range(0,len(calls),size):out.extend(rpc(name+'-'+str(i//size),calls[i:i+size]))
 return out
def h(s):return '0x'+keccak256(s.encode()).hex()
def word(x):return(int(x,16)if isinstance(x,str)else x%(1<<256)).to_bytes(32,'big').hex()
def data(sig,*args):return h(sig)[:10]+''.join(word(x)for x in args)
def call(addr,sig,*args):return('eth_call',[{'to':addr,'data':data(sig,*args)},PIN])
def vals(result):
 raw=result['result'][2:];assert len(raw)%64==0
 return[int(raw[i:i+64],16)for i in range(0,len(raw),64)]
def topicaddr(addr):return'0x'+word(addr)
def v4call(key,zfo,amount):return('eth_call',[{'to':QV4,'data':data('quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))',32,*key,int(zfo),amount,256,0),'gas':hex(2000000)},PIN])
def v3call(fee,zfo,amount):return('eth_call',[{'to':QV3,'data':data('quoteExactInputSingle((address,address,uint256,uint24,uint160))',W if zfo else Z,Z if zfo else W,amount,fee,0),'gas':hex(2000000)},PIN])
def canonical(name):
 r=rpc(name,[('eth_getBlockByNumber',[hex(N),False])]);assert r[0]['result']['hash']==ANCHOR['block_hash'];return True
def discovery():
 topic=h('Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)')
 logs=rpc('delta-discovery',[('eth_getLogs',[{'address':C,'fromBlock':hex(109785804),'toBlock':hex(N),'topics':[topic,None,topicaddr(ZERO),topicaddr(Z)]}]),('eth_getLogs',[{'address':F,'fromBlock':hex(109785804),'toBlock':hex(N),'topics':[h('PoolCreated(address,address,uint24,int24,address)'),topicaddr(W),topicaddr(Z)]}]),('eth_getLogs',[{'address':F,'fromBlock':hex(109785804),'toBlock':hex(N),'topics':[h('FeeAmountEnabled(uint24,int24)')]}])])
 pools=json.loads((OLD/'v4-discovered-pools.json').read_text());known={p['poolId']for p in pools};new=[]
 assert all('result'in x for x in logs)
 for log in logs[0]['result']:
  v=vals({'result':log['data']});key=[ZERO,Z,v[0],v[1]if v[1]<1<<255 else v[1]-(1<<256),'0x'+format(v[2],'040x')]
  pid='0x'+keccak256(bytes.fromhex(''.join(word(x)for x in key))).hex();assert pid==log['topics'][1]
  row={'poolId':pid,'key':key,'blockNumber':int(log['blockNumber'],16),'transactionHash':log['transactionHash'],'hookless':v[2]==0,'static':not(v[0]&0x800000)}
  if pid not in known:pools.append(row);new.append(row);known.add(pid)
 put('v4-pools.json',pools)
 # Prior unbounded fee log request failed. Fill that discovery gap once with <=10M-block reads.
 fee_calls=[('eth_getLogs',[{'address':F,'fromBlock':hex(low),'toBlock':hex(min(low+9999999,N)),'topics':[h('FeeAmountEnabled(uint24,int24)')]}])for low in range(0,N+1,10000000)]
 feesraw=batch('v3-enabled-fee-history',fee_calls)
 assert all('result'in x for x in feesraw)
 fees={}
 for answer in feesraw:
  for log in answer['result']:
   fee=int(log['topics'][1],16);spacing=int(log['topics'][2],16);fees[fee]={'fee':fee,'tickSpacing':spacing,'log':log}
 assert fees
 fee_states=rpc('v3-enabled-fee-pools',[call(F,'getPool(address,address,uint24)',Z,W,fee)for fee in sorted(fees)])
 for fee,r in zip(sorted(fees),fee_states):fees[fee]['getPool_response']=r;fees[fee]['pool']='0x'+r['result'][-40:]
 put('v3-enabled-fees.json',list(fees.values()))
 put('discovery.json',{'anchor':ANCHOR,'prior_anchor':109785803,'delta_from':109785804,'new_v4':new,'v3_delta_pool_events':logs[1]['result'],'v3_delta_fee_events':logs[2]['result'],'v3_enabled_fee_history_reads':len(fee_calls),'v3_enabled_fees':sorted(fees),'all_v4_keys':len(pools),'source_scope':'single official core/native ETH/fixedZZZ; single official v3factory/WETH/fixedZZZ; no hooked/dynamic/multihop/other factory venue qualification'})
 print(json.dumps({'new_v4':len(new),'all_v4':len(pools),'v3_enabled_fees':sorted(fees)}))
def state():
 pools=[p for p in read('v4-pools.json')if p['hookless']and p['static']and p['key'][2]<1000000]
 calls=[]
 for p in pools:calls.extend([call(S,'getSlot0(bytes32)',p['poolId']),call(S,'getLiquidity(bytes32)',p['poolId'])])
 res=batch('v4-state',calls)
 old={p['poolId']:p for p in json.loads((OLD/'v4-hookless-state.json').read_text())}
 for i,p in enumerate(pools):
  sr,lr=res[i*2:i*2+2];assert'result'in sr and'result'in lr
  p['slot0_response']=sr;p['liquidity_response']=lr;p['liquidity']=vals(lr)[0]
  p['slot0']=dict(zip(['sqrtPriceX96','tick','protocolFee','lpFee'],decode_slot0([sr['result'][j:j+64]for j in range(2,258,64)],expected_fee=p['key'][2])))
  p['principal_compatible_fee']=p['key'][2]<=100000
  p['changed_from_prior']=None if p['poolId']not in old else any(p[k]!=old[p['poolId']].get(k)for k in('liquidity','slot0'))
 put('v4-state.json',pools)
 v3=[p for p in read('v3-enabled-fees.json')if int(p['pool'],16)]
 labels=['token0()','token1()','fee()','tickSpacing()','liquidity()','slot0()','factory()'];calls=[]
 for p in v3:calls.extend(call(p['pool'],sig)for sig in labels)
 res=batch('v3-state',calls)
 for i,p in enumerate(v3):
  p['reads']=dict(zip(labels,res[i*7:i*7+7]));p['liquidity']=vals(p['reads']['liquidity()'])[0];p['sqrtPriceX96']=vals(p['reads']['slot0()'])[0]
  assert vals(p['reads']['token0()'])[0]==int(W,16)and vals(p['reads']['token1()'])[0]==int(Z,16)and vals(p['reads']['fee()'])[0]==p['fee']and vals(p['reads']['factory()'])[0]==int(F,16)
 put('v3-state.json',v3)
 binds=json.loads((OLD/'bindings-runtime-hashes.json').read_text());res=rpc('runtime-pins',[('eth_getCode',[p['address'],PIN])for p in binds])
 for p,r in zip(binds,res):
  raw=bytes.fromhex(r['result'][2:]);p['new_runtime_bytes']=len(raw);p['new_runtime_keccak256']='0x'+keccak256(raw).hex();p['unchanged']=p['new_runtime_keccak256']==p['runtime_keccak256']
 put('runtime-pins.json',binds)
 rpc('bindings',[call(S,'poolManager()'),call(QV4,'poolManager()'),call('0xcaf681a66d020601342297493863e78c959e5cb2','factory()'),call('0xcaf681a66d020601342297493863e78c959e5cb2','WETH9()'),call(Z,'decimals()')])
 print(json.dumps({'states':len(pools),'active':sum(bool(p['liquidity'])for p in pools),'changed':sum(p['changed_from_prior']is True for p in pools),'newly_active':[p['poolId']for p in pools if p['liquidity']and(not old.get(p['poolId'],{}).get('liquidity'))],'runtime_unchanged':all(p['unchanged']for p in binds)}))
def quotes():
 pools=read('v4-state.json');chosen=next(p for p in pools if p['poolId']==SELECTED);ratio=Fraction(chosen['slot0']['sqrtPriceX96']**2,1<<192)
 feed=rpc('eth-sizing-round',[call('0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9','latestRoundData()'),call('0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9','decimals()')]);v=vals(feed[0]);price=Fraction(v[1],10**vals(feed[1])[0])
 vectors=[('tiny_eth',True,10**6),('tiny_zzz',False,10**12),('zzz1',False,10**18),('zzz100',False,100*10**18),('zzz1000',False,1000*10**18),('zzz10000',False,10000*10**18)]
 for usd in[100,5]:
  amount=int(Fraction(usd)*10**18/price)
  vectors.extend([(f'nominal_{usd}usd_eth_half',True,amount//2),(f'nominal_{usd}usd_zzz_half',False,int(Fraction(amount)*ratio/2)),(f'nominal_{usd}usd_eth_full',True,amount),(f'nominal_{usd}usd_zzz_full',False,int(Fraction(amount)*ratio))])
 put('sizing.json',{'warning':'Conditional size labels only. Single ETH feed and selected-pool spot are not independent USD truth or configured PoPL prices. Full/half vectors are quote probes, not complete operations.','anchor':ANCHOR,'eth_usd':str(price),'eth_feed_round_words':v,'selected_ratio':str(ratio),'vectors':[{'label':label,'zeroForOne':zfo,'amountIn':amount}for label,zfo,amount in vectors]})
 rows=[];calls=[]
 for p in pools:
  vv=vectors if p['liquidity']or p['key'][2]<=10000 else vectors[:3]
  for label,zfo,amount in vv:
   rows.append({'version':4,'poolId':p['poolId'],'key':p['key'],'L':p['liquidity'],'label':label,'zeroForOne':zfo,'amountIn':amount,'sqrtPriceX96':p['slot0']['sqrtPriceX96'],'lpFee':p['slot0']['lpFee'],'protocolFee':p['slot0']['protocolFee'],'principal_compatible_fee':p['principal_compatible_fee']});calls.append(v4call(p['key'],zfo,amount))
 for p in read('v3-state.json'):
  for label,zfo,amount in vectors:
   rows.append({'version':3,'pool':p['pool'],'fee':p['fee'],'L':p['liquidity'],'label':label,'zeroForOne':zfo,'amountIn':amount,'sqrtPriceX96':p['sqrtPriceX96'],'principal_compatible':False,'fresh7_worker_compatible':False});calls.append(v3call(p['fee'],zfo,amount))
 res=batch('quotes',calls,16)
 for row,r in zip(rows,res):
  row['response']=r
  if'result'in r:
   v=vals(r);row['amountOut']=v[0];row['quoteGasEstimate']=v[-1];own=Fraction(row['sqrtPriceX96']**2,1<<192);expected=Fraction(row['amountIn'])*(own if row['zeroForOne']else 1/own);sel=Fraction(row['amountIn'])*(ratio if row['zeroForOne']else 1/ratio)
   row['ownspot_output_exact']=str(expected);row['selectedspot_output_exact']=str(sel);row['loss_bps_vs_own_spot']=float((1-Fraction(v[0])/expected)*10000);row['loss_bps_vs_selected_spot']=float((1-Fraction(v[0])/sel)*10000)
   if row['version']==3:row['sqrtAfter']=v[1];row['initializedTicksCrossed']=v[2]
  else:row['failure_class']='not_enough_liquidity_wrapped'if'7a5ed734'in r['error'].get('data','')else'preserved_error'
 put('quotes.json',rows);canonical('canonical-after-quotes');print(json.dumps({'calls':len(rows),'success':sum('amountOut'in r for r in rows),'errors':sum('error'in r['response']for r in rows),'zeroL_native_positive':[{'poolId':r['poolId'],'label':r['label'],'out':r['amountOut']}for r in rows if r['version']==4 and r['L']==0 and r['zeroForOne']and r.get('amountOut',0)>0]}))
if __name__=='__main__':{'discovery':discovery,'state':state,'quotes':quotes}[sys.argv[1]]()
