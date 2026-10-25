import copy,tempfile,unittest
from unittest.mock import patch
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
    def seeded_copy(self,**overrides):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        chain=Chain();chain.transfer(2,B);chain.transfer(5,C)
        index=Indexer(dict(self.config,database=str(Path(directory.name)/'copy.sqlite'),**overrides),chain)
        self.addCleanup(index.close);index.step()
        return index,chain
    @staticmethod
    def database_snapshot(index):
        return '\n'.join(index.db.iterdump())
    def test_missing_header_never_authorizes_rollback_even_after_a_proved_tip_mismatch(self):
        for missing in (5,4):
            with self.subTest(missing=missing):
                index,chain=self.seeded_copy();before=self.database_snapshot(index)
                if missing==4:chain.fork(5)
                original=chain.call
                def call(method,params):
                    if method=='eth_getBlockByNumber' and params[0]==hex(missing):return None
                    return original(method,params)
                error=None
                with patch.object(chain,'call',side_effect=call):
                    try:index.reconcile()
                    except RpcError as exc:error=exc
                self.assertEqual(self.database_snapshot(index),before)
                self.assertIsNotNone(error)
                self.assertEqual(index.next_block,6)
    def test_malformed_or_misnumbered_header_preserves_database_and_cursor(self):
        changes=({'number':'0x4'},{'hash':'0x1'},{'hash':'0x'+'00'*32},
                 {'parentHash':'not-a-hash'},{'timestamp':'0x00'})
        for deeper in (False,True):
            for change in changes:
                with self.subTest(deeper=deeper,change=change):
                    index,chain=self.seeded_copy();before=self.database_snapshot(index)
                    if deeper:chain.fork(5)
                    number=4 if deeper else 5
                    wrong={**chain.blocks[number],**change}
                    if 'number' in change:wrong['number']=hex(number+1)
                    original=chain.call
                    def call(method,params):
                        if method=='eth_getBlockByNumber' and params[0]==hex(number):return copy.deepcopy(wrong)
                        return original(method,params)
                    error=None
                    with patch.object(chain,'call',side_effect=call):
                        try:index.reconcile()
                        except RpcError as exc:error=exc
                    self.assertEqual(self.database_snapshot(index),before)
                    self.assertIsNotNone(error)
                    self.assertEqual(index.next_block,6)
    def test_same_hash_inconsistent_metadata_does_not_authorize_rollback(self):
        for field,value in (('parentHash',h(999)),('timestamp','0x999')):
            with self.subTest(field=field):
                index,chain=self.seeded_copy();before=self.database_snapshot(index)
                chain.blocks[5][field]=value
                with self.assertRaisesRegex(RpcError,'same block hash'):index.reconcile()
                self.assertEqual(self.database_snapshot(index),before)
    def test_ancestor_must_remain_stable_until_rollback(self):
        index,chain=self.seeded_copy();before=self.database_snapshot(index);chain.fork(5)
        original=chain.call;reads=0
        def call(method,params):
            nonlocal reads
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]=='0x4':
                reads+=1
                if reads==2:result['hash']=h(4,2)
            return result
        with patch.object(chain,'call',side_effect=call),self.assertRaisesRegex(RpcError,'changed during reconciliation'):
            index.reconcile()
        self.assertEqual(reads,2);self.assertEqual(self.database_snapshot(index),before)
    def test_inconsistent_remote_ancestry_preserves_history(self):
        index,chain=self.seeded_copy();before=self.database_snapshot(index);chain.fork(5)
        chain.blocks[5]['parentHash']=h(999)
        with self.assertRaisesRegex(RpcError,'ancestry changed'):index.reconcile()
        self.assertEqual(self.database_snapshot(index),before)
    def test_full_bounded_reorg_requires_the_original_start_anchor(self):
        for anchored in (True,False):
            for changed_parent in (False,True):
                with self.subTest(anchored=anchored,changed_parent=changed_parent):
                    index,chain=self.seeded_copy(**({} if anchored else {'start_parent_hash':None}))
                    before=self.database_snapshot(index);chain.fork(1)
                    if changed_parent:chain.blocks[1]['parentHash']=h(999)
                    if anchored and not changed_parent:
                        self.assertEqual(index.reconcile(),5);self.assertEqual(index.next_block,1)
                        self.assertEqual(index.nft_owners(A),{})
                        self.assertEqual(index.step(),5)
                    else:
                        with self.assertRaisesRegex(RpcError,'No reviewed common ancestor'):index.reconcile()
                        self.assertEqual(self.database_snapshot(index),before)
    def test_reconciliation_read_cost_is_bounded_and_idle_path_unchanged(self):
        self.idx.step()
        with patch.object(self.chain,'call',wraps=self.chain.call) as observed:
            self.assertEqual(self.idx.reconcile(),0)
            self.assertEqual(observed.call_count,1)
        self.chain.fork(5)
        with patch.object(self.chain,'call',wraps=self.chain.call) as observed:
            self.assertEqual(self.idx.reconcile(),1)
            self.assertEqual(observed.call_count,3)
    def test_exact_configured_reorg_depth_still_recovers(self):
        self.idx.max_reorg=2;self.idx.step();self.chain.fork(4)
        self.assertEqual(self.idx.reconcile(),2)
        self.assertEqual(self.idx.next_block,4)
        self.assertEqual(self.idx.step(),2)
    def test_changed_genesis_is_not_treated_as_an_empty_history(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        chain=Chain();chain.blocks[0]={'number':'0x0','hash':h(0,2),'parentHash':h(0),'timestamp':'0x0'}
        chain.blocks[1]['parentHash']=chain.blocks[0]['hash']
        index=Indexer(dict(self.config,start_block=0,start_parent_hash=None,max_reorg_depth=6,
                           database=str(Path(directory.name)/'genesis.sqlite')),chain)
        self.addCleanup(index.close);index.step();before=self.database_snapshot(index)
        for number in range(9):
            chain.blocks[number]['hash']=h(number,3)
            chain.blocks[number]['parentHash']=chain.blocks[number-1]['hash'] if number else h(0)
        with self.assertRaisesRegex(RpcError,'No reviewed common ancestor'):index.reconcile()
        self.assertEqual(self.database_snapshot(index),before)
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
