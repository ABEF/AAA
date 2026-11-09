"""One bounded public canonical price snapshot; no signing/update transaction."""
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
PROVIDERS = ('https://rpc.mainnet.chain.robinhood.com', 'https://robinhood.rpc.pinax.network')
ETH_PROXY = '0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9'
ETH_SECONDARY = '0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22'
PYTH_CORE = '0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a'
PYTH_ETH = '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
ALLOWED = {'eth_chainId', 'eth_getBlockByNumber', 'eth_call', 'eth_getCode', 'eth_getStorageAt'}
records = []
deadline = time.monotonic()+55


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError('unreviewed_redirect')


def rpc(url, method, params):
    assert method in ALLOWED
    if time.monotonic() >= deadline:
        raise TimeoutError('total_read_budget')
    index = len(records)+1
    record = dict(provider=url, method=method, params=params,
        observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record)
    try:
        req = urllib.request.Request(url, data=json.dumps(dict(jsonrpc='2.0',id=index,method=method,params=params)).encode(),
            headers={'Content-Type':'application/json','User-Agent':'PoPL-bounded-readonly-prices/1'})
        with urllib.request.build_opener(NoRedirects()).open(req, timeout=min(10,max(.1,deadline-time.monotonic()))) as response:
            raw = response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:
            raise ValueError('response_limit')
        envelope=json.loads(raw)
        record['response']=envelope
        if envelope.get('id')!=index or envelope.get('jsonrpc')!='2.0' or ('result' in envelope)==('error' in envelope):
            raise ValueError('invalid_rpc_envelope')
        if 'error' in envelope:
            raise ValueError('rpc_refusal')
        return envelope['result']
    except urllib.error.HTTPError as error:
        record.update(http_status=error.code,error_type='HTTPError');error.close();raise
    except Exception as error:
        record['error_type']=type(error).__name__
        raise


result={'source_commit':'99a01e9','qualification':False,'configured_popl_prices':None}
try:
    url=None
    for candidate in PROVIDERS:
        try:
            if rpc(candidate,'eth_chainId',[])!='0x1237':raise ValueError('wrong_chain')
            head=rpc(candidate,'eth_getBlockByNumber',['latest',False])
            number=int(head['number'],16)-11
            header=rpc(candidate,'eth_getBlockByNumber',[hex(number),False])
            if int(header['number'],16)!=number:raise ValueError('wrong_header')
            block={'blockHash':header['hash'],'requireCanonical':True}
            # A genuine EIP1898 read is required before selecting the provider.
            round_data=rpc(candidate,'eth_call',[{'to':ETH_PROXY,'data':calldata('latestRoundData()'),'gas':hex(500000)},block])
            url=candidate
            break
        except Exception:
            continue
    if url is None:raise ValueError('no_usable_canonical_provider')
    result.update(provider=url,chain_id=4663,observed_head=int(head['number'],16),confirmations=12,block_number=number,
        block_hash=header['hash'],block_timestamp=int(header['timestamp'],16),eth_proxy=ETH_PROXY,
        eth_round_raw=round_data,canonical_selector=block)
    for name,target,signature,args in (
            ('eth_decimals',ETH_PROXY,'decimals()',()),
            ('eth_aggregator',ETH_PROXY,'aggregator()',()),
            ('secondary_round',ETH_SECONDARY,'latestRoundData()',()),
            ('secondary_aggregator',ETH_SECONDARY,'aggregator()',()),
            ('pyth_eth',PYTH_CORE,'getPriceUnsafe(bytes32)',(PYTH_ETH,)),
            ('pyth_owner',PYTH_CORE,'owner()',())):
        try:result[name]=rpc(url,'eth_call',[{'to':target,'data':calldata(signature,*args),'gas':hex(500000)},block])
        except Exception as error:result[name+'_error']=type(error).__name__
    for name,target in (('eth_proxy',ETH_PROXY),('eth_secondary',ETH_SECONDARY),('pyth_core',PYTH_CORE)):
        try:
            code=rpc(url,'eth_getCode',[target,block])
            if not isinstance(code,str) or not code.startswith('0x') or len(code)<4:raise ValueError('invalid_code')
            result[name+'_runtime']={'bytes':(len(code)-2)//2,'keccak256':'0x'+keccak256(bytes.fromhex(code[2:])).hex()}
        except Exception as error:result[name+'_runtime_error']=type(error).__name__
    end=rpc(url,'eth_getBlockByNumber',[hex(number),False])
    result['final_canonical_header_recheck']=end['hash']==header['hash'] and end['timestamp']==header['timestamp']
    if not result['final_canonical_header_recheck']:raise ValueError('canonical_anchor_changed')
    result['snapshot_complete']=True
except Exception as error:
    result.update(snapshot_complete=False,error_type=type(error).__name__)
finally:
    result['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for name,value in (('feed-read-rpc.json',records),('feed-read-snapshot.json',result)):
        with (OUT/name).open('x',encoding='utf-8') as stream:
            json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps(result,indent=2))
