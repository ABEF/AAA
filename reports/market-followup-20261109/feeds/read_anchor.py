"""Fixed canonical-anchor public eth_call/code/storage only. No update or signing."""
import datetime, json, sys, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from zzz_ops.abi import calldata,keccak256
OUT=Path(__file__).resolve().parent
A=json.loads((OUT.parent/'shared/anchor.json').read_text())
URL=A['rpc']; BLOCK=A['selector']; LOG=[]
CL='0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9'
CL2='0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22'
AGG='0x6091E64eb7138EEF066a80FD3A0d7427B91f2721'
PC='0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a'
ID='0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
ADD=json.loads((OUT/'discovery/api3-addresses.raw').read_text())
API={k:v['4663'] for k,v in ADD.items() if isinstance(v,dict) and '4663'in v}
def word(n):return f'{n:064x}'
def b32(s):return '0x'+s.encode().hex().ljust(64,'0')
def dynamic_empty(signature,*head):
 return '0x'+keccak256(signature.encode()).hex()[:8]+''.join(str(x).removeprefix('0x').rjust(64,'0') for x in head)+word(32*(len(head)+1))+word(0)
class NoRedirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):fp.close();raise ValueError('unreviewed_redirect')
def rpc(method,params):
 assert method in ('eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getStorageAt')
 row={'id':len(LOG)+1,'method':method,'params':params,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};LOG.append(row)
 try:
  req=urllib.request.Request(URL,data=json.dumps({'jsonrpc':'2.0','id':row['id'],'method':method,'params':params}).encode(),headers={'Content-Type':'application/json','User-Agent':'PoPL-bounded-readonly-followup/1'})
  with urllib.request.build_opener(NoRedirects()).open(req,timeout=8) as r:raw=r.read(2*1024*1024+1)
  if len(raw)>2*1024*1024:raise ValueError('response_limit')
  env=json.loads(raw);row['response']=env
  if env.get('id')!=row['id']or env.get('jsonrpc')!='2.0'or ('result'in env)==('error'in env):raise ValueError('invalid_envelope')
  if 'error'in env:raise ValueError('rpc_refusal')
  return env['result']
 except urllib.error.HTTPError as e:row.update(http_status=e.code,error_type='HTTPError');e.close();raise
 except Exception as e:row['error_type']=type(e).__name__;raise
def call(address,signature,*args,data=None):return rpc('eth_call',[{'to':address,'data':data or calldata(signature,*args),'gas':hex(500000)},BLOCK])
def attempt(fn):
 try:return fn()
 except Exception as e:return {'error_type':type(e).__name__}
result={'anchor':{k:A[k] for k in ('chain_id','block_number','block_hash','block_timestamp','selector')},'provider':URL,'qualification':False,'reads':{}}
try:
 if rpc('eth_chainId',[])!='0x1237':raise ValueError('wrong_chain')
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False])
 if h['hash']!=A['block_hash']or int(h['timestamp'],16)!=A['block_timestamp']:raise ValueError('wrong_anchor')
 groups=[('chainlink-primary',CL,['latestRoundData()','decimals()','aggregator()','owner()','proposedAggregator()']),('chainlink-secondary',CL2,['latestRoundData()','aggregator()','owner()']),('chainlink-aggregator',AGG,['owner()','typeAndVersion()','latestConfigDetails()','aggregator()','transmitters()']),('pyth-core',PC,['version()','governanceDataSource()','singleUpdateFeeInWei()','transactionFeeInWei()','validDataSources()','wormhole()','getValidTimePeriod()','lastExecutedGovernanceSequence()']),('api3-factory',API['Api3ReaderProxyV1Factory'],['owner()','api3ServerV1OevExtension()']),('api3-server',API['Api3ServerV1'],['manager()','accessControlRegistry()','adminRole()']),('api3-market',API['Api3MarketV2'],['owner()','airseekerRegistry()']),('api3-registry',API['AirseekerRegistry'],['owner()','activeDapiNameCount()','activeDataFeedCount()'])]
 for label,address,methods in groups:
  row={'address':address};result['reads'][label]=row
  for m in methods:row[m]=attempt(lambda a=address,m=m:call(a,m))
  row['code']=attempt(lambda a=address:rpc('eth_getCode',[a,BLOCK]))
 result['reads']['pyth-core']['getPriceUnsafe(bytes32)']=attempt(lambda:call(PC,'getPriceUnsafe(bytes32)',ID))
 for slotname,label in [('implementation','eip1967.proxy.implementation'),('admin','eip1967.proxy.admin')]:
  slot='0x'+word(int.from_bytes(keccak256(label.encode()),'big')-1)
  result['reads']['pyth-core'][slotname]=attempt(lambda s=slot:rpc('eth_getStorageAt',[PC,s,BLOCK]))
 # Fee zero for an empty update is not a per-feed proof; capture both getters and invalid-byte rejection.
 result['reads']['pyth-core']['getUpdateFee(empty)']=attempt(lambda:call(PC,'',data=dynamic_empty('getUpdateFee(bytes[])')))
 for symbol in ('ETH/USD','ZZZ/USD'):
  name=b32(symbol);namehash='0x'+keccak256(bytes.fromhex(name[2:])).hex()
  row={'name':name,'name_hash':namehash};result['reads']['api3-'+symbol]=row
  row['data_feed_id']=attempt(lambda n=namehash:call(API['Api3ServerV1'],'dapiNameHashToDataFeedId(bytes32)',n))
  row['market_data']=attempt(lambda n=name:call(API['Api3MarketV2'],'getDapiData(bytes32)',n))
  row['subscription_id']=attempt(lambda n=name:call(API['Api3MarketV2'],'dapiNameToCurrentSubscriptionId(bytes32)',n))
  row['update_parameters']=attempt(lambda n=name:call(API['AirseekerRegistry'],'dapiNameToUpdateParameters(bytes32)',n))
  row['communal_proxy']=attempt(lambda n=name:call(API['Api3ReaderProxyV1Factory'],'',data=dynamic_empty('computeApi3ReaderProxyV1Address(bytes32,uint256,bytes)',n,word(1))))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
except Exception as e:result['error_type']=type(e).__name__
finally:
 result['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for name,data in [('anchor-reads.json',result),('anchor-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items()if k!='reads'},indent=2))
