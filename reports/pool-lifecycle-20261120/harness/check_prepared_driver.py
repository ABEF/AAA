"""New offline controls for the prepared report driver; no actual node/RPC."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'reports/recommendations-execution-20261120/pool/run_pool.py'
spec = importlib.util.spec_from_file_location('prepared_pool_driver', SOURCE)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
SOURCE_HASH = hashlib.sha256(SOURCE.read_bytes()).hexdigest()


class FakeProcess:
    pid = 12345
    def __init__(self, timeout=False):
        self.code = None
        self.terminated = False
        self.killed = False
        self.timeout = timeout
    def poll(self):
        return self.code
    def terminate(self):
        self.terminated = True
    def kill(self):
        self.killed = True
        self.timeout = False
    def wait(self, timeout):
        if self.timeout:
            raise subprocess.TimeoutExpired('fake-owned-process', timeout)
        self.code = 0
        return self.code


def bare_node():
    node = driver.Node.__new__(driver.Node)
    node.process = FakeProcess()
    node.deadline = time.monotonic() + 10
    node.port = 1
    node.wire = []
    node.receipts = []
    node.pending = None
    return node


class PreparedDriverControls(unittest.TestCase):
    def test_serialized_capture_survives_later_nested_transaction_mutation(self):
        sent = []
        class Connection:
            def __init__(self, *args, **kwargs):
                pass
            def request(self, method, path, body, headers):
                sent.append(body)
            def getresponse(self):
                body = json.loads(sent[-1])
                class Response:
                    status = 200
                    def read(self, maximum):
                        return json.dumps({'jsonrpc':'2.0','id':body['id'],'result':'0x'}).encode()
                return Response()
            def close(self):
                pass
        node = bare_node()
        tx = {'gas':'0x1e84800', 'accessList':[{'storageKeys':['0x01']}]}
        with patch.object(driver.http.client, 'HTTPConnection', Connection):
            self.assertEqual(node.call('eth_call', [tx, 'latest']), '0x')
        tx['gas'] = '0x1'
        tx['accessList'][0]['storageKeys'].append('0x02')
        captured = node.wire[0]
        self.assertEqual(captured['request'], json.loads(sent[0]))
        self.assertEqual(captured['request']['params'][0]['gas'], '0x1e84800')
        self.assertEqual(captured['request']['params'][0]['accessList'][0]['storageKeys'], ['0x01'])
        self.assertEqual(captured['serialized_request_sha256'], hashlib.sha256(sent[0].encode()).hexdigest())

    def cleanup_case(self, timeout):
        node = bare_node()
        node.process = FakeProcess(timeout)
        node.stdout = io.BytesIO()
        node.stderr = io.BytesIO()
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(driver, 'OUT', Path(temporary)):
                def fail_start():
                    raise RuntimeError('controlled-startup-failure')
                node._start = fail_start
                with self.assertRaisesRegex(RuntimeError, 'controlled-startup-failure'):
                    node.__enter__()
                saved = json.loads((Path(temporary)/'cleanup.json').read_bytes())
                self.assertTrue(saved['owned_node_stopped'])
                self.assertEqual(saved['pid'], node.process.pid)
                self.assertIsNone(saved['pending'])
                self.assertTrue((Path(temporary)/'local-wire.json.gz').is_file())
        self.assertTrue(node.process.terminated)
        self.assertEqual(node.process.killed, timeout)
        self.assertTrue(node.stdout.closed)
        self.assertTrue(node.stderr.closed)

    def test_startup_exception_stops_only_the_owned_process_and_keeps_evidence(self):
        self.cleanup_case(False)

    def test_stubborn_startup_process_is_killed_after_bounded_wait(self):
        self.cleanup_case(True)

    def negative_case(self, selector, used):
        node = bare_node()
        calls = []
        def fake_call(method, params=(), allow_error=False):
            calls.append(method)
            if method == 'eth_getTransactionCount':
                return '0x0'
            if method == 'eth_call':
                return {'error': {'data': selector}}
            if method == 'eth_gasPrice':
                return '0x0'
            if method == 'eth_sendTransaction':
                return '0x' + 'ab' * 32
            if method == 'eth_getTransactionReceipt':
                return {'status':'0x0','gasUsed':hex(used)}
            if method == 'eth_getTransactionByHash':
                return {'input':'0x1234','nonce':'0x0','value':'0x0'}
            raise AssertionError(method)
        node.call = fake_call
        return node, calls

    def test_wrong_revert_selector_refuses_before_any_submission(self):
        node, calls = self.negative_case('0xdeadbeef', 100000)
        with self.assertRaisesRegex(AssertionError, 'liquidity sizing'):
            node.send('new-negative', '0x'+'11'*20, '0x1234', expected_success=False)
        self.assertNotIn('eth_sendTransaction', calls)

    def test_out_of_gas_cannot_count_as_the_expected_liquidity_rejection(self):
        selector = '0x' + driver.keccak256(b'Slippage()')[:4].hex()
        node, calls = self.negative_case(selector, 1000000)
        with self.assertRaisesRegex(AssertionError, 'Out-of-gas'):
            node.send('new-negative', '0x'+'11'*20, '0x1234', expected_success=False)
        self.assertEqual(node.receipts, [])
        self.assertIsNotNone(node.pending)

    def test_intended_failure_is_only_accepted_with_unexhausted_gas(self):
        selector = '0x' + driver.keccak256(b'Slippage()')[:4].hex()
        node, calls = self.negative_case(selector, 900000)
        with contextlib.redirect_stdout(io.StringIO()):
            node.send('new-negative', '0x'+'11'*20, '0x1234', expected_success=False)
        self.assertEqual(len(node.receipts), 1)
        self.assertEqual(node.receipts[0]['padded_gas'], 1000000)
        self.assertIsNone(node.pending)

    def test_local_write_refuses_when_listener_is_not_owned(self):
        node = bare_node()
        node.owner = lambda: set()
        with patch.object(driver.http.client, 'HTTPConnection', side_effect=AssertionError('network must not be reached')) as connection:
            with self.assertRaises(AssertionError):
                node.call('anvil_setBalance', ['0x'+'11'*20, '0x1'])
            connection.assert_not_called()

    def test_unknown_method_refuses_before_transport(self):
        node = bare_node()
        with patch.object(driver.http.client, 'HTTPConnection', side_effect=AssertionError('network must not be reached')) as connection:
            with self.assertRaises(AssertionError):
                node.call('eth_sendRawTransaction', ['0x00'])
            connection.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
