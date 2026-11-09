"""The public catalog's actual base feed, distinct from the inactive name binding."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
ID=json.loads((OUT/'api3-management-selected.json').read_text())['ETH_USD'][0][1]
result={'anchor':{k:A[k]for k in ('block_number','block_hash','block_timestamp')},'feed_id':ID,'reads':{},'qualification':False}
try:
 for label,address,m in [('market_base',API['Api3MarketV2'],'getDataFeedData(bytes32)'),('server_base',API['Api3ServerV1'],'dataFeeds(bytes32)'),('registry_details',API['AirseekerRegistry'],'dataFeedIdToDetails(bytes32)')]:
  result['reads'][label]=attempt(lambda a=address,m=m:call(a,m,ID))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
finally:
 for name,data in [('api3-base.json',result),('api3-base-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
