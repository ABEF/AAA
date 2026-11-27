"""NEW isolated Anvil proof of the constructor STATICCALL read tool.

Only newly compiled test-double runtimes are injected on a newly owned node.
This is not current PoPL runtime, Robinhood provider or production acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import unittest
import urllib.request

from frontend_api import canonical_cache as cache
from frontend_api import read_batch as batch
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError
from zzz_ops.work_budget import Budget, request_scope
from tests_python.test_read_batch import CURRENCIES, ETH, OWNER, View, ZZZ

ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
SOLC=TOOLS/'toolchain-0.8.26/solc.exe'
ANVIL=TOOLS/'foundry-v1.4.4/anvil.exe'
SOURCE='''// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
contract ReadOnlyFixture {
 function ownerOf(uint256) external pure returns(address){return address(99);}
 function mintOrdinalOf(uint256 id) external pure returns(uint256){return id+7;}
 function tokenAtOrdinal(uint256 ordinal) external pure returns(uint256){return ordinal-7;}
 function sharesOf(uint256 id) external pure returns(uint256){return id*10;}
 function nftBucket(uint256) external pure returns(uint256){return 1;}
 function weightOf(uint256 id) external pure returns(uint256){return id%3+1;}
 function rewardBucket(uint256) external pure returns(uint256){return 1;}
 function claimableComponents(uint256 id,address) external pure returns(uint256,uint256){return(id*13,id*7);}
 function claimable(uint256 id,address) external pure returns(uint256){return id*20;}
}
contract WritingFixture {
 fallback() external {assembly{sstore(0,1)}}
}
'''


class WireRPC:
    def __init__(self,url,process):
        self.url=url
        self.process=process
        self.sequence=0
        self.calls=[]
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self,method,params=None):
        if self.process.poll() is not None:
            raise RpcError('Owned local fixture process is not running')
        self.sequence+=1
        self.calls.append((method,params))
        request={'jsonrpc':'2.0','id':self.sequence,'method':method,'params':params or []}
        raw=json.dumps(request).encode()
        with self.opener.open(urllib.request.Request(self.url,data=raw,
                headers={'Content-Type':'application/json'}),timeout=5) as handle:
            payload=handle.read(1024*1024+1)
        if len(payload)>1024*1024:
            raise RpcError('Local fixture response exceeded bound')
        body=json.loads(payload)
        if body.get('id')!=self.sequence or body.get('jsonrpc')!='2.0' or 'error' in body:
            raise RpcError('Local fixture RPC failed')
        return body['result']


class ReadBatchEVMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SOLC.is_file() or not ANVIL.is_file():
            raise unittest.SkipTest('Pinned local Solidity/Anvil tools unavailable')
        assert hashlib.sha256(SOLC.read_bytes()).hexdigest()=='537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67'
        cls.anvil_sha256=hashlib.sha256(ANVIL.read_bytes()).hexdigest()
        assert cls.anvil_sha256=='d438383b871c726407ecc5829279bea44ceac63a712be9e010813ca0a15434b6'
        cls.anvil_version=subprocess.check_output([str(ANVIL),'--version'],timeout=5).decode()
        request={'language':'Solidity','sources':{'ReadOnlyFixture.sol':{'content':SOURCE}},
                 'settings':{'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},
                    'viaIR':True,'evmVersion':'cancun','outputSelection':{'*':{'*':['evm.deployedBytecode.object']}}}}
        result=subprocess.run([str(SOLC),'--standard-json'],input=json.dumps(request).encode(),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
        compiled=json.loads(result.stdout)
        assert not any(e['severity']=='error' for e in compiled.get('errors',[]))
        cls.code={k:'0x'+v['evm']['deployedBytecode']['object'] for k,v in compiled['contracts']['ReadOnlyFixture.sol'].items()}
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        assert port!=8902
        cls.chain_id=(1<<48)|int.from_bytes(os.urandom(6),'big')
        cls.process=subprocess.Popen([str(ANVIL),'--host','127.0.0.1','--port',str(port),
            '--chain-id',str(cls.chain_id),'--gas-limit','30000000','--silent'],stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        cls.addClassCleanup(cls.stop)
        cls.wire=WireRPC('http://127.0.0.1:'+str(port),cls.process)
        end=time.monotonic()+10
        while True:
            if cls.process.poll() is not None:
                raise AssertionError('New isolated Anvil stopped before readiness')
            try:
                if cls.wire.call('eth_chainId',[])==hex(cls.chain_id):break
            except (OSError,RpcError):pass
            if time.monotonic()>=end:raise AssertionError('New isolated Anvil readiness timeout')
            time.sleep(.05)
        cls.genesis=cls.wire.call('eth_getBlockByNumber',['0x0',False])['hash']
        cls.fixture_installs=[]
        assert cls.wire.call('eth_getTransactionCount',[ETH,'latest'])=='0x0'
        assert cls.wire.call('eth_blockNumber',[])=='0x0'
        cls.modules=tuple(cls.install('ReadOnlyFixture',i) for i in range(4))
        cls.writing=cls.install('WritingFixture',4)

    @classmethod
    def stop(cls):
        if cls.process.poll() is None:
            cls.process.terminate()
        try:cls.process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            cls.process.kill();cls.process.communicate(timeout=5)

    @classmethod
    def install(cls,name,index):
        if cls.process.poll() is not None or cls.wire.call('eth_chainId',[])!=hex(cls.chain_id):
            raise AssertionError('Wrong or stopped isolated test chain')
        assert cls.wire.call('eth_getBlockByNumber',['0x0',False])['hash']==cls.genesis
        assert cls.wire.call('eth_getTransactionCount',[ETH,'latest'])=='0x0'
        assert cls.wire.call('eth_blockNumber',[])=='0x0'
        target='0x'+f'{(cls.chain_id<<16)+index+1:040x}'
        assert cls.wire.call('eth_getCode',[target,'latest'])=='0x'
        # Explicit isolated test seam: no real contract/transaction acceptance
        # is inferred from installing these tiny fixture runtimes directly.
        cls.wire.call('anvil_setCode',[target,cls.code[name]])
        assert cls.wire.call('eth_getCode',[target,'latest'])==cls.code[name]
        cls.fixture_installs.append({'fixture':name,'address':target,
            'runtime_sha256':hashlib.sha256(bytes.fromhex(cls.code[name][2:])).hexdigest()})
        return target

    def view(self,modules=None):
        from types import SimpleNamespace
        p=View(self.wire)
        p.chain=self.chain_id
        p.contracts={r:SimpleNamespace(address=a) for r,a in zip(('nft','vault','royalties','rewards'),modules or self.modules)}
        header=self.wire.call('eth_getBlockByNumber',['latest',False])
        return p,{'blockHash':header['hash'],'requireCanonical':True}

    def test_actual_creation_returns_maximum_fixed_records_without_persistent_code_or_nonce(self):
        p,block=self.view()
        nonce=self.wire.call('eth_getTransactionCount',[ETH,'latest'])
        creation_address='0x'+keccak256(bytes.fromhex('d694'+'00'*20+'80')).hex()[-40:]
        self.assertEqual(nonce,'0x0')
        self.assertEqual(self.wire.call('eth_getCode',[creation_address,'latest']),'0x')
        first=len(self.wire.calls)
        with request_scope(Budget(seconds=25,calls=1024,posts=2048)),cache.scope(p):
            self.assertEqual(batch.prefetch_accounts(p,block,(11,12,13,14),(ETH,ZZZ),CURRENCIES),1)
            self.assertEqual(p._addr('nft','ownerOf(uint256)',11,block=block),OWNER)
            self.assertEqual(p._uint('nft','tokenAtOrdinal(uint256)',21,block=block),14)
            self.assertEqual(p._uint('rewards','claimable(uint256,address)',12,ETH,block=block),240)
            self.assertEqual(p._uint('royalties','claimable(uint256,address)',14,CURRENCIES[-1],block=block),280)
            self.assertEqual(batch.prefetch_accounts(p,block,(11,12,13,14),(ETH,ZZZ),CURRENCIES),0)
        reads=self.wire.calls[first:]
        self.assertEqual(len(reads),1)
        self.assertEqual(reads[0][0],'eth_call')
        self.assertNotIn('to',reads[0][1][0])
        self.assertNotEqual(batch.MAGIC[0],0xef)
        self.assertEqual(self.wire.call('eth_getTransactionCount',[ETH,'latest']),nonce)
        self.assertEqual(self.wire.call('eth_getCode',[creation_address,'latest']),'0x')

    def test_actual_staticcall_refuses_child_storage_write_and_preserves_failed_getter(self):
        modules=(self.modules[0],self.modules[1],self.writing,self.modules[3])
        p,block=self.view(modules)
        before=self.wire.call('eth_getStorageAt',[self.writing,'0x0','latest'])
        first=len(self.wire.calls)
        with request_scope(Budget(seconds=25,calls=1024,posts=2048)),cache.scope(p):
            batch.prefetch_accounts(p,block,(11,),(ETH,ZZZ),CURRENCIES)
            with self.assertRaisesRegex(RpcError,'batch getter failed'):
                p._uint('royalties','weightOf(uint256)',11,block=block)
            self.assertEqual(p._uint('vault','sharesOf(uint256)',11,block=block),110)
        self.assertEqual(len(self.wire.calls[first:]),1)
        self.assertEqual(self.wire.call('eth_getStorageAt',[self.writing,'0x0','latest']),before)
