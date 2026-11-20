"""Independent saved-wire/trace arithmetic for the finite Entry partition.

This reads evidence only; no RPC, EVM execution, signing or source mutation.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
def load(path):return json.loads(Path(path).read_bytes())
def words(raw):
    assert raw.startswith('0x')and(len(raw)-2)%64==0
    return [int(raw[i:i+64],16)for i in range(2,len(raw),64)]
def selector(sig):return '0x'+keccak256(sig.encode())[:4].hex()
def flatten(frame):
    yield frame
    for c in frame.get('calls',[]):yield from flatten(c)
def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    assert not a.output.exists();e=a.evidence;result=load(e/'RESULT.json');assert result['successful']and result['production_approved']is False
    instances=load(e/'construction/instances.json');roles={r['role']:r['address']for r in instances};assert len(instances)==39
    states=load(e/'STATES.json');receipts=load(e/'ALL_SETUP_SCENARIO_RECEIPTS.json');wire=json.loads(gzip.decompress((e/'local-wire.json.gz').read_bytes()))
    sent={r['response']['result']:r['request']['params'][0]for r in wire if r['request']['method']=='eth_sendTransaction'and 'result'in r['response']}
    assert len(sent)==len(receipts)+44
    labels=['new_ETH_activation','new_ZZZ_activation','new_ETH_growth','new_ZZZ_growth'];rows=[]
    feed_prices={}
    for role in ('eth_feed_a','eth_feed_b','zzz_feed_a','zzz_feed_b'):
        row,=[r for r in receipts if r['label']=='helper:'+role]
        feed_prices[role]=int(row['submitted']['data'][-64:],16)
    assert feed_prices['eth_feed_a']==feed_prices['eth_feed_b']==2000*10**18
    assert feed_prices['zzz_feed_a']==feed_prices['zzz_feed_b']>0
    price0,price1=feed_prices['eth_feed_a'],feed_prices['zzz_feed_a']
    def value(a0,a1):return a0*price0//10**18+a1*price1//10**18
    for index,label in enumerate(labels):
        r,=[r for r in receipts if r['label']==label];h=r['receipt']['transactionHash'];tx=sent[h]
        assert tx==r['submitted']and int(r['receipt']['status'],16)==1
        estimate=r['estimate'];padded=(estimate*12000+9999)//10000
        assert r['cap']==32000000 and r['padding_bps']==2000 and r['padded_gas']==padded==int(tx['gas'],16)<=32000000
        assert int(r['receipt']['gasUsed'],16)<padded
        entry=words('0x'+tx['data'][10:]);assert len(entry)==9
        nft,pool,asset,source,minL,deadline,increase,loss,policy=entry
        assert minL==1 and loss==300 and policy!=0 and increase==int(index>=2)
        before,after=states[index*2:index*2+2];assert before['label']==label+':before'and after['label']==label+':after'
        frames=list(flatten(load(e/(label+'-trace.json'))))
        def calls(role,sig):return [f for f in frames if f.get('to','').lower()==roles[role]and f.get('input','').startswith(selector(sig))]
        balance,=calls('liquidity','balance(bytes32,uint256,uint256,uint256,uint256)')
        ba=words('0x'+balance['input'][10:]);balanced=words(balance['output']);assert len(ba)==5 and len(balanced)==2
        assert ba[0]==pool and ba[2:4]==([source,0]if asset==0 else[0,source])and ba[4]==deadline
        assert int(balance.get('value','0x0'),16)==ba[2]
        if index==0:
            put,=calls('liquidity','mint(bytes32,int24,int24,uint256,uint256,uint128,uint256)');pa=words('0x'+put['input'][10:]);budgets=pa[3:5];putResult=words(put['output']);spent=putResult[1:]
        else:
            put,=calls('liquidity','increase(bytes32,uint256,uint256,uint256,uint128,uint256)');pa=words('0x'+put['input'][10:]);budgets=pa[2:4];spent=words(put['output'])
        assert budgets==balanced and all(x<=y for x,y in zip(spent,budgets))and int(put.get('value','0x0'),16)==budgets[0]
        book,=calls('migration_budget','contributionResult(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint32)')
        args=words('0x'+book['input'][10:]);actual=words(book['output'])
        bucket,inputUSD,supply,incumbentNAV,oldLP,newLP,idle,limits=args
        net=newLP+idle-incumbentNAV;issued=net if supply==0 else supply*net//incumbentNAV
        assert actual==[issued,net]and supply==sum(before['shares'])and bucket==int(after['bucket'])
        target=index%2;assert nft==int(after['ids'][target])and issued==after['shares'][target]-before['shares'][target]
        assert after['total_shares']==supply+issued==sum(after['shares'])and after['allocation_tree'][0]==after['total_shares']
        assert limits>>16==300 and net>=inputUSD-inputUSD*300//10000 and newLP-oldLP>=inputUSD-inputUSD*300//10000
        event='0x'+keccak256(b'ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)').hex()
        credited,=[l for l in r['receipt']['logs']if l['address'].lower()==roles['contribution_pricing']and l['topics'][0]==event]
        lower,upper,marginal,eventNet,spot,basis=words(credited['data'])
        sourceLower=value(source,0)if asset==0 else value(0,source)
        sourceUpper=(source*(price0 if asset==0 else price1)+10**18-1)//10**18
        assert inputUSD==lower==sourceLower and upper==sourceUpper and upper-lower in(0,1)
        assert marginal==newLP-oldLP and eventNet==net and marginal>=upper-upper*300//10000 and net>=upper-upper*300//10000
        nav=calls('migration_budget','contributionNav(uint256)');assert len(nav)==3
        n0,n1,n2=[words(f['output'])for f in nav];assert n2==[newLP,idle]and n1[0]==oldLP
        for mark in nav:
            children=list(flatten(mark));groups=[f for f in children if f.get('to','').lower()==roles['vault']and f.get('input','').startswith(selector('group(uint256)'))]
            assert groups
            group=words(groups[-1]['output'])
            principal=[f for f in children if f.get('to','').lower()==roles['liquidity']and f.get('input','').startswith(selector('portfolioAmounts(uint256)'))]
            assert len(principal)==int(group[1]!=0)
            amounts=words(principal[0]['output'])if principal else[0,0]
            assert words(mark['output'])==[value(*amounts),value(*group[2:4])]
        values=calls('migration_budget','valueBucket(uint256,uint256,uint256)')
        # The initial mint has no incumbent. Every later join includes exactly
        # fresh-swap and late released-compound value in the incumbent basis.
        assert len(values)==(1 if index==0 else 2)
        for f in values:
            va=words('0x'+f['input'][10:]);assert words(f['output'])==[value(va[1],va[2])]
        compound=sum(words(f['output'])[0]for f in values)
        assert incumbentNAV==n1[0]+n0[1]+compound
        assert after['entry_balances']==[0,0]and after['secondary']==0
        if index>0:
            assert before['main']==after['main']and before['ticks']==after['ticks']and before['group'][5:7]==after['group'][5:7]and after['mainL']>before['mainL']
            assert before['shares'][1-target]==after['shares'][1-target]
        if index<2:assert after['lp_claim_ETH'][target]==after['lp_claim_ZZZ'][target]==0
        rows.append({'label':label,'hash':h,'estimate':estimate,'padded_gas':padded,'actual_gas':int(r['receipt']['gasUsed'],16),'source_amount':str(source),'entrant_only_balancing_budget':list(map(str,ba[2:4])),'balanced_then_minted_budget':list(map(str,balanced)),'spent':list(map(str,spent)),'netUSD':str(net),'shares':str(issued),'incumbent_basis_reconciled':True,'nav_valued_from_actual_manager_amounts_at_fixed_fixture_marks':True,'independent_physical_tick_math_or_market_oracle':False})
    assert load(e/'cleanup.json')['owned_node_stopped']and load(e/'cleanup.json')['pending']is None
    assert load(e/'LOCAL_SEAL.json')['access']==roles['access']and load(e/'LOCAL_SEAL.json')['new_fixture_only']is True
    report={'schema':1,'passed':True,'read_only_saved_evidence':True,'transactions':rows,'normal_instances':39,'unchanged_tests_rerun':False,'production_approved':False,'input_files':{str(p.relative_to(e)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(e.glob('*'))if p.is_file()and p.suffix in('.json','.gz')}}
    with a.output.open('x',encoding='utf8')as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'passed':True,'contributions':len(rows),'output':str(a.output)}));return 0
if __name__=='__main__':raise SystemExit(main())
