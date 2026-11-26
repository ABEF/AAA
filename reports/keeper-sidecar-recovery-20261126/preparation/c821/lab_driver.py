"""Fixed root coordinator; only new c821 services, private runtime and network."""
from pathlib import Path
import base64,gzip,json,os,signal,stat,sys,threading,time,traceback
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import TCPServer
from lab_common import LAB,SOURCE,RUNTIME,PREFIX,JOBS,UNITS,sha,enc,need,publish,packed,read_json,file_pin,run

ANCHOR=UNITS[0]
END=time.monotonic()+165
STARTED=[];PASSED=[];DETAILS={};COMMANDS=[];PROPERTIES={};RECEIVED=[]
FIELDS=('Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,'
 'ExecStart,Type,User,Group,PrivateNetwork,JoinsNamespaceOf,Restart,KillMode,TimeoutStartUSec,TimeoutStopUSec,'
 'RuntimeMaxUSec,RemainAfterExit,MemoryMax,MemorySwapMax,TasksMax,ProtectSystem,ReadWritePaths,FragmentPath,'
 'BindPaths,BindReadOnlyPaths,CapabilityBoundingSet,PropagatesStopTo,StartLimitIntervalUSec,StartLimitBurst,'
 'ExecMainStartTimestampMonotonic,InvocationID')

def command(argv,timeout=15):
    need(time.monotonic()<END,'driver_deadline')
    code,out,err=run(argv,timeout=min(timeout,max(1,END-time.monotonic())),manager=True)
    COMMANDS.append({'program':Path(argv[0]).name,'argv_sha256':sha(enc(argv)),
        'code':code,'stdout_sha256':sha(out),'stderr_sha256':sha(err),
        'owned_units':[x for x in argv if x in UNITS]})
    need(len(COMMANDS)<=150,'manager_count')
    return code,out,err

def props(unit):
    need(unit in UNITS)
    code,out,_=command(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+FIELDS])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found','manager_show')
    record=PROPERTIES.setdefault(unit,{})
    if value.get('LoadState')=='loaded'and'first_existing'not in record:record['first_existing']=value
    record['last']=value
    return value

def empty(p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group in('/system.slice/'+u for u in UNITS),'foreign_group')
    path=Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs'
    try:raw=path.read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096,'group_bound');return not raw.strip()

def wait_for(predicate,seconds=30,label='wait_expired'):
    end=min(END,time.monotonic()+seconds)
    while time.monotonic()<end:
        value=predicate()
        if value:return value
        time.sleep(.1)
    raise ValueError(label)

def completed(job):
    p=props(PREFIX+'-'+job+'.service')
    stamp=p.get('ExecMainStartTimestampMonotonic','0')
    return p if stamp.isdigit()and int(stamp)>0 and p.get('ExecMainCode','0')!='0'and empty(p)and p.get('SubState')in('dead','failed','exited')else None

def manager(verb,unit):
    need(verb=='stop'and unit in UNITS)
    return command(['/usr/bin/systemctl',verb,unit])[0]

def start_job(job):
    need(job in JOBS)
    unit=PREFIX+'-'+job+'.service';before=props(unit)
    need(before.get('LoadState')in('not-found','error')and not before.get('FragmentPath'),'existing_unit')
    policy={'Type':'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes',
     'JoinsNamespaceOf':ANCHOR,'After':ANCHOR,'PrivateTmp':'yes','PrivateDevices':'yes',
     'ProtectSystem':'strict','ProtectHome':'yes','NoNewPrivileges':'yes','ProtectKernelTunables':'yes',
     'ProtectKernelModules':'yes','ProtectControlGroups':'yes','RestrictSUIDSGID':'yes',
     'LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
     'RestrictAddressFamilies':'AF_UNIX AF_INET','ReadWritePaths':str(RUNTIME),'UMask':'0077',
     'Restart':'no','RemainAfterExit':'yes','TimeoutStartSec':'180','TimeoutStopSec':'2',
     'KillMode':'control-group','SendSIGKILL':'yes','FinalKillSignal':'SIGKILL',
     'MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32','LimitCORE':'0','LimitFSIZE':'65536',
     'StartLimitIntervalSec':'0','WorkingDirectory':str(SOURCE),
     'BindReadOnlyPaths':str(LAB/'masks/key.empty')+':'+str(RUNTIME/'working/keystore.secret')+' '+
        str(LAB/'masks/password.empty')+':'+str(RUNTIME/'working/password.secret'),
     'StandardOutput':'append:'+str(RUNTIME/(job+'.stdout')),
     'StandardError':'append:'+str(RUNTIME/(job+'.stderr'))}
    if job=='target':
        policy['BindPaths']=' '.join(str(RUNTIME/'restored'/source)+':'+str(RUNTIME/destination)
            for source,destination in(('scheduler','schedule'),('alerts','alerts'),('backups','backups')))
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit]
    argv+=['--property='+k+'='+v for k,v in policy.items()]
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1',
        'PYTHONNOUSERSITE':'1','PYTHONUNBUFFERED':'1','TMPDIR':str(RUNTIME/'tmp'),'HOME':str(RUNTIME/'home')}
    argv+=['--setenv='+k+'='+v for k,v in env.items()]
    actual=['/usr/bin/python3','-B',str(SOURCE/('run_focused.py'if job=='checks'else'run_flow.py'))]
    if job!='checks':actual.append(job)
    code,_,_=command([*argv,'--',*actual]);need(code==0,'native_start')
    p=props(unit)
    need(p.get('Type')=='oneshot'and p.get('TimeoutStartUSec')=='3min'and p.get('TimeoutStopUSec')=='2s'
        and p.get('User')=='nobody'and p.get('Group')=='nogroup'and p.get('PrivateNetwork')=='yes'
        and p.get('JoinsNamespaceOf')==ANCHOR and p.get('KillMode')=='control-group'
        and p.get('Restart')=='no'and p.get('CapabilityBoundingSet')==''and p.get('StartLimitIntervalUSec')=='0',
        'effective_unit_policy')
    finished=wait_for(lambda:completed(job),seconds=60,label='actual_job_completion_missing')
    need(finished['ExecMainStatus']=='0','worker_failed')
    return{'initial':p,'completed':finished}

def progress(name):
    need(name not in STARTED,'scenario_repeated');STARTED.append(name)
    publish('PROGRESS.json',{'schema':1,'started':STARTED,'passed':PASSED,'current':name,'old_test_bodies_run':0})

def passed(name,value):
    need(name==STARTED[-1]and name not in PASSED);PASSED.append(name);DETAILS[name]=value
    publish('PROGRESS.json',{'schema':1,'started':STARTED,'passed':PASSED,'current':None,'old_test_bodies_run':0})

class Receiver(HTTPServer):
    allow_reuse_address=True
    def server_bind(self):TCPServer.server_bind(self);self.server_name,self.server_port='127.0.0.1',self.server_address[1]

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(2)
    def log_message(self,*_):pass
    def do_POST(self):
        need(self.path=='/alerts','receiver_path');size=int(self.headers['Content-Length']);need(0<size<=2048)
        value=json.loads(self.rfile.read(size));need(value['unsigned']is True and value['readiness_approved']is False)
        RECEIVED.append(value);need(len(RECEIVED)<=32,'receiver_bound')
        raw=enc({'event_id':value['event_id'],'accepted':True})
        self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

def close_receiver(server,thread):
    if server is not None:server.shutdown();server.server_close();thread.join(timeout=2);need(not thread.is_alive())

def main():
    import socket
    need(os.getuid()==0 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'root_private_namespace')
    need(not(RUNTIME/'RESULT.json').exists(),'no_replay')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
    from fixture import fixture
    began=time.monotonic();server=thread=None;cleanup=False
    result={'schema':1,'success':False,'old_test_bodies_run':0,'public_transactions':0,
        'signer_contents_read':False,'production_approved':False}
    try:
        # Reserve a port number without running a receiver during source capture.
        with socket.socket()as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        fixture('http://127.0.0.1:'+str(port)+'/alerts')
        original_journal=file_pin(RUNTIME/'working/runtime/journal.json')
        progress('new_focused_recovery_methods');properties=start_job('checks')
        checked=read_json(RUNTIME/'FOCUSED_RESULT.json')
        need(checked['success']is True and checked['old_test_bodies_run']==0,'focused_methods_failed')
        passed('new_focused_recovery_methods',{'properties':properties,'selected_methods':checked['selected_methods'],
            'methods_passed':checked['tests_run']})
        progress('actual_unsigned_capture_verify_restore');properties=start_job('source')
        source=read_json(RUNTIME/'SOURCE_RESULT.json');need(source['success']is True,'source_flow_failed')
        source_before={name:file_pin(RUNTIME/relative)for name,relative in{
            'selection':'schedule/selected.json','alerts':'alerts/state.json','policy':'policy.json',
            'config':'keeper-config.json','journal':'working/runtime/journal.json'}.items()}
        need(empty(props(PREFIX+'-source.service')),'source_not_fenced')
        passed('actual_unsigned_capture_verify_restore',{'properties':properties,'bundle_manifest_pin':source['bundle_manifest_pin'],
            'source_files':source['source_files'],'restored_files':source['restored_files'],
            'source_state_unchanged':source['source_state_unchanged'],'source_locks':source['source_locks'],
            'fresh_restore_locks':source['fresh_restore_locks'],'source_job_empty_before_target':True})
        progress('mapped_target_resumes_same_outbox_and_pending_clock')
        server=Receiver(('127.0.0.1',port),Handler)
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.02},daemon=True);thread.start()
        properties=start_job('target');target=read_json(RUNTIME/'TARGET_RESULT.json')
        need(target['success']is True,'target_flow_failed')
        ids=[e['event_id']for e in source['observer_before']['outbox']]
        need(ids==target['same_queued_ids']and set(ids)<={e['event_id']for e in RECEIVED},'receiver_ids_changed')
        need(source['observer_before']['pending']==target['observer_after']['pending'],'target_pending_changed')
        source_after={name:file_pin(RUNTIME/relative)for name,relative in{
            'selection':'schedule/selected.json','alerts':'alerts/state.json','policy':'policy.json',
            'config':'keeper-config.json','journal':'working/runtime/journal.json'}.items()}
        need(source_before==source_after,'original_source_mutated_by_target')
        need(read_json(RUNTIME/'restored/alerts/state.json')==target['observer_after'],'target_mapping_missing')
        passed('mapped_target_resumes_same_outbox_and_pending_clock',{'properties':properties,'queued_ids':ids,
            'source_before':source_before,'source_after':source_after,
            'actual_received_ids':[e['event_id']for e in RECEIVED],
            'preserved_first_seen':target['pending_first_seen_preserved'],'original_policy_unchanged':True})
        progress('final_fenced_preservation')
        for unit in UNITS[1:]:need(manager('stop',unit)==0,'job_stop')
        need(all(empty(props(unit))for unit in UNITS[1:]),'worker_group_survived')
        need(file_pin(RUNTIME/'working/runtime/journal.json')==original_journal,'source_journal_changed')
        passed('final_fenced_preservation',{'worker_groups_empty':3,'original_journal':original_journal,
            'original_source_state_preserved':True,'target_only_new_namespace_mapping':True})
        result['success']=True
    except BaseException as exc:
        result['error_type']=type(exc).__name__;text=str(exc)
        result['error_code']=text if isinstance(exc,ValueError)and text.replace('_','').isalnum()else'scoped_failure'
        result['frames']=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}
            for f in traceback.extract_tb(exc.__traceback__)[-8:]]
    finally:
        try:
            for unit in UNITS[1:]:
                if props(unit).get('LoadState')!='not-found':manager('stop',unit)
            cleanup=all(empty(props(unit))for unit in UNITS[1:])
        except BaseException as exc:result['cleanup_error_type']=type(exc).__name__
        close_receiver(server,thread)
        result.update(elapsed_seconds=time.monotonic()-began,cleanup=cleanup,
            started_scenarios=STARTED,passed_scenarios=PASSED,scenario_details=DETAILS,
            receiver_events=packed(RECEIVED),fixture_seam='public synthetic vectors, current source hashes and wallclock; no chain')
        publish('NATIVE_PROPERTIES.json',{'schema':1,'units':packed(PROPERTIES)})
        publish('MANAGER_TRACE.json',{'schema':1,'commands':packed(COMMANDS),'count':len(COMMANDS)})
        logs={}
        for job in JOBS:
            for channel in('stdout','stderr'):
                path=RUNTIME/(job+'.'+channel)
                if path.exists():
                    raw=path.read_bytes();need(len(raw)<=65536,'log_bound')
                    logs[path.name]={'bytes':len(raw),'sha256':sha(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')}
        publish('WORKER_LOGS.json',{'schema':1,'logs':logs,'only_disposable_lab_metadata':True})
        publish('RESULT.json',result)
    print(json.dumps({'success':result['success'],'passed_stages':len(PASSED),'cleanup':cleanup}))
    return 0 if result['success']and cleanup else 1

if __name__=='__main__':raise SystemExit(main())
