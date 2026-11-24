"""NEW isolated Ubuntu operator utilities; no signer or service adoption.

Run only after the actor has stopped, while its same owned Anvil remains alive.
History tools operate on NEW bytecopies of preserved synthetic source9/V9 data;
these are offline integrity checks, not actual F6/V10 history qualification.
"""
from pathlib import Path
import argparse,copy,hashlib,json,os,re,stat,sys,time

LAB=Path('/opt/popl-ubuntu-features-20261124-c7ed')
RUN=LAB/'runtime/run-001'
OLD=Path('/opt/popl-wallet-latency-20261123-c7e5')
HISTORY=OLD/'runtime/run-001/wallet1000-main/data'
LIMIT=64*1024*1024
PINS={
 'raw.sqlite':('aed6781e5a3214fca0d553000d0ebe2a0937669d86f1d3e62d41936ab7eda091',16*1024*1024),
 'checkpoint-candidate.json':('861f01fb3f6ca00d99a02b722bf2c434d126ff469ef36958875bab336492bf48',32*1024*1024),
 'api-checkpoint.json':('b8ab1db98c31b9b18ae4a2cee3df4d3e6a8d5b3cdd4596c00c602504b85c95b0',1024*1024)}


def need(ok,reason):
    if not ok:raise ValueError(reason)


def sha(data):return hashlib.sha256(data).hexdigest()


def save(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw)<=1024*1024,'Utility receipt exceeds bound')
    with path.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def old_read(name):
    expected,maximum=PINS[name];path=HISTORY/name;opened=[]
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);opened.append(fd)
        for part in path.parts[1:-1]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);opened.append(fd)
            entry=os.fstat(fd);need(stat.S_ISDIR(entry.st_mode)and entry.st_uid in(0,65534)and not entry.st_mode&0o022,'Old history directory identity')
        parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);opened.append(fd);before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode)and before.st_uid==65534 and before.st_nlink==1 and not before.st_mode&0o022 and before.st_size<=maximum,'Old history file identity/bound')
        parts=[];size=0
        while True:
            raw=os.read(fd,min(65536,maximum+1-size))
            if not raw:break
            size+=len(raw);need(size<=maximum,'Old history read bound');parts.append(raw)
        after=os.fstat(fd);current=os.stat(path.name,dir_fd=parent,follow_symlinks=False)
        key=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns)
        data=b''.join(parts);need(key(before)==key(after)==key(current)and size==before.st_size and sha(data)==expected,'Old history input changed or pin differs')
        return data
    finally:
        for fd in reversed(opened):os.close(fd)


def wal_state():
    rows={}
    for suffix in('-wal','-journal'):
        path=HISTORY/('raw.sqlite'+suffix)
        try:entry=path.lstat()
        except FileNotFoundError:rows[suffix]={'present':False,'bytes':0};continue
        need(stat.S_ISREG(entry.st_mode)and entry.st_uid==65534 and entry.st_nlink==1 and entry.st_size==0,'Uncaptured history sidecar requires separate review')
        rows[suffix]={'present':True,'bytes':entry.st_size}
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--keeper-config',type=Path,required=True);parser.add_argument('--rpc-url',required=True);parser.add_argument('--bucket',required=True)
    args=parser.parse_args();source=args.source_root.resolve();out=args.output.resolve();config=args.keeper_config.resolve()
    need(os.name=='posix'and os.geteuid()==65534,'Unprivileged Ubuntu utility context required')
    need(source==LAB/'source/contracts'and out==RUN/'utilities'and config==RUN/'keeper/live/config.json','Fixed utility paths differ')
    need(args.rpc_url=='http://127.0.0.1:19592'and re.fullmatch('[1-9][0-9]{0,77}',args.bucket)is not None and int(args.bucket)<1<<256,'Owned RPC/bucket differs')
    out.mkdir(mode=0o700,exist_ok=False);(out/'tmp').mkdir(mode=0o700)
    sys.dont_write_bytecode=True;sys.path.insert(0,str(source))
    from keeper.cast_process import run_cast
    from frontend_api.earnings_checkpoint import source_identity
    cfg=json.loads(config.read_bytes());need(cfg['chain_id']==4663 and cfg['rpc_urls']==[args.rpc_url],'Actual keeper chain/RPC differs')
    state=Path(cfg['state_path']);health=Path(cfg['health_path'])
    need(state.resolve().is_relative_to(RUN/'keeper/live')and health.resolve().is_relative_to(RUN/'keeper/live'),'Keeper output path differs')
    need(json.loads(state.read_bytes()).get('pending')is None,'Stop actor and reconcile pending before utilities')
    before={'configuration':sha(config.read_bytes()),'state':sha(state.read_bytes()),'health':sha(health.read_bytes())}
    environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONPATH':str(source),'TMPDIR':str(out/'tmp')}
    result={'schema':1,'scope':'actual isolated keeper.ops CLI plus offline synthetic-history integrity only','success':False,'complete_Ubuntu_qualification':False,'public_transactions':0,'signing':False,'sealing':False,'adoption':False,'production_approved':False,'commands':[],'not_executed':{'checkpoint_builder':'Existing same-semantic-source current1000NFT c7e5 actualUbuntu CLI evidence reused; no unchanged rerun','positive_checkpoint_importer':'Standalone c7e5 graph has no appended authenticated replacement; a valid shorter-prefix/new-lineage fixture is required. Same-graph negative CLI is separate.'}}
    until=time.monotonic()+300;history_before=None;sidecars_before=None;stage='keeper_preflight'
    def operation(label,argv,*,timeout=45,expected=0,json_result=False):
        remaining=until-time.monotonic();need(remaining>0,'Utility aggregate deadline')
        started=time.monotonic();r=run_cast([sys.executable,'-B',*map(str,argv)],env=environment,timeout=min(timeout,remaining))
        for kind,body in(('stdout',r.stdout),('stderr',r.stderr)):
            with(out/(label+'.'+kind)).open('x',encoding='utf-8')as stream:stream.write(body)
        row={'name':label,'exit_code':r.returncode,'expected_exit_code':expected,'elapsed_seconds':time.monotonic()-started,'stdout_bytes':len(r.stdout.encode()),'stderr_bytes':len(r.stderr.encode())};result['commands'].append(row)
        need(r.returncode==expected,'Utility command refused: '+label)
        return json.loads(r.stdout.strip().splitlines()[-1])if json_result else r
    try:
        common=['-m','keeper.ops','--config',config]
        preflight=operation('keeper-preflight',common+['preflight'],json_result=True)
        need(preflight['ok']is True and preflight['lp_routing']['state']=='validated','Actual keeper preflight is unavailable');save(out/'PREFLIGHT.json',preflight)
        stage='keeper_review';review=operation('keeper-review',common+['review','--bucket',args.bucket,'--simulate'],timeout=60,json_result=True)
        need(review['ok']is True and review['read_only']is True and review['production_approved']is False and review['profile']['accounting_version']==7 and len(review['operations'])==3,'Actual typed operation review differs')
        need(all(row['state']!='unsupported'for row in review['operations']),'Actual typed review fell back to historical support');save(out/'OPERATION_REVIEW.json',review)
        stage='keeper_health';check=operation('keeper-health',common+['health','--max-age','1800'],json_result=True);need(check['ok']is True,'Actual daemon health is not healthy');save(out/'HEALTH.json',check)
        stage='keeper_snapshot';snapshot=out/'keeper-snapshot.json';saved=operation('keeper-snapshot',common+['snapshot','--output',snapshot],json_result=True)
        verified=operation('keeper-verify-snapshot',common+['verify-snapshot','--input',snapshot,'--max-age','3600'],json_result=True)
        need(saved['ok']is verified['ok']is True and saved['sha256']==verified['sha256'],'Actual keeper snapshot differs');result['keeper_snapshot_sha256']=sha(snapshot.read_bytes())
        stage='actual_indexer_partition'
        try:
            from indexer_utility import run as indexer_run
            result['indexer']=indexer_run(source,out,cfg,operation)
        except Exception as exc:
            result['indexer']={'success':False,'failure_stage':'indexer_bootstrap','error_class':type(exc).__name__,'production_approved':False}
        stage='history_input_copy';sidecars_before=wal_state();history_before={name:old_read(name)for name in PINS}
        need(sum(map(len,history_before.values()))<=LIMIT,'Copied history total input bound')
        history=out/'history';history.mkdir(mode=0o700);owned=history/'inputs';owned.mkdir(mode=0o700)
        for name,raw in history_before.items():
            with(owned/name).open('xb')as stream:stream.write(raw)
        checkpoint=json.loads(history_before['checkpoint-candidate.json']);need(checkpoint['schema']==2 and checkpoint['sources']==source_identity(2),'Current semantic checkpoint sources differ')
        copied=copy.deepcopy(json.loads(history_before['api-checkpoint.json']));need(copied['accounting_version']==7,'Expected accounting7 synthetic source')
        copied['history']['database']=str(owned/'raw.sqlite');copied['earnings_history']['checkpoint']={'path':str(owned/'checkpoint-candidate.json'),'sha256':PINS['checkpoint-candidate.json'][0]}
        copied_cfg=owned/'api-owned.json';save(copied_cfg,copied)
        stage='history_backup';bundle=history/'backup';operation('history-backup',[source/'scripts/history-recovery.py','backup','--config',copied_cfg,'--output',bundle,'--max-bytes',str(LIMIT)],timeout=90)
        manifest_raw=(bundle/'manifest.json').read_bytes();manifest_sha=sha(manifest_raw);manifest=json.loads(manifest_raw)
        need(manifest['raw_retention']['window_seconds']==86400 and manifest['raw_retention']['pruned']is False and manifest['checkpoint']['sha256']==PINS['checkpoint-candidate.json'][0],'History backup lost required window/phase')
        need(len(manifest['databases'])==1 and manifest['databases'][0]['snapshot']['tip']['timestamp']-manifest['checkpoint']['anchor']['timestamp']>=86400,'Preserved history does not cover full24-hour suffix')
        stage='history_verify';operation('history-verify',[source/'scripts/history-recovery.py','verify','--bundle',bundle,'--manifest-sha256',manifest_sha,'--max-bytes',str(LIMIT)],timeout=90)
        stage='history_restore';restored=history/'restored';operation('history-restore',[source/'scripts/history-recovery.py','restore','--bundle',bundle,'--manifest-sha256',manifest_sha,'--output',restored,'--max-bytes',str(LIMIT)],timeout=90)
        need(sha((restored/'checkpoint.json').read_bytes())==PINS['checkpoint-candidate.json'][0]and(restored/'manifest.json').read_bytes()==manifest_raw,'Restored checkpoint/manifest bytes differ')
        for entry in manifest['files']:
            left=(bundle/entry['path']).resolve();right=(restored/entry['path']).resolve()
            need(left.is_relative_to(bundle.resolve())and right.is_relative_to(restored.resolve())and left.stat().st_size==right.stat().st_size==entry['bytes']<=LIMIT and sha(left.read_bytes())==sha(right.read_bytes())==entry['sha256'],'Restored raw artifact differs')
        stage='history_bad_pin_refusal';operation('history-bad-manifest',[source/'scripts/history-recovery.py','verify','--bundle',bundle,'--manifest-sha256','0'*64,'--max-bytes',str(LIMIT)],expected=1,timeout=30)
        result['history']={'scope':'preserved synthetic V9/source9 only; no new chain/RPC acceptance','old_original_pins':{n:p[0]for n,p in PINS.items()},'manifest_sha256':manifest_sha,'database_summaries':manifest['databases'],'checkpoint_info':manifest['checkpoint'],'full_window_seconds':86400,'raw_retention':manifest['raw_retention'],'checkpoint_bytes_preserved':True,'all_phase_bytes_preserved':True,'negative_manifest_refused':True,'package_byte_cap':LIMIT,'defaults_or_HTTP_limits_changed':False}
        stage='same_graph_import_refusal'
        target=copy.deepcopy(copied);target['earnings_history'].pop('checkpoint');target['rpc_urls']=['http://127.0.0.1:19593']
        target_config=history/'import-target.json';save(target_config,target)
        # The importer is strictly for a shorter graph plus a NEW authenticated
        # replacement. Demonstrate that exact source precondition separately
        # with the explicit offline NoNetwork adapter, then exercise real CLI.
        from frontend_api.service import Projection
        from frontend_api.history_recovery import NoNetwork
        from frontend_api.history import HistoryError
        from frontend_api.earnings_checkpoint_import import _ImportedPrefix
        from frontend_api.earnings_checkpoint_v3 import peers
        projection=Projection(target,rpc=NoNetwork());need(len(peers(projection.earnings_history))==1,'Expected standalone import-refusal graph')
        prefix={'path':str(owned/'checkpoint-candidate.json'),'sha256':PINS['checkpoint-candidate.json'][0]}
        expected='Prefix must precede a new authenticated replacement';observed=None
        try:_ImportedPrefix(projection.earnings_history,prefix,history_before['checkpoint-candidate.json'],checkpoint)
        except HistoryError as exc:observed=str(exc)
        need(observed==expected,'Standalone importer source precondition differs')
        candidate=history/'import-refused-candidate.json';review=history/'import-refused-review.json'
        operation('same-graph-import-refused',[source/'scripts/import-earnings-checkpoint.py','--config',target_config,'--prefix',owned/'checkpoint-candidate.json','--prefix-sha256',PINS['checkpoint-candidate.json'][0],'--block','99','--output',candidate,'--review-output',review],expected=1,timeout=45)
        need(not candidate.exists()and not review.exists(),'Refused import unexpectedly published artifacts')
        result['checkpoint_importer']={'scope':'NEGATIVE actual CLI plus explicit NoNetwork precondition diagnostic only','same_graph_refused':True,'positive_import_qualified':False,'candidate_or_review_published':False,'source_precondition':expected,'CLI_inner_message_exposed':False,'old_prefix_bytes_preserved':sha((owned/'checkpoint-candidate.json').read_bytes())==PINS['checkpoint-candidate.json'][0]}
        result['success']=result['indexer']['success']is True
    except Exception as exc:result.update(failure_stage=stage,error_class=type(exc).__name__)
    finally:
        result['keeper_state_preserved']={'configuration':sha(config.read_bytes())==before['configuration'],'state':sha(state.read_bytes())==before['state'],'health':sha(health.read_bytes())==before['health']}
        result['old_history_inputs_preserved']=False
        try:
            if history_before is not None:
                need(all(old_read(name)==raw for name,raw in history_before.items())and wal_state()==sidecars_before,'Old history inputs changed')
                result['old_history_inputs_preserved']=True
        except Exception as exc:result['preservation_error_class']=type(exc).__name__
        if not all(result['keeper_state_preserved'].values())or(history_before is not None and not result['old_history_inputs_preserved']):result['success']=False
        save(out/'RESULT.json',result)
    print(json.dumps({'success':result['success'],'commands':len(result['commands']),'scope':result['scope'],'coverage_complete':False}));return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
