"""Fixed-anchor proxy and upstream reads only; no mutation or feed update."""
import datetime
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path.cwd()))
from zzz_ops.abi import calldata, keccak256

OUT = Path(__file__).resolve().parent
S = json.loads((OUT/'feed-read-snapshot.json').read_text())
URL = S['provider']
BLOCK = S['canonical_selector']
ALLOWED = {'eth_chainId', 'eth_call', 'eth_getCode', 'eth_getStorageAt', 'eth_getBlockByNumber'}
records = []
deadline = time.monotonic()+55


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError('unreviewed_redirect')


def rpc(method, params):
    assert method in ALLOWED
    if time.monotonic() >= deadline: raise TimeoutError('total_read_budget')
    index = len(records)+1
    record = dict(method=method,params=params,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record)
    try:
        req=urllib.request.Request(URL,data=json.dumps(dict(jsonrpc='2.0',id=index,method=method,params=params)).encode(),
            headers={'Content-Type':'application/json','User-Agent':'PoPL-bounded-readonly-upstreams/1'})
        with urllib.request.build_opener(NoRedirects()).open(req,timeout=min(10,max(.1,deadline-time.monotonic()))) as response:
            raw=response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:raise ValueError('response_limit')
        envelope=json.loads(raw);record['response']=envelope
        if envelope.get('id')!=index or envelope.get('jsonrpc')!='2.0' or ('result' in envelope)==('error' in envelope):raise ValueError('invalid_envelope')
        if 'error' in envelope:raise ValueError('rpc_refusal')
        return envelope['result']
    except urllib.error.HTTPError as error:record.update(error_type='HTTPError',http_status=error.code);error.close();raise
    except Exception as error:record['error_type']=type(error).__name__;raise


result=dict(provider=URL,block_number=S['block_number'],block_hash=S['block_hash'],qualification=False,reads={})
try:
    if rpc('eth_chainId',[])!='0x1237':raise ValueError('wrong_chain')
    for name,target,methods in (
            ('eth_proxy',S['eth_proxy'],('owner()','proposedAggregator()','phaseId()')),
            ('eth_secondary','0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22',('owner()','phaseId()')),
            ('eth_aggregator','0x6091E64eb7138EEF066a80FD3A0d7427B91f2721',('owner()','typeAndVersion()','latestConfigDetails()','transmitters()')),
            ('pyth_core','0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a',('version()','governanceDataSource()','getValidTimePeriod()'))):
        row={'address':target};result['reads'][name]=row
        for method in methods:
            try:row[method]=rpc('eth_call',[{'to':target,'data':calldata(method),'gas':hex(500000)},BLOCK])
            except Exception as error:row[method]={'error_type':type(error).__name__}
        code=rpc('eth_getCode',[target,BLOCK]);row['runtime']={'bytes':(len(code)-2)//2,'keccak256':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
    core='0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a'
    slots={name:'0x'+f'{(int.from_bytes(keccak256(label.encode()),"big")-1):064x}' for name,label in (
        ('implementation','eip1967.proxy.implementation'),('admin','eip1967.proxy.admin'))}
    for name,slot in slots.items():
        raw=rpc('eth_getStorageAt',[core,slot,BLOCK]);result['reads']['pyth_core'][name+'_slot']=dict(slot=slot,value=raw)
        if name=='implementation' and int(raw,16):
            address='0x'+raw[-40:];code=rpc('eth_getCode',[address,BLOCK]);result['reads']['pyth_implementation']={'address':address,'runtime_bytes':(len(code)-2)//2,'runtime_keccak256':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
    header=rpc('eth_getBlockByNumber',[hex(S['block_number']),False])
    result['final_canonical_header_recheck']=header['hash']==S['block_hash'] and int(header['timestamp'],16)==S['block_timestamp']
    result['complete']=result['final_canonical_header_recheck']
except Exception as error:result.update(complete=False,error_type=type(error).__name__)
finally:
    result['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for name,value in (('upstream-read-rpc.json',records),('upstream-read-snapshot.json',result)):
        with (OUT/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))
