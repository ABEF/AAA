"""Bounded helpers for this fixed, isolated sidecar-state recovery lab only."""
from pathlib import Path
import base64,gzip,hashlib,json,os,selectors,signal,subprocess,time

LAB=Path('/opt/popl-keeper-sidecar-recovery-20261126-c820')
SOURCE=LAB/'source'
RUNTIME=LAB/'runtime'
PREFIX='popl-keeper-sidecar-recovery-20261126-c820'
JOBS=('checks','source','target')
UNITS=(PREFIX+'.service',*(PREFIX+'-'+job+'.service'for job in JOBS))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(value):return(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def need(value,code='lab_assertion'):
    if not value:raise ValueError(code)

def publish(name,value):
    need(name in ('PROGRESS.json','RESULT.json','SOURCE_RESULT.json','TARGET_RESULT.json',
        'FOCUSED_RESULT.json','FOCUSED_PROGRESS.json','WORKER_LOGS.json','NATIVE_PROPERTIES.json','MANAGER_TRACE.json'))
    raw=enc(value);need(len(raw)<=32768,'evidence_bound')
    temporary=RUNTIME/(name+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,RUNTIME/name)
    fd=os.open(RUNTIME,os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def packed(value):
    raw=enc(value);need(len(raw)<=256*1024,'decoded_evidence_bound')
    return{'decoded_bytes':len(raw),'decoded_sha256':sha(raw),
        'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')}

def read_json(path):
    raw=path.read_bytes();need(len(raw)<=65536,'input_bound');return json.loads(raw)

def file_pin(path):
    raw=path.read_bytes();need(len(raw)<=65536,'file_bound')
    return{'bytes':len(raw),'sha256':sha(raw)}

def run(argv,*,timeout=30,manager=False):
    """Unmasked spawn and signal-masked reap ownership; total64KiB capture."""
    if manager:need(argv[0]in('/usr/bin/systemctl','/usr/bin/systemd-run'))
    else:
        need(argv[:3]==['/usr/bin/python3','-B',str(SOURCE/'scripts/keeper-sidecar-recovery.py')]
            or argv[:3]==['/usr/bin/python3','-B',str(SOURCE/'scripts/keeper-schedule.py')])
    child=owned=None;parts=[bytearray(),bytearray()];size=0;end=time.monotonic()+timeout
    signals={signal.SIGINT,signal.SIGTERM,signal.SIGHUP,signal.SIGALRM}
    try:
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            close_fds=True,start_new_session=True)
        owned=child
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                need(time.monotonic()<end,'process_deadline')
                for key,_ in selector.select(min(.1,max(.001,end-time.monotonic()))):
                    raw=os.read(key.fd,min(16384,65537-size))
                    if not raw:selector.unregister(key.fileobj);continue
                    size+=len(raw);need(size<=65536,'capture_bound');parts[key.data].extend(raw)
        while True:
            need(time.monotonic()<end,'process_deadline')
            prior=signal.pthread_sigmask(signal.SIG_BLOCK,signals)
            try:
                try:code=child.wait(timeout=min(.05,max(.001,end-time.monotonic())))
                except subprocess.TimeoutExpired:continue
                owned=None;return code,bytes(parts[0]),bytes(parts[1])
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,prior)
    finally:
        try:
            if owned is not None:
                prior=signal.pthread_sigmask(signal.SIG_BLOCK,signals)
                try:
                    if owned.returncode is None:
                        try:os.killpg(owned.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                    owned.wait(timeout=2);owned=None
                finally:signal.pthread_sigmask(signal.SIG_SETMASK,prior)
        finally:
            if child is not None:child.stdout.close();child.stderr.close()
