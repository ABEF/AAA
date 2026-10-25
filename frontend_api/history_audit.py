"""Read-only comparison of an earnings index with a separately reviewed RPC.

One bounded window of one configured epoch, never a full-history/finality proof.
Does not start a service, repair a database, alter cursor state or sign anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from frontend_api.history import _hash, _quantity
from frontend_api.service import Projection, _keys
from zzz_ops.abi import address
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.rpc import Rpc
from zzz_ops.work_budget import BudgetedRPC, bounded_request, checkpoint

MAX_BLOCKS = 128
MAX_LOGS = 10000
MAX_LOG_BYTES = 65536
MAX_BYTES = 8 * 1024 * 1024


class AuditError(ValueError):
    """Only fixed, non-secret error codes are safe to report."""


def require(condition, code):
    if not condition:
        raise AuditError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def load_json(path):
    with Path(path).open('rb') as handle:
        raw = handle.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, 'configuration_too_large')
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(AuditError('invalid_json_number')))


def number(value):
    require(type(value) is int and 0 <= value < 1 << 63, 'invalid_block_number')
    return value


def normalize_log(raw):
    require(isinstance(raw, dict) and raw.get('removed', False) is False, 'malformed_or_removed_log')
    topics = raw['topics']
    require(isinstance(topics, list) and len(topics) <= 4 and all(
        isinstance(t, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}', t) for t in topics), 'invalid_log_topics')
    data = raw['data']
    require(isinstance(data, str) and len(data) <= MAX_LOG_BYTES and
            re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', data), 'invalid_log_data')
    return dict(block_number=number(_quantity(raw['blockNumber'])), block_hash=_hash(raw['blockHash']),
                transaction_hash=_hash(raw['transactionHash']), transaction_index=number(_quantity(raw['transactionIndex'])),
                log_index=number(_quantity(raw['logIndex'])), address=address(raw['address']),
                topics=[t.lower() for t in topics], data=data.lower())


class Inventory:
    def __init__(self, headers, contracts):
        self.headers, self.contracts = headers, set(contracts)
        self.logs, self.transactions, self.tx_indexes = {}, {}, {}
        self.size = 0

    def add(self, raw):
        checkpoint()
        log = normalize_log(raw)
        block, index = log['block_number'], log['log_index']
        require(block in self.headers and log['block_hash'] == self.headers[block]['hash'], 'log_block_mismatch')
        require(log['address'] in self.contracts, 'unexpected_log_emitter')
        key = (block, index)
        require(key not in self.logs, 'duplicate_log_index')
        tx, tx_index = log['transaction_hash'], log['transaction_index']
        require(self.transactions.setdefault(tx, (block, tx_index)) == (block, tx_index), 'transaction_identity_conflict')
        require(self.tx_indexes.setdefault((block, tx_index), tx) == tx, 'transaction_index_conflict')
        self.size += len(json.dumps(log, separators=(',', ':')))
        require(len(self.logs) < MAX_LOGS and self.size <= MAX_BYTES, 'log_window_limit')
        self.logs[key] = log
        return log

    def seal(self):
        last = {}
        for (block, _), log in sorted(self.logs.items()):
            require(log['transaction_index'] >= last.get(block, 0), 'noncanonical_transaction_order')
            last[block] = log['transaction_index']
        return digest([self.logs[key] for key in sorted(self.logs)])


class HistoryAudit:
    def __init__(self, config, audit_config, rpc=None):
        self.projection = Projection(config)
        require(self.projection.earnings_history is not None, 'earnings_profile_required')
        _keys(audit_config, {'schema', 'rpc_urls', 'provider_id', 'independence_review_sha256'}, 'history audit')
        require(type(audit_config['schema']) is int and audit_config['schema'] == 1, 'unsupported_audit_schema')
        provider = audit_config['provider_id']
        require(isinstance(provider, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', provider), 'invalid_provider_id')
        review = audit_config['independence_review_sha256']
        require(isinstance(review, str) and re.fullmatch(r'[0-9a-f]{64}', review) and int(review, 16) != 0,
                'independence_review_required')
        transport = Rpc(audit_config['rpc_urls'], self.projection.chain, timeout=5, retries=1)
        # Distinct URLs alone do not establish independent infrastructure. Reject
        # obvious reuse; the review record must establish separate operators.
        from urllib.parse import urlsplit
        primary_hosts = {urlsplit(url).hostname.lower() for url in config['rpc_urls']}
        require(not primary_hosts & {urlsplit(url).hostname.lower() for url in transport.urls}, 'same_provider_host')
        self.rpc = BudgetedRPC(rpc or transport)
        self.provider, self.review = provider, review
        self.peers = ([e.projection for e in self.projection.lineage.entries] if self.projection.lineage else []) + [self.projection]

    def header(self, height):
        raw = self.rpc.call('eth_getBlockByNumber', [hex(height), False])
        require(isinstance(raw, dict) and _quantity(raw['number']) == height, 'invalid_rpc_header')
        return dict(number=height, hash=_hash(raw['hash']), parent=_hash(raw['parentHash']),
                    timestamp=number(_quantity(raw['timestamp'])))

    @bounded_request
    def run(self, controller, start, end):
        start, end = number(start), number(end)
        require(start <= end and end - start < MAX_BLOCKS, 'block_window_limit')
        controller = address(controller)
        peer = next((p for p in self.peers if p.contracts['access'].address == controller), None)
        require(peer is not None, 'unconfigured_epoch')
        history = peer.history
        require(start >= history.start, 'window_before_history')
        # Rpc.call returns a checked integer for eth_chainId; explicitly injected
        # read transports may return the canonical wire quantity. No bool/float
        # coercion is allowed for either representation.
        observed_chain = self.rpc.call('eth_chainId', [])
        chain = number(observed_chain) if type(observed_chain) is int else _quantity(observed_chain)
        require(chain == peer.chain, 'wrong_chain')
        head = number(_quantity(self.rpc.call('eth_blockNumber', [])))
        require(end <= head-peer.confirmations+1 and peer.start <= head-peer.confirmations+1, 'insufficient_confirmations')
        anchor = self.header(peer.start)
        require(anchor['hash'] == peer.start_hash, 'deployment_anchor_mismatch')
        database = sqlite3.connect(history.database.as_uri()+'?mode=ro', uri=True, timeout=1)
        try:
            database.execute('PRAGMA query_only=ON')
            database.execute('PRAGMA trusted_schema=OFF')
            def interrupted():
                try:
                    checkpoint(); return 0
                except WorkLimit:
                    return 1
            database.set_progress_handler(interrupted, 1000)
            database.execute('BEGIN')
            result = self.compare(database, peer, start, end, anchor, head)
            database.rollback()
            return result
        finally:
            database.close()

    def compare(self, db, peer, start, end, anchor, head):
        history = peer.history
        cursor = db.execute('SELECT next_block,config FROM cursors WHERE chain=?', (peer.chain,)).fetchone()
        require(cursor is not None and type(cursor[0]) is int and cursor[0] > end, 'incomplete_cursor')
        require(isinstance(cursor[1], str) and len(cursor[1]) <= MAX_LOG_BYTES, 'invalid_cursor_identity')
        require(json.loads(cursor[1], object_pairs_hook=unique_object) == dict(contracts=history.contracts,
            start=history.start, parent_hash=history.parent), 'cursor_identity_mismatch')
        rows = db.execute('SELECT number,hash,parent,timestamp FROM blocks WHERE chain=? AND number BETWEEN ? AND ? ORDER BY number',
                          (peer.chain, start, end)).fetchall()
        require(len(rows) == end-start+1, 'missing_stored_blocks')
        if start == history.start:
            parent = history.parent
        else:
            preceding = db.execute('SELECT hash FROM blocks WHERE chain=? AND number=?', (peer.chain, start-1)).fetchone()
            require(preceding is not None, 'missing_boundary_block')
            parent = _hash(preceding[0])
        headers = {}
        previous_time = None
        for expected, row in zip(range(start, end+1), rows):
            require(type(row[0]) is int and row[0] == expected and type(row[3]) is int, 'invalid_stored_header')
            remote = self.header(expected)
            require((row[1], row[2], row[3]) == (remote['hash'], remote['parent'], remote['timestamp']), 'header_disagreement')
            require(remote['parent'] == parent and (previous_time is None or remote['timestamp'] >= previous_time), 'broken_ancestry')
            headers[expected] = remote
            parent, previous_time = remote['hash'], remote['timestamp']
        local = Inventory(headers, history.contracts)
        # All stored emitters are examined: filtering could hide a tampered row.
        query = '''SELECT block_number,block_hash,transaction_hash,log_index,address,
                   length(raw),substr(raw,1,?) FROM logs
                   WHERE chain=? AND block_number BETWEEN ? AND ? ORDER BY block_number,log_index LIMIT ?'''
        for row in db.execute(query, (MAX_LOG_BYTES+1, peer.chain, start, end, MAX_LOGS+1)):
            require(type(row[5]) is int and row[5] <= MAX_LOG_BYTES, 'stored_log_too_large')
            log = local.add(json.loads(row[6], object_pairs_hook=unique_object))
            require(tuple(row[:5]) == (log['block_number'], log['block_hash'], log['transaction_hash'],
                                      log['log_index'], log['address']), 'stored_log_columns_mismatch')
        remote = Inventory(headers, history.contracts)
        for lower in range(start, end+1, 32):
            upper = min(end, lower+31)
            logs = self.rpc.call('eth_getLogs', [{'address': history.contracts, 'fromBlock': hex(lower), 'toBlock': hex(upper)}])
            require(isinstance(logs, list) and len(logs) <= MAX_LOGS, 'invalid_rpc_log_inventory')
            for raw in logs:
                log = remote.add(raw)
                require(lower <= log['block_number'] <= upper, 'rpc_log_outside_requested_chunk')
        local_hash, remote_hash = local.seal(), remote.seal()
        missing = sorted(remote.logs.keys()-local.logs.keys())
        extra = sorted(local.logs.keys()-remote.logs.keys())
        different = sorted(key for key in local.logs.keys() & remote.logs.keys() if local.logs[key] != remote.logs[key])
        require(self.header(end) == headers[end] and self.header(peer.start) == anchor, 'chain_changed_during_audit')
        final_head = number(_quantity(self.rpc.call('eth_blockNumber', [])))
        require(end <= final_head-peer.confirmations+1 and peer.start <= final_head-peer.confirmations+1, 'confirmation_depth_changed')
        checkpoint()
        return dict(schema=1, status='matched' if not (missing or extra or different) else 'mismatch',
            scope='one_configured_epoch_window', chain_id=peer.chain, controller=peer.contracts['access'].address,
            configuration_sha256=self.projection.identity, provider_id=self.provider, independence_review_sha256=self.review,
            from_block=start, to_block=end, from_parent_hash=headers[start]['parent'], to_block_hash=headers[end]['hash'],
            confirmations=peer.confirmations, observed_head_start=head, observed_head_end=final_head,
            block_headers_sha256=digest(list(headers.values())), contracts=history.contracts,
            required_earnings_emitters=sorted({peer.contracts[r].address for r in ('nft','vault','rewards','royalties','handoff')} |
                {c.address for c in self.projection.earnings_history.profiles[peer.contracts['access'].address].values()}),
            local_logs=len(local.logs), rpc_logs=len(remote.logs), local_logs_sha256=local_hash, rpc_logs_sha256=remote_hash,
            discrepancies={kind:dict(count=len(keys), examples=[dict(block_number=k[0], log_index=k[1]) for k in keys[:20]])
                           for kind,keys in [('missing_from_index',missing),('absent_from_rpc',extra),('conflicting',different)]},
            limitations='Provider agreement is not consensus or log-completeness proof. Only this window was compared; runtime/lifecycle, epoch cutoffs, economic replay, prices and whole-history coverage need separate verification.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--audit-rpc-config', required=True)
    parser.add_argument('--controller', required=True)
    parser.add_argument('--from-block', type=int, required=True)
    parser.add_argument('--to-block', type=int, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    can_write = False
    try:
        audit = HistoryAudit(load_json(args.config), load_json(args.audit_rpc_config))
        output = Path(args.output).resolve()
        protected = {Path(args.config).resolve(), Path(args.audit_rpc_config).resolve()}
        for peer in audit.peers:
            protected.update(Path(str(peer.history.database)+suffix) for suffix in ('', '-wal', '-shm', '-journal'))
        require(output not in protected and not output.exists(), 'protected_or_existing_output')
        can_write = True
        report = audit.run(args.controller, args.from_block, args.to_block)
        code = 0 if report['status'] == 'matched' else 2
    except AuditError as exc:
        report, code = dict(schema=1, status='unavailable', error=str(exc)), 2
    except (RpcError, ValueError, KeyError, TypeError, OverflowError, OSError, sqlite3.Error):
        # Never echo raw exception/config/URL/database contents into a report.
        report, code = dict(schema=1, status='unavailable', error='audit_failed_closed'), 2
    if not can_write:
        print(json.dumps(report))
        return 2
    try:
        # Exclusive creation cannot replace a database, config or prior receipt.
        with Path(args.output).open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(report, indent=2)+'\n')
    except OSError:
        print(json.dumps(dict(schema=1, status='unavailable', error='output_not_created')))
        return 2
    print(json.dumps(dict(schema=1, status=report['status'])))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
