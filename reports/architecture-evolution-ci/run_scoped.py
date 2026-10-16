"""Reproduce only the published fork-runner unit module with a six-line fix.

No fork, network request, Forge execution, signing or repository mutation occurs.
The runner and Solidity inventory fixtures come from the exact recorded commit.
"""
from pathlib import Path
import argparse
import datetime
import difflib
import hashlib
import json
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
BASE = '4fbd4c0bb6e0c066a92af76213708958e4e438e8'
TEST = 'tests_python/test_fork_runner.py'
FIXTURES = (TEST, 'scripts/run-fork-checks.py',
            'test/UniswapV4Fork.t.sol', 'test/NativePoolFork.t.sol')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch-dir', type=Path, required=True)
    parser.add_argument('--ci-log', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch_dir.resolve()
    mirror = scratch / 'mirror-4fbd4c0'
    watched = (TEST, 'scripts/run-fork-checks.py')
    worktree_before = {p: sha((ROOT / p).read_bytes()) for p in watched}
    frozen_before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                     for p in (ROOT / 'reports/architecture-evolution').rglob('*')
                     if p.is_file()}
    originals = {p: subprocess.check_output(['git', 'show', BASE + ':' + p], cwd=ROOT)
                 for p in FIXTURES}
    original = originals[TEST].decode('utf-8')
    assert original.count('self.fail') == 3
    fixed = original.replace('self.fail', 'self.spawn_failure')
    replacements = {
        "'29 successful source tests, zero skips'": "'33 successful source tests, zero skips'",
        'self.assertEqual(len(native),20)': 'self.assertEqual(len(native),24)',
        'self.assertEqual(RUNNER.verify_fork_results(json.dumps(results)),29)':
            'self.assertEqual(RUNNER.verify_fork_results(json.dumps(results)),33)',
    }
    for before, after in replacements.items():
        assert fixed.count(before) == 1, before
        fixed = fixed.replace(before, after)
    scoped = fixed.encode('utf-8')
    assert len(re.findall(r'^    def test_', original, re.M)) == 28
    assert len(re.findall(r'^    def test_', fixed, re.M)) == 28
    assert 'self.fail' not in fixed
    write(scratch / TEST, scoped)
    for rel, data in originals.items():
        write(REPORT / 'sources/baseline' / rel, data)
        write(mirror / rel, scoped if rel == TEST else data)
    write(REPORT / 'sources/scoped' / TEST, scoped)
    diff = ''.join(difflib.unified_diff(original.splitlines(keepends=True),
                                      fixed.splitlines(keepends=True),
                                      fromfile=BASE + '/' + TEST, tofile='scoped/' + TEST))
    write(REPORT / 'scoped.patch', diff.encode('utf-8'))
    ci_bytes = args.ci_log.read_bytes()
    ci_lines = ci_bytes.decode('utf-8').splitlines(keepends=True)
    start = next(i for i, line in enumerate(ci_lines) if 'ERROR: test_successful_complete_run_' in line)
    end = next(i for i in range(start, len(ci_lines)) if 'FAILED (failures=2, errors=1)' in ci_lines[i]) + 1
    write(REPORT / 'original-ci-failures.log', ''.join(ci_lines[start:end]).encode('utf-8'))
    before = {p: sha((mirror / p).read_bytes()) for p in FIXTURES}
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests_python',
               '-p', 'test_fork_runner.py', '-v']
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    result = subprocess.run(command, cwd=mirror, capture_output=True, text=True,
                            encoding='utf-8', timeout=60, check=False)
    elapsed = time.monotonic() - clock
    write(REPORT / 'tests.log', (result.stdout + result.stderr).encode('utf-8'))
    match = re.search(r'Ran (\d+) tests? in [\d.]+s', result.stderr)
    count = int(match[1]) if match else None
    after = {p: sha((mirror / p).read_bytes()) for p in FIXTURES}
    worktree_after = {p: sha((ROOT / p).read_bytes()) for p in watched}
    frozen_after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                    for p in (ROOT / 'reports/architecture-evolution').rglob('*')
                    if p.is_file()}
    receipt = {
        'started_at_utc': started, 'baseline_commit': BASE,
        'mode': 'Isolated mirror; only the 28 existing fork-runner Python unit tests; no real fork or Forge execution',
        'python': sys.version, 'command': command, 'mirror': str(mirror),
        'elapsed_seconds': elapsed, 'exit_code': result.returncode,
        'tests_run': count, 'successful': result.returncode == 0 and count == 28,
        'failures': 0 if result.returncode == 0 else None,
        'errors': 0 if result.returncode == 0 else None,
        'skips': 0 if result.returncode == 0 and 'skipped=' not in result.stderr else None,
        'original_ci': {
            'run_id': 38976039899, 'job_id': 117225610456,
            'sanitized_log_sha256': sha(ci_bytes), 'full_run_tests': 568,
            'failures': 2, 'errors': 1,
            'affected_module_tests': 28,
            'causes': ['Native source inventory is already 24 but the published expectation is 20',
                       'Total source inventory is already 33 but two published expectations are 29',
                       'ForkProcessTests self.fail boolean masks unittest.TestCase.fail on assertion error'],
            'not_claimed': 'No fresh broad 568-test run or green follow-up Ubuntu CI is asserted'},
        'scoped_copy': str(scratch / TEST), 'scoped_sha256': sha(scoped),
        'original_committed_sha256': {p: sha(data) for p, data in originals.items()},
        'mirror_before_sha256': before, 'mirror_after_sha256': after,
        'mirror_sources_unchanged': before == after,
        'exact_source_and_destination_copies': {
            'baseline': 'sources/baseline', 'fixed_test': 'sources/scoped/' + TEST},
        'working_files_before_sha256': worktree_before,
        'working_files_after_sha256': worktree_after,
        'dirty_working_files_preserved': worktree_before == worktree_after,
        'frozen_architecture_bundle_unchanged': frozen_before == frozen_after,
        'frozen_bundle_sha256': frozen_before,
        'driver_sha256': sha(Path(__file__).read_bytes()),
        'limitations': ['Synthetic RPC/subprocess/server fixtures only; Solidity files are inventory text inputs',
                        'Does not qualify the unpublished process runner or its additional tests',
                        'No production Solidity/source edit, staging, commit, push or real asset operation'],
    }
    write(REPORT / 'receipt.json', (json.dumps(receipt, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({k: receipt[k] for k in ('baseline_commit', 'tests_run', 'successful',
          'exit_code', 'scoped_copy', 'scoped_sha256', 'mirror_sources_unchanged',
          'dirty_working_files_preserved', 'frozen_architecture_bundle_unchanged')}, indent=2))
    if not receipt['successful'] or not receipt['mirror_sources_unchanged'] or not receipt['dirty_working_files_preserved'] or not receipt['frozen_architecture_bundle_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
