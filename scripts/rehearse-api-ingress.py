"""Isolated real-nginx/loopback rehearsal. No RPC, signer or existing service use."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from frontend_api.admission import ClientAdmission
from frontend_api.server import ReadServer, handler
from frontend_api.activation_server import handler as activation_handler

ORIGIN = 'https://popl.example.test'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nginx', required=True, help='Explicit installed nginx binary')
    parser.add_argument('--output', required=True, help='New external rehearsal directory')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.is_relative_to(ROOT) or output.exists():
        parser.error('output must be a new directory outside the repository')
    binary = Path(args.nginx).resolve(strict=True)
    output.mkdir(parents=True)
    (output/'logs').mkdir()
    (output/'temp').mkdir()
    checks, calls, headers = [], [], []
    gate, entered = threading.Event(), threading.Event()
    hidden = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}

    class Projection:
        def protocol(self):
            calls.append('protocol')
            return {'canonical': True}
        def nft(self, token):
            calls.append(token)
            if token == 1:
                entered.set()
                if not gate.wait(5): raise TimeoutError()
            if token == 13: raise RuntimeError('PRIVATE_UPSTREAM_ERROR')
            return {'token_id': token}
        def prepare(self, payload):
            calls.append(payload)
            return {'unsigned': True}
        def wallet_summary(self, owner, block, offset):
            calls.append(('summary', owner, block, offset))
            return {'scope': 'summary', 'offset': offset}
        def wallet_earnings(self, owner, block, offset):
            calls.append(('earnings', owner, block, offset))
            return {'scope': 'earnings', 'offset': offset}
        def collection(self, block, offset):
            calls.append(('collection', block, offset))
            return {'scope': 'collection', 'offset': offset}

    def observed(factory):
        class Observed(factory(Projection(), Projection())):
            def begin_work(self):
                headers.append(dict(self.headers))
                super().begin_work()
        return Observed

    services = [ReadServer(('127.0.0.1',0),observed(factory),admission=ClientAdmission(),proxy_origin=ORIGIN)
                for factory in (handler, activation_handler)]
    threads = []
    process = None
    runtime_sources = ['frontend_api/admission.py','frontend_api/http_runtime.py','frontend_api/server.py',
                       'frontend_api/activation_server.py','scripts/rehearse-api-ingress.py']
    config_sources = [f'config/nginx/popl-api-{name}.conf' for name in ('http','common','locations')]
    bindings = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in runtime_sources+config_sources}
    # Only adapt ports, include/log paths for isolation. Policy stays unchanged.
    for source in config_sources:
        content = (ROOT/source).read_text()
        content = content.replace('/etc/nginx/popl/', output.as_posix()+'/')
        content = content.replace('/var/log/nginx/', (output/'logs').as_posix()+'/')
        for old, service in zip((8787,8788),services):
            content = content.replace(f'127.0.0.1:{old}',f'127.0.0.1:{service.server_port}')
        (output/Path(source).name).write_text(content,encoding='utf-8')
    with socket.socket() as temporary:
        temporary.bind(('127.0.0.1',0)); port=temporary.getsockname()[1]
    config = output/'nginx.conf'
    config.write_text(f'''daemon off;
worker_processes 1;
pid logs/nginx.pid;
error_log logs/error.log crit;
events {{ worker_connections 128; }}
http {{
  client_body_temp_path temp/client;
  proxy_temp_path temp/proxy;
  fastcgi_temp_path temp/fastcgi;
  uwsgi_temp_path temp/uwsgi;
  scgi_temp_path temp/scgi;
  server_tokens off;
  client_header_timeout 5s;
  large_client_header_buffers 4 8k;
  keepalive_timeout 5s;
  include "{(output/'popl-api-http.conf').as_posix()}";
  server {{
    listen 127.0.0.1:{port};
    server_name 127.0.0.1;
    include "{(output/'popl-api-locations.conf').as_posix()}";
    location / {{ return 404; }}
  }}
}}
''',encoding='utf-8')
    command=[str(binary),'-p',output.as_posix()+'/', '-c',str(config)]
    def require(condition, description):
        if not condition: raise AssertionError(description)
        checks.append(description)
    def request(path='/v1/protocol', method='GET', extra=None, body=None):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=7)
        try:
            connection.request(method,path,body,extra or {})
            response=connection.getresponse()
            return response.status,dict(response.getheaders()),response.read().decode()
        finally: connection.close()
    result={'approved_for_production':False,'transport':'local HTTP only; production TLS/host configuration not rehearsed',
            'source_sha256':bindings,'checks':checks,'nginx_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
    try:
        validation=subprocess.run(command+['-t'],capture_output=True,text=True,timeout=10,**hidden)
        (output/'nginx-validation.log').write_text(validation.stderr,encoding='utf-8')
        require(validation.returncode==0,'Actual nginx accepts candidate configuration')
        version=subprocess.run([str(binary),'-v'],capture_output=True,text=True,timeout=10,**hidden)
        result['nginx_version']=version.stderr.strip()
        for service in services:
            t=threading.Thread(target=service.serve_forever,kwargs={'poll_interval':.01},daemon=True)
            t.start();threads.append(t)
        with (output/'process.log').open('wb') as log:
            process=subprocess.Popen(command,cwd=output,stdout=log,stderr=log,**hidden)
        deadline=time.monotonic()+5
        while True:
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.2): break
            except OSError:
                if time.monotonic()>deadline: raise TimeoutError('Isolated nginx failed to start')
                time.sleep(.05)
        status,h,body=request(extra={'X-PoPL-Client-IP':'192.0.2.123','X-Forwarded-For':'192.0.2.123',
                                    'Authorization':'PRIVATE_AUTH','Cookie':'PRIVATE_COOKIE'})
        require(status==200 and json.loads(body)=={'canonical':True},'Confirmed read passes through exact loopback Host')
        require(h.get('Cache-Control')=='no-store','Responses are not cached')
        incoming={k.lower():v for k,v in headers[-1].items()}
        require(incoming.get('x-popl-client-ip')=='127.0.0.1','Edge overwrites forged client identity')
        require(not any(k in incoming for k in ('authorization','cookie','x-forwarded-for','forwarded')),'Credentials and untrusted forwarding headers are stripped')
        for scope in ('summary','earnings'):
            path='/v1/wallets/0x'+'1'*40+'/'+scope+'/99/'
            time.sleep(.14)
            status,_,body=request(path+'16')
            require(status==200 and json.loads(body)=={'scope':scope,'offset':16},'Bounded wallet '+scope+' passes reviewed proxy')
            time.sleep(.14);before=len(calls)
            require(request(path+'1')[0]==400 and len(calls)==before,'Invalid '+scope+' cursor has no projection work')
            time.sleep(.14);before=len(calls)
            require(request(path+'1000')[0]==404 and len(calls)==before,'Oversized '+scope+' cursor has no projection work')
            time.sleep(.14);before=len(calls)
            require(request(path+'16','POST')[0]==405 and len(calls)==before,'Wallet '+scope+' is read-only through proxy')
        time.sleep(.14)
        status,_,body=request('/v1/collection/99/16')
        require(status==200 and json.loads(body)=={'scope':'collection','offset':16},'Collection chunks pass reviewed proxy')
        for path,method,expected in [('/v1/collection/99/1','GET',400),('/v1/collection/99/1000','GET',404),('/v1/collection/99/0','POST',405)]:
            time.sleep(.14);before=len(calls)
            require(request(path,method)[0]==expected and len(calls)==before,'Invalid collection path/method has no projection work: '+path)
        for path,method,expected in [('/v1/transactions/prepare','GET',405),('/v1/protocol','POST',405),
                                     ('/v1/activation/prepare','OPTIONS',405),('/v1/PRIVATE_UNKNOWN','GET',404),
                                     ('/v1/protocol?PRIVATE_QUERY=1','GET',404)]:
            before=len(calls)
            require(request(path,method)[0]==expected and len(calls)==before,f'No upstream work for {method} {path}')
            time.sleep(.14)
        for path in ('/v1/transactions/prepare','/v1/activation/prepare'):
            before=len(calls)
            status,_,_=request(path,'POST',{'Content-Type':'application/json','Origin':'https://evil.test'},'{}')
            require(status==403 and len(calls)==before,'Cross-origin preparation refused: '+path)
            time.sleep(.14)
            status,_,body=request(path,'POST',{'Content-Type':'application/json','Origin':ORIGIN},'{"case":"unsigned"}')
            require(status==200 and json.loads(body)=={'unsigned':True},'Exact-origin unsigned preparation succeeds: '+path)
            time.sleep(.14)
        before=len(calls)
        require(request('/v1/transactions/prepare','POST',{'Content-Type':'application/json','Origin':ORIGIN},'x'*16385)[0]==413
                and len(calls)==before,'Oversized body rejected at edge before work')
        time.sleep(.2)
        status,_,body=request('/v1/nfts/13')
        require(status==503 and 'PRIVATE_UPSTREAM_ERROR' not in body,'Upstream failure remains sanitized and is not retried')
        require(calls.count(13)==1,'Exactly one backend invocation for failed read')
        time.sleep(.2)
        with ThreadPoolExecutor(2) as pool:
            first=pool.submit(request,'/v1/nfts/1')
            require(entered.wait(1),'Slow request admitted')
            second=pool.submit(request,'/v1/nfts/1')
            deadline=time.monotonic()+1
            while calls.count(1)<2 and time.monotonic()<deadline: time.sleep(.01)
            try:
                require(calls.count(1)==2,'Two client requests admitted within limit')
                require(request('/v1/nfts/2')[0]==429,'Third concurrent client request rejected by edge')
            finally: gate.set()
            require(first.result()[0]==200 and second.result()[0]==200,'Admitted requests finish without response crossover')
        time.sleep(.2)
        require(request('/v1/nfts/3')[0]==200,'Client capacity recovers after completion')
        result['passed']=True
    except BaseException as exc:
        result['passed']=False
        result['failure_type']=type(exc).__name__
        raise
    finally:
        gate.set()
        if process is not None:
            subprocess.run(command+['-s','quit'],capture_output=True,timeout=10,**hidden)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=5)
                result['passed']=False;result['cleanup_failed']=True
        for service in services:
            if threads: service.shutdown()
            service.server_close()
        for t in threads:t.join(timeout=2)
        access=output/'logs/popl-api-access.log'
        if access.exists():
            logged=access.read_text()
            safe=all(secret not in logged for secret in ('PRIVATE_', '192.0.2.', '/v1/', '127.0.0.1'))
            result['sanitized_access_log']=safe
            if not safe:result['passed']=False
        result['check_count']=len(checks)
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if not result.get('passed'): raise SystemExit('Rehearsal failed; inspect sanitized result')
    print(json.dumps({'passed':True,'checks':len(checks),'result':str(output/'result.json')}))


if __name__=='__main__':main()
