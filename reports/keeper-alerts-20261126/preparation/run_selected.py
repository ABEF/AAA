"""Run only the reviewed NEW alert methods once, inside the c815 unit."""
from pathlib import Path
import contextlib,hashlib,importlib.util,json,os,signal,socket,subprocess,sys,time,unittest

ROOT=Path(__file__).resolve().parent
RUNTIME=Path('/opt/popl-keeper-alerts-20261126-c815/runtime')
SELECTED=('test_backup_rotation_and_hash_publication_preserve_pending_age_and_outbox', 'test_competing_sidecar_lock_refuses_without_mutating_state', 'test_configuration_race_preserves_outbox_and_cannot_emit_recovery', 'test_corrupt_health_is_sanitized_and_does_not_hide_backup_result', 'test_dropped_ack_is_at_least_once_with_same_event_id', 'test_dry_health_requires_explicit_alert_mode', 'test_failed_durable_publication_sends_nothing_and_keeps_original_outbox', 'test_full_publicly_generated_outbox_drains_without_pruning_or_reset', 'test_hashless_pending_and_mismatched_health_never_receive_known_hash_grace', 'test_health_and_backup_age_failures_are_independently_visible', 'test_incident_dedup_is_durable_across_repeated_one_shots', 'test_known_pending_grace_tracks_first_observation_across_restarts', 'test_pending_grace_cannot_mask_wrong_configuration_or_source', 'test_real_current_health_and_backup_validators_compose_without_side_effects', 'test_real_local_receiver_acknowledges_incident_and_later_recovery', 'test_recovery_requires_fresh_health_and_a_verified_backup', 'test_redirect_is_not_followed_and_environment_proxies_are_ignored', 'test_slow_trickle_headers_obey_absolute_delivery_budget', 'test_snapshot_adapter_has_identical_checks_without_rereading_health_file', 'test_unsafe_receiver_resource_bounds_and_input_aliases_fail_without_secret_echo', 'test_wrong_ack_keeps_event_for_identical_retry')
CLASS='KeeperAlertsTests'
TEST_FILE='tests_python/test_keeper_alerts.py'

def deny(*_,**__):raise AssertionError('Forbidden alert selection side effect')

class BoundedStream:
    def __init__(self):self.parts=[];self.size=0
    def write(self,value):
        raw=value.encode('utf8');self.size+=len(raw)
        if self.size>65536:raise ValueError('Bounded alert diagnostics exceeded')
        self.parts.append(value)
    def flush(self):pass

class TrackedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.started=[];self.outcomes={}
    def startTest(self,test):
        name=test.id().rsplit('.',1)[-1]
        if name not in SELECTED or name in self.started:raise AssertionError('Unreviewed or repeated alert method')
        self.started.append(name);super().startTest(test)
    def addSuccess(self,test):self.outcomes[test.id().rsplit('.',1)[-1]]='passed';super().addSuccess(test)
    def addError(self,test,err):self.outcomes[test.id().rsplit('.',1)[-1]]='error';super().addError(test,err)
    def addFailure(self,test,err):self.outcomes[test.id().rsplit('.',1)[-1]]='failed';super().addFailure(test,err)
    def addSkip(self,test,reason):self.outcomes[test.id().rsplit('.',1)[-1]]='skipped';super().addSkip(test,reason)

def timeout(*_):raise TimeoutError('Isolated alert method deadline')

def main():
    assert os.name=='posix'and os.getuid()==os.getgid()==65534 and set(os.getgroups())<={65534}
    assert os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE']
    assert os.environ['TMPDIR']==str(RUNTIME/'tmp')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
    signal.signal(signal.SIGALRM,timeout);signal.alarm(175)
    original_connect=socket.socket.connect;original_create=socket.create_connection;original_bind=socket.socket.bind
    def local_address(value):
        if not(isinstance(value,tuple)and len(value)==2 and value[0]=='127.0.0.1'and type(value[1])is int and 0<=value[1]<=65535):deny()
    def connect(sock,address):local_address(address);return original_connect(sock,address)
    def create(address,*args,**kwargs):local_address(address);return original_create(address,*args,**kwargs)
    def bind(sock,address):local_address(address);return original_bind(sock,address)
    socket.socket.connect=connect;socket.create_connection=create;socket.socket.bind=bind
    subprocess.Popen=deny;os.system=deny
    spec=importlib.util.spec_from_file_location('new_keeper_alert_selection',ROOT/TEST_FILE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    import keeper.monitor
    keeper.monitor.Keeper.__init__=deny
    cls=getattr(module,CLASS);suite=unittest.TestSuite(cls(name)for name in SELECTED)
    stream=BoundedStream();started=time.monotonic()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=TrackedResult).run(suite)
    failures={case.id().rsplit('.',1)[-1]:hashlib.sha256(detail.encode()).hexdigest()for case,detail in result.errors+result.failures}
    success=(result.wasSuccessful()and result.testsRun==len(SELECTED)and not result.skipped
        and result.started==list(SELECTED)and all(result.outcomes.get(n)=='passed'for n in SELECTED))
    value={'schema':1,'success':success,'selected_methods':list(SELECTED),'tests_run':result.testsRun,
        'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped),
        'method_outcomes':{n:result.outcomes.get(n,'not_run')for n in SELECTED},
        'diagnostic_sha256':hashlib.sha256(''.join(stream.parts).encode()).hexdigest(),'diagnostic_bytes':stream.size,
        'error_digests_only':failures,'elapsed_seconds':time.monotonic()-started,'uid':os.getuid(),'gid':os.getgid(),
        'supplementary_groups':os.getgroups(),'network_namespace_is_private':True,'loopback_only_guards':True,
        'Popen_and_Keeper_construction_denied':True,'old_test_bodies_run':0,'previously_green_methods_run':0,
        'signing_attempts':0,'public_network_used':False,'production_approved':False}
    fd=os.open(RUNTIME/'RESULT.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w',encoding='utf8')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    signal.alarm(0)
    print(json.dumps({'new_alert_methods':len(SELECTED),'success':success,'errors_or_failures':len(failures)}))
    return 0 if success else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'new_alert_selection_refused':True,'error_type':type(exc).__name__}),file=sys.stderr)
        raise SystemExit(1)from None
