"""Offline publication checks only; no test imports, signer, RPC or service calls."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import unquote

SOURCE_PINS = {
    'keeper/recovery_bundle.py': 'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268',
    'scripts/keeper-recovery.py': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf',
    'tests_python/test_keeper_recovery_bundle.py': 'e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9',
}
PRESERVED = {
    'reports/source-checks.json': '049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
    'scripts/run-fork-checks.py': '875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
    'tests_python/test_fork_runner.py': '6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
    'tests_python/test_frontend_history.py': '361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb',
}
DOCS = ['AGENTS.md', 'PROJECT_CONTEXT.md', 'README.md', 'TODO.md',
    'docs/AUDIT_FINDINGS.md', 'docs/IMPLEMENTATION_STATUS.md', 'docs/KEEPER_RECOVERY.md',
    'docs/KEEPER_REHEARSALS.md', 'docs/OPERATOR_MANUAL.md', 'docs/ROADMAP.md',
    'docs/WORKLOAD_COVERAGE.md', 'docs/WORK_HANDOFF.md', 'docs/README.md', 'reports/README.md']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    report = root / 'reports/keeper-backup-20261126'
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    checks = []
    for name, digest in {**SOURCE_PINS, **PRESERVED}.items():
        assert sha((root / name).read_bytes()) == digest, name
    for name in SOURCE_PINS:
        ast.parse((root / name).read_bytes())
    checks.append({'check': 'tested_source_and_four_unrelated_dirty_files_exact', 'passed': True})
    reviewed = json.loads((report / 'verification/POST_REVIEW.json').read_bytes())
    for name, row in reviewed['artifacts'].items():
        raw = (root / name).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], name
    assert reviewed['distinct_NEW_methods_passed'] == 33
    assert reviewed['previously_green_methods_reexecuted'] == 0
    checks.append({'check': 'independent_saved_review_artifact_pins_match', 'passed': True})
    historical = {}
    for folder in ('keeper-full-audit-20261126', 'ubuntu-daemon-storage-20261126'):
        base = root / 'reports' / folder
        rows = json.loads((base / 'ARTIFACTS.json').read_bytes())['files']
        for name, row in rows.items():
            raw = (base / name).read_bytes()
            assert sha(raw) == row['sha256'] and len(raw) == row['bytes'], folder + '/' + name
        historical[folder] = len(rows)
    assert historical == {'keeper-full-audit-20261126': 77, 'ubuntu-daemon-storage-20261126': 88}
    checks.append({'check': 'prior_165_report_artifacts_unchanged', 'passed': True})
    identity = reviewed['source_pins']
    assert identity == SOURCE_PINS
    for name, row in reviewed['artifacts'].items():
        if name.startswith(('keeper/', 'zzz_ops/')) and name != 'keeper/recovery_bundle.py':
            assert sha((root / name).read_bytes()) == row['sha256']
    host = json.loads((report / 'verification/HOST_RECONCILIATION.json').read_bytes())
    assert host['lifecycle_reconciliation_verified'] is True
    assert host['original_comparison_success'] is False
    assert host['unexplained_differences_in_supplied_projection'] == 0
    for name, row in host['artifacts'].items():
        raw = (report / name).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], name
    assert sha((report / 'preparation/reconcile_host.py').read_bytes()) == host['reviewer_source_sha256']
    checks.append({'check': 'daemon_identity_and_original_host_nonpass_supplement_retained', 'passed': True})
    outputs = {}
    for label, command in (
        ('todo', [sys.executable, '-B', '-X', 'utf8', 'scripts/sync-project-todo.py', '--check']),
        ('inventory', [sys.executable, '-B', '-X', 'utf8', 'scripts/build-workload-inventory.py', '--check',
            'reports/keeper-backup-20261126/FUNCTION_INVENTORY.json']),
        ('diff', ['git', 'diff', '--check', '--', '.gitattributes', *DOCS, 'docs/project-todo.json',
            'docs/WORKLOAD_PLAN.json', 'scripts/verify.sh']),
    ):
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=30, check=True)
        assert len(result.stdout) + len(result.stderr) <= 32768
        outputs[label] = {'exit_code': result.returncode, 'stdout': result.stdout.decode('utf8'),
            'stderr': result.stderr.decode('utf8')}
    checks.append({'check': 'current_todo_inventory_and_scoped_diff_static_checks', 'passed': True})
    diff = subprocess.run(['git', 'diff', '--unified=0', '--', *DOCS], cwd=root,
        capture_output=True, timeout=30, check=True).stdout.decode('utf8')
    added = {}; current = None
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            current = line[6:]
        elif current and line.startswith('+') and not line.startswith('+++'):
            added[current] = added.get(current, '') + line[1:] + '\n'
    for name in ('docs/KEEPER_BACKUP.md', 'reports/keeper-backup-20261126/REVIEW.md'):
        added[name] = (root / name).read_text(encoding='utf8')
    count = 0
    pending_outputs = set()
    for name, text in added.items():
        for target in re.findall(r'\]\(([^\s)]+)(?:\s+[^)]*)?\)', text):
            target = unquote(target.strip('<>')).split('#', 1)[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
                continue
            path = ((root / name).parent / target).resolve()
            count += 1
            if path in {report / 'verification/PUBLICATION_CHECKS.json', report / 'ARTIFACTS.json'}:
                pending_outputs.add(str(path.relative_to(root)).replace('\\', '/'))
            else:
                assert path.is_file() or path.is_dir(), name + ':' + target
    checks.append({'check': 'new_guide_report_and_added_local_link_targets', 'passed': True,
        'targets_checked': count, 'publication_outputs_created_after_this_read': sorted(pending_outputs)})
    out = {'schema': 1, 'success': True, 'source_pins': SOURCE_PINS, 'preserved_unrelated': PRESERVED,
        'historical_artifacts_verified': historical, 'checks': checks, 'static_command_outputs': outputs,
        'test_bodies_executed': 0, 'server_actions': 0, 'signer_material_read': False,
        'production_approved': False, 'checker_sha256': sha(Path(__file__).read_bytes())}
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(out, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'success': True, 'checks': len(checks), 'historical_files': sum(historical.values()),
        'new_link_targets': count, 'tests_executed': 0, 'server_actions': 0}))


if __name__ == '__main__':
    main()
