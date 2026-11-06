"""Current-profile lifecycle reads across canonical synthetic snapshots.

Actual Projection code runs; these transcripts do not simulate markets, sign,
operate a service, or establish compatibility of an existing deployed runtime.
"""
import unittest

from frontend_api.service import Projection, ProjectionError
from tests_python.test_frontend_policy_v6 import FrontendPolicyV6Tests
from zzz_ops.rpc import RpcError
from zzz_ops.tick_math import sqrt_price_at_tick
from zzz_ops.production_v5 import physical_amounts as expected_amounts


class MarketLifecycleProjectionTests(unittest.TestCase):
    def setUp(self):
        fixture = FrontendPolicyV6Tests("runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.config, self.rpc, self.q, self.c = fixture.config, fixture.rpc, fixture.q, fixture.c
        self.config["custody_version"] = 5
        self.rpc.put(self.c["principal_exit"], "CUSTODY_VERSION()", values=(5,))
        self.p = Projection(self.config, self.rpc, clock=lambda: 1000)

    def read(self, step):
        self.rpc.hash = "0x" + f"{step:064x}"
        return self.p.nft(self.rpc.nft_id)

    def test_current_projection_tracks_single_dual_pending_disable_and_residual_close(self):
        # Canonical synthetic snapshots for one long-lived reader, not an EVM
        # execution/LP-ID-allocation history. Raw amounts follow actual ticks/L.
        phases = ((0,0,0,500000,0,0),(1,124,0,500000,1,1),
                  (0,124,50,550000,2,1),(0,0,50,550000,2,1))
        residual_close=None
        for step, (mode, aux, tick, main_liquidity,geometry,applied) in enumerate(phases, 200):
            with self.subTest(step=step):
                self.q.mode = mode
                self.q.secondary, self.q.secondary_count = aux, int(bool(aux))
                self.q.tick=tick;self.q.physical_liquidities={123:main_liquidity,124:500000 if aux else 0}
                main=expected_amounts(sqrt_price_at_tick(tick),[self.q.lower,self.q.upper],main_liquidity)
                auxiliary=expected_amounts(sqrt_price_at_tick(tick),list(self.q.aux_ticks),500000) if aux else [0,0]
                aggregate=[a+b for a,b in zip(main,auxiliary)]
                if step==202:residual_close=auxiliary
                if step==203:self.q.position[2:4]=residual_close
                # Residual-only close preserves main/applied policy. Desired
                # modeOFF therefore remains pending until whole replacement.
                self.q.geometry,self.q.applied=geometry,applied
                value = self.read(step)
                portfolio = value["position"]["local_custody"]["portfolio"]
                self.assertEqual(bool(mode), portfolio["desired_residual_enabled"])
                self.assertEqual(str(aux) if aux else None, portfolio["secondary_lp_token_id"])
                self.assertEqual(list(map(str, aggregate)), portfolio["principal_amounts_raw"])
                self.assertEqual(geometry!=applied,portfolio['configuration_pending'])
                self.assertEqual(2 if aux else 1, len(portfolio["physical_legs"]))
                self.assertEqual("17", value["claimable"]["lp"][0]["raw"])
                self.assertEqual("33333333333333333333", value["claimable"]["royalties"][0]["raw"])

    def test_reference_outage_and_recovery_preserve_dual_custody_and_raw_claims(self):
        self.q.secondary, self.q.secondary_count = 124, 1
        self.q.overrides[self.c["rebalance_confirmation"], "marketSides(uint256)"] = RpcError("synthetic feed outage")
        failed = self.read(210)
        self.assertFalse(failed["position"]["current_lp_value"]["available"])
        self.assertEqual("124", failed["position"]["local_custody"]["portfolio"]["secondary_lp_token_id"])
        self.rpc.put(self.c["nft"], "currentLPValue(uint256)", (self.rpc.nft_id,), (1, 1500 * 10**18))
        del self.q.overrides[self.c["rebalance_confirmation"], "marketSides(uint256)"]
        recovered = self.read(211)
        self.assertTrue(recovered["position"]["current_lp_value"]["available"])
        self.assertEqual(failed["claimable"], recovered["claimable"])

    def test_missing_residual_after_healthy_read_never_reuses_previous_backing(self):
        self.q.secondary, self.q.secondary_count = 124, 1
        self.read(220)
        self.q.fail_leg_owner = True
        with self.assertRaises(ProjectionError):
            self.read(221)
        self.q.fail_leg_owner = False
        recovered = self.read(222)
        self.assertEqual("124", recovered["position"]["local_custody"]["portfolio"]["secondary_lp_token_id"])

    def test_inconsistent_residual_inventory_cannot_become_an_empty_single_position(self):
        self.q.secondary, self.q.secondary_count = 124, 1
        self.read(230)
        stale=self.q.read(self.c['liquidity'],'portfolioAmounts(uint256)',123,count=2)
        self.q.secondary = 0  # one getter drops the residual while total remains stale
        self.q.overrides[self.c['liquidity'],'portfolioAmounts(uint256)']=stale
        with self.assertRaises(ProjectionError):
            self.read(231)
        self.q.secondary_count = 0
        del self.q.overrides[self.c['liquidity'],'portfolioAmounts(uint256)']
        result = self.read(232)
        self.assertIsNone(result["position"]["local_custody"]["portfolio"]["secondary_lp_token_id"])
