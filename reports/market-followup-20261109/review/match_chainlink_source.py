import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
raw=(ROOT/'chainlink-aggregator-source-v2.raw').read_bytes()
explorer=json.loads(raw)
snap=json.loads((ROOT.parent/'feeds'/'anchor-reads.json').read_text(encoding='utf-8'))
entry=snap['reads']['chainlink-aggregator']
assert entry['address'].lower()=='0x6091e64eb7138eef066a80fd3a0d7427b91f2721'
actual=bytes.fromhex(entry['code'][2:]);reported=bytes.fromhex(explorer['deployed_bytecode'][2:])
def digest(blob):return '0x'+keccak256(blob).hex()
with (ROOT/'ChainlinkDualAggregator.explorer.sol').open('x',encoding='utf-8',newline='\n') as out:out.write(explorer['source_code'])
result={
 'address':entry['address'],'anchor':snap['anchor'],'qualification':False,
 'url':'https://robinhoodchain.blockscout.com/api/v2/smart-contracts/'+entry['address'],
 'explorer_name':explorer['name'],'compiler':explorer['compiler_version'],'file_path':explorer['file_path'],
 'is_verified':explorer['is_verified'],'is_fully_verified':explorer['is_fully_verified'],
 'is_partially_verified':explorer['is_partially_verified'],'license_type':explorer['license_type'],
 'reported_runtime_bytes':len(reported),'canonical_runtime_bytes':len(actual),
 'reported_runtime_keccak256':digest(reported),'canonical_runtime_keccak256':digest(actual),
 'reported_runtime_equals_canonical':reported==actual,
 'source_json_sha256':hashlib.sha256(raw).hexdigest(),
 'source_sha256':hashlib.sha256(explorer['source_code'].encode()).hexdigest(),
 'functions':[row['name'] for row in explorer['abi'] if row.get('type')=='function'],
 'constructor_args':explorer['decoded_constructor_args'],
 'limitation':'Explorer-reported verified source runtime equals shared-anchor onchain runtime; not independently recompiled, audited, feed-independent or operating-approved.'}
with (ROOT/'chainlink-source-match.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('functions','constructor_args','anchor')},indent=2))
