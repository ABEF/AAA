"""NEW finite composition coordinator; fixed private units, no old test bodies."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import TCPServer
import base64,gzip,json,os,socket,stat,sys,threading,time,traceback
from lab_common import LAB,SOURCE,HELPERS,RUNTIME,PREFIX,JOBS,UNITS,TIMERS,sha,enc,need,publish,packed,read_json,file_pin,run

ANCHOR=UNITS[0];BEGAN=time.monotonic();END=BEGAN+760;CLEANING=False
MODEL_ARGS=__MODEL_ARGS__
STARTED=[];PASSED=[];DETAILS={};COMMANDS=[];PROPERTIES={};RECEIVED=[]
FIELDS=('Id,LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainCode,ExecMainStatus,'
 'ExecStart,Type,User,Group,PrivateNetwork,JoinsNamespaceOf,Restart,KillMode,TimeoutStartUSec,TimeoutStopUSec,'
 'RuntimeMaxUSec,RemainAfterExit,MemoryMax,MemorySwapMax,TasksMax,ProtectSystem,ReadWritePaths,FragmentPath,'
 'BindPaths,BindReadOnlyPaths,CapabilityBoundingSet,PropagatesStopTo,StartLimitIntervalUSec,'
 'ExecMainStartTimestampMonotonic,InvocationID,NextElapseUSecMonotonic,LastTriggerUSecMonotonic,TimersMonotonic')


def command(argv,timeout=15):
    deadline=BEGAN+895 if CLEANING else END
    need(time.monotonic()<deadline,'driver_deadline')
    code,out,err=run(argv,timeout=min(timeout,max(1,deadline-time.monotonic())),manager=True)
    COMMANDS.append({'program':Path(argv[0]).name,'argv_sha256':sha(enc(argv)),'code':code,
        'stdout_sha256':sha(out),'stderr_sha256':sha(err),'owned_units':[x for x in argv if x in (*UNITS,*TIMERS)]})
    need(len(COMMANDS)<=300,'manager_count');return code,out,err


def props(unit):
    need(unit in (*UNITS,*TIMERS),'foreign_unit')
    code,out,_=command(['/usr/bin/systemctl','show',unit,'--no-pager','--property='+FIELDS])
    value=dict(line.split('=',1)for line in out.decode('utf8','strict').splitlines()if'='in line)
    need(code==0 or code==1 and value.get('LoadState')=='not-found','manager_show')
    record=PROPERTIES.setdefault(unit,{})
    if value.get('LoadState')=='loaded'and'first_existing'not in record:record['first_existing']=value
    record['last']=value;return value


def empty(p):
    if p.get('MainPID','0')!='0':return False
    group=p.get('ControlGroup','')
    if not group:return True
    need(group in('/system.slice/'+u for u in UNITS),'foreign_group')
    try:raw=(Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_bytes()
    except FileNotFoundError:return True
    need(len(raw)<=4096,'group_bound');return not raw.strip()


def wait_for(predicate,seconds,label):
    until=min(END,time.monotonic()+seconds)
    while time.monotonic()<until:
        value=predicate()
        if value:return value
        time.sleep(.2)
    raise ValueError(label)


def marker(name,model=False):
    need(name in ('READY','PENDING','INCLUDED','SETTLED','HEALTHY','COMPLETE','MODEL_RESULT','MODEL_STOP',
        'MODEL_EVIDENCE','RACE_READY','RACE_RESULT','HOLD_READY','HOLD_RESULT'))
    path=(RUNTIME/'model'if model else RUNTIME)/(name+'.json')
    return read_json(path)if path.exists()else None


def control(name):
    need(name in ('RELEASE_RACE','HOLD','RELEASE_HOLD','INCLUDE','CAPTURE_FINAL'))
    path=RUNTIME/'control'/(name+'.json');raw=enc({'schema':1,'name':name});need(not path.exists(),'control_exists')
    temporary=path.with_suffix('.partial')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444)
    os.rename(temporary,path)


def records(action=None):
    paths=sorted((RUNTIME/'records').glob('*.json'));need(len(paths)<=128,'record_count')
    rows=[read_json(path)for path in paths]
    return[row for row in rows if action is None or row['action']==action]


def progress(name):
    need(name not in STARTED,'scenario_repeated');STARTED.append(name)
    publish('PROGRESS.json',{'schema':1,'started':STARTED,'passed':PASSED,'current':name,'old_test_bodies_run':0})


def passed(name,value):
    need(name==STARTED[-1]and name not in PASSED);PASSED.append(name);DETAILS[name]=value
    publish('PROGRESS.json',{'schema':1,'started':STARTED,'passed':PASSED,'current':None,'old_test_bodies_run':0})


def launch(job,ready=None,timer=None):
    need(job in JOBS,'unknown_job');unit=PREFIX+'-'+job+'.service'
    need(props(unit).get('LoadState')=='not-found','existing_unit')
    long=job in ('model','keeper')
    policy={'Type':'exec'if long else'oneshot','User':'nobody','Group':'nogroup','PrivateNetwork':'yes',
        'JoinsNamespaceOf':ANCHOR,'After':ANCHOR,'PrivateTmp':'yes','PrivateDevices':'yes','ProtectSystem':'strict',
        'ProtectHome':'yes','NoNewPrivileges':'yes','ProtectKernelTunables':'yes','ProtectKernelModules':'yes',
        'ProtectControlGroups':'yes','RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'',
        'AmbientCapabilities':'','RestrictAddressFamilies':'AF_UNIX AF_INET','ReadWritePaths':str(RUNTIME),
        'UMask':'0077','Restart':'no','RemainAfterExit':'yes'if job in('init','barrier')else'no',
        'TimeoutStartSec':'180','TimeoutStopSec':'120'if long else'2','KillMode':'control-group',
        'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','MemoryMax':'512M'if job=='model'else'256M',
        'MemorySwapMax':'0','TasksMax':'64'if job=='model'else'32','LimitCORE':'0','LimitFSIZE':'65536',
        'StartLimitIntervalSec':'0','WorkingDirectory':str(SOURCE),
        'StandardOutput':'append:'+str(RUNTIME/(job+'.stdout')),'StandardError':'append:'+str(RUNTIME/(job+'.stderr'))}
    if long:policy['RuntimeMaxSec']='860'
    if not long:
        cfg=read_json(Path(ready['configuration_path']))
        policy['BindReadOnlyPaths']=str(LAB/'masks/key.empty')+':'+cfg['keystore']+' '+str(LAB/'masks/password.empty')+':'+cfg['password_file']
    if job=='observe':policy.update(IPAddressDeny='any',IPAddressAllow='127.0.0.1/32')
    env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8',
        'PYTHONPATH':str(HELPERS)+':'+str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1',
        'PYTHONUNBUFFERED':'1','TMPDIR':str(RUNTIME/'tmp'),'HOME':str(RUNTIME/'home'),
        'POPL_LAB_HOST_NETWORK_NAMESPACE':os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE']}
    argv=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit]
    if timer is not None:
        need(job in('backup','observe')and timer==(45 if job=='backup'else 10),'timer_policy')
        argv+=['--on-active=1s','--on-unit-inactive='+str(timer)+'s',
            '--timer-property=AccuracySec=100ms','--timer-property=RandomizedDelaySec=0']
    argv+=['--property='+k+'='+v for k,v in policy.items()]+['--setenv='+k+'='+v for k,v in env.items()]
    if job=='model':body=['/usr/bin/python3','-B',str(HELPERS/'model_service.py'),*MODEL_ARGS]
    elif job=='keeper':
        body=['/usr/bin/python3','-B','-m','keeper.monitor','--config',ready['configuration_path'],'--live']
        need(body==ready['monitor_argv'],'monitor_argv')
    else:body=['/usr/bin/python3','-B',str(HELPERS/'schedule_worker.py'),job]
    code,_,_=command([*argv,'--',*body]);need(code==0,'native_start')
    p=props(unit)
    need(p.get('Type')==policy['Type']and p.get('User')=='nobody'and p.get('Group')=='nogroup'
        and p.get('PrivateNetwork')=='yes'and p.get('JoinsNamespaceOf')==ANCHOR
        and p.get('KillMode')=='control-group'and p.get('Restart')=='no'
        and p.get('CapabilityBoundingSet')==''and p.get('StartLimitIntervalUSec')in('0','0s'),'effective_unit_policy')
    return p


def stop(unit):
    need(unit in (*UNITS[1:],*TIMERS),'stop_scope')
    p=props(unit)
    if p.get('LoadState')=='not-found':return p
    code,_,_=command(['/usr/bin/systemctl','stop',unit],timeout=20);need(code==0,'unit_stop')
    return props(unit)


class Receiver(HTTPServer):
    def server_bind(self):TCPServer.server_bind(self);self.server_name,self.server_port='127.0.0.1',self.server_address[1]


class Handler(BaseHTTPRequestHandler):
    def setup(self):super().setup();self.connection.settimeout(2)
    def log_message(self,*_):pass
    def do_POST(self):
        need(self.path=='/alerts','receiver_path');size=int(self.headers['Content-Length']);need(0<size<=2048)
        value=json.loads(self.rfile.read(size));need(value['unsigned']is True and value['readiness_approved']is False)
        RECEIVED.append(value);need(len(RECEIVED)<=64,'receiver_bound')
        raw=enc({'event_id':value['event_id'],'accepted':True})
        self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)


def prepare_policy(ready,port):
    from keeper import scheduling
    cfgpath=Path(ready['configuration_path']);cfg=read_json(cfgpath)
    need(sha(cfgpath.read_bytes())==ready['configuration_sha256'],'configuration_pin')
    expected=RUNTIME/'model/composition/actor'
    need(cfgpath==expected/'config.json'and cfg['state_path']==str(expected/'state.json')
        and cfg['health_path']==str(expected/'health.json')and cfg['lock_path']==str(expected/'keeper.lock')
        and cfg['keystore']==str(expected/'secrets/keeper')and cfg['password_file']==str(expected/'secrets/password'),'fixed_runtime_paths')
    need(cfg['interval_seconds']==240 and cfg['confirmations']==12 and cfg['max_gas_limit']==24000000
        and cfg['maintenance']['harvest_interval_seconds']==3600,'keeper_limits')
    policy={'schema':1,'kind':'popl-keeper-schedule','configuration':str(cfgpath),
        'configuration_sha256':sha(cfgpath.read_bytes()),'working_directory':str(SOURCE),
        'scheduler_directory':str(RUNTIME/'schedule'),'backup_directory':str(RUNTIME/'backups'),
        'alert_directory':str(RUNTIME/'alerts'),
        'source_files_sha256':{name:sha((SOURCE/name).read_bytes())for name in scheduling.SOURCE_FILES},
        'max_backups':32,'max_health_age_seconds':300,'max_backup_age_seconds':900,
        'pending_max_age_seconds':1,'receiver':'http://127.0.0.1:'+str(port)+'/alerts',
        'allow_dry_run':False,'max_bytes':16777216,'max_seconds':60}
    path=RUNTIME/'policy.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
    with os.fdopen(fd,'wb')as stream:stream.write(enc(policy));stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444)
    return policy


def main():
    global CLEANING
    need(os.getuid()==0 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'root_private_namespace')
    need(not(RUNTIME/'RESULT.json').exists(),'no_replay')
    began=time.monotonic();server=thread=None;ready=None;cleanup=False;policy=None
    result={'schema':1,'success':False,'old_test_bodies_run':0,'public_transactions':0,
        'production_approved':False,'new_seals':0,'scope':'one_missing_keeper_timer_composition'}
    try:
        progress('current_copied_state_and_normal_daemon')
        launch('model');ready=wait_for(lambda:marker('READY',True),90,'model_not_ready')
        with socket.socket()as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        policy=prepare_policy(ready,port);launch('init',ready)
        wait_for(lambda:records('init'),20,'init_missing')
        init=records('init')[0];need(init.get('value',{}).get('scheduler_initialized')is True,'initialization_failed')
        launch('barrier',ready);race_ready=wait_for(lambda:marker('RACE_READY'),20,'race_not_ready')
        launch('backup',ready,timer=45);launch('observe',ready,timer=10);launch('keeper',ready)
        pending=wait_for(lambda:marker('PENDING',True),45,'actual_pending_missing')
        control('RELEASE_RACE');race=wait_for(lambda:marker('RACE_RESULT'),20,'race_result_missing')
        need(race['success']is True and race['selection_before']==race['selection_after_under_lock'],'race_selection_changed')
        passed('current_copied_state_and_normal_daemon',{'READY':ready,'PENDING':pending,'instrumented_race':race,
            'lab_only_policy':policy,'production_cadences_selected':False})
        progress('actual_timer_contention_and_same_pending_history')
        def queued_pending():
            value=read_json(RUNTIME/'alerts/state.json')
            return value if value['pending']is not None and bool(value['outbox'])and any(
                event['reason_code']=='pending_prolonged'for event in value['outbox'])else None
        pending_alert=wait_for(queued_pending,35,'pending_alert_missing')
        # Acquire the explicit test lock only after ordinary jobs have become
        # inactive; otherwise a valid ordinary owner can win the same lock.
        for timer in TIMERS:stop(timer)
        wait_for(lambda:all(empty(props(PREFIX+'-'+job+'.service'))for job in('backup','observe')),15,'sidecars_not_idle')
        control('HOLD');hold=wait_for(lambda:marker('HOLD_READY'),10,'hold_missing')
        for timer in TIMERS:
            code,_,_=command(['/usr/bin/systemctl','start',timer]);need(code==0,'timer_resume')
        def both_contended():
            kinds={row['action']for row in records()if row['action']in('backup','observe')
                and row['started_monotonic']>=hold['monotonic']and row.get('value',{}).get('refusal_code')=='scheduler_lock'}
            return kinds if kinds=={'backup','observe'}else None
        contention=wait_for(both_contended,55,'timer_contention_not_witnessed')
        control('RELEASE_HOLD');held=wait_for(lambda:marker('HOLD_RESULT'),10,'hold_result_missing')
        need(held['success']is True,'held_state_mutation')
        server=Receiver(('127.0.0.1',port),Handler)
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.02},daemon=True);thread.start()
        def acknowledged():
            value=read_json(RUNTIME/'alerts/state.json')
            return value if value['pending']==hold['pending']and not value['outbox']and set(hold['queued_ids'])<={e['event_id']for e in RECEIVED}else None
        ack=wait_for(acknowledged,25,'same_outbox_not_acknowledged')
        need(ack['sequence']==hold['sequence'],'pre_inclusion_sequence_changed')
        passed('actual_timer_contention_and_same_pending_history',{'hold':hold,'result':held,
            'queued_before_hold':pending_alert,'after_ack':ack,'same_ids_received':hold['queued_ids'],
            'actual_contended_jobs':sorted(contention)})
        progress('ordinary_pending_recovery_and_required_fresh_observations')
        control('INCLUDE');included=wait_for(lambda:marker('INCLUDED',True),30,'inclusion_missing')
        settled=wait_for(lambda:marker('SETTLED',True),300,'normal_receipt_recovery_missing')
        healthy=wait_for(lambda:marker('HEALTHY',True),300,'normal_fresh_healthy_cycle_missing')
        need(healthy.get('acceptance',{}).get('checker',{}).get('ok')is True,'healthy_semantics_not_proved')
        def final_observed():
            rows=records('observe');good=[row for row in rows if row['started_monotonic']>=healthy['monotonic']
                and row.get('returncode')==0 and row.get('value',{}).get('ok')is True]
            backups=[row for row in records('backup')if row['started_monotonic']>=settled['monotonic']
                and row.get('returncode')==0 and row.get('value',{}).get('ok')is True]
            return{'observer':good[-1],'backup':backups[-1]}if good and backups else None
        final_jobs=wait_for(final_observed,65,'eventual_timer_progress_missing')
        passed('ordinary_pending_recovery_and_required_fresh_observations',{'INCLUDED':included,
            'SETTLED':settled,'HEALTHY':healthy,'final_timer_jobs':final_jobs,
            'actual_unchanged_keeper_poll_seconds':240,'directed_chain_mining_is_not_wallclock_proof':True})
        progress('fenced_final_physical_capture')
        for unit in (*TIMERS,PREFIX+'-backup.service',PREFIX+'-observe.service',PREFIX+'-barrier.service',PREFIX+'-keeper.service'):stop(unit)
        need(all(empty(props(PREFIX+'-'+job+'.service'))for job in('keeper','backup','observe','barrier')),'work_not_fenced')
        control('CAPTURE_FINAL');complete=wait_for(lambda:marker('COMPLETE',True),30,'physical_capture_incomplete')
        model=wait_for(lambda:marker('MODEL_RESULT',True),10,'model_result_missing')
        need(marker('MODEL_EVIDENCE',True)is not None,'actual_model_vectors_missing')
        need(complete.get('success')is True and model.get('success')is True,'model_not_complete')
        passed('fenced_final_physical_capture',{'COMPLETE':complete,'MODEL_RESULT':model,'captured_before_model_teardown':True})
        result['success']=True
    except BaseException as exc:
        result['error_type']=type(exc).__name__;text=str(exc)
        result['error_code']=text if isinstance(exc,ValueError)and text.replace('_','').isalnum()else'scoped_failure'
        result['frames']=[{'file':Path(frame.filename).name,'line':frame.lineno,'function':frame.name}
            for frame in traceback.extract_tb(exc.__traceback__)[-8:]]
    finally:
        CLEANING=True
        # Stop source writers/timers first. The model owns Anvil and captures its
        # final physical vectors before its own stop, even on a failed campaign.
        for unit in (*TIMERS,*(PREFIX+'-'+job+'.service'for job in('backup','observe','init','barrier','keeper'))):
            try:stop(unit)
            except BaseException as exc:result.setdefault('cleanup_errors',[]).append(type(exc).__name__)
        try:stop(PREFIX+'-model.service')
        except BaseException as exc:result.setdefault('cleanup_errors',[]).append(type(exc).__name__)
        stopped=marker('MODEL_STOP',True)
        if not (stopped is not None and stopped.get('success')is True
                and stopped.get('final_source_and_inputs_unchanged')is True
                and stopped.get('cleanup',{}).get('stopped')is True):
            result.update(success=False,model_final_acceptance_failed=True)
        if server is not None:
            server.shutdown();server.server_close();thread.join(2);need(not thread.is_alive(),'receiver_not_stopped')
        try:cleanup=all(empty(props(unit))for unit in UNITS[1:])
        except BaseException:cleanup=False
        all_records=records();publish('SIDECAR_RESULT.json',{'schema':1,'records':packed(all_records),
            'invocations':len(all_records),'receiver_events':packed(RECEIVED),'max_backups':32,
            'lab_backup_seconds':45,'lab_observer_seconds':10,'complete_output_not_truncated':True})
        publish('NATIVE_PROPERTIES.json',{'schema':1,'units':packed(PROPERTIES)})
        publish('MANAGER_TRACE.json',{'schema':1,'commands':packed(COMMANDS),'count':len(COMMANDS)})
        logs={}
        for job in ('driver',*JOBS):
            for channel in('stdout','stderr'):
                path=RUNTIME/(job+'.'+channel)
                if path.exists():
                    raw=path.read_bytes();need(len(raw)<=65536,'log_bound')
                    logs[path.name]={'bytes':len(raw),'sha256':sha(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')}
        publish('WORKER_LOGS.json',{'schema':1,'logs':logs})
        result.update(elapsed_seconds=time.monotonic()-began,cleanup=cleanup,started_scenarios=STARTED,
            passed_scenarios=PASSED,scenario_details=packed(DETAILS),model_stop=stopped,
            receiver_events=packed(RECEIVED),zero_component_test_bodies_run=True)
        publish('RESULT.json',result)
    print(json.dumps({'success':result['success'],'passed_stages':len(PASSED),'cleanup':cleanup}))
    return 0 if result['success']and cleanup else 1


if __name__=='__main__':raise SystemExit(main())
