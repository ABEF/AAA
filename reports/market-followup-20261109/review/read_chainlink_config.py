"""One exact historic ConfigSet block; public read-only RPC allowlist."""
import datetime,hashlib,json,pathlib,sys,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
anchor=json.loads((ROOT.parent/'shared'/'anchor.json').read_text(encoding='utf-8'))
feed=json.loads((ROOT.parent/'feeds'/'anchor-reads.json').read_text(encoding='utf-8'))
ag=feed['reads']['chainlink-aggregator'];address=ag['address']
latest=bytes.fromhex(ag['latestConfigDetails()'][2:]);assert len(latest)==96
count=int.from_bytes(latest[:32],'big');height=int.from_bytes(latest[32:64],'big');expected=latest[64:]
signature='ConfigSet(uint32,bytes32,uint64,address[],address[],uint8,bytes,uint64,bytes)'
topic='0x'+keccak256(signature.encode()).hex()
records=[]
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):fp.close();raise ValueError('unreviewed_redirect')
def rpc(method,params):
    assert method in ('eth_chainId','eth_getBlockByNumber','eth_getLogs')
    identifier=len(records)+1;row={'id':identifier,'method':method,'params':params,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};records.append(row)
    req=urllib.request.Request(anchor['rpc'],data=json.dumps({'jsonrpc':'2.0','id':identifier,'method':method,'params':params}).encode(),headers={'Content-Type':'application/json','User-Agent':'PoPL-readonly-config/1'})
    try:
        with urllib.request.build_opener(NoRedirects()).open(req,timeout=12) as response:raw=response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:raise ValueError('response_limit')
        row['raw_sha256']=hashlib.sha256(raw).hexdigest();row['response']=value=json.loads(raw)
        if value.get('jsonrpc')!='2.0' or value.get('id')!=identifier or ('result'in value)==('error'in value):raise ValueError('invalid_envelope')
        if 'error'in value:raise ValueError('rpc_refusal')
        return value['result']
    except urllib.error.HTTPError as error:row.update(error_type='HTTPError',http_status=error.code);error.close();raise
    except Exception as error:row['error_type']=type(error).__name__;raise
result={'qualification':False,'aggregator':address,'source':'chainlink-source-match.json','latest_config_count':count,'latest_config_block':height,'latest_config_digest':'0x'+expected.hex()}
try:
    assert int(rpc('eth_chainId',[]),16)==4663
    header=rpc('eth_getBlockByNumber',[hex(height),False]);assert int(header['number'],16)==height
    logs=rpc('eth_getLogs',[{'address':address,'fromBlock':hex(height),'toBlock':hex(height),'topics':[topic]}])
    rows=[]
    for event in logs:
        assert event['blockHash']==header['hash'] and int(event['blockNumber'],16)==height and event['address'].lower()==address.lower() and event['topics']==[topic] and not event['removed']
        data=bytes.fromhex(event['data'][2:]);assert len(data)>=288 and len(data)%32==0
        words=[int.from_bytes(data[i:i+32],'big') for i in range(0,288,32)]
        def array(offset):
            assert offset%32==0 and 288<=offset<=len(data)-32
            size=int.from_bytes(data[offset:offset+32],'big');assert 0<size<=31 and offset+32+size*32<=len(data)
            out=[]
            for i in range(size):
                item=data[offset+32+i*32:offset+64+i*32];assert int.from_bytes(item[:12],'big')==0
                out.append('0x'+item[-20:].hex())
            assert len(set(out))==len(out)
            return out
        signers=array(words[3]);transmitters=array(words[4]);assert data[32:64]==expected and words[2]==count and 0<words[5]<256
        rows.append({'transactionHash':event['transactionHash'],'logIndex':int(event['logIndex'],16),'previousConfigBlockNumber':words[0],
                     'configDigest':'0x'+data[32:64].hex(),'configCount':words[2],'signers':signers,'transmitters':transmitters,'f':words[5],
                     'offchainConfigVersion':words[7],'onchain_config_offset':words[6],'offchain_config_offset':words[8]})
    assert len(rows)==1
    after=rpc('eth_getBlockByNumber',[hex(height),False]);assert after['hash']==header['hash']
    tipanchor=rpc('eth_getBlockByNumber',[hex(anchor['block_number']),False]);assert tipanchor['hash']==anchor['block_hash']
    result.update(complete=True,canonical_block_hash=header['hash'],rows=rows,
                  limitation='Addresses and f are public config evidence, not verified node organizations, data-vendor independence, market methodology, source recompilation or uptime acceptance.')
except Exception as error:result.update(complete=False,error_type=type(error).__name__)
finally:
    with (ROOT/'chainlink-config-rpc.json').open('x',encoding='utf-8') as out:json.dump(records,out,indent=2);out.write('\n')
    with (ROOT/'chainlink-config-findings.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result,indent=2))
