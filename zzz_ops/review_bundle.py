"""Offline, bounded exports of committed review inputs; never release approval."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_MEMBERS = 2048
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_ARCHIVE = MAX_TOTAL + 1024 * 1024
HEX40 = re.compile(r'[0-9a-f]{40}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
TOP = {'README.md', 'TODO.md', 'foundry.toml', 'package.json', 'package-lock.json',
       'requirements.txt', 'requirements-dev.txt', 'remappings.txt', '.gitmodules', 'slither.config.json'}
FIXTURES = {'reports/production/keccak-vectors.json'}
CATALOG = 'design/nft-metadata/palette-system-v1/'
CATALOG_FILES = {'README.md', 'art-catalog.js', 'export-inventory.mjs', 'inventory.json',
                 'packed-catalog.json', 'palette-system.mjs', 'palette-system.test.mjs'}
CODE = {'src', 'script', 'test', 'scripts', 'tests_python', 'keeper', 'frontend_api', 'indexer', 'zzz_ops'}
SUFFIXES = {'.sol', '.py', '.sh', '.json', '.md', '.txt', '.service', '.timer'}


class BundleError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise BundleError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def path_name(name):
    require(isinstance(name, str) and 0 < len(name) <= 240, 'Invalid member path')
    require(name.isascii() and not any(c in name for c in '\\:*?"<>|') and not any(ord(c) < 32 for c in name),
            'Noncanonical member path')
    parts = PurePosixPath(name).parts
    require(not name.startswith('/') and name == '/'.join(parts) and
            all(p not in ('', '.', '..') for p in parts), 'Unsafe member path')
    require(all(not p.endswith((' ', '.')) for p in parts), 'Ambiguous member path')
    require(all(not re.fullmatch(r'(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p, re.I) for p in parts),
            'Reserved member path')
    return name


def admitted(name):
    path_name(name)
    parts = PurePosixPath(name).parts
    if any(p.startswith('.') for p in parts) and not name.startswith('.github/workflows/') and name != '.gitmodules':
        return False
    if any(p.casefold() in {'secrets', 'keystores', 'credentials'} for p in parts):
        return False
    if name in TOP:
        return True
    if name in FIXTURES or (name.startswith(CATALOG) and name[len(CATALOG):] in CATALOG_FILES):
        return True
    if name.startswith('.github/workflows/'):
        return PurePosixPath(name).suffix in {'.yml', '.yaml'}
    if parts[0] == 'docs':
        return name.endswith('.md') or name in {'docs/project-todo.json',
            'docs/function-reference.json', 'docs/function-reference-notes.json'}
    if parts[0] == 'config':
        return name.endswith('.example.json') or (name.startswith('config/nginx/') and name.endswith('.conf'))
    if parts[0] in CODE:
        if PurePosixPath(name).suffix not in SUFFIXES:
            return False
        if name.endswith('.json') and parts[0] in {'keeper', 'frontend_api', 'indexer'}:
            return name.endswith('.example.json') or name in {'indexer/event_schema.json', 'indexer/historical_event_schema.json'}
        return True
    return False


def git(root, *args, data=None):
    # Argument vectors only; no shell, user refs or credential/environment reads.
    try:
        result = subprocess.run(['git', '--no-replace-objects', '-C', str(root), *args], input=data,
                                capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BundleError('Git snapshot read failed') from None
    require(result.returncode == 0, 'Git snapshot read failed')
    return result.stdout


def frozen_files(root, commit):
    require(isinstance(commit, str) and HEX40.fullmatch(commit), 'Use an exact lowercase 40-character commit')
    actual = git(root, 'rev-parse', '--verify', commit + '^{commit}').decode().strip()
    require(actual == commit, 'Commit identity mismatch')
    tree = git(root, 'rev-parse', commit + '^{tree}').decode().strip()
    records, gitlinks, excluded = [], [], []
    raw_tree = git(root, 'ls-tree', '-r', '-l', '-z', commit)
    require(len(raw_tree) <= 4 * 1024 * 1024, 'Git tree inventory is oversized')
    for raw in raw_tree.split(b'\0'):
        if not raw:
            continue
        meta, raw_name = raw.split(b'\t', 1)
        mode, kind, oid, size = meta.decode('ascii').split()
        name = raw_name.decode('utf-8', 'strict')
        path_name(name)
        if kind == 'commit':
            gitlinks.append({'path': name, 'commit': oid})
            excluded.append({'path': name, 'reason': 'gitlink_dependency_not_bundled'})
            continue
        if not admitted(name):
            excluded.append({'path': name, 'reason': 'outside_review_source_allowlist'})
            continue
        require(mode in ('100644', '100755') and kind == 'blob', 'Review source must be a regular file')
        require(HEX40.fullmatch(oid) and size.isdigit(), 'Malformed Git blob inventory')
        require(int(size) <= MAX_FILE, 'Review source file is oversized')
        records.append({'path': name, 'mode': mode, 'git_blob_sha1': oid, 'size': int(size)})
    require(0 < len(records) <= MAX_MEMBERS - 2, 'Review source member count is invalid')
    require(sum(r['size'] for r in records) <= MAX_TOTAL - 1024 * 1024, 'Review source is oversized')
    records.sort(key=lambda r: r['path'])
    request = ''.join(r['git_blob_sha1'] + '\n' for r in records).encode()
    result = git(root, 'cat-file', '--batch', data=request)
    require(len(result) <= MAX_TOTAL, 'Git blob response is oversized')
    stream, files = io.BytesIO(result), {}
    for record in records:
        header = stream.readline().decode('ascii').strip().split()
        require(header == [record['git_blob_sha1'], 'blob', str(record['size'])], 'Git blob identity mismatch')
        raw = stream.read(record['size'])
        require(len(raw) == record['size'] and stream.read(1) == b'\n', 'Truncated Git blob')
        require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == record['git_blob_sha1'],
                'Git blob content mismatch')
        require(not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----', raw),
                'Private-key marker in review source; inspect before export')
        files[record['path']] = raw
        record['sha256'] = digest(raw)
    require(stream.read() == b'', 'Unexpected Git blob response')
    return tree, records, gitlinks, files, sorted(excluded, key=lambda r: r['path'])


def dependency_record(files, gitlinks):
    required = {'foundry.toml', 'package.json', 'package-lock.json', 'scripts/install-deps.sh'}
    require(required <= files.keys(), 'Compiler/dependency installation inputs are incomplete')
    if 'scripts/generate-artwork-library.py' in files:
        require({CATALOG + 'inventory.json', CATALOG + 'packed-catalog.json'} <= files.keys(),
                'Committed artwork generation fixtures are missing')
    if 'tests_python/test_abi.py' in files:
        require(FIXTURES <= files.keys(), 'Committed ABI verification fixture is missing')
    if 'scripts/generate-function-reference.py' in files:
        require({'docs/function-reference.json', 'docs/function-reference-notes.json',
                 'docs/CONTRACT_FUNCTIONS.md'} <= files.keys(), 'Callable-reference snapshot/explanations are missing')
    require(not gitlinks or '.gitmodules' in files, 'Gitlink source metadata is missing')
    for name in ('package-lock.json', '.gitmodules'):
        if name in files:
            require(not re.search(rb'https?://[^/\s"\x27]+@', files[name]), 'Credential-bearing dependency URL is forbidden')
    profile = tomllib.loads(files['foundry.toml'].decode())['profile']['default']
    require(profile.get('solc_version') == '0.8.26' and profile.get('evm_version') == 'cancun',
            'Unsupported compiler profile; review the bundle schema')
    package, lock = strict_json(files['package.json']), strict_json(files['package-lock.json'])
    declared = package.get('devDependencies', {})
    require(isinstance(declared, dict) and declared and lock.get('lockfileVersion') == 3, 'Unsupported dependency lock')
    require(lock['packages']['']['devDependencies'] == declared, 'Root package/lock mismatch')
    npm = []
    for name, version in sorted(declared.items()):
        require(isinstance(version, str) and re.fullmatch(r'\d+\.\d+\.\d+', version), 'Dependency version is not pinned')
        resolved = lock['packages'].get('node_modules/' + name, {})
        require(resolved.get('version') == version and isinstance(resolved.get('integrity'), str) and
                resolved['integrity'].startswith('sha512-'), 'Dependency integrity is missing')
        npm.append({'name': name, 'version': version, 'integrity': resolved['integrity']})
    pins = re.findall(rb'^forge_std_commit=([0-9a-f]{40})\r?$', files['scripts/install-deps.sh'], re.M)
    require(len(pins) == 1, 'forge-std install pin missing or ambiguous')
    return {'self_contained': False, 'network_fetch_required': True,
            'compiler_profile': profile, 'npm_direct': npm,
            'forge_std_commit': pins[0].decode(), 'gitlinks': gitlinks,
            'installation': 'bash scripts/install-deps.sh; npm ci --ignore-scripts and exact forge-std commit checks',
            'limitations': 'External compiler/npm/forge-std contents and installed binaries are not bundled or qualified.'}


def handoff(commit):
    return f'''# Frozen PoPL review inputs - NOT APPROVED

Source commit: `{commit}`. The archive contains committed source, tests, tooling,
operator documentation, locked dependency inputs and the original task ledger.
No working-tree draft, local runtime state, wallet key, private RPC configuration,
historical test report, deployed runtime or dependency installation is included.
The exact committed artwork catalogue and fixed Keccak vectors are included as
generation/test inputs; the vectors are not historical production-approval evidence.
This export runs no test and makes no production-readiness claim.

Verify the archive against its SHA-256 received over a trusted separate channel.
After verification, inspect the source and install dependencies on an isolated
unprivileged Ubuntu host with Python 3.11+, Foundry 1.4.4 and Solidity 0.8.26.
The bundle is not self-contained: compiler/npm/forge-std downloads need independent
integrity and supply-chain review. Do not supply a real wallet to local rehearsals.

From the extracted `source` directory, after reviewing each command:

```sh
bash scripts/install-deps.sh
bash scripts/verify.sh
python3 scripts/rehearse-keeper.py --offline --output /review/keeper-rehearsal.json
python3 scripts/validate-production-config.py --config config/production.example.json
```

The example validation MUST remain blocked. Local/fixture tests do not qualify
real pools, independent USD feeds, routes, VRF, RPCs, authorities or OpenSea.
Current OpenSea qualification requires explicit mint_integration_version 1 and
production_qualification_supported true in addition to all gate checks and actual
independent review. Legacy consistency-only profiles cannot qualify production.
The vault_direct_v1 mint surface does not establish OpenSea primary compatibility.
`rehearse-keeper.py` starts its own disposable loopback chain and temporary
encrypted signer; it never uses the existing operator's chain or wallet.

Then follow docs/PRODUCTION_PREFLIGHT.md, docs/KEEPER_REHEARSALS.md,
docs/SECURITY_AUDIT_PLAN.md and docs/RELEASE_CHECKLIST.md for exact-configuration
market, target-chain and real-host evidence. No public transaction, deployment,
service action, sealing, or authority appointment is authorized by this export.
Use reviewed separate deployments for any later authorized rehearsal. Preserve
source/configuration/tool hashes, complete logs, explicit substitutes and failures.
Historical evidence is not rebased onto this commit by copying it into a folder.

The independent auditor must review custody/governance trust, shared LP/rewards,
royalty cohorts, price bounds, native reserves, external dependencies, recovery,
same-chain handoff and cross-component operation. Record findings, remediation
and independent sign-off separately. Integrated bridges and post-halt ownership
recovery are deferred; source-chain external custody is not a guaranteed return.

Remaining inputs: actual independently approved dual feeds and cheaper conversion
routes, supported randomness, public authority wallets, exact OpenSea product and
settlement compatibility, qualified RPC/API/keeper hosting, native wallet and
operating/restore rehearsals, published artwork, independent audit and release
approval. The included Todo is the snapshot's source of tasks, not a new checklist.
'''.encode()


def pack(root, commit):
    tree, records, gitlinks, files, excluded = frozen_files(root, commit)
    instructions = handoff(commit)
    manifest = {'schema': 1, 'kind': 'popl-frozen-review-inputs', 'source_commit': commit,
                'source_tree_sha1': tree, 'production_approved': False, 'tests_executed': False,
                'files': records, 'excluded_files': excluded, 'dependencies': dependency_record(files, gitlinks),
                'handoff_sha256': digest(instructions)}
    members = {'HANDOFF.md': instructions, 'manifest.json': canonical(manifest)}
    members.update({'source/' + k: v for k, v in files.items()})
    require(sum(map(len, members.values())) <= MAX_TOTAL, 'Bundle expanded size is oversized')
    modes = {'source/' + r['path']: r['mode'] for r in records}
    return zip_bytes(members, modes), manifest


def zip_bytes(members, modes):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if modes.get(name) == '100755' else 0o100644) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, raw)
    raw = result.getvalue()
    require(len(raw) <= MAX_ARCHIVE, 'Archive is oversized')
    return raw


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate manifest key')
            result[key] = value
        return result
    def reject_constant(value):
        raise BundleError('Nonfinite JSON constant')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)


def verify(raw, expected_sha256):
    require(isinstance(expected_sha256, str) and HEX64.fullmatch(expected_sha256), 'Trusted expected SHA-256 is required')
    require(len(raw) <= MAX_ARCHIVE and digest(raw) == expected_sha256, 'Archive SHA-256 mismatch')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            require(2 < len(infos) <= MAX_MEMBERS, 'Archive member count is invalid')
            names = [path_name(i.filename) for i in infos]
            require(len(set(names)) == len(names) and len({n.casefold() for n in names}) == len(names),
                    'Duplicate or case-colliding member')
            require(names == sorted(names), 'Archive ordering is not canonical')
            require(sum(i.file_size for i in infos) <= MAX_TOTAL, 'Archive expanded size is oversized')
            for info in infos:
                require(not info.is_dir() and info.file_size <= MAX_FILE and info.compress_type == zipfile.ZIP_STORED and
                        info.compress_size == info.file_size and not info.flag_bits & 1 and
                        info.create_system == 3 and info.external_attr >> 16 in (0o100644, 0o100755) and
                        info.date_time == (1980, 1, 1, 0, 0, 0), 'Unsupported or unsafe archive member')
            members = {i.filename: archive.read(i) for i in infos}
        manifest = strict_json(members['manifest.json'])
        require(canonical(manifest) == members['manifest.json'], 'Manifest encoding is not canonical')
        require(set(manifest) == {'schema', 'kind', 'source_commit', 'source_tree_sha1', 'production_approved',
                                 'tests_executed', 'files', 'excluded_files', 'dependencies', 'handoff_sha256'}, 'Unknown manifest shape')
        require(manifest['schema'] == 1 and manifest['kind'] == 'popl-frozen-review-inputs' and
                manifest['production_approved'] is False and manifest['tests_executed'] is False and
                HEX40.fullmatch(manifest['source_commit']) and HEX40.fullmatch(manifest['source_tree_sha1']),
                'Invalid review manifest identity')
        require(digest(members['HANDOFF.md']) == manifest['handoff_sha256'] and
                members['HANDOFF.md'] == handoff(manifest['source_commit']), 'Handoff identity mismatch')
        expected, files, previous = {'manifest.json', 'HANDOFF.md'}, {}, ''
        require(isinstance(manifest['files'], list), 'Manifest file inventory is invalid')
        for record in manifest['files']:
            require(set(record) == {'path', 'mode', 'git_blob_sha1', 'size', 'sha256'}, 'Invalid source record')
            name = path_name(record['path'])
            require(admitted(name) and name > previous, 'Source inventory is not admitted, unique and ordered')
            previous = name
            require(record['mode'] in ('100644', '100755') and type(record['size']) is int and
                    0 <= record['size'] <= MAX_FILE and HEX40.fullmatch(record['git_blob_sha1']) and
                    HEX64.fullmatch(record['sha256']), 'Invalid source metadata')
            member = 'source/' + name
            expected.add(member)
            raw_file = members[member]
            require(len(raw_file) == record['size'] and digest(raw_file) == record['sha256'] and
                    hashlib.sha1(b'blob ' + str(len(raw_file)).encode() + b'\0' + raw_file).hexdigest() == record['git_blob_sha1'],
                    'Source file integrity mismatch')
            require(archive.getinfo(member).external_attr >> 16 == int(record['mode'], 8), 'Source mode mismatch')
            files[name] = raw_file
        require(set(members) == expected, 'Archive contains missing or unlisted members')
        gitlinks = manifest['dependencies']['gitlinks']
        require(isinstance(gitlinks, list) and all(set(x) == {'path', 'commit'} and path_name(x['path']) and
                HEX40.fullmatch(x['commit']) for x in gitlinks), 'Invalid gitlink inventory')
        require(manifest['dependencies'] == dependency_record(files, gitlinks), 'Dependency identity mismatch')
        excluded, last = manifest['excluded_files'], ''
        require(isinstance(excluded, list) and len(excluded) <= 10000, 'Excluded inventory is oversized')
        linked = {x['path'] for x in gitlinks}
        for row in excluded:
            require(set(row) == {'path', 'reason'}, 'Invalid excluded source record')
            name = path_name(row['path'])
            require(name > last and name not in files, 'Excluded source is duplicate or included')
            last = name
            require((row['reason'] == 'outside_review_source_allowlist' and not admitted(name)) or
                    (row['reason'] == 'gitlink_dependency_not_bundled' and name in linked), 'Invalid source exclusion')
        require(linked == {x['path'] for x in excluded if x['reason'] == 'gitlink_dependency_not_bundled'},
                'Excluded Gitlink inventory mismatch')
        modes = {'source/' + r['path']: r['mode'] for r in manifest['files']}
        require(zip_bytes(members, modes) == raw, 'Noncanonical archive bytes or appended data')
        return {'ok': True, 'production_approved': False, 'source_commit': manifest['source_commit'],
                'source_tree_sha1': manifest['source_tree_sha1'], 'source_files': len(files),
                'archive_sha256': expected_sha256, 'tests_executed': False, 'dependencies_bundled': False}
    except BundleError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, zipfile.BadZipFile, RuntimeError):
        raise BundleError('Malformed review archive') from None


def publish(path, raw, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    require(not path.is_relative_to(root), 'Write review archives outside the source repository')
    require(path.suffix == '.zip' and path.parent.is_dir(), 'Use a .zip in an existing external directory')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.popl-review-', dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        # Same-filesystem hard link is atomic and refuses to replace an existing name.
        os.link(temporary, path)
    except FileExistsError:
        raise BundleError('Output already exists; immutable review archive was not replaced') from None
    except OSError:
        raise BundleError('Exclusive atomic archive publication failed') from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('--commit', required=True)
    create.add_argument('--output', required=True, type=Path)
    check = sub.add_parser('verify')
    check.add_argument('--bundle', required=True, type=Path)
    check.add_argument('--expected-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'create':
            raw, _ = pack(ROOT, args.commit)
            result = verify(raw, digest(raw))
            publish(args.output, raw, ROOT)
        else:
            require(args.bundle.stat().st_size <= MAX_ARCHIVE, 'Archive is oversized')
            result = verify(args.bundle.read_bytes(), args.expected_sha256)
        print(json.dumps(result, sort_keys=True))
        return 0
    except BundleError as exc:
        print(json.dumps({'ok': False, 'production_approved': False, 'error': str(exc)}))
        return 1
    except (OSError, KeyError, TypeError, ValueError, UnicodeError):
        # Git stderr, file contents, host paths and arbitrary exception text are not reports.
        print(json.dumps({'ok': False, 'production_approved': False,
                          'error': 'Review bundle rejected; inspect exact inputs and the documented limits.'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
