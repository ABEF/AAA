"""Actual unsigned manual reviews on NEW owned local Anvil only.

Accepts no RPC URL, private key, signer, public-chain or existing-node target.
The explicit test exporter supplies authenticated setup/delta state. Production
readers prepare every operation unchanged before a disposable governance EOA is
impersonated on this process's own chain. No existing service/journal is touched.
"""
from __future__ import annotations
import argparse
import datetime as dt
import gzip
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from frontend_api.service import Projection, ROLES, ZERO
from frontend_api.portfolio_v6 import ROLES as PORTFOLIO_ROLES
from zzz_ops import manual_lp_review as manual
from zzz_ops import management_review as management
from zzz_ops import operator_review as offline
from zzz_ops.abi import calldata,decode_words,keccak256
from zzz_ops.errors import RpcError
from zzz_ops.work_budget import consume,timeout

CHAIN=31337
BLOCK_GAS=32_000_000
PROFILE_GAS=24_000_000
READER_ROLES=ROLES+('principal_exit','rewards_canonical','seadrop_mint','seadrop')+PORTFOLIO_ROLES
EXTRA_ROLES=tuple(sorted(manual.EXTRAS))
PROTECTED_PORTS=frozenset((8902,57306))
READS=frozenset(('web3_clientVersion','eth_chainId','eth_blockNumber','eth_getBlockByNumber',
    'eth_getBlockByHash','eth_getCode','eth_getBalance','eth_getTransactionByHash',
    'eth_getTransactionReceipt','eth_getTransactionCount','eth_call','eth_estimateGas',
    'eth_gasPrice','debug_traceCall','debug_traceTransaction'))
MUTATIONS=frozenset(('evm_setNextBlockTimestamp','evm_mine','anvil_impersonateAccount','eth_sendTransaction'))


def require(condition,message):
    if not condition:raise ValueError(message)


class OwnedRPCFailure(RpcError):
    def __init__(self,error):
        self.error=error
        super().__init__('The owned local RPC returned an error; exact local response retained')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def save(path,value):
    # Genesis, receipts and call trees are evidence, not operator-review
    # artifacts. Their independent file ceiling never changes review limits.
    path=Path(path);raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    require(len(raw)<=64*1024*1024,'Bounded local evidence file exceeded64MiB')
    with path.open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return sha(raw)


def minimal_environment(binary_directory):
    names=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE',
        'LOCALAPPDATA','APPDATA','PROGRAMDATA')
    result={name:os.environ[name] for name in names if name in os.environ}
    result['PATH']=str(binary_directory)+os.pathsep+str(Path(result.get('SystemRoot','C:/Windows'))/'System32')
    return result


def canonical_type(item):
    return ('('+','.join(canonical_type(x) for x in item['components'])+')'+item['type'][5:]
        if item['type'].startswith('tuple') else item['type'])


def event_signature(item):return item['name']+'('+','.join(canonical_type(x) for x in item['inputs'])+')'


def dynamic_string(words,index,*,base=0):
    start=base+int(words[index],16)//32;length=int(words[start],16)
    require(length<=4096,'Oversized exporter string')
    return bytes.fromhex(''.join(words[start+1:]))[:length].decode('utf-8')


def dynamic_array(words,index):
    start=int(words[index],16)//32;length=int(words[start],16)
    require(length<=64,'Unbounded exporter array')
    require(start+1+length<=len(words),'Truncated exporter array')
    return words[start+1:start+1+length]


def dynamic_bytes(words,index):
    start=int(words[index],16)//32;length=int(words[start],16)
    require(length<=262144,'Unbounded exporter calldata')
    return '0x'+''.join(words[start+1:])[:length*2]


def parse_export(folder,artifact_path):
    """Authenticate the new selected method's literal events and dump hashes."""
    raw=(folder/'forge.json').read_bytes();result=json.loads(raw)
    methods=[(suite,name,row) for suite,group in result.items() for name,row in group.get('test_results',{}).items()]
    require(len(methods)==1 and methods[0][2]['status']=='Success','Exactly one successful new host method is required')
    artifact=json.loads(artifact_path.read_bytes())
    events={'0x'+keccak256(event_signature(item).encode()).hex():item['name']
        for item in artifact['abi'] if item['type']=='event' and item['name'].startswith('Recovery')}
    exports=[];bindings=None;asset=None;selected={};calls={};baseline=None;materialized={};reference_failures={};reference_quotes={}
    for log in methods[0][2]['logs']:
        name=events.get(log['topics'][0]);words=decode_words(log['data'])
        if name=='RecoveryBindings':
            offset=int(words[0],16)//32;count=int(words[offset],16);base=offset+1
            require(count==len(READER_ROLES)+len(EXTRA_ROLES),'Unexpected recovery role count')
            names=[dynamic_string(words,base+i,base=base) for i in range(count)]
            addresses=['0x'+word[-40:] for word in dynamic_array(words,1)]
            hashes=['0x'+word for word in dynamic_array(words,2)]
            require(names==list(READER_ROLES+EXTRA_ROLES),'Recovery role order differs')
            require(len(addresses)==len(hashes)==count and len(set(addresses))==count,'Recovery bindings are not distinct')
            bindings=dict(zip(names,({'address':a,'code_hash':h} for a,h in zip(addresses,hashes))))
        elif name=='RecoveryAsset':asset={'address':'0x'+words[0][-40:],'decimals':int(words[1],16)}
        elif name=='RecoverySelected':
            label=dynamic_string(words,0);schema=int(words[1],16);action=dynamic_string(words,2)
            require(len(words)>=15,'Truncated selected emergency request')
            signed=lambda word:int(word,16)-(1<<256) if int(word,16)>=1<<255 else int(word,16)
            selected[label]={'schema':schema,'action':action,'bucket':str(int(words[3],16)),
                'checks':str(int(words[5],16)),'lower':str(signed(words[6])),'upper':str(signed(words[7])),
                'swapPool':'0x'+words[8],'zeroForOne':bool(int(words[9],16)),
                'amountIn':str(int(words[10],16)),'minimumOut':str(int(words[11],16)),
                'minimumLiquidity':str(int(words[12],16)),'deadline':str(int(words[13],16)),
                'review_notes_sha256':sha(('Explicit controlled local '+label).encode()),
                'evidence_sha256':[sha(raw)]}
            if schema==2:selected[label]['expected_position_status']='parked'
        elif name=='RecoveryUnsignedCall':
            label=dynamic_string(words,0)
            calls[label]={'sender':'0x'+words[1][-40:],'to':'0x'+words[2][-40:],
                'value':int(words[3],16),'data':dynamic_bytes(words,4),'cap':int(words[5],16),'padding_bps':int(words[6],16),
                'bucket':int(words[7],16),'nft_ids':[int(x,16) for x in dynamic_array(words,8)]}
        elif name=='RecoveryBaseline':baseline={'path':dynamic_string(words,0),'keccak256':'0x'+words[1]}
        elif name=='RecoveryReferenceRejection':
            reference_failures[dynamic_string(words,0)]={'request':dynamic_bytes(words,1),'reason':dynamic_bytes(words,2),
                'before_state':'0x'+words[3],'after_state':'0x'+words[4],'original_request_hash':'0x'+words[5]}
        elif name=='RecoveryReferenceQuote':
            output,liquidity,minimum_out,minimum_liquidity=[int(word,16) for word in words[1:5]]
            require(output>=minimum_out and liquidity>=minimum_liquidity,'Recorded reference quote did not meet original floors')
            reference_quotes[dynamic_string(words,0)]={'output':str(output),'liquidity':str(liquidity),
                'original_minimum_out':str(minimum_out),'original_minimum_liquidity':str(minimum_liquidity),
                'swap_and_lp_floors_feasible':True}
        elif name=='RecoveryCodeMaterialized':
            address_='0x'+log['topics'][1][-40:] if len(log['topics'])>1 else '0x'+words[0][-40:]
            start=0 if len(log['topics'])>1 else 1
            materialized[address_]={'hash':'0x'+words[start],'length':int(words[start+1],16)}
        elif name=='RecoveryState':
            label=dynamic_string(words,0)
            exports.append({'label':label,'path':dynamic_string(words,1),'delta_keccak256':'0x'+words[2],
                'number':int(words[3],16),'timestamp':int(words[4],16),'chain_id':int(words[5],16),
                'governance':'0x'+words[6][-40:],'bucket':int(words[7],16),
                'nft_ids':[int(x,16) for x in dynamic_array(words,8)],'setup_hash':'0x'+words[9],
                'harness':log['address'].lower()})
    require(bindings is not None and asset is not None and baseline is not None and exports,'Incomplete recovery export')
    for item in exports:
        require(re.fullmatch(r'[a-z0-9-]{1,64}',item['label']) is not None,'Invalid recovery label')
        require(item['chain_id']==CHAIN,'Exporter must use the isolated local chain')
        item.update(bindings=bindings,asset=asset,baseline=baseline,materialized=materialized,
            selection=selected.get(item['label']),call=calls.get(item['label']),
            forge_sha256=sha(raw),method=methods[0][1],reference_rejection=reference_failures.get(item['label']),
            reference_quote=reference_quotes.get(item['label']))
    return exports


class OwnedNode:
    """A new PID-bound loopback process; admin calls cannot target an old node."""
    def __init__(self,binary,genesis,output):
        self.binary=Path(binary);self.genesis=genesis;self.output=Path(output)
        self.records=[];self.proc=None;self.anchor=None;self.timestamp=genesis['timestamp'];self.pending=None;self.runtime_pins=None;self.created=False
        self.http=None;self.http_lock=threading.Lock()
        self.deadline=time.monotonic()+600
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1]
        require(self.port not in PROTECTED_PORTS,'Protected historical port selected')
        self.url='http://127.0.0.1:'+str(self.port)

    def _listening_pid(self):
        require(os.name=='nt','This reviewed launcher requires Windows PID ownership checks')
        environment=minimal_environment(self.binary.parent)
        netstat=Path(environment.get('SystemRoot','C:/Windows'))/'System32/netstat.exe'
        run=subprocess.run([str(netstat),'-ano','-p','TCP'],capture_output=True,env=environment,
            timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        require(run.returncode==0,'Local socket ownership check failed')
        # Parse in memory; unrelated machine endpoints are never logged.
        rows=[line.split() for line in run.stdout.decode(errors='replace').splitlines()]
        pids={int(row[-1]) for row in rows if len(row)>=5 and row[0]=='TCP'
            and row[1]=='127.0.0.1:'+str(self.port) and row[2]=='0.0.0.0:0' and row[-1].isdigit()}
        return pids

    def _wire(self,method,params=None,*,maximum_timeout=60):
        require(self.proc is not None and self.proc.poll() is None,'Owned node is not running')
        require(method in READS|MUTATIONS,'Unreviewed local RPC method')
        remaining=self.deadline-time.monotonic();require(remaining>0,'Owned case exceeded its bounded lifetime')
        request={'jsonrpc':'2.0','id':len(self.records)+1,'method':method,'params':params or []}
        consume('posts')
        wire_timeout=timeout(min(maximum_timeout,remaining));started=time.monotonic()
        # Literal loopback only: no environment/system proxy discovery and no
        # automatic reconnect retry of an uncertain operation. A later distinct
        # read may create a new connection after this one has been closed.
        with self.http_lock:
            try:
                if self.http is None:self.http=http.client.HTTPConnection('127.0.0.1',self.port,timeout=wire_timeout)
                self.http.timeout=wire_timeout
                if self.http.sock is not None:self.http.sock.settimeout(wire_timeout)
                self.http.request('POST','/',json.dumps(request).encode(),{'Content-Type':'application/json'})
                response=self.http.getresponse();raw=response.read(64*1024*1024+1)
                require(response.status==200,'Owned local RPC HTTP refusal')
            except BaseException:
                if self.http is not None:self.http.close();self.http=None
                raise
        require(len(raw)<=64*1024*1024,'Bounded local RPC response exceeded')
        value=json.loads(raw);self.records.append({'method':method,'params':params or [],'response':value,
            'actual_wire_seconds':time.monotonic()-started})
        if 'error' in value:raise OwnedRPCFailure(value['error'])
        return value['result']

    def call(self,method,params=None):
        require(method in READS,'Preparation transport is read-only')
        value=self._wire(method,params)
        return int(value,16) if method=='eth_chainId' else value

    def assert_owned(self):
        require(self.proc is not None and self.proc.poll() is None,'Owned process stopped')
        require(self._listening_pid()=={self.proc.pid},'Loopback listener is not the exact owned PID')
        require(int(self._wire('eth_chainId'),16)==CHAIN,'Owned chain identity changed')
        header=self._wire('eth_getBlockByNumber',[self.genesis['number'],False])
        require(self.anchor is not None and header['hash']==self.anchor,'Owned genesis anchor changed')
        require(self.runtime_pins is not None,'Current runtime identities have not been authenticated')
        for target,expected in self.runtime_pins.items():
            code=self._wire('eth_getCode',[target,'latest'])
            require('0x'+keccak256(bytes.fromhex(code[2:])).hex()==expected,'Owned current runtime identity changed')

    def admin(self,method,params=None):
        require(method in MUTATIONS,'Unreviewed state-changing method')
        self.assert_owned();return self._wire(method,params)

    def __enter__(self):
        try:return self._start()
        except BaseException:
            self.__exit__(*sys.exc_info());raise

    def _start(self):
        self.output.mkdir(parents=True,exist_ok=False);self.created=True
        save(self.output/'genesis.json',self.genesis)
        command=[str(self.binary),'--host','127.0.0.1','--port',str(self.port),'--accounts','0','--silent',
            '--init',str(self.output/'genesis.json'),'--gas-limit',str(BLOCK_GAS),'--chain-id',str(CHAIN),'--hardfork','cancun']
        self.log=(self.output/'anvil.log').open('xb')
        self.proc=subprocess.Popen(command,cwd=self.output,env=minimal_environment(self.binary.parent),stdout=self.log,
            stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        startup_deadline=time.monotonic()+20
        while time.monotonic()<startup_deadline:
            require(self.proc.poll() is None,'Owned node exited during startup')
            if self._listening_pid()=={self.proc.pid}:break
            time.sleep(.1)
        else:raise ValueError('Owned node did not bind its selected loopback port')
        require(int(self._wire('eth_chainId'),16)==CHAIN,'Owned node has wrong chain')
        require('anvil' in self._wire('web3_clientVersion').lower(),'Expected the owned Anvil process')
        head=self._wire('eth_getBlockByNumber',['latest',False])
        require(head['number']==self.genesis['number'] and head['timestamp']==self.genesis['timestamp']
            and int(head['gasLimit'],16)==BLOCK_GAS,'Restored local genesis differs')
        self.anchor=head['hash'];self.timestamp=int(head['timestamp'],16)
        save(self.output/'process.json',{'pid':self.proc.pid,'port':self.port,'chain_id':CHAIN,
            'command':command,'genesis_hash':self.anchor,'node_environment':'Explicit minimal runtime whitelist; no wallet/RPC variables forwarded'})
        return self

    def bind_runtimes(self,pins):
        for target,expected in pins.items():
            code=self._wire('eth_getCode',[target,'latest'])
            require('0x'+keccak256(bytes.fromhex(code[2:])).hex()==expected,'Restored runtime differs from authenticated export')
        self.runtime_pins=dict(pins)

    def mine(self,count=1):
        for _ in range(count):
            self.timestamp=max(self.timestamp+1,int(time.time()))
            self.admin('evm_setNextBlockTimestamp',[self.timestamp]);self.admin('evm_mine',[])

    def __exit__(self,kind,error,traceback):
        if self.http is not None:self.http.close();self.http=None
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=10)
        if hasattr(self,'log'):self.log.close()
        if self.created:
            with gzip.open(self.output/'rpc-records.json.gz','wt',encoding='utf-8') as stream:json.dump(self.records,stream,separators=(',',':'))
            save(self.output/'cleanup.json',{'owned_pid':self.proc.pid if self.proc else None,
                'owned_node_stopped':self.proc is None or self.proc.poll() is not None,'pending_submission':self.pending,
                'failure_type':type(error).__name__ if error else None,'old_environment_mutations':0})


class RecordingProxy:
    """One bounded local read-only listener for the real production CLI."""
    def __init__(self,node):self.node=node

    def __enter__(self):
        node=self.node;node.assert_owned()
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.0'
            def log_message(self,*args):pass
            def setup(self):super().setup();self.connection.settimeout(5)
            def do_POST(self):
                self.close_connection=True
                expected='127.0.0.1:'+str(self.server.server_port)
                query=None
                try:
                    require(self.path=='/' and self.headers.get_all('Host')==[expected],'Unexpected local proxy host/path')
                    require(self.headers.get_all('Content-Type')==['application/json'],'Unexpected local proxy media type')
                    lengths=self.headers.get_all('Content-Length')
                    require(lengths is not None and len(lengths)==1 and lengths[0].isdigit(),'Invalid local proxy length')
                    length=int(lengths[0]);require(1<=length<=262144,'Unbounded local proxy request')
                    query=json.loads(self.rfile.read(length))
                    require(type(query) is dict and query.get('jsonrpc')=='2.0' and query.get('method') in READS
                        and isinstance(query.get('params',[]),list),'Only individual read requests are permitted')
                    require(node.proc is not None and node.proc.poll() is None,'Owned node stopped during preparation')
                    result=node._wire(query['method'],query.get('params',[]),maximum_timeout=5)
                    response={'jsonrpc':'2.0','id':query.get('id'),'result':result}
                except OwnedRPCFailure as exc:
                    response={'jsonrpc':'2.0','id':query.get('id') if isinstance(query,dict) else None,'error':exc.error}
                except Exception:
                    response={'jsonrpc':'2.0','id':query.get('id') if isinstance(query,dict) else None,
                        'error':{'code':-32000,'message':'Owned read-only rehearsal proxy refused the request'}}
                raw=json.dumps(response,separators=(',',':')).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers()
                try:self.wfile.write(raw)
                except (OSError,TimeoutError):pass
        class Server(HTTPServer):request_queue_size=4
        self.server=Server(('127.0.0.1',0),Handler)
        require(self.server.server_port not in PROTECTED_PORTS,'Protected read-only proxy port selected')
        self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.1},daemon=True)
        self.thread.start();return self

    def __exit__(self,*ignored):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=10)
        require(not self.thread.is_alive(),'Owned read-only proxy did not stop')


def verify_proxy_refusals(proxy,node):
    probes=[('mutation',{'jsonrpc':'2.0','id':1,'method':'eth_sendTransaction','params':[{}]},None),
        ('batch',[{'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]}],None),
        ('wrong_host',{'jsonrpc':'2.0','id':1,'method':'eth_chainId','params':[]},'wrong.invalid'),
        ('unhashable_method',{'jsonrpc':'2.0','id':1,'method':[],'params':[]},None)]
    results=[]
    for name,payload,host in probes:
        count=len(node.records);headers={'Content-Type':'application/json'}
        if host:headers['Host']=host
        request=urllib.request.Request(proxy.url,json.dumps(payload).encode(),headers=headers)
        with urllib.request.urlopen(request,timeout=5) as response:result=json.load(response)
        require('error' in result and len(node.records)==count,'Read-only proxy forwarded a forbidden request')
        results.append({'probe':name,'refused_before_owned_rpc':True})
    return results


def restore(case,folder):
    paths=[Path(case['baseline']['path']).resolve(),Path(case['path']).resolve()]
    require(all(path.is_relative_to(folder.resolve()) for path in paths),'Exporter state path escapes its owned method folder')
    base_raw,delta_raw=(path.read_bytes() for path in paths)
    require('0x'+keccak256(base_raw).hex()==case['baseline']['keccak256']==case['setup_hash'],'Setup state authentication failed')
    require('0x'+keccak256(delta_raw).hex()==case['delta_keccak256'],'Pre-call state authentication failed')
    base,delta=json.loads(base_raw),json.loads(delta_raw)
    alloc={target.lower():{**row,'storage':dict(row.get('storage',{}))} for target,row in base.items()}
    zeros=0
    for target,row in delta.items():
        target=target.lower();previous=alloc.get(target,{})
        if previous.get('code') and row.get('code'):require(previous['code']==row['code'],'Restored runtime changed between setup and delta')
        old=previous.get('storage',{});new=row.get('storage',{})
        zeros+=sum(int(value,16)==0 and int(old.get(slot,'0x0'),16)!=0 for slot,value in new.items())
        alloc[target]={**previous,**row,'storage':{**old,**new}}
    for role,item in case['bindings'].items():
        require(item['address'] in alloc,'A required pinned role is absent from the authenticated export')
        code=alloc[item['address']].get('code','0x')
        require('0x'+keccak256(bytes.fromhex(code[2:])).hex()==item['code_hash'],'Exported role runtime hash differs')
    token=case['asset']['address'];require(token in alloc and alloc[token].get('code'),'Fixed token runtime missing')
    token_hash='0x'+keccak256(bytes.fromhex(alloc[token]['code'][2:])).hex()
    genesis={'config':{'chainId':CHAIN,'homesteadBlock':0,'eip150Block':0,'eip155Block':0,'eip158Block':0,
        'byzantiumBlock':0,'constantinopleBlock':0,'petersburgBlock':0,'istanbulBlock':0,'berlinBlock':0,
        'londonBlock':0,'terminalTotalDifficulty':0,'shanghaiTime':0,'cancunTime':0},
        'number':hex(case['number']),'timestamp':hex(case['timestamp']),'nonce':'0x0','extraData':'0x',
        'gasLimit':hex(BLOCK_GAS),'difficulty':'0x0','mixHash':'0x'+'0'*64,'coinbase':ZERO,'baseFeePerGas':'0x0','alloc':alloc}
    provenance={'setup_sha256':sha(base_raw),'delta_sha256':sha(delta_raw),'setup_keccak256':case['setup_hash'],
        'delta_keccak256':case['delta_keccak256'],'setup_accounts':len(base),'delta_accounts':len(delta),
        'merged_accounts':len(alloc),'explicit_nonzero_to_zero_overrides':zeros,
        'state_scope':'Exact authenticated setup plus per-slot pre-call delta; no invented balances, code or header data.'}
    return genesis,token_hash,provenance


def inputs(node,case,token_hash,*,read_url):
    config={'schema':2,'chain_id':CHAIN,'rpc_urls':[read_url],'accounting_version':7,'custody_version':5,
        'mint_integration_version':2,'execution_price_version':1,'protocol_policy_version':1,'fee_intake_version':1,
        'royalty_reporting':{'schema':5,'converter':None},'deployment_block':case['number'],
        'deployment_block_hash':node.anchor,'confirmations':2,'max_block_age_seconds':120,
        'contracts':{role:case['bindings'][role] for role in READER_ROLES},
        'assets':[{'address':ZERO,'decimals':18,'symbol':'ETH','code_hash':None},
            {'address':case['asset']['address'],'decimals':case['asset']['decimals'],'symbol':'ZZZ','code_hash':token_hash}]}
    catalog=offline.Catalog();p=Projection(config)
    policy={'schema':1,'projection_sha256':p.identity,'reference_sha256':catalog.reference_sha256,
        'source_snapshot_sha256':catalog.source_snapshot_sha256,'governance':case['governance'],
        'extra_contracts':{role:case['bindings'][role] for role in EXTRA_ROLES},
        'fee_policy':{'max_gas_limit':str(PROFILE_GAS),'max_gas_price_wei':'10000000000',
            'max_network_fee_wei':'240000000000000000','estimate_includes_all_fees':True,
            'review_hash':'0x'+keccak256(b'CONTROLLED LOCAL ONLY gas budget, not Robinhood fee approval').hex()}}
    return config,policy,catalog


def static_read(node,pins,role,signature,*args,count=1,block='latest'):
    target=pins[role]['address'] if role in pins else role
    safe=[('0x'+'0'*39+'1') if value==ZERO else value for value in args]
    data=calldata(signature,*safe)
    for index,value in enumerate(args):
        if value==ZERO:data=data[:10+64*index]+'0'*64+data[10+64*(index+1):]
    words=decode_words(node.call('eth_call',[{'to':target,'data':data},block]))
    require(len(words)==count,'A required actual state getter returned an incompatible word count')
    return [int(word,16) for word in words]


def state(node,case):
    pins=case['bindings'];bucket=case['bucket'];token=case['asset']['address'];head=node.call('eth_getBlockByNumber',['latest',False])
    block={'blockHash':head['hash'],'requireCanonical':True}
    def read(role,signature,*args,count=1):return static_read(node,pins,role,signature,*args,count=count,block=block)
    position=read('vault','group(uint256)',bucket,count=8);main=position[1];residual=read('liquidity','secondaryId(uint256)',main)[0]
    legs=[]
    for identifier in (main,residual):
        if identifier:
            ticks=read('liquidity','ticks(uint256)',identifier,count=2)
            ticks=[x-(1<<256) if x>=1<<255 else x for x in ticks]
            legs.append({'id':str(identifier),'ticks':ticks,'liquidity':str(read('position_manager','getPositionLiquidity(uint256)',identifier)[0]),
                'owner':'0x'+f'{read("position_manager","ownerOf(uint256)",identifier)[0]:040x}',
                'amounts_raw':list(map(str,read('liquidity','amounts(uint256)',identifier,count=2)))})
    membership='0x'+f'{read("access","module(bytes32)","0x"+keccak256(b"ZZZMembership").hex())[0]:040x}'
    holdings=[]
    for identifier in case['nft_ids']:
        holdings.append({'id':str(identifier),'owner':'0x'+f'{read("nft","ownerOf(uint256)",identifier)[0]:040x}',
            'shares':str(read('vault','sharesOf(uint256)',identifier)[0]),
            'eligible':bool(read(membership,'eligible(uint256)',identifier)[0]),
            'royalty_weight':read('royalties','weightOf(uint256)',identifier)[0],
            'claimable_lp_raw':[str(read('rewards','claimable(uint256,address)',identifier,asset)[0]) for asset in (ZERO,token)]})
    books=[]
    for asset in (ZERO,token):
        balance=lambda role: int(node.call('eth_getBalance',[pins[role]['address'],block]),16) if asset==ZERO else read(token,'balanceOf(address)',pins[role]['address'])[0]
        books.append({'asset':asset,'compound':str(read('fees','compoundBalance(uint256,address)',bucket,asset)[0]),
            'buyback':str(read('fees','buybackBalance(address)',asset)[0]),'dust':str(read('fees','dust(uint256,address)',bucket,asset)[0]),
            'accounted':str(read('fees','accounted(address)',asset)[0]),'fees_balance':str(balance('fees')),
            'liabilities':str(read('rewards','liabilities(address)',asset)[0]),'rewards_balance':str(balance('rewards')),
            'vault_balance':str(balance('vault')),'manager_balance':str(balance('liquidity')),'executor_balance':str(balance('lp_position_executor'))})
    gov=case['governance']
    return {'head':head,'position':list(map(str,position)),'legs':legs,'secondary_id':str(residual),
        'active_secondary_count':read('liquidity','activeSecondaryCount()')[0],
        'total_shares':str(read('vault','bucketTotalShares(uint256)',bucket)[0]),
        'tree':list(map(str,read('rewards','allocationTree(uint256)',bucket,count=3))),
        'nfts':holdings,'books':books,'paused':bool(read('access','paused()')[0]),
        'governance':'0x'+f'{read("access","governance()")[0]:040x}',
        'governance_code':node.call('eth_getCode',[gov,block]),'governance_eth':node.call('eth_getBalance',[gov,block]),
        'governance_zzz':str(read(token,'balanceOf(address)',gov)[0]),
        'last_compound':str(read('budget','lastCompound(uint256)',bucket)[0]),
        'parking_nonce':str(read('principal_exit','parkingNonce(uint256)',bucket)[0]),
        'custody_epoch':str(read('principal_exit','custodyEpoch(uint256)',bucket)[0]),
        'royalty_total_weight':str(read('royalties','totalWeight()')[0]),
        'execution_active':bool(read('oracle','executionActive()')[0]),
        'emergency_active':bool(read('budget','emergencyActive()')[0]),
        'consolidation_active':bool(read('principal_exit','consolidationActive()')[0]),
        'desired_residual_enabled':bool(read('portfolio_policy','enabled(bytes32)','0x'+f'{position[0]:064x}')[0]),
        'registry_revision':str(read('pools','configurationRevision()')[0]),
        'portfolio_control':'0x'+f'{read("portfolio_policy","controlFingerprint(bytes32)","0x"+f"{position[0]:064x}")[0]:064x}',
        'canonical_state':read('access','canonicalState()')[0],'exit_started':bool(read('access','lpExitStarted()')[0]),
        'vault_allowances':[str(read(token,'allowance(address,address)',pins['vault']['address'],pins[role]['address'])[0])
            for role in ('liquidity','lp_position_executor')]}


def prepare_cli(python,node,config,policy,selection,*,label,management_action=False):
    destination=node.output/label;destination.mkdir(exist_ok=False)
    for name,value in [('read-config',config),('policy',policy),('selection',selection)]:save(destination/(name+'.json'),value)
    script=ROOT/'scripts'/('prepare-operator-management.py' if management_action else 'prepare-manual-lp.py')
    command=[str(python),'-I','-B','-X','utf8',str(script)]
    for name in ('read-config','policy','selection'):command+=['--'+name,str(destination/(name+'.json'))]
    artifact_path=destination/'review.json';command+=['--output',str(artifact_path)]
    pins={name:sha((ROOT/name).read_bytes()) for name in ('zzz_ops/manual_lp_review.py','zzz_ops/management_review.py',
        'zzz_ops/management_base.py','zzz_ops/management_custody.py','frontend_api/service.py','frontend_api/portfolio_v6.py')}
    start=time.monotonic();first=len(node.records)
    with (destination/'stdout.json').open('xb') as out,(destination/'stderr.json').open('xb') as err:
        run=subprocess.run(command,cwd=destination,env=minimal_environment(Path(python).parent),stdout=out,stderr=err,
            timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    after={name:sha((ROOT/name).read_bytes()) for name in pins}
    save(destination/'cli-execution.json',{'command':command,'exit_code':run.returncode,'seconds':time.monotonic()-start,
        'recorded_rpc_requests':len(node.records)-first,'source_before':pins,'source_after':after,
        'source_unchanged':pins==after,'default_time_time_clock':True,'rpc_transport':'Actual production Rpc via owned read-only recording proxy'})
    require(pins==after,'Preparer source changed during the actual CLI')
    require(run.returncode==0 and artifact_path.is_file(),'Actual production CLI did not produce a complete valid review')
    artifact=json.loads(artifact_path.read_bytes())
    require(artifact.get('ready_for_submission') is False and artifact.get('production_approved') is False,
        'Unsigned preparation cannot grant production or submission approval')
    return artifact,destination


def execute_review(node,case,artifact,destination):
    """Only this fresh node may execute the exact reviewed call, once."""
    tx=dict(artifact['transaction']);gov=case['governance'];pins=case['bindings']
    require(tx['from']==gov and tx['to']==pins['principal_exit']['address'] and tx['value']=='0x0'
        and tx['chainId']==hex(CHAIN),'Unsigned operation envelope differs from local governance scope')
    initial,final=artifact['simulation']['initial'],artifact['simulation']['final']
    gas=int(final['padded_gas'] if 'padded_gas' in final else final['transaction_gas'])
    require(int(final['gas_limit_cap'])==PROFILE_GAS and gas<=PROFILE_GAS,'Reviewed operation exceeds the unchanged24M profile')
    block={'blockHash':artifact['final_control_head']['hash'],'requireCanonical':True}
    capped={**tx,'gas':hex(PROFILE_GAS)}
    require(node.call('eth_call',[capped,block])=='0x','Exact full-cap operation simulation failed')
    exact={**tx,'gas':hex(gas)}
    require(node.call('eth_call',[exact,block])=='0x','Exact25%-padded operation simulation failed')
    trace=node.call('debug_traceCall',[capped,block,{'tracer':'callTracer','tracerConfig':{'withLog':True},'timeout':'60s'}])
    require(not trace.get('error') and trace.get('from','').lower()==gov and trace.get('to','').lower()==tx['to'],
        'Actual full-operation trace differs or failed')
    def frames(frame):
        yield frame
        for child in frame.get('calls',[]):yield from frames(child)
    require(not any(frame.get('to','').lower()==case['harness'] for frame in frames(trace)),
        'Production recovery called the omitted test harness')
    before=state(node,case);save(destination/'before.json',before)
    node.admin('anvil_impersonateAccount',[gov])
    nonce=node.call('eth_getTransactionCount',[gov,'pending'])
    submitted={**exact,'nonce':nonce,'gasPrice':hex(int(final['gas_price_wei']))}
    node.pending={'label':destination.name,'transaction':submitted,'hash':None,'state':'intent'}
    save(destination/'intent.json',node.pending)
    node.timestamp=max(node.timestamp+1,int(time.time()));node.admin('evm_setNextBlockTimestamp',[node.timestamp])
    txhash=node.admin('eth_sendTransaction',[submitted]);node.pending.update(hash=txhash,state='submitted')
    save(destination/'submitted.json',node.pending)
    receipt=None;deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        receipt=node.call('eth_getTransactionReceipt',[txhash])
        if receipt is not None:break
        time.sleep(.1)
    require(receipt is not None,'Local transaction receipt remains unresolved; no resend permitted')
    save(destination/'receipt.json',receipt)
    require(int(receipt['status'],16)==1,'The exact local governance transaction reverted')
    actual=node.call('eth_getTransactionByHash',[txhash]);save(destination/'transaction.json',actual)
    require(actual['from'].lower()==gov and actual['to'].lower()==tx['to'] and actual['input']==tx['data']
        and int(actual['value'],16)==0 and int(actual['gas'],16)==gas,'Included transaction differs from reviewed calldata/envelope')
    included=node.call('eth_getBlockByHash',[receipt['blockHash'],False])
    require(included['hash']==receipt['blockHash'] and int(included['timestamp'],16)<=int(artifact['expires_at']),
        'Receipt inclusion missed the original review expiry')
    used=int(receipt['gasUsed'],16);require(used<=gas,'Actual receipt exceeded reviewed gas')
    receipt_trace=node.call('debug_traceTransaction',[txhash,{'tracer':'callTracer','tracerConfig':{'withLog':True},'timeout':'60s'}])
    require(not receipt_trace.get('error'),'Actual included transaction trace failed')
    save(destination/'call-trace.json',trace);save(destination/'receipt-trace.json',receipt_trace)
    node.pending.update(state='confirmed');node.timestamp=int(included['timestamp'],16)
    node.mine(2);after=state(node,case);save(destination/'after.json',after)
    return before,after,receipt,{'transaction_hash':txhash,'receipt_gas_used':used,'cold_trace_call_gas':int(trace['gasUsed'],16),
        'initial_estimate':int(initial['estimated_gas']),'final_estimate':int(final['estimated_gas']),
        'required_25_percent_padded_gas':gas,'profile_cap':PROFILE_GAS,'remaining_profile_margin':PROFILE_GAS-gas,
        'full_cap_call_passed':True,'exact_padded_call_passed':True,'actual_local_receipt_success':True,
        'effective_gas_price_wei':int(receipt['effectiveGasPrice'],16),'receipt_local_gas_cost_wei':used*int(receipt['effectiveGasPrice'],16),
        'fee_scope':'Controlled local EVM gas only; no complete Robinhood fee or spending-policy approval.'}


def verify_post(node,case,before,after,receipt,*,action,minimum_liquidity=None,closed_by_receipt=False):
    pins=case['bindings'];old=list(map(int,before['position']));new=list(map(int,after['position']))
    require(before['paused'] and after['paused'],'Manual execution changed global pause state')
    require(after['governance']==case['governance'] and after['governance_code']=='0x','Governance identity is not the actual empty-code owner')
    require(after['canonical_state']==0 and not after['exit_started'],'Manual execution changed canonical/terminal lifecycle')
    require(after['registry_revision']==before['registry_revision'],'Manual execution changed registry controls')
    if action=='C':
        # completeConsolidation intentionally invalidates old samples/jitter,
        # even when desired mode was already OFF. That advances its control
        # fingerprint rather than preserving an obsolete review commitment.
        applied='0x'+keccak256(b'PortfolioApplied(uint256,bytes32,uint64)').hex()
        require(after['portfolio_control']!=before['portfolio_control'] and any(
            log['address'].lower()==pins['portfolio_policy']['address'] and log['topics'][0]==applied
            and int(log['topics'][1],16)==old[1] and int(log['topics'][2],16)==old[0]
            for log in receipt['logs']),'Consolidation did not acknowledge its intended control update')
    else:require(after['portfolio_control']==before['portfolio_control'],'Manual execution changed portfolio controls')
    require(not any(after[field] for field in ('execution_active','emergency_active','consolidation_active')),'An operation context leaked after the receipt')
    require(after['total_shares']==before['total_shares'] and after['tree'][0]==before['tree'][0], 'Aggregate share/accounting weight changed')
    require(after['royalty_total_weight']==before['royalty_total_weight'],'Royalty membership changed')
    require(len(before['nfts'])==len(after['nfts'])==len(case['nft_ids']),'NFT witness inventory differs')
    for prior,current in zip(before['nfts'],after['nfts']):
        require(current==prior,'An NFT owner, share, royalty right or funded LP claim changed')
    require(new[0]==old[0] and new[4]==old[4],'Pool identity or original contribution accounting changed')
    for prior,current in zip(before['books'],after['books']):
        for field in ('asset','buyback','dust','liabilities','rewards_balance','manager_balance','executor_balance'):
            require(current[field]==prior[field],'Existing rewards, reserves or protected prefunds changed')
        release=int(prior['compound']) if action=='D' else 0
        require(int(current['compound'])==int(prior['compound'])-release,'Designated compound movement differs')
        require(int(prior['accounted'])-int(current['accounted'])==release,'Compound release did not reconcile accounted reserves')
        require(int(prior['fees_balance'])-int(current['fees_balance'])==release,'Actual fee-controller backing did not match reserve release')
        require(int(current['fees_balance'])>=int(current['accounted']) and int(current['rewards_balance'])>=int(current['liabilities']),
            'Existing claims or protocol reserves lost their backing')
        require(int(current['accounted'])==sum(int(current[field]) for field in ('compound','buyback','dust')),'Reserve classifications do not reconcile')
    require(after['vault_allowances']==['0','0'],'A principal allowance remains after execution')
    spent=int(before['governance_eth'],16)-int(after['governance_eth'],16)
    require(spent==int(receipt['gasUsed'],16)*int(receipt['effectiveGasPrice'],16),'Governance paid anything beyond its actual local network gas')
    require(after['governance_zzz']==before['governance_zzz'],'Governance received/spent fixed-ZZZ principal')
    fee_topic='0x'+keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
    collected=[decode_words(log['data']) for log in receipt['logs'] if log['address'].lower()==pins['vault']['address']
        and log['topics'][0]==fee_topic]
    require(all(len(row)==2 and not any(int(word,16) for word in row) for row in collected),
        'The controlled no-new-fee assumption does not match actual receipt events')
    if action=='park':
        require(new[7]==4 and new[1]==0 and not after['legs'] and after['secondary_id']=='0','Parking did not close both physical legs')
        require(new[2]+new[3]>0 and after['active_secondary_count']==0,'Parked principal is missing or a residual remains')
        require(new[5:7]==old[5:7],'Parking changed previous centre/rebalance time')
        require(after['last_compound']==before['last_compound'],'Parking changed the compound clock')
    else:
        require(new[7]==1 and new[1]>0 and len(after['legs'])==1 and after['secondary_id']=='0'
            and after['active_secondary_count']==0,'Recovery did not finish with exactly one main')
        require(after['legs'][0]['owner']==pins['vault']['address'] and int(after['legs'][0]['liquidity'])>0,'New main custody/liquidity is invalid')
        if action=='C':
            require(new[1]==old[1] and new[5:7]==old[5:7] and after['legs'][0]['ticks']==before['legs'][0]['ticks'],
                'Consolidation replaced or recentered the existing main')
            require(int(after['legs'][0]['liquidity'])>int(before['legs'][0]['liquidity']),'Consolidation did not increase the existing main')
            if minimum_liquidity is not None:
                require(int(after['legs'][0]['liquidity'])>=int(before['legs'][0]['liquidity'])+minimum_liquidity,
                    'Consolidation missed the original exact added-liquidity floor')
            included=node.call('eth_getBlockByHash',[receipt['blockHash'],False])
            require(int(after['last_compound'])==int(included['timestamp'],16),'Consolidation compound clock differs from actual inclusion')
            require(not after['desired_residual_enabled'],'Explicit consolidation mode should remain disabled in this fixture')
        else:
            require(new[1]!=old[1],'Full recovery did not create a replacement main')
            included=node.call('eth_getBlockByHash',[receipt['blockHash'],False])
            require(new[6]==int(included['timestamp'],16),'Replacement rebalance time differs from actual inclusion')
            require(after['last_compound']==before['last_compound'],'Full emergency changed the unrelated compound clock')
            if minimum_liquidity is not None:
                require(int(after['legs'][0]['liquidity'])>=minimum_liquidity,'Replacement missed the original new-position liquidity floor')
    old_ids=[int(leg['id']) for leg in before['legs'] if action!='C' or int(leg['id'])!=old[1]]
    for identifier in old_ids:
        if closed_by_receipt:
            leg=next(row for row in before['legs'] if int(row['id'])==identifier)
            transfer='0x'+keccak256(b'Transfer(address,address,uint256)').hex()
            modify='0x'+keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
            burned=any(log['address'].lower()==pins['position_manager']['address'] and len(log['topics'])==4
                and log['topics'][0]==transfer and int(log['topics'][1],16)==int(pins['vault']['address'],16)
                and int(log['topics'][2],16)==0 and int(log['topics'][3],16)==identifier for log in receipt['logs'])
            deltas=[]
            for log in receipt['logs']:
                if (log['address'].lower()!=pins['pool_manager']['address'] or log['topics'][0]!=modify
                    or len(log['topics'])!=3 or int(log['topics'][1],16)!=old[0]
                    or int(log['topics'][2],16)!=int(pins['position_manager']['address'],16)):continue
                words=list(map(lambda word:int(word,16),decode_words(log['data'])))
                if len(words)!=4 or words[3]!=identifier:continue
                signed=lambda value:value-(1<<256) if value>=1<<255 else value
                if [signed(words[0]),signed(words[1])]==leg['ticks']:deltas.append(signed(words[2]))
            require(burned and sum(deltas)==-int(leg['liquidity']),
                'Actual receipt does not prove full old-position liquidity removal and burn')
        else:
            require(static_read(node,pins,'position_manager','getPositionLiquidity(uint256)',identifier)[0]==0,
                'A physical LP expected to close remains funded')
    if old[1] and action!='C':require(static_read(node,pins,'liquidity','secondaryId(uint256)',old[1])[0]==0,'Old residual association remains')
    if action in ('C','park'):
        require(int(after['parking_nonce'])==int(before['parking_nonce'])+1 and int(after['custody_epoch'])==int(before['custody_epoch'])+(action=='C'),
            'Custody counters did not match the selected operation')
    else:require((after['parking_nonce'],after['custody_epoch'])==(before['parking_nonce'],before['custody_epoch']), 'Full emergency changed unrelated custody counters')
    return {'all_selected_nft_rights_preserved':True,'exact_existing_reward_and_buyback_books_preserved':True,
        'compound_release_and_actual_backing_reconciled':True,'closed_physical_legs_zero_liquidity':True,
        'closed_physical_leg_count':len(old_ids),
        'closure_proof':('not_applicable_no_preexisting_live_legs' if not old_ids else
            'actual_receipt_full_delta_and_pinned_position_manager_burn' if closed_by_receipt else 'actual_post_receipt_getters'),
        'main_identity_geometry_and_clock_match_selected_action':True,'governance_paid_only_receipt_gas':True,
        'global_pause_retained':True,'new_fees_in_controlled_receipt_raw':[list(map(lambda word:str(int(word,16)),row)) for row in collected]}


def capture_reference_rejection(node,case,artifact,destination):
    evidence=case.get('reference_rejection')
    if evidence is None:return None
    require(evidence['before_state']==evidence['after_state'],'The host reference refusal did not preserve its atomic witness')
    words=decode_words(evidence['request']);require(len(words)==12,'Reference rejection request ABI differs')
    signed=lambda value:value-(1<<256) if value>=1<<255 else value
    request={name:('0x'+words[i] if i in (1,5,11) else bool(int(words[i],16)) if i==6
        else signed(int(words[i],16)) if i in (3,4) else int(words[i],16)) for i,name in enumerate(manual.FIELDS)}
    require(request['checks']==14,'Reference rejection must retain the full selected financial/operations guards')
    exported_request=dict(request)
    # The negative is a separately recorded read-only variant of THIS review,
    # changing only its venue. A new explicit deadline must never be confused
    # with the earlier export's expired diagnostic request.
    request={**artifact['arguments'],'swapPool':exported_request['swapPool']}
    _,data=manual.encode(request,case['selection']['action'])
    tx={**artifact['transaction'],'data':data,'gas':hex(PROFILE_GAS)}
    block={'blockHash':artifact['final_control_head']['hash'],'requireCanonical':True}
    before=state(node,case);reverted=False
    try:node.call('eth_call',[tx,block])
    except OwnedRPCFailure as exc:
        reverted=isinstance(exc.error,dict) and isinstance(exc.error.get('data'),str) and exc.error['data'].startswith('0x')
    require(reverted,'The recorded reference-venue negative did not return an actual EVM rejection')
    trace=node.call('debug_traceCall',[tx,block,{'tracer':'callTracer','tracerConfig':{'withLog':True},'timeout':'60s'}])
    require(bool(trace.get('error')),'The reference negative trace unexpectedly succeeded')
    def frames(frame):
        yield frame
        for child in frame.get('calls',[]):yield from frames(child)
    flat=list(frames(trace));pins=case['bindings']
    context_selector='0x'+keccak256(b'balanceContext(bytes32)').hex()[:8]
    fingerprint_selectors=tuple('0x'+keccak256((name+'('+manual.TUPLE+')').encode()).hex()[:8]
        for name in ('emergencyFingerprint','consolidationEmergencyFingerprint'))
    contexts=[frame.get('output') for frame in flat if frame.get('to','').lower()==pins['liquidity']['address']
        and frame.get('input','').startswith(context_selector) and not frame.get('error')]
    fingerprints=[frame.get('output') for frame in flat if frame.get('to','').lower()==pins['custody_validation']['address']
        and frame.get('input','').startswith(fingerprint_selectors) and not frame.get('error')]
    swap_selector='0x'+keccak256(b'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)').hex()[:8]
    swaps=[frame for frame in flat if frame.get('to','').lower()==pins['pool_manager']['address']
        and frame.get('input','').startswith(swap_selector) and not frame.get('error')]
    after=state(node,case);require(after==before,'A failed read-only reference probe changed actual state')
    summary={'actual_evm_rejection':True,'actual_state_unchanged':True,'host_atomic_before':evidence['before_state'],
        'host_atomic_after':evidence['after_state'],'host_quote':case.get('reference_quote'),
        'exported_request':exported_request,'actual_read_only_variant':request,
        'successful_actual_core_swaps':len(swaps),'successful_balance_context_outputs':contexts,
        'successful_emergency_fingerprint_outputs':fingerprints,
        'changed_after_successful_core_swap':bool(swaps and len(set(fingerprints))>1 and any(
            index>max(i for i,item in enumerate(flat) if item in swaps) and frame.get('output')!=fingerprints[0]
            for index,frame in enumerate(flat) if frame.get('to','').lower()==pins['custody_validation']['address']
            and frame.get('input','').startswith(fingerprint_selectors) and not frame.get('error'))),
        'scope':'Actual rejection and full trace; exact late-context attribution is claimed only when successful swaps and changed outputs are both present.'}
    save(destination/'reference-negative-trace.json',trace);save(destination/'reference-negative.json',summary)
    return summary


def run_case(python,anvil,folder,case,output,*,active_before_park=None,new_review_seconds=None):
    case={**case,'selection':dict(case['selection'])}
    source=active_before_park or case
    genesis,token_hash,provenance=restore(source,folder)
    pins=source['bindings'];runtime_pins={item['address']:item['code_hash'] for item in pins.values()}
    runtime_pins[source['asset']['address']]=token_hash
    summary={'schema':1,'case':case['label'],'successful':False,'public_transactions':0,'existing_node_changes':0,
        'state_provenance':provenance,'source_forge_sha256':case['forge_sha256'],'source_method':case['method'],
        'profile':'accounting7/custody5/mint2/V10/execution1/LP3','actual_cli':True,'injected_clock':False,
        'scope':'Controlled real current contracts and local EVM, not production feeds/routes/provider/complete fees or release acceptance.'}
    node=OwnedNode(anvil,genesis,output)
    try:
        with node:
            node.bind_runtimes(runtime_pins);node.mine(2)
            if new_review_seconds is not None:
                original=dict(case['selection']);head=node.call('eth_getBlockByNumber',['latest',False])
                case['selection']['deadline']=str(int(head['timestamp'],16)+new_review_seconds)
                case['selection']['review_notes_sha256']=sha((manual.digest(original)+':new explicit original-deadline review').encode())
                save(node.output/'new-review-intent.json',{'original_export_selection':original,'new_operator_selection':case['selection'],
                    'reason':'Explicitly requested NEW review before preparation; no submitted transaction or prepared artifact is rewritten.',
                    'genuine_head_hash':head['hash'],'genuine_head_timestamp':int(head['timestamp'],16)})
            with RecordingProxy(node) as proxy:
                if case['label']=='active-c14':
                    summary['read_only_proxy_negative_checks']=verify_proxy_refusals(proxy,node)
                    save(node.output/'proxy-refusals.json',summary['read_only_proxy_negative_checks'])
                config,policy,catalog=inputs(node,source,token_hash,read_url=proxy.url)
                save(node.output/'read-config.json',config);save(node.output/'manual-policy.json',policy)
                if active_before_park is not None:
                    park={'schema':1,'action':'park','parameters':{'bucket':str(case['bucket']),'minimum0':'1','minimum1':'1'},
                        'expires_at':case['selection']['deadline'],'review_notes_sha256':sha(b'Explicit local Active-to-Parked journey'),
                        'evidence_sha256':[case['forge_sha256']]}
                    prepared,destination=prepare_cli(python,node,config,policy,park,label='park',management_action=True)
                    before,after,receipt,gas=execute_review(node,source,prepared,destination)
                    assertions=verify_post(node,source,before,after,receipt,action='park')
                    save(destination/'assertions.json',assertions);summary['park_journey']={'gas':gas,'assertions':assertions}
                original=case['selection'];require(original is not None,'No explicit host-selected manual request')
                require(case['call']['cap']==PROFILE_GAS and case['call']['padding_bps']==2500,'Host profile cap/padding differs')
                prepared,destination=prepare_cli(python,node,config,policy,original,label='manual')
                require(prepared['action']==original['action'] and int(prepared['arguments']['checks'])==int(original['checks']),
                    'The actual preparer changed the selected action or safeguard mask')
                for field in ('bucket','lower','upper','swapPool','zeroForOne','amountIn','minimumOut','minimumLiquidity','deadline'):
                    require(prepared['arguments'][field]==original[field],'The actual preparer changed an original operation input')
                summary['reference_venue_negative']=capture_reference_rejection(node,case,prepared,destination)
                # The limited keeper may never acquire governance recovery authority.
                wrong={**prepared['transaction'],'from':'0x'+f'{0xBEEF:040x}','gas':hex(PROFILE_GAS)}
                rejected=False
                try:node.call('eth_call',[wrong,{'blockHash':prepared['final_control_head']['hash'],'requireCanonical':True}])
                except OwnedRPCFailure as exc:
                    rejected=isinstance(exc.error,dict) and exc.error.get('data')=='0x'+keccak256(b'Unauthorized()').hex()[:8]
                require(rejected,'The limited keeper unexpectedly acquired manual governance authority')
                before,after,receipt,gas=execute_review(node,case,prepared,destination)
                assertions=verify_post(node,case,before,after,receipt,action=original['action'],
                    minimum_liquidity=int(original['minimumLiquidity']))
                save(destination/'assertions.json',assertions)
                summary.update(successful=True,gas=gas,assertions=assertions,governance=case['governance'],
                    limited_keeper_manual_call_rejected=True,owned_pid=node.proc.pid,owned_port=node.port,
                    recorded_actual_rpc_calls=len(node.records),selection_sha256=manual.digest(original),
                    unsigned_artifact_sha256=sha((destination/'review.json').read_bytes()))
    except Exception as exc:
        summary['failure_type']=type(exc).__name__
        summary['failure_message']=str(exc) if isinstance(exc,ValueError) else 'Actual local review/execution failed; retained evidence is required.'
        raise
    finally:
        if node.created:
            cleanup=Path(output)/'cleanup.json'
            if cleanup.exists():summary['owned_node_stopped']=json.loads(cleanup.read_bytes())['owned_node_stopped']
            save(Path(output)/'VERIFICATION.json',summary)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exports',required=True,type=Path);parser.add_argument('--host-artifact',required=True,type=Path)
    parser.add_argument('--anvil',required=True,type=Path);parser.add_argument('--python',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);parser.add_argument('--case')
    parser.add_argument('--new-review-deadline-seconds',type=int,
        help='Explicit NEW review intent before preparation; never changes an existing artifact or submits twice')
    args=parser.parse_args(argv)
    require(args.exports.is_dir() and args.host_artifact.is_file() and args.anvil.is_file() and args.python.is_file(),'Required owned fixture or pinned tool is missing')
    require(not args.output.exists(),'Evidence output must be new')
    require(args.new_review_deadline_seconds is None or 60<=args.new_review_deadline_seconds<=600,
        'The explicit new local review duration must be60..600seconds')
    cases=parse_export(args.exports,args.host_artifact);selected=[row for row in cases if row['selection'] is not None]
    if args.case:selected=[row for row in selected if row['label']==args.case]
    require(selected,'No explicit requested new recovery case')
    args.output.mkdir(parents=True,exist_ok=False);results=[]
    with (args.output/'REHEARSAL_SOURCE.py').open('xb') as stream:stream.write(Path(__file__).read_bytes())
    for case in selected:
        active=next((row for row in cases if row['label']=='parked14-before-park'),None) if case['label']=='parked-d14' else None
        result=run_case(args.python,args.anvil,args.exports,case,args.output/case['label'],active_before_park=active,
            new_review_seconds=args.new_review_deadline_seconds)
        results.append(result);print(json.dumps({'case':case['label'],'successful':result['successful'],'gas':result['gas'],'owned_node_stopped':result['owned_node_stopped']}),flush=True)
    save(args.output/'CAMPAIGN.json',{'schema':1,'cases':results,'successful':all(row['successful'] for row in results),
        'old_test_methods_executed':0,'public_transactions':0,'old_environment_mutations':0})
    return 0


if __name__=='__main__':raise SystemExit(main())
