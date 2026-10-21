"""Fresh local Anvil + real unsigned APIs + reviewed website coordinator.

No public RPC/key input. Owns only its new Anvil child. Production API validators
and wallet signer remain unchanged; market/feed/VRF boundaries are explicit mocks.
"""
from __future__ import annotations
import argparse
import hashlib
import http.client
import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import re
import socket
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from frontend_api.service import Projection, ZERO
from frontend_api.activation import ActivationTransactions
from frontend_api.activation_config import MODULES
from frontend_api.transactions import Transactions
from frontend_api.worker import WorkerPool
from frontend_api.server import ReadServer, handler as read_handler
from frontend_api.activation_server import handler as activation_handler
from frontend_api.http_runtime import BoundedHandler
from frontend_api.admission import ClientAdmission
from zzz_ops.abi import keccak256

spec=importlib.util.spec_from_file_location('popl_local_stack',ROOT/'scripts/local-stack.py')
stack=importlib.util.module_from_spec(spec);spec.loader.exec_module(stack)


def configurations(lab):
    """Derive pins only from this process's freshly deployed, source-checked fixture."""
    lab.guard();c=lab.contracts
    config=json.loads((lab.home/'api.json').read_text())
    config['earnings_history']['prices']['feeds'].append(dict(
        asset=ZERO,priced_token=lab.weth,token_code_hash=lab.pin(lab.weth)['code_hash'],
        source=lab.feed,source_code_hash=lab.pin(lab.feed)['code_hash'],max_age=3600,feed_decimals=8))
    stack.save(lab.home/'api.json',config)
    p=Projection(config)
    review='0x'+keccak256(b'LOCAL ANVIL API REHEARSAL ONLY; no production fee review').hex()
    tc=dict(schema=1,chain_id=31337,projection_sha256=p.identity,fee_policy=dict(
        estimate_includes_all_fees=True,review_hash=review,max_gas_price_wei=str(100*10**9),max_network_fee_wei=str(10**18)))
    roles={r:c[r] for r in MODULES}
    roles.update(entry=c['entry'],activation_assets=lab.addr('pools','activationAssets()'),budget=lab.addr('vault','migrationBudget()'))
    deps={lab.addr('liquidity',method) for method in ('positionManager()','poolManager()','stateView()','permit2()')}
    sources=[]
    for a in lab.input_assets:
        token=lab.weth if a['address']==ZERO else a['address']
        sources.append(dict(pool_id=lab.pool,source_asset=a['address'],route_id=a['route_id'],
                            asset_policy_id=lab.read(roles['activation_assets'],'activePolicy(address)',token)[0]))
        sources[-1]['asset_policy_id']='0x'+sources[-1]['asset_policy_id']
        if a['route_id']!='0x'+'0'*64:
            route=lab.read('entry','route(bytes32)',a['route_id'])
            deps.update('0x'+x[-40:] for x in route[2:5])
    tokens=set(lab.tokens)|{a['address'] for a in lab.input_assets if a['address']!=ZERO}
    ac=dict(schema=1,contracts={r:lab.pin(a) for r,a in roles.items()},
        dependencies=[lab.pin(a) for a in sorted(deps)],sources=sources,
        tokens=[dict(address=a,code_hash=lab.pin(a)['code_hash'],decimals=lab.uint(a,'decimals()'),
                     feed=lab.feed,feed_code_hash=lab.pin(lab.feed)['code_hash'],feed_decimals=8,max_age=3600) for a in sorted(tokens)],
        sequencer=dict(address=ZERO,policy_id='0x'+'0'*64),call_pins=[],storage_pins=[],
        fee_policy=dict(estimate_includes_all_fees=True,review_hash=review,max_gas_price_wei=str(100*10**9)))
    activation=ActivationTransactions(p,ac);transactions=Transactions(p,tc)
    code=lambda a:lab.rpc('eth_getCode',[a,'latest'])
    manifest=dict(schema=1,mode='read-and-prepare',environment='rehearsal',id='0'*64,chain_id=31337,
        chain_name='PoPL Local API Anvil',genesis_hash=lab.genesis,deployment_block=config['deployment_block'],
        deployment_block_hash=config['deployment_block_hash'],confirmations=1,max_age_seconds=120,
        api_prefix='/api',rpc_url=lab.rpc_url,projection_sha256=p.identity,
        activation_sha256=activation.config.identity,transaction_sha256=transactions.config.identity,
        activation_fee_review=review,transaction_fee_review=review,pool_id=lab.pool,
        contracts={r:dict(address=c[r],runtime_code=code(c[r])) for r in ('access','nft','vault','entry','claim_router','oracle')},
        input_assets=[dict(a,valuation_asset=lab.weth if a['address']==ZERO else a['address'],
                           **({} if a['address']==ZERO else dict(runtime_code=code(a['address'])))) for a in lab.input_assets],
        reward_assets=[{k:a[k] for k in ('address','symbol','decimals')} for a in config['assets']],
        limits=dict(gas=12000000,gas_price_wei=str(100*10**9),network_fee_wei=str(10**18),
                    native_value_wei=str(99999*10**18),contribution_usd_18=str(99999*10**18)))
    manifest['id']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    for name,value in [('transaction-config',tc),('activation-config',ac),('website-manifest',manifest)]:
        stack.save(lab.home/(name+'.json'),value)
    return config,tc,ac,manifest


def web_handler(lab,manifest,ports,allowed):
    origin=f'http://127.0.0.1:{lab.args.port}'
    root=Path(lab.args.website)/'dist'
    class Handler(BoundedHandler):
        def log_message(self,*args):pass
        def output(self,status,body,kind='application/json'):
            self.close_connection=True
            self.send_response(status)
            self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' "+lab.rpc_url+"; frame-ancestors 'none'; base-uri 'none'; object-src 'none'")
            self.end_headers()
            if self.command!='HEAD':self.wfile.write(body)
        def _json(self,status,value):self.output(status,json.dumps(value).encode())
        def valid(self):
            return (self.headers.get_all('Host',[])==[f'127.0.0.1:{lab.args.port}'] and
                    self.headers.get_all('Transfer-Encoding') is None and self.headers.get_all('Expect') is None)
        def forward(self,body=None):
            path=self.path[4:]
            if not re.fullmatch(r'/v1/[a-zA-Z0-9/_-]+',path):self._json(404,{'error':'unknown_endpoint'});return
            port=ports[1] if path=='/v1/activation/prepare' else ports[0]
            self.begin_work()
            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=32)
            try:
                conn.request(self.command,path,body=body,headers={'Content-Type':'application/json'})
                response=conn.getresponse();data=response.read(1024*1024+1)
                if len(data)>1024*1024:raise ValueError('response too large')
                self.output(response.status,data)
            except (OSError,ValueError):self._json(503,{'error':'local_api_unavailable'})
            finally:conn.close()
        def do_GET(self):
            if not self.valid() or self.headers.get_all('Content-Length',[]) not in ([],['0']):self._json(400,{'error':'invalid_request'});return
            if self.path.startswith('/api/'):self.forward();return
            if self.path=='/deployment-config.js':
                self.begin_work();self.output(200,('export const DEPLOYMENT = '+json.dumps(manifest)+';\n').encode(),'text/javascript');return
            name=self.path.split('?',1)[0].lstrip('/') or 'index.html'
            if name not in allowed:self._json(404,{'error':'not_found'});return
            self.begin_work()
            self.output(200,(root/name).read_bytes(),mimetypes.guess_type(name)[0] or 'application/octet-stream')
        def do_POST(self):
            if not self.valid() or self.headers.get_all('Origin',[])!=[origin]:self._json(403,{'error':'origin_not_allowed'});return
            if self.path not in ('/api/v1/transactions/prepare','/api/v1/activation/prepare'):self._json(404,{'error':'unknown_endpoint'});return
            lengths=self.headers.get_all('Content-Length',[])
            if len(lengths)!=1 or not re.fullmatch(r'[0-9]{1,5}',lengths[0]) or int(lengths[0])>16384:self._json(413,{'error':'invalid_body_size'});return
            if self.headers.get_all('Content-Type',[])!=['application/json']:self._json(415,{'error':'application_json_required'});return
            body=self.rfile.read(int(lengths[0]))
            if len(body)!=int(lengths[0]):self._json(400,{'error':'incomplete_body'});return
            self.forward(body)
    return Handler


def maintain(lab,stop):
    """Local miner, MockVRF fulfiller and indexer only; never sends a holder action."""
    last_mine=time.monotonic()
    try:
        while not stop.wait(.75):
            lab.guard()
            for identifier in lab.ids():
                if not lab.uint('nft','traitsReady(uint256)',identifier):
                    request=lab.uint('nft','requestOf(uint256)',identifier)
                    ordinal=lab.uint('nft','mintOrdinalOf(uint256)',identifier)
                    lab.call(lab.vrf,'fulfill(uint256,uint256,uint256)',request,ordinal*721,ordinal*7919)
                    lab.call('nft','finalizeTraits(uint256)',identifier)
            # Fresh timestamp without advancing time artificially or resetting state.
            if time.monotonic()-last_mine>=15:
                lab.rpc('evm_mine');last_mine=time.monotonic()
            while lab.indexer.step():pass
    except Exception as exc:
        stack.save(lab.home/'maintenance-error.json',{'time':int(time.time()),'type':type(exc).__name__})
        print('Local fixture maintenance stopped; inspect evidence. No automatic transaction retry.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('anvil','cast','artifacts','fixture-artifacts','state','website'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--port',type=int,default=8902)
    args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('Use a loopback unprivileged port')
    # Only explicitly generated public build files are served, never repo/config/state.
    build=Path(args.website)/'dist'
    if not (build/'index.html').is_file():parser.error('Build the website first')
    allowed={p.relative_to(build).as_posix() for p in build.rglob('*') if p.is_file() and not p.is_symlink()}
    if any(x.startswith('.') or '..' in x.split('/') for x in allowed):parser.error('Invalid public build')
    with socket.socket() as probe:probe.bind(('127.0.0.1',args.port))
    args.named_assets=True;args.native_input=True;args.venue_fixture='LocalAPIVenue'
    lab=stack.Lab(args);servers=[];stop=threading.Event();maintenance=None
    try:
        lab.start()
        # >8 actual wallet holdings exercise pagination, with the original four active/dormant positions intact.
        for _ in range(14):lab.mint(lab.accounts[1])
        lab.sync()
        config,tc,ac,manifest=configurations(lab)
        read=WorkerPool(config,transaction_config=tc,workers=4)
        activation=WorkerPool(config,ac,workers=2)
        for h in (read_handler(read,read),activation_handler(activation,activation)):
            server=ReadServer(('127.0.0.1',0),h,max_connections=8,admission=ClientAdmission(max_active=4))
            servers.append(server);threading.Thread(target=server.serve_forever,daemon=True).start()
        ports=[s.server_address[1] for s in servers]
        server=ReadServer(('127.0.0.1',args.port),web_handler(lab,manifest,ports,allowed),max_connections=16)
        servers.append(server)
        maintenance=threading.Thread(target=maintain,args=(lab,stop),daemon=True);maintenance.start()
        stack.save(lab.home/'running.json',dict(url=f'http://127.0.0.1:{args.port}',rpc=lab.rpc_url,
            pid=os.getpid(),anvil_pid=lab.process.pid,api_ports=ports,state=str(lab.home),
            accounts=lab.accounts[1:],scope='Fresh local API/Anvil rehearsal; market, feed and VRF substitutes'))
        print(f'OPEN http://127.0.0.1:{args.port}/#my-nfts | Evidence: {lab.home}',flush=True)
        server.serve_forever()
    finally:
        stop.set()
        if maintenance:maintenance.join(timeout=25)
        for server in servers:server.server_close()
        lab.close()

if __name__=='__main__':main()
