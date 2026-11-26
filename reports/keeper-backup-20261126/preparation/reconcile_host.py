"""Classify only the five saved observer lifecycle differences, offline."""
from pathlib import Path
import argparse,ast,datetime as dt,hashlib,json

SERVICE='zzz-stage-observer.service';TIMER='zzz-stage-observer.timer'
START='7d4958e842da4a758f6c1cdc7b36dcc5'
SUCCESS='7ad2d189f7e94e70a38c781354912448'
STARTED='39f53479d3a045ac8e11786248231fbf'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def micros(value):
 stamp=dt.datetime.fromisoformat(value)
 assert stamp.tzinfo is not None
 delta=stamp.astimezone(dt.timezone.utc)-dt.datetime(1970,1,1,tzinfo=dt.timezone.utc)
 return (delta.days*86400+delta.seconds)*1000000+delta.microseconds


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path.cwd());a=parser.parse_args()
 root=a.root.resolve();report=root/'reports/keeper-backup-20261126';artifacts={}
 def read(name):
  path=report/name;assert path.is_file()and not path.is_symlink();raw=path.read_bytes();assert 0<len(raw)<=1024*1024
  artifacts[name]={'bytes':len(raw),'sha256':sha(raw)};return raw
 def load(name):return json.loads(read(name))
 comparison=load('verification/HOST_COMPARISON.json');difference=load('verification/HOST_DIFFERENCES.json')
 copy=load('verification/HOST_COPY_RECEIPT.json');observer=load('evidence/observer/RESULT.json')
 execution=load('evidence/observer/EXECUTION.json');raw_stdout=read('evidence/observer/RAW_STDOUT.json')
 source=read('preparation/read_observer_lifecycle.py')
 for row in copy['files']:
  raw=read(row['path']);assert row['exact_copy']is True and row['sha256']==sha(raw)and row['bytes']==len(raw)
 assert copy['original_permissions_unchanged']is True
 assert comparison['success']is False and comparison['checks']['five_existing_units_preserved']is False
 assert comparison['existing_units_checked']==5 and comparison['owned_labs_checked']==7
 assert comparison['non_ambient_difference_count']==5 and comparison['ignored_observer_invocation_count']==1
 assert comparison['network_calls']==comparison['service_actions']==0
 assert all(value is True for key,value in comparison['checks'].items()if key!='five_existing_units_preserved')
 assert difference['derived_projection']is True and difference['full_private_host_snapshot_exported']is False
 expected={(SERVICE,'ActiveState'):('activating','inactive'),(SERVICE,'SubState'):('start','dead'),
  (SERVICE,'MainPID'):('102656','0'),(SERVICE,'ControlGroup'):('/system.slice/'+SERVICE,''),
  (TIMER,'SubState'):('running','waiting')}
 actual={(row['unit'],row['property']):(row['before'],row['after'])for row in difference['differences']}
 assert len(difference['differences'])==len(actual)==5 and actual==expected
 assert difference['ignored']==[{'property':'InvocationID','unit':SERVICE}]
 assert json.loads(raw_stdout)==observer and sha(raw_stdout)==execution['stdout_sha256']
 assert execution['exit_code']==0 and execution['capture_reason']is None and execution['capture_errors']==[]
 assert execution['read_only']is True and execution['service_actions']==0 and execution['stderr_sha256']==sha(b'')
 remote=[ast.literal_eval(n.value)for n in ast.parse(source).body if isinstance(n,ast.Assign)
  and any(isinstance(t,ast.Name)and t.id=='REMOTE'for t in n.targets)]
 assert len(remote)==1 and sha(remote[0].encode())==execution['remote_source_sha256']
 assert observer['read_only']is True and observer['application_code_executed']is False
 assert observer['service_actions']==0 and observer['secrets_exported']is False and observer['message_text_exported']is False
 service=observer['properties'][SERVICE];timer=observer['properties'][TIMER]
 assert service['Type']=='oneshot'and service['Result']=='success'and service['ExecMainCode']=='1'and service['ExecMainStatus']=='0'
 assert service['ActiveState']=='inactive'and service['SubState']=='dead'and service['MainPID']=='0'
 assert timer['ActiveState']=='active'and timer['SubState']=='waiting'and timer['Triggers']==SERVICE
 events=observer['manager_events'];assert len(events)==9
 assert all(str(row['_PID'])=='1'and row['UNIT']==SERVICE and set(row)<=
  {'_PID','UNIT','MESSAGE_ID','__REALTIME_TIMESTAMP','EXIT_CODE','EXIT_STATUS'}for row in events)
 assert [row['MESSAGE_ID']for row in events]==[START,SUCCESS,STARTED]*3
 times=[int(row['__REALTIME_TIMESTAMP'])for row in events];assert times==sorted(times)
 start=micros(observer['interval_UTC'][0]+'+00:00');end=micros(observer['interval_UTC'][1]+'+00:00')
 assert all(start<=t<=end for t in times)
 before=micros(difference['before_observed_utc']);after=micros(difference['final_observed_utc'])
 assert times[0]<before<times[1]<times[2]<times[3]<times[4]<times[5]<times[6]<times[7]<times[8]<after
 classified=[]
 reasons={'ActiveState':'The baseline caught the oneshot during start; PID1 records clean completion before the final snapshot.',
  'SubState':'The service finished start-to-dead; its timer returned from running to waiting for the next activation.',
  'MainPID':'The initial observer process completed; the service no longer had a main PID.',
  'ControlGroup':'The completed observer invocation released its service cgroup.'}
 for row in difference['differences']:
  classified.append({**row,'classification':'ambient_observer_oneshot_timer_lifecycle',
   'reason':reasons[row['property']]})
 output={'schema':1,'lifecycle_reconciliation_verified':True,'original_comparison_success':False,
  'original_comparison_rewritten':False,'five_identical_service_states_claimed':False,
  'classified_differences':classified,'classified_difference_count':5,'additional_recorded_InvocationID_changes':1,
  'unexplained_differences_in_supplied_projection':0,'remaining_six_comparison_checks_true':True,
  'seven_previously_owned_labs_stopped_before_and_after':True,'manager_clean_oneshot_completions_in_window':3,
  'baseline_caught_between_start_and_first_clean_completion':True,
  'final_snapshot_after_last_clean_completion':True,'read_only_probe_bound_to_exact_source_and_capture':True,
  'systemd_message_source':{'url':'https://raw.githubusercontent.com/systemd/systemd/v255/src/systemd/sd-messages.h',
   'starting':START,'unit_success':SUCCESS,'job_started':STARTED,
   'scope':'v255 symbol meanings supplied and verified by the parent; UNIT_STARTED alone is not treated as continued activity.'},
  'artifacts':artifacts,'reviewer_source_sha256':sha(Path(__file__).read_bytes()),
  'postreview_server_or_service_actions':0,'test_bodies_run':0,'full_host_acceptance':False,'production_approved':False,
  'limitations':['Classifies the supplied five-difference projection and bound read-only captures; does not recalculate private full host snapshots.',
   'The separate InvocationID change remains recorded; its before/after values are not exported in the projection.',
   'Normal observer lifecycle evidence is not sustained operation, source adoption, off-host recovery or release approval.']}
 target=report/'verification/HOST_RECONCILIATION.json'
 with target.open('x',encoding='utf8')as f:json.dump(output,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
 print(json.dumps({'lifecycle_reconciliation_verified':True,'classified_differences':5,
  'original_comparison_success':False,'five_identical_service_states_claimed':False}))


if __name__=='__main__':main()
