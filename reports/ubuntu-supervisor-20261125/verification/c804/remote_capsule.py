"""Fixed-path isolated lab control. No installed service or credential mutations."""
from pathlib import Path,PurePosixPath
import argparse,base64,hashlib,io,json,os,re,shutil,stat,subprocess,tarfile,time

LAB=Path('/opt/popl-ubuntu-supervisor-20261125-c804')
UNIT='popl-ubuntu-supervisor-20261125-c804-model.service'
UPLOAD=Path('/tmp/popl-ubuntu-supervisor-20261125-c804.inputs.tar.gz')
MAX_ARCHIVE=96*1024*1024
MAX_UNPACKED=256*1024*1024
MAX_MEMBERS=2048
BUNDLE_SHA='ec23d1fff6f17bb3e3f29446e81223763a1ff1134737107e743cbe3c902e710e'
MANIFEST_SHA='2f43ef13cc3679b8fdc26546234618bc381205416a93db3f3c0a2f13a415f0dd'
SOURCE_MANIFEST_SHA='4a1812fc018799f0d71d20f681ad73cecc593e69fe6b25736dd1c759923f060a'
WORKER_SHA='9054e71cd737a95185dc9228d7ccfac114b8bb227df0baddab1953f2fef23bda'
UTILITY_SHA='363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4'
INDEXER_SHA='7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'
ANVIL='/opt/popl-history-export-20261124-c7eb/tools/anvil'
ANVIL_SHA='05ee0cf1758024ea5e23dae562d92955ace205ab299091a43d2fa5bdeb6933bd'
CAST='/opt/popl-ubuntu-20261121-8a629f43/bin/cast'
CAST_SHA='d55f540256f0dd8b940a125d435919948a5e8c140262e9923067cbfa95ef2970'
ORIGINAL=Path('/opt/popl-ubuntu-20261121-8a629f43')
ORIGINAL_BUNDLE_SHA='08ad9a5d069c502536526d444aa8f1fd296c13f15db46160c150d27e61c7b266'
ORIGINAL_MANIFEST_SHA='8da3fe0b06f4010be3030292a4ed7dadcb36978d4029f418f0c791461d4ffc58'
COPIED_INPUTS={'restore-state.json': (13643211, '42ab11fd14bd02868359fb3fdd84e961f3f8050245f0cb370d1962be823d9b9a'), 'instances.json': (4845414, 'e94a9dc5d4f3f04211ad77e62612b2284301584c3e363203198311d34d128e56'), 'entry-receipts.json': (696971, '425902fae92cdbb210f3a12afc80908b9bd186ec1ae80060c427d9f302f3c519')}
ALLOWED=('MANIFEST.json', 'inputs/SOURCE_MANIFEST.json', 'inputs/TRADER.json', 'inputs/bindings.json', 'source/contracts/frontend_api/__init__.py', 'source/contracts/frontend_api/activation.py', 'source/contracts/frontend_api/activation_config.py', 'source/contracts/frontend_api/activation_server.py', 'source/contracts/frontend_api/activation_trace.py', 'source/contracts/frontend_api/activation_v4.py', 'source/contracts/frontend_api/admission.py', 'source/contracts/frontend_api/canonical_cache.py', 'source/contracts/frontend_api/claim_planner.py', 'source/contracts/frontend_api/collection.py', 'source/contracts/frontend_api/custody.py', 'source/contracts/frontend_api/earnings.py', 'source/contracts/frontend_api/earnings_checkpoint.py', 'source/contracts/frontend_api/earnings_checkpoint_build.py', 'source/contracts/frontend_api/earnings_checkpoint_import.py', 'source/contracts/frontend_api/earnings_checkpoint_v2.py', 'source/contracts/frontend_api/earnings_checkpoint_v3.py', 'source/contracts/frontend_api/earnings_exact_lp.py', 'source/contracts/frontend_api/earnings_prices.py', 'source/contracts/frontend_api/earnings_replay.py', 'source/contracts/frontend_api/history.py', 'source/contracts/frontend_api/history_audit.py', 'source/contracts/frontend_api/history_recovery.py', 'source/contracts/frontend_api/http_runtime.py', 'source/contracts/frontend_api/lifecycle.py', 'source/contracts/frontend_api/lineage.py', 'source/contracts/frontend_api/liquidity_context.py', 'source/contracts/frontend_api/mint_readiness.py', 'source/contracts/frontend_api/portfolio.py', 'source/contracts/frontend_api/portfolio_v5.py', 'source/contracts/frontend_api/portfolio_v6.py', 'source/contracts/frontend_api/portfolio_v7.py', 'source/contracts/frontend_api/principal_return.py', 'source/contracts/frontend_api/royalty_reporting.py', 'source/contracts/frontend_api/server.py', 'source/contracts/frontend_api/service.py', 'source/contracts/frontend_api/transaction_gas.py', 'source/contracts/frontend_api/transactions.py', 'source/contracts/frontend_api/wallet_earnings.py', 'source/contracts/frontend_api/wallet_view.py', 'source/contracts/frontend_api/worker.py', 'source/contracts/indexer/__init__.py', 'source/contracts/indexer/event_schema.json', 'source/contracts/indexer/events.py', 'source/contracts/indexer/historical_event_schema.json', 'source/contracts/indexer/monitor.py', 'source/contracts/keeper/__init__.py', 'source/contracts/keeper/cast_process.py', 'source/contracts/keeper/compound_policy.py', 'source/contracts/keeper/health.py', 'source/contracts/keeper/monitor.py', 'source/contracts/keeper/operation_review.py', 'source/contracts/keeper/ops.py', 'source/contracts/keeper/principal.py', 'source/contracts/keeper/probe.py', 'source/contracts/keeper/rebalance_confirmation.py', 'source/contracts/keeper/royalties.py', 'source/contracts/keeper/staging-install.sh', 'source/contracts/keeper/staging-monitor-install.sh', 'source/contracts/keeper/staging.py', 'source/contracts/keeper/staging_observer.py', 'source/contracts/keeper/watchdog.py', 'source/contracts/keeper/zzz-keeper.service', 'source/contracts/scripts/build-earnings-checkpoint.py', 'source/contracts/scripts/build-workload-inventory.py', 'source/contracts/scripts/check-focused-evidence.py', 'source/contracts/scripts/check-local-deployment-evidence.py', 'source/contracts/scripts/check-market-evidence.py', 'source/contracts/scripts/check-python-publication.py', 'source/contracts/scripts/check-slither-review.py', 'source/contracts/scripts/check-source9-rehearsal-evidence.py', 'source/contracts/scripts/check-staging-monitor.py', 'source/contracts/scripts/generate-artwork-library.py', 'source/contracts/scripts/generate-dynamic-range-vectors.py', 'source/contracts/scripts/generate-function-reference.py', 'source/contracts/scripts/generate-operator-reference.py', 'source/contracts/scripts/generate_event_schema.py', 'source/contracts/scripts/history-recovery.py', 'source/contracts/scripts/import-earnings-checkpoint.py', 'source/contracts/scripts/install-deps.sh', 'source/contracts/scripts/inventory-nft-holders.py', 'source/contracts/scripts/local-api-stack.py', 'source/contracts/scripts/local-stack.py', 'source/contracts/scripts/local_browser.py', 'source/contracts/scripts/local_clock.py', 'source/contracts/scripts/local_fixture_profile.py', 'source/contracts/scripts/local_inputs.py', 'source/contracts/scripts/local_wallet.py', 'source/contracts/scripts/observe-production-config.py', 'source/contracts/scripts/prepare-deployment-sequence.py', 'source/contracts/scripts/prepare-deployment.py', 'source/contracts/scripts/prepare-dollar-rehearsal.py', 'source/contracts/scripts/prepare-manual-lp.py', 'source/contracts/scripts/prepare-opensea-drop.py', 'source/contracts/scripts/prepare-operator-management.py', 'source/contracts/scripts/prepare-operator-review.py', 'source/contracts/scripts/prepare-preseal.py', 'source/contracts/scripts/prepare-release-review.py', 'source/contracts/scripts/prepare_ipfs_bundle.py', 'source/contracts/scripts/rehearse-api-ingress.py', 'source/contracts/scripts/rehearse-keeper.py', 'source/contracts/scripts/rehearse-local-deployment.py', 'source/contracts/scripts/rehearse-manual-recovery.py', 'source/contracts/scripts/rehearse-manual-reference.py', 'source/contracts/scripts/run-current-pool-fork.py', 'source/contracts/scripts/run-fork-checks.py', 'source/contracts/scripts/run-keeper-tests.py', 'source/contracts/scripts/run_python_tests.py', 'source/contracts/scripts/source9_rehearsal_api.py', 'source/contracts/scripts/source9_rehearsal_deploy.py', 'source/contracts/scripts/source9_rehearsal_fork.py', 'source/contracts/scripts/source9_rehearsal_state.py', 'source/contracts/scripts/source_checks.py', 'source/contracts/scripts/sync-project-todo.py', 'source/contracts/scripts/validate-production-config.py', 'source/contracts/scripts/verify-hookless-pool.py', 'source/contracts/scripts/verify-local-stack.py', 'source/contracts/scripts/verify-local-website.py', 'source/contracts/scripts/verify-normal-profile.py', 'source/contracts/scripts/verify-slither.sh', 'source/contracts/scripts/verify.sh', 'source/contracts/zzz_ops/__init__.py', 'source/contracts/zzz_ops/abi.py', 'source/contracts/zzz_ops/deployment_plan.py', 'source/contracts/zzz_ops/deployment_sequence.py', 'source/contracts/zzz_ops/errors.py', 'source/contracts/zzz_ops/ethereum_fees.py', 'source/contracts/zzz_ops/evidence.py', 'source/contracts/zzz_ops/exact_lp.py', 'source/contracts/zzz_ops/execution_price.py', 'source/contracts/zzz_ops/factory_code_v2.py', 'source/contracts/zzz_ops/factory_code_v3.py', 'source/contracts/zzz_ops/factory_code_v4.py', 'source/contracts/zzz_ops/factory_code_v5.py', 'source/contracts/zzz_ops/factory_code_v6.py', 'source/contracts/zzz_ops/focused_evidence.py', 'source/contracts/zzz_ops/function_reference.py', 'source/contracts/zzz_ops/historical_production.py', 'source/contracts/zzz_ops/holder_preflight.py', 'source/contracts/zzz_ops/log_provenance.py', 'source/contracts/zzz_ops/lp_execution.py', 'source/contracts/zzz_ops/management_base.py', 'source/contracts/zzz_ops/management_custody.py', 'source/contracts/zzz_ops/management_exit.py', 'source/contracts/zzz_ops/management_review.py', 'source/contracts/zzz_ops/manual_lp_review.py', 'source/contracts/zzz_ops/market_evidence.py', 'source/contracts/zzz_ops/mint_policy_v2.py', 'source/contracts/zzz_ops/opensea_drop.py', 'source/contracts/zzz_ops/operator_reference.py', 'source/contracts/zzz_ops/operator_review.py', 'source/contracts/zzz_ops/physical_portfolio.py', 'source/contracts/zzz_ops/position.py', 'source/contracts/zzz_ops/preseal_plan.py', 'source/contracts/zzz_ops/price_policy.py', 'source/contracts/zzz_ops/production_observer.py', 'source/contracts/zzz_ops/production_observer_v10.py', 'source/contracts/zzz_ops/production_observer_v11.py', 'source/contracts/zzz_ops/production_observer_v12.py', 'source/contracts/zzz_ops/production_observer_v13.py', 'source/contracts/zzz_ops/production_observer_v14.py', 'source/contracts/zzz_ops/production_observer_v15.py', 'source/contracts/zzz_ops/production_observer_v4.py', 'source/contracts/zzz_ops/production_observer_v5.py', 'source/contracts/zzz_ops/production_observer_v6.py', 'source/contracts/zzz_ops/production_observer_v7.py', 'source/contracts/zzz_ops/production_observer_v8.py', 'source/contracts/zzz_ops/production_observer_v9.py', 'source/contracts/zzz_ops/production_v10.py', 'source/contracts/zzz_ops/production_v11.py', 'source/contracts/zzz_ops/production_v12.py', 'source/contracts/zzz_ops/production_v13.py', 'source/contracts/zzz_ops/production_v14.py', 'source/contracts/zzz_ops/production_v15.py', 'source/contracts/zzz_ops/production_v2.py', 'source/contracts/zzz_ops/production_v4.py', 'source/contracts/zzz_ops/production_v5.py', 'source/contracts/zzz_ops/production_v6.py', 'source/contracts/zzz_ops/production_v7.py', 'source/contracts/zzz_ops/production_v8.py', 'source/contracts/zzz_ops/production_v9.py', 'source/contracts/zzz_ops/protocol_policy.py', 'source/contracts/zzz_ops/range_policy.py', 'source/contracts/zzz_ops/rebalance_confirmation.py', 'source/contracts/zzz_ops/review_bundle.py', 'source/contracts/zzz_ops/royalty_read_policy.py', 'source/contracts/zzz_ops/rpc.py', 'source/contracts/zzz_ops/state.py', 'source/contracts/zzz_ops/tick_math.py', 'source/contracts/zzz_ops/work_budget.py', 'source/helpers/job_cases.py', 'source/helpers/keeper_jobs.py', 'source/helpers/keeper_runtime.py', 'source/helpers/model_service.py', 'source/helpers/native_control.py')
PUBLIC_PATHS={'model-READY.json': ('model', 'model/READY.json'), 'model-COMPLETE.json': ('model', 'model/COMPLETE.json'), 'model-RESULT.json': ('model', 'model/RESULT.json'), 'model-EVENTS.json': ('model', 'model/EVENTS.json'), 'case-BINDINGS.json': ('model', 'model/supervisor/BINDINGS.json'), 'case-BINDING_REFUSAL.json': ('model', 'model/supervisor/BINDING_REFUSAL.json'), 'case-CLOCK_REPAIR.json': ('model', 'model/supervisor/CLOCK_REPAIR.json'), 'case-INITIAL_JOURNAL.json': ('model', 'model/supervisor/INITIAL_JOURNAL.json'), 'case-FINANCIAL_BEFORE.json': ('model', 'model/supervisor/FINANCIAL_BEFORE.json'), 'case-DURABLE_PENDING.json': ('model', 'model/supervisor/DURABLE_PENDING.json'), 'case-FAULT_TRIGGER.json': ('model', 'model/supervisor/FAULT_TRIGGER.json'), 'case-FAULT_CLOSED.json': ('model', 'model/supervisor/FAULT_CLOSED.json'), 'case-RECOVERED_JOURNAL.json': ('model', 'model/supervisor/RECOVERED_JOURNAL.json'), 'case-HEALTHY_NORMAL_CYCLE.json': ('model', 'model/supervisor/HEALTHY_NORMAL_CYCLE.json'), 'case-FINANCIAL_AFTER.json': ('model', 'model/supervisor/FINANCIAL_AFTER.json'), 'case-FRONTEND_REFUSAL.json': ('model', 'model/supervisor/FRONTEND_REFUSAL.json'), 'case-SETUP.json': ('model', 'model/supervisor/SETUP.json'), 'case-RECEIPTS.json': ('model', 'model/supervisor/RECEIPTS.json'), 'case-RAW_REVIEWS.json': ('model', 'model/supervisor/RAW_REVIEWS.json'), 'case-RESULT.json': ('model', 'model/supervisor/RESULT.json'), 'native-BASELINE.json': ('control', 'BASELINE.json'), 'native-WITNESS_STATE.json': ('control', 'WITNESS_STATE.json'), 'native-NATIVE_RESTART_PROOF.json': ('control', 'NATIVE_RESTART_PROOF.json'), 'native-JOURNAL_DURING_RESTART.json': ('control', 'JOURNAL_DURING_RESTART.json'), 'native-model.stdout.log': ('model', 'native-model.stdout.log'), 'native-model.stderr.log': ('model', 'native-model.stderr.log'), 'native-keeper.stdout.log': ('model', 'native-keeper.stdout.log'), 'native-keeper.stderr.log': ('model', 'native-keeper.stderr.log')}
PUBLIC=tuple(PUBLIC_PATHS)

class ControlRefusal(ValueError):pass

def require(value,message):
    if not value:raise ControlRefusal(message)

def sha(data):return hashlib.sha256(data).hexdigest()

def run(argv,timeout=12):
    result=subprocess.run(argv,capture_output=True,timeout=timeout)
    require(len(result.stdout)+len(result.stderr)<=256*1024,'Control output exceeds bound')
    return result

def properties():
    p=run(['systemctl','show',UNIT,'--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainStatus,PrivateNetwork,User,Group,NoNewPrivileges,ProtectSystem,ProtectHome,PrivateDevices,KillMode,RuntimeMaxUSec,TimeoutStopUSec,MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,CPUWeight,IOWeight,Nice','--no-pager'])
    values={}
    for line in p.stdout.decode('utf-8','strict').splitlines():
        if '='in line:
            key,value=line.split('=',1);values[key]=value
    return values

def secure_file(path,owner=0,maximum=MAX_ARCHIVE):
    st=path.lstat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid==owner and st.st_nlink==1,'Unexpected file identity')
    require(not st.st_mode&0o022 and 0<=st.st_size<=maximum,'Unsafe file mode or size')
    return st

def ownership():
    require(os.geteuid()==0,'Root control required')
    st=LAB.lstat();require(stat.S_ISDIR(st.st_mode) and st.st_uid==0 and not st.st_mode&0o022,'Unowned lab')
    secure_file(LAB/'LAB_ID.json',maximum=4096)
    record=json.loads((LAB/'LAB_ID.json').read_bytes())
    require(record.get('lab')==str(LAB) and record.get('unit')==UNIT,'Lab marker mismatch')
    return record

def member_maximum(name):
    return 32*1024*1024

def manifest_entries(raw):
    require(0<len(raw)<=MAX_ARCHIVE and sha(raw)==BUNDLE_SHA,'Only reviewed c7f0 source bundle is admitted')
    data={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz')as archive:
        for member in archive:
            require(len(data)<MAX_MEMBERS,'Source member count exceeds bound')
            path=PurePosixPath(member.name)
            require(member.isfile()and not path.is_absolute()and '..'not in path.parts and '\\'not in member.name and member.name==str(path),'Unsafe source member')
            require(member.name not in data and member.name in ALLOWED,'Unreviewed source member')
            maximum=member_maximum(member.name);require(0<=member.size<=maximum,'Member size exceeds bound')
            total+=member.size;require(total<=MAX_UNPACKED,'Unpacked bound exceeded')
            value=archive.extractfile(member).read(maximum+1);require(len(value)==member.size,'Member length differs');data[member.name]=value
    require(set(data)==set(ALLOWED)and sha(data['MANIFEST.json'])==MANIFEST_SHA,'Bundle inventory or manifest differs')
    manifest=json.loads(data['MANIFEST.json'])
    require(manifest['schema']==1 and manifest['source_stage']=='source_base_plus_overrides'and manifest['no_signer_or_credentials']is True and manifest['public_RPC']is False and manifest['sealing_forbidden']is True and manifest['preexisting_sealed_state_only']is True and manifest['new_disposable_local_signing']is True,'Reviewed permissions differ')
    require(type(manifest['members'])is dict and set(data)==set(manifest['members'])|{'MANIFEST.json'},'Source member inventory differs')
    for name,pin in manifest['members'].items():
        require(type(pin)is dict and set(pin)=={'bytes','sha256'}and type(pin['bytes'])is int and len(data[name])==pin['bytes']and sha(data[name])==pin['sha256'],'Source member pin differs')
    require(sha(data['inputs/SOURCE_MANIFEST.json'])==SOURCE_MANIFEST_SHA,'Reviewed source identity differs')
    for name,digest in (('keeper_runtime.py', 'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4'), ('keeper_jobs.py', '363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4'), ('job_cases.py', '7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'), ('model_service.py', '9054e71cd737a95185dc9228d7ccfac114b8bb227df0baddab1953f2fef23bda'), ('native_control.py', 'cdc34179f146fedd19d13e3e7fdcbbe1efce9719d800c63148e6971d1069d18f')):require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')
    return manifest,data


def checked_read(path,maximum,*,owners=(0,),expected=None):
    opened=[]
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
        for part in path.parts[1:-1]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd)
            st=os.fstat(fd);require(stat.S_ISDIR(st.st_mode)and st.st_uid in owners and not st.st_mode&0o022,'Unsafe directory identity')
        parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd);before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode)and before.st_uid in owners and before.st_nlink==1 and not before.st_mode&0o022 and before.st_size<=maximum,'Unsafe file identity or bound')
        parts=[];size=0
        while True:
            raw=os.read(fd,min(65536,maximum+1-size))
            if not raw:break
            size+=len(raw);require(size<=maximum,'Read bound exceeded');parts.append(raw)
        after=os.fstat(fd);current=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
        key=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns)
        data=b''.join(parts);require(key(before)==key(after)==key(current)and size==before.st_size,'File changed during read')
        if expected is not None:require(sha(data)==expected,'Fixed public input pin differs')
        return data
    finally:
        for fd in reversed(opened):os.close(fd)


def original_inputs():
    marker=json.loads(checked_read(ORIGINAL/'lab.json',16384,owners=(0,65534)))
    require(marker.get('schema')==1 and marker.get('bundle_sha256')==ORIGINAL_BUNDLE_SHA,'Original lab identity differs')
    checked_read(ORIGINAL/'INPUT_MANIFEST.json',2*1024*1024,expected=ORIGINAL_MANIFEST_SHA)
    result={}
    for name,(size,digest)in COPIED_INPUTS.items():
        value=checked_read(ORIGINAL/'public'/name,size,expected=digest);require(len(value)==size,'Original public input size differs');result[name]=value
    return result


def install(a):
    import pwd
    require(os.geteuid()==0 and not os.path.lexists(LAB),'New lab must not exist')
    require(properties().get('LoadState')=='not-found','Owned unit name already exists')
    secure_file(UPLOAD);raw=UPLOAD.read_bytes();require(sha(raw)==a.bundle_sha256,'Uploaded archive pin differs')
    manifest,data=manifest_entries(raw)
    user=pwd.getpwnam('nobody');require((user.pw_uid,user.pw_gid)==(65534,65534),'Unexpected unprivileged identity')
    copied_inputs=original_inputs()
    tools=[('anvil',ANVIL,ANVIL_SHA),('cast',CAST,CAST_SHA)]
    for name,path,digest in tools:
        checked_read(Path(path),128*1024*1024,expected=digest)
    # No extractall, links, replacement or broad filesystem command is used.
    LAB.mkdir(mode=0o755)
    for name,value in {**data,**{'inputs/'+name:raw for name,raw in copied_inputs.items()}}.items():
        path=LAB/name;path.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o444)
        with os.fdopen(descriptor,'wb')as stream:stream.write(value);stream.flush();os.fsync(stream.fileno())
        os.chmod(path,0o444)
    (LAB/'tools').mkdir(mode=0o755)
    copied={}
    for name,path,digest in tools:
        target=LAB/'tools'/name
        with target.open('xb')as stream:stream.write(checked_read(Path(path),128*1024*1024,expected=digest))
        os.chmod(target,0o555);require(sha(target.read_bytes())==digest,'Copied tool changed')
        copied[name]={'path':str(target),'sha256':digest}
    runtime=LAB/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,65534,65534)
    for base in ('source','inputs','tools'):
        target=LAB/base
        if target.exists():
            for path in sorted((p for p in target.rglob('*')if p.is_dir()),key=lambda p:len(p.parts),reverse=True):os.chmod(path,0o555)
            os.chmod(target,0o555)
    record={'schema':1,'lab':str(LAB),'unit':UNIT,'bundle_sha256':a.bundle_sha256,'controller_sha256':a.controller_sha256,'source_manifest_sha256':sha(data['MANIFEST.json']),'members':len(manifest['members']),'tools':copied,'source_readonly':True,'uid':65534,'source_stage':'source_base_plus_overrides','copied_inputs':{name:{'bytes':len(raw),'sha256':sha(raw)}for name,raw in copied_inputs.items()},'controlled_copied_state_only':True,'new_sealing':False,'source_identity_manifest_sha256':SOURCE_MANIFEST_SHA}
    with (LAB/'LAB_ID.json').open('x',encoding='utf-8')as stream:json.dump(record,stream,sort_keys=True)
    os.chmod(LAB/'LAB_ID.json',0o444)
    return {'phase':'installed',**record,'existing_services_changed':False,'upload_retained':True}

def runtime(a):
    require(a.attempt==1,'Only reviewed run-001 is admitted')
    return LAB/'runtime'/('run-%03d'%a.attempt)

def start(a):
    record=ownership();require(record['controller_sha256']==a.controller_sha256,'Controller source changed')
    require(properties().get('ActiveState')not in ('active','activating','deactivating'),'Owned unit is running')
    require(sha((LAB/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'Installed manifest differs')
    manifest=json.loads((LAB/'MANIFEST.json').read_bytes())
    for name,pin in manifest['members'].items():
        path=LAB/name;identity=secure_file(path,maximum=member_maximum(name));require(identity.st_size==pin['bytes']and sha(path.read_bytes())==pin['sha256'],'Installed member changed')

    target=runtime(a);require(not os.path.lexists(target),'Attempt runtime already exists')
    target.mkdir(mode=0o700);os.chown(target,65534,65534)
    (target/'tmp').mkdir(mode=0o700);os.chown(target/'tmp',65534,65534)
    for name in ('controller.stdout.log','controller.stderr.log'):
        path=target/name;path.touch(mode=0o600,exist_ok=False);os.chown(path,65534,65534)
    policy={'User':'nobody','Group':'nogroup','NoNewPrivileges':'yes','PrivateNetwork':'yes','PrivateDevices':'yes','ProtectSystem':'strict','ProtectHome':'yes','ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectControlGroups':'yes','RestrictSUIDSGID':'yes','LockPersonality':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'','RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6','ReadWritePaths':str(LAB/'runtime'),'InaccessiblePaths':'/tmp /var/tmp','UMask':'0077','KillMode':'control-group','SendSIGKILL':'yes','LimitCORE':'0','RuntimeMaxSec':'900','TimeoutStopSec':'5','MemoryMax':'2G','MemorySwapMax':'0','TasksMax':'128','CPUQuota':'150%','CPUWeight':'10','IOWeight':'10','Nice':'10','WorkingDirectory':str(target),'StandardOutput':'append:'+str(target/'controller.stdout.log'),'StandardError':'append:'+str(target/'controller.stderr.log')}
    command=['systemd-run','--unit='+UNIT,'--collect','--quiet']
    for key,value in policy.items():command+=['--property='+key+'='+value]
    env={'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONPATH':str(LAB/'source/helpers'), 'POPL_LAB_HOST_NETWORK_NAMESPACE':os.readlink('/proc/self/ns/net'),'TMPDIR':str(target/'tmp'),'POPL_LAB_ROOT':str(LAB),'POPL_LAB_SOURCE':str(LAB/'source/contracts'),'POPL_LAB_INPUTS':str(LAB/'inputs'),'POPL_LAB_RUNTIME':str(target)}
    for key,value in env.items():command+=['--setenv='+key+'='+value]
    for name,digest in [('anvil',ANVIL_SHA),('cast',CAST_SHA)]:checked_read(LAB/'tools'/name,128*1024*1024,expected=digest)
    for name,(size,digest)in COPIED_INPUTS.items():require(len(checked_read(LAB/'inputs'/name,size,expected=digest))==size,'Copied input size differs')
    command+=['/usr/bin/python3','-B',str(LAB/'source/helpers/run_jobs.py'),'--source-manifest-sha256',SOURCE_MANIFEST_SHA,'--base-sha256','f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4','--trader-sha256','262c96c16ba47710e6baa49ec5e43b78f2cf69519e7c70b6c6cf638cafe861aa']
    result=run(command,timeout=20);require(result.returncode==0,'Owned transient unit did not start')
    return {'phase':'started','attempt':a.attempt,'unit':UNIT,'runtime':str(target),'policy_requested':policy,'properties':properties(),'existing_services_changed':False,'host_network_namespace':os.readlink('/proc/self/ns/net'),'controlled_copied_state_only':True,'new_sealing':False,'source_stage':record['source_stage']}

def status(a):
    record=ownership();require(record['controller_sha256']==a.controller_sha256,'Controller source changed')
    values=properties();pid=int(values.get('MainPID','0'));namespace={}
    if pid:
        for name,path in [('host','/proc/self/ns/net'),('owned','/proc/%d/ns/net'%pid)]:
            try:namespace[name]=os.readlink(path)
            except FileNotFoundError:namespace[name]=None
    group=values.get('ControlGroup','');pids=[]
    if group:
        require(group=='/system.slice/'+UNIT,'Unexpected owned cgroup')
        try:pids=[int(v)for v in (Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs').read_text().splitlines()]
        except FileNotFoundError:pass
        require(len(pids)<=128,'Owned PID bound exceeded')
    files={};target=runtime(a)
    for name,relative in PUBLIC_PATHS.items():
        if relative is None:continue
        path=target/relative
        if path.exists():
            st=secure_file(path,owner=65534,maximum=2*1024*1024)
            files[name]={'bytes':st.st_size,'uid':st.st_uid,'mode':oct(st.st_mode&0o777)}
    return {'phase':'status','attempt':a.attempt,'unit':UNIT,'properties':values,'network_namespace':namespace,'owned_cgroup_pids':pids,'public_files':files}

def stop(a):
    ownership();before=status(a)
    if before['properties'].get('LoadState')!='not-found':
        result=run(['systemctl','stop',UNIT],timeout=15);require(result.returncode==0,'Owned unit stop failed')
    after=status(a)
    require(after['properties'].get('ActiveState')in ('inactive','failed')and int(after['properties'].get('MainPID','0'))==0 and not after['owned_cgroup_pids'],'Owned process cleanup incomplete')
    return {'phase':'stopped','before':before,'after':after,'only_owned_unit_stopped':True,'lab_and_artifacts_retained':True}

def fetch(a):
    ownership();require(a.artifact in PUBLIC,'Unapproved artifact name')
    relative=PUBLIC_PATHS[a.artifact]
    if relative is not None:
        require('secrets'not in PurePosixPath(relative).parts,'Private subtree is never exportable')
        data=checked_read(runtime(a)/relative,2*1024*1024,owners=(0,65534))
        require((runtime(a)/relative).lstat().st_uid==65534,'Artifact writer differs')
    else:
        path=runtime(a)/'jobs/RESULT.json';original=None;result=None
        if path.exists():original=checked_read(path,2*1024*1024,owners=(0,65534));result=json.loads(original)
        values=properties();shared={'schema':1,'derived_only':True,'source_result_sha256':None if original is None else sha(original),'unit_properties':values,'production_approved':False,'public_signing':False,'new_sealing':False,'source_stage':'source_base_plus_overrides'}
        if a.artifact=='SUMMARY.json':
            shared.update(result_available=result is not None)
            if result is not None:shared.update({key:result.get(key)for key in ('success','scope','features','shared_RPC_requests','raw_submission_attempts','tracked_children_stopped','secret_disposition','all_enabled_jobs_qualified','unexecuted')})
        elif a.artifact=='CLEANUP.json':
            shared.update(result_available=result is not None,helper_cleanup=None if result is None else result.get('cleanup'),helper_tracked_children_stopped=None if result is None else result.get('tracked_children_stopped'))
            shared['owned_control_readback']=status(a)
        else:
            shared.update(result_available=result is not None,failed=None if result is None else result.get('success')is not True)
            if result is not None:shared.update({key:result.get(key)for key in ('failure_stage','error_class','fixed_guard','last_model_RPC_failure','gateway_refusals','raw_submission_attempts')})
            elif values.get('ActiveState')not in ('active','activating'):shared.update(failed=True,reason='owned_helper_exited_without_result')
        data=json.dumps(shared,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(data)<=2*1024*1024,'Derived artifact exceeds bound')
    return {'phase':'public_artifact','attempt':a.attempt,'artifact':a.artifact,'bytes':len(data),'sha256':sha(data),'base64':base64.b64encode(data).decode('ascii'),'private_material_exported':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('install','start','startkeeper','baseline','observe','status','stop','fetch'));parser.add_argument('--controller-sha256',required=True);parser.add_argument('--bundle-sha256');parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--artifact');a=parser.parse_args()
    globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    try:
        require(re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None,'Invalid controller pin')
        if a.action=='install':require(re.fullmatch('[0-9a-f]{64}',a.bundle_sha256 or'')is not None,'Invalid bundle pin')
        result=globals()[a.action](a)
    except BaseException as exc:
        # All require() messages are reviewed fixed literals; never emit arbitrary exception text.
        site={'function':None,'line':None};trace=exc.__traceback__
        while trace is not None:
            frame=trace.tb_frame;name=frame.f_code.co_name
            if frame.f_code.co_filename==__file__ and name!='require' and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}',name)and 0<trace.tb_lineno<10000:site={'function':name,'line':trace.tb_lineno}
            trace=trace.tb_next
        kind=type(exc).__name__;kind=kind if kind in {'ControlRefusal','FileNotFoundError','PermissionError','OSError','ValueError','JSONDecodeError','TimeoutExpired','SystemExit','KeyboardInterrupt'}else'Other'
        guard=str(exc)if type(exc)is ControlRefusal else None
        if guard is not None and(len(guard)>160 or any(ord(x)<32 or ord(x)>126 for x in guard)):guard=None
        print(json.dumps({'phase':a.action,'failed':True,'reason':'bounded_owned_lab_control_failed','error_type':kind,'fixed_guard':guard,'site':site,'lab':str(LAB),'unit':UNIT}));raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))
"""Appended to the fixed reviewed installer/controller; never standalone."""
import importlib.util
import sys
import time
sys.dont_write_bytecode=True
CONTROL=LAB/'control'
NATIVE_PINS={'source_manifest_sha256': '4a1812fc018799f0d71d20f681ad73cecc593e69fe6b25736dd1c759923f060a', 'base_sha256': 'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4', 'jobs_sha256': '363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4', 'cases_sha256': '7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7', 'model_sha256': '9054e71cd737a95185dc9228d7ccfac114b8bb227df0baddab1953f2fef23bda'}
NATIVE_SHA='cdc34179f146fedd19d13e3e7fdcbbe1efce9719d800c63148e6971d1069d18f'

def native():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    path=LAB/'source/helpers/native_control.py';checked_read(path,2*1024*1024,expected=NATIVE_SHA)
    spec=importlib.util.spec_from_file_location('fixed_native',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def record_control(name,value):
    require(name in {'BASELINE.json','WITNESS_STATE.json','NATIVE_RESTART_PROOF.json','JOURNAL_DURING_RESTART.json','SIGNER_KILL.json'},'Closed native record name')
    if not CONTROL.exists():CONTROL.mkdir(mode=0o700)
    st=CONTROL.lstat();require(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o700,'Native control directory differs')
    raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(raw)<=2*1024*1024,'Native record exceeds bound')
    target=CONTROL/name;temporary=CONTROL/(name+'.tmp')
    if target.exists():secure_file(target,maximum=2*1024*1024)
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,target)

def control_json(name):return json.loads(checked_read(CONTROL/name,2*1024*1024))

def verify_installed():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    raw=checked_read(LAB/'MANIFEST.json',2*1024*1024,expected=MANIFEST_SHA);manifest=json.loads(raw)
    for name,pin in manifest['members'].items():require(len(checked_read(LAB/name,member_maximum(name),expected=pin['sha256']))==pin['bytes'],'Installed member size differs')

def start(a):
    verify_installed();n=native()
    try:return {'phase':'model_started','native':n.native_start_model(NATIVE_PINS)}
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def startkeeper(a):
    n=native()
    try:return {'phase':'keeper_started','native':n.native_start_keeper()}
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def public_files():
    result={}
    for name,(kind,relative)in PUBLIC_PATHS.items():
        path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
        if path.exists():
            st=secure_file(path,owner=65534 if kind=='model'else 0,maximum=2*1024*1024)
            result[name]={'bytes':st.st_size,'uid':st.st_uid}
    return result

def status(a):return {'phase':'native_status','native':native().native_status(),'public_files':public_files()}

def lock_identity(n,probe=False):
    import fcntl
    path=n.LIVE/'keeper.lock';fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        st=os.fstat(fd);require(stat.S_ISREG(st.st_mode)and st.st_uid==65534,'Native lock identity differs')
        if probe:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(fd,fcntl.LOCK_UN)
        return {'dev':st.st_dev,'ino':st.st_ino,'uid':st.st_uid,'exclusive_probe_when_empty':probe}
    finally:os.close(fd)

def baseline(a):
    n=native();require(not(CONTROL/'BASELINE.json').exists(),'Native baseline already exists')
    snapshot=n.native_status(include_journal=False);w=n.RestartWitness(snapshot)
    journal=n._read(n.LIVE/'state.json',2*1024*1024,owners=(0,65534));state=json.loads(journal)
    require(type(state.get('pending'))is dict,'Native baseline needs pending work')
    data={'snapshot':snapshot,'lock':lock_identity(n),'journal_sha256':sha(journal),'journal_raw_utf8':journal.decode('utf8'),'state':state}
    record_control('BASELINE.json',data);record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'native_baseline_saved','journal_sha256':sha(journal),'old_main_pid':w.old_main,'old_process_count':len(w.old_processes)}

def observe(a):
    n=native();require((CONTROL/'BASELINE.json').exists(),'Native baseline absent')
    base=control_json('BASELINE.json');stored=control_json('WITNESS_STATE.json');w=n.RestartWitness(base['snapshot']);w.__dict__.update(stored)
    until=time.monotonic()+25;count=0
    while time.monotonic()<until:
        w.capture();count+=1
        if w.empty_before_restart is not None and not(CONTROL/'JOURNAL_DURING_RESTART.json').exists():
            raw=n._read(n.LIVE/'state.json',2*1024*1024,owners=(0,65534));require(sha(raw)==base['journal_sha256'],'Pending journal changed before native restart')
            lock=lock_identity(n,probe=True);require((lock['dev'],lock['ino'])==(base['lock']['dev'],base['lock']['ino']),'Native lock inode changed')
            record_control('JOURNAL_DURING_RESTART.json',{'raw_utf8':raw.decode('utf8'),'sha256':sha(raw),'lock':lock,'old_generation_empty_at':w.empty_before_restart})
        if w.new_invocation is not None:
            proof=w.finish();after=lock_identity(n);require((after['dev'],after['ino'])==(base['lock']['dev'],base['lock']['ino']),'Restarted lock inode changed')
            proof['lock_before']=base['lock'];proof['lock_after']=after;record_control('NATIVE_RESTART_PROOF.json',proof);break
        time.sleep(4)
    record_control('WITNESS_STATE.json',w.__dict__)
    return {'phase':'native_observed','samples_added':count,'samples_total':len(w.samples),'old_empty_seen':w.empty_before_restart is not None,'new_invocation_seen':w.new_invocation is not None,'proof_available':(CONTROL/'NATIVE_RESTART_PROOF.json').exists()}

def stop(a):
    n=native()
    try:return n.native_stop_owned()
    except n.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def fetch(a):
    ownership();require(a.artifact in PUBLIC_PATHS,'Unapproved public artifact')
    kind,relative=PUBLIC_PATHS[a.artifact];path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
    data=checked_read(path,2*1024*1024,owners=(0,65534)if kind=='model'else(0,))
    return {'phase':'public_artifact','attempt':1,'artifact':a.artifact,'bytes':len(data),'sha256':sha(data),'base64':base64.b64encode(data).decode('ascii'),'private_material_exported':False}

if __name__=='__main__':main()
