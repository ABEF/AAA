"""Publish exact finite newly frozen source records;0EVM executions and no state adoption.

The standard solid tar.xz retains every original state export byte while avoiding
13 duplicate compressed VM images. Archive validation never extracts a path.
"""
from pathlib import Path
import gzip,hashlib,io,json,lzma,tarfile

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-gas-20261118')
D=P/'full-flow-final'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
 D.mkdir(exist_ok=True);files=[]
 def put(name,raw,*,compressed=False):
  dest=D/name;dest.parent.mkdir(parents=True,exist_ok=True)
  stored=gzip.compress(raw,mtime=0)if compressed else raw
  if dest.exists():assert dest.read_bytes()==stored,('Existing evidence differs',name)
  else:dest.write_bytes(stored)
  files.append({'file':name,'sha256':sha(stored),'bytes':len(stored),'original_sha256':sha(raw),'original_bytes':len(raw),'additional_gzip_applied':compressed})
 def copy(name,*,compressed=False):put(name+('.gz'if compressed else''),(V/name).read_bytes(),compressed=compressed)
 result=json.loads((V/'full01/EXECUTION.json').read_bytes());summary=json.loads((V/'full01/local-rpc/SUMMARY.json').read_bytes())
 assert result['pass']and result['source_bracket_stable']and result['base_config_unchanged']and result['compiled_source_metadata_verified']
 assert len(result['methods'])==1 and summary['completed_cases']==13 and summary['verification_complete']
 assert len(summary['meets_20m_cases'])+len(summary['fails_20m_cases'])==13
 assert all(row['production_trace_measurement_verified']and row['royalty_trace_verification']['verified']and row['owned_node_stopped']for row in summary['results'])
 start=json.loads((V/'full01/START.json').read_bytes());checker=json.loads((V/'full01/local-rpc/CHECKER_START.json').read_bytes())
 for name,pin in [('run_full_flow.py',start['runner_sha256']),('verify_full_flow.py',checker['checker_sha256'])]:
  raw=(P/name).read_bytes();assert sha(raw)==pin;put('source-helpers/'+name,raw)
 for name in ['EXECUTION.json','START.json','SOURCE_TEST.sol.txt','COMPILED_INPUT_SOURCE_POOL.json.gz',
              'PRODUCER.json','PID.json','HARNESS_RESOURCES.json','foundry.toml','ORIGINAL_foundry.toml',
              'BASELINE_COMPARISON.json','stderr.log']:
  copy('full01/'+name)
 for name in ['raw.json','producer-artifact.json']:copy('full01/'+name,compressed=True)
 for name in ['CHECKER_START.json','SUMMARY.json']:copy('full01/local-rpc/'+name)
 for folder in sorted((V/'full01/local-rpc').iterdir()):
  if folder.is_dir():
   for name in ['VERIFICATION.json','rpc-records.json.gz','anvil.log']:copy(folder.relative_to(V).as_posix()+'/'+name)
 for stage in ['full01-compile01']:
  for name in ['START.json','RESULT.json','stdout.log','stderr.log','SOURCE_POOL.json.gz']:
   if(V/stage/name).is_file():copy(stage+'/'+name)
 for name in ['SOURCE_FREEZE.json','NORMAL_BINDING.json','RUN_WINDOW.json','FULL_COMPILE_INVENTORY.json','NONSELECTED_TEST_MAINTENANCE.json','PROVEN_RUNNER_ADOPTION.json','RESOLVED_REMAPPINGS.json']:
  copy(name)
 for stage in ['owned-config-preflight01','owned-config-preflight02','owned-config-preflight03','owned-config-preflight04']:
  for name in ['NO_EXECUTION.json','START.json','EXECUTION.json','BASELINE_EFFECTIVE_CONFIG.json','OWNED_EFFECTIVE_CONFIG.json','OWNED_CONFIG_PREFLIGHT.json','foundry.toml','ORIGINAL_foundry.toml','PID.json','HARNESS_RESOURCES.json','stderr.log','raw.json']:
   if(V/stage/name).is_file():copy(stage+'/'+name)
 for name in ['original-run-full-flow.py','first-owned-runner.py','last-owned-runner.py','last-owned-run-window.json']:
  if(V/'owned-config-adoption'/name).is_file():copy('owned-config-adoption/'+name)
 entries=[];total=0
 for source in sorted((V/'full01/exports').iterdir()):
  assert source.is_file()and source.suffix=='.json'
  raw=source.read_bytes();assert len(raw)<=20*1024*1024
  entries.append({'name':'exports/'+source.name,'bytes':len(raw),'sha256':sha(raw)});total+=len(raw)
 assert len(entries)==14 and total<=256*1024*1024
 archive=D/'full01/exports.tar.xz';assert not archive.exists(),'Use a new publication stage rather than replace an archive'
 with lzma.open(archive,'wb',filters=[{'id':lzma.FILTER_LZMA2,'dict_size':64*1024*1024,'preset':6}])as packed:
  with tarfile.open(fileobj=packed,mode='w|',format=tarfile.USTAR_FORMAT)as tar:
   for row in entries:
    raw=(V/'full01'/row['name']).read_bytes();info=tarfile.TarInfo(row['name']);info.size=len(raw);info.mode=0o644;info.mtime=0
    tar.addfile(info,io.BytesIO(raw))
 # Check all actual archive members and original bytes without extraction.
 remaining={row['name']:row for row in entries};observed=0
 with tarfile.open(archive,'r|xz')as tar:
  for member in tar:
   assert member.isfile()and member.name in remaining
   row=remaining.pop(member.name);assert member.size==row['bytes']
   stream=tar.extractfile(member);assert stream is not None
   raw=stream.read(20*1024*1024+1);assert len(raw)==row['bytes']and sha(raw)==row['sha256'];observed+=1
 assert not remaining and observed==14
 raw=archive.read_bytes();files.append({'file':archive.relative_to(D).as_posix(),'sha256':sha(raw),'bytes':len(raw),'format':'standard tar.xz','verified_members':entries,'original_bytes':total,'extraction_performed':False})
 manifest={'schema':1,'scope':'Explicitly frozen fresh1,000NFT/999Entry setup; one affected existing method,13cold exported cases. Not13tests or universal max-state/market qualification.',
  'source_method_count':1,'cold_case_count':13,'diagnostic_results_do_not_admit_failed20m_profiles':True,'actual20m_calls_succeeded':sum(row['actual_20m_call']['ok']for row in summary['results']),'full20pct_profile_passes':len(summary['meets_20m_cases']),'full20pct_profile_refusals':len(summary['fails_20m_cases']),
  'unchanged_old_tests_executed':0,'public_transactions':0,'production_approved':False,'files':files}
 put('MANIFEST.json',(json.dumps(manifest,indent=2)+'\n').encode())
 print(json.dumps({'files_excluding_manifest':len(files)-1,'export_archive_bytes':len(archive.read_bytes()),'export_original_bytes':total,
                   'evidence_bytes':sum(row['bytes']for row in files),'all14original_exports_verified':True,'new_executions':0}),flush=True)
if __name__=='__main__':main()
