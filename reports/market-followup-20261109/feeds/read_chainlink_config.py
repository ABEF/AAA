"""Exact explorer-discovered Chainlink ABI, fixed-anchor controls and one historical ConfigSet log block."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
result={'anchor':{k:A[k]for k in ('block_number','block_hash','block_timestamp')},'reads':{},'qualification':False}
try:
 for m in ('getTransmitters()','getValidatorConfig()','getRequesterAccessController()','getBillingAccessController()','getLinkToken()','getBilling()','checkEnabled()','latestConfigDigestAndEpoch()','latestTransmissionDetails()','minAnswer()','maxAnswer()'):
  result['reads'][m]=attempt(lambda m=m:call(AGG,m))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
finally:
 for name,data in [('chainlink-controls.json',result),('chainlink-controls-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
