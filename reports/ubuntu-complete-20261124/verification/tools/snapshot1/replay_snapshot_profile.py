"""NEW targeted44 captured-envelope replay, then affected export/reload only.

No old construction/preflight/test runner, estimate, compiler, public RPC, seal,
batch mining, time change, pruning, source mutation or automatic resend runs.
Old C6 files are read only; all processes/output belong to the new c7eb unit.
This separately approved snapshot1 budget does not change production limits.
"""
from pathlib import Path,PurePosixPath
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import time

OLD=Path('/opt/popl-wallet-history-20261123-c7e6')
FIXTURE=OLD/'runtime/run-001/fixture'
SOURCE=OLD/'source/contracts'
NEW=Path('/opt/popl-history-export-20261124-c7eb')
EXPECTED_OUTPUT=NEW/'runtime/run-001/replay'
PINS_SHA='b43e2ad6fdf895e672af4d7f544908197373cebe4623f648aa01b283d8210193'
ORIGINAL_NODE_SHA='cc36100e6eb11abf1dd0fb317c2c473bfbfac25546c6f12b1af61c229ef4ff9c'
NODE_SHA='777018092e71bc383bf00b11d616f5b377448ec78ead7f054943026b7bbf769a'
ORIGINAL_CAPTURE_SHA='07a5fd2f578d2c244d73e12e8004d6209c3103ff46da34aa72ecae445a28e566'
CAPTURE_SHA='a334fc775c3e04fc035f78e6e6d89925e4bfe26d4978eec8ed21b4e684eef128'
DIAGNOSTIC_SHA='fda75faca27ecf9bea24d9e9b9c8cd46daeefeec0ffbb5c78e40d1bb2020acef'
POLICY_SHA='8c0cf81ebf4a21742ef79965c9421f427256faaa04fada5eac6f0f0e6141a900'
ANVIL_SHA='05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'
OWNER='0x000000000000000000000000000000000000a0a0'
LIMIT=16*1024*1024
EXPANDED_STATE_LIMIT=128*1024*1024
CAP=32000000


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def need(ok,message):
    if not ok:raise ValueError(message)
def same(actual,expected):return type(actual)is type(expected)and actual==expected
def identity(st):return(st.st_dev,st.st_ino,st.st_mode,st.st_uid,st.st_nlink,st.st_size,st.st_mtime_ns)


def secure_read(path,owner,maximum):
    """Every fixed old-C6 component is opened without following symlinks."""
    need(path.is_absolute()and path.is_relative_to(OLD),'Fixed old-C6 read only')
    opened=[]
    try:
        descriptor=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(descriptor)
        current=Path('/')
        for part in path.parts[1:-1]:
            descriptor=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=descriptor);opened.append(descriptor)
            current=current/part;st=os.fstat(descriptor);expected=65534 if current.is_relative_to(OLD/'runtime')else 0
            need(stat.S_ISDIR(st.st_mode)and st.st_uid==expected and not st.st_mode&0o022,'Old-C6 directory identity')
        parent=descriptor;descriptor=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(descriptor)
        before=os.fstat(descriptor)
        need(stat.S_ISREG(before.st_mode)and before.st_uid==owner and before.st_nlink==1 and
             not before.st_mode&0o022 and 0<=before.st_size<=maximum,'Old-C6 file identity/bound')
        chunks=[];size=0
        while True:
            raw=os.read(descriptor,min(65536,maximum+1-size))
            if not raw:break
            size+=len(raw);need(size<=maximum,'Old-C6 file read bound');chunks.append(raw)
        need(identity(before)==identity(os.fstat(descriptor))==identity(os.stat(path.name,dir_fd=parent,follow_symlinks=False))and size==before.st_size,'Old-C6 input changed during read')
        return b''.join(chunks)
    finally:
        for descriptor in reversed(opened):os.close(descriptor)


def import_pinned(name,path,pin):
    need(not path.is_symlink()and sha(path.read_bytes())==pin,'Pinned helper differs')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def diagnosis(exc,node,stage,D):
    result=dict(stage=stage,**D.failure(exc));result['Node_record_count']=None if node is None else len(node.records)
    result['Node_retained_encoded_bytes']=None if node is None else node.retained
    result['Node_sent']=None if node is None else node.sent
    result['Node_work_deadline_elapsed']=None if node is None else time.monotonic()>=node.until
    result['fixed_export_guard']=str(exc)if str(exc)in {'Malformed owned state encoding','Compressed export bound','Decompressed state exceeds128MiB','Historical snapshots absent','Reloaded numeric0 identity differs','Reloaded head differs'}else None
    return result


def decode_dump_hex(value):
    """Strict ASCII paired-hex decode without per-pair regular-expression state."""
    need(type(value)is str and value.startswith('0x')and len(value)%2==0,'Malformed owned state encoding')
    encoded_bytes=len(value)-2
    need(encoded_bytes<=2*LIMIT,'Compressed export bound')
    try:compressed=bytes.fromhex(value[2:])
    except ValueError:raise ValueError('Malformed owned state encoding')from None
    # fromhex permits ASCII whitespace; exactlength rejects ALL skipped bytes.
    need(len(compressed)*2==encoded_bytes,'Malformed owned state encoding')
    return compressed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--anvil',type=Path,required=True);parser.add_argument('--anvil-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();here=Path(__file__).resolve().parent
    need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Unprivileged private namespace required')
    need(out==EXPECTED_OUTPUT and args.anvil.resolve()==NEW/'tools/anvil'and args.anvil_sha256==ANVIL_SHA,'Fixed owned invocation differs')
    out.mkdir(mode=0o700,exist_ok=False)
    def save(name,value):
        raw=json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n';need(len(raw)<=LIMIT,'Private report bound')
        with(out/name).open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    result=dict(schema=1,scope='NEW snapshot1 targeted44 captured-envelope fixture plus full returned-state export/reload; not exact old c7e6 reconstruction',success=False,
        replay_complete=False,export_complete=False,reload_complete=False,transactions=0,instances=0,public_calls=0,
        public_signing=False,sealed=False,production_approved=False,financial_or_API_qualified=False,
        estimates=0,compiler_runs=0,old_constructor_runner_calls=0,old_test_bodies_run=0,cleanup=[],diagnostics=[])
    node=reload_node=None;stage='fixed_input_authentication';D=None;before={};source_before={};genesis_before=None;genesis_copy=None;artifacts=None
    try:
        pin_raw=(here/'C6_INPUT_PINS.json').read_bytes();need(sha(pin_raw)==PINS_SHA,'C6 input pin manifest differs');pins=json.loads(pin_raw)
        need(pins['old_lab']==str(OLD)and pins['old_fixture']==str(FIXTURE)and pins['old_source']==str(SOURCE),'C6 fixed path manifest differs')
        policy_raw=(here/'SNAPSHOT_POLICY.json').read_bytes();need(sha(policy_raw)==POLICY_SHA,'Snapshot1 policy pin differs')
        policy=json.loads(policy_raw)
        need(policy['profile']=='isolated_snapshot1'and policy['operator_approved']is True and
             policy['HTTP_response_bytes']=={'default':LIMIT,'exact_anvil_dumpState_true':32*1024*1024}and
             policy['compressed_export_bytes']==LIMIT and policy['expanded_restore_JSON_bytes']==EXPANDED_STATE_LIMIT,
             'Dedicated snapshot1 policy differs')
        result['snapshot_profile']=policy
        result['source_identities']=dict(original_C6_Node_sha256=ORIGINAL_NODE_SHA,new_snapshot_Node_sha256=NODE_SHA,
                                        original_C6_Capture_sha256=ORIGINAL_CAPTURE_SHA,new_snapshot_Capture_sha256=CAPTURE_SHA,
                                        new_diagnostics_sha256=DIAGNOSTIC_SHA,snapshot_policy_sha256=POLICY_SHA)
        for name,pin in {'v4_node.py':ORIGINAL_NODE_SHA,'snapshot_node.py':NODE_SHA,'wire_capture.py':ORIGINAL_CAPTURE_SHA,'snapshot_wire_capture.py':CAPTURE_SHA,'snapshot_diagnostics.py':DIAGNOSTIC_SHA}.items():
            need(sha((here/name).read_bytes())==pin,'Unchanged helper bytes differ')
        marker=json.loads(secure_read(OLD/'LAB_ID.json',0,4096));need(marker['lab']==str(OLD)and marker['unit']=='popl-wallet-history-20261123-c7e6.service'and
            marker['bundle_sha256']==pins['bundle_sha256']and marker['source_manifest_sha256']==pins['manifest_sha256'],'Original lab marker differs')
        manifest_raw=secure_read(OLD/'MANIFEST.json',0,128*1024);need(sha(manifest_raw)==pins['manifest_sha256'],'Original immutable manifest differs')
        manifest=json.loads(manifest_raw);need(manifest['members']==pins['normal_manifest_members'],'Original member map differs')
        raw_inputs={}
        for name,pin in pins['files'].items():
            need('/'not in name and'\\'not in name and name in {'RESULT.json','SOURCE.json','CONSTRUCTION_RESULT.json','NFT_HISTORY_PROOF.json','PRESEAL_DIAGNOSTICS.json','HISTORY_EXPORT.json','instances.json','bindings.json','anvil-wire-capture.json','anvil-wire.json.gz'},'Fixed input filename differs')
            raw=secure_read(FIXTURE/name,65534,pin['bytes']);need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'Original captured input pin differs')
            raw_inputs[name]=raw;before[name]=sha(raw)
        original_result=json.loads(raw_inputs['RESULT.json']);need(original_result['success']is True and original_result['constructor_success']is True and original_result['historical_code_proof']is True and
             original_result['all_owned_stopped']is True and same(original_result['transactions'],44)and same(original_result['instances'],39),'Original construction evidence differs')
        members=manifest['members'];prefix='source/contracts/'
        for member,pin in members.items():
            path=PurePosixPath(member)
            need(not path.is_absolute()and '..'not in path.parts and'\\'not in member,'Original source member path differs')
            raw=secure_read(OLD/member,0,pin['bytes']);need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'Original source member differs');source_before[member]=sha(raw)
        runtime_source=json.loads(raw_inputs['SOURCE.json'])
        expected_source={n[len(prefix):]:p['sha256']for n,p in members.items()if n.startswith(prefix)and n.endswith('.sol')}
        buildprefix=prefix+'reports/activation-final-six-20261118/build/final/'
        expected_build={n.rsplit('/',1)[-1]:p['sha256']for n,p in members.items()if n.startswith(buildprefix)}
        need(len(expected_source)==100 and runtime_source['source_pins']==expected_source and len(expected_build)==4 and runtime_source['build_pins']==expected_build and
             runtime_source['runner_sha256']==ORIGINAL_NODE_SHA and runtime_source['capture_sha256']==ORIGINAL_CAPTURE_SHA and runtime_source['maintained_constructor_sha256']==members[prefix+'scripts/rehearse-local-deployment.py']['sha256'],'Original runtime/source identity differs')
        sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE));sys.path.insert(0,str(here))
        M=import_pinned('dedicated_snapshot_node',here/'snapshot_node.py',NODE_SHA);D=import_pinned('snapshot_failure_observer',here/'snapshot_diagnostics.py',DIAGNOSTIC_SHA)
        C=import_pinned('unchanged_wire_verifier',here/'wire_capture.py',ORIGINAL_CAPTURE_SHA)
        from zzz_ops import deployment_plan as P
        from zzz_ops.abi import keccak256,calldata
        Maintained=import_pinned('maintained_readback_only',SOURCE/'scripts/rehearse-local-deployment.py',members[prefix+'scripts/rehearse-local-deployment.py']['sha256'])
        with gzip.GzipFile(fileobj=io.BytesIO(raw_inputs['anvil-wire.json.gz']))as stream:raw_wire=stream.read(64*1024*1024+1)
        need(len(raw_wire)<=64*1024*1024,'Original wire bound');wire=json.loads(raw_wire)
        need(C.verify_wire_capture(wire)==json.loads(raw_inputs['anvil-wire-capture.json']),'Original wire authentication differs')
        records=wire['records'];genesis_rows=[r for r in records if r['request']['method']=='eth_getBlockByNumber'and r['request']['params']==['0x0',False]]
        need(genesis_rows and all(r['response']['result']==pins['original_numeric_zero_header']for r in genesis_rows),'Original genuine numeric0 header differs')
        original_zero=pins['original_numeric_zero_header'];genesis_raw=secure_read(FIXTURE/'genesis.json',65534,LIMIT);genesis_before=sha(genesis_raw);original_genesis=json.loads(genesis_raw)
        expected_genesis,_=Maintained.genesis();expected_genesis['timestamp']=original_zero['timestamp'];expected_genesis['alloc'][OWNER]['nonce']='0x6a'
        need(original_genesis==expected_genesis,'Original full genesis schema differs')
        genesis_copy=out/'genesis.json'
        descriptor=os.open(genesis_copy,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'wb')as stream:stream.write(genesis_raw);stream.flush();os.fsync(stream.fileno())
        need(sha(genesis_copy.read_bytes())==genesis_before,'Owned bytecopy genesis differs')
        artifacts=P.Artifacts(root=SOURCE)
        submits=[r for r in records if r['request']['method']=='eth_sendTransaction'];need(len(submits)==44,'Exactly44 captured submission envelopes required')
        old_receipts={r['request']['params'][0].lower():r['response']['result']for r in records if r['request']['method']=='eth_getTransactionReceipt'and type(r['response'].get('result'))is dict}
        instances=json.loads(raw_inputs['instances.json']);addresses={r['role']:r['address'].lower()for r in instances}
        need(len(instances)==len(addresses)==len(set(addresses.values()))==39,'Original39 instance map differs')
        groups={};old_hashes=[]
        for ordinal,row in enumerate(submits):
            tx=row['request']['params'][0];expected_keys={'from','value','data','gas','nonce','gasPrice'}|({'to'}if 'to'in tx else set())
            need(set(tx)==expected_keys and tx['from']==OWNER and tx['value']=='0x0'and int(tx['nonce'],16)==106+ordinal and
                 21000<=int(tx['gas'],16)<=CAP and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',tx['data'])is not None and
                 tx['data'][:10]!='0x'+keccak256(b'seal()')[:4].hex(),'Captured exact envelope differs')
            old_hash=row['response']['result'].lower();need(old_hash not in old_hashes and old_hash in old_receipts and old_receipts[old_hash]['status']=='0x1','Original distinct receipt identity differs');old_hashes.append(old_hash)
        for row in instances:
            proof=row['create_proof'];old_hash=proof['transaction_hash'].lower();need(old_hash in old_hashes and row['exact_normal_initcode_execution_authenticated']is True and
                proof['input'].lower()==row['full_initcode_hex'].lower()and len(bytes.fromhex(row['full_initcode_hex'][2:]))<=49152 and
                len(bytes.fromhex(proof['output'][2:]))==row['runtime_bytes']<=24576 and sha(bytes.fromhex(proof['output'][2:]))==row['runtime_sha256']and
                '0x'+keccak256(bytes.fromhex(proof['output'][2:])).hex()==row['runtime_keccak256'],'Original actual CREATE runtime/input evidence differs')
            groups.setdefault(old_hash,[]).append(row)
        need(sum(bool(v)for v in groups.values())==25,'Original25 CREATE groups differ')
        save('INPUT_AUTHENTICATION.json',dict(schema=1,original_fixed_file_pins=before,original_manifest_sha256=sha(manifest_raw),source_pins=runtime_source['source_pins'],build_pins=runtime_source['build_pins'],
            genesis_raw_sha256_first_observed=genesis_before,historic_genesis_raw_pin_available=False,full_genesis_dict_authenticated=True,original_numeric_zero_header=original_zero,
            read_only_old_source=True,old_constructor_runner_calls=0,old_test_bodies_run=0))
        stage='owned_replay_node_start';node=M.Node(args.anvil.resolve(),out,genesis_copy,19611,args.anvil_sha256);node.start()
        new_zero=node.wire('eth_getBlockByNumber',['0x0',False]);need(node.anchor==original_zero['hash']and new_zero==original_zero,'Actual original numeric0 identity differs before mutation')
        need(int(node.wire('eth_getTransactionCount',[OWNER,'latest']),16)==106 and int(node.wire('eth_getTransactionCount',[OWNER,'pending']),16)==106,'Original disposable nonce differs')
        node.mutate('anvil_impersonateAccount',[OWNER]);completed=[];headers=[new_zero];history=None;new_hashes=[];actual_instance_count=0
        for ordinal,row in enumerate(submits):
            stage='targeted_replay_%02d'%(ordinal+1);old_hash=old_hashes[ordinal];tx=json.loads(json.dumps(row['request']['params'][0]));expected_group=groups.get(old_hash,[])
            need(node.pending is None and node.sent==ordinal,'Pending-first replay refuses another submission')
            need(int(node.wire('eth_getTransactionCount',[OWNER,'latest']),16)==int(node.wire('eth_getTransactionCount',[OWNER,'pending']),16)==106+ordinal,'Fresh exact replay nonce differs')
            fresh_price=node.wire('eth_gasPrice');need(int(fresh_price,16)==int(tx['gasPrice'],16),'Fresh fee differs from captured exact envelope')
            need(int(node.wire('eth_getBalance',[OWNER,'latest']),16)>=int(tx['gas'],16)*int(tx['gasPrice'],16),'Exact replay complete-fee funding bound')
            nft_parent=None
            if any(x['role']=='nft'for x in expected_group):
                nft_parent=node.wire('eth_getBlockByNumber',['latest',False]);need(node.wire('eth_getCode',[addresses['nft'],dict(blockHash=nft_parent['hash'],requireCanonical=True)])=='0x','Actual replay NFT parent absence differs')
            save('INTENT-%02d.json'%(ordinal+1),dict(schema=1,ordinal=ordinal+1,original_transaction_hash=old_hash,exact_envelope=tx,automatic_resend=False))
            node.pending='submission_uncertain_do_not_resend';node.authorized=(tx.get('to'),tx['data'])
            try:new_hash=node.mutate('eth_sendTransaction',[tx])
            finally:node.authorized=None
            node.pending=new_hash;need(re.fullmatch(r'0x[0-9a-fA-F]{64}',new_hash)is not None and int(new_hash,16)!=0 and new_hash not in new_hashes,'New actual transaction hash differs');new_hashes.append(new_hash)
            receipt=None;receipt_deadline=time.monotonic()+20
            while time.monotonic()<receipt_deadline:
                receipt=node.wire('eth_getTransactionReceipt',[new_hash])
                if receipt:break
                time.sleep(.05)
            need(type(receipt)is dict and int(receipt['status'],16)==1 and receipt['transactionHash'].lower()==new_hash.lower(),'Successful replay receipt unavailable; never resend')
            need(int(receipt['gasUsed'],16)==int(old_receipts[old_hash]['gasUsed'],16),'Actual replay gas differs from captured receipt')
            need(int(receipt['blockNumber'],16)==int(new_zero['number'],16)+ordinal+1,'Actual one-block-per-envelope replay differs')
            replay_header=node.wire('eth_getBlockByNumber',[receipt['blockNumber'],False])
            need(type(replay_header)is dict and replay_header['number']==receipt['blockNumber']and
                 replay_header['hash']==receipt['blockHash']and replay_header['parentHash']==headers[-1]['hash']and
                 int(replay_header['timestamp'],16)>=int(headers[-1]['timestamp'],16),'New replay header ancestry differs')
            headers.append(json.loads(encode(replay_header)))
            actual=node.wire('eth_getTransactionByHash',[new_hash]);need(actual['hash'].lower()==new_hash.lower()and actual['from'].lower()==OWNER and actual.get('to')==tx.get('to')and
                actual['input'].lower()==tx['data'].lower()and actual['nonce']==tx['nonce']and actual['gas']==tx['gas']and int(actual['gasPrice'],16)==int(tx['gasPrice'],16)and actual['value']=='0x0'and int(receipt['gasUsed'],16)<=int(tx['gas'],16),'Included exact replay envelope differs')
            node.pending=None
            if expected_group:
                need(receipt['contractAddress'].lower()==old_receipts[old_hash]['contractAddress'].lower(),'Actual top CREATE address differs')
                trace=node.wire('debug_traceTransaction',[new_hash,{'tracer':'callTracer'}]);created={};stack=[trace];frames=0
                while stack:
                    frame=stack.pop();frames+=1;need(frames<=2048 and not frame.get('error'),'New actual CREATE trace refused')
                    if frame.get('type')in('CREATE','CREATE2'):
                        need(frame['type']=='CREATE'and frame['to'].lower()not in created,'Actual child CREATE type/address differs');created[frame['to'].lower()]=frame
                    stack.extend(frame.get('calls',[]))
                need(set(created)=={x['address'].lower()for x in expected_group},'Actual created child set differs')
                for instance in expected_group:
                    address=instance['address'].lower();frame=created[address];proof=instance['create_proof']
                    need(frame['from'].lower()==proof['creator'].lower()and frame['input'].lower()==proof['input'].lower()and frame['output'].lower()==proof['output'].lower(),'Actual child constructor/returned runtime differs')
                    need(node.wire('eth_getCode',[address,'latest']).lower()==frame['output'].lower(),'Actual created runtime readback differs')
                    node.code_pins[address]=frame['output'].lower();actual_instance_count+=1
                if nft_parent is not None:
                    nft_created=node.wire('eth_getBlockByNumber',[receipt['blockNumber'],False]);need(nft_created['hash']==receipt['blockHash']and nft_created['parentHash']==nft_parent['hash']and int(nft_created['number'],16)==int(nft_parent['number'],16)+1,'Actual replay NFT creation ancestry differs')
                    nft_code=created[addresses['nft']]['output'];history=M.proof(node,addresses['nft'],nft_parent,nft_created,nft_code);save('NFT_HISTORY_PROOF.json',history)
            else:need(receipt.get('contractAddress')is None,'Binding unexpectedly creates top contract')
            completed.append(dict(ordinal=ordinal+1,original_transaction_hash=old_hash,new_transaction_hash=new_hash,receipt=receipt,exact_envelope=tx,actual_created_instances=len(expected_group)))
            save('RECEIPT-%02d.json'%(ordinal+1),completed[-1]);result['transactions']=node.sent;result['instances']=actual_instance_count
            print(json.dumps(dict(completed=len(completed),maximum=44,actual_instances=actual_instance_count,sealed=False)),flush=True)
        need(node.sent==len(completed)==44 and actual_instance_count==39 and history is not None,'Targeted replay incomplete')
        history=M.proof(node,addresses['nft'],history['parent_header'],history['creation_header'],next(r for r in instances if r['role']=='nft')['create_proof']['output']);save('FINAL_NFT_HISTORY_PROOF.json',history)
        need(int(node.wire('eth_call',[dict(to=addresses['access'],data=calldata('isSealed()')),'latest']),16)==0 and
             int(node.wire('eth_call',[dict(to=addresses['nft'],data=calldata('mintedCount()')),'latest']),16)==0,'Replay unexpectedly sealed or populated')
        node.guard();owner_state=dict(latest_nonce=node.wire('eth_getTransactionCount',[OWNER,'latest']),pending_nonce=node.wire('eth_getTransactionCount',[OWNER,'pending']),balance=node.wire('eth_getBalance',[OWNER,'latest']))
        need(int(owner_state['latest_nonce'],16)==int(owner_state['pending_nonce'],16)==150,'Replay final nonce differs')
        save('REPLAY_RECEIPTS.json',completed);save('REPLAY_HEADERS.json',headers);save('PRE_EXPORT_OWNER_STATE.json',owner_state)
        result.update(replay_complete=True,transactions=44,instances=39,historical_code_proof=True,new_replay_header_count=len(headers),old_C6_complete_header_history_known=False)
        stage='export_head';export_head=node.wire('eth_getBlockByNumber',['latest',False])
        need(export_head==headers[-1]and export_head['hash']==completed[-1]['receipt']['blockHash']and int(export_head['number'],16)==int(new_zero['number'],16)+len(completed),'Export head moved outside exact replay')
        save('EXPORT_INTENT.json',dict(method='anvil_dumpState',params=[True],fixed_response_bytes=32*1024*1024,fixed_compressed_bytes=LIMIT,fixed_decompressed_bytes=EXPANDED_STATE_LIMIT,snapshot_policy_sha256=POLICY_SHA,retained_encoded_bytes=node.retained,requests=len(node.records)))
        stage='original_Node_wire_dump';value=node.wire('anvil_dumpState',[True]);stage='source_expected_encoding'
        compressed=decode_dump_hex(value);need(len(compressed)<=LIMIT,'Compressed export bound')
        with(out/'preserved-history.dump.gz').open('xb')as stream:stream.write(compressed)
        result['export_compressed_bytes']=len(compressed)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed))as stream:raw=stream.read(EXPANDED_STATE_LIMIT+1)
        result['export_decompressed_bytes_observed']=len(raw);need(len(raw)<=EXPANDED_STATE_LIMIT,'Decompressed state exceeds128MiB')
        state=json.loads(raw);need(type(state)is dict and state.get('historical_states')is not None,'Historical snapshots absent')
        historical=state['historical_states']
        need(type(historical)is list and all(type(pair)is list and len(pair)==2 and type(pair[0])is str and
            re.fullmatch(r'0x[0-9a-fA-F]{64}',pair[0])is not None and type(pair[1])is dict for pair in historical),'Pinned historical snapshot pair schema differs')
        # Preserve every returned state byte. Container facts are observations,
        # not invented acceptance gates for header serialization or tip keys.
        block_container=state.get('blocks');transaction_container=state.get('transactions')
        result['state_container_observations']=dict(blocks_type=type(block_container).__name__,
            blocks_container_length=len(block_container)if type(block_container)in(list,dict)else None,
            transactions_type=type(transaction_container).__name__,
            transactions_container_length=len(transaction_container)if type(transaction_container)in(list,dict)else None)
        restore=out/'preserved-history.json'
        with restore.open('xb')as stream:stream.write(raw)
        result.update(export_complete=True,export_decompressed_bytes=len(raw),historical_snapshot_count=len(historical),history_scope='Complete returned true-dump bytes retained; success requires all45 NEW headers/44 receipts and NFT proof after reload, not equality of every historical account/storage slot.')
        stage='affected_state_reload';reload_folder=out/'reload';reload_folder.mkdir(mode=0o700,exist_ok=False)
        reload_node=M.Node(args.anvil.resolve(),reload_folder,genesis_copy,19612,args.anvil_sha256,load=restore);reload_node.start()
        need(reload_node.anchor==node.anchor and reload_node.wire('eth_getBlockByNumber',['0x0',False])==new_zero,'Reloaded numeric0 identity differs')
        replay_head=reload_node.wire('eth_getBlockByNumber',['latest',False]);need(all(replay_head[k]==export_head[k]for k in('hash','number','timestamp','stateRoot')),'Reloaded head differs')
        reloaded_headers=[]
        for expected_header in headers:
            actual_header=reload_node.wire('eth_getBlockByNumber',[expected_header['number'],False])
            need(actual_header==expected_header,'Reloaded new replay header differs')
            reloaded_headers.append(actual_header)
        save('RELOADED_HEADERS.json',reloaded_headers)
        reloaded_receipts=[]
        for expected in completed:
            actual_receipt=reload_node.wire('eth_getTransactionReceipt',[expected['new_transaction_hash']])
            need(actual_receipt==expected['receipt'],'Reloaded new replay receipt differs')
            reloaded_receipts.append(actual_receipt)
        save('RELOADED_RECEIPTS.json',reloaded_receipts)
        result.update(reloaded_header_count=len(reloaded_headers),reloaded_receipt_count=len(reloaded_receipts),
                      same_complete_new_replay_headers_and_receipts=True)
        reload_node.code_pins=dict(node.code_pins);reload_node.guard();runtimes=[]
        for instance in instances:
            code=reload_node.wire('eth_getCode',[instance['address'],'latest']);need(code.lower()==instance['create_proof']['output'].lower()and
                sha(bytes.fromhex(code[2:]))==instance['runtime_sha256'],'Reloaded actual runtime differs');runtimes.append(instance['role'])
        replay_owner=dict(latest_nonce=reload_node.wire('eth_getTransactionCount',[OWNER,'latest']),pending_nonce=reload_node.wire('eth_getTransactionCount',[OWNER,'pending']),balance=reload_node.wire('eth_getBalance',[OWNER,'latest']))
        need(replay_owner==owner_state,'Reloaded actual nonce/balance differs');save('RELOADED_OWNER_STATE.json',replay_owner)
        reader=Maintained.Rehearsal(reload_node,artifacts,reload_folder);bindings=reader.bindings(addresses)
        need(len(bindings)==112 and bindings==json.loads(raw_inputs['bindings.json']),'Reloaded112 typed binding/state readbacks differ');save('RELOADED_BINDINGS.json',bindings)
        proof=M.proof(reload_node,addresses['nft'],history['parent_header'],history['creation_header'],next(r for r in instances if r['role']=='nft')['create_proof']['output']);save('RELOADED_NFT_HISTORY_PROOF.json',proof)
        artifacts.check_sources();result.update(reload_complete=True,reloaded_runtime_count=len(runtimes),reloaded_bindings=len(bindings),same_numeric0_and_head=True,same_actual_historical_code=True,same_owner_nonce_balance=True,success=True)
    except Exception as exc:
        result.update(failure_stage=stage,error_class=type(exc).__name__)
        if D is not None:result['diagnostics'].append(diagnosis(exc,node,stage,D))
    finally:
        if reload_node is not None:result['cleanup'].append(dict(label='reload',**reload_node.close('reload-anvil')))
        if node is not None:result['cleanup'].append(dict(label='replay',**node.close('anvil')))
        result['all_owned_stopped']=bool(result['cleanup'])and all(row.get('stopped')is True for row in result['cleanup'])
        result['old_inputs_preserved']=False
        try:
            for name,pin in before.items():need(sha(secure_read(FIXTURE/name,65534,16*1024*1024))==pin,'Original captured file changed')
            for member,pin in source_before.items():need(sha(secure_read(OLD/member,0,members[member]['bytes']))==pin,'Original fixed source/helper changed')
            if genesis_before is not None:need(sha(secure_read(FIXTURE/'genesis.json',65534,LIMIT))==genesis_before,'Original genesis bytes changed')
            if genesis_copy is not None:need(sha(genesis_copy.read_bytes())==genesis_before,'Owned bytecopy genesis changed')
            if artifacts is not None:artifacts.check_sources()
            result['old_inputs_preserved']=bool(before)and bool(source_before)and genesis_before is not None
            result['old_fixed_source_members_preserved']=len(source_before)
            result['old_genesis_raw_sha256_before_after']=genesis_before
        except Exception as exc:result['input_preservation_error_class']=type(exc).__name__
        if not result['all_owned_stopped']or not result['old_inputs_preserved']or any(r.get('wire_capture_failed')is True or r.get('output_overflow')is True for r in result['cleanup']):result['success']=False
        result['status']=('input_preservation_failed'if 'input_preservation_error_class'in result else
            'input_authentication_refused'if not result['old_inputs_preserved']else
            'cleanup_incomplete'if not result['all_owned_stopped']else
            'capture_incomplete'if any(r.get('wire_capture_failed')is True or r.get('output_overflow')is True for r in result['cleanup'])else
            'complete'if result['success']else 'replay_complete_export_or_reload_refused'if result['replay_complete']else 'replay_refused')
        if node is not None:result['transactions']=node.sent;result['pending']=node.pending
        save('RESULT.json',result)
    print(json.dumps(dict(success=result['success'],status=result['status'],transactions=result['transactions'],all_owned_stopped=result['all_owned_stopped'])));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
