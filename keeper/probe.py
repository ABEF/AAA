"""Bounded, read-only RPC compatibility observations. Never approves live use."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from keeper.monitor import error_context, positive, rpc_hash, rpc_quantity
from zzz_ops.abi import address,calldata,keccak256
from zzz_ops.errors import RemoteRPCError
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import atomic_json


PROBE_FROM='0x'+'00'*18+'dead'
APPROVAL='0x'+keccak256(b'Approval(address,address,uint256)').hex()
TRACE_GAS=500000

def _remote_error(exc):
    seen=set()
    for _ in range(4):
        if exc is None or id(exc) in seen:return None
        seen.add(id(exc))
        if isinstance(exc,RemoteRPCError):return exc
        exc=exc.__cause__
    return None

def _approval_trace(client,target,selector):
    """Discarded approve(0) simulation, never a wallet transaction or override."""
    data=calldata('approve(address,uint256)',PROBE_FROM,0)
    tx={'from':PROBE_FROM,'to':target,'value':'0x0','data':data,'gas':hex(TRACE_GAS)}
    output=client.call('eth_call',[tx,selector])
    if output not in ('0x','0x'+f'{1:064x}'):raise ValueError('Probe approve simulation did not succeed')
    trace=client.call('debug_traceCall',[tx,selector,
        {'tracer':'callTracer','timeout':'5s','tracerConfig':{'withLog':True}}])
    if (not isinstance(trace,dict) or trace.get('type')!='CALL' or address(trace.get('from'))!=PROBE_FROM or
            address(trace.get('to'))!=target or trace.get('input','').lower()!=data or
            rpc_quantity(trace.get('value'),'trace value')!=0 or trace.get('output')!=output):
        raise ValueError('Trace differs from exact discarded probe call')
    gas=rpc_quantity(trace.get('gasUsed'),'trace gas',minimum=1)
    supplied=rpc_quantity(trace.get('gas'),'trace provided gas',minimum=1)
    if gas>TRACE_GAS or supplied>TRACE_GAS:raise ValueError('Trace exceeds probe gas limit')
    stack=[(trace,0)];logs=[];count=0
    while stack:
        frame,depth=stack.pop();count+=1
        if (count>256 or depth>16 or not isinstance(frame,dict) or frame.get('error') or
                frame.get('revertReason') or not isinstance(frame.get('calls',[]),list) or
                not isinstance(frame.get('logs',[]),list)):
            raise ValueError('Malformed or excessive call trace')
        if len(frame.get('calls',[]))>256 or len(frame.get('logs',[]))>256:raise ValueError('Excessive trace frame')
        logs.extend(frame.get('logs',[]))
        if len(logs)>256:raise ValueError('Excessive trace logs')
        stack.extend((child,depth+1) for child in frame.get('calls',[]))
    expected={'address':target,'topics':[APPROVAL,'0x'+PROBE_FROM[2:].rjust(64,'0'),
                                       '0x'+PROBE_FROM[2:].rjust(64,'0')],'data':'0x'+'0'*64}
    if len(logs)!=1 or not isinstance(logs[0],dict):raise ValueError('Actual Approval event witness is missing')
    event=logs[0]
    if (address(event.get('address'))!=target or event.get('topics')!=expected['topics'] or event.get('data')!=expected['data']):
        raise ValueError('Approval witness differs from zero-allowance probe')
    return {'gas_used':gas,'approval_event_verified':True,'state_overrides':False,
            'scope':'discarded read-only simulation, not a submitted approval or persistent state change'}

def probe(config, target, data, *, confirmations=12, receipt_blocks=12, factory=Rpc,
          profile='keeper_v1', expected_genesis=None, expected_runtime=None):
    target = address(target)
    if not isinstance(data,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2}){4,4096}',data): raise ValueError('Invalid probe calldata')
    positive(confirmations,'confirmations');positive(receipt_blocks,'receipt_blocks')
    if confirmations>1000 or receipt_blocks>32: raise ValueError('Probe exceeds bounded range')
    if profile not in ('keeper_v1','activation_api_v1'):raise ValueError('Unsupported explicit probe profile')
    if profile=='activation_api_v1':
        expected_genesis=rpc_hash(expected_genesis,'reviewed genesis pin')
        expected_runtime=rpc_hash(expected_runtime,'reviewed runtime pin')
        for value in (expected_genesis,expected_runtime):
            if int(rpc_hash(value,'reviewed probe pin'),16)==0:raise ValueError('Nonzero reviewed probe pins required')
    elif expected_genesis is not None or expected_runtime is not None:raise ValueError('Pins require the explicit preparation profile')
    urls = config['rpc_urls'];chain = config['chain_id']
    if not isinstance(urls,list) or not 1<=len(urls)<=8: raise ValueError('One to eight endpoints required')
    report = {'schema':2,'profile':profile,'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'chain_id':chain,
        'scope':'read_only_point_in_time_compatibility; not finality, uptime or fee-budget qualification',
        'production_approved':False,'probe_address':target,'probe_calldata':data,'endpoints':[]}
    if profile=='activation_api_v1':report['reviewed_pins']={'genesis_hash':expected_genesis,'runtime_code_hash':expected_runtime}
    reference = None
    for index,url in enumerate(urls):
        endpoint = {'index':index,'checks':[],'receipts':[]};report['endpoints'].append(endpoint)
        client = factory([url],chain,timeout=8,retries=1)
        original_call = client.call
        deadline = time.monotonic()+90
        calls = 0
        def bounded_call(method,params):
            nonlocal calls
            calls += 1
            if calls>100 or time.monotonic()>deadline:raise TimeoutError('Endpoint probe budget exhausted')
            result=original_call(method,params)
            if time.monotonic()>deadline:raise TimeoutError('Endpoint probe result exceeded its deadline')
            return result
        client.call = bounded_call
        def observe(name, fn):
            start = time.monotonic()
            try: value = fn();entry = {'name':name,'ok':True,'value':value}
            except Exception as exc:
                entry = {'name':name,'ok':False,**error_context(exc)}
                remote=_remote_error(exc)
                if remote:entry['remote_error']={'code':remote.code,'reason':remote.reason}
                if exc.__cause__ is not None:
                    entry['cause_type'] = type(exc.__cause__).__name__
                    status = getattr(exc.__cause__,'code',None)
                    if isinstance(exc.__cause__,HTTPError) and type(status) is int and 100<=status<=599:
                        entry['transport_status'] = status
            entry['duration_ms'] = round((time.monotonic()-start)*1000,2);endpoint['checks'].append(entry)
            return entry.get('value') if entry['ok'] else None
        if profile=='activation_api_v1':
            def genesis():
                header=client.call('eth_getBlockByNumber',['0x0',False])
                if rpc_quantity(header['number'],'genesis number')!=0 or rpc_hash(header['hash'],'genesis hash')!=expected_genesis:
                    raise ValueError('Genesis differs from reviewed chain identity')
                return expected_genesis
            if observe('genesis_identity',genesis) is None:continue
        def head():
            header = client.call('eth_getBlockByNumber',['latest',False])
            number = rpc_quantity(header['number'],'head number');stamp = rpc_quantity(header['timestamp'],'head timestamp')
            if abs(time.time()-stamp)>120:raise ValueError('Stale RPC head')
            return {'number':number,'hash':rpc_hash(header['hash'],'head hash'),'timestamp':stamp}
        latest = observe('fresh_head',head)
        if latest is None: continue
        if reference is None:
            try:
                number = latest['number']-confirmations
                if number<0:raise ValueError('Insufficient chain history')
                header = client.call('eth_getBlockByNumber',[hex(number),False])
                if rpc_quantity(header['number'],'reference number')!=number:raise ValueError('Wrong reference block')
                reference = {'number':number,'hash':rpc_hash(header['hash'],'reference hash'),
                    'timestamp':rpc_quantity(header['timestamp'],'reference timestamp')}
                report['reference_block'] = reference
            except Exception as exc:
                endpoint['reference_error']=error_context(exc);continue
        def same_block():
            header = client.call('eth_getBlockByNumber',[hex(reference['number']),False])
            if (rpc_quantity(header['number'],'block number')!=reference['number'] or rpc_hash(header['hash'],'block hash')!=reference['hash'] or
                    rpc_quantity(header['timestamp'],'block timestamp')!=reference['timestamp']):
                raise ValueError('Provider disagrees with reference block')
            return reference['hash']
        observe('common_block_hash',same_block)
        selector = {'blockHash':reference['hash'],'requireCanonical':True}
        def hex_result(method,params, *, nonempty=False):
            result = client.call(method,params)
            if not isinstance(result,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',result) or nonempty and result=='0x':
                raise ValueError('Malformed or empty hex result')
            if profile=='activation_api_v1' and method=='eth_getCode':
                if len(result)>2+2*24576:raise ValueError('Probe runtime exceeds the normal code-size bound')
                if '0x'+keccak256(bytes.fromhex(result[2:])).hex()!=expected_runtime:
                    raise ValueError('Probe runtime differs from reviewed pin')
            return {'bytes':(len(result)-2)//2,'sha256':hashlib.sha256(result.encode()).hexdigest()}
        observe('canonical_hash_eth_call',lambda:hex_result('eth_call',[{'to':target,'data':data},selector],nonempty=True))
        runtime=observe('canonical_hash_code',lambda:hex_result('eth_getCode',[target,selector],nonempty=True))
        observe('canonical_hash_storage',lambda:hex_result('eth_getStorageAt',[target,'0x0',selector],nonempty=True))
        def reject_unknown_hash():
            try:client.call('eth_call',[{'to':target,'data':data},{'blockHash':'0x'+'00'*32,'requireCanonical':True}])
            except RpcError as exc:
                remote=_remote_error(exc)
                if remote and remote.method=='eth_call' and remote.code in (-32000,-32001) and remote.reason=='unavailable_block':return True
                raise
            raise ValueError('Provider silently accepted an unavailable canonical block')
        observe('unknown_hash_rejected',reject_unknown_hash)
        if profile=='activation_api_v1':
            def approval_trace():
                if runtime is None:raise ValueError('Reviewed runtime must match before trace simulation')
                return _approval_trace(client,target,selector)
            observe('actual_call_tracer_with_log',approval_trace)
        observe('gas_price_wei',lambda:rpc_quantity(client.call('eth_gasPrice',[]),'gas price'))
        for tag in ('safe','finalized'):
            def tagged(tag=tag):
                header = client.call('eth_getBlockByNumber',[tag,False])
                return {'number':rpc_quantity(header['number'],'tag number'),'hash':rpc_hash(header['hash'],'tag hash')}
            observe(tag+'_tag',tagged)
        def receipts():
            # Fixed scan and result caps. Skip chain-internal txs; retain only ordinary tx types.
            for number in range(reference['number'],max(-1,reference['number']-receipt_blocks),-1):
                block = client.call('eth_getBlockByNumber',[hex(number),False])
                for tx_hash in block['transactions'][:8]:
                    tx = client.call('eth_getTransactionByHash',[tx_hash])
                    if rpc_quantity(tx.get('type','0x0'),'transaction type') not in (0,1,2,3,4):continue
                    receipt = client.call('eth_getTransactionReceipt',[tx_hash])
                    if rpc_hash(receipt['blockHash'],'receipt block')!=rpc_hash(block['hash'],'sample block') or \
                            rpc_hash(receipt['transactionHash'],'receipt tx')!=rpc_hash(tx_hash,'sample tx'):
                        raise ValueError('Receipt inclusion mismatch')
                    sample = {'transaction':tx_hash,'block':number,
                        'gas_used':rpc_quantity(receipt['gasUsed'],'receipt gas',minimum=1),
                        'effective_gas_price_wei':rpc_quantity(receipt['effectiveGasPrice'],'receipt gas price'),
                        'status':rpc_quantity(receipt['status'],'receipt status')}
                    for field in ('l1Fee','gasUsedForL1','l1GasUsed'):
                        sample[field] = rpc_quantity(receipt[field],field) if field in receipt else None
                    sample['gas_times_price_wei'] = str(sample['gas_used']*sample['effective_gas_price_wei'])
                    endpoint['receipts'].append(sample)
                    if len(endpoint['receipts'])>=3:return len(endpoint['receipts'])
            if not endpoint['receipts']:raise ValueError('No ordinary receipt sample in bounded window')
            return len(endpoint['receipts'])
        observe('ordinary_receipt_samples',receipts)
        observe('reference_still_canonical',same_block)
    report['compatibility_checks_passed'] = bool(report.get('reference_block')) and all(
        len(endpoint['checks'])==(13 if profile=='activation_api_v1' else 11) and all(check['ok'] for check in endpoint['checks']) for endpoint in report['endpoints'])
    return report


class _Parser(argparse.ArgumentParser):
    def error(self,message):raise ValueError('Invalid probe arguments')

def _read_config(path):
    with Path(path).open('rb') as source:raw=source.read(65537)
    if len(raw)>65536:raise ValueError('Probe configuration exceeds size limit')
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError('Duplicate probe configuration key')
            value[key]=item
        return value
    def constant(_):raise ValueError('Nonfinite probe configuration number')
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    if not isinstance(value,dict):raise ValueError('Probe configuration must be an object')
    return value

def main(argv=None):
    parser=_Parser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--address',required=True)
    parser.add_argument('--calldata',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--profile',choices=('keeper_v1','activation_api_v1'),default='keeper_v1')
    parser.add_argument('--genesis-hash');parser.add_argument('--runtime-hash')
    parser.add_argument('--confirmations',type=int,default=12);parser.add_argument('--receipt-blocks',type=int,default=12)
    try:
        args=parser.parse_args(argv)
        if Path(args.config).resolve()==Path(args.output).resolve():raise ValueError('Preserve the probe input configuration')
        config=_read_config(args.config)
        report=probe(config,args.address,args.calldata,profile=args.profile,confirmations=args.confirmations,
            receipt_blocks=args.receipt_blocks,expected_genesis=args.genesis_hash,expected_runtime=args.runtime_hash)
        report['probe_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        atomic_json(args.output,report)
        print(json.dumps({'compatibility_checks_passed':report['compatibility_checks_passed'],'production_approved':False,
            'endpoints':len(report['endpoints']),'reference_block':report.get('reference_block')}))
        return 0 if report['compatibility_checks_passed'] else 1
    except Exception as exc:
        print(json.dumps({'compatibility_checks_passed':False,**error_context(exc)}));return 1


if __name__=='__main__':sys.exit(main())
