"""Capture one public Anvil startup read on an owned private diagnostic port."""
from pathlib import Path
import importlib.util
import subprocess
ROOT=Path(__file__).resolve().parents[3]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121')
spec=importlib.util.spec_from_file_location('strict',ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
INNER=r'''
import http.server,json,threading,subprocess,os,time
lab='/opt/popl-ubuntu-20261121-c8876a3a';rows=[]
class H(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  n=int(self.headers.get('Content-Length','0'));assert 0<n<8192
  raw=self.rfile.read(n);obj=json.loads(raw)
  assert obj.get('method')in('eth_chainId','eth_getBlockByNumber')
  rows.append(obj);b=b'{"jsonrpc":"2.0","id":0,"error":{"code":-32070,"message":"bounded startup diagnostic"}}'
  self.send_response(200);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
s=http.server.HTTPServer(('127.0.0.1',18549),H);s.timeout=.2
p=subprocess.Popen([lab+'/bin/anvil','--host','127.0.0.1','--port','18550','--chain-id','4663','--fork-url','http://127.0.0.1:18549','--fork-block-number','119107223','--accounts','0','--no-storage-caching','--silent'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
try:
 end=time.monotonic()+6
 while not rows and p.poll()is None and time.monotonic()<end:s.handle_request()
finally:
 if p.poll()is None:p.terminate()
 try:_,err=p.communicate(timeout=3)
 except subprocess.TimeoutExpired:p.kill();_,err=p.communicate()
 s.server_close()
print(json.dumps({'requests':rows,'Anvil_exit':p.returncode,'stderr':err.decode()[:1000],'signing':False}))
'''
CODE="import subprocess,json\np=subprocess.run(['systemctl','show','popl-ubuntu-20261121-c8876a3a-cache.service','-p','MainPID','--value'],capture_output=True,text=True,check=True);pid=int(p.stdout);assert pid>1\nr=subprocess.run(['nsenter','--target',str(pid),'--net','--setuid','65534','--setgid','65534','python3','-c',"+repr(INNER)+"],capture_output=True,timeout=12);print(r.stdout.decode());assert r.returncode==0\n"
r=subprocess.run([*T.ssh(),'python3','-'],input=CODE.encode(),capture_output=True,timeout=25)
(V/'run/start-preflight-01/STARTUP_WIRE.json').write_bytes(r.stdout)
assert r.returncode==0,r.stderr.decode()
print(r.stdout.decode())
