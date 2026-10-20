"""Disposable loopback PoPL browser lab. Never accepts an RPC URL or wallet key.

Real sealed core + Entry + shared accounting; test-only venue, feeds and VRF.
Uses only unlocked accounts on an Anvil child created by this process. This is
not a public deployment tool or a production API/signing service.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256, decode_words
from zzz_ops.rpc import Rpc
from zzz_ops.errors import RpcError, WorkLimit
from indexer.monitor import Indexer
from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions
from scripts.local_wallet import LocalWallet
from scripts.local_clock import LocalChainClock
from scripts.local_inputs import deploy_inputs, configure_inputs, input_for, input_tx, settle_lp

CHAIN = 31337
UNIT = 10**18
LABELS = dict(access='ZZZAccessController', vault='ZZZVault', nft='ZZZNFT',
    liquidity='ZZZLiquidityManager', rewards='ZZZRewards', membership='ZZZMembership',
    fees='ZZZFeeController', strategy='ZZZStrategy', compounder='ZZZCompounder',
    buyback='ZZZBuyback', migration='ZZZMigration', transport='ZZZBridgeRouter',
    bridge='ZZZBridgeAdapter', receiver='ZZZMigrationReceiver', oracle='ZZZOracle',
    pools='ZZZPoolRegistry', routes='ZZZMigrationRegistry', handoff='ZZZCanonicalHandoff',
    nft_canonical='ZZZNFTCanonical', vault_canonical='ZZZVaultCanonical', fees_canonical='ZZZFeesCanonical')

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, data):
    path=Path(path);temporary=path.with_name(path.name+'.'+secrets.token_hex(6)+'.tmp')
    try:
        with temporary.open('x',encoding='utf-8',newline='\n') as output:
            output.write(json.dumps(data,indent=2)+'\n');output.flush();os.fsync(output.fileno())
        temporary.replace(path)
    finally:temporary.unlink(missing_ok=True)
def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]

def parse_payload(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('Duplicate JSON field')
            result[key]=value
        return result
    def invalid_constant(value): raise ValueError('Non-finite JSON number')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid_constant)

def validate_action(payload, accounts):
    if not isinstance(payload,dict): raise ValueError('Expected an action object')
    action=payload.get('action')
    fields={'mint':set(),'fund':set(),'rebalance':set(),'activate':{'id','amount'},
            'increase':{'id','amount'},'claim':{'id'},'claim_all':set(),'transfer':{'id'},'execute':{'draft_id'}}
    if not isinstance(action,str) or action not in fields: raise ValueError('Unsupported local action')
    expected={'action','account'}|fields[action]
    if action in ('activate','increase') and 'asset' in payload:
        expected.add('asset')
        if payload['asset'] not in ('ZZZ','USDG','USDC','ETH','TEST-1'):raise ValueError('Unsupported input asset')
    if set(payload)!=expected: raise ValueError('Unexpected or missing action fields')
    if not isinstance(payload['account'],str) or payload['account'] not in accounts: raise ValueError('Choose a disposable local test account')
    if 'id' in fields[action] and (not isinstance(payload['id'],str) or not re.fullmatch(r'[1-9][0-9]{0,77}',payload['id']) or int(payload['id'])>=2**256):
        raise ValueError('Expected a canonical uint256 NFT ID string')
    if 'amount' in fields[action]:
        minimum = 5 if action == 'increase' else 100
        if (not isinstance(payload['amount'],str) or not re.fullmatch(r'[1-9][0-9]{0,4}',payload['amount']) or
                not minimum <= int(payload['amount']) <= 99999):
            raise ValueError(f'Use a whole test-token amount from {minimum} to 99,999')
        if action == 'activate' and payload['amount'] != '100':
            raise ValueError('Activation is exactly $100 at the local $1 token price; grow LP separately')
    if 'draft_id' in fields[action] and (not isinstance(payload['draft_id'],str) or not re.fullmatch(r'[a-f0-9]{32}',payload['draft_id'])):
        raise ValueError('Invalid confirmation ID')

class LocalConflict(ValueError): pass

class OperationLedger:
    """Session-scoped replay protection; never evict an operation and reexecute it."""
    def __init__(self, path):
        self.path=path;self.revision=0;self.items={}
    def run(self, envelope, lab):
        if not isinstance(envelope,dict) or set(envelope)!={'operation_id','revision','payload'}: raise ValueError('Expected a complete operation envelope')
        identifier=envelope['operation_id'];revision=envelope['revision'];payload=envelope['payload']
        if not isinstance(identifier,str) or not re.fullmatch(r'[a-f0-9]{32}',identifier):raise ValueError('Invalid operation ID')
        if type(revision) is not int or revision<0:raise ValueError('Invalid revision')
        validate_action(payload,lab.accounts[1:])
        fingerprint=json.dumps([revision,payload],sort_keys=True,separators=(',',':'))
        if identifier in self.items:
            item=self.items[identifier]
            if item['fingerprint']!=fingerprint:raise LocalConflict('Operation ID already used for different inputs')
            return dict(item['outcome'],replayed=True)
        if payload['action']=='execute':
            # Only server-held, exact unsigned drafts may span unrelated wallet
            # operations. The draft binds this envelope revision; execution pins
            # the sender nonce and resimulates unchanged calldata and gas limits.
            lab.wallet.validate_draft(payload, revision)
        elif revision!=self.revision:raise LocalConflict('State changed. Refresh before preparing a new action')
        if len(self.items)>=256:raise LocalConflict('Local session operation limit reached; start a fresh lab')
        if lab.uncertain:raise LocalConflict('Uncertain local submission: inspect submission records and start a fresh lab; do not retry')
        item={'fingerprint':fingerprint,'outcome':{'operation_id':identifier,'status':'pending','transactions':[]}}
        self.items[identifier]=item
        try:save(self.path,self.items) # Durable intent precedes any transaction.
        except OSError:lab.uncertain=True;raise
        before=len(lab.receipts)
        try:
            lab.action(payload)
            outcome={'operation_id':identifier,'status':'confirmed'}
        except Exception as exc:
            outcome={'operation_id':identifier,'status':'failed','error':str(exc)[:350]}
        self.revision+=1
        outcome.update(revision=self.revision,transactions=[r['receipt']['transactionHash'] for r in lab.receipts[before:]],uncertain=lab.uncertain)
        item['outcome']=outcome
        try:save(self.path,self.items)
        except OSError:lab.uncertain=True;raise
        return outcome

@lru_cache(maxsize=64)
def runtime_hash(code):
    return '0x'+keccak256(bytes.fromhex(code[2:])).hex()

class LocalProjection(Projection):
    def _fresh(self, header):
        # Sample the actual chain at each initial/final freshness boundary.
        # Budget checkpoints use elapsed monotonic time, not thousands of RPCs.
        if isinstance(self.clock, LocalChainClock): self.clock.refresh()
        return super()._fresh(header)

    def _code(self, addr, expected, block):
        # Cache the pure hash of exact runtime BYTES, never the RPC read or the
        # address's identity. Every request still reads the pinned block hash.
        code=self.rpc.call('eth_getCode',[addr,block])
        if not isinstance(code,str) or len(code)>49154 or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code):
            raise ProjectionError('Missing or malformed pinned runtime code')
        if runtime_hash(code)!=expected: raise ProjectionError('Runtime code differs from deployment pin')

class LocalReadRPC(Rpc):
    """Deduplicate exact hash-bound reads within ONE local aggregate response.

    Final canonical header/depth checks, chain checks, latest reads, estimates,
    writes and independent HTTP requests are never cached.
    """
    aggregation=False
    def call(self, method, params=None):
        selector=(params or [None])[-1]
        pinned=isinstance(selector,dict) and selector.get('requireCanonical') is True and set(selector)=={'blockHash','requireCanonical'}
        cache=self.aggregation and pinned and method in ('eth_call','eth_getCode','eth_getStorageAt')
        key=json.dumps([method,params],sort_keys=True) if cache else None
        if cache and key in self.memo:return self.memo[key]
        result=super().call(method,params)
        if cache and len(self.memo)<2048:self.memo[key]=result
        return result

class Lab:
    def __init__(self, args):
        self.args=args; self.contracts={}; self.receipts=[]; self.approvals={}; self.used_sources=set()
        self.home=Path(args.state).resolve()/('run-'+time.strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3))
        self.home.mkdir(parents=True, exist_ok=False)
        self.operations=OperationLedger(self.home/'operations.json');self.uncertain=False;self.submissions=[]
        self.wallet=LocalWallet(self)
        self.process=None; self.indexer=None; self.started=time.time(); self.token=secrets.token_hex(32)
        self.api=None; self.preparer=None; self.genesis=None; self.server=None; self.rpc_port=free_port();self.lock=threading.RLock()
        self.rpc_url=f'http://127.0.0.1:{self.rpc_port}'
    def rpc(self, method, params=None):
        req=urllib.request.Request(self.rpc_url, data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or []}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=20) as response: data=json.load(response)
        if 'error' in data: raise RuntimeError(method+': '+str(data['error'].get('message','local RPC error'))[:500])
        return data['result']
    def guard(self):
        if self.process is None or self.process.poll() is not None: raise RuntimeError('Owned Anvil process is not running')
        if self.rpc('eth_chainId') != hex(CHAIN) or 'anvil' not in self.rpc('web3_clientVersion').lower(): raise RuntimeError('Local chain identity changed')
        if self.genesis and self.rpc('eth_getBlockByNumber',['0x0',False])['hash'] != self.genesis: raise RuntimeError('Local genesis changed')
    @lru_cache(maxsize=2048)
    def encode(self, signature, *args, constructor=False):
        result=subprocess.run([self.args.cast,'abi-encode' if constructor else 'calldata',signature,*[str(a).lower() if isinstance(a,bool) else str(a) for a in args]],capture_output=True,text=True,timeout=20)
        if result.returncode: raise RuntimeError('Local ABI encoding failed: '+result.stderr[:400])
        return result.stdout.strip()
    def read(self, role, signature, *args):
        target=self.contracts.get(role,role)
        return decode_words(self.rpc('eth_call',[{'to':target,'data':self.encode(signature,*args)},'latest']))
    def uint(self, role, signature, *args): return int(self.read(role,signature,*args)[0],16)
    def addr(self, role, signature, *args): return '0x'+self.read(role,signature,*args)[0][-40:]
    def block(self): return self.rpc('eth_getBlockByNumber',['latest',False])
    def clock(self): return int(self.block()['timestamp'],16)
    def pin(self, addr):
        return {'address':addr,'code_hash':'0x'+keccak256(bytes.fromhex(self.rpc('eth_getCode',[addr,'latest'])[2:])).hex()}
    def simulate(self, tx):
        self.guard()
        if tx['from'] not in self.accounts: raise ValueError('Only disposable local accounts are permitted')
        wrap_limit=(4_000_000*UNIT if tx['from']==self.accounts[0] else 99_999*UNIT) if getattr(self,'weth',None)==tx.get('to') and tx.get('data')=='0xd0e30db0' else UNIT
        if getattr(self,'native_input',False) and tx.get('to')==self.contracts.get('entry') and tx.get('data','').startswith('0x'+keccak256(b'execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))')[:4].hex()):wrap_limit=99_999*UNIT
        if int(tx.get('value','0x0'),16)>wrap_limit: raise ValueError('Local value limit exceeded')
        response=self.rpc('eth_call',[tx,'latest'])
        if tx.get('data','').startswith('0x095ea7b3') and response not in ('0x','0x'+f'{1:064x}'):
            raise ValueError('Token rejected exact approval; reset-only tokens are unsupported')
        gas=int(self.rpc('eth_estimateGas',[tx]),16)
        if gas>29_000_000: raise ValueError('Local gas limit exceeded')
        price=int(self.rpc('eth_gasPrice'),16)
        limit=min(30_000_000,(gas*120+99)//100)
        if int(self.rpc('eth_getBalance',[tx['from'],'latest']),16)<int(tx.get('value','0x0'),16)+limit*price: raise ValueError('Insufficient local balance')
        return {**tx,'gas':hex(limit),'gasPrice':hex(price)}, {'estimate':str(gas),'gas_price_wei':str(price),'max_cost_wei':str(limit*price)}
    def send(self, tx, label, approved=False):
        fresh, gas=self.simulate({k:v for k,v in tx.items() if k not in ('gas','gasPrice')})
        if approved:
            if int(fresh['gas'],16)>int(tx['gas'],16) or int(fresh['gasPrice'],16)>int(tx['gasPrice'],16):
                raise ValueError('Gas requirement increased; prepare a new confirmation')
            self.rpc('eth_call',[tx,'latest'])
        else:tx=fresh
        before=self.rpc('eth_getBalance',[tx['from'],'latest'])
        submission={'label':label,'transaction':tx,'status':'submitting'}
        self.submissions.append(submission);save(self.home/'submissions.json',self.submissions)
        try:
            transaction=self.rpc('eth_sendTransaction',[tx]);submission.update(hash=transaction,status='pending')
            save(self.home/'submissions.json',self.submissions)
            for _ in range(100):
                receipt=self.rpc('eth_getTransactionReceipt',[transaction])
                if receipt: break
                time.sleep(.05)
            else: raise RuntimeError('Local receipt timeout; do not resubmit blindly')
            submission.update(status='mined',receipt=receipt)
            save(self.home/'submissions.json',self.submissions)
        except Exception:
            self.uncertain=True
            submission['status']='uncertain';save(self.home/'submissions.json',self.submissions)
            raise
        item={'label':label,'transaction':tx,'receipt':receipt,'gas_quote':gas,'native_before':before,'native_after':None}
        self.receipts.append(item);save(self.home/'receipts.json',self.receipts)
        item['native_after']=self.rpc('eth_getBalance',[tx['from'],'latest'])
        save(self.home/'receipts.json',self.receipts)
        if int(receipt['status'],16)!=1: raise RuntimeError('Local transaction reverted: '+transaction)
        return receipt
    def call(self, role, signature, *args, sender=None, value=0):
        return self.send({'from':sender or self.accounts[0],'to':self.contracts.get(role,role),'data':self.encode(signature,*args),'value':hex(value)},signature)
    def deploy(self, name, signature='constructor()', args=(), *, local=False):
        source='LocalInputFixtures.sol' if name.startswith('LocalInput') else (('LocalDemoVenue.sol' if name.startswith('Local') else name+'.sol') if name!='MockVRF' else 'MockVRF.sol')
        if name=='LocalNativeRegistry':source='LocalNativeRegistry.sol'
        path=Path(self.args.fixture_artifacts if local else self.args.artifacts)/source/(name+'.json')
        artifact=json.loads(path.read_text(encoding='utf-8'))
        metadata=artifact.get('metadata') or json.loads(artifact['rawMetadata'])
        # Authenticate source content, including dependencies, before reuse.
        for source, info in metadata['sources'].items():
            key=(source,info['keccak256'])
            if key in self.used_sources: continue
            file=ROOT/source
            if not file.is_file() or '0x'+keccak256(file.read_bytes()).hex()!=info['keccak256']: raise RuntimeError('Stale compiler source: '+source)
            self.used_sources.add(key)
        code=artifact['bytecode']['object']
        if not code.startswith('0x'): code='0x'+code
        receipt=self.send({'from':self.accounts[0],'data':code+self.encode(signature,*args,constructor=True)[2:],'value':'0x0'},'deploy '+name)
        address=receipt['contractAddress'].lower()
        if name=='ZZZNFT': self.nft_block=int(receipt['blockNumber'],16)
        self.artifacts.append({'name':name,'file':str(path),'sha256':digest(path),'address':address})
        return address
    def bind(self, role, address):
        self.contracts[role]=address
        self.call('access','bind(bytes32,address)','0x'+keccak256(LABELS[role].encode()).hex(),address)
    def start(self):
        self.native_input=bool(getattr(self.args,'native_input',False))
        self.artifacts=[]
        self.log=(self.home/'anvil.log').open('w',encoding='utf-8')
        command=[self.args.anvil,'--host','127.0.0.1','--port',str(self.rpc_port),'--chain-id',str(CHAIN),'--silent']
        if getattr(self.args,'named_assets',False):command+=['--balance','10000000']
        self.process=subprocess.Popen(command,stdout=self.log,stderr=subprocess.STDOUT)
        for _ in range(100):
            try: self.guard();break
            except (OSError,RuntimeError): time.sleep(.1)
        else: raise RuntimeError('Anvil did not start')
        self.genesis=self.rpc('eth_getBlockByNumber',['0x0',False])['hash']
        self.accounts=[x.lower() for x in self.rpc('eth_accounts')[:3]]
        admin,alice,bob=self.accounts
        print('Deploying isolated PoPL core; local fixture boundaries only.',flush=True)
        self.contracts['access']=self.deploy('ZZZAccessController','constructor(uint256,address[],address[],address,address)',(0,'['+admin+']','['+admin+']',admin,admin))
        if getattr(self.args,'named_assets',False):deploy_inputs(self)
        else:
            first=self.deploy('LocalToken','constructor(string)',('TEST-A',),local=True)
            second=self.deploy('LocalToken','constructor(string)',('TEST-B',),local=True)
            self.tokens=sorted([first,second])
        self.feed=self.deploy('LocalFeed',local=True)
        self.vrf=self.deploy('MockVRF',local=True)
        ac=self.contracts['access']
        self.bind('vault',self.deploy('ZZZVault','constructor(address,uint256,address)',(ac,CHAIN,admin)))
        self.bind('nft',self.deploy('ZZZNFT','constructor(address,string)',(ac,'')))
        self.bind('liquidity',self.deploy('LocalDemoVenue','constructor(address,address,address)',(ac,*self.tokens),local=True))
        for role in ('rewards','membership','fees','strategy','compounder','migration','transport','receiver','pools','routes','handoff'):
            if role=='pools' and self.native_input:
                self.bind(role,self.deploy('LocalNativeRegistry','constructor(address,address,address)',(ac,self.weth,self.tokens[1]),local=True))
            else:self.bind(role,self.deploy(LABELS[role],'constructor(address)',(ac,)))
        self.bind('buyback',self.deploy('ZZZBuyback','constructor(address,address,uint256)',(ac,self.tokens[0],1000*UNIT)))
        self.bind('bridge',self.deploy('ZZZBridgeAdapter','constructor(address,address)',(ac,self.contracts['transport'])))
        self.bind('oracle',self.deploy('ZZZOracle','constructor(address,address)',(ac,ZERO)))
        self.bind('nft_canonical',self.deploy('ZZZNFTCanonical','constructor(address,address)',(ac,self.contracts['nft'])))
        self.bind('vault_canonical',self.deploy('ZZZVaultCanonical','constructor(address,address,uint256)',(ac,self.contracts['vault'],CHAIN)))
        self.bind('fees_canonical',self.deploy('ZZZFeesCanonical','constructor(address,address)',(ac,self.contracts['fees'])))
        self.contracts['royalties']=self.addr('nft','royaltyRewards()')
        self.contracts['claim_router']=self.addr('nft','claimRouter()')
        self.contracts['entry']=self.addr('pools','activationEntry()')
        self.call('nft','configureRandomness(address,bytes32,uint256,uint16,uint32,bool)',self.vrf,'0x'+'01'*32,1,3,500000,False)
        for token in self.tokens:
            self.call('oracle','setFeed(address,address,uint32)',token,self.feed,3600)
            self.call('rewards','addAsset(address)',token)
            for account in self.accounts:
                if token==getattr(self,'weth',None):self.call(token,'transfer(address,uint256)',account,100000*UNIT)
                else:self.call(token,'mint(address,uint256)',account,100000*UNIT)
            self.call(token,'transfer(address,uint256)' if token==getattr(self,'weth',None) else 'mint(address,uint256)',self.contracts['liquidity'],1000000*UNIT)
            self.call(token,'approve(address,uint256)',self.contracts['liquidity'],100000*UNIT)
        self.configure_pool(1000)
        if getattr(self.args,'named_assets',False):configure_inputs(self)
        self.call('access','seal()')
        self.setup_api()
        for value in (0,1432,2000,12000):
            identifier=self.mint(alice)
            if value: self.contribute(alice,identifier,value*UNIT,False)
        self.sync()
        self.fund()
        self.sync()
        self.preparer=Transactions(self.api,{'schema':1,'chain_id':CHAIN,'projection_sha256':self.api.identity,'fee_policy':{'estimate_includes_all_fees':True,'review_hash':'0x'+keccak256(b'LOCAL ANVIL ONLY; not production fee review').hex(),'max_gas_price_wei':str(100*10**9),'max_network_fee_wei':str(UNIT)}})
        save(self.home/'deployment.json',{'chain_id':CHAIN,'rpc':self.rpc_url,'genesis':self.genesis,'accounts':self.accounts,'contracts':self.contracts,'tokens':self.tokens,'artifacts':self.artifacts,'boundaries':['LocalDemoVenue replaces LiquidityManager/Uniswap','LocalFeed always fresh $1 mock','MockVRF has no verifiable randomness','Unlocked disposable Anvil accounts only']})
        print('Local deployment and confirmed API ready.',flush=True)
    def configure_pool(self, width):
        sig='configure(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))'
        value=f'(({self.tokens[0]},{self.tokens[1]},3000,60,{ZERO}),true,true,{width},300,100,100,600,{5*UNIT},{10**30})'
        first=ZERO if getattr(self,'native_input',False) else self.tokens[0]
        if getattr(self,'native_input',False):sig=sig.replace('configure(', 'configureNative(');value=value.replace(self.tokens[0],ZERO)
        self.pool='0x'+keccak256(bytes.fromhex(self.encode('key(address,address,uint24,int24,address)',first,self.tokens[1],3000,60,ZERO,constructor=True)[2:])).hex()
        if self.uint('access','isSealed()'):
            data=self.encode(sig,value);salt='0x'+secrets.token_hex(32);empty='0x'+'00'*32
            self.call('access','schedule(address,uint256,bytes,bytes32,bytes32,uint256)',self.contracts['pools'],0,data,empty,salt,0)
            self.call('access','execute(address,uint256,bytes,bytes32,bytes32)',self.contracts['pools'],0,data,empty,salt)
        else:self.call('pools',sig,value)
        self.width=width
    def setup_api(self):
        c=self.contracts
        emitters=sorted(c[r] for r in ('nft','vault','rewards','royalties','handoff','fees','membership'))
        config={'schema':2,'chain_id':CHAIN,'rpc_urls':[self.rpc_url],'deployment_block':1,'deployment_block_hash':self.rpc('eth_getBlockByNumber',['0x1',False])['hash'],'confirmations':1,'max_block_age_seconds':120,'contracts':{r:self.pin(c[r]) for r in ('access','nft','vault','rewards','royalties','claim_router','handoff','vault_canonical')},'assets':[{'address':a,'code_hash':self.pin(a)['code_hash'],'symbol':'TEST-'+str(i+1),'decimals':18} for i,a in enumerate(self.tokens)]+[{'address':ZERO,'code_hash':None,'symbol':'ETH','decimals':18}], 'history':{'database':str(self.home/'indexer.sqlite'),'start_block':1,'start_parent_hash':self.genesis,'contracts':emitters,'max_events':10000},'earnings_history':{'schema':1,'deployments':[{'controller':c['access'],'fees':self.pin(c['fees']),'membership':self.pin(c['membership'])}],'prices':None}}
        # Native ETH intentionally has no USD mark. Test tokens use the pinned
        # mock feed; no production stablecoin peg or native price is invented.
        config['earnings_history']['prices']={'oracle':self.pin(c['oracle']),'sequencer':None,'feeds':[{'asset':a,'priced_token':a,'token_code_hash':self.pin(a)['code_hash'],'source':self.feed,'source_code_hash':self.pin(self.feed)['code_hash'],'max_age':3600,'feed_decimals':8} for a in self.tokens]}
        if getattr(self,'input_assets',None):
            zzz=input_for(self,'ZZZ')['address']
            for a in config['assets']:
                if a['address']!=ZERO:a['symbol']='ZZZ' if a['address']==zzz else 'WETH'
        config['deployment_block']=self.nft_block
        config['deployment_block_hash']=self.rpc('eth_getBlockByNumber',[hex(self.nft_block),False])['hash']
        config['history']['start_block']=self.nft_block
        config['history']['start_parent_hash']=self.rpc('eth_getBlockByNumber',[hex(self.nft_block-1),False])['hash']
        save(self.home/'api.json',config)
        index={'chain_id':CHAIN,'rpc_urls':[self.rpc_url],'start_block':1,'start_parent_hash':self.genesis,'confirmations':1,'block_chunk':100,'contracts':emitters,'database':str(self.home/'indexer.sqlite')}
        index.update(start_block=self.nft_block,start_parent_hash=config['history']['start_parent_hash'])
        save(self.home/'indexer.json',index); self.indexer=Indexer(index)
        self.indexer.db.close()
        self.indexer.db=sqlite3.connect(index['database'],timeout=10,check_same_thread=False)
        self.indexer.db.execute('PRAGMA foreign_keys=ON')
        self.read_rpc=LocalReadRPC([self.rpc_url],CHAIN,timeout=5,retries=2)
        self.api=LocalProjection(config,rpc=self.read_rpc,clock=LocalChainClock(self.clock))
    def sync(self):
        self.guard();self.rpc('evm_mine')
        while self.indexer.step(): pass
    def mint(self, owner):
        if self.uint('nft','mintedCount()')>=20: raise ValueError('Local browser fixture capped at 20 NFTs')
        self.call('vault','mintDormant()',sender=owner,value=UNIT//20)
        count=self.uint('nft','mintedCount()');identifier=self.uint('nft','tokenAtOrdinal(uint256)',count)
        request=self.uint('nft','requestOf(uint256)',identifier)
        self.call(self.vrf,'fulfill(uint256,uint256,uint256)',request,count*721,count*7919)
        self.call('nft','finalizeTraits(uint256)',identifier)
        return str(identifier)
    def contribution_tx(self, owner, identifier, amount, increase):
        # Original source is already a pool asset; no unqualified V3 route is
        # pretended here. Real Strategy balances it in the test-only venue.
        return input_tx(self,owner,identifier,amount//UNIT,increase)
    def contribute(self, owner, identifier, amount, increase):
        # Cheap shape, lifecycle and balance checks precede approval. Entry is
        # simulated after approval; a later failure can still leave allowance.
        active=bool(self.uint('vault','nftBucket(uint256)',identifier))
        if active!=increase:raise ValueError('Activate a dormant NFT or add LP to an already active NFT')
        minimum = 5 if increase else 100
        if not minimum*UNIT<=amount<=99999*UNIT:raise ValueError(f'Local contribution outside {minimum}..99,999')
        token=input_for(self)['address']
        if self.uint(token,'balanceOf(address)',owner)<amount:raise ValueError('Insufficient local input balance')
        self.call(token,'approve(address,uint256)',self.contracts['entry'],amount,sender=owner)
        self.send(self.contribution_tx(owner,identifier,amount,increase),'increase' if increase else 'activate')
    def fund(self):
        active=[i for i in self.ids() if self.uint('vault','nftBucket(uint256)',i)]
        if not active: raise ValueError('Activate an NFT before funding fee streams')
        bucket=self.uint('vault','nftBucket(uint256)',active[0])
        self.call('liquidity','fundFees(uint256,uint256)',100*UNIT,0)
        self.call('vault','collectFees(uint256,uint256)',bucket,self.clock()+120)
        settle_lp(self,active)
        self.send({'from':self.accounts[0],'to':self.contracts['royalties'],'value':hex(UNIT//100),'data':'0x'},'fund local ETH royalties')
        self.call('royalties','sync(address)',ZERO)
    def ids(self): return [str(self.uint('nft','tokenAtOrdinal(uint256)',n)) for n in range(1,self.uint('nft','mintedCount()')+1)]
    def optional_earnings(self, identifier=None):
        # Optional history must not erase independently confirmed balances.
        # Exhausted budgets remain terminal; never retry or fabricate zero USD.
        try:
            return self.api.earnings(identifier)
        except WorkLimit:
            raise
        except RpcError:
            print(json.dumps({'event':'local_earnings_unavailable','scope':'collection' if identifier is None else 'nft'}),flush=True)
            return {'available':False,'reason':'earnings_unavailable'}
    def state(self):
        self.sync()
        self.read_rpc.memo={};self.read_rpc.aggregation=True
        try:
            positions=[self.api.nft(i) for i in self.ids()]
            for position in positions:
                position['earnings']=(self.optional_earnings(position['token_id']) if position['position']['activated']
                                      else {'available':False,'reason':'not_activated'})
            inputs=getattr(self,'input_assets',None)
            return {'mode':'LOCAL ANVIL TEST ONLY','revision':self.operations.revision,'uncertain':self.uncertain,'chain_id':CHAIN,'accounts':self.accounts[1:],'contracts':self.contracts,'pool':self.pool,'tokens':self.tokens,'input_assets':inputs,'contribution_flow':{'native_eth_atomic':bool(getattr(self,'native_input',False)),'max_transactions':2,'activation_usd':100,'min_topup_usd':5},'protocol':self.api.protocol(),'nfts':positions,'earnings':self.optional_earnings(),'transactions':[{'label':r['label'],'hash':r['receipt']['transactionHash'],'block':int(r['receipt']['blockNumber'],16),'gas_used':int(r['receipt']['gasUsed'],16)} for r in self.receipts[-12:]]}
        finally:self.read_rpc.aggregation=False;self.read_rpc.memo={}
    def action(self, payload):
        validate_action(payload,self.accounts[1:])
        if payload.get('asset') is not None:
            raise ValueError('Named input contributions require the explicit prepare/execute confirmation flow')
        action=payload.get('action');owner=payload.get('account')
        if owner not in self.accounts[1:]: raise ValueError('Choose a disposable local test account')
        self.sync()
        if action=='execute':return self.wallet.execute(payload)
        if action=='mint':
            if self.uint('nft','mintedCount()')>=20: raise ValueError('Local browser fixture capped at 20 NFTs')
            # Exercise published unsigned preparation before submitting locally.
            draft=self.preparer.prepare({'action':'mint','wallet':owner})
            self.send({k:v for k,v in draft['transaction'].items() if k!='chainId'},'prepared local mint')
            identifier=self.uint('nft','tokenAtOrdinal(uint256)',self.uint('nft','mintedCount()'))
            self.call(self.vrf,'fulfill(uint256,uint256,uint256)',self.uint('nft','requestOf(uint256)',identifier),self.uint('nft','mintedCount()')*721,12345)
            self.call('nft','finalizeTraits(uint256)',identifier)
        elif action=='fund': self.fund()
        elif action=='rebalance':
            active=[i for i in self.ids() if self.uint('vault','nftBucket(uint256)',i)]
            if not active: raise ValueError('Activate an NFT before rebalancing')
            self.rpc('evm_increaseTime',[601]);self.rpc('evm_mine')
            self.configure_pool(2000 if self.width==1000 else 1000)
            bucket=self.uint('vault','nftBucket(uint256)',active[0])
            self.call('vault','rebalance(uint256,uint128,uint256)',bucket,1,self.clock()+120)
        elif action in ('activate','increase','claim','transfer'):
            identifier=payload.get('id')
            if not isinstance(identifier,str) or identifier not in self.ids(): raise ValueError('Unknown local NFT')
            if self.addr('nft','ownerOf(uint256)',identifier)!=owner: raise ValueError('Selected wallet does not own this NFT')
            if action in ('activate','increase'):
                amount=payload.get('amount')
                if not isinstance(amount,str) or not re.fullmatch(r'[1-9][0-9]{0,4}',amount): raise ValueError('Use a whole test-token amount, at most 99,999')
                self.contribute(owner,identifier,int(amount)*UNIT,action=='increase')
            elif action=='transfer':
                other=next(a for a in self.accounts[1:] if a!=owner)
                self.call('nft','transferFrom(address,address,uint256)',owner,other,identifier,sender=owner)
            else:
                item=self.api.nft(identifier)
                claims=[{'token_id':identifier,'asset':a['asset'],'royalty':scope=='royalties'} for scope in ('lp','royalties') for a in item['claimable'][scope] if int(a['raw'])>0 and
                        (item['claimable'].get('default_settlement')!='native_eth' or a['asset']==ZERO)]
                draft=self.preparer.prepare({'action':'claim','wallet':owner,'claims':claims})
                self.send({k:v for k,v in draft['transaction'].items() if k!='chainId'},'prepared combined claim')
        else: raise ValueError('Unsupported local action')
        # Outcome is saved before optional, fallible UI/API refresh.
    def validate_wallet_action(self,payload):
        validate_action(payload,self.accounts[1:])
    def close(self):
        if self.indexer: self.indexer.db.close()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        if hasattr(self,'log'): self.log.close()

class LocalHTTPServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,*args,**kwargs):
        self.slots=threading.BoundedSemaphore(12)
        super().__init__(*args,**kwargs)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()

def make_server(lab):
    website=Path(lab.args.website).resolve() if lab.args.website else None
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def setup(self):
            super().setup();self.connection.settimeout(5)
        def valid(self, write=False):
            host=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get_all('Host')!=[host]: return False
            if self.headers.get('Transfer-Encoding') or self.headers.get('Expect'): return False
            if write and (self.headers.get_all('Origin')!=['http://'+host] or self.headers.get_all('X-Local-Token')!=[lab.token] or self.headers.get_all('Content-Type')!=['application/json']): return False
            return True
        def output(self, status, data, mime='application/json'):
            raw=json.dumps(data).encode() if mime=='application/json' else data
            try:
                style="'self' 'unsafe-inline'" if self.path.startswith('/app/') else "'self'"
                self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',f"default-src 'self'; script-src 'self'; style-src {style}; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'");self.end_headers();self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,TimeoutError):pass # Outcome already saved; never resubmit.
        def do_GET(self):
            if not self.valid(): return self.output(403,{'error':'Invalid local host'})
            try:
                if self.path=='/session': return self.output(200,{'token':lab.token,'mode':'LOCAL ANVIL TEST ONLY','chain_id':CHAIN,'accounts':lab.accounts[1:]})
                if self.path=='/state':
                    if not lab.lock.acquire(blocking=False):return self.output(409,{'error':'Local operation in progress; refresh shortly'})
                    try:result=lab.state()
                    finally:lab.lock.release()
                    return self.output(200,result)
                local={'/':'index.html','/local.js':'local.js','/local.css':'local.css'}
                if website and self.path.startswith('/app/'):
                    name=self.path[5:] or 'index.html'
                    allowed={'index.html','app.js','domain.js','wallet.js','artworks.js','palette-system.js','styles.css','local-client.js','local-view.js','local-view.css'}
                    if name not in allowed and not re.fullmatch(r'assets/[a-zA-Z0-9/_\-.]+\.(svg|png|jpg|jpeg|webp|json|mp4)',name):
                        return self.output(404,{'error':'Unknown website resource'})
                    if '..' in Path(name).parts:return self.output(404,{})
                    path=(website/name).resolve()
                    if not path.is_relative_to(website):return self.output(404,{})
                    if name.startswith('assets/') and not path.is_relative_to(website/'assets'):return self.output(404,{})
                elif self.path in local: path=ROOT/'tools/local-ui'/local[self.path]
                elif website and self.path=='/palette-system.js': path=website/'palette-system.js'
                elif website and self.path.startswith('/assets/nfts/') and re.fullmatch(r'/assets/nfts/[a-zA-Z0-9/_\-.]+\.(svg|png)',self.path):
                    path=(website/self.path[1:]).resolve()
                    if not path.is_relative_to(website/'assets/nfts'): return self.output(404,{})
                else:return self.output(404,{'error':'Unknown local resource'})
                self.output(200,path.read_bytes(),mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            except Exception as exc:
                with (lab.home/'errors.log').open('a',encoding='utf-8') as f: traceback.print_exc(file=f)
                self.output(503,{'error':str(exc)[:350]})
        def do_POST(self):
            if not self.valid(True): return self.output(403,{'error':'Local origin/session required'})
            length=self.headers.get_all('Content-Length',[])
            if len(length)!=1 or not re.fullmatch(r'[1-9][0-9]{0,3}',length[0]) or int(length[0])>2048:return self.output(400,{'error':'Invalid bounded request'})
            if self.path not in ('/action','/prepare'):return self.output(404,{})
            try:
                raw=self.rfile.read(int(length[0]))
                if len(raw)!=int(length[0]):raise ValueError('Incomplete request body')
                payload=parse_payload(raw)
                if self.path=='/prepare':
                    if not lab.lock.acquire(blocking=False):return self.output(409,{'error':'Local operation in progress; refresh shortly'})
                    try:result=lab.wallet.prepare(payload)
                    finally:lab.lock.release()
                    return self.output(200,result)
                if payload=={'action':'stop'}:
                    if not lab.lock.acquire(blocking=False):return self.output(409,{'error':'Wait for the active operation before stopping'})
                    # Keep the lock held: no transaction can race shutdown.
                    self.output(200,{'stopping':True})
                    threading.Thread(target=self.server.shutdown,daemon=True).start()
                else:
                    if not lab.lock.acquire(blocking=False):return self.output(409,{'error':'Local operation in progress; retry the SAME operation ID'})
                    try: result=lab.operations.run(payload,lab)
                    finally:lab.lock.release()
                    self.output(200,result)
            except Exception as exc:
                with (lab.home/'errors.log').open('a',encoding='utf-8') as f: traceback.print_exc(file=f)
                self.output(409 if isinstance(exc,LocalConflict) else 400,{'error':str(exc)[:350],'rejected':isinstance(exc,ValueError)})
    return LocalHTTPServer(('127.0.0.1',lab.args.port),Handler)

def serve(lab):
    server=make_server(lab);lab.server=server
    save(lab.home/'running.json',{'url':f'http://127.0.0.1:{server.server_port}','pid':__import__('os').getpid(),'anvil_pid':lab.process.pid,'state':str(lab.home),'scope':'local disposable fixture, no public assets'})
    print(f'OPEN http://127.0.0.1:{server.server_port} | Evidence: {lab.home}',flush=True)
    try:server.serve_forever()
    finally:server.server_close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('anvil','cast','artifacts','fixture-artifacts','state'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--website',required=True);parser.add_argument('--port',type=int,default=8890)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--named-assets',action='store_true',help='Disposable ZZZ/USDG/USDC/ETH UI fixtures; not public routes')
    parser.add_argument('--native-input',action='store_true',help='Local-only native admission mock; ETH wraps atomically inside production Entry')
    args=parser.parse_args()
    if args.native_input and not args.named_assets:parser.error('--native-input requires --named-assets')
    if not (Path(args.website)/'palette-system.js').is_file() or not (Path(args.website)/'assets/nfts').is_dir():
        parser.error('--website must contain the existing palette-system.js and assets/nfts')
    if not 1024<=args.port<=65535:parser.error('Use a local unprivileged port between 1024 and 65535')
    if not args.verify_only:
        with socket.socket() as probe:probe.bind(('127.0.0.1',args.port))
    lab=Lab(args)
    try:
        lab.start()
        if args.verify_only:
            save(lab.home/'snapshot.json',lab.state());print('Verified local deployment + API.',flush=True)
        else:serve(lab)
    finally:lab.close()
if __name__=='__main__':main()
