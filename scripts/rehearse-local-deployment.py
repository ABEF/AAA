"""Constructor/binding rehearsal on a new, PID-owned, disposable local chain.

No RPC URL, key, nonce plan, public transaction, sealing or operating configuration
is accepted. Native dependency doubles make this constructor-only evidence;
their runtimes DO NOT satisfy the production registry's native-code admission.
"""
from __future__ import annotations
import argparse,gzip,hashlib,http.client,json,os,re,socket,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from zzz_ops import deployment_plan as P
from zzz_ops.abi import keccak256

CHAIN=4663;CAP=32_000_000;PADDING=12500
SENDER='0x000000000000000000000000000000000000a0a0'
KEEPER='0x000000000000000000000000000000000000beef'
GUARDIAN='0x000000000000000000000000000000000000a0a1'
PAYEE='0x000000000000000000000000000000000000a0a2'
READS=frozenset(('web3_clientVersion','eth_chainId','eth_getBlockByNumber','eth_getCode',
 'eth_getBalance','eth_getTransactionCount','eth_getTransactionReceipt','eth_getTransactionByHash',
 'eth_estimateGas','eth_call','eth_gasPrice','debug_traceTransaction'))
PROTECTED=frozenset((8902,57306))
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode('ascii')
    require(len(raw)<=64*1024*1024,'Evidence file exceeds bound')
    with Path(path).open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return sha(raw)
def env(binary):
    names=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')
    result={name:os.environ[name] for name in names if name in os.environ}
    result['PATH']=str(binary.parent)+os.pathsep+str(Path(result.get('SystemRoot','C:/Windows'))/'System32')
    return result
def data(signature,types=(),values=()):return '0x'+(keccak256(signature.encode())[:4]+P.encode_constructor(types,values)).hex()
def address(word):
    require(type(word)is str and re.fullmatch('0x[0-9a-fA-F]{64}',word) is not None and int(word,16)<1<<160,'Invalid address return')
    return '0x'+word[-40:].lower()
def selector_getters(values):
    """Auditable EVM selector dispatcher; all other selectors revert."""
    prefix=bytes.fromhex('5f3560e01c');branches=[]
    # DUP1 PUSH4 selector EQ PUSH2 destination JUMPI =11bytes per branch.
    start=len(prefix)+11*len(values)+3
    for i,(signature,value) in enumerate(values.items()):
        branches.append(b'\x80\x63'+keccak256(signature.encode())[:4]+b'\x14\x61'+(start+i*29).to_bytes(2,'big')+b'\x57')
    # Each body: JUMPDEST POP PUSH20 value PUSH0 MSTORE PUSH1 32 PUSH0 RETURN.
    bodies=b''.join(b'\x5b\x50\x73'+bytes.fromhex(value[2:])+bytes.fromhex('5f5260205ff3') for value in values.values())
    require(all(len(x)==11 for x in branches) and len(bodies)==29*len(values),'Getter assembly shape')
    return prefix+b''.join(branches)+bytes.fromhex('5f5ffd')+bodies

def genesis():
    path=ROOT/'reports/opensea-integration-20261109/official-seadrop/derived/deployed-runtime.hex'
    raw=path.read_bytes();code=bytes.fromhex(raw.decode().strip().removeprefix('0x'))
    require('0x'+keccak256(code).hex()==P.SEADROP_HASH,'Archived SeaDrop runtime changed')
    seeded={P.NATIVE[k]:{'balance':'0x0','code':'0x5f5ffd','nonce':'0x1','storage':{}} for k in ('pool_manager','permit2','zzz')}
    seeded[P.NATIVE['position_manager']]={'balance':'0x0','nonce':'0x1','storage':{},'code':'0x'+selector_getters({'poolManager()':P.NATIVE['pool_manager'],'permit2()':P.NATIVE['permit2']}).hex()}
    seeded[P.NATIVE['state_view']]={'balance':'0x0','nonce':'0x1','storage':{},'code':'0x'+selector_getters({'poolManager()':P.NATIVE['pool_manager']}).hex()}
    seeded[P.SEADROP]={'balance':'0x0','nonce':'0x1','code':'0x'+code.hex(),'storage':{'0x'+'0'*64:'0x'+'0'*63+'1'}}
    seeded[SENDER]={'balance':hex(10**25),'nonce':'0x0','code':'0x','storage':{}}
    result={'config':{'chainId':CHAIN,'homesteadBlock':0,'eip150Block':0,'eip155Block':0,'eip158Block':0,'byzantiumBlock':0,'constantinopleBlock':0,'petersburgBlock':0,'istanbulBlock':0,'berlinBlock':0,'londonBlock':0,'shanghaiTime':0,'cancunTime':0},
      'nonce':'0x0','timestamp':hex(int(time.time())),'extraData':'0x','gasLimit':hex(CAP),'difficulty':'0x0','mixHash':'0x'+'0'*64,'coinbase':P.ZERO,'baseFeePerGas':'0x3b9aca00','alloc':seeded}
    return result,{'archive_path':str(path.relative_to(ROOT)),'archive_sha256':sha(raw),'seadrop_runtime_keccak256':P.SEADROP_HASH,'native_dependencies':'Controlled constructor-only revert/selector doubles; not production native runtime hashes','seeded_code_sha256':{a:sha(bytes.fromhex(row['code'][2:])) for a,row in seeded.items() if row['code']!='0x'}}

class Node:
    def __init__(self,binary,folder,initial):
        self.binary=Path(binary).resolve();self.folder=Path(folder).resolve();self.genesis=initial;self.proc=None;self.connection=None;self.anchor=None;self.records=[];self.pending=None;self.created=False;self.ownership=[]
        self.code_pins={a:row['code'].lower() for a,row in initial['alloc'].items() if row.get('code')not in (None,'0x')}
        self.deadline=time.monotonic()+900
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1]
        require(self.port not in PROTECTED,'Protected historical port')
    def owner(self):
        require(os.name=='nt','Reviewed Windows PID check required')
        run=subprocess.run([str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/netstat.exe'),'-ano','-p','TCP'],capture_output=True,timeout=5,env=env(self.binary),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        require(run.returncode==0,'Socket owner unavailable')
        rows=(line.split() for line in run.stdout.decode(errors='replace').splitlines())
        return {int(row[-1]) for row in rows if len(row)>=5 and row[0]=='TCP' and row[1]=='127.0.0.1:'+str(self.port) and row[2]=='0.0.0.0:0' and row[-1].isdigit()}
    def wire(self,method,params=None,mutation=False):
        require(self.proc is not None and self.proc.poll() is None,'Owned child not alive')
        require(method in READS or mutation and method in ('anvil_impersonateAccount','eth_sendTransaction'),'RPC method outside closed local workflow')
        require(time.monotonic()<self.deadline and len(self.records)<6000,'Rehearsal work budget exhausted')
        request={'jsonrpc':'2.0','id':len(self.records)+1,'method':method,'params':params or []}
        body=json.dumps(request).encode();frozen_request=json.loads(body)
        if self.connection is None:self.connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=30)
        self.connection.request('POST','/',body,{'Content-Type':'application/json'})
        response=self.connection.getresponse();raw=response.read(16*1024*1024+1)
        require(response.status==200 and len(raw)<=16*1024*1024,'Unbounded/failed local response')
        result=json.loads(raw);self.records.append({'request':frozen_request,'response':json.loads(raw)})
        require(result.get('id')==request['id'] and 'result'in result and 'error'not in result,'Owned local RPC refused request')
        return result['result']
    def guard(self):
        require(self.proc is not None and self.proc.poll()is None,'Owned child not alive')
        observed=self.owner();self.ownership.append({'port':self.port,'expected_pid':self.proc.pid,'observed_listener_pids':sorted(observed),'before_rpc_index':len(self.records)})
        require(observed=={self.proc.pid},'Local port not owned by exact child PID')
        require(int(self.wire('eth_chainId'),16)==CHAIN,'Local chain changed')
        head=self.wire('eth_getBlockByNumber',['0x0',False]);require(head['hash']==self.anchor and int(head['gasLimit'],16)==CAP,'Local genesis changed')
        for target,pin in self.code_pins.items():require(self.wire('eth_getCode',[target,'latest']).lower()==pin,'Owned runtime changed')
    def mutate(self,method,params):
        self.guard()
        if method=='anvil_impersonateAccount':require(params==[SENDER],'Only fixed disposable bootstrap EOA')
        else:
            require(method=='eth_sendTransaction' and len(params)==1 and params[0]['from']==SENDER and params[0].get('value')=='0x0','Only zero-value closed deployment workflow')
        return self.wire(method,params,True)
    def __enter__(self):
        try:
            self.folder.mkdir(parents=True,exist_ok=False);self.created=True;save(self.folder/'genesis.json',self.genesis)
            require(self.binary.name.lower()=='anvil.exe' and self.binary.is_file(),'Explicit Anvil binary required')
            command=[str(self.binary),'--host','127.0.0.1','--port',str(self.port),'--accounts','0','--silent','--init',str(self.folder/'genesis.json'),'--gas-limit',str(CAP),'--chain-id',str(CHAIN),'--hardfork','cancun']
            self.proc=subprocess.Popen(command,cwd=self.folder,env=env(self.binary),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            until=time.monotonic()+20
            while time.monotonic()<until:
                require(self.proc.poll()is None,'Owned Anvil exited')
                if self.owner()=={self.proc.pid}:break
                time.sleep(.1)
            else:raise ValueError('Owned Anvil did not bind port')
            require(int(self.wire('eth_chainId'),16)==CHAIN,'Wrong new local chain')
            head=self.wire('eth_getBlockByNumber',['0x0',False]);self.anchor=head['hash']
            require(head['timestamp']==self.genesis['timestamp'] and int(head['gasLimit'],16)==CAP,'Genesis mismatch')
            self.guard();save(self.folder/'process.json',{'pid':self.proc.pid,'port':self.port,'genesis_hash':self.anchor,'chain_id':CHAIN,'command':command,'binary_sha256':sha(self.binary.read_bytes()),'minimal_environment':True,'size_limit_override':False,'public_rpc':False})
            self.mutate('anvil_impersonateAccount',[SENDER]);return self
        except BaseException:self.__exit__(*sys.exc_info());raise
    def __exit__(self,kind,error,traceback):
        if self.connection:self.connection.close();self.connection=None
        if self.proc and self.proc.poll()is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=10)
        if self.created:
            with gzip.open(self.folder/'rpc-records.json.gz','wt',encoding='utf-8')as stream:json.dump(self.records,stream,separators=(',',':'))
            save(self.folder/'socket-ownership.json',self.ownership)
            save(self.folder/'cleanup.json',{'pid':self.proc.pid if self.proc else None,'owned_node_stopped':not self.proc or self.proc.poll()is not None,'pending_submission':self.pending,'failure_type':type(error).__name__ if error else None,'existing_nodes_contacted':False})

class Rehearsal:
    def __init__(self,node,artifacts,output):self.node=node;self.artifacts=artifacts;self.output=output;self.addresses={};self.receipts=[];self.creates={};self.factory_addresses=[]
    def call(self,target,signature,types=(),values=()):return self.node.wire('eth_call',[{'to':target,'data':data(signature,types,values)},'latest'])
    def getter(self,target,signature):return address(self.call(target,signature))
    def nonces(self):return {a:self.node.wire('eth_getTransactionCount',[a,'latest'])for a in (SENDER,*self.factory_addresses)}
    def transaction(self,label,payload,to=None):
        require(len(self.receipts)<44 and type(payload)is str and payload.startswith('0x'),'Closed transaction count/type')
        if to is None:require(0<len(payload[2:])//2<=49152,'Full creation input exceeds EIP3860')
        else:
            allowed={(self.addresses['access'],data('bindProtocolPolicy(address)',('address',),(self.addresses['protocol_policy'],)))}
            if 'lp_converter'in self.addresses:allowed.add((self.addresses['rewards'],data('bindConverter(address)',('address',),(self.addresses['lp_converter'],))))
            if 'seadrop_mint'in self.addresses:allowed.add((self.addresses['nft'],data('setSeaDropMint(address)',('address',),(self.addresses['seadrop_mint'],))))
            for role,name,_ in P.TOP:
                if role in P.MODULES and role in self.addresses:allowed.add((self.addresses['access'],data('bind(bytes32,address)',('bytes32','address'),('0x'+keccak256(name.encode()).hex(),self.addresses[role]))))
            require((to,payload)in allowed and payload[:10]!='0x'+keccak256(b'seal()')[:4].hex(),'Binding outside exact closed allowlist')
        tx={'from':SENDER,'value':'0x0','data':payload,'gas':hex(CAP)}
        if to is not None:tx['to']=to
        self.node.guard();before=self.nonces();simulated=self.node.wire('eth_call',[tx,'latest']);estimated=int(self.node.wire('eth_estimateGas',[tx]),16)
        padded=(estimated*PADDING+9999)//10000;require(21000<=padded<=CAP,'Padded deployment does not fit original local block cap')
        tx['gas']=hex(padded);require(self.node.wire('eth_call',[tx,'latest'])==simulated,'Exact padded simulation differs')
        require(self.nonces()==before,'Simulation changed sender/factory nonce')
        tx['nonce']=before[SENDER];tx['gasPrice']=self.node.wire('eth_gasPrice')
        self.node.pending='submission_uncertain_do_not_resend'
        txhash=self.node.mutate('eth_sendTransaction',[tx]);self.node.pending=txhash
        receipt=None;until=time.monotonic()+20
        while time.monotonic()<until:
            receipt=self.node.wire('eth_getTransactionReceipt',[txhash])
            if receipt:break
            time.sleep(.05)
        require(receipt is not None and int(receipt['status'],16)==1,'No successful included receipt; never resend automatically')
        self.node.pending=None;actual=self.node.wire('eth_getTransactionByHash',[txhash])
        require(actual['input'].lower()==payload.lower() and int(actual['nonce'],16)==int(before[SENDER],16) and int(actual['gas'],16)==padded and actual['from'].lower()==SENDER and int(actual['value'],16)==0,'Included transaction differs from original review')
        require(int(receipt['gasUsed'],16)<=padded,'Receipt exceeds padded limit')
        if to is None:
            created=receipt['contractAddress'].lower();require(self.node.wire('eth_getCode',[created,'latest']).lower()==simulated.lower(),'Actual constructor return differs from simulation')
            trace=self.node.wire('debug_traceTransaction',[txhash,{'tracer':'callTracer'}]);raw=P.canonical(trace)
            trace_name=f'{len(self.receipts)+1:02d}-'+label.replace(':','-')+'-trace.json.gz'
            with gzip.open(self.output/trace_name,'wb')as stream:stream.write(raw)
            def collect(frame):
                require(not frame.get('error'),'Included CREATE trace contains reverted child')
                if frame.get('type')in ('CREATE','CREATE2'):
                    require(frame['type']=='CREATE' and frame.get('to')and frame.get('input')and frame.get('output'),'Expected exact CREATE input/output')
                    target=frame['to'].lower();require(target not in self.creates,'Duplicate created instance')
                    self.creates[target]={'creator':frame['from'].lower(),'input':frame['input'].lower(),'output':frame['output'].lower(),'transaction_hash':txhash,'trace_file':trace_name,'trace_sha256':sha(raw)}
                    self.node.code_pins[target]=frame['output'].lower()
                for child in frame.get('calls',[]):collect(child)
            collect(trace)
        else:require(simulated=='0x' and actual['to'].lower()==to,'Binding output/target mismatch')
        row={'label':label,'transaction':actual,'receipt':receipt,'estimated_gas':estimated,'padded_gas':padded,'padding_bps':PADDING,'simulation_return':simulated,'nonce_before':before,'simulation_nonce_unchanged':True}
        save(self.output/(f'{len(self.receipts)+1:02d}-'+label.replace(':','-')+'.json'),row);self.receipts.append(row)
        return receipt['contractAddress'].lower() if to is None else None
    def arguments(self,refs):
        values=[]
        for ref in refs:
            if ref=='zero':value=P.ZERO
            elif ref=='chain':value=str(CHAIN)
            elif ref.startswith('p:'):value=self.addresses[ref[2:]]
            else:value=self.inputs[ref[2:]]
            values.append(value)
        return values
    def run(self):
        self.inputs={'governance':SENDER,'keeper':KEEPER,'guardian':GUARDIAN,'mint_recipient':PAYEE,'sequencer':P.ZERO,**P.NATIVE,'seadrop':P.SEADROP,'seadrop_codehash':P.SEADROP_HASH,'base_uri':'ipfs://controlled-constructor-rehearsal/','buyback_maximum_trade_usd':str(100*10**18)}
        for role,name,refs in P.TOP:
            obj=self.artifacts.contract(name)[1];encoded=P.encode_constructor(P.TYPES[name],self.arguments(refs));payload='0x'+obj['evm']['bytecode']['object']+encoded.hex()
            self.addresses[role]=self.transaction('create:'+role,payload)
            if role=='access':
                self.factory_addresses=[self.getter(self.addresses['access'],getter)for getter in ('royaltyFactory()','activationAssetsFactory()')]
            if role=='protocol_policy':self.transaction('bind:protocol_policy',data('bindProtocolPolicy(address)',('address',),(self.addresses[role],)),self.addresses['access'])
            if role in P.MODULES:self.transaction('bind:'+role,data('bind(bytes32,address)',('bytes32','address'),('0x'+keccak256(name.encode()).hex(),self.addresses[role])),self.addresses['access'])
        self.transaction('bind:lp_converter',data('bindConverter(address)',('address',),(self.addresses['lp_converter'],)),self.addresses['rewards'])
        self.transaction('bind:seadrop_mint',data('setSeaDropMint(address)',('address',),(self.addresses['seadrop_mint'],)),self.addresses['nft'])
        require(len(self.receipts)==44,'Expected exactly25 creations+19bindings')
        return self.verify()

    def verify(self):
        a=self.addresses;children={}
        getters={'royalty_factory':('access','royaltyFactory()'),'activation_assets_factory':('access','activationAssetsFactory()'),'lp_balance_math':('balancing_router','balanceMath()'),'lp_position_executor':('liquidity','positionOperator()'),'contribution_pricing':('oracle','contributionPricing()'),'activation_assets':('pools','activationAssets()'),'activation_entry':('pools','activationEntry()'),'royalty_rewards':('nft','royaltyRewards()'),'claim_router':('nft','claimRouter()'),'rewards_canonical':('rewards','canonicalModule()'),'custody_validation':('migration','validation()'),'lp_v4_executor':('lp_converter','v4Executor()')}
        for role,(parent,getter)in getters.items():children[role]=self.getter(a[parent],getter)
        for i in range(2):children['royalty_data_part'+str(i)]=self.getter(children['royalty_factory'],'part'+str(i)+'()')
        all_addresses={**a,**children};require(len(set(all_addresses.values()))==39,'Discovered instances not39 distinct addresses')
        plan=P.template();plan['planned_addresses']=dict(a);plan['inputs']=dict(self.inputs);review=P.prepare(plan,build_profile=self.artifacts.profile);save(self.output/'actual-address-input.json',plan);save(self.output/'offline-plan.json',review)
        rows={row['role']:row for row in review['instances']};instances=[]
        require(set(self.creates)==set(all_addresses.values()),'Exactly39 actual CREATE trace instances required')
        for role,target in all_addresses.items():
            row=rows[role];actual=bytes.fromhex(self.node.wire('eth_getCode',[target,'latest'])[2:]);proof=self.creates[target]
            expected_input=row['full_initcode_hex']
            if expected_input is None:
                refs={'activation_entry':(a['access'],a['pools'],children['activation_assets']),'claim_router':(a['access'],a['nft'],children['royalty_rewards'])}
                require(role in refs,'Unexpected unresolved child constructor')
                obj=self.artifacts.contract(row['contract'])[1]
                expected_input='0x'+obj['evm']['bytecode']['object']+P.encode_constructor(P.TYPES[row['contract']],refs[role]).hex()
            require(proof['input']==expected_input.lower() and proof['output']=='0x'+actual.hex(),'Executed child constructor input/returned runtime differs')
            expected_creator=SENDER if role in a else all_addresses[row['creator_role']]
            require(proof['creator']==expected_creator,'Actual child creator differs from source graph')
            if row['contract']=='ZZZRoyaltyCodeData':require(actual.hex()==row['returned_runtime_hex'][2:],'Inert returned runtime differs')
            else:
                require(len(actual)==row['runtime_bytes']<=24576,'Deployed runtime size differs')
            require(len(bytes.fromhex(expected_input[2:]))<=49152,'Internal CREATE fullinit exceeds EIP3860')
            instances.append({'role':role,'contract':row['contract'],'address':target,'runtime_bytes':len(actual),'runtime_keccak256':'0x'+keccak256(actual).hex(),'runtime_sha256':sha(actual),'exact_normal_initcode_execution_authenticated':True,'full_initcode_hex':expected_input,'create_proof':proof})
        for row in self.receipts:
            if row['label'].startswith('create:'):require(row['transaction']['input'].lower()==rows[row['label'][7:]]['full_initcode_hex'].lower(),'Offline planner/actual initcode differ')
        observations=self.bindings(all_addresses)
        save(self.output/'instances.json',instances);save(self.output/'bindings.json',observations)
        return {'status':'controlled_local_constructor_and_binding_rehearsal_passed','build_profile':self.artifacts.profile,'production_approved':False,'release_ready':False,'sealed':False,'chain_id':CHAIN,'top_level_create_receipts':25,'binding_receipts':19,'total_receipts':44,'discovered_instances':39,'all_exact_normal_initcode_executions_authenticated':True,'offline_planner_top_level_payloads_match_actual':True,'worst_padded_gas':max(r['padded_gas']for r in self.receipts),'total_actual_gas':sum(int(r['receipt']['gasUsed'],16)for r in self.receipts),'production_operating_configuration_performed':False,'public_transactions':0,'existing_nodes_contacted':False}

    def bindings(self,a):
        results=[]
        def check(role,signature,expected,types=(),values=()):
            actual=self.call(a[role],signature,types,values);want=('0x'+int(expected).to_bytes(32,'big').hex())if type(expected)is int else ('0x'+bytes.fromhex(expected[2:]).rjust(32,b'\0').hex())
            require(actual.lower()==want.lower(),'Actual binding/state getter mismatch: '+role+'.'+signature);results.append({'role':role,'signature':signature,'arguments':list(values),'actual':actual,'expected':want})
        for role,name,_ in P.TOP:
            if role in P.MODULES:check('access','module(bytes32)',a[role],('bytes32',),('0x'+keccak256(name.encode()).hex(),))
        pairs=[('access','protocolPolicy()','protocol_policy'),('access','bootstrap()',SENDER),('access','governance()',SENDER),('vault','migrationBudget()','migration_budget'),('migration_budget','vault()','vault'),('strategy','portfolioPolicy()','portfolio_policy'),('strategy','rebalanceConfirmation()','rebalance_confirmation'),('liquidity','positionManager()',P.NATIVE['position_manager']),('liquidity','poolManager()',P.NATIVE['pool_manager']),('liquidity','stateView()',P.NATIVE['state_view']),('liquidity','permit2()',P.NATIVE['permit2']),('liquidity','balancingRouter()','balancing_router'),('lp_position_executor','liquidityManager()','liquidity'),('lp_balance_math','balancer()','balancing_router'),('contribution_pricing','oracle()','oracle'),('activation_assets','registry()','pools'),('activation_entry','registry()','pools'),('activation_entry','activationAssets()','activation_assets'),('royalty_rewards','nft()','nft'),('royalty_rewards','canonicalController()','access'),('claim_router','nft()','nft'),('claim_router','royalties()','royalty_rewards'),('rewards_canonical','rewards()','rewards'),('custody_validation','migration()','migration'),('lp_converter','ledger()','rewards'),('lp_v4_executor','parent()','lp_converter'),('seadrop_mint','nft()','nft'),('seadrop_mint','seaDrop()',P.SEADROP),('seadrop_mint','seaDropCodeHash()',P.SEADROP_HASH),('nft_canonical','nft()','nft'),('vault_canonical','vault()','vault'),('fees_canonical','fees()','fees'),('rewards','converter()','lp_converter'),('nft','seaDropMint()','seadrop_mint')]
        pairs.extend([('royalty_factory','controller()','access'),('activation_assets_factory','access()','access'),('buyback','zzz()',P.NATIVE['zzz']),('nft','metadataRenderer()','metadata_renderer'),('lp_converter','wrapper()',P.ZERO),('liquidity','executionStrategy()','lp_balance_math')])
        for role,getter,value in pairs:check(role,getter,a.get(value,value))
        ledger=bytes.fromhex(self.artifacts.contract('ZZZRoyaltyRewards')[1]['evm']['bytecode']['object'])
        check('royalty_factory','royaltyCodeHash()','0x'+keccak256(ledger).hex());check('royalty_factory','creationCodeLength()',len(ledger))
        for i,piece in enumerate((ledger[:24573],ledger[24573:])):check('royalty_factory','part'+str(i)+'CodeHash()','0x'+keccak256(b'\x5f\x5f\xfd'+piece).hex())
        check('activation_assets_factory','assetsOf(address)',a['activation_assets'],('address',),(a['pools'],))
        for role in ('protocol_policy','migration_budget','metadata_renderer','portfolio_policy','rebalance_confirmation','balancing_router','oracle','liquidity','pools','strategy','vault','rewards','fees','membership','migration','compounder','buyback','nft','nft_canonical','vault_canonical','fees_canonical','canonical','lp_converter','seadrop_mint','activation_assets','activation_entry','lp_position_executor','contribution_pricing','claim_router','rewards_canonical','custody_validation'):check(role,'access()',a['access'])
        for sig in ('isSealed()','paused()','preparationActive()','lpExitStarted()','canonicalState()'):check('access',sig,0)
        for role,sig in (('nft','mintedCount()'),('nft','randomnessConfigured()'),('seadrop_mint','configured()'),('lp_converter','enabled()'),('activation_assets','zzz()'),('migration','currentZZZ()'),('rebalance_confirmation','maxObservationGap()')):check(role,sig,0)
        check('vault','canonicalChainId()',CHAIN);check('rewards','assetCount()',1);check('rewards','isAsset(address)',0,('address',),(P.NATIVE['zzz'],))
        check('vault','bucketCount()',0);check('liquidity','activeSecondaryCount()',0)
        check('access','keepers(address)',1,('address',),(KEEPER,));check('access','guardians(address)',1,('address',),(GUARDIAN,))
        sale=self.call(a['protocol_policy'],'salePolicy()');words=[sale[2+i*64:2+(i+1)*64]for i in range(4)]
        require(len(sale)==258 and int(words[0],16)==5*10**16 and '0x'+words[1][-40:]==PAYEE and int(words[2],16)==0 and int(words[3],16)==1,'Constructor sale policy differs')
        results.append({'role':'protocol_policy','signature':'salePolicy()','actual':sale,'constructor_mint_recipient_verified':PAYEE})
        return results

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--anvil',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--build-profile',default=P.DEFAULT_BUILD_PROFILE,help='Exact trusted build identifier; never reuses historical objects implicitly.');args=parser.parse_args(argv)
    P.trusted_build(args.build_profile)
    require(not os.path.lexists(args.output),'Exclusive new evidence folder required');output=args.output.resolve();require(not output.exists(),'Exclusive new evidence folder required')
    artifacts=P.Artifacts(build_profile=args.build_profile);initial,dependencies=genesis();pins={name:sha((ROOT/name).read_bytes())for name in ('scripts/rehearse-local-deployment.py','zzz_ops/deployment_plan.py','zzz_ops/abi.py')}
    # Refused sources/dependencies must not consume an otherwise new run path.
    output.mkdir(parents=True);save(output/'dependencies.json',dependencies);save(output/'source-stage.json',{'tool_sources_sha256':pins,'request_capture':'immutable_serialized_request_and_response_snapshot','accepted_build_profile':artifacts.profile,'accepted_build_files_sha256':artifacts.file_pins,'source_sha256':artifacts.source_pins})
    try:
        with Node(args.anvil,output/'node',initial)as node:
            case=Rehearsal(node,artifacts,output);result=case.run();artifacts.check_sources();require(all(sha((ROOT/name).read_bytes())==pin for name,pin in pins.items()),'Rehearsal source changed during actual calls');save(output/'SOURCE_UNCHANGED.json',pins);save(output/'RESULT.json',result)
        print(json.dumps(result));return 0
    except Exception as exc:
        save(output/'FAILED.json',{'failure_type':type(exc).__name__,'reason':str(exc)if type(exc)is ValueError else 'Unexpected local rehearsal failure; inspect bounded evidence','public_transactions':0,'sealing_attempted':False})
        print(json.dumps({'status':'local_rehearsal_failed','reason':type(exc).__name__}));return 1
if __name__=='__main__':raise SystemExit(main())
