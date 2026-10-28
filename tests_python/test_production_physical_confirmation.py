"""Synthetic schema6 contradictions; no live provider, service or transaction."""
import copy
import unittest
from unittest.mock import patch

from zzz_ops import production_v4 as P
from zzz_ops import production_observer_v4 as O
from zzz_ops.tick_math import sqrt_price_at_tick
from tests_python import production_v4_fixtures as F


class PhysicalConfirmationTests(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.old,'HASH',F.RUNTIME),
                patch.object(P.V,'NATIVE_DEPENDENCIES',{role:(address,F.RUNTIME)
                    for role,(address,_pin) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start();self.addCleanup(context.stop)
        self.cfg=F.active(F.fixture());self.chain=self.cfg['chains'][0]
        self.bucket=self.chain['holder_exit']['observed']['buckets'][0]
        self.row=self.chain['rebalance_confirmation']['observed']['buckets'][0]

    def report(self,cfg=None):return P.validate(cfg or self.cfg,expected_commit=F.COMMIT,now=F.NOW)
    def codes(self,cfg=None):return {item['code'] for item in self.report(cfg)['issues']}
    def not_due(self):
        self.row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=False,ready=False,
            raw_needed=False,range_pending=False)

    def test_opposite_condition_and_stored_side_cannot_relabel_physical_exit(self):
        self.row.update(condition_side=1,stored_side=1)
        self.assertIn('confirmation.physical_side',self.codes())

    def test_false_raw_candidate_cannot_hide_cooled_outside_lp(self):
        self.not_due()
        self.assertIn('confirmation.raw_physical',self.codes())

    def test_manual_exception_requires_a_real_recorded_centre_range_change(self):
        self.row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=True,range_pending=True)
        self.assertIn('confirmation.range_pending',self.codes())
        self.assertIn('confirmation.physical_side',self.codes())
        self.bucket['lp_ticks'][1]-=200
        self.bucket.update(F.physical_position(self.chain['pools'][0],self.bucket['lp_ticks']))
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_inside_lp_cannot_report_an_ordinary_outside_candidate(self):
        self.bucket['position'][5]=2**96;self.bucket['lp_ticks']=[-4200,7000]
        self.bucket.update(F.physical_position(self.chain['pools'][0],self.bucket['lp_ticks']))
        self.assertIn('confirmation.raw_physical',self.codes())
        self.not_due()
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])

    def test_boundaries_preserve_lower_inclusive_upper_exclusive_and_downward_tick(self):
        for tick,sqrt_tick,side in ((-14200,-14200,0),(-14201,-14200,1),(-3000,-3000,2)):
            with self.subTest(tick=tick):
                cfg=copy.deepcopy(self.cfg);chain=cfg['chains'][0]
                chain['pools'][0]['slot0'].update(tick=tick,sqrt_price_x96=str(sqrt_price_at_tick(sqrt_tick)))
                row=chain['rebalance_confirmation']['observed']['buckets'][0]
                row.update(condition_side=side,stored_side=side or 2,raw_needed=bool(side),ready=bool(side),
                    condition_identity=F.RUNTIME if side else P.ZERO_HASH)
                self.assertTrue(self.report(cfg)['inventory_consistent'],self.report(cfg)['issues'])

    def test_noncanonical_or_unaligned_physical_ticks_are_rejected(self):
        for ticks in ((-14200,-3000),[-14199,-3000],[-14200,True],[-3000,-14200],[-900000,-3000]):
            with self.subTest(ticks=ticks):
                cfg=copy.deepcopy(self.cfg);cfg['chains'][0]['holder_exit']['observed']['buckets'][0]['lp_ticks']=ticks
                self.assertFalse(self.report(cfg)['inventory_consistent'])

    def test_paused_helper_keeps_raw_history_without_range_pending_dependency(self):
        self.chain['holder_exit']['observed']['paused']=True
        self.row.update(condition_side=0,condition_identity=P.ZERO_HASH,manual=False,ready=False,range_pending=None)
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        rpc=F.RPC(self.cfg);strategy=self.chain['modules']['strategy']['address']
        rpc.overrides[strategy,F.selector('rangeUpdatePending(uint256)')+F.O._word(7)]='0x'
        observed=O.observe(self.cfg,rpc)
        self.assertTrue(observed['chains'][0]['observation']['complete'])
        self.assertIsNone(observed['chains'][0]['rebalance_confirmation']['observed']['buckets'][0]['range_pending'])

    def test_no_physical_ticks_are_invented_for_parked_or_dormant_principal(self):
        self.bucket['position'][1]=0;self.bucket['position'][7]=4
        self.bucket.update(lp_owner=None,lp_liquidity=None,lp_ticks=None,lp_pool_key=None,lp_position_info=None);self.not_due()
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        cfg=F.fixture();chain=cfg['chains'][0];chain['holder_exit']['observed']['minted_count']=1
        chain['nft_inventory']['observed_bindings']['mintedCount']=1
        chain['holder_exit']['observed']['nfts']=[dict(id=101,ordinal=1,reverse_ordinal=1,
            owner=F.old.addr(20000),bucket=0,shares=0,eth=0,zzz=0,allocated=False,paid=False,claimable=None)]
        self.assertTrue(self.report(cfg)['inventory_consistent'],self.report(cfg)['issues'])

    def test_old_schema6_observations_require_reobservation_without_defaults(self):
        for location,key in (('bucket','lp_ticks'),('bucket','lp_pool_key'),('bucket','lp_position_info'),('row','range_pending')):
            cfg=copy.deepcopy(self.cfg);chain=cfg['chains'][0]
            record=chain['holder_exit']['observed']['buckets'][0] if location=='bucket' else chain['rebalance_confirmation']['observed']['buckets'][0]
            record.pop(key)
            self.assertIn('schema.keys',self.codes(cfg))

    def test_observer_reads_physical_ticks_and_pending_at_the_same_pinned_hash(self):
        rpc=F.RPC(self.cfg);observed=O.observe(self.cfg,rpc)
        self.assertTrue(observed['chains'][0]['observation']['complete'])
        self.assertTrue(self.report(observed)['inventory_consistent'],self.report(observed)['issues'])
        wanted={(self.chain['modules']['liquidity']['address'],F.selector('ticks(uint256)')+F.O._word(99)),
            (self.chain['dependencies']['position_manager']['address'],F.selector('getPoolAndPositionInfo(uint256)')+F.O._word(99)),
            (self.chain['modules']['strategy']['address'],F.selector('rangeUpdatePending(uint256)')+F.O._word(7))}
        calls={(params[0]['to'],params[0]['data']) for method,params in rpc.calls if method=='eth_call'
            and params[-1]=={'blockHash':F.RUNTIME,'requireCanonical':True}}
        self.assertTrue(wanted<=calls)

    def test_exited_positions_cannot_retain_idle_principal(self):
        for index in (2,3):
            cfg=F.exited(copy.deepcopy(self.cfg));cfg['chains'][0]['holder_exit']['observed']['buckets'][0]['position'][index]=1
            self.assertIn('exit.terminal_idle',self.codes(cfg))

    def test_foreign_pool_key_cannot_qualify_with_valid_owner_liquidity_and_ticks(self):
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        self.bucket['lp_pool_key'][1]=f'{int(F.old.addr(22222),16):064x}'
        self.assertIn('exit.lp_pool_identity',self.codes())
        observed=O.observe(self.cfg,F.RPC(self.cfg))
        self.assertFalse(observed['chains'][0]['observation']['complete'])
        self.assertIsNone(observed['chains'][0]['holder_exit']['observed'])

    def test_physical_pool_key_requires_exact_canonical_static_abi(self):
        original=self.bucket['lp_pool_key']+[self.bucket['lp_position_info']]
        bad=[original[:5],original+[original[-1]]]
        for index,value in ((0,1<<160),(1,1<<160),(2,1<<24),(3,1<<24),(4,1<<160)):
            words=list(original);words[index]=f'{value:064x}';bad.append(words)
        for words in bad:
            with self.subTest(words=len(words)):
                rpc=F.RPC(self.cfg);posm=self.chain['dependencies']['position_manager']['address']
                rpc.overrides[posm,F.selector('getPoolAndPositionInfo(uint256)')+F.O._word(99)]='0x'+''.join(words)
                observed=O.observe(self.cfg,rpc)
                self.assertFalse(observed['chains'][0]['observation']['complete'])
                self.assertIsNone(observed['chains'][0]['holder_exit']['observed'])

    def test_packed_position_ticks_must_equal_manager_ticks(self):
        self.bucket['lp_position_info']=f'{int(self.bucket["lp_position_info"],16)^(1<<8):064x}'
        self.assertIn('exit.lp_pool_identity',self.codes())
        observed=O.observe(self.cfg,F.RPC(self.cfg))
        self.assertFalse(observed['chains'][0]['observation']['complete'])

    def test_packed_pool_prefix_and_subscriber_match_installed_layout(self):
        original=int(self.bucket['lp_position_info'],16)
        self.bucket['lp_position_info']=f'{original|1:064x}'
        self.assertTrue(self.report()['inventory_consistent'],self.report()['issues'])
        observed=O.observe(self.cfg,F.RPC(self.cfg))
        self.assertTrue(observed['chains'][0]['observation']['complete'])
        for value in (original^(1<<255),original|2):
            self.bucket['lp_position_info']=f'{value:064x}'
            self.assertIn('exit.lp_pool_identity',self.codes())
            observed=O.observe(self.cfg,F.RPC(self.cfg))
            self.assertFalse(observed['chains'][0]['observation']['complete'])


if __name__=='__main__':unittest.main()
