import copy
from dataclasses import asdict
from fractions import Fraction
import json
import unittest

from zzz_ops.abi import calldata, keccak256
from zzz_ops.revenue_share import (FeeEvent, Measurement, Snapshot, ZERO, allocate_receipt,
                                   calculate, collect_snapshot, digest)
from zzz_ops.rpc import RpcError


POOL = '0x' + '1' * 64
TOKEN = '0x' + '2' * 40


def h(number):
    return '0x' + f'{number:064x}'


def addr(number):
    return '0x' + f'{number:040x}'


def encoded(*values):
    return '0x' + ''.join(f'{(int(v, 16) if isinstance(v, str) else v) % (1 << 256):064x}' for v in values)


def samples():
    return [Snapshot(4663, POOL, 100 + n * 10, h(100 + n * 10), 1000 + n * 10, 200,
                     100, value, 'a' * 64) for n, value in enumerate((25, 75, 0, 50))]


def measurement(items=None):
    return Measurement(items if items is not None else samples(), chain_id=4663, pool_id=POOL,
                       start=1000, end=1030, max_gap_seconds=10, min_confirmations=12)


def event(sample_index=0, *, offset=5, amount=100, asset=ZERO, log_index=0):
    sample = samples()[sample_index]
    return FeeEvent(4663, POOL, sample.block_number + offset, h(sample.block_number + offset),
                    sample.timestamp + offset, h(10000 + sample_index * 100 + offset), log_index,
                    asset, amount, sample.record_id)


def dataset(policy='time_weighted_active'):
    value = {'schema': 1, 'policy': policy, 'chain_id': 4663, 'pool_id': POOL,
             'start': 1000, 'end': 1030, 'max_gap_seconds': 10, 'min_confirmations': 12,
             'snapshots': [asdict(s) for s in samples()], 'admitted_fee_assets': [ZERO, TOKEN],
             'creator_receipts': [{'asset': ZERO, 'raw_amount': '101'}]}
    if policy == 'fee_weighted_sampled_active':
        value.update({'events_complete': True, 'fee_events': [asdict(event(0)), asdict(event(1, amount=300)),
                                                           asdict(event(2))]})
    return value


class RevenueMeasurementTests(unittest.TestCase):
    def test_time_weighted_share_exact_one_third_and_explicit_intervals(self):
        report = measurement().time_weighted()
        self.assertEqual(report['share'], {'numerator': '1', 'denominator': '3'})
        self.assertEqual([(i['start'], i['end']) for i in report['intervals']], [(1000, 1010), (1010, 1020), (1020, 1030)])
        self.assertEqual(report['intervals'][2]['share']['numerator'], '0')
        self.assertFalse(report['moves_funds'])
        self.assertEqual(report['policy_status'], 'proposal_not_creator_approved')

    def test_fee_weighted_busy_period_and_separate_raw_asset_denominators(self):
        events = [event(0), event(1, amount=300), event(2),
                  event(0, offset=6, amount=1000, asset=TOKEN), event(1, offset=6, amount=100, asset=TOKEN)]
        report = measurement().fee_weighted(events, admitted_assets=[ZERO, TOKEN], events_complete=True)
        amounts = {item['asset']: item for item in report['assets']}
        self.assertEqual(amounts[ZERO]['raw_fee_total'], '500')
        self.assertEqual(amounts[ZERO]['share'], {'numerator': '1', 'denominator': '2'})
        self.assertEqual(amounts[TOKEN]['raw_fee_total'], '1100')
        self.assertEqual(amounts[TOKEN]['share'], {'numerator': '13', 'denominator': '44'})
        self.assertNotIn('combined_raw_fee_total', report)
        self.assertEqual(report, measurement().fee_weighted(reversed(events), admitted_assets=[TOKEN, ZERO], events_complete=True))

    def test_own_block_end_state_is_never_used_for_its_fee_event(self):
        prior = event(0, offset=10)
        report = measurement().fee_weighted([prior], admitted_assets=[ZERO], events_complete=True)
        self.assertEqual(report['assets'][0]['share'], {'numerator': '1', 'denominator': '4'})
        wrong = asdict(prior); wrong['sample_id'] = samples()[1].record_id
        with self.assertRaisesRegex(ValueError, 'prior-block'):
            measurement().fee_weighted([wrong], admitted_assets=[ZERO], events_complete=True)

    def test_missing_boundaries_gaps_and_order_fail_closed(self):
        originals = samples()
        variants = [originals[1:], originals[:-1], [originals[0], originals[2], originals[3]],
                    [originals[0], originals[2], originals[1], originals[3]],
                    originals[:2] + [originals[1]] + originals[2:]]
        for values in variants:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    measurement(values)

    def test_cross_chain_pool_underconfirmed_and_impossible_share_rejected(self):
        changes = ({'chain_id': 1}, {'pool_id': h(999)}, {'observed_head': 101},
                   {'popl_active_liquidity': 101}, {'pool_active_liquidity': 0},
                   {'block_hash': samples()[0].block_hash})
        for fields in changes:
            values = [asdict(s) for s in samples()]
            values[1].update(fields)
            with self.subTest(fields=fields):
                with self.assertRaises(ValueError):
                    measurement(values)

    def test_zero_total_active_and_zero_popl_share_is_zero_not_division_error(self):
        values = [asdict(s) for s in samples()]
        for item in values:
            item.update(pool_active_liquidity=0, popl_active_liquidity=0)
        self.assertEqual(measurement(values).time_weighted()['share'], {'numerator': '0', 'denominator': '1'})

    def test_raw_liquidity_never_passes_through_float_or_usd(self):
        values = [asdict(s) for s in samples()]
        for item in values:
            item.update(pool_active_liquidity=2**128 - 1, popl_active_liquidity=2**127 + 17)
        report = measurement(values).time_weighted()
        self.assertEqual(Fraction(int(report['share']['numerator']), int(report['share']['denominator'])),
                         Fraction(2**127 + 17, 2**128 - 1))
        for field, value in (('pool_active_liquidity', 100.0), ('chain_id', True), ('popl_active_liquidity', str(2**128))):
            bad = [asdict(s) for s in samples()]; bad[0][field] = value
            with self.assertRaises(ValueError):
                measurement(bad)

    def test_event_duplicate_unbound_wrong_chain_pool_asset_or_window_rejected(self):
        good = asdict(event())
        mutations = [{'sample_id': 'f' * 64}, {'chain_id': 1}, {'pool_id': h(99)}, {'asset': addr(44)},
                     {'timestamp': 1030}, {'block_number': 100}, {'timestamp': 999},
                     {'raw_amount': -1}, {'raw_amount': 1.5}, {'block_hash': '0x00'}]
        for changes in mutations:
            bad = dict(good, **changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    measurement().fee_weighted([bad], admitted_assets=[ZERO], events_complete=True)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            measurement().fee_weighted([good, good], admitted_assets=[ZERO], events_complete=True)
        with self.assertRaisesRegex(ValueError, 'Complete'):
            measurement().fee_weighted([good], admitted_assets=[ZERO], events_complete=False)

    def test_conflicting_block_and_transaction_provenance_rejected(self):
        first = asdict(event(log_index=0))
        second = dict(first, log_index=1, block_hash=h(999))
        with self.assertRaisesRegex(ValueError, 'block hash'):
            measurement().fee_weighted([first, second], admitted_assets=[ZERO], events_complete=True)
        second = asdict(event(offset=6)); second['transaction_hash'] = first['transaction_hash']; second['log_index'] = 1
        with self.assertRaisesRegex(ValueError, 'transaction'):
            measurement().fee_weighted([first, second], admitted_assets=[ZERO], events_complete=True)
        second = asdict(event(offset=6)); second['timestamp'] = first['timestamp'] - 1
        with self.assertRaisesRegex(ValueError, 'block order'):
            measurement().fee_weighted([first, second], admitted_assets=[ZERO], events_complete=True)

    def test_no_fees_is_explicit_unavailable_not_fabricated_share(self):
        report = measurement().fee_weighted([], admitted_assets=[ZERO], events_complete=True)
        self.assertIsNone(report['assets'][0]['share'])
        self.assertIn('No positive', report['assets'][0]['unavailable_reason'])

    def test_actual_receipt_floor_conservation_and_exact_dust(self):
        value = allocate_receipt('101', Fraction(1, 3))
        self.assertEqual(value['proposed_popl_raw'], '33')
        self.assertEqual(value['creator_retained_raw'], '68')
        self.assertEqual(value['fractional_raw_unit_remainder'], {'numerator': '2', 'denominator': '3'})
        for amount in (0, 1, 2**256 - 1):
            for share in (Fraction(0), Fraction(1, 3), Fraction(1)):
                item = allocate_receipt(amount, share)
                self.assertEqual(int(item['proposed_popl_raw']) + int(item['creator_retained_raw']), amount)
                self.assertLess(Fraction(int(item['fractional_raw_unit_remainder']['numerator']),
                                         int(item['fractional_raw_unit_remainder']['denominator'])), 1)
        for share in (0.5, Fraction(-1), Fraction(2)):
            with self.assertRaises(ValueError):
                allocate_receipt(100, share)

    def test_dataset_reports_hashes_and_no_payment_authority(self):
        value = dataset()
        report = calculate(value)
        self.assertEqual(report['creator_receipt_allocations'][0]['proposed_popl_raw'], '33')
        self.assertEqual(report['dataset_sha256'], digest(value))
        payload = dict(report); payload.pop('report_sha256')
        self.assertEqual(report['report_sha256'], digest(payload))
        self.assertEqual(report, calculate(json.loads(json.dumps(value))))
        fee = calculate(dataset('fee_weighted_sampled_active'))
        self.assertEqual(fee['creator_receipt_allocations'][0]['proposed_popl_raw'], '50')
        self.assertFalse(fee['creator_receipt_allocations'][0]['moves_funds'])

    def test_missing_fee_asset_evidence_cannot_allocate_creator_receipt(self):
        value = dataset('fee_weighted_sampled_active')
        value['creator_receipts'][0]['asset'] = TOKEN
        with self.assertRaisesRegex(ValueError, 'No fee-weighted'):
            calculate(value)
        value = dataset(); value['creator_receipts'][0]['asset'] = addr(44)
        with self.assertRaisesRegex(ValueError, 'admitted'):
            calculate(value)
        value = dataset(); value['creator_receipts'] *= 2
        with self.assertRaisesRegex(ValueError, 'Consolidate'):
            calculate(value)


class CollectorRPC:
    def __init__(self):
        self.calls = []
        self.number = 100
        self.head = 120
        self.hash = h(100)
        self.tick = -20
        self.reorg = False
        self.header_count = 0
        self.fail_hash_pin = False
        self.codes = {addr(n): '0x' + bytes([0x60, n, 0]).hex() for n in range(100, 104)}
        self.key = encoded(0, addr(7), 0, 60, addr(8))[2:]
        self.pool = '0x' + keccak256(bytes.fromhex(self.key)).hex()
        self.config = {'chain_id': 4663, 'pool_id': self.pool, 'bucket_id': 55, 'min_confirmations': 12,
                       'contracts': {role: {'address': addr(n), 'code_hash': '0x' + keccak256(bytes.fromhex(self.codes[addr(n)][2:])).hex()}
                                     for role, n in zip(('state_view', 'position_manager', 'pool_manager', 'vault'), range(100, 104))}}
        self.responses = {}
        self.put(100, 'poolManager()', (), (addr(102),))
        self.put(101, 'poolManager()', (), (addr(102),))
        self.put(103, 'poolBucket(bytes32)', (self.pool,), (55,))
        self.group = [self.pool, 77, 0, 0, 100, 1, 100, 1, 4663, addr(103), addr(99), ZERO, addr(7), 4663, addr(103)]
        self.put(103, 'group(uint256)', (55,), self.group)
        self.put(101, 'ownerOf(uint256)', (77,), (addr(103),))
        lower = (-60) % (1 << 24)
        info = (lower << 8) | (60 << 32)
        self.responses[(addr(101), calldata('getPoolAndPositionInfo(uint256)', 77))] = '0x' + self.key + encoded(info)[2:]
        self.put(100, 'getLiquidity(bytes32)', (self.pool,), (100,))
        self.put(101, 'getPositionLiquidity(uint256)', (77,), (34,))

    def put(self, target, signature, args, values):
        self.responses[(addr(target), calldata(signature, *args))] = encoded(*values)

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId':
            return 4663
        if method == 'eth_blockNumber':
            return hex(self.head)
        if method == 'eth_getBlockByNumber':
            self.header_count += 1
            return {'number': hex(self.number), 'hash': h(101) if self.reorg and self.header_count > 1 else self.hash,
                    'timestamp': hex(1000)}
        if method in ('eth_call', 'eth_getCode'):
            if self.fail_hash_pin or params[-1] != {'blockHash': self.hash, 'requireCanonical': True}:
                raise RpcError('No canonical EIP1898 support')
            if method == 'eth_getCode':
                return self.codes[params[0]]
            item = params[0]
            if item['data'] == calldata('getSlot0(bytes32)', self.pool):
                return encoded(1 << 96, self.tick, 0, 0)
            return self.responses[(item['to'], item['data'])]
        raise AssertionError('Unexpected RPC method ' + method)


class RevenueCollectorTests(unittest.TestCase):
    def setUp(self):
        self.rpc = CollectorRPC()

    def test_actual_v4_and_vault_abi_collector_reports_34_percent_active(self):
        result = collect_snapshot(self.rpc, self.rpc.config, 100)
        self.assertEqual(result.share, Fraction(17, 50))
        self.assertEqual(result.popl_active_liquidity, 34)
        self.assertEqual(result.pool_active_liquidity, 100)
        self.assertEqual(result.block_hash, h(100))
        self.assertEqual(result.source_id, digest(self.rpc.config))
        self.assertTrue(all(p[-1] == {'blockHash': h(100), 'requireCanonical': True}
                            for method, p in self.rpc.calls if method in ('eth_call', 'eth_getCode')))
        self.assertFalse(any('send' in method.lower() for method, _ in self.rpc.calls))

    def test_out_of_range_and_exact_upper_boundary_count_zero(self):
        for tick in (-61, 60, 1000):
            self.rpc.tick = tick
            result = collect_snapshot(self.rpc, self.rpc.config, 100)
            self.assertEqual(result.popl_active_liquidity, 0)
            self.assertEqual(result.share, Fraction(0))
        self.rpc.tick = -60
        self.assertEqual(collect_snapshot(self.rpc, self.rpc.config, 100).share, Fraction(17, 50))

    def test_reorg_runtime_hash_and_unsupported_block_hash_fail_closed(self):
        for issue in ('reorg', 'runtime', 'unsupported'):
            self.rpc = CollectorRPC()
            if issue == 'reorg': self.rpc.reorg = True
            if issue == 'runtime': self.rpc.codes[addr(103)] = '0x6000'
            if issue == 'unsupported': self.rpc.fail_hash_pin = True
            with self.subTest(issue=issue):
                with self.assertRaises(RpcError):
                    collect_snapshot(self.rpc, self.rpc.config, 100)

    def test_unconfirmed_wrong_pool_owner_and_remote_custody_rejected(self):
        for issue in ('unconfirmed', 'pool', 'owner', 'remote', 'missing'):
            self.rpc = CollectorRPC()
            if issue == 'unconfirmed': self.rpc.head = 105
            if issue == 'pool': self.rpc.put(103, 'poolBucket(bytes32)', (self.rpc.pool,), (56,))
            if issue == 'owner': self.rpc.put(101, 'ownerOf(uint256)', (77,), (addr(104),))
            if issue == 'remote':
                self.rpc.group[13] = 1
                self.rpc.put(103, 'group(uint256)', (55,), self.rpc.group)
            if issue == 'missing':
                self.rpc.group[7] = 3
                self.rpc.put(103, 'group(uint256)', (55,), self.rpc.group)
            with self.subTest(issue=issue):
                with self.assertRaises(RpcError):
                    collect_snapshot(self.rpc, self.rpc.config, 100)

    def test_actual_position_pool_key_mismatch_and_impossible_liquidity_rejected(self):
        self.rpc.put(101, 'getPositionLiquidity(uint256)', (77,), (101,))
        with self.assertRaisesRegex(RpcError, 'exceeds'):
            collect_snapshot(self.rpc, self.rpc.config, 100)
        self.rpc = CollectorRPC()
        self.rpc.responses[(addr(101), calldata('getPoolAndPositionInfo(uint256)', 77))] = encoded(0, addr(7), 0, 120, addr(8), 0)
        with self.assertRaisesRegex(RpcError, 'different actual'):
            collect_snapshot(self.rpc, self.rpc.config, 100)


if __name__ == '__main__':
    unittest.main()
