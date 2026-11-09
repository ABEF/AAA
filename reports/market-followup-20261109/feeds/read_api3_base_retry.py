"""One bounded alternate-public-provider retry of the exact shared anchor, never latest substitution."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
URL='https://robinhood.rpc.pinax.network'
ID=json.loads((OUT/'api3-management-selected.json').read_text())['ETH_USD'][0][1]
result={'anchor':{k:A[k]for k in ('block_number','block_hash','block_timestamp')},'provider':URL,'feed_id':ID,'reads':{},'qualification':False}
try:
 if rpc('eth_chainId',[])!='0x1237':raise ValueError('wrong_chain')
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False])
 if h['hash']!=A['block_hash']or int(h['timestamp'],16)!=A['block_timestamp']:raise ValueError('wrong_anchor')
 for label,address,m in [('market_base',API['Api3MarketV2'],'getDataFeedData(bytes32)'),('server_base',API['Api3ServerV1'],'dataFeeds(bytes32)'),('registry_details',API['AirseekerRegistry'],'dataFeedIdToDetails(bytes32)')]:
  result['reads'][label]=attempt(lambda a=address,m=m:call(a,m,ID))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
except Exception as exc:result['error_type']=type(exc).__name__
finally:
 for name,data in [('api3-base-retry.json',result),('api3-base-retry-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
