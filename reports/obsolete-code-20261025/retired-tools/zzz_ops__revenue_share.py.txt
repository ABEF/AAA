"""Proposed creator-revenue measurement. Exact arithmetic; no payout authority.

Snapshots are samples of active liquidity, not historical Uniswap fee-growth
accounting. These policies must be agreed with the creator before financial use.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import atomic_json, integer

ZERO = '0x' + '0' * 40
MAX_RECORDS = 100000


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def hash32(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value) or int(value, 16) == 0:
        raise ValueError('Expected a nonzero 32-byte block/pool/transaction hash')
    return value.lower()


def asset_address(value: Any) -> str:
    return ZERO if value == ZERO else address(value)


def raw_amount(value: Any, name: str = 'raw_amount', *, bits: int = 256) -> int:
    number = integer(value, name)
    if number >= 1 << bits:
        raise ValueError(f'{name} exceeds uint{bits}')
    return number


def fraction_json(value: Fraction) -> dict[str, str]:
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


@dataclass(frozen=True)
class Snapshot:
    chain_id: int
    pool_id: str
    block_number: int
    block_hash: str
    timestamp: int
    observed_head: int
    pool_active_liquidity: int
    popl_active_liquidity: int
    # Hash of the collector configuration/source receipt. Not a signature or
    # claim that the offline verifier independently queried the chain.
    source_id: str

    @classmethod
    def parse(cls, item: dict[str, Any]) -> 'Snapshot':
        if not isinstance(item, dict) or set(item) != set(cls.__dataclass_fields__):
            raise ValueError('Missing or unknown snapshot fields')
        source = item['source_id']
        if not isinstance(source, str) or not re.fullmatch(r'[0-9a-f]{64}', source):
            raise ValueError('Expected SHA-256 source receipt identity')
        return cls(integer(item['chain_id'], 'chain_id', minimum=1), hash32(item['pool_id']),
                   integer(item['block_number'], 'block_number'), hash32(item['block_hash']),
                   integer(item['timestamp'], 'timestamp'), integer(item['observed_head'], 'observed_head'),
                   raw_amount(item['pool_active_liquidity'], 'pool_active_liquidity', bits=128),
                   raw_amount(item['popl_active_liquidity'], 'popl_active_liquidity', bits=128), source)

    @property
    def record_id(self) -> str:
        return digest(asdict(self))

    @property
    def share(self) -> Fraction:
        if self.popl_active_liquidity > self.pool_active_liquidity:
            raise ValueError('PoPL active liquidity exceeds the entire pool active liquidity')
        return Fraction(self.popl_active_liquidity, self.pool_active_liquidity) if self.pool_active_liquidity else Fraction(0)


@dataclass(frozen=True)
class FeeEvent:
    chain_id: int
    pool_id: str
    block_number: int
    block_hash: str
    timestamp: int
    transaction_hash: str
    log_index: int
    asset: str
    raw_amount: int
    sample_id: str

    @classmethod
    def parse(cls, item: dict[str, Any]) -> 'FeeEvent':
        if not isinstance(item, dict) or set(item) != set(cls.__dataclass_fields__):
            raise ValueError('Missing or unknown fee event fields')
        sample_id = item['sample_id']
        if not isinstance(sample_id, str) or not re.fullmatch(r'[0-9a-f]{64}', sample_id):
            raise ValueError('Fee event must bind a snapshot record ID')
        return cls(integer(item['chain_id'], 'chain_id', minimum=1), hash32(item['pool_id']),
                   integer(item['block_number'], 'block_number'), hash32(item['block_hash']),
                   integer(item['timestamp'], 'timestamp'), hash32(item['transaction_hash']),
                   integer(item['log_index'], 'log_index'), asset_address(item['asset']),
                   raw_amount(item['raw_amount']), sample_id)


class Measurement:
    def __init__(self, snapshots: Iterable[Snapshot | dict[str, Any]], *, chain_id: int,
                 pool_id: str, start: int, end: int, max_gap_seconds: int,
                 min_confirmations: int):
        self.chain = integer(chain_id, 'chain_id', minimum=1)
        self.pool = hash32(pool_id)
        self.start = integer(start, 'start')
        self.end = integer(end, 'end', minimum=self.start + 1)
        self.max_gap = integer(max_gap_seconds, 'max_gap_seconds', minimum=1)
        self.depth = integer(min_confirmations, 'min_confirmations', minimum=1)
        self.samples = []
        for item in snapshots:
            if len(self.samples) == MAX_RECORDS:
                raise ValueError('Snapshot inventory exceeds the bounded record count')
            # Even dataclass instances are revalidated: direct construction is
            # not an alternate way to skip bounds/provenance validation.
            sample = Snapshot.parse(asdict(item) if isinstance(item, Snapshot) else item)
            if sample.chain_id != self.chain or sample.pool_id != self.pool:
                raise ValueError('Snapshot belongs to another chain or pool')
            if sample.observed_head - sample.block_number + 1 < self.depth:
                raise ValueError('Snapshot lacks the required confirmation depth')
            sample.share
            self.samples.append(sample)
        if len(self.samples) < 2 or self.samples[0].timestamp != self.start or self.samples[-1].timestamp != self.end:
            raise ValueError('Complete exact start/end boundary snapshots are required')
        seen = set()
        for sample in self.samples:
            if sample.block_hash in seen:
                raise ValueError('Duplicate or conflicting snapshot block hash')
            seen.add(sample.block_hash)
        for previous, current in zip(self.samples, self.samples[1:]):
            if current.block_number <= previous.block_number or current.timestamp <= previous.timestamp:
                raise ValueError('Snapshot blocks/times must be strictly increasing; no overlaps or reorder')
            if current.timestamp - previous.timestamp > self.max_gap:
                raise ValueError('Snapshot gap exceeds the approved sampling bound')

    def _base(self, policy: str) -> dict[str, Any]:
        return {'schema': 1, 'policy': policy, 'policy_status': 'proposal_not_creator_approved',
                'chain_id': self.chain, 'pool_id': self.pool, 'start': self.start, 'end': self.end,
                'window': '[start,end)', 'min_confirmations': self.depth,
                'max_gap_seconds': self.max_gap,
                'source_records': [sample.record_id for sample in self.samples],
                'canonicality': 'Offline provenance validation; block hashes must be independently verified.',
                'limitation': 'Sampled active-liquidity share; not actual historical v4 fee-growth/tick-crossing attribution.',
                'moves_funds': False}

    def time_weighted(self) -> dict[str, Any]:
        intervals = []
        weighted = Fraction(0)
        for previous, current in zip(self.samples, self.samples[1:]):
            seconds = current.timestamp - previous.timestamp
            weighted += previous.share * seconds
            intervals.append({'start': previous.timestamp, 'end': current.timestamp,
                              'sample_id': previous.record_id, 'share': fraction_json(previous.share)})
        report = self._base('time_weighted_active')
        report.update({'share': fraction_json(weighted / (self.end - self.start)), 'intervals': intervals})
        report['report_sha256'] = digest(report)
        return report

    def fee_weighted(self, events: Iterable[FeeEvent | dict[str, Any]], *, admitted_assets: Iterable[str],
                     events_complete: bool) -> dict[str, Any]:
        if events_complete is not True:
            raise ValueError('Complete confirmed fee event inventory must be explicitly attested')
        assets = [asset_address(a) for a in admitted_assets]
        if not assets or len(assets) > 32 or len(assets) != len(set(assets)):
            raise ValueError('One to 32 distinct admitted raw fee assets are required')
        samples = {s.record_id: (s, nxt) for s, nxt in zip(self.samples, self.samples[1:])}
        totals = {asset: 0 for asset in assets}
        weighted = {asset: Fraction(0) for asset in assets}
        count = {asset: 0 for asset in assets}
        seen = set()
        block_hashes = {s.block_number: s.block_hash for s in self.samples}
        block_times = {s.block_number: s.timestamp for s in self.samples}
        transaction_blocks = {}
        inventory = []
        for item in events:
            if len(inventory) == MAX_RECORDS:
                raise ValueError('Fee event inventory exceeds the bounded record count')
            event = FeeEvent.parse(asdict(item) if isinstance(item, FeeEvent) else item)
            if event.chain_id != self.chain or event.pool_id != self.pool or event.asset not in totals:
                raise ValueError('Fee event chain/pool/asset is not admitted')
            pair = samples.get(event.sample_id)
            if pair is None:
                raise ValueError('Fee event is not bound to an admitted left-hand interval sample')
            sample, nxt = pair
            # Samples are END-of-block states. A fee in the next sample's
            # block must bind its PREVIOUS block sample, never the post-trade
            # state of its own block. Internal right endpoints are included;
            # the overall period still excludes timestamp == end.
            if not sample.timestamp <= event.timestamp <= nxt.timestamp or not self.start <= event.timestamp < self.end or not sample.block_number < event.block_number <= nxt.block_number:
                raise ValueError('Fee event is not strictly after its prior-block sample within the interval')
            if self.samples[-1].observed_head - event.block_number + 1 < self.depth:
                raise ValueError('Fee event lacks required confirmation depth')
            key = (event.transaction_hash, event.log_index)
            if key in seen:
                raise ValueError('Duplicate fee event identity')
            seen.add(key)
            block_identity = (event.block_hash, event.timestamp)
            if event.block_number in block_hashes and (block_hashes[event.block_number], block_times[event.block_number]) != block_identity:
                raise ValueError('Fee events disagree about their canonical block hash/time')
            block_hashes[event.block_number] = event.block_hash
            block_times[event.block_number] = event.timestamp
            if event.transaction_hash in transaction_blocks and transaction_blocks[event.transaction_hash] != event.block_number:
                raise ValueError('One transaction cannot belong to multiple blocks')
            transaction_blocks[event.transaction_hash] = event.block_number
            totals[event.asset] += event.raw_amount
            weighted[event.asset] += sample.share * event.raw_amount
            count[event.asset] += 1
            inventory.append(asdict(event))
        times = [timestamp for _, timestamp in sorted(block_times.items())]
        if any(current < previous for previous, current in zip(times, times[1:])):
            raise ValueError('Fee event timestamps contradict chain block order')
        # Deterministic output independent of event ingestion order. On-chain
        # order is still recorded and duplicate identities are never aggregated.
        inventory.sort(key=lambda e: (e['block_number'], e['transaction_hash'], e['log_index']))
        report = self._base('fee_weighted_sampled_active')
        report['event_inventory_sha256'] = digest(inventory)
        report['event_completeness'] = 'Operator-attested complete; the offline calculator cannot prove omitted logs absent.'
        report['assets'] = [{'asset': asset, 'fee_events': count[asset], 'raw_fee_total': str(totals[asset]),
                             'share': fraction_json(weighted[asset] / totals[asset]) if totals[asset] else None,
                             'unavailable_reason': None if totals[asset] else 'No positive raw fee observations for this asset.'}
                            for asset in sorted(assets)]
        report['report_sha256'] = digest(report)
        return report


def allocate_receipt(receipt_raw: Any, share: Fraction) -> dict[str, Any]:
    """Proposed floor allocation of one raw-asset creator receipt; no transfer.

    The creator retained amount includes the sub-unit rounding remainder. It is
    not a second PoPL liability or an extra amount to add to the receipt.
    """
    receipt = raw_amount(receipt_raw, 'creator_receipt_raw')
    if not isinstance(share, Fraction) or not 0 <= share <= 1:
        raise ValueError('Allocation requires an exact share from zero through one')
    exact = receipt * share
    payment = exact.numerator // exact.denominator
    return {'creator_receipt_raw': str(receipt), 'share': fraction_json(share),
            'proposed_popl_raw': str(payment), 'creator_retained_raw': str(receipt - payment),
            'fractional_raw_unit_remainder': fraction_json(exact - payment),
            'rounding_policy': 'floor_each_window; sub-unit remainder stays with creator unless separately agreed',
            'moves_funds': False}


def calculate(dataset: dict[str, Any]) -> dict[str, Any]:
    required = {'schema', 'policy', 'chain_id', 'pool_id', 'start', 'end', 'max_gap_seconds',
                'min_confirmations', 'snapshots', 'creator_receipts', 'admitted_fee_assets'}
    if not isinstance(dataset, dict) or dataset.get('schema') != 1 or type(dataset.get('schema')) is not int:
        raise ValueError('Expected revenue-share dataset schema 1')
    policy = dataset.get('policy')
    if policy == 'fee_weighted_sampled_active':
        required |= {'events_complete', 'fee_events'}
    elif policy != 'time_weighted_active':
        raise ValueError('Unknown proposed measurement policy')
    if set(dataset) != required:
        raise ValueError('Missing or unknown revenue-share dataset fields')
    if not isinstance(dataset['admitted_fee_assets'], list):
        raise ValueError('A reviewed fee-asset allowlist is required')
    admitted = [asset_address(a) for a in dataset['admitted_fee_assets']]
    if not admitted or len(admitted) > 32 or len(set(admitted)) != len(admitted):
        raise ValueError('One to 32 distinct admitted raw fee assets are required')
    measurement = Measurement(dataset['snapshots'], **{k: dataset[k] for k in
                              ('chain_id', 'pool_id', 'start', 'end', 'max_gap_seconds', 'min_confirmations')})
    if policy == 'time_weighted_active':
        report = measurement.time_weighted()
        shares = None
    else:
        report = measurement.fee_weighted(dataset['fee_events'], admitted_assets=dataset['admitted_fee_assets'],
                                           events_complete=dataset['events_complete'])
        shares = {item['asset']: item['share'] for item in report['assets']}
    if not isinstance(dataset['creator_receipts'], list) or len(dataset['creator_receipts']) > 32:
        raise ValueError('Creator receipts must be a bounded per-asset list')
    allocations = []
    seen = set()
    for receipt in dataset['creator_receipts']:
        if not isinstance(receipt, dict) or set(receipt) != {'asset', 'raw_amount'}:
            raise ValueError('Expected one actual creator receipt amount per asset')
        asset = asset_address(receipt['asset'])
        if asset not in admitted:
            raise ValueError('Creator receipt is not an admitted fee asset')
        if asset in seen:
            raise ValueError('Consolidate creator receipts once per asset and window')
        seen.add(asset)
        fraction = report['share'] if shares is None else shares.get(asset)
        if fraction is None:
            raise ValueError('No fee-weighted share available for the creator receipt asset')
        share = Fraction(int(fraction['numerator']), int(fraction['denominator']))
        allocations.append({'asset': asset, **allocate_receipt(receipt['raw_amount'], share)})
    report['creator_receipt_allocations'] = sorted(allocations, key=lambda x: x['asset'])
    report['dataset_sha256'] = digest(dataset)
    report.pop('report_sha256')
    report['report_sha256'] = digest(report)
    return report


def collect_snapshot(rpc: Rpc, config: dict[str, Any], block_number: int) -> Snapshot:
    """Read one existing local shared position at a canonical confirmed block.

    Fixed code/address pins come from an independently reviewed deployment
    manifest. No arbitrary eth_call, sender, transaction or callback is accepted.
    """
    fields = {'chain_id', 'pool_id', 'bucket_id', 'min_confirmations', 'contracts'}
    if not isinstance(config, dict) or set(config) != fields:
        raise ValueError('Missing or unknown snapshot collector fields')
    chain = integer(config['chain_id'], 'chain_id', minimum=1)
    pool = hash32(config['pool_id'])
    bucket = raw_amount(config['bucket_id'], 'bucket_id')
    if bucket == 0:
        raise ValueError('A nonzero shared bucket is required')
    depth = integer(config['min_confirmations'], 'min_confirmations', minimum=1)
    number = integer(block_number, 'block_number')
    roles = {'state_view', 'position_manager', 'pool_manager', 'vault'}
    if not isinstance(config['contracts'], dict) or set(config['contracts']) != roles:
        raise ValueError('Four reviewed collector contract pins are required')
    pins = {}
    for role, item in config['contracts'].items():
        if not isinstance(item, dict) or set(item) != {'address', 'code_hash'}:
            raise ValueError('Invalid collector runtime pin')
        pins[role] = (address(item['address']), hash32(item['code_hash']))
    if len({item[0] for item in pins.values()}) != 4:
        raise ValueError('Collector contract addresses must be distinct')
    if rpc.call('eth_chainId', []) != chain:
        raise RpcError('Collector chain differs from reviewed deployment')
    head = int(rpc.call('eth_blockNumber', []), 16)
    if head - number + 1 < depth:
        raise RpcError('Selected sample block lacks the required confirmation depth')
    header = rpc.call('eth_getBlockByNumber', [hex(number), False])
    if not isinstance(header, dict) or int(header['number'], 16) != number:
        raise RpcError('Missing or misnumbered snapshot block')
    block_hash = hash32(header['hash'])
    timestamp = int(header['timestamp'], 16)
    block = {'blockHash': block_hash, 'requireCanonical': True}
    for addr, code_hash in pins.values():
        code = rpc.call('eth_getCode', [addr, block])
        if not isinstance(code, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', code) or '0x' + keccak256(bytes.fromhex(code[2:])).hex() != code_hash:
            raise RpcError('Collector runtime differs from reviewed deployment')

    def call(role, signature, *args, words=1):
        data = decode_words(rpc.call('eth_call', [{'to': pins[role][0], 'data': calldata(signature, *args)}, block]))
        if len(data) != words:
            raise RpcError('Unexpected collector static ABI return length')
        return data

    def result_addr(word):
        if int(word[:24], 16) != 0:
            raise RpcError('Noncanonical collector ABI address')
        return address('0x' + word[24:])

    for role in ('state_view', 'position_manager'):
        if result_addr(call(role, 'poolManager()')[0]) != pins['pool_manager'][0]:
            raise RpcError('Collector pool manager bindings disagree')
    if int(call('vault', 'poolBucket(bytes32)', pool)[0], 16) != bucket:
        raise RpcError('Pool is not assigned to the reviewed canonical bucket')
    group = call('vault', 'group(uint256)', bucket, words=15)
    if '0x' + group[0] != pool or int(group[7], 16) != 1:
        raise RpcError('No active local custody in the selected pool')
    if int(group[8], 16) != chain or result_addr(group[9]) != pins['vault'][0] or int(group[13], 16) != chain or result_addr(group[14]) != pins['vault'][0]:
        raise RpcError('Remote/in-flight/imported custody cannot be sampled as local home LP')
    lp_id = int(group[1], 16)
    if lp_id == 0 or result_addr(call('position_manager', 'ownerOf(uint256)', lp_id)[0]) != pins['vault'][0]:
        raise RpcError('LP NFT is not owned by the reviewed vault')
    info = call('position_manager', 'getPoolAndPositionInfo(uint256)', lp_id, words=6)
    if '0x' + keccak256(bytes.fromhex(''.join(info[:5]))).hex() != pool:
        raise RpcError('LP NFT belongs to a different actual v4 pool')
    packed = int(info[5], 16)
    def signed24(value):
        return value - (1 << 24) if value >= 1 << 23 else value
    lower = signed24((packed >> 8) & ((1 << 24) - 1))
    upper = signed24((packed >> 32) & ((1 << 24) - 1))
    if not -887272 <= lower < upper <= 887272:
        raise RpcError('Invalid physical LP tick range')
    slot = call('state_view', 'getSlot0(bytes32)', pool, words=4)
    tick = int(slot[1], 16)
    tick = tick - (1 << 256) if tick >= 1 << 255 else tick
    if not -887272 <= tick <= 887272 or int(slot[0], 16) == 0:
        raise RpcError('Uninitialized or malformed pool slot0')
    total = raw_amount(int(call('state_view', 'getLiquidity(bytes32)', pool)[0], 16), bits=128)
    liquidity = raw_amount(int(call('position_manager', 'getPositionLiquidity(uint256)', lp_id)[0], 16), bits=128)
    active = liquidity if lower <= tick < upper else 0
    if active > total:
        raise RpcError('Owned active liquidity exceeds the pool active liquidity')
    after = rpc.call('eth_getBlockByNumber', [hex(number), False])
    if not isinstance(after, dict) or hash32(after['hash']) != block_hash or int(after['number'], 16) != number or int(after['timestamp'], 16) != timestamp:
        raise RpcError('Canonical block changed during snapshot collection')
    if rpc.call('eth_chainId', []) != chain:
        raise RpcError('RPC chain changed during snapshot collection')
    return Snapshot(chain, pool, number, block_hash, timestamp, head, total, active, digest(config))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    calculate_parser = sub.add_parser('calculate', help='Calculate a proposed share from a complete immutable dataset')
    calculate_parser.add_argument('--input', required=True)
    calculate_parser.add_argument('--output', required=True)
    sample_parser = sub.add_parser('snapshot', help='Read one confirmed actual shared LP position')
    sample_parser.add_argument('--config', required=True)
    sample_parser.add_argument('--block', required=True, type=int)
    sample_parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'calculate':
        result = calculate(json.loads(Path(args.input).read_text(encoding='utf-8')))
    else:
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        if not isinstance(config, dict) or set(config) != {'rpc_urls', 'measurement'}:
            raise ValueError('Expected fixed RPC URLs and measurement collector configuration')
        rpc = Rpc(config['rpc_urls'], integer(config['measurement']['chain_id'], 'chain_id', minimum=1))
        result = asdict(collect_snapshot(rpc, config['measurement'], args.block))
    atomic_json(args.output, result)
    print(json.dumps({'event': 'revenue_share_artifact_written', 'command': args.command,
                      'sha256': digest(result), 'moves_funds': False}))


if __name__ == '__main__':
    main()
