"""Fixed-path isolated lab control. No installed service or credential mutations."""
from pathlib import Path,PurePosixPath
import argparse,base64,hashlib,io,json,os,re,shutil,stat,subprocess,tarfile,time

LAB=Path('/opt/popl-ubuntu-backup-recovery-20261126-c813')
UNIT='popl-ubuntu-backup-recovery-20261126-c813-model.service'
UPLOAD=Path('/tmp/popl-ubuntu-backup-recovery-20261126-c813.inputs.tar.gz')
MAX_ARCHIVE=96*1024*1024
MAX_UNPACKED=256*1024*1024
MAX_MEMBERS=2048
BUNDLE_SHA='8316ada3b9846b7e22d87c0224c450232083b6d863308318953bfbc1b2a212f5'
MANIFEST_SHA='414aa69b6890d8255833d76e282106f9fe4e5bd07b02b4a8673bf7fd3c32e177'
SOURCE_MANIFEST_SHA='d606c4ca389ea4177f1703de63e7a3b18ee524b18fd6a5da5b399d6e0dd78781'
WORKER_SHA='2b596730226e88b59a7e2ff48189eb88a7b0ed5803134c66ac8ebc6149943747'
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
ALLOWED=('MANIFEST.json', 'inputs/SOURCE_MANIFEST.json', 'inputs/TRADER.json', 'inputs/bindings.json', 'source/contracts/frontend_api/__init__.py', 'source/contracts/frontend_api/activation.py', 'source/contracts/frontend_api/activation_config.py', 'source/contracts/frontend_api/activation_server.py', 'source/contracts/frontend_api/activation_trace.py', 'source/contracts/frontend_api/activation_v4.py', 'source/contracts/frontend_api/admission.py', 'source/contracts/frontend_api/canonical_cache.py', 'source/contracts/frontend_api/claim_planner.py', 'source/contracts/frontend_api/collection.py', 'source/contracts/frontend_api/custody.py', 'source/contracts/frontend_api/earnings.py', 'source/contracts/frontend_api/earnings_checkpoint.py', 'source/contracts/frontend_api/earnings_checkpoint_build.py', 'source/contracts/frontend_api/earnings_checkpoint_import.py', 'source/contracts/frontend_api/earnings_checkpoint_v2.py', 'source/contracts/frontend_api/earnings_checkpoint_v3.py', 'source/contracts/frontend_api/earnings_exact_lp.py', 'source/contracts/frontend_api/earnings_prices.py', 'source/contracts/frontend_api/earnings_replay.py', 'source/contracts/frontend_api/history.py', 'source/contracts/frontend_api/history_audit.py', 'source/contracts/frontend_api/history_recovery.py', 'source/contracts/frontend_api/http_runtime.py', 'source/contracts/frontend_api/lifecycle.py', 'source/contracts/frontend_api/lineage.py', 'source/contracts/frontend_api/liquidity_context.py', 'source/contracts/frontend_api/mint_readiness.py', 'source/contracts/frontend_api/portfolio.py', 'source/contracts/frontend_api/portfolio_v5.py', 'source/contracts/frontend_api/portfolio_v6.py', 'source/contracts/frontend_api/portfolio_v7.py', 'source/contracts/frontend_api/principal_return.py', 'source/contracts/frontend_api/royalty_reporting.py', 'source/contracts/frontend_api/server.py', 'source/contracts/frontend_api/service.py', 'source/contracts/frontend_api/transaction_gas.py', 'source/contracts/frontend_api/transactions.py', 'source/contracts/frontend_api/wallet_earnings.py', 'source/contracts/frontend_api/wallet_view.py', 'source/contracts/frontend_api/worker.py', 'source/contracts/indexer/__init__.py', 'source/contracts/indexer/event_schema.json', 'source/contracts/indexer/events.py', 'source/contracts/indexer/historical_event_schema.json', 'source/contracts/indexer/monitor.py', 'source/contracts/keeper/__init__.py', 'source/contracts/keeper/cast_process.py', 'source/contracts/keeper/compound_policy.py', 'source/contracts/keeper/health.py', 'source/contracts/keeper/monitor.py', 'source/contracts/keeper/operation_review.py', 'source/contracts/keeper/ops.py', 'source/contracts/keeper/principal.py', 'source/contracts/keeper/probe.py', 'source/contracts/keeper/rebalance_confirmation.py', 'source/contracts/keeper/recovery_bundle.py', 'source/contracts/keeper/royalties.py', 'source/contracts/keeper/staging-install.sh', 'source/contracts/keeper/staging-monitor-install.sh', 'source/contracts/keeper/staging.py', 'source/contracts/keeper/staging_observer.py', 'source/contracts/keeper/watchdog.py', 'source/contracts/keeper/zzz-keeper.service', 'source/contracts/scripts/build-earnings-checkpoint.py', 'source/contracts/scripts/build-workload-inventory.py', 'source/contracts/scripts/check-focused-evidence.py', 'source/contracts/scripts/check-local-deployment-evidence.py', 'source/contracts/scripts/check-market-evidence.py', 'source/contracts/scripts/check-python-publication.py', 'source/contracts/scripts/check-slither-review.py', 'source/contracts/scripts/check-source9-rehearsal-evidence.py', 'source/contracts/scripts/check-staging-monitor.py', 'source/contracts/scripts/generate-artwork-library.py', 'source/contracts/scripts/generate-dynamic-range-vectors.py', 'source/contracts/scripts/generate-function-reference.py', 'source/contracts/scripts/generate-operator-reference.py', 'source/contracts/scripts/generate_event_schema.py', 'source/contracts/scripts/history-recovery.py', 'source/contracts/scripts/import-earnings-checkpoint.py', 'source/contracts/scripts/install-deps.sh', 'source/contracts/scripts/inventory-nft-holders.py', 'source/contracts/scripts/keeper-recovery.py', 'source/contracts/scripts/local-api-stack.py', 'source/contracts/scripts/local-stack.py', 'source/contracts/scripts/local_browser.py', 'source/contracts/scripts/local_clock.py', 'source/contracts/scripts/local_fixture_profile.py', 'source/contracts/scripts/local_inputs.py', 'source/contracts/scripts/local_wallet.py', 'source/contracts/scripts/observe-production-config.py', 'source/contracts/scripts/prepare-deployment-sequence.py', 'source/contracts/scripts/prepare-deployment.py', 'source/contracts/scripts/prepare-dollar-rehearsal.py', 'source/contracts/scripts/prepare-manual-lp.py', 'source/contracts/scripts/prepare-opensea-drop.py', 'source/contracts/scripts/prepare-operator-management.py', 'source/contracts/scripts/prepare-operator-review.py', 'source/contracts/scripts/prepare-preseal.py', 'source/contracts/scripts/prepare-release-review.py', 'source/contracts/scripts/prepare_ipfs_bundle.py', 'source/contracts/scripts/rehearse-api-ingress.py', 'source/contracts/scripts/rehearse-keeper.py', 'source/contracts/scripts/rehearse-local-deployment.py', 'source/contracts/scripts/rehearse-manual-recovery.py', 'source/contracts/scripts/rehearse-manual-reference.py', 'source/contracts/scripts/run-current-pool-fork.py', 'source/contracts/scripts/run-fork-checks.py', 'source/contracts/scripts/run-keeper-tests.py', 'source/contracts/scripts/run_python_tests.py', 'source/contracts/scripts/source9_rehearsal_api.py', 'source/contracts/scripts/source9_rehearsal_deploy.py', 'source/contracts/scripts/source9_rehearsal_fork.py', 'source/contracts/scripts/source9_rehearsal_state.py', 'source/contracts/scripts/source_checks.py', 'source/contracts/scripts/sync-project-todo.py', 'source/contracts/scripts/validate-production-config.py', 'source/contracts/scripts/verify-hookless-pool.py', 'source/contracts/scripts/verify-local-stack.py', 'source/contracts/scripts/verify-local-website.py', 'source/contracts/scripts/verify-normal-profile.py', 'source/contracts/scripts/verify-slither.sh', 'source/contracts/scripts/verify.sh', 'source/contracts/zzz_ops/__init__.py', 'source/contracts/zzz_ops/abi.py', 'source/contracts/zzz_ops/deployment_plan.py', 'source/contracts/zzz_ops/deployment_sequence.py', 'source/contracts/zzz_ops/errors.py', 'source/contracts/zzz_ops/ethereum_fees.py', 'source/contracts/zzz_ops/evidence.py', 'source/contracts/zzz_ops/exact_lp.py', 'source/contracts/zzz_ops/execution_price.py', 'source/contracts/zzz_ops/factory_code_v2.py', 'source/contracts/zzz_ops/factory_code_v3.py', 'source/contracts/zzz_ops/factory_code_v4.py', 'source/contracts/zzz_ops/factory_code_v5.py', 'source/contracts/zzz_ops/factory_code_v6.py', 'source/contracts/zzz_ops/focused_evidence.py', 'source/contracts/zzz_ops/function_reference.py', 'source/contracts/zzz_ops/historical_production.py', 'source/contracts/zzz_ops/holder_preflight.py', 'source/contracts/zzz_ops/log_provenance.py', 'source/contracts/zzz_ops/lp_execution.py', 'source/contracts/zzz_ops/management_base.py', 'source/contracts/zzz_ops/management_custody.py', 'source/contracts/zzz_ops/management_exit.py', 'source/contracts/zzz_ops/management_review.py', 'source/contracts/zzz_ops/manual_lp_review.py', 'source/contracts/zzz_ops/market_evidence.py', 'source/contracts/zzz_ops/mint_policy_v2.py', 'source/contracts/zzz_ops/opensea_drop.py', 'source/contracts/zzz_ops/operator_reference.py', 'source/contracts/zzz_ops/operator_review.py', 'source/contracts/zzz_ops/physical_portfolio.py', 'source/contracts/zzz_ops/position.py', 'source/contracts/zzz_ops/preseal_plan.py', 'source/contracts/zzz_ops/price_policy.py', 'source/contracts/zzz_ops/production_observer.py', 'source/contracts/zzz_ops/production_observer_v10.py', 'source/contracts/zzz_ops/production_observer_v11.py', 'source/contracts/zzz_ops/production_observer_v12.py', 'source/contracts/zzz_ops/production_observer_v13.py', 'source/contracts/zzz_ops/production_observer_v14.py', 'source/contracts/zzz_ops/production_observer_v15.py', 'source/contracts/zzz_ops/production_observer_v4.py', 'source/contracts/zzz_ops/production_observer_v5.py', 'source/contracts/zzz_ops/production_observer_v6.py', 'source/contracts/zzz_ops/production_observer_v7.py', 'source/contracts/zzz_ops/production_observer_v8.py', 'source/contracts/zzz_ops/production_observer_v9.py', 'source/contracts/zzz_ops/production_v10.py', 'source/contracts/zzz_ops/production_v11.py', 'source/contracts/zzz_ops/production_v12.py', 'source/contracts/zzz_ops/production_v13.py', 'source/contracts/zzz_ops/production_v14.py', 'source/contracts/zzz_ops/production_v15.py', 'source/contracts/zzz_ops/production_v2.py', 'source/contracts/zzz_ops/production_v4.py', 'source/contracts/zzz_ops/production_v5.py', 'source/contracts/zzz_ops/production_v6.py', 'source/contracts/zzz_ops/production_v7.py', 'source/contracts/zzz_ops/production_v8.py', 'source/contracts/zzz_ops/production_v9.py', 'source/contracts/zzz_ops/protocol_policy.py', 'source/contracts/zzz_ops/range_policy.py', 'source/contracts/zzz_ops/read_process.py', 'source/contracts/zzz_ops/rebalance_confirmation.py', 'source/contracts/zzz_ops/review_bundle.py', 'source/contracts/zzz_ops/royalty_read_policy.py', 'source/contracts/zzz_ops/rpc.py', 'source/contracts/zzz_ops/state.py', 'source/contracts/zzz_ops/tick_math.py', 'source/contracts/zzz_ops/work_budget.py', 'source/helpers/independent_private.py', 'source/helpers/job_cases.py', 'source/helpers/keeper_jobs.py', 'source/helpers/keeper_runtime.py', 'source/helpers/model_service.py', 'source/helpers/native_base.py', 'source/helpers/recovery_control.py')
PUBLIC_PATHS={'model-READY.json': ('model', 'model/READY.json'), 'model-PENDING_READY.json': ('model', 'model/PENDING_READY.json'), 'model-RESTORE_READY.json': ('model', 'model/RESTORE_READY.json'), 'model-INCLUDED.json': ('model', 'model/INCLUDED.json'), 'model-SETTLED.json': ('model', 'model/SETTLED.json'), 'model-DRY.json': ('model', 'model/DRY.json'), 'model-COMPLETE.json': ('model', 'model/COMPLETE.json'), 'model-RESULT.json': ('model', 'model/RESULT.json'), 'model-EVENTS.json': ('model', 'model/EVENTS.json'), 'model-INDEPENDENT.json': ('model', 'model/INDEPENDENT.json'), 'case-BINDINGS.json': ('model', 'model/supervisor/BINDINGS.json'), 'case-BINDING_REFUSAL.json': ('model', 'model/supervisor/BINDING_REFUSAL.json'), 'case-CLOCK_REPAIR.json': ('model', 'model/supervisor/CLOCK_REPAIR.json'), 'case-FINANCIAL_INITIAL.json': ('model', 'model/supervisor/FINANCIAL_INITIAL.json'), 'case-FINANCIAL_INCLUDED.json': ('model', 'model/supervisor/FINANCIAL_INCLUDED.json'), 'case-FINANCIAL_FINAL.json': ('model', 'model/supervisor/FINANCIAL_FINAL.json'), 'case-CANONICAL.json': ('model', 'model/supervisor/CANONICAL.json'), 'case-EVIDENCE.json': ('model', 'model/supervisor/EVIDENCE.json'), 'case-SOURCE_PRESERVED.json': ('model', 'model/supervisor/SOURCE_PRESERVED.json'), 'case-SETUP.json': ('model', 'model/supervisor/SETUP.json'), 'case-RECEIPTS.json': ('model', 'model/supervisor/RECEIPTS.json'), 'case-RAW_REVIEWS.json': ('model', 'model/supervisor/RAW_REVIEWS.json'), 'case-RESULT.json': ('model', 'model/supervisor/RESULT.json'), 'native-SOURCE_FENCE.json': ('control', 'SOURCE_FENCE.json'), 'native-RECOVERY_RECEIPT.json': ('control', 'RECOVERY_RECEIPT.json'), 'native-DRY_RECEIPT.json': ('control', 'DRY_RECEIPT.json'), 'native-FENCED.json': ('control', 'FENCED.json'), 'native-RECOVERY_COMPLETE.json': ('control', 'RECOVERY_COMPLETE.json'), 'native-DRY_COMPLETE.json': ('control', 'DRY_COMPLETE.json'), 'native-FINAL_STOP.json': ('control', 'FINAL_STOP.json'), 'native-model.stdout.log': ('model', 'native-model.stdout.log'), 'native-model.stderr.log': ('model', 'native-model.stderr.log'), 'native-keeper.stdout.log': ('model', 'native-keeper.stdout.log'), 'native-keeper.stderr.log': ('model', 'native-keeper.stderr.log'), 'native-resolve.stdout.log': ('model', 'native-resolve.stdout.log'), 'native-resolve.stderr.log': ('model', 'native-resolve.stderr.log')}
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
    p=run(['systemctl','show',UNIT,'--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,Result,ExecMainStatus,PrivateNetwork,User,Group,NoNewPrivileges,ProtectSystem,ProtectHome,PrivateDevices,KillMode,RuntimeMaxUSec,TimeoutStopUSec,MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,CPUWeight,IOWeight,Nice,PrivateMounts,TemporaryFileSystem','--no-pager'])
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
    for name,digest in (('keeper_runtime.py', 'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4'), ('keeper_jobs.py', '363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4'), ('job_cases.py', '7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'), ('independent_private.py', '5efec210669a694827fd2f75f9052ce0be5ab9196f27c9ce1da2f2fa363eb4c2'), ('model_service.py', '2b596730226e88b59a7e2ff48189eb88a7b0ed5803134c66ac8ebc6149943747'), ('native_base.py', 'fe476c1f95d1c72a9f604889c500f501d3e7fe951714edd7806e2ae406d72765'), ('recovery_control.py', '62b0b8fcc6801a219806f667499ce5965552e86b7954790c626453875c371455')):require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')
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
    other=run(['/usr/bin/systemctl','show','popl-ubuntu-backup-recovery-20261126-c813-keeper.service','--no-pager','--property=LoadState'])
    require(other.stdout.decode('utf-8','strict').strip()=='LoadState=not-found','Owned keeper unit name already exists')
    other=run(['/usr/bin/systemctl','show','popl-ubuntu-backup-recovery-20261126-c813-resolve.service','--no-pager','--property=LoadState'])
    require(other.stdout.decode('utf-8','strict').strip()=='LoadState=not-found','Owned resolve unit name already exists')
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



"""Closed c813 backup-to-new-runtime actions; appended only by reviewed packaging."""
import importlib.util
import selectors
import signal
import sys
from types import SimpleNamespace
sys.dont_write_bytecode=True
CONTROL=LAB/'control'
NATIVE_PINS={'source_manifest_sha256': 'd606c4ca389ea4177f1703de63e7a3b18ee524b18fd6a5da5b399d6e0dd78781', 'base_sha256': 'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4', 'jobs_sha256': '363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4', 'cases_sha256': '7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7', 'model_sha256': '2b596730226e88b59a7e2ff48189eb88a7b0ed5803134c66ac8ebc6149943747', 'independent_sha256': '5efec210669a694827fd2f75f9052ce0be5ab9196f27c9ce1da2f2fa363eb4c2'}
BASE_SHA='fe476c1f95d1c72a9f604889c500f501d3e7fe951714edd7806e2ae406d72765'
CONTROL_SHA='62b0b8fcc6801a219806f667499ce5965552e86b7954790c626453875c371455'

def run(argv,timeout=12):
    require(type(argv)is list and argv and 0<timeout<=20,'Invalid fixed controller work bound')
    child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        start_new_session=True,close_fds=True,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8'})
    outputs=[bytearray(),bytearray()];size=0;finished=False;deadline=time.monotonic()+timeout
    try:
        with selectors.DefaultSelector()as selector:
            for index,pipe in enumerate((child.stdout,child.stderr)):
                os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,index)
            while selector.get_map():
                require(time.monotonic()<deadline,'Fixed controller command deadline exceeded')
                for key,_ in selector.select(min(.2,max(.001,deadline-time.monotonic()))):
                    chunk=os.read(key.fd,min(16384,256*1024+1-size))
                    if not chunk:selector.unregister(key.fileobj);continue
                    size+=len(chunk);require(size<=256*1024,'Fixed controller command output bound exceeded');outputs[key.data].extend(chunk)
        require(time.monotonic()<deadline,'Fixed controller completion deadline exceeded')
        code=child.wait(timeout=max(.001,deadline-time.monotonic()));finished=True
        return SimpleNamespace(returncode=code,stdout=bytes(outputs[0]),stderr=bytes(outputs[1]))
    finally:
        if not finished:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait(timeout=2)
        child.stdout.close();child.stderr.close()

def native():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    for name,pin in (('native_base.py',BASE_SHA),('recovery_control.py',CONTROL_SHA)):
        path=LAB/'source/helpers'/name;checked_read(path,2*1024*1024,expected=pin)
        module_name='native_base'if name=='native_base.py'else'fixed_c813_recovery'
        spec=importlib.util.spec_from_file_location(module_name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[module_name]=module;spec.loader.exec_module(module)
    return module

def invoke(method,*args):
    n=native()
    try:return getattr(n,method)(*args)
    except n.N.NativeRefusal as exc:raise ControlRefusal(str(exc))from None

def record_control(name,value):
    markers={'FENCED.json','RECOVERY_COMPLETE.json','DRY_COMPLETE.json'}
    require(name in markers|{'SOURCE_FENCE.json','RECOVERY_RECEIPT.json','DRY_RECEIPT.json','FINAL_STOP.json'},'Closed recovery record name')
    if not CONTROL.exists():CONTROL.mkdir(mode=0o755);os.chmod(CONTROL,0o755,follow_symlinks=False)
    st=CONTROL.lstat();require(stat.S_ISDIR(st.st_mode)and st.st_uid==0 and stat.S_IMODE(st.st_mode)==0o755,'Recovery control directory differs')
    raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n';require(len(raw)<=2*1024*1024,'Recovery record exceeds bound')
    target=CONTROL/name;require(not os.path.lexists(target),'Recovery control record already exists')
    mode=0o644 if name in markers else 0o600
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode);os.fchmod(fd,mode)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return sha(raw)

def verify_installed():
    record=ownership();require(record['controller_sha256']==ACTIVE_CONTROLLER_SHA,'Controller source changed')
    manifest=json.loads(checked_read(LAB/'MANIFEST.json',2*1024*1024,expected=MANIFEST_SHA))
    for name,pin in manifest['members'].items():
        require(len(checked_read(LAB/name,member_maximum(name),expected=pin['sha256']))==pin['bytes'],'Installed member size differs')

def start(a):
    verify_installed();return {'phase':'model_started','native':invoke('start_model',NATIVE_PINS)}

def startkeeper(a):return {'phase':'stock_keeper_started','native':invoke('start_keeper')}

def stopkeeper(a):return {'phase':'keeper_fence_requested','native':invoke('stopkeeper')}

def public_files():
    result={}
    for name,(kind,relative)in PUBLIC_PATHS.items():
        path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
        if path.exists():
            item=secure_file(path,owner=65534 if kind=='model'else 0,maximum=2*1024*1024)
            result[name]={'bytes':item.st_size,'uid':item.st_uid}
    return result

def status(a):
    value=invoke('status')
    completed=value.pop('unsigned_completion',None)
    if completed is not None:
        require(type(completed)is dict and set(completed)=={'kind','receipt','marker'}and completed['kind']in ('recover','dry'),'Closed unsigned completion differs')
        receipt_name,marker_name=(('RECOVERY_RECEIPT.json','RECOVERY_COMPLETE.json')if completed['kind']=='recover'else('DRY_RECEIPT.json','DRY_COMPLETE.json'))
        require(not(CONTROL/receipt_name).exists()and not(CONTROL/marker_name).exists(),'Unsigned completion already recorded')
        record_control(receipt_name,completed['receipt']);record_control(marker_name,completed['marker'])
    return {'phase':'native_status','native':value,'public_files':public_files()}

def fence(a):
    require(not(CONTROL/'SOURCE_FENCE.json').exists(),'Source fence already recorded')
    result=invoke('fence');receipt=record_control('SOURCE_FENCE.json',result)
    marker={key:result[key]for key in ('schema','keeper_fenced_empty','automatic_restart_inhibited','accepted_hash','journal_sha256')}
    digest=record_control('FENCED.json',marker)
    return {'phase':'source_fenced_before_restore','receipt_sha256':receipt,'marker_sha256':digest,'result':result}

def recover(a):
    require(not(CONTROL/'RECOVERY_RECEIPT.json').exists(),'Unsigned recovery already recorded')
    return {'phase':'restored_unsigned_recovery_started','result':invoke('recover')}

def dry(a):
    require(not(CONTROL/'DRY_RECEIPT.json').exists(),'Unsigned metadata review already recorded')
    return {'phase':'restored_unsigned_metadata_started','result':invoke('dry')}

def stop(a):
    result=invoke('stop_owned')
    if result.get('phase')=='stopped'and not(CONTROL/'FINAL_STOP.json').exists():record_control('FINAL_STOP.json',result)
    return result

def fetch(a):
    ownership();require(a.artifact in PUBLIC_PATHS,'Unapproved public artifact')
    kind,relative=PUBLIC_PATHS[a.artifact]
    path=(LAB/'runtime/run-001'/relative)if kind=='model'else CONTROL/relative
    raw=checked_read(path,2*1024*1024,owners=(0,65534)if kind=='model'else(0,))
    return {'phase':'public_artifact','attempt':1,'artifact':a.artifact,'bytes':len(raw),
        'sha256':sha(raw),'base64':base64.b64encode(raw).decode('ascii'),'private_material_exported':False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('install','start','startkeeper','status','stopkeeper','fence','recover','dry','stop','fetch'))
    parser.add_argument('--controller-sha256',required=True);parser.add_argument('--bundle-sha256')
    parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--artifact');a=parser.parse_args()
    globals()['ACTIVE_CONTROLLER_SHA']=a.controller_sha256
    try:
        require(a.attempt==1 and re.fullmatch('[0-9a-f]{64}',a.controller_sha256)is not None,'Fixed controller identity differs')
        if a.action=='install':require(re.fullmatch('[0-9a-f]{64}',a.bundle_sha256 or'')is not None,'Invalid bundle pin')
        result=globals()[a.action](a)
    except BaseException as exc:
        site={'function':None,'line':None};trace=exc.__traceback__
        while trace is not None:
            name=trace.tb_frame.f_code.co_name
            if trace.tb_frame.f_code.co_filename==__file__ and name!='require'and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,63}',name)and 0<trace.tb_lineno<10000:
                site={'function':name,'line':trace.tb_lineno}
            trace=trace.tb_next
        kind=type(exc).__name__
        kind=kind if kind in {'ControlRefusal','FileNotFoundError','PermissionError','OSError','ValueError','JSONDecodeError','TimeoutExpired'}else'Other'
        guard=str(exc)if type(exc)is ControlRefusal else None
        if guard is not None and(len(guard)>160 or any(ord(char)<32 or ord(char)>126 for char in guard)):guard=None
        print(json.dumps({'phase':a.action,'failed':True,'reason':'bounded_owned_lab_control_failed',
            'error_type':kind,'fixed_guard':guard,'site':site,'lab':str(LAB),'unit':UNIT}))
        raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
