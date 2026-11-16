"""Verify captured market evidence offline. No RPC, EVM, compiler or test suite."""
from pathlib import Path,PurePosixPath
from fractions import Fraction
import argparse,gzip,io,hashlib,json,sys,zipfile
def require(ok,why):
    if not ok:raise ValueError(why)
class Reader:
    def __init__(self,path):
        self.path=Path(path).resolve();self.zip=zipfile.ZipFile(self.path)if self.path.is_file()else None
        if self.zip:
            rows=self.zip.infolist();names=[r.filename for r in rows];require(len(names)==len(set(names))and len(names)<=512 and sum(r.file_size for r in rows)<=20*1024*1024,'Unbounded/duplicate ZIP inventory')
            require(all(not PurePosixPath(n).is_absolute()and '..'not in PurePosixPath(n).parts and '\\'not in n for n in names),'Unsafe ZIP path')
    def raw(self,name):
        require(type(name)is str and not PurePosixPath(name).is_absolute()and '..'not in PurePosixPath(name).parts and '\\'not in name,'Unsafe member path')
        if self.zip:
            with self.zip.open(name)as f:raw=f.read(2*1024*1024+1)
        else:
            p=(self.path/name).resolve();require(p.is_relative_to(self.path),'Unsafe evidence directory path')
            with p.open('rb')as f:raw=f.read(2*1024*1024+1)
        require(len(raw)<=2*1024*1024,'Oversized evidence member');return raw
    def obj(self,name):return json.loads(self.raw(name))
def words(raw):
    require(type(raw)is str and raw.startswith('0x')and (len(raw)-2)%64==0,'Bad static ABI');return [int(raw[i:i+64],16)for i in range(2,len(raw),64)]
def frac(raw):return Fraction(int(raw['numerator']),int(raw['denominator']))
def word(raw):return (int(raw,16)if type(raw)is str else raw%(1<<256)).to_bytes(32,'big')
def relations(c,result,candidate,by):
    def wire(label):
        row=by[label]['response'];return row['result']if 'result'in row else {'rpc_error':row['error']}
    for obj in (c,result,candidate):require(obj['production_approved']is False and obj['deployable_configuration']is False,'Approval must remain false')
    a=c['anchor'];header=wire('fresh-anchor');final=wire('final-canonical-numbered-header')
    require(a['header']==header and c['final_header']==final==header and a['hash']==header['hash']and a['number']==int(header['number'],16)and a['timestamp']==int(header['timestamp'],16)and a['selector']=={'blockHash':header['hash'],'requireCanonical':True},'Embedded anchor lacks actual wire support')
    for obj in (result,candidate):require(obj['anchor']=={k:v for k,v in a.items()if k!='header'},'Derived anchor differs from captured anchor')
    feeds=c['feeds'];cl=feeds['chainlink_primary'];cl2=feeds['chainlink_secondary']
    require(cl['aggregator']==wire('chainlink_primary.aggregator')and cl2['aggregator']==wire('chainlink_secondary.aggregator')and cl['latestRoundData']==wire('chainlink.primary.round')and cl['decimals']==wire('chainlink.primary.decimals'),'Embedded Chainlink observation lacks wire support')
    require(feeds['chainlink_aggregator']['address']=='0x'+cl['aggregator'][-40:],'Aggregator binding differs')
    for name in ('pyth','api3'):require(feeds[name]['observation']==wire(name+'.observation')and feeds[name]['implementation_slot']==wire(name+'.implementation-slot'),'Embedded proxy/feed observation lacks wire support')
    require(result['feeds']['api3']['current_read']==feeds['api3']['observation'],'Derived API3 read differs')
    require(type(c['quotes'])is list and type(result['quotes'])is list and len(c['quotes'])==len(result['quotes'])==6,'Exactly six quoted observations are required')
    expected={(name,direction)for name in ('selected','largest-known-active-L','cheap-fee-only')for direction in (True,False)}
    require({(q['venue_label'],q['zero_for_one'])for q in c['quotes']}==expected,'Wrong/duplicate quoted venue directions')
    pools={p['poolId']:p for p in c['known_pool_states']};selection={'selected':'selected','largest-known-active-L':'largest_known_active_L_reference','cheap-fee-only':'cheap_fee_only_conversion_lead'}
    for q,d in zip(c['quotes'],result['quotes']):
        require(q['pool_id']==c['quote_selection'][selection[q['venue_label']]]and q['key']==pools[q['pool_id']]['key'],'Executed PoolKey differs from valued pool')
        label='quote.'+q['venue_label']+'.'+('ETH-to-ZZZ'if q['zero_for_one']else 'ZZZ-to-ETH')
        require(q['result']==wire(label)and all(d.get(k)==v for k,v in q.items()),'Embedded quote/result differs from actual wire')
        require(d['whole_operation_qualified']is False,'Point quote cannot qualify a whole operation')
def main():
    here=Path(__file__).resolve().parent;default=here/'evidence.zip'if (here/'evidence.zip').is_file()else here
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence',type=Path,default=default);parser.add_argument('--repo',type=Path);args=parser.parse_args()
    roots=[args.repo]if args.repo else [Path.cwd(),*Path(__file__).resolve().parents]
    repo=next((p.resolve()for p in roots if p is not None and (p/'zzz_ops/abi.py').is_file()),None);require(repo is not None,'Supply repository with --repo')
    require(hashlib.sha256((repo/'zzz_ops/abi.py').read_bytes()).hexdigest()=='154d92685b6e473bd064880ec15a16a9b8aafa0b9104df671538cf1375a7250d','Reviewed Keccak helper changed');sys.path.insert(0,str(repo));from zzz_ops.abi import keccak256
    e=Reader(args.evidence);manifest=e.obj('manifest.json')
    for row in manifest['files']:
        raw=e.raw(row['path']);require(len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'],'Evidence hash mismatch')
    c=e.obj('capture/CAPTURE.json');result=e.obj('RESULTS.json');primary=e.obj('capture/RPC.json');anchor=c['anchor'];selector=anchor['selector'];require(c['canonical_final_recheck']and c['final_header']==anchor['header'],'Unclosed primary anchor')
    require(result['production_approved']is False and result['deployable_configuration']is False and e.obj('CANDIDATE_CONFIG.json')['deployable_configuration']is False,'Approval must remain false')
    total=0;errors=0
    for phase,count in (('capture',33),('discovery',3),('discovery-gap',3)):
        log=e.obj(phase+'/RPC.json');require(log['endpoint']=='https://robinhood.rpc.pinax.network'and log['read_only']is True and log['retries']==0 and len(log['rows'])==count,'Wrong phase/method budget')
        for i,row in enumerate(log['rows'],1):
            raw=e.raw(phase+'/'+row['raw_file']);require(hashlib.sha256(raw).hexdigest()==row['raw_sha256']and len(raw)<=262144 and json.loads(raw)==row['response'],'Raw response mismatch')
            request=row['request'];require(request['id']==i and row['response']['id']==i and row['http_status']==200 and row['finished_elapsed_seconds']<=90,'Envelope/time boundary')
            if i>1:require(row['started_elapsed_seconds']-log['rows'][i-2]['started_elapsed_seconds']>=2,'Actual HTTP pacing')
            if request['method']in ('eth_call','eth_getCode','eth_getStorageAt'):require(phase=='capture'and request['params'][-1]==selector,'Mixed state anchor')
            require(request['method']in ('eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getStorageAt','eth_getLogs'),'Unexpected write/method');errors+=int('error'in row['response']);total+=1
    by={r['label']:r for r in primary['rows']};require(len(by)==33,'Duplicate primary labels');relations(c,result,e.obj('CANDIDATE_CONFIG.json'),by)
    if e.zip:
        for name in ('RESULTS.json','CANDIDATE_CONFIG.json'):
            sibling=e.path.parent/name
            if sibling.is_file():
                with sibling.open('rb')as stream:standalone=stream.read(2*1024*1024+1)
                require(standalone==e.raw(name),'Standalone report snapshot differs from ZIP member')
    require(by['chain']['response']['result']=='0x1237'and by['independent-genesis']['response']['result']['hash']=='0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c','Chain/genesis')
    with gzip.GzipFile(fileobj=io.BytesIO(e.raw('provenance/Nov13-CAPTURE.json.gz')))as stream:prior_raw=stream.read(2*1024*1024+1)
    require(len(prior_raw)<=2*1024*1024,'Unbounded prior provenance');prior=json.loads(prior_raw)
    runtime_pins=[(label,pin,prior['runtimes'][label]['keccak256'])for label,pin in c['runtimes'].items()]
    runtime_pins.extend((name,c['feeds'][name]['runtime'],prior['feeds'][name]['runtime']['keccak256'])for name in ('chainlink_primary','chainlink_secondary','pyth','api3'))
    runtime_pins.append(('chainlink_aggregator',c['feeds']['chainlink_aggregator'],prior['feeds']['chainlink_aggregator']['runtime']['keccak256']))
    runtime_pins.extend((name+'.implementation',c['feeds'][name]['implementation_runtime'],prior['feeds'][name]['implementation_runtime']['keccak256'])for name in ('pyth','api3'))
    for label,pin,expected in runtime_pins:
        row=by[label+'.runtime'];raw=bytes.fromhex(row['response']['result'][2:]);require(row['request']['params'][0]==pin['address']and len(raw)==pin['bytes']and '0x'+keccak256(raw).hex()==pin['keccak256']==expected,'Runtime changed before semantic interpretation')
    pools=c['known_pool_states'];require(len(pools)==95 and len({p['poolId']for p in pools})==95,'Wrong known pool inventory');slots=[]
    for p in pools:
        require('0x'+keccak256(b''.join(word(x)for x in p['key'])).hex()==p['poolId'],'PoolKey hash');slot=int.from_bytes(keccak256(word(p['poolId'])+word(6)),'big');slots.extend((slot,slot+3))
    packed=[]
    for i,start in enumerate(range(0,len(slots),50)):
        chunk=slots[start:start+50];r=by[f'known95-bulk-{i}'];expected='0x'+(keccak256(b'extsload(bytes32[])')[:4]+word(32)+word(len(chunk))+b''.join(word(x)for x in chunk)).hex();require(r['request']['params'][0]['data']==expected,'Bulk storage selection');v=words(r['response']['result']);require(v[:2]==[32,len(chunk)]and len(v)==len(chunk)+2,'Bulk ABI');packed+=v[2:]
    for i,p in enumerate(pools):
        v,L=packed[2*i:2*i+2];s=p['slot0'];tick=(v>>160)&0xffffff;tick-=1<<24 if tick&(1<<23)else 0
        require(v>>232==0 and L<1<<128 and int(p['active_liquidity'])==L and s=={'sqrtPriceX96':v&((1<<160)-1),'tick':tick,'protocolFee':(v>>184)&0xffffff,'lpFee':(v>>208)&0xffffff}and s['lpFee']==p['key'][2],'State/fee decode')
    cl=words(c['feeds']['chainlink_primary']['latestRoundData']);dec=words(c['feeds']['chainlink_primary']['decimals'])[0];eth=Fraction(cl[1],10**dec);require(frac(result['feeds']['chainlink']['usd'])==eth and c['feeds']['chainlink_primary']['aggregator']==c['feeds']['chainlink_secondary']['aggregator'],'ETH price/independence')
    py=words(c['feeds']['pyth']['observation']);exp=py[2]-(1<<256)if py[2]>>255 else py[2];pyprice=Fraction(py[0])*Fraction(10)**exp
    require(frac(result['feeds']['pyth']['stored_usd'])==pyprice and result['feeds']['pyth']['age_seconds']==anchor['timestamp']-py[3]and frac(result['feeds']['pyth']['spread_vs_chainlink_bps'])==abs(pyprice-eth)/min(pyprice,eth)*10000,'Pyth math')
    for q,d in zip(c['quotes'],result['quotes']):
        p=next(p for p in pools if p['poolId']==q['pool_id']);n=int(q['input_raw']);direction=q['zero_for_one'];fee=p['slot0']['protocolFee']&4095 if direction else p['slot0']['protocolFee']>>12;fee+=p['slot0']['lpFee']-fee*p['slot0']['lpFee']//1000000;require(fee==q['known_directional_total_fee_pips'],'Directional fee')
        row=by['quote.'+q['venue_label']+'.'+('ETH-to-ZZZ'if direction else 'ZZZ-to-ETH')];expected='0x'+(keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+word(32)+b''.join(word(x)for x in q['key'])+word(int(direction))+word(n)+word(256)+word(0)).hex();require(row['request']['params'][0]['data']==expected and int(row['request']['params'][0]['gas'],16)==500000 and q['qualified_usd']is False and q['postspot']is None,'Quote exact input/gas/scope')
        if type(q['result'])is str:
            v=words(q['result']);P=Fraction(p['slot0']['sqrtPriceX96']**2,1<<192);ideal=n*(P if direction else 1/P);net=ideal*Fraction(1000000-fee,1000000)
            require(len(v)==2 and int(d['amount_out_raw'])==v[0]and frac(d['conditional_own_spot_gross_loss_bps'])==(1-Fraction(v[0])/ideal)*10000 and frac(d['conditional_extra_loss_after_known_fee_bps'])==(1-Fraction(v[0])/net)*10000,'Analytical ownspot loss')
        else:
            error=q['result']['rpc_error'];b=bytes.fromhex(error['data'][2:]);require(b[:4]==keccak256(b'UnexpectedRevertBytes(bytes)')[:4]and int.from_bytes(b[4:36],'big')==32,'Unrecognized quote error wrapper');length=int.from_bytes(b[36:68],'big');require(len(b)==68+((length+31)//32)*32 and not any(b[68+length:]),'Malformed quote error')
            if length==36:require(b[68:72]==keccak256(b'NotEnoughLiquidity(bytes32)')[:4]and b[72:104]==bytes.fromhex(q['pool_id'][2:])and d['error_decode']['classification']=='exact_full_input_incomplete','Incorrect fullinput classification')
            else:require(length==0 and d['error_decode']['classification']=='empty_wrapped_revert_at_500k_unknown_cause','Unknown error falsely classified')
    topic='0x'+keccak256(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
    for phase,lo,hi,target in (('discovery',113296580,anchor['number'],anchor),('discovery-gap',110324512,113296579,c['prior_anchor'])):
        d=e.obj(phase+'/RESULT.json');rows=e.obj(phase+'/RPC.json')['rows'];query=rows[1]['request']['params'][0];require(d['canonical_closed']is True and d['new_pool_keys']==[] and rows[1]['response']['result']==[] and rows[1]['request']['method']=='eth_getLogs','Discovery result')
        require(int(query['fromBlock'],16)==lo and int(query['toBlock'],16)==hi and query['address']==c['runtimes']['core']['address']and query['topics']==[topic,None,'0x'+'0'*64,'0x'+'7dbf38976f6d3b9c529e7d9484a71898b409ee6a'.rjust(64,'0')],'Discovery range/topics')
        require(rows[0]['response']['result']==rows[2]['response']['result']==target['header'],'Discovery numbered canonical closure')
    print(json.dumps({'status':'PASS','public_files':len(manifest['files']),'actual_read_responses':total,'valid_results':total-errors,'explicit_rpc_errors':errors,'known_pool_states':95,'quote_diagnostics':6,'discovery_queries':2,'new_initializations_in_checked_intervals':0,'network_calls':0,'EVM_runs':0,'compiler_runs':0,'test_suites_rerun':0}))
if __name__=='__main__':main()
