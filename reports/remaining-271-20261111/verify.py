"""Read-only individualized finding provenance checks; no security approval."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = '6cfa4f1d478c3d15470519801f9703f9f8a8d656'
PRIOR = ROOT / 'reports/daily-reconciliation-audit-20261111/history/inherited-310-findings.json'
PARTS = {'contracts': 60, 'backend': 94, 'evidence-frontend': 87, 'contracts-supplement': 30}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pointer(value, where):
    for item in where.strip('/').split('/'):
        item = item.replace('~1', '/').replace('~0', '~')
        value = value[int(item)] if isinstance(value, list) else value[item]
    return value


def local_path(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name,
            'Expected a relative repository path')
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts, 'Unsafe evidence path')
    return path


def inspect(data_root, website_root):
    prior = load(PRIOR)
    expected = {row['id']: row for row in prior['rows'] if not row['current_reassessment_ids']}
    require(len(expected) == 271, 'Original remaining set must contain271 IDs')
    tasks = {t['id'] for a in load(ROOT / 'docs/project-todo.json')['areas'] for t in a['tasks']}
    blobs, seen, distinct_files = {}, set(), set()
    reports = []
    coverage_path = data_root / 'COVERAGE.json'
    coverage = load(coverage_path) if coverage_path.is_file() else None
    navigation = {row['id']: row for row in coverage['records']} if coverage is not None else {}
    for part, count in PARTS.items():
        data = load(data_root / part / 'FINDINGS.json')
        rows = data['rows']
        require(len(rows) == count, part + ': incomplete individual coverage')
        for row in rows:
            identifier = row['id']
            require(identifier in expected and identifier not in seen, 'Unexpected/duplicate finding ID')
            seen.add(identifier)
            old = expected[identifier]
            origin = row.get('original_provenance', {})
            matrix = row.get('original_matrix', origin.get('matrix'))
            where = row.get('original_json_pointer', row.get('json_pointer', origin.get('json_pointer')))
            checksum = row.get('original_record_sha256', origin.get('record_sha256'))
            require((matrix, where, checksum) ==
                    (old['original_matrix'], old['json_pointer'], old['original_record_sha256']),
                    identifier + ': original identity/pointer changed')
            original = load(ROOT / local_path(matrix))
            require(pointer(original, where) == old['original_record'], identifier + ': original record changed')
            require(row.get('title') == old['title'], identifier + ': original title changed')
            assessment = row.get('assessment')
            require(isinstance(assessment, (dict, str)) and bool(assessment), identifier + ': missing assessment')
            details = assessment if isinstance(assessment, dict) else row
            if isinstance(assessment, str):
                require(len(assessment) >= 40 and len(row.get('subclaims', [])) >= 2,
                        identifier + ': missing individual/subclaim assessment')
            else:
                require(bool(assessment.get('source_implementation')) and
                        'actionable_remainder' in assessment, identifier + ': missing split assessment')
            owners = details.get('task_ids', row.get('task_ids', []))
            require(owners and all(owner in tasks for owner in owners), identifier + ': missing Todo owner')
            if coverage is not None:
                indexed = navigation.get(identifier, {})
                canonical = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
                summary = ' '.join(assessment['source_implementation']) if isinstance(assessment, dict) else assessment
                require(indexed.get('record_sha256_canonical') == digest(canonical) and
                        indexed.get('assessment_summary') == summary and indexed.get('task_ids') == owners and
                        indexed.get('part') == part, identifier + ': coverage record differs from full assessment')
            evidence = details.get('current_evidence', row.get('current_evidence', []))
            require(bool(evidence), identifier + ': missing concrete evidence')
            for item in evidence:
                name = item['path']
                repository = item.get('repository', 'ABEF/AAA')
                # The backend report uses this explicit repository prefix;
                # the other parts use a separate repository field.
                if name.startswith('AAA-website/'):
                    require('repository' not in item or repository == 'ABEF/AAA-website',
                            'Conflicting website evidence repository')
                    repository = 'ABEF/AAA-website'
                    name = name[len('AAA-website/'):]
                relative = local_path(name)
                require(repository in ('ABEF/AAA', 'ABEF/AAA-website'), 'Unknown evidence repository')
                repo = website_root if repository == 'ABEF/AAA-website' else ROOT
                revision = item['revision']
                key = (str(repo), revision, name)
                if key not in blobs:
                    if re.fullmatch(r'[0-9a-f]{40}', revision):
                        blobs[key] = subprocess.check_output(
                            ['git', '-c', 'safe.directory=' + str(repo), 'show', revision + ':' + name], cwd=repo)
                    else:
                        require(repository == 'ABEF/AAA' and 'working' in revision,
                                'New candidate evidence needs an explicit working-source label')
                        blobs[key] = (repo / relative).read_bytes()
                raw = blobs[key]
                lf = raw.replace(b'\r\n', b'\n')
                raw_hash = item.get('sha256_raw', item.get('sha256'))
                require(raw_hash is not None or item.get('sha256_lf') is not None, 'Missing evidence hash')
                if raw_hash is not None:
                    require(digest(raw) == raw_hash, identifier + ': evidence raw hash changed: ' + name)
                if item.get('sha256_lf') is not None:
                    require(digest(lf) == item['sha256_lf'], identifier + ': evidence LF hash changed: ' + name)
                lines = lf.decode('utf-8-sig').splitlines()
                numbers = item.get('lines', [item.get('line_start', item.get('line'))])
                term = item.get('term')
                require(term and numbers and all(type(n) is int and 1 <= n <= len(lines) and
                        term.lower() in lines[n-1].lower() for n in numbers),
                        identifier + ': source locator mismatch: ' + name)
                if item.get('excerpt'):
                    require(item['excerpt'].replace('\r\n', '\n').strip('\n') in lf.decode('utf-8-sig'),
                            identifier + ': excerpt absent from declared revision: ' + name)
                distinct_files.add((repository, name))
        if coverage is not None:
            require(digest((data_root / part / 'FINDINGS.json').read_bytes()) ==
                    coverage['parts'][part]['sha256'], part + ': coverage source hash changed')
        reports.append({'part': part, 'individually_reviewed': len(rows)})
    require(seen == set(expected), 'Remaining finding IDs omitted')
    if coverage is not None:
        require(len(coverage['records']) == 271 and
                {row['id'] for row in coverage['records']} == seen,
                'Coverage index omits or duplicates records')
    fixes_path = data_root / 'FIXES.json'
    fixed_sources = 0
    if fixes_path.is_file():
        for name, expected_hash in load(fixes_path)['source_changes'].items():
            require(digest((ROOT / local_path(name)).read_bytes()) == expected_hash,
                    'Post-baseline correction source changed: ' + name)
            fixed_sources += 1
    return {'baseline': BASELINE, 'parts': reports, 'reviewed_remaining': len(seen),
            'previously_reviewed': 39, 'original_registry': 310,
            'exact_original_pointers': len(seen), 'distinct_evidence_files': len(distinct_files),
            'evidence_revision_file_pairs': len(blobs), 'integrity_checks_active_under_optimization': True,
            'post_baseline_source_files_verified': fixed_sources,
            'claim_all_obligations_resolved': False, 'production_approval': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=HERE,
                        help='Explicit input directory; useful for read-only negative verification.')
    parser.add_argument('--website-root', type=Path, default=ROOT.parent.parent / 'aaa-website')
    args = parser.parse_args()
    try:
        result = inspect(args.data_root.resolve(), args.website_root.resolve())
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'successful': False, 'error': str(exc)}))
        return 1
    print(json.dumps({'successful': True, **result}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
