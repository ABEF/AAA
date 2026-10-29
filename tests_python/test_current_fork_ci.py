"""Static CI wiring guards, not a run of GitHub Actions or the live fork suite."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPILER = 'https://binaries.soliditylang.org/linux-amd64/solc-linux-amd64-v0.8.26+commit.8a97fa7a'
SHA256 = 'd5f23436f443edb85d8e76906d12f0a86ce0490e7663a9e608efeb7a93f149ef'


class CurrentForkCIWiringTests(unittest.TestCase):
    def job(self):
        text = (ROOT / '.github/workflows/verify.yml').read_text(encoding='utf-8')
        return text.split('  robinhood-fork:\n', 1)[1]

    def test_current_profile_runner_and_reviewed_compiler_are_explicit(self):
        job = self.job()
        command = next((line for line in job.splitlines()
                        if 'python3 scripts/run-current-pool-fork.py ' in line), '')
        self.assertIn('--rpc-env ROBINHOOD_FORK_RPC_URL', command)
        self.assertIn('--solc "${{ steps.current-solc.outputs.solc }}"', command)
        self.assertIn('--output reports/production/current-pool-fork', command)
        self.assertNotIn('python3 scripts/run-fork-checks.py', job)
        self.assertIn('ROBINHOOD_FORK_RPC_URL: ${{ secrets.ROBINHOOD_RPC_URL', job)

    def test_pinned_compiler_is_verified_before_any_execution(self):
        job = self.job()
        self.assertIn('id: current-solc', job)
        curl = next((line for line in job.splitlines() if 'curl --fail ' in line), '')
        for flag in ('--silent', '--show-error', "--proto '=https'", '--connect-timeout 10', '--max-time 120'):
            self.assertIn(flag, curl)
        self.assertIn(COMPILER, curl)
        check = f'printf \'%s  %s\\n\' \'{SHA256}\' "$solc" | sha256sum --check --strict'
        self.assertIn(check, job)
        self.assertLess(job.index(check), job.index('chmod 755 "$solc"'))
        self.assertLess(job.index(check), job.index('python3 scripts/run-current-pool-fork.py'))

    def test_current_receipt_and_output_are_retained_without_build_cache(self):
        job = self.job()
        self.assertIn('if: always()', job)
        for name in ('receipt.json', 'forge-results.json', 'forge-stderr.log'):
            self.assertIn('reports/production/current-pool-fork/' + name, job)
        self.assertIn('reports/production/current-pool-fork.log', job)
        self.assertNotRegex(job, r'path:\s*reports/production/current-pool-fork\s*$')

    def test_workflow_is_read_only_and_does_not_broadcast(self):
        text = (ROOT / '.github/workflows/verify.yml').read_text(encoding='utf-8')
        self.assertIn('permissions:\n  contents: read', text)
        job = self.job()
        self.assertIn('persist-credentials: false', job)
        self.assertNotRegex(job, r'--broadcast|eth_send(?:Raw)?Transaction|\bcast send\b|PRIVATE_KEY')
