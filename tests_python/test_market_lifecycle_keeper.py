"""Composed source6/custody5 worker decisions, inert RPC and temp journals.

This exercises real worker/read-review code, not a live daemon or EVM keeper.
"""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET
from keeper.operation_review import PinnedReads, Review
from tests_python.test_keeper_compound_range_policy import words
from tests_python.test_keeper_policy_v6 import PolicyRPC
from zzz_ops.position import decode_position
from zzz_ops.rpc import RpcError


class MarketRPC(PolicyRPC):
    def call(self, method, params):
        # The existing eligibility companion reader deliberately requests this
        # preliminary runtime at latest; later physical reads remain hash-pinned.
        if method == "eth_getCode" and params == [self.budget, "latest"]:
            return self.code(self.budget)
        return super().call(method, params)


class MarketLifecycleKeeperTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.rpc = MarketRPC(Path(tmp.name) / "market.json")
        self.rpc.cfg["custody_version"] = 5
        self.rpc.overrides[self.rpc.contracts["principal_exit"], "CUSTODY_VERSION()"] = words(5)
        self.k = Keeper(self.rpc.cfg, rpc=self.rpc)

    def due(self):
        with patch("keeper.monitor.time.time", return_value=self.rpc.now):
            return self.k._compound_due(
                7, [NATIVE_ASSET, self.rpc.zzz], [1, 1],
                {"compound_thresholds": {NATIVE_ASSET: 1, self.rpc.zzz: 1}},
                self.rpc.now, words(*self.rpc.position))

    def test_compound_decisions_follow_mode_threshold_and_range_across_restart(self):
        self.rpc.physical_side = self.rpc.reference = 0
        self.k.save()
        saved = self.k.path.read_bytes()
        self.assertTrue(self.due())
        self.rpc.secondary, self.rpc.secondary_count, self.rpc.summed = 124, 1, (130, 240)
        self.rpc.mode = 1
        self.assertTrue(self.due())
        self.rpc.geometry = 1  # disable is pending: do not compound around merge
        self.rpc.mode = 0
        self.assertFalse(self.due())
        self.rpc.geometry = self.rpc.applied = 0
        self.rpc.physical_side = self.rpc.reference = 2
        self.assertFalse(self.due())
        self.rpc.tick = self.rpc.upper
        self.assertFalse(self.due())
        self.rpc.tick = 0
        self.rpc.physical_side = self.rpc.reference = 0
        self.k = Keeper(self.rpc.cfg, rpc=self.rpc)
        self.assertTrue(self.due())
        self.assertEqual(saved, self.k.path.read_bytes())

    def test_reference_fault_blocks_compound_but_both_leg_harvest_review_survives(self):
        self.rpc.secondary, self.rpc.secondary_count, self.rpc.summed = 124, 1, (130, 240)
        self.rpc.overrides[self.rpc.contracts["rebalance_confirmation"], "marketSides(uint256)"] = RpcError("synthetic reference outage")
        self.k.save()
        saved = self.k.path.read_bytes()
        with self.assertRaises(RpcError):
            self.due()
        header = self.rpc.call("eth_getBlockByNumber", ["latest", False])
        position = decode_position(self.rpc.read(self.rpc.contracts["vault"], "group(uint256)", 7, count=8), 6)
        self.k.rpc = PinnedReads(self.rpc, header)
        with patch("subprocess.run") as signer:
            result = Review(self.k, header, False, simulate=False).harvest_custody(position)
        self.assertTrue(result["allowed"])
        self.assertEqual(2, len(result["physical_legs"]))
        signer.assert_not_called()
        self.assertEqual(saved, self.k.path.read_bytes())

    def test_current_profile_pending_recovery_precedes_broken_fresh_reads(self):
        self.k.state["pending"] = {"key": "rebalance:7", "hash": "0x" + "a1" * 32}
        before = copy.deepcopy(self.k.state)
        with patch.object(self.k, "poll_pending", return_value=True) as recover, \
                patch.object(self.k, "_validate_accounting_version", side_effect=AssertionError("recovery first")), \
                patch("subprocess.run") as signer:
            self.k.cycle()
        recover.assert_called_once()
        signer.assert_not_called()
        self.assertEqual(before, self.k.state)
