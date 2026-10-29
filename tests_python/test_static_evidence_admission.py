"""Real CLI parsing and Bash orchestration with inert analyzer/checker tools."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
GIT_BASH=Path('C:/Program Files/Git/bin/bash.exe')
BASH=str(GIT_BASH) if os.name=='nt' and GIT_BASH.exists() else shutil.which('bash')


class StaticReviewCLIAdmissionTests(unittest.TestCase):
    def setUp(self):
        subject=Path(os.environ.get('POPL_STATIC_CHECK_SUBJECT',ROOT/'scripts/check-slither-review.py'))
        spec=importlib.util.spec_from_file_location('static_review_subject',subject)
        self.subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.subject)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)

    def invoke(self,report='{}',review='{}',*,missing=False):
        report_file=self.directory/'SYNTHETIC-PRIVATE-REPORT.json'
        review_file=self.directory/'review.json'
        if not missing:report_file.write_text(report,encoding='utf-8')
        review_file.write_text(review,encoding='utf-8')
        output=io.StringIO()
        with patch.object(sys,'argv',['review',str(report_file),'--review',str(review_file)]), \
                patch.object(self.subject,'check',return_value=[]) as check,redirect_stdout(output):
            status=self.subject.main()
        return status,json.loads(output.getvalue()),check

    def test_ambiguous_analyzer_json_is_rejected_before_coverage_check(self):
        for raw in ('{"success":false,"success":true}',
                    '{"results":{"detectors":[],"detectors":[]}}',
                    r'{"success":true,"\u0073uccess":true}',
                    '{"optional":NaN}','{"optional":Infinity}','{"optional":1e999}'):
            with self.subTest(raw=raw):
                status,result,check=self.invoke(report=raw)
                self.assertTrue(status);self.assertFalse(result['review_coverage_pass']);check.assert_not_called()

    def test_ambiguous_review_json_is_rejected_before_coverage_check(self):
        for raw in ('{"independent_audit":true,"independent_audit":false}',
                    '{"source_sha256_lf":{"src/Core.sol":"one","src/Core.sol":"two"}}',
                    '{"optional":-Infinity}','{"optional":1e999}'):
            with self.subTest(raw=raw):
                status,result,check=self.invoke(review=raw)
                self.assertTrue(status);self.assertFalse(result['review_coverage_pass']);check.assert_not_called()

    def test_nonobjects_and_malformed_inputs_are_rejected_before_check(self):
        for raw in ('null','[]','true','7','"text"','{"marker":"SYNTHETIC-PRIVATE-MARKER",'):
            for slot in ('report','review'):
                with self.subTest(raw=raw,slot=slot):
                    status,result,check=self.invoke(**{slot:raw})
                    self.assertTrue(status);check.assert_not_called()
                    self.assertNotIn('SYNTHETIC-PRIVATE',json.dumps(result))

    def test_missing_input_diagnostic_does_not_echo_path(self):
        status,result,check=self.invoke(missing=True)
        self.assertTrue(status);check.assert_not_called()
        self.assertNotIn('SYNTHETIC-PRIVATE',json.dumps(result))

    def test_valid_utf8_finite_objects_reach_unchanged_coverage_validation(self):
        report={'label':'Café λ','finite':1.25};review={'independent_audit':False}
        status,result,check=self.invoke(json.dumps(report,ensure_ascii=False),json.dumps(review))
        self.assertFalse(status);self.assertTrue(result['review_coverage_pass'])
        check.assert_called_once_with(report,review)

    def test_invalid_review_identity_never_reaches_check_or_echoes_value(self):
        raw=json.dumps({'findings':[{'fingerprint':'SYNTHETIC-PRIVATE-MARKER'}]})
        status,result,check=self.invoke(review=raw)
        self.assertTrue(status);check.assert_not_called()
        self.assertNotIn('SYNTHETIC-PRIVATE',json.dumps(result))

    def test_unexpected_review_source_name_is_not_echoed(self):
        report={'success':True,'results':{'detectors':[]}}
        review={'source_sha256_lf':{'SYNTHETIC-PRIVATE-MARKER':'f'*64},
                'findings':[],'independent_audit':False}
        errors=self.subject.check(report,review,root=self.directory)
        self.assertTrue(errors)
        self.assertNotIn('SYNTHETIC-PRIVATE',json.dumps(errors))


@unittest.skipUnless(BASH,'Bash required for actual static-runner orchestration')
class StaticRunnerAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'static evidence fixture'
        (self.root/'scripts').mkdir(parents=True);(self.root/'bin').mkdir()
        (self.root/'reports/production').mkdir(parents=True)
        subject=Path(os.environ.get('POPL_STATIC_RUNNER_SUBJECT',ROOT/'scripts/verify-slither.sh'))
        (self.root/'scripts/verify-slither.sh').write_bytes(subject.read_bytes())
        self.old={name:('ORIGINAL '+name+'\n').encode() for name in ('slither-current.json','slither-current.log')}
        for name,data in self.old.items():(self.root/'reports/production'/name).write_bytes(data)
        analyzer='''#!/usr/bin/env bash
set -eu
if [[ "${1:-}" == '--version' ]]; then printf '%s\\n' "${POPL_TEST_STATIC_VERSION:-0.11.6}"; exit 0; fi
printf 'analyze\\n' >> "$POPL_TEST_STATIC_CALLS"
output=''
while (($#)); do
  if [[ "$1" == '--json' ]]; then output="$2"; shift 2; else shift; fi
done
printf '{"success":true,"results":{"detectors":[]}}\\n' > "$output"
printf 'controlled analyzer diagnostic\\n'
exit "${POPL_TEST_STATIC_ANALYZER_EXIT:-0}"
'''
        checker='''#!/usr/bin/env bash
set -eu
printf 'review:%s\\n' "$*" >> "$POPL_TEST_STATIC_CALLS"
if [[ "${POPL_TEST_STATIC_REVIEW_EXIT:-0}" == 0 ]]; then flag=true; else flag=false; fi
printf '{"review_coverage_pass":%s,"independent_audit":false}\\n' "$flag"
exit "${POPL_TEST_STATIC_REVIEW_EXIT:-0}"
'''
        for name,text in [('slither',analyzer),('python3',checker)]:
            path=self.root/'bin'/name;path.write_bytes(text.encode());path.chmod(0o755)
        tee='''#!/usr/bin/env bash
if [[ "${POPL_TEST_STATIC_LOG_FAILURE:-0}" == 1 && "${1:-}" == */slither-current.log ]]; then
  printf 'log-failure-injected\\n' >> "$POPL_TEST_STATIC_CALLS"
  cat >/dev/null
  printf 'controlled log-write failure\\n' >&2
  exit 1
fi
exec /usr/bin/tee "$@"
'''
        path=self.root/'bin/tee';path.write_bytes(tee.encode());path.chmod(0o755)
        self.calls=self.root/'calls.txt'

    def invoke(self,**extra):
        env=dict(os.environ)
        for key in ('BASH_ENV','ENV','POPL_SLITHER_OUTPUT_DIR'):env.pop(key,None)
        env.update(POPL_TEST_STATIC_BIN=(self.root/'bin').as_posix(),POPL_TEST_STATIC_CALLS=self.calls.as_posix(),**extra)
        # Git Bash prepends system tools when it imports Windows PATH. Resolve
        # the fixture directory inside Bash before selecting the inert tools.
        command='PATH="$(cd "$POPL_TEST_STATIC_BIN" && pwd):$PATH"; export PATH; exec bash scripts/verify-slither.sh'
        return subprocess.run([BASH,'--noprofile','--norc','-c',command],cwd=self.root,env=env,
            capture_output=True,text=True,encoding='utf-8',timeout=20)

    def assert_legacy_unchanged(self):
        for name,data in self.old.items():self.assertEqual((self.root/'reports/production'/name).read_bytes(),data)

    def test_existing_requested_directory_is_refused_before_analyzer(self):
        output=self.root/'existing';output.mkdir();(output/'sentinel').write_bytes(b'preserved')
        result=self.invoke(POPL_SLITHER_OUTPUT_DIR=output.as_posix())
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(self.calls.exists());self.assertEqual((output/'sentinel').read_bytes(),b'preserved')
        self.assert_legacy_unchanged()

    def test_default_runs_have_distinct_evidence_and_preserve_old_reports(self):
        first=self.invoke();second=self.invoke()
        self.assertEqual(first.returncode,0,first.stderr);self.assertEqual(second.returncode,0,second.stderr)
        evidence=sorted((self.root/'reports').glob('slither.*'))
        self.assertEqual(len(evidence),2)
        for directory in evidence:
            self.assertTrue((directory/'slither-current.json').is_file())
            self.assertIn('controlled analyzer diagnostic',(directory/'slither-current.log').read_text())
            self.assertTrue((directory/'review-coverage.json').is_file())
        self.assert_legacy_unchanged()

    def test_analyzer_failure_retains_evidence_and_never_runs_review(self):
        result=self.invoke(POPL_TEST_STATIC_ANALYZER_EXIT='2')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('review:',self.calls.read_text())
        evidence=list((self.root/'reports').glob('slither.*'));self.assertEqual(len(evidence),1)
        self.assertIn('controlled analyzer diagnostic',(evidence[0]/'slither-current.log').read_text())
        self.assert_legacy_unchanged()

    def test_findings_exit_reaches_checker_and_review_failure_propagates(self):
        result=self.invoke(POPL_TEST_STATIC_ANALYZER_EXIT='255',POPL_TEST_STATIC_REVIEW_EXIT='1')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('review:',self.calls.read_text())
        evidence=list((self.root/'reports').glob('slither.*'));self.assertEqual(len(evidence),1)
        self.assertTrue((evidence[0]/'review-coverage.json').is_file())
        self.assert_legacy_unchanged()

    def test_wrong_analyzer_version_stops_without_analysis(self):
        result=self.invoke(POPL_TEST_STATIC_VERSION='0.0.0')
        self.assertNotEqual(result.returncode,0);self.assertFalse(self.calls.exists())
        evidence=list((self.root/'reports').glob('slither.*'));self.assertEqual(len(evidence),1)
        self.assertTrue((evidence[0]/'slither-version.txt').is_file())
        self.assert_legacy_unchanged()

    def test_failed_analyzer_log_capture_never_reaches_review(self):
        result=self.invoke(POPL_TEST_STATIC_LOG_FAILURE='1')
        self.assertIn('log-failure-injected',self.calls.read_text(),'fault injection must actually reach tee')
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('review:',self.calls.read_text())
        self.assert_legacy_unchanged()


if __name__=='__main__':unittest.main()
