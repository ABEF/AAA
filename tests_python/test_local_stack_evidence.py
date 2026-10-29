"""Local lab evidence boundaries; no server or financial call is executed."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


ROOT=Path(__file__).resolve().parents[1]


class LocalStackEvidenceTests(unittest.TestCase):
    def setUp(self):
        path=Path(os.environ.get('POPL_STACK_EVIDENCE_SCRIPT',ROOT/'scripts/verify-local-stack.py'))
        spec=importlib.util.spec_from_file_location('local_stack_evidence_subject',path)
        self.subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.subject)
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.output=Path(self.directory.name)/'receipt.json'

    def test_previous_evidence_blocks_before_any_lab_request(self):
        initial=b'{"original_evidence":true}\n';self.output.write_bytes(initial)
        with patch.object(self.subject.urllib.request,'urlopen',side_effect=urllib.error.URLError('isolated fixture')) as request:
            with self.assertRaises(FileExistsError):self.subject.run(8890,self.output)
        request.assert_not_called();self.assertEqual(self.output.read_bytes(),initial)

    def test_failed_request_preserves_initial_and_failure_status(self):
        def fail(request,**kwargs):
            self.assertEqual(json.loads(self.output.read_text())['status'],'in_progress')
            self.assertEqual(request.full_url,'http://127.0.0.1:8890/session')
            raise urllib.error.URLError('isolated fixture')
        with patch.object(self.subject.urllib.request,'urlopen',side_effect=fail) as request:
            with self.assertRaises(urllib.error.URLError):self.subject.run(8890,self.output)
        self.assertEqual(request.call_count,1)
        result=json.loads(self.output.read_text())
        self.assertEqual(result['status'],'failed');self.assertEqual(result['error_type'],'URLError')

    def test_reserved_marker_survives_interrupt_without_action_retry(self):
        with patch.object(self.subject.urllib.request,'urlopen',side_effect=KeyboardInterrupt) as request:
            with self.assertRaises(KeyboardInterrupt):self.subject.run(8890,self.output)
        self.assertEqual(request.call_count,1)
        self.assertEqual(json.loads(self.output.read_text())['status'],'in_progress')

    def test_success_publishes_complete_result_to_its_owned_file(self):
        expected={'scope':'isolated mocked exercise','checks':['independent expected check'],'snapshot':{'value':'unchanged'}}
        def exercise(port):
            self.assertEqual(port,8890)
            self.assertEqual(json.loads(self.output.read_text())['status'],'in_progress')
            return expected.copy()
        with patch.object(self.subject,'_exercise',side_effect=exercise) as exercise_mock, \
                patch.object(self.subject.urllib.request,'urlopen') as request:
            result=self.subject.run(8890,self.output)
        request.assert_not_called();exercise_mock.assert_called_once_with(8890)
        self.assertEqual(result,{**expected,'status':'passed'})
        self.assertEqual(json.loads(self.output.read_text()),result)

    def test_reservation_storage_failure_prevents_exercise(self):
        with patch.object(self.subject.os,'fsync',side_effect=OSError('storage unavailable')), \
                patch.object(self.subject,'_exercise') as exercise, \
                patch.object(self.subject.urllib.request,'urlopen') as request:
            with self.assertRaises(OSError):self.subject.run(8890,self.output)
        request.assert_not_called();exercise.assert_not_called()


if __name__=='__main__':unittest.main()
