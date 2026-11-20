"""Verify only retained fork wire, receipts and source bytes; no chain access."""
from pathlib import Path
import collections,gzip,hashlib,json,sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
from zzz_ops.deployment_plan import Artifacts,encode_constructor

V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
CASE=V/'recommendations-execution-20261120/pool/attempt3'
HERE=Path(__file__).resolve().parent
OWNER='0x000000000000000000000000000000000000a0a0'
CORE='0x8366a39cc670b4001a1121b8f6a443a643e40951'
POSM='0x58daec3116aae6d93017baaea7749052e8a04fa7'
STATE='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
PERMIT2='0x000000000022d473030f116ddee9f6b43ac78ba3'
ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
ZERO='0x'+'0'*40
BLOCK=119107223

def load(path):return json.loads(Path(path).read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def word(value):return (int(value,16)if isinstance(value,str)and value.startswith('0x')else int(value)).to_bytes(32,'big')
def raw_data(types,values):return encode_constructor(types,values).hex()

def main():
    artifacts=Artifacts();wire=json.loads(gzip.decompress((CASE/'local-wire.json.gz').read_bytes()))
    for i,row in enumerate(wire,1):
        assert row['request']['jsonrpc']=='2.0'and row['request']['id']==row['response']['id']==i
        assert ('result'in row['response'])!=('error'in row['response'])
    pristine=load(CASE/'pristine.json');stage=load(CASE/'source-stage.json')
    assert stage['runner_sha256']==sha((CASE/'runner-attempt3.py').read_bytes())
    assert stage['production_build']==artifacts.profile and stage['source_sha256']==artifacts.source_pins
    assert pristine['block']==BLOCK and pristine['hash']=='0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335'
    key=b''.join(word(x)for x in [ZERO,ZZZ,10020,200,ZERO]);assert '0x'+keccak256(key).hex()==POOL==pristine['pool']
    assert pristine['active_L']=='0'and pristine['no_added_local_liquidity_yet']
    first_mutation=next(i for i,r in enumerate(wire)if r['request']['method'].startswith('anvil_'))
    before=wire[:first_mutation]
    def lookup(method,params):
        rows=[r['response']for r in before if r['request']['method']==method and r['request']['params']==params]
        assert len(rows)==1,(method,params)
        return rows[0]
    for target,expected in pristine['runtime_hashes'].items():
        code=lookup('eth_getCode',[target,'latest'])['result'];assert '0x'+keccak256(bytes.fromhex(code[2:])).hex()==expected
    for target,signature,expected in [(POSM,'poolManager()',CORE),(POSM,'permit2()',PERMIT2),(STATE,'poolManager()',CORE)]:
        data='0x'+keccak256(signature.encode())[:4].hex()
        response=lookup('eth_call',[{'to':target,'data':data},'latest'])['result']
        assert int(response,16)==int(expected,16)
    for target,signature,result in [(STATE,'getLiquidity(bytes32)',int(pristine['active_L'])),(STATE,'getSlot0(bytes32)',None)]:
        data='0x'+(keccak256(signature.encode())[:4]+word(POOL)).hex()
        response=lookup('eth_call',[{'to':target,'data':data},'latest'])['result']
        if result is not None:assert int(response,16)==result
        else:assert [str(int(response[i:i+64],16))for i in range(2,len(response),64)]==pristine['slot0']
    quote_call=next(r for r in before if r['request']['method']=='eth_call'and r['request']['params'][0]['to']=='0x8dc178efb8111bb0973dd9d722ebeff267c98f94')
    quote_result=quote_call['response'];actual_quote=quote_result if 'error'in quote_result else quote_result['result']
    assert actual_quote==pristine['diagnostic_quote_response']
    mutation_methods=collections.Counter(r['request']['method']for r in wire if r['request']['method'].startswith('anvil_')or r['request']['method']=='eth_sendTransaction')
    assert mutation_methods=={'anvil_impersonateAccount':1,'anvil_setBalance':1,'eth_sendTransaction':12},mutation_methods
    sent=[(i,r)for i,r in enumerate(wire)if r['request']['method']=='eth_sendTransaction']
    fixture=load(CASE/'fixture-output.json')['contracts'];fobjects={n:o for objects in fixture.values()for n,o in objects.items()}
    mockpath=V/'maximum-workload-20261119/test-out/Mocks.sol/MockAccess.json';mock=load(mockpath)
    assert sha(mockpath.read_bytes())==stage['mock_access_artifact_sha256']
    def normal(name):return artifacts.contract(name)[1]['evm']['bytecode']['object']
    names=['MockAccess','ZZZProtocolPolicy','bind_protocol_policy','ZZZOracle','ZZZPortfolioPolicy','ZZZRebalanceConfirmation','ZZZStrategy','ZZZPoolRegistry','ZZZLPBalancer','ZZZLiquidityManager','PoolFixtureBudget','PoolFixtureAssets']
    receipts=[];addresses={};previous=-1
    for index,((position,row),name)in enumerate(zip(sent,names)):
        tx=row['request']['params'][0];hash_=row['response']['result'];assert tx['from']==OWNER and int(tx['value'],16)==0
        section=wire[previous+1:position];previous=position
        estimates=[r for r in section if r['request']['method']=='eth_estimateGas'and r['request']['params'][0]['data']==tx['data']]
        assert len(estimates)==1
        estimate=int(estimates[0]['response']['result'],16);padded=(estimate*12500+9999)//10000
        assert int(tx['gas'],16)==padded<=32_000_000
        calls=[r for r in section if r['request']['method']=='eth_call'and r['request']['params'][0].get('data')==tx['data']and r['request']['params'][0].get('from')==OWNER]
        # Actual attempt3 capture retained mutable transaction aliases. Those
        # old bytes are preserved, never retrospectively repaired. Only their
        # independent responses/included transaction/receipt can establish the
        # following partial result; original preflight envelopes are unproven.
        assert len(calls)==2 and all(int(c['request']['params'][0]['gas'],16)==padded for c in calls)
        assert calls[0]['response']['result']==calls[1]['response']['result']
        observed=[r['response']['result']for r in wire[position+1:]if r['request']['method']=='eth_getTransactionReceipt'and r['request']['params']==[hash_]and r['response'].get('result')is not None]
        assert len(observed)==1;receipt=observed[0]
        assert receipt['transactionHash']==hash_ and int(receipt['status'],16)==1 and int(receipt['gasUsed'],16)<=padded
        included=[r['response']['result']for r in wire[position+1:]if r['request']['method']=='eth_getTransactionByHash'and r['request']['params']==[hash_]]
        assert len(included)==1
        actual=included[0];assert actual['input']==tx['data'] and actual['from']==OWNER and actual['nonce']==tx['nonce']and actual['gas']==tx['gas']and int(actual['value'],16)==0
        if index:assert int(tx['nonce'],16)==int(receipts[-1]['transaction']['nonce'],16)+1
        assert int(receipt['blockNumber'],16)==BLOCK+index+1
        if name=='MockAccess':expected=mock['bytecode']['object'];addresses[name]=receipt['contractAddress'].lower()
        elif name=='bind_protocol_policy':
            expected='0x'+(keccak256(b'setProtocolPolicy(address)')[:4]+encode_constructor(('address',),(addresses['ZZZProtocolPolicy'],))).hex();assert tx['to']==addresses['MockAccess']
        else:
            controller=addresses['MockAccess'];args={
                'ZZZProtocolPolicy':(('address','address'),(controller,OWNER)),
                'ZZZOracle':(('address','address'),(controller,ZERO)),
                'ZZZPortfolioPolicy':(('address',),(controller,)),
                'ZZZRebalanceConfirmation':(('address',),(controller,)),
                'ZZZStrategy':(('address','address','address'),(controller,addresses.get('ZZZPortfolioPolicy'),addresses.get('ZZZRebalanceConfirmation'))),
                'ZZZPoolRegistry':(('address',),(controller,)),
                'ZZZLPBalancer':(('address','address','address'),(controller,CORE,STATE)),
                'ZZZLiquidityManager':(('address',)*6,(controller,POSM,STATE,CORE,PERMIT2,addresses.get('ZZZLPBalancer'))),
            }
            if name in args:code=normal(name);types,values=args[name];expected='0x'+code+raw_data(types,values)
            else:expected='0x'+fobjects[name]['evm']['bytecode']['object']
            addresses[name]=receipt['contractAddress'].lower()
        assert tx['data']==expected
        receipts.append({'label':name,'transaction':actual,'receipt':receipt,'estimated_gas_response':estimate,'included_gas_equals25pct_padded_response':True,'padded_gas':padded,'independent_preflight_return_results_match':True,'original_preflight_envelopes_not_authenticated':True,'expected_creation_or_binding_input_matches':True})
    relay=load(CASE/'relay/summary.json');events=[json.loads(line)for line in (CASE/'relay/events.jsonl').read_text().splitlines()]
    attempts=[r for r in events if r['event']=='upstream_attempt'];rate_limits=sum(r.get('http_status')==429 for r in attempts)
    assert len(attempts)==relay['upstream_attempts']==118 and relay['retries']==15 and rate_limits>0
    cleanup=load(CASE/'cleanup.json');assert cleanup['owned_node_stopped']and cleanup['pending']is None and not cleanup['existing_nodes_contacted']
    assert not (CASE/'test-funding.json').exists()and not (CASE/'RESULT.json').exists()
    verification={'schema':1,'kind':'independent_saved_wire_review_no_execution','pristine_pool_key_and_five_native_runtimes_verified':True,'unmodified_active_liquidity':'0','original_bounded_quote_matches_wire':True,'local_setup_receipts_verified':12,'local_creations':11,'local_policy_binding_calls':1,'included_gas_equals25pct_padded_estimate_response':True,'original_preflight_request_metadata_defect':'Mutable transaction aliases overwrote earlier full-cap gas/nonce metadata; original bytes retained, original preflight envelopes not authenticated. Future driver now freezes the serialized request.','production_build':artifacts.profile,'normal_source_pins':len(artifacts.source_pins),'upstream_attempts':118,'upstream_http429':rate_limits,'bounded_retries':15,'interruption':'Operator-agent stopped matched owned PID under recurrent rate limiting, during custody-fixture eth_call; this is not a proven impossible pool or contract guard refusal.','local_ETH_gas_funding_only':True,'no_token_balance_substitution':True,'no_pool_LP_mint_increase_harvest_close':True,'funded_partition_complete':False,'negative_growth_not_executed':True,'owned_PID_stopped':cleanup['pid'],'no_pending_submission':True,'behavioral_test_pass_claim':False,'production_approved':False}
    for name,data in [('SETUP_RECEIPTS.json',receipts),('VERIFICATION.json',verification)]:
        with (HERE/name).open('x',encoding='utf8',newline='\n')as f:json.dump(data,f,indent=2);f.write('\n')
    print(json.dumps(verification))

if __name__=='__main__':main()
