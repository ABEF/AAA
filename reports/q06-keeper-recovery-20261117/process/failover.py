"""NEW bounded HTTP failover exceeds120s while making actual progress.

Private-network loopback only. No keeper signing, contracts, keys or journals.
The production RPC/decoder and main-thread watchdog hook run unmodified.
"""
from pathlib import Path
import json,os,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from keeper.watchdog import ProgressWatchdog,ProgressRPC
from zzz_ops.rpc import Rpc
from zzz_ops.state import atomic_json

def main():
    root=Path(sys.argv[1]);assert os.getuid()!=0
    watchdog=ProgressWatchdog.from_environment();assert watchdog.seconds==120
    watchdog.pulse(force=True);servers=[];events=[];lock=threading.Lock()
    try:
        for index in range(8):
            def handler_for(i):
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self,*a):pass
                    def do_POST(self):
                        n=int(self.headers['Content-Length']);assert 0<n<4096
                        q=json.loads(self.rfile.read(n));time.sleep(7.5)
                        if q['method']=='eth_chainId':body={'result':'0x1237'}
                        elif q['method']=='eth_blockNumber' and i==7:body={'result':'0x64'}
                        elif q['method']=='eth_blockNumber':body={'error':{'code':-32000,'message':'Synthetic bounded refusal'}}
                        else:raise AssertionError('Unexpected rehearsal method')
                        raw=json.dumps({'jsonrpc':'2.0','id':q['id'],**body}).encode()
                        self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                        with lock:events.append({'endpoint_index':i,'method':q['method'],'completed_monotonic':time.monotonic()})
                return Handler
            server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(index));server.daemon_threads=True
            threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server)
        rpc=ProgressRPC(Rpc(['http://127.0.0.1:'+str(s.server_port) for s in servers],4663,
            transport_attempt_complete=watchdog.pulse),watchdog)
        start=time.monotonic();atomic_json(root/'started.json',{'pid':os.getpid(),'watchdog_seconds':watchdog.seconds})
        result=rpc.call('eth_blockNumber');elapsed=time.monotonic()-start
        assert result=='0x64' and elapsed>120 and len(events)==16
        atomic_json(root/'completed.json',{'pid':os.getpid(),'elapsed_seconds':elapsed,'result':result,
            'completed_http_responses':events,'watchdog_seconds':watchdog.seconds,
            'scope':'Actual Linux bounded failover/progress; synthetic replies, no signing/market/provider qualification'})
    finally:
        for server in servers:server.shutdown();server.server_close()
if __name__=='__main__':main()
