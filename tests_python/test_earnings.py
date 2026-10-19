"""Known economic examples and byte-level SQLite/RPC integration, no network."""
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from frontend_api.earnings_replay import Replay, SPECS, SCALE
from frontend_api.earnings_prices import Prices, value_report
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection, UnknownNFT
from frontend_api.server import ReadServer, handler
from indexer.monitor import Indexer
from tests_python.test_frontend_api import addr, words, configuration
from tests_python.test_frontend_history import HistoryRPC, h
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, request_scope

ROLES={'nft':addr(2),'vault':addr(3),'rewards':addr(4),'royalties':addr(5),'handoff':addr(7),
       'fees':addr(40),'membership':addr(41)}

def event(role,name,indexed=(),data=(),block=20,index=0):
    sig=next(s for r,s in SPECS if r==role and s.startswith(name+'('))
    return {'address':ROLES[role],'blockNumber':hex(block),'blockHash':h(block),
        'transactionHash':h(1000+block),'logIndex':hex(index),'removed':False,
        'topics':['0x'+keccak256(sig.encode()).hex(),*[words(x) for x in indexed]],'data':words(*data)}

def consume(model,ev,timestamp=None):
    model(ev['address'],ev['topics'],ev['data'],int(ev['blockNumber'],16),ev['blockHash'],
          timestamp if timestamp is not None else 891+int(ev['blockNumber'],16),
          ev['transactionHash'],int(ev['logIndex'],16))

def init(model,identifiers=(11,22)):
    model.begin(ROLES,[addr(20),addr(21)],[ZERO,addr(21)])
    events=[event('royalties','AssetAdded',(ZERO,),(999,),10),
            event('royalties','AssetAdded',(addr(21),),(100,),10,1)]
    events += [event('nft','Transfer',(ZERO,addr(30),identifier),(),11+n) for n,identifier in enumerate(identifiers)]
    for e in events:consume(model,e)

def activate(model,identifier,shares,weight=1,block=13,deferred=False):
    ev=[event('membership','MembershipActivated',(identifier,),(),block)]
    if deferred:ev += [event('royalties','RoyaltyAssetDeferred',(identifier,addr(21)),(),block,1)]
    ev += [event('royalties','Activated',(identifier,),(weight,),block,2),
           event('vault','SharesAdded',(identifier,5),(shares,100*10**18),block,3)]
    for e in ev:consume(model,e)


class EarningsReplayTests(unittest.TestCase):
    def model(self,target=11):
        m=Replay(1000,target);init(m);activate(m,11,100);return m

    def test_individual_collective_royalties_and_topup_have_independent_weights(self):
        m=self.model()
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),20))
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(100,1),20,1))
        consume(m,event('vault','SharesAdded',(11,5),(100,100),22))
        activate(m,22,200,3,25)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),30))
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(100,1),30,1))
        m.finish()
        self.assertEqual(m.totals['lp_individual',addr(20)],120)
        self.assertEqual(m.totals['lp_collective',addr(20)],15)
        self.assertEqual(m.totals['royalties',ZERO],125)

    def test_prior_fees_exclude_new_entrant_and_transfers_do_not_reset_earnings(self):
        m=self.model(22)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),20))
        activate(m,22,100,3,25)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),30))
        consume(m,event('nft','Transfer',(addr(30),addr(31),22),(),31))
        self.assertEqual(m.totals['lp_individual',addr(20)],40)
        self.assertEqual(m.totals['lp_collective',addr(20)],5)

    def test_window_boundary_and_fraction_carry_are_exact(self):
        m=Replay(100000,11);init(m);activate(m,11,1);activate(m,22,2,1,14)
        # The earlier 1/3 raw-unit allocation and the later 2/3 both round down
        # in the global index. A third credit crosses the first whole raw unit.
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(1,0),20),13600)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(2,0),21),13601)
        self.assertEqual(m.totals['lp_individual',addr(20)],0)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(1,0),22),99999)
        self.assertEqual(m.totals['lp_individual',addr(20)],1)
        self.assertEqual(m.day['lp_individual',addr(20)],1)
        self.assertEqual(m.day['lp_owner_allocated',addr(20)],3)

    def test_collection_gross_dust_and_allocations_do_not_double_count(self):
        m=self.model(None)
        consume(m,event('fees','FeesAllocated',(5,addr(20)),(80,19),20))
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(64,8),20,1))
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(19,0),21))
        consume(m,event('fees','MembershipDustSettled',(5,addr(20)),(19,),21,1))
        consume(m,event('fees','FeesAllocated',(5,addr(20)),(20,1),22))
        self.assertEqual(m.totals['lp_processed',addr(20)],120)
        self.assertEqual(m.totals['lp_owner_allocated',addr(20)],83)
        self.assertEqual(m.totals['lp_compounding_allocated',addr(20)],5)
        self.assertEqual(m.totals['lp_buyback_allocated',addr(20)],5)

    def test_uneligible_receipts_and_admission_prefunds_are_not_nft_earnings(self):
        m=Replay(1000,11);init(m)
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(77,0),12,2))
        activate(m,11,100)
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(23,1),20))
        self.assertEqual(m.totals['royalties_received',ZERO],100)
        self.assertEqual(m.totals['royalties_quarantined',ZERO],77)
        self.assertEqual(m.totals['royalties',ZERO],23)

    def test_recovery_assigns_old_receipts_before_new_members_join(self):
        m=self.model(22);activate(m,22,100,3,14,True)
        consume(m,event('royalties','RoyaltiesReceived',(addr(21),),(100,1),20))
        consume(m,event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(2,2),20,1))
        consume(m,event('royalties','RoyaltiesReceived',(addr(21),),(100,1),21))
        self.assertEqual(m.totals['royalties',addr(21)],75)
        m.finish()

    def test_canonical_recovery_reverse_event_order_still_protects_earlier_cohort(self):
        m=self.model(22);activate(m,22,100,3,14,True)
        consume(m,event('handoff','Frozen',(h(1),addr(101)),(),19))
        consume(m,event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(2,2),20))
        consume(m,event('royalties','RoyaltiesReceived',(addr(21),),(100,1),20,1))
        self.assertEqual(m.totals['royalties',addr(21)],0)
        self.assertEqual(m.cohorts[addr(21)],{11,22})
        m.finish()

    def test_same_chain_epoch_carries_rights_and_skips_import_transfers(self):
        m=self.model();consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),20))
        consume(m,event('handoff','Frozen',(h(1),addr(101)),(),21))
        consume(m,event('handoff','Retired',(h(1),addr(101)),(h(2),),30,5));m.finish()
        m.begin(ROLES,[addr(20),addr(21)],[ZERO,addr(21)],(30,h(1030),h(1),h(2)))
        consume(m,event('nft','Transfer',(ZERO,addr(30),11),(),25))
        consume(m,event('handoff','Activated',(h(1),addr(1)),(h(2),),30,4))
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),31))
        m.finish();self.assertEqual(len(m.minted),2)
        self.assertEqual(m.totals['lp_individual',addr(20)],160)

    def test_invalid_recovery_activation_shares_and_rounding_fail_closed(self):
        bad=[event('royalties','Activated',(11,),(1,),20),
             event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(9,10),20),
             event('royalties','RoyaltiesReceived',(ZERO,),(99,0),20),
             event('fees','FeesAllocated',(5,addr(20)),(19,0),20),
             event('fees','MembershipDustSettled',(5,addr(20)),(1,),20),
             event('vault','SharesAdded',(11,6),(100,100),20)]
        for ev in bad:
            with self.subTest(ev=ev),self.assertRaises(HistoryError):consume(self.model(),ev)

    def test_unknown_emitter_claim_and_conversion_events_are_not_income(self):
        m=self.model();before=dict(m.totals)
        for sig in ('Claimed(uint256,address,address,uint256)','RoyaltyConverted(uint256,address,uint256,uint256)'):
            ev=event('royalties','RoyaltiesReceived',(ZERO,),(100,1));ev['topics'][0]='0x'+keccak256(sig.encode()).hex()
            consume(m,ev)
        ev=event('fees','FeesAllocated',(5,addr(20)),(100,0));ev['address']=addr(99);consume(m,ev)
        self.assertEqual(before,dict(m.totals))

    def test_work_budget_and_malformed_layout_stop_replay(self):
        m=self.model();ev=event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10))
        clock=[0];budget=Budget(clock=lambda:clock[0])
        with self.assertRaises(WorkLimit),request_scope(budget):
            clock[0]=26;consume(m,ev)
        ev['data']=words(1)
        with self.assertRaises(HistoryError):consume(m,ev)

    def test_thousand_nfts_share_one_pool_without_thousand_reward_reads(self):
        m=Replay(10000,999);init(m,())
        for i in range(1,1001):
            consume(m,event('nft','Transfer',(ZERO,addr(30),i),(),20))
            activate(m,i,1,1,20)
        consume(m,event('rewards','PoolRewardsCredited',(5,addr(20)),(1000,1000),21))
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(1000,1),21,1))
        m.finish()
        self.assertEqual(len(m.supply),1)
        self.assertEqual([m.totals['lp_individual',addr(20)],m.totals['lp_collective',addr(20)],m.totals['royalties',ZERO]],[1,1,1])


def native_put(rpc,target,sig,args=(),values=(0,)):
    if args and args[-1]==ZERO:
        data=calldata(sig,*args[:-1],addr(1))[:-64]+'0'*64
        rpc.responses[target,data]=words(*values)
    else:rpc.put(target,sig,args,values)


class EarningsAPITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.rpc=HistoryRPC();self.cfg=configuration()
        i,j=self.rpc.nft_id,self.rpc.other;self.rpc.logs=[]
        def add(ev):
            ev['blockHash']=self.rpc.header(int(ev['blockNumber'],16))['hash'];self.rpc.logs.append(ev)
        for ev in (event('royalties','AssetAdded',(ZERO,),(0,),10),event('royalties','AssetAdded',(addr(21),),(0,),10,1),
                   event('nft','Transfer',(ZERO,addr(30),i),(),11),event('nft','Transfer',(ZERO,addr(31),j),(),12),
                   event('membership','MembershipActivated',(i,),(),13),event('royalties','Activated',(i,),(1,),13,1),
                   event('vault','SharesAdded',(i,5),(100,100*10**18),13,2),
                   event('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),20),
                   event('fees','FeesAllocated',(5,addr(20)),(100,0),20,1),
                   event('royalties','RoyaltiesReceived',(ZERO,),(100,1),21)):add(ev)
        self.cfg['history']={'database':str(Path(self.temp.name)/'index.sqlite'),'start_block':10,'start_parent_hash':h(9),
                             'contracts':sorted(ROLES.values()),'max_events':1000}
        extra={}
        for role,n in (('fees',40),('membership',41)):
            code=bytes([0x60,n,0]);self.rpc.codes[addr(n)]='0x'+code.hex()
            extra[role]={'address':addr(n),'code_hash':'0x'+keccak256(code).hex()}
            self.rpc.put(addr(n),'access()',values=(addr(1),))
            label='ZZZFeeController' if role=='fees' else 'ZZZMembership'
            self.rpc.put(addr(1),'module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(addr(n),))
        self.cfg['earnings_history']={'schema':1,'deployments':[dict(controller=addr(1),**extra)],'prices':None}
        self.rpc.put(addr(41),'totalEligible()',values=(1,))
        for sig,value in (('totalWeight()',1),('activationCount()',1),('SCALE()',SCALE)):
            self.rpc.put(addr(5),sig,values=(value,))
        self.rpc.put(addr(4),'SCALE()',values=(SCALE,))
        self.rpc.put(addr(3),'bucketTotalShares(uint256)',(5,),(100,))
        self.rpc.put(addr(3),'sharesOf(uint256)',(i,),(100,))
        self.rpc.put(addr(5),'weightOf(uint256)',(i,),(1,))
        for asset in (addr(20),addr(21)):
            self.rpc.put(addr(4),'ownerIndex(uint256,address)',(5,asset),(80*SCALE//100 if asset==addr(20) else 0,))
            self.rpc.put(addr(4),'index(address)',(asset,),(10*SCALE if asset==addr(20) else 0,))
            self.rpc.put(addr(4),'claimable(uint256,address)',(i,asset),(90 if asset==addr(20) else 0,))
        for asset in (ZERO,addr(21)):
            for sig,value in (('index(address)',100*SCALE if asset==ZERO else 0),('eligibleWeight(address)',1),('eligibleCount(address)',1),('pending(address)',0)):
                native_put(self.rpc,addr(5),sig,(asset,),(value,))
            native_put(self.rpc,addr(5),'claimable(uint256,address)',(i,asset),(100 if asset==ZERO else 0,))
        config=dict(self.cfg['history'],chain_id=31337,rpc_urls=['http://127.0.0.1:8545'],confirmations=12,
                    block_chunk=200,max_reorg_depth=100,poll_seconds=1);config.pop('max_events')
        self.index=Indexer(config,self.rpc);self.index.step()

    def tearDown(self):self.index.close();self.temp.cleanup()
    def read(self,identifier=None):return Projection(self.cfg,self.rpc,clock=lambda:1000).earnings(identifier)

    def test_collection_and_nft_reconcile_exact_confirmed_history(self):
        c=self.read();n=self.read(str(self.rpc.nft_id))
        row=next(a for a in c['all_time'] if a['asset']==addr(20))
        self.assertEqual(row['lp_processed_raw'],'100');self.assertEqual(row['lp_compounding_allocated_raw'],'5')
        row=next(a for a in n['all_time'] if a['asset']==addr(20))
        self.assertEqual(row['lp_individual_raw'],'80');self.assertEqual(row['lp_collective_raw'],'10')
        self.assertIsNone(n['all_time_usd_at_current_price_18']['lp_individual'])
        self.assertFalse(n['claims_and_conversions_are_income'])

    def test_missing_profile_coverage_and_unminted_nft_are_explicit(self):
        cfg=copy.deepcopy(self.cfg);cfg['history']['contracts'].remove(addr(40))
        with self.assertRaises(ValueError):Projection(cfg,self.rpc)
        cfg=copy.deepcopy(self.cfg);del cfg['earnings_history']
        with self.assertRaises(HistoryError):Projection(cfg,self.rpc,clock=lambda:1000).earnings()
        with self.assertRaises(UnknownNFT):self.read('123')

    def test_index_or_share_drift_and_missing_logs_do_not_return_fabricated_income(self):
        self.rpc.put(addr(4),'index(address)',(addr(20),),(999,))
        with self.assertRaises(HistoryError):self.read()
        self.rpc.put(addr(4),'index(address)',(addr(20),),(10*SCALE,))
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=20',(addr(4),))
        with self.assertRaises(HistoryError):self.read()

    def test_actual_claim_and_conversion_reconcile_without_new_income(self):
        def log(sig,block,topics,data):
            ev=self.rpc.raw(block,0,addr(5),['0x'+keccak256(sig.encode()).hex(),*[words(x) for x in topics]],words(*data))
            with self.index.db:self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',(31337,block,ev['blockHash'],ev['transactionHash'],0,addr(5),None,None,json.dumps(ev)))
        # Existing native income 100: claim 30; earned history stays 100.
        log('Claimed(uint256,address,address,uint256)',30,(self.rpc.nft_id,ZERO,addr(30)),(30,))
        native_put(self.rpc,addr(5),'claimable(uint256,address)',(self.rpc.nft_id,ZERO),(70,))
        out=self.read(str(self.rpc.nft_id))
        self.assertEqual(next(a for a in out['all_time'] if a['asset']==ZERO)['royalties_raw'],'100')
        native_put(self.rpc,addr(5),'claimable(uint256,address)',(self.rpc.nft_id,ZERO),(71,))
        with self.assertRaises(HistoryError):self.read(str(self.rpc.nft_id))

    def test_pending_royalties_do_not_enter_processed_earnings(self):
        native_put(self.rpc,addr(5),'pending(address)',(ZERO,),(50,))
        native_put(self.rpc,addr(5),'claimable(uint256,address)',(self.rpc.nft_id,ZERO),(150,))
        out=self.read(str(self.rpc.nft_id))
        self.assertEqual(next(a for a in out['all_time'] if a['asset']==ZERO)['royalties_raw'],'100')

    def test_runtime_drift_and_history_gaps_fail_closed(self):
        self.rpc.codes[addr(40)]='0x6000'
        with self.assertRaises(RpcError):self.read()
        self.rpc.codes[addr(40)]='0x602800'
        with self.index.db:self.index.db.execute('DELETE FROM blocks WHERE number=15')
        with self.assertRaises(HistoryError):self.read()

    def test_read_only_http_endpoints_and_invalid_ids(self):
        p=Projection(self.cfg,self.rpc,clock=lambda:1000)
        server=ReadServer(('127.0.0.1',0),handler(p));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for path,status in (('/v1/earnings',200),(f'/v1/nfts/{self.rpc.nft_id}/earnings',200),('/v1/nfts/0/earnings',404),('/v1/nfts/'+str(2**256)+'/earnings',400)):
                c=http.client.HTTPConnection('127.0.0.1',server.server_port);c.request('GET',path)
                r=c.getresponse();r.read();self.assertEqual(r.status,status);c.close()
        finally:server.shutdown();server.server_close();thread.join()

    def price_config(self):
        oracle,feed=addr(50),addr(51)
        for a,code in ((oracle,b'oracle'),(feed,b'feed')):self.rpc.codes[a]='0x'+code.hex()
        self.rpc.put(oracle,'access()',values=(addr(1),))
        self.rpc.put(addr(1),'module(bytes32)',('0x'+keccak256(b'ZZZOracle').hex(),),(oracle,))
        self.rpc.put(oracle,'sequencerFeed()',values=(ZERO,))
        self.rpc.put(oracle,'feeds(address)',(addr(20),),(feed,60,8,18))
        self.rpc.put(oracle,'price(address)',(addr(20),),(2*10**18,))
        return {'oracle':{'address':oracle,'code_hash':'0x'+keccak256(b'oracle').hex()},'sequencer':None,'feeds':[
            {'asset':addr(20),'priced_token':addr(20),'token_code_hash':self.cfg['assets'][1]['code_hash'],
             'source':feed,'source_code_hash':'0x'+keccak256(b'feed').hex(),'max_age':60,'feed_decimals':8}]}

    def test_current_price_changes_usd_without_changing_earned_tokens(self):
        self.cfg['earnings_history']['prices']=self.price_config()
        before=self.read(str(self.rpc.nft_id))
        self.rpc.put(addr(50),'price(address)',(addr(20),),(3*10**18,))
        after=self.read(str(self.rpc.nft_id))
        self.assertEqual(before['all_time'][1]['lp_individual_raw'],after['all_time'][1]['lp_individual_raw'])
        self.assertEqual(before['all_time_usd_at_current_price_18']['lp_individual'],'160')
        self.assertEqual(after['all_time_usd_at_current_price_18']['lp_individual'],'240')
        self.assertIsNone(after['all_time_usd_at_current_price_18']['royalties'])

    def test_failed_or_changed_price_preserves_raw_history_and_does_not_swallow_budget(self):
        self.cfg['earnings_history']['prices']=self.price_config()
        self.rpc.put(addr(50),'feeds(address)',(addr(20),),(addr(51),61,8,18))
        result=self.read();self.assertIsNone(result['all_time_usd_at_current_price_18']['lp_processed'])
        self.assertEqual(result['all_time'][1]['lp_processed_raw'],'100')
        original=self.rpc.call
        def fail(method,args):
            if method=='eth_call' and args[0]['to']==addr(50):raise WorkLimit('rpc_budget')
            return original(method,args)
        with patch.object(self.rpc,'call',side_effect=fail),self.assertRaises(WorkLimit):self.read()

    def insert(self, ev):
        n=int(ev['blockNumber'],16);ev['blockHash']=self.rpc.header(n)['hash']
        with self.index.db:self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
            (31337,n,ev['blockHash'],ev['transactionHash'],int(ev['logIndex'],16),ev['address'],None,None,json.dumps(ev)))

    def test_conversion_and_later_native_claim_preserve_original_earned_currency(self):
        i=self.rpc.nft_id
        self.insert(event('royalties','RoyaltiesReceived',(addr(21),),(200,1),25))
        conversion=self.rpc.raw(26,0,addr(5),['0x'+keccak256(b'RoyaltyConverted(uint256,address,uint256,uint256)').hex(),words(i),words(addr(21))],words(200,50))
        claim=self.rpc.raw(27,0,addr(5),['0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex(),words(i),words(ZERO),words(addr(30))],words(140))
        self.insert(conversion);self.insert(claim)
        self.rpc.put(addr(5),'index(address)',(addr(21),),(200*SCALE,))
        native_put(self.rpc,addr(5),'claimable(uint256,address)',(i,ZERO),(10,))
        out=self.read(str(i));rows={r['asset']:r for r in out['all_time']}
        self.assertEqual(rows[ZERO]['royalties_raw'],'100')
        self.assertEqual(rows[addr(21)]['royalties_raw'],'200')
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE block_number=26')
        with self.assertRaises(HistoryError):self.read(str(i))

    def test_dormant_nft_has_zero_earned_income_without_sharing_old_receipts(self):
        i=self.rpc.other
        self.rpc.put(addr(2),'mintOrdinalOf(uint256)',(i,),(2,))
        self.rpc.put(addr(2),'tokenAtOrdinal(uint256)',(2,),(i,))
        for target,sig in ((3,'sharesOf(uint256)'),(3,'nftBucket(uint256)'),(5,'weightOf(uint256)')):
            self.rpc.put(addr(target),sig,(i,),(0,))
        for target,assets in ((4,[addr(20),addr(21)]),(5,[ZERO,addr(21)])):
            for asset in assets:native_put(self.rpc,addr(target),'claimable(uint256,address)',(i,asset),(0,))
        result=self.read(str(i))
        self.assertTrue(all(int(v)==0 for row in result['all_time'] for k,v in row.items() if k.endswith('_raw')))

    def test_final_snapshot_expiry_rejects_even_successful_replay(self):
        times=[1000,1000,1300]
        with self.assertRaises(RpcError):Projection(self.cfg,self.rpc,clock=lambda:times.pop(0) if times else 1300).earnings()

    def test_price_alias_and_module_policy_cannot_be_silently_changed(self):
        cfg=self.price_config();cfg['feeds'][0]['priced_token']=addr(21)
        self.cfg['earnings_history']['prices']=cfg
        with self.assertRaises(ValueError):Projection(self.cfg,self.rpc)
        self.cfg['earnings_history']['prices']=self.price_config()
        self.rpc.put(addr(50),'sequencerFeed()',values=(addr(52),))
        result=self.read()
        self.assertIsNone(result['all_time_usd_at_current_price_18']['lp_processed'])

    def test_collection_before_first_mint_is_zero_not_an_indexer_error(self):
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE block_number>10')
        for target,sig in ((2,'mintedCount()'),(41,'totalEligible()'),(5,'totalWeight()'),(5,'activationCount()')):
            self.rpc.put(addr(target),sig,values=(0,))
        for asset in (addr(20),addr(21)):self.rpc.put(addr(4),'index(address)',(asset,),(0,))
        for asset in (ZERO,addr(21)):
            for sig in ('index(address)','eligibleCount(address)','eligibleWeight(address)'):
                native_put(self.rpc,addr(5),sig,(asset,),(0,))
        out=self.read()
        self.assertTrue(all(int(v)==0 for row in out['all_time'] for k,v in row.items() if k.endswith('_raw')))

    def test_supervised_worker_dispatches_read_only_earnings(self):
        from frontend_api.worker import _run,WorkerClient
        output=Path(self.temp.name)/'worker-result.json'
        projection=Projection(self.cfg,self.rpc,clock=lambda:1000)
        with patch('frontend_api.worker.Projection',return_value=projection):
            _run(str(output),self.cfg,None,'earnings',str(self.rpc.nft_id))
        result=json.loads(output.read_bytes())
        self.assertEqual(result['ok']['token_id'],str(self.rpc.nft_id))
        client=WorkerClient(self.cfg)
        with patch.object(client,'_request',return_value={'verified':True}) as request:
            self.assertEqual(client.earnings(),{'verified':True});request.assert_called_once_with('earnings',None)


class EarningsLineageTests(unittest.TestCase):
    def setUp(self):
        from tests_python.test_frontend_lineage import LineageRPC
        self.temp=tempfile.TemporaryDirectory();self.rpc=LineageRPC(Path(self.temp.name),2)
        r=self.rpc;i=r.nft_id
        r.logs=[e for e in r.logs if e['topics'][0]=='0x'+keccak256(b'Transfer(address,address,uint256)').hex()]
        self.profiles=[]
        for n,c in enumerate(r.configs):
            roles={k:c['contracts'][k]['address'] for k in ('nft','vault','rewards','royalties','handoff')}
            roles.update(fees=addr(40+100*n),membership=addr(41+100*n))
            extra={}
            for role in ('fees','membership'):
                a=roles[role];code=bytes([0x61,40 if role=='fees' else 41,n]);r.codes[a]='0x'+code.hex();r.birth[a]=c['deployment_block']
                extra[role]={'address':a,'code_hash':'0x'+keccak256(code).hex()}
                r.put(a,'access()',c['contracts']['access']['address'])
                r.put(c['contracts']['access']['address'],'module(bytes32)',a,'0x'+keccak256(('ZZZFeeController' if role=='fees' else 'ZZZMembership').encode()).hex())
            self.profiles.append(dict(controller=c['contracts']['access']['address'],**extra))
            def add(role,name,topics=(),data=(),block=20,index=0):
                e=event(role,name,topics,data,block,index);e['address']=roles[role];r.logs.append(e)
            add('royalties','AssetAdded',(ZERO,),(0,),c['deployment_block'])
            add('royalties','AssetAdded',(addr(21),),(0,),c['deployment_block'],1)
            if not n:
                add('membership','MembershipActivated',(i,),(),12)
                add('royalties','Activated',(i,),(2,),12,1)
                add('vault','SharesAdded',(i,5),(100,100),12,2)
                add('handoff','Frozen',(h(3000),addr(101)),(),29,5)
            add('rewards','PoolRewardsCredited',(5,addr(20)),(80,10),15 if not n else 40)
            add('fees','FeesAllocated',(5,addr(20)),(100,0),15 if not n else 40,1)
            add('royalties','RoyaltiesReceived',(ZERO,),(100,1),16 if not n else 41)
            for role,sig,value in (('membership','totalEligible()',1),('royalties','totalWeight()',2),('royalties','activationCount()',1),('royalties','SCALE()',SCALE),('rewards','SCALE()',SCALE)):
                r.put(roles[role],sig,value)
            for sig,value in (('sharesOf(uint256)',100),('bucketTotalShares(uint256)',100)):
                r.put(roles['vault'],sig,value,i if sig.startswith('shares') else 5)
            for asset in (addr(20),addr(21)):
                r.put(roles['rewards'],'ownerIndex(uint256,address)',(n+1)*80*SCALE//100 if asset==addr(20) else 0,5,asset)
                r.put(roles['rewards'],'index(address)',(n+1)*10*SCALE if asset==addr(20) else 0,asset)
                r.put(roles['rewards'],'claimable(uint256,address)',(n+1)*90 if asset==addr(20) else 0,i,asset)
            for asset in (ZERO,addr(21)):
                for sig,value in (('index(address)',(n+1)*50*SCALE if asset==ZERO else 0),('eligibleWeight(address)',2),('eligibleCount(address)',1),('pending(address)',0)):
                    data=calldata(sig,addr(1))[:-64]+'0'*64 if asset==ZERO else calldata(sig,asset)
                    r.responses[roles['royalties'],data]=words(value)
                data=calldata('claimable(uint256,address)',i,addr(1))[:-64]+'0'*64 if asset==ZERO else calldata('claimable(uint256,address)',i,asset)
                r.responses[roles['royalties'],data]=words((n+1)*100 if asset==ZERO else 0)
            c['history']['contracts']=sorted(roles.values())
            c['history']['database']=str(Path(self.temp.name)/f'earnings-{n}.sqlite')
        for receipt in r.receipts.values():r.logs.extend(receipt['logs'])
        r.close();r.indexes=[]
        for n,c in enumerate(r.configs):
            r.head=41 if not n else 110
            cfg=dict(c['history'],chain_id=31337,rpc_urls=['http://127.0.0.1:8545'],confirmations=12,block_chunk=200,max_reorg_depth=100,poll_seconds=1);cfg.pop('max_events')
            index=Indexer(cfg,r);r.indexes.append(index);index.step()
        r.head=110;self.cfg=copy.deepcopy(r.configs[-1])
        self.cfg['predecessors']=[dict({k:r.configs[0][k] for k in ('deployment_block','deployment_block_hash','contracts','assets','history')},retirement_transaction_hash=h(2000))]
        self.cfg['earnings_history']={'schema':1,'deployments':self.profiles,'prices':None}

    def tearDown(self):self.rpc.close();self.temp.cleanup()

    def test_real_receipt_and_two_databases_preserve_both_epochs_without_import_income(self):
        for identifier in (None,str(self.rpc.nft_id)):
            result=Projection(self.cfg,self.rpc,clock=lambda:1000).earnings(identifier)
            row=next(a for a in result['all_time'] if a['asset']==addr(20))
            self.assertEqual(row['lp_processed_raw'] if identifier is None else row['lp_individual_raw'],'200' if identifier is None else '160')
            self.assertEqual(len(result['provenance']['epochs']),2)
        with self.rpc.indexes[1].db:self.rpc.indexes[1].db.execute('DELETE FROM logs WHERE address=? AND block_number=30',(addr(107),))
        with self.assertRaises(HistoryError):Projection(self.cfg,self.rpc,clock=lambda:1000).earnings()


if __name__=='__main__':unittest.main()
