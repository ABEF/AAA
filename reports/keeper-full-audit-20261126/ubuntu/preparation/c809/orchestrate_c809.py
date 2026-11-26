"""Parent-reviewed fixed c809 campaign. NO action on import.

Only reviewed host_control actions; phase work<=600s, cleanup<=240s, total<=840s.
Always stop both exact owned units after any attempted installation/start.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

BASE=Path(__file__).resolve().parent
HOST=BASE/'host_control.py'
BUNDLE=BASE/'c809.inputs.tar.gz'
RUN=BASE/'campaign-001'
PINS={'c809.inputs.tar.gz':'96224579d6e05e990aa207e53dc6b6829713d4b3c8c0f17866b18dfae25b39cd',
    'remote_capsule.py':'85affe72b0e9b25144523db3176d36db39756702c263a589b373430ae941f94b',
    'host_control.py':'478b39e3c9797ed2381e3284ec7a71490ac5c6dddf2d8a08a98fe569ad10cdc0'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def need(value,message):
    if not value:raise RuntimeError(message)

def write(name,value):
    path=RUN/name
    with path.open('x',encoding='utf8')as stream:stream.write(json.dumps(value,indent=2,sort_keys=True)+'\n')

def progress(stage,**fields):print(json.dumps({'stage':stage,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**fields}),flush=True)

def main():
    need(not RUN.exists(),'Fresh campaign output required');RUN.mkdir(mode=0o700)
    for name,pin in PINS.items():need(sha((BASE/name).read_bytes())==pin,'Parent-approved prepared source changed')
    write('PARENT_PREEXECUTION_APPROVAL.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'authorization':'Root reviewed generated capsule/build/hostwrapper and authorized ONLY fixed NEW c809 upload/install/start/status/prove/repair/stop/fetch',
        'pins':PINS,'no_public_transactions_or_sealing':True,'original_environments_preserved':True,
        'phase_seconds':600,'cleanup_seconds':240,'total_seconds':840,'RPC_maximum':6000})
    started=time.monotonic();phase_end=started+600;all_end=started+840
    counts={};actions=[];installed_or_attempted=False;completed=False;cleanup=False;failure=None;final_status=None
    def action(name,*,cleanup_mode=False,artifact=None):
        end=all_end if cleanup_mode else phase_end
        timeout=150 if name in ('upload','install')else 55
        need(time.monotonic()+timeout<=end,'Reserved action/cleanup deadline exhausted')
        index=counts.get(name,0)+1;counts[name]=index;label=f'{name}-{index:03d}'
        output=RUN/label
        command=[sys.executable,'-X','utf8',str(HOST),name,'--output',str(output)]
        if name=='upload':command+=['--bundle',str(BUNDLE)]
        if name=='install':command+=['--bundle-sha256',PINS['c809.inputs.tar.gz']]
        if name=='fetch':command+=['--artifact',artifact]
        log=RUN/(label+'.parent.stdout');err=RUN/(label+'.parent.stderr')
        before=time.monotonic();reason=None
        with log.open('xb')as stdout,err.open('xb')as stderr:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
            try:
                while child.poll()is None:
                    if time.monotonic()-before>timeout:reason='parent_action_timeout';child.kill();break
                    if log.stat().st_size+err.stat().st_size>65536:reason='parent_capture_overflow';child.kill();break
                    time.sleep(.1)
                child.wait(timeout=2)
            finally:
                if child.poll()is None:child.kill();child.wait(timeout=2)
        row={'action':name,'attempt':index,'artifact':artifact,'exit_code':child.returncode,
            'reason':reason,'seconds':time.monotonic()-before,'parent_stdout_sha256':sha(log.read_bytes()),
            'parent_stderr_sha256':sha(err.read_bytes())}
        actions.append(row)
        need(child.returncode==0 and reason is None,'Fixed host action refused')
        receipt=json.loads((output/'EXECUTION.json').read_bytes())
        need(receipt['exit_code']==0 and receipt.get('failed_capture_reason')is None,'Host capture refused')
        if name=='fetch':return json.loads((output/artifact).read_bytes())
        return json.loads((output/'PUBLIC_RESULT.json').read_bytes())
    try:
        progress('uploading_reviewed_bundle')
        action('upload');installed_or_attempted=True;action('install')
        progress('starting_private_model')
        action('start')
        while True:
            state=action('status');native=state['native'];model=native['units']['popl-keeper-full-audit-20261126-c809-model.service']
            if 'model-READY.json'in state['public_files']:break
            need(model['properties'].get('ActiveState')not in ('failed','inactive'),'Model exited before ready')
            need(time.monotonic()+65<phase_end,'Model ready deadline');time.sleep(5)
        progress('model_ready_linux_check_completed_starting_invalid_keeper')
        action('startkeeper')
        while True:
            state=action('status');p=state['native']['units']['popl-keeper-full-audit-20261126-c809-keeper.service']['properties']
            if p.get('Result')=='start-limit-hit':break
            need(p.get('ActiveState')!='failed','Unexpected native keeper failure')
            need(time.monotonic()+65<phase_end,'Rate-limit deadline');time.sleep(10)
        action('prove');progress('five_native_failures_sixth_refused_original_journal_preserved')
        action('repair');progress('restored_exact_good240_configuration')
        while True:
            state=action('status');native=state['native']
            if 'model-COMPLETE.json'in state['public_files']:
                complete=action('fetch',artifact='model-COMPLETE.json');need(complete.get('success')is True,'Model completion refused');break
            need(native['units']['popl-keeper-full-audit-20261126-c809-model.service']['properties'].get('ActiveState')=='active','Model stopped before healthy idle')
            need(native['units']['popl-keeper-full-audit-20261126-c809-keeper.service']['properties'].get('ActiveState')not in ('failed','inactive'),'Repaired keeper stopped')
            need(time.monotonic()+65<phase_end,'Healthy cycle deadline');time.sleep(5)
        completed=True;progress('fresh_healthy_idle_cycle_zero_stock_sends')
    except BaseException as exc:
        failure={'error_type':type(exc).__name__,'stage':'campaign','fixed_reason':str(exc)if type(exc)is RuntimeError else None}
        progress('campaign_refused',error_type=type(exc).__name__)
    finally:
        if installed_or_attempted:
            progress('stopping_only_owned_c809_units')
            while time.monotonic()+55<=all_end:
                try:
                    result=action('stop',cleanup_mode=True)
                    if result.get('phase')=='stopped'and result.get('all_owned_units_stopped')is True:
                        native=result['native_status']
                        need(all(not row['cgroup']['pids']and row['properties'].get('MainPID','0')=='0'for row in native['units'].values()),'Final owned cgroup is not empty')
                        cleanup=True;break
                except BaseException as exc:
                    actions.append({'action':'cleanup_observation','error_type':type(exc).__name__})
                time.sleep(5)
            progress('owned_cleanup_observed',both_cgroups_empty=cleanup)
    # Read-only exports after cleanup; no retry or worker/financial journey rerun.
    exported={}
    if installed_or_attempted and cleanup:
        try:
            final_status=action('status',cleanup_mode=True)
            for artifact in ('model-RESULT.json','model-SELECTED_LINUX_TEST.json','native-RATE_LIMIT_PROOF.json',
                    'native-REPAIR.json','native-FINAL_STOP.json','case-INITIAL_JOURNAL.json','case-FINAL_JOURNAL.json',
                    'case-HEALTHY_IDLE_CYCLE.json','case-FINANCIAL_BEFORE.json','case-FINANCIAL_AFTER.json',
                    'case-SETUP.json','case-RECEIPTS.json','case-RAW_REVIEWS.json','model-EVENTS.json'):
                if artifact in final_status['public_files']:exported[artifact]=action('fetch',cleanup_mode=True,artifact=artifact)
        except BaseException as exc:
            failure=failure or {'error_type':type(exc).__name__,'stage':'post_cleanup_export'}
    model=exported.get('model-RESULT.json',{});test=exported.get('model-SELECTED_LINUX_TEST.json',{})
    proof=exported.get('native-RATE_LIMIT_PROOF.json',{})
    accepted=(completed and cleanup and failure is None and model.get('success')is True and model.get('raw_attempts')==0 and
        model.get('raw_forwarded')==0 and model.get('shared_RPC_requests',6001)<=6000 and test.get('success')is True and
        test.get('tests_run')==1 and test.get('skipped')==0 and proof.get('five_started_sixth_refused')is True)
    result={'schema':1,'success':bool(accepted),'completed':completed,'cleanup':cleanup,'failure':failure,
        'elapsed_seconds':time.monotonic()-started,'actions':actions,'exports':list(exported),
        'final_status':final_status,'root_original_host_state_comparison_required':True,
        'public_transactions':0,'new_seals':0,'old_green_test_bodies_run':0,'production_approved':False}
    write('ORCHESTRATION_RESULT.json',result);progress('campaign_complete',success=bool(accepted),cleanup=cleanup,
        shared_RPC_requests=model.get('shared_RPC_requests'),selected_new_Linux_tests=test.get('tests_run'))
    return 0 if accepted else 1

if __name__=='__main__':raise SystemExit(main())
