"""Bound this one finite Entry integration and all owned descendants."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args();assert a.attempt.isalnum()
    out=V/'pool-integration-20261120/entry';out.mkdir(parents=True,exist_ok=True)
    target=out/a.attempt;assert not target.exists()
    helper=ROOT/'scripts/run-current-pool-fork.py'
    spec=importlib.util.spec_from_file_location('entry_job_supervisor',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    command=[sys.executable,str(Path(__file__).with_name('run_entry.py')),'--attempt',a.attempt]
    environment={k:v for k,v in os.environ.items()if not any(x in k.upper()for x in('PRIVATE_KEY','MNEMONIC','RPC_URL','RPC_HEADERS','JWT_SECRET'))}
    start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat();proc=None
    prefix=out/(a.attempt+'-supervisor')
    with Path(str(prefix)+'.stdout').open('xb')as stdout,Path(str(prefix)+'.stderr').open('xb')as stderr,open(os.devnull,'rb')as stdin:
        try:
            proc=m._WindowsJobProcess(command,environment,stdin,stdout,stderr);code=proc.wait(1020)
        except subprocess.TimeoutExpired:code=124
        finally:
            if proc:proc.close()
    result={'schema':1,'command':command,'started_utc':started,'elapsed_seconds':time.monotonic()-start,'returncode':code,'whole_process_tree_bound_seconds':1020,'job_helper_sha256':sha(helper),'runner_sha256':sha(Path(__file__).with_name('run_entry.py')),'stdout_sha256':sha(str(prefix)+'.stdout'),'stderr_sha256':sha(str(prefix)+'.stderr'),'production_approved':False,'unchanged_tests_rerun':False}
    with Path(str(prefix)+'.json').open('x',encoding='utf8')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result));return code
if __name__=='__main__':raise SystemExit(main())
