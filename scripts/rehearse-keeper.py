"""Isolated Ubuntu process rehearsal: local Anvil, disposable encrypted signer.

Never accepts an external RPC or existing key. This tests operating mechanics
against KeeperVenue, NOT real protocol economics or Robinhood dependencies.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from keeper.monitor import error_context, signer_environment
from keeper.ops import create_snapshot, verify_snapshot, preflight
from zzz_ops.abi import calldata, keccak256
from zzz_ops.state import atomic_json


def check(condition, message):
    if not condition: raise AssertionError(message)


def wait_until(checker, timeout=20):
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        try:
            value = checker()
            if value: return value
        except (OSError,ValueError): pass
        time.sleep(.05)
    raise TimeoutError('Rehearsal condition did not complete')


def rpc(url, method, params=None):
    # Every endpoint is allocated by this process on loopback; no caller URL.
    check(url.startswith('http://127.0.0.1:'),'Nonlocal rehearsal RPC')
    request = urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or []}).encode(),
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=10) as response: data = json.load(response)
    if 'error' in data: raise RuntimeError('Local rehearsal RPC rejected '+method)
    return data['result']


class FaultProxy:
    def __init__(self,url):
        self.url = url;self.mode = 'normal';self.hit = threading.Event();self.release = threading.Event()
        self.broadcasts = [];self.attempts = 0;self.server = None
    def __enter__(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                try:
                    if owner.mode == 'outage': self.send_error(503);return
                    if owner.mode == 'wrong_chain' and body['method'] == 'eth_chainId': result = '0x1'
                    elif body['method'] == 'eth_sendRawTransaction':
                        owner.attempts += 1
                        if owner.mode == 'before_broadcast':
                            owner.hit.set();owner.release.wait(15);self.send_error(503);return
                        result = rpc(owner.url,body['method'],body['params']);owner.broadcasts.append(result)
                        if owner.mode == 'after_broadcast': owner.hit.set();owner.release.wait(15)
                    else: result = rpc(owner.url,body['method'],body['params'])
                    raw = json.dumps({'jsonrpc':'2.0','id':body['id'],'result':result}).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json')
                    self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError): pass
        self.server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.endpoint = 'http://127.0.0.1:'+str(self.server.server_port)
        return self
    def __exit__(self,*args):
        self.release.set();self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
    def fault(self,mode):
        self.mode = mode;self.hit.clear();self.release.clear()


class Lab:
    def __init__(self, root, bytecode, binaries):
        self.root = root;self.bytecode = bytecode;self.bin = binaries;self.children = [];self.logs = []
    def __enter__(self):
        try: return self.start()
        except Exception:
            self.__exit__();raise
    def start(self):
        self.root.mkdir(mode=0o700)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{port}'
        self.anvil = self.spawn([self.bin['anvil'],'--host','127.0.0.1','--port',str(port),'--chain-id','31337','--silent'])
        wait_until(lambda: rpc(self.url,'eth_chainId')=='0x7a69')
        check('anvil' in rpc(self.url,'web3_clientVersion').lower(),'Expected isolated Anvil')
        self.admin = rpc(self.url,'eth_accounts')[0]
        receipt = self.tx({'from':self.admin,'data':self.bytecode,'gas':'0x4c4b40'})
        self.venue = receipt['contractAddress'].lower()
        self.host = self.root/'host-a';self.host.mkdir(mode=0o700)
        self.password = self.root/'password';self.password.write_text(secrets.token_hex(32));self.password.chmod(0o600)
        keydir = self.root/'keys';keydir.mkdir(mode=0o700)
        env = signer_environment();env['CAST_PASSWORD'] = self.password.read_text()
        result = subprocess.run([self.bin['cast'],'wallet','new',str(keydir),'keeper'],env=env,
            capture_output=True,text=True,timeout=60)
        check(result.returncode==0,'Encrypted rehearsal wallet creation failed')
        self.key = keydir/'keeper';self.key.chmod(0o600)
        result = subprocess.run([self.bin['cast'],'wallet','address','--keystore',str(self.key),'--password-file',str(self.password)],
            env=signer_environment(),capture_output=True,text=True,timeout=30)
        check(result.returncode==0,'Rehearsal wallet address failed');self.sender = result.stdout.strip().lower()
        rpc(self.url,'anvil_setBalance',[self.sender,hex(10**20)])
        self.admin_call('authorize(address,bool)',self.sender,1)
        code = rpc(self.url,'eth_getCode',[self.venue,'latest']);codehash = '0x'+keccak256(bytes.fromhex(code[2:])).hex()
        self.cfg = {'chain_id':31337,'accounting_model':'shared-pools-v2','rpc_urls':[self.url],'sender':self.sender,
            'contracts':{k:self.venue for k in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'code_hashes':{k:codehash for k in ('access','vault','strategy','fees','compounder','buyback','pools')},
            'reviewed_for_live_use':True,'receipt_fee_policy':'included','cast_binary':self.bin['cast'],
            'keystore':str(self.key),'password_file':str(self.password),'confirmations':1,'interval_seconds':60,
            'max_gas_limit':500000,'max_gas_price_wei':10**11,'max_transaction_cost_wei':10**17,'max_daily_cost_wei':10**18,
            'state_path':str(self.host/'state.json'),'health_path':str(self.host/'health.json'),'lock_path':str(self.host/'keeper.lock'),
            'maintenance':{'compound':False,'sync_external_rewards':False,'harvest':True,'harvest_interval_seconds':14400}}
        self.config = self.root/'config.json';self.write_config()
        self.cli('--initialize-state')
        return self
    def __exit__(self,*args):
        for process in reversed(self.children): self.kill(process)
        for handle in self.logs:handle.close()
    def spawn(self,command):
        handle = tempfile.TemporaryFile();self.logs.append(handle)
        p = subprocess.Popen(command,cwd=ROOT,env=signer_environment(),stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
        self.children.append(p);return p
    def kill(self,p):
        # Always kill the group: the parent may have died while cast is still alive.
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=10)
    def write_config(self): atomic_json(self.config,self.cfg)
    def cli(self,*args,expect=0):
        p = self.spawn([sys.executable,'-m','keeper.monitor','--config',str(self.config),*args])
        try: result = p.wait(timeout=45)
        except subprocess.TimeoutExpired:self.kill(p);raise
        if result != expect:
            # Keeper's logs are sanitized; never expose wallet command stdout.
            handle = self.logs[-1];handle.seek(0);print(handle.read().decode(errors='replace'),flush=True)
        check(result==expect,'Keeper CLI exit differs');return p
    def worker(self):return self.spawn([sys.executable,'-m','keeper.monitor','--config',str(self.config),'--live','--once'])
    def state(self):return json.loads(Path(self.cfg['state_path']).read_text())
    def health(self):return json.loads(Path(self.cfg['health_path']).read_text())
    def nonce(self):return int(rpc(self.url,'eth_getTransactionCount',[self.sender,'latest']),16)
    def tx(self,tx):
        tx_hash = rpc(self.url,'eth_sendTransaction',[tx])
        receipt = wait_until(lambda:rpc(self.url,'eth_getTransactionReceipt',[tx_hash]))
        check(receipt['status']=='0x1','Rehearsal administrator transaction failed');return receipt
    def admin_call(self,sig,*args):return self.tx({'from':self.admin,'to':self.venue,'data':calldata(sig,*args),'gas':'0x7a120'})
    def count(self,sig):return int(rpc(self.url,'eth_call',[{'to':self.venue,'data':calldata(sig)},'latest']),16)
    def settle(self):self.cli('--live','--once');check(self.state()['pending'] is None,'Pending transaction did not settle')


def run(root, bytecode, binaries, record):
    with Lab(root/'normal',bytecode,binaries) as lab:
        record('fresh_signer_read_only_preflight',preflight(lab.cfg)['ok'])
        lab.cli('--live','--once');check(lab.state()['pending'],'No durable transaction intent');lab.settle()
        check(lab.nonce()==1 and lab.count('harvests()')==1,'First shared-bucket harvest mismatch')
        costs = sum(lab.state()['spent'].values());check(costs>0,'Gas not recorded')
        lab.cli('--live','--once');check(lab.nonce()==1 and sum(lab.state()['spent'].values())==costs,'Duplicate harvest or cost')
        record('encrypted_signer_receipt_exactly_once',True)

        # A migrated runtime directory and same encrypted signer, never two workers.
        backup = lab.root/'snapshot.json';create_snapshot(lab.cfg,backup);check(verify_snapshot(lab.cfg,backup)['ok'],'Snapshot verify')
        hostb = lab.root/'host-b';hostb.mkdir(mode=0o700)
        restored = json.loads(backup.read_text())['payload']['state']
        for field,name in [('state_path','state.json'),('health_path','health.json'),('lock_path','keeper.lock')]: lab.cfg[field]=str(hostb/name)
        atomic_json(lab.cfg['state_path'],restored);lab.write_config()
        check(preflight(lab.cfg)['ok'],'New-host preflight failed')
        lab.cli('--live','--once');check(lab.nonce()==1 and lab.state()['spent']==restored['spent'],'Restore lost budget or replayed')
        record('new_directory_restore_preserves_budget',True)

        # Simulate an aged maintenance timestamp, not three days of real uptime.
        aged = lab.state();aged['last']['harvest:1'] = int(time.time())-3*86400;atomic_json(lab.cfg['state_path'],aged)
        lab.admin_call('requestRebalance()')
        lab.cli('--live','--once');lab.cli('--live','--once');lab.settle();lab.cli('--live','--once')
        check(lab.count('rebalances()')==1 and lab.count('harvests()')==2 and lab.nonce()==3,'Downtime replayed missed intervals')
        record('aged_maintenance_current_state_not_replay',True)

        # Old snapshot now has stale nonce even though its receipt anchor is canonical.
        current = lab.state();stale = copy.deepcopy(restored)
        stale['last']['harvest:1'] = int(time.time())-3*86400
        atomic_json(lab.cfg['state_path'],stale)
        result = preflight(lab.cfg);check('nonce_reconciliation_required' in result['reasons'],'Stale backup accepted')
        lab.admin_call('requestRebalance()');lab.cli('--live','--once',expect=1)
        check(lab.nonce()==3,'Stale restore signed')
        current['last']['harvest:1'] = int(time.time())-14401
        atomic_json(lab.cfg['state_path'],current)
        record('stale_backup_blocks_signing',True)
        lab.admin_call('setPaused(bool)',1);lab.cli('--live','--once')
        check(lab.health()['strategy_paused'] and lab.nonce()==3,'Paused keeper performed maintenance')
        lab.admin_call('setPaused(bool)',0)
        lab.admin_call('authorize(address,bool)',lab.sender,0);lab.cli('--live','--once',expect=1)
        check(lab.nonce()==3,'Revoked signer operated');lab.admin_call('authorize(address,bool)',lab.sender,1)
        record('pause_and_role_revocation',True)
        rpc(lab.url,'anvil_setBalance',[lab.sender,'0x0']);lab.cli('--live','--once',expect=1)
        check(lab.nonce()==3 and lab.state()['pending'] is None,'Low balance signed')
        rpc(lab.url,'anvil_setBalance',[lab.sender,hex(10**20)])
        record('low_balance_blocks_broadcast',True)

        with FaultProxy(lab.url) as proxy:
            lab.cfg['rpc_urls']=[proxy.endpoint,lab.url];lab.write_config()
            for mode in ('outage','wrong_chain'):
                proxy.fault(mode);check(preflight(lab.cfg)['ok'],'Read fallback failed')
            record('actual_http_outage_wrong_chain_fallback',True)
        lab.cfg['rpc_urls']=[lab.url];lab.write_config()

        # Concurrent worker must fail under the actual process lock.
        prior = lab.health()['time']
        p = lab.spawn([sys.executable,'-m','keeper.monitor','--config',str(lab.config)])
        wait_until(lambda:lab.health()['time']!=prior and p.poll() is None)
        lab.cli('--once',expect=1);lab.kill(p)
        lab.cli('--once');record('concurrent_process_lock_and_restart',True)

        good = Path(lab.cfg['state_path']).read_bytes()
        Path(lab.cfg['state_path']).write_text('{broken');lab.cli('--live','--once',expect=1)
        Path(lab.cfg['state_path']).unlink();lab.cli('--live','--once',expect=1)
        Path(lab.cfg['state_path']).write_bytes(good);Path(lab.cfg['state_path']).chmod(0o600)
        record('missing_corrupt_state_blocks_start',True)
        folder = Path(lab.cfg['state_path']).parent;folder.chmod(0o500)
        try:lab.cli('--live','--once',expect=1);check(lab.nonce()==3,'Storage failure signed')
        finally:folder.chmod(0o700)
        record('unwritable_runtime_blocks_signing',True)

    for fault in ('before_broadcast','after_broadcast'):
        with Lab(root/fault,bytecode,binaries) as lab, FaultProxy(lab.url) as proxy:
            lab.cfg['rpc_urls']=[proxy.endpoint];lab.write_config();proxy.fault(fault)
            p = lab.worker()
            check(proxy.hit.wait(30),'Did not reach broadcast crash point')
            lab.kill(p);proxy.release.set();proxy.mode='normal'
            state = lab.state();check(state['pending'] and state['pending']['hash'] is None,'Intent was not durable before crash')
            attempts = proxy.attempts;lab.cli('--live','--once')
            check(proxy.attempts==attempts and lab.health()['status']=='recovery_required','Ambiguous restart resubmitted')
            if fault == 'before_broadcast':
                check(lab.nonce()==0 and not proxy.broadcasts,'Unsent intent was broadcast')
            else:
                check(lab.nonce()==1 and len(proxy.broadcasts)==1,'Unexpected duplicate broadcast')
                lab.cli('--resolve-pending',proxy.broadcasts[0])
                check(lab.state()['pending'] is None and lab.state()['next_nonce']==1,'Verified hash did not recover')
                costs = sum(lab.state()['spent'].values());lab.cli('--live','--once')
                check(lab.nonce()==1 and sum(lab.state()['spent'].values())==costs,'Recovery repeated transaction/cost')
            record('process_kill_'+fault,True)

    with Lab(root/'reorg',bytecode,binaries) as lab:
        snapshot = rpc(lab.url,'evm_snapshot')
        lab.cli('--live','--once');lab.settle();state = lab.state()
        check(rpc(lab.url,'evm_revert',[snapshot]),'Local reorg failed')
        rpc(lab.url,'evm_mine')
        lab.cli('--live','--once',expect=1)
        check(lab.state()==state and lab.nonce()==0,'Invalidated checkpoint changed state or signed')
        record('confirmed_receipt_reorg_halts_restart',True)


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    parser.add_argument('--offline',action='store_true');args = parser.parse_args()
    check(os.name=='posix' and os.getuid()!=0,'Run as an unprivileged Linux/Unix user')
    binaries = {name:shutil.which(name) for name in ('cast','forge','anvil')}
    check(all(binaries.values()),'Pinned Foundry tools required')
    versions = {name:subprocess.check_output([path,'--version'],text=True).strip() for name,path in binaries.items()}
    check(all('1.4.4' in version for version in versions.values()),'Use reviewed Foundry 1.4.4')
    sources = ['keeper/monitor.py','keeper/ops.py','zzz_ops/abi.py','zzz_ops/state.py','zzz_ops/rpc.py',
        'keeper/rehearsal/KeeperVenue.sol','scripts/rehearse-keeper.py']
    hashes = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    report = {'schema':1,'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'local Anvil / test-only venue; no public signing',
        'production_approved':False,'source_hashes':hashes,'versions':versions,'cases':[],'ok':False}
    def record(name,ok):
        check(ok,name);report['cases'].append({'name':name,'ok':True});print(json.dumps(report['cases'][-1]),flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix='zzz-keeper-rehearsal-') as temporary:
            root = Path(temporary);build = root/'build';(build/'src').mkdir(parents=True)
            shutil.copyfile(ROOT/'keeper/rehearsal/KeeperVenue.sol',build/'src/KeeperVenue.sol')
            (build/'foundry.toml').write_text('[profile.default]\nsolc_version="0.8.26"\nevm_version="cancun"\n')
            command = [binaries['forge'],'build','--root',str(build)] + (['--offline'] if args.offline else [])
            result = subprocess.run(command,capture_output=True,text=True,timeout=120,env=signer_environment())
            check(result.returncode==0,'Fixture compilation failed')
            bytecode = json.loads((build/'out/KeeperVenue.sol/KeeperVenue.json').read_text())['bytecode']['object']
            run(root,bytecode,binaries,record)
            report['ok'] = True
    except Exception as exc:
        report['error'] = error_context(exc)
        if isinstance(exc,AssertionError):report['error']['assertion'] = str(exc)
        print(json.dumps(report['error']),flush=True)
    if hashes != {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}:report['ok']=False
    atomic_json(args.output,report)
    return 0 if report['ok'] else 1


if __name__ == '__main__':sys.exit(main())
