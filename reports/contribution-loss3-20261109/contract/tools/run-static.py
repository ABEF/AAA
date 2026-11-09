from pathlib import Path
import collections,datetime,hashlib,json,os,subprocess,sys,time,uuid
R=Path.cwd();E=Path(__file__).resolve().parent;V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
normal=Path(sys.argv[1]);D=E/('static-'+uuid.uuid4().hex[:10]);D.mkdir()
build=json.loads((normal/'production-size-gates.json').read_text());assert build['all_pass']
inp=json.loads((normal/'compiler-input.json').read_text());out=json.loads((normal/'compiler-output.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tracked=sorted([p.relative_to(R).as_posix() for p in (R/'src').rglob('*.sol')]+['foundry.toml','package-lock.json','slither.config.json'])
before={f:sha(R/f) for f in tracked}
for f,h in {**build['source_sha256'],**build['dependency_source_sha256']}.items():assert sha(R/f)==h,f
(D/'build-info').mkdir();(D/'out').mkdir()
bid=sha(normal/'compiler-input.json')[:16]
info={'id':bid,'source_id_to_path':{str(x['id']):p for p,x in out['sources'].items()},'language':'Solidity',
 '_format':'ethers-rs-sol-build-info-1','input':inp,'output':out,'solcVersion':'0.8.26','solcLongVersion':'0.8.26'}
bi=D/'build-info'/(bid+'.json');bi.write_text(json.dumps(info,separators=(',',':')))
python=V/'production-readiness-20261014/slither-venv/Scripts/python.exe'
forge=V/'foundry-v1.4.4/forge.exe'
cmd=[str(python),'-B','-X','utf8','-m','slither','.',
 '--foundry-ignore-compile','--foundry-out-directory',str(D/'out'),
 '--foundry-build-info-directory',str(D/'build-info'),'--config-file',str(R/'slither.config.json'),
 '--json',str(D/'slither.json'),'--json-types','detectors,compilations','--disable-color']
keep=('SystemRoot','WINDIR','SystemDrive','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','HOMEDRIVE','HOMEPATH')
env={k:os.environ[k] for k in keep if k in os.environ}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPYCACHEPREFIX=str(D/'unused-pycache'),FOUNDRY_OFFLINE='true')
env['PATH']=str(forge.parent)+os.pathsep+str(V/'toolchain-0.8.26')+os.pathsep+str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32')
record={'kind':'Actual offline Slither using final closed normal compiler output; no recompile',
 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,
 'normal_directory':str(normal),'source_before':before,'compiler_input_sha256':sha(normal/'compiler-input.json'),
 'compiler_output_sha256':sha(normal/'compiler-output.json'),'build_info_sha256':sha(bi),
 'python_sha256':sha(python),'forge_sha256':sha(forge),'credentials_inherited':False,
 'normal_limits_relaxed':False,'compiler_invoked':False,'production_approved':False}
(D/'START.json').write_text(json.dumps(record,indent=2)+'\n')
start=time.monotonic()
with (D/'slither.log').open('wb') as log:
    proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:code=proc.wait(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait();(D/'TIMEOUT.json').write_text(json.dumps({'owned_pid':proc.pid,'timeout':300,'not_a_pass':True}));raise
raw=json.loads((D/'slither.json').read_text());findings=raw.get('results',{}).get('detectors',[])
(D/'detectors-only.json').write_text(json.dumps({'success':raw.get('success'),'error':raw.get('error'),
 'results':{'detectors':findings}},indent=2)+'\n')
after={f:sha(R/f) for f in tracked}
record.update(analyzer_exit_code=code,elapsed_seconds=round(time.monotonic()-start,3),
 finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_after=after,
 source_unchanged=before==after,analyzer_success=raw.get('success'),analyzer_error=raw.get('error'),
 detector_count=len(findings),by_detector=dict(collections.Counter(f['check'] for f in findings)),
 by_impact=dict(collections.Counter(f['impact'] for f in findings)),raw_report_sha256=sha(D/'slither.json'),
 raw_log_sha256=sha(D/'slither.log'))
(D/'EXECUTION.json').write_text(json.dumps(record,indent=2)+'\n')
print(str(D));print(json.dumps({k:record[k] for k in ['source_unchanged','analyzer_success','analyzer_exit_code','detector_count']}))
raise SystemExit(0 if record['source_unchanged'] and record['analyzer_success'] else 1)
