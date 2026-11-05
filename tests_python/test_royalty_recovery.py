"""Recovery income is distinct from old entitlements, conversion and receipts."""
import unittest

from frontend_api.earnings_replay import Replay, SCALE, ZERO
from frontend_api.history import HistoryError
from tests_python.test_earnings import init, activate, consume, event
from tests_python.test_frontend_api import addr
from indexer.events import decode


class RoyaltyRecoveryReplayTests(unittest.TestCase):
    def model(self, target=11):
        m=Replay(1000,target); init(m); activate(m,11,100,1)
        return m

    def test_recovered_eth_uses_current_weights_without_recounting_empty_receipt(self):
        m=Replay(1000,22);init(m)
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(300,0),12))
        activate(m,11,100,1);activate(m,22,100,2,14)
        consume(m,event('royalties','UnallocatedRoyaltiesRecovered',(ZERO,),(300,300,3,1),20))
        self.assertEqual(m.totals['royalties_received',ZERO],300)
        self.assertEqual(m.totals['royalties_quarantined',ZERO],300)
        self.assertEqual(m.totals['royalties_recovered',ZERO],300)
        self.assertEqual(m.totals['royalties_allocated',ZERO],300)
        self.assertEqual(m.totals['royalties',ZERO],200);m.finish()

    def test_unknown_source_needs_no_descriptor_and_dormant_gets_no_recovery(self):
        m=self.model(22)
        consume(m,event('royalties','UnallocatedRoyaltiesRecovered',(addr(999),),(600,300,1,1),20))
        self.assertEqual(m.totals['royalties',ZERO],0)
        self.assertEqual(m.royalty_index[ZERO],300*SCALE)
        self.assertEqual(m.totals['royalties_recovered',addr(999)],0);m.finish()

    def test_deferred_token_keeps_old_cohort_while_recovery_eth_uses_all_active(self):
        m=self.model(22);activate(m,22,100,3,14,True)
        consume(m,event('royalties','RoyaltiesReceived',(addr(21),),(400,1),20))
        consume(m,event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(2,2),20,1))
        consume(m,event('royalties','UnallocatedRoyaltiesRecovered',(addr(999),),(600,400,4,1),21))
        self.assertEqual(m.totals['royalties',addr(21)],0)
        self.assertEqual(m.totals['royalties',ZERO],300);m.finish()

    def test_fraction_carry_is_preserved_across_regular_and_recovered_allocations(self):
        m=self.model();activate(m,22,100,2,14)
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(1,1),20))
        consume(m,event('royalties','UnallocatedRoyaltiesRecovered',(addr(999),),(3,3,3,1),21))
        self.assertEqual(m.totals['royalties',ZERO],1)
        self.assertEqual(m.scaled['royalties',ZERO],SCALE//3+SCALE)

    def test_wrong_weight_zero_values_bad_native_or_frozen_state_reject(self):
        for values,source in [((1,1,2,1),addr(999)),((0,1,1,1),addr(999)),
                              ((1,0,1,1),addr(999)),((1,1,1,0),addr(999)),((2,1,1,1),ZERO)]:
            with self.subTest(values=values,source=source),self.assertRaises(HistoryError):
                consume(self.model(),event('royalties','UnallocatedRoyaltiesRecovered',(source,),values,20))
        m=self.model();consume(m,event('handoff','Frozen',('0x'+'1'*64,addr(200)),(),19))
        with self.assertRaises(HistoryError):
            consume(m,event('royalties','UnallocatedRoyaltiesRecovered',(ZERO,),(1,1,1,1),20))

    def test_indexer_decodes_recovery_without_requiring_token_admission(self):
        ev=event('royalties','UnallocatedRoyaltiesRecovered',(addr(999),),(600,300,3,1),20)
        name,parsed=decode(ev)
        self.assertEqual(name,'UnallocatedRoyaltiesRecovered')
        self.assertEqual(parsed['asset'],addr(999));self.assertEqual(parsed['nativeAmount'],'300')


if __name__=='__main__':unittest.main()
