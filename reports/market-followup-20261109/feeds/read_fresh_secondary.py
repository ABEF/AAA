"""Separately labeled contemporary source liveness, not a replacement for the shared anchor."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
SHARED=A.copy(); ID=json.loads((OUT/'api3-management-selected.json').read_text())['ETH_USD'][0][1]
PYTH_ETH='0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
result={'purpose':'Separately labeled contemporary liveness only; never substitute for original shared route/price anchor.','original_shared_anchor':{k:SHARED[k]for k in ('block_number','block_hash','block_timestamp')},'provider':URL,'api3_base_feed_id':ID,'reads':{},'qualification':False}
try:
 if rpc('eth_chainId',[])!='0x1237':raise ValueError('wrong_chain')
 head=rpc('eth_getBlockByNumber',['latest',False]);number=int(head['number'],16)-12
 h=rpc('eth_getBlockByNumber',[hex(number),False]);BLOCK={'blockHash':h['hash'],'requireCanonical':True}
 result['secondary_anchor']={'chain_id':4663,'block_number':number,'block_hash':h['hash'],'block_timestamp':int(h['timestamp'],16),'selector':BLOCK,'observed_head':int(head['number'],16),'depth':13}
 for label,address,m,params in [('api3_market_base',API['Api3MarketV2'],'getDataFeedData(bytes32)',(ID,)),('api3_server_base',API['Api3ServerV1'],'dataFeeds(bytes32)',(ID,)),('api3_registry_details',API['AirseekerRegistry'],'dataFeedIdToDetails(bytes32)',(ID,)),('chainlink_primary',CL,'latestRoundData()',()),('pyth_ETH',PC,'getPriceUnsafe(bytes32)',(PYTH_ETH,))]:
  result['reads'][label]=attempt(lambda a=address,m=m,p=params:call(a,m,*p))
 end=rpc('eth_getBlockByNumber',[hex(number),False]);result['canonical_recheck']=end['hash']==h['hash']and end['timestamp']==h['timestamp']
except Exception as exc:result['error_type']=type(exc).__name__
finally:
 for name,data in [('fresh-secondary-reads.json',result),('fresh-secondary-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
