"""One serialized, bounded, read-only Robinhood market refresh. No adoption."""
from pathlib import Path
from fractions import Fraction
import datetime as dt,gzip,hashlib,json,sys,time,threading,urllib.request,urllib.error
R=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E=Path(__file__).resolve().parent;OUT=E/'capture'
sys.path.insert(0,str(R))
from zzz_ops.abi import keccak256
URL='https://robinhood.rpc.pinax.network'
GENESIS='0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c'
MAX_CALLS=33;MAX_SECONDS=90;INTERVAL=2;MAX_REPLY=262144;TIMEOUT=12
ZERO='0x'+'0'*40;ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
SELECTED='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
CORE='0x8366a39cc670b4001a1121b8f6a443a643e40951';VIEW='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
QUOTER='0x8dc178efb8111bb0973dd9d722ebeff267c98f94'
CL='0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9';CL2='0x5058adee53b04e374d8bedbad634bc4778f50b22'
PYTH='0x8250f4af4b972684f7b336503e2d6dfedeb1487a';API3='0x3c57b17052bdd5ff75b1f03c5f3afddbcfb8de1c'
ETH_ID='0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
OLD=R/'reports/predeployment-qualification-20261113/markets'
PRIOR=json.loads(gzip.decompress((OLD/'CAPTURE_PARTIAL.json.gz').read_bytes()))
POOLS=json.loads((R/'reports/market-followup-20261109/routes/v4-state.json').read_bytes())
def require(ok,reason):
    if not ok:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,value):
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    with (OUT/name).open('wb')as f:f.write(raw)
def word(v):return (int(v,16)if type(v)is str else v%(1<<256)).to_bytes(32,'big')
def vals(value,count=None):
    require(type(value)is str and value.startswith('0x')and (len(value)-2)%64==0,'Noncanonical ABI words')
    result=[int(value[i:i+64],16)for i in range(2,len(value),64)]
    require(count is None or len(result)==count,'Wrong exact ABI length');return result
def frac(value):return {'numerator':str(value.numerator),'denominator':str(value.denominator),'decimal':f'{value.numerator/value.denominator:.18g}'}
def protocol_fee(p,direction):return (p['slot0']['protocolFee']&4095)if direction else (p['slot0']['protocolFee']>>12)
def fee(p,direction):
    protocol=protocol_fee(p,direction);lp=p['slot0']['lpFee'];require(protocol<=1000 and lp<1000000,'Unrecognized directional fee')
    return protocol+lp-protocol*lp//1000000
class Stop(Exception):pass
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):fp.close();raise Stop('provider_redirect_refused')
class Capture:
    def __init__(self):self.rows=[];self.start=None;self.last=None;self.stopped=False;self.block=None
    def rpc(self,method,params,label,closure=False):
        require(method in ('eth_chainId','eth_getBlockByNumber','eth_getCode','eth_getStorageAt','eth_call'),'Read-only method boundary')
        require(not self.stopped,'Provider already stopped')
        if self.start is None:self.start=time.perf_counter()
        remaining=MAX_SECONDS-(time.perf_counter()-self.start)
        wait=max(0,INTERVAL-(time.perf_counter()-self.last))if self.last is not None else 0
        reserve=0 if closure else TIMEOUT
        if len(self.rows)>=MAX_CALLS or remaining<=wait+reserve+.05:raise Stop('original_work_budget_preserves_closure')
        if wait:time.sleep(wait)
        remaining=MAX_SECONDS-(time.perf_counter()-self.start)
        request={'jsonrpc':'2.0','id':len(self.rows)+1,'method':method,'params':params};body=json.dumps(request).encode()
        timeout_budget=min(TIMEOUT,remaining-reserve)
        row={'id':request['id'],'label':label,'request':json.loads(body),'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'timeout_seconds':timeout_budget};self.rows.append(row)
        try:
            req=urllib.request.Request(URL,body,{'Content-Type':'application/json','User-Agent':'PoPL-readonly-market-refresh/1'})
            # One daemon request worker at a time. The supervisor caps the WHOLE
            # HTTP operation (DNS, headers and body), including slow-drip replies.
            # On timeout this phase stops permanently; no later request/thread
            # is launched. Process exit terminates any timed-out daemon worker.
            done=threading.Event();outcome={}
            def perform():
                self.last=time.perf_counter();row['started_elapsed_seconds']=self.last-self.start
                try:
                    with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirects).open(req,timeout=timeout_budget)as response:
                        outcome['raw']=response.read(MAX_REPLY+1);outcome['http_status']=response.status;outcome['headers']={k:response.headers[k]for k in ('Date','Retry-After')if response.headers.get(k)is not None}
                except BaseException as exc:outcome['error']=exc
                finally:done.set()
            worker=threading.Thread(target=perform,daemon=True);worker.start()
            if not done.wait(timeout_budget):self.stopped=True;raise Stop('absolute_http_deadline_no_retry')
            if 'error'in outcome:raise outcome['error']
            raw=outcome['raw'];row.update(http_status=outcome['http_status'],headers=outcome['headers'])
            require(len(raw)<=MAX_REPLY,'Response exceeds original256KiB bound')
            name=f'rpc-{request["id"]:02d}.raw';(OUT/name).write_bytes(raw);row.update(raw_file=name,raw_sha256=sha(raw),raw_bytes=len(raw))
            result=json.loads(raw);require(type(result)is dict and result.get('jsonrpc')=='2.0'and type(result.get('id'))is int and result['id']==request['id']and ('result'in result)!=('error'in result),'Invalid JSON-RPC envelope')
            row['response']=json.loads(raw)
            if 'error'in result:
                err=result['error'];code=err.get('code')if type(err)is dict else None;message=err.get('message','')if type(err)is dict else ''
                if code in (-32005,-32029,-32601)or type(message)is str and any(x in message.lower()for x in ('rate limit','too many requests','request limit')):self.stopped=True;raise Stop('provider_work_or_method_refusal')
                return {'rpc_error':err}
            return result['result']
        except urllib.error.HTTPError as exc:
            row.update(http_status=exc.code,error_class='HTTPError',headers={k:exc.headers[k]for k in ('Date','Retry-After')if exc.headers.get(k)is not None});exc.close();self.stopped=True;raise Stop('provider_http_refusal')
        except Exception as exc:
            row.setdefault('error_class',type(exc).__name__)
            if not isinstance(exc,Stop)or str(exc)!='original_work_budget_preserves_closure':self.stopped=True
            raise
        finally:
            row['finished_elapsed_seconds']=time.perf_counter()-self.start
            save('RPC.json',{'endpoint':URL,'read_only':True,'retries':0,'maximum_calls':MAX_CALLS,'maximum_seconds':MAX_SECONDS,'actual_start_interval_seconds':INTERVAL,'maximum_response_bytes':MAX_REPLY,'rows':self.rows})
    def call(self,target,signature,args=(),label=None,data=None,gas=500000):
        encoded=data or '0x'+(keccak256(signature.encode())[:4]+b''.join(word(a)for a in args)).hex()
        return self.rpc('eth_call',[{'to':target,'data':encoded,'gas':hex(gas)},self.block],label or signature)
    def code(self,target,label,expected):
        value=self.rpc('eth_getCode',[target,self.block],label+'.runtime');require(type(value)is str and value.startswith('0x')and len(value)%2==0,'Invalid runtime hex')
        raw=bytes.fromhex(value[2:]);observed={'address':target,'bytes':len(raw),'keccak256':'0x'+keccak256(raw).hex(),'expected_prior_keccak256':expected,'matches_prior_runtime':'0x'+keccak256(raw).hex()==expected}
        require(observed['matches_prior_runtime'],'Runtime changed; source/layout interpretation stopped');return observed

def main():
    OUT.mkdir(exist_ok=False);c=Capture();result={'source_baseline':'519ff4f075022f789f46facbab56f0a944705b11','production_approved':False,'deployable_configuration':False,'canonical_final_recheck':False,'feeds':{},'runtimes':{},'quotes':[],'prior_anchor':PRIOR['anchor'],'prior_pool_inventory_sha256':sha((R/'reports/market-followup-20261109/routes/v4-state.json').read_bytes()),'zzz_decimal_provenance':'18from prior authenticated fixed implementation/getter. Current exactruntimehash must match; no arbitrary token-label inference.','public_transactions':0,'source_or_settings_changes':False}
    source_files=['zzz_ops/abi.py','src/ZZZOracle.sol','src/ZZZV4SpotPriceFeed.sol','src/ZZZPoolRegistry.sol','src/ZZZLPBalanceMath.sol','src/ZZZLPBalancer.sol','node_modules/@uniswap/v4-core/src/libraries/StateLibrary.sol','node_modules/@uniswap/v4-core/src/libraries/ProtocolFeeLibrary.sol','node_modules/@uniswap/v4-periphery/src/lens/V4Quoter.sol']
    save('SOURCE_PINS.json',{p:sha((R/p).read_bytes())for p in source_files});save('PLAN.json',{'maximum_calls':33,'maximum_seconds':90,'interval_seconds':2,'timeout_seconds':12,'response_bytes':262144,'retries':0,'quote_input_scope':'Full nominal$100/$5-sized ETH inputs are diagnostics, never assumed protocol swap fractions; reverse1000ZZZ has no qualifiedUSD label.','runtime_and_old_source_provenance':str(OLD.relative_to(R)),'inventory_scope':'95historically authenticated poolkeys; no global-highest/TVL/completeness claim'})
    try:
        require(c.rpc('eth_chainId',[],'chain')=='0x1237','Wrong chain')
        require(c.rpc('eth_getBlockByNumber',['0x0',False],'independent-genesis')['hash']==GENESIS,'Independent genesis pin mismatch')
        header=c.rpc('eth_getBlockByNumber',['latest',False],'fresh-anchor');require(abs(time.time()-int(header['timestamp'],16))<=120,'Stale/future head')
        c.block={'blockHash':header['hash'],'requireCanonical':True};result['anchor']={'chain_id':4663,'number':int(header['number'],16),'hash':header['hash'],'timestamp':int(header['timestamp'],16),'selector':c.block,'header':header};save('ANCHOR.json',result['anchor'])
        for label,target in (('core',CORE),('state_view',VIEW),('quoter',QUOTER),('zzz',ZZZ)):result['runtimes'][label]=c.code(target,label,PRIOR['runtimes'][label]['keccak256'])
        slots=[]
        for p in POOLS:
            require('0x'+keccak256(b''.join(word(x)for x in p['key'])).hex()==p['poolId']and p['key'][0]==ZERO and p['key'][1].lower()==ZZZ and p['key'][4]==ZERO and p['key'][2]<1000000,'Historical key not authenticated native static pool')
            n=int.from_bytes(keccak256(word(p['poolId'])+word(6)),'big');slots.extend([n,n+3])
        values=[]
        for i,start in enumerate(range(0,len(slots),50)):
            chunk=slots[start:start+50];data='0x'+(keccak256(b'extsload(bytes32[])')[:4]+word(32)+word(len(chunk))+b''.join(word(x)for x in chunk)).hex();v=vals(c.call(CORE,'',data=data,label=f'known95-bulk-{i}'))
            require(v[:2]==[32,len(chunk)]and len(v)==len(chunk)+2,'Bad canonical bulk layout');values+=v[2:]
        states=[]
        for i,p in enumerate(POOLS):
            packed,L=values[2*i:2*i+2];tick=(packed>>160)&0xffffff;tick-=1<<24 if tick&(1<<23)else 0
            s={'sqrtPriceX96':packed&((1<<160)-1),'tick':tick,'protocolFee':(packed>>184)&0xffffff,'lpFee':(packed>>208)&0xffffff}
            require(packed>>232==0 and 0<=L<1<<128 and s['sqrtPriceX96']>0 and s['lpFee']==p['key'][2],'Bad static-pool layout')
            states.append({'poolId':p['poolId'],'key':p['key'],'slot0':s,'active_liquidity':str(L),'reference_fee_only_candidate':s['lpFee']<1000000,'strict_principal_fee_only_candidate':s['lpFee']<100000})
        result['known_pool_states']=states
        for name,target in (('chainlink_primary',CL),('chainlink_secondary',CL2)):
            result['feeds'][name]={'address':target,'runtime':c.code(target,name,PRIOR['feeds'][name]['runtime']['keccak256']),'aggregator':c.call(target,'aggregator()',label=name+'.aggregator')}
        aggregator='0x'+word(vals(result['feeds']['chainlink_primary']['aggregator'],1)[0]).hex()[-40:]
        require(aggregator==PRIOR['feeds']['chainlink_aggregator']['address'],'Aggregator identity changed; requires separate review')
        result['feeds']['chainlink_aggregator']=c.code(aggregator,'chainlink_aggregator',PRIOR['feeds']['chainlink_aggregator']['runtime']['keccak256'])
        clraw=c.call(CL,'latestRoundData()',label='chainlink.primary.round');decraw=c.call(CL,'decimals()',label='chainlink.primary.decimals');result['feeds']['chainlink_primary'].update(latestRoundData=clraw,decimals=decraw)
        v=vals(clraw,5);dec=vals(decraw,1)[0];ts=result['anchor']['timestamp'];valid=0<v[0]<1<<80 and 0<v[1]<1<<255 and 0<v[2]<=v[3]<=ts and v[0]<=v[4]<1<<80 and 0<=dec<=18 and ts-v[3]<=86400 and Fraction(v[1]*10**18,10**dec)<=10**36
        eth_price=Fraction(v[1],10**dec)if valid else None;result['conditional_eth_usd']=None if eth_price is None else frac(eth_price)
        result['feeds']['chainlink_primary'].update(structurally_valid_hard_day=valid,age_seconds=ts-v[3],same_aggregator_as_secondary=result['feeds']['chainlink_primary']['aggregator']==result['feeds']['chainlink_secondary']['aggregator'],qualified_independent_pair=False)
        for name,target,signature,args in (('pyth',PYTH,'getPriceUnsafe(bytes32)',(ETH_ID,)),('api3',API3,'read()',())):
            prior=PRIOR['feeds'][name];row={'address':target,'runtime':c.code(target,name,prior['runtime']['keccak256'])};result['feeds'][name]=row
            slot='0x'+word(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1).hex();implementation=c.rpc('eth_getStorageAt',[target,slot,c.block],name+'.implementation-slot');row['implementation_slot']=implementation
            require(implementation==prior['implementation_slot'],'Proxy implementation changed; requires separate review')
            row['implementation_runtime']=c.code('0x'+implementation[-40:],name+'.implementation',prior['implementation_runtime']['keccak256']);row['observation']=c.call(target,signature,args,label=name+'.observation')
        selected=next(p for p in states if p['poolId']==SELECTED);reference=max((p for p in states if p['poolId']!=SELECTED and p['reference_fee_only_candidate']),key=lambda p:int(p['active_liquidity']))
        cheap=[p for p in states if p['poolId']not in (SELECTED,reference['poolId'])and p['strict_principal_fee_only_candidate']and fee(p,False)<10000]
        require(cheap,'No cheap fee-only diagnostic candidate')
        conversion=max(cheap,key=lambda p:(int(p['active_liquidity']),-fee(p,False)))
        result['quote_selection']={'selected':selected['poolId'],'largest_known_active_L_reference':reference['poolId'],'cheap_fee_only_conversion_lead':conversion['poolId'],'no_global_tvl_or_ownership_or_depth_claim':True}
        for label,p,nominal in (('selected',selected,100),('largest-known-active-L',reference,100),('cheap-fee-only',conversion,5)):
            for direction in (True,False):
                if direction and eth_price is None:continue
                amount=int(Fraction(nominal*10**18,1)/eth_price)if direction else 1000*10**18
                require(0<amount<1<<128,'Quote amount outside exact ABI')
                encoded='0x'+(keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+word(32)+b''.join(word(x)for x in p['key'])+word(int(direction))+word(amount)+word(256)+word(0)).hex()
                observed=c.call(QUOTER,'',data=encoded,label=f'quote.{label}.'+('ETH-to-ZZZ'if direction else 'ZZZ-to-ETH'))
                result['quotes'].append({'venue_label':label,'pool_id':p['poolId'],'key':p['key'],'zero_for_one':direction,'input_raw':str(amount),'nominal_USD_from_single_ETH_round_only':nominal if direction else None,'result':observed,'gas_ceiling':500000,'postspot':None,'qualified_usd':False,'known_directional_total_fee_pips':fee(p,direction)})
    except Exception as exc:
        result['stopped']={'exception_type':type(exc).__name__,'reason':str(exc)if isinstance(exc,(Stop,ValueError))else 'Transport failed; no retry','provider_stopped':c.stopped}
    finally:
        if result.get('anchor')and not c.stopped:
            try:
                h=c.rpc('eth_getBlockByNumber',[hex(result['anchor']['number']),False],'final-canonical-numbered-header',closure=True)
                result['canonical_final_recheck']=h==result['anchor']['header'];result['final_header']=h
            except Exception as exc:result['closure_failure']={'exception_type':type(exc).__name__,'provider_stopped':c.stopped}
        result['request_count']=len(c.rows);result['phase_elapsed_seconds']=None if c.start is None else time.perf_counter()-c.start
        result['safeguards_unchanged']={'source_agreement_bps':300,'contribution_total_bps':300,'minimum_marginal_lp_bps':9700,'conversion_total_bps':100,'additional_loss_bps':100,'maintenance_bps':300}
        result['source_pins_unchanged']=all(sha((R/p).read_bytes())==pin for p,pin in json.loads((OUT/'SOURCE_PINS.json').read_bytes()).items());save('CAPTURE.json',result)
        print(json.dumps({'requests':result['request_count'],'canonical':result['canonical_final_recheck'],'quotes':len(result['quotes']),'elapsed_seconds':result['phase_elapsed_seconds'],'stopped':result.get('stopped')}))
if __name__=='__main__':main()
