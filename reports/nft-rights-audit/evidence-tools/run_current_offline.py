"""Fresh normal offline Solidity execution; preserve every earlier receipt."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
EVIDENCE = Path(__file__).resolve().parent
EXTERNAL = EVIDENCE.parent
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(EVIDENCE))
from capture_verification import Capture
spec = importlib.util.spec_from_file_location('fork_runner', REPO/'scripts/run-fork-checks.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


def snapshot():
    paths = set((REPO/'src').rglob('*.sol')) | set((REPO/'test').rglob('*.sol')) | set((REPO/'script').rglob('*.sol'))
    paths |= {REPO/'foundry.toml', REPO/'package-lock.json'}
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def main():
    log = EVIDENCE/'solidity-tests.log'
    receipt = EVIDENCE/'solidity-run-summary.json'
    if log.exists() or receipt.exists():
        raise RuntimeError('Do not overwrite a prior execution receipt')
    before = snapshot()
    command = [str(EXTERNAL/'foundry-v1.4.4/forge.exe'), 'test', '--offline',
        '--use', str(EXTERNAL/'toolchain-0.8.26/solc.exe'), '--ast', '--build-info',
        '--build-info-path', str(EVIDENCE/'test-out/build-info'), '--out', str(EVIDENCE/'test-out'),
        '--cache-path', str(EVIDENCE/'test-cache'), '-vv']
    env = os.environ.copy()
    env.pop('RUN_ROBINHOOD_FORK_TESTS', None); env.pop('ROBINHOOD_RPC_URL', None)
    for key in ('FOUNDRY_OUT', 'FOUNDRY_CACHE_PATH', 'FOUNDRY_PROFILE', 'FOUNDRY_BUILD_INFO_PATH'):
        env.pop(key, None)
    state = {'status': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256_before': before, 'command': command, 'deadline_seconds': 1200,
        'public_transactions': False, 'production_approved': False}
    receipt.write_text(json.dumps(state, indent=2)+'\n', encoding='utf-8')
    started = time.monotonic()
    print('Starting full normal offline Solidity suite; bounded 1200 seconds.', flush=True)
    try:
        os.chdir(REPO)
        result = runner.run_process_tree(command, env=env, text=True, capture_output=True, timeout=1200)
        log.write_text((result.stdout or '')+(result.stderr or ''), encoding='utf-8')
        state['exit_code'] = result.returncode
        state['source_sha256_after'] = snapshot()
        state['source_unchanged'] = state['source_sha256_after'] == before
        state['complete_suite_compiler_bindings'] = Capture(REPO).solidity(result.returncode)
        state['status'] = 'passed' if (result.returncode == 0 and state['source_unchanged'] and
            state['complete_suite_compiler_bindings']['passed_current_source']) else 'failed_or_incomplete'
    except BaseException as exc:
        state['status'] = 'failed_or_incomplete'; state['exception_type'] = type(exc).__name__
        state['exception_reason'] = str(exc)
    finally:
        state['elapsed_seconds'] = round(time.monotonic()-started, 3)
        state['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(state, indent=2)+'\n', encoding='utf-8')
        bound = state.get('complete_suite_compiler_bindings', {})
        print(json.dumps({**{key:state.get(key) for key in ('status','exit_code','source_unchanged','elapsed_seconds','exception_type','exception_reason')},
            'counts': {key:bound.get(key) for key in ('passed','failed','skipped','total','suites')}}, indent=2), flush=True)
    return 0 if state['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
