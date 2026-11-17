"""Check final source/docs/evidence bindings without executing behavior suites."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = json.loads((REPORT / 'SOURCE_SNAPSHOT.json').read_text())
    for name, expected in source['source_sha256'].items():
        assert digest((ROOT / name).read_bytes()) == expected, name
    normal = json.loads(gzip.decompress((REPORT / 'build/compiler-input.json.gz').read_bytes()))
    production = {name: row for name, row in normal['sources'].items() if name.startswith('src/')}
    assert len(production) == 61
    for name, row in production.items():
        assert (ROOT / name).read_bytes().replace(b'\r\n', b'\n') == row['content'].encode().replace(b'\r\n', b'\n'), name

    commands = [
        ['scripts/generate-function-reference.py', '--check'],
        ['scripts/generate-operator-reference.py', '--check'],
        ['scripts/sync-project-todo.py', '--check'],
    ]
    outcomes = []
    for command in commands:
        run = subprocess.run([sys.executable, *command], cwd=ROOT, capture_output=True, text=True)
        assert run.returncode == 0, (command, run.stdout, run.stderr)
        outcomes.append({'command': command, 'exit_code': run.returncode, 'stdout': run.stdout.strip()})

    changed = subprocess.check_output(['git', 'diff', '--name-only', '--', '*.md'], cwd=ROOT).decode().splitlines()
    files = [ROOT / name for name in changed]
    files += sorted(REPORT.glob('*.md'))
    pattern = re.compile(r'\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')
    checked = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        for match in pattern.finditer(text):
            target = match.group(1).strip('<>')
            if target.startswith(('#', 'http:', 'https:', 'mailto:', 'plugin:', 'app:')):
                continue
            file_part = unquote(target.split('#', 1)[0])
            assert (path.parent / file_part).resolve().is_file(), (path.relative_to(ROOT), target)
            checked += 1
    whitespace = subprocess.run(['git', '-c', 'core.whitespace=cr-at-eol', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert whitespace.returncode == 0, whitespace.stdout
    result = {
        'source_snapshot_pass': True, 'normal_production_source_binding_count': len(production),
        'generated_checks': outcomes, 'changed_markdown_files_checked': len(files),
        'local_file_links_checked': checked, 'link_scope': 'File targets, not remote availability or every generated heading fragment.',
        'whitespace_check_pass': True, 'test_methods_executed': 0,
        'publication_index_check': 'recorded separately after exact staging',
        'production_approved': False,
    }
    (REPORT / 'MAINTENANCE.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'source_files': len(production), 'generated_checks': len(outcomes), 'local_file_links': checked, 'test_methods_executed': 0}))


if __name__ == '__main__':
    main()
