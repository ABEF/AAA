"""Fixed c813 composition; no action on import, no generic remote execution.

Only a NEW private lab. At most 600 seconds phase work + 240 seconds cleanup.
Always stop the keeper group before the model, including on evidence errors.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
RUN=BASE/'campaign-001'
HOST=BASE/'host_control.py'
MODEL='popl-ubuntu-backup-recovery-20261126-c813-model.service'
KEEPER='popl-ubuntu-backup-recovery-20261126-c813-keeper.service'
RESOLVE='popl-ubuntu-backup-recovery-20261126-c813-resolve.service'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def need(value,reason):
    if not value:raise RuntimeError(reason)


def main():
    need(not RUN.exists(),'Fresh campaign output required')
    # The separate root-approved pin file is generated only after static review.
    pins=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    need(set(pins)=={'c813.inputs.tar.gz','remote_capsule.py','host_control.py','orchestrate_c813.py','package_c813.py','capsule_extension.py','model_service.py','recovery_control.py','independent_private.py'},'Root review pin set differs')
    for name,digest in pins.items():need(sha((BASE/name).read_bytes())==digest,'Reviewed preparation changed')
    RUN.mkdir(mode=0o700)
    def write(name,value):
        with (RUN/name).open('x',encoding='utf8')as stream:
            stream.write(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    def progress(stage,**fields):
        print(json.dumps({'stage':stage,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**fields}),flush=True)
    write('PARENT_PREEXECUTION_APPROVAL.json',{'schema':1,'pins':pins,
        'scope':'Only fixed c813 upload/install/start/status/startkeeper/stopkeeper/fence/recover/dry/stop/fetch; same-host runtime separation, not off-host fencing',
        'phase_seconds':600,'cleanup_seconds':240,'total_seconds':840,'RPC_maximum':6000,
        'public_transactions':0,'new_seals':0,'production_source_changes':0,'old_test_bodies_run':0})
    started=time.monotonic();phase_end=started+600;all_end=started+840
    actions=[];counts={};install_attempted=False;installed=False;completed=False;cleanup=False;failure=None;exported={};last=None
    def action(name,*,cleanup_mode=False,artifact=None):
        limit=150 if name in ('upload','install')else 55
        need(time.monotonic()+limit<=(all_end if cleanup_mode else phase_end),'Reserved action deadline exhausted')
        index=counts.get(name,0)+1;counts[name]=index;label=f'{name}-{index:03d}'
        output=RUN/label;stdout=RUN/(label+'.parent.stdout');stderr=RUN/(label+'.parent.stderr')
        argv=[sys.executable,'-X','utf8',str(HOST),name,'--output',str(output)]
        if name=='upload':argv+=['--bundle',str(BASE/'c813.inputs.tar.gz')]
        if name=='install':argv+=['--bundle-sha256',pins['c813.inputs.tar.gz']]
        if name=='fetch':argv+=['--artifact',artifact]
        begin=time.monotonic();reason=None
        with stdout.open('xb')as out,stderr.open('xb')as err:
            child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
            try:
                while child.poll()is None:
                    if time.monotonic()-begin>limit:reason='parent_action_timeout';child.kill();break
                    if stdout.stat().st_size+stderr.stat().st_size>65536:reason='parent_capture_overflow';child.kill();break
                    time.sleep(.1)
                child.wait(timeout=2)
            finally:
                if child.poll()is None:child.kill();child.wait(timeout=2)
        row={'action':name,'attempt':index,'artifact':artifact,'exit_code':child.returncode,
            'reason':reason,'seconds':time.monotonic()-begin,
            'parent_stdout_sha256':sha(stdout.read_bytes()),'parent_stderr_sha256':sha(stderr.read_bytes())}
        actions.append(row)
        need(child.returncode==0 and reason is None,'Fixed host action refused: '+name)
        receipt=json.loads((output/'EXECUTION.json').read_bytes())
        need(receipt['exit_code']==0 and receipt.get('failed_capture_reason')is None,'Bounded host capture refused')
        return json.loads((output/(artifact if name=='fetch'else'PUBLIC_RESULT.json')).read_bytes())
    def state_until(marker):
        while True:
            state=action('status')
            if marker in state['public_files']:return state
            need(state['native']['units'][MODEL]['properties'].get('ActiveState')=='active','Private model exited before '+marker)
            need(time.monotonic()+65<phase_end,'Phase deadline waiting for '+marker)
            time.sleep(3)
    def stop_keeper():
        action('stopkeeper')
        while True:
            state=action('status');row=state['native']['units'][KEEPER];p=row['properties']
            if p.get('ActiveState')in ('inactive','failed')and p.get('MainPID','0')=='0'and not row['cgroup']['pids']:return state
            need(time.monotonic()+65<phase_end,'Keeper fencing deadline');time.sleep(2)
    try:
        progress('uploading_reviewed_new_lab')
        action('upload')
        # Once install is invoked it may have partially created this new lab,
        # even if its reply is lost. Upload-only failure cannot have services.
        install_attempted=True
        action('install');installed=True;action('start')
        state_until('model-READY.json');action('startkeeper')
        progress('waiting_for_one_actual_accepted_hash_known_pending')
        state_until('model-PENDING_READY.json');stop_keeper();action('fence')
        progress('old_group_fenced_snapshotting_and_restoring_exact_pending_bytes')
        state_until('model-INCLUDED.json');action('recover')
        progress('checking_unsigned_stock_receipt_recovery')
        state_until('model-SETTLED.json');action('dry')
        progress('checking_unsigned_fresh_metadata_review')
        state_until('model-COMPLETE.json')
        complete=action('fetch',artifact='model-COMPLETE.json')
        need(complete.get('success')is True,'Model completion refused')
        completed=True
    except BaseException as exc:
        failure={'stage':'phase','error_type':type(exc).__name__,
            'fixed_reason':str(exc)if type(exc)is RuntimeError else None}
        progress('campaign_refused',error_type=type(exc).__name__)
    finally:
        if install_attempted:
            progress('stopping_only_owned_c813_groups')
            while time.monotonic()+55<=all_end:
                try:
                    result=action('stop',cleanup_mode=True)
                    if result.get('all_owned_units_stopped')is True:
                        need(all(not r['cgroup']['pids']and r['properties'].get('MainPID','0')=='0'
                            for r in result['native_status']['units'].values()),'Owned group remains live')
                        cleanup=True;break
                except BaseException as exc:actions.append({'action':'cleanup_observation','error_type':type(exc).__name__})
                time.sleep(3)
            progress('owned_cleanup_observed',all_groups_empty=cleanup)
    if install_attempted and cleanup:
        try:
            last=action('status',cleanup_mode=True)
            # Fetch only the capsule's explicit public JSON allowlist; never keys,
            # raw signed envelopes, or arbitrary paths. Freeze each once locally.
            for artifact in last['public_files']:
                need(type(artifact)is str and'/'not in artifact and'\\'not in artifact,'Invalid public artifact name')
                if not artifact.endswith('.json'):continue
                exported[artifact]=action('fetch',cleanup_mode=True,artifact=artifact)
        except BaseException as exc:failure=failure or{'stage':'post_cleanup_export','error_type':type(exc).__name__}
    model=exported.get('model-RESULT.json',{})
    independent=exported.get('model-INDEPENDENT.json',{})
    accepted=(completed and cleanup and failure is None and model.get('success')is True
        and model.get('final_financial_capture_complete')is True
        and model.get('post_inclusion_financial_unchanged')is True
        and independent.get('success')is True
        and model.get('raw_attempts')==1 and model.get('raw_forwarded')==1
        and model.get('shared_RPC_requests',6001)<=6000)
    result={'schema':1,'success':bool(accepted),'completed':completed,'cleanup':cleanup,'failure':failure,
        'installation_attempted':install_attempted,'installation_succeeded':installed,
        'cleanup_required':install_attempted,'cleanup_skipped_no_install_attempt':not install_attempted,
        'independent_check_passed':independent.get('success')is True,
        'elapsed_seconds':time.monotonic()-started,'actions':actions,'exports':list(exported),'final_status':last,
        'root_original_host_comparison_required':True,'public_transactions':0,'new_seals':0,
        'old_test_bodies_run':0,'new_test_bodies_run':0,'new_composed_scenarios':1,'production_approved':False}
    write('ORCHESTRATION_RESULT.json',result)
    progress('campaign_complete',success=bool(accepted),cleanup=cleanup,shared_RPC_requests=model.get('shared_RPC_requests'))
    return 0 if accepted else 1


if __name__=='__main__':raise SystemExit(main())
