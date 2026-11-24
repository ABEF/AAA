"""NEW controlled-genesis normal-F6 construction and actual NFT code history.

Exactly44 zero-value CREATE/binding transactions; no seal or operating action.
Root starts this script only in a NEW unprivileged private-network owned unit.
No fork URL, provider, key, existing chain or positive financial API is used.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import http.client
import importlib.util
import io
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from wire_capture import WireCapture,verify_wire_capture

LIMIT=16*1024*1024
CAP=32_000_000
OWNER='0x000000000000000000000000000000000000a0a0'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def save(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
def need(ok,message):
    if not ok:raise ValueError(message)


def owns(pid,port):
    wanted=[]
    for table in ('/proc/net/tcp','/proc/net/tcp6'):
        for line in Path(table).read_text().splitlines()[1:]:
            row=line.split()
            if row[3]=='0A' and int(row[1].rsplit(':',1)[1],16)==port:wanted.append(row[9])
    if len(wanted)!=1:return False
    inode='socket:['+wanted[0]+']'
    try:return any(os.readlink(p)==inode for p in (Path('/proc')/str(pid)/'fd').iterdir())
    except (FileNotFoundError,PermissionError):return False


class Child:
    def __init__(self,args,cwd):
        self.chunks=[[],[]];self.total=0;self.lock=threading.Lock();self.overflow=False;self.threads=[]
        self.p=subprocess.Popen(list(map(str,args)),cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
        for ordinal,stream in enumerate((self.p.stdout,self.p.stderr)):
            t=threading.Thread(target=self.drain,args=(ordinal,stream),daemon=True);t.start();self.threads.append(t)
    def drain(self,ordinal,stream):
        try:
            while True:
                raw=stream.read(4096)
                if not raw:break
                with self.lock:
                    remaining=max(0,65536-self.total)
                    self.chunks[ordinal].append(raw[:remaining]);self.total+=min(remaining,len(raw))
                    if len(raw)>remaining:self.overflow=True
        finally:stream.close()
    def stop(self,folder,label):
        if self.p.poll() is None:
            os.killpg(self.p.pid,signal.SIGTERM)
            try:self.p.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(self.p.pid,signal.SIGKILL);self.p.wait(timeout=3)
        for t in self.threads:t.join(timeout=2)
        for ordinal,kind in enumerate(('stdout','stderr')):(folder/(label+'.'+kind)).write_bytes(b''.join(self.chunks[ordinal]))
        return dict(pid=self.p.pid,stopped=self.p.poll() is not None,returncode=self.p.returncode,output_bytes=self.total,output_overflow=self.overflow)


class Node:
    def __init__(self,binary,folder,genesis,port,expected_binary,*,load=None):
        self.binary=binary;self.folder=folder;self.genesis=genesis;self.port=port;self.load=load
        self.capture=WireCapture()
        self.proc=None;self.child=None;self.anchor=None;self.pending=None;self.records=self.capture.records;self.retained=self.capture.retained;self.code_pins={}
        self.expected_binary=expected_binary;self.authorized=None;self.sent=0;self.until=time.monotonic()+900
    def start(self):
        need(os.name=='posix' and os.geteuid()!=0,'Unprivileged isolated Linux node required')
        need(sha(self.binary.read_bytes())==self.expected_binary,'Anvil binary pin differs')
        with socket.socket()as reserve:reserve.bind(('127.0.0.1',self.port))
        args=[self.binary,'--host','127.0.0.1','--port',str(self.port),'--accounts','0','--silent','--chain-id','4663',
              '--hardfork','cancun','--gas-limit',str(CAP)]
        args+=['--load-state',self.load] if self.load else ['--init',self.genesis]
        self.child=Child(args,self.folder);self.proc=self.child.p
        stop=time.monotonic()+20
        while not owns(self.proc.pid,self.port):
            need(self.proc.poll() is None and not self.child.overflow,'Owned Anvil startup refused')
            need(time.monotonic()<stop,'Owned Anvil startup deadline');time.sleep(.05)
        need(self.wire('eth_chainId',[])=='0x1237','Wrong isolated chain')
        self.anchor=self.wire('eth_getBlockByNumber',['0x0',False])['hash']
        if self.load is None:
            alloc=json.loads(self.genesis.read_bytes())['alloc']
            self.code_pins={a:r['code'].lower() for a,r in alloc.items() if r.get('code') not in (None,'0x')}
        need(int(self.wire('eth_getBlockByNumber',['latest',False])['gasLimit'],16)==CAP,'Gas cap differs')
        save(self.folder/('reload-launch.json' if self.load else 'launch.json'),dict(argv=list(map(str,args)),binary_sha256=self.expected_binary,
            node_pid=self.proc.pid,private_network_namespace=os.readlink('/proc/self/ns/net'),
            cgroup=Path('/proc/self/cgroup').read_text(),fork=False,controlled_complete_genesis=True,public_RPC=False))
        return self
    def guard(self):
        need(self.proc is not None and self.proc.poll() is None and not self.child.overflow,'Owned node unavailable')
        need(owns(self.proc.pid,self.port),'Owned listener identity differs')
        need(os.readlink('/proc/self/ns/net')==os.readlink('/proc/'+str(self.proc.pid)+'/ns/net'),'Node network namespace differs')
        need(Path('/proc/self/cgroup').read_text()==Path('/proc/'+str(self.proc.pid)+'/cgroup').read_text(),'Node cgroup differs')
        need(self.wire('eth_chainId',[])=='0x1237','Owned chain changed')
        need(self.wire('eth_getBlockByNumber',['0x0',False])['hash']==self.anchor,'Owned genesis changed')
        for address,code in self.code_pins.items():need(self.wire('eth_getCode',[address,'latest']).lower()==code,'Created runtime changed')
    def wire(self,method,params=None,mutation=False):
        allowed={'eth_chainId','eth_getBlockByNumber','eth_getCode','eth_getBalance','eth_getTransactionCount',
            'eth_getTransactionReceipt','eth_getTransactionByHash','eth_estimateGas','eth_call','eth_gasPrice','debug_traceTransaction','anvil_dumpState'}
        need(method in allowed or mutation and method in ('anvil_impersonateAccount','eth_sendTransaction'),'Closed local method allowlist')
        need(self.proc is not None and self.proc.poll() is None and owns(self.proc.pid,self.port),'Owned node identity missing')
        need(time.monotonic()<self.until and len(self.records)<6000,'Existing finite construction work bound')
        q=dict(jsonrpc='2.0',id=len(self.records)+1,method=method,params=[] if params is None else params)
        body=encode(q);need(len(body)<=128*1024,'Local request size bound')
        end=min(self.until,time.monotonic()+30)
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=min(30,self.until-time.monotonic()))
        try:
            conn.request('POST','/',body,{'Content-Type':'application/json'});response=conn.getresponse();parts=[];size=0
            need(response.status==200,'Owned HTTP status differs')
            while True:
                need(time.monotonic()<end and time.monotonic()<self.until,'Local response deadline')
                part=response.read1(min(65536,LIMIT+1-size))
                need(time.monotonic()<end and time.monotonic()<self.until,'Local response deadline')
                if not part:break
                size+=len(part);need(size<=LIMIT,'Local response exceeds16MiB');parts.append(part)
            raw=b''.join(parts)
        finally:conn.close()
        r=json.loads(raw)
        need(type(r)is dict and r.get('jsonrpc')=='2.0' and type(r.get('id'))is int and r['id']==q['id'] and ('result'in r)!=('error'in r),'Local response identity differs')
        self.capture.add(q,r,raw);self.retained=self.capture.retained
        need('error'not in r,'Owned RPC refused '+method)
        return r['result']
    def mutate(self,method,params):
        self.guard()
        if method=='anvil_impersonateAccount':need(params==[OWNER] and self.sent==0,'Only fixed disposable bootstrap')
        else:
            need(method=='eth_sendTransaction' and self.sent<44 and self.authorized is not None,'Unreviewed submission forbidden')
            tx=params[0];to,data=self.authorized
            need(len(params)==1 and tx['from']==OWNER and tx.get('to')==to and tx['data']==data and tx['value']=='0x0','Exact construction envelope differs')
            need(int(tx['nonce'],16)==106+self.sent and int(tx['gas'],16)<=CAP,'Nonce/gas differs')
            self.sent+=1
        return self.wire(method,params,mutation=True)
    def close(self,label):
        result=self.child.stop(self.folder,label) if self.child else dict(stopped=True,not_started=True)
        try:
            if self.records:
                raw=self.capture.encoded();summary=verify_wire_capture(self.capture.document())
                with (self.folder/(label+'-wire.json.gz')).open('xb')as target:
                    with gzip.GzipFile(fileobj=target,mode='wb')as stream:stream.write(raw)
                save(self.folder/(label+'-wire-capture.json'),summary)
        except Exception as exc:result.update(wire_capture_failed=True,error_type=type(exc).__name__)
        return result


def proof(node,nft,parent,created,expected_code):
    for header in (parent,created):
        live=node.wire('eth_getBlockByNumber',[header['number'],False]);need(live['hash']==header['hash'],'Proof header changed')
    before=node.wire('eth_getCode',[nft,dict(blockHash=parent['hash'],requireCanonical=True)])
    at=node.wire('eth_getCode',[nft,dict(blockHash=created['hash'],requireCanonical=True)])
    latest=node.wire('eth_getCode',[nft,'latest'])
    need(before=='0x' and at.lower()==latest.lower()==expected_code.lower(),'Actual historical NFT code proof differs')
    return dict(parent_header=parent,creation_header=created,nft=nft,parent_code=before,creation_code_sha256=sha(bytes.fromhex(at[2:])),
                latest_code_sha256=sha(bytes.fromhex(latest[2:])),require_canonical=True,saved_provider_fallback=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',required=True,type=Path);ap.add_argument('--anvil',required=True,type=Path)
    ap.add_argument('--anvil-sha256',required=True);ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args();source=a.source.resolve();output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(source))
    from zzz_ops.deployment_plan import Artifacts,TOP,MODULES
    from zzz_ops.abi import keccak256
    from graph_addresses import graph
    spec=importlib.util.spec_from_file_location('maintained_constructor_only',source/'scripts/rehearse-local-deployment.py')
    M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
    artifacts=Artifacts(root=source);expected,sequence=graph(106,TOP,MODULES,keccak256)
    initial,deps=M.genesis();initial['alloc'][OWNER]['nonce']='0x6a'
    need(all(x not in initial['alloc']for x in expected.values()),'Predicted graph collides with controlled genesis')
    genesis=output/'genesis.json';save(genesis,initial);save(output/'controlled-dependencies.json',deps)
    save(output/'SOURCE.json',dict(artifacts_profile=artifacts.profile,build_pins=artifacts.file_pins,source_pins=artifacts.source_pins,
        maintained_constructor_sha256=sha((source/'scripts/rehearse-local-deployment.py').read_bytes()),
        runner_sha256=sha(Path(__file__).read_bytes()),native_dependencies='DECLARED CONSTRUCTOR DOUBLES, not real market/fork',
        capture_sha256=sha((Path(__file__).resolve().parent/'wire_capture.py').read_bytes()),
        new_genesis_nonce=106,old_test_bodies_run=0,sealing_authorized=False))
    node=None;reload_node=None;case=None;section='owned_node_start';history=None;archive=None
    result=dict(schema=1,scope='NEW standalone controlled-genesis UNSEALED normalF6 constructor/history proof only',
        source_fork_qualified=False,financial_or_API_qualified=False,sealed=False,public_calls=0,public_signing=False,
        old_test_bodies_run=0,production_approved=False)
    try:
        node=Node(a.anvil.resolve(),output,genesis,19561,a.anvil_sha256)
        node.start()
        need(int(node.wire('eth_getTransactionCount',[OWNER,'latest']),16)==106 and
             int(node.wire('eth_getTransactionCount',[OWNER,'pending']),16)==106,'Disposable nonce differs')
        first=node.wire('eth_getBlockByNumber',['latest',False])
        for target in expected.values():
            at=dict(blockHash=first['hash'],requireCanonical=True)
            need(node.wire('eth_getCode',[target,at])=='0x' and int(node.wire('eth_getBalance',[target,at]),16)==0 and
                 int(node.wire('eth_getTransactionCount',[target,at]),16)==0,'Controlled genesis collision differs')
        node.mutate('anvil_impersonateAccount',[OWNER])
        class NewHistoryRehearsal(M.Rehearsal):
            def transaction(self,label,payload,to=None):
                nonlocal section,history
                section=label;ordinal=len(self.receipts);step=sequence[ordinal]
                need(label==('create:'+step['role']if step['kind']=='create'else 'bind:'+('protocol_policy'if step['kind']=='bind_policy'else step['role'])),
                     'Closed44 sequence differs')
                need(payload[:10]!='0x'+keccak256(b'seal()')[:4].hex(),'Seal selector forbidden')
                parent=None
                if label=='create:nft':
                    parent=node.wire('eth_getBlockByNumber',['latest',False])
                    need(node.wire('eth_getCode',[expected['nft'],dict(blockHash=parent['hash'],requireCanonical=True)])=='0x','Actual NFT-parent absence failed')
                node.authorized=(to,payload)
                try:value=super().transaction(label,payload,to)
                finally:node.authorized=None
                if step['kind']=='create':need(value==expected[step['role']],'Actual CREATE address differs')
                if parent is not None:
                    created=node.wire('eth_getBlockByNumber',['latest',False])
                    need(created['parentHash']==parent['hash']and int(created['number'],16)==int(parent['number'],16)+1,'Actual NFT creation ancestry differs')
                    history=proof(node,expected['nft'],parent,created,self.creates[expected['nft']]['output'])
                elif history is not None and label=='bind:nft':
                    history=proof(node,expected['nft'],history['parent_header'],history['creation_header'],self.creates[expected['nft']]['output'])
                    save(output/'NFT_HISTORY_PROOF.json',history)
                print(json.dumps(dict(completed=len(self.receipts),maximum=44,label=label,sealed=False)),flush=True)
                return value
        section='normal44_construction';case=NewHistoryRehearsal(node,artifacts,output);constructed=case.run()
        need(node.sent==len(case.receipts)==44 and constructed['sealed']is False and history is not None,'Unsealed construction/proof incomplete')
        rows=json.loads((output/'instances.json').read_bytes());actual={r['role']:r['address']for r in rows}
        need(actual==expected and len(actual)==39,'39actual graph differs')
        need(int(case.call(actual['access'],'isSealed()'),16)==0 and int(case.call(actual['nft'],'mintedCount()'),16)==0,'Unexpected operating/sealed state')
        artifacts.check_sources();save(output/'CONSTRUCTION_RESULT.json',constructed)
        save(output/'PRESEAL_DIAGNOSTICS.json',dict(ready=False,unsigned_seal_prepared=False,seal_simulated=False,seal_broadcast=False,
            missing=['FixedZZZcontribution/exit binding','ZZZLPRewards admission','Configured randomness','Complete mint/drop policy','Qualified operating inputs'],
            reason='Only constructors/bindings authorized; ordinary live paths require seal and remain unqualified'))
        result.update(constructor_success=True,historical_code_proof=True,transactions=44,instances=39)
        section='bounded_preserved_history_export'
        try:
            exported_head=node.wire('eth_getBlockByNumber',['latest',False])
            value=node.wire('anvil_dumpState',[True]);need(type(value)is str and value.startswith('0x')and len(value)%2==0,'Malformed owned state encoding')
            compressed=bytes.fromhex(value[2:]);need(len(compressed)<=LIMIT,'Compressed export bound')
            with (output/'preserved-history.dump.gz').open('xb')as target:target.write(compressed)
            with gzip.GzipFile(fileobj=io.BytesIO(compressed))as stream:raw=stream.read(LIMIT+1)
            if len(raw)>LIMIT:
                archive=dict(exported=True,roundtrip=False,refusal='decompressed_state_exceeds16MiB',compressed_bytes=len(compressed),
                    compressed_sha256=sha(compressed),decompressed_bytes_observed=len(raw),original_dump_retained=True)
            else:
                state=json.loads(raw);need(state.get('historical_states')is not None,'History was not preserved')
                restore=output/'preserved-history.json'
                with restore.open('xb')as target:target.write(raw)
                section='preserved_history_reload'
                reload_node=Node(a.anvil.resolve(),output,genesis,19562,a.anvil_sha256,load=restore)
                reload_node.start()
                need(reload_node.anchor==node.anchor,'Reloaded genesis differs')
                replay_head=reload_node.wire('eth_getBlockByNumber',['latest',False])
                need(all(replay_head[k]==exported_head[k]for k in ('hash','number','timestamp','stateRoot')),'Reloaded head differs')
                for row in rows:
                    code=reload_node.wire('eth_getCode',[row['address'],'latest'])
                    need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==row['runtime_keccak256'],'Reloaded normal runtime differs')
                recheck=M.Rehearsal(reload_node,artifacts,output)
                repeated_bindings=recheck.bindings(actual)
                save(output/'RELOADED_BINDINGS.json',repeated_bindings)
                checked=proof(reload_node,actual['nft'],history['parent_header'],history['creation_header'],case.creates[actual['nft']]['output'])
                save(output/'RELOADED_NFT_HISTORY_PROOF.json',checked)
                archive=dict(exported=True,roundtrip=True,compressed_bytes=len(compressed),decompressed_bytes=len(raw),
                    compressed_sha256=sha(compressed),decompressed_sha256=sha(raw),same_actual_historical_code=True,same_genesis_and_head=True,normal_runtime_count=39,normal_bindings_rechecked=len(repeated_bindings))
        except Exception as exc:
            archive=dict(exported=False,roundtrip=False,refusal='bounded_export_or_reload_refused',section=section,error_type=type(exc).__name__)
        save(output/'HISTORY_EXPORT.json',archive);result.update(archive=archive,success=True)
    except Exception as exc:
        result.update(success=False,blocking_section=section,error_type=type(exc).__name__,safe_message=str(exc)[:250],
            transactions=0 if node is None else node.sent,pending=None if node is None else node.pending)
    finally:
        clean=[]
        if reload_node is not None:clean.append(dict(label='reload',**reload_node.close('reload-anvil')))
        if node is not None:clean.append(dict(label='original',**node.close('anvil')))
        result['cleanup']=clean;result['all_owned_stopped']=bool(clean)and all(c['stopped']for c in clean)
        save(output/'RESULT.json',result)
    print(json.dumps(result,sort_keys=True));return 0 if result.get('success')is True else 1

if __name__=='__main__':raise SystemExit(main())
