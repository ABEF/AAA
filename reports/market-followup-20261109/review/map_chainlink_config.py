"""Bounded L1-height to L2 log-range mapping; no chain writes or global scan."""
import datetime,json,pathlib,sys,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
anchor=json.loads((ROOT.parent/'shared'/'anchor.json').read_text(encoding='utf-8'))
feed=json.loads((ROOT.parent/'feeds'/'anchor-reads.json').read_text(encoding='utf-8'))
ag=feed['reads']['chainlink-aggregator'];address=ag['address']
latest=bytes.fromhex(ag['latestConfigDetails()'][2:]);assert len(latest)==96
count=int.from_bytes(latest[:32],'big');height=int.from_bytes(latest[32:64],'big');expected=latest[64:]
topic='0x'+keccak256(b'ConfigSet(uint32,bytes32,uint64,address[],address[],uint8,bytes,uint64,bytes)').hex()
records=[];headers={}
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):fp.close();raise ValueError('unreviewed_redirect')
def rpc(method,params):
    assert method in ('eth_chainId','eth_getBlockByNumber','eth_getLogs') and len(records)<32
    identifier=len(records)+1;row={'id':identifier,'method':method,'params':params,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};records.append(row)
    req=urllib.request.Request(anchor['rpc'],data=json.dumps({'jsonrpc':'2.0','id':identifier,'method':method,'params':params}).encode(),headers={'Content-Type':'application/json','User-Agent':'PoPL-readonly-config-map/1'})
    try:
        with urllib.request.build_opener(NoRedirects()).open(req,timeout=10) as response:raw=response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:raise ValueError('response_limit')
        row['response']=value=json.loads(raw)
        if value.get('jsonrpc')!='2.0' or value.get('id')!=identifier or ('result'in value)==('error'in value):raise ValueError('invalid_envelope')
        if 'error'in value:raise ValueError('rpc_refusal')
        return value['result']
    except urllib.error.HTTPError as error:row.update(error_type='HTTPError',http_status=error.code);error.close();raise
    except Exception as error:row['error_type']=type(error).__name__;raise
def header(number):
    if number not in headers:
        result=rpc('eth_getBlockByNumber',[hex(number),False]);assert int(result['number'],16)==number
        headers[number]=result
    return headers[number]
result={'qualification':False,'aggregator':address,'latest_config_count':count,'config_block_number_opcode':height,
        'block_number_semantics':'Arbitrum NUMBER opcode uses first non-Arbitrum ancestor height; RPC L2 block numbers differ.',
        'primary_doc':'https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time'}
try:
    assert int(rpc('eth_chainId',[]),16)==4663
    prior=json.loads((ROOT/'chainlink-config-rpc.json').read_text(encoding='utf-8'))
    upper=prior[1]['response']['result'];assert int(upper['number'],16)==height and int(upper['l1BlockNumber'],16)>height
    headers[height]=upper
    assert int(header(0)['l1BlockNumber'],16)<=height
    low=0;high=height
    while low<high:
        middle=(low+high)//2
        if int(header(middle)['l1BlockNumber'],16)<height:low=middle+1
        else:high=middle
    first=low;assert int(header(first)['l1BlockNumber'],16)==height
    last=min(first+2000,anchor['block_number'])
    logs=rpc('eth_getLogs',[{'address':address,'fromBlock':hex(first),'toBlock':hex(last),'topics':[topic]}])
    rows=[]
    for event in logs:
        assert not event['removed'] and event['address'].lower()==address.lower() and event['topics']==[topic]
        data=bytes.fromhex(event['data'][2:]);assert len(data)>=288 and len(data)%32==0
        words=[int.from_bytes(data[i:i+32],'big') for i in range(0,288,32)]
        if data[32:64]!=expected or words[2]!=count:continue
        def array(offset):
            assert offset%32==0 and 288<=offset<=len(data)-32
            size=int.from_bytes(data[offset:offset+32],'big');assert 0<size<=31 and offset+32+size*32<=len(data)
            out=[]
            for i in range(size):
                item=data[offset+32+i*32:offset+64+i*32];assert int.from_bytes(item[:12],'big')==0
                out.append('0x'+item[-20:].hex())
            assert len(set(out))==len(out)
            return out
        block=int(event['blockNumber'],16);canonical=rpc('eth_getBlockByNumber',[hex(block),False])
        assert canonical['hash']==event['blockHash'] and int(canonical['l1BlockNumber'],16)==height
        rows.append({'transactionHash':event['transactionHash'],'blockNumber_L2':block,'blockHash':event['blockHash'],'logIndex':int(event['logIndex'],16),
                     'previousConfigBlockNumber':words[0],'configDigest':'0x'+data[32:64].hex(),'configCount':words[2],
                     'signers':array(words[3]),'transmitters':array(words[4]),'f':words[5],'offchainConfigVersion':words[7]})
    assert len(rows)==1
    current=rpc('eth_getBlockByNumber',[hex(anchor['block_number']),False]);assert current['hash']==anchor['block_hash']
    result.update(complete=True,first_L2_block_matching_L1=first,log_range_L2=[first,last],rows=rows,
                  limitation='Mapped range bounded to2001L2blocks and exact current config digest. Public keys/f are not verified node organizations, data-vendor independence or operating acceptance.')
except Exception as error:result.update(complete=False,error_type=type(error).__name__)
finally:
    result['rpc_calls']=len(records)
    for name,value in [('chainlink-config-map-rpc.json',records),('chainlink-config-map-findings.json',result)]:
        with (ROOT/name).open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')
    print(json.dumps(result,indent=2))
