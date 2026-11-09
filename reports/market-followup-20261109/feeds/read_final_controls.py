"""Bounded final fixed-anchor source-control reads; no service or chain writes."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
result={'anchor':{k:A[k]for k in ('block_number','block_hash','block_timestamp')},'reads':{},'qualification':False}
try:
 result['reads']['pyth-quorum-5']=attempt(lambda:call('0xb27e5ca259702f209a29225d0eddc131039c9933','quorum(uint256)',5))
 proxy='0x3c57b17052bdd5ff75b1f03c5f3afddbcfb8de1c'
 for name,label in [('implementation','eip1967.proxy.implementation'),('admin','eip1967.proxy.admin')]:
  slot='0x'+word(int.from_bytes(keccak256(label.encode()),'big')-1)
  raw=attempt(lambda s=slot:rpc('eth_getStorageAt',[proxy,s,BLOCK]));result['reads']['api3-'+name+'-slot']=raw
  if name=='implementation'and isinstance(raw,str)and int(raw,16):
   addr='0x'+raw[-40:];code=rpc('eth_getCode',[addr,BLOCK]);result['reads']['api3-implementation']={'address':addr,'code':code,'bytes':(len(code)-2)//2,'keccak256':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
 typ=attempt(lambda:call(API['Api3MarketV2'],'DAPI_PRICING_MERKLE_ROOT_HASH_TYPE()'));result['reads']['api3-pricing-hash-type']=typ
 if isinstance(typ,str):result['reads']['api3-pricing-root-at-anchor']=attempt(lambda:call(API['Api3MarketV2'],'getHashValue(bytes32)',typ))
 h=rpc('eth_getBlockByNumber',[hex(A['block_number']),False]);result['canonical_recheck']=h['hash']==A['block_hash']and int(h['timestamp'],16)==A['block_timestamp']
finally:
 for name,data in [('final-controls.json',result),('final-controls-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps({k:{x:y for x,y in v.items()if x!='code'}if isinstance(v,dict)else v for k,v in result['reads'].items()},indent=2))
