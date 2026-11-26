"""Unsigned one-shot keeper observations and a separate durable alert outbox.

Only an explicitly configured loopback test receiver is supported. Health and
backup integrity never approve live operation, canonical state or host fencing.
Pending age means time observed by this sidecar, not transaction submission age.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import time
from urllib.parse import urlsplit

from keeper.ops import health_check, timestamp
from keeper import recovery_bundle
from zzz_ops.state import atomic_json, process_lock

MAX_CONFIG_BYTES=1024*1024
MAX_HEALTH_BYTES=1024*1024
MAX_STATE_BYTES=1024*1024
MAX_OUTBOX=64
MAX_DELIVERIES=8
MAX_HTTP_BYTES=8192
HTTP_SECONDS=2
REASONS=frozenset(('configuration_unavailable','input_identity_invalid','health_unavailable',
 'health_stale','health_identity_mismatch','health_not_healthy','journal_unavailable',
 'journal_identity_mismatch','pending_ambiguous','pending_prolonged','backup_unavailable',
 'backup_stale','backup_invalid','backup_identity_mismatch','monitor_identity_changed',
 'clock_retreat','source_unavailable','resource_budget'))
REFUSAL_CODES=frozenset(('invalid_input','input_identity','sidecar_state','sidecar_lock',
 'resource_budget','publication','delivery_unavailable','outbox_full'))
EVENT_FIELDS=frozenset(('schema','event_id','type','reason_code','sequence','observed_at',
 'scope_sha256','unsigned','readiness_approved'))
IDENTITY_KEYS=('chain_id','sender','contracts','accounting_model','accounting_version',
 'custody_version','protocol_policy_version','portfolio_version','maintenance_policy_version',
 'rebalance_confirmation_version','fee_intake_version','lp_routing_version',
 'execution_quality_version','execution_price_version','royalty_settlement_version')
PENDING_HEALTH_REASONS=frozenset(('pending','maintenance_not_healthy','no_successful_cycle_yet',
 'execution_observation_not_current','execution_observation_unavailable',
 'confirmation_observation_not_current','confirmation_observation_unavailable'))

class AlertRefusal(ValueError):
    """Fixed diagnostics, excluding paths, configuration and exception text."""
    def __init__(self,code):
        self.code=code if type(code)is str and code in REFUSAL_CODES else 'invalid_input'
        super().__init__('Keeper alert check refused ['+self.code+'].')

def _need(value,code='invalid_input'):
    if not value:raise AlertRefusal(code)

def _uint(value,maximum=(1<<63)-1):
    _need(type(value)is int and 0<=value<=maximum);return value

def _sha(raw):return hashlib.sha256(raw).hexdigest()
def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def _digest(value):return _sha(_json(value))
def _hex(value):return type(value)is str and re.fullmatch('[0-9a-f]{64}',value)is not None

class _Budget:
    def __init__(self,seconds):
        _need(type(seconds)is int and 1<=seconds<=120);self.end=time.monotonic()+seconds
    def check(self):_need(time.monotonic()<self.end,'resource_budget')
    def remaining(self):self.check();return max(1,min(60,int(self.end-time.monotonic())))

def _pairs(rows):
    value={}
    for key,item in rows:_need(key not in value);value[key]=item
    return value

def _decode(raw,*,allow_floats=False):
    def constant(_):raise AlertRefusal('invalid_input')
    value=json.loads(raw.decode('utf8'),object_pairs_hook=_pairs,parse_constant=constant)
    _need(type(value)is dict);stack=[(value,0)];count=0
    while stack:
        item,depth=stack.pop();count+=1;_need(depth<=32 and count<=100000)
        if type(item)is dict:stack.extend((v,depth+1)for v in item.values())
        elif type(item)is list:stack.extend((v,depth+1)for v in item)
        elif type(item)is float:_need(allow_floats and math.isfinite(item))
    return value

def _path(value,base):
    p=Path(value)
    _need(not p.drive or p.is_absolute(),'input_identity')
    _need('..'not in p.parts and not str(p).startswith(('//','\\\\')),'input_identity')
    p=p if p.is_absolute()else base/p
    p=Path(os.path.abspath(p))
    for parent in reversed(p.parents):
        st=parent.lstat();_need(stat.S_ISDIR(st.st_mode)and not parent.is_symlink(),'input_identity')
    if p.exists()or p.is_symlink():_need(not p.is_symlink(),'input_identity')
    return p

def _read(path,maximum,budget):
    budget.check();parent=path.parent.lstat()
    _need(stat.S_ISDIR(parent.st_mode)and parent.st_uid in (0,os.getuid())and not parent.st_mode&0o022,'input_identity')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);_need(stat.S_ISREG(before.st_mode)and before.st_nlink==1
         and before.st_uid in (0,os.getuid())and not before.st_mode&0o022
         and 0<before.st_size<=maximum,'input_identity')
        parts=[];total=0
        while True:
            budget.check();part=os.read(fd,min(65536,maximum+1-total))
            if not part:break
            total+=len(part);_need(total<=maximum,'resource_budget');parts.append(part)
        after=os.fstat(fd);named=path.lstat()
        key=lambda st:(st.st_dev,st.st_ino,st.st_mode,st.st_uid,st.st_nlink,st.st_size,st.st_mtime_ns)
        _need(key(before)==key(after)==key(named)and total==before.st_size,'input_identity')
        return b''.join(parts)
    finally:os.close(fd)

def _identity(config):
    value={k:config.get(k,0 if k.endswith('_version')else None)for k in IDENTITY_KEYS}
    if type(value['sender'])is str:value['sender']=value['sender'].lower()
    contracts=value['contracts']
    if type(contracts)is dict:value['contracts']={k:v.lower()if type(v)is str else v for k,v in contracts.items()}
    return value

def _sidecar(directory,protected):
    # The caller and trusted ancestors remain the host boundary, matching the
    # project's process_lock contract. No original runtime path is written.
    for p in protected:
        _need(directory!=p and not directory.is_relative_to(p)and not p.is_relative_to(directory),'input_identity')
    parent=directory.parent.lstat();_need(parent.st_uid in(0,os.getuid())and not parent.st_mode&0o022,'input_identity')
    if not directory.exists():directory.mkdir(mode=0o700)
    st=directory.lstat();_need(stat.S_ISDIR(st.st_mode)and not directory.is_symlink()
     and st.st_uid==os.getuid()and stat.S_IMODE(st.st_mode)==0o700,'input_identity')
    entries=[]
    for entry in directory.iterdir():
        _need(entry.name in ('state.json','alert.lock')and len(entries)<2,'sidecar_state');entries.append(entry)
        item=entry.lstat();_need(stat.S_ISREG(item.st_mode)and item.st_nlink==1 and not entry.is_symlink()
         and item.st_uid==os.getuid()and not item.st_mode&0o077,'sidecar_state')
        for p in protected:
            try:original=p.lstat()
            except FileNotFoundError:continue
            _need((item.st_dev,item.st_ino)!=(original.st_dev,original.st_ino),'input_identity')

def _event_valid(event):
    _need(type(event)is dict and set(event)==EVENT_FIELDS,'sidecar_state')
    _need(event['schema']==1 and type(event['schema'])is int and _hex(event['event_id'])
     and event['type']in ('incident','recovery')and event['reason_code']in REASONS
     and _hex(event['scope_sha256'])and event['unsigned']is True and event['readiness_approved']is False,'sidecar_state')
    _uint(event['sequence']);_uint(event['observed_at'])
    expected=_digest([1,event['scope_sha256'],event['sequence'],event['type'],event['reason_code']])
    _need(event['event_id']==expected,'sidecar_state')

def _load_state(path,budget):
    if not path.exists():return {'schema':1,'scope_sha256':None,'sequence':0,'last_observed_at':0,'active':{},'pending':None,'outbox':[]}
    state=_decode(_read(path,MAX_STATE_BYTES,budget))
    _need(set(state)=={'schema','scope_sha256','sequence','last_observed_at','active','pending','outbox'}
     and type(state['schema'])is int and state['schema']==1 and
     (state['scope_sha256']is None or _hex(state['scope_sha256'])),'sidecar_state')
    _uint(state['sequence']);_uint(state['last_observed_at'])
    _need(type(state['active'])is dict and set(state['active'])<=REASONS and
     all(_hex(v)for v in state['active'].values()),'sidecar_state')
    p=state['pending']
    _need(p is None or type(p)is dict and set(p)=={'intent_sha256','first_seen'}
     and _hex(p['intent_sha256'])and type(p['first_seen'])is int and 0<=p['first_seen']<=state['last_observed_at'],'sidecar_state')
    _need(type(state['outbox'])is list and len(state['outbox'])<=MAX_OUTBOX,'sidecar_state')
    ids=[];sequence=0
    for e in state['outbox']:
        _event_valid(e);_need(sequence<e['sequence']<=state['sequence'],'sidecar_state');sequence=e['sequence'];ids.append(e['event_id'])
    _need(len(ids)==len(set(ids)),'sidecar_state');return state

def _receiver(value):
    if value is None:return None
    _need(type(value)is str and len(value)<=128)
    p=urlsplit(value)
    try:port=p.port
    except ValueError:raise AlertRefusal('invalid_input')from None
    _need(p.scheme=='http'and p.hostname=='127.0.0.1'and type(port)is int and 1<=port<=65535
     and p.netloc=='127.0.0.1:'+str(port)and p.path=='/alerts'and not p.query and not p.fragment
     and p.username is None and p.password is None)
    return port

def _deliver(port,event,budget):
    payload=_json(event);_need(len(payload)<=2048,'resource_budget');budget.check()
    end=min(budget.end,time.monotonic()+HTTP_SECONDS)
    request=(b'POST /alerts HTTP/1.1\r\nHost: 127.0.0.1:'+str(port).encode()+
     b'\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: '+str(len(payload)).encode()+b'\r\n\r\n'+payload)
    with socket.create_connection(('127.0.0.1',port),timeout=max(.001,end-time.monotonic()))as conn:
        conn.settimeout(max(.001,end-time.monotonic()));conn.sendall(request);raw=bytearray();length=None;offset=None
        while True:
            _need(time.monotonic()<end,'delivery_unavailable');conn.settimeout(max(.001,end-time.monotonic()))
            part=conn.recv(min(4096,MAX_HTTP_BYTES+1-len(raw)))
            if not part:break
            raw.extend(part);_need(len(raw)<=MAX_HTTP_BYTES,'delivery_unavailable')
            if offset is None and b'\r\n\r\n'in raw:
                header,body=bytes(raw).split(b'\r\n\r\n',1);offset=len(header)+4
                lines=header.decode('ascii').split('\r\n');_need(len(lines)<=33,'delivery_unavailable')
                status=re.fullmatch(r'HTTP/1\.[01] ([0-9]{3})(?: [\x20-\x7e]*)?',lines[0]);_need(status is not None and 200<=int(status[1])<300,'delivery_unavailable')
                headers={}
                for line in lines[1:]:
                    name,sep,value=line.partition(':');name=name.lower()
                    _need(sep and re.fullmatch('[a-z0-9-]+',name)and name not in headers,'delivery_unavailable');headers[name]=value.strip()
                _need('transfer-encoding'not in headers and headers.get('content-encoding','identity')=='identity'
                 and re.fullmatch('[0-9]{1,4}',headers.get('content-length','')),'delivery_unavailable')
                length=int(headers['content-length']);_need(0<length<=4096,'delivery_unavailable')
            if offset is not None and len(raw)>=offset+length:break
        _need(offset is not None and len(raw)==offset+length,'delivery_unavailable')
        ack=_decode(bytes(raw[offset:]));_need(set(ack)=={'event_id','accepted'}and
         ack['event_id']==event['event_id']and ack['accepted']is True,'delivery_unavailable')

def _pending(state,health,config,prior,now):
    pending=state.get('pending')
    if pending is None:return None,None,False
    if not(type(pending)is dict and type(pending.get('key'))is str and len(pending['key'])<=200
     and type(pending.get('nonce'))is int and 0<=pending['nonce']<1<<64
     and type(pending.get('to'))is str and re.fullmatch('0x[0-9a-fA-F]{40}',pending['to'])
     and type(pending.get('data'))is str and len(pending['data'])<=262144
     and re.fullmatch('0x(?:[0-9a-fA-F]{2})*',pending['data'])and pending.get('value')==0):
        return None,None,False
    fingerprint=_digest([_identity(config),pending['key'],pending['nonce'],pending['to'].lower(),pending['data'].lower(),pending['value']])
    observed=prior if type(prior)is dict and prior['intent_sha256']==fingerprint else{'intent_sha256':fingerprint,'first_seen':now}
    age=now-observed['first_seen'];h=pending.get('hash')
    ordinary=(type(h)is str and re.fullmatch('0x[0-9a-fA-F]{64}',h)is not None and int(h,16)!=0
     and health.get('status')=='awaiting_receipt'and health.get('pending')is True
     and health.get('pending_action')==pending['key']and state.get('next_nonce')==pending['nonce'])
    return observed,age,ordinary

def run_once(config_path,*,working_directory,backup_bundle,backup_manifest_sha256,backup_config_path,
             directory,max_health_age_seconds,max_backup_age_seconds,pending_max_age_seconds,
             receiver=None,allow_dry_run=False,now=None,max_seconds=60,max_bytes=recovery_bundle.DEFAULT_BYTES):
    """Observe once, persist before delivery, and return only sanitized facts.

    Missing/invalid inputs cannot produce a recovery. A recorded pending grace
    does not change health_check's unready result. Delivery is at least once;
    receivers must use event_id for deduplication after an ambiguous ack.
    """
    _need(os.name=='posix');budget=_Budget(max_seconds);now=int(time.time())if now is None else _uint(now)
    for value in(max_health_age_seconds,max_backup_age_seconds,pending_max_age_seconds):_need(type(value)is int and 1<=value<=31536000)
    _need(type(allow_dry_run)is bool and type(max_bytes)is int and 1<=max_bytes<=recovery_bundle.MAX_BYTES)
    _need(_hex(backup_manifest_sha256));port=_receiver(receiver)
    base=Path(working_directory);_need(base.is_absolute());base=_path(base,Path('/'))
    cfg_path=_path(config_path,base);backup_cfg_path=_path(backup_config_path,base)
    bundle=_path(backup_bundle,base);sidecar=_path(directory,base)
    reasons=[];config=backup_config=None;health=journal=None;health_ok=backup_ok=False;health_reasons=None;current_identity=None
    cfg_raw=backup_cfg_raw=None;health_raw=journal_raw=None;health_path=journal_path=None;sources=None
    try:
        # Share the current reviewed profile parser, without constructing Keeper.
        # The first bounded read rejects FIFOs/oversized files before its reader.
        cfg_raw=_read(cfg_path,MAX_CONFIG_BYTES,budget)
        _,checked_raw,config,current_identity=recovery_bundle._configuration(cfg_path,budget)
        _need(checked_raw==cfg_raw,'input_identity')
    except Exception:reasons.append('configuration_unavailable')
    try:backup_cfg_raw=_read(backup_cfg_path,MAX_CONFIG_BYTES,budget);backup_config=_decode(backup_cfg_raw)
    except Exception:reasons.append('backup_unavailable')
    protected=[cfg_path,backup_cfg_path,bundle]
    if config is not None:
        journal_path=_path(config.get('state_path','var/keeper.json'),base)
        health_path=_path(config.get('health_path',str(journal_path.with_suffix('.health.json'))),base)
        _need(len({cfg_path,journal_path,health_path})==3,'input_identity')
        protected.extend((journal_path,journal_path.parent,health_path))
        for k in('keystore','password_file','lock_path'):
            if config.get(k):
                reference=_path(config[k],base)
                _need(reference not in {cfg_path,backup_cfg_path,journal_path,health_path},'input_identity')
                protected.append(reference)
    _sidecar(sidecar,protected)
    try:guard=process_lock(sidecar/'alert.lock');guard.__enter__()
    except Exception:raise AlertRefusal('sidecar_lock')from None
    try:
        state=_load_state(sidecar/'state.json',budget)
        if now<state['last_observed_at']:reasons.append('clock_retreat')
        observed_at=max(now,state['last_observed_at'])
        if config is not None:
            try:
                health_raw=_read(health_path,MAX_HEALTH_BYTES,budget);health=_decode(health_raw,allow_floats=True)
                checked=health_check(config,max_age=max_health_age_seconds,allow_dry_run=allow_dry_run,now=now,snapshot=health)
                health_ok=checked['ok']is True;health_reasons=checked['reasons']
                age=now-timestamp(health.get('time'))
                if age< -30 or age>max_health_age_seconds:reasons.append('health_stale')
                if(health.get('configuration_sha256')!=_digest(config)or health.get('chain_id')!=config.get('chain_id')
                   or health.get('sender')!=str(config.get('sender','')).lower()):reasons.append('health_identity_mismatch')
            except Exception:reasons.append('health_unavailable')
            try:
                journal_raw=_read(journal_path,max_bytes,budget)
                journal=recovery_bundle._state(journal_raw,current_identity)
            except Exception:reasons.append('journal_unavailable')
        try:sources=recovery_bundle.source_hashes(budget=budget)
        except Exception:reasons.append('source_unavailable')
        if backup_config is not None:
            try:
                recovery_bundle.verify(bundle,backup_manifest_sha256,backup_cfg_path,max_age_seconds=max_backup_age_seconds,
                 max_bytes=max_bytes,max_seconds=budget.remaining(),now=now)
                backup_ok=True
                if config is None or _digest(_identity(backup_config))!=_digest(_identity(config)):
                    backup_ok=False;reasons.append('backup_identity_mismatch')
            except recovery_bundle.RecoveryRefusal as exc:
                reasons.append('backup_stale'if exc.code=='backup_age_or_floor'else'backup_invalid')
            except Exception:reasons.append('backup_unavailable')
        scope=_digest([1,_sha(cfg_raw)if cfg_raw else None,_sha(backup_cfg_raw)if backup_cfg_raw else None,sources,
         max_health_age_seconds,max_backup_age_seconds,pending_max_age_seconds,allow_dry_run])
        if state['scope_sha256']is not None and scope!=state['scope_sha256']:reasons.append('monitor_identity_changed')
        pending_observed=None;pending_age=None;ordinary=False
        if journal is not None and health is not None and config is not None:
            pending_observed,pending_age,ordinary=_pending(journal,health,config,state['pending'],observed_at)
            if journal.get('pending')is not None:
                if not ordinary:reasons.append('pending_ambiguous')
                elif pending_age>pending_max_age_seconds:reasons.append('pending_prolonged')
            elif health.get('pending')is not False:reasons.append('pending_ambiguous')
        ordinary=(ordinary and not reasons and health_reasons is not None and set(health_reasons)<=PENDING_HEALTH_REASONS
         and health is not None and health.get('live')is(not allow_dry_run)
         and health.get('strategy_paused')is False and health.get('canonical_state')==0 and health.get('preparation_active')is False
         and all(type(health.get(k))is int and health[k]==0 for k in('skipped_buckets','blocked_actions','consecutive_failures','confirmed_reverts')))
        if not health_ok and not ordinary:reasons.append('health_not_healthy')
        # Re-read only the already identified inputs. Never recover from a
        # capture invalidated between validation and outbox publication.
        try:
            if cfg_raw is not None:_need(_read(cfg_path,MAX_CONFIG_BYTES,budget)==cfg_raw,'input_identity')
            if backup_cfg_raw is not None:_need(_read(backup_cfg_path,MAX_CONFIG_BYTES,budget)==backup_cfg_raw,'input_identity')
            if health_raw is not None:_need(_read(health_path,MAX_HEALTH_BYTES,budget)==health_raw,'input_identity')
            if journal_raw is not None:_need(_read(journal_path,max_bytes,budget)==journal_raw,'input_identity')
            _need(recovery_bundle.source_hashes(budget=budget)==sources,'input_identity')
        except Exception:reasons.append('input_identity_invalid');health_ok=backup_ok=False;ordinary=False
        reasons=sorted(set(reasons));_need(set(reasons)<=REASONS)
        healthy=health_ok and backup_ok and not reasons
        classification='healthy'if healthy else'pending_grace'if ordinary and backup_ok and not reasons else'incident'
        attempted=acknowledged=0;delivery='disabled'if port is None else'no_events';delivery_failed=False
        def drain():
            nonlocal attempted,acknowledged,delivery,delivery_failed
            if port is None or delivery_failed:return
            while state['outbox']and attempted<MAX_DELIVERIES:
                attempted+=1
                try:_deliver(port,state['outbox'][0],budget)
                except Exception:delivery='failed';delivery_failed=True;break
                state['outbox'].pop(0)
                try:atomic_json(sidecar/'state.json',state)
                except Exception:raise AlertRefusal('publication')from None
                acknowledged+=1;delivery='acknowledged'
        # Existing events are already durable. Drain them before applying new
        # transitions so a full queue can recover once its receiver is healthy.
        # Both drains share the same eight-attempt bound for this invocation.
        drain()
        new_ids=[]
        def queue(kind,code):
            _need(len(state['outbox'])<MAX_OUTBOX,'outbox_full');state['sequence']+=1
            event={'schema':1,'type':kind,'reason_code':code,'sequence':state['sequence'],'observed_at':observed_at,
             'scope_sha256':scope,'unsigned':True,'readiness_approved':False}
            event['event_id']=_digest([1,scope,event['sequence'],kind,code]);_event_valid(event)
            state['outbox'].append(event);new_ids.append(event['event_id']);return event['event_id']
        for code in reasons:
            if code not in state['active']:state['active'][code]=queue('incident',code)
        if healthy:
            for code in sorted(state['active']):queue('recovery',code)
            state['active']={}
        state.update(scope_sha256=scope,last_observed_at=observed_at,pending=pending_observed)
        budget.check();_need(len(_json(state))<=MAX_STATE_BYTES,'resource_budget')
        try:atomic_json(sidecar/'state.json',state)
        except Exception:raise AlertRefusal('publication')from None
        drain()
        return {'schema':1,'unsigned':True,'readiness_approved':False,
         'ok':classification in('healthy','pending_grace')and not state['outbox'],
         'observation':{'health_ok':health_ok,'backup_ok':backup_ok,'classification':classification,
          'reason_codes':reasons,'pending_observed_seconds':pending_age},
         'delivery':{'attempted':attempted,'acknowledged':acknowledged,'state':delivery},
         'outbox_count':len(state['outbox']),'active_incident_count':len(state['active']),'event_ids':new_ids}
    finally:guard.__exit__(None,None,None)
