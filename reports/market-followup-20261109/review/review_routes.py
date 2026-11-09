"""Independent offline integrity, integer band and floor review of captured evidence."""
import hashlib,json,math,pathlib
from fractions import Fraction
ROOT=pathlib.Path(__file__).resolve().parent
R=ROOT.parent/'routes'
def read(name):return json.loads((R/name).read_text(encoding='utf-8'))
manifest=read('PACKAGE_MANIFEST_v2.json')
if isinstance(manifest,dict): manifest=manifest.get('files',manifest.get('artifacts',manifest))
assert isinstance(manifest,list)
bad=[]
for row in manifest:
    path=R/row['path']
    if not path.exists() or path.stat().st_size!=row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:bad.append(row['path'])
assert not bad
states=read('v4-state.json');bands=read('common-reference-bands-v2.json');matrix=read('route-matrix-final-v2.json')
selected=next(p for p in states if p['poolId'].startswith('0x501122'))
m=10**18
lo=math.isqrt(95*m*m//100)
if lo*lo<95*m*m//100:lo+=1
hi=math.isqrt((105*m//100+1)*m-1)
step=2**32
def interval(s):
    # r=floor(S*m/R); floor(r*r/m) lies in [.95*m,1.05*m].
    lower=s*m//(hi+1)+1
    upper=s*m//lo
    return ((lower+step-1)//step*step,upper//step*step)
base=interval(selected['slot0']['sqrtPriceX96'])
checked=[];disagreements=[]
for p in states:
    a,b=interval(p['slot0']['sqrtPriceX96'])
    lower=max(a,base[0]);upper=min(b,base[1]);overlap=lower<=upper
    prior=next(row for row in bands['rows'] if row['poolId']==p['poolId'])
    if overlap!=prior['shared_reference_500bps_bands_overlap']:disagreements.append(p['poolId'])
    assert prior['principal_fee_compatible']==(p['key'][2]<100000)
    checked.append({'poolId':p['poolId'],'active':p['liquidity']>0,'principal_fee_compatible':p['key'][2]<100000,
                    'integer_reference_interval_nonempty':overlap,'common_referenceX96_min':lower,'common_referenceX96_max':upper})
assert not disagreements
passing=[row for row in matrix['rows'] if not row['zeroForOne'] and row.get('conditional_conversion_floor_only')]
assert passing and max(row['amountOut'] for row in passing)==36249908446
for row in matrix['rows']:
    expected=row['conditional_point_expected']
    required=(expected*9900+9999)//10000
    assert required==row['conditional_conversion_100bps_minimum']
    if row['zeroForOne']:assert row['conditional_conversion_floor_only'] is None
    elif 'amountOut' in row:assert row['conditional_conversion_floor_only']==(expected>0 and row['amountOut']>=required)
gas=read('gas-economy.json');assert gas['anchor_base_fee_per_gas_wei']*21000==421218000000
assert Fraction(gas['intrinsic_basefee_cost_to_largest_passing_output'])==Fraction(421218000000,36249908446)
capacity=read('small-capacity-quotes.json')
sel=[r for r in capacity if r['poolId']==selected['poolId']]
assert next(r for r in sel if r['amountIn']==388557)['amountOut']==1
assert 'error'in next(r for r in sel if r['amountIn']==388558)['response']
result={
 'review_type':'Independent internal evidence review; not external audit, source deployment or operating approval.',
 'qualification':False,'manifest_payloads_verified':len(manifest),'manifest_mismatches':bad,
 'strict_registry_fee_candidates':sum(p['key'][2]<100000 for p in states),
 'inclusive_balancer_fee_ceiling_states':sum(p['key'][2]<=100000 for p in states),
 'precision_correction':'Registry requires fee < maxSlippageBps*100 and maxSlippageBps<=1000; inactive exact100000fee pool is not principal admissible. Finalv2 records70 strict candidates versus71 inclusive Balancer ceiling states. Activeband conclusion unchanged.',
 'integer_band_derivation':'Registry <=500bps; relativeRoot=floor(S*1e18/R), relativePrice=floor(relativeRoot^2/1e18). Compute exact accepted relativeRoot integers, then intersect exact R intervals rounded to Oracle referenceX96 multiple2^32.',
 'accepted_relative_root_min':lo,'accepted_relative_root_max':hi,'states_checked':len(states),'band_classification_disagreements':disagreements,
 'active_principal_same_reference_candidates':[row['poolId'] for row in checked if row['active'] and row['principal_fee_compatible'] and row['integer_reference_interval_nonempty']],
 'continuous_band_summary':'max(P)/min(P)<=1.05/.95 is the continuous necessary bound; exact integer calculation agrees for all95 observed states. Lower-bound USD ratio is common for same token pair; no independent USD truth inferred.',
 'limits':['Bands are necessary pre-swap principal constraints with selected destination retained. They do not apply to the distinct earned converter or approve any source/setting.',
           'Tiny conditional1% passes exist; no global all-route conversion failure may be claimed. Largest observed passing output versus intrinsic gas is an anchor arithmetic diagnostic only.',
           '388557rawZZZ is a sampled exact current-range full-fill boundary with official response at388557 and rejection at388558; no absence of distant liquidity is inferred.',
           '23 successful outputs beyond captured words retain unavailable postspot; 19 other cheap zeroL errors are not relabelled as proven no liquidity.',
           '138main+13capacity exact replay checks and22successful200kgas rechecks overlap earlier quotes; counts are not independent acceptance tests.',
           'No complete current3% activation/growth/conversion, entitlement batching, target execution gas or operating acceptance was established.'],
 'guard_and_arithmetic_assessment':'Consistent with inspected current Oracle/Strategy/Registry/Balancer/Converter source and stated limited evidence. No production safeguard change or defect repair is required by these observations.',
 'state_intervals':checked}
with (ROOT/'route-independent-review-v2.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='state_intervals'},indent=2))
