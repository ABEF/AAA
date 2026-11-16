"""Prepare an offline prefix-import candidate and review; never signs or installs."""
import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from frontend_api.earnings_checkpoint_build import BuildBudget
from frontend_api.earnings_checkpoint_import import prepare, publish, output_preflight
from frontend_api.service import Projection
from zzz_ops.rpc import RpcError
from zzz_ops.state import read_json
from zzz_ops.work_budget import request_scope


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--prefix', required=True, type=Path)
    parser.add_argument('--prefix-sha256', required=True)
    parser.add_argument('--block', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--review-output', required=True, type=Path)
    parser.add_argument('--max-seconds', type=int, default=60)
    parser.add_argument('--max-calls', type=int, default=4096)
    parser.add_argument('--max-posts', type=int, default=8192)
    args = parser.parse_args(argv)
    try:
        budget = BuildBudget(args.max_seconds, args.max_calls, args.max_posts)
        with request_scope(budget):
            if not re.fullmatch('[0-9a-f]{64}', args.prefix_sha256):
                raise ValueError('Invalid reviewed prefix digest')
            if not 1 <= args.block < 1 << 63:
                raise ValueError('Invalid checkpoint block')
            output_preflight(args.output, args.review_output, prefix_path=args.prefix)
            config = read_json(args.config, encoding='utf-8')
            if not isinstance(config, dict) or not isinstance(config.get('earnings_history'), dict):
                raise ValueError('Missing earnings profile')
            if 'checkpoint' in config['earnings_history']:
                raise ValueError('Target configuration must not install a checkpoint')
            projection = Projection(config)
            if projection.earnings_history is None:
                raise ValueError('Missing earnings profile')
            raw, review = prepare(projection.earnings_history, args.block,
                                  {'path': str(args.prefix), 'sha256': args.prefix_sha256},
                                  budget=budget)
            publish(args.output, args.review_output, raw, review)
    except (OSError, ValueError, RpcError, KeyError, TypeError, RecursionError):
        print('Checkpoint import failed. Preserve the prefix, reviewed configuration and raw databases. '
              'Inspect both requested output paths: unapproved artifacts may exist. '
              'No artifact was approved or installed.', file=sys.stderr)
        return 1
    print('Candidate SHA-256: ' + hashlib.sha256(raw).hexdigest())
    print('Import review SHA-256: ' + hashlib.sha256(review).hexdigest())
    print('Not approved or installed. Independently review both artifacts before pinning; '
          'the served checkpoint must precede the full24-hour window.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
