"""PREPARATION ONLY: c811 accepted-hash EACCES with the stock normal daemon.

One new fault composition, authenticated copied F6 state and one real local
harvest. Root supplies independent native exit/fence/restart/resolver evidence.
No prior test body, feature journey, public action or live adoption is executed.
"""
from pathlib import Path
import argparse
import copy
import datetime as dt
import json
import os
import re
import signal
import stat
import sys
import threading
import time

import keeper_runtime as B
import keeper_jobs as J
import job_cases as C

LAB = Path('/opt/popl-ubuntu-daemon-storage-20261126-c811')
SOURCE = LAB / 'source/contracts'
OUT = LAB / 'runtime/run-001/model'
CONTROL = LAB / 'control'
for module in (B, J, C):
    module.LAB, module.SOURCE, module.OUT = LAB, SOURCE, OUT
need, save, sha = B.need, B.save, B.sha
SOURCE_HEAD = 'c07d5b153149f7c072ee5ff785c1cabac60197f6'
MONITOR_SHA = '90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'
TX_FIELDS = ('hash', 'from', 'to', 'input', 'nonce', 'value', 'gas', 'gasPrice',
             'type', 'chainId', 'maxFeePerGas', 'maxPriorityFeePerGas',
             'blockHash', 'blockNumber', 'transactionIndex')


def snapshot(path):
    with path.open('rb') as handle:
        raw = handle.read(2 * 1024 * 1024 + 1)
    need(len(raw) <= 2 * 1024 * 1024, 'Owned checkpoint read exceeds bound')
    return {'sha256': sha(raw), 'raw_utf8': raw.decode('utf-8', 'strict'),
            'state': json.loads(raw)}


def marker():
    path = CONTROL / 'RESOLUTION_COMPLETE.json'
    try:
        item = path.lstat()
    except FileNotFoundError:
        return None
    need(stat.S_ISREG(item.st_mode) and not path.is_symlink() and
         item.st_uid == 0 and item.st_nlink == 1 and not item.st_mode & 0o022 and
         0 < item.st_size <= 16384, 'Root resolution marker identity differs')
    return B.json_file(path)


class Model(J.Model):
    def __init__(self, folder, work):
        super().__init__(folder, work)
        self.case = None
        self.accepted = None

    def start(self, env):
        need(sha(self.binary.read_bytes()) == B.ANVIL_SHA, 'Anvil bytes differ')
        self.controlled_genesis_timestamp = int(time.time())
        self.child = B.Child([
            self.binary, '--host', '127.0.0.1', '--port', '19591', '--accounts', '0',
            '--silent', '--chain-id', '4663', '--hardfork', 'cancun',
            '--gas-limit', '32000000', '--gas-price', '1000000000',
            '--block-base-fee-per-gas', '1', '--timestamp',
            str(self.controlled_genesis_timestamp), '--load-state',
            LAB / 'inputs/restore-state.json'], self.folder, env, self.folder / 'anvil')
        deadline = time.monotonic() + 20
        while True:
            need(self.child.process.poll() is None and not self.child.overflow,
                 'Owned model startup failed')
            if B.owns(self.child.process.pid, 19591):
                try:
                    if self.rpc('eth_chainId', []) == '0x1237':
                        break
                except (ConnectionError, OSError):
                    pass
            need(time.monotonic() < deadline, 'Owned model startup deadline')
            time.sleep(.1)
        head = self.rpc('eth_getBlockByNumber', ['latest', False])
        need(head['hash'].lower() == B.IMPORTED_HASH and
             int(head['gasLimit'], 16) == 32000000, 'Copied F6 anchor differs')
        return head

    def guard(self):
        # Inherited guard authenticates durable intent, config, approved job,
        # sender, free nonce and the unchanged financial envelope before send.
        need(self.accepted is None and self.raw_send_count ==
             self.work.raw_attempts == 1 and self.raw_forwarded == 0,
             'Only one fresh raw submission is admitted')
        super().guard()
        need(self.work.raw == 1, 'Only one guarded harvest is admitted')

    def request(self, request):
        answer = super().request(request)
        if request['method'] != 'eth_sendRawTransaction':
            return answer
        # The actual node has accepted these signed bytes. Never retain those
        # bytes or signature fields; only exact public intent/receipt vectors.
        case = self.case
        value = answer.get('result')
        need(case is not None and self.accepted is None and
             type(value) is str and re.fullmatch(r'0x[0-9a-f]{64}', value) and
             int(value, 16) != 0 and 'error' not in answer,
             'Actual node did not accept the original signed harvest')
        journal = Path(case.cfg['state_path'])
        captured = snapshot(journal)
        state = captured['state']
        pending = state.get('pending')
        need(type(pending) is dict and pending.get('hash') is None and
             pending['nonce'] == state['next_nonce'] == 0 and
             pending['key'] == 'harvest:' + str(J.BUCKET) and
             pending['to'] == case.a['vault'] and pending['value'] == 0 and
             self.raw_send_count == self.raw_forwarded == self.work.raw_attempts ==
             self.work.raw == 1, 'Durable accepted-boundary intent differs')
        transaction = self.rpc('eth_getTransactionByHash', [value])
        fee = pending['fee_review']
        from zzz_ops.ethereum_fees import fee_cap, transaction_chain_id
        need(type(transaction) is dict and transaction['hash'] == value and
             transaction['from'].lower() == case.sender and
             transaction['to'].lower() == pending['to'] and
             transaction['input'] == pending['data'] and
             int(transaction['nonce'], 16) == 0 and
             int(transaction['value'], 16) == 0 and
             transaction_chain_id(transaction) == 4663 and
             int(transaction['gas'], 16) == fee['gas_limit'] <= 24000000 and
             fee_cap(transaction) == fee['max_fee_per_gas'] <= 5000000000 and
             transaction.get('blockNumber') is None and
             self.rpc('eth_getTransactionReceipt', [value]) is None and
             int(self.rpc('eth_getTransactionCount', [case.sender,'latest']),16) == 0 and
             int(self.rpc('eth_getTransactionCount', [case.sender,'pending']),16) == 1,
             'Actual accepted unmined signed transaction differs')
        actor = case.folder / 'actor'
        identity = actor.lstat()
        need(journal == actor / 'state.json' and not actor.is_symlink() and
             stat.S_ISDIR(identity.st_mode) and identity.st_uid == os.getuid() and
             stat.S_IMODE(identity.st_mode) == 0o700 and
             sha(case.config_path.read_bytes()) == self.review['config_sha'],
             'Only the fresh owned actor directory may lose write permission')
        # Genuine EACCES: the stock unprivileged daemon must fail its own
        # atomic hash publication. The existing file remains fully readable.
        os.chmod(actor, 0o500)
        need(stat.S_IMODE(actor.lstat().st_mode) == 0o500 and
             journal.read_bytes().decode('utf-8', 'strict') == captured['raw_utf8'],
             'Fault did not preserve the original hashless journal')
        self.accepted = {
            'accepted_hash': value, 'utc': time.time(), 'monotonic': time.monotonic(),
            'journal_sha256': captured['sha256'],
            'journal_raw_utf8': captured['raw_utf8'], 'state': state,
            'intent': copy.deepcopy(pending),
            'configuration_sha256': self.review['config_sha'],
            'semantic_configuration_sha256': sha(B.enc(case.cfg)),
            'actor_path': str(actor), 'actor_device': identity.st_dev,
            'actor_inode': identity.st_ino, 'mode_before': '0700', 'mode_fault': '0500',
            'node_accepted_before_permission_change': True,
            'permission_change_before_original_hash_response': True,
            'unmined_at_capture': True, 'raw_signature_retained': False,
            'transaction_without_signature': {k: transaction.get(k) for k in TX_FIELDS},
            'native_exit_and_original_EACCES_diagnostics_require_root_evidence': True,
        }
        save(case.folder / 'HASH_SAVE_FAULT_ARMED.json', self.accepted)
        case.stage = 'await_actual_daemon_EACCES_exit_and_root_repair'
        # The inherited closed gateway serializes this ORIGINAL answer to real
        # Cast. No monkeypatch or fabricated signer result is involved.
        return answer


C.Model = Model


def main():
    parser = argparse.ArgumentParser()
    for name in ('source-manifest', 'base', 'jobs', 'cases'):
        parser.add_argument('--' + name + '-sha256', required=True)
    args = parser.parse_args()
    need(os.geteuid() == 65534 and os.readlink('/proc/self/ns/net') !=
         os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'], 'Private unprivileged lab required')
    for module, digest in ((B, args.base_sha256), (J, args.jobs_sha256),
                           (C, args.cases_sha256)):
        need(sha(Path(module.__file__).read_bytes()) == digest, 'Frozen setup helper differs')
    OUT.mkdir(mode=0o700, exist_ok=False)
    source = B.validate_source(args.source_manifest_sha256)
    need(source['source_head'] == SOURCE_HEAD and
         sha((SOURCE / 'keeper/monitor.py').read_bytes()) == MONITOR_SHA,
         'Current exact daemon source required')
    for name, (size, digest) in B.INPUTS.items():
        raw = (LAB / 'inputs' / name).read_bytes()
        need(len(raw) == size and sha(raw) == digest, 'Copied F6 input differs')
    need(sha((LAB / 'tools/cast').read_bytes()) == B.CAST_SHA, 'Cast differs')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    rows = B.json_file(LAB / 'inputs/instances.json')
    addresses = {row['role']: row['address'].lower() for row in rows}
    pins = {row['role']: row['runtime_keccak256'].lower() for row in rows}
    need(len(rows) == len(addresses) == len(set(addresses.values())) == 39,
         'Exact F6 graph required')
    tmp = OUT / 'tmp'
    tmp.mkdir(mode=0o700)
    env = {'TMPDIR': str(tmp), 'PATH': str(LAB / 'tools') + ':/usr/bin:/bin',
           'LANG': 'C.UTF-8', 'HOME': str(OUT / 'unadopted-home'),
           'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1'}
    os.environ.update(env)
    work, events = J.Work(), J.Events()
    case = C.Case('supervisor', work, env, addresses, pins, rows,
                  B.json_file(LAB / 'inputs/bindings.json'), events)
    case.model.case = case
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    result = {'schema': 1, 'success': False, 'source_head': source['source_head'],
              'old_feature_journeys_or_tests_run': 0, 'public_transactions': 0,
              'new_seals': 0, 'production_approved': False,
              'full_daemon_native_phase_proof_requires_root_evidence': True}
    try:
        case.start()
        case.configure(maintenance={'compound': False, 'compound_idle': False,
            'harvest': True, 'minimum_liquidity': 1, 'harvest_interval_seconds': 3600})
        need(case.cfg['interval_seconds'] == 240 and case.cfg['confirmations'] == 12 and
             case.cfg['execution_quality_version'] == 1 and
             case.cfg['rebalance_confirmation_version'] == 3,
             'Fresh daemon profile and unchanged recovery cadence required')
        case.model.review['allowed'] = [('harvest', 'vault', 'collectFees(uint256,uint256)')]
        case.lock_guard.__exit__(None, None, None)
        case.lock_guard, case.k = None, None
        journal = Path(case.cfg['state_path'])
        initial = snapshot(journal)
        need(initial['state']['pending'] is None and initial['state']['next_nonce'] == 0 and
             not initial['state']['spent'], 'Unused original keeper journal required')
        need(all(int(case.model.rpc('eth_getTransactionCount', [case.sender, tag]), 16) == 0
                 for tag in ('latest', 'pending')), 'Private setup changed keeper nonce')
        need(case.uint('strategy', 'needsRebalance(uint256)', J.BUCKET) == 0 and
             case.uint('strategy', 'rangeUpdatePending(uint256)', J.BUCKET) == 0 and
             case.words('rebalance_confirmation', 'observations(uint256)', J.BUCKET) == [0,0,0,0] and
             case.words('rebalance_confirmation', 'marketSides(uint256)', J.BUCKET) == [0,0],
             'Harvest-only partition requires no rebalance or observation need')
        before = {'rights': case.rights(), 'physical': case.physical(), 'money': case.money()}
        save(case.folder / 'INITIAL_JOURNAL.json', initial)
        save(case.folder / 'FINANCIAL_BEFORE.json', before)
        for _ in range(12):
            case.advance()
        # Automine remains false and interval zero: resolver adoption happens
        # before inclusion. Root marker is mandatory before controlled mining.
        save(OUT / 'READY.json', {
            'source_head': source['source_head'], 'namespace': os.readlink('/proc/self/ns/net'),
            'configuration_path': str(case.config_path),
            'configuration_sha256': sha(case.config_path.read_bytes()),
            'semantic_configuration_sha256': sha(B.enc(case.cfg)),
            'state_path': str(journal), 'health_path': case.cfg['health_path'],
            'sender': case.sender, 'original_journal_sha256': initial['sha256'],
            'monitor_argv': ['/usr/bin/python3', '-m', 'keeper.monitor', '--config',
                             str(case.config_path), '--live'],
            'monitor_working_directory': str(SOURCE),
            'fault_stage': 'accepted_node_hash_before_Cast_response',
            'only_actor_directory_will_be_chmod_0500': True,
            'all_guard_limits_unchanged': True, 'all_other_financial_jobs_disabled': True,
            'required_root_resolution_marker': str(CONTROL / 'RESOLUTION_COMPLETE.json')})
        blocked, mined, recovered, healthy = False, False, False, False
        recovery_observed_utc = None
        recovery_observed_monotonic = None
        recovery_refresh_health = None
        case.stage = 'await_stock_daemon_first_harvest'
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Shared900second work bound exceeded')
            need(case.model.child.process.poll() is None and not case.model.child.overflow,
                 'Owned Anvil stopped or overflowed')
            need(case.model.raw_send_count <= 1 and work.raw_attempts <= 1 and
                 case.model.raw_forwarded <= 1 and work.raw <= 1, 'Unexpected second raw attempt')
            accepted = case.model.accepted
            if accepted is None:
                continue
            need(sha(case.config_path.read_bytes()) == accepted['configuration_sha256'],
                 'Original complete keeper configuration changed')
            current = snapshot(journal)
            state, pending = current['state'], current['state'].get('pending')
            health_path = Path(case.cfg['health_path'])
            if type(pending) is dict and pending.get('hash') is None:
                need(current['sha256'] == accepted['journal_sha256'],
                     'Original durable hashless journal changed')
                if health_path.exists() and not blocked:
                    health = B.json_file(health_path)
                    if (health.get('status') == 'recovery_required' and
                            health.get('pending') is True and health.get('pending_action') == pending['key'] and
                            dt.datetime.fromisoformat(health['time']).timestamp() >= accepted['utc']):
                        need(stat.S_IMODE((case.folder / 'actor').lstat().st_mode) == 0o700,
                             'Actual hashless restart requires repaired actor directory')
                        save(case.folder / 'HASHLESS_RESTART_BLOCKED.json', {
                            'accepted_hash': accepted['accepted_hash'], 'state': state,
                            'journal_sha256': current['sha256'], 'raw_utf8': current['raw_utf8'],
                            'health': health, 'no_resend': True,
                            'actual_native_exit_repair_restart_requires_root_evidence': True})
                        blocked = True
                        case.stage = 'await_fenced_stock_no_live_resolution'
            elif type(pending) is dict and not recovered:
                expected = copy.deepcopy(accepted['state'])
                expected['pending']['hash'] = accepted['accepted_hash']
                need(blocked and state == expected, 'Resolver must change only the known hash')
                if not mined:
                    control = marker()
                    if control is not None:
                        need(set(control) == {'schema','accepted_hash','state_sha256',
                             'signing_enabled','manager_wait_completion'} and control['schema'] == 1 and
                             control['accepted_hash'] == accepted['accepted_hash'] and
                             control['state_sha256'] == current['sha256'] and
                             control['signing_enabled'] is False and
                             control['manager_wait_completion'] is True,
                             'Explicit fenced no-live resolver marker differs')
                        need(case.model.rpc('eth_getTransactionReceipt', [accepted['accepted_hash']]) is None,
                             'Original transaction mined before explicit resolution')
                        for _ in range(12):
                            case.advance()
                        receipt = case.model.rpc('eth_getTransactionReceipt', [accepted['accepted_hash']])
                        head = case.model.rpc('eth_getBlockByNumber', ['latest', False])
                        need(type(receipt) is dict and receipt['status'] == '0x1' and
                             int(head['number'],16) - int(receipt['blockNumber'],16) + 1 == 12,
                             'Exactly12 controlled confirmations required')
                        save(case.folder / 'RESOLUTION_READY.json', {
                            'accepted_hash': accepted['accepted_hash'],
                            'resolved_journal': current, 'root_marker': control,
                            'receipt': receipt, 'head': head, 'confirmations': 12,
                            'no_raw_submission_during_resolution': True})
                        # Only after recording the exact12-confirmation barrier,
                        # advance ordinary empty blocks on this owned node.
                        # This preserves fresh chain time during the unchanged
                        # 240second daemon wait; it submits no transaction.
                        case.model.rpc('evm_setIntervalMining', [1])
                        save(case.folder / 'POST_RESOLUTION_MINING.json', {
                            'exact12_barrier_recorded_first':True,
                            'owned_node_interval_mining_seconds':1,
                            'automine_remains_disabled':True,
                            'keeper_configuration_or_guard_changed':False,
                            'new_raw_submission':False})
                        mined = True
                        case.stage = 'await_normal_daemon_receipt_recovery'
            elif pending is None and not recovered:
                need(blocked and mined and state['next_nonce'] == 1,
                     'Hashless block, explicit resolver or confirmed recovery missing')
                h = accepted['accepted_hash']
                receipt = case.model.rpc('eth_getTransactionReceipt', [h])
                tx = case.model.rpc('eth_getTransactionByHash', [h])
                block = case.model.rpc('eth_getBlockByNumber', [receipt['blockNumber'], False])
                head = case.model.rpc('eth_getBlockByNumber', ['latest', False])
                intent = accepted['intent']
                need(receipt['status'] == '0x1' and receipt['transactionHash'] == tx['hash'] == h and
                     tx['from'].lower() == case.sender and tx['to'].lower() == intent['to'] and
                     tx['input'] == intent['data'] and int(tx['nonce'],16) == 0 and
                     int(tx['value'],16) == 0 and receipt['blockHash'] == tx['blockHash'] == block['hash'] and
                     receipt['blockNumber'] == tx['blockNumber'] == block['number'] and
                     receipt['transactionIndex'] == tx['transactionIndex'] and
                     int(head['number'],16) - int(block['number'],16) + 1 >= 12,
                     'Actual accepted harvest canonical receipt differs')
                from zzz_ops.ethereum_fees import execution_price
                price = execution_price(tx, block, receipt)
                used, l1 = int(receipt['gasUsed'],16), int(receipt.get('l1Fee','0x0'),16)
                fee, paid = intent['fee_review'], used * price + l1
                need(0 < used <= int(tx['gas'],16) == fee['gas_limit'] <= 24000000 and
                     0 < price <= fee['max_fee_per_gas'] <= 5000000000 and
                     l1 == 0 == fee['l1_fee_allowance_wei'] and fee['receipt_fee_policy'] == 'included' and
                     paid <= fee['maximum_cost_wei'] <= 10**16,
                     'Actual receipt exceeds original captured fee bounds')
                day = dt.datetime.fromtimestamp(int(block['timestamp'],16), dt.timezone.utc).date().isoformat()
                observation = {'transaction':h, 'reported_price_wei':int(receipt['effectiveGasPrice'],16),
                    'execution_price_wei':price, 'gas_used':used, 'l1_fee_wei':l1,
                    'receipt_fee_policy':'included', 'cost_wei':paid}
                need(state['last_fee_observation'] == observation and
                     sum(int(v) for v in state['spent'].values()) == int(state['spent'][day]) == paid and
                     state['last'][intent['key']] == int(block['timestamp'],16) and
                     state['receipt_anchor'] == {'number':int(block['number'],16),
                         'hash':block['hash'], 'timestamp':int(block['timestamp'],16), 'nonce':0} and
                     all(int(case.model.rpc('eth_getTransactionCount',[case.sender,tag]),16) == 1
                         for tag in ('latest','pending')),
                     'Recovered canonical costs, day, harvest clock or nonce differ')
                recovery_observed_utc = time.time()
                recovery_observed_monotonic = time.monotonic()
                save(case.folder / 'RECOVERED_JOURNAL.json', {
                    'accepted_hash':h, 'journal':current, 'paid_wei':paid,
                    'receipt':receipt, 'receipt_block':block, 'head':head,
                    'recovery_observed_utc':recovery_observed_utc,
                    'recovery_observed_monotonic':recovery_observed_monotonic,
                    'transaction_without_signature':{k:tx.get(k) for k in TX_FIELDS},
                    'native_normal_daemon_recovery_requires_root_evidence':True})
                case.receipts.append({'action':intent['key'], 'hash':h, 'intent':intent,
                    'receipt':receipt, 'actual_transaction_checked':True,
                    'confirmations':12, 'explicit_hash_resolution':True})
                recovered = True
                case.stage = 'await_next_normal_240second_cycle'
            if recovered and health_path.exists():
                health = B.json_file(health_path)
                if (recovery_refresh_health is None and health.get('status') == 'degraded' and
                        health.get('pending') is False and
                        health.get('rebalance_confirmation_health',{}).get('policy',{}).get('state') ==
                        'pending_recovery'):
                    recovery_refresh_health = health
                    save(case.folder / 'RECOVERY_REFRESH_HEALTH.json', health)
                if (health.get('status') == 'healthy_v2' and health.get('pending') is False and
                        health.get('pending_action') is None and
                        health.get('configuration_sha256') == accepted['semantic_configuration_sha256'] and
                        health.get('sender') == case.sender and health.get('chain_id') == 4663 and
                        health.get('live') is True and
                        dt.datetime.fromisoformat(health['time']).timestamp() >= recovery_observed_utc):
                    need(recovery_refresh_health is not None,
                         'Distinct degraded receipt-recovery cycle was not observed')
                    health_time = dt.datetime.fromisoformat(health['time']).timestamp()
                    refresh_time = dt.datetime.fromisoformat(recovery_refresh_health['time']).timestamp()
                    elapsed = time.monotonic() - recovery_observed_monotonic
                    need(health_time - refresh_time >= 239 and elapsed >= 239,
                         'Fresh healthy cycle did not retain the normal240second wait')
                    save(case.folder / 'HEALTHY_NORMAL_CYCLE.json', health)
                    save(case.folder / 'HEALTHY_TIMING.json', {
                        'configured_interval_seconds':240,
                        'configured_confirmations':12,
                        'recovery_health_utc':refresh_time, 'healthy_health_utc':health_time,
                        'health_elapsed_seconds':health_time-refresh_time,
                        'recovery_observed_utc':recovery_observed_utc,
                        'monotonic_elapsed_seconds':elapsed,
                        'minimum_observation_allowance_seconds':239,
                        'poll_delay_or_configuration_changed':False})
                    save(case.folder / 'HEALTHY_JOURNAL.json', snapshot(journal))
                    healthy = True
                    break
        need(blocked and mined and recovered and healthy, 'Complete normal daemon recovery not observed')
        after = {'rights':case.rights(), 'physical':case.physical(), 'money':case.money()}
        need(before == after, 'Zero-fee storage harvest changed rights, LP or classified backing')
        save(case.folder / 'FINANCIAL_AFTER.json', after)
        need(case.model.raw_send_count == case.model.raw_forwarded == work.raw_attempts == work.raw == 1,
             'Successful recovery repeated a raw submission')
        B.validate_source(args.source_manifest_sha256)
        need(all(sha((LAB/'inputs'/name).read_bytes()) == digest
                 for name,(_,digest) in B.INPUTS.items()), 'Original copied F6 inputs changed')
        result.update(success=True, accepted_hash=case.model.accepted['accepted_hash'],
            hashless_restart_blocked=True, explicit_no_live_resolution=True,
            confirmations=12, fresh_normal_healthy_cycle=True,
            principal_rewards_backing_preserved=True, source_fixture_config_preserved=True)
        save(OUT/'COMPLETE.json', result)
        case.stage = 'await_root_keeper_fence_then_model_stop'
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Root cleanup exceeded shared900second bound')
            need(case.model.raw_send_count == work.raw_attempts == 1, 'Unexpected send after healthy cycle')
    except Exception as exc:
        result.update(B.safe_error(exc), failure_stage=case.stage)
        result['success'] = False
    finally:
        # Root must stop/fence keeper before stopping this model. Capture final
        # original checkpoint bytes after that fence, separately from recovery.
        cleanup = None
        try:
            journal = Path(case.cfg['state_path']) if case.cfg else None
            if journal is not None and journal.exists():
                save(case.folder/'FINAL_JOURNAL.json', snapshot(journal))
        except Exception as exc:
            result.update(success=False, final_checkpoint_capture_error=B.safe_error(exc))
        finally:
            case.outcome.update(status='passed' if result['success'] else 'failed')
            try:
                cleanup = case.close()
            except Exception as exc:
                result.update(success=False, owned_model_cleanup_error=B.safe_error(exc))
        result.update(cleanup=cleanup, shared_RPC_requests=work.count,
            raw_attempts=work.raw_attempts, raw_forwarded=case.model.raw_forwarded,
            secret_disposition='retained only in new owned lab; no contents or hashes exported')
        try:
            save(OUT/'EVENTS.json', {'fixture_setup_events':''.join(events.parts)})
        except Exception as exc:
            result.update(success=False, event_capture_error=B.safe_error(exc))
        try:
            save(OUT/'RESULT.json', result)
        except Exception:
            # All child cleanup was already attempted. Root independently
            # fences the fixed units and refuses missing final evidence.
            return 1
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
