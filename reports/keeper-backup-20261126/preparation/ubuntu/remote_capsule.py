"""Fixed c812 unsigned file-only capsule. Execute only after root review."""
from pathlib import Path,PurePosixPath
import hashlib
import io
import json
import os
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import time

LAB=Path('/opt/popl-keeper-backup-20261126-c812')
EXPECTED={'source/keeper/monitor.py': {'bytes': 194496, 'sha256': '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'}, 'source/keeper/ops.py': {'bytes': 13932, 'sha256': 'a81eb06001024f11f751691ba2b8fd7f37605f10feba925006bf57242751fa6b'}, 'source/keeper/health.py': {'bytes': 24415, 'sha256': 'dd25d2151295d09dcdebc4b0331b82c8d2b384a5501b49d0bfeb483d396b5c04'}, 'source/keeper/rebalance_confirmation.py': {'bytes': 11926, 'sha256': '6cc29d78aaf4c3804379e9b15d0ff177ff537da1158e66a3111ae2c85d6d317d'}, 'source/keeper/compound_policy.py': {'bytes': 17260, 'sha256': '129d330417c37747e16456fd18c892550cf870bdad31847e328b42a5c7270e29'}, 'source/keeper/cast_process.py': {'bytes': 4617, 'sha256': 'b6203067b022625bce2bfb415bb6ed85620dc8c7002b51f2d3d4c9296c5ac3e1'}, 'source/zzz_ops/protocol_policy.py': {'bytes': 5907, 'sha256': '4d73e7a3f6d6b98c91f083e2c557a48259ac9bcc0dbe2fb7752f74c4335bb5c3'}, 'source/zzz_ops/lp_execution.py': {'bytes': 6860, 'sha256': '90c985622387a4de8d52dd075856a4cf25e8c2e5bc62f4a3490978fc8cf746b0'}, 'source/zzz_ops/execution_price.py': {'bytes': 2280, 'sha256': '1d0ff892d43ec450438e7d2a1c2f783e6d9f9aec66f1fe98e3c35f5b09de47e2'}, 'source/zzz_ops/rebalance_confirmation.py': {'bytes': 17194, 'sha256': '77a41f2520be5d5c6768505e7bfe75f68db79d37f611062750ecd02f58185331'}, 'source/zzz_ops/abi.py': {'bytes': 4797, 'sha256': 'c4c755f1a9bf8db70b1ecb81e2b4e6765581961289f6f550502983e375293d91'}, 'source/zzz_ops/rpc.py': {'bytes': 9709, 'sha256': '6b76610b1bc042196198657e069b30ef1009aff3237d71979e8d21495fb6380f'}, 'source/zzz_ops/state.py': {'bytes': 4644, 'sha256': '78985688f9fc0cebf4aa5912b1401a338ac1e9ce21d8c787393e0e2d421976cf'}, 'source/reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json': {'bytes': 7965, 'sha256': '70b4e6081c561092d7c7cadf173da48180b912839818ee262c2cf830b83e463f'}, 'source/reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-FINAL_JOURNAL.json': {'bytes': 5831, 'sha256': 'bad79f40b335fe06ac7587c054ecbffeb8e835c8ca7257f795758b5ebdc26292'}, 'source/keeper/__init__.py': {'bytes': 1, 'sha256': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b'}, 'source/keeper/recovery_bundle.py': {'bytes': 36223, 'sha256': 'fe1185f008e047a3c7447bc2dc36e748f1ecff3a7ca6f1552114ad236060f268'}, 'source/scripts/keeper-recovery.py': {'bytes': 3423, 'sha256': '450b87f611b90d2cdb4139bd2bb2cc8f10696821c1ae6b72ccba7613a64ff6cf'}, 'source/tests_python/test_keeper_recovery_bundle.py': {'bytes': 38398, 'sha256': 'e7ba697edee57e08dcf4e40e55633a2cb82b76ae592a8ebea2489c66aea016d9'}, 'source/run_selected.py': {'bytes': 3517, 'sha256': '819bd9f1dedfffbbe2e2225753f0f8add8e0eb8de614b5337c5c92689005c8bd'}, 'SOURCE_MANIFEST.json': {'bytes': 5007, 'sha256': 'b943bd4a2ff62ad73e6319eeab3da69c15faeeb5dd58748d17c1e553d0ff7320'}}
BUNDLE_SHA='43f4a2ec6aeba418db3ed8aa9be24c54e130966a3045b18cd0769f14f118a59d'
SOURCE_MANIFEST_SHA='b943bd4a2ff62ad73e6319eeab3da69c15faeeb5dd58748d17c1e553d0ff7320'
MAX_ARCHIVE=2*1024*1024
child=None
controller_end=0
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def need(value):
    if not value:raise ValueError('Fixed isolated recovery selection refused')


def group_members(pgid):
    found=[];count=0
    for entry in Path('/proc').iterdir():
        count+=1;need(count<=10000 and time.monotonic()<controller_end)
        if not entry.name.isdecimal():continue
        try:
            raw=(entry/'stat').read_bytes()
            if len(raw)>4096:continue
            fields=raw.rsplit(b') ',1)[1].split()
            if int(fields[2])==pgid:found.append(int(entry.name))
        except (OSError,ValueError,IndexError):pass
    return sorted(found)


def drop_identity():
    os.setgroups([]);os.setgid(65534);os.setuid(65534)
    signal.pthread_sigmask(signal.SIG_SETMASK,set())


def reap(process,timeout):
    global child
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT})
    try:
        code=process.wait(timeout=timeout)
        child=None  # Clear ownership before deferred signals can run.
        return code
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)


def halt(*_):
    if child is not None:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        try:reap(child,2)
        except subprocess.TimeoutExpired:pass
    raise TimeoutError('Fixed isolated controller deadline')


def main():
    global child,controller_end
    need(os.geteuid()==0 and not os.path.lexists(LAB))
    controller_end=time.monotonic()+110
    for signum in (signal.SIGTERM,signal.SIGHUP,signal.SIGALRM,signal.SIGINT):signal.signal(signum,halt)
    signal.alarm(110)
    raw=sys.stdin.buffer.read(MAX_ARCHIVE+1)
    need(0<len(raw)<=MAX_ARCHIVE and sha(raw)==BUNDLE_SHA)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz')as archive:
        data={};expanded=0
        for item in archive:
            need(len(data)<len(EXPECTED)and item.name not in data)
            need(item.isfile()and item.name==str(PurePosixPath(item.name))and not item.name.startswith('/')
                and '..'not in PurePosixPath(item.name).parts and '\\'not in item.name and ':'not in item.name)
            need(item.name in EXPECTED and 0<=item.size<=1024*1024)
            expanded+=item.size;need(expanded<=8*1024*1024)
            value=archive.extractfile(item).read(1024*1024+1)
            need(EXPECTED[item.name]=={'bytes':len(value),'sha256':sha(value)})
            data[item.name]=value
    need(set(data)==set(EXPECTED))
    need(sha(data['SOURCE_MANIFEST.json'])==SOURCE_MANIFEST_SHA)
    manifest=json.loads(data['SOURCE_MANIFEST.json'])
    need(manifest['selected_methods']==[
        'test_posix_private_output_modes_and_writable_parent_refusal',
        'test_posix_atomic_source_replace_during_open_fd_capture_refuses_without_rollback',
        'test_symlink_source_parent_and_package_payload_are_refused'])
    LAB.mkdir(mode=0o755);os.chmod(LAB,0o755)
    for name,value in sorted(data.items()):
        path=LAB/name
        for folder in reversed(path.parent.parents):
            if folder==LAB or folder.is_relative_to(LAB):
                folder.mkdir(exist_ok=True,mode=0o755);os.chmod(folder,0o755)
        path.parent.mkdir(exist_ok=True,mode=0o755);os.chmod(path.parent,0o755)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
        os.fchmod(fd,0o444)
        with os.fdopen(fd,'wb')as f:f.write(value);f.flush();os.fsync(f.fileno())
    runtime=LAB/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
    for name in ('tmp','home'):
        p=runtime/name;p.mkdir(mode=0o700);os.chown(p,65534,65534)
    def identity():
        result={}
        for name,expected in EXPECTED.items():
            p=LAB/name;st=p.lstat();need(stat.S_ISREG(st.st_mode)and st.st_uid==0 and not st.st_mode&0o222)
            need(st.st_size==expected['bytes'])
            value=p.read_bytes();need(expected=={'bytes':len(value),'sha256':sha(value)})
            result[name]=sha(value)
        return result
    before=identity();started=time.monotonic()
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(LAB/'source'),
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONUNBUFFERED':'1',
        'TMPDIR':str(runtime/'tmp'),'HOME':str(runtime/'home')}
    argv=['/usr/bin/python3','-B',str(LAB/'source/run_selected.py')]
    previous=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT})
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            cwd=LAB/'source',env=env,start_new_session=True,preexec_fn=drop_identity,close_fds=True)
        process=child  # Publish ownership before pending cleanup signals run.
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous)
    buffers=[bytearray(),bytearray()];size=0;failure=None;complete_wait=False;group_before_wait=[]
    deadline=time.monotonic()+90
    try:
        with selectors.DefaultSelector()as sel:
            for index,pipe in enumerate((process.stdout,process.stderr)):
                os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,index)
            while sel.get_map():
                if time.monotonic()>=deadline:failure='selection_timeout';break
                for key,_ in sel.select(min(.1,max(.001,deadline-time.monotonic()))):
                    value=os.read(key.fd,min(16384,65537-size))
                    if not value:sel.unregister(key.fileobj);continue
                    size+=len(value)
                    if size>65536:failure='selection_output_limit';break
                    buffers[key.data].extend(value)
                if failure:break
        if failure is None:
            group_before_wait=group_members(process.pid)
            need(set(group_before_wait)<={process.pid})
            try:reap(process,max(.001,deadline-time.monotonic()));complete_wait=True
            except subprocess.TimeoutExpired:failure='selection_timeout'
    finally:
        if child is not None:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            reap(process,2)
        complete_wait=process.returncode is not None
        process.stdout.close();process.stderr.close()
    after=identity();left=group_members(process.pid)
    result_path=runtime/'RESULT.json';st=result_path.lstat()
    need(stat.S_ISREG(st.st_mode)and st.st_uid==65534 and st.st_nlink==1 and
        stat.S_IMODE(st.st_mode)==0o600 and 0<st.st_size<=65536)
    fd=os.open(result_path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        opened=os.fstat(fd);need((opened.st_dev,opened.st_ino)==(st.st_dev,st.st_ino))
        result_raw=os.read(fd,65537)
        after_read=os.fstat(fd);need(after_read.st_size==st.st_size==len(result_raw))
    finally:os.close(fd)
    named=result_path.lstat();need((named.st_dev,named.st_ino)==(st.st_dev,st.st_ino))
    result=json.loads(result_raw)
    success=(failure is None and process.returncode==0 and complete_wait and not left and
        result.get('success')is True and result.get('tests_run')==3 and result.get('skipped')==0)
    signal.alarm(0)
    print(json.dumps({'schema':1,'success':success,'lab':str(LAB),'source_manifest_sha256':SOURCE_MANIFEST_SHA,
        'source_before':before,'source_after':after,'source_files_unchanged':before==after,
        'selected_result':result,'result_sha256':sha(result_raw),'returncode':process.returncode,
        'stdout_sha256':sha(buffers[0]),'stderr_sha256':sha(buffers[1]),'combined_output_bytes':size,
        'capture_failure':failure,'child_pid':process.pid,'child_wait_complete':complete_wait,
        'group_before_wait':group_before_wait,'group_after_wait':left,'elapsed_seconds':time.monotonic()-started,
        'services_changed':False,'existing_environments_changed':False,'signing_attempts':0,
        'public_transactions':0,'old_test_bodies_run':0},sort_keys=True))
    return 0 if success else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'success':False,'error_type':type(exc).__name__,'fixed_reason':'isolated_file_selection_refused'}))
        raise SystemExit(1)from None
