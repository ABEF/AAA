"""DISTINCT Ubuntu schema3 two-epoch prefix -> three-epoch import only.

Actual CLI main/argparse in a fixture-injected process, not stock HTTP/provider
admission. Preserved synthetic lifecycle/getter truths are explicit; raw logs,
SQL/replay/import/codecs/recovery are current production implementations.
No socket, Anvil, signing, transaction, old test method or wallet journey.
"""
from pathlib import Path
from contextlib import ExitStack,redirect_stdout,redirect_stderr
import argparse,copy,hashlib,io,json,os,runpy,socket,sys,time,unittest
from unittest.mock import patch
EXPECTED=Path('/opt/popl-ubuntu-features-20261124-c7ee')


def need(ok,message):
 if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def raw_json(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def exclusive(path,value):
 with path.open('xb')as stream:stream.write(raw_json(value))


def verify_pins(root,path):
 pins=json.loads(path.read_bytes());need(type(pins)is dict and 1<=len(pins)<=4096,'Pinned source/data inventory bound')
 for rel,item in pins.items():
  target=root/rel;need(type(rel)is str and not Path(rel).is_absolute()and '..'not in Path(rel).parts and target.resolve().is_relative_to(root.resolve())and target.is_file()and not target.is_symlink(),'Pinned input path')
  need(target.stat().st_size==item['bytes']<=2*1024*1024 if root.name=='contracts'else target.stat().st_size==item['bytes']<=16*1024*1024,'Pinned input size')
  need(sha(target.read_bytes())==item['sha256'],'Pinned input bytes changed')
 return pins


def main():
 parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 source=args.source_root;out=args.output;helper=Path(__file__).resolve().parent;data=helper/'data'
 need(os.name=='posix'and os.getuid()==65534 and source==EXPECTED/'source/contracts'and out==EXPECTED/'runtime/run-001/history'and helper==EXPECTED/'source/helpers','Fixed unprivileged owned Linux unit paths')
 need(os.environ.get('POPL_LAB_HOST_NETWORK_NAMESPACE','').startswith('net:[')and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private network namespace required')
 out.mkdir(parents=True,exist_ok=False);inputs=out/'inputs';inputs.mkdir()
 source_pins=verify_pins(source,helper/'SOURCE_PINS.json');data_pins=verify_pins(data,helper/'DATA_PINS.json')
 sys.path.insert(0,str(source));sys.path.insert(0,str(helper))
 import preserved_fixture as fixture
 from frontend_api.service import Projection
 from frontend_api.earnings_checkpoint import decode,source_identity
 from frontend_api.earnings_checkpoint_v3 import sources
 from tests_python.test_earnings_checkpoint_prefix_import import prefix_configuration
 result=dict(schema=1,scope=__doc__,success=False,source_files=len(source_pins),data_files=len(data_pins),network_performed=False,stock_HTTP_provider_admission=False,original_case_repeated=False,old_test_methods_run=0,old_wallet_journeys_run=0,public_transactions=0,signing=False,sealing=False,installed=False,production_approved=False,stages=[])
 started=time.monotonic();case=unittest.TestCase()
 def no_network(*args,**kwargs):raise AssertionError('All socket connections forbidden in this offline unit')
 def cli(name,script,args,projection=None):
  need(time.monotonic()-started<300,'Aggregate offline workload deadline')
  call=runpy.run_path(str(source/'scripts'/script),run_name='popl_offline_cli')['main']
  if projection is not None:call.__globals__['Projection']=projection
  stdout,stderr=io.StringIO(),io.StringIO();began=time.monotonic()
  with redirect_stdout(stdout),redirect_stderr(stderr):code=call(list(map(str,args)))
  a,b=stdout.getvalue().encode(),stderr.getvalue().encode();need(len(a)+len(b)<=65536,'CLI capture bound')
  (out/(name+'.stdout')).write_bytes(a);(out/(name+'.stderr')).write_bytes(b)
  result['stages'].append(dict(name=name,exit_code=code,elapsed_seconds=time.monotonic()-began,stdout_bytes=len(a),stderr_bytes=len(b)))
  (out/'PROGRESS.json').write_bytes(raw_json(result));need(code==0,'Current CLI refused at '+name)
 try:
  with patch.object(socket.socket,'connect',no_network):
   from negative_import import run as negative_run
   result['same_graph_negative']=negative_run(source,out)
   need(result['same_graph_negative']['success']is True,'Previously unexecuted standalone negative partition refused')
   f=fixture.hydrate(data,inputs,case)
   result.update(nft_count=1000,active_count=900,epochs=3,input_raw_tables=[fixture.tables(inputs/f'epoch-{n}.sqlite')for n in range(3)])
   prefix=data/'current-prefix.json';reference=data/'current-checkpoint.json';need(json.loads(prefix.read_bytes())['sources']==source_identity(2)and json.loads(reference.read_bytes())['sources']==sources(),'Current input semantic source maps')
   with ExitStack()as stack:
    for name,method in (('_verify_deployment',f.verify),('_admitted',f.admitted),('_call',f.read_call)):
     def wrapper(p,*a,_method=method,**kw):return _method(p,*a,**kw)
     stack.enter_context(patch.object(Projection,name,wrapper))
    # New graph length2 is a prefix, not a relabelled three-epoch checkpoint.
    config2=out/'two-epoch-config.json';exclusive(config2,prefix_configuration(f,1));f.safe=220;f.head=231
    prefix2=out/'two-epoch-prefix.json';review2=out/'two-epoch-review.json'
    limits=['--max-seconds',120,'--max-calls',65536,'--max-posts',65536]
    cli('new-two-epoch-prefix','import-earnings-checkpoint.py',['--config',config2,'--prefix',prefix,'--prefix-sha256',sha(prefix.read_bytes()),'--block',161,'--output',prefix2,'--review-output',review2,*limits],f.projection)
    two=json.loads(prefix2.read_bytes());two_review=json.loads(review2.read_bytes());need(two['schema']==3 and two['sources']==sources()and two_review['target_graph_length']==2 and len(two_review['appended_handoffs'])==1,'New two-epoch prefix/source proof')
    f.safe=299;f.head=310;config3=out/'three-epoch-config.json';exclusive(config3,f.config);candidate=out/'three-epoch-checkpoint.json';review3=out/'three-epoch-review.json'
    cli('NEW-schema3-two-to-three','import-earnings-checkpoint.py',['--config',config3,'--prefix',prefix2,'--prefix-sha256',sha(prefix2.read_bytes()),'--block',161,'--output',candidate,'--review-output',review3,*limits],f.projection)
    final=json.loads(candidate.read_bytes());review=json.loads(review3.read_bytes())
    need(final['schema']==3 and final['sources']==sources()and review['prefix_schema']==3 and review['prefix_graph_length']==2 and review['target_graph_length']==3 and len(review['appended_handoffs'])==1,'Actual schema3 branch/handoff/source proof')
    need(review['earliest_served_timestamp']==decode(final['anchor'])['timestamp']+86400<=f.timestamp(f.safe),'Full 86400s window')
    expected=decode(json.loads(reference.read_bytes())['state']);actual=decode(final['state']);provenance=actual['active']['history']['provenance']
    expected_checkpoint=dict(block_hash=decode(two['anchor'])['hash'],block_number=161,sha256=sha(prefix2.read_bytes()),trust='Explicitly reviewed configuration pin; not a log-completeness proof.')
    need(provenance['checkpoint']==expected_checkpoint and provenance['suffix_logs_examined']==0,'New prefix-specific active history provenance')
    expected['active']['history']['provenance']['checkpoint']=expected_checkpoint;expected['active']['history']['provenance']['suffix_logs_examined']=0
    need(expected==actual,'Complete financial/raw state differs beyond exact prefix provenance')
    phases=[phase for tree in actual['active']['exact_lp']['owner_trees'].values()for book in tree['carry']for phase in book.values()]
    need(any(high for high,low in phases)and any(low for high,low in phases),'Full-width nonzero high/low phase')
    cfg=copy.deepcopy(f.config);cfg['earnings_history']['checkpoint']=dict(path=str(candidate),sha256=sha(candidate.read_bytes()));backup_config=out/'backup-config.json';exclusive(backup_config,cfg)
    bundle=out/'bundle';restored=out/'restored';common=['--max-bytes',64*1024*1024,'--max-seconds',120]
    cli('new-history-backup','history-recovery.py',['backup','--config',backup_config,'--review',review3,'--review-sha256',sha(review3.read_bytes()),'--output',bundle,*common])
    manifest=bundle/'manifest.json';pin=sha(manifest.read_bytes())
    cli('new-history-verify','history-recovery.py',['verify','--bundle',bundle,'--manifest-sha256',pin,*common])
    cli('new-history-restore','history-recovery.py',['restore','--bundle',bundle,'--manifest-sha256',pin,'--output',restored,*common])
    cli('new-restored-verify','history-recovery.py',['verify','--bundle',restored,'--manifest-sha256',pin,*common])
    need(json.loads(manifest.read_bytes())['raw_retention']['pruned']is False and [fixture.tables(restored/f'databases/{n:03d}.sqlite')for n in range(3)]==result['input_raw_tables'],'All exact raw rows retained/restored')
    need((restored/'checkpoint.json').read_bytes()==candidate.read_bytes()and(restored/'import-review.json').read_bytes()==review3.read_bytes(),'Restored candidate/review bytes')
    result.update(success=True,current_prefix2_sha256=sha(prefix2.read_bytes()),current_checkpoint3_sha256=sha(candidate.read_bytes()),current_review3_sha256=sha(review3.read_bytes()),manifest_sha256=pin,full_window_seconds=86400,nonzero_high_low_phase=True,whole_state_equal_except_exact_prefix_provenance=True,restored_exact_tables=True,restored_artifact_bytes_exact=True)
 except Exception as exc:result.update(error_class=type(exc).__name__,error=str(exc));raise
 finally:
  case.doCleanups();result['source_pins_unchanged']=verify_pins(source,helper/'SOURCE_PINS.json')==source_pins;result['data_pins_unchanged']=verify_pins(data,helper/'DATA_PINS.json')==data_pins
  if not(result['source_pins_unchanged']and result['data_pins_unchanged']):result['success']=False
  result['elapsed_seconds']=time.monotonic()-started;exclusive(out/'RESULT.json',result)
 print(json.dumps({k:result[k]for k in ('success','elapsed_seconds','source_pins_unchanged','data_pins_unchanged')}))


if __name__=='__main__':main()
