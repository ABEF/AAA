"""LP settlement: native claims, immutable earned history and bounded automation."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from frontend_api.history import LP_CONVERTED, CLAIMED, ZERO, HistoryError
from frontend_api.service import Projection
from keeper.monitor import Keeper
from keeper.royalties import BATCH
from tests_python.test_frontend_api import addr, words
from tests_python import test_royalty_reporting as history_tests
from tests_python import test_earnings as earnings_tests
from tests_python.test_earnings import native_put
from tests_python import test_royalty_keeper as keeper_tests
from tests_python.test_royalty_keeper import PIN, HASH
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError

def native_inventory(rpc):
    rpc.put(addr(4),'assetCount()',values=(3,))
    for n,asset in enumerate((ZERO,addr(20),addr(21))): rpc.put(addr(4),'assets(uint256)',(n,),(asset,))
    native_put(rpc,addr(4),'claimable(uint256,address)',(rpc.nft_id,ZERO),(0,))

def insert(test,block,topic,data,owner=None):
    topics=[topic,words(test.rpc.nft_id),words(ZERO if owner else addr(20))]
    if owner:topics.append(words(owner))
    ev=test.rpc.raw(block,0,addr(4),topics,words(*data))
    with test.index.db:test.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
        (31337,block,ev['blockHash'],ev['transactionHash'],0,addr(4),None,None,json.dumps(ev)))

class LPHistoryTests(unittest.TestCase):
    setUp=history_tests.ConversionHistoryTests.setUp
    tearDown=history_tests.ConversionHistoryTests.tearDown
    def read(self):return Projection(self.cfg,self.rpc,clock=lambda:1000).nft(str(self.rpc.nft_id))
    def test_conversions_are_separate_from_royalty_conversion_and_actual_claims(self):
        native_inventory(self.rpc);before=self.read()
        insert(self,50,LP_CONVERTED,(80,10,8,1));insert(self,51,LP_CONVERTED,(16,2,1,1))
        result=self.read();report=result['lp_conversions']
        self.assertEqual(report['total_eth_credited_raw'],'11')
        self.assertEqual(report['assets'][0]['source_converted_raw'],'108')
        self.assertEqual(result['royalty_conversions']['total_eth_credited_raw'],'0')
        self.assertEqual(before['previously_claimed']['assets'],result['previously_claimed']['assets'])
        insert(self,52,CLAIMED,(11,),owner=addr(30));after=self.read()
        eth=next(a for a in after['previously_claimed']['assets'] if a['asset']==ZERO)
        self.assertEqual(eth['lp_raw'],'11');self.assertEqual(eth['royalties_raw'],'7')
    def test_missing_history_never_becomes_zero(self):
        native_inventory(self.rpc);del self.cfg['history'];report=self.read()['lp_conversions']
        self.assertFalse(report['available']);self.assertIsNone(report['total_eth_credited_raw'])
    def test_malformed_or_unbacked_component_history_rejected(self):
        native_inventory(self.rpc)
        for amounts in ((1,2),(0,10,1,1),(80,0,8,1),(0,0,1,0)):
            insert(self,50,LP_CONVERTED,amounts)
            with self.assertRaises(HistoryError):self.read()
            with self.index.db:self.index.db.execute('DELETE FROM logs WHERE block_number=50')
    def test_legacy_source_only_inventory_cannot_accept_native_conversion_event(self):
        insert(self,50,LP_CONVERTED,(80,10,8,1))
        with self.assertRaises(HistoryError):self.read()

class LPEarningsTests(unittest.TestCase):
    setUp=earnings_tests.EarningsAPITests.setUp
    tearDown=earnings_tests.EarningsAPITests.tearDown
    read=earnings_tests.EarningsAPITests.read
    def test_source_and_native_claims_reconcile_without_new_income(self):
        native_inventory(self.rpc);i=self.rpc.nft_id
        for sig,args in [('ownerIndex(uint256,address)',(5,ZERO)),('index(address)',(ZERO,))]:
            native_put(self.rpc,addr(4),sig,args,(0,))
        insert(self,30,LP_CONVERTED,(80,10,8,1))
        self.rpc.put(addr(4),'claimable(uint256,address)',(i,addr(20)),(0,))
        native_put(self.rpc,addr(4),'claimable(uint256,address)',(i,ZERO),(9,))
        before=self.read(str(i));row=next(a for a in before['all_time'] if a['asset']==addr(20))
        self.assertEqual((row['lp_individual_raw'],row['lp_collective_raw']),('80','10'))
        eth=next(a for a in before['all_time'] if a['asset']==ZERO)
        self.assertEqual(eth['lp_individual_raw'],'0');self.assertEqual(eth['royalties_raw'],'100')
        insert(self,31,CLAIMED,(9,),owner=addr(30));native_put(self.rpc,addr(4),'claimable(uint256,address)',(i,ZERO),(0,))
        after=self.read(str(i));self.assertEqual(before['all_time'],after['all_time'])
        native_put(self.rpc,addr(4),'claimable(uint256,address)',(i,ZERO),(1,))
        with self.assertRaises(HistoryError):self.read(str(i))

class LPLineageTests(unittest.TestCase):
    def test_two_replacements_preserve_lp_conversion_once_without_claiming_it(self):
        with tempfile.TemporaryDirectory() as temp:
            rpc=history_tests.LineageRPC(Path(temp))
            try:
                for i,block in enumerate((15,45,80)):
                    ledger=addr(4+100*i)
                    rpc.put(ledger,'assetCount()',3)
                    for n,asset in enumerate((ZERO,addr(20),addr(21))):rpc.put(ledger,'assets(uint256)',asset,n)
                    rpc.responses[ledger,history_tests.native_data('claimable(uint256,address)',rpc.nft_id,ZERO)]=words(0)
                    ev=rpc.raw(ledger,block,10,[LP_CONVERTED,words(rpc.nft_id),words(addr(20))],words(80*(i+1),10*(i+1),8*(i+1),i+1))
                    with rpc.indexes[i].db:rpc.indexes[i].db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                        (31337,block,ev['blockHash'],ev['transactionHash'],10,ledger,None,None,json.dumps(ev)))
                result=Projection(rpc.config,rpc,clock=lambda:1000).nft(str(rpc.nft_id))
                report=result['lp_conversions']
                self.assertEqual(report['total_eth_credited_raw'],'54')
                self.assertEqual(report['assets'][0]['source_converted_raw'],'540')
                self.assertEqual(report['assets'][0]['last_event']['ledger'],addr(204))
                eth=next(a for a in result['previously_claimed']['assets'] if a['asset']==ZERO)
                self.assertEqual(eth['lp_raw'],'0');self.assertEqual(eth['royalties_raw'],'120')
                del rpc.config['predecessors']
                missing=Projection(rpc.config,rpc,clock=lambda:1000).nft(str(rpc.nft_id))
                self.assertFalse(missing['lp_conversions']['available'])
            finally:rpc.close()

class LPKeeperTests(unittest.TestCase):
    def setUp(self):
        keeper_tests.RoyaltyKeeperTests.setUp(self)
        cfg=copy.deepcopy(self.cfg);cfg['lp_conversion']=cfg.pop('royalty_conversion')
        mapping={'rewards':'royalties','lp_converter':'royalty_converter','lp_nft':'royalty_nft','lp_wrapper':'royalty_wrapper'}
        for target,old in mapping.items():cfg['contracts'][target]=cfg['contracts'][old];cfg['code_hashes'][target]=PIN
        ledger=cfg['contracts']['rewards']
        self.rpc.values[ledger,calldata('access()')]=int(cfg['contracts']['access'],16)
        self.rpc.values[cfg['contracts']['access'],calldata('module(bytes32)','0x'+keccak256(b'ZZZRewards').hex())]=int(ledger,16)
        # LP balances do not depend on royalty weight. Include the third NFT.
        self.rpc.values[cfg['contracts']['oracle'],calldata('quote(address,address,uint256)',self.rpc.asset,cfg['contracts']['lp_wrapper'],300)]=30000
        self.cfg=cfg;self.k=Keeper(cfg,rpc=self.rpc)
    def test_pinned_lp_batch_uses_same_serial_sender_and_one_percent_floor(self):
        with patch.object(self.k,'submit',return_value=False) as submit:self.k.lp_rewards.scan_once()
        self.assertEqual(submit.call_args.args[:3],('rewards',BATCH,(self.rpc.asset,[1,2,3],self.rpc.route,29700,100180)))
        self.assertEqual(submit.call_args.kwargs,{'maximum_cost':297})
        calls=[p for m,p in self.rpc.calls if m=='eth_call'];self.assertTrue(all(p[1]=={'blockHash':HASH,'requireCanonical':True} for p in calls))
        self.assertFalse(any(p[0]['data'].startswith(calldata('weightOf(uint256)',1)[:10]) for p in calls))
    def test_preparation_and_canonical_locks_prevent_lp_submission(self):
        self.rpc.values[self.contracts['access'],calldata('preparationActive()')]=1
        self.assertFalse(self.k.submit('rewards',BATCH,(self.rpc.asset,[1],self.rpc.route,1,100100),'test'))
        self.assertFalse(any(m=='eth_estimateGas' for m,_ in self.rpc.calls))
    def test_failure_rotates_without_affecting_nonce_or_royalty_state(self):
        self.k.lp_rewards.routes.append(dict(self.k.lp_rewards.routes[0],asset=addr(101)))
        self.k.state['next_nonce']=7;self.rpc.fail=True
        with patch('keeper.monitor.log'):self.assertFalse(self.k._convert_rewards(self.k.lp_rewards))
        self.assertEqual(self.k.state['lp_conversion']['asset'],1);self.assertEqual(self.k.state['next_nonce'],7)
        self.assertNotIn('royalty_conversion',self.k.state)
    def test_disabled_binding_and_reorg_reject_without_signing(self):
        self.rpc.reorg=True
        with self.assertRaises(RpcError):self.k.lp_rewards.scan_once()
        self.rpc.reorg=False;self.rpc.values[self.cfg['contracts']['rewards'],calldata('converter()')]=1
        with self.assertRaises(RpcError):self.k.lp_rewards.scan_once()
    def test_small_lp_batch_waits_without_royalty_sync(self):
        self.k.lp_rewards.routes[0]['minimum_source_units']=1000
        with patch.object(self.k,'submit') as submit:self.k.lp_rewards.scan_once();submit.assert_not_called()
    def test_dry_run_does_not_sign(self):
        with patch('subprocess.run') as signer,patch('keeper.monitor.log'):
            self.assertFalse(self.k.lp_rewards.scan_once());signer.assert_not_called()
    def test_busy_conversion_streams_leave_maintenance_a_turn_and_pending_blocks_all(self):
        k=self.k;k.royalties.enabled=True
        k.config['buybacks']=[{'token':addr(100),'amount':1,'pool_id':'0x'+'1'*64}]
        order=[]
        def view(role,sig,*args):return 0 if sig=='paused()' else 1
        def convert(worker):order.append(worker.key);return True
        def submit(role,*args,**kw):order.append(role);return True
        with patch.object(k,'poll_pending',return_value=False) as pending,patch.object(k,'canonical_state',return_value=0),patch.object(k,'preparation_active',return_value=False),patch.object(k,'view',side_effect=view),patch.object(k,'save'),patch.object(k,'_head',return_value=(1,100000)),patch.object(k,'_bucket_batch',return_value=[]),patch.object(k,'_convert_rewards',side_effect=convert),patch.object(k,'submit',side_effect=submit):
            for _ in range(3):k.cycle()
            self.assertEqual(order,['lp_conversion','royalty_conversion','buyback'])
            pending.return_value=True;k.cycle()
            self.assertEqual(len(order),3);self.assertEqual(k.state['conversion_turn'],0)

if __name__=='__main__':unittest.main()
