import copy,tempfile,unittest
from pathlib import Path
from indexer.monitor import Indexer
from zzz_ops.abi import keccak256
from zzz_ops.rpc import RpcError
A='0x'+'11'*20;B='0x'+'22'*20;C='0x'+'33'*20
TRANSFER='0x'+keccak256(b'Transfer(address,address,uint256)').hex()
def h(n,salt=0):return '0x'+f'{n+salt*10000:064x}'
def word(n):return '0x'+f'{n:064x}'
class Chain:
    def __init__(self):
        self.blocks={i:{'number':hex(i),'hash':h(i),'parentHash':h(i-1),'timestamp':hex(1000+i)} for i in range(1,9)}
        self.head=6;self.logs=[];self.max_range=100;self.extra=None
    def transfer(self,n,owner,tid=7):
        self.logs.append({'address':A,'blockNumber':hex(n),'blockHash':self.blocks[n]['hash'],'transactionHash':h(100+n),
            'logIndex':'0x0','topics':[TRANSFER,word(0),word(int(owner,16)),word(tid)],'data':'0x','removed':False})
    def fork(self,start):
        for i in range(start,9):
            self.blocks[i]['hash']=h(i,1);self.blocks[i]['parentHash']=self.blocks[i-1]['hash'] if i>1 else h(0)
        self.logs=[x for x in self.logs if int(x['blockNumber'],16)<start]
    def call(self,method,params):
        if method=='eth_blockNumber':return hex(self.head)
        if method=='eth_getBlockByNumber':return copy.deepcopy(self.blocks.get(int(params[0],16)))
        if method=='eth_getLogs':
            lo,hi=int(params[0]['fromBlock'],16),int(params[0]['toBlock'],16)
            if hi-lo+1>self.max_range:raise RpcError('range')
            out=[copy.deepcopy(x) for x in self.logs if lo<=int(x['blockNumber'],16)<=hi]
            if self.extra:out.append(copy.deepcopy(self.extra))
            return out
        raise AssertionError(method)
class IndexerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.chain=Chain()
        self.config={'chain_id':1,'start_block':1,'start_parent_hash':h(0),'confirmations':2,'block_chunk':10,
                     'max_reorg_depth':5,'contracts':[A],'database':str(Path(self.tmp.name)/'index.sqlite')}
        self.idx=Indexer(self.config,self.chain);self.addCleanup(self.idx.close)
    def test_confirmed_only(self):
        self.chain.transfer(5,B);self.chain.transfer(6,C)
        self.assertEqual(self.idx.step(),5);self.assertEqual(self.idx.next_block,6)
        self.assertEqual(self.idx.nft_owners(A),{'7':B})
    def test_repeat_no_duplicates(self):
        self.chain.transfer(2,B);self.idx.step()
        self.assertEqual(self.idx.step(),0)
        self.assertEqual(self.idx.db.execute('select count(*) from logs').fetchone()[0],1)
    def test_resume_database(self):
        self.idx.step();other=Indexer(self.config,self.chain)
        try:self.assertEqual(other.next_block,6)
        finally:other.close()
    def test_changed_contracts_rejected(self):
        with self.assertRaises(ValueError):Indexer(dict(self.config,contracts=[B]),self.chain)
    def test_reorg_rolls_back_owner(self):
        self.chain.transfer(2,B);self.chain.transfer(5,C);self.idx.step()
        self.chain.fork(5);self.chain.transfer(5,A)
        self.assertEqual(self.idx.step(),1);self.assertEqual(self.idx.nft_owners(A),{'7':A})
        self.assertEqual(self.idx.db.execute('select count(*) from logs').fetchone()[0],2)
    def test_reorg_bound_fails_closed(self):
        self.idx.max_reorg=2;self.idx.step();self.chain.fork(3)
        with self.assertRaises(RpcError):self.idx.step()
        self.assertEqual(self.idx.next_block,6)
    def test_reduce_rpc_range(self):
        self.chain.max_range=2
        self.assertEqual(self.idx.step(),2);self.assertEqual(self.idx.next_block,3)
    def test_wrong_parent_no_commit(self):
        self.chain.blocks[3]['parentHash']=h(999)
        with self.assertRaises(RpcError):self.idx.step()
        self.assertEqual(self.idx.next_block,1)
        self.assertEqual(self.idx.db.execute('select count(*) from blocks').fetchone()[0],0)
    def test_wrong_log_block_no_commit(self):
        self.chain.transfer(2,B);self.chain.logs[0]['blockHash']=h(999)
        with self.assertRaises(RpcError):self.idx.step()
        self.assertEqual(self.idx.next_block,1)
    def test_removed_log_rejected(self):
        self.chain.transfer(2,B);self.chain.logs[0]['removed']=True
        with self.assertRaises(RpcError):self.idx.step()
    def test_unrequested_contract_rejected(self):
        self.chain.transfer(2,B);self.chain.logs[0]['address']=C
        with self.assertRaises(RpcError):self.idx.step()
    def test_duplicate_log_atomic_failure(self):
        self.chain.transfer(2,B);self.chain.logs.append(dict(self.chain.logs[0]))
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):self.idx.step()
        self.assertEqual(self.idx.next_block,1)
        self.assertEqual(self.idx.db.execute('select count(*) from blocks').fetchone()[0],0)
    def test_empty_blocks_preserved(self):
        self.idx.step();self.assertEqual(self.idx.db.execute('select count(*) from blocks').fetchone()[0],5)
    def test_burn_removes_current_owner(self):
        self.chain.transfer(2,B);self.chain.transfer(4,'0x'+'00'*20);self.idx.step()
        self.assertEqual(self.idx.nft_owners(A),{})
    def test_multiple_collections_do_not_mix(self):
        self.chain.transfer(2,B);self.idx.step();self.assertEqual(self.idx.nft_owners(C),{})
    def test_integer_configuration_rejects_floats_and_booleans(self):
        for field in ('chain_id','start_block','confirmations','block_chunk','max_reorg_depth','poll_seconds'):
            for value in (True,False,1.5,1.0,'1.5',None):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                    Indexer(dict(self.config,**{field:value}),self.chain)
    def test_poll_interval_must_be_positive(self):
        for value in (0,-1,'0'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                Indexer(dict(self.config,poll_seconds=value),self.chain)
    def test_decimal_string_configuration_remains_supported(self):
        config=dict(self.config,poll_seconds='3',block_chunk='2',confirmations='2')
        index=Indexer(config,self.chain)
        try:
            self.assertEqual(index.poll_seconds,3)
            self.assertEqual(index.step(),2)
        finally:index.close()
