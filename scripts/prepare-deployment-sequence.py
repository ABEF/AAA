"""Prepare a conditional offline EOA deployment sequence; never deploy or seal."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from zzz_ops import deployment_plan as D
from zzz_ops import deployment_sequence as S


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # Rejected values can accidentally contain credentials. Emit a closed
        # diagnostic code rather than argparse's value-bearing message.
        D.fail('invalid_cli_arguments')


def output_preflight(source, output):
    if os.path.lexists(output):
        D.fail('existing_output_preserved')
    if not output.parent.is_dir():
        D.fail('output_parent_missing')
    if source.resolve() == output.resolve():
        D.fail('input_output_alias')


def main(argv=None):
    parser = Parser(prog='prepare-deployment-sequence', description=__doc__, allow_abbrev=False)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--deployer', required=True)
    parser.add_argument('--starting-nonce', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-profile', default=D.DEFAULT_BUILD_PROFILE,
                        help='Exact trusted build identifier; no automatic fallback.')
    stage = 'input'; publishing = False
    try:
        args = parser.parse_args(argv)
        D.trusted_build(args.build_profile)
        S.validate_sender_nonce(args.deployer, args.starting_nonce)
        output_preflight(args.input, args.output)
        with args.input.open('rb') as stream:
            value = D.decode(stream.read(D.MAX_INPUT+1))
        stage = 'offline_sequence_preparation'
        result = S.prepare(value, args.deployer, args.starting_nonce,
                           build_profile=args.build_profile)
        plan = result['constructor_plan']
        complete = plan['input_assignments_complete'] and plan['top_level_constructor_payloads_complete']
        stage = 'rendering'; raw = D.render(result)
        stage = 'publication'; publishing = True
        D.write_exclusive(args.output, raw)
        print(json.dumps({'artifact_created': True, 'status': result['status'],
            'build_profile': result['build_profile'], 'manifest_sha256': result['manifest_sha256'],
            'offline_only': True, 'ready_for_submission': False, 'production_approved': False,
            'transaction_submitted': False, 'nonce_reserved': False}))
        return 0 if complete else 2
    except Exception as exc:
        reason = exc.code if type(exc) is D.PlanError else 'offline_sequence_unavailable'
        if publishing:
            reason = 'publication_uncertain'
        print(json.dumps({'artifact_created': False, 'offline_only': True,
            'ready_for_submission': False, 'production_approved': False,
            'transaction_submitted': False, 'nonce_reserved': False,
            'stage': stage, 'reason': reason,
            'output_may_exist': publishing or reason == 'existing_output_preserved'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
