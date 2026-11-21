"""Read-only diagnostics restricted to this campaign's new lab, no secrets."""
from pathlib import Path
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
V = Path("C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121")
spec = importlib.util.spec_from_file_location("lab_transport", ROOT / "reports/ubuntu-keeper-20261121/transport/strict_transport.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
CODE = r'''
import pathlib,subprocess,json
lab=pathlib.Path('/opt/popl-ubuntu-20261121-c8876a3a')
result={}
for name in ('cache','anvil','proxy','keeper'):
 unit=lab.name+'-'+name+'.service'
 p=subprocess.run(['systemctl','show',unit,'-p','LoadState','-p','ActiveState','-p','MainPID','-p','Result','-p','ExecMainStatus','-p','ExecStart','-p','PrivateNetwork','-p','JoinsNamespaceOf'],capture_output=True,text=True,timeout=10)
 result[name]={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 if name=='cache':
  props=dict(x.split('=',1)for x in p.stdout.splitlines()if'='in x);pid=int(props.get('MainPID','0'))
  if pid>1:
   q=subprocess.run(['nsenter','--target',str(pid),'--net','--setuid','65534','--setgid','65534','python3','-c',"import http.client; c=http.client.HTTPConnection('127.0.0.1',18545,timeout=3); c.request('POST','/',b'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_chainId\",\"params\":[]}',{'Content-Type':'application/json'});r=c.getresponse();print(r.status,r.read().decode())"],capture_output=True,text=True,timeout=7)
   result['readonly_chain_probe']={'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr}
for rel in ('logs/preflight-cache.log','evidence/preflight-cache/events.jsonl'):
 path=lab/rel
 if path.exists():result[rel]=path.read_text()[-30000:]
print(json.dumps(result,indent=2))
'''
r = subprocess.run([*t.ssh(), "python3", "-"], input=CODE.encode(), capture_output=True, timeout=60)
out = V / "run/start-preflight-01/DIAGNOSTIC.json"
out.write_bytes(r.stdout)
assert r.returncode == 0
print(r.stdout.decode())
