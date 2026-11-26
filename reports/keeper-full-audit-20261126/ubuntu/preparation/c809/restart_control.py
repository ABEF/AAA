"""PREPARATION ONLY. Closed c809 root controller; import performs no host action.

The parent must authenticate this module AND the byte-identical c804 native_base
before calls. No remote transport or arbitrary unit, path, command or config.
"""
from pathlib import Path
import copy
import json
import os
import re
import stat
import time
import native_base as N

LAB=Path('/opt/popl-keeper-full-audit-20261126-c809')
MODEL_UNIT='popl-keeper-full-audit-20261126-c809-model.service'
KEEPER_UNIT='popl-keeper-full-audit-20261126-c809-keeper.service'
for key,value in {'LAB':LAB,'MODEL_UNIT':MODEL_UNIT,'KEEPER_UNIT':KEEPER_UNIT,
    'UNITS':(MODEL_UNIT,KEEPER_UNIT),'SOURCE':LAB/'source/contracts','HELPERS':LAB/'source/helpers',
    'RUN':LAB/'runtime/run-001','MODEL':LAB/'runtime/run-001/model',
    'LIVE':LAB/'runtime/run-001/model/supervisor/actor',
    'CONFIG':LAB/'runtime/run-001/model/supervisor/actor/config.json',
    'READY':LAB/'runtime/run-001/model/READY.json'}.items():setattr(N,key,value)
need=N.need

def ready():
    N._ownership()
    value=json.loads(N._read(N.READY,65536,owners=(0,N.UID)))
    need(value.get('configuration_path')==str(N.CONFIG)and
        value.get('good_configuration_path')==str(N.MODEL/'supervisor/GOOD_CONFIG.json')and
        value.get('state_path')==str(N.LIVE/'state.json')and
        value.get('monitor_argv')==['/usr/bin/python3','-m','keeper.monitor','--config',str(N.CONFIG),'--live']and
        value.get('monitor_working_directory')==str(N.SOURCE),'Fixed restart ready paths differ')
    for field in ('bad_configuration_sha256','good_configuration_sha256','original_journal_sha256'):
        need(type(value.get(field))is str and re.fullmatch('[0-9a-f]{64}',value[field]),'Restart ready pin differs')
    return value

def _config_checks(config,interval):
    exact={'chain_id':4663,'rpc_urls':['http://127.0.0.1:19592'],
        'cast_binary':str(LAB/'tools/cast'),'keystore':str(N.LIVE/'secrets/keeper'),
        'password_file':str(N.LIVE/'secrets/password'),'state_path':str(N.LIVE/'state.json'),
        'health_path':str(N.LIVE/'health.json'),'lock_path':str(N.LIVE/'keeper.lock'),
        'interval_seconds':interval,'confirmations':12,'max_gas_limit':24000000,
        'max_gas_price_wei':'5000000000','max_transaction_cost_wei':'10000000000000000',
        'max_daily_cost_wei':'50000000000000000','l1_fee_allowance_wei':'0','receipt_fee_policy':'included',
        'maintenance':{'compound':False,'compound_idle':False,'harvest':False,'minimum_liquidity':1,'harvest_interval_seconds':3600},
        'bucket_overrides':{},'adaptive_range':{'enabled':False},'royalty_conversion':{'enabled':False},
        'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},
        'principal_distribution':{'enabled':False},'buybacks':[]}
    need(all(config.get(key)==value for key,value in exact.items()),'Fixed restart guard/job configuration differs')

def start_model(pins):return N.native_start_model(pins)

def _keeper_start_spec(*,reuse_logs=False):
    previous=N._logs
    if reuse_logs:
        def logs(kind):
            need(kind=='keeper','Only keeper logs may be retained for restart')
            result=[]
            for stream in ('stdout','stderr'):
                path=N.RUN/('native-keeper.'+stream+'.log')
                N._read(path,N.MAX_OUTPUT,owners=(0,N.UID))
                result.append('append:'+str(path))
            return result
        N._logs=logs
    try:policy=N._common_policy('keeper')
    finally:N._logs=previous
    policy.update(WatchdogSec='120s',TimeoutStopSec='120s',Restart='on-failure',RestartSec='30s',
        NotifyAccess='main',WatchdogSignal='SIGKILL',StartLimitIntervalSec='600s',StartLimitBurst='5',
        JoinsNamespaceOf=MODEL_UNIT,Requires=MODEL_UNIT,After=MODEL_UNIT)
    env={'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(N.SOURCE),
        'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1',
        'TMPDIR':str(N.MODEL/'tmp'),'HOME':str(N.LIVE/'secrets')}
    argv=['/usr/bin/python3','-m','keeper.monitor','--config',str(N.CONFIG),'--live']
    return argv,policy,env

def start_invalid_keeper():
    evidence=ready();raw=N._read(N.CONFIG,256*1024,owners=(0,N.UID),expected=evidence['bad_configuration_sha256'])
    config=json.loads(raw);_config_checks(config,0)
    N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID),expected=evidence['original_journal_sha256'])
    model=N._properties(MODEL_UNIT);need(model.get('ActiveState')=='active'and int(model.get('MainPID','0'))>1,'Fresh model is not active')
    proc=N._proc(int(model['MainPID']))
    need(proc is not None and proc['uid']==N.UID and proc['network_namespace']==evidence['namespace']and
        proc['network_namespace']!=os.readlink('/proc/self/ns/net'),'Fresh model private namespace differs')
    argv,policy,env=_keeper_start_spec();result=N._start(KEEPER_UNIT,argv,policy,env)
    N._keeper_policy_checks(result['properties'])
    need(result['properties'].get('StartLimitIntervalUSec')=='10min'and
        result['properties'].get('StartLimitBurst')=='5','Loaded restart bound differs')
    return result

def status():return N.native_status()

def prove_rate_limit():
    evidence=ready();snapshot=status();keeper=snapshot['units'][KEEPER_UNIT];p=keeper['properties']
    need(p.get('ActiveState')=='failed'and p.get('Result')=='start-limit-hit'and
        p.get('MainPID')=='0'and not keeper['cgroup']['pids'],'Keeper has not reached an empty native start limit')
    need(int(p.get('NRestarts','-1'))==5,'Native retry counter does not show refused sixth attempt')
    rows=keeper['manager_journal']
    starts=[row for row in rows if row.get('MESSAGE_ID')=='39f53479d3a045ac8e11786248231fbf']
    exits=[row for row in rows if row.get('MESSAGE_ID')=='98e322203f7a4ed290d09fe03c09fe15']
    need(len(starts)==len(exits)==5,'Native journal does not prove exactly five actual starts and main exits')
    starts.sort(key=lambda row:int(row['__MONOTONIC_TIMESTAMP']))
    exits.sort(key=lambda row:int(row['__MONOTONIC_TIMESTAMP']))
    invocations=set()
    for index,(start,exit)in enumerate(zip(starts,exits)):
        invocation=start.get('INVOCATION_ID')
        need(type(invocation)is str and re.fullmatch('[0-9a-f]{32}',invocation)and
            invocation==exit.get('INVOCATION_ID')and invocation not in invocations,
            'Native invocation start/exit identity differs')
        invocations.add(invocation)
        begin,end=int(start['__MONOTONIC_TIMESTAMP']),int(exit['__MONOTONIC_TIMESTAMP'])
        need(begin<=end and exit.get('EXIT_CODE')=='exited'and str(exit.get('EXIT_STATUS'))=='1',
            'Native main exit is not the intended pre-signing failure')
        if index:
            previous=int(exits[index-1]['__MONOTONIC_TIMESTAMP'])
            need(begin>=previous+30_000_000,'Native restart happened before30seconds')
    need(int(exits[-1]['__MONOTONIC_TIMESTAMP'])-int(starts[0]['__MONOTONIC_TIMESTAMP'])<600_000_000,
        'Five failures did not occur within the original600second window')
    N._read(N.CONFIG,256*1024,owners=(0,N.UID),expected=evidence['bad_configuration_sha256'])
    N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID),expected=evidence['original_journal_sha256'])
    raw=N._read(N.RUN/'native-keeper.stdout.log',N.MAX_OUTPUT,owners=(0,N.UID))
    errors=[]
    for line in raw.splitlines():
        row=json.loads(line)
        if row.get('event')=='keeper_halted':
            need(row.get('error_type')=='ValueError'and 'integer' in row.get('error_site',''),'Unexpected halt cause in rate-limit partition')
            errors.append(row)
        else:need(False,'Unexpected stock progress before invalid interval refusal')
    need(len(errors)==5,'Expected exactly five pre-constructor stock failures')
    need(not (N.LIVE/'health.json').exists(),'Invalid startup wrote a runtime health cycle')
    return {'schema':1,'success':True,'systemd_snapshot':snapshot,'exact_stock_halts':errors,
        'native_started_invocations':starts,'native_main_exits':exits,
        'five_started_sixth_refused':True,'invalid_starts_preserved_exact_journal':True,
        'financial_jobs_run':0,'raw_signer_sends':0,'policy':{'starts':5,'window_seconds':600,'restart_seconds':30}}

def restore_good_and_restart(proof):
    """Exact single-field repair only; no journal changes, nonce adoption or resend."""
    need(type(proof)is dict and proof.get('success')is True and proof.get('five_started_sixth_refused')is True,'Reviewed captured start-limit proof required')
    # Re-prove current fixed native state immediately before the only repair.
    prove_rate_limit();evidence=ready()
    bad=N._read(N.CONFIG,256*1024,owners=(0,N.UID),expected=evidence['bad_configuration_sha256'])
    good=N._read(N.MODEL/'supervisor/GOOD_CONFIG.json',256*1024,owners=(0,N.UID),expected=evidence['good_configuration_sha256'])
    a,b=json.loads(bad),json.loads(good);_config_checks(a,0);_config_checks(b,240)
    expected=copy.deepcopy(a);expected['interval_seconds']=240;need(expected==b,'Repair changes more than polling interval')
    temporary=N.LIVE/'config.restart-repair.tmp'
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        os.fchown(fd,N.UID,N.GID);position=0
        while position<len(good):
            written=os.write(fd,good[position:]);need(written>0,'Owned configuration write made no progress');position+=written
        os.fsync(fd)
    finally:os.close(fd)
    # Destination exact bytes/identity were validated above and only this root
    # controller can edit the owned lab while stock unit is fully stopped.
    os.replace(temporary,N.CONFIG)
    parent=os.open(N.LIVE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(parent)
    finally:os.close(parent)
    N._read(N.CONFIG,256*1024,owners=(0,N.UID),expected=evidence['good_configuration_sha256'])
    N._read(N.LIVE/'state.json',2*1024*1024,owners=(0,N.UID),expected=evidence['original_journal_sha256'])
    reset=N._run(['/usr/bin/systemctl','reset-failed',KEEPER_UNIT]);need(reset['returncode']==0,'Owned reset-failed refused')
    # Transient failed units may be unloaded after reset-failed. Recreate only
    # the SAME exact owned unit/spec/logs if unloaded; otherwise start it.
    if N._properties(KEEPER_UNIT).get('LoadState')=='not-found':
        argv,policy,env=_keeper_start_spec(reuse_logs=True);started=N._start(KEEPER_UNIT,argv,policy,env)
    else:
        response=N._run(['/usr/bin/systemctl','start',KEEPER_UNIT],timeout=20)
        need(response['returncode']==0,'Owned repaired keeper start refused')
        started={'unit':KEEPER_UNIT,'properties':N._properties(KEEPER_UNIT),'same_loaded_unit':True}
    N._keeper_policy_checks(started['properties'])
    return {'phase':'good240_restarted','good_configuration_sha256':evidence['good_configuration_sha256'],
        'journal_unchanged_before_recovery':True,'result':started}

def stop_owned():return N.native_stop_owned()
