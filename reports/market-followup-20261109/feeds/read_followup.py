"""Read-only follow-up using the exact public anchor helpers, no state changes."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
# Only our reviewed helper definitions; do not rerun the previous campaign.
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
S=json.loads((OUT/'anchor-reads.json').read_text()); result={'anchor':S['anchor'],'reads':{},'qualification':False}
def code(address):
 raw=rpc('eth_getCode',[address,BLOCK])
 return {'raw':raw,'bytes':(len(raw)-2)//2,'keccak256':'0x'+keccak256(bytes.fromhex(raw[2:])).hex()}
try:
 for label,address,methods in [
  ('chainlink-owner','0xee27d5ae494300902d90454e8630a3f1c68c9c52',['getOwners()','getThreshold()','owner()']),
  ('api3-forwarder',API['OwnableCallForwarder'],['owner()']),
  ('api3-safe',API['GnosisSafeWithoutProxy'],['getOwners()','getThreshold()']),
  ('pyth-wormhole','0xb27e5ca259702f209a29225d0eddc131039c9933',['getCurrentGuardianSetIndex()','governanceChainId()','governanceContract()','chainId()']),
  ('pyth-implementation','0x66e9cba5529824a03b5bc9931d9c63637101d0f7',[])]:
  row={'address':address,'runtime':attempt(lambda a=address:code(a))};result['reads'][label]=row
  for m in methods:row[m]=attempt(lambda a=address,m=m:call(a,m))
 idx=result['reads']['pyth-wormhole']['getCurrentGuardianSetIndex()']
 if isinstance(idx,str):result['reads']['pyth-wormhole']['guardianSet']=attempt(lambda:call('0xb27e5ca259702f209a29225d0eddc131039c9933','getGuardianSet(uint32)',int(idx,16)))
 for symbol in ('ETH/USD','ZZZ/USD'):
  addr='0x'+S['reads']['api3-'+symbol]['communal_proxy'][-40:];row={'address':addr};result['reads']['api3-'+symbol]=row
  row['runtime']=attempt(lambda a=addr:code(a))
  for m in ('owner()','api3ServerV1()','api3ServerV1OevExtension()','dapiName()','dappId()','read()','decimals()','latestRoundData()'):
   row[m]=attempt(lambda a=addr,m=m:call(a,m))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
finally:
 for name,data in [('followup-reads.json',result),('followup-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps({k:{x:y for x,y in v.items()if x!='runtime'}for k,v in result['reads'].items()},indent=2))
