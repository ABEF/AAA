"""Untrusted holder-inventory files stay bounded and never become approval.

Only temporary local files/inert RPC fixtures are used. No wallet or real RPC.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python import test_holder_preflight as fixtures

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / 'scripts/inventory-nft-holders.py'
SPEC = importlib.util.spec_from_file_location('holder_inventory_cli_input', SCRIPT_PATH)
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
LIMIT = 2 * 1024 * 1024


class HolderInventoryInputTests(unittest.TestCase):
    def read(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(raw)
            return CLI.read_json(path)

    def main(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(CLI.sys, 'argv', ['inventory-nft-holders.py', *map(str, args)]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = CLI.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_stream_read_is_bounded_before_rejecting_oversized_file(self):
        class LimitedStream(io.BytesIO):
            def read(self, size=-1):
                self.requested = size
                return super().read(size)
        stream = LimitedStream(b' ' * (LIMIT + 128))
        with patch.object(Path, 'open', return_value=stream), \
                patch.object(Path, 'read_bytes', return_value=b'{}') as unbounded:
            with self.assertRaisesRegex(ValueError, 'bound'):
                CLI.read_json('untrusted.json')
            unbounded.assert_not_called()
        self.assertEqual(stream.requested, LIMIT + 1)

    def test_exact_size_limit_and_finite_json_remain_accepted(self):
        head = b'{"chain_id":42,"finite":1.25,"nested":{"ok":true}}'
        self.assertEqual(self.read(head + b' ' * (LIMIT - len(head))),
                         {'chain_id': 42, 'finite': 1.25, 'nested': {'ok': True}})
        with self.assertRaises(ValueError):
            self.read(head + b' ' * (LIMIT + 1 - len(head)))

    def test_duplicate_keys_at_any_depth_are_rejected(self):
        for raw in (b'{"chain_id":1,"chain_id":2}',
                    b'{"source":{"nft":"a","nft":"b"}}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.read(raw)

    def test_nonfinite_constants_and_float_overflow_are_rejected(self):
        for number in ('NaN', 'Infinity', '-Infinity', '1e999', '-1e999'):
            raw = ('{"snapshot":{"value":' + number + '}}').encode()
            with self.subTest(number=number), self.assertRaises(ValueError):
                self.read(raw)

    def test_malformed_and_deep_json_fail_as_validation_errors(self):
        for raw in (b'{', b'\xff', b'[' * 2000 + b'0' + b']' * 2000):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                self.read(raw)

    def test_invalid_scan_input_is_sanitized_without_rpc_or_report(self):
        marker = 'must_not_echo_provider_or_file_content'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            target = Path(directory) / 'report.json'
            path.write_text('{"marker":"' + marker + '","value":NaN}')
            with patch.object(CLI, 'Rpc') as rpc:
                code, out, err = self.main('scan', '--config', path, '--output', target)
                rpc.assert_not_called()
            self.assertEqual(code, 1)
            self.assertFalse(target.exists())
            self.assertEqual(out, '')
            self.assertIn('Inventory failed', err)
            self.assertNotIn(marker, err)

    def test_failed_summary_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            page, target = Path(directory) / 'bad.json', Path(directory) / 'report.json'
            page.write_bytes(b'{')
            target.write_bytes(b'original evidence')
            code, _out, err = self.main('summarize', page, '--output', target)
            self.assertEqual(code, 1)
            self.assertEqual(target.read_bytes(), b'original evidence')
            self.assertIn('Inventory failed', err)

    def test_valid_summary_preserves_exclusive_output_and_nonapproval(self):
        rpc = fixtures.FakeRPC(0)
        page_value = fixtures.scan_page(rpc, rpc.cfg, now=lambda: 1001)
        with tempfile.TemporaryDirectory() as directory:
            page, target = Path(directory) / 'page.json', Path(directory) / 'report.json'
            page.write_text(json.dumps(page_value))
            code, _out, _err = self.main('summarize', page, '--output', target)
            self.assertEqual(code, 0)
            report = json.loads(target.read_text())
            self.assertTrue(report['complete'])
            self.assertFalse(report['release_approved'])
            original = target.read_bytes()
            code, _out, err = self.main('summarize', page, '--output', target)
            self.assertEqual(code, 1)
            self.assertEqual(target.read_bytes(), original)
            self.assertIn('Inventory failed', err)


if __name__ == '__main__':
    unittest.main()
