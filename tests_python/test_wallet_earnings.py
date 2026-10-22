"""Focused current-holdings earnings: exact fractions, lineage and HTTP bounds."""
import copy
import http.client
import json
import threading
import unittest
from unittest.mock import patch

from tests_python import test_earnings as fixtures
from tests_python.test_earnings import event, consume, init, activate, addr, words, ZERO
from frontend_api.earnings_replay import Replay, NFT
from frontend_api.service import Projection
from frontend_api.history import HistoryError
from frontend_api.server import ReadServer, handler
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError, WorkLimit


class SelectionReplayTests(unittest.TestCase):
    def test_selected_totals_equal_individual_histories_without_pooling_fractions(self):
        group = Replay(100000, selected=(11, 22))
        singles = [Replay(100000, i) for i in (11, 22)]
        for model in [group, *singles]:
            init(model)
            activate(model, 11, 1)
            activate(model, 22, 2, 3, 14, True)
            for n, timestamp in enumerate((13600, 13601, 99999)):
                consume(model, event('rewards', 'PoolRewardsCredited', (5, addr(20)), (1, 1), 20+n), timestamp)
            consume(model, event('royalties', 'RoyaltiesReceived', (addr(21),), (9, 1), 23), 99999)
            consume(model, event('royalties', 'RoyaltyEligibilityRecovered', (addr(21),), (2, 2), 23, 1), 99999)
            consume(model, event('royalties', 'RoyaltiesReceived', (addr(21),), (7, 1), 24), 100000)
            consume(model, event('nft', 'Transfer', (addr(30), addr(31), 22), (), 25), 100000)
            model.finish()
        for metric in NFT:
            for asset in (addr(20), addr(21), ZERO):
                self.assertEqual(group.totals[metric, asset], sum(m.totals[metric, asset] for m in singles))
                self.assertEqual(group.day[metric, asset], sum(m.day[metric, asset] for m in singles))
        # 3 collective raw units split over two NFTs leaves one whole unit each,
        # not three by pooling their fractional entitlements.
        self.assertEqual(group.totals['lp_collective', addr(20)], 2)

    def test_selection_bound_and_duplicates_rejected(self):
        for selected in ((11, 11), tuple(range(1, 18)), (True,), (0,), (2**256,), [11]):
            with self.subTest(selected=selected), self.assertRaises(HistoryError):
                Replay(1000, selected=selected)


class WalletEarningsTests(unittest.TestCase):
    setUp = fixtures.EarningsAPITests.setUp
    tearDown = fixtures.EarningsAPITests.tearDown
    insert = fixtures.EarningsAPITests.insert
    price_config = fixtures.EarningsAPITests.price_config

    def read(self, owner=None, block=99, offset=0):
        return Projection(self.cfg, self.rpc, clock=lambda:1000).wallet_earnings(owner or addr(30), block, offset)

    def test_real_sqlite_replay_matches_single_nft_and_pins_inventory(self):
        out = self.read()
        single = Projection(self.cfg, self.rpc, clock=lambda:1000).earnings(str(self.rpc.nft_id))
        self.assertEqual(out['all_time'], single['all_time'])
        self.assertEqual(out['last_24h'], single['last_24h'])
        self.assertEqual(out['token_ids'], [str(self.rpc.nft_id)])
        self.assertEqual(out['scope'], 'wallet_chunk')
        self.assertIsNone(out['next_offset'])

    def test_transfer_moves_lifetime_history_to_current_holder(self):
        self.insert(event('nft', 'Transfer', (addr(30), addr(32), self.rpc.nft_id), (), 30))
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(32),))
        for owner, count in ((30, 0), (32, 1)):
            self.rpc.put(addr(2), 'balanceOf(address)', (addr(owner),), (count,))
        old = self.read(addr(30)); new = self.read(addr(32))
        self.assertEqual(old['count'], 0)
        self.assertTrue(all(int(v)==0 for row in old['all_time'] for k,v in row.items() if k.endswith('_raw')))
        self.assertEqual(next(r for r in new['all_time'] if r['asset']==addr(20))['lp_individual_raw'], '80')

    def test_claims_conversions_not_new_income_and_missing_conversion_rejected(self):
        i = self.rpc.nft_id
        self.insert(event('royalties','RoyaltiesReceived',(addr(21),),(200,1),25))
        self.insert(self.rpc.raw(26,0,addr(5),['0x'+keccak256(b'RoyaltyConverted(uint256,address,uint256,uint256)').hex(),words(i),words(addr(21))],words(200,50)))
        self.insert(self.rpc.raw(27,0,addr(5),['0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex(),words(i),words(ZERO),words(addr(30))],words(140)))
        self.rpc.put(addr(5),'index(address)',(addr(21),),(200*fixtures.SCALE,))
        fixtures.native_put(self.rpc,addr(5),'claimable(uint256,address)',(i,ZERO),(10,))
        out = self.read(); rows = {r['asset']:r for r in out['all_time']}
        self.assertEqual(rows[ZERO]['royalties_raw'],'100')
        self.assertEqual(rows[addr(21)]['royalties_raw'],'200')
        with self.index.db:self.index.db.execute('DELETE FROM logs WHERE block_number=26')
        with self.assertRaises(HistoryError):self.read()

    def test_incomplete_or_mismatched_inventory_never_becomes_zero(self):
        self.rpc.put(addr(2),'balanceOf(address)',(addr(30),),(2,))
        with self.assertRaises(HistoryError):self.read()
        self.rpc.put(addr(2),'balanceOf(address)',(addr(30),),(1,))
        self.rpc.put(addr(2),'ownerOf(uint256)',(self.rpc.nft_id,),(addr(32),))
        with self.assertRaises(HistoryError):self.read()

    def test_unconfirmed_stale_and_invalid_cursors_rejected(self):
        for block, offset in ((100,0),(9,0),(99,1),(99,16),(True,0),(99,1000)):
            with self.subTest(block=block,offset=offset), self.assertRaises((RpcError, ValueError)):
                self.read(block=block, offset=offset)
        with self.assertRaises(RpcError):
            Projection(self.cfg,self.rpc,clock=lambda:1300).wallet_earnings(addr(30),99)

    def test_current_prices_and_unpriced_nonzero_components_remain_separate(self):
        self.cfg['earnings_history']['prices']=self.price_config()
        out = self.read()
        self.assertEqual(out['all_time_usd_at_current_price_18']['lp_individual'],'160')
        self.assertIsNone(out['all_time_usd_at_current_price_18']['royalties'])

    def test_three_chunks_cover_all_holdings_without_replaying_per_nft(self):
        for n in range(32):
            i=100+n; ordinal=3+n
            self.insert(event('nft','Transfer',(ZERO,addr(30),i),(),12,10+n))
            for sig,args,value in (('ownerOf(uint256)',(i,),addr(30)),('mintOrdinalOf(uint256)',(i,),ordinal),('tokenAtOrdinal(uint256)',(ordinal,),i)):
                self.rpc.put(addr(2),sig,args,(value,))
            for target,sig in ((3,'sharesOf(uint256)'),(3,'nftBucket(uint256)'),(5,'weightOf(uint256)')):
                self.rpc.put(addr(target),sig,(i,),(0,))
            for target,assets in ((4,[addr(20),addr(21)]),(5,[ZERO,addr(21)])):
                for asset in assets:fixtures.native_put(self.rpc,addr(target),'claimable(uint256,address)',(i,asset),(0,))
        self.rpc.put(addr(2),'mintedCount()',values=(34,))
        self.rpc.put(addr(2),'balanceOf(address)',(addr(30),),(33,))
        parts=[self.read(offset=n) for n in (0,16,32)]
        self.assertEqual([len(p['token_ids']) for p in parts],[16,16,1])
        self.assertEqual(len({i for p in parts for i in p['token_ids']}),33)
        self.assertEqual(len({p['inventory_sha256'] for p in parts}),1)
        self.assertEqual(sum(int(next(r for r in p['all_time'] if r['asset']==addr(20))['lp_individual_raw']) for p in parts),80)

    def test_missing_profile_and_work_budget_fail_closed(self):
        cfg = copy.deepcopy(self.cfg); del cfg['earnings_history']
        with self.assertRaises(HistoryError):Projection(cfg,self.rpc).wallet_earnings(addr(30),99)
        with patch('frontend_api.wallet_earnings.checkpoint',side_effect=WorkLimit('deadline')), self.assertRaises(WorkLimit):
            self.read()

    def test_http_and_supervised_worker_dispatch(self):
        from frontend_api.worker import WorkerClient, _run
        from pathlib import Path
        p = Projection(self.cfg,self.rpc,clock=lambda:1000)
        server=ReadServer(('127.0.0.1',0),handler(p)); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for suffix,status in (('99/0',200),('99/1',400),('100/0',503),('99/1000',404)):
                c=http.client.HTTPConnection('127.0.0.1',server.server_port)
                c.request('GET',f'/v1/wallets/{addr(30)}/earnings/{suffix}')
                r=c.getresponse();r.read();self.assertEqual(r.status,status);c.close()
        finally:server.shutdown();server.server_close();thread.join()
        output=Path(self.temp.name)/'wallet-worker.json'
        with patch('frontend_api.worker.Projection',return_value=p):
            _run(str(output),self.cfg,None,'wallet_earnings',[addr(30),99,0])
        self.assertEqual(json.loads(output.read_text())['ok']['scope'],'wallet_chunk')
        with patch.object(WorkerClient,'_request',return_value={'ok':True}) as request:
            self.assertEqual(WorkerClient(self.cfg).wallet_earnings(addr(30),99),{'ok':True})
            request.assert_called_once_with('wallet_earnings',[addr(30),99,0])


class WalletLineageTests(unittest.TestCase):
    setUp = fixtures.EarningsLineageTests.setUp
    tearDown = fixtures.EarningsLineageTests.tearDown

    def test_two_epochs_survive_replacement_without_import_income(self):
        p=Projection(self.cfg,self.rpc,clock=lambda:1000)
        owner=p._addr('nft','ownerOf(uint256)',self.rpc.nft_id,block={'blockHash':fixtures.h(98),'requireCanonical':True})
        self.rpc.put(addr(102),'balanceOf(address)',1,owner)
        out=p.wallet_earnings(owner,98)
        self.assertEqual(next(r for r in out['all_time'] if r['asset']==addr(20))['lp_individual_raw'],'160')
        self.assertEqual(len(out['provenance']['epochs']),2)
        with self.rpc.indexes[1].db:self.rpc.indexes[1].db.execute('DELETE FROM logs WHERE address=? AND block_number=30',(addr(107),))
        with self.assertRaises(HistoryError):p.wallet_earnings(owner,98)


if __name__ == '__main__':unittest.main()
