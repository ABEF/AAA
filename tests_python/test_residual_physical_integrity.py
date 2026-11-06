"""Fresh6 readers reject correlated, physically impossible two-leg replies."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from keeper.compound_policy import observe
from tests_python.test_keeper_policy_v6 import PolicyRPC
from zzz_ops.tick_math import sqrt_price_at_tick,MIN_SQRT,MAX_SQRT
from zzz_ops.physical_portfolio import physical_amounts,portfolio_fingerprints
from zzz_ops.production_v5 import physical_amounts as historical_amounts
from zzz_ops.production_v6 import physical_amounts as preflight_amounts


class ResidualPhysicalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.rpc=PolicyRPC(Path(self.temp.name)/'inert.json')
        self.rpc.secondary=124;self.rpc.secondary_count=1
        # The fresh residual lies inside the main, initially beyond spot.
        self.rpc.aux_ticks=(20,80)
    def read(self,**kwargs):
        return observe(self.rpc.read,self.rpc.code,contracts=self.rpc.contracts,
            code_hashes=self.rpc.cfg['code_hashes'],bucket=7,accounting_version=6,
            physical_only=kwargs.pop('physical_only',True),**kwargs)
    def override(self,method,*values):
        self.rpc.overrides[self.rpc.contracts['liquidity'],method]=[f'{v:064x}' for v in values]

    def test_consistent_wrong_leg_and_aggregate_amounts_are_rejected(self):
        self.override('amounts(uint256)',100,200)
        self.override('portfolioAmounts(uint256)',200,400)
        with self.assertRaisesRegex(ValueError,'physical principal'):
            self.read()

    def test_nonzero_but_wrong_stable_fingerprint_is_rejected(self):
        self.override('portfolioFingerprint(uint256)',202)
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            self.read()

    def test_noncontained_residual_is_rejected_even_with_matching_amounts(self):
        self.rpc.aux_ticks=(110,200)
        with self.assertRaisesRegex(ValueError,'contain'):
            self.read()

    def test_wrong_liquidity_sensitive_fingerprint_is_rejected(self):
        self.override('executionPortfolioFingerprint(uint256)',303)
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            self.read()

    def test_opposite_per_leg_errors_cannot_cancel_in_the_total(self):
        original=self.rpc.read
        def read(target,method,*args,count=1):
            result=original(target,method,*args,count=count)
            if target==self.rpc.contracts['liquidity'] and method=='amounts(uint256)':
                amounts=[int(w,16) for w in result]
                amounts[0]+=1 if args==(123,) else -1
                return [f'{v:064x}' for v in amounts]
            return result
        self.rpc.read=read
        with self.assertRaisesRegex(ValueError,'physical principal'):
            self.read()

    def test_mixed_and_converted_residuals_stay_included_with_pending_off_mode(self):
        self.rpc.mode=0;self.rpc.geometry=1;self.rpc.applied=0
        for tick in (-200,-100,19,20,50,79,80,100,200):
            with self.subTest(tick=tick):
                self.rpc.tick=tick
                result=self.read()
                self.assertEqual(124,result['secondary_id']);self.assertEqual(2,len(result['physical_legs']))
                self.assertFalse(result['desired_residual_enabled']);self.assertTrue(result['portfolio_configuration_pending'])
                self.assertNotIn('allowed',result)

    def test_single_main_and_enabled_without_useful_residual_are_valid(self):
        self.rpc.secondary=0;self.rpc.secondary_count=0;self.rpc.mode=1
        result=self.read()
        self.assertEqual(0,result['secondary_id']);self.assertEqual(1,len(result['physical_legs']))
        self.assertTrue(result['desired_residual_enabled'])

    def test_main_growth_changes_execution_identity_not_stable_geometry(self):
        before=self.read();target=self.rpc.posm
        self.rpc.overrides[target,'getPositionLiquidity(uint256)']=[f'{900:064x}']
        after=self.read()
        self.assertEqual(before['portfolio_fingerprint'],after['portfolio_fingerprint'])
        self.assertNotEqual(before['execution_portfolio_fingerprint'],after['execution_portfolio_fingerprint'])

    def test_existing_claim_read_does_not_add_reference_or_usd_calls(self):
        target=self.rpc.contracts['rebalance_confirmation']
        self.rpc.overrides[target,'marketSides(uint256)']=ValueError('optional reference unavailable')
        result=self.read()
        self.assertEqual('physical_portfolio_not_maintenance_eligibility',result['scope'])
        self.assertFalse(any(method=='marketSides(uint256)' for _,method,_ in self.rpc.calls))

    def test_neutral_math_preserves_preflight_and_historical_floor_results(self):
        for ticks in ([-887272,887272],[-100,100],[-100,-10],[10,100]):
            for price in (MIN_SQRT,MAX_SQRT-1,sqrt_price_at_tick(ticks[0]),sqrt_price_at_tick(ticks[1]-1),1<<96):
                for liquidity in (1,500,10**18,(1<<128)-1):
                    with self.subTest(ticks=ticks,price=price,liquidity=liquidity):
                        result=physical_amounts(price,ticks,liquidity)
                        self.assertEqual(historical_amounts(price,ticks,liquidity),result)
                        self.assertEqual(preflight_amounts(price,ticks,liquidity),result)
        # Independent integer floor vectors at Q96, symmetric stored tick bounds.
        a,b=sqrt_price_at_tick(-100),sqrt_price_at_tick(100);liquidity=10**18;q96=1<<96
        self.assertEqual([liquidity*(b-q96)//b,liquidity*(q96-a)//q96],physical_amounts(q96,[-100,100],liquidity))

    def test_typed_fingerprint_preserves_complete_info_and_rejects_aliases(self):
        args=dict(executor=self.rpc.contracts['lp_position_executor'],position_manager=self.rpc.posm,
            vault=self.rpc.contracts['vault'],pool=self.rpc.pool,main=(123,5,500),secondary=(124,7,900))
        first=portfolio_fingerprints(**args)
        args['main']=(123,5,501);second=portfolio_fingerprints(**args)
        self.assertEqual(first[0],second[0]);self.assertNotEqual(first[1],second[1])
        args['main']=(123,4,501);self.assertNotEqual(second[0],portfolio_fingerprints(**args)[0])
        args['secondary']=(123,7,900)
        with self.assertRaises(ValueError):portfolio_fingerprints(**args)

    def context(self):
        from frontend_api.portfolio_v6 import contribution_context
        from frontend_api.service import Contract
        from tests_python.test_keeper_compound_range_policy import words
        self.rpc.tick=90;self.rpc.position[6]=self.rpc.now-3600
        c=self.rpc.contracts
        for method,values in (('RANGE_POLICY_VERSION()',(1,)),('keeperRangePolicy(bytes32)',(0,0,0,0,0,0,0)),
                ('keeperRangeTarget(bytes32)',(0,)),('validatePrice(bytes32)',(sqrt_price_at_tick(90),))):
            self.rpc.overrides[c['strategy'],method]=words(*values)
        pins={**c,'budget':self.rpc.budget,'position_manager':self.rpc.posm,'permit2':'0x'+'d3'*20}
        calls=[];block={'blockHash':'0x'+'ab'*32,'requireCanonical':True}
        def call(target,method,*args,block,words=1):
            self.assertEqual({'blockHash':'0x'+'ab'*32,'requireCanonical':True},block)
            calls.append((target,method,args));return self.rpc.read(target,method,*args,count=words)
        def rpc_call(method,params):
            self.assertEqual('eth_getCode',method);self.assertEqual(block,params[1]);return self.rpc.code(params[0])
        p=SimpleNamespace(contracts={role:Contract(target,self.rpc.pin) for role,target in pins.items()},
            _call=call,rpc=SimpleNamespace(call=rpc_call))
        intended=dict(orientation=1,keeper=dict(enabled=False,narrow_trigger_bps=0,widen_trigger_bps=0,
            minimum_interval_seconds=0,configuration_hash='0x'+'00'*32,review_hash='0x'+'00'*32))
        result=contribution_context(p,pins,self.rpc.pool,7,words(*self.rpc.position),words(*self.rpc.config),
            {'timestamp':self.rpc.now},block,range_policy_version=1,range_policy=intended,
            maintenance_policy_version=3,rebalance_confirmation_version=3)
        return result,calls

    def test_contribution_context_reuses_one_verified_execution_hash(self):
        result,calls=self.context()
        self.assertEqual(1,sum(method=='executionPortfolioFingerprint(uint256)' for _,method,_ in calls))
        self.assertEqual(2,len(result['portfolio']['physical_legs']))
        self.assertIsNotNone(result['portfolio']['execution_portfolio_fingerprint'])

    def test_contribution_context_rejects_wrong_execution_hash(self):
        from frontend_api.service import ProjectionError
        self.override('executionPortfolioFingerprint(uint256)',303)
        with self.assertRaises(ProjectionError):self.context()


if __name__=='__main__':unittest.main()
