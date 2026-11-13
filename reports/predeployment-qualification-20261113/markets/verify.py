"""Offline evidence integrity and interpretation checks only: no RPC/EVM/test suite."""
from pathlib import Path
from fractions import Fraction
import gzip
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
R=HERE.parents[2]
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256

def load(name):return json.loads((HERE/name).read_bytes())
def zipped(name):return json.loads(gzip.decompress((HERE/name).read_bytes()))
def words(s):
    assert isinstance(s,str) and s.startswith('0x') and (len(s)-2)%64==0
    return [int(s[i:i+64],16) for i in range(2,len(s),64)]
def word(n):return (int(n,16) if isinstance(n,str) else n).to_bytes(32,'big')
def fraction(o):return Fraction(int(o['numerator']),int(o['denominator']))

def main():
    manifest=load('manifest.json')
    for item in manifest['files']:
        p=HERE/item['path'];raw=p.read_bytes()
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],item['path']
    for item in load('SOURCE_BINDINGS.json')['files']:
        assert hashlib.sha256((R/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    initial=zipped('RPC.json.gz');closure=zipped('CLOSURE_RPC.json.gz')
    cap=zipped('CAPTURE_PARTIAL.json.gz');closed=zipped('CLOSURE.json.gz')
    result=load('RESULTS.json');candidate=load('CANDIDATE_CONFIG.json')
    index={(x['phase'],x['id']):x for x in load('RAW_INDEX.json')['raw']}
    anchor=cap['anchor'];selector=anchor['selector']
    assert anchor['chain_id']==4663 and selector=={'blockHash':anchor['hash'],'requireCanonical':True}
    counts={'results':0,'errors':0,'denials':0}
    for phase,log in [('initial',initial),('closure',closure)]:
        assert log['endpoint']=='https://robinhood.rpc.pinax.network' and log['read_only'] is True
        for i,row in enumerate(log['rows'],1):
            assert row['id']==i
            assert row['method'] in ('eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getStorageAt')
            if row['method'] in ('eth_call','eth_getCode','eth_getStorageAt'):assert row['params'][-1]==selector
            if 'response' not in row:
                assert phase=='initial' and row['id']==51 and row['http_status']==429
                counts['denials']+=1;continue
            item=index[(phase,i)];raw=gzip.decompress((HERE/item['path']).read_bytes())
            assert len(raw)==item['raw_bytes']==row['response_bytes']
            assert hashlib.sha256(raw).hexdigest()==item['raw_sha256']==row['response_sha256']
            wire=json.loads(raw);assert wire==row['response'] and wire['id']==i and wire['jsonrpc']=='2.0'
            assert ('result'in wire)!=('error'in wire)
            counts['results' if 'result'in wire else 'errors']+=1
            if row['method']=='eth_call':assert int(row['params'][0]['gas'],16)<=500000
    assert counts=={'results':53,'errors':4,'denials':1}
    assert len(initial['rows'])==51 and len(closure['rows'])==7 and len(index)==57
    assert hashlib.sha256(gzip.decompress((HERE/'RPC.json.gz').read_bytes())).hexdigest()==closure['original_capture_sha256']
    assert cap['complete'] is False and cap['canonical_final_recheck'] is False
    assert closed['canonical_closed'] is True and result['canonical_final_recheck'] is True
    assert all(h==anchor['header'] for h in (closed['header_before'],closed['header_after']))
    by_label={x['label']:x for x in initial['rows']}
    assert by_label['chain']['response']['result']=='0x1237'
    for key,expected in cap['runtimes'].items():
        raw=bytes.fromhex(by_label[key+'.runtime']['response']['result'][2:])
        assert len(raw)==expected['bytes'] and '0x'+keccak256(raw).hex()==expected['keccak256']
        assert expected['matches_prior_runtime'] is True
    for label,entry in [('chainlink_primary',cap['feeds']['chainlink_primary']['runtime']),('chainlink_secondary',cap['feeds']['chainlink_secondary']['runtime']),
                        ('chainlink_aggregator',cap['feeds']['chainlink_aggregator']['runtime']),('pyth',cap['feeds']['pyth']['runtime']),
                        ('pyth.implementation',cap['feeds']['pyth']['implementation_runtime']),('api3.implementation',cap['feeds']['api3']['implementation_runtime']),
                        ('api3-proxy',cap['feeds']['api3']['runtime'])]:
        runtime=bytes.fromhex(by_label[label+'.runtime']['response']['result'][2:])
        assert len(runtime)==entry['bytes'] and '0x'+keccak256(runtime).hex()==entry['keccak256']
    pools=json.loads((R/'reports/market-followup-20261109/routes/v4-state.json').read_bytes())
    assert len(pools)==len(cap['known_pool_states'])==95
    slots=[]
    for p in pools:
        assert '0x'+keccak256(b''.join(word(x) for x in p['key'])).hex()==p['poolId']
        slot=int.from_bytes(keccak256(word(p['poolId'])+word(6)),'big');slots.extend([slot,slot+3])
    raw_state=[]
    for i,start in enumerate(range(0,len(slots),50)):
        row=by_label['known-pool-slots-'+str(i)];chunk=slots[start:start+50]
        data='0x'+(keccak256(b'extsload(bytes32[])')[:4]+word(32)+word(len(chunk))+b''.join(word(x) for x in chunk)).hex()
        assert row['params'][0]['data']==data
        v=words(row['response']['result']);assert v[:2]==[32,len(chunk)] and len(v)==len(chunk)+2
        raw_state.extend(v[2:])
    for i,(old,p) in enumerate(zip(pools,cap['known_pool_states'])):
        packed,L=raw_state[i*2:i*2+2];tick=(packed>>160)&0xffffff
        if tick&(1<<23):tick-=1<<24
        state={'sqrtPriceX96':packed&((1<<160)-1),'tick':tick,'protocolFee':(packed>>184)&0xffffff,'lpFee':(packed>>208)&0xffffff}
        assert packed>>232==0 and L<1<<128 and state==p['slot0'] and L==p['liquidity']
        assert p['poolId']==old['poolId'] and p['key']==old['key'] and state['lpFee']==old['key'][2]
        assert p['strict_principal_fee_candidate']==(old['key'][2]<100000)
    assert sum(p['changed_since_nov9'] for p in cap['known_pool_states'])==8
    assert sum(bool(p['liquidity']) and p['strict_principal_fee_candidate'] for p in cap['known_pool_states'])==7
    selected=next(p for p in cap['known_pool_states'] if p['poolId']==candidate['selected_lp_pool_id'])
    assert selected['liquidity']==0
    assert words(by_label['stateview.liquidity.'+selected['poolId']]['response']['result'])==[0]
    assert int(closed['third_candidate_liquidity'])==int(closure['rows'][1]['response']['result'],16)
    physical=Fraction(selected['slot0']['sqrtPriceX96']**2,1<<192)
    for p in result['markets']['all_bands']:
        relative=Fraction(p['slot0']['sqrtPriceX96']**2,1<<192)/physical
        assert fraction(p['price_ratio_to_selected'])==relative
        assert p['common_reference_at_hard_500bps_possible']==(max(relative,1/relative)<=Fraction(105,95))
    feeds=cap['feeds'];cl=words(feeds['chainlink_primary']['latestRoundData()']);py=words(feeds['pyth']['getPriceUnsafe(bytes32)'])
    assert words(feeds['chainlink_primary']['aggregator()'])==words(feeds['chainlink_secondary']['aggregator()'])
    assert result['feeds']['chainlink']['age_seconds']==anchor['timestamp']-cl[3]==2235
    exponent=py[2]-(1<<256) if py[2]>>255 else py[2]
    first=Fraction(cl[1],10**8);second=Fraction(py[0])*Fraction(10)**exponent
    spread=abs(first-second)/min(first,second)*10000
    assert fraction(result['feeds']['pyth']['spread_vs_chainlink_bps'])==spread and spread>300
    assert result['feeds']['pyth']['age_seconds']==anchor['timestamp']-py[3]==541758
    assert words(feeds['api3']['base_feed'])==[0,0]
    assert feeds['api3']['read()']['rpc_error']['data']=='0x8086c764'
    qrows=closure['rows'][2:6]
    assert len(closed['quotes'])==len(result['quotes'])==len(qrows)==4
    for q,d,row in zip(closed['quotes'],result['quotes'],qrows):
        assert int(row['params'][0]['gas'],16)==q['gas_ceiling']==200000 and row['params'][0]['to'].lower()=='0x8dc178efb8111bb0973dd9d722ebeff267c98f94'
        expected='0x'+(keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+word(32)+b''.join(word(x) for x in q['key'])+word(int(q['zero_for_one']))+word(int(q['input_raw']))+word(256)+word(0)).hex()
        assert row['params'][0]['data']==expected and q['postspot'] is None and q['qualified_usd'] is False
        if isinstance(q['result'],str):
            v=words(q['result']);assert len(v)==2 and v==[int(q['amount_out_raw']),q['quoter_reported_gas']]
            p=next(p for p in cap['known_pool_states'] if p['poolId']==q['pool_id'])
            ratio=Fraction(p['slot0']['sqrtPriceX96']**2,1<<192)
            ideal=int(q['input_raw'])*(ratio if q['zero_for_one'] else 1/ratio)
            loss=(1-Fraction(v[0],1)/ideal)*10000
            assert fraction(d['conditional_own_spot_gross_loss_bps'])==loss and loss>300
            assert all(not x['passes_both'] for x in d['conditional_analytic_floors_at_own_initial_spot'].values())
        else:
            assert row['response']['error']==q['result']['rpc_error']
            raw=bytes.fromhex(q['result']['rpc_error']['data'][2:])
            assert raw[:4]==keccak256(b'UnexpectedRevertBytes(bytes)')[:4]
            assert int.from_bytes(raw[4:36],'big')==32
            n=int.from_bytes(raw[36:68],'big');assert len(raw)==68+((n+31)//32)*32 and not any(raw[68+n:])
            if q['pool_id']==selected['poolId']:
                assert n==36 and raw[68:72]==keccak256(b'NotEnoughLiquidity(bytes32)')[:4] and raw[72:104]==bytes.fromhex(selected['poolId'][2:])
            else:assert n==0
    assert result['quotes'][1]['error_decode']['classification']=='full_input_incomplete'
    assert result['quotes'][3]['error_decode']['classification']=='unavailable'
    assert candidate['production_approved'] is False and candidate['deployable_configuration'] is False
    assert candidate['eth_secondary'] is None and candidate['zzz_primary'] is None and candidate['zzz_secondary'] is None
    assert result['unchanged_safeguards']=={'contribution_total_bps':300,'minimum_marginal_deployed_lp_bps':9700,'conversion_total_bps':100,'maintenance_total_bps':300,'additional_execution_loss_bps':100,'source_agreement_bps':300,'principal_spot_hard_ceiling_bps':500}
    print(json.dumps({'status':'PASS','public_files':len(manifest['files']),'raw_rpc_responses':len(index),'attempts':58,'canonical_original_anchor_rechecked':True,'new_quotes':4,'network_calls':0,'evm_executions':0,'test_suites_executed':0}))

if __name__=='__main__':main()
