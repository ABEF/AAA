"""One new real-core F6 typed LP partition; public transport is read-only."""
from pathlib import Path
import gzip,hashlib,http.client,importlib.util,json,os,socket,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from warm_cache import cached_fork_provider,PUBLIC_ENDPOINT
from zzz_ops.deployment_plan import Artifacts
from zzz_ops.abi import keccak256

V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OUT=V/'pool-lifecycle-20261120/run/attempt4'
HERE=Path(__file__).resolve().parent
TOOLS=V/'foundry-v1.4.4'
SOLC=V/'toolchain-0.8.26/solc.exe'
BLOCK=119107223
HASH='0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335'
POOL='0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
ZERO='0x'+'0'*40
OWNER='0x000000000000000000000000000000000000a0a0'
CORE='0x8366a39cc670b4001a1121b8f6a443a643e40951'
POSM='0x58daec3116aae6d93017baaea7749052e8a04fa7'
STATE='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
PERMIT2='0x000000000022d473030f116ddee9f6b43ac78ba3'
ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
QUOTER='0x8dc178efb8111bb0973dd9d722ebeff267c98f94'
PINS={CORE:'bd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626',POSM:'c873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2',STATE:'7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6',PERMIT2:'5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca',ZZZ:'3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597'}
CAP=32_000_000
READS={'eth_chainId','web3_clientVersion','eth_getBlockByNumber','eth_getCode','eth_call','eth_estimateGas','eth_getBalance','eth_getTransactionCount','eth_getTransactionReceipt','eth_getTransactionByHash','eth_gasPrice','eth_getStorageAt'}
LOCAL={'anvil_impersonateAccount','anvil_setBalance','anvil_setStorageAt','eth_sendTransaction','evm_mine','anvil_dumpState'}

def save(name,value):
    with (OUT/name).open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,indent=2);f.write('\n')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def word(v):return (int(v,16)if isinstance(v,str)and v.startswith('0x')else int(v)).to_bytes(32,'big')
def words(raw):return [int(raw[i:i+64],16)for i in range(2,len(raw),64)]
def addr(raw):return '0x'+raw[-40:]
def module(name):return '0x'+keccak256(name.encode()).hex()
def toolenv():return {k:os.environ[k]for k in ('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA')if k in os.environ}
def abi(signature,*args):
    p=subprocess.run([str(TOOLS/'cast.exe'),'calldata',signature,*(('true'if v else'false')if type(v)is bool else str(v)for v in args)],capture_output=True,timeout=20,env=toolenv(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert p.returncode==0,p.stderr.decode(errors='replace')
    return p.stdout.decode().strip()

class Node:
    def __init__(self,url):
        with socket.socket()as sock:sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1]
        assert self.port not in (8902,57306)
        self.url=url;self.process=None;self.wire=[];self.receipts=[];self.pending=None;self.deadline=time.monotonic()+900
    def owner(self):
        p=subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/netstat.exe'),'-ano','-p','TCP'],capture_output=True,timeout=6,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        assert p.returncode==0
        return {int(x[-1])for line in p.stdout.decode(errors='replace').splitlines()if len(x:=line.split())>=5 and x[0]=='TCP'and x[1]=='127.0.0.1:'+str(self.port)and x[2]=='0.0.0.0:0'}
    def call(self,method,params=(),allow_error=False):
        assert self.process and self.process.poll()is None and time.monotonic()<self.deadline
        assert method in READS|LOCAL and len(self.wire)<4000
        if method in LOCAL:assert self.owner()=={self.process.pid}
        body={'jsonrpc':'2.0','id':len(self.wire)+1,'method':method,'params':list(params)}
        encoded=json.dumps(body);frozen=json.loads(encoded)
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=60)
        try:c.request('POST','/',encoded,{'Content-Type':'application/json'});r=c.getresponse();raw=r.read(16*1024*1024+1);assert r.status==200 and len(raw)<=16*1024*1024
        finally:c.close()
        result=json.loads(raw);self.wire.append({'request':frozen,'serialized_request_sha256':sha(encoded.encode()),'response':result});assert result['id']==body['id']
        if 'error'in result:
            if allow_error:return result
            raise ValueError('Local '+method+' refused: '+json.dumps(result['error']))
        return result['result']
    def __enter__(self):
        try:return self._start()
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise
    def _start(self):
        command=[str(TOOLS/'anvil.exe'),'--host','127.0.0.1','--port',str(self.port),'--accounts','0','--silent','--chain-id','4663','--hardfork','cancun','--gas-limit',str(CAP),'--fork-url',self.url,'--fork-block-number',str(BLOCK),'--no-storage-caching']
        self.stdout=(OUT/'anvil.stdout').open('xb');self.stderr=(OUT/'anvil.stderr').open('xb')
        self.process=subprocess.Popen(command,cwd=OUT,env=toolenv(),stdout=self.stdout,stderr=self.stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for _ in range(400):
            assert self.process.poll()is None,'Anvil exited'
            if self.owner()=={self.process.pid}:break
            time.sleep(.05)
        else:raise ValueError('Owned node did not listen')
        assert int(self.call('eth_chainId'),16)==4663
        assert self.call('eth_getBlockByNumber',[hex(BLOCK),False])['hash']==HASH
        save('process.json',{'pid':self.process.pid,'port':self.port,'binary_sha256':sha((TOOLS/'anvil.exe').read_bytes()),'public_transport_readonly':True,'fork_block':BLOCK,'fork_hash':HASH,'gas_cap':CAP,'size_override':False})
        return self
    def __exit__(self,*errors):
        if self.process and self.process.poll()is None and self.pending is None:
            try:
                snapshot=self.call('anvil_dumpState',[]);assert isinstance(snapshot,str)and snapshot.startswith('0x')
                raw=bytes.fromhex(snapshot[2:]);assert len(raw)<=8*1024*1024
                with (OUT/'owned-state.dump').open('xb')as state:state.write(raw)
                save('owned-state-capture.json',{'sha256':sha(raw),'bytes':len(raw),'block':self.call('eth_getBlockByNumber',['latest',False]),'owned_pid':self.process.pid,'no_pending':True,'source':'owned isolated node only; not a public checkpoint'})
            except BaseException as capture_error:
                save('owned-state-capture-error.json',{'error_class':type(capture_error).__name__,'message':str(capture_error),'snapshot_complete':False})
        if self.process and self.process.poll()is None:
            self.process.terminate()
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=10)
        with gzip.open(OUT/'local-wire.json.gz','wt',encoding='utf8')as f:json.dump(self.wire,f,separators=(',',':'))
        for name in ('stdout','stderr'):
            if getattr(self,name,None):getattr(self,name).close()
        save('cleanup.json',{'owned_node_stopped':not self.process or self.process.poll()is not None,'pid':self.process.pid if self.process else None,'pending':self.pending,'error':str(errors[1])if errors and errors[1]else None,'existing_nodes_contacted':False})
    def read(self,target,signature,*args):return self.call('eth_call',[{'to':target,'data':abi(signature,*args)},'latest'])
    def send(self,label,to,data,value=0,expected_success=True):
        nonce=self.call('eth_getTransactionCount',[OWNER,'latest']);operation_cap=CAP if to is None else 24_000_000;tx={'from':OWNER,'data':data,'value':hex(value),'gas':hex(operation_cap)}
        if to:tx['to']=to
        simulation=self.call('eth_call',[tx,'latest'],allow_error=True)
        if expected_success:
            assert isinstance(simulation,str),('simulation failed',label,simulation)
            estimate=int(self.call('eth_estimateGas',[tx]),16);padded=(estimate*12500+9999)//10000;assert padded<=operation_cap
            tx['gas']=hex(padded);assert self.call('eth_call',[tx,'latest'])==simulation
        else:
            assert isinstance(simulation,dict)and'error'in simulation
            assert simulation['error'].get('data')=='0x'+keccak256(b'Slippage()')[:4].hex(),'Expected liquidity sizing/minimum guard'
            estimate=None;padded=1_000_000;tx['gas']=hex(padded)
        assert self.call('eth_getTransactionCount',[OWNER,'latest'])==nonce
        tx.update(nonce=nonce,gasPrice=self.call('eth_gasPrice'))
        self.pending='submission_uncertain';h=self.call('eth_sendTransaction',[tx]);self.pending=h
        receipt=None
        for _ in range(400):
            receipt=self.call('eth_getTransactionReceipt',[h])
            if receipt:break
            time.sleep(.05)
        assert receipt and int(receipt['status'],16)==int(expected_success),(label,receipt)
        if not expected_success:assert int(receipt['gasUsed'],16)<padded,'Out-of-gas is not the intended liquidity guard'
        self.pending=None;actual=self.call('eth_getTransactionByHash',[h]);assert actual['input']==data and actual['nonce']==nonce and int(actual['value'],16)==value
        assert actual['from']==OWNER and actual['to']==to and actual['gas']==tx['gas'] and actual['type']=='0x0' and actual.get('chainId','0x1237')=='0x1237'
        assert receipt['transactionHash']==h and receipt['from']==OWNER and receipt['to']==to
        if to is None:assert receipt['contractAddress'] is not None
        else:assert receipt['contractAddress'] is None
        row={'label':label,'transaction':tx,'receipt':receipt,'estimated_gas':estimate,'padded_gas':padded,'simulation':simulation};self.receipts.append(row)
        print(json.dumps({'stage':label,'gas':int(receipt['gasUsed'],16),'ok':expected_success}),flush=True)
        return addr(receipt['contractAddress'])if not to else simulation

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    artifacts=Artifacts()
    source_pool=V/'maximum-workload-20261119/producer06/COMPILED_INPUT_SOURCE_POOL.json.gz'
    compiled=json.loads(gzip.decompress(source_pool.read_bytes()))['sources']
    mock_path=V/'maximum-workload-20261119/test-out/Mocks.sol/MockAccess.json'
    mock=json.loads(mock_path.read_bytes());mock_sources=json.loads(mock['rawMetadata'])['sources']
    for name,record in mock_sources.items():
        raw=(ROOT/name).read_bytes();content=compiled[name]['content'].encode()
        assert raw==content and '0x'+keccak256(content).hex()==record['keccak256'],name
        if name in artifacts.source_pins:assert sha(raw)==artifacts.source_pins[name],name
    prior=V/'recommendations-execution-20261120/pool/attempt2'
    old_manifest=json.loads((ROOT/'reports/recommendations-execution-20261120/pool/EVIDENCE_MANIFEST.json').read_bytes())
    prior_input=(prior/'fixture-input.json').read_bytes();assert sha(prior_input)==old_manifest['members']['attempt2/fixture-input.json']['sha256']
    old_request=json.loads(prior_input);copied_fixture=(HERE/'PoolCustodyFixture.sol').read_text()
    matched=[name for name,row in old_request['sources'].items()if name.replace('\\','/').endswith('/PoolCustodyFixture.sol')and row=={'content':copied_fixture}]
    assert len(matched)==1,'Unique exact retained fixture unit required'
    sources={matched[0]:{'content':copied_fixture},'test/local/Source9RehearsalFixtures.sol':{'content':(ROOT/'test/local/Source9RehearsalFixtures.sol').read_text()}}
    request={'language':'Solidity','sources':sources,'settings':{'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'viaIR':True,'evmVersion':'cancun','outputSelection':{'*':{'*':['abi','evm.bytecode.object','evm.deployedBytecode.object']}}}}
    save('fixture-input.json',request)
    prior=V/'recommendations-execution-20261120/pool/attempt2';assert json.loads((prior/'fixture-input.json').read_bytes())==request
    retained=(prior/'fixture-output.json').read_bytes();assert sha(retained)==old_manifest['members']['attempt2/fixture-output.json']['sha256'];fixture=json.loads(retained)
    assert not [e for e in fixture.get('errors',[])if e['severity']=='error']
    (OUT/'fixture-output.json').write_bytes(retained)
    save('fixture-reuse.json',{'source':str(prior/'fixture-output.json'),'sha256':sha(retained),'input_unchanged':True,'compiler_rerun':False})
    fobjects={name:obj for records in fixture['contracts'].values()for name,obj in records.items()}
    save('source-stage.json',{'production_build':artifacts.profile,'source_sha256':artifacts.source_pins,'build_files':artifacts.file_pins,'producer_source_pool_sha256':sha(source_pool.read_bytes()),'mock_access_artifact_sha256':sha(mock_path.read_bytes()),'fixture_compilation_only':True,'runner_sha256':sha(Path(__file__).read_bytes()),'anvil_sha256':sha((TOOLS/'anvil.exe').read_bytes()),'solc_sha256':sha(SOLC.read_bytes())})
    try:
      with cached_fork_provider(PUBLIC_ENDPOINT,BLOCK,HASH,OUT/'relay',requests_per_second=.5)as relay:
       with Node(relay.url)as n:
        identities={a:'0x'+keccak256(bytes.fromhex(n.call('eth_getCode',[a,'latest'])[2:])).hex()for a in PINS}
        assert identities=={a:'0x'+h for a,h in PINS.items()}
        original_slot=words(n.read(STATE,'getSlot0(bytes32)',POOL));original_L=int(n.read(STATE,'getLiquidity(bytes32)',POOL),16)
        assert original_L==0 and original_slot[0]>0 and original_slot[3]==10020
        for target,getter,expected in [(POSM,'poolManager()',CORE),(POSM,'permit2()',PERMIT2),(STATE,'poolManager()',CORE)]:assert addr(n.read(target,getter))==expected
        quote='0x'+(keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+word(32)+b''.join(word(x)for x in [ZERO,ZZZ,10020,200,ZERO,True,10**12,256,0])).hex()
        pristine_quote=n.call('eth_call',[{'to':QUOTER,'data':quote,'gas':hex(200000)},'latest'],allow_error=True)
        save('pristine.json',{'block':BLOCK,'hash':HASH,'pool':POOL,'runtime_hashes':identities,'slot0':list(map(str,original_slot)),'active_L':str(original_L),'diagnostic_native_input_wei':str(10**12),'diagnostic_quote_response':pristine_quote,'no_added_local_liquidity_yet':True})
        assert n.call('eth_getCode',[OWNER,'latest'])=='0x'
        n.call('anvil_impersonateAccount',[OWNER]);n.call('anvil_setBalance',[OWNER,hex(1000*10**18)])
        def deploy(name,args='',fixture=False,raw=None):
            obj=None if raw else (fobjects[name]if fixture else artifacts.contract(name)[1])
            code=raw or obj['evm']['bytecode']['object']
            if code.startswith('0x'):code=code[2:]
            assert len(code+args)//2<=49152
            return n.send('deploy:'+name,None,'0x'+code+args)
        def constructor(sig,*args):
            run=subprocess.run([str(TOOLS/'cast.exe'),'abi-encode',sig,*(('true'if v else'false')if type(v)is bool else str(v)for v in args)],capture_output=True,timeout=20,env=toolenv(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert run.returncode==0;return run.stdout.decode().strip()[2:]
        def send(target,sig,*args,value=0,label=None,expected=True):return n.send(label or sig,target,abi(sig,*args),value,expected)
        control=deploy('MockAccess',raw=mock['bytecode']['object'])
        policy=deploy('ZZZProtocolPolicy',constructor('constructor(address,address)',control,OWNER));send(control,'setProtocolPolicy(address)',policy)
        oracle=deploy('ZZZOracle',constructor('constructor(address,address)',control,ZERO))
        portfolio=deploy('ZZZPortfolioPolicy',constructor('constructor(address)',control))
        confirmation=deploy('ZZZRebalanceConfirmation',constructor('constructor(address)',control))
        strategy=deploy('ZZZStrategy',constructor('constructor(address,address,address)',control,portfolio,confirmation))
        registry=deploy('ZZZPoolRegistry',constructor('constructor(address)',control))
        balancer=deploy('ZZZLPBalancer',constructor('constructor(address,address,address)',control,CORE,STATE))
        manager=deploy('ZZZLiquidityManager',constructor('constructor(address,address,address,address,address,address)',control,POSM,STATE,CORE,PERMIT2,balancer))
        budget=deploy('PoolFixtureBudget',fixture=True);assets=deploy('PoolFixtureAssets',fixture=True)
        vault=deploy('PoolCustodyFixture',constructor('constructor(address,address)',manager,budget),fixture=True)
        for name,address in [('ZZZOracle',oracle),('ZZZStrategy',strategy),('ZZZPoolRegistry',registry),('ZZZLiquidityManager',manager),('ZZZVault',vault),('ZZZRewards',assets)]:send(control,'bind(bytes32,address)',module(name),address)
        review='0x'+keccak256(b'EXPLICIT CORRELATED PRICES AND OWNED LOCAL FORK TEST').hex()
        ethprice=2000*10**18;zzzprice=ethprice*(1<<192)//(original_slot[0]**2)
        for token,price in [(ZERO,ethprice),(ZZZ,zzzprice)]:
            fs=[deploy('Source9RehearsalFeed',constructor('constructor(int256)',price),fixture=True)for _ in range(2)]
            feeds=['('+','.join((f,'0x'+keccak256(bytes.fromhex(n.call('eth_getCode',[f,'latest'])[2:])).hex(),'0x'+keccak256(('CORRELATED'+f).encode()).hex(),'86400','18'))+')'for f in fs]
            send(oracle,'setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)',token,*feeds,300,review)
        activation=addr(n.read(registry,'activationAssets()'))
        send(activation,'configureZZZ(address,bytes32,bytes32)',ZZZ,'0x'+PINS[ZZZ],review)
        config='(('+','.join((ZERO,ZZZ,'10020','200',ZERO))+'),true,true,5000,500,100,200,43200,100000000000000000000,1000000000000000000000000)'
        send(registry,'configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))',config)
        send(strategy,'setRangeOrientation(bytes32,uint8)',POOL,1)
        send(control,'seal()')
        child=addr(n.read(manager,'positionOperator()'))
        slot=words(n.read(STATE,'getSlot0(bytes32)',POOL));ticks=words(n.read(strategy,'target(bytes32)',POOL));lower=ticks[0]-(1<<256)if ticks[0]>>255 else ticks[0];upper=ticks[1]-(1<<256)if ticks[1]>>255 else ticks[1]
        a0=10**17;a1=a0*original_slot[0]**2//(1<<192)*2;fund=a1*10
        assert 0<fund<=100_000_000*10**18
        mapping_slot='0x'+keccak256(word(vault)+word(0)).hex();before_storage=n.call('eth_getStorageAt',[ZZZ,mapping_slot,'latest']);assert int(before_storage,16)==int(n.read(ZZZ,'balanceOf(address)',vault),16)==0
        n.call('anvil_setStorageAt',[ZZZ,mapping_slot,'0x'+word(fund).hex()]);assert int(n.read(ZZZ,'balanceOf(address)',vault),16)==fund
        save('test-funding.json',{'kind':'LOCAL BALANCE SUBSTITUTE ONLY','owner':vault,'token':ZZZ,'mapping_slot':mapping_slot,'before':before_storage,'after':str(fund),'source_or_runtime_change':False,'independent_external_depth':False,'correlated_fixture_prices':{'ETH':str(ethprice),'ZZZ':str(zzzprice)}})
        deadline_records=[]
        def deadline():
            assert n.pending is None
            n.call('evm_mine',[])
            head=n.call('eth_getBlockByNumber',['latest',False]);now=int(head['timestamp'],16);reviewed=now+300
            assert now<=reviewed<=now+600
            deadline_records.append({'block':head['number'],'hash':head['hash'],'timestamp':now,'deadline':reviewed,'TTL_seconds':300,'owned_empty_block_refresh':True})
            return reviewed
        id=int(n.read(POSM,'nextTokenId()'),16)
        send(vault,'mint(bytes32,int24,int24,uint256,uint256,uint128,uint256)',POOL,lower,upper,a0,a1,1,deadline(),value=a0,label='new_current_f6_mint')
        initial_L=int(n.read(POSM,'getPositionLiquidity(uint256)',id),16);assert initial_L>0 and addr(n.read(POSM,'ownerOf(uint256)',id))==vault
        assert int(n.read(STATE,'getLiquidity(bytes32)',POOL),16)==initial_L
        before_increase=words(n.read(manager,'ticks(uint256)',id))
        send(vault,'increase(bytes32,uint256,uint256,uint256,uint128,uint256)',POOL,id,a0//10,a1//10,1,deadline(),value=a0//10,label='new_current_f6_increase')
        increased_L=int(n.read(POSM,'getPositionLiquidity(uint256)',id),16);assert increased_L>initial_L and words(n.read(manager,'ticks(uint256)',id))==before_increase
        def state():return {'native':int(n.call('eth_getBalance',[vault,'latest']),16),'token':int(n.read(ZZZ,'balanceOf(address)',vault),16),'L':int(n.read(POSM,'getPositionLiquidity(uint256)',id),16),'allowance':int(n.read(ZZZ,'allowance(address,address)',vault,child),16)}
        good=state()
        send(vault,'increase(bytes32,uint256,uint256,uint256,uint128,uint256)',POOL,id,a0//10,a1//10,(1<<128)-1,deadline(),value=a0//10,label='new_impossible_minL_actual_rollback',expected=False)
        assert state()==good
        trader=deploy('Source9RehearsalTrader',fixture=True)
        trader_balance_before=int(n.read(ZZZ,'balanceOf(address)',OWNER),16)
        send(trader,'execute(bool,uint256,uint256,uint160)',True,10**12,1,4295128740,value=10**12,label='new_actual_core_native_swap')
        trader_balance_after=int(n.read(ZZZ,'balanceOf(address)',OWNER),16);trader_gain=trader_balance_after-trader_balance_before
        trader_amount=trader_gain//2;assert trader_gain>0 and 0<trader_amount<=trader_gain
        save('bounded-trade-inputs.json',{'native_input_wei':str(10**12),'prior_owner_ZZZ':str(trader_balance_before),'actual_forward_ZZZ_gain':str(trader_gain),'reverse_input_ZZZ':str(trader_amount),'reverse_is_half_actual_forward_gain':True})
        send(ZZZ,'approve(address,uint256)',trader,trader_amount)
        send(trader,'execute(bool,uint256,uint256,uint160)',False,trader_amount,1,1461446703485210103287273052203988822378723970341,label='new_actual_core_token_swap')
        harvest_before=state();send(vault,'collect(bytes32,uint256,uint256)',POOL,id,deadline(),label='new_current_f6_harvest');harvest_after=state()
        assert harvest_after['native']>harvest_before['native'] and harvest_after['token']>harvest_before['token'] and harvest_after['L']==harvest_before['L']
        send(vault,'collect(bytes32,uint256,uint256)',POOL,id,deadline(),label='new_current_f6_second_harvest');assert state()==harvest_after
        principal=words(n.read(manager,'amounts(uint256)',id));send(vault,'close(bytes32,uint256,uint256)',POOL,id,deadline(),label='new_current_f6_close')
        assert isinstance(n.call('eth_call',[{'to':POSM,'data':abi('ownerOf(uint256)',id)},'latest'],allow_error=True),dict)
        final_native=int(n.call('eth_getBalance',[vault,'latest']),16);final_token=int(n.read(ZZZ,'balanceOf(address)',vault),16)
        assert final_native>=harvest_after['native']+principal[0]and final_token>=harvest_after['token']+principal[1]
        assert int(n.read(STATE,'getLiquidity(bytes32)',POOL),16)==0
        for target in (manager,child):
            assert int(n.call('eth_getBalance',[target,'latest']),16)==0 and int(n.read(ZZZ,'balanceOf(address)',target),16)==0
            assert int(n.read(ZZZ,'allowance(address,address)',target,PERMIT2),16)==0
            approved=words(n.read(PERMIT2,'allowance(address,address,address)',target,ZZZ,POSM));assert approved[0]==0
        for target,pin in identities.items():assert '0x'+keccak256(bytes.fromhex(n.call('eth_getCode',[target,'latest'])[2:])).hex()==pin
        artifacts.check_sources();save('receipts.json',n.receipts);save('deadline-records.json',deadline_records)
        save('RESULT.json',{'successful':True,'original_active_L':'0','new_initial_L':str(initial_L),'new_increased_L':str(increased_L),'ticks':[lower,upper],'collected_ETH':str(harvest_after['native']-harvest_before['native']),'collected_ZZZ':str(harvest_after['token']-harvest_before['token']),'repeat_harvest_no_new_income':True,'actual_failed_growth_rollback':True,'principal_before_close':list(map(str,principal)),'final_custody_native':str(final_native),'final_custody_ZZZ':str(final_token),'final_active_L':'0','manager_child_residuals_zero':True,'source_unchanged':True,'production_approved':False,'control_seams':['MockAccess','typed fixture custody/budget/asset admission book','correlated USD feed pair','local balance substitutions'],'excluded':['Entry activation/growth accounting','NFT shares/rewards allocation','independent source qualification','external depth','production gas/fees or operation']})
      return 0
    except BaseException as exc:
      save('FAILED.json',{'error_class':type(exc).__name__,'reason':str(exc),'retry_or_reset':False});raise

if __name__=='__main__':raise SystemExit(main())
