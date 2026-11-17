"""Late advancing-head canonicality; real preparer with injected read-only RPC."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests_python import test_manual_lp_review as fixture
from tests_python import test_parked_manual_lp_review as parked_fixture
from tests_python import test_management_review as management_fixture
from zzz_ops import manual_lp_review as M
from zzz_ops.management_base import ManagementBlocked


class ManualFinalAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = M.offline.Catalog()

    def setUp(self):
        self.f = fixture.ManualLPReviewTests('runTest')
        self.f.catalog = self.catalog
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.transitions = []

    def advance_on_last_head(self, *, reorg):
        rpc = self.f.rpc
        original = rpc.call

        def call(method, params):
            value = original(method, params)
            # Snapshot head, final anchor, _finish head, final head. Earlier
            # pinned reads remain honest; the new fork appears only now.
            if method == 'eth_blockNumber' and rpc.block_reads == 4:
                self.transitions.append(len(rpc.simulations))
                rpc.inner.head = 111
                rpc.extra_headers[111] = ('0x' + 'bc' * 32, 4001)
                if reorg:
                    rpc.extra_headers[110] = ('0x' + 'ab' * 32, 4000)
                return hex(111)
            return value

        rpc.call = call

    def test_advancing_head_reorg_cannot_release_orphaned_final_review(self):
        self.advance_on_last_head(reorg=True)
        with self.assertRaises(M.ManualReadBlocked) as caught:
            self.f.prepare()
        self.assertEqual('final_anchor_changed', caught.exception.manual_code)
        self.assertEqual('final_canonicality', caught.exception.manual_stage)
        self.assertEqual([4], self.transitions)
        self.assertEqual(4, len(self.f.rpc.simulations))
        self.assertEqual(2, len(self.f.rpc.estimates))

    def test_healthy_advancing_head_keeps_frozen_transaction_without_resimulation(self):
        self.advance_on_last_head(reorg=False)
        result = self.f.prepare()
        self.assertEqual([4], self.transitions)
        self.assertEqual(111, result['last_head']['number'])
        self.assertEqual(110, result['final_control_head']['number'])
        self.assertEqual(self.f.rpc.latest_hash, result['final_control_head']['hash'])
        self.assertEqual(4, len(self.f.rpc.simulations))
        self.assertEqual(2, len(self.f.rpc.estimates))
        self.assertEqual(self.f.rpc.simulations[1][0], self.f.rpc.simulations[3][0])
        self.assertEqual(hex(125000), result['transaction']['gas'])
        self.assertEqual('4180', result['arguments']['deadline'])
        self.assertFalse(result['ready_for_submission'])
        self.assertFalse(any('send' in method.lower() for method, _ in self.f.rpc.calls))

    def test_parked_emergency_reorg_uses_the_same_final_anchor_refusal(self):
        self.f = parked_fixture.ParkedManualLPReviewTests('runTest')
        self.f.catalog = self.catalog
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.advance_on_last_head(reorg=True)
        with self.assertRaises(M.ManualReadBlocked) as caught:
            self.f.prepare()
        self.assertEqual('final_anchor_changed', caught.exception.manual_code)
        self.assertEqual('final_canonicality', caught.exception.manual_stage)
        self.assertEqual([4], self.transitions)
        self.assertEqual(4, len(self.f.rpc.simulations))

    def test_reorg_cli_reports_the_cause_without_publishing_an_artifact(self):
        self.advance_on_last_head(reorg=True)
        paths = {key: Path(self.f.tmp.name)/(key+'.json')
                 for key in ('read-config', 'policy', 'selection', 'output')}
        for key, value in (('read-config', self.f.config), ('policy', self.f.policy),
                           ('selection', self.f.request)):
            paths[key].write_bytes(M.offline.render(value))
        actual = M.prepare

        def prepare(config, policy, request):
            return actual(config, policy, request, rpc=self.f.rpc,
                          clock=lambda: self.f.now, catalog=self.catalog)

        stderr, stdout = io.StringIO(), io.StringIO()
        args = [item for key, path in paths.items() for item in ('--'+key, str(path))]
        with patch.object(M, 'prepare', side_effect=prepare), \
                contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
            self.assertEqual(1, M.main(args))
        response = json.loads(stderr.getvalue())
        self.assertEqual('final_anchor_changed', response['reason'])
        self.assertEqual('final_canonicality', response['stage'])
        self.assertFalse(response['output_may_exist'])
        self.assertFalse(response['transaction_submitted'])
        self.assertEqual('', stdout.getvalue())
        self.assertFalse(paths['output'].exists())


class ManagementFinalAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        management_fixture.ManagementReviewTests.setUpClass()

    def setUp(self):
        self.f = management_fixture.ManagementReviewTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.transitions = []

    def test_management_already_rechecks_final_anchor_after_advancing_head(self):
        ManualFinalAnchorTests.advance_on_last_head(self, reorg=True)
        with self.assertRaises(ManagementBlocked) as caught:
            self.f.prepare()
        self.assertEqual('final_anchor_changed', caught.exception.code)
        self.assertEqual('final_canonicality', caught.exception.management_stage)
        self.assertEqual([4], self.transitions)
        self.assertEqual(4, len(self.f.rpc.simulations))

    def test_management_healthy_head_advancement_keeps_original_review(self):
        ManualFinalAnchorTests.advance_on_last_head(self, reorg=False)
        result = self.f.prepare()
        self.assertEqual([4], self.transitions)
        self.assertEqual(111, result['last_head']['number'])
        self.assertEqual(110, result['final_control_head']['number'])
        self.assertEqual(self.f.request, result['original_selection'])
        self.assertEqual(self.f.rpc.simulations[1][0], self.f.rpc.simulations[3][0])
        self.assertEqual(4, len(self.f.rpc.simulations))
        self.assertEqual(2, len(self.f.rpc.estimates))
        self.assertFalse(result['ready_for_submission'])


if __name__ == '__main__':
    unittest.main()
