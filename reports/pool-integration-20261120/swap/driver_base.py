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
OUT=Path(os.environ.get('POPL_SWAP_CASE',str(V/'pool-integration-20261120/swap/attempt2')))
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
LOCAL={'anvil_impersonateAccount','anvil_setBalance','anvil_setStorageAt','eth_sendTransaction','evm_mine','anvil_dumpState','anvil_loadState','evm_setNextBlockTimestamp'}

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

