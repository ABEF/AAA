"""Final source/doc/preservation checks; no tests, compiler, RPC or chain calls."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
BASELINE = '003c8d8dc88b60cbfbcc8caf61fa864c6487b40f'
EXPECTED_PRODUCTION = {'src/ZZZVault.sol', 'src/ZZZNFTMetadata.sol',
                       'src/ZZZMigrationBudget.sol', 'src/ZZZCustodyValidation.sol'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    assert git('branch', '--show-current').decode().strip() == 'main'
    protected = json.loads((OWN / 'BASELINE.json').read_text())['protected']
    retained = {name: {'expected': pin, 'actual': sha((ROOT / name).read_bytes())}
                for name, pin in protected.items()}
    assert all(row['expected'] == row['actual'] for row in retained.values())
    changed = set(git('diff', '--name-only', BASELINE).decode().splitlines())
    assert {name for name in changed if name.startswith('src/')} == EXPECTED_PRODUCTION
    assert {name for name in changed if name.startswith('reports/')} <= {'reports/README.md', 'reports/source-checks.json'}
    compiler_start = json.loads((OWN / 'build/START.json').read_text())
    compiler_matches = {name: sha((ROOT / name).read_bytes()) == pin
                        for name, pin in compiler_start['source_sha256'].items()}
    assert len(compiler_matches) == 100 and all(compiler_matches.values())
    extra = ['test/SeaDropArtworkBoundary20261117.t.sol', 'test/SealCriticalInputs20261117.t.sol',
             'test/helpers/AccountingExecutionFixture.sol', 'docs/SEAL_READINESS.md']
    extra += [path.relative_to(ROOT).as_posix() for path in (ROOT / 'test/fixtures/seal-critical-003c8d8').rglob('*') if path.is_file()]
    snapshot = sorted((changed - set(protected)) | set(extra) | set(compiler_start['source_sha256']))
    pins = {name: sha((ROOT / name).read_bytes()) for name in snapshot}
    commands = [
        [sys.executable, 'scripts/generate-function-reference.py', '--check'],
        [sys.executable, 'scripts/generate-operator-reference.py', '--check'],
        [sys.executable, 'scripts/sync-project-todo.py', '--check'],
        ['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--check'],
    ]
    def run(command):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        return {'command': command, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(run, commands))
    assert all(row['exit_code'] == 0 for row in checks), checks
    markdown = {ROOT / name for name in snapshot if name.endswith('.md')}
    markdown.update(OWN.glob('*.md'))
    links = []
    for path in sorted(markdown):
        for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            target = raw.strip().strip('<>')
            if not target or target.startswith(('#', 'http:', 'https:', 'mailto:', 'plugin:', 'codex:')):
                continue
            target = unquote(target.split('#', 1)[0])
            # Absolute user-machine references remain explicit filesystem links.
            match = re.match(r'^(.*?)(?::\d+)?$', target)
            target = match.group(1)
            resolved = Path(target) if re.match(r'^[A-Za-z]:[/\\]', target) else path.parent / target
            links.append({'from': path.relative_to(ROOT).as_posix(), 'target': raw, 'exists': resolved.exists()})
    assert all(row['exists'] for row in links), [row for row in links if not row['exists']]
    assert pins == {name: sha((ROOT / name).read_bytes()) for name in pins}
    record = {'schema': 1, 'baseline': BASELINE, 'production_approved': False,
              'production_changed': sorted(EXPECTED_PRODUCTION), 'accepted_closed_build_sources': compiler_matches,
              'protected_files': retained, 'historical_tracked_reports_unchanged_except_declared': True,
              'source_snapshot_sha256': pins, 'maintenance_checks': checks, 'local_file_links': links,
              'tests_or_compiler_or_services_executed_by_this_check': False,
              'existing_anvil_journals_sites_signers_monitoring_actions': []}
    (OWN / 'COMPLETION.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_pins': len(pins), 'closed_build_source_matches': len(compiler_matches),
                      'protected_files': len(retained), 'maintenance_checks': len(checks), 'local_links': len(links)}))


if __name__ == '__main__':
    main()
