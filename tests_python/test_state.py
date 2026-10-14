import json
from pathlib import Path
import tempfile
import unittest
from zzz_ops.state import atomic_json,process_lock,read_json

class StateTests(unittest.TestCase):
    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';atomic_json(p,{'n':2**200});self.assertEqual(read_json(p)['n'],2**200)
            self.assertEqual(p.stat().st_mode&0o777,0o600)
    def test_missing_default(self):self.assertEqual(read_json('/missing/does-not-exist.json',{'x':1}),{'x':1})
    def test_malformed_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s';p.write_text('not json')
            with self.assertRaises(json.JSONDecodeError):read_json(p,{})
    def test_concurrent_lock_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with process_lock(Path(d)/'lock'):
                with self.assertRaises(RuntimeError):
                    with process_lock(Path(d)/'lock'):pass
    def test_lock_released(self):
        with tempfile.TemporaryDirectory() as d:
            with process_lock(Path(d)/'lock'):pass
            with process_lock(Path(d)/'lock'):pass
