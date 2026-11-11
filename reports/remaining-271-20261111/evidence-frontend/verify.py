"""Read-only provenance checks; explicit failures remain effective under Python -O."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WEBSITE = ROOT.parents[1] / 'aaa-website'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def at(value, pointer):
    for item in pointer.strip('/').split('/'):
        item = item.replace('~1', '/').replace('~0', '~')
        value = value[int(item)] if isinstance(value, list) else value[item]
    return value


def main():
    findings = load(HERE / 'FINDINGS.json')
    rows = findings['rows']
    inherited = load(ROOT / 'reports/daily-reconciliation-audit-20261111/history/inherited-310-findings.json')['rows']
    expected = {row['id']: row for row in inherited if not row['current_reassessment_ids']}
    require(len(rows) == 87 and len({row['id'] for row in rows}) == 87, 'Wrong assigned count/duplicate ID')
    cache = {}
    task_ids = set()

    def tasks(value):
        if isinstance(value, dict):
            if 'status' in value and 'id' in value:
                task_ids.add(value['id'])
            for child in value.values():
                tasks(child)
        elif isinstance(value, list):
            for child in value:
                tasks(child)

    tasks(load(ROOT / 'docs/project-todo.json'))
    for row in rows:
        require(row['id'] in expected, 'Row was not among remaining271')
        original = expected[row['id']]
        for field in ('original_matrix', 'json_pointer', 'original_record_sha256', 'original_matrix_sha256'):
            require(row[field] == original[field], 'Original provenance changed: ' + row['id'])
        raw = (ROOT / row['original_matrix']).read_bytes()
        require(sha(raw) == row['original_matrix_sha256'], 'Original matrix bytes changed')
        require(at(json.loads(raw.decode('utf-8-sig')), row['json_pointer']) == original['original_record'],
                'Original pointer detail differs')
        require(row['original_record_read_in_full'] is True and len(row['assessment']) >= 100,
                'Missing individual substantive assessment')
        require(len(row['subclaims']) >= 2 and row['current_evidence'] and row['unresolved_action'],
                'Missing split claim/evidence/action')
        require(set(row['task_ids']) <= task_ids, 'Unknown task ID')
        for evidence in row['current_evidence']:
            root = WEBSITE if evidence['repository'] == 'ABEF/AAA-website' else ROOT
            key = (str(root), evidence['revision'], evidence['path'])
            if key not in cache:
                if evidence['hash_mode'] == 'working_file_raw_sha256':
                    require(evidence['path'] == 'scripts/generate-artwork-library.py', 'Unexpected working source')
                    cache[key] = (root / evidence['path']).read_bytes()
                else:
                    require(evidence['hash_mode'] == 'git_blob_raw_sha256', 'Unknown hash mode')
                    cache[key] = subprocess.check_output(['git', '-c', 'safe.directory=' + str(root),
                        'show', evidence['revision'] + ':' + evidence['path']], cwd=root)
            raw = cache[key]
            require(sha(raw) == evidence['sha256'], 'Evidence bytes differ')
            lines = raw.decode('utf-8-sig').splitlines()
            require(evidence['lines'] and all(evidence['term'].casefold() in lines[n - 1].casefold()
                    for n in evidence['lines']), 'Evidence line/term differs')
    generator = load(HERE / 'GENERATOR_ADMISSION.json')
    for field, path in [('generator_sha256', 'scripts/generate-artwork-library.py'),
                        ('test_sha256', 'tests_python/test_artwork_generator_validation.py'),
                        ('library_sha256', 'src/libraries/ZZZArtwork.sol')]:
        require(sha((ROOT / path).read_bytes()) == generator['after'][field], 'Generator artifact drift')
    require(generator['before']['library_sha256'] == generator['after']['library_sha256'], 'Library regenerated')
    require(generator['before']['catalogue_sha256'] == generator['after']['catalogue_sha256'], 'Catalogue regenerated')
    for row in load(HERE / 'ARTIFACTS.json')['files']:
        raw = (HERE / row['path']).read_bytes()
        require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Public artifact drift')
    print(json.dumps({'rows': len(rows), 'exact_original_pointers': 87,
        'concrete_evidence_files': len(cache), 'no_optimized_away_assertions': True,
        'new_generator_methods': 4, 'affected_valid_control': 1,
        'historical_tests_rerun': 0, 'production_approved': False}))


if __name__ == '__main__':
    main()
