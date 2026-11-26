"""Only the reviewed affected day-audit method, in the fixed c817 private unit."""
from pathlib import Path
import contextlib,hashlib,importlib.util,json,os,resource,signal,socket,subprocess,sys,time,unittest

ROOT=Path(__file__).resolve().parent
RUNTIME=Path('/opt/popl-keeper-day-audit-20261126-c817/runtime')
SELECTION=__SELECTION__
SELECTED=__SELECTED__

def deny(*_,**__):raise AssertionError('Forbidden day-audit side effect')

def publish(name,value):
    assert name in ('PROGRESS.json','RESULT.json')
    raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();assert len(raw)<=65536
    temporary=RUNTIME/(name+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,RUNTIME/name)
    directory=os.open(RUNTIME,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(directory)
    finally:os.close(directory)

class BoundedStream:
    def __init__(self):self.parts=[];self.size=0
    def write(self,value):
        raw=value.encode('utf8');self.size+=len(raw)
        if self.size>65536:raise ValueError('Bounded day-audit diagnostics exceeded')
        self.parts.append(value)
    def flush(self):pass

def method_id(test):return '.'.join(test.id().rsplit('.',2)[-2:])

class TrackedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.started=[];self.finished=[];self.outcomes={};self.error_locations={}
    def progress(self):
        publish('PROGRESS.json',{'schema':1,'selected_methods':list(SELECTED),'started':self.started,
            'finished':self.finished,'method_outcomes':self.outcomes,'error_locations':self.error_locations,
            'old_test_bodies_run':0,'production_approved':False})
    def startTest(self,test):
        name=method_id(test)
        if name not in SELECTED or name in self.started:raise AssertionError('Unreviewed or repeated day-audit method')
        self.started.append(name);self.outcomes[name]='entered';self.progress();super().startTest(test)
    def stopTest(self,test):
        self.finished.append(method_id(test));self.progress();super().stopTest(test)
    def details(self,test,err):
        name=method_id(test);frames=[];tb=err[2]
        while tb is not None:
            path=Path(tb.tb_frame.f_code.co_filename)
            try:label=path.relative_to(ROOT).as_posix()
            except ValueError:label='stdlib'
            frames.append({'file':label,'line':tb.tb_lineno,'function':tb.tb_frame.f_code.co_name[:80]})
            tb=tb.tb_next
        self.error_locations[name]={'exception_type':err[0].__name__,'frames':frames[-8:]}
    def addSuccess(self,test):self.outcomes[method_id(test)]='passed';super().addSuccess(test)
    def addError(self,test,err):
        self.outcomes[method_id(test)]='error';self.details(test,err);super().addError(test,err)
    def addFailure(self,test,err):
        self.outcomes[method_id(test)]='failed';self.details(test,err);super().addFailure(test,err)
    def addSkip(self,test,reason):self.outcomes[method_id(test)]='skipped';super().addSkip(test,reason)
    def addSubTest(self,test,subtest,err):
        if err is not None:self.outcomes[method_id(test)]='failed_subtest';self.details(test,err)
        super().addSubTest(test,subtest,err)

def timeout(*_):raise KeyboardInterrupt('Isolated day-audit deadline')

def main():
    assert os.name=='posix'and os.getuid()==os.getgid()==65534 and set(os.getgroups())<={65534}
    assert os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE']
    assert os.environ['TMPDIR']==str(RUNTIME/'tmp')
    file_limit=resource.getrlimit(resource.RLIMIT_FSIZE)
    assert file_limit==(65536,65536)
    sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
    signal.signal(signal.SIGALRM,timeout);signal.alarm(175)
    original_connect=socket.socket.connect;original_create=socket.create_connection;original_bind=socket.socket.bind
    original_kill=os.kill;self_sigints=[]
    def local_address(value):
        if not(isinstance(value,tuple)and len(value)==2 and value[0]=='127.0.0.1'and type(value[1])is int and 0<=value[1]<=65535):deny()
    def connect(sock,address):local_address(address);return original_connect(sock,address)
    def create(address,*args,**kwargs):local_address(address);return original_create(address,*args,**kwargs)
    def bind(sock,address):local_address(address);return original_bind(sock,address)
    def own_sigint(pid,number):
        if pid!=os.getpid()or number!=signal.SIGINT:deny()
        self_sigints.append(number);return original_kill(pid,number)
    socket.socket.connect=connect;socket.create_connection=create;socket.socket.bind=bind
    subprocess.Popen=deny;os.system=deny;os.kill=own_sigint;os.killpg=deny
    import keeper.monitor
    keeper.monitor.Keeper.__init__=deny
    cases=[]
    for index,row in enumerate(SELECTION):
        spec=importlib.util.spec_from_file_location('c817_new_'+str(index),ROOT/row['file'])
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cls=getattr(module,row['class'])
        cases.extend(cls(name)for name in row['methods'])
    assert [method_id(case)for case in cases]==list(SELECTED)
    stream=BoundedStream();started=time.monotonic()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=TrackedResult).run(unittest.TestSuite(cases))
    failures={case.id():hashlib.sha256(detail.encode()).hexdigest()for case,detail in result.errors+result.failures}
    success=(result.wasSuccessful()and result.testsRun==len(SELECTED)and not result.skipped
        and result.started==list(SELECTED)and result.finished==list(SELECTED)
        and all(result.outcomes.get(n)=='passed'for n in SELECTED))
    value={'schema':1,'success':success,'selection':list(SELECTION),'selected_methods':list(SELECTED),
        'tests_run':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped),
        'method_outcomes':{n:result.outcomes.get(n,'not_run')for n in SELECTED},
        'diagnostic_sha256':hashlib.sha256(''.join(stream.parts).encode()).hexdigest(),'diagnostic_bytes':stream.size,
        'error_digests_only':failures,'error_locations':result.error_locations,'elapsed_seconds':time.monotonic()-started,
        'uid':os.getuid(),'gid':os.getgid(),'supplementary_groups':os.getgroups(),'network_namespace_is_private':True,
        'RLIMIT_FSIZE_soft_hard_bytes':list(file_limit),
        'loopback_only_guards':True,'Popen_and_Keeper_construction_denied':True,
        'only_self_SIGINT_permitted':True,'actual_self_SIGINT_count':len(self_sigints),
        'old_test_bodies_run':0,'previously_green_methods_run':0,'affected_method_rerun':True,'signing_attempts':0,
        'public_network_used':False,'production_approved':False}
    publish('RESULT.json',value);signal.alarm(0)
    print(json.dumps({'affected_day_audit_methods':len(SELECTED),'success':success,'errors_or_failures':len(failures)}))
    return 0 if success else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Exception,KeyboardInterrupt)as exc:
        print(json.dumps({'new_day_audit_selection_refused':True,'error_type':type(exc).__name__}),file=sys.stderr)
        raise SystemExit(1)from None
