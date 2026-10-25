"""Actual read-RPC adapter composition for history qualification; no network."""
import copy
import json
import unittest

from frontend_api.history_audit import AuditError, HistoryAudit
from tests_python import test_history_audit as fixture
from tests_python.test_frontend_api import addr
from zzz_ops.rpc import Rpc, RpcError


class OfflineReadTransport(Rpc):
    """Retain Rpc.call chain checks/normalization; replace only HTTP I/O."""

    def __init__(self, source):
        super().__init__(['https://independent.invalid'], 31337, retries=1)
        self.source = source

    def _read_http(self, url, raw):
        request = json.loads(raw)
        result = self.source.call(request['method'], request['params'])
        return json.dumps(dict(jsonrpc='2.0', id=request['id'], result=result)).encode()


class HistoryAuditTransportTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.HistoryAuditTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def audit(self, rpc):
        return HistoryAudit(self.f.cfg, self.f.policy, rpc).run(addr(1), 10, 19)

    def test_actual_rpc_checked_integer_chain_id_can_complete_read_only_audit(self):
        before = self.f.snapshot()
        transport = OfflineReadTransport(self.f.rpc)
        self.assertEqual(transport.call('eth_chainId'), 31337)
        self.assertIs(type(transport.call('eth_chainId')), int)
        result = self.audit(transport)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['local_logs'], 3)
        self.assertEqual(result['local_logs_sha256'], result['rpc_logs_sha256'])
        self.assertEqual(self.f.snapshot(), before)

    def test_canonical_wire_quantity_injected_adapter_remains_supported(self):
        before = self.f.snapshot()
        self.assertEqual(self.f.rpc.call('eth_chainId'), '0x7a69')
        self.assertEqual(self.audit(self.f.rpc)['status'], 'matched')
        self.assertEqual(self.f.snapshot(), before)

    def test_boolean_float_wrong_or_noncanonical_chain_ids_fail_without_database_changes(self):
        before = self.f.snapshot()
        for value in (True, 31337.0, '31337', '0x07a69', '0x0', '0x7a68', -1, None):
            with self.subTest(value=value):
                self.f.rpc.mutate = lambda method, params, result, answer=value: answer if method == 'eth_chainId' else result
                with self.assertRaises((AuditError, RpcError)):
                    self.audit(self.f.rpc)
                self.assertEqual(self.f.snapshot(), before)

    def test_actual_transport_wrong_network_stays_fail_closed_before_history(self):
        before = self.f.snapshot()
        self.f.rpc.mutate = lambda method, params, result: '0x1' if method == 'eth_chainId' else result
        with self.assertRaises(RpcError):
            self.audit(OfflineReadTransport(self.f.rpc))
        self.assertFalse(any(method == 'eth_getLogs' for method, _params in self.f.rpc.calls))
        self.assertEqual(self.f.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
