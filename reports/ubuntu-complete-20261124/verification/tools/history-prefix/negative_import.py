"""ONLY the previously unexecuted standalone negative importer CLI partition."""
from pathlib import Path
import copy,hashlib,json,os,sys,time

PRIOR=Path('/opt/popl-ubuntu-features-20261124-c7ed/runtime/run-001/utilities')
RESULT_SHA='3cb045c353dc8124bb9fd5acdbd9009aca0427ea5a9e027b001ff2e05b60ac60'
PINS={'raw.sqlite':'aed6781e5a3214fca0d553000d0ebe2a0937669d86f1d3e62d41936ab7eda091','checkpoint-candidate.json':'861f01fb3f6ca00d99a02b722bf2c434d126ff469ef36958875bab336492bf48','api-checkpoint.json':'b8ab1db98c31b9b18ae4a2cee3df4d3e6a8d5b3cdd4596c00c602504b85c95b0'}


def need(ok,message):
 if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def dump(path,value):
 with path.open('xb')as stream:stream.write((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())


def run(source,out):
 from frontend_api.service import Projection
 from frontend_api.history_recovery import NoNetwork
 from frontend_api.history import HistoryError
 from frontend_api.earnings_checkpoint_import import _ImportedPrefix
 from keeper.cast_process import run_cast
 root=out/'same-graph-negative';root.mkdir();(root/'tmp').mkdir();inputs=root/'inputs';inputs.mkdir()
 prior_result=PRIOR/'RESULT.json';need(prior_result.is_file()and not prior_result.is_symlink()and prior_result.stat().st_size<65536,'Prior utility result identity')
 old_result_raw=prior_result.read_bytes();need(sha(old_result_raw)==RESULT_SHA,'Exact preserved utility failure bytes differ');old=json.loads(old_result_raw)
 need(old.get('success')is False and old.get('failure_stage')=='same_graph_import_refusal'and old.get('error_class')=='HistoryError'and old['indexer']['success']is True and all(old['keeper_state_preserved'].values())and old['old_history_inputs_preserved']is True,'Prior finite outcomes/known negative failure differ')
 history=PRIOR/'history';original_candidates=[history/'import-refused-candidate.json',history/'import-refused-review.json'];need(all(not p.exists()for p in original_candidates),'Prior negative artifacts unexpectedly exist')
 before={};sidecars={};raws={}
 for name,digest in PINS.items():
  original=history/'inputs'/name;need(original.is_file()and not original.is_symlink()and original.stat().st_size<=32*1024*1024,'Preserved input file bounds')
  raw=original.read_bytes();need(sha(raw)==digest,'Preserved input bytes changed');before[name]=digest;raws[name]=raw
  with(inputs/name).open('xb')as stream:stream.write(raw)
 for suffix in ('-wal','-shm','-journal'):
  p=history/'inputs'/('raw.sqlite'+suffix)
  if p.exists():
   need(p.is_file()and not p.is_symlink()and p.stat().st_size<=65536,'Preserved SQLite sidecar shape')
   raw=p.read_bytes();sidecars[suffix]=(len(raw),sha(raw))
   if suffix in ('-wal','-journal'):need(not raw,'Cannot omit nonempty copied WAL/journal')
  else:sidecars[suffix]=None
 result=dict(schema=1,scope=__doc__,success=False,known_original_failure='peers() called outside diagnostic try on a standalone graph',prior_result_sha256=RESULT_SHA,stock_ops_indexer_backup_repeated=False,no_original_journal_read_or_write=True,signing=False,public_transactions=0,sealing=False,production_approved=False)
 try:
  cfg=copy.deepcopy(json.loads(raws['api-checkpoint.json']));cfg['history']['database']=str(inputs/'raw.sqlite');cfg['earnings_history'].pop('checkpoint',None);cfg['rpc_urls']=['http://127.0.0.1:19593'];config=root/'target-config.json';dump(config,cfg)
  projection=Projection(cfg,rpc=NoNetwork());need(projection.lineage is None,'Expected exact standalone graph')
  prefix={'path':str(inputs/'checkpoint-candidate.json'),'sha256':PINS['checkpoint-candidate.json']};expected='Checkpoint3 requires the complete configured lineage';observed=None
  try:_ImportedPrefix(projection.earnings_history,prefix,raws['checkpoint-candidate.json'],json.loads(raws['checkpoint-candidate.json']))
  except HistoryError as exc:observed=str(exc)
  need(observed==expected,'Standalone source precondition differs')
  candidate=root/'refused-candidate.json';review=root/'refused-review.json';environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','PYTHONPATH':str(source),'TMPDIR':str(root/'tmp')}
  start=time.monotonic();r=run_cast([sys.executable,'-B',str(source/'scripts/import-earnings-checkpoint.py'),'--config',str(config),'--prefix',str(inputs/'checkpoint-candidate.json'),'--prefix-sha256',PINS['checkpoint-candidate.json'],'--block','99','--output',str(candidate),'--review-output',str(review)],env=environment,timeout=30)
  for label,value in (('stdout',r.stdout),('stderr',r.stderr)):
   with(root/('cli.'+label)).open('x',encoding='utf-8')as stream:stream.write(value)
  need(r.returncode==1 and 'Checkpoint import failed.'in r.stderr and not candidate.exists()and not review.exists(),'Actual negative CLI failed to refuse without publication')
  result.update(success=True,source_precondition=expected,actual_CLI_exit_code=r.returncode,actual_CLI_seconds=time.monotonic()-start,candidate_published=False,review_published=False)
 finally:
  result['preserved_prior_result_unchanged']=sha(prior_result.read_bytes())==RESULT_SHA
  result['preserved_input_bytes_unchanged']=all(sha((history/'inputs'/name).read_bytes())==digest for name,digest in before.items())
  current={}
  for suffix in sidecars:
   p=history/'inputs'/('raw.sqlite'+suffix);current[suffix]=(p.stat().st_size,sha(p.read_bytes()))if p.exists()else None
  result['preserved_sidecars_unchanged']=current==sidecars;result['prior_candidates_still_absent']=all(not p.exists()for p in original_candidates)
  if not all(result[k]for k in ('preserved_prior_result_unchanged','preserved_input_bytes_unchanged','preserved_sidecars_unchanged','prior_candidates_still_absent')):result['success']=False
  dump(root/'RESULT.json',result)
 return result
