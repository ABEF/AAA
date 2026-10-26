import unittest
import copy

from frontend_api.activation import ActivationTransactions
from frontend_api.service import Projection, ProjectionError
from tests_python.test_frontend_activation import ActivationRPC
from tests_python.test_frontend_api import MockRPC, addr, configuration
from zzz_ops.tick_math import sqrt_price_at_tick


class LiquidityContextTests(unittest.TestCase):
    def setup_service(self, **options):
        self.rpc = ActivationRPC(**options)
        return ActivationTransactions(Projection(configuration(), self.rpc, clock=lambda:1000), self.rpc.config)

    def tick(self, tick):
        # Match actual v4 integer TickMath, including the strategy observation.
        price = sqrt_price_at_tick(tick)
        self.rpc.put(self.rpc.pins['state_view'],'getSlot0(bytes32)',(self.rpc.pool,),
                     (price,tick if tick >= 0 else 2**256+tick,0,0))
        self.rpc.put(self.rpc.pins['strategy'],'validatePrice(bytes32)',(self.rpc.pool,),(price,))

    def test_lower_inclusive_upper_exclusive_and_outside_allowed(self):
        for tick,active in [(-121,False),(-120,True),(0,True),(119,True),(120,False),(121,False)]:
            svc=self.setup_service();self.tick(tick)
            with self.subTest(tick=tick):
                result=svc.prepare(self.rpc.request)
                self.assertTrue(result['activation_ready'])
                context=result['liquidity_context'];self.assertEqual(context['in_range'],active)
                self.assertEqual(len(context['warnings']),0 if active else 1)
                if not active:
                    warning=context['warnings'][0]['message']
                    self.assertIn('1970-01-01T01:00:01+00:00',warning)
                    self.assertIn('Next keeper check: unavailable',warning)
                self.assertIsNone(context['rebalance']['expected_execution_at'])

    def test_due_rebalance_does_not_block_in_range_or_outside_contribution(self):
        for tick in (0,121):
            svc=self.setup_service(increase=True);self.tick(tick)
            config=[addr(20)]+self.rpc.pool_values[1:];config[11]=10
            self.rpc.put(self.rpc.pins['pools'],'get(bytes32)',(self.rpc.pool,),config)
            self.rpc.put(self.rpc.pins['pools'],'accounting(bytes32)',(self.rpc.pool,),config)
            self.rpc.put(self.rpc.pins['oracle'],'referenceX96(address,address)',(addr(20),addr(21)),(2**96*11//10,))
            self.rpc.put(self.rpc.pins['strategy'],'needsRebalance(uint256)',(self.rpc.bucket,),(1,))
            result=svc.prepare(self.rpc.request);context=result['liquidity_context']
            self.assertTrue(result['activation_ready']);self.assertEqual(context['rebalance']['status'],'eligible_now')
            self.assertIn('eligible now',context['warnings'][0]['message'])
            self.assertEqual(context['rebalance']['earliest_eligible_at'],11)

    def test_new_range_has_no_fabricated_last_or_next_rebalance(self):
        svc=self.setup_service(new_pool=True);r=svc.prepare(self.rpc.request)['liquidity_context']
        self.assertEqual(r['range_basis'],'proposed_initial_position')
        self.assertIsNone(r['lp_token_id']);self.assertIsNone(r['rebalance']['earliest_eligible_at'])
        self.assertEqual(r['rebalance']['status'],'new_position')

    def test_approval_also_contains_warning_and_no_pledge_of_execution(self):
        svc=self.setup_service();self.tick(121);self.rpc.allowance=0
        result=svc.prepare(self.rpc.request)
        self.assertFalse(result['activation_ready'])
        self.assertEqual(result['liquidity_context']['warnings'][0]['code'],'LP_OUT_OF_RANGE')

    def test_malformed_range_custody_price_or_eligibility_fails_closed(self):
        for role,method,args,values in [
            ('liquidity','ticks(uint256)',(9,),(2**24-120,120)),
            ('liquidity','ticks(uint256)',(9,),(120,120)),
            ('liquidity','ticks(uint256)',(9,),(2**256-121,120)),
            ('strategy','validatePrice(bytes32)',None,(1,)),
            ('strategy','needsRebalance(uint256)',(5,),(1,))]:
            svc=self.setup_service()
            self.rpc.put(self.rpc.pins[role],method,(self.rpc.pool,) if args is None else args,values)
            with self.subTest(method=method,values=values),self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)

    def test_current_physical_id_is_resolved_again_after_rebalance(self):
        svc=self.setup_service(increase=True)
        first=svc.prepare(self.rpc.request)['liquidity_context']
        self.rpc.lp_id=44
        self.rpc.put(addr(3),'group(uint256)',(5,),(self.rpc.pool,44,0,0,1000*10**18,2**96,990,1,31337,addr(3),addr(68),addr(20),addr(21),31337,addr(3)))
        self.rpc.put(self.rpc.pins['liquidity'],'ticks(uint256)',(44,),(2**256-600,600))
        second=svc.prepare(self.rpc.request)['liquidity_context']
        self.assertEqual(first['lp_token_id'],'9');self.assertEqual(second['lp_token_id'],'44')
        self.assertEqual(second['lower_tick'],-600);self.assertEqual(second['rebalance']['earliest_eligible_at'],4590)
        self.assertTrue(second['reprepare_on_position_or_range_change'])

    def test_approved_range_update_can_be_due_at_flat_price(self):
        for allowance in (0, 10**30):
            svc=self.setup_service(increase=True);self.rpc.allowance=allowance
            self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(1,))
            waiting=svc.prepare(self.rpc.request)['liquidity_context']['rebalance']
            self.assertEqual(waiting['status'],'cooldown')
            self.assertFalse(waiting['price_trigger_met'])
            self.assertTrue(waiting['range_update_pending'])
            self.assertIn('approved range update is pending',waiting['explanation'])
            config=[addr(20)]+self.rpc.pool_values[1:];config[11]=600
            for getter in ('get(bytes32)','accounting(bytes32)'):
                self.rpc.put(self.rpc.pins['pools'],getter,(self.rpc.pool,),config)
            self.rpc.put(self.rpc.pins['strategy'],'needsRebalance(uint256)',(5,),(1,))
            result=svc.prepare(self.rpc.request);r=result['liquidity_context']['rebalance']
            self.assertEqual(r['status'],'eligible_now');self.assertEqual(r['eligibility_reason'],'range_update')
            self.assertFalse(r['price_trigger_met']);self.assertIsNone(r['expected_execution_at'])
            self.assertEqual(result['activation_ready'],allowance!=0)

    def test_both_causes_reported_and_applied_range_clears_pending(self):
        svc=self.setup_service();config=[addr(20)]+self.rpc.pool_values[1:];config[11]=600
        for getter in ('get(bytes32)','accounting(bytes32)'):
            self.rpc.put(self.rpc.pins['pools'],getter,(self.rpc.pool,),config)
        self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(1,))
        self.rpc.put(self.rpc.pins['strategy'],'needsRebalance(uint256)',(5,),(1,))
        self.rpc.put(self.rpc.pins['oracle'],'referenceX96(address,address)',(addr(20),addr(21)),(2**96*11//10,))
        self.assertEqual(svc.prepare(self.rpc.request)['liquidity_context']['rebalance']['eligibility_reason'],'price_and_range')
        self.rpc.put(self.rpc.pins['oracle'],'referenceX96(address,address)',(addr(20),addr(21)),(2**96,))
        for getter in ('rangeUpdatePending(uint256)','needsRebalance(uint256)'):
            self.rpc.put(self.rpc.pins['strategy'],getter,(5,),(0,))
        r=svc.prepare(self.rpc.request)['liquidity_context']['rebalance']
        self.assertFalse(r['range_update_pending']);self.assertIsNone(r['eligibility_reason'])
        self.assertEqual(r['status'],'waiting_for_price_trigger')

    def test_invalid_range_flag_and_inconsistent_eligibility_fail_closed(self):
        svc=self.setup_service()
        self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(2,))
        with self.assertRaises(ProjectionError):svc.prepare(self.rpc.request)
        self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(1,))
        config=[addr(20)]+self.rpc.pool_values[1:];config[11]=600
        for getter in ('get(bytes32)','accounting(bytes32)'):
            self.rpc.put(self.rpc.pins['pools'],getter,(self.rpc.pool,),config)
        with self.assertRaisesRegex(ProjectionError,'eligibility disagrees'):svc.prepare(self.rpc.request)

    def test_new_position_does_not_inherit_existing_range_update_flag(self):
        svc=self.setup_service(new_pool=True)
        self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(1,))
        r=svc.prepare(self.rpc.request)['liquidity_context']['rebalance']
        self.assertFalse(r['range_update_pending']);self.assertIsNone(r['eligibility_reason'])

    def range_service(self, *, pending=False, mode=1):
        self.rpc = ActivationRPC(increase=True)
        self.rpc.config['range_policy_version'] = 1
        keeper = {'enabled':False,'narrow_trigger_bps':0,'widen_trigger_bps':0,
            'minimum_interval_seconds':0,'configuration_hash':'0x'+'00'*32,'review_hash':'0x'+'00'*32}
        self.rpc.config['range_policies'] = [{'pool_id':self.rpc.pool,'orientation':mode,'keeper':keeper}]
        config = [addr(20)]+self.rpc.pool_values[1:]
        config[7]=5000;config[8]=2000;config[11]=600
        for getter in ('get(bytes32)','accounting(bytes32)'):
            self.rpc.put(self.rpc.pins['pools'],getter,(self.rpc.pool,),config)
        for getter,values in (('RANGE_POLICY_VERSION()',(1,)),('rangeOrientation(bytes32)',(mode,)),
                ('keeperRangePolicy(bytes32)',(0,0,0,0,0,0,0)),('keeperRangeTarget(bytes32)',(0,))):
            self.rpc.put(self.rpc.pins['strategy'],getter,() if getter.endswith('()') else (self.rpc.pool,),values)
        self.rpc.put(self.rpc.pins['oracle'],'referenceX96(address,address)',(addr(20),addr(21)),(2**96*11//10,))
        self.rpc.put(self.rpc.pins['strategy'],'rangeUpdatePending(uint256)',(5,),(int(pending),))
        self.rpc.put(self.rpc.pins['strategy'],'needsRebalance(uint256)',(5,),(int(pending or mode==0),))
        return ActivationTransactions(Projection(configuration(),self.rpc,clock=lambda:1000),self.rpc.config)

    def test_inverse_price_orientation_recomputes_trigger_and_pending_width(self):
        for mode,pending,reason in ((0,False,'price_trigger'),(1,False,None),(1,True,'range_update')):
            with self.subTest(mode=mode,pending=pending):
                service=self.range_service(mode=mode,pending=pending)
                context=service.prepare(self.rpc.request)['liquidity_context']
                # sqrt ratio1.1: direct price moves21%, inverse moves17.36%.
                self.assertEqual(context['rebalance']['price_trigger_met'],mode==0)
                self.assertEqual(context['rebalance']['eligibility_reason'],reason)
                self.assertEqual(context['rebalance']['eligible_at_snapshot'],pending or mode==0)
                self.assertEqual(context['range_orientation'],mode)
                self.assertEqual(context['keeper_range_policy']['target_half_width_bps'],0)

    def test_explicit_range_profile_rejects_malformed_or_mismatched_observations(self):
        cases=[('RANGE_POLICY_VERSION()',(),(2,)),('rangeOrientation(bytes32)',None,(0,)),
               ('rangeOrientation(bytes32)',None,(2,)),('keeperRangePolicy(bytes32)',None,(2,0,0,0,0,0,0)),
               ('keeperRangePolicy(bytes32)',None,(0,0,0,0,1001,0,0)),('keeperRangeTarget(bytes32)',None,(1000,))]
        for getter,args,values in cases:
            with self.subTest(getter=getter,values=values):
                service=self.range_service()
                self.rpc.put(self.rpc.pins['strategy'],getter,(self.rpc.pool,) if args is None else args,values)
                with self.assertRaises(ProjectionError): service.prepare(self.rpc.request)

    def test_range_profile_intent_and_eligibility_are_not_inferred(self):
        self.range_service()
        for version in (True,2):
            config=copy.deepcopy(self.rpc.config);config['range_policy_version']=version
            with self.subTest(version=version),self.assertRaises(ValueError):
                ActivationTransactions(Projection(configuration(),self.rpc),config)
        config=copy.deepcopy(self.rpc.config);config['range_policies']=[]
        with self.assertRaises(ValueError):ActivationTransactions(Projection(configuration(),self.rpc),config)
        service=self.range_service()
        self.rpc.put(self.rpc.pins['strategy'],'needsRebalance(uint256)',(5,),(1,))
        with self.assertRaisesRegex(ProjectionError,'eligibility disagrees'):service.prepare(self.rpc.request)


class CurrentPositionTests(unittest.TestCase):
    def test_replacement_id_denominator_and_current_mark_are_independent_of_historical_input(self):
        rpc=MockRPC();service=Projection(configuration(),rpc,clock=lambda:1000)
        rpc.put(addr(3),'contributionUSD(uint256)',(rpc.nft_id,),(500*10**18,))
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(1,490*10**18))
        first=service.nft(str(rpc.nft_id))['position']
        self.assertEqual(first['current_lp_value']['raw'],str(490*10**18))
        self.assertEqual(first['cumulative_gross_contribution_usd_18'],str(500*10**18))
        self.assertEqual(first['local_custody']['lp_token_id'],'9')
        rpc.put(addr(3),'group(uint256)',(5,),(444,44,0,0,10000*10**18,2**96,999,1,31337,addr(3),addr(7),addr(20),addr(21),31337,addr(3)))
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(1,600*10**18))
        second=service.nft(str(rpc.nft_id))['position']
        self.assertEqual(second['local_custody']['lp_token_id'],'44')
        self.assertEqual(second['current_lp_value']['raw'],str(600*10**18))
        self.assertEqual(first['shares_raw'],second['shares_raw'])

    def test_invalid_active_custody_and_share_denominator_fail_closed(self):
        for field,value in [(1,0),(7,6),(8,999),(9,addr(99)),(13,999),(14,addr(99))]:
            rpc=MockRPC();service=Projection(configuration(),rpc,clock=lambda:1000)
            group=[444,9,0,0,10000*10**18,2**96,999,1,31337,addr(3),addr(7),addr(20),addr(21),31337,addr(3)]
            group[field]=value;rpc.put(addr(3),'group(uint256)',(5,),group)
            with self.subTest(field=field),self.assertRaises(ProjectionError):service.nft(str(rpc.nft_id))
        rpc=MockRPC();rpc.put(addr(3),'bucketTotalShares(uint256)',(5,),(1,))
        with self.assertRaises(ProjectionError):Projection(configuration(),rpc,clock=lambda:1000).nft(str(rpc.nft_id))

    def test_remote_value_remains_unavailable_and_fee_rights_remain(self):
        rpc=MockRPC();rpc.put(addr(3),'nftStatus(uint256)',(rpc.nft_id,),(3,))
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(0,0))
        service=Projection(configuration(),rpc,clock=lambda:1000);r=service.nft(str(rpc.nft_id))
        self.assertIsNone(r['position']['current_lp_value']['raw']);self.assertIsNone(r['position']['local_custody'])
        self.assertTrue(r['position']['activated']);self.assertTrue(r['claimable']['royalties'])
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(1,0))
        with self.assertRaises(ProjectionError):service.nft(str(rpc.nft_id))
