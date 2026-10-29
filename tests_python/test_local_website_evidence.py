"""Evidence admission checks only; no local server or transaction is contacted."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


ROOT=Path(__file__).resolve().parents[1]


class LocalWebsiteEvidenceTests(unittest.TestCase):
    def setUp(self):
        source=Path(os.environ.get('POPL_EVIDENCE_SCRIPT',ROOT/'scripts/verify-local-website.py'))
        spec=importlib.util.spec_from_file_location('local_website_evidence_subject',source)
        self.subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.subject)
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.output=Path(self.directory.name)/'receipt.json'

    def run_subject(self):
        with patch.object(sys,'argv',['verify-local-website.py','--port','8890','--output',str(self.output)]), \
                patch('sys.stdout',new=io.StringIO()):
            self.subject.main()

    def test_existing_evidence_is_refused_before_any_request(self):
        original=b'{"status":"passed","original":true}\n'
        self.output.write_bytes(original)
        with patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(FileExistsError):self.run_subject()
        request.assert_not_called();self.assertEqual(self.output.read_bytes(),original)

    def test_existing_directory_is_refused_before_any_request(self):
        self.output.mkdir()
        with patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(OSError):self.run_subject()
        request.assert_not_called();self.assertTrue(self.output.is_dir())

    def test_missing_parent_is_refused_before_any_request(self):
        self.output=self.output.parent/'missing'/'receipt.json'
        with patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(FileNotFoundError):self.run_subject()
        request.assert_not_called();self.assertFalse(self.output.exists())

    def test_competing_writer_at_reservation_is_not_overwritten(self):
        real_open=Path.open;original=b'{"status":"other_campaign"}\n'
        def race(path,*args,**kwargs):
            if path==self.output and args and args[0]=='x':
                with real_open(path,'wb') as handle:handle.write(original)
            return real_open(path,*args,**kwargs)
        with patch.object(Path,'open',race),patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(FileExistsError):self.run_subject()
        request.assert_not_called();self.assertEqual(self.output.read_bytes(),original)

    def test_dangling_symlink_is_refused_without_creating_target(self):
        target=self.output.parent/'missing-target.json'
        try:self.output.symlink_to(target)
        except (OSError,NotImplementedError):self.skipTest('Host does not permit creating a symbolic link')
        with patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(FileExistsError):self.run_subject()
        request.assert_not_called();self.assertTrue(self.output.is_symlink());self.assertFalse(target.exists())

    def test_initial_marker_precedes_request_and_failure_evidence_survives(self):
        def fail(request,**kwargs):
            self.assertEqual(json.loads(self.output.read_text())['status'],'in_progress')
            self.assertEqual(request.full_url,'http://127.0.0.1:8890/session')
            raise urllib.error.URLError('isolated unavailable fixture')
        with patch.object(self.subject.urllib.request,'urlopen',side_effect=fail) as request:
            with self.assertRaises(urllib.error.URLError):self.run_subject()
        self.assertEqual(request.call_count,1)
        record=json.loads(self.output.read_text())
        self.assertEqual(record['status'],'failed');self.assertEqual(record['operations'],[])
        self.assertIn('isolated unavailable fixture',record['error'])

    def test_interruption_never_becomes_a_passing_record_or_a_retry(self):
        with patch.object(self.subject.urllib.request,'urlopen',side_effect=KeyboardInterrupt) as request:
            with self.assertRaises(KeyboardInterrupt):self.run_subject()
        self.assertEqual(request.call_count,1)
        record=json.loads(self.output.read_text())
        self.assertEqual(record['status'],'in_progress');self.assertEqual(record['operations'],[])

    def test_initial_storage_failure_prevents_all_http_and_closes_file(self):
        opened=[];real_open=Path.open
        def capture(path,*args,**kwargs):
            handle=real_open(path,*args,**kwargs)
            if path==self.output:opened.append(handle)
            return handle
        with patch.object(Path,'open',capture),patch.object(self.subject.os,'fsync',side_effect=OSError('storage unavailable')), \
                patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(OSError):self.run_subject()
        request.assert_not_called();self.assertTrue(opened);self.assertTrue(all(h.closed for h in opened))


if __name__=='__main__':unittest.main()
