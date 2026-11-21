"""New finite actual-core LP fee/reserve/current-owner claim partition only."""
from pathlib import Path
import argparse,copy,gzip,hashlib,io,json,sys,time,zipfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import driver_base as B
B.READS.add('debug_traceTransaction')
from eager_oracle import TwoLeaf
from zzz_ops.deployment_plan import Artifacts
from zzz_ops.abi import keccak256
V=B.V;ZERO=B.ZERO;ZZZ=B.ZZZ;OWNER=B.OWNER;BUYER='0x000000000000000000000000000000000000a0a7'
PRIOR=V/'pool-integration-20261120/entry/attempt1'
ENTRY_HASH='e56b8d78aba465c673aa0379e6a4214860189e935c133dafc7da8c46aa99d2ff'

def load(p):return json.loads(Path(p).read_bytes())
def save(p,x):
    with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(x,f,indent=2);f.write('\n')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def sig(s):return '0x'+keccak256(s.encode()).hex()
def selector(s):return sig(s)[:10]
def flat(frame):
    yield frame
    for c in frame.get('calls',[]):yield from flat(c)
def token_topic(x):return '0x'+x[-40:]

def authenticate():
    archive=ROOT/'reports/pool-integration-20261120/entry/evidence.zip';m=load(archive.with_name('EVIDENCE_MANIFEST.json'))
    assert sha(archive.read_bytes())==m['sha256']==ENTRY_HASH
    names=['owned-state.dump','owned-state-capture.json','construction/instances.json','STATES.json','ALL_SETUP_SCENARIO_RECEIPTS.json','HELPER_REUSE.json','relay/full-cache.json','upstream-wire.jsonl','DERIVED_SEED.json','PRIOR_CACHE_IMPORT.json','SOURCE_STAGE.json']
    names +=[x+'-trace.json'for x in('new_ETH_activation','new_ZZZ_activation','new_ETH_growth','new_ZZZ_growth')]
    with zipfile.ZipFile(archive)as z:
        for name in names:
            raw=z.read('attempt1/'+name);pin=m['members']['attempt1/'+name]
            assert len(raw)==pin['bytes']and sha(raw)==pin['sha256']and raw==(PRIOR/name).read_bytes(),name
    snapshot=(PRIOR/'owned-state.dump').read_bytes();capture=load(PRIOR/'owned-state-capture.json')
    assert sha(snapshot)==capture['sha256']=='b4c01efff093fa73d69c837d004c534f456a1776af8fb84dfb6043e69bda238a'and capture['no_pending']
    return snapshot,capture,m

class Node(B.Node):
    def send(self,label,to,data,value=0,sender=OWNER,cap=24_000_000,padding=2500):
        assert sender in(OWNER,BUYER)and cap in(12_000_000,24_000_000)and padding in(2000,2500)
        nonce=self.call('eth_getTransactionCount',[sender,'latest']);tx={'from':sender,'data':data,'value':hex(value),'gas':hex(cap)}
        if to:tx['to']=to
        simulation=self.call('eth_call',[tx,'latest']);assert isinstance(simulation,str)
        estimate=int(self.call('eth_estimateGas',[tx]),16);padded=(estimate*(10000+padding)+9999)//10000;assert padded<=cap
        tx['gas']=hex(padded);assert self.call('eth_call',[tx,'latest'])==simulation
        assert self.call('eth_getTransactionCount',[sender,'latest'])==nonce
        tx.update(nonce=nonce,gasPrice=self.call('eth_gasPrice'));self.pending='submission_uncertain'
        h=self.call('eth_sendTransaction',[tx]);self.pending=h
        receipt=None
        for _ in range(400):
            receipt=self.call('eth_getTransactionReceipt',[h])
            if receipt:break
            time.sleep(.05)
        assert receipt and int(receipt['status'],16)==1,(label,receipt)
        actual=self.call('eth_getTransactionByHash',[h]);assert actual['input']==data and actual['from']==sender and actual['to']==to and actual['nonce']==nonce
        assert actual['gas']==tx['gas']and actual['gasPrice']==tx['gasPrice']and int(actual['value'],16)==value and actual.get('chainId','0x1237')=='0x1237'
        assert receipt['transactionHash']==h and receipt['from']==sender and receipt['to']==to
        self.pending=None
        trace=self.call('debug_traceTransaction',[h,{'tracer':'callTracer'}]);assert not trace.get('error')
        trace_name='trace-'+label.replace(':','_')+'.json';save(B.OUT/trace_name,trace)
        row={'label':label,'submitted':copy.deepcopy(tx),'simulation':simulation,'receipt':receipt,'estimate':estimate,'padded_gas':padded,'cap':cap,'padding_bps':padding,'trace':trace_name};self.receipts.append(row)
        print(json.dumps({'label':label,'gas':int(receipt['gasUsed'],16),'estimate':estimate,'padded':padded}),flush=True)
        return row
    def clock(self):
        assert self.pending is None
        last=self.call('eth_getBlockByNumber',['latest',False]);stamp=int(last['timestamp'],16)
        self.call('evm_setNextBlockTimestamp',[stamp+1]);self.call('evm_mine',[])
        head=self.call('eth_getBlockByNumber',['latest',False]);pending=self.call('eth_getBlockByNumber',['pending',False]);assert int(head['timestamp'],16)==stamp+1 and int(pending['timestamp'],16)>=stamp+1
        return stamp+301

class Model:
    def __init__(self,roles,ids,bucket):
        self.roles=roles;self.ids=ids;self.bucket=bucket;self.owner=TwoLeaf();self.collective=TwoLeaf();self.allocated={ZERO:0,ZZZ:0};self.flushed={ZERO:0,ZZZ:0};self.unit={ZERO:0,ZZZ:0};self.dust={ZERO:0,ZZZ:0};self.claims=[]
    def replay(self,receipt):
        for log in receipt['logs']:
            a=log['address'];t=log['topics'];d=B.words(log['data'])
            if a==self.roles['rewards']:
                if t[0]==sig('ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)'):
                    ordinal,old,weight,total=d;assert self.ids[ordinal-1]==int(t[1],16)and int(t[2],16)==self.bucket
                    assert self.owner.weights[ordinal-1]==old;self.owner.weight(ordinal,weight);assert sum(self.owner.weights)==total
                elif t[0]==sig('CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)'):
                    ordinal,old,weight,total=d;assert self.ids[ordinal-1]==int(t[1],16)and self.collective.weights[ordinal-1]==old
                    self.collective.weight(ordinal,weight);assert sum(self.collective.weights)==total
                elif t[0]==sig('PoolRewardsCredited(uint256,address,uint256,uint256)'):
                    assert int(t[1],16)==self.bucket;token=token_topic(t[2]);assert token in(ZERO,ZZZ)
                    self.owner.credit(token,d[0]);self.collective.credit(token,d[1]);self.allocated[token]+=sum(d)
                elif t[0]==sig('Claimed(uint256,address,address,uint256)'):
                    i=self.ids.index(int(t[1],16))+1;token=token_topic(t[2]);amount=self.owner.take(token,i)+self.collective.take(token,i);assert amount==d[0]
                    self.claims.append({'nft':str(self.ids[i-1]),'token':token,'recipient':token_topic(t[3]),'amount':str(amount)})
            elif a==self.roles['fees']:
                if t[0]==sig('FeesAllocated(uint256,address,uint256,uint256)'):
                    assert int(t[1],16)==self.bucket;token=token_topic(t[2]);assert d[0]%20==0;self.unit[token]+=d[0]//20;self.dust[token]=d[1]
                elif t[0]==sig('MembershipDustSettled(uint256,address,uint256)'):
                    token=token_topic(t[2]);assert self.dust[token]==d[0];self.flushed[token]+=d[0];self.dust[token]=0

class Case:
    def __init__(self,n,out,roles,ids,bucket,model):self.n=n;self.out=out;self.r=roles;self.ids=ids;self.bucket=bucket;self.m=model;self.states=[];self.harvests=[];self.payouts=[]
    def read(self,role,signature,*args):return B.words(self.n.read(self.r.get(role,role),signature,*args))
    def balance(self,token,address):return int(self.n.call('eth_getBalance',[address,'latest']),16)if token==ZERO else self.read(ZZZ,'balanceOf(address)',address)[0]
    def state(self,label):
        group=self.read('vault','group(uint256)',self.bucket);main=group[1]
        row={'label':label,'head':self.n.call('eth_getBlockByNumber',['latest',False]),'group':group,'main':main,'L':self.read(B.POSM,'getPositionLiquidity(uint256)',main)[0],'ticks':self.read('liquidity','ticks(uint256)',main),'shares':[self.read('vault','sharesOf(uint256)',i)[0]for i in self.ids],'owners':['0x'+self.n.read(self.r['nft'],'ownerOf(uint256)',i)[-40:]for i in self.ids],'eligible':self.read('membership','totalEligible()')[0],'royalty_enrollment':self.read('royalty_rewards','activationCount()')[0],'assets':{}}
        for token in(ZERO,ZZZ):
            claims=[self.read('rewards','claimableComponents(uint256,address)',i,token)for i in self.ids]
            expected=[[self.m.owner.claim(token,o),self.m.collective.claim(token,o)]for o in(1,2)]
            assert claims==expected,('oracle mismatch',label,token,claims,expected)
            liability=self.read('rewards','liabilities(address)',token)[0];assert liability==sum(map(sum,claims))
            own=self.read('rewards','allocationTree(uint256)',self.bucket);shared=self.read('rewards','allocationTree(uint256)',0);index=1 if token==ZERO else 2
            assert own[index]==sum(x[0]for x in claims)and shared[index]==sum(x[1]for x in claims)
            fee={'dust':self.read('fees','dust(uint256,address)',self.bucket,token)[0],'compound':self.read('fees','compoundBalance(uint256,address)',self.bucket,token)[0],'buyback':self.read('fees','buybackBalance(address)',token)[0],'accounted':self.read('fees','accounted(address)',token)[0],'cash':self.balance(token,self.r['fees'])}
            assert fee['dust']==self.m.dust[token]and fee['accounted']==fee['cash']==fee['dust']+fee['compound']+fee['buyback']
            assert self.read('rewards','orphaned(address)',token)==[0]and self.read('rewards','directLiabilities(address)',token)==[0]
            rewards_cash=self.balance(token,self.r['rewards']);assert rewards_cash==liability
            row['assets'][token]={'claims':claims,'liabilities':liability,'rewards_cash':rewards_cash,'fees':fee,'vault_cash':self.balance(token,self.r['vault'])}
        assert row['eligible']==row['royalty_enrollment']==2 and sum(row['shares'])==self.read('vault','bucketTotalShares(uint256)',self.bucket)[0]
        assert row['shares']==self.m.owner.weights and self.m.collective.weights==[1,1]
        assert self.read('rewards','allocationTree(uint256)',self.bucket)[0]==sum(row['shares']) and self.read('rewards','allocationTree(uint256)',0)[0]==2
        assert '0x'+self.n.read(B.POSM,'ownerOf(uint256)',main)[-40:]==self.r['vault']
        if self.states:
            first=self.states[0];assert row['group']==first['group']and row['main']==first['main']and row['L']==first['L']and row['ticks']==first['ticks']and row['shares']==first['shares']
        self.states.append(row);save(self.out/f'state-{len(self.states):02d}.json',row);return row
    def send(self,label,role,signature,*args,value=0,sender=OWNER,claim=False):
        row=self.n.send(label,self.r.get(role,role),B.abi(signature,*args),value,sender,12_000_000 if claim else 24_000_000,2000 if claim else 2500);self.m.replay(row['receipt']);return row
    def harvest(self,label,expect_positive):
        before=self.state(label+':before');deadline=self.n.clock();r=self.send(label,'vault','collectFees(uint256,uint256)',self.bucket,deadline);after=self.state(label+':after')
        logs=[x for x in r['receipt']['logs']if x['address']==self.r['vault']and x['topics'][0]==sig('FeesCollected(uint256,uint256,uint256)')];assert len(logs)==1 and int(logs[0]['topics'][1],16)==self.bucket
        amounts=B.words(logs[0]['data']);assert any(amounts)if expect_positive else amounts==[0,0]
        for token,amount in zip((ZERO,ZZZ),amounts):
            old=before['assets'][token];new=after['assets'][token];units,dust=divmod(old['fees']['dust']+amount,20)
            assert new['fees']['dust']==dust and new['fees']['compound']-old['fees']['compound']==units and new['fees']['buyback']-old['fees']['buyback']==units
            assert new['liabilities']-old['liabilities']==18*units
            assert new['rewards_cash']-old['rewards_cash']==18*units
            assert new['fees']['cash']-old['fees']['cash']==amount-18*units
            assert new['vault_cash']==old['vault_cash']
            assert new['fees']['cash']+new['rewards_cash']-old['fees']['cash']-old['rewards_cash']==amount
            if not amount:assert new==old
        self.harvests.append({'label':label,'transaction_hash':r['receipt']['transactionHash'],'actual_receipts':list(map(str,amounts)),'before':before['assets'],'after':after['assets']})
        return r
    def claim(self,label,index,token,sender):
        before=self.state(label+':before');fee_before=before['assets'][token]['fees'];amount=sum(before['assets'][token]['claims'][index]);cash=self.balance(token,sender)
        assert before['owners'][index]==sender
        r=self.send(label,'rewards','claim(uint256,address)',self.ids[index],token,sender=sender,claim=True);assert int(r['simulation'],16)==amount
        events=[x for x in r['receipt']['logs']if x['address']==self.r['rewards']and x['topics'][0]==sig('Claimed(uint256,address,address,uint256)')]
        assert len(events)==1 and int(events[0]['topics'][1],16)==self.ids[index]and token_topic(events[0]['topics'][2])==token and token_topic(events[0]['topics'][3])==sender and B.words(events[0]['data'])==[amount]
        after_cash=self.balance(token,sender);gas=int(r['receipt']['gasUsed'],16)*int(r['receipt']['effectiveGasPrice'],16)
        assert after_cash==cash+amount-(gas if token==ZERO else 0)
        after=self.state(label+':after');assert after['assets'][token]['claims'][index]==[0,0]and after['assets'][token]['fees']==fee_before
        self.payouts.append({'label':label,'hash':r['receipt']['transactionHash'],'nft':str(self.ids[index]),'token':token,'recipient':sender,'amount':str(amount),'recipient_before':str(cash),'recipient_after':str(after_cash),'local_execution_gas_cost':str(gas),'complete_target_fee_qualified':False})
        return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);args=p.parse_args();assert args.attempt.isalnum()
    out=V/'pool-fees-20261121/run'/args.attempt;out.mkdir(parents=True,exist_ok=False);B.OUT=out
    for name in('run_fees.py','driver_base.py','warm_cache.py','eager_oracle.py'):(out/('source-'+name)).write_bytes((HERE/name).read_bytes())
    snapshot,capture,manifest=authenticate();artifacts=Artifacts();artifacts.check_sources()
    with gzip.GzipFile(fileobj=io.BytesIO(snapshot))as compressed:derived=compressed.read(16*1024*1024+1)
    assert len(derived)<=16*1024*1024 and isinstance(json.loads(derived),dict)
    with (out/'restore-state.json').open('xb')as f:f.write(derived)
    save(out/'RESTORE_INPUT.json',{'compressed_source_sha256':sha(snapshot),'derived_state_sha256':sha(derived),'derived_bytes':len(derived),'decompressed_bound_bytes':16*1024*1024,'transport':'CLI --load-state new owned node only','RPC_request_limit_unchanged':True})
    instances=load(PRIOR/'construction/instances.json');roles={x['role']:x['address']for x in instances};priorstates=load(PRIOR/'STATES.json');last=priorstates[-1];ids=list(map(int,last['ids']));bucket=int(last['bucket']);assert len(ids)==2
    model=Model(roles,ids,bucket);prefix=load(PRIOR/'ALL_SETUP_SCENARIO_RECEIPTS.json')
    for r in prefix:model.replay(r['receipt'])
    released={ZERO:0,ZZZ:0}
    for name in('new_ETH_activation','new_ZZZ_activation','new_ETH_growth','new_ZZZ_growth'):
        for frame in flat(load(PRIOR/(name+'-trace.json'))):
            if frame.get('to')==roles['fees']and frame.get('input','').startswith(selector('releaseCompound(uint256,address)')):
                a=B.words('0x'+frame['input'][10:]);assert a[0]==bucket;released['0x'+hex(a[1])[2:].zfill(40)]+=B.words(frame['output'])[0]
    helper=load(PRIOR/'HELPER_REUSE.json');fixture=V/'fresh-entry3-rehearsal-fixture-compile-subagent1';raw=(fixture/'fixture-compiler-stdout.json').read_bytes();inp=(fixture/'fixture-compiler-input.json').read_bytes()
    assert sha(raw)==helper['fixture_output_sha256']and sha(inp)==helper['fixture_input_sha256'];compiled=json.loads(raw);trader=compiled['contracts']['test/local/Source9RehearsalFixtures.sol']['Source9RehearsalTrader']
    source=(ROOT/'test/local/Source9RehearsalFixtures.sol').read_bytes();assert sha(source)==helper['source_sha256']
    feedrow,=[r for r in prefix if r['label']=='helper:eth_feed_a'];feed=feedrow['receipt']['contractAddress']
    save(out/'INPUT_PROVENANCE.json',{'prior_archive_sha256':ENTRY_HASH,'prior_snapshot_sha256':sha(snapshot),'source_sha256':artifacts.source_pins,'build_pins':artifacts.file_pins,'fixture_helper_reused':helper,'prefix_receipts_replayed':len(prefix),'prior_compound_released':{k:str(v)for k,v in released.items()},'production_approved':False})
    case=None
    try:
      with B.cached_fork_provider(B.PUBLIC_ENDPOINT,B.BLOCK,B.HASH,out/'relay',requests_per_second=.5)as relay:
       with Node(relay.url)as n:
        restored=n.call('eth_getBlockByNumber',['latest',False]);assert all(restored[k]==capture['block'][k]for k in('hash','number','stateRoot','timestamp'))
        pending=n.call('eth_getBlockByNumber',['pending',False]);n.clock();head=n.call('eth_getBlockByNumber',['latest',False]);save(out/'RESTORED_CLOCK.json',{'restored_head':restored,'pending_before':pending,'repaired_head':head,'owned_only':True})
        assert int(n.read(roles['access'],'isSealed()'),16)==1 and int(n.read(roles['nft'],'mintedCount()'),16)==2
        for instance in instances:
            code=n.call('eth_getCode',[instance['address'],'latest']);assert '0x'+keccak256(bytes.fromhex(code[2:])).hex()==instance['runtime_keccak256']
        case=Case(n,out,roles,ids,bucket,model);baseline=case.state('restored_baseline')
        for token in(ZERO,ZZZ):
            fees=baseline['assets'][token]['fees'];assert fees['buyback']==model.unit[token]and fees['compound']==model.unit[token]-released[token]
        for index,identifier in enumerate(ids,1):assert case.read('nft','mintOrdinalOf(uint256)',identifier)==[index]
        n.call('anvil_impersonateAccount',[OWNER]);n.call('anvil_impersonateAccount',[BUYER]);assert n.call('eth_getCode',[BUYER,'latest'])=='0x';n.call('anvil_setBalance',[BUYER,hex(10**18)])
        creation=n.send('setup:external_fee_trader',None,'0x'+trader['evm']['bytecode']['object']);trader_address=creation['receipt']['contractAddress'];roles['trader']=trader_address
        def trade(label,direction,amount):
            before=case.balance(ZZZ,OWNER)
            r=case.send(label,'trader','execute(bool,uint256,uint256,uint160)',direction,amount,1,4295128740 if direction else 1461446703485210103287273052203988822378723970341,value=amount if direction else 0)
            output=int(r['simulation'],16);assert output>0
            assert case.balance(ZZZ,trader_address)==0 and case.balance(ZERO,trader_address)==0
            if direction:assert case.balance(ZZZ,OWNER)==before+output
            return output
        received=trade('new:external_native_to_ZZZ',True,10**15)
        case.send('setup:approve_exact_reverse','zzz'if'zzz'in roles else ZZZ,'approve(address,uint256)',trader_address,received//2)
        trade('new:external_ZZZ_to_native',False,received//2)
        assert case.read(ZZZ,'allowance(address,address)',OWNER,trader_address)==[0]
        case.harvest('new:collect_actual_both_asset_fees',True);case.harvest('new:repeat_collection_no_fee',False)
        case.claim('new:partial_ETH_claim',0,ZERO,OWNER)
        case.send('new:transfer_NFT_to_second_owner','nft','transferFrom(address,address,uint256)',OWNER,BUYER,ids[0])
        assert case.state('after_transfer')['owners']==[BUYER,OWNER]
        now=int(n.call('eth_getBlockByNumber',['latest',False])['timestamp'],16)
        case.send('new:controlled_ETH_feed_fault',feed,'set(int256,uint256,uint256)',0,now,now)
        refusal=n.call('eth_call',[{'to':roles['oracle'],'data':B.abi('price(address)',ZERO)},'latest'],allow_error=True)
        assert refusal.get('error',{}).get('data')=='0x'+keccak256(b'InvalidPrice(address)')[:4].hex()+B.word(0).hex(),refusal
        save(out/'ORACLE_REFUSAL.json',{'response':refusal,'owned_fixture_feed':feed,'production_feed_modified':False})
        trade('new:post_transfer_native_trade',True,5*10**14)
        case.harvest('new:collect_during_feed_fault',True)
        before_wrong=case.state('former_owner_refusal:before')
        wrong=n.call('eth_call',[{'from':OWNER,'to':roles['rewards'],'data':B.abi('claim(uint256,address)',ids[0],ZZZ),'gas':hex(12_000_000)},'latest'],allow_error=True)
        assert wrong.get('error',{}).get('data')=='0x'+keccak256(b'Unauthorized()')[:4].hex(),wrong
        after_wrong=case.state('former_owner_refusal:after');assert after_wrong['assets']==before_wrong['assets']and after_wrong['group']==before_wrong['group']and after_wrong['shares']==before_wrong['shares']
        save(out/'FORMER_OWNER_REFUSAL.json',{'response':wrong,'simulation_only':True,'no_transaction_sent':True,'before_assets':before_wrong['assets'],'after_assets':after_wrong['assets'],'exact_unchanged':True})
        case.claim('new:new_owner_ETH_claim',0,ZERO,BUYER);case.claim('new:new_owner_ZZZ_claim',0,ZZZ,BUYER)
        case.claim('new:other_NFT_ETH_claim',1,ZERO,OWNER);case.claim('new:other_NFT_ZZZ_claim',1,ZZZ,OWNER)
        case.claim('new:repeat_empty_ETH_claim',1,ZERO,OWNER);case.claim('new:repeat_empty_ZZZ_claim',1,ZZZ,OWNER)
        final=case.state('final_all_allocated_LP_rights_drained')
        for token in(ZERO,ZZZ):assert final['assets'][token]['liabilities']==final['assets'][token]['rewards_cash']==0
        assert case.read(ZZZ,'allowance(address,address)',OWNER,trader_address)==[0]
        for actor,spender in((roles['vault'],roles['fees']),(roles['fees'],roles['rewards']),(roles['liquidity'],B.PERMIT2),(roles['lp_position_executor'],B.PERMIT2)):
            assert case.read(ZZZ,'allowance(address,address)',actor,spender)==[0]
        artifacts.check_sources();save(out/'STATES.json',case.states);save(out/'HARVESTS.json',case.harvests);save(out/'PAYOUTS.json',case.payouts)
        save(out/'RESULT.json',{'successful':True,'finite_NFTs':2,'new_local_transactions':len(n.receipts),'normal_F6_graph_reused':39,'actual_two_asset_fees_split_exact_80_10_5_5':True,'independent_eager_prefix_and_extension_replay':True,'both_raw_LP_assets_claimed':True,'normal_ETH_only_conversion_qualified':False,'current_owner_prior_and_new_income':True,'faulty_feed_blocks_price_but_not_harvest_or_claim':True,'principal_and_fee_reserves_preserved':True,'zero_Reward_liabilities_both_assets':True,'classified_fee_dust_and_5percent_reserves_retained':True,'live_environment_changed':False,'production_approved':False})
    except BaseException as exc:save(out/'FAILED.json',{'class':type(exc).__name__,'reason':str(exc),'production_approved':False});raise
    finally:
        if case:save(out/'receipts.json',case.n.receipts)
        save(out/'SOURCE_STAGE.json',{'driver_sha256':sha(Path(__file__).read_bytes()),'helper_sha256':{name:sha((HERE/name).read_bytes())for name in('driver_base.py','warm_cache.py','eager_oracle.py')},'production_profile':artifacts.profile,'source_pins':artifacts.source_pins,'production_source_changed':False})
    return 0
if __name__=='__main__':raise SystemExit(main())
