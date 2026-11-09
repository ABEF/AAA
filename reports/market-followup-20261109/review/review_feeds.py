"""Independent offline decoding and provenance-scope review of fresh feed evidence."""
import hashlib,json,pathlib,sys
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parent;F=ROOT.parent/'feeds'
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
def read(name):return json.loads((F/name).read_text(encoding='utf-8'))
def words(raw):
    assert isinstance(raw,str) and raw.startswith('0x') and (len(raw)-2)%64==0
    return [int(raw[i:i+64],16) for i in range(2,len(raw),64)]
def signed(n):return n-2**256 if n>=2**255 else n
out=read('FEED_FINDINGS.json');a=read('anchor-reads.json');follow=read('followup-reads.json')
manifest=read('artifact-sha256.json')
for name,pin in manifest.items():
    blob=(F/name).read_bytes()
    assert len(blob)==pin['bytes'] and hashlib.sha256(blob).hexdigest()==pin['sha256']
raw=a['reads'];t=a['anchor']['block_timestamp']
c=words(raw['chainlink-primary']['latestRoundData()']);p=words(raw['pyth-core']['getPriceUnsafe(bytes32)'])
assert len(c)==5 and len(p)==4 and 0<c[0]<2**80 and c[4]>=c[0] and c[1]>0 and 0<c[2]<=c[3]<=t
cp=Fraction(c[1],10**8);exp=signed(p[2]);pp=Fraction(signed(p[0]))*(Fraction(10)**exp)
assert out['chainlink']['age_seconds']==t-c[3]==133
assert out['pyth']['age_seconds']==t-p[3]==229537 and t-p[3]>86400
low=min(cp,pp);high=max(cp,pp)
assert (high-low)*10000>low*300
assert raw['chainlink-primary']['aggregator()']==raw['chainlink-secondary']['aggregator()']
assert out['eth_pair']['passes_300bps'] is False and out['qualification'] is False
pin_checks=[]
for label,record in raw.items():
    code=record.get('code')
    if isinstance(code,str):
        blob=bytes.fromhex(code[2:]);pin=out['runtime_pins'][label]
        assert pin['bytes']==len(blob) and pin['keccak256']=='0x'+keccak256(blob).hex()
        pin_checks.append(label)
assert out['api3']['ETH/USD']['data_feed_id']=='0x'+'0'*64
base=read('api3-base-retry.json');assert words(base['reads']['server_base'])==[0,0] and base['canonical_recheck'] is True
assert base['anchor']['block_hash']==a['anchor']['block_hash']
assert out['api3']['ZZZ/USD']['runtime_bytes']==0
source=(F/'discovery/api3-proxy-source.raw').read_text(encoding='utf-8')
assert 'roundId = answeredInRound = 0;' in source
offers=read('api3-pricing/api3-eth-offers.raw');proofs=[]
for leaf in offers['leaves']:
    name,chain,params,duration,price=leaf['value'];assert int(chain)==4663 and bytes.fromhex(name[2:]).rstrip(b'\x00')==b'ETH/USD'
    def word(n):return int(n).to_bytes(32,'big')
    dynamic=bytes.fromhex(params[2:]);assert len(dynamic)==96
    encoded=bytes.fromhex(name[2:])+word(chain)+word(5*32)+word(duration)+word(price)+word(len(dynamic))+dynamic
    node=keccak256(keccak256(encoded))
    for entry in leaf['proof']:
        peer=bytes.fromhex(entry[2:]);assert len(peer)==32
        node=keccak256(b''.join(sorted((node,peer))))
    valid='0x'+node.hex()==offers['merkleRoot'];assert valid;proofs.append(valid)
assert len(proofs)==5 and out['api3']['offers']['root_matches_shared_anchor'] is True
config=json.loads((ROOT/'chainlink-config-map-findings.json').read_text(encoding='utf-8'))['rows'][0]
assert out['chainlink']['current_config']['event']==config and out['chainlink']['current_config']['transmitters_match_current_getter'] is True
assert config['f']==3 and len(config['signers'])==10 and len(config['transmitters'])==10
overlap=out['literal_public_address_overlap']
for first,second,key in [('chainlink_admin_owners','api3_admin_owners','chainlink_admin_vs_api3_admin'),
                        ('chainlink_report_signers','pyth_verifier_keys','chainlink_report_signers_vs_pyth_keys')]:
    assert sorted(set(overlap[first])&set(overlap[second]))==overlap[key]
fresh=read('fresh-secondary-reads.json');assert fresh['canonical_recheck'] and fresh['secondary_anchor']['block_hash']!=a['anchor']['block_hash']
result={
 'review_type':'Independent internal evidence review; not external audit or source/operating approval.',
 'qualification':False,'feed_findings_sha256':hashlib.sha256((F/'FEED_FINDINGS.json').read_bytes()).hexdigest(),
 'manifest_payloads_verified':len(manifest),'manifest_mismatches':[],
 'shared_anchor':{'block_number':a['anchor']['block_number'],'hash':a['anchor']['block_hash'],'timestamp':t},
 'validated':['Exact primary/secondary Chainlink aggregator identity; canonical fiveword ETH round, 133s age.',
              'Pyth integer exponent/price decode and229537s age; exact lower-denominator agreement fails300bps.',
              'All'+str(len(pin_checks))+' initial runtime pins reproduce the raw code bytes.',
              'API3 original-anchor unset ETH name binding and base value/timestamp[0,0] mean unavailable observation, not zero USD.',
              'API3 pinned source returns roundId/answeredInRound0 and therefore cannot directly satisfy current Oracle; separate adapter work would preserve positive genuine timestamp.',
              'All5 API3 ETH offer proofs reconstruct the published/onchain anchor root; offers are not purchases, active publishers or full funding quotations.',
              'Exact Chainlink config event digest/count/transmitters match current shared-anchor getters; 10signers/10transmitters/f3.',
              'Literal public-address intersections match retained sets; distinct keys do not prove distinct people/upstream markets.',
              'Secondary liveness anchor remains explicitly separate and is not substituted into original market quotes.'],
 'assessment':'The feed findings correctly retain unqualified status. Fresh prices, code existence, published catalog/provider labels, offers and distinct administration keys are each weaker than the required independent correct-token USD pair and operating service.',
 'api3_offer_unit_assessment':'Pinned Api3MarketV2 lines646/866 compute dailyPrice=(price*1days)/duration; lines253-255 compare sponsor native balance+msg.value against expected sponsor balance. Thus price is total-duration native-wei funding parameter (ETH here), not USD or exact payable quote. Final required payment depends on sponsor balance, queue, rounding and gas. No purchase or funding was simulated or made.',
 'remaining':['No two qualified fixedZZZ/USD publications established. Exact-token CEX books are custom-upstream leads only and require USDT/USD plus manipulation/depth/publication review.',
              'No qualified independent ETH pair at either observed anchor; API3 inactive and direct ABI unsuitable; Pyth stale/authenticated updater funding missing.',
              'No correctchain Chainlink uptime feed listed; chain and upstream outage/grace policy remains unresolved.',
              'Explorer partial source verification and bytecode equality are not independent source recompilation. Real operator/reporting organizations and market inputs remain unqualified.',
              'Public RPC historic state failed while historic headers remained readable; one alternate provider success does not qualify archive or availability.']}
with (ROOT/'feed-independent-review-v2.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result,indent=2))
