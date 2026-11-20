"""Bound exactly this new runner and its owned descendants with a Windows job."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[3]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
OUT=V/'pool-lifecycle-20261120/run'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    source=ROOT/'scripts/run-current-pool-fork.py'
    spec=importlib.util.spec_from_file_location('owned_process_job',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    command=[sys.executable,str(Path(__file__).with_name('run_pool.py'))]
    environment={k:v for k,v in os.environ.items()if not any(x in k.upper()for x in('PRIVATE_KEY','MNEMONIC','RPC_URL','RPC_HEADERS','JWT_SECRET'))}
    start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat();process=None
    with (OUT/'driver04.stdout').open('xb')as stdout,(OUT/'driver04.stderr').open('xb')as stderr,open(os.devnull,'rb')as stdin:
        try:
            process=module._WindowsJobProcess(command,environment,stdin,stdout,stderr)
            code=process.wait(1020)
        except subprocess.TimeoutExpired:code=124
        finally:
            if process:process.close()
    receipt={'schema':1,'command':command,'started_utc':started,'elapsed_seconds':time.monotonic()-start,'returncode':code,
        'supervisor':'Windows kill-on-close job,1020s whole process-tree bound','supervisor_helper_sha256':sha(source.read_bytes()),
        'runner_sha256':sha(Path(__file__).with_name('run_pool.py').read_bytes()),'cache_helper_sha256':sha(Path(__file__).with_name('warm_cache.py').read_bytes()),
        'stdout_sha256':sha((OUT/'driver04.stdout').read_bytes()),'stderr_sha256':sha((OUT/'driver04.stderr').read_bytes()),
        'unchanged_tests_rerun':False,'production_approved':False}
    with (OUT/'EXECUTION04.json').open('x',encoding='utf8',newline='\n')as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt));return code
if __name__=='__main__':raise SystemExit(main())
