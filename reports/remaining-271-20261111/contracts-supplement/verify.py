"""Read-only exact-row/source checks; no optimized-away assertions or test bodies."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def pointer(value, path):
    for item in path.strip('/').split('/'):
        item = item.replace('~1', '/').replace('~0', '~')
        value = value[int(item)] if isinstance(value, list) else value[item]
    return value


def main():
    report = load(HERE / 'FINDINGS.json')
    rows = report['rows']
    expected = {row['id']: row for row in load(ROOT /
        'reports/daily-reconciliation-audit-20261111/history/inherited-310-findings.json')['rows']
        if not row['current_reassessment_ids']}
    earlier87 = {row['id'] for row in load(HERE.parent / 'evidence-frontend/FINDINGS.json')['rows']}
    require(len(rows) == 30 and len({row['id'] for row in rows}) == 30, 'Wrong count/duplicate IDs')
    require(not earlier87.intersection(row['id'] for row in rows), 'Supplement duplicates the87')
    cache = {}
    for row in rows:
        require(row['id'] in expected, 'Not a remaining271 original row')
        original = expected[row['id']]
        for key in ('original_matrix', 'json_pointer', 'original_record_sha256', 'original_matrix_sha256'):
            require(row[key] == original[key], 'Original pointer/hash changed')
        raw = (ROOT / row['original_matrix']).read_bytes()
        require(digest(raw) == row['original_matrix_sha256'], 'Original report changed')
        require(pointer(json.loads(raw.decode('utf-8-sig')), row['json_pointer']) == original['original_record'],
                'Original pointer content differs')
        require(row['original_record_read_in_full'] is True and len(row['assessment']) > 100
                and len(row['subclaims']) >= 2 and row['unresolved_action'] and row['task_ids'],
                'Missing individualized assessment or boundary')
        for evidence in row['current_evidence']:
            require(evidence['revision'] == report['baseline'] and
                    evidence['hash_mode'] == 'git_blob_raw_sha256', 'Mixed evidence source revision')
            key = (evidence['revision'], evidence['path'])
            if key not in cache:
                cache[key] = subprocess.check_output(['git', 'show', ':'.join(key)], cwd=ROOT)
            raw = cache[key]
            require(digest(raw) == evidence['sha256'], 'Source hash differs')
            lines = raw.decode('utf-8-sig').splitlines()
            require(evidence['lines'] and all(evidence['term'].casefold() in lines[n-1].casefold()
                for n in evidence['lines']), 'Source term/line differs')
    for row in load(HERE / 'ARTIFACTS.json')['files']:
        raw = (HERE / row['path']).read_bytes()
        require(digest(raw) == row['sha256'] and len(raw) == row['bytes'], 'Artifact drift')
    print(json.dumps({'individual_records': 30, 'original_pointers_verified': 30,
        'source_files_verified': len(cache), 'all_87_prior_rows_separate': True,
        'new_code_changes': 0, 'test_bodies_executed': 0, 'production_approved': False}))


if __name__ == '__main__':
    main()
