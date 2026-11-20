"""Independent offline decoding of NEW direct-Manager swap evidence; no RPC."""
from pathlib import Path
import gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
CASE=V/'pool-integration-20261120/swap/attempt2'
CORE='0x8366a39cc670b4001a1121b8f6a443a643e40951'
POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
def load(name):return json.loads((CASE/name).read_bytes())
def words(raw):return [int(raw[x:x+64],16)for x in range(2,len(raw),64)]
def signed(x):return x-(1<<256)if x>>255 else x
def verify():
    wire=json.loads(gzip.decompress((CASE/'local-wire.json.gz').read_bytes()));receipts=load('receipts.json');swaps=load('SWAPS.json');states=load('STATES.json')
    for row in wire:
        request=row['request'];response=row['response']
        assert request['jsonrpc']==response['jsonrpc']=='2.0'and request['id']==response['id']
        assert hashlib.sha256(json.dumps(request).encode()).hexdigest()==row['serialized_request_sha256']
    assert len(receipts)==6
    for item in receipts:
        tx=item['transaction'];receipt=item['receipt'];h=receipt['transactionHash']
        sends=[row for row in wire if row['request']['method']=='eth_sendTransaction'and row['response'].get('result')==h]
        inclusions=[row for row in wire if row['request']['method']=='eth_getTransactionReceipt'and row['request']['params']==[h]and row['response'].get('result')]
        actual=[row['response']['result']for row in wire if row['request']['method']=='eth_getTransactionByHash'and row['request']['params']==[h]]
        assert len(sends)==len(inclusions)==len(actual)==1 and sends[0]['request']['params']==[tx]and inclusions[0]['response']['result']==receipt
        assert int(receipt['status'],16)==1 and item['padded_gas']==(item['estimated_gas']*12500+9999)//10000==int(tx['gas'],16)
        assert item['padded_gas']<=(32_000_000 if tx.get('to')is None else 24_000_000)
        for key in ('from','to','nonce','gas','gasPrice','value'):assert actual[0].get(key)==tx.get(key)
        assert actual[0]['input']==tx['data']and actual[0]['chainId']=='0x1237'
    direct=[item for item in receipts if item['label'].startswith('new:')];assert len(direct)==len(swaps)==len(states)==2
    event='0x'+keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
    provenance=load('INPUT_PROVENANCE.json');manager=provenance['addresses']['ZZZLiquidityManager'];decoded=[]
    for item,row,state in zip(direct,swaps,states):
        assert item['label']==row['label']==state['label'];args=words('0x'+item['transaction']['data'][10:]);assert len(args)==5
        assert '0x'+args[0].to_bytes(32,'big').hex()==POOL and bool(args[1])==row['direction_native_to_ZZZ']
        amount=int(row['input_raw']);out=int(row['simulated_output_raw']);assert args[2]==amount and args[3]==int(row['caller_minimum_raw'])>0
        assert int(item['simulation'],16)==out==int(row['actual_output_delta'])
        logs=[log for log in item['receipt']['logs']if log['address']==CORE and log['topics'][0]==event]
        assert len(logs)==1;log=logs[0];assert log['topics'][1]==POOL and '0x'+log['topics'][2][-40:]==manager
        delta0,delta1,sqrt,liquidity,tick,fee=words(log['data']);delta0,delta1=signed(delta0),signed(delta1)
        assert (delta0,delta1)==((-amount,out)if args[1]else(out,-amount))
        before,after=state['before'],state['after'];assert after['pool_L']==before['pool_L']==liquidity
        assert after['slot0'][0]==sqrt and after['slot0'][1]==tick
        assert after['native']==before['native']+(0 if args[1]else out)
        assert after['ZZZ']==before['ZZZ']+(out if args[1]else-amount)
        for key in ('manager_native','manager_ZZZ','allowance','child_native','child_ZZZ'):assert before[key]==after[key]==0
        decoded.append({'label':item['label'],'transaction_hash':item['receipt']['transactionHash'],'core_input':str(amount),'core_output':str(out),'core_combined_fee_units':fee,'gas_actual':int(item['receipt']['gasUsed'],16),'gas_estimate':item['estimated_gas'],'gas_padded_25_percent':item['padded_gas']})
    bad=load('CALLER_FLOOR_ROLLBACK.json');assert bad['before']==bad['after']and bad['transaction_sent']is False
    assert bad['simulation_error']['error']['data']=='0x'+keccak256(b'Slippage()')[:4].hex()
    clock=load('RESTORED_CLOCK.json');assert int(clock['pending_before']['timestamp'],16)<clock['owned_next_timestamp']
    assert int(clock['latest_after']['timestamp'],16)==int(clock['pending_after']['timestamp'],16)==clock['owned_next_timestamp']
    cleanup=load('cleanup.json');assert cleanup['owned_node_stopped']and cleanup['pending']is None and cleanup['error']is None
    upstream=[json.loads(line)for line in(CASE/'upstream-wire.jsonl').read_text().splitlines()]
    assert len(upstream)==26 and all(row['http_status']==200 for row in upstream)
    return {'passed':True,'offline_only':True,'saved_local_rows':len(wire),'included_successful_transactions':len(receipts),'new_direct_swap_behaviors':2,'simulation_only_caller_floor_rollback':True,'core_events':decoded,'final_run_public_reads':len(upstream),'source_contract_changes':False,'production_approved':False}
if __name__=='__main__':
    result=verify();target=Path(__file__).with_name('VERIFICATION.json')
    with target.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
