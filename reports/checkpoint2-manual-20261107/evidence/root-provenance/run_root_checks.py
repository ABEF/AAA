from pathlib import Path
import subprocess,sys,json,hashlib,time
R=Path.cwd();E=Path(__file__).parent;D=E/('root-tests-'+sys.argv[1]);D.mkdir(exist_ok=False)
mods=sys.argv[2:]
before={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for folder in ('frontend_api','zzz_ops')for p in Path(folder).glob('*.py')}
t=time.monotonic();run=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','-v',*mods],capture_output=True,cwd=R)
(D/'stdout.txt').write_bytes(run.stdout);(D/'stderr.txt').write_bytes(run.stderr)
after={p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in before}
v=dict(modules=mods,exit_code=run.returncode,elapsed=time.monotonic()-t,before=before,after=after)
(D/'status.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(dict(directory=str(D),exit_code=run.returncode,elapsed=v['elapsed'],source_drift=[p for p in before if before[p]!=after[p]],tail=run.stderr.decode('utf-8','replace')[-3500:])))
