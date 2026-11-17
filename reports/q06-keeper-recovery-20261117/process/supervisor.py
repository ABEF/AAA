"""Owned transient Linux units only; never controls an installed keeper/site.

Root is transport/setup only. Every rehearsal worker runs as nobody, with
private networking, strict filesystems, no privileges and bounded resources.
No external RPC/key/config, installed journal, reboot or package install.
"""
from pathlib import Path
import hashlib,json,os,pwd,re,signal,subprocess,sys,time
WORKER=Path(__file__).with_name('worker.py');ENTRY=WORKER.with_name('entry.py');FAILOVER=WORKER.with_name('failover.py')
FIELDS=('Id','LoadState','ActiveState','SubState','MainPID','NRestarts','InvocationID','Result',
        'WatchdogUSec','WatchdogSignal','KillMode','SendSIGKILL','FinalKillSignal','NotifyAccess',
        'TimeoutStopUSec','RestartUSec','Restart','User','Group','PrivateNetwork','NoNewPrivileges',
        'ProtectSystem','ProtectHome','LimitCORE','ControlGroup','ExecMainStatus','ExecMainCode')

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
    raw=json.dumps(value,indent=2,sort_keys=True).encode()+b'\n';Path(p).write_bytes(raw)
def command(argv,timeout=15,check=True):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
    if check and p.returncode:raise RuntimeError('Owned command failed: '+argv[0]+': '+p.stderr[-600:])
    return p
def state(unit):
    p=command(['systemctl','show',unit,'--no-pager',*[x for f in FIELDS for x in('-p',f)]],check=False)
    return dict(x.split('=',1) for x in p.stdout.splitlines() if '=' in x)
def proc(pid):
    try:
        text=Path('/proc/'+str(pid)+'/stat').read_text();tail=text[text.rindex(')')+2:].split()
        return {'pid':pid,'state':tail[0],'start_ticks':tail[19],
                'cgroup':Path('/proc/'+str(pid)+'/cgroup').read_text().strip()}
    except (OSError,ValueError):return None
def existing():
    rows=json.loads(command(['systemctl','list-units','--type=service','--all','--output=json','--no-pager']).stdout)
    names=[r['unit'] for r in rows if re.search(r'(?:zzz|popl|nginx|caddy)',r['unit'],re.I)
           and not r['unit'].startswith('popl-q06-20261117-')]
    return {name:{k:v for k,v in state(name).items() if k in('Id','LoadState','ActiveState','SubState','MainPID','InvocationID','NRestarts')}for name in names}

class Lab:
    def __init__(self,base):
        self.base=base.resolve();assert re.fullmatch(r'/(?:run|opt)/popl-q06-20261117-[0-9a-f]{12}',str(self.base))
        assert os.getuid()==0 and self.base.is_dir() and not self.base.is_symlink()
        self.prefix=self.base.name;self.units=[];self.timeline=[];self.results={};self.owner=pwd.getpwnam('nobody')
        self.before=existing();put(self.base/'existing-services-before.json',self.before)
    def event(self,name,**kw):
        row={'name':name,'monotonic':time.monotonic(),'utc':time.time(),**kw};self.timeline.append(row)
        put(self.base/'timeline.json',self.timeline);print(json.dumps(row),flush=True)
    def path(self,name):
        assert re.fullmatch(r'[a-z0-9-]+',name)
        p=self.base/'cases'/name
        if not p.exists():p.mkdir(mode=0o700,parents=True);os.chown(p,self.owner.pw_uid,self.owner.pw_gid)
        assert p.resolve().is_relative_to(self.base) and not p.is_symlink()
        return p
    def start(self,name,argv,root,restart=False):
        unit=self.prefix+'-'+name+'.service';assert unit not in self.units
        assert root.resolve().is_relative_to(self.base/'cases');self.units.append(unit)
        props={'Type':'simple','User':self.owner.pw_name,'Group':'nogroup','WorkingDirectory':str(WORKER.parents[3]),
            'WatchdogSec':'120s','NotifyAccess':'main','WatchdogSignal':'SIGKILL','KillMode':'control-group',
            'SendSIGKILL':'yes','FinalKillSignal':'SIGKILL','LimitCORE':'0','TimeoutStopSec':'120s',
            'Restart':'on-failure'if restart else'no','RestartSec':'30s','StartLimitIntervalSec':'600','StartLimitBurst':'5',
            'NoNewPrivileges':'yes','PrivateNetwork':'yes','PrivateTmp':'yes','ProtectSystem':'strict',
            'ProtectHome':'yes','ProtectControlGroups':'yes','PrivateDevices':'yes','CapabilityBoundingSet':'',
            'RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6','CPUQuota':'20%','MemoryMax':'192M','TasksMax':'24',
            'RuntimeMaxSec':'480s','ReadWritePaths':str(root),'UMask':'0077',
            'StandardOutput':'append:'+str(root/'stdout.log'),'StandardError':'append:'+str(root/'stderr.log')}
        cmd=['systemd-run','--quiet','--unit='+unit]
        for k,v in props.items():cmd+=['--property',k+'='+v]
        # Unit-manager substitution supplies ONLY its watchdog identity. Strip
        # every other inherited variable before Python or an inert signer runs.
        cmd+=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8',
              'PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','PYTHONNOUSERSITE=1',
              'WATCHDOG_USEC=${WATCHDOG_USEC}','WATCHDOG_PID=${WATCHDOG_PID}',
              'NOTIFY_SOCKET=${NOTIFY_SOCKET}',*argv]
        command(cmd);s=state(unit);put(root/(name+'-loaded.json'),s)
        if s.get('LoadState')=='loaded':
            assert s['WatchdogUSec']=='2min' and s['WatchdogSignal']=='9'and s['NotifyAccess']=='main',s
            assert s['KillMode']=='control-group'and s['FinalKillSignal']=='9'and s['User']=='nobody',s
        self.event('started',unit=unit,case=root.name);return unit
    def worker(self,mode,name,root,restart=False):
        return self.start(name,['/usr/bin/python3',str(WORKER),'--root',str(root),'--mode',mode],root,restart)
    def wait(self,test,seconds=180,unit=None):
        until=time.monotonic()+seconds;notice=time.monotonic()+30
        while time.monotonic()<until:
            result=test()
            if result:return result
            if unit:
                s=state(unit)
                if s.get('ActiveState')=='failed':raise AssertionError('Owned unit failed: '+unit+' '+s.get('Result',''))
            if time.monotonic()>=notice:self.event('waiting',unit=unit);notice+=30
            time.sleep(.2)
        raise TimeoutError('Owned scenario deadline')
    def file(self,p,seconds=180,unit=None):return self.wait(lambda:p.exists() and json.loads(p.read_text()),seconds,unit)
    def exited(self,unit,seconds=45):
        return self.wait(lambda:state(unit).get('ActiveState')in('inactive','failed'),seconds)
    def stop(self,unit):
        assert unit in self.units and unit.startswith(self.prefix+'-')
        command(['systemctl','stop','--no-block',unit]);return self.exited(unit,140)
    def prepare(self,name):
        root=self.path(name);u=self.worker('prepare','prep-'+name,root)
        self.file(root/'prepared.json',unit=u);self.exited(u)
        assert state(u).get('Result')in('success',None,'')
        assert (root/'state.json').stat().st_mode&0o777==0o600
        self.event('prepared',case=name);return root
    def cleanup(self):
        for u in self.units:
            assert u.startswith(self.prefix+'-')
            command(['systemctl','kill','--kill-whom=all','--signal=KILL',u],check=False)
            command(['systemctl','stop','--no-block',u],check=False)
        for u in self.units:
            self.exited(u,20);command(['systemctl','reset-failed',u],check=False)
        after=existing();put(self.base/'existing-services-after.json',after)
        changes={name:{'before':row,'after':after.get(name)}for name,row in self.before.items()if after.get(name)!=row}
        put(self.base/'SUMMARY.json',{'results':self.results,'units':self.units,'all_owned_units_stopped':True,
            'existing_service_observed_changes':changes,'existing_service_commands_modified':False,
            'journals_written_only_below':str(self.base/'cases'),'production_approved':False})

def preflight(lab):
    root=lab.prepare('probe');lab.results['prepare']=json.loads((root/'prepared.json').read_text())
    lab.event('preflight_complete')

def campaign(lab):
    # Fast real submission/hash/receipt reconciliation, entirely synthetic wire.
    root=lab.prepare('receipt');u=lab.worker('submit','submit',root)
    lab.file(root/'signer_ready.json',unit=u);(root/'allow_hash.flag').touch()
    lab.file(root/'submitted.json',unit=u);lab.exited(u)
    r=lab.worker('recover','recover',root);rec=lab.file(root/'recovered.json',unit=r);lab.exited(r)
    calls=[json.loads(x)for x in(root/'cast-calls.jsonl').read_text().splitlines()]
    assert sum(x['kind']=='send_inert'for x in calls)==1
    lab.results['exact_receipt_once']=rec;lab.event('receipt_recovered_once')
    # The actual new post-save guard under systemctl's real SIGTERM.
    root=lab.prepare('stop-intent');u=lab.worker('stop-intent','stop-intent',root,True)
    lab.file(root/'intent_saved.json',unit=u);saved=(root/'state.json').read_bytes();lab.stop(u)
    result=lab.file(root/'stop_intent_prevented.json');assert saved==(root/'state.json').read_bytes()
    assert int(state(u).get('NRestarts','0'))==0
    lab.results['stop_during_save']=result;lab.event('intent_stop_prevented_signer')
    # Two real source120s watchdog/group interruption paths run concurrently.
    rpc=lab.prepare('rpc');signer=lab.prepare('signer');fail=lab.path('failover')
    ru=lab.start('rpc',['/usr/bin/python3',str(ENTRY),'rpc',str(rpc)],rpc,True)
    lab.file(rpc/'rpc_stalled.json',unit=ru)
    lock_inode=(rpc/'keeper.lock').stat().st_ino
    contender=lab.worker('lock-contend','contender',rpc);lab.exited(contender)
    assert state(contender).get('Result')!='success'and not(rpc/'lock_acquired.json').exists()
    su=lab.start('signer',['/usr/bin/python3',str(ENTRY),'signer',str(signer)],signer,True)
    ready=lab.file(signer/'signer_descendants.json',unit=su);lab.file(signer/'grandchild_ready.json',unit=su)
    old_main=int(state(su)['MainPID']);children={str(pid):proc(pid)for pid in(old_main,ready['signer'],ready['grandchild'])}
    before_pending=(signer/'state.json').read_bytes();command(['systemctl','kill','--kill-whom=main','--signal=KILL',su])
    fu=lab.start('failover',['/usr/bin/python3',str(FAILOVER),str(fail)],fail)
    old_rpc=int(state(ru)['MainPID']);rpc_generation=proc(old_rpc)
    served_rpc=lab.file(rpc/'serving.json',190,ru)
    assert served_rpc['pid']!=old_rpc and (proc(old_rpc)is None or proc(old_rpc)['state']=='Z')
    assert (rpc/'keeper.lock').stat().st_ino==lock_inode
    assert int(state(ru)['NRestarts'])==1
    lab.results['rpc_watchdog_restart']={'new_pid':served_rpc['pid'],'old_process':rpc_generation,
        'lock_inode_preserved':True,'n_restarts':1};lab.event('rpc_watchdog_restarted')
    served_signer=lab.file(signer/'serving.json',190,su)
    assert (signer/'state.json').read_bytes()==before_pending
    assert all(proc(int(pid))is None or proc(int(pid))['state']=='Z'for pid in children)
    assert int(state(su)['NRestarts'])==1
    calls=[json.loads(x)for x in(signer/'cast-calls.jsonl').read_text().splitlines()]
    assert sum(x['kind']=='send_inert'for x in calls)==1
    lab.results['signer_descendant_restart']={'new_pid':served_signer['pid'],'old_processes':children,
        'same_hashless_journal':True,'send_inert_calls':1,'n_restarts':1};lab.event('signer_group_clean_before_recovery')
    completed=lab.file(fail/'completed.json',190,fu);lab.exited(fu)
    assert int(state(fu).get('NRestarts','0'))==0
    lab.results['bounded_failover_over120s']=completed
    lab.stop(ru);lab.stop(su);lab.event('campaign_complete')

if __name__=='__main__':
    lab=Lab(Path(sys.argv[1]));phase=sys.argv[2]
    try:
        if phase=='preflight':preflight(lab)
        elif phase=='campaign':campaign(lab)
        else:raise ValueError('Unknown owned phase')
    except Exception as exc:
        put(lab.base/'FAILURE.json',{'kind':type(exc).__name__,'message':str(exc),'results':lab.results})
        print(json.dumps({'failure':type(exc).__name__,'message':str(exc)}),flush=True);raise
    finally:lab.cleanup()
