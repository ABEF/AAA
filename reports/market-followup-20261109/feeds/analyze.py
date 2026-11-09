"""Decode captured public evidence only, with exact low-denominator agreement test."""
import ast,datetime,decimal,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from zzz_ops.abi import keccak256
P=Path(__file__).resolve().parent; D=decimal.Decimal
def read(n):return json.loads((P/n).read_text(encoding='utf8'))
def save(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def words(s):
 assert isinstance(s,str)and re.fullmatch('0x(?:[0-9a-fA-F]{64})*',s)
 return [int(s[i:i+64],16)for i in range(2,len(s),64)]
def signed(n):return n-(1<<256)if n>>255 else n
def utc(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
R=read('anchor-reads.json');F=read('followup-reads.json');T=R['anchor']['block_timestamp']
C=words(R['reads']['chainlink-primary']['latestRoundData()']);Y=words(R['reads']['pyth-core']['getPriceUnsafe(bytes32)'])
eth=D(C[1])/10**8;pyth=D(signed(Y[0]))*D(10)**signed(Y[2]);low=min(eth,pyth);high=max(eth,pyth)
res={'anchor':R['anchor'],'canonical_rechecks':[R['canonical_recheck'],F['canonical_recheck']],
 'chainlink':{'proxy':R['reads']['chainlink-primary']['address'],'secondary_proxy':R['reads']['chainlink-secondary']['address'],'aggregator':'0x'+R['reads']['chainlink-primary']['aggregator()'][-40:],
  'round_id':str(C[0]),'answered_in_round':str(C[4]),'answer_raw':str(C[1]),'decimals':8,'usd':str(eth),'started_at':C[2],'updated_at':C[3],'updated_at_utc':utc(C[3]),'age_seconds':T-C[3],
  'secondary_same_aggregator':R['reads']['chainlink-primary']['aggregator()']==R['reads']['chainlink-secondary']['aggregator()'],
  'owner':'0x'+R['reads']['chainlink-primary']['owner()'][-40:],'owner_safe_threshold':int(F['reads']['chainlink-owner']['getThreshold()'],16),'owner_safe_owner_count':words(F['reads']['chainlink-owner']['getOwners()'])[1],
  'chosen_max_age_seconds':None,'catalog_heartbeat_seconds':86400,'catalog_deviation_percent':'0.5','qualified':False},
 'pyth':{'core':R['reads']['pyth-core']['address'],'feed_id':'0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace','price_raw':str(signed(Y[0])),'confidence_raw':str(Y[1]),'exponent':signed(Y[2]),'usd':str(pyth),'confidence_bps':str(D(Y[1])*10000/D(signed(Y[0]))),'publish_time':Y[3],'publish_time_utc':utc(Y[3]),'age_seconds':T-Y[3],
  'passes_hard_86400_age':0<=T-Y[3]<=86400,'single_update_fee_wei':int(R['reads']['pyth-core']['singleUpdateFeeInWei()'],16),'transaction_fee_wei':int(R['reads']['pyth-core']['transactionFeeInWei()'],16),
  'get_update_fee_empty_wei':int(R['reads']['pyth-core']['getUpdateFee(empty)'],16),'authenticated_current_packet_available_in_campaign':False,'unauthenticated_current_Hermes_status':401,'paid_plan_and_updater_funding_qualified':False,'qualified':False},
 'eth_pair':{'low_usd':str(low),'high_usd':str(high),'spread_bps_against_low':str((high-low)*10000/low),'passes_300bps':(high-low)*10000<=low*300,'exact_test':'(high - low) * 10000 <= low * 300','qualified':False},
 'runtime_pins':{},'api3':{},'qualification':False}
for group,data in R['reads'].items():
 code=data.get('code')
 if isinstance(code,str):res['runtime_pins'][group]={'address':data['address'],'bytes':(len(code)-2)//2,'keccak256':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
for group,data in F['reads'].items():
 code=data.get('runtime',{})
 if isinstance(code,dict)and'keccak256'in code:res['runtime_pins'][group]={'address':data['address'],**{k:v for k,v in code.items()if k!='raw'}}
for symbol in ('ETH/USD','ZZZ/USD'):
 a=R['reads']['api3-'+symbol];b=F['reads']['api3-'+symbol]
 md=words(a['market_data'])
 res['api3'][symbol]={'name':a['name'],'name_hash':a['name_hash'],'data_feed_id':a['data_feed_id'],'subscription_id':a['subscription_id'],'value':md[1],'timestamp':md[2],
 'computed_communal_proxy':b['address'],'runtime_bytes':b['runtime']['bytes'],'runtime_keccak256':b['runtime']['keccak256'],'read_result':b['read()'],'decimals_result':b['decimals()'],
 'qualified':False,'requires_new_adapter_for_current_Oracle':True,'source_implementation_latestRoundData_roundId_and_answeredInRound':0}
text=(P/'discovery/api3-index-js.raw').read_text(encoding='utf8')
m=re.search(r"pve=JSON.parse\(('(?:[^'\\]|\\.)*')\)",text)
catalog=json.loads(ast.literal_eval(m.group(1)))
cat={'source':'discovery/api3-index-js.raw','row_count':len(catalog),'ETH_USD':[v for v in catalog if v.get('name')=='ETH/USD'],'ZZZ_matches':[v for v in catalog if 'ZZZ'in json.dumps(v).upper()or'7dbf38976f6d3b9c529e7d9484a71898b409ee6a'in json.dumps(v).lower()]}
save('api3-catalog-extracted.json',cat)
offers=read('api3-pricing/api3-eth-offers.raw');print('offer_keys',list(offers));print(json.dumps(offers,indent=2)[:4000])
print('api3_catalog',json.dumps(cat))
save('decoded-findings.json',res)
print(json.dumps({k:v for k,v in res.items()if k!='runtime_pins'},indent=2))
