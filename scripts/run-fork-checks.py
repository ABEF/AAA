"""Test infrastructure: serial, bounded, uncached read-only archive RPC relay.

Never signs/broadcasts. Requires an explicitly chosen upstream; does not repair,
cache, simulate or substitute any on-chain data. All fork block tags pass through.
"""
from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

MAX_REQUEST=1024*1024
MAX_RESPONSE=8*1024*1024
FORGE_COMMIT='05794498bf47257b144e2e2789a1d5bf8566be0e'
ROOT=Path(__file__).resolve().parents[1]
FORK_SUITES=('test/UniswapV4Fork.t.sol:UniswapV4ForkTest','test/NativePoolFork.t.sol:NativePoolForkTest')
FORK_PATTERN='^(UniswapV4ForkTest|NativePoolForkTest)$'
READ_METHODS=frozenset({'eth_chainId','eth_gasPrice','eth_blockNumber','eth_getBlockByNumber','eth_getBlockByHash',
    'eth_getCode','eth_getStorageAt','eth_getBalance','eth_getTransactionCount','eth_getLogs',
    'eth_call','eth_getTransactionByHash','eth_getTransactionReceipt','web3_clientVersion'})

def error(status,request_id,message,code=-32098):
    return status,json.dumps({'jsonrpc':'2.0','id':request_id,'error':{'code':code,'message':message}}).encode()

class Relay:
    def __init__(self,upstream,*,interval=1.25,post=None,clock=time.monotonic,sleep=time.sleep):
        if not isinstance(upstream,str) or not upstream.strip():raise ValueError('Explicit upstream RPC is required')
        try:
            parsed=urllib.parse.urlsplit(upstream)
            secure=parsed.scheme=='https' or parsed.scheme=='http' and parsed.hostname in ('localhost','127.0.0.1','::1')
            valid=secure and bool(parsed.hostname) and not parsed.fragment
            parsed.port  # Reject malformed ports without reporting the input URL.
        except ValueError:valid=False
        if not valid:raise ValueError('Upstream requires HTTPS or loopback HTTP')
        if isinstance(interval,bool) or not isinstance(interval,(int,float)) or not math.isfinite(interval) or interval<1.25:
            raise ValueError('Archive relay interval must be at least 1.25 seconds')
        self.upstream=upstream;self.interval=interval;self.post=post or self._post
        self.clock=clock;self.sleep=sleep;self.next_request=0.0;self.lock=threading.Lock()
        # Upstream exceptions and credential-bearing error bodies never enter logs.
        self.private=[upstream]+[value for value in (parsed.username,parsed.password) if value]
        self.private.extend(value for _,value in urllib.parse.parse_qsl(parsed.query) if value)

    def _post(self,body):
        request=urllib.request.Request(self.upstream,data=body,headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=30) as response:return response.status,response.read(MAX_RESPONSE+1)
        except urllib.error.HTTPError as exc:
            with exc:return exc.code,exc.read(MAX_RESPONSE+1)

    def handle(self,body):
        if not isinstance(body,bytes) or len(body)>MAX_REQUEST:return error(413,None,'RPC request exceeds size limit')
        try:request=json.loads(body)
        except (UnicodeError,json.JSONDecodeError):return error(400,None,'Malformed JSON-RPC request',-32600)
        if not isinstance(request,dict) or request.get('jsonrpc')!='2.0' or 'id' not in request or \
            not (request['id'] is None or type(request['id']) in (int,str)) or not isinstance(request.get('params',[]),list):
            return error(400,None,'Malformed JSON-RPC request',-32600)
        method=request.get('method');request_id=request['id']
        if not isinstance(method,str) or method not in READ_METHODS:
            identifier=method if isinstance(method,str) and re.fullmatch(r'[A-Za-z0-9_]{1,64}',method) else 'invalid'
            return error(403,request_id,f'RPC method denied by the fork read-only allowlist: {identifier}',-32601)
        with self.lock:
            for attempt in range(3):
                delay=max(0.0,self.next_request-self.clock())
                if delay:self.sleep(delay)
                self.next_request=self.clock()+self.interval
                try:status,response=self.post(body)
                except (OSError,ValueError,TimeoutError):return error(502,request_id,'Archive RPC transport failed')
                if status==429:
                    if attempt<2:self.sleep(6*(2**attempt));continue
                    return error(429,request_id,'Archive RPC rate limit persisted after three attempts')
                if status!=200:return error(status if 400<=status<=599 else 502,request_id,'Archive RPC HTTP request failed')
                if not isinstance(response,bytes) or len(response)>MAX_RESPONSE:
                    return error(502,request_id,'Archive RPC response exceeds size limit')
                try:payload=json.loads(response)
                except (UnicodeError,json.JSONDecodeError):return error(502,request_id,'Archive RPC returned malformed JSON')
                if not isinstance(payload,dict) or payload.get('jsonrpc')!='2.0' or 'id' not in payload or \
                    type(payload['id']) is not type(request_id) or payload['id']!=request_id or \
                    ('result' in payload)==('error' in payload):
                    return error(502,request_id,'Archive RPC response identity or envelope mismatch')
                if 'error' in payload and any(value in json.dumps(payload['error'],ensure_ascii=False) for value in self.private):
                    return error(502,request_id,'Archive RPC returned sensitive transport details')
                return status,response  # Exact upstream bytes, including JSON-RPC error replies.
        raise AssertionError('Bounded retry loop must return')

class RelayServer:
    def __init__(self,relay):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                try:length=int(self.headers.get('Content-Length',''))
                except ValueError:length=-1
                if not 0<=length<=MAX_REQUEST:status,payload=error(413,None,'Invalid RPC request length')
                else:
                    self.connection.settimeout(30)
                    try:status,payload=relay.handle(self.rfile.read(length))
                    except (OSError,TimeoutError):status,payload=error(400,None,'Incomplete RPC request')
                self.send_response(status);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(payload)))
                try:self.end_headers();self.wfile.write(payload)
                except OSError:pass  # Forge may have already aborted its local request.
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
    def start(self):self.thread.start()
    def close(self):
        if self.thread.is_alive():self.server.shutdown()
        self.server.server_close()
        if self.thread.is_alive():self.thread.join(timeout=5)

def expected_tests(source):
    # Both selected suites declare their tests directly. Fail closed on an empty
    # inventory or overload rather than accepting a filtered/disabled green run.
    text=(ROOT/source).read_text(encoding='utf-8')
    text=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '', text)
    names=re.findall(r'\bfunction\s+(test[A-Za-z0-9_]*)\s*\(',text)
    if not names or len(names)!=len(set(names)):
        raise ValueError('Selected fork source test inventory is empty or ambiguous')
    return set(names)

def verify_fork_results(output):
    if not isinstance(output,str):raise ValueError('Selected fork output is absent')
    results=json.loads(output)
    if not isinstance(results,dict):raise ValueError('Selected fork results must be a JSON object')
    suites={key.replace('\\','/'):value for key,value in results.items()}
    if len(suites)!=len(results) or set(suites)!=set(FORK_SUITES):
        raise ValueError('Both exact selected fork suites must execute')
    total=0
    for suite in FORK_SUITES:
        result=suites[suite]
        tests=result.get('test_results') if isinstance(result,dict) else None
        if not isinstance(tests,dict):raise ValueError('Selected fork test results are absent')
        names=[]
        for signature,test in tests.items():
            match=re.fullmatch(r'(test[A-Za-z0-9_]*)\([^\n]*\)',signature)
            if not match or not isinstance(test,dict) or test.get('status')!='Success':
                raise ValueError('Every selected fork test must succeed without skips')
            names.append(match[1])
        if len(names)!=len(set(names)) or set(names)!=expected_tests(suite.split(':',1)[0]):
            raise ValueError('Selected fork execution does not cover its complete source inventory')
        total+=len(names)
    return total

def run_fork(upstream,*,forge=None,run=subprocess.run,server_factory=RelayServer,relay_factory=Relay):
    # The former wrapped/native fixture was retired, not qualified for the new
    # LP-only candidate. Never contact RPC/Forge or substitute archived source.
    missing=[suite.split(':',1)[0] for suite in FORK_SUITES
        if not (ROOT/suite.split(':',1)[0]).is_file()]
    if missing:
        print('Fork qualification blocked: current selected fixture unavailable: '+', '.join(missing)+
            '. A reviewed current native fork suite is required; archived tests are historical only. '
            'No RPC or Forge process was started.',file=sys.stderr,flush=True)
        return 2
    relay=relay_factory(upstream)
    executable=forge or shutil.which('forge') or 'forge'
    version=run([executable,'--version'],capture_output=True,text=True,check=False)
    if version.returncode or not re.search(r'\bVersion:\s*1\.4\.4(?:-v1\.4\.4)?(?:\s|$)',version.stdout) or FORGE_COMMIT not in version.stdout:
        raise ValueError('Pinned Forge 1.4.4 build is required')
    server=server_factory(relay)
    try:
        server.start()
        environment=dict(os.environ,RUN_ROBINHOOD_FORK_TESTS='true',ROBINHOOD_RPC_URL=server.url)
        for name in ('ROBINHOOD_ARCHIVE_RPC_URL','ETH_RPC_URL','ETH_RPC_HEADERS','ETH_RPC_JWT_SECRET'):
            environment.pop(name,None)
        command=[executable,'test','--match-contract',FORK_PATTERN,'--threads','1','--no-storage-caching','-vvv','--json']
        result=run(command,env=environment,capture_output=True,text=True,check=False)
        if result.stdout:print(result.stdout,end='' if result.stdout.endswith('\n') else '\n',flush=True)
        if result.stderr:print(result.stderr,end='' if result.stderr.endswith('\n') else '\n',file=sys.stderr,flush=True)
        if result.returncode:return result.returncode
        total=verify_fork_results(result.stdout)
        print(f'Fork coverage verified: both exact suites, {total} successful source tests, zero skips.',flush=True)
        return 0
    finally:server.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream',default=os.environ.get('ROBINHOOD_ARCHIVE_RPC_URL'))
    parser.add_argument('--forge')
    args=parser.parse_args()
    try:return run_fork(args.upstream,forge=args.forge)
    except (OSError,ValueError,TimeoutError):
        print('Fork runner failed: verify the explicit archive RPC, pinned Forge and complete unskipped results for both selected suites.',file=sys.stderr)
        return 1

if __name__=='__main__':sys.exit(main())
