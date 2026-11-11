"""Read-only report integrity, including explicit external-original limitations.

No feature tests run. No receipt or report is written. All integrity conditions
remain active with Python -O. The original local verification.json is historical.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = '6cfa4f1d478c3d15470519801f9703f9f8a8d656'
PRIOR = 'reports/daily-reconciliation-audit-20261111/history/inherited-310-findings.json'
# Original90-row assignment in retained registry order; final30 were reassigned.
CONTRACT_TOPICS = frozenset(('authority', 'canonical', 'confirmation', 'entry',
    'identity', 'portfolio', 'randomness', 'recovery', 'revenue', 'routing',
    'royalties', 'shares', 'valuation'))
EXTERNAL_ORIGINAL = 'reports/operations-hardening/README.md'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_pairs)


def load(path):
    return parse(path.read_bytes())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative_path(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name,
            'Expected a relative repository path')
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts, 'Unsafe evidence path')
    return path


def pointer(value, path):
    require(isinstance(path, str) and path.startswith('/'), 'Invalid original JSON pointer')
    for key in path.split('/')[1:]:
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def inspect(data_root, external_originals=None):
    cache = {}

    def blob(path):
        relative_path(path)
        if path not in cache:
            cache[path] = subprocess.check_output(
                ['git', '-c', 'safe.directory=' + str(ROOT), 'show', BASELINE + ':' + path], cwd=ROOT)
        return cache[path]

    registry = parse(blob(PRIOR))['rows']
    require(len(registry) == 310, 'Original registry must contain310 rows')
    remaining = [row for row in registry if not row['current_reassessment_ids']]
    require(len(remaining) == 271, 'Original remaining set must contain271 rows')
    contract_packet = [row for row in remaining if row['current_topic'] in CONTRACT_TOPICS]
    require(len(contract_packet) == 90, 'Original contract topic partition must contain90 rows')
    assigned = contract_packet[:60]
    report = load(data_root / 'FINDINGS.json')
    require(report['baseline'] == BASELINE and report['assigned_indices'] == [0, 60],
            'Wrong source baseline or assignment')
    require(report['input_count'] == report['reviewed_count'] == len(report['rows']) == 60,
            'Incomplete assigned contract coverage: expected60 rows')
    require(report['original_packet_count'] == 90, 'Wrong original packet count')
    require([row['id'] for row in report['rows']] == [row['id'] for row in assigned],
            'Assigned IDs are omitted, duplicated, reordered or unexpected')
    tasks = {task['id'] for area in parse(blob('docs/project-todo.json'))['areas'] for task in area['tasks']}
    source_references, evidence_files = 0, set()
    for old, row in zip(assigned, report['rows']):
        label = row['id']
        require((row['original_matrix'], row['original_json_pointer'], row['original_record_sha256']) ==
                (old['original_matrix'], old['json_pointer'], old['original_record_sha256']),
                label + ': original identity/pointer changed')
        require(row['title'] == old['title'], label + ': original title changed')
        original = pointer(parse(blob(row['original_matrix'])), row['original_json_pointer'])
        # Original reconciliation hashes use JSON's default ASCII escaping.
        canonical = json.dumps(original, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
        require(digest(canonical) == row['original_record_sha256'] and original == old['original_record'],
                label + ': original record/hash differs')
        assessment = row['assessment']
        for field in ('source_implementation', 'live_qualification',
                      'accepted_risk_or_supersession', 'actionable_remainder'):
            parts = assessment[field]
            require(isinstance(parts, list) and parts and
                    all(isinstance(text, str) and len(text) >= 45 for text in parts),
                    label + ': missing substantive split assessment: ' + field)
        require(row['fresh_execution'] is False and row['task_ids'] and not set(row['task_ids']) - tasks,
                label + ': execution scope/Todo identity differs')
        require(len(row['current_evidence']) >= 2, label + ': missing current evidence')
        for evidence in row['current_evidence']:
            require(evidence['revision'] == BASELINE and evidence['hash_mode'] == 'raw_bytes_and_utf8_LF',
                    label + ': mixed evidence baseline/mode')
            raw = blob(evidence['path'])
            text = raw.decode('utf-8-sig').replace('\r\n', '\n')
            require(digest(raw) == evidence['sha256'] and digest(text.encode()) == evidence['sha256_lf'],
                    label + ': evidence hash differs: ' + evidence['path'])
            lines = text.splitlines()
            start, end = evidence['line_start'], evidence['line_end']
            require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines) and
                    evidence['term'] in lines[start - 1], label + ': evidence locator differs')
            excerpt = '\n'.join(lines[start - 1:end]) + '\n'
            require(excerpt == evidence['excerpt'] and digest(excerpt.encode()) == evidence['excerpt_sha256_lf'],
                    label + ': evidence excerpt differs')
            source_references += 1
            evidence_files.add(evidence['path'])

    sections = load(data_root / 'original-sections.json')
    require(len(sections) == 135, 'Historical section reference count differs')
    git_sections, external_checked, external_skipped = 0, 0, []
    for section in sections:
        index = section['index']
        require(type(index) is int and 0 <= index < len(assigned), 'Unexpected section assignment')
        old = assigned[index]
        require(old['id'] == section['id'], 'Historical section ID differs')
        original = old['original_record']
        sources = original.get('historical_sources', []) + ([original['original']] if 'original' in original else [])
        declared = {source.get('original_sha256', source.get('sha256')) for source in sources
                    if source.get('path') == section['path']}
        require(section['raw_sha256'] in declared, 'Historical source hash differs from original record')
        if section['source_mode'] == 'git_baseline':
            raw = blob(section['path'])
            git_sections += 1
        else:
            require(section['source_mode'] == 'retained_untracked_original_not_git_baseline' and
                    section['path'] == EXTERNAL_ORIGINAL, 'Unknown external original source')
            if external_originals is None:
                external_skipped.append({key: section[key] for key in ('id', 'path', 'source_mode', 'raw_sha256')})
                continue
            raw = (external_originals / relative_path(section['path'])).read_bytes()
            external_checked += 1
        require(digest(raw) == section['raw_sha256'], 'Historical source bytes differ')
        lines = raw.decode('utf-8-sig').splitlines()
        start, end = section['line_start'], section['line_end']
        require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
                'Historical section locator differs')
        require('\n'.join(lines[start - 1:end]) + '\n' == section['text'], 'Historical section text differs')

    require(git_sections == 134 and external_checked + len(external_skipped) == 1,
            'Historical source-mode coverage differs')
    return {'baseline': BASELINE, 'assigned_indices': [0, 60], 'rows': 60,
            'expected_rows_derived_from': 'Git-baseline inherited310, remaining271, explicit contract topic partition90, first60',
            'source_references': source_references, 'unique_evidence_files': len(evidence_files),
            'historical_section_references': len(sections), 'git_backed_sections_checked': git_sections,
            'external_original_checked': external_checked == 1,
            'complete_original_raw_checks': not external_skipped,
            'external_originals_unchecked': external_skipped,
            'integrity_checks_active_under_optimization': True,
            'read_only': True, 'feature_tests_executed': 0,
            'historical_receipt_rewritten': False, 'production_approval': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=HERE,
                        help='Explicit report input directory, useful for negative artifact checks.')
    parser.add_argument('--external-originals', type=Path,
                        help='Optional archive root preserving repository-relative original paths. Never required for tracked checks.')
    args = parser.parse_args()
    try:
        result = inspect(args.data_root.resolve(), args.external_originals.resolve() if args.external_originals else None)
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'successful': False, 'error': str(exc)}))
        return 1
    print(json.dumps({'successful': True, **result}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
