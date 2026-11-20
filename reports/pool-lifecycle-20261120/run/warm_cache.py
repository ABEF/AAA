"""Report-only exact-anchor derived seed and immutable full cache export."""
from contextlib import contextmanager
import copy,gzip,hashlib,json,threading,time,zipfile
from pathlib import Path
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from scripts import source9_rehearsal_fork as F
from zzz_ops.abi import keccak256
from zzz_ops.deployment_sequence import create_address

ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'reports/recommendations-execution-20261120/pool'
PUBLIC_ENDPOINT=F.PUBLIC_ENDPOINT
BLOCK=119107223
ANCHOR='0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335'
GENESIS='0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c'
HELPER='6c52f68b6d66cfa28d18c13eee0a1930123dec82d54143446ac76ef9069629b4'
OWNER='0x000000000000000000000000000000000000a0a0'
PRIOR=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/pool-lifecycle-20261120/run/attempt2')
PRIOR_FULL='321118fa3f94f48a0e5fb11d0da651b81c2515cb2cdee9fd0bbcd020e35f8bdf'
PRIOR_WIRE='0c38070e9803100df63cdc041d3ba4e2c5c273c239ab9dc6abe173c1f29b178b'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n')as h:json.dump(value,h,indent=2);h.write('\n')

def derive_seed(output):
    """Recover only candidate bytes whose two digests match cached success events."""
    helper=ROOT/'scripts/source9_rehearsal_fork.py'
    assert sha(helper.read_bytes())==HELPER
    # Expected helper identity is set from its already reviewed immutable input.
    old_manifest=json.loads((OLD/'EVIDENCE_MANIFEST.json').read_bytes())
    archive=OLD/'evidence.zip';raw_archive=archive.read_bytes()
    assert sha(raw_archive)==old_manifest['sha256']=='d1010145cf42181c98e5b967ca487eb2327ec6b50a34c24394b81606c2bad6d1'
    with zipfile.ZipFile(archive)as z:
        def member(name):
            raw=z.read(name);expected=old_manifest['members'][name]
            assert len(raw)==expected['bytes']and sha(raw)==expected['sha256'];return raw
        raw_events=member('attempt3/relay/events.jsonl')
        events=[json.loads(line)for line in raw_events.decode().splitlines()]
        wire=json.loads(gzip.decompress(member('attempt3/local-wire.json.gz')))
        pristine=json.loads(member('attempt3/pristine.json'))
    assert pristine['block']==BLOCK and pristine['hash']==ANCHOR
    evidence={}
    for line,event in enumerate(events,1):
        if event['event']!='read_result' or event.get('cached')is not True:continue
        key=event['request_sha256'];value=event['result_sha256']
        if key in evidence:assert evidence[key][0]==value
        evidence[key]=(value,line,event['method'])
    validator=object.__new__(F._ForkCache);validator.anchor_number=BLOCK;validator.anchor_hash=ANCHOR
    entries={};provenance=[]
    def admit(method,params,result,derivation):
        request={'jsonrpc':'2.0','id':1,'method':method,'params':params}
        assert validator._validate(request)==(method,params)
        if not validator._cacheable(method,params) or not validator._valid_result(method,result,params):return
        key=F._digest({'method':method,'params':params});record=evidence.get(key)
        if not record or record[2]!=method or F._digest(result)!=record[0]:return
        row={'method':method,'params':copy.deepcopy(params),'result':copy.deepcopy(result),'result_sha256':record[0]}
        assert key not in entries or entries[key]==row
        entries[key]=row;provenance.append({'request_sha256':key,'source_event_line':record[1],'result_sha256':record[0],'derivation':derivation})
    admit('eth_chainId',[],'0x1237','known4663 scalar; exact event hash required')
    first_mutation=next(i for i,r in enumerate(wire)if r['request']['method'].startswith('anvil_'))
    addresses={OWNER,*pristine['runtime_hashes']}
    for row in wire[:first_mutation]:
        req,answer=row['request'],row['response']
        if req['method']=='eth_getCode' and'result'in answer:
            target=req['params'][0];addresses.add(target)
            admit('eth_getCode',[target,hex(BLOCK)],answer['result'],'pre-mutation local bytes matched to exact upstream request/result hashes')
    top={create_address(OWNER,n)for n in range(96)}
    addresses.update(top)
    addresses.update(create_address(parent,n)for parent in top for n in range(1,17))
    for target in addresses:
        admit('eth_getCode',[target,hex(BLOCK)],'0x','candidate empty synthetic CREATE account; accepted only on both recorded hashes')
        for method in ('eth_getBalance','eth_getTransactionCount'):
            admit(method,[target,hex(BLOCK)],'0x0','candidate zero synthetic CREATE account; accepted only on both recorded hashes')
    assert len(entries)<=F.MAX_CACHE_ENTRIES
    report={'schema':1,'kind':'derived_hash_verified_seed_not_raw_upstream_export','anchor_number':BLOCK,'anchor_hash':ANCHOR,
        'source_archive_sha256':sha(raw_archive),'source_events_sha256':sha(raw_events),'helper_sha256':sha(helper.read_bytes()),
        'entries':entries,'derivations':provenance,'unknowns_remain_misses':True,'latest_or_errors_admitted':False,
        'production_approved':False,'network_calls':0}
    dump(output,report);return report

def prior_full_entries(seed,output):
    """Authenticate a fixed ordered export chain; no arbitrary artifact adoption."""
    chain=[
        (PRIOR,PRIOR_FULL,PRIOR_WIRE),
        (PRIOR.parent/'attempt3','65c17dd1bbde06fb95bda969a29fe1c512bef77c4a4de7b74053d31125e02733','666bd35b587ff78e563f53ebc5a120a1a8026f843cb8543b083c3fbb4d9c1a80')]
    authorized=copy.deepcopy(seed['entries']);sources=[];previous=None
    validator=object.__new__(F._ForkCache);validator.anchor_number=BLOCK;validator.anchor_hash=ANCHOR
    for case,expected_full,expected_wire in chain:
        raw=(case/'relay/full-cache.json').read_bytes();wire=(case/'upstream-wire.jsonl').read_bytes()
        assert sha(raw)==expected_full and sha(wire)==expected_wire
        export=json.loads(raw);assert export['anchor_number']==BLOCK and export['anchor_hash']==ANCHOR
        old_seed_raw=(case/'DERIVED_SEED.json').read_bytes();assert sha(old_seed_raw)==export['derived_seed_sha256']
        old_seed=json.loads(old_seed_raw);assert old_seed['entries']==seed['entries']
        if previous is not None:
            assert export['prior_full_export_sha256']==previous
            assert sha((case/'PRIOR_CACHE_IMPORT.json').read_bytes())==export['prior_import_manifest_sha256']
        observed={}
        for line in wire.decode().splitlines():
            row=json.loads(line);assert row['http_status']==200
            body=row['request_bytes_utf8'].encode();reply=row['response_bytes_utf8'].encode()
            assert sha(body)==row['request_sha256']and sha(reply)==row['response_sha256']
            req,answer=F._loads(body),F._loads(reply)
            assert req['jsonrpc']==answer['jsonrpc']=='2.0'and req['id']==answer['id']and'result'in answer and'error'not in answer
            key=F._digest({'method':req['method'],'params':req['params']})
            if key in observed:assert observed[key]==answer['result']
            observed[key]=answer['result']
        for key,row in export['entries'].items():
            method,params=row['method'],row['params']
            assert validator._validate(dict(jsonrpc='2.0',id=1,method=method,params=params))==(method,params)
            assert validator._cacheable(method,params)and validator._valid_result(method,row['result'],params)
            assert key==F._digest(dict(method=method,params=params))and row['result_sha256']==F._digest(row['result'])
            if key in observed:assert row['result']==observed[key]
            else:assert key in authorized and row==authorized[key]
            if key in authorized:assert row==authorized[key]
            authorized[key]=copy.deepcopy(row)
        previous=expected_full;sources.append({'full_export_sha256':expected_full,'raw_upstream_sha256':expected_wire,'entries':len(export['entries'])})
    dump(output,{'schema':1,'kind':'full_exact_anchor_export_chain_import','entries':len(authorized),'ordered_sources':sources,
        'unmatched_or_latest_or_error_entries_admitted':False,'old_derived_entries':len(seed['entries']),'production_approved':False})
    return authorized

@contextmanager
def cached_fork_provider(public_url,anchor_number,anchor_hash,evidence_dir,requests_per_second=.5):
    assert public_url==PUBLIC_ENDPOINT and anchor_number==BLOCK and anchor_hash==ANCHOR and requests_per_second==.5
    directory=Path(evidence_dir);directory.parent.mkdir(parents=True,exist_ok=True)
    seed=derive_seed(directory.parent/'DERIVED_SEED.json')
    imported=prior_full_entries(seed,directory.parent/'PRIOR_CACHE_IMPORT.json')
    state={'post_count':0,'refused':False};deadline=time.monotonic()+900
    upstream=(directory.parent/'upstream-wire.jsonl').open('x',encoding='utf8',newline='\n')
    core=None
    def post(body):
        assert not state['refused'] and time.monotonic()<deadline and state['post_count']<600
        state['post_count']+=1
        status,response=F._https_post(PUBLIC_ENDPOINT,body)
        upstream.write(json.dumps({'request_bytes_utf8':body.decode(),'request_sha256':sha(body),'http_status':status,
            'response_bytes_utf8':response.decode(errors='strict'),'response_sha256':sha(response)},separators=(',',':'))+'\n');upstream.flush()
        refused=status!=200
        if status==200:
            answer=F._loads(response)
            refused=isinstance(answer,dict)and isinstance(answer.get('error'),dict)and answer['error'].get('code')in(-32005,-32029,-32601,-32011)
        if refused:state['refused']=True;core._closing.set()
        return status,response
    class ExportCache(F._ForkCache):
        def __init__(self,*args,**kwargs):
            self.known={};super().__init__(*args,**kwargs)
        def handle(self,raw):
            status,response=super().handle(raw)
            try:
                req=F._loads(raw);method,params=self._validate(req);key=F._digest({'method':method,'params':params})
                if key in self._cache:self.known[key]={'method':method,'params':copy.deepcopy(params)}
            except (ValueError,KeyError,PermissionError,TypeError):pass
            return status,response
        def close(self,completed):
            if not self._finished:
                dump(self._directory/'full-cache.json',{'schema':1,'anchor_number':BLOCK,'anchor_hash':ANCHOR,
                    'entries':{k:dict(self.known[k],result=copy.deepcopy(v),result_sha256=F._digest(v))for k,v in self._cache.items()},
                    'derived_seed_sha256':sha((directory.parent/'DERIVED_SEED.json').read_bytes()),
                    'prior_full_export_sha256':'65c17dd1bbde06fb95bda969a29fe1c512bef77c4a4de7b74053d31125e02733','prior_import_manifest_sha256':sha((directory.parent/'PRIOR_CACHE_IMPORT.json').read_bytes()),
                    'production_approved':False})
            super().close(completed)
    core=ExportCache(PUBLIC_ENDPOINT,BLOCK,ANCHOR,directory,.5,_post=post)
    server=thread=None;completed=False
    try:
        core.verify_anchor()
        status,raw=core.handle(F._bytes({'jsonrpc':'2.0','id':3,'method':'eth_getBlockByNumber','params':['0x0',False]}))
        answer=F._loads(raw);assert status==200 and answer.get('result',{}).get('hash')==GENESIS and answer['result'].get('number')=='0x0'
        dump(directory.parent/'FRESH_IDENTITY.json',{'chain_id':4663,'anchor_number':BLOCK,'anchor_hash':ANCHOR,'genesis_hash':GENESIS,'fresh_network_verified':True})
        for key,row in imported.items():
            if key in core._cache:assert F._digest(core._cache[key])==row['result_sha256']
            else:core._cache[key]=copy.deepcopy(row['result']);core._cache_bytes+=len(F._bytes(row['result']))
            core.known[key]={'method':row['method'],'params':copy.deepcopy(row['params'])}
        core._record('verified_full_seed_loaded',entries=len(imported),old_derived_entries=len(seed['entries']),seed_sha256=sha((directory.parent/'DERIVED_SEED.json').read_bytes()),full_export_sha256='65c17dd1bbde06fb95bda969a29fe1c512bef77c4a4de7b74053d31125e02733')
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.0'
            def log_message(self,*_args):pass
            def setup(self):super().setup();self.connection.settimeout(5)
            def do_POST(self):
                port=self.server.server_address[1];lengths=self.headers.get_all('Content-Length',[])
                valid=self.path=='/'and self.headers.get_all('Host',[])==[f'127.0.0.1:{port}']and len(lengths)==1 and lengths[0].isdecimal()and 0<int(lengths[0])<=F.MAX_REQUEST and self.headers.get_all('Transfer-Encoding')is None and self.headers.get_all('Expect')is None
                if valid:
                    body=self.rfile.read(int(lengths[0]));status,raw=core.handle(body)if len(body)==int(lengths[0])else(400,F._bytes(core._error(None,'Incomplete request')))
                else:status,raw=400,F._bytes(core._error(None,'Invalid request framing'))
                try:
                    self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Connection','close');self.end_headers();self.wfile.write(raw)
                except OSError:pass
        class Server(ThreadingHTTPServer):daemon_threads=False;request_queue_size=128
        server=Server(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.05},daemon=True);thread.start()
        yield SimpleNamespace(url=f'http://127.0.0.1:{server.server_address[1]}',evidence_dir=directory)
        completed=True
    finally:
        core._closing.set()
        if server:server.shutdown();server.server_close()
        if thread:thread.join(timeout=5)
        core.close(completed);upstream.close()
