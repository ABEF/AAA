"""Negative-only CLI/egress tests; these fixtures never establish website acceptance."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'rehearse-source9-consumer.mjs'
NODE = shutil.which('node') or (r'C:\Program Files\nodejs\node.exe' if Path(r'C:\Program Files\nodejs\node.exe').is_file() else None)


@unittest.skipUnless(NODE, 'Node is required for the standalone website consumer runner')
class Source9ConsumerRunnerFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.website = self.root / 'website'
        self.website.mkdir()
        self.manifest = self.root / 'manifest.json'
        self.cases = self.root / 'cases.json'
        self.output = self.root / 'evidence.json'
        self.manifest.write_text(json.dumps({'schema': 4, 'source_profile': 9, 'accounting_version': 7,
            'environment': 'rehearsal', 'rpc_url': 'http://127.0.0.1:19999', 'api_prefix': '/api'}), encoding='utf8')
        self.cases.write_text(json.dumps([{'name': 'rejected_case', 'action': 'read',
            'account': '0x' + '1' * 40, 'id': '1',
            'reject': {'stage': 'read_protocol', 'category': 'consumer_validation',
                       'message': 'Expected source-authored local guard'}}]), encoding='utf8')

    def run_consumer(self, *, origin='http://127.0.0.1:19998'):
        return subprocess.run([NODE, str(SCRIPT), '--website-root', str(self.website),
            '--manifest', str(self.manifest), '--origin', origin, '--cases', str(self.cases),
            '--output', str(self.output)], capture_output=True, text=True, timeout=15)

    def test_existing_evidence_is_never_overwritten(self):
        self.output.write_bytes(b'original evidence\x00')
        result = self.run_consumer()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.output.read_bytes(), b'original evidence\x00')

    def test_nonliteral_origin_is_rejected_before_source_import(self):
        for origin in ('http://localhost:19998', 'http://127.1:19998', 'https://127.0.0.1:19998',
                       'http://127.0.0.1:19998/api', 'http://127.0.0.1:19998/?token=PRIVATE_SENTINEL'):
            with self.subTest(origin=origin):
                result = self.run_consumer(origin=origin)
                report = json.loads(self.output.read_text())
                self.assertEqual(result.returncode, 1)
                self.assertFalse(report['passed'])
                self.assertEqual(report['cases'], [])
                self.assertNotIn('PRIVATE_SENTINEL', self.output.read_text() + result.stdout + result.stderr)
                self.output.unlink()

    def test_remote_rpc_and_untyped_growth_fail_before_source_import(self):
        original = self.manifest.read_text()
        self.manifest.write_text(original.replace('http://127.0.0.1:19999', 'https://PRIVATE_SENTINEL.example/rpc'))
        result = self.run_consumer()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('PRIVATE_SENTINEL', self.output.read_text() + result.stdout + result.stderr)
        self.output.unlink()
        self.manifest.write_text(original)
        self.cases.write_text(json.dumps([{'name': 'missing_amount', 'action': 'increase', 'asset': 'ZZZ',
            'account': '0x' + '1' * 40, 'id': '1'}]))
        self.assertEqual(self.run_consumer().returncode, 1)
        self.assertEqual(json.loads(self.output.read_text())['cases'], [])

    def test_broad_and_transient_rejections_are_not_admitted(self):
        selected = json.loads(self.cases.read_text())[0]
        for expected in (True, {}, {'stage': 'prepare', 'category': 'consumer_validation'},
                {'stage': 'prepare', 'category': 'unavailable', 'message': 'Unavailable'},
                {'stage': 'prepare', 'category': 'http', 'http_status': 503},
                {'stage': 'prepare', 'category': 'http', 'http_status': 429},
                {'stage': 'verify_review', 'category': 'consumer_validation', 'message': 'Runner assertion'}):
            with self.subTest(expected=expected):
                self.cases.write_text(json.dumps([{**selected, 'reject': expected}]))
                result = self.run_consumer()
                self.assertEqual(result.returncode, 1)
                report = json.loads(self.output.read_text())
                self.assertFalse(report['passed'])
                self.assertEqual(report['cases'], [])
                self.output.unlink()

    def test_typed_rejection_matches_exact_guard_and_never_unrelated_failures(self):
        assertions = '''
import assert from 'node:assert/strict';
const {matchesRejection:matches}=await import(SCRIPT_URI);
const local={stage:'prepare',category:'consumer_validation',message:'Guard rejected contribution'};
assert.equal(matches(local,{...local}),true);
for(const actual of [{...local,stage:'activation_quote'}, {...local,message:'Wrong owner'},
    {...local,category:'unavailable'}, {stage:'prepare',category:'http',http_status:503},
    {...local,stage:'verify_review'}])assert.equal(matches(local,actual),false);
const http={stage:'prepare',category:'http',http_status:400};
assert.equal(matches(http,{...http,message:'Safe backend request error'}),true);
assert.equal(matches(http,{...http,http_status:503}),false);
assert.equal(matches({...http,http_status:503},{...http,http_status:503}),false);
assert.equal(matches(true,local),false);
'''.replace('SCRIPT_URI', json.dumps(SCRIPT.as_uri()))
        result = subprocess.run([NODE, '--input-type=module', '-e', assertions],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_forbidden_rpc_attempt_cannot_count_as_expected_rejection(self):
        # Deliberately hostile boundary fixture. It never represents the actual
        # DeploymentAPI and cannot establish a successful rehearsal.
        (self.website / 'package.json').write_text('{"type":"module"}')
        (self.website / 'browser-wallet.js').write_text('export function createChainReader() { return {}; }')
        for method in ('eth_sendTransaction', 'eth_sign', 'eth_getTransactionCount', 'debug_traceCall'):
            with self.subTest(method=method):
                (self.website / 'deployment-api.js').write_text('''
export class DeploymentAPI {
  constructor(manifest, {fetcher}) { this.manifest=manifest; this.fetcher=fetcher; }
  async protocol() {
    await this.fetcher(this.manifest.rpc_url+'/', {method:'POST',body:JSON.stringify({
      jsonrpc:'2.0',id:1,method:METHOD,params:[]})});
    throw Error('PRIVATE_REMOTE_SENTINEL');
  }
}
'''.replace('METHOD', json.dumps(method)), encoding='utf8')
                result = self.run_consumer()
                report = json.loads(self.output.read_text())
                self.assertEqual(result.returncode, 1)
                self.assertTrue(report['forbidden_operation_attempted'])
                self.assertFalse(report['cases'][0]['passed'])
                self.assertEqual(report['rpc_method_counts'], {})
                self.assertNotIn('PRIVATE_REMOTE_SENTINEL', self.output.read_text() + result.stdout + result.stderr)
                self.output.unlink()


if __name__ == '__main__':
    unittest.main()
