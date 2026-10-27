"""Independent harvest scheduling boundaries; no chain, signer or fund movement."""
import unittest
from unittest.mock import patch
from tests_python import test_holder_exit_profile as H
from tests_python import test_local_position_services as L


class HourlyHarvestTests(unittest.TestCase):
    def setUp(self):
        self.fixture = H.HolderExitKeeperTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.k = self.fixture.k
        self.base = self.fixture.f.base
        self.base.ids = [7]
        self.base.rebalance = False
        self.k.maintenance = {'harvest': True, 'compound': False}

    def cycle(self, elapsed, *, keeper=None, rpc=None):
        k = keeper or self.k
        clock = rpc or self.fixture.rpc
        k.state['last']['harvest:7'] = clock.now - elapsed
        with patch('keeper.monitor.time.time', side_effect=lambda:clock.now), \
                patch.object(k,'submit',return_value=True) as submit:
            k.cycle()
        return submit

    def test_hour_boundary_harvests_without_any_rebalance(self):
        self.cycle(3599).assert_not_called()
        submitted = self.cycle(3600)
        submitted.assert_called_once_with('vault','collectFees(uint256,uint256)',
            (7,self.fixture.rpc.now+180),'harvest:7')

    def test_explicit_schedule_and_bucket_overrides_keep_precedence(self):
        self.k.maintenance['harvest_interval_seconds'] = 7200
        self.cycle(3600).assert_not_called()
        self.k.overrides = {'7':{'harvest_interval_seconds':3600}}
        submitted = self.cycle(3600)
        self.assertEqual(submitted.call_args.args[1],'collectFees(uint256,uint256)')
        self.k.overrides['7']['harvest'] = False
        self.cycle(14400).assert_not_called()

    def test_historical_omitted_schedule_keeps_its_four_hour_behavior(self):
        f = L.LocalPositionKeeperTests('runTest')
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.base.ids = [7]
        f.base.rebalance = False
        f.k.maintenance = {'harvest': True, 'compound': False}
        self.cycle(3600,keeper=f.k,rpc=f.rpc).assert_not_called()
        submitted = self.cycle(14400,keeper=f.k,rpc=f.rpc)
        self.assertEqual(submitted.call_args.args[1],'collectFees(uint256,uint256)')
