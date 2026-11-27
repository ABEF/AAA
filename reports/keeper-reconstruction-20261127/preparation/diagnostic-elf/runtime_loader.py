"""Fixed c824 failure diagnosis: private loader stderr and actual OS ELF aliases."""
from pathlib import Path
import base64,hashlib,json,os,selectors,signal,stat,subprocess,time

STDERR=Path('/opt/popl-keeper-reconstruction-20261127-c824/negative-root/reconstruction/runtime/stderr.log')
LIB=Path('/usr/lib/x86_64-linux-gnu')
CANONICAL={'ld-linux-x86-64.so.2','libbz2.so.1.0.4','libc.so.6','libcrypto.so.3',
    'libexpat.so.1.9.1','liblzma.so.5.4.5','libm.so.6','libssl.so.3','libz.so.1.3'}
LDD_TARGETS=('/usr/bin/python3',
    '/usr/lib/python3.12/lib-dynload/_bz2.cpython-312-x86_64-linux-gnu.so',
    '/usr/lib/python3.12/lib-dynload/_lzma.cpython-312-x86_64-linux-gnu.so')
END=time.monotonic()+20
sha=lambda raw:hashlib.sha256(raw).hexdigest()
key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def need(value):
    if not value:raise ValueError('fixed_loader_diagnostic_refused')


def stderr():
    before=STDERR.lstat();need(stat.S_ISREG(before.st_mode)and before.st_uid==65534 and before.st_nlink==1
        and not before.st_mode&0o077 and 0<=before.st_size<=65536)
    fd=os.open(STDERR,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        need(key(before)==key(os.fstat(fd)));raw=os.read(fd,65537)
        need(len(raw)==before.st_size and key(before)==key(os.fstat(fd))==key(STDERR.lstat()))
    finally:os.close(fd)
    return{'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}


def libraries():
    before=LIB.lstat();need(stat.S_ISDIR(before.st_mode)and before.st_uid==0 and not before.st_mode&0o022)
    links={};found={};visited=0
    with os.scandir(LIB)as entries:
        for entry in entries:
            visited+=1;need(visited<=8192 and time.monotonic()<END)
            item=entry.stat(follow_symlinks=False)
            if entry.name in CANONICAL:
                need(stat.S_ISREG(item.st_mode)and item.st_uid==0 and item.st_nlink==1 and not item.st_mode&0o022)
                found[entry.name]={'type':'regular','uid':item.st_uid,'mode':stat.S_IMODE(item.st_mode),
                    'link_count':item.st_nlink,'bytes':item.st_size}
                need(key(item)==key(Path(entry.path).lstat()))
            elif stat.S_ISLNK(item.st_mode):
                target=os.readlink(entry.path);need(len(target)<=512)
                links[entry.name]=(target,item)
    need(set(found)==CANONICAL and key(before)==key(LIB.lstat()))
    def destination(name):
        seen=set()
        for _ in range(8):
            if name in CANONICAL:return name
            if name in seen or name not in links:return None
            seen.add(name);target=links[name][0]
            candidate=Path(os.path.normpath(target if target.startswith('/')else str(LIB/target)))
            if candidate.parent!=LIB:return None
            name=candidate.name
        return None
    aliases=[]
    for name,(target,item)in sorted(links.items()):
        canonical=destination(name)
        if canonical is None:continue
        need(len(aliases)<32 and time.monotonic()<END)
        path=LIB/name;need(item.st_uid==0 and item.st_nlink==1 and key(item)==key(path.lstat())and os.readlink(path)==target)
        aliases.append({'name':name,'target':target,'canonical':canonical,'type':'symlink',
            'uid':item.st_uid,'mode':stat.S_IMODE(item.st_mode),'link_count':item.st_nlink})
    return{'directory':str(LIB),'visited_entries':visited,'canonical_files':found,'aliases':aliases,
        'symlink_targets_followed_or_opened':False}


def ldd(target):
    need(target in LDD_TARGETS and time.monotonic()<END)
    child=owned=None;parts=[bytearray(),bytearray()];size=0;end=min(END,time.monotonic()+5)
    try:
        child=subprocess.Popen(['/usr/bin/ldd',target],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            env={'PATH':'/usr/bin:/bin','LANG':'C'},start_new_session=True,close_fds=True);owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end)
                for selected,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(selected.fd,min(8192,8193-size))
                    if not raw:selector.unregister(selected.fileobj);continue
                    size+=len(raw);need(size<=8192);parts[selected.data].extend(raw)
        code=child.wait(timeout=max(.001,end-time.monotonic()));owned=None
        return{'target':target,'exit_code':code,'stdout':bytes(parts[0]).decode('utf8','strict'),
            'stderr':bytes(parts[1]).decode('utf8','strict'),'combined_output_bytes':size}
    finally:
        try:
            if owned is not None:
                if owned.poll()is None:
                    try:os.killpg(owned.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                owned.wait(timeout=2)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()


def main():
    try:
        result={'schema':1,'kind':'popl-c824-loader-and-OS-alias-diagnostic','private_loader_stderr':stderr(),
            'OS_library_metadata':libraries(),'ldd':[ldd(target)for target in LDD_TARGETS],
            'application_imports':0,'native_keeper_calls':0,'service_actions':0,'host_mutations':0,
            'configuration_or_journal_or_signer_files_accessed':False}
    except Exception as exc:
        result={'schema':1,'kind':'popl-c824-loader-and-OS-alias-diagnostic','refused':True,'error_type':type(exc).__name__}
    raw=(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();need(len(raw)<=16384)
    print(raw.decode('utf8'),end='');return 1 if result.get('refused')else 0


if __name__=='__main__':raise SystemExit(main())
