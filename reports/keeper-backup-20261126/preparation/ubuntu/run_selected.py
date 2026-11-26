"""Exactly three NEW unsigned file-only methods; no action on import."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import os
import signal
import socket
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parent
RUNTIME=Path('/opt/popl-keeper-backup-20261126-c812/runtime')
SELECTED=(
 'test_posix_private_output_modes_and_writable_parent_refusal',
 'test_posix_atomic_source_replace_during_open_fd_capture_refuses_without_rollback',
 'test_symlink_source_parent_and_package_payload_are_refused',
)


def deny(*_,**__):raise AssertionError('Forbidden isolated recovery side effect')


class BoundedStream:
    def __init__(self):self.parts=[];self.size=0
    def write(self,value):
        raw=value.encode('utf8');self.size+=len(raw)
        if self.size>65536:raise ValueError('Bounded test diagnostic overflow')
        self.parts.append(value)
    def flush(self):pass


def timeout(*_):raise TimeoutError('Isolated selection deadline')


def main():
    assert os.getuid()==os.getgid()==65534 and os.getgroups()==[] and os.name=='posix'
    assert os.environ['TMPDIR']==str(RUNTIME/'tmp')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
    signal.signal(signal.SIGALRM,timeout);signal.alarm(90)
    socket.create_connection=deny;socket.socket.connect=deny;subprocess.Popen=deny
    spec=importlib.util.spec_from_file_location('selected_new_keeper_recovery',ROOT/'tests_python/test_keeper_recovery_bundle.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite=unittest.TestSuite(module.KeeperRecoveryBundleTests(name)for name in SELECTED)
    stream=BoundedStream();started=time.monotonic()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    names={case.id().rsplit('.',1)[-1]for case,_ in result.errors+result.failures+result.skipped}
    failed={case.id().rsplit('.',1)[-1]:hashlib.sha256(detail.encode()).hexdigest()
        for case,detail in result.errors+result.failures}
    value={'schema':1,'selected_methods':list(SELECTED),'tests_run':result.testsRun,
        'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped),
        'method_outcomes':{name:'failed'if name in failed else'skipped'if name in names else'passed'for name in SELECTED},
        'error_digests_only':failed,'diagnostic_sha256':hashlib.sha256(''.join(stream.parts).encode()).hexdigest(),
        'diagnostic_bytes':stream.size,'elapsed_seconds':time.monotonic()-started,
        'uid':os.getuid(),'gid':os.getgid(),'supplementary_groups':os.getgroups(),
        'network_and_Popen_guards':True,'services_changed':False,'signing_attempts':0,
        'old_test_bodies_run':0,'previously_green_portable_methods_run':0,
        'success':result.wasSuccessful()and result.testsRun==3 and not result.skipped}
    fd=os.open(RUNTIME/'RESULT.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w',encoding='utf8')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    signal.alarm(0)
    print(json.dumps({'selected_new_methods':3,'success':value['success'],'test_errors_or_failures':len(failed)}))
    return 0 if value['success']else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'selected_run_failed':True,'error_type':type(exc).__name__}),file=sys.stderr)
        raise SystemExit(1)from None
