"""Prepare an unsigned offline pre-seal configuration review; never configure or seal."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zzz_ops import deployment_plan as D
from zzz_ops import preseal_plan as P


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # Rejected values can accidentally contain credentials. Do not echo
        # argparse's value-bearing error or a caller-selected private path.
        D.fail('invalid_cli_arguments')


def output_preflight(source, output):
    if os.path.lexists(output):
        D.fail('existing_output_preserved')
    if not output.parent.is_dir():
        D.fail('output_parent_missing')
    if source.resolve() == output.resolve():
        D.fail('input_output_alias')


def completeness(result, build_profile):
    """Never publish a malformed internal result as an approved transaction."""
    if (type(result) is not dict or type(result.get('configuration_inputs_complete')) is not bool or
            result.get('offline_only') is not True or result.get('build_profile') != build_profile or
            any(result.get(flag) is not False for flag in (
                'ready_for_submission', 'production_approved', 'transaction_submitted',
                'rpc_performed', 'simulation_performed', 'authority_verified'))):
        D.fail('invalid_preseal_result')
    complete = result['configuration_inputs_complete']
    expected = ('complete_unsigned_preseal_review_pending_live_verification' if complete else
                'blocked_preview_missing_inputs')
    if result.get('status') != expected:
        D.fail('invalid_preseal_result')
    D._hash(result.get('manifest_sha256'), prefix=False)
    return complete


def main(argv=None):
    parser = Parser(prog='prepare-preseal', description=__doc__, allow_abbrev=False)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-profile', default=D.DEFAULT_BUILD_PROFILE,
                        help='Exact trusted build identifier; no automatic fallback.')
    stage = 'input'; publishing = False
    try:
        args = parser.parse_args(argv)
        D.trusted_build(args.build_profile)
        output_preflight(args.input, args.output)
        with args.input.open('rb') as stream:
            value = D.decode(stream.read(D.MAX_INPUT+1))
        stage = 'offline_preseal_preparation'
        result = P.prepare(value, build_profile=args.build_profile)
        complete = completeness(result, args.build_profile)
        stage = 'rendering'; raw = D.render(result)
        stage = 'publication'; publishing = True
        D.write_exclusive(args.output, raw)
        print(json.dumps({'artifact_created': True, 'status': result['status'],
            'build_profile': result['build_profile'], 'manifest_sha256': result['manifest_sha256'],
            'configuration_inputs_complete': complete, 'offline_only': True,
            'ready_for_submission': False, 'production_approved': False,
            'transaction_submitted': False, 'authority_verified': False}))
        return 0 if complete else 2
    except Exception as exc:
        reason = exc.code if type(exc) is D.PlanError else 'offline_preseal_unavailable'
        if publishing:
            reason = 'publication_uncertain'
        print(json.dumps({'artifact_created': False, 'offline_only': True,
            'ready_for_submission': False, 'production_approved': False,
            'transaction_submitted': False, 'authority_verified': False,
            'stage': stage, 'reason': reason,
            'output_may_exist': publishing or reason == 'existing_output_preserved'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
