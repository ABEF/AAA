"""Verify the app's literal management mapping root at the separately labeled fresh anchor."""
import ast,re
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('read_anchor.py')
exec(compile(SOURCE.read_text().split("result={'anchor':",1)[0],str(SOURCE),'exec'))
FRESH=json.loads((OUT/'fresh-secondary-reads.json').read_text());BLOCK=FRESH['secondary_anchor']['selector']
s=(OUT/'discovery/api3-index-js.raw').read_text(encoding='utf8')
rows=json.loads(ast.literal_eval(re.search(r"fve=JSON.parse\(('(?:[^'\\]|\\.)*')\)",s).group(1)))
leaves=[]
for name,feed,sponsor in rows:
 encoded=bytes.fromhex(name[2:])+bytes.fromhex(feed[2:])+bytes.fromhex(sponsor[2:]).rjust(32,b'\0')
 leaves.append(keccak256(keccak256(encoded)))
leaves.sort();tree=[b'']*(2*len(leaves)-1)
for i,leaf in enumerate(leaves):tree[len(tree)-1-i]=leaf
for i in range(len(tree)-1-len(leaves),-1,-1):
 a,b=tree[2*i+1],tree[2*i+2];tree[i]=keccak256(min(a,b)+max(a,b))
literal=re.search('uve="(0x[0-9a-f]{64})"',s).group(1);computed='0x'+tree[0].hex()
TYPE='0x'+keccak256(b'dAPI management Merkle root').hex()
result={'fresh_secondary_anchor':FRESH['secondary_anchor'],'literal_app_root':literal,'computed_all_292_leaf_root':computed,'literal_root_verified':literal==computed,'selected_ETH_entry':json.loads((OUT/'api3-management-selected.json').read_text())['ETH_USD'],'source':'discovery/api3-index-js.raw','qualification':False}
try:
 result['onchain_root']=call(API['Api3MarketV2'],'getHashValue(bytes32)',TYPE)
 result['root_matches_onchain']=result['onchain_root']==computed
 h=rpc('eth_getBlockByNumber',[hex(FRESH['secondary_anchor']['block_number']),False]);result['canonical_recheck']=h['hash']==BLOCK['blockHash']and int(h['timestamp'],16)==FRESH['secondary_anchor']['block_timestamp']
except Exception as exc:result['error_type']=type(exc).__name__
finally:
 for name,data in [('api3-mapping-proof.json',result),('api3-mapping-proof-rpc.json',LOG)]:
  with (OUT/name).open('x',encoding='utf8')as f:json.dump(data,f,indent=2);f.write('\n')
 print(json.dumps(result,indent=2))
