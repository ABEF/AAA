"""Independent offline wire, physical receipt, reserve and exact-unit replay."""
from pathlib import Path
import argparse,gzip,hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from eager_oracle import TwoLeaf
from zzz_ops.abi import keccak256
ZERO='0x'+'0'*40;ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'

def load(p):return json.loads(Path(p).read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def words(raw):assert raw.startswith('0x')and(len(raw)-2)%64==0;return [int(raw[i:i+64],16)for i in range(2,len(raw),64)]
def sig(value):return '0x'+keccak256(value.encode()).hex()
def address(topic):return '0x'+topic[-40:]
def flat(frame):
    yield frame
    for child in frame.get('calls',[]):yield from flat(child)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();assert not a.output.exists();e=a.evidence
    result=load(e/'RESULT.json');assert result['successful']and result['production_approved']is False
    prior=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/pool-integration-20261120/entry/attempt1')
    instances=load(prior/'construction/instances.json');r={x['role']:x['address']for x in instances};old=load(prior/'STATES.json')[-1];ids=list(map(int,old['ids']));bucket=int(old['bucket'])
    prefix=load(prior/'ALL_SETUP_SCENARIO_RECEIPTS.json');receipts=load(e/'receipts.json');states=load(e/'STATES.json');assert len(receipts)==17
    wire=json.loads(gzip.decompress((e/'local-wire.json.gz').read_bytes()))
    for index,row in enumerate(wire,1):
        req=row['request'];assert req['id']==row['response']['id']==index and sha(json.dumps(req).encode())==row['serialized_request_sha256']
    sends={x['response']['result']:(index,x['request']['params'][0])for index,x in enumerate(wire)if x['request']['method']=='eth_sendTransaction'};assert len(sends)==17
    tx_summaries=[]
    for row in receipts:
        rc=row['receipt'];h=rc['transactionHash'];index,tx=sends[h];assert tx==row['submitted']and int(rc['status'],16)==1
        got,=[x['response']['result']for x in wire if x['request']['method']=='eth_getTransactionByHash'and x['request']['params']==[h]]
        assert (got['from'],got['to'],got['nonce'],got['input'],got['gas'],got['gasPrice'],got['value'])==(tx['from'],tx.get('to'),tx['nonce'],tx['data'],tx['gas'],tx['gasPrice'],tx['value'])
        assert got['blockHash']==rc['blockHash']and got['blockNumber']==rc['blockNumber']and rc['transactionHash']==h and rc['from']==tx['from']and rc['to']==tx.get('to')
        assert got.get('chainId','0x1237')=='0x1237'and got['type']=='0x0'
        assert row['padded_gas']==(row['estimate']*(10000+row['padding_bps'])+9999)//10000==int(tx['gas'],16)<=row['cap']
        assert int(rc['gasUsed'],16)<=row['padded_gas']
        full={'from':tx['from'],'data':tx['data'],'value':tx['value'],'gas':hex(row['cap'])}
        if 'to'in tx:full['to']=tx['to']
        estimate_calls=[x for x in wire[:index]if x['request']['method']=='eth_estimateGas'and x['request']['params']==[full]and int(x['response'].get('result','0x0'),16)==row['estimate']];assert estimate_calls
        traces=[x['response']['result']for x in wire if x['request']['method']=='debug_traceTransaction'and x['request']['params'][0]==h];assert len(traces)==1 and traces[0]==load(e/row['trace'])
        tx_summaries.append({'label':row['label'],'hash':h,'estimate':row['estimate'],'padded':row['padded_gas'],'actual':int(rc['gasUsed'],16),'padding_bps':row['padding_bps'],'cap':row['cap']})
    # Deliberately different event dispatcher from the driver; bigint rational
    # eager allocation shares only the standalone independently reviewed policy.
    own=TwoLeaf();shared=TwoLeaf();owners={};events=prefix+receipts
    def replay(row):
        for log in row['receipt']['logs']:
            t=log['topics'];d=words(log['data'])
            if log['address']==r['nft']and t[0]==sig('Transfer(address,address,uint256)'):
                identifier=int(t[3],16);assert identifier in ids;owners[identifier]=address(t[2])
            if log['address']!=r['rewards']:continue
            if t[0]==sig('ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)'):
                ordinal,previous,weight,total=d;assert ids[ordinal-1]==int(t[1],16)and own.weights[ordinal-1]==previous;own.weight(ordinal,weight);assert sum(own.weights)==total
            elif t[0]==sig('CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)'):
                ordinal,previous,weight,total=d;assert shared.weights[ordinal-1]==previous;shared.weight(ordinal,weight);assert sum(shared.weights)==total
            elif t[0]==sig('PoolRewardsCredited(uint256,address,uint256,uint256)'):
                assert int(t[1],16)==bucket;token=address(t[2]);assert token in(ZERO,ZZZ);own.credit(token,d[0]);shared.credit(token,d[1])
            elif t[0]==sig('Claimed(uint256,address,address,uint256)'):
                identifier=int(t[1],16);token=address(t[2]);ordinal=ids.index(identifier)+1;assert address(t[3])==owners[identifier]
                assert own.take(token,ordinal)+shared.take(token,ordinal)==d[0]
    for row in prefix:replay(row)
    cursor=0
    for state in states:
        while cursor<len(receipts)and int(receipts[cursor]['receipt']['blockNumber'],16)<=int(state['head']['number'],16):replay(receipts[cursor]);cursor+=1
        assert state['owners']==[owners[i]for i in ids]and state['shares']==own.weights and shared.weights==[1,1]
        for token in(ZERO,ZZZ):
            expected=[[own.claim(token,i),shared.claim(token,i)]for i in(1,2)];asset=state['assets'][token];assert asset['claims']==expected and asset['liabilities']==sum(map(sum,expected))==asset['rewards_cash']
            fee=asset['fees'];assert fee['cash']==fee['accounted']==fee['dust']+fee['compound']+fee['buyback']and 0<=fee['dust']<20
        assert state['group']==states[0]['group']and state['main']==states[0]['main']and state['L']==states[0]['L']and state['ticks']==states[0]['ticks']
    assert cursor==17
    # Independently connect real physical receipts to exact fee allocation calls.
    feed_addresses={row['receipt']['contractAddress']for row in prefix if row['label'].startswith('helper:')and '_feed_'in row['label']}
    forbidden=feed_addresses|{r['oracle']};harvest_rows=[];fee_intakes={ZERO:0,ZZZ:0}
    for row in receipts:
        is_harvest='collect_actual_'in row['label']or'repeat_collection' in row['label']or'collect_during_'in row['label']
        is_claim='claim'in row['label'];trace=load(e/row['trace']);frames=list(flat(trace))
        if is_harvest or is_claim:assert not any(frame.get('to')in forbidden for frame in frames)
        if not is_harvest:continue
        logs=[x for x in row['receipt']['logs']if x['address']==r['vault']and x['topics'][0]==sig('FeesCollected(uint256,uint256,uint256)')];assert len(logs)==1
        amounts=words(logs[0]['data']);assert int(logs[0]['topics'][1],16)==bucket
        native_in=sum(int(f.get('value','0x0'),16)for f in frames if f.get('type')=='CALL'and f.get('to')==r['vault'])
        assert native_in==amounts[0]
        transfers=[log for log in row['receipt']['logs']if log['address']==ZZZ and log['topics'][0]==sig('Transfer(address,address,uint256)')]
        token_in=sum(words(log['data'])[0]for log in transfers if address(log['topics'][2])==r['vault']);assert token_in==amounts[1]
        allocations=[f for f in frames if f.get('to')==r['fees']and f.get('input','').startswith(sig('allocate(uint256,address,uint256)')[:10])]
        assert len(allocations)==sum(bool(x)for x in amounts)
        h,=[x for x in load(e/'HARVESTS.json')if x['label']==row['label']]
        for token,amount in zip((ZERO,ZZZ),amounts):
            old=h['before'][token];new=h['after'][token];units,dust=divmod(old['fees']['dust']+amount,20)
            assert new['fees']['dust']==dust and new['fees']['compound']-old['fees']['compound']==units and new['fees']['buyback']-old['fees']['buyback']==units
            assert new['liabilities']-old['liabilities']==18*units and new['fees']['cash']-old['fees']['cash']==amount-18*units and new['vault_cash']==old['vault_cash']
            credits=[f for f in frames if f.get('to')==r['rewards']and f.get('input','').startswith(sig('creditPool(uint256,address,uint256,uint256)')[:10])and words('0x'+f['input'][10:])[1]==int(token,16)]
            assert len(credits)==int(units>0)
            if units:
                credit=credits[0];assert credit['from']==r['fees']and words('0x'+credit['input'][10:])==[bucket,int(token,16),16*units,2*units]
                assert int(credit.get('value','0x0'),16)==(18*units if token==ZERO else 0)
                allocated=[x for x in row['receipt']['logs']if x['address']==r['fees']and x['topics'][0]==sig('FeesAllocated(uint256,address,uint256,uint256)')and address(x['topics'][2])==token];assert len(allocated)==1 and words(allocated[0]['data'])==[20*units,dust]
            matching=[f for f in allocations if words('0x'+f['input'][10:])==[bucket,int(token,16),amount]]
            assert len(matching)==int(amount>0)
            if amount:assert matching[0]['from']==r['vault']and int(matching[0].get('value','0x0'),16)==(amount if token==ZERO else 0)
            fee_intakes[token]+=amount
        harvest_rows.append({'label':row['label'],'actual_native_receipt':str(native_in),'actual_ZZZ_receipt':str(token_in),'allocate_inputs_match':True,'Oracle_and_feed_calls':0})
    assert len(harvest_rows)==3
    for payout in load(e/'PAYOUTS.json'):
        row,=[x for x in receipts if x['receipt']['transactionHash']==payout['hash']];tx=row['submitted'];args=words('0x'+tx['data'][10:]);assert args==[int(payout['nft']),int(payout['token'],16)]and tx['from']==payout['recipient']
        events=[x for x in row['receipt']['logs']if x['address']==r['rewards']and x['topics'][0]==sig('Claimed(uint256,address,address,uint256)')];assert len(events)==1
        event=events[0];assert int(event['topics'][1],16)==int(payout['nft'])and address(event['topics'][2])==payout['token']and address(event['topics'][3])==payout['recipient']and words(event['data'])==[int(payout['amount'])]
        gas=int(row['receipt']['gasUsed'],16)*int(row['receipt']['effectiveGasPrice'],16);assert int(payout['local_execution_gas_cost'])==gas
        assert int(payout['recipient_after'])==int(payout['recipient_before'])+int(payout['amount'])-(gas if payout['token']==ZERO else 0)
    final=states[-1]
    assert all(final['assets'][t]['liabilities']==final['assets'][t]['rewards_cash']==0 for t in(ZERO,ZZZ))
    assert load(e/'cleanup.json')['owned_node_stopped']and load(e/'cleanup.json')['pending']is None
    restore=load(e/'RESTORE_INPUT.json');derived=(e/'restore-state.json').read_bytes();assert sha(derived)==restore['derived_state_sha256']and len(derived)==restore['derived_bytes']<=restore['decompressed_bound_bytes']
    process=load(e/'process.json');assert '--load-state'in process['command']and process['request_size_limit_override']is False and '--no-request-size-limit'not in process['command']
    source=load(e/'SOURCE_STAGE.json');assert source['driver_sha256']==sha((e/'source-run_fees.py').read_bytes())
    result={'schema':1,'passed':True,'offline_only':True,'immutable_wire_rows':len(wire),'exact_included_successful_transactions':17,'all_state_eager_components_reconciled':len(states),'transaction_gas':tx_summaries,'physical_receipt_proofs':harvest_rows,'new_actual_fee_receipts':{k:str(v)for k,v in fee_intakes.items()},'claim_payouts_verified':7,'funded_claims':5,'empty_repeat_claims':2,'reserve_cash_and_zero_Reward_liabilities':True,'normal_ETH_only_conversion_qualified':False,'independent_physical_valuation_qualified':False,'production_approved':False}
    with a.output.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'passed':True,'wire_rows':len(wire),'transactions':17,'state_replays':len(states),'harvests':3,'payouts':7}))
if __name__=='__main__':main()
