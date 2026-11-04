"""Exact checkpoint/suffix differential and independent SQLite/RPC boundaries.

Actual fresh Projection/Earnings/History and builder execute. RPC transcripts
are synthetic; no network, old Anvil, installed database or key is used.
"""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from frontend_api.earnings_checkpoint import decode,encode,source_identity
from frontend_api.earnings_checkpoint_build import build,publish_candidate,BuildBudget
from frontend_api.earnings_replay import Replay,SCALE
from frontend_api.history import HistoryError,ZERO
from frontend_api.service import Projection
from indexer.monitor import Indexer
from tests_python import test_frontend_policy_v6 as profile_fixtures
from tests_python.test_earnings import event,consume,init,activate,ROLES,native_put
from tests_python.test_frontend_api import addr,words
from zzz_ops.abi import keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.rpc import RpcError
from zzz_ops.work_budget import Budget,request_scope


def block_hash(n):return '0x'+f'{100000+n:064x}'


class MarketRPC:
    def __init__(self,inner,nft):
        self.inner,self.nft=inner,nft;self.reorg=None;self.fail=False
        self.head=110
    def hash(self,n):
        h=self.inner.anchor if n==10 else self.inner.hash if n==99 else block_hash(n)
        if self.reorg==n:h='0x'+'c'*64
        return h
    def header(self,n):
        return dict(number=hex(n),hash=self.hash(n),parentHash=self.hash(n-1),
                    timestamp=hex(1000000+n*1200))
    def call(self,method,params=None):
        if self.fail:raise HistoryError('Synthetic unavailable RPC')
        if method=='eth_getBlockByNumber':return self.header(int(params[0],16))
        if method=='eth_blockNumber':return hex(self.head)
        if method=='eth_getCode' and params[0]==self.nft and params[1]['blockHash']==block_hash(9):return '0x'
        if method in ('eth_call','eth_getCode','eth_getStorageAt'):
            tag=params[-1]
            if not isinstance(tag,dict) or tag.get('requireCanonical') is not True or tag.get('blockHash') not in {self.hash(n) for n in range(10,self.head+1)}:
                raise HistoryError('Synthetic noncanonical hash')
            # The base ABI transcript describes the fixed state of this phase;
            # this wrapper authenticates the requested historical header first.
            params=[*params[:-1],dict(blockHash=self.inner.hash,requireCanonical=True)]
        return self.inner.call(method,params)


class CheckpointAPITests(unittest.TestCase):
    def setUp(self):
        f=profile_fixtures.FrontendPolicyV6Tests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.config=copy.deepcopy(f.config);self.inner=f.rpc
        self.c={r:v['address'] for r,v in self.config['contracts'].items()}
        self.config['custody_version']=5
        self.put(self.c['principal_exit'],'CUSTODY_VERSION()',values=(5,))
        self.rpc=MarketRPC(self.inner,self.c['nft'])
        self.i=self.inner.nft_id;self.j=int.from_bytes(keccak256(b'checkpoint dormant'),'big')
        self.path=Path(self.tmp.name)/'raw.sqlite'
        self.config['history']=dict(database=str(self.path),start_block=10,start_parent_hash=block_hash(9),
            contracts=sorted(ROLES.values()),max_events=1000)
        extra={}
        for role,n in (('fees',40),('membership',41)):
            code=bytes([0x60,n,0]);self.inner.codes[addr(n)]='0x'+code.hex()
            extra[role]=dict(address=addr(n),code_hash='0x'+keccak256(code).hex())
            self.put(addr(n),'access()',values=(self.c['access'],))
            label='ZZZFeeController' if role=='fees' else 'ZZZMembership'
            self.put(self.c['access'],'module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(addr(n),))
        self.config['earnings_history']=dict(schema=1,deployments=[dict(controller=self.c['access'],**extra)],prices=None)
        for sig,n in (('FEE_INTAKE_VERSION()',1),):self.put(addr(40),sig,values=(n,))
        self.put(addr(41),'totalEligible()',values=(1,))
        for sig,n in (('totalWeight()',1),('activationCount()',1),('SCALE()',SCALE)):
            self.put(addr(5),sig,values=(n,))
        self.put(addr(4),'SCALE()',values=(SCALE,))
        self.put(addr(2),'mintedCount()',values=(2,))
        for ordinal,i in enumerate((self.i,self.j),1):
            self.put(addr(2),'mintOrdinalOf(uint256)',(i,),(ordinal,))
            self.put(addr(2),'tokenAtOrdinal(uint256)',(ordinal,),(i,))
            self.put(addr(2),'ownerOf(uint256)',(i,),(addr(29+ordinal),))
            self.put(addr(3),'sharesOf(uint256)',(i,),(100 if i==self.i else 0,))
            self.put(addr(3),'nftBucket(uint256)',(i,),(5 if i==self.i else 0,))
            self.put(addr(5),'weightOf(uint256)',(i,),(1 if i==self.i else 0,))
        self.put(addr(3),'bucketTotalShares(uint256)',(5,),(100,))
        for a in (ZERO,addr(20)):
            self.put(addr(40),'dust(uint256,address)',(5,a),(0,))
        for a in (ZERO,addr(21)):
            for sig,n in (('eligibleCount(address)',1),('eligibleWeight(address)',1),('pending(address)',0)):
                self.put(addr(5),sig,(a,),(n,))
        self.set_earnings(80,10,100)
        cfg=dict(database=str(self.path),chain_id=31337,start_block=10,start_parent_hash=block_hash(9),
                 contracts=sorted(ROLES.values()),rpc_urls=['http://127.0.0.1:1'])
        self.index=Indexer(cfg,self.rpc);self.addCleanup(self.index.db.close)
        with self.index.db:
            for n in range(10,100):
                h=self.rpc.header(n)
                self.index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                    (31337,n,h['hash'],h['parentHash'],int(h['timestamp'],16)))
            self.index.db.execute('UPDATE cursors SET next_block=100')
        for ev in (
            event('royalties','AssetAdded',(ZERO,),(0,),10),
            event('royalties','AssetAdded',(addr(21),),(0,),10,1),
            event('nft','Transfer',(ZERO,addr(30),self.i),(),11),
            event('nft','Transfer',(ZERO,addr(31),self.j),(),12),
            event('membership','MembershipActivated',(self.i,),(),13),
            event('royalties','Activated',(self.i,),(1,),13,1),
            event('vault','SharesAdded',(self.i,5),(100,100),13,2),
            event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),20),
            event('fees','FeesAllocated',(5,addr(20)),(100,0),20,1),
            event('royalties','RoyaltiesReceived',(ZERO,),(100,1),21)):
            self.insert(ev)

    def put(self,target,signature,args=(),values=(0,)):
        native_put(self.inner,target,signature,args,values)

    def set_earnings(self,personal,collective,royalties):
        for a in (ZERO,addr(20)):
            self.put(addr(4),'ownerIndex(uint256,address)',(5,a),(personal*SCALE//100 if a==addr(20) else 0,))
            self.put(addr(4),'index(address)',(a,),(collective*SCALE if a==addr(20) else 0,))
            for i in (self.i,self.j):
                self.put(addr(4),'claimable(uint256,address)',(i,a),(personal+collective if i==self.i and a==addr(20) else 0,))
        for a in (ZERO,addr(21)):
            self.put(addr(5),'index(address)',(a,),(royalties*SCALE if a==ZERO else 0,))
            for i in (self.i,self.j):
                self.put(addr(5),'claimable(uint256,address)',(i,a),(royalties if i==self.i and a==ZERO else 0,))

    def insert(self,ev):
        ev=copy.deepcopy(ev);n=int(ev['blockNumber'],16);ev['blockHash']=self.rpc.header(n)['hash']
        with self.index.db:self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
            (31337,n,ev['blockHash'],ev['transactionHash'],int(ev['logIndex'],16),ev['address'],None,None,json.dumps(ev)))

    def projection(self,config=None):return Projection(config or self.config,self.rpc,clock=lambda:1118801)

    def candidate(self,number=21):
        return build(self.projection().earnings_history,number)

    def install(self,raw=None,name='checkpoint.json'):
        raw=self.candidate() if raw is None else raw
        path=Path(self.tmp.name)/name;digest=publish_candidate(path,raw)
        self.config['earnings_history']['checkpoint']=dict(path=str(path),sha256=digest)
        return path

    def suffix(self):
        self.insert(event('rewards','PoolRewardsCredited',(5,addr(20)),(160,20),40))
        self.insert(event('fees','FeesAllocated',(5,addr(20)),(200,0),40,1))
        self.insert(event('royalties','RoyaltiesReceived',(ZERO,),(200,1),41))
        self.set_earnings(240,30,300)

    def test_seeded_collection_nft_wallet_and_dormant_equal_full_replay(self):
        self.install();self.suffix()
        full=copy.deepcopy(self.config);del full['earnings_history']['checkpoint']
        for identifier in (None,str(self.i),str(self.j)):
            a=self.projection().earnings(identifier);b=self.projection(full).earnings(identifier)
            for key in ('all_time','last_24h','window','event_count'):
                self.assertEqual(a[key],b[key])
        result=self.projection().earnings(str(self.i))
        rows={r['asset']:r for r in result['all_time']};day={r['asset']:r for r in result['last_24h']}
        self.assertEqual(('240','30','300'),(rows[addr(20)]['lp_individual_raw'],rows[addr(20)]['lp_collective_raw'],rows[ZERO]['royalties_raw']))
        self.assertEqual(('160','20','200'),(day[addr(20)]['lp_individual_raw'],day[addr(20)]['lp_collective_raw'],day[ZERO]['royalties_raw']))
        wallet=self.projection().wallet_earnings(addr(30),99)
        self.assertEqual(result['all_time'],wallet['all_time'])
        self.assertEqual(3,result['provenance']['epochs'][0]['history']['suffix_logs_examined'])

    def test_lifetime_event_bound_is_replaced_by_same_bounded_suffix_not_truncation(self):
        self.install();self.suffix();self.config['history']['max_events']=3
        self.assertTrue(self.projection().earnings(str(self.i))['available'])
        full=copy.deepcopy(self.config);del full['earnings_history']['checkpoint']
        with self.assertRaisesRegex(HistoryError,'bound exceeded'):self.projection(full).earnings(str(self.i))
        self.config['history']['max_events']=2
        with self.assertRaisesRegex(HistoryError,'bound exceeded'):self.projection().earnings(str(self.i))

    def test_restart_and_repeated_reads_do_not_mutate_checkpoint_or_double_count(self):
        path=self.install();self.suffix();raw=path.read_bytes();p=self.projection()
        first=p.earnings(str(self.i))
        self.assertEqual(first,p.earnings(str(self.i)))
        self.assertEqual(first,self.projection().earnings(str(self.i)))
        self.assertEqual(raw,path.read_bytes())

    def test_hash_mismatch_missing_partial_duplicate_json_and_source_drift_reject(self):
        path=self.install();raw=path.read_bytes()
        for data in (raw[:-1]+b' ',b'{',b'{"schema":1,"schema":1}'):
            path.write_bytes(data)
            with self.assertRaises(HistoryError):self.projection()
        path.write_bytes(raw)
        with patch('frontend_api.earnings_checkpoint.source_identity',return_value={}):
            with self.assertRaisesRegex(HistoryError,'source changed'):self.projection()
        path.unlink()
        with self.assertRaises(HistoryError):self.projection()

    def test_checkpoint_anchor_reorg_and_unavailable_rpc_never_fall_back_to_zero(self):
        self.install();self.rpc.reorg=21
        with self.assertRaisesRegex(HistoryError,'anchor'):self.projection().earnings(str(self.i))
        self.rpc.reorg=None;self.rpc.fail=True
        with self.assertRaises(HistoryError):self.projection().earnings(str(self.i))

    def test_missing_suffix_block_and_duplicate_prefix_transaction_reject(self):
        self.install()
        ev=event('royalties','RoyaltiesReceived',(ZERO,),(1,1),40,1)
        ev['transactionHash']=event('royalties','RoyaltiesReceived',(ZERO,),(100,1),21)['transactionHash']
        self.insert(ev)
        with self.assertRaisesRegex(HistoryError,'prefix'):self.projection().earnings(str(self.i))
        with self.index.db:
            self.index.db.execute('DELETE FROM logs WHERE block_number=40')
            self.index.db.execute('DELETE FROM blocks WHERE number=42')
        with self.assertRaisesRegex(HistoryError,'gaps'):self.projection().earnings(str(self.i))

    def test_recent_checkpoint_cannot_erase_part_of_the_rolling_day(self):
        self.install(self.candidate(40))
        with self.assertRaisesRegex(HistoryError,'rolling day'):self.projection().earnings(str(self.i))

    def test_advance_checkpoint_carries_exact_history_and_rejects_overwrite(self):
        path=self.install();self.suffix();raw=build(self.projection().earnings_history,41)
        data=json.loads(raw);self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),data['previous_sha256'])
        state=decode(data['state'])
        self.assertEqual(240, state['accounts'][self.i]['lp_individual',addr(20)]//SCALE)
        with self.assertRaises(FileExistsError):publish_candidate(path,raw)
        self.assertNotEqual(raw,path.read_bytes())

    def test_reader_still_checks_live_rights_indexes_claims_and_runtime(self):
        self.install()
        self.put(addr(4),'ownerIndex(uint256,address)',(5,addr(20)),(999,))
        with self.assertRaisesRegex(HistoryError,'index'):self.projection().earnings(str(self.i))
        self.set_earnings(80,10,100)
        self.put(addr(4),'claimable(uint256,address)',(self.i,addr(20)),(91,))
        with self.assertRaisesRegex(HistoryError,'reconcile'):self.projection().earnings(str(self.i))
        self.set_earnings(80,10,100);self.inner.codes[addr(40)]='0x6001'
        with self.assertRaises(RpcError):self.projection().earnings(str(self.i))

    def test_concurrent_readers_keep_separate_replay_accounts(self):
        path=self.install();self.suffix();p=self.projection();before=path.read_bytes()
        with ThreadPoolExecutor(max_workers=4) as pool:
            values=list(pool.map(p.earnings,[str(self.i),str(self.j),str(self.i),str(self.j)]))
        self.assertEqual(values[0]['all_time'],values[2]['all_time'])
        self.assertEqual(values[1]['all_time'],values[3]['all_time'])
        self.assertTrue(all(int(v)==0 for r in values[1]['all_time'] for k,v in r.items() if k.endswith('_raw')))
        self.assertEqual(before,path.read_bytes())

    def test_wal_ingestion_during_read_keeps_one_sqlite_snapshot(self):
        self.install();original=sqlite3.connect;advanced=[]
        def connect(*args,**kwargs):
            connection=original(*args,**kwargs)
            def trace(sql):
                if 'SELECT COUNT(*)' in sql and not advanced:
                    advanced.append(True)
                    h=self.rpc.header(100)
                    with self.index.db:
                        self.index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                            (31337,100,h['hash'],h['parentHash'],int(h['timestamp'],16)))
                        self.index.db.execute('UPDATE cursors SET next_block=101')
            connection.set_trace_callback(trace)
            return connection
        with patch('frontend_api.history.sqlite3.connect',side_effect=connect):
            result=self.projection().earnings(str(self.i))
        self.assertTrue(advanced)
        self.assertEqual('80',next(r for r in result['all_time'] if r['asset']==addr(20))['lp_individual_raw'])

    def test_bad_reapproved_state_and_wrong_deployment_profile_are_rejected(self):
        raw=self.candidate();original=json.loads(raw)
        for n,mutate in enumerate((
            lambda v:v['shared']['supply'].__setitem__(5,101),
            lambda v:v['accounts'][self.i].__setitem__(('lp_individual',addr(20)),True),
            lambda v:v['shared']['weights'].__setitem__(self.i,4),
            lambda v:v['history']['owners'].__setitem__(self.i,ZERO),
            lambda v:v['emitters'].__setitem__('fees',addr(77)),
            lambda v:v['royalty_assets'].remove(ZERO),
        )):
            data=copy.deepcopy(original);state=decode(data['state']);mutate(state);data['state']=encode(state)
            self.install(json.dumps(data).encode(),name='bad-'+str(n))
            with self.assertRaises(HistoryError):self.projection()
        self.config['earnings_history'].pop('checkpoint')
        self.install(raw,name='valid')
        bad=copy.deepcopy(self.config);bad['custody_version']=4
        with self.assertRaises(HistoryError):self.projection(bad)
        bad=copy.deepcopy(self.config);bad['assets'][1]['symbol']='OTHER'
        with self.assertRaises(HistoryError):self.projection(bad)

    def test_builder_refuses_false_nft_rights_and_pending_fee_pairs(self):
        with self.assertRaises(WorkLimit):
            build(self.projection().earnings_history,21,budget=BuildBudget(calls=1))
        with patch('frontend_api.earnings_checkpoint_build.decode',side_effect=HistoryError('reader bound')):
            with self.assertRaisesRegex(HistoryError,'reader bound'):self.candidate()
        with patch('frontend_api.earnings_checkpoint_build.source_identity',side_effect=[source_identity(),{}]):
            with self.assertRaisesRegex(HistoryError,'source changed'):self.candidate()
        self.put(addr(3),'sharesOf(uint256)',(self.i,),(101,))
        with self.assertRaisesRegex(HistoryError,'rights'):self.candidate()
        self.put(addr(3),'sharesOf(uint256)',(self.i,),(100,))
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=20',(addr(40),))
        with self.assertRaisesRegex(HistoryError,'epoch|fee allocation'):self.candidate()

    def test_hard_link_failure_cannot_publish_or_replace_a_partial_candidate(self):
        raw=self.candidate();target=Path(self.tmp.name)/'failed.json'
        with patch('frontend_api.earnings_checkpoint_build.os.link',side_effect=OSError('unsupported')):
            with self.assertRaises(OSError):publish_candidate(target,raw)
        self.assertFalse(target.exists())
        self.assertFalse(list(target.parent.glob('.failed.json.*.partial')))

    def activate_second_views(self):
        self.put(addr(41),'totalEligible()',values=(2,))
        for sig,n in (('totalWeight()',4),('activationCount()',2)):
            self.put(addr(5),sig,values=(n,))
        self.put(addr(3),'bucketTotalShares(uint256)',(5,),(200,))
        self.put(addr(3),'sharesOf(uint256)',(self.j,),(100,))
        self.put(addr(3),'nftBucket(uint256)',(self.j,),(5,))
        self.put(addr(5),'weightOf(uint256)',(self.j,),(3,))
        for a in (ZERO,addr(21)):
            self.put(addr(5),'eligibleCount(address)',(a,),(2,))
            self.put(addr(5),'eligibleWeight(address)',(a,),(4,))

    def test_membership_dust_settles_to_incumbent_before_second_activation(self):
        self.install()
        for ev in (
            event('fees','FeesAllocated',(5,addr(20)),(0,19),39),
            event('rewards','PoolRewardsCredited',(5,addr(20)),(19,0),40),
            event('fees','MembershipDustSettled',(5,addr(20)),(19,),40,1),
            event('membership','MembershipActivated',(self.j,),(),40,2),
            event('royalties','Activated',(self.j,),(3,),40,3),
            event('vault','SharesAdded',(self.j,5),(100,100),40,4)):
            self.insert(ev)
        self.set_earnings(99,10,100);self.activate_second_views()
        i=self.projection().earnings(str(self.i));j=self.projection().earnings(str(self.j))
        self.assertEqual('99',next(r for r in i['all_time'] if r['asset']==addr(20))['lp_individual_raw'])
        self.assertTrue(all(int(v)==0 for r in j['all_time'] for k,v in r.items() if k.endswith('_raw')))
        collection=self.projection().earnings()
        row=next(r for r in collection['all_time'] if r['asset']==addr(20))
        self.assertEqual(['119','99','10','5','5'],[row[k+'_raw'] for k in
            ('lp_processed','lp_owner_allocated','lp_collective_allocated','lp_compounding_allocated','lp_buyback_allocated')])

    def test_royalty_recovery_after_checkpoint_preserves_prior_eligible_cohort(self):
        self.install()
        for ev in (
            event('membership','MembershipActivated',(self.j,),(),40),
            event('royalties','RoyaltyAssetDeferred',(self.j,addr(21)),(),40,1),
            event('royalties','Activated',(self.j,),(3,),40,2),
            event('vault','SharesAdded',(self.j,5),(100,100),40,3),
            event('royalties','RoyaltiesReceived',(addr(21),),(100,1),41),
            event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(2,2),41,1),
            event('royalties','RoyaltiesReceived',(addr(21),),(100,1),42)):
            self.insert(ev)
        self.activate_second_views()
        self.put(addr(5),'index(address)',(addr(21),),(125*SCALE,))
        self.put(addr(5),'claimable(uint256,address)',(self.i,addr(21)),(125,))
        self.put(addr(5),'claimable(uint256,address)',(self.j,addr(21)),(75,))
        for identifier,expected in ((self.i,'125'),(self.j,'75')):
            result=self.projection().earnings(str(identifier))
            self.assertEqual(expected,next(r for r in result['all_time'] if r['asset']==addr(21))['royalties_raw'])

    def test_checkpoint_age_boundary_includes_complete_rolling_day(self):
        raw=self.candidate(27)  # timestamp exactly target99 -86400.
        self.install(raw)
        self.assertTrue(self.projection().earnings(str(self.i))['available'])
        # One more block would hide part of the requested day and must fail.
        del self.config['earnings_history']['checkpoint']
        self.install(self.candidate(28),name='too-new')
        with self.assertRaisesRegex(HistoryError,'rolling day'):self.projection().earnings(str(self.i))

    def test_fraction_crossing_after_checkpoint_is_attributed_to_the_actual_day(self):
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE block_number=20')
        for ev in (event('membership','MembershipActivated',(self.j,),(),14),
                   event('royalties','Activated',(self.j,),(3,),14,1),
                   event('vault','SharesAdded',(self.j,5),(200,100),14,2),
                   event('rewards','PoolRewardsCredited',(5,addr(20)),(16,2),20),
                   event('fees','FeesAllocated',(5,addr(20)),(20,0),20,1)):
            self.insert(ev)
        self.activate_second_views()
        self.put(addr(3),'sharesOf(uint256)',(self.j,),(200,))
        self.put(addr(3),'bucketTotalShares(uint256)',(5,),(300,))
        delta=16*SCALE//300
        def state(n):
            self.put(addr(4),'ownerIndex(uint256,address)',(5,addr(20)),(n*delta,))
            self.put(addr(4),'index(address)',(addr(20),),(n*SCALE,))
            self.put(addr(5),'index(address)',(ZERO,),(25*SCALE,))
            for i,shares,royalty in ((self.i,100,25),(self.j,200,75)):
                self.put(addr(4),'claimable(uint256,address)',(i,addr(20)),(n*delta*shares//SCALE+n,))
                self.put(addr(5),'claimable(uint256,address)',(i,ZERO),(royalty,))
        state(1);self.install()
        for number in (40,41,42):
            self.insert(event('rewards','PoolRewardsCredited',(5,addr(20)),(16,2),number))
            self.insert(event('fees','FeesAllocated',(5,addr(20)),(20,0),number,1))
        state(4)
        result=self.projection().earnings(str(self.i))
        all_time=next(r for r in result['all_time'] if r['asset']==addr(20))
        day=next(r for r in result['last_24h'] if r['asset']==addr(20))
        self.assertEqual(str(4*delta*100//SCALE),all_time['lp_individual_raw'])
        self.assertEqual('16',day['lp_individual_raw'])  # Three new5.x credits plus the carried fraction.

    def test_currency_descriptor_append_does_not_reinterpret_existing_checkpoint(self):
        self.install()
        self.config['assets'].append(dict(address=addr(60),symbol='ROY',decimals=18,code_hash='0x'+keccak256(b'roy').hex()))
        self.inner.codes[addr(60)]='0x'+b'roy'.hex()
        self.put(addr(60),'decimals()',values=(18,))
        self.put(addr(5),'assetCount()',values=(3,))
        self.put(addr(5),'assets(uint256)',(2,),(addr(60),))
        for sig,n in (('index(address)',0),('pending(address)',0),('eligibleCount(address)',1),('eligibleWeight(address)',1)):
            self.put(addr(5),sig,(addr(60),),(n,))
        for i in (self.i,self.j):self.put(addr(5),'claimable(uint256,address)',(i,addr(60)),(0,))
        self.insert(event('royalties','AssetAdded',(addr(60),),(99,),40))
        result=self.projection().earnings(str(self.i))
        row=next(r for r in result['all_time'] if r['asset']==addr(60))
        self.assertEqual('0',row['royalties_raw'])

    def test_transfer_and_claim_suffix_preserve_earned_amounts(self):
        self.install()
        self.insert(event('nft','Transfer',(addr(30),addr(32),self.i),(),40))
        self.put(addr(2),'ownerOf(uint256)',(self.i,),(addr(32),))
        self.put(addr(2),'balanceOf(address)',(addr(30),),(0,))
        self.put(addr(2),'balanceOf(address)',(addr(32),),(1,))
        # Claimed is intentionally not an income event in Replay.
        ev=dict(address=addr(4),blockNumber=hex(41),blockHash=self.rpc.header(41)['hash'],transactionHash=block_hash(999),
            logIndex='0x0',topics=['0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex(),words(self.i),words(addr(20)),words(addr(32))],data=words(40),removed=False)
        self.insert(ev);self.put(addr(4),'claimable(uint256,address)',(self.i,addr(20)),(50,))
        result=self.projection().earnings(str(self.i))
        self.assertEqual(addr(32),result['owner'])
        self.assertEqual('80',next(r for r in result['all_time'] if r['asset']==addr(20))['lp_individual_raw'])
        self.assertEqual(result['all_time'],self.projection().wallet_earnings(addr(32),99)['all_time'])


class CheckpointEncodingTests(unittest.TestCase):
    def test_all_nft_tracking_is_bounded_at1000_with_independent_fractions(self):
        m=Replay(100000,track_all=True);init(m,identifiers=tuple(range(1,1001)))
        for i in range(1,1001):activate(m,i,i,1+(i%3),block=2000+i)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(123456,789),4000),99999)
        m.finish()
        self.assertEqual(1000,len(m.accounts))
        delta=123456*SCALE//sum(range(1,1001))
        self.assertEqual(delta*731,m.accounts[731]['lp_individual',addr(20)])
        self.assertEqual(delta*731//SCALE,m.account_totals[731]['lp_individual',addr(20)])
        with self.assertRaisesRegex(HistoryError,'mint'):
            consume(m,event('nft','Transfer',(ZERO,addr(30),1001),(),4001),100000)

    def test_fraction_checkpoint_roundtrip_tracks_all_without_raising_wallet_selection_cap(self):
        m=Replay(100000,track_all=True);init(m);activate(m,11,1);activate(m,22,2,3,14)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(1,1),20),1000)
        self.assertEqual(0,m.account_totals[11]['lp_individual',addr(20)])
        self.assertGreater(m.accounts[11]['lp_individual',addr(20)],0)
        self.assertEqual(dict(m.accounts[11]),decode(encode(dict(m.accounts[11]))))
        with self.assertRaises(HistoryError):Replay(1000,selected=tuple(range(1,18)))

    def test_strict_tagged_decoder_rejects_ambiguous_malformed_and_oversized_data(self):
        for value in (1,1.5,['object',[]],['int','01'],['int',str(1<<512)],['map',[[1,2]]],
                      ['set',['x','x']],['map',[['x',None],['x',None]]]):
            with self.subTest(value=str(value)[:80]):
                with self.assertRaises(HistoryError):decode(value)
        with self.assertRaises(HistoryError):decode(['list',['a','b']],limit=1)

    def test_offline_budgets_are_bounded_and_never_replace_a_stricter_outer_scope(self):
        for args in ((0,1,1),(3601,1,1),(60,65537,1),(60,1,False)):
            with self.assertRaises(ValueError):BuildBudget(*args)
        with request_scope(Budget(calls=1)) as outer:
            with request_scope(BuildBudget(calls=10)) as inner:self.assertIs(inner,outer)


if __name__=='__main__':unittest.main()
