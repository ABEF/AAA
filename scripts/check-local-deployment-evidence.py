"""Reconcile captured local deployment evidence offline; never starts a node."""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,re,sys,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT)not in sys.path:sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256
from zzz_ops.deployment_plan import TOP,INTERNAL,MODULES,TYPES,BUILD,BUILD_PINS,ZERO,LEGACY_BUILD_PROFILE,trusted_build,validate
LIMIT=128*1024*1024
LEGACY_RUNNER='ba804ab363243762e48b478a698df538b23185d4b73351ffcb9270a0928b3eb2'
READ_METHODS=frozenset(('web3_clientVersion','eth_chainId','eth_getBlockByNumber','eth_getCode',
 'eth_getBalance','eth_getTransactionCount','eth_getTransactionReceipt','eth_getTransactionByHash',
 'eth_estimateGas','eth_call','eth_gasPrice','debug_traceTransaction'))
RPC_METHODS=READ_METHODS|{'anvil_impersonateAccount','eth_sendTransaction'}
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

def check_wire(wire):
    require(type(wire)is list and 1<=len(wire)<=6000,'Unbounded wire inventory')
    for ordinal,row in enumerate(wire,1):
        require(type(row)is dict and type(row.get('request'))is dict and type(row.get('response'))is dict,'Invalid RPC envelope')
        request=row['request'];response=row['response']
        require(request.get('method')in RPC_METHODS,'RPC method outside closed rehearsal workflow')
        require(request.get('jsonrpc')=='2.0'and response.get('jsonrpc')=='2.0'and type(request.get('id'))is int and
            request['id']==ordinal and type(response.get('id'))is int and response['id']==ordinal and
            type(request.get('params'))is list and 'result'in response and 'error'not in response,'Incomplete or mismatched RPC envelope')
        if request['method']=='eth_sendTransaction':require(len(request['params'])==1 and type(request['params'][0])is dict,'Invalid submission request envelope')

def quantity(value):
    require(type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value)is not None,'Noncanonical submission quantity')
    return int(value,16)

def submission_address(value):
    require(type(value)is str and re.fullmatch(r'0x[0-9a-fA-F]{40}',value)is not None,'Invalid submission address')
    return value.lower()

def check_submission(request,actual,target):
    require(set(request)=={'from','value','data','gas','nonce','gasPrice'}|({'to'}if'to'in request else set()),'Unexpected submission fields')
    require(submission_address(request['from'])==submission_address(actual['from']),'Exact submission sender differs')
    if target is None:require(request.get('to')is None and actual.get('to')is None,'Creation submission target differs')
    else:require(submission_address(request.get('to'))==submission_address(actual.get('to'))==target,'Binding submission target differs')
    require(type(request['data'])is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',request['data'])is not None and request['data'].lower()==actual['input'].lower(),'Exact submission calldata differs')
    for field in ('value','gas','nonce','gasPrice'):require(quantity(request[field])==quantity(actual[field]),'Exact submission '+field+' differs')
    require(quantity(actual.get('type','0x0'))==0,'Unexpected submission transaction type')

def check_carrier_runtime(role,ledger,actual,claimed):
    require(role in ('royalty_data_part0','royalty_data_part1'),'Unknown inert carrier role')
    piece=ledger[:24573]if role=='royalty_data_part0'else ledger[24573:]
    expected='0x'+(b'\x5f\x5f\xfd'+piece).hex()
    require(actual==claimed==expected,'Inert carrier returned runtime differs from trusted ledger slice')

def constructor_specifications():
    specs={role:(name,'top_level',None,refs)for role,name,refs in TOP}
    specs.update({role:(name,'internal_create_only',parent,refs)for role,name,parent,refs,_ in INTERNAL})
    specs.update({f'royalty_data_part{i}':('ZZZRoyaltyCodeData','inert_internal_create_only','royalty_factory',(f'd:{i}',))for i in range(2)})
    require(len(specs)==39,'Wrong closed constructor inventory')
    return specs

def constructor_values(refs,actual_input,addresses,ledger,resolve_getters):
    result=[]
    discoveries={'Registry.activationAssets()':'activation_assets','NFT.royaltyRewards()':'royalty_rewards'}
    for ref in refs:
        if ref=='zero':value=ZERO
        elif ref=='chain':value=actual_input['chain_id']
        else:
            prefix,name=ref.split(':',1)
            if prefix=='i':value=actual_input['inputs'][name]
            elif prefix=='p':value=addresses[name]
            elif prefix=='g':value=addresses[discoveries[name]]if resolve_getters else None
            elif prefix=='d':value='0x'+(ledger[:24573]if name=='0'else ledger[24573:]).hex()
            else:raise ValueError('Unknown closed constructor reference')
        result.append(value)
    return result
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

def expected_bindings(a,inputs,ledger):
    """Closed constructor/state expectations, independent of evidence rows."""
    result={}
    def add(role,signature,value,values=()):
        key=(role,signature,tuple(values));require(key not in result,'Duplicate expected binding observation')
        word=('0x'+value.to_bytes(32,'big').hex())if type(value)is int else ('0x'+bytes.fromhex(value[2:]).rjust(32,b'\0').hex())
        result[key]=(word,False)
    for role,name,_ in TOP:
        if role in MODULES:add('access','module(bytes32)',a[role],('0x'+keccak256(name.encode()).hex(),))
    pairs=[('access','protocolPolicy()','protocol_policy'),('access','bootstrap()',inputs['governance']),('access','governance()',inputs['governance']),('vault','migrationBudget()','migration_budget'),('migration_budget','vault()','vault'),('strategy','portfolioPolicy()','portfolio_policy'),('strategy','rebalanceConfirmation()','rebalance_confirmation'),('liquidity','positionManager()',inputs['position_manager']),('liquidity','poolManager()',inputs['pool_manager']),('liquidity','stateView()',inputs['state_view']),('liquidity','permit2()',inputs['permit2']),('liquidity','balancingRouter()','balancing_router'),('lp_position_executor','liquidityManager()','liquidity'),('lp_balance_math','balancer()','balancing_router'),('contribution_pricing','oracle()','oracle'),('activation_assets','registry()','pools'),('activation_entry','registry()','pools'),('activation_entry','activationAssets()','activation_assets'),('royalty_rewards','nft()','nft'),('royalty_rewards','canonicalController()','access'),('claim_router','nft()','nft'),('claim_router','royalties()','royalty_rewards'),('rewards_canonical','rewards()','rewards'),('custody_validation','migration()','migration'),('lp_converter','ledger()','rewards'),('lp_v4_executor','parent()','lp_converter'),('seadrop_mint','nft()','nft'),('seadrop_mint','seaDrop()',inputs['seadrop']),('seadrop_mint','seaDropCodeHash()',inputs['seadrop_codehash']),('nft_canonical','nft()','nft'),('vault_canonical','vault()','vault'),('fees_canonical','fees()','fees'),('rewards','converter()','lp_converter'),('nft','seaDropMint()','seadrop_mint'),('royalty_factory','controller()','access'),('activation_assets_factory','access()','access'),('buyback','zzz()',inputs['zzz']),('nft','metadataRenderer()','metadata_renderer'),('lp_converter','wrapper()',ZERO),('liquidity','executionStrategy()','lp_balance_math')]
    for role,signature,value in pairs:add(role,signature,a.get(value,value))
    add('royalty_factory','royaltyCodeHash()','0x'+keccak256(ledger).hex());add('royalty_factory','creationCodeLength()',len(ledger))
    for i,piece in enumerate((ledger[:24573],ledger[24573:])):add('royalty_factory','part'+str(i)+'CodeHash()','0x'+keccak256(b'\x5f\x5f\xfd'+piece).hex())
    add('activation_assets_factory','assetsOf(address)',a['activation_assets'],(a['pools'],))
    for role in ('protocol_policy','migration_budget','metadata_renderer','portfolio_policy','rebalance_confirmation','balancing_router','oracle','liquidity','pools','strategy','vault','rewards','fees','membership','migration','compounder','buyback','nft','nft_canonical','vault_canonical','fees_canonical','canonical','lp_converter','seadrop_mint','activation_assets','activation_entry','lp_position_executor','contribution_pricing','claim_router','rewards_canonical','custody_validation'):add(role,'access()',a['access'])
    for signature in ('isSealed()','paused()','preparationActive()','lpExitStarted()','canonicalState()'):add('access',signature,0)
    for role,signature in (('nft','mintedCount()'),('nft','randomnessConfigured()'),('seadrop_mint','configured()'),('lp_converter','enabled()'),('activation_assets','zzz()'),('migration','currentZZZ()'),('rebalance_confirmation','maxObservationGap()')):add(role,signature,0)
    add('vault','canonicalChainId()',4663);add('rewards','assetCount()',1);add('rewards','isAsset(address)',0,(inputs['zzz'],))
    add('vault','bucketCount()',0);add('liquidity','activeSecondaryCount()',0)
    add('access','keepers(address)',1,(inputs['keeper'],));add('access','guardians(address)',1,(inputs['guardian'],))
    sale='0x'+encoded(('uint256','address','address','uint256'),(5*10**16,inputs['mint_recipient'],ZERO,1)).hex()
    result[('protocol_policy','salePolicy()',())]=(sale,True)
    require(len(result)==112,'Wrong closed binding observation inventory')
    return result

def check_bindings(bindings,wire,all_addresses,inputs,ledger):
    expected=expected_bindings(all_addresses,inputs,ledger)
    require(type(bindings)is list and len(bindings)==len(expected),'Incomplete binding observation inventory')
    seen=set()
    for row in bindings:
        arguments=row.get('arguments',[])
        require(type(arguments)is list and all(type(value)is str for value in arguments),'Invalid binding observation arguments')
        key=(row['role'],row['signature'],tuple(arguments))
        require(key in expected and key not in seen,'Unexpected or duplicate binding observation');seen.add(key)
        wanted,sale=expected[key]
        require(row['actual']==wanted,'Independent binding observation value mismatch')
        if sale:require(row.get('constructor_mint_recipient_verified')==inputs['mint_recipient'],'Wrong binding observation sale recipient')
        else:require(row.get('expected')==wanted,'Missing or wrong independently derived binding observation expectation')
        signature=row['signature'];types=tuple(signature.split('(',1)[1][:-1].split(','))if not signature.endswith('()')else()
        request_data=call(signature,types,arguments)
        returns=[x['response'].get('result')for x in wire if x['request']['method']=='eth_call'and x['request']['params'][0].get('to','').lower()==all_addresses[row['role']]and x['request']['params'][0].get('data')==request_data]
        require(wanted in returns,'Binding observation not present in actual wire')
    require(seen==set(expected),'Incomplete binding observation coverage')

def reconcile(evidence,build=None):
    e=Evidence(evidence);prefix='attempt1/'if e.zip else ''
    obj=lambda name:e.obj(prefix+name)
    result=obj('RESULT.json');stage=obj('source-stage.json');cleanup=obj('node/cleanup.json');process=obj('node/process.json');owners=obj('node/socket-ownership.json')
    legacy=stage['tool_sources_sha256']['scripts/rehearse-local-deployment.py']==LEGACY_RUNNER
    require(legacy or stage.get('request_capture')=='immutable_serialized_request_and_response_snapshot','Unknown transport capture scope')
    require(result['status']=='controlled_local_constructor_and_binding_rehearsal_passed'and result['sealed']is False and result['release_ready']is False and result['production_approved']is False,'Wrong result/approval scope')
    require(cleanup['owned_node_stopped']is True and cleanup['pending_submission']is None and cleanup['failure_type']is None,'Owned node not cleanly stopped')
    require(type(process['chain_id'])is int and process['chain_id']==4663 and process['port']not in (8902,57306)and process['minimal_environment']is True and process['size_limit_override']is False,'Wrong local launcher boundary')
    command=process['command'];require(command[command.index('--host')+1]=='127.0.0.1'and command[command.index('--accounts')+1]=='0'and '--silent'in command and command[command.index('--hardfork')+1]=='cancun'and command[command.index('--gas-limit')+1]=='32000000','Wrong local launch flags')
    require(all(x['expected_pid']==process['pid']and x['observed_listener_pids']==[process['pid']]and x['port']==process['port']for x in owners),'Socket ownership proof differs')
    require(obj('SOURCE_UNCHANGED.json')==stage['tool_sources_sha256'],'Source changed during transactions')
    profile=stage.get('accepted_build_profile',LEGACY_BUILD_PROFILE)
    spec=trusted_build(profile)
    require(stage['accepted_build_files_sha256']==spec['files'],'Accepted build pin inventory or values differ from fixed reviewed build')
    require(type(result.get('chain_id'))is int and result['chain_id']==4663,'Wrong result/approval/chain scope')
    require(result.get('build_profile',LEGACY_BUILD_PROFILE)==profile,'Missing or mismatched result build profile')
    build=ROOT/spec['directory']if build is None else Path(build)
    accepted={}
    for name,pin in spec['files'].items():
        with (Path(build)/name).open('rb')as stream:raw=stream.read(LIMIT+1)
        require(len(raw)<=LIMIT and sha(raw)==pin,'Accepted compiler artifact changed');accepted[name]=raw
    with gzip.GzipFile(fileobj=io.BytesIO(accepted['compiler-output.json.gz']))as stream:raw=stream.read(LIMIT+1)
    require(len(raw)<=LIMIT,'Unbounded accepted compiler output');compiler=json.loads(raw)
    plan=obj('offline-plan.json');commit=plan.pop('manifest_sha256');require(sha(canonical(plan))==commit,'Offline plan commitment mismatch')
    actual_input=obj('actual-address-input.json');addresses=actual_input['planned_addresses'];instances=obj('instances.json');by_role={x['role']:x for x in instances}
    require(validate(actual_input)==actual_input and plan['inputs']==actual_input and plan['input_sha256']==sha(canonical(actual_input)),'Input/plan/chain binding mismatch')
    require(plan['accepted_build']['files_sha256']==spec['files'],'Plan accepted build identity differs')
    require(plan.get('build_profile',LEGACY_BUILD_PROFILE)==profile and plan['accepted_build'].get('profile',LEGACY_BUILD_PROFILE)==profile,'Missing or mismatched plan build profile')
    require(len(instances)==39 and len(by_role)==39 and len({x['address']for x in instances})==39,'Wrong instance inventory')
    rows={x['role']:x for x in plan['instances']};all_addresses={x['role']:x['address']for x in instances}
    specifications=constructor_specifications()
    require(len(plan['instances'])==39 and set(rows)==set(specifications)==set(all_addresses),'Wrong closed constructor role inventory')
    ledger=bytes.fromhex(compiler['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    wire,_=e.zipped_json(prefix+'node/rpc-records.json.gz');check_wire(wire)
    mutations=[(i,x)for i,x in enumerate(wire)if x['request']['method']in ('eth_sendTransaction','anvil_impersonateAccount')]
    require(len(mutations)==45 and mutations[0][1]['request']['method']=='anvil_impersonateAccount','Wrong mutation inventory')
    require(mutations[0][1]['request']['params']==[actual_input['inputs']['governance']],'Wrong exact impersonation target')
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
        check_submission(sends[tx['hash']],tx,target)
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
        name,mode,parent,refs=specifications[role];source='src/'+name+'.sol'
        require(row['contract']==name and row['source']==source and row['mode']==mode and row['creator_role']==parent and instance['contract']==name,'Constructor identity differs from closed graph')
        contract=compiler['contracts'][source][name];abi=next((x['inputs']for x in contract['abi']if x['type']=='constructor'),[])
        types=tuple(x['type']for x in abi)
        require(types==TYPES[name]and row['constructor_types']==list(types),'Constructor ABI differs')
        symbolic=constructor_values(refs,actual_input,all_addresses,ledger,False)
        expected_arguments=[{'name':item['name'],'type':item['type'],'source':ref,'value':value}for item,ref,value in zip(abi,refs,symbolic)]
        require(len(refs)==len(abi)and row['arguments']==expected_arguments,'Constructor argument record differs from validated inputs/closed graph')
        values=constructor_values(refs,actual_input,all_addresses,ledger,True)
        expected_init='0x'+contract['evm']['bytecode']['object']+encoded(types,values).hex()
        require(frame['input'].lower()==proof['input']==instance['full_initcode_hex'].lower()==expected_init.lower(),'Accepted normal fullinit/actualtrace differs')
        expected_creator=actual_input['inputs']['governance']if mode=='top_level'else all_addresses[parent]
        require(frame['from'].lower()==expected_creator==proof['creator']and digest==proof['trace_sha256'],'Wrong actual CREATE parent/trace hash')
        runtime=bytes.fromhex(frame['output'][2:]);require(proof['output']==frame['output'].lower()and len(runtime)==instance['runtime_bytes']<=24576 and len(bytes.fromhex(expected_init[2:]))<=49152,'Runtime/initcode bound')
        require(sha(runtime)==instance['runtime_sha256']and '0x'+keccak256(runtime).hex()==instance['runtime_keccak256'],'Actual runtime digest differs')
        codes=[x['response'].get('result')for x in wire if x['request']['method']=='eth_getCode'and x['request']['params'][0].lower()==instance['address']]
        require('0x'+runtime.hex()in codes,'Actual runtime not observed with getCode')
        if name=='ZZZRoyaltyCodeData':check_carrier_runtime(role,ledger,'0x'+runtime.hex(),row['returned_runtime_hex'])
    bindings=obj('bindings.json')
    check_bindings(bindings,wire,all_addresses,actual_input['inputs'],ledger)
    require(sum(int(x['receipt']['gasUsed'],16)for x in txs)==result['total_actual_gas']and max(x['padded_gas']for x in txs)==result['worst_padded_gas'],'Gas totals differ')
    return {'status':'offline_reconciliation_passed','build_profile':profile,'receipts':44,'top_level_constructors':25,'bindings':19,'instances':39,'binding_observations':len(bindings),'wire_requests':len(wire),'total_actual_gas':result['total_actual_gas'],'worst_padded_gas':result['worst_padded_gas'],'legacy_mutable_transaction_request_capture':legacy,'preflight_request_fields_verified_from_original_wire':False,'preflight_request_scope':'Legacy transaction dictionaries were aliased: original full-cap/estimate/padded preflight gas/nonce/gasPrice fields are source-demonstrated, not exact original wire evidence.'if legacy else 'Immutable request snapshots are available; exact preflight stage fields are not evaluated by this checker.','submission_receipt_trace_getters_verified':True,'node_started':False,'rpc_calls':0,'compiler_runs':0,'tests_rerun':0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',required=True,type=Path);p.add_argument('--build',type=Path);p.add_argument('--output',type=Path);args=p.parse_args();result=reconcile(args.evidence,args.build);raw=json.dumps(result,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf8')as f:f.write(raw)
    print(raw);return 0
if __name__=='__main__':raise SystemExit(main())
