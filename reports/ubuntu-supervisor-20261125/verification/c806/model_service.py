"""DRAFT c806: withhold a real accepted Cast reply while native main is killed.

Requires separate root native PID/cgroup evidence and an explicit stock resolver.
No c804 execution, header/body framing case, or previous feature journey runs.
"""
from pathlib import Path
import argparse
import datetime as dt
import http.client
import json
import os
import re
import select
import signal
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import keeper_runtime as B
import keeper_jobs as J
import job_cases as C
import model_service_base as F

LAB = Path('/opt/popl-ubuntu-supervisor-20261125-c806')
SOURCE = LAB / 'source/contracts'
OUT = LAB / 'runtime/run-001/model'
for module in (B, J, C, F):
    module.LAB, module.SOURCE, module.OUT = LAB, SOURCE, OUT
C.Model = F.Model
need, save, sha = B.need, B.save, B.sha
TX_FIELDS = ('hash', 'from', 'to', 'input', 'nonce', 'value', 'gas', 'gasPrice',
             'type', 'chainId', 'maxFeePerGas', 'maxPriorityFeePerGas',
             'blockHash', 'blockNumber', 'transactionIndex')


class Peer:
    def __init__(self, case):
        self.case = case
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.held = None
        self.closed = None
        self.count = 0
        peer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.connection.settimeout(30)
                identifier = None
                method = None
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    need(0 < size <= B.MAX_REQUEST, 'Signer frontend request bound')
                    body = self.rfile.read(size)
                    q = json.loads(body)
                    need(type(q) is dict and q.get('jsonrpc') == '2.0' and
                         type(q.get('id')) is int and type(q.get('method')) is str,
                         'Signer frontend envelope differs')
                    identifier = q['id']
                    method = q['method']
                    need(method in B.READ_METHODS | {'eth_sendRawTransaction'},
                         'Signer frontend method differs')
                    with peer.lock:
                        peer.count += 1
                        need(peer.count <= 6000 and
                             time.monotonic() < case.model.work.deadline,
                             'Signer frontend work bound')
                    conn = http.client.HTTPConnection('127.0.0.1', 19592, timeout=30)
                    try:
                        conn.request('POST', '/', body, {'Content-Type': 'application/json'})
                        response = conn.getresponse()
                        need(response.status == 200, 'Signer upstream HTTP differs')
                        payload = response.read(B.MAX_RESPONSE + 1)
                        need(len(payload) <= B.MAX_RESPONSE, 'Signer response bound')
                    finally:
                        conn.close()
                    if method == 'eth_sendRawTransaction':
                        answer = json.loads(payload)
                        h = answer.get('result')
                        need(type(answer) is dict and answer.get('id') == identifier and
                             type(h) is str and re.fullmatch(r'0x[0-9a-f]{64}', h) and
                             int(h, 16) != 0 and 'error' not in answer,
                             'Actual node did not accept first signed transaction')
                        journal = Path(case.cfg['state_path'])
                        raw = journal.read_bytes()
                        state = json.loads(raw)
                        pending = state.get('pending')
                        need(type(pending) is dict and pending.get('hash') is None and
                             pending['nonce'] == state['next_nonce'] == 0 and
                             pending['key'] == 'harvest:' + str(J.BUCKET) and
                             pending['to'] == case.a['vault'] and
                             case.model.raw_forwarded == case.model.work.raw ==
                             case.model.work.raw_attempts == 1,
                             'Durable pre-response hashless intent differs')
                        tx = case.model.rpc('eth_getTransactionByHash', [h])
                        need(type(tx) is dict and tx['hash'] == h and
                             tx['from'].lower() == case.sender and
                             tx['to'].lower() == pending['to'] and
                             tx['input'] == pending['data'] and
                             int(tx['nonce'], 16) == 0 and int(tx['value'], 16) == 0,
                             'Actual accepted signed transaction differs')
                        with peer.lock:
                            need(peer.held is None, 'Only one accepted reply may be held')
                            peer.held = {
                                'accepted_hash': h, 'journal_sha256': sha(raw),
                                'journal_raw_utf8': raw.decode('utf-8', 'strict'),
                                'intent': pending, 'state': state,
                                'utc': time.time(), 'monotonic': time.monotonic(),
                                'maximum_hold_seconds': 75,
                                'actual_Cast_liveness_requires_native_capture': True,
                                'actual_node_accepted_before_withholding': True,
                                'no_raw_signature_or_request_params_retained': True,
                                'unmined_at_observation': tx.get('blockNumber') is None,
                                'transaction_without_signature': {k: tx.get(k) for k in TX_FIELDS},
                            }
                            save(case.folder / 'CAST_REPLY_HELD.json', peer.held)
                        started = time.monotonic()
                        disconnected = False
                        while (not peer.stop.is_set() and
                               time.monotonic() - started < 75):
                            readable, _, _ = select.select([self.connection], [], [], .2)
                            if readable and self.connection.recv(1, socket.MSG_PEEK) == b'':
                                disconnected = True
                                break
                        peer.closed = {
                            'accepted_hash': h, 'utc': time.time(),
                            'monotonic': time.monotonic(),
                            'elapsed_seconds': time.monotonic() - started,
                            'client_disconnected_before_reply': disconnected,
                            'reply_returned': False,
                            'native_Cast_death_requires_root_receipt': True,
                        }
                        save(case.folder / 'CAST_CLIENT_CLOSED.json', peer.closed)
                        # On native death retain the accepted hash as evidence;
                        # no response retry, additional send, or journal adoption.
                        if disconnected or peer.stop.is_set():
                            self.close_connection = True
                            return
                except Exception as exc:
                    payload = B.enc({'jsonrpc': '2.0', 'id': identifier,
                                     'error': {'code': -32072,
                                               'message': 'Owned signer frontend refused'}})
                    if not (case.folder / 'FRONTEND_REFUSAL.json').exists():
                        save(case.folder / 'FRONTEND_REFUSAL.json', B.safe_error(exc))
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    if method == 'eth_sendRawTransaction' and peer.closed is not None:
                        save(case.folder / 'HELD_REPLY_RETURNED.json', {
                            'accepted_hash': peer.held['accepted_hash'],
                            'utc': time.time(), 'manual_native_kill_not_observed_by_peer': True})
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 19593), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        need(not self.thread.is_alive(), 'Signer frontend did not stop')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-manifest-sha256', required=True)
    parser.add_argument('--base-sha256', required=True)
    parser.add_argument('--jobs-sha256', required=True)
    parser.add_argument('--cases-sha256', required=True)
    parser.add_argument('--base-model-sha256', required=True)
    args = parser.parse_args()
    need(os.geteuid() == 65534 and os.readlink('/proc/self/ns/net') !=
         os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'], 'Private unprivileged signer lab required')
    for module, digest in ((B, args.base_sha256), (J, args.jobs_sha256),
                           (C, args.cases_sha256), (F, args.base_model_sha256)):
        need(sha(Path(module.__file__).read_bytes()) == digest, 'Frozen signer helper differs')
    OUT.mkdir(mode=0o700, exist_ok=False)
    source = B.validate_source(args.source_manifest_sha256)
    need(source['source_head'] == '7f862557df8e8cbaf8494c7b1c12f18e07be436d' and
         len(source['members']) == 190, 'Exact190member production source required')
    for name, (size, digest) in B.INPUTS.items():
        raw = (LAB / 'inputs' / name).read_bytes()
        need(len(raw) == size and sha(raw) == digest, 'Copied signer fixture differs')
    need(sha((LAB / 'tools/cast').read_bytes()) == B.CAST_SHA, 'Cast differs')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    rows = B.json_file(LAB / 'inputs/instances.json')
    addresses = {r['role']: r['address'].lower() for r in rows}
    pins = {r['role']: r['runtime_keccak256'].lower() for r in rows}
    need(len(rows) == len(addresses) == len(set(addresses.values())) == 39,
         'Exact F6 normal graph required')
    tmp = OUT / 'tmp'
    tmp.mkdir(mode=0o700)
    env = {'TMPDIR': str(tmp), 'PATH': str(LAB / 'tools') + ':/usr/bin:/bin',
           'LANG': 'C.UTF-8', 'HOME': str(OUT / 'unadopted-home'),
           'PYTHONPATH': str(SOURCE), 'PYTHONDONTWRITEBYTECODE': '1'}
    os.environ.update(env)
    work, events = J.Work(), J.Events()
    case = C.Case('supervisor', work, env, addresses, pins, rows,
                  B.json_file(LAB / 'inputs/bindings.json'), events)
    peer = None
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    result = {'schema': 1, 'success': False, 'controlled_copied_state': True,
              'public_transactions': 0, 'new_seals': 0,
              'old_feature_journeys_or_tests_run': 0, 'production_approved': False,
              'native_active_Cast_cleanup_requires_root_receipt': True,
              'manual_SIGKILL_main_case_not_watchdog_case': True}
    try:
        case.start()
        peer = Peer(case)
        case.configure(rpc_urls=['http://127.0.0.1:19593'], maintenance={
            'compound': False, 'compound_idle': False, 'harvest': True,
            'minimum_liquidity': 1, 'harvest_interval_seconds': 3600})
        case.model.review['allowed'] = [('harvest', 'vault', 'collectFees(uint256,uint256)')]
        case.lock_guard.__exit__(None, None, None)
        case.lock_guard = None
        case.k = None
        journal = Path(case.cfg['state_path'])
        raw = journal.read_bytes()
        initial = json.loads(raw)
        need(initial['pending'] is None and initial['next_nonce'] == 0, 'Unused signer journal required')
        before = {'rights': case.rights(), 'physical': case.physical(), 'money': case.money()}
        save(case.folder / 'INITIAL_JOURNAL.json', {
            'sha256': sha(raw), 'raw_utf8': raw.decode('utf-8'), 'state': initial})
        save(case.folder / 'FINANCIAL_BEFORE.json', before)
        for _ in range(12):
            case.advance()
        case.model.rpc('evm_setIntervalMining', [1])
        save(OUT / 'READY.json', {
            'model_pid': os.getpid(), 'namespace': os.readlink('/proc/self/ns/net'),
            'source_head': source['source_head'], 'sender': case.sender,
            'configuration_path': str(case.config_path),
            'configuration_sha256': sha(case.config_path.read_bytes()),
            'state_path': case.cfg['state_path'], 'health_path': case.cfg['health_path'],
            'monitor_argv': ['/usr/bin/python3', '-m', 'keeper.monitor',
                             '--config', str(case.config_path), '--live'],
            'monitor_working_directory': str(SOURCE),
            'actual_active_Cast_native_capture_required': True,
            'manual_SIGKILL_main_required_within_seconds_of_CAST_REPLY_HELD': True,
            'resolver_required': 'stock --resolve-pending accepted_hash after native hashless restart proof',
            'all_guard_limits_unchanged': True})
        blocked = False
        recovered = False
        healthy = False
        case.stage = 'native_wait_for_active_Cast_kill'
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Shared900second signer work bound')
            need(case.model.child.process.poll() is None and not case.model.child.overflow,
                 'Owned signer Anvil stopped/overflowed')
            if peer.held is None:
                continue
            need(not (case.folder / 'HELD_REPLY_RETURNED.json').exists(),
                 'Original Cast reply returned before native cleanup proof')
            state = B.json_file(journal)
            pending = state.get('pending')
            health_path = Path(case.cfg['health_path'])
            if type(pending) is dict and pending.get('hash') is None:
                need(sha(journal.read_bytes()) == peer.held['journal_sha256'],
                     'Hashless journal changed before explicit stock resolution')
                if peer.closed is not None and health_path.exists() and not blocked:
                    health = B.json_file(health_path)
                    if (health.get('status') == 'recovery_required' and health.get('pending') is True and
                            health.get('pending_action') == pending['key']):
                        stamp = dt.datetime.fromisoformat(health['time']).timestamp()
                        if stamp >= peer.closed['utc']:
                            need(work.raw_attempts == work.raw == case.model.raw_forwarded == 1,
                                 'Hashless restart attempted another send')
                            save(case.folder / 'HASHLESS_RESTART_BLOCKED.json', {
                                'accepted_hash': peer.held['accepted_hash'],
                                'journal_sha256': sha(journal.read_bytes()),
                                'raw_utf8': journal.read_text(encoding='utf-8'),
                                'state': state, 'health': health, 'no_resend': True,
                                'native_restart_requires_root_receipt': True,
                                'explicit_stock_resolver_required': True})
                            blocked = True
                            case.stage = 'await_explicit_stock_resolver'
            elif type(pending) is dict:
                expected = dict(peer.held['intent'], hash=peer.held['accepted_hash'])
                need(blocked and pending == expected,
                     'Only accepted known hash may be explicitly resolved after restart proof')
            elif not recovered:
                need(blocked and peer.closed is not None and
                     peer.closed['client_disconnected_before_reply'] is True and
                     state['next_nonce'] == 1, 'Native cleanup/hashless block/resolution incomplete')
                h = peer.held['accepted_hash']
                receipt = case.model.rpc('eth_getTransactionReceipt', [h])
                tx = case.model.rpc('eth_getTransactionByHash', [h])
                block = case.model.rpc('eth_getBlockByNumber', [receipt['blockNumber'], False])
                head = case.model.rpc('eth_getBlockByNumber', ['latest', False])
                p = peer.held['intent']
                need(receipt['status'] == '0x1' and receipt['transactionHash'] == tx['hash'] == h and
                     tx['from'].lower() == case.sender and tx['to'].lower() == p['to'] and
                     tx['input'] == p['data'] and int(tx['nonce'], 16) == 0 and
                     int(tx['value'], 16) == 0 and
                     receipt['blockHash'] == tx['blockHash'] == block['hash'] and
                     receipt['blockNumber'] == tx['blockNumber'] == block['number'] and
                     receipt['transactionIndex'] == tx['transactionIndex'] and
                     int(head['number'], 16) - int(block['number'], 16) + 1 >= 12,
                     'Actual accepted transaction canonical inclusion differs')
                from zzz_ops.ethereum_fees import execution_price
                price = execution_price(tx, block, receipt)
                reported = int(receipt['effectiveGasPrice'], 16)
                used = int(receipt['gasUsed'], 16)
                l1 = int(receipt.get('l1Fee', '0x0'), 16)
                f = p['fee_review']
                paid = used * price + l1
                need(0 < used <= int(tx['gas'], 16) <= f['gas_limit'] <= 24000000 and
                     0 < price <= f['max_fee_per_gas'] <= 5000000000 and
                     l1 == 0 == f['l1_fee_allowance_wei'] and
                     f['receipt_fee_policy'] == 'included' and
                     paid <= f['maximum_cost_wei'] <= 10**16,
                     'Actual signer receipt exceeds unchanged captured fee bounds')
                day = dt.datetime.fromtimestamp(int(block['timestamp'], 16), dt.timezone.utc).date().isoformat()
                observation = {'transaction': h, 'reported_price_wei': reported,
                               'execution_price_wei': price, 'gas_used': used,
                               'l1_fee_wei': l1, 'receipt_fee_policy': 'included', 'cost_wei': paid}
                need(state['last_fee_observation'] == observation and
                     sum(int(v) for v in state['spent'].values()) == int(state['spent'][day]) == paid and
                     state['last'][p['key']] == int(block['timestamp'], 16) and
                     work.raw_attempts == work.raw == case.model.raw_forwarded == 1 and
                     int(case.model.rpc('eth_getTransactionCount', [case.sender, 'latest']), 16) == 1,
                     'Stock resolver did not account exactly once without resend')
                save(case.folder / 'RECOVERED_JOURNAL.json', {
                    'accepted_hash': h, 'state': state, 'journal_sha256': sha(journal.read_bytes()),
                    'paid_wei': paid, 'canonical_execution_price_wei': price,
                    'reported_effective_gas_price_wei': reported,
                    'receipt': receipt, 'receipt_block': block, 'head': head,
                    'transaction_without_signature': {k: tx.get(k) for k in TX_FIELDS},
                    'explicit_stock_resolver_native_command_requires_root_receipt': True})
                case.receipts.append({'action': p['key'], 'hash': h, 'intent': p,
                                      'receipt': receipt, 'actual_transaction_checked': True,
                                      'confirmations': 12, 'explicit_hash_resolution': True})
                recovered = True
                case.stage = 'await_fresh_native_normal_cycle'
            if recovered and health_path.exists():
                health = B.json_file(health_path)
                if health.get('status') == 'healthy_v2':
                    save(case.folder / 'HEALTHY_NORMAL_CYCLE.json', health)
                    healthy = True
                    break
        need(blocked and recovered and healthy, 'Complete native signer recovery not observed')
        after = {'rights': case.rights(), 'physical': case.physical(), 'money': case.money()}
        need(before['rights'] == after['rights'] and before['physical'] == after['physical'],
             'NFT or LP principal rights changed')
        save(case.folder / 'FINANCIAL_AFTER.json', after)
        B.validate_source(args.source_manifest_sha256)
        need(all(sha((LAB / 'inputs' / n).read_bytes()) == digest
                 for n, (_, digest) in B.INPUTS.items()), 'Original copied signer inputs changed')
        result.update(success=True, accepted_hash=peer.held['accepted_hash'],
                      hashless_restart_blocked=True, explicit_resolution_recovered=True,
                      fresh_native_healthy_cycle=True, source_and_fixture_preserved=True,
                      principal_rights_preserved=True)
        save(OUT / 'COMPLETE.json', result)
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Root signer cleanup deadline')
    except Exception as exc:
        result.update(B.safe_error(exc), failure_stage=case.stage)
        result['success'] = False
    finally:
        if peer is not None:
            peer.close()
        case.outcome.update(status='passed' if result['success'] else 'failed')
        cleanup = case.close()
        result.update(cleanup=cleanup, shared_RPC_requests=work.count,
                      raw_attempts=work.raw_attempts, raw_forwarded=case.model.raw_forwarded,
                      frontend_requests=None if peer is None else peer.count,
                      secret_disposition='retained only in new owned lab; no contents/hashes exported')
        save(OUT / 'EVENTS.json', {'combined_stdout_stderr': ''.join(events.parts)})
        save(OUT / 'RESULT.json', result)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
