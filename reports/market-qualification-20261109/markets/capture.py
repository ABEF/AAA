import datetime, hashlib, json, pathlib, sys, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
RPC = 'https://rpc.mainnet.chain.robinhood.com/'
METHODS = {'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getBlockByHash','eth_getCode','eth_call','eth_getLogs','eth_getStorageAt'}

def save(name, url, payload=None):
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if '/' in name or '\\' in name:
        raise ValueError('flat exclusive capture name required')
    body = None if payload is None else json.dumps(payload,separators=(',',':')).encode('utf-8')
    request = {'url':url,'method':'GET' if body is None else 'POST','read_only':True,'utc':stamp}
    if payload is not None:
        values=payload if isinstance(payload,list) else [payload]
        if any(x.get('method') not in METHODS for x in values):
            raise ValueError('unapproved method')
        request['json']=payload
    with (ROOT/(name+'-request.json')).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(request,f,indent=2);f.write('\n')
    headers={'User-Agent':'PoPL-readonly-market-qualification/1','Accept':'application/json'}
    if body is not None: headers['Content-Type']='application/json'
    result={**request}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers),timeout=45) as response:
            raw=response.read(8*1024*1024+1);result['http_status']=response.status
            result['headers']=dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw=exc.read(8*1024*1024+1);result['http_status']=exc.code;result['headers']=dict(exc.headers)
    except Exception as exc:
        result['transport_error']=type(exc).__name__+': '+str(exc)
        raw=b''
    if len(raw)>8*1024*1024: raise ValueError('response exceeds bounded capture')
    with (ROOT/(name+'-response.raw')).open('xb') as f: f.write(raw)
    result['response_bytes']=len(raw);result['sha256']=hashlib.sha256(raw).hexdigest()
    with (ROOT/(name+'-result.json')).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,indent=2);f.write('\n')
    try: parsed=json.loads(raw)
    except Exception: parsed=None
    print(json.dumps({'capture':name,'status':result.get('http_status'),'bytes':len(raw),'transport_error':result.get('transport_error')}))
    return parsed

def rpc(name,calls):
    if not isinstance(calls,list): calls=[calls]
    if len(calls)>32: raise ValueError('bounded batch')
    req=[{'jsonrpc':'2.0','id':i+1,'method':m,'params':p} for i,(m,p) in enumerate(calls)]
    res=save(name,RPC,req)
    if not isinstance(res,list): return res
    if len(res)!=len(req) or {x.get('id') for x in res}!={x['id'] for x in req}: raise ValueError('invalid response IDs')
    return sorted(res,key=lambda x:x['id'])

if __name__=='__main__':
    first=rpc('anchor-01',[('eth_chainId',[]),('eth_blockNumber',[])])
    print(json.dumps(first))
    if any('error' in x for x in first) or int(first[0]['result'],16)!=4663: raise ValueError('chain mismatch/read failure')
    height=int(first[1]['result'],16)-20
    block=rpc('anchor-02',[('eth_getBlockByNumber',[hex(height),False])])
    with (ROOT/'anchor.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(block[0]['result'],f,indent=2);f.write('\n')
    print(json.dumps({k:block[0]['result'][k] for k in ['number','hash','timestamp','gasLimit']}))
