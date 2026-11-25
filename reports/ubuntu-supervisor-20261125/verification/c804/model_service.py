"""DRAFT ONLY: new private model peer for a native supervised stock keeper.

Frozen c7f0 helpers supply setup/model/gateway; no old job/cycle/settle runs.
The main keeper MUST be a separate native unit, not a child of this helper.
No remote action, installer action, feature journey, or test is performed here.
"""
from pathlib import Path
import argparse
import datetime as dt
import http.client
import json
import os
import re
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import keeper_runtime as B
import keeper_jobs as J
import job_cases as C

LAB = Path('/opt/popl-ubuntu-supervisor-20261125-c804')
SOURCE = LAB / 'source/contracts'
OUT = LAB / 'runtime/run-001/model'
for module in (B, J, C):
    module.LAB, module.SOURCE, module.OUT = LAB, SOURCE, OUT
need, save, sha = B.need, B.save, B.sha


class Model(J.Model):
    def start(self, env):
        # c803's coherent Anvil input only; production/default fees stay intact.
        need(sha(self.binary.read_bytes()) == B.ANVIL_SHA, 'Anvil differs')
        self.controlled_genesis_timestamp = int(time.time())
        self.child = B.Child([
            self.binary, '--host', '127.0.0.1', '--port', '19591',
            '--accounts', '0', '--silent', '--chain-id', '4663',
            '--hardfork', 'cancun', '--gas-limit', '32000000',
            '--gas-price', '1000000000', '--block-base-fee-per-gas', '1',
            '--timestamp', str(self.controlled_genesis_timestamp),
            '--load-state', LAB / 'inputs/restore-state.json',
        ], self.folder, env, self.folder / 'anvil')
        end = time.monotonic() + 20
        while True:
            need(self.child.process.poll() is None and not self.child.overflow,
                 'Owned model startup failed')
            if B.owns(self.child.process.pid, 19591):
                try:
                    if self.rpc('eth_chainId', []) == '0x1237':
                        break
                except (ConnectionError, OSError):
                    pass
            need(time.monotonic() < end, 'Owned model startup deadline')
            time.sleep(.1)
        head = self.rpc('eth_getBlockByNumber', ['latest', False])
        need(head['hash'].lower() == B.IMPORTED_HASH and
             int(head['gasLimit'], 16) == 32000000, 'Copied anchor differs')
        return head

    def guard(self):
        need(self.work.raw == 0 and self.raw_forwarded == 0,
             'Exactly one first stock harvest is admitted')
        super().guard()


C.Model = Model


class Peer:
    """Unchanged requests/results except one incomplete chunk-size line."""
    def __init__(self, case):
        self.case = case
        self.path = case.folder / 'actor/state.json'
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.trigger = None
        self.closed = None
        self.count = 0
        self.threads = []
        peer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.connection.settimeout(30)
                identifier = None
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    need(0 < size <= B.MAX_REQUEST, 'Frontend request bound')
                    body = self.rfile.read(size)
                    q = json.loads(body)
                    need(type(q) is dict and q.get('jsonrpc') == '2.0' and
                         type(q.get('id')) is int and type(q.get('method')) is str,
                         'Frontend request envelope differs')
                    identifier = q['id']
                    method = q['method']
                    need(method in B.READ_METHODS | {'eth_sendRawTransaction'},
                         'Frontend closed method set')
                    with peer.lock:
                        peer.count += 1
                        need(peer.count <= 6000 and
                             time.monotonic() < case.model.work.deadline,
                             'Frontend work bound')
                        pending = (B.json_file(peer.path).get('pending')
                                   if peer.path.exists() else None)
                        eligible = (peer.trigger is None and
                                    method == 'eth_getTransactionReceipt' and
                                    type(pending) is dict and
                                    type(pending.get('hash')) is str and
                                    q.get('params') == [pending['hash']])
                        if eligible:
                            case.model.work.consume()
                            raw = peer.path.read_bytes()
                            peer.trigger = {
                                'method': method, 'request_id': identifier,
                                'monotonic': time.monotonic(), 'utc': time.time(),
                                'pending_hash': pending['hash'],
                                'journal_sha256': sha(raw),
                                'journal_raw_utf8': raw.decode('utf-8', 'strict'),
                                'intent': pending, 'fault': 'chunk_size_without_CRLF',
                                'trickle_interval_seconds': 1,
                                'maximum_trickle_seconds': 160,
                                'completed_http_reply': False,
                            }
                            save(case.folder / 'FAULT_TRIGGER.json', peer.trigger)
                    if eligible:
                        # Complete headers, then keep HTTPResponse.read1 inside
                        # chunk-size readline with one hex byte/second and no
                        # CRLF. No finished HTTP attempt or pulse is synthesized.
                        self.connection.sendall(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                        started = time.monotonic()
                        fragments = 0
                        disconnected = False
                        try:
                            while (not peer.stop.wait(1) and
                                   time.monotonic() - started < 160):
                                self.connection.sendall(b'1')
                                fragments += 1
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            disconnected = True
                        finally:
                            peer.closed = {
                                'monotonic': time.monotonic(), 'utc': time.time(),
                                'elapsed_seconds': time.monotonic() - started,
                                'fragments': fragments,
                                'peer_disconnected': disconnected,
                                'completed_http_reply': False,
                            }
                            save(case.folder / 'FAULT_CLOSED.json', peer.closed)
                            self.close_connection = True
                        return
                    conn = http.client.HTTPConnection('127.0.0.1', 19592, timeout=30)
                    try:
                        conn.request('POST', '/', body, {'Content-Type': 'application/json'})
                        response = conn.getresponse()
                        need(response.status == 200, 'Frontend upstream HTTP differs')
                        payload = response.read(B.MAX_RESPONSE + 1)
                        need(len(payload) <= B.MAX_RESPONSE, 'Frontend response bound')
                    finally:
                        conn.close()
                except Exception as exc:
                    payload = B.enc({'jsonrpc': '2.0', 'id': identifier,
                                     'error': {'code': -32071,
                                               'message': 'Owned frontend refused'}})
                    if not (case.folder / 'FRONTEND_REFUSAL.json').exists():
                        save(case.folder / 'FRONTEND_REFUSAL.json', B.safe_error(exc))
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
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
        need(not self.thread.is_alive(), 'Frontend listener did not stop')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-manifest-sha256', required=True)
    parser.add_argument('--base-sha256', required=True)
    parser.add_argument('--jobs-sha256', required=True)
    parser.add_argument('--cases-sha256', required=True)
    args = parser.parse_args()
    need(os.geteuid() == 65534 and os.readlink('/proc/self/ns/net') !=
         os.environ['POPL_LAB_HOST_NETWORK_NAMESPACE'], 'Private unprivileged lab required')
    for module, digest in ((B, args.base_sha256), (J, args.jobs_sha256),
                           (C, args.cases_sha256)):
        need(sha(Path(module.__file__).read_bytes()) == digest, 'Frozen helper differs')
    OUT.mkdir(mode=0o700, exist_ok=False)
    source = B.validate_source(args.source_manifest_sha256)
    need(source['source_head'] == '7f862557df8e8cbaf8494c7b1c12f18e07be436d',
         'Root must set the exact reviewed source commit before packaging')
    need(len(source['members']) == 190, 'Exact production source member count differs')
    for name, (size, digest) in B.INPUTS.items():
        raw = (LAB / 'inputs' / name).read_bytes()
        need(len(raw) == size and sha(raw) == digest, 'Copied input differs')
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
              'native_watchdog_verification_requires_root_receipt': True}
    try:
        case.start()
        peer = Peer(case)
        case.configure(rpc_urls=['http://127.0.0.1:19593'], maintenance={
            'compound': False, 'compound_idle': False, 'harvest': True,
            'minimum_liquidity': 1, 'harvest_interval_seconds': 3600})
        case.model.review['allowed'] = [('harvest', 'vault', 'collectFees(uint256,uint256)')]
        # Setup-only direct objects must release the lock before the separate
        # native ExecStart launches the actual complete monitor main loop.
        case.lock_guard.__exit__(None, None, None)
        case.lock_guard = None
        case.k = None
        initial = Path(case.cfg['state_path']).read_bytes()
        initial_state = json.loads(initial)
        need(initial_state['pending'] is None and initial_state['next_nonce'] == 0,
             'Fresh journal is not unused')
        before = {'rights': case.rights(), 'physical': case.physical(),
                  'money': case.money()}
        save(case.folder / 'INITIAL_JOURNAL.json', {
            'sha256': sha(initial), 'raw_utf8': initial.decode('utf-8'),
            'state': initial_state})
        save(case.folder / 'FINANCIAL_BEFORE.json', before)
        # Empty interval blocks make later confirmed reads fresh without any
        # model-directed RPC/transaction submitted by the stock signer.
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
            'native_main_pid_required': True, 'notify_access_required': 'main',
            'watchdog_seconds_required': 120, 'all_guard_limits_unchanged': True})
        case.stage = 'stock_native_wait_for_fault'
        recovered = False
        healthy = False
        first_pending = None
        journal = Path(case.cfg['state_path'])
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Shared900second model work bound')
            need(case.model.child.process.poll() is None and
                 not case.model.child.overflow, 'Owned Anvil stopped/overflowed')
            state = B.json_file(journal)
            candidate = state.get('pending')
            if first_pending is None and type(candidate) is dict and type(candidate.get('hash')) is str:
                raw = journal.read_bytes()
                actual = case.model.rpc('eth_getTransactionByHash', [candidate['hash']])
                need(type(actual) is dict and actual['hash'] == candidate['hash'] and
                     actual['from'].lower() == case.sender and
                     actual['to'].lower() == candidate['to'] == case.a['vault'] and
                     actual['input'] == candidate['data'] and int(actual['nonce'], 16) == 0 and
                     candidate['nonce'] == state['next_nonce'] == 0 and
                     candidate['key'] == 'harvest:' + str(J.BUCKET) and
                     case.model.raw_forwarded == work.raw == work.raw_attempts == 1,
                     'First durable stock pending identity differs')
                first_pending = {'sha256': sha(raw), 'raw_utf8': raw.decode('utf-8', 'strict'),
                                 'state': state, 'monotonic': time.monotonic(), 'utc': time.time(),
                                 'unmined_at_observation': actual.get('blockNumber') is None,
                                 'transaction_without_signature': {k: actual.get(k) for k in (
                                     'hash', 'from', 'to', 'input', 'nonce', 'value', 'gas',
                                     'gasPrice', 'type', 'chainId', 'maxFeePerGas',
                                     'maxPriorityFeePerGas', 'blockHash', 'blockNumber',
                                     'transactionIndex')}}
                save(case.folder / 'DURABLE_PENDING.json', first_pending)
            if peer.trigger is not None:
                case.stage = 'same_journal_native_recovery'
                need(first_pending is not None and peer.trigger['journal_sha256'] == first_pending['sha256'],
                     'Saved pending bytes changed before the framing stall')
            if peer.trigger is not None and not recovered and state.get('pending') is None:
                pending = peer.trigger['intent']
                need(state['next_nonce'] == 1, 'Recovery nonce differs')
                receipt = case.model.rpc('eth_getTransactionReceipt', [pending['hash']])
                tx = case.model.rpc('eth_getTransactionByHash', [pending['hash']])
                need(type(receipt) is dict and receipt['status'] == '0x1' and
                     tx['from'].lower() == case.sender and
                     tx['to'].lower() == pending['to'] and tx['input'] == pending['data'] and
                     int(tx['nonce'], 16) == 0 and int(tx['value'], 16) == 0,
                     'Actual saved transaction identity/receipt differs')
                block = case.model.rpc('eth_getBlockByNumber', [receipt['blockNumber'], False])
                head = case.model.rpc('eth_getBlockByNumber', ['latest', False])
                need(int(head['number'], 16) - int(receipt['blockNumber'], 16) + 1 >= 12,
                     'Twelve actual confirmations absent')
                from zzz_ops.ethereum_fees import execution_price
                canonical_price = execution_price(tx, block, receipt)
                reported_price = int(receipt['effectiveGasPrice'], 16)
                gas_used = int(receipt['gasUsed'], 16)
                fee_review = pending['fee_review']
                l1_fee = int(receipt.get('l1Fee', '0x0'), 16)
                need(receipt['transactionHash'] == tx['hash'] == pending['hash'] and
                     receipt['blockHash'] == tx['blockHash'] == block['hash'] and
                     receipt['blockNumber'] == tx['blockNumber'] == block['number'] and
                     receipt['transactionIndex'] == tx['transactionIndex'] and
                     0 < gas_used <= int(tx['gas'], 16) <= fee_review['gas_limit'] and
                     0 < canonical_price <= fee_review['max_fee_per_gas'] and
                     l1_fee == 0 == fee_review['l1_fee_allowance_wei'] and
                     fee_review['receipt_fee_policy'] == 'included',
                     'Canonical inclusion or captured fee bound differs')
                paid = gas_used * canonical_price + l1_fee
                need(paid <= fee_review['maximum_cost_wei'] <= 10**16 and
                     state['last_fee_observation'] == {
                         'transaction': pending['hash'], 'reported_price_wei': reported_price,
                         'execution_price_wei': canonical_price, 'gas_used': gas_used,
                         'l1_fee_wei': l1_fee, 'receipt_fee_policy': 'included', 'cost_wei': paid},
                     'Exact canonical fee observation differs')
                day = dt.datetime.fromtimestamp(int(block['timestamp'], 16), dt.timezone.utc).date().isoformat()
                need(sum(int(x) for x in state['spent'].values()) == paid and
                     int(state['spent'][day]) == paid and
                     state['last'][pending['key']] == int(block['timestamp'], 16),
                     'Recovery exact spend/harvest clock differs')
                need(case.model.raw_forwarded == work.raw == work.raw_attempts == 1,
                     'Recovery attempted another broadcast')
                case.receipts.append({'action': pending['key'], 'hash': pending['hash'],
                                      'receipt': receipt, 'intent': pending,
                                      'actual_transaction_checked': True,
                                      'confirmations': 12,
                                      'native_lifecycle_requires_external_receipt': True})
                save(case.folder / 'RECOVERED_JOURNAL.json', {
                    'sha256': sha(journal.read_bytes()), 'state': state,
                    'same_original_pending_hash': pending['hash'], 'paid_wei': paid,
                    'canonical_execution_price_wei': canonical_price,
                    'reported_effective_gas_price_wei': reported_price,
                    'receipt': receipt, 'receipt_block': block, 'head': head,
                    'transaction_without_signature': {k: tx.get(k) for k in (
                        'hash', 'from', 'to', 'input', 'nonce', 'value', 'gas',
                        'gasPrice', 'type', 'chainId', 'maxFeePerGas',
                        'maxPriorityFeePerGas', 'blockHash', 'blockNumber',
                        'transactionIndex')}})
                recovered = True
            health_path = Path(case.cfg['health_path'])
            if recovered and health_path.exists():
                health = B.json_file(health_path)
                if health.get('status') == 'healthy_v2':
                    save(case.folder / 'HEALTHY_NORMAL_CYCLE.json', health)
                    healthy = True
                    break
        need(recovered and healthy, 'Stock recovery/fresh healthy cycle incomplete')
        after = {'rights': case.rights(), 'physical': case.physical(), 'money': case.money()}
        # This copied state has no new swaps; a fee harvest must retain rights
        # and principal. Books may change only by the actual harvested receipt.
        need(after['rights'] == before['rights'] and
             after['physical'] == before['physical'], 'NFT/LP principal rights changed')
        save(case.folder / 'FINANCIAL_AFTER.json', after)
        B.validate_source(args.source_manifest_sha256)
        need(all(sha((LAB / 'inputs' / n).read_bytes()) == digest
                 for n, (_, digest) in B.INPUTS.items()), 'Original copied inputs changed')
        result.update(success=True, saved_hash_recovered=True,
                      fresh_stock_healthy_cycle=True, raw_attempts=work.raw_attempts,
                      raw_forwarded=case.model.raw_forwarded, shared_RPC_requests=work.count,
                      source_and_fixture_preserved=True, principal_rights_preserved=True)
        # Root stops the keeper first, then model. Keep peer available meanwhile.
        save(OUT / 'COMPLETE.json', result)
        while not stop.wait(.2):
            need(time.monotonic() < work.deadline, 'Root cleanup deadline')
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
