"""Reconcile captured local deployment evidence offline; never starts a node."""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,re,sys,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT)not in sys.path:sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
from zzz_ops.deployment_plan import TOP,INTERNAL,MODULES,TYPES,BUILD,BUILD_PINS,ZERO
LIMIT=128*1024*1024
LEGACY_RUNNER='ba804ab363243762e48b478a698df538b23185d4b73351ffcb9270a0928b3eb2'
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def encoded(types,values):
    heads=[];tail=b''
    for typ,value in zip(types,values):
        if typ in ('string','bytes'):
            raw=value.encode('utf8')if typ=='string'else bytes.fromhex(value[2:]);heads.append((32*len(types)+len(tail)).to_bytes(32,'big'));tail+=len(raw).to_bytes(32,'big')+raw+bytes((-len(raw))%32)
        elif typ=='address':heads.append(bytes.fromhex(value[2:]).rjust(32,b'\0'))
        elif typ=='bytes32':heads.append(bytes.fromhex(value[2:]))
        else:heads.append(int(value).to_bytes(32,'big'))
    return b''.join(heads)+tail
def call(signature,types,values):return '0x'+(keccak256(signature.encode())[:4]+encoded(types,values)).hex()
class Evidence:
    def __init__(self,path):
        self.path=Path(path);self.zip=zipfile.ZipFile(self.path)if self.path.is_file()else None
        if self.zip:
            members=self.zip.infolist();names=[x.filename for x in members]
            require(len(names)==len(set(names))and len(names)<=256,'Duplicate/unbounded zip inventory')
            require(all(not PurePosixPath(n).is_absolute()and '..'not in PurePosixPath(n).parts and '\\'not in n for n in names),'Unsafe member path')
            require(sum(x.file_size for x in members)<=256*1024*1024 and all(x.file_size<=LIMIT for x in members),'Unbounded zip')
    def raw(self,name):
        if self.zip:
            with self.zip.open(name)as f:raw=f.read(LIMIT+1)
        else:
            path=(self.path/name).resolve();require(path.is_relative_to(self.path.resolve()),'Unsafe evidence path')
            with path.open('rb')as f:raw=f.read(LIMIT+1)
        require(len(raw)<=LIMIT,'Evidence file too large');return raw
    def obj(self,name):return json.loads(self.raw(name))
    def zipped_json(self,name):
        with gzip.GzipFile(fileobj=io.BytesIO(self.raw(name)))as f:raw=f.read(LIMIT+1)
        require(len(raw)<=LIMIT,'Unbounded gzip');return json.loads(raw),sha(raw)

def reconcile(evidence,build):
    e=Evidence(evidence);prefix='attempt1/'if e.zip else ''
    obj=lambda name:e.obj(prefix+name)
    result=obj('RESULT.json');stage=obj('source-stage.json');cleanup=obj('node/cleanup.json');process=obj('node/process.json');owners=obj('node/socket-ownership.json')
    legacy=stage['tool_sources_sha256']['scripts/rehearse-local-deployment.py']==LEGACY_RUNNER
    require(legacy or stage.get('request_capture')=='immutable_serialized_request_and_response_snapshot','Unknown transport capture scope')
    require(result['status']=='controlled_local_constructor_and_binding_rehearsal_passed'and result['sealed']is False and result['release_ready']is False and result['production_approved']is False,'Wrong result/approval scope')
    require(cleanup['owned_node_stopped']is True and cleanup['pending_submission']is None and cleanup['failure_type']is None,'Owned node not cleanly stopped')
    require(process['chain_id']==4663 and process['port']not in (8902,57306)and process['minimal_environment']is True and process['size_limit_override']is False,'Wrong local launcher boundary')
    command=process['command'];require(command[command.index('--host')+1]=='127.0.0.1'and command[command.index('--accounts')+1]=='0'and '--silent'in command and command[command.index('--hardfork')+1]=='cancun'and command[command.index('--gas-limit')+1]=='32000000','Wrong local launch flags')
    require(all(x['expected_pid']==process['pid']and x['observed_listener_pids']==[process['pid']]and x['port']==process['port']for x in owners),'Socket ownership proof differs')
    require(obj('SOURCE_UNCHANGED.json')==stage['tool_sources_sha256'],'Source changed during transactions')
    require(stage['accepted_build_files_sha256']==BUILD_PINS,'Accepted build pin inventory or values differ from fixed reviewed build')
    accepted={}
    for name,pin in BUILD_PINS.items():
        with (Path(build)/name).open('rb')as stream:raw=stream.read(LIMIT+1)
        require(len(raw)<=LIMIT and sha(raw)==pin,'Accepted compiler artifact changed');accepted[name]=raw
    with gzip.GzipFile(fileobj=io.BytesIO(accepted['compiler-output.json.gz']))as stream:raw=stream.read(LIMIT+1)
    require(len(raw)<=LIMIT,'Unbounded accepted compiler output');compiler=json.loads(raw)
    plan=obj('offline-plan.json');commit=plan.pop('manifest_sha256');require(sha(canonical(plan))==commit,'Offline plan commitment mismatch')
    actual_input=obj('actual-address-input.json');addresses=actual_input['planned_addresses'];instances=obj('instances.json');by_role={x['role']:x for x in instances}
    require(len(instances)==39 and len(by_role)==39 and len({x['address']for x in instances})==39,'Wrong instance inventory')
    rows={x['role']:x for x in plan['instances']};all_addresses={x['role']:x['address']for x in instances}
    wire,_=e.zipped_json(prefix+'node/rpc-records.json.gz');require(1<=len(wire)<=6000,'Unbounded wire inventory')
    mutations=[(i,x)for i,x in enumerate(wire)if x['request']['method']in ('eth_sendTransaction','anvil_impersonateAccount')]
    require(len(mutations)==45 and mutations[0][1]['request']['method']=='anvil_impersonateAccount','Wrong mutation inventory')
    for index,entry in mutations:
        previous=[x for x in owners if x['before_rpc_index']<=index];require(previous,'Mutation lacks prior socket proof')
        start=previous[-1]['before_rpc_index'];between=wire[start:index]
        require(between[0]['request']['method']=='eth_chainId'and int(between[0]['response']['result'],16)==4663,'Missing pre-mutation chain check')
        require(between[1]['request']['method']=='eth_getBlockByNumber'and between[1]['response']['result']['hash']==process['genesis_hash'],'Missing pre-mutation genesis check')
        require(not any(x['request']['method']in ('eth_sendTransaction','anvil_impersonateAccount')for x in between),'Mutation lacks fresh own-PID proof')
    sends={x['response']['result']:x['request']['params'][0]for _,x in mutations[1:]};receipt_wire={x['response']['result']['transactionHash']:x['response']['result']for x in wire if x['request']['method']=='eth_getTransactionReceipt'and x['response'].get('result')}
    expected=[]
    for role,name,_ in TOP:
        expected.append(('create:'+role,None,None))
        if role=='protocol_policy':expected.append(('bind:protocol_policy',addresses['access'],call('bindProtocolPolicy(address)',('address',),(addresses[role],))))
        if role in MODULES:expected.append(('bind:'+role,addresses['access'],call('bind(bytes32,address)',('bytes32','address'),('0x'+keccak256(name.encode()).hex(),addresses[role]))))
    expected.extend([('bind:lp_converter',addresses['rewards'],call('bindConverter(address)',('address',),(addresses['lp_converter'],))),('bind:seadrop_mint',addresses['nft'],call('setSeaDropMint(address)',('address',),(addresses['seadrop_mint'],)))])
    require(len(expected)==44,'Expected44 transactions')
    txs=[];frames={}
    for n,(label,target,payload)in enumerate(expected,1):
        row=obj(f'{n:02d}-'+label.replace(':','-')+'.json');tx=row['transaction'];receipt=row['receipt'];txs.append(row)
        require(row['label']==label and tx['hash']in sends and receipt==receipt_wire[tx['hash']]and receipt['transactionHash']==tx['hash']and int(receipt['status'],16)==1,'Receipt not actual captured successful transaction')
        require(int(tx['value'],16)==0 and tx['from'].lower()==actual_input['inputs']['governance']and int(tx['nonce'],16)==n-1,'Sender/value/nonce mismatch')
        require(sends[tx['hash']]['data']==tx['input']and int(sends[tx['hash']]['gas'],16)==int(tx['gas'],16),'Exact submission payload differs')
        require(row['padded_gas']==(row['estimated_gas']*12500+9999)//10000==int(tx['gas'],16)<=32000000 and int(receipt['gasUsed'],16)<=row['padded_gas'],'Gas/padding mismatch')
        require(row['simulation_nonce_unchanged']is True,'Missing no-state-change simulation proof')
        if target is not None:require(tx['to'].lower()==target and tx['input']==payload and row['simulation_return']=='0x','Binding graph or output mismatch')
        else:
            role=label[7:];require(receipt['contractAddress'].lower()==addresses[role]and tx['input']==rows[role]['full_initcode_hex'],'Constructor address/input differs from offline planner')
            trace,digest=e.zipped_json(prefix+f'{n:02d}-'+label.replace(':','-')+'-trace.json.gz')
            def walk(frame):
                require(not frame.get('error'),'CREATE trace reverted')
                if frame['type']=='CREATE':
                    created=frame['to'].lower();require(created not in frames,'Duplicate CREATE');frames[created]=(frame,digest)
                for child in frame.get('calls',[]):walk(child)
            walk(trace)
    require(set(frames)=={x['address']for x in instances},'CREATE trace graph differs from39getters')
    for instance in instances:
        role=instance['role'];row=rows[role];frame,digest=frames[instance['address']];proof=instance['create_proof']
        contract=compiler['contracts'][row['source']][row['contract']];types=tuple(x['type']for x in next((x['inputs']for x in contract['abi']if x['type']=='constructor'),[]))
        require(types==TYPES[row['contract']],'Constructor ABI differs')
        values=[x['value']for x in row['arguments']]
        if role=='activation_entry':values=[addresses['access'],addresses['pools'],all_addresses['activation_assets']]
        if role=='claim_router':values=[addresses['access'],addresses['nft'],all_addresses['royalty_rewards']]
        expected_init='0x'+contract['evm']['bytecode']['object']+encoded(types,values).hex()
        require(frame['input'].lower()==proof['input']==instance['full_initcode_hex'].lower()==expected_init.lower(),'Accepted normal fullinit/actualtrace differs')
        expected_creator=actual_input['inputs']['governance']if role in addresses else all_addresses[row['creator_role']]
        require(frame['from'].lower()==expected_creator==proof['creator']and digest==proof['trace_sha256'],'Wrong actual CREATE parent/trace hash')
        runtime=bytes.fromhex(frame['output'][2:]);require(proof['output']==frame['output'].lower()and len(runtime)==instance['runtime_bytes']<=24576 and len(bytes.fromhex(expected_init[2:]))<=49152,'Runtime/initcode bound')
        require(sha(runtime)==instance['runtime_sha256']and '0x'+keccak256(runtime).hex()==instance['runtime_keccak256'],'Actual runtime digest differs')
        codes=[x['response'].get('result')for x in wire if x['request']['method']=='eth_getCode'and x['request']['params'][0].lower()==instance['address']]
        require('0x'+runtime.hex()in codes,'Actual runtime not observed with getCode')
        if row['contract']=='ZZZRoyaltyCodeData':require('0x'+runtime.hex()==row['returned_runtime_hex'],'Inert carrier data mismatch')
    bindings=obj('bindings.json');require(len(bindings)>=100,'Incomplete binding/state observations')
    for observation in bindings:
        signature=observation['signature'];types=tuple(signature.split('(',1)[1][:-1].split(','))if not signature.endswith('()')else ();values=observation.get('arguments',[])
        request_data=call(signature,types,values);returns=[x['response'].get('result')for x in wire if x['request']['method']=='eth_call'and x['request']['params'][0].get('to','').lower()==all_addresses[observation['role']]and x['request']['params'][0].get('data')==request_data]
        require(observation['actual']in returns,'Binding observation not present in actual wire')
        if 'expected'in observation:require(observation['actual']==observation['expected'],'Binding comparison failed')
    require(sum(int(x['receipt']['gasUsed'],16)for x in txs)==result['total_actual_gas']and max(x['padded_gas']for x in txs)==result['worst_padded_gas'],'Gas totals differ')
    return {'status':'offline_reconciliation_passed','receipts':44,'top_level_constructors':25,'bindings':19,'instances':39,'binding_observations':len(bindings),'wire_requests':len(wire),'total_actual_gas':result['total_actual_gas'],'worst_padded_gas':result['worst_padded_gas'],'legacy_mutable_transaction_request_capture':legacy,'preflight_request_fields_verified_from_original_wire':False,'preflight_request_scope':'Legacy transaction dictionaries were aliased: original full-cap/estimate/padded preflight gas/nonce/gasPrice fields are source-demonstrated, not exact original wire evidence.'if legacy else 'Immutable request snapshots are available; exact preflight stage fields are not evaluated by this checker.','submission_receipt_trace_getters_verified':True,'node_started':False,'rpc_calls':0,'compiler_runs':0,'tests_rerun':0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',required=True,type=Path);p.add_argument('--build',type=Path,default=ROOT/BUILD);p.add_argument('--output',type=Path);args=p.parse_args();result=reconcile(args.evidence,args.build);raw=json.dumps(result,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf8')as f:f.write(raw)
    print(raw);return 0
if __name__=='__main__':raise SystemExit(main())
