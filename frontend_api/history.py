"""Read-only, snapshot-consistent projection of the existing indexer database.

The database is operator-maintained evidence, not a cryptographic proof of log
completeness. Raw, fixed-layout logs are replayed; cached decoded labels are not
trusted. Actual ownership is cross-checked by the RPC service before serving.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sqlite3
from types import MappingProxyType
from typing import Any

from zzz_ops.abi import address, decode_words, keccak256
from zzz_ops.rpc import RpcError, _unique_object, _reject_constant, _finite_float
from zzz_ops.work_budget import checkpoint, WorkLimit
from zzz_ops.state import integer

ZERO = '0x' + '0' * 40
TRANSFER = '0x' + keccak256(b'Transfer(address,address,uint256)').hex()
CLAIMED = '0x' + keccak256(b'Claimed(uint256,address,address,uint256)').hex()
ROYALTY_CONVERTED = '0x' + keccak256(b'RoyaltyConverted(uint256,address,uint256,uint256)').hex()
LP_CONVERTED = '0x' + keccak256(b'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)').hex()


class HistoryError(RpcError):
    """Incomplete, mismatched or malformed confirmed history; fail closed."""


def _stored_json(raw):
    # SQLite is operator-maintained evidence, not permission to accept a second,
    # more permissive JSON dialect than the ingress that originally wrote it.
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant, parse_float=_finite_float)


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value) or int(value, 16) == 0:
        raise HistoryError('Malformed history hash')
    return value.lower()


def _quantity(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value):
        raise HistoryError('Malformed history RPC quantity')
    return int(value, 16)


def _topic_address(word: str) -> str:
    if not isinstance(word, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', word) or int(word[2:26], 16):
        raise HistoryError('Malformed indexed history address')
    return '0x' + word[-40:].lower()


@dataclass(frozen=True)
class HistorySnapshot:
    owners: Any
    # (nft_id, asset) -> (lifetime LP claims, lifetime royalty claims)
    claims: Any
    provenance: Any
    # (nft_id, source asset) -> source spent, ETH credited, count, last event.
    # This is denomination conversion, never payment or newly earned revenue.
    conversions: Any
    lp_conversions: Any = field(default_factory=lambda: MappingProxyType({}))

    def claimed(self, nft_id: int, assets: set[str]) -> list[dict[str, str]]:
        records = []
        for asset in sorted(assets):
            lp, royalties = self.claims.get((nft_id, asset), (0, 0))
            records.append({'asset': asset, 'lp_raw': str(lp), 'royalties_raw': str(royalties),
                            'total_raw': str(lp + royalties)})
        return records


def merge_conversions(destination, incoming, nft_id):
    for (identifier, asset), value in incoming.items():
        if identifier != nft_id:
            continue
        previous = destination.get((identifier, asset))
        if previous is None:
            destination[identifier, asset] = value
        else:
            last = max((previous[3], value[3]), key=lambda e: (e['block_number'], e['log_index']))
            destination[identifier, asset] = (previous[0] + value[0], previous[1] + value[1], previous[2] + value[2], last)


def conversion_report(conversions, nft_id, descriptors, provenance):
    if conversions is None:
        return {'available': False, 'assets': None, 'total_eth_credited_raw': None,
                'reason': 'Complete confirmed conversion history is unavailable; zero is not inferred.'}
    assets = []
    for (identifier, asset), (source, native, count, last) in sorted(conversions.items()):
        if identifier != nft_id:
            continue
        descriptor = descriptors[asset]
        assets.append({'asset': asset, 'symbol': descriptor.symbol, 'decimals': descriptor.decimals,
                       'source_converted_raw': str(source), 'eth_credited_raw': str(native),
                       'event_count': count, 'last_event': dict(last)})
    return {'available': True, 'assets': assets,
            'total_eth_credited_raw': str(sum(int(item['eth_credited_raw']) for item in assets)),
            'eth_decimals': 18, 'provenance': provenance,
            'scope': 'Lifetime NFT conversion credits across the complete configured same-chain lineage. Not claims, new revenue, or the remaining claimable balance.'}


class History:
    def __init__(self, config: dict[str, Any], *, chain_id: int, nft: str, rewards: str, royalties: str):
        fields = {'database', 'start_block', 'start_parent_hash', 'contracts', 'max_events'}
        if not isinstance(config, dict) or set(config) != fields:
            raise ValueError('Missing or unknown confirmed history configuration fields')
        if not isinstance(config['database'], str) or not config['database']:
            raise ValueError('A fixed local history database path is required')
        self.database = Path(config['database']).expanduser().resolve()
        self.chain = integer(chain_id, 'chain_id', minimum=1)
        self.start = integer(config['start_block'], 'history.start_block', minimum=1)
        self.parent = _hash(config['start_parent_hash'])
        self.max_events = integer(config['max_events'], 'history.max_events', minimum=1)
        if self.max_events > 1000000 or self.chain >= 1 << 63 or self.start >= 1 << 63:
            raise ValueError('Confirmed history configuration exceeds supported bounds')
        if not isinstance(config['contracts'], list) or not 3 <= len(config['contracts']) <= 128:
            raise ValueError('A bounded exact tracked-contract inventory is required')
        self.contracts = sorted(address(a) for a in config['contracts'])
        if len(self.contracts) != len(set(self.contracts)):
            raise ValueError('Duplicate history contract addresses')
        self.nft, self.rewards, self.royalties = address(nft), address(rewards), address(royalties)
        if len({self.nft, self.rewards, self.royalties}) != 3 or not {self.nft, self.rewards, self.royalties} <= set(self.contracts):
            raise ValueError('History must track the three distinct pinned NFT/reward emitters')

    def read(self, *, block_number: int, block_hash: str, block_timestamp: int,
             minted_count: int, lp_assets: set[str], royalty_assets: set[str], consumer=None,
             extra_emitters=()) -> HistorySnapshot:
        if type(block_number) is not int or not self.start <= block_number < 1 << 63:
            raise HistoryError('Confirmed history target precedes coverage or exceeds SQLite bounds')
        if type(minted_count) is not int or not 0 <= minted_count <= 1000:
            raise HistoryError('Canonical NFT supply exceeds the bounded collection')
        if len(lp_assets - {ZERO}) > 32 or len(royalty_assets) > 17 or ZERO not in royalty_assets:
            raise HistoryError('Unsupported history reward asset inventory')
        target_hash = _hash(block_hash)
        emitters = sorted({self.nft, self.rewards, self.royalties, *(address(a) for a in extra_emitters)})
        if not set(emitters) <= set(self.contracts) or len(emitters) > 8:
            raise HistoryError('Financial replay requires complete reviewed emitter coverage')
        # mode=ro never creates a missing database. Do not use immutable=1:
        # a live WAL database must still participate in ordinary snapshot locks.
        try:
            connection = sqlite3.connect(self.database.as_uri() + '?mode=ro', uri=True, timeout=1)
            try:
                connection.execute('PRAGMA query_only=ON')
                connection.execute('PRAGMA trusted_schema=OFF')
                def interrupted():
                    try:
                        checkpoint()
                        return 0
                    except WorkLimit:
                        return 1
                connection.set_progress_handler(interrupted, 1000)
                connection.execute('BEGIN')
                result = self._read(connection, block_number, target_hash, block_timestamp,
                                    minted_count, lp_assets, royalty_assets, consumer, emitters)
                connection.rollback()
                return result
            finally:
                connection.close()
        except (sqlite3.Error, OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
            raise HistoryError('Confirmed indexer history is unavailable or malformed') from exc

    def _read(self, db, target, target_hash, target_timestamp, minted_count, lp_assets, royalty_assets, consumer, emitters):
        row = db.execute('SELECT next_block,config FROM cursors WHERE chain=?', (self.chain,)).fetchone()
        if row is None or type(row[0]) is not int or row[0] <= target:
            raise HistoryError('Indexer has not completely processed the confirmed target block')
        identity = _stored_json(row[1])
        expected_identity = {'contracts': self.contracts, 'start': self.start, 'parent_hash': self.parent}
        if identity != expected_identity:
            raise HistoryError('Indexer chain/start/parent/contract identity differs from reviewed history configuration')
        bounds = db.execute('SELECT COUNT(*),MIN(number),MAX(number) FROM blocks WHERE chain=? AND number BETWEEN ? AND ?',
                            (self.chain, self.start, target)).fetchone()
        if bounds != (target - self.start + 1, self.start, target):
            raise HistoryError('Indexer block history has gaps')
        first = db.execute('SELECT hash,parent FROM blocks WHERE chain=? AND number=?', (self.chain, self.start)).fetchone()
        last = db.execute('SELECT hash,timestamp FROM blocks WHERE chain=? AND number=?', (self.chain, target)).fetchone()
        if first[1] != self.parent or last != (target_hash, target_timestamp):
            raise HistoryError('Indexer anchor/tip does not match the canonical projection')
        broken = db.execute('''SELECT 1 FROM blocks c JOIN blocks p ON p.chain=c.chain AND p.number=c.number-1
            WHERE c.chain=? AND c.number>? AND c.number<=? AND c.parent!=p.hash LIMIT 1''',
                            (self.chain, self.start, target)).fetchone()
        if broken:
            raise HistoryError('Indexer stored block ancestry is discontinuous')
        # Raw event/emitter filters are enforced below. Do not filter by the
        # indexer's optional decoded event label: that could hide a real event.
        rows = db.execute('''SELECT l.block_number,l.block_hash,l.transaction_hash,l.log_index,l.address,l.raw,b.hash,b.timestamp
            FROM logs l JOIN blocks b ON b.chain=l.chain AND b.number=l.block_number
            WHERE l.chain=? AND l.block_number>=? AND l.block_number<=? AND l.address IN ('''
            + ','.join('?' for _ in emitters) + ') ORDER BY l.block_number,l.log_index LIMIT ?',
                          (self.chain, self.start, target, *emitters, self.max_events + 1))
        owners = {}
        claims = {}
        conversions = {}
        lp_conversions = {}
        seen_logs = set()
        transaction_blocks = {}
        examined = 0
        claim_events = 0
        conversion_events = 0
        lp_conversion_events = 0
        for number, block_hash, transaction_hash, log_index, emitter, raw, stored_hash, timestamp in rows:
            checkpoint()
            examined += 1
            if examined > self.max_events:
                raise HistoryError('History event bound exceeded; no truncated projection is served')
            if type(number) is not int or type(log_index) is not int or log_index < 0 or not isinstance(raw, str) or len(raw) > 131072:
                raise HistoryError('Malformed or oversized stored log')
            _hash(block_hash); _hash(transaction_hash)
            if block_hash != stored_hash or (number, log_index) in seen_logs:
                raise HistoryError('Orphaned or duplicate block/log history identity')
            seen_logs.add((number, log_index))
            if transaction_hash in transaction_blocks and transaction_blocks[transaction_hash] != number:
                raise HistoryError('Stored transaction appears in multiple blocks')
            transaction_blocks[transaction_hash] = number
            item = _stored_json(raw)
            if not isinstance(item, dict) or item.get('removed') is not False or address(item['address']) != emitter:
                raise HistoryError('Stored raw log emitter/removed identity differs')
            if _quantity(item['blockNumber']) != number or _hash(item['blockHash']) != block_hash or _hash(item['transactionHash']) != transaction_hash or _quantity(item['logIndex']) != log_index:
                raise HistoryError('Stored raw log provenance differs from its confirmed row')
            topics = item.get('topics')
            if not isinstance(topics, list) or len(topics) > 4 or any(not isinstance(t, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', t) for t in topics):
                raise HistoryError('Malformed fixed event topics')
            data = item.get('data')
            if not isinstance(data, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', data):
                raise HistoryError('Malformed raw event data')
            if not topics:
                continue
            if type(timestamp) is not int or not 0 <= timestamp <= target_timestamp:
                raise HistoryError('Invalid financial-event timestamp')
            if consumer is not None:
                consumer(emitter, topics, item.get('data'), number, block_hash, timestamp,
                         transaction_hash, log_index)
            topic = topics[0].lower()
            if emitter == self.nft and topic == TRANSFER:
                if len(topics) != 4 or item.get('data') != '0x':
                    raise HistoryError('Noncanonical ERC721 Transfer layout')
                sender, recipient = _topic_address(topics[1]), _topic_address(topics[2])
                nft_id = int(topics[3], 16)
                if recipient == ZERO:
                    raise HistoryError('Burn is not implemented by the pinned canonical NFT')
                if sender == ZERO:
                    if nft_id in owners or len(owners) == 1000:
                        raise HistoryError('Duplicate mint or oversized ownership inventory')
                elif owners.get(nft_id) != sender:
                    raise HistoryError('Transfer chain is missing a mint or predecessor owner')
                owners[nft_id] = recipient
            elif emitter in (self.rewards, self.royalties) and topic == CLAIMED:
                if len(topics) != 4:
                    raise HistoryError('Noncanonical Claimed indexed layout')
                data = decode_words(item.get('data'))
                if len(data) != 1:
                    raise HistoryError('Claimed amount must contain exactly one uint256 word')
                nft_id = int(topics[1], 16)
                asset, recipient = _topic_address(topics[2]), _topic_address(topics[3])
                admitted = lp_assets if emitter == self.rewards else royalty_assets
                if nft_id not in owners or asset not in admitted or recipient == ZERO:
                    raise HistoryError('Claim is not bound to a minted NFT and admitted ledger asset')
                # A legitimate payout callback can transfer the NFT before the
                # ledger emits Claimed. Its recorded recipient is the owner at
                # authorization/payout time, not necessarily at emitted-log time.
                lp, royalty = claims.get((nft_id, asset), (0, 0))
                amount = int(data[0], 16)
                claims[nft_id, asset] = (lp + amount, royalty) if emitter == self.rewards else (lp, royalty + amount)
                claim_events += 1
            elif (emitter == self.royalties and topic == ROYALTY_CONVERTED) or (emitter == self.rewards and topic == LP_CONVERTED):
                is_lp = emitter == self.rewards
                if len(topics) != 3:
                    raise HistoryError('Noncanonical reward conversion topics')
                data = decode_words(item.get('data'))
                if len(data) != (4 if is_lp else 2):
                    raise HistoryError('Unexpected reward conversion amount layout')
                nft_id = int(topics[1], 16)
                asset = _topic_address(topics[2])
                amounts = [int(value, 16) for value in data]
                source, native = (sum(amounts[:2]), sum(amounts[2:])) if is_lp else amounts
                admitted = lp_assets if is_lp else royalty_assets
                if nft_id not in owners or asset == ZERO or asset not in admitted or ZERO not in admitted or (source == 0 and native != 0):
                    raise HistoryError('Reward conversion is not bound to a minted NFT and admitted currencies')
                if is_lp and ((amounts[0] == 0 and amounts[2] != 0) or (amounts[1] == 0 and amounts[3] != 0)):
                    raise HistoryError('LP conversion credits an empty reward component')
                if type(timestamp) is not int or not 0 <= timestamp <= target_timestamp:
                    raise HistoryError('Invalid conversion block timestamp')
                target_conversions = lp_conversions if is_lp else conversions
                before_source, before_native, count, _ = target_conversions.get((nft_id, asset), (0, 0, 0, None))
                last = MappingProxyType({'ledger': emitter, 'block_number': number, 'block_hash': block_hash,
                    'timestamp': timestamp, 'transaction_hash': transaction_hash, 'log_index': log_index})
                target_conversions[nft_id, asset] = (before_source + source, before_native + native, count + 1, last)
                if is_lp: lp_conversion_events += 1
                else: conversion_events += 1
        if len(owners) != minted_count:
            raise HistoryError('Transfer mint inventory differs from canonical mintedCount')
        provenance = {'available': True, 'from_block': self.start, 'start_block_hash': first[0], 'start_parent_hash': self.parent,
                      'through_block': target, 'block_hash': target_hash, 'indexer_next_block': row[0],
                      'logs_examined': examined, 'claim_events': claim_events, 'royalty_conversion_events': conversion_events,
                      'lp_conversion_events': lp_conversion_events, 'minted_count': minted_count,
                      'scope': 'All owners and all prior claims through the exact confirmed block, per NFT and asset.',
                      'completeness': 'Operator-maintained complete indexer ingestion; SQLite is not a cryptographic log-completeness proof.'}
        return HistorySnapshot(MappingProxyType(owners), MappingProxyType(claims), MappingProxyType(provenance),
                               MappingProxyType(conversions), MappingProxyType(lp_conversions))
