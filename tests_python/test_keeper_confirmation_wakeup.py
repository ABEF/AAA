"""Outer-loop confirmation deadlines: inert RPC, monotonic time, no signer.

Reproduces a real daemon gap that status/schedule-only tests cannot detect.
"""
import contextlib
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, main
from keeper.rebalance_confirmation import PORTFOLIO_STATE_NAMESPACE
from tests_python.test_keeper_policy_v6 import PolicyRPC
from zzz_ops.rpc import RpcError


class StopLoop(Exception):
    pass


class KeeperConfirmationWakeupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.rpc = PolicyRPC(Path(tmp.name) / "state.json")
        self.rpc.cfg["interval_seconds"] = 240
        self.k = Keeper(self.rpc.cfg, rpc=self.rpc)
        self.now = self.rpc.now
        self.mono = 1000.0

    def schedule(self, *, next_in=240, execute_in=0):
        self.k.state[PORTFOLIO_STATE_NAMESPACE] = {"7": dict(
            identity="0x" + "12" * 32, observed_at=self.now,
            last_checked_at=self.now, next_check_at=self.now + next_in,
            execute_after=self.now + execute_in if execute_in else 0)}

    def head(self):
        with patch("keeper.monitor.time.time", return_value=self.now), \
                patch("keeper.monitor.time.monotonic", return_value=self.mono):
            self.k._head()

    def delay(self, mono=None):
        with patch("keeper.monitor.time.monotonic", return_value=self.mono if mono is None else mono):
            return self.k.poll_delay(240)

    def test_outer_sleep_honors_ten_minute_maturity_before_next_four_minute_check(self):
        self.schedule(next_in=120)
        self.head()
        self.assertEqual(120, self.delay())

    def test_outer_sleep_honors_short_jitter_and_does_not_redraw_it(self):
        self.schedule(execute_in=60)
        self.head()
        before = copy.deepcopy(self.k.state)
        with patch("keeper.monitor.secrets.randbelow") as random:
            self.assertEqual(60, self.delay())
        random.assert_not_called()
        self.assertEqual(before, self.k.state)

    def test_time_spent_after_last_head_is_removed_from_remaining_sleep(self):
        self.schedule()
        self.head()
        self.assertEqual(150, self.delay(self.mono + 90))

    def test_fractional_clock_rounds_to_one_second_timer_granularity(self):
        self.schedule(next_in=120)
        self.head()
        self.assertEqual(120, self.delay(self.mono + 0.1))

    def test_overdue_candidate_uses_bounded_retry_instead_of_busy_spin(self):
        self.schedule(next_in=60)
        self.head()
        self.assertEqual(60, self.delay(self.mono + 120))

    def test_pending_receipt_and_global_failure_keep_recovery_polling_and_backoff(self):
        self.schedule(execute_in=60)
        self.head()
        self.k.state["pending"] = {"key": "saved"}
        self.assertEqual(240, self.delay())
        self.k.state["pending"] = None
        self.k._cycle_error = True
        self.k.cycle_failures = 2
        self.assertEqual(960, self.delay())

    def test_earliest_of_multiple_buckets_and_stale_300_second_records_is_used(self):
        self.schedule(next_in=240)
        second = dict(self.k.state[PORTFOLIO_STATE_NAMESPACE]["7"], next_check_at=self.now + 30)
        self.k.state[PORTFOLIO_STATE_NAMESPACE]["8"] = second
        self.head()
        self.assertEqual(30, self.delay())
        self.k.state[PORTFOLIO_STATE_NAMESPACE].pop("8")
        self.k.state[PORTFOLIO_STATE_NAMESPACE]["7"]["next_check_at"] = self.now + 300
        self.assertEqual(240, self.delay())

    def test_missing_expired_or_retreating_runtime_clock_never_guesses_chain_time(self):
        self.schedule(execute_in=60)
        self.assertEqual(240, self.delay())
        self.head()
        for mono in (self.mono - 1, self.mono + 601):
            with self.subTest(monotonic=mono):
                self.assertEqual(240, self.delay(mono))

    def test_restart_does_not_reuse_a_persisted_local_clock_or_change_journal(self):
        self.schedule(execute_in=60)
        self.head()
        self.k.save()
        saved = self.k.path.read_bytes()
        self.k = Keeper(self.rpc.cfg, rpc=self.rpc)
        self.assertEqual(240, self.delay())
        self.head()
        self.assertEqual(60, self.delay())
        self.assertEqual(saved, self.k.path.read_bytes())

    def test_invalid_new_head_cannot_replace_last_valid_scheduling_anchor(self):
        self.schedule(execute_in=60)
        self.head()
        original = self.rpc.call
        def fault(method, params):
            if method == "eth_getBlockByNumber":
                return {"number": "0x64", "hash": "invalid", "timestamp": hex(self.now + 100)}
            return original(method, params)
        with patch.object(self.rpc, "call", side_effect=fault), self.assertRaises(RpcError):
            self.head()
        self.assertEqual(60, self.delay())

    def daemon_sleep(self, pulse_seconds=0):
        self.schedule(execute_in=60)
        self.head()
        config = self.k.path.with_name("config.json")
        config.write_text(json.dumps(self.rpc.cfg))
        forced = 0
        clock = [self.mono]
        def pulse(*, force=False):
            nonlocal forced
            if force:
                forced += 1
                if forced == 5:
                    raise StopLoop()
            else:clock[0] += pulse_seconds
        def sleeping(seconds):clock[0] += seconds
        with patch("sys.argv", ["keeper.monitor", "--config", str(config)]), \
                patch("keeper.monitor.signal.signal"), \
                patch("keeper.monitor.process_lock", return_value=contextlib.nullcontext()), \
                patch("keeper.monitor.ProgressWatchdog.from_environment", return_value=SimpleNamespace(enabled=False, pulse=pulse)), \
                patch("keeper.monitor.Keeper", return_value=self.k), \
                patch.object(self.k, "run_cycle", return_value=True), \
                patch("keeper.monitor.time.monotonic", side_effect=lambda:clock[0]), \
                patch("keeper.monitor.time.sleep",side_effect=sleeping) as sleep, self.assertRaises(StopLoop):
            main()
        return sleep, clock[0]-self.mono

    def test_actual_daemon_sleep_uses_deadline_instead_of_full_interval(self):
        sleep,elapsed = self.daemon_sleep()
        self.assertEqual(60, sleep.call_count)
        self.assertEqual(60, elapsed)

    def test_watchdog_work_does_not_accumulate_into_the_entire_sleep_interval(self):
        sleep,elapsed = self.daemon_sleep(pulse_seconds=2)
        self.assertLessEqual(elapsed,62)
        self.assertLess(sleep.call_count,60)
