"""ONLY unexecuted c7ee state validation and four offline recovery stages.

The original c7ee false result/source/artifacts stay unchanged. Both importer
stages are reused, never rerun. Six observed differences must match the exact
new prefix Seed provenance, with every other decoded financial/raw field equal.
"""
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
import argparse,copy,hashlib,json,os,socket,sqlite3,sys,time
from unittest.mock import patch
LAB=Path('/opt/popl-ubuntu-features-20261124-c7f2')
OLD=Path('/opt/popl-ubuntu-features-20261124-c7ee')
SOURCE=OLD/'source/contracts';DATA=OLD/'source/helpers/data';PRIOR=OLD/'runtime/run-001/history'
PINS={'result':(PRIOR/'RESULT.json','5e72b7f64d1a943b63ec5f2f3a209f5a4ffe91d8528055c22bd003bb9fa2698f',2933),
'prefix2':(PRIOR/'two-epoch-prefix.json','0cbc526d54791249de03915e2f8c8f35d9bf51961e74410679a2b25c85db454e',2428908),
'candidate':(PRIOR/'three-epoch-checkpoint.json','90b354c9bf31e0a591128ea4520902ec963e84add30fbe608d5a6e515d048ee3',2435584),
'reference':(DATA/'current-checkpoint.json','3aa212be10e7f0bbc0c9552d7a4b14c99d583aa469145206d2c5358076405cd3',2435248),
'prefix1':(DATA/'current-prefix.json','f105958bac8a54566c7e67c44bb51594ebc4ab94c9e461c239ef9a1342415049',2273168),
'review2':(PRIOR/'two-epoch-review.json','0cd55a1c662d8ea6614e890737262986e3a39e07a092c0e49305a6de170bf9c7',16707),
'review3':(PRIOR/'three-epoch-review.json','472659deb39a970d4ab170a266e0cb25b996c923eae0ab4bd8924e8564221713',22578)}
SOURCE_PINS_SHA='1c7b060b510a26e4fc58f4897bda6cfad016373afcaee010fdd596d13cecaa41'


def need(ok,message):
 if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encode(value):return(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def write(path,value):
 with path.open('xb')as stream:stream.write(encode(value))


def read(path,maximum=32*1024*1024):
 need(path.resolve()==path and path.is_file()and not path.is_symlink()and path.stat().st_size<=maximum,'Fixed input file path/bound')
 return path.read_bytes()


def source_check():
 raw=read(OLD/'source/helpers/SOURCE_PINS.json',1024*1024);need(sha(raw)==SOURCE_PINS_SHA,'Prior source pins changed');pins=json.loads(raw)
 need(len(pins)==489,'Copied source inventory differs')
 for rel,item in pins.items():
  path=SOURCE/rel;raw=read(path,2*1024*1024);need(len(raw)==item['bytes']and sha(raw)==item['sha256'],'Prior source member changed')
 return pins


def tables(path):
 connection=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  need(connection.execute('PRAGMA integrity_check').fetchone()==('ok',),'Copied/restored database integrity')
  return{t:dict(rows=len(rows),sha256=sha(encode(rows)))for t in('cursors','blocks','logs')for rows in[connection.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall()]}
 finally:connection.close()


def main():
 parser=argparse.ArgumentParser(allow_abbrev=False);parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 need(os.name=='posix'and os.getuid()==65534 and args.source_root==SOURCE and args.output==LAB/'runtime/run-001/history'and Path(__file__).resolve().parent==LAB/'source/helpers','Fixed unprivileged continuation paths')
 need(os.environ.get('POPL_LAB_HOST_NETWORK_NAMESPACE','').startswith('net:[')and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'New private network namespace required')
 out=args.output;out.mkdir(parents=True,exist_ok=False);inputs=out/'inputs';inputs.mkdir();(out/'tmp').mkdir()
 sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
 from frontend_api.earnings_checkpoint import decode,source_identity
 from frontend_api.earnings_checkpoint_v3 import sources
 from frontend_api.earnings_checkpoint_import import _bind_review,producer_sources
 from keeper.cast_process import run_cast
 initial_source=source_check();raws={};original_paths={}
 for name,(path,digest,size)in PINS.items():
  raw=read(path);need(len(raw)==size and sha(raw)==digest,'Prior reviewed artifact pin changed');raws[name]=raw;original_paths[path]=digest
 old_source_pins=json.loads(read(OLD/'source/helpers/DATA_PINS.json',1024*1024))
 for n in range(3):
  rel=f'fixture-001/epoch-{n}.sqlite';path=DATA/rel;raw=read(path,16*1024*1024);need(sha(raw)==old_source_pins[rel]['sha256']and len(raw)==old_source_pins[rel]['bytes'],'Prior complete raw DB differs')
  need(all(not Path(str(path)+suffix).exists()for suffix in('-wal','-shm','-journal')),'Prior immutable data has unexpected sidecars');original_paths[path]=sha(raw)
  with(inputs/f'epoch-{n}.sqlite').open('xb')as stream:stream.write(raw)
 result=dict(schema=1,scope=__doc__,success=False,no_importer_or_builder_rerun=True,no_stock_keeper_indexer_rerun=True,no_network=True,old_test_methods_run=0,old_wallet_journeys_run=0,public_transactions=0,signing=False,sealing=False,installed=False,production_approved=False,stages=[])
 began=time.monotonic();stage='precise_state_validation'
 def forbidden(*args,**kwargs):raise AssertionError('All connections forbidden in offline continuation')
 def cli(name,argv):
  remaining=300-(time.monotonic()-began);need(remaining>0,'Continuation aggregate deadline');start=time.monotonic()
  env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONPATH':str(SOURCE),'TMPDIR':str(out/'tmp')}
  r=run_cast([sys.executable,'-B',str(SOURCE/'scripts/history-recovery.py'),*map(str,argv)],env=env,timeout=min(120,remaining))
  for label,value in(('stdout',r.stdout),('stderr',r.stderr)):
   with(out/(name+'.'+label)).open('x',encoding='utf-8')as stream:stream.write(value)
  result['stages'].append(dict(name=name,exit_code=r.returncode,elapsed_seconds=time.monotonic()-start,stdout_bytes=len(r.stdout.encode()),stderr_bytes=len(r.stderr.encode())));(out/'PROGRESS.json').write_bytes(encode(result));need(r.returncode==0,'Unexecuted recovery stage refused')
 try:
  with patch.object(socket.socket,'connect',forbidden):
   prior=json.loads(raws['result']);need(prior['success']is False and prior['same_graph_negative']['success']is True and len(prior['stages'])==2 and all(row['exit_code']==0 for row in prior['stages']),'Preserved c7ee partial results differ')
   prefix1,prefix2,candidate,reference=(json.loads(raws[k])for k in('prefix1','prefix2','candidate','reference'));review2,review3=(json.loads(raws[k])for k in('review2','review3'))
   need(prefix1['sources']==source_identity(2)and prefix2['sources']==candidate['sources']==reference['sources']==sources(),'Current exact semantic sources differ')
   need(review2['producer_sources']==review3['producer_sources']==producer_sources(),'Actual importer producer source identity differs');_bind_review(prefix2,review2);_bind_review(candidate,review3)
   need(review2['prefix_sha256']==PINS['prefix1'][1]and review2['target_graph_length']==2 and len(review2['appended_handoffs'])==1 and review3['prefix_schema']==3 and review3['prefix_sha256']==PINS['prefix2'][1]and review3['prefix_graph_length']==2 and review3['target_graph_length']==3 and len(review3['appended_handoffs'])==1,'Reviewed graph provenance differs')
   p=decode(prefix2['state']);a=decode(reference['state']);b=decode(candidate['state']);need(p['cursor']==a['cursor']==b['cursor']==1 and len(p['completed'])==len(a['completed'])==len(b['completed'])==1,'Exact epoch cursor differs')
   retired=p['completed'][0]['anchor'];active=decode(prefix2['anchor']);handoff=review2['appended_handoffs'][0]
   need(retired==a['completed'][0]['anchor']==b['completed'][0]['anchor']and retired['number']==140 and handoff['block_number']==retired['number']and handoff['block_hash']==retired['hash']and handoff['timestamp']==retired['timestamp'],'Completed cutoff is not the authenticated first handoff')
   need(active==decode(candidate['anchor'])==decode(reference['anchor'])and active['number']==161 and review3['input_anchor']==active and review3['target_anchor']==active,'Active imported anchor differs')
   trust='Explicitly reviewed configuration pin; not a log-completeness proof.'
   for row,anchor in((a['active'],active),(a['completed'][0],retired)):
    row['history']['provenance']['checkpoint']=dict(block_number=anchor['number'],block_hash=anchor['hash'],sha256=PINS['prefix2'][1],trust=trust);row['history']['provenance']['suffix_logs_examined']=0
   need(a==b,'Other decoded financial/raw state differs beyond exactly authenticated Seed provenance')
   phases=[phase for tree in b['active']['exact_lp']['owner_trees'].values()for book in tree['carry']for phase in book.values()];need(any(high for high,low in phases)and any(low for high,low in phases),'Nonzero exact high/low phase omitted')
   need(review3['earliest_served_timestamp']==active['timestamp']+86400<=1000000+299*1200,'Full86400s suffix not retained')
   result.update(all_decoded_state_exact_except_six_authenticated_provenance_differences=True,normalization_source='LineageCheckpoint.snapshot supplies Seed(prefix2 digest, local completed cutoff or active anchor); History._read records new checkpoint and suffix0',active_anchor=active,completed_anchor=retired,prefix2_sha256=PINS['prefix2'][1],checkpoint_sha256=PINS['candidate'][1],review_sha256=PINS['review3'][1],full_window_seconds=86400,nonzero_high_low_phase=True)
   stage='prepare_new_backup_copy';cfg_path=PRIOR/'three-epoch-config.json';cfg_raw=read(cfg_path,1024*1024);original_paths[cfg_path]=sha(cfg_raw);cfg=json.loads(cfg_raw)
   need(sha(json.dumps({k:v for k,v in cfg.items()if k!='rpc_urls'},sort_keys=True,separators=(',',':')).encode())==review3['target_configuration_sha256'],'Original reviewed configuration identity differs')
   for n,c in enumerate(cfg['predecessors']+[cfg]):need(c['history']['database']==str(PRIOR/f'inputs/epoch-{n}.sqlite'),'Original source DB path differs');c['history']['database']=str(inputs/f'epoch-{n}.sqlite')
   cp=inputs/'checkpoint.json';review=inputs/'import-review.json'
   with cp.open('xb')as stream:stream.write(raws['candidate'])
   with review.open('xb')as stream:stream.write(raws['review3'])
   cfg['earnings_history']['checkpoint']=dict(path=str(cp),sha256=PINS['candidate'][1]);config=out/'backup-config.json';write(config,cfg);raw_tables=[tables(inputs/f'epoch-{n}.sqlite')for n in range(3)]
   common=['--max-bytes',64*1024*1024,'--max-seconds',120];bundle=out/'bundle';restored=out/'restored'
   stage='backup';cli('backup',['backup','--config',config,'--review',review,'--review-sha256',PINS['review3'][1],'--output',bundle,*common]);manifest_raw=read(bundle/'manifest.json',1024*1024);pin=sha(manifest_raw)
   stage='verify';cli('verify',['verify','--bundle',bundle,'--manifest-sha256',pin,*common])
   stage='restore';cli('restore',['restore','--bundle',bundle,'--manifest-sha256',pin,'--output',restored,*common])
   stage='restored_verify';cli('restored-verify',['verify','--bundle',restored,'--manifest-sha256',pin,*common])
   manifest=json.loads(manifest_raw);need(manifest['raw_retention']['pruned']is False and manifest['raw_retention']['window_seconds']==86400 and manifest['checkpoint']['earliest_served_timestamp']==active['timestamp']+86400<=manifest['databases'][-1]['snapshot']['tip']['timestamp'],'Manifest full suffix/retention differs')
   need([tables(restored/f'databases/{n:03d}.sqlite')for n in range(3)]==raw_tables==prior['input_raw_tables'],'Every restored raw table does not match original cohort')
   need(read(restored/'checkpoint.json')==raws['candidate']and read(restored/'import-review.json')==raws['review3'],'Restored checkpoint/review bytes differ')
   result.update(success=True,nft_count=1000,active_count=900,epochs=3,all_restored_raw_tables_exact=True,all_restored_phase_and_review_bytes_exact=True,manifest_sha256=pin,raw_table_digests=raw_tables)
 except Exception as exc:result.update(failure_stage=stage,error_class=type(exc).__name__);raise
 finally:
  result['prior_artifacts_unchanged']=all(sha(read(path))==digest for path,digest in original_paths.items());result['prior_source_unchanged']=source_check()==initial_source
  if not(result['prior_artifacts_unchanged']and result['prior_source_unchanged']):result['success']=False
  result['elapsed_seconds']=time.monotonic()-began;write(out/'RESULT.json',result)
 print(json.dumps({k:result[k]for k in('success','elapsed_seconds','prior_artifacts_unchanged','prior_source_unchanged')}))


if __name__=='__main__':main()
