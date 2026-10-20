import unittest
from unittest.mock import Mock
from scripts.local_clock import LocalChainClock
from zzz_ops.work_budget import Budget
from zzz_ops.errors import WorkLimit


class LocalClockTests(unittest.TestCase):
    def test_checkpoints_advance_without_network_reads(self):
        now=[0.0];read=Mock(return_value=1000)
        clock=LocalChainClock(read,lambda:now[0]);clock.refresh()
        budget=Budget(seconds=25,clock=lambda:now[0]);budget.expire_at(1010,clock)
        for _ in range(2000):budget.check()
        read.assert_called_once()
        now[0]=10
        with self.assertRaises(WorkLimit):budget.check()

    def test_explicit_resampling_observes_chain_time_jump(self):
        now=[0];read=Mock(side_effect=[1000,2000])
        clock=LocalChainClock(read,lambda:now[0]);clock.refresh()
        budget=Budget(seconds=25,clock=lambda:now[0]);budget.expire_at(1010,clock)
        clock.refresh()
        with self.assertRaises(WorkLimit):budget.check()

    def test_uninitialized_failed_or_invalid_samples_fail(self):
        for invalid in [True,-1,'1000',None]:
            clock=LocalChainClock(lambda:invalid)
            with self.assertRaises(RuntimeError):clock()
            with self.assertRaises(ValueError):clock.refresh()
        read=Mock(side_effect=OSError('offline'));clock=LocalChainClock(read)
        with self.assertRaises(OSError):clock.refresh()

    def test_projection_samples_at_each_freshness_boundary(self):
        import importlib.util
        from pathlib import Path
        spec=importlib.util.spec_from_file_location('clock_lab',Path(__file__).resolve().parents[1]/'scripts/local-stack.py')
        lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
        p=object.__new__(lab.LocalProjection);read=Mock(side_effect=[1000,1201])
        p.clock=LocalChainClock(read,lambda:0);p.max_age=120
        p._fresh({'timestamp':1000})
        with self.assertRaises(lab.ProjectionError):p._fresh({'timestamp':1000})
        self.assertEqual(read.call_count,2)


if __name__=='__main__':unittest.main()
