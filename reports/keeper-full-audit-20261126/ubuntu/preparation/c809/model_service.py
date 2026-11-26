"""PREPARATION ONLY: fresh c809 restart-limit peer; no old financial journey.

Root must review/package exact source/helper/input pins before any execution.
Only a fresh private namespace and copied authenticated F6 state are admitted.
"""
from pathlib import Path
import argparse
import contextlib
import copy
import importlib.util
import io
import json
import os
import signal
import sys
import time
import unittest

import keeper_runtime as B
import keeper_jobs as J
import job_cases as C

LAB=Path('/opt/popl-keeper-full-audit-20261126-c809')
SOURCE=LAB/'source/contracts'
OUT=LAB/'runtime/run-001/model'
for module in (B,J,C):module.LAB,module.SOURCE,module.OUT=LAB,SOURCE,OUT
need,save,sha=B.need,B.save,B.sha

class Model(J.Model):
    def start(self,env):
        need(sha(self.binary.read_bytes())==B.ANVIL_SHA,'Anvil differs')
        self.controlled_genesis_timestamp=int(time.time())
        self.child=B.Child([self.binary,'--host','127.0.0.1','--port','19591',
            '--accounts','0','--silent','--chain-id','4663','--hardfork','cancun',
            '--gas-limit','32000000','--gas-price','1000000000',
            '--block-base-fee-per-gas','1','--timestamp',str(self.controlled_genesis_timestamp),
            '--load-state',LAB/'inputs/restore-state.json'],self.folder,env,self.folder/'anvil')
        deadline=time.monotonic()+20
        while True:
            need(self.child.process.poll()is None and not self.child.overflow,'Owned model startup failed')
            if B.owns(self.child.process.pid,19591):
                try:
                    if self.rpc('eth_chainId',[])=='0x1237':break
                except (ConnectionError,OSError):pass
            need(time.monotonic()<deadline,'Owned model startup deadline');time.sleep(.1)
        head=self.rpc('eth_getBlockByNumber',['latest',False])
        need(head['hash'].lower()==B.IMPORTED_HASH and int(head['gasLimit'],16)==32000000,'Copied F6 anchor differs')
        return head
    def guard(self):
        # Even an unexpected keeper intent cannot pass the test gateway.
        raise B.HarnessRefusal('No stock signed send is admitted in restart-only partition')

C.Model=Model

def selected_linux_test(source):
    """Run only the NEW Linux inherited-pipe body, never the other green methods."""
    relative='tests_python/test_read_process.py'
    row=source['members'].get(relative)
    need(type(row)is dict,'Explicit selected Linux test pin is absent')
    path=SOURCE/relative;raw=path.read_bytes()
    need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'Selected Linux test differs')
    spec=importlib.util.spec_from_file_location('popl_c809_selected_read_process',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    name='test_exited_parent_cannot_strand_a_unix_inherited_pipe'
    suite=unittest.TestSuite([module.ReadProcessTests(name)])
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    text=stream.getvalue();need(len(text.encode())<=65536,'Selected Linux test output exceeds64KiB')
    record={'method':'tests_python.test_read_process.ReadProcessTests.'+name,
        'source_sha256':sha(raw),'tests_run':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'skipped':len(result.skipped),'success':result.wasSuccessful(),
        'output':text,'other_test_bodies_run':0}
    save(OUT/'SELECTED_LINUX_TEST.json',record)
    need(result.testsRun==1 and result.wasSuccessful()and not result.skipped,'Selected Linux check did not pass')

def main():
    parser=argparse.ArgumentParser()
    for name in ('source-manifest','base','jobs','cases'):parser.add_argument('--'+name+'-sha256',required=True)
    args=parser.parse_args()
    need(os.geteuid()==65534 and os.readlink('/proc/self/ns/net')!=os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'],'Private unprivileged lab required')
    for module,pin in ((B,args.base_sha256),(J,args.jobs_sha256),(C,args.cases_sha256)):
        need(sha(Path(module.__file__).read_bytes())==pin,'Frozen setup helper differs')
    OUT.mkdir(mode=0o700,exist_ok=False)
    source=B.validate_source(args.source_manifest_sha256)
    for name,(size,pin)in B.INPUTS.items():
        raw=(LAB/'inputs'/name).read_bytes();need(len(raw)==size and sha(raw)==pin,'Copied fixture input differs')
    need(sha((LAB/'tools/cast').read_bytes())==B.CAST_SHA,'Cast differs')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(SOURCE))
    selected_linux_test(source)
    rows=B.json_file(LAB/'inputs/instances.json')
    addresses={row['role']:row['address'].lower()for row in rows};pins={row['role']:row['runtime_keccak256'].lower()for row in rows}
    need(len(rows)==len(addresses)==len(set(addresses.values()))==39,'Exact F6 graph required')
    tmp=OUT/'tmp';tmp.mkdir(mode=0o700)
    env={'TMPDIR':str(tmp),'PATH':str(LAB/'tools')+':/usr/bin:/bin','LANG':'C.UTF-8',
        'HOME':str(OUT/'unadopted-home'),'PYTHONPATH':str(SOURCE),'PYTHONDONTWRITEBYTECODE':'1'}
    os.environ.update(env)
    work,events=J.Work(),J.Events()
    case=C.Case('supervisor',work,env,addresses,pins,rows,B.json_file(LAB/'inputs/bindings.json'),events)
    stop=__import__('threading').Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set());signal.signal(signal.SIGINT,lambda *_:stop.set())
    result={'schema':1,'success':False,'source_head':source['source_head'],
        'old_feature_journeys_or_tests_run':0,'public_transactions':0,'new_seals':0,
        'production_approved':False,'restart_proof_requires_root_systemd_evidence':True}
    try:
        case.start()
        case.configure(maintenance={'compound':False,'compound_idle':False,'harvest':False,
            'minimum_liquidity':1,'harvest_interval_seconds':3600})
        case.model.review['allowed']=[]
        case.lock_guard.__exit__(None,None,None);case.lock_guard=None;case.k=None
        journal=Path(case.cfg['state_path']);initial=journal.read_bytes();state=json.loads(initial)
        need(state['pending']is None and state['next_nonce']==0 and not state['spent'],'Unused original keeper journal required')
        need(all(int(case.model.rpc('eth_getTransactionCount',[case.sender,tag]),16)==0 for tag in ('latest','pending')),'Setup changed keeper nonce')
        need(case.uint('strategy','needsRebalance(uint256)',J.BUCKET)==0 and
             case.uint('strategy','rangeUpdatePending(uint256)',J.BUCKET)==0,'Ordinary rebalance/range change is due')
        need(case.words('rebalance_confirmation','observations(uint256)',J.BUCKET)==[0,0,0,0]and
             case.words('rebalance_confirmation','marketSides(uint256)',J.BUCKET)==[0,0],
             'Idle partition requires empty samples and neither market at the adjustment threshold')
        from keeper.compound_policy import classify_range
        physical=case.physical();ticks=physical['ticks'];ticks=[x-2**256 if x>=2**255 else x for x in ticks]
        slot=case.words(B.STATE,'getSlot0(bytes32)',J.POOL);tick=slot[1]-2**256 if slot[1]>=2**255 else slot[1]
        need(classify_range(lower=ticks[0],upper=ticks[1],tick=tick,range_update_pending=False)['in_range'],'Main LP is not physically in range')
        before={'rights':case.rights(),'physical':physical,'money':case.money()}
        save(case.folder/'INITIAL_JOURNAL.json',{'sha256':sha(initial),'raw_utf8':initial.decode(),'state':state})
        save(case.folder/'FINANCIAL_BEFORE.json',before)
        good=case.config_path.read_bytes();save(case.folder/'GOOD_CONFIG.json',copy.deepcopy(case.cfg))
        need((case.folder/'GOOD_CONFIG.json').read_bytes()==good,'Good configuration archive bytes differ')
        # B.save intentionally refuses an existing path. Only this one owned
        # lab config may be atomically replaced; the original journal is never
        # rewritten during invalid restarts.
        from zzz_ops.state import atomic_json
        bad=copy.deepcopy(case.cfg);bad['interval_seconds']=0
        need(case.config_path==case.folder/'actor/config.json'and not case.config_path.is_symlink(),
             'Owned bad-config target differs')
        atomic_json(case.config_path,bad)
        need(journal.read_bytes()==initial,'Invalid config preparation changed original journal')
        for _ in range(12):case.advance()
        case.model.rpc('evm_setIntervalMining',[1])
        save(OUT/'READY.json',{'source_head':source['source_head'],'namespace':os.readlink('/proc/self/ns/net'),
            'configuration_path':str(case.config_path),'bad_configuration_sha256':sha(case.config_path.read_bytes()),
            'good_configuration_path':str(case.folder/'GOOD_CONFIG.json'),'good_configuration_sha256':sha(good),
            'original_journal_sha256':sha(initial),'state_path':str(journal),'health_path':case.cfg['health_path'],
            'sender':case.sender,'monitor_argv':['/usr/bin/python3','-m','keeper.monitor','--config',str(case.config_path),'--live'],
            'monitor_working_directory':str(SOURCE),'watchdog_seconds_required':120,
            'invalid_interval_fails_before_constructor_and_signer':True,'all_financial_jobs_disabled':True})
        healthy=False
        while not stop.wait(.2):
            need(time.monotonic()<work.deadline,'Shared900second bound exceeded')
            need(case.model.child.process.poll()is None and not case.model.child.overflow,'Owned Anvil stopped/overflowed')
            need(case.model.raw_send_count==case.model.raw_forwarded==work.raw_attempts==work.raw==0,'Unexpected signer send attempted')
            current=B.json_file(journal)
            need(current.get('pending')is None and current.get('next_nonce')==0 and not current.get('spent'),'Idle restart changed pending/nonce/spending')
            health=Path(case.cfg['health_path'])
            if not healthy and health.exists() and B.json_file(health).get('status')=='healthy_v2':
                need(B.json_file(case.config_path)==case.cfg,'Healthy recovery configuration differs from original240 profile')
                need(case.uint('strategy','needsRebalance(uint256)',J.BUCKET)==0,'Ordinary rebalance became due')
                after={'rights':case.rights(),'physical':case.physical(),'money':case.money()}
                need(after==before,'Idle recovery changed NFT/LP/backing rights')
                need(all(int(case.model.rpc('eth_getTransactionCount',[case.sender,tag]),16)==0 for tag in ('latest','pending')),'Recovered keeper nonce differs')
                save(case.folder/'HEALTHY_IDLE_CYCLE.json',B.json_file(health));save(case.folder/'FINANCIAL_AFTER.json',after)
                save(case.folder/'FINAL_JOURNAL.json',{'sha256':sha(journal.read_bytes()),'raw_utf8':journal.read_text(),'state':current})
                healthy=True;result.update(success=True,healthy_idle_cycle=True,keeper_nonce=0,raw_attempts=0,raw_forwarded=0,
                    shared_RPC_requests=work.count,rights_backing_preserved=True)
                save(OUT/'COMPLETE.json',result)
        need(healthy,'Root stopped before healthy idle recovery')
    except BaseException as exc:
        result.update(success=False,**B.safe_error(exc),failure_stage=case.stage)
    finally:
        case.outcome.update(status='passed'if result['success']else'failed')
        try:result['cleanup']=case.close()
        except BaseException as exc:result.update(success=False,cleanup_error=B.safe_error(exc))
        result.update(shared_RPC_requests=work.count,raw_attempts=work.raw_attempts,raw_forwarded=case.model.raw_forwarded,
            secret_disposition='fresh local lab only; no credential content/hash exported')
        save(OUT/'RESULT.json',result)
    return 0 if result['success']else 1

if __name__=='__main__':raise SystemExit(main())
