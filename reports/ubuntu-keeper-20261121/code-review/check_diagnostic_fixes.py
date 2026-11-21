"""Run only four new parity cases and three affected existing methods, offline."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
NEW = 'tests_python.test_keeper_operation_review_followup.KeeperOperationReviewFollowupTests.'
OLD = 'tests_python.test_keeper_operation_review.KeeperOperationReviewTests.'
METHODS = [NEW + name for name in (
    'test_profile2_quotes_once_before_same_typed_simulation_and_estimate',
    'test_profile2_zero_quote_refuses_before_any_operation_simulation',
    'test_in_range_foreign_observation_blocks_compound_without_blocking_harvest',
    'test_tracked_malformed_observation_is_unavailable_and_never_invents_clear')]
AFFECTED = [OLD + name for name in (
    'test_hash_pinning_and_exact_fixed_calls_without_nonce_or_broadcast',
    'test_numeric_gas_caps_accumulate_exact_known_blockers',
    'test_local_confirmation_reset_blocks_principal_only_and_clear_ack_is_informational')]


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage', choices=('before', 'after'), required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    path = ROOT / 'keeper/operation_review.py'
    if args.stage == 'before':
        raw = subprocess.run(['git', 'cat-file', 'blob', 'HEAD:keeper/operation_review.py'],
                             cwd=ROOT, capture_output=True, check=True).stdout
        previous = args.output / 'operation_review.before.py'
        previous.write_bytes(raw)
        spec = importlib.util.spec_from_file_location('keeper.operation_review', previous)
        module = importlib.util.module_from_spec(spec)
        sys.modules['keeper.operation_review'] = module
        spec.loader.exec_module(module)
    else:
        raw = path.read_bytes()
    capture = io.StringIO()
    selection = METHODS + (AFFECTED if args.stage == 'after' else [])
    suite = unittest.defaultTestLoader.loadTestsFromNames(selection)
    result = unittest.TextTestRunner(stream=capture, verbosity=2).run(suite)
    log = capture.getvalue().encode()
    (args.output / 'TESTS.log').write_bytes(log)
    record = {'schema': 1, 'stage': args.stage, 'methods': selection, 'run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
              'successful': result.wasSuccessful(), 'tested_review_sha256': sha(raw),
              'current_review_sha256': sha(path.read_bytes()),
              'monitor_sha256': sha((ROOT / 'keeper/monitor.py').read_bytes()),
              'new_tests_sha256': sha((ROOT / 'tests_python/test_keeper_operation_review_followup.py').read_bytes()),
              'log_sha256': sha(log), 'unchanged_suites_run': False, 'network_or_signing_used': False}
    (args.output / 'RESULT.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
