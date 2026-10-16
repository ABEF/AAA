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
from keeper.monitor import error_context, positive, rpc_hash, rpc_quantity
from zzz_ops.abi import address
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import atomic_json


def probe(config, target, data, *, confirmations=12, receipt_blocks=12, factory=Rpc):
    target = address(target)
    if not isinstance(data,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2}){4,4096}',data): raise ValueError('Invalid probe calldata')
    positive(confirmations,'confirmations');positive(receipt_blocks,'receipt_blocks')
    if confirmations>1000 or receipt_blocks>32: raise ValueError('Probe exceeds bounded range')
    urls = config['rpc_urls'];chain = config['chain_id']
    if not isinstance(urls,list) or not 1<=len(urls)<=8: raise ValueError('One to eight endpoints required')
    report = {'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'chain_id':chain,
        'scope':'read_only_point_in_time_compatibility; not finality, uptime or fee-budget qualification',
        'production_approved':False,'probe_address':target,'probe_calldata':data,'endpoints':[]}
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
            return original_call(method,params)
        client.call = bounded_call
        def observe(name, fn):
            start = time.monotonic()
            try: value = fn();entry = {'name':name,'ok':True,'value':value}
            except Exception as exc:
                entry = {'name':name,'ok':False,**error_context(exc)}
                if exc.__cause__ is not None:
                    entry['cause_type'] = type(exc.__cause__).__name__
                    status = getattr(exc.__cause__,'code',None)
                    if type(status) is int:entry['transport_status'] = status
            entry['duration_ms'] = round((time.monotonic()-start)*1000,2);endpoint['checks'].append(entry)
            return entry.get('value') if entry['ok'] else None
        def head():
            header = client.call('eth_getBlockByNumber',['latest',False])
            number = rpc_quantity(header['number'],'head number');stamp = rpc_quantity(header['timestamp'],'head timestamp')
            if abs(time.time()-stamp)>120:raise ValueError('Stale RPC head')
            return {'number':number,'hash':rpc_hash(header['hash'],'head hash'),'timestamp':stamp}
        latest = observe('fresh_head',head)
        if latest is None: continue
        if reference is None:
            number = latest['number']-confirmations
            if number<0:raise ValueError('Insufficient chain history')
            header = client.call('eth_getBlockByNumber',[hex(number),False])
            if rpc_quantity(header['number'],'reference number')!=number:raise ValueError('Wrong reference block')
            reference = {'number':number,'hash':rpc_hash(header['hash'],'reference hash')}
            report['reference_block'] = reference
        def same_block():
            header = client.call('eth_getBlockByNumber',[hex(reference['number']),False])
            if rpc_quantity(header['number'],'block number')!=reference['number'] or rpc_hash(header['hash'],'block hash')!=reference['hash']:
                raise ValueError('Provider disagrees with reference block')
            return reference['hash']
        observe('common_block_hash',same_block)
        selector = {'blockHash':reference['hash'],'requireCanonical':True}
        def hex_result(method,params, *, nonempty=False):
            result = client.call(method,params)
            if not isinstance(result,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',result) or nonempty and result=='0x':
                raise ValueError('Malformed or empty hex result')
            return {'bytes':(len(result)-2)//2,'sha256':hashlib.sha256(result.encode()).hexdigest()}
        observe('canonical_hash_eth_call',lambda:hex_result('eth_call',[{'to':target,'data':data},selector],nonempty=True))
        observe('canonical_hash_code',lambda:hex_result('eth_getCode',[target,selector],nonempty=True))
        observe('canonical_hash_storage',lambda:hex_result('eth_getStorageAt',[target,'0x0',selector],nonempty=True))
        def reject_unknown_hash():
            try:client.call('eth_call',[{'to':target,'data':data},{'blockHash':'0x'+'00'*32,'requireCanonical':True}])
            except RpcError:return True
            raise ValueError('Provider silently accepted an unavailable canonical block')
        observe('unknown_hash_rejected',reject_unknown_hash)
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
        len(endpoint['checks'])==11 and all(check['ok'] for check in endpoint['checks']) for endpoint in report['endpoints'])
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--address',required=True)
    parser.add_argument('--calldata',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        config=json.loads(Path(args.config).read_text(encoding='utf-8'))
        report=probe(config,args.address,args.calldata)
        report['probe_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        atomic_json(args.output,report)
        print(json.dumps({'compatibility_checks_passed':report['compatibility_checks_passed'],'production_approved':False,
            'endpoints':len(report['endpoints']),'reference_block':report.get('reference_block')}))
        return 0 if report['compatibility_checks_passed'] else 1
    except Exception as exc:
        print(json.dumps({'compatibility_checks_passed':False,**error_context(exc)}));return 1


if __name__=='__main__':sys.exit(main())
