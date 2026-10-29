"""Final-depth keeper diagnostics with inert pinned RPCs, never signing."""
import copy
import datetime as dt
import json
import unittest
from unittest.mock import patch

from tests_python import test_keeper_execution_telemetry as fixtures


class KeeperTelemetryCompletionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.KeeperExecutionTelemetryTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.k, self.rpc = self.fixture.k, self.fixture.rpc
        self.previous = self.fixture._observe()['last_confirmed']

    def final_head(self, value):
        original = self.rpc.call
        count = 0
        def call(method, params):
            nonlocal count
            if method == 'eth_getBlockByNumber' and params[0] == 'latest':
                count += 1
                if count == 2:
                    return copy.deepcopy(value)
            return original(method, params)
        return patch.object(self.rpc, 'call', side_effect=call)

    def assert_unavailable(self):
        record = self.fixture._observe()
        self.assertEqual('unavailable', record['state'])
        self.assertEqual(self.previous, record['last_confirmed'])
        self.assertIsNotNone(record['last_error'])

    def test_advancing_head_exports_actual_final_depth_without_mutating_the_journal(self):
        before = copy.deepcopy(self.k.state)
        final = dict(number='0x65', hash='0x'+'66'*32, timestamp=hex(self.rpc.now+1))
        with self.final_head(final):
            report = self.fixture._observe()
        self.assertEqual('observed_this_cycle', report['state'])
        self.assertEqual(101, report['last_confirmed']['head_number'])
        self.assertEqual(99, report['last_confirmed']['block_number'])
        self.assertEqual(before, self.k.state)

    def test_depth_retreat_cannot_relabel_the_old_anchor_as_confirmed(self):
        with self.final_head(self.fixture.confirmed_header):
            self.assert_unavailable()

    def test_same_height_head_reorg_cannot_publish_mixed_observation(self):
        final = dict(number='0x64', hash='0x'+'66'*32, timestamp=hex(self.rpc.now))
        with self.final_head(final):
            self.assert_unavailable()

    def test_malformed_final_heads_fail_closed_with_prior_evidence_retained(self):
        good = dict(number='0x64', hash=self.fixture.latest['blockHash'], timestamp=hex(self.rpc.now))
        for final in (None, {}, {**good, 'number': True}, {**good, 'hash': '0x00'},
                      {key: value for key, value in good.items() if key != 'timestamp'}):
            with self.subTest(final=final), self.final_head(final):
                self.assert_unavailable()

    def test_final_clock_future_stale_or_retreat_is_unavailable(self):
        for stamp in (self.rpc.now+31, self.rpc.now-601, self.rpc.now-1):
            final = dict(number='0x65', hash='0x'+'66'*32, timestamp=hex(stamp))
            with self.subTest(timestamp=stamp), self.final_head(final):
                self.assert_unavailable()

    def test_anchor_reorg_during_observation_is_still_rejected(self):
        original = self.rpc.call
        count = 0
        def call(method, params):
            nonlocal count
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == '0x63':
                count += 1
                if count == 2:
                    return {**result, 'hash': '0x'+'77'*32}
            return result
        with patch.object(self.rpc, 'call', side_effect=call):
            self.assert_unavailable()

    def test_depth_failure_cannot_advance_the_last_successful_cycle(self):
        previous = dt.datetime.fromtimestamp(self.rpc.now-10, dt.timezone.utc).isoformat()
        self.k.last_success_at = previous
        with self.final_head(self.fixture.confirmed_header), \
                patch.object(self.k, 'cycle'), patch('keeper.monitor.time.time', return_value=self.rpc.now), \
                patch('subprocess.run') as signer:
            self.assertFalse(self.k.run_cycle())
        signer.assert_not_called()
        report = json.loads(self.k.health_path.read_text(encoding='utf-8'))
        self.assertEqual('degraded', report['status'])
        self.assertEqual(previous, report['last_success_at'])
        self.assertEqual(self.previous, report['lp_execution_health']['last_confirmed'])


if __name__ == '__main__':
    unittest.main()
