"""One unsigned timer invocation; creates no systemd service or production policy."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from keeper.scheduling import REFUSAL_CODES, ScheduleRefusal, run_once


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, 'Invalid keeper-schedule arguments. Use --help.\n')


def main(argv=None):
    parser = SafeArgumentParser(prog='keeper-schedule', description=__doc__)
    parser.add_argument('action', choices=('init', 'backup', 'observe', 'rebind'))
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--policy-sha256', required=True)
    parser.add_argument('--previous-policy', type=Path)
    parser.add_argument('--previous-policy-sha256')
    options = parser.parse_args(argv)
    if options.action == 'rebind':
        if options.previous_policy is None or options.previous_policy_sha256 is None:
            parser.error('Rebind needs the previous reviewed policy.')
    elif options.previous_policy is not None or options.previous_policy_sha256 is not None:
        parser.error('Previous policy is supported only for rebind.')
    try:
        result = run_once(options.action, options.policy, options.policy_sha256,
            previous_policy_path=options.previous_policy,
            previous_policy_sha256=options.previous_policy_sha256)
    except Exception as exc:
        known = type(exc) is ScheduleRefusal and exc.code in REFUSAL_CODES
        result = {'schema': 1, 'unsigned': True, 'readiness_approved': False,
            'ok': False, 'refusal_code': exc.code if known else 'invalid_input'}
        if known and exc.cause_code is not None:
            result['cause_code'] = exc.cause_code
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
