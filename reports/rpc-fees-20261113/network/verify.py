"""Offline evidence integrity reconciliation; never sends RPC or executes EVM."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

def require(ok,message):
    if not ok:raise ValueError(message)
def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def reply(row):return row['rpc_response']['result']
def quantity(value):
    require(isinstance(value,str)and value.startswith('0x'),'Invalid hex quantity')
    return int(value,16)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-root',type=Path)
    args=parser.parse_args()
    manifest=read(HERE/'ARTIFACTS.json')
    for item in manifest['public_files']:
        path=(HERE/item['path']).resolve()
        require(path.parent==HERE and sha(path)==item['sha256'],'Public artifact mismatch '+item['path'])
    data=read(HERE/'RPC.json');rows=data['rows'];results=read(HERE/'RESULTS.json')
    methods=read(HERE/'METHODS.json');sources=read(HERE/'SOURCES.json')
    require(len(rows)==56,'RPC count changed')
    counts={'attempts':len(rows),'valid_rpc_results':0,'rpc_errors':0,'http_denials':0,
            'restricted_network_transport_failures':0}
    phases={}
    for number,row in enumerate(rows,1):
        require(row['sequence']==number,'Sequence changed')
        request=row['request'];method=request['method'];phase=row['phase']
        require(method in methods['allowed_methods'],'Non-reviewed method')
        require(row['provider']in methods['approved_endpoints'],'Provider changed')
        phases.setdefault(phase,[]).append(row)
        require(request['id']==len(phases[phase]),'Phase request ID changed')
        if row['transport_environment']=='restricted_network':
            require(method=='eth_chainId'and row['error_class']=='URLError','Restricted failure changed')
            counts['restricted_network_transport_failures']+=1;continue
        require(row['body_truncated']is False,'Truncated response')
        if row['http_status']==403:
            require(phase=='permitted/triport'and method=='eth_chainId','Unexpected denial')
            counts['http_denials']+=1;continue
        require(row['http_status']==200,'Unexpected transport result')
        body=row['rpc_response']
        require(body['jsonrpc']=='2.0'and body['id']==request['id'],'Envelope mismatch')
        if 'error'in body:counts['rpc_errors']+=1
        else:counts['valid_rpc_results']+=1
        if method=='eth_chainId':require(reply(row)=='0x1237','Wrong chain')
        if method in ('eth_call','eth_estimateGas','debug_traceCall'):
            require(len(request['params'])==(3 if method=='debug_traceCall'else 2),'Override or missing selector')
            tx=request['params'][0];selector=request['params'][1]
            require(isinstance(selector,dict)and set(selector)=={'blockHash','requireCanonical'}and
                    selector['requireCanonical']is True,'Missing canonical selector')
            require(set(tx)<={'from','to','value','data','gas'},'Unexpected transaction field')
            require(tx['to']in ('0x000000000000000000000000000000000000006c',
                '0x000000000000000000000000000000000000006b','0x0000000000000000000000000000000000000064',
                '0x00000000000000000000000000000000000000c8','0x0bd7d308f8e1639fab988df18a8011f41eacad73'),
                'Non-reviewed execution target')
            require(quantity(tx['gas'])in(200000,500000,20000000,24000000),'Gas field changed')
            if method=='debug_traceCall':require(request['params'][2]==
                {'tracer':'callTracer','timeout':'5s','tracerConfig':{'withLog':True}},'Trace options changed')
    expected={'attempts':56,'valid_rpc_results':50,'rpc_errors':3,'http_denials':1,
              'restricted_network_transport_failures':2}
    require(counts==data['counts']==results['counts']==expected,'Count reconciliation failed')
    require({k:len(v)for k,v in phases.items()}=={'restricted/triport':1,'restricted/pinax':1,
        'permitted/triport':1,'permitted/pinax':16,'permitted/pinax-fees':22,'permitted/pinax-receipt':11,
        'permitted/pinax-zero-tip':4},
        'Phase scope changed')
    utc_intervals=[]
    for name,phase in phases.items():
        require(phase[0]['request']['method']=='eth_chainId','Chain handshake missing')
        if name.startswith('permitted/pinax'):require(reply(phase[0])=='0x1237','Invalid chain identity')
        for before,after in zip(phase,phase[1:]):
            elapsed=(dt.datetime.fromisoformat(after['observed_at_utc'])-dt.datetime.fromisoformat(before['observed_at_utc'])).total_seconds()
            require(elapsed>0,'Non-increasing UTC observation order')
            utc_intervals.append(elapsed)
    require(min(utc_intervals)==methods['bounds']['minimum_observed_utc_interval_seconds_within_phase'],
            'Recorded UTC interval minimum changed')
    require(methods['bounds']['monotonic_intervals_recorded']is False,'Unrecorded monotonic timing claimed')
    capability=phases['permitted/pinax'];anchor=results['capability_anchor']
    require(reply(capability[2])['hash']==anchor['hash'],'Capability anchor changed')
    code=bytes.fromhex(reply(capability[3])[2:]);pin=results['token_witness']
    require(len(code)==pin['bytes']==2202 and '0x'+keccak256(code).hex()==pin['keccak256'],
            'Witness runtime changed')
    original_pins=read(ROOT/'reports/market-followup-20261109/routes/runtime-pins.json')
    historical=next(x for x in original_pins if x['name']=='WETH')
    require(historical['runtime_keccak256']==pin['keccak256']and historical['runtime_bytes']==len(code),
            'Independent runtime provenance changed')
    trace_row=capability[6];trace=reply(trace_row);tx=trace_row['request']['params'][0]
    require(trace_row['request']['method']=='debug_traceCall','Trace absent')
    require(trace_row['request']['params'][1]=={'blockHash':anchor['hash'],'requireCanonical':True},'Trace anchor changed')
    require(tx['from']=='0x000000000000000000000000000000000000dead'and tx['to']==pin['address']and
            tx['value']=='0x0'and quantity(tx['gas'])==500000,'Not a zero-allowance witness')
    require(tx['data']=='0x095ea7b3'+'dead'.rjust(64,'0')+'0'*64,'Witness calldata changed')
    require(trace.get('type')=='CALL'and trace.get('from')==tx['from']and trace.get('to')==tx['to']and
            trace.get('input')==tx['data']and trace.get('output')==reply(capability[5])and
            quantity(trace['value'])==0 and quantity(trace['gasUsed'])==pin['gas_used']==33237,
            'Actual trace does not match witness')
    stack=[trace];logs=[];visited=0
    while stack:
        frame=stack.pop();visited+=1
        require(visited<=256 and not frame.get('error')and not frame.get('revertReason'),'Bad trace frame')
        logs.extend(frame.get('logs',[]));stack.extend(frame.get('calls',[]))
    require(len(logs)==1,'Missing or extra event')
    event=logs[0]
    require(event['address']==pin['address']and event['topics']==
        ['0x'+keccak256(b'Approval(address,address,uint256)').hex(),'0x'+'dead'.rjust(64,'0'),'0x'+'dead'.rjust(64,'0')]
        and event['data']=='0x'+'0'*64,'Wrong Approval event')
    for idx,gas in((7,20000000),(9,24000000)):
        require(quantity(capability[idx]['request']['params'][0]['gas'])==gas and
                quantity(reply(capability[idx]))==32000000 and quantity(reply(capability[idx+1]))==23003,
                'Gas-field diagnostic changed')
    for row in capability[11:14]:
        require(row['request']['params'][1]['blockHash']=='0x'+'00'*32,'Negative hash changed')
        error=row['rpc_response']['error'];require(error['code']==-32000,'Not a recognized missing-block code')
        expected_message=('block '+'0x'+'00'*32+' not found')if row['request']['method']=='debug_traceCall'else'header not found'
        require(error['message']==expected_message,'Not the exact requested missing block')
    require(reply(capability[14])['hash']==reply(capability[15])['hash']==anchor['hash'],'Capability header recheck failed')
    fee_anchor=results['fee_anchor'];fee=phases['permitted/pinax-fees'];receipt=phases['permitted/pinax-receipt']
    require(reply(fee[2])['hash']==reply(fee[-1])['hash']==reply(receipt[1])['hash']==reply(receipt[-1])['hash']==fee_anchor['hash'],
            'Fee anchor or recheck mismatch')
    require(len([r for r in fee if r['request']['method']=='eth_call'and
        r['request']['params'][0]['to']=='0x00000000000000000000000000000000000000c8'and
        r['request']['params'][0]['data'].startswith('0x77d488a2')])==10,'L1-only source payload count changed')
    actual=reply(receipt[7]);paid=reply(receipt[8]);header=reply(receipt[9])
    require(actual['hash']==paid['transactionHash']and actual['blockHash']==paid['blockHash']==header['hash']==fee_anchor['hash']and
            actual['blockNumber']==paid['blockNumber']==header['number'],'Ordinary receipt inclusion mismatch')
    require(quantity(actual['type'])==2 and quantity(actual['maxPriorityFeePerGas'])>0,'Nonzero-tip witness lost')
    zero=phases['permitted/pinax-zero-tip'];ztx=reply(zero[1]);zreceipt=reply(zero[2]);zheader=reply(zero[3])
    require(ztx['hash']==zreceipt['transactionHash']and ztx['blockHash']==zreceipt['blockHash']==zheader['hash']==fee_anchor['hash']
            and ztx['blockNumber']==zreceipt['blockNumber']==zheader['number'],'Zero-tip receipt inclusion mismatch')
    require(quantity(ztx['type'])==2 and quantity(ztx['maxPriorityFeePerGas'])==0,'Not an actual zero-tip witness')
    q=results['qualification']
    require(q['actual_call_tracer_log_witness']is True and q['canonical_hash_call_estimate_fields_20m_24m']is True,'Positive witness missing')
    for key in ('full_activation_api_v1_profile_pass','independent_genesis_pin_approved',
        'effective_20m_24m_provider_execution_proven','full_popl_operation_on_public_provider',
        'complete_popl_fee_policy_approved','operator_spending_caps_selected','archive_uptime_load_recovery_qualified',
        'provider_adopted','keys_accounts_or_state_overrides_used'):
        require(q[key]is False,'Unproven qualification '+key)
    require(q['public_transactions']==q['signatures']==q['service_site_journal_heartbeat_changes']==0,'Unauthorized action claim')
    for path,digest in sources['source_sha256'].items():require(sha(ROOT/path)==digest,'Source drift '+path)
    external_count=0
    if args.external_root:
        external=args.external_root.resolve()
        for item in manifest['external_files']:
            path=(external/item['path']).resolve()
            require(path.is_relative_to(external)and sha(path)==item['sha256'],'External artifact mismatch '+item['path'])
            external_count+=1
        for row in rows:
            if 'raw_relative_path'not in row:continue
            raw=(external/row['raw_relative_path']).read_bytes()
            require(hashlib.sha256(raw).hexdigest()==row['response_sha256'],'Raw response changed')
            if 'rpc_response'in row:require(json.loads(raw)==row['rpc_response'],'Raw and parsed reply differ')
    print(json.dumps({'status':'PASS','rpc_attempts':len(rows),'actual_log_witness':True,
        'public_artifacts':len(manifest['public_files']),'external_files_checked':external_count,
        'new_rpc_calls':0,'new_evm_or_test_executions':0,'provider_adopted':False,'fee_policy_approved':False}))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError)as exc:
        print('ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
