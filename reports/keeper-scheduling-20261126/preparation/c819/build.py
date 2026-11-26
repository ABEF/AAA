"""Offline c819 exact source closure/package preparation; no application imports."""
from pathlib import Path
import argparse
import ast
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

ROOT = Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE = Path(__file__).resolve().parent
HEAD = '03d6caddbe88b552d7edab102cfae0a32847cf37'
NEW = ('keeper/scheduling.py', 'scripts/keeper-schedule.py', 'tests_python/test_keeper_scheduling.py')
TEMPLATES = ('keeper/zzz-keeper-backup.service', 'keeper/zzz-keeper-backup.timer',
    'keeper/zzz-keeper-observer.service', 'keeper/zzz-keeper-observer.timer')
PREPARATION = ('build.py', 'capsule_template.py', 'lab_driver.py', 'hold_lock.py',
    'run_focused_template.py', 'host_control.py')
STATIC = ('reports/ubuntu-backup-recovery-20261126/evidence/c814/model-DRY.json',
    'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json')
HEALTH = ('keeper/monitor.py', 'keeper/ops.py', 'keeper/health.py', 'keeper/rebalance_confirmation.py',
    'keeper/compound_policy.py', 'keeper/cast_process.py', 'zzz_ops/protocol_policy.py',
    'zzz_ops/lp_execution.py', 'zzz_ops/execution_price.py', 'zzz_ops/rebalance_confirmation.py',
    'zzz_ops/abi.py', 'zzz_ops/rpc.py', 'zzz_ops/state.py')
OBSERVER = ('keeper/alerts.py', 'scripts/keeper-alerts.py', 'keeper/recovery_bundle.py', 'scripts/keeper-recovery.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(raw):
    return {'bytes': len(raw), 'sha256': sha(raw)}


def enc(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()


def git(*args):
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
    r = subprocess.run(['git', *args], cwd=ROOT, env=env, capture_output=True, check=True, timeout=30)
    assert len(r.stdout) <= 8*1024*1024
    return r.stdout


def write(name, raw):
    with (BASE/name).open('xb') as stream:
        stream.write(raw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--review-pins', type=Path, required=True)
    a = p.parse_args()
    review = json.loads(a.review_pins.read_bytes())
    assert set(review) == {'source_head', 'reviewed_worktree_files', 'reviewed_preparation_files'}
    assert review['source_head'] == HEAD and git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert set(review['reviewed_worktree_files']) == set(NEW+TEMPLATES)
    assert set(review['reviewed_preparation_files']) == set(PREPARATION)
    preparation = {}
    for name in PREPARATION:
        raw = (BASE/name).read_bytes()
        assert sha(raw) == review['reviewed_preparation_files'][name]
        if name not in ('capsule_template.py', 'run_focused_template.py'):
            ast.parse(raw, filename=name)
        preparation[name] = raw
    overrides = {}
    for name in NEW+TEMPLATES:
        raw = (ROOT/name).read_bytes()
        assert sha(raw) == review['reviewed_worktree_files'][name] and len(raw) <= 1024*1024
        overrides[name] = raw
        if name.endswith('.py'):
            ast.parse(raw, filename=name)
    tree = ast.parse(overrides['tests_python/test_keeper_scheduling.py'])
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'KeeperSchedulingTests')
    assert ast.dump(cls.bases[0]) == "Attribute(value=Name(id='unittest', ctx=Load()), attr='TestCase', ctx=Load())"
    methods = [node.name for node in cls.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    assert len(methods) == len(set(methods)) == 10
    method_pins = {node.name: sha(ast.dump(node, include_attributes=False).encode())
        for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in methods}
    names = set(git('ls-tree', '-r', '--name-only', HEAD).decode().splitlines())
    members = {}
    rows = {}
    edges = {}
    queue = [*NEW, *HEALTH, *OBSERVER]

    def module_path(module):
        stem = module.replace('.', '/')
        return next((name for name in (stem+'.py', stem+'/__init__.py') if name in names or name in overrides), None)

    while queue:
        name = queue.pop(0)
        if name in rows:
            continue
        assert len(rows) < 256
        raw = overrides[name] if name in overrides else git('show', HEAD+':'+name)
        assert len(raw) <= 1024*1024
        body = ast.parse(raw, filename=name)
        members['source/'+name] = raw
        rows[name] = {'stage': 'new_reviewed_worktree' if name in overrides else 'exact_HEAD', **pin(raw)}
        parts = name.split('/')
        for count in range(1, len(parts)):
            package = '/'.join(parts[:count])+'/__init__.py'
            if package in names and package not in rows:
                queue.append(package)
        deps = set()
        for node in ast.walk(body):
            requested = []
            if isinstance(node, ast.Import):
                requested = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level:
                    here = name.removesuffix('.py').replace('/', '.').split('.')[:-1]
                    module = '.'.join(here[:len(here)-node.level+1]+([module] if module else []))
                requested = [module, *[module+'.'+alias.name for alias in node.names if alias.name != '*']]
            for module in requested:
                path = module_path(module)
                if path is not None:
                    deps.add(path)
                elif module.split('.')[0] not in ('keeper', 'zzz_ops', 'frontend_api', 'indexer', 'scripts', 'tests_python'):
                    assert module.split('.')[0] in sys.stdlib_module_names, ('unreviewed_dependency', name, module)
        edges[name] = sorted(deps)
        queue.extend(sorted(deps))
    for name in TEMPLATES:
        members['source/'+name] = overrides[name]
    for name in STATIC:
        raw = (ROOT/name).read_bytes()
        assert raw == git('show', HEAD+':'+name) and len(raw) <= 65536
        members['source/'+name] = raw
    for name in ('lab_driver.py', 'hold_lock.py'):
        members['source/'+name] = preparation[name]
    focused = preparation['run_focused_template.py'].decode().replace('__METHODS__', repr(tuple(methods)))
    ast.parse(focused)
    members['source/run_focused.py'] = focused.encode()
    manifest = {'schema': 1, 'source_head': HEAD, 'new_methods': methods,
        'new_method_AST_sha256': method_pins, 'source_files': rows, 'static_import_edges': edges,
        'new_reviewed_worktree_files': list(NEW+TEMPLATES),
        'old_helper_setup_only': ['tests_python/test_keeper_alerts.py'], 'old_test_bodies_run': 0,
        'daemon13_unchanged': True, 'no_Keeper_Cast_RPC_Anvil_or_signer': True,
        'lab_only_timers_seconds': {'backup': 6, 'observe': 3},
        'reviewed_preparation_sha256': review['reviewed_preparation_files'],
        'members': {name: pin(raw) for name, raw in members.items()}}
    manifest_raw = enc(manifest)
    members['SOURCE_MANIFEST.json'] = manifest_raw
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, raw in sorted(members.items()):
                item = tarfile.TarInfo(name)
                item.size = len(raw)
                item.mode = 0o444
                item.uid = item.gid = 0
                item.uname = item.gname = 'root'
                item.mtime = 0
                archive.addfile(item, io.BytesIO(raw))
    bundle = buffer.getvalue()
    assert len(bundle) <= 2*1024*1024 and sum(map(len, members.values())) <= 8*1024*1024
    controller = preparation['capsule_template.py'].decode().replace('__MEMBERS__', repr({n: pin(r) for n, r in members.items()}))
    controller = controller.replace('__BUNDLE_SHA__', repr(sha(bundle))).replace('__SOURCE_MANIFEST_SHA__', repr(sha(manifest_raw)))
    ast.parse(controller)
    assert len(controller.encode()) <= 65536
    assert all((BASE/name).read_bytes() == raw for name, raw in preparation.items())
    assert all((ROOT/name).read_bytes() == raw for name, raw in overrides.items())
    write('c819.inputs.tar.gz', bundle)
    write('SOURCE_MANIFEST.json', manifest_raw)
    write('run_focused.py', focused.encode())
    write('remote_capsule.py', controller.encode())
    receipt = {'schema': 1, 'source_head': HEAD, 'bundle': pin(bundle), 'controller': pin(controller.encode()),
        'source_manifest': pin(manifest_raw), 'focused_runner': pin(focused.encode()),
        'source_members': len(rows), 'archive_members': len(members), 'new_method_count': len(methods),
        'new_methods': methods, 'tests_run': 0, 'network_or_server_actions': 0,
        'root_driver_only_caps': ['CHOWN', 'DAC_OVERRIDE', 'FOWNER'], 'worker_caps_empty': True,
        'driver_timeout_seconds': 180, 'work_target_seconds': 165, 'capture_bytes': 65536,
        'existing_environment_adoption': False, 'production_approved': False}
    write('BUILD_RECEIPT.json', enc(receipt))
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
