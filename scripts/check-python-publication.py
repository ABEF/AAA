"""Check static repository Python imports in exact Git blobs, never local extras.

This reads Git only. It executes no package code, tests, RPC or signing. Dynamic
imports and third-party installation/version correctness remain separate checks.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('frontend_api', 'keeper', 'zzz_ops', 'indexer', 'tests_python', 'scripts')
DIRECTORIES = PACKAGES


def check_sources(sources):
    modules = {path[:-3].replace('/', '.'): path for path in sources if path.endswith('.py')}
    packages = {name[:-9] for name in modules if name.endswith('.__init__')}
    # Namespace packages are valid; no missing __init__.py is inferred.
    for name in modules:
        parts = name.split('.')
        packages.update('.'.join(parts[:n]) for n in range(1, len(parts)))
    exports = {}
    for package in packages:
        init = modules.get(package+'.__init__')
        names = set()
        if init is not None:
            try:
                body = ast.parse(sources[init], filename=init)
                for item in ast.walk(body):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        names.add(item.name)
                    elif isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                        names.add(item.id)
                    elif isinstance(item, (ast.Import, ast.ImportFrom)):
                        names.update(alias.asname or alias.name.split('.')[0] for alias in item.names)
            except (SyntaxError, ValueError):
                pass  # The source pass below records the syntax failure.
        exports[package] = names
    errors = []
    for path, raw in sorted(sources.items()):
        if not path.endswith('.py'):
            continue
        try:
            tree = ast.parse(raw, filename=path)
        except (SyntaxError, ValueError) as exc:
            errors.append(dict(file=path, line=getattr(exc, 'lineno', None), error='invalid_python_syntax'))
            continue
        here = path[:-3].replace('/', '.').split('.')[:-1]
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level > len(here):
                        errors.append(dict(file=path, line=node.lineno, error='relative_import_beyond_package'))
                        continue
                    base = here[:len(here)-node.level+1]
                    target = '.'.join((*base, *((node.module or '').split('.') if node.module else ())))
                else:
                    target = node.module or ''
                targets = [target]
                if target in packages and '__getattr__' not in exports[target]:
                    # ``from package import submodule`` must not be hidden by
                    # an untracked submodule. Explicit __init__ exports remain
                    # valid without importing or executing that package.
                    targets.extend(target+'.'+item.name for item in node.names
                        if item.name != '*' and item.name not in exports[target])
            for target in targets:
                if target.split('.')[0] in PACKAGES and target not in modules and target not in packages:
                    errors.append(dict(file=path, line=node.lineno, missing_module=target))
    return errors


def git(*args, input=None):
    return subprocess.run(['git', *args], cwd=ROOT, input=input, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True, timeout=30).stdout


def read_sources(revision=None, index=False):
    if index:
        entries = git('ls-files', '--stage', '-z', '--', *DIRECTORIES)
        identity = 'index'
    else:
        identity = git('rev-parse', '--verify', (revision or 'HEAD')+'^{commit}').decode('ascii').strip()
        entries = git('ls-tree', '-r', '-z', identity, '--', *DIRECTORIES)
    blobs = []
    for item in entries.split(b'\0'):
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        path = name.decode('utf-8')
        parts = metadata.split()
        if index and parts[2] != b'0':
            raise ValueError('Unmerged Git index cannot establish publication closure')
        if path.endswith('.py'):
            blobs.append((path, parts[1] if index else parts[2]))
    query = b''.join(digest+b'\n' for _path, digest in blobs)
    stream = git('cat-file', '--batch', input=query)
    offset = 0
    sources = {}
    for path, digest in blobs:
        end = stream.index(b'\n', offset)
        header = stream[offset:end].split()
        if len(header) != 3 or header[0] != digest or header[1] != b'blob':
            raise ValueError('Git blob identity differs')
        size = int(header[2])
        offset = end+1
        sources[path] = stream[offset:offset+size]
        offset += size+1
        if stream[offset-1:offset] != b'\n':
            raise ValueError('Malformed Git blob stream')
    if offset != len(stream):
        raise ValueError('Unexpected Git blob tail')
    return identity, sources


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--revision', default=None, help='Exact commit/ref; defaults to HEAD')
    choice.add_argument('--index', action='store_true', help='Review staged publication bytes, excluding untracked files')
    args = parser.parse_args(argv)
    identity, sources = read_sources(args.revision, args.index)
    errors = check_sources(sources)
    report = dict(kind='static_python_publication_closure', revision=identity,
        successful=not errors, files=len(sources), errors=errors,
        source_sha256={path:hashlib.sha256(raw).hexdigest() for path, raw in sorted(sources.items())},
        limitations=['Static module imports only; dynamic imports, wildcard and dynamic package exports require separate coverage',
            'Third-party dependencies and runtime behavior are not verified',
            'Working-tree and untracked files never satisfy Git publication imports'])
    print(json.dumps(report, sort_keys=True))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
