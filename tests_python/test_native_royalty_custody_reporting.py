"""Native royalty custody is not LP custody; all RPC/logs here are local fixtures."""
import unittest
from unittest.mock import patch

from frontend_api.earnings_replay import Replay, SCALE
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection, ProjectionError
from tests_python import test_earnings as earnings_fixture
from tests_python.test_earnings import activate, consume, event, init, native_put
from tests_python.test_frontend_api import MockRPC, addr, configuration, words
from tests_python.test_frontend_history import h
from tests_python.test_royalty_reporting import native_data, profile
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError
from indexer.monitor import Indexer


def custody_event(name, asset=ZERO, identifier=None, amount=10**18, *, block=20, index=0):
    """Encode the production event independently of the replay's known-event table."""
    identifier = identifier or h(601)
    if name == 'RoyaltyCustodyExited':
        signature = 'RoyaltyCustodyExited(bytes32,address,address,uint256,bytes32)'
        indexed, data = (identifier, asset, addr(91)), (amount, h(602))
    else:
        signature = 'RoyaltyCustodyReturned(bytes32,address,uint256)'
        indexed, data = (identifier, asset), (amount,)
    result = event('royalties', 'AssetAdded', (asset,), (0,), block, index)
    result.update(topics=['0x'+keccak256(signature.encode()).hex(), *[words(x) for x in indexed]],
                  data=words(*data))
    return result


def native_activation(model, identifier=22, weight=3, block=21):
    # Mirrors successful Vault activation while ETH royalties remain externally held.
    for entry in (
        event('membership', 'MembershipActivated', (identifier,), (), block),
        event('royalties', 'RoyaltyAssetDeferred', (identifier, ZERO), (), block, 1),
        event('royalties', 'Activated', (identifier,), (weight,), block, 2),
        event('vault', 'SharesAdded', (identifier, 5), (100, 100*10**18), block, 3),
    ):
        consume(model, entry)


class NativeCustodyProjectionTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC(); self.cfg = profile(configuration(), self.rpc)
        self.identifier = self.rpc.nft_id
        self._native('eligibleCount(address)', (ZERO,), (2,))
        self._native('eligibleFor(uint256,address)', (self.identifier, ZERO), (0,))
        self._native('custodyNonce(address)', (ZERO,), (1,))
        self._native('eligibleWeight(address)', (ZERO,), (3,))
        self.rpc.put(addr(5), 'totalWeight()', values=(8,))
        self.rpc.put(addr(5), 'claimable(uint256,address)', (self.identifier, ZERO), (0,))

    def _native(self, signature, args, values):
        self.rpc.responses[addr(5), native_data(signature, *args)] = words(*values)

    def read(self):
        return Projection(self.cfg, self.rpc, clock=lambda: 1000).nft(str(self.identifier))

    def test_current_holdings_survive_native_custody_and_return_before_recovery(self):
        original = self.rpc.call
        claim = native_data('claimable(uint256,address)', self.identifier, ZERO)
        def in_custody(method, args):
            if method == 'eth_call' and args[0]['to'] == addr(5) and args[0]['data'] == claim:
                raise RpcError('CustodyInTransit')
            return original(method, args)
        with patch.object(self.rpc, 'call', side_effect=in_custody):
            held = self.read()
        native, stable = held['claimable']['royalties']
        self.assertTrue(held['position']['activated'])
        self.assertEqual(native['eligibility'], 'deferred')
        self.assertFalse(native['available']); self.assertIsNone(native['raw'])
        self.assertTrue(stable['available']); self.assertTrue(held['claimable']['lp'][0]['available'])
        # returnCustody restores funds without syncing: a historical positive
        # nonce and the old eligible prefix remain, even though custody has ended.
        restored = self.read()['claimable']['royalties'][0]
        self.assertEqual(restored['eligibility'], 'deferred'); self.assertEqual(restored['raw'], '0')
        self._native('eligibleCount(address)', (ZERO,), (5,))
        self._native('eligibleFor(uint256,address)', (self.identifier, ZERO), (1,))
        self.rpc.put(addr(5), 'claimable(uint256,address)', (self.identifier, ZERO), (30,))
        recovered = self.read()['claimable']['royalties'][0]
        self.assertEqual(recovered['eligibility'], 'eligible'); self.assertEqual(recovered['raw'], '30')

    def test_native_gap_requires_real_custody_history_and_consistent_weight_bounds(self):
        for signature, args, values in (
            ('custodyNonce(address)', (ZERO,), (0,)),
            ('eligibleWeight(address)', (ZERO,), (1,)),
            ('eligibleWeight(address)', (ZERO,), (7,)),
            ('eligibleWeight(address)', (ZERO,), (6,)),
            ('totalWeight()', (), (4,)),
            ('totalWeight()', (), (16,)),
            ('eligibleFor(uint256,address)', (self.identifier, ZERO), (1,)),
        ):
            with self.subTest(signature=signature, values=values):
                self.setUp()
                if args and args[-1] == ZERO: self._native(signature, args, values)
                else: self.rpc.put(addr(5), signature, args, values)
                with self.assertRaises(ProjectionError): self.read()

    def test_missing_legacy_custody_getter_is_not_assumed_to_be_an_outage(self):
        self._native('custodyNonce(address)', (ZERO,), ())
        with self.assertRaises(ProjectionError): self.read()

    def test_deferred_native_currency_cannot_report_retroactive_credit(self):
        self.rpc.put(addr(5), 'claimable(uint256,address)', (self.identifier, ZERO), (1,))
        with self.assertRaises(ProjectionError): self.read()


class NativeCustodyReplayTests(unittest.TestCase):
    def model(self):
        model = Replay(1000, selected=(11,22)); init(model); activate(model, 11, 100)
        consume(model, event('royalties','RoyaltiesReceived',(ZERO,),(10**18,1),19))
        consume(model, custody_event('RoyaltyCustodyExited'))
        return model

    def test_exact_return_and_recovery_preserve_earlier_receipts_without_new_income(self):
        model = self.model(); native_activation(model)
        # Plain receipts while away emit no sync event. Exact custody return is
        # not royalties; the following sync allocates only the extra0.5ETH.
        consume(model, custody_event('RoyaltyCustodyReturned', block=22))
        consume(model, event('royalties','RoyaltiesReceived',(ZERO,),(5*10**17,1),23))
        consume(model, event('royalties','RoyaltyEligibilityRecovered',(ZERO,),(2,2),23,1))
        consume(model, event('royalties','RoyaltiesReceived',(ZERO,),(4*10**18,1),24))
        model.finish()
        self.assertEqual(model.account_totals[11]['royalties',ZERO], 25*10**17)
        self.assertEqual(model.account_totals[22]['royalties',ZERO], 3*10**18)
        self.assertEqual(model.totals['royalties_received',ZERO], 55*10**17)
        self.assertEqual(model.cohorts[ZERO], {11,22})

    def test_restored_but_unsynced_history_keeps_newcomer_out_of_native_cohort(self):
        model = self.model(); native_activation(model)
        consume(model, custody_event('RoyaltyCustodyReturned', block=22)); model.finish()
        self.assertEqual(model.cohorts[ZERO], {11})
        self.assertEqual(model.account_totals[22]['royalties',ZERO], 0)
        self.assertEqual(model.totals['royalties_received',ZERO], 10**18)

    def test_native_deferral_without_authenticated_active_custody_still_rejected(self):
        model = Replay(1000,22); init(model); activate(model,11,100)
        with self.assertRaises(HistoryError): native_activation(model)
        model = self.model()
        consume(model,custody_event('RoyaltyCustodyReturned',block=21))
        with self.assertRaises(HistoryError): native_activation(model,block=22)

    def test_wrong_emitter_cannot_authorize_native_deferral(self):
        model = Replay(1000,22); init(model); activate(model,11,100)
        spoof = custody_event('RoyaltyCustodyExited'); spoof['address'] = addr(92)
        consume(model,spoof)
        with self.assertRaises(HistoryError): native_activation(model)

    def test_duplicate_exit_or_wrong_return_cannot_invent_restored_backing(self):
        for mutation in ('duplicate','wrong_id','wrong_amount'):
            with self.subTest(mutation=mutation):
                model = self.model()
                bad = (custody_event('RoyaltyCustodyExited',block=21) if mutation=='duplicate' else
                       custody_event('RoyaltyCustodyReturned',identifier=h(999) if mutation=='wrong_id' else None,
                                     amount=1 if mutation=='wrong_amount' else 10**18,block=21))
                with self.assertRaises(HistoryError): consume(model,bad)

    def test_external_custody_cannot_sync_income_or_recover_eligibility(self):
        for name, indexed, data in (
            ('RoyaltiesReceived',(ZERO,),(100,1)),
            ('RoyaltyEligibilityRecovered',(ZERO,),(2,2)),
        ):
            with self.subTest(name=name):
                model = self.model(); native_activation(model)
                with self.assertRaises(HistoryError): consume(model,event('royalties',name,indexed,data,22))

    def test_return_without_extra_income_recovers_without_counting_custody_twice(self):
        model = self.model(); native_activation(model)
        consume(model,custody_event('RoyaltyCustodyReturned',block=22))
        consume(model,event('royalties','RoyaltyEligibilityRecovered',(ZERO,),(2,2),23))
        model.finish()
        self.assertEqual(model.totals['royalties_received',ZERO], 10**18)
        self.assertEqual(model.account_totals[22]['royalties',ZERO], 0)


class NativeCustodyHistoryAPITests(unittest.TestCase):
    def setUp(self):
        # Composition reuses the real byte-level SQLite/RPC fixture without
        # inheriting and silently rerunning all its unrelated test methods.
        self.base = earnings_fixture.EarningsAPITests(); self.base.setUp()

    def tearDown(self): self.base.tearDown()

    def _history(self, recovered):
        base = self.base; rpc = base.rpc; i,j = rpc.nft_id,rpc.other
        for ordinal,identifier in enumerate((i,j),1):
            rpc.put(addr(2),'mintOrdinalOf(uint256)',(identifier,),(ordinal,))
            rpc.put(addr(2),'tokenAtOrdinal(uint256)',(ordinal,),(identifier,))
        entries = [custody_event('RoyaltyCustodyExited',amount=100,block=22),
                   event('membership','MembershipActivated',(j,),(),23),
                   event('royalties','RoyaltyAssetDeferred',(j,ZERO),(),23,1),
                   event('royalties','Activated',(j,),(3,),23,2),
                   event('vault','SharesAdded',(j,5),(100,100*10**18),23,3)]
        if recovered:
            entries += [custody_event('RoyaltyCustodyReturned',amount=100,block=24),
                        event('royalties','RoyaltiesReceived',(ZERO,),(50,1),25),
                        event('royalties','RoyaltyEligibilityRecovered',(ZERO,),(2,2),25,1),
                        event('royalties','RoyaltiesReceived',(ZERO,),(400,1),26)]
        for entry in entries:
            entry['blockHash'] = rpc.header(int(entry['blockNumber'],16))['hash']; rpc.logs.append(entry)
        rpc.put(addr(41),'totalEligible()',values=(2,))
        rpc.put(addr(5),'totalWeight()',values=(4,)); rpc.put(addr(5),'activationCount()',values=(2,))
        rpc.put(addr(3),'bucketTotalShares(uint256)',(5,),(200,))
        rpc.put(addr(3),'nftBucket(uint256)',(j,),(5,)); rpc.put(addr(3),'sharesOf(uint256)',(j,),(100,))
        rpc.put(addr(5),'weightOf(uint256)',(j,),(3,))
        for asset in (addr(20),addr(21)):
            rpc.put(addr(4),'claimable(uint256,address)',(j,asset),(0,))
        for asset in (ZERO,addr(21)):
            count = 1 if asset == ZERO and not recovered else 2
            weight = 1 if asset == ZERO and not recovered else 4
            index = (250 if recovered else 100)*SCALE if asset==ZERO else 0
            for signature,value in (('eligibleCount(address)',count),('eligibleWeight(address)',weight),
                                    ('index(address)',index),('pending(address)',0)):
                native_put(rpc,addr(5),signature,(asset,),(value,))
            native_put(rpc,addr(5),'claimable(uint256,address)',(i,asset),(250 if recovered and asset==ZERO else 100 if asset==ZERO else 0,))
            native_put(rpc,addr(5),'claimable(uint256,address)',(j,asset),(300 if recovered and asset==ZERO else 0,))
        # Re-ingest the complete augmented stream into a fresh temporary index;
        # no existing database, live process or chain is reset.
        base.index.close(); base.cfg['history']['database'] += '.custody'
        cfg = dict(base.cfg['history'],chain_id=31337,rpc_urls=['http://127.0.0.1:8545'],confirmations=12,
                   block_chunk=200,max_reorg_depth=100,poll_seconds=1); cfg.pop('max_events')
        base.index = Indexer(cfg,rpc); base.index.step()
        return i,j

    def test_complete_indexed_history_recovers_both_nfts_after_exact_native_return(self):
        i,j = self._history(True)
        reports = [self.base.read(str(identifier)) for identifier in (i,j)]
        earned = [next(row for row in report['all_time'] if row['asset']==ZERO)['royalties_raw'] for report in reports]
        self.assertEqual(earned,['250','300'])
        collection = self.base.read()
        native = next(row for row in collection['all_time'] if row['asset']==ZERO)
        self.assertEqual(native['royalties_received_raw'],'550')
        self.assertEqual(native['royalties_allocated_raw'],'550')

    def test_external_custody_keeps_unverifiable_nft_reconciliation_closed(self):
        i,_ = self._history(False); original = self.base.rpc.call
        pending = native_data('pending(address)',ZERO)
        def held(method,args):
            if method=='eth_call' and args[0]['to']==addr(5) and args[0]['data']==pending:
                raise RpcError('CustodyInTransit')
            return original(method,args)
        with patch.object(self.base.rpc,'call',side_effect=held):
            with self.assertRaises(RpcError): self.base.read(str(i))
            native = next(row for row in self.base.read()['all_time'] if row['asset']==ZERO)
            self.assertEqual(native['royalties_received_raw'],'100')


if __name__ == '__main__': unittest.main()
