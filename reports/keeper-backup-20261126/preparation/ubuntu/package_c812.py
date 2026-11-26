"""Offline c812 exact source selection and closed-capsule preparation only."""
from pathlib import Path
import ast
import gzip
import hashlib
import io
import json
import subprocess
import tarfile

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='f36b848278479ca1cb9499d5fa831757b1e34c45'
HEALTH=(
 'keeper/monitor.py','keeper/ops.py','keeper/health.py','keeper/rebalance_confirmation.py',
 'keeper/compound_policy.py','keeper/cast_process.py','zzz_ops/protocol_policy.py',
 'zzz_ops/lp_execution.py','zzz_ops/execution_price.py','zzz_ops/rebalance_confirmation.py',
 'zzz_ops/abi.py','zzz_ops/rpc.py','zzz_ops/state.py')
NEW=('keeper/recovery_bundle.py','scripts/keeper-recovery.py','tests_python/test_keeper_recovery_bundle.py')
STATIC=('reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json',
 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-FINAL_JOURNAL.json')
SELECTED=(
 'test_posix_private_output_modes_and_writable_parent_refusal',
 'test_posix_atomic_source_replace_during_open_fd_capture_refuses_without_rollback',
 'test_symlink_source_parent_and_package_payload_are_refused')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()


def git(*args):
    return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=True,timeout=30).stdout


def write(name,raw):
    with (BASE/name).open('xb')as stream:stream.write(raw)


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    data={}
    for name in (*HEALTH,*STATIC,'keeper/__init__.py'):
        raw=(ROOT/name).read_bytes();assert raw==git('show',HEAD+':'+name)
        data['source/'+name]=raw
    assert not ast.parse(data['source/keeper/__init__.py']).body
    for name in NEW:
        raw=(ROOT/name).read_bytes();ast.parse(raw);data['source/'+name]=raw
    assert sha(data['source/keeper/recovery_bundle.py'])=='fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268'
    assert sha(data['source/scripts/keeper-recovery.py'])=='450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'
    assert sha(data['source/tests_python/test_keeper_recovery_bundle.py'])=='e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9'
    runner=(BASE/'run_selected.py').read_bytes();ast.parse(runner);data['source/run_selected.py']=runner
    test_text=data['source/tests_python/test_keeper_recovery_bundle.py'].decode();tree=ast.parse(test_text)
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef)and node.name=='KeeperRecoveryBundleTests')
    methods={node.name:node for node in cls.body if isinstance(node,ast.FunctionDef)}
    selected={name:sha(ast.dump(methods[name],include_attributes=False).encode())for name in SELECTED}
    manifest={'schema':1,'source_head':HEAD,'selected_methods':list(SELECTED),'selected_method_AST_sha256':selected,
        'members':{name:pin(raw)for name,raw in sorted(data.items())},
        'unchanged_health_sources_from_HEAD':list(HEALTH),'new_working_tree_source_files':list(NEW),
        'static_published_fixtures_only':list(STATIC),'unsigned_file_tests_only':True,
        'previously_green_portable_methods_selected':0,'service_or_signing_actions':0,
        'current_windows_stage':{'methods_run':31,'passes':30,'symlink_skip':1,'POSIX_methods_not_run':2}}
    manifest_raw=enc(manifest);data['SOURCE_MANIFEST.json']=manifest_raw
    out=io.BytesIO()
    with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0)as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(data.items()):
                info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o444;info.uid=info.gid=0;info.uname=info.gname='root';info.mtime=0
                archive.addfile(info,io.BytesIO(raw))
    bundle=out.getvalue();assert len(bundle)<=2*1024*1024
    capsule=(BASE/'capsule_template.py').read_text().replace('__MEMBERS__',repr({name:pin(raw)for name,raw in data.items()})).replace(
        '__BUNDLE_SHA__',repr(sha(bundle))).replace('__SOURCE_MANIFEST_SHA__',repr(sha(manifest_raw)))
    ast.parse(capsule)
    write('c812.inputs.tar.gz',bundle);write('SOURCE_MANIFEST.json',manifest_raw);write('remote_capsule.py',capsule.encode())
    receipt={'schema':1,'bundle':pin(bundle),'controller':pin(capsule.encode()),'source_manifest':pin(manifest_raw),
        'runner':pin(runner),'local_preparation_only':True,'tests_run':0,'network_calls':0,'service_changes':0,
        'selected_new_methods':list(SELECTED),'source_members':len(data)-1,'archive_members':len(data),
        'process_uid_gid':65534,'child_work_seconds':90,'combined_output_bytes':65536,'failure_cleanup_seconds':2}
    write('BUILD_RECEIPT.json',enc(receipt));print(json.dumps(receipt))


if __name__=='__main__':main()
