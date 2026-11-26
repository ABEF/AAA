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
EXPECTED=__MEMBERS__
BUNDLE_SHA=__BUNDLE_SHA__
SOURCE_MANIFEST_SHA=__SOURCE_MANIFEST_SHA__
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
