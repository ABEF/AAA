"""Unsigned exact scheduler/observer capture and fresh review-only restoration."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from keeper.sidecar_recovery import backup, verify, restore, DEFAULT_BYTES, SidecarRefusal, REFUSAL_CODES


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, 'Invalid keeper-sidecar-recovery arguments. Use --help.\n')


def main(argv=None):
    parser = SafeArgumentParser(prog='keeper-sidecar-recovery', description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    for name in ('backup', 'verify', 'restore'):
        command = commands.add_parser(name)
        command.add_argument('--policy', type=Path, required=True)
        command.add_argument('--policy-sha256', required=True)
        command.add_argument('--max-bytes', type=int, default=DEFAULT_BYTES)
        command.add_argument('--max-seconds', type=int, default=60)
        if name != 'backup':
            command.add_argument('--bundle', type=Path, required=True)
            command.add_argument('--manifest-sha256', required=True)
            command.add_argument('--max-age-seconds', type=int, required=True)
            command.add_argument('--minimum-created-at', type=int, default=0)
        if name != 'verify':
            command.add_argument('--output', type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        args = {'max_bytes': options.max_bytes, 'max_seconds': options.max_seconds}
        if options.action == 'backup':
            _, pin = backup(options.policy, options.policy_sha256, options.output, **args)
            plan_pin = None
        else:
            args.update(max_age_seconds=options.max_age_seconds, minimum_created_at=options.minimum_created_at)
            pin = options.manifest_sha256
            if options.action == 'verify':
                verify(options.bundle, pin, options.policy, options.policy_sha256, **args)
                plan_pin = None
            else:
                _, plan_pin = restore(options.bundle, pin, options.policy, options.policy_sha256, options.output, **args)
    except Exception as exc:
        code = exc.code if type(exc) is SidecarRefusal and exc.code in REFUSAL_CODES else 'invalid_input'
        print(json.dumps({'schema': 1, 'ok': False, 'unsigned': True,
            'readiness_approved': False, 'refusal_code': code}, sort_keys=True))
        return 1
    result = {'schema': 1, 'ok': True, 'unsigned': True, 'readiness_approved': False,
        'manifest_sha256': pin}
    if plan_pin is not None:
        result['restore_plan_sha256'] = plan_pin
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
