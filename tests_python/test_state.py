import json
import os
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
    def test_stale_predictable_temporary_file_is_never_clobbered(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';stale=Path(d)/'state.json.tmp'
            stale.write_text('leave untouched');atomic_json(p,{'pending':7})
            self.assertEqual(stale.read_text(),'leave untouched')
            self.assertEqual(read_json(p),{'pending':7})
            self.assertFalse(list(Path(d).glob('.state.json.*.tmp')))
    def test_predictable_temp_hardlink_cannot_overwrite_another_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';victim=Path(d)/'unrelated'
            victim.write_text('retain original');os.link(victim,Path(d)/'state.json.tmp')
            atomic_json(p,{'pending':7})
            self.assertEqual(victim.read_text(),'retain original')
            self.assertEqual(read_json(p),{'pending':7})
    @unittest.skipUnless(os.name=='posix','Unix symlink/permission semantics required')
    def test_predictable_temp_symlink_cannot_overwrite_another_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';victim=Path(d)/'unrelated'
            victim.write_text('retain original');(Path(d)/'state.json.tmp').symlink_to(victim)
            atomic_json(p,{'pending':7})
            self.assertEqual(victim.read_text(),'retain original')
            self.assertEqual(p.stat().st_mode&0o777,0o600)
    def test_serialization_failure_retains_previous_state_and_removes_exclusive_temp(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';atomic_json(p,{'pending':7})
            with self.assertRaises(TypeError):atomic_json(p,{'invalid':object()})
            self.assertEqual(read_json(p),{'pending':7})
            self.assertFalse(list(Path(d).glob('.state.json.*.tmp')))
