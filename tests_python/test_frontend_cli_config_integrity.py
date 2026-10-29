"""CLI JSON review integrity, before workers, RPC or listeners can be created."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from frontend_api import activation, activation_server, server


class FrontendCLIConfigIntegrityTest(unittest.TestCase):
    def invoke(self, kind, documents):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            argv = [kind]
            for flag, raw in documents:
                path = Path(temporary) / (flag.removeprefix('--') + '.json')
                path.write_text(raw, encoding='utf-8')
                argv.extend((flag, str(path)))
            stack.enter_context(patch('sys.argv', argv))
            stdout, stderr = io.StringIO(), io.StringIO()
            stack.enter_context(redirect_stdout(stdout))
            stack.enter_context(redirect_stderr(stderr))
            workers = stack.enter_context(patch('frontend_api.worker.WorkerPool'))
            workers.return_value.chain = 31337
            projection = stack.enter_context(patch('frontend_api.service.Projection'))
            transactions = stack.enter_context(patch.object(activation, 'ActivationTransactions'))
            transactions.return_value.prepare.return_value = {'prepared': True}
            read_server = stack.enter_context(patch.object(server, 'ReadServer'))
            activation_listener = stack.enter_context(patch.object(activation_server, 'ReadServer'))
            status = None
            try:
                {'read': server.main, 'activation-server': activation_server.main,
                 'activation-cli': activation.main}[kind]()
            except SystemExit as exc:
                status = exc.code
            return dict(status=status, stdout=stdout.getvalue(), stderr=stderr.getvalue(),
                        workers=workers, projection=projection, transactions=transactions,
                        listeners=(read_server, activation_listener))

    @staticmethod
    def documents(kind):
        flags = {'read': ('--config', '--transaction-config'),
                 'activation-server': ('--config', '--activation-config'),
                 'activation-cli': ('--config', '--activation-config', '--request')}[kind]
        return [(flag, '{"label":"Café λ","ratio":1.25}') for flag in flags]

    def assert_rejected_before_work(self, kind):
        invalid = ('{"chain_id":31337,"chain_id":4663}',
                   '{"policy":{"amount":"100","amount":"10000"}}',
                   '{"secret_endpoint":"https://user:secret@example.invalid","value":NaN}',
                   '{"value":Infinity}', '{"value":-Infinity}', '{"value":1e999}',
                   '[]', 'null', 'true', '7', '"text"')
        for position in range(len(self.documents(kind))):
            for raw in invalid:
                with self.subTest(kind=kind, position=position, raw=raw):
                    documents = self.documents(kind)
                    documents[position] = (documents[position][0], raw)
                    result = self.invoke(kind, documents)
                    self.assertEqual(result['status'], 1)
                    result['workers'].assert_not_called()
                    result['projection'].assert_not_called()
                    result['transactions'].assert_not_called()
                    for listener in result['listeners']:
                        listener.assert_not_called()
                    self.assertNotIn('secret', result['stderr'])
                    self.assertNotIn('example.invalid', result['stderr'])
                    self.assertEqual(result['stdout'], '')

    def test_read_cli_rejects_ambiguous_objects_before_worker_creation(self):
        self.assert_rejected_before_work('read')

    def test_activation_server_rejects_all_inputs_before_worker_creation(self):
        self.assert_rejected_before_work('activation-server')

    def test_activation_cli_rejects_request_before_projection_creation(self):
        self.assert_rejected_before_work('activation-cli')

    def test_valid_utf8_objects_retain_finite_values_and_reach_existing_validators(self):
        expected = {'label': 'Café λ', 'ratio': 1.25}
        for kind in ('read', 'activation-server', 'activation-cli'):
            with self.subTest(kind=kind):
                result = self.invoke(kind, self.documents(kind))
                self.assertIsNone(result['status'])
                if kind == 'read':
                    result['workers'].assert_called_once_with(expected, transaction_config=expected, workers=4)
                elif kind == 'activation-server':
                    result['workers'].assert_called_once_with(expected, expected, workers=4)
                else:
                    result['projection'].assert_called_once_with(expected)
                    result['transactions'].assert_called_once_with(result['projection'].return_value, expected)
                    result['transactions'].return_value.prepare.assert_called_once_with(expected)
                    self.assertEqual(json.loads(result['stdout']), {'prepared': True})


if __name__ == '__main__':
    unittest.main()
