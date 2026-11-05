"""Fresh royalty4 keeper boundaries; no network, signer or operating journal.

Exercises the newly admitted profile explicitly rather than treating royalty2
coverage as proof of the new profile. LP conversion remains independently typed.
"""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.royalties import BATCH, RoyaltyAutomation
from tests_python import test_keeper_confirmation_wakeup as clock_fixtures


def account(n):
    return '0x'+f'{n:040x}'


class CurrentRoyaltyKeeperBoundaryTests(unittest.TestCase):
    def worker(self, *, lp=False, version=4):
        key='lp_conversion' if lp else 'royalty_conversion'
        names=('rewards','lp_converter','lp_nft','oracle','lp_v4_executor') if lp else (
            'royalties','royalty_converter','royalty_nft','oracle','royalty_v4_executor')
        return SimpleNamespace(accounting_version=6,royalty_settlement_version=version,state={},
            config={key:{'enabled':True,'profile':'v4_native',
                'assets':[{'asset':account(100),'route_id':'0x'+'12'*32,
                    'minimum_source_units':1,'minimum_output_wei':1}]},
                'code_hashes':{name:'0x'+'34'*32 for name in names}},
            contracts={name:account(i+1) for i,name in enumerate(names)})

    def test_current_disabled_royalty_worker_needs_no_converter_and_preserves_saved_state(self):
        state={'pending':{'hash':'0x'+'56'*32,'nonce':7},'royalty_conversion':{'historical':'evidence'}}
        for version in (3,4):
            with self.subTest(version=version):
                k=SimpleNamespace(config={},state=copy.deepcopy(state),royalty_settlement_version=version)
                worker=RoyaltyAutomation(k)
                self.assertFalse(worker.enabled)
                self.assertEqual(k.state,state)
                self.assertFalse(hasattr(worker,'routes'))

    def test_current_royalty_worker_rejects_enabled_or_hidden_conversion_configuration(self):
        for version in (3,4):
            for settings in ({'enabled':True},{'enabled':False,'profile':'v4_native'},
                             {'enabled':False,'assets':[]},{'enabled':False,'max_nfts_per_cycle':1}):
                with self.subTest(version=version,settings=settings):
                    k=SimpleNamespace(config={'royalty_conversion':settings},
                        royalty_settlement_version=version,state={'pending':{'original':'evidence'}})
                    before=copy.deepcopy(k.state)
                    with self.assertRaisesRegex(ValueError,'prohibit conversion settings'):
                        RoyaltyAutomation(k)
                    self.assertEqual(k.state,before)

    def test_current_direct_royalty_conversion_rejects_before_reads_or_nonce_work(self):
        # No RPC or submit dependency exists on the subject: passing this check
        # must reject before those dependencies can be reached.
        for version in (3,4):
            with self.subTest(version=version):
                k=SimpleNamespace(state={},royalty_settlement_version=version)
                with self.assertRaisesRegex(ValueError,'cannot be swapped'):
                    Keeper.submit(k,'royalties',BATCH,(),'unexpected')
                self.assertEqual(k.state,{})

    def test_pending_recovery_is_not_replaced_by_a_new_current_royalty_action(self):
        pending={'key':'historical','hash':'0x'+'56'*32,'nonce':7,'data':'0xabcd'}
        for version in (3,4):
            with self.subTest(version=version):
                k=SimpleNamespace(state={'pending':copy.deepcopy(pending)},royalty_settlement_version=version)
                self.assertFalse(Keeper.submit(k,'royalties',BATCH,(),'unexpected'))
                self.assertEqual(k.state,{'pending':pending})

    def test_current_royalty_profile_keeps_reviewed_lp_conversion_separate(self):
        for version in (3,4):
            with self.subTest(version=version):
                k=self.worker(lp=True,version=version)
                worker=RoyaltyAutomation(k,lp=True)
                self.assertTrue(worker.enabled)
                self.assertEqual((worker.ledger,worker.converter,worker.profile),
                                 ('rewards','lp_converter','v4_native'))
                self.assertIn('lp_conversion',k.state)
                self.assertNotIn('royalty_conversion',k.state)

    def test_exact_royalty_profile_requires_accounting6_and_is_admitted_by_real_constructor(self):
        with self.assertRaisesRegex(ValueError,'requires accounting6'):
            Keeper({'royalty_settlement_version':4,'accounting_version':1})
        fixture=clock_fixtures.KeeperConfirmationWakeupTests('runTest')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        cfg=copy.deepcopy(fixture.rpc.cfg)
        cfg['royalty_settlement_version']=4
        current=Keeper(cfg,rpc=fixture.rpc)
        self.assertEqual(current.royalty_settlement_version,4)
        self.assertFalse(current.royalties.enabled)

    def test_historical_conversion_remains_explicit_and_does_not_get_relabelled(self):
        k=self.worker(version=0)
        worker=RoyaltyAutomation(k)
        self.assertTrue(worker.enabled)
        self.assertEqual((worker.ledger,worker.converter,worker.profile),
                         ('royalties','royalty_converter','v4_native'))
        self.assertEqual(k.royalty_settlement_version,0)


class CurrentSchedulingClockBoundaryTests(unittest.TestCase):
    def test_nonfinite_elapsed_clock_never_becomes_a_readiness_or_short_sleep_guess(self):
        fixture=clock_fixtures.KeeperConfirmationWakeupTests('runTest')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.schedule(execute_in=60);fixture.head()
        before=copy.deepcopy(fixture.k.state)
        for value in (float('nan'),float('inf'),float('-inf')):
            with self.subTest(value=value),patch('keeper.monitor.time.monotonic',return_value=value):
                self.assertEqual(fixture.k.poll_delay(240),240)
        self.assertEqual(fixture.k.state,before)


if __name__=='__main__':
    unittest.main()
