"""One reviewed NEW alert selection; only the fixed c815 unit may run/stop."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys,time

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
RUN=BASE/'campaign-001'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def need(value):
    if not value:raise ValueError('Reviewed isolated alert campaign refused')

def main():
    approval=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    expected={'c815.inputs.tar.gz','remote_capsule.py','host_control.py','orchestrate_c815.py','package_c815.py',
        'capsule_template.py','run_selected_template.py','run_selected.py',
        'keeper/alerts.py','keeper/ops.py','scripts/keeper-alerts.py','tests_python/test_keeper_alerts.py'}
    need(set(approval)==expected and not RUN.exists())
    for name,digest in approval.items():
        path=(ROOT/name)if'/'in name else(BASE/name)
        need(sha(path.read_bytes())==digest)
    RUN.mkdir(mode=0o755);start=time.monotonic();phase_end=start+240;final_end=start+300
    counts={};actions=[];start_attempted=False;installed=False;selection_complete=False;cleanup=False;failure=None;artifacts={}
    def write(name,value):
        with(RUN/name).open('x',encoding='utf8')as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    write('PREEXECUTION_APPROVAL.json',{'schema':1,'pins':approval,'all_test_bodies_NEW':True,
        'phase_seconds':240,'cleanup_seconds':60,'unit_work_seconds':180,'combined_output_bytes':65536,
        'only_private_loopback_HTTP':True,'public_transactions':0,'new_seals':0,'production_adoption':False})
    def progress(stage,**detail):print(json.dumps({'stage':stage,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**detail}),flush=True)
    def action(name,*,artifact=None,cleanup_mode=False):
        need(time.monotonic()+50<=(final_end if cleanup_mode else phase_end))
        index=counts.get(name,0)+1;counts[name]=index;label=f'{name}-{index:03d}';output=RUN/label
        stdout=RUN/(label+'.stdout');stderr=RUN/(label+'.stderr')
        argv=[sys.executable,'-B','-X','utf8',str(BASE/'host_control.py'),name,'--output',str(output)]
        if artifact:argv+=['--artifact',artifact]
        began=time.monotonic();reason=None
        with stdout.open('xb')as out,stderr.open('xb')as err:
            child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                while child.poll()is None:
                    if time.monotonic()-began>48:reason='parent_action_timeout';child.kill();break
                    if stdout.stat().st_size+stderr.stat().st_size>65536:reason='parent_output_limit';child.kill();break
                    time.sleep(.1)
                child.wait(timeout=2)
            finally:
                if child.poll()is None:child.kill();child.wait(timeout=2)
        actions.append({'action':name,'index':index,'artifact':artifact,'exit_code':child.returncode,'reason':reason,
            'seconds':time.monotonic()-began,'stdout_sha256':sha(stdout.read_bytes()),'stderr_sha256':sha(stderr.read_bytes())})
        need(child.returncode==0 and reason is None)
        receipt=json.loads((output/'EXECUTION.json').read_bytes())
        need(receipt['exit_code']==0 and receipt['capture_reason']is None and not receipt['capture_errors'])
        return json.loads((output/(artifact if name=='fetch'else'PUBLIC_RESULT.json')).read_bytes())
    try:
        progress('installing_reviewed_readonly_alert_selection')
        action('install');installed=True
        # Installation cannot start a service. An unknown START reply can, so
        # cleanup becomes mandatory only immediately before that action.
        start_attempted=True;action('start')
        progress('running_NEW_Ubuntu_alert_methods')
        while True:
            status=action('status')
            need(not status['output_limit_exceeded'])
            if status['terminal']:
                need(status['result_present']);selection_complete=True;break
            need(time.monotonic()+55<phase_end);time.sleep(3)
    except BaseException as exc:
        failure={'phase':'selection','error_type':type(exc).__name__};progress('selection_refused',error_type=type(exc).__name__)
    finally:
        if start_attempted:
            progress('stopping_only_fixed_new_alert_unit')
            try:
                stopped=action('stop',cleanup_mode=True);cleanup=stopped.get('all_owned_group_empty')is True
            except BaseException as exc:failure=failure or{'phase':'cleanup','error_type':type(exc).__name__}
    if cleanup:
        for name in ('RESULT.json','FINAL.json'):
            try:artifacts[name]=action('fetch',artifact=name,cleanup_mode=True)
            except BaseException as exc:failure=failure or{'phase':'saved_export','error_type':type(exc).__name__}
    selected=artifacts.get('RESULT.json',{});final=artifacts.get('FINAL.json',{})
    accepted=(selection_complete and cleanup and failure is None and selected.get('success')is True
        and selected.get('tests_run')==len(selected.get('selected_methods',[]))and selected.get('tests_run',0)>0
        and selected.get('errors')==selected.get('failures')==selected.get('skipped')==0
        and final.get('source_unchanged')is True and final.get('all_owned_group_empty')is True)
    result={'schema':1,'success':bool(accepted),'installed':installed,'process_start_attempted':start_attempted,
        'cleanup_required':start_attempted,'cleanup':cleanup,'failure':failure,'selection_complete':selection_complete,
        'elapsed_seconds':time.monotonic()-start,'actions':actions,'source_pins':approval,
        'tests_run':selected.get('tests_run'),'old_test_bodies_run':0,'public_transactions':0,
        'existing_environment_changes':False,'offhost_or_external_alert_delivery_qualified':False,
        'parent_host_preservation_review_required':True,'production_approved':False}
    write('ORCHESTRATION_RESULT.json',result);progress('alert_campaign_complete',success=bool(accepted),cleanup=cleanup)
    return 0 if accepted else 1

if __name__=='__main__':raise SystemExit(main())
