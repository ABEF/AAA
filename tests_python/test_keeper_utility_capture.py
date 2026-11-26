"""NEW utility integration checks; no SSH, staging initialization or old tests."""
import ast
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from keeper import staging
from zzz_ops.read_process import ReadProcessError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('utility_monitor', ROOT / 'scripts/check-staging-monitor.py')
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


class KeeperUtilityCaptureTests(unittest.TestCase):
    def test_staging_wallet_commands_use_reviewed_cast_capture_and_original_deadlines(self):
        # Statically review the initializer's secret-bearing calls. Invoking the
        # initializer would create a signer and fixture, outside these checks.
        tree = ast.parse(Path(staging.__file__).read_text())
        captures = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == 'run_cast']
        self.assertEqual(len(captures), 2)
        self.assertEqual([next(k.value.value for k in node.keywords if k.arg == 'timeout')
                          for node in captures], [60, 30])
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                             and isinstance(node.func.value, ast.Name)
                             and node.func.value.id == 'subprocess' for node in ast.walk(tree)))
        self.assertIs(staging.run_cast, __import__('keeper.cast_process', fromlist=['run_cast']).run_cast)

    def invoke(self, result=None, error=None):
        with tempfile.TemporaryDirectory() as directory:
            argv = ['check-staging-monitor.py', '--key', str(Path(directory) / 'PRIVATE-KEY'),
                    '--known-hosts', str(Path(directory) / 'hosts'),
                    '--backup-directory', str(Path(directory) / 'backups'), '--ssh', 'reviewed-ssh']
            output = io.StringIO()
            with patch('sys.argv', argv), patch('sys.stdout', output), \
                    patch.object(MONITOR, 'run_read_process', return_value=result, side_effect=error) as run:
                code = MONITOR.main()
            return code, json.loads(output.getvalue()), run.call_args

    def test_monitor_retains_exact_forced_account_and_thirty_second_deadline(self):
        with patch.object(MONITOR, 'validate_export', return_value=({'ok': True}, None)):
            code, report, call = self.invoke(subprocess.CompletedProcess([], 0, b'{}', b''))
        self.assertEqual((code, report['ok']), (0, True))
        command = call.args[0]
        self.assertEqual(command[-2:], ['zzz-stage-monitor@46.225.185.212', 'status'])
        self.assertEqual(command[0], 'reviewed-ssh')
        self.assertEqual(call.kwargs, {'timeout': 30})
        for option in ('BatchMode=yes', 'IdentitiesOnly=yes', 'StrictHostKeyChecking=yes'):
            self.assertIn(option, command)

    def test_monitor_capture_failure_exports_no_secret_or_partial_snapshot(self):
        code, report, _call = self.invoke(error=ReadProcessError('Read-only process output exceeded byte limit'))
        self.assertEqual((code, report['ok'], report['reasons']), (1, False, ['monitor_unavailable']))
        self.assertNotIn('PRIVATE-KEY', json.dumps(report))
        self.assertNotIn('offhost_snapshot_sha256', report)

    def test_nonzero_monitor_exit_fails_before_parsing_or_backup(self):
        with patch.object(MONITOR, 'validate_export') as validate:
            code, report, _call = self.invoke(subprocess.CompletedProcess([], 7, b'{}', b'PRIVATE-CHILD-OUTPUT'))
        validate.assert_not_called()
        self.assertEqual((code, report['ok']), (1, False))
        self.assertNotIn('PRIVATE-CHILD-OUTPUT', json.dumps(report))
