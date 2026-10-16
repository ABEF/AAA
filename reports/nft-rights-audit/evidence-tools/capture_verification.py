"""Capture external development evidence; never publish reports or infer readiness.

Run from the contract repository once the commands have finished. Exit statuses
must be supplied from the actual caller; log text alone cannot prove process exit.
An incomplete/stale source closure is recorded as an issue and exits nonzero.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

EVIDENCE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path(r'C:\Users\Ali\Desktop\2.x holas\Oto\zzz-protocol-v2-reviewed\zzz-protocol-v2')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def text(path):
    return Path(path).read_text(encoding='utf-8-sig', errors='replace')


def reference(path):
    path = Path(path)
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def source_snapshot(root):
    paths = {p for folder in ('src','test','script','zzz_ops','frontend_api','keeper','indexer','tests_python','scripts')
             for p in (root/folder).rglob('*') if p.is_file() and (p.suffix in ('.sol','.py') or 'fixtures' in p.parts and p.suffix == '.json')}
    paths.update(root/name for name in ('foundry.toml','package-lock.json'))
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def bytecode(value):
    value = value.removeprefix('0x')
    if not value or not re.fullmatch(r'[0-9a-fA-F]+', value) or len(value) % 2:
        raise ValueError('Missing, malformed or unlinked bytecode')
    return value.lower()


class Capture:
    def __init__(self, root):
        self.root = root.resolve()
        sys.path.insert(0, str(self.root))
        from zzz_ops.abi import keccak256
        self.keccak = keccak256
        self.hash_cache = {}
        self.content_cache = {}
        self.normalized_cache = {}
        self.build_cache = {}
        self.issues = []

    def current(self, name):
        path = self.root / name
        key = str(path.resolve())
        if key not in self.hash_cache:
            raw = path.read_bytes()
            self.content_cache[key] = raw
            self.hash_cache[key] = {'sha256': hashlib.sha256(raw).hexdigest(),
                                    'keccak256': '0x' + self.keccak(raw).hex()}
        return self.hash_cache[key]

    def units(self, artifact_root):
        key = str(artifact_root)
        if key not in self.build_cache:
            entries = []
            for path in sorted((artifact_root / 'build-info').glob('*.json')):
                data = read_json(path)
                entries.append((path, data))
            if not entries:
                raise ValueError(f'No compiler build-info under {artifact_root}')
            self.build_cache[key] = entries
        return self.build_cache[key]

    def artifact(self, artifact_root, source, contract):
        path = artifact_root / Path(source).name / (contract + '.json')
        artifact = read_json(path)
        # Foundry's parsed metadata normalizes ABI/settings representation;
        # the raw compiler metadata binds the bytecode's metadata digest.
        metadata = json.loads(artifact['rawMetadata']) if artifact.get('rawMetadata') else artifact['metadata']
        target = metadata['settings']['compilationTarget']
        if target != {source: contract}:
            raise ValueError(f'Artifact target mismatch: {source}:{contract}')
        closure, expected_inputs = {}, {}
        for name, record in metadata['sources'].items():
            current = dict(self.current(name))
            raw = self.content_cache[str((self.root/name).resolve())]
            compiled = raw
            compiled_sha = current['sha256']
            compiled_keccak = current['keccak256']
            transformation = 'none'
            if current['keccak256'] != record['keccak256']:
                # Forge's vendored dependencies are checked out with CRLF on
                # Windows, while the compiler input uses LF. Accept only this
                # explicit dependency transformation, then require those exact
                # bytes in the matching build-info input below. Production and
                # project test sources retain strict raw-byte matching.
                if name not in self.normalized_cache:
                    normalized = raw.replace(b'\r\n', b'\n')
                    self.normalized_cache[name] = (normalized, hashlib.sha256(normalized).hexdigest(),
                        '0x' + self.keccak(normalized).hex())
                compiled, compiled_sha, compiled_keccak = self.normalized_cache[name]
                if (not name.startswith('lib/') or compiled == raw or
                        compiled_keccak != record['keccak256']):
                    raise ValueError(f'Stale metadata source: {name} in {contract}')
                transformation = 'vendored_dependency_CRLF_to_LF'
            current['compiler_content_transformation'] = transformation
            current['compiler_content_sha256'] = compiled_sha
            current['compiler_content_keccak256'] = compiled_keccak
            expected_inputs[name] = compiled
            closure[name] = current
        runtime = bytecode(artifact['deployedBytecode']['object'])
        initial = bytecode(artifact['bytecode']['object'])
        matches = []
        for unit_path, unit in self.units(artifact_root):
            output = unit.get('output', {}).get('contracts', {}).get(source, {}).get(contract)
            if not output:
                continue
            if (bytecode(output['evm']['bytecode']['object']) != initial or
                    bytecode(output['evm']['deployedBytecode']['object']) != runtime or
                    json.loads(output['metadata']) != metadata):
                continue
            inputs = unit.get('input', {}).get('sources', {})
            if any(name not in inputs or inputs[name]['content'].encode() != compiled
                   for name, compiled in expected_inputs.items()):
                continue
            matches.append(reference(unit_path))
        if not matches:
            raise ValueError(f'No current compiler input/output closure matches {source}:{contract}')
        return {'source': source, 'contract': contract, 'artifact': reference(path),
                'runtime_bytes': len(runtime)//2, 'initcode_object_bytes': len(initial)//2,
                'compiler_version': metadata['compiler']['version'],
                'compiler_settings': metadata['settings'],
                'current_metadata_source_bindings': closure, 'matching_build_info': matches}

    def production(self, exit_code):
        baseline_path = self.root / 'reports/gap-hardening/production-size-gates.json'
        baseline = read_json(baseline_path)
        names = [row['contract'] for row in baseline['contracts']]
        if len(names) != len(set(names)):
            raise ValueError('Ambiguous historical module selection')
        records, covered = [], {}
        for name in names:
            item = self.artifact(EVIDENCE/'production-out', f'src/{name}.sol', name)
            covered.update({path: binding for path, binding in item['current_metadata_source_bindings'].items()
                            if path.startswith('src/')})
            item['runtime_margin_bytes'] = baseline['runtime_limit'] - item['runtime_bytes']
            item['initcode_object_margin_bytes'] = baseline['initcode_limit'] - item['initcode_object_bytes']
            item['runtime_pass'] = item['runtime_margin_bytes'] >= 0
            item['initcode_object_pass'] = item['initcode_object_margin_bytes'] >= 0
            records.append(item)
        expected = {p.relative_to(self.root).as_posix() for p in (self.root/'src').rglob('*.sol')}
        if set(covered) != expected:
            raise ValueError('Selected production artifacts do not bind every current Solidity source')
        return {'exit_code_supplied_by_caller': exit_code,
                'normal_build_log': reference(EVIDENCE/'production-build-verified.log'),
                'earlier_failed_build_log_preserved': reference(EVIDENCE/'production-build.log'),
                'selection_only_from_historical_report': reference(baseline_path),
                'runtime_limit': baseline['runtime_limit'], 'initcode_limit': baseline['initcode_limit'],
                'deployment_arguments_not_included': True,
                'count': len(records), 'source_count': len(covered), 'source_bindings': covered,
                'contracts': records, 'passed': exit_code == 0 and all(
                    r['runtime_pass'] and r['initcode_object_pass'] for r in records)}

    @staticmethod
    def counts(log):
        matches = list(re.finditer(r'Ran (\d+) test suites?[^\n]*: (\d+) tests? passed, '
            r'(\d+) failed, (\d+) skipped \((\d+) total tests?\)', log))
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous completed Forge run summary')
        suites, passed, failed, skipped, total = map(int, matches[0].groups())
        if passed + failed + skipped != total:
            raise ValueError('Forge summary does not conserve the test inventory')
        return {'suites': suites, 'passed': passed, 'failed': failed, 'skipped': skipped, 'total': total}

    def solidity(self, exit_code):
        path = EVIDENCE/'solidity-tests.log'
        log = text(path)
        counts = self.counts(log)
        suites = re.findall(r'^Ran (\d+) tests? for ([^:\n]+):([A-Za-z0-9_]+)\s*$', log, re.M)
        if (len(suites) != counts['suites'] or len({(s,c) for _,s,c in suites}) != len(suites) or
                sum(int(n) for n,_,_ in suites) != counts['total']):
            raise ValueError('Executed suite headers differ from final summary')
        expected_suites = set()
        for candidate in (EVIDENCE/'test-out').glob('*.t.sol/*.json'):
            record = read_json(candidate)
            meta = json.loads(record['rawMetadata']) if record.get('rawMetadata') else record.get('metadata',{})
            targets = meta.get('settings',{}).get('compilationTarget',{})
            functions = [item.get('name','') for item in record.get('abi',[]) if item.get('type')=='function']
            if record.get('bytecode',{}).get('object') not in (None,'','0x') and any(
                    name.startswith(('test','invariant')) for name in functions):
                expected_suites.update((source,contract) for source,contract in targets.items() if source.startswith('test/'))
        if {(s,c) for _,s,c in suites} != expected_suites:
            raise ValueError('Executed suites do not cover the complete deployable test artifact inventory')
        skipped_suites = []
        for block in re.split(r'(?=^Ran \d+ tests? for )',log,flags=re.M)[1:]:
            header = re.match(r'Ran \d+ tests? for ([^:\n]+):([A-Za-z0-9_]+)',block)
            skips = re.findall(r'^\[SKIP[^\n]*',block,re.M)
            if skips:
                if len(skips)!=1 or 'setUp()' not in skips[0]:
                    raise ValueError('Unexpected skipped test in offline run')
                skipped_suites.append(':'.join(header.groups()))
        if set(skipped_suites)!={'test/NativePoolFork.t.sol:NativePoolForkTest','test/UniswapV4Fork.t.sol:UniswapV4ForkTest'} or counts['skipped']!=len(skipped_suites):
            raise ValueError('Offline skip inventory differs from the two intentional fork setup skips')
        bindings = []
        for count, source, contract in suites:
            item = self.artifact(EVIDENCE/'test-out', source.replace('\\','/'), contract)
            item['tests_in_suite'] = int(count)
            bindings.append(item)
        return {**counts, 'log': reference(path), 'exit_code_supplied_by_caller': exit_code,
                'executed_suite_artifact_bindings': bindings,
                'passed_current_source': exit_code == 0 and counts['failed'] == 0,
                'skipped_lines': re.findall(r'^\[SKIP[^\n]*', log, re.M),
                'scope': 'Offline Solidity execution; skipped fork setup is not public-chain fork evidence.'}

    def python(self):
        path = EVIDENCE/'python-tests.json'
        record = read_json(path)
        bindings = record['source_sha256']
        expected = {p.relative_to(self.root).as_posix() for folder in
            ('src','zzz_ops','frontend_api','keeper','indexer','tests_python','scripts')
            for p in (self.root/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.sol')}
        if set(bindings) != expected:
            raise ValueError('Python receipt source inventory differs from current source')
        stale = [name for name,digest in bindings.items() if self.current(name)['sha256'] != digest]
        if stale:
            raise ValueError('Python receipt is stale: '+', '.join(stale))
        excluded = record['unix_cases_reserved_for_ubuntu']
        if record['tests_run'] + len(excluded) != record['inventory']:
            raise ValueError('Python test inventory differs from executed/excluded counts')
        return {'receipt': reference(path), 'log': reference(EVIDENCE/'python-tests.log'),
                'inventory': record['inventory'], 'tests_run': record['tests_run'],
                'failures': record['failures'], 'errors': record['errors'], 'skipped': record['skipped'],
                'unix_cases_reserved_for_ubuntu': excluded,
                'source_unchanged_during_run': record['source_unchanged_during_run'],
                'source_sha256': bindings,
                'passed_current_source': bool(record['successful'] and record['source_unchanged_during_run']
                    and not record['failures'] and not record['errors'] and not record['skipped'])}

    def gas(self):
        directory = EVIDENCE.parent/'combined-capacity-20261016'
        binding_path = directory/'final-source-bindings.json'
        bindings = read_json(binding_path)
        stale = [item['path'] for item in bindings if self.current(item['path'])['sha256'] != item['sha256']]
        if stale:
            raise ValueError('Combined-capacity final receipt is stale: '+', '.join(stale))
        source = text(self.root/'test/CombinedCapacityGas.t.sol')
        budget = int(re.search(r'LOCAL_GAS_BUDGET\s*=\s*([\d_]+)', source)[1].replace('_',''))
        final_path = directory/'final-four-bucket-gas.log'
        initial_path = directory/'initial-capacity-failure.log'
        final = text(final_path); initial = text(initial_path)
        measured = {label:int(value) for label,value in re.findall(r'^\s*(combined\.[^:\n]+): (\d+)\s*$', final,re.M)}
        failed_measurements = {label:int(value) for label,value in re.findall(r'^\s*(combined\.[^:\n]+): (\d+)\s*$', initial,re.M)}
        counts = self.counts(final)
        expected_cases = set(re.findall(r'function\s+(test\w+)\s*\(', source))
        passed_cases = set(re.findall(r'^\[PASS\]\s+(test\w+)\(', final, re.M))
        if (counts['failed'] or counts['skipped'] or not expected_cases or
                passed_cases != expected_cases or len(measured) != counts['passed'] or
                len(expected_cases) != counts['passed']):
            raise ValueError('Gas receipt does not completely pass every current case with one measured operation each')
        if not measured or not all(x < budget for x in measured.values()):
            raise ValueError('A current combined-capacity operation exceeds the unchanged local gas budget')
        return {'final_log': reference(final_path), 'final_source_bindings': reference(binding_path),
                'final_counts': counts, 'local_budget': budget, 'operation_gas': measured,
                'all_measured_operations_below_budget': bool(measured) and all(x<budget for x in measured.values()),
                'initial_failure': {'log': reference(initial_path), 'counts': self.counts(initial),
                    'operation_gas': failed_measurements, 'scope': 'Historical 16-bucket combined workload; not current-cap success.'},
                'scope': 'Mock venue and feeds; cold operation gas deltas exclude intrinsic/calldata gas, setup and refunds. Actual venue/strategy qualification remains open.'}

    def rpc_probe(self):
        path = EVIDENCE/'rpc-hash-selector-probe.json'
        report = read_json(path)
        calls = report['calls']
        state_reads = [item for item in calls if item['method'] in ('eth_call','eth_getCode','eth_getStorageAt')]
        selectors = [item['params'][-1] for item in state_reads]
        success = bool(state_reads) and all(item.get('http_status') == 200 and
            'result' in item.get('response',{}) for item in state_reads)
        pinned = all(selector == selectors[0] and selector.get('requireCanonical') is True for selector in selectors)
        return {'evidence': reference(path), 'utc': report['utc'], 'endpoint': report['endpoint'],
                'tested_methods': [item['method'] for item in state_reads],
                'canonical_hash_selector': selectors[0] if selectors else None,
                'all_tested_state_reads_succeeded': success and pinned and report.get('canonical_header_unchanged') is True,
                'scope': 'Only few paced public-provider compatibility reads. Not a complete quote, sustained provider qualification, fork execution or liquidity transaction.'}

    def section(self,name,callback):
        try:return callback()
        except Exception as exc:
            self.issues.append({'section':name,'error_type':type(exc).__name__,'reason':str(exc)})
            return {'available':False,'reason':str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--production-exit-code', type=int)
    parser.add_argument('--solidity-exit-code', type=int)
    args = parser.parse_args()
    capture = Capture(args.root)
    before = source_snapshot(capture.root)
    result = {'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'development_evidence_only', 'production_approved': False,
              'independent_external_audit': False, 'smart_contracts_deployed': False,
              'scope': 'Capture current development receipts without publishing them or upgrading historical evidence.'}
    result['production'] = capture.section('production',lambda:capture.production(args.production_exit_code))
    result['solidity'] = capture.section('solidity',lambda:capture.solidity(args.solidity_exit_code))
    result['python'] = capture.section('python',capture.python)
    result['combined_capacity_gas'] = capture.section('combined_capacity_gas',capture.gas)
    result['rpc_compatibility'] = capture.section('rpc_compatibility',capture.rpc_probe)
    result['fork'] = {'current_success_claimed':False,
        'reason':'This capture does not ingest a fresh completed fork execution. Record that separately with its actual result and source closure.'}
    result['static_analysis'] = {'current_review_claimed':False,
        'reason':'Current internal Slither review and coverage are captured separately by the root reviewer; no independent audit is implied.'}
    result['source_sha256_before_capture'] = before
    result['source_unchanged_during_capture'] = before == source_snapshot(capture.root)
    if not result['source_unchanged_during_capture']:
        capture.issues.append({'section':'source','reason':'Source changed while evidence was being captured.'})
    for name,field in (('production','passed'),('solidity','passed_current_source'),('python','passed_current_source')):
        if result[name].get(field) is not True:
            capture.issues.append({'section':name,'reason':'Current-source success/exit evidence is incomplete or failed.'})
    result['issues'] = capture.issues
    result['captured_checks_complete'] = not capture.issues
    (EVIDENCE/'capture-summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if result['production'].get('passed') is True:
        (EVIDENCE/'production-size-gates.current.json').write_text(json.dumps(result['production'],indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'captured_checks_complete':not capture.issues,'issues':capture.issues,
        'production_count':result['production'].get('count'),'source_count':result['production'].get('source_count'),
        'solidity_counts':{k:result['solidity'].get(k) for k in ('passed','failed','skipped','total','suites')},
        'python_tests':result['python'].get('tests_run')},indent=2))
    return 0 if not capture.issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
