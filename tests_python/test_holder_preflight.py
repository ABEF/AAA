import copy
import unittest
from unittest.mock import patch

from zzz_ops.abi import calldata, keccak256
from zzz_ops.holder_preflight import digest, scan_page, summarize
from zzz_ops.rpc import RpcError
from zzz_ops.errors import WorkLimit


def addr(n): return '0x' + format(n, '040x')
def encoded(n): return '0x' + format(n, '064x')
def code_hash(raw): return '0x' + keccak256(bytes.fromhex(raw[2:])).hex()


class FakeRPC:
    def __init__(self, count=3):
        self.calls = []
        self.header = {'number': '0x64', 'hash': encoded(987), 'timestamp': '0x3e8'}
        self.chain, self.head, self.reorg, self.header_reads = 42, 112, False, 0
        self.cfg = {'chain_id': 42, 'block_number': 100, 'block_hash': self.header['hash'],
                    'minimum_confirmations': 12, 'source': self.binding(1, 2), 'destination': None}
        self.codes = {addr(1): '0x6001', addr(2): '0x6002', addr(3): '0x6001', addr(4): '0x6002',
                      addr(10): '0x', addr(11): '0x60806040', addr(12): '0xef0100' + addr(77)[2:]}
        self.values = {}
        for c, n, state in ((1, 2, 0), (3, 4, 2)):
            for sig, value, args in (
                ('module(bytes32)', n, ('0x' + keccak256(b'ZZZNFT').hex(),)),
                ('isSealed()', 1, ()), ('canonicalState()', state, ()),
                ('preparationActive()', 0, ()), ('preparationHash()', 0, ())):
                self.set(addr(c), sig, value, *args)
            self.set(addr(n), 'access()', c)
        self.set(addr(2), 'mintedCount()', count)
        for ordinal in range(1, count + 1):
            self.set(addr(2), 'tokenAtOrdinal(uint256)', ordinal * 100, ordinal)
            self.set(addr(2), 'ownerOf(uint256)', 10 + (ordinal - 1) % 3, ordinal * 100)

    @staticmethod
    def binding(c, n):
        return {'controller': addr(c), 'nft': addr(n),
                'controller_code_hash': code_hash('0x6001'), 'nft_code_hash': code_hash('0x6002')}

    def set(self, target, sig, value, *args):
        self.values[(target, calldata(sig, *args))] = encoded(value)

    def call(self, method, args):
        self.calls.append((method, args))
        if method == 'eth_chainId': return self.chain
        if method == 'eth_getBlockByNumber':
            if args[0] == 'latest': return {'number': hex(self.head)}
            self.header_reads += 1
            return dict(self.header, hash=encoded(998)) if self.reorg and self.header_reads > 1 else self.header.copy()
        if method in ('eth_call', 'eth_getCode'):
            assert args[1] == {'blockHash': self.cfg['block_hash'], 'requireCanonical': True}
            if method == 'eth_getCode': return self.codes[args[0]]
            return self.values[(args[0]['to'], args[0]['data'])]
        raise AssertionError('Unexpected or non-read method: ' + method)


class HolderPreflightTest(unittest.TestCase):
    def scan(self, rpc=None, **kwargs):
        rpc = rpc or FakeRPC()
        return scan_page(rpc, rpc.cfg, now=lambda: 1001, **kwargs)

    def test_inventory_flags_contract_and_delegated_owners_without_approving(self):
        rpc = FakeRPC(); page = self.scan(rpc); report = summarize([page])
        self.assertTrue(report['complete']); self.assertFalse(report['release_approved'])
        self.assertTrue(report['requires_frozen_rescan'])
        self.assertEqual([v['kind'] for v in report['unresolved_contract_holders']], ['contract', 'delegated_account'])
        self.assertEqual(report['unresolved_contract_holders'][1]['delegation_target'], addr(77))
        self.assertEqual(report['unresolved_contract_holders'][0]['token_ids'], ['200'])
        self.assertTrue(all(m in ('eth_chainId', 'eth_getBlockByNumber', 'eth_call', 'eth_getCode') for m, _ in rpc.calls))

    def test_empty_collection_is_complete_but_never_release_approval(self):
        report = summarize([self.scan(FakeRPC(0))])
        self.assertTrue(report['complete']); self.assertEqual(report['inventoried_nfts'], 0)
        self.assertFalse(report['release_approved'])

    def test_pages_detect_missing_and_complete_all_1000_without_supply_change(self):
        rpc = FakeRPC(1000)
        pages = [self.scan(rpc, first=i, limit=50) for i in range(1, 1001, 50)]
        report = summarize(pages)
        self.assertTrue(report['complete']); self.assertEqual(report['inventoried_nfts'], 1000)
        self.assertEqual(summarize(pages[:-1])['missing_ordinals'], list(range(951, 1001)))

    def test_frozen_source_and_explicit_inert_replacement_still_require_review(self):
        rpc = FakeRPC(); rpc.cfg['destination'] = rpc.binding(3, 4)
        rpc.set(addr(1), 'canonicalState()', 1)
        report = summarize([self.scan(rpc)])
        self.assertFalse(report['requires_frozen_rescan']); self.assertFalse(report['replacement_not_supplied'])
        self.assertFalse(report['release_approved']); self.assertEqual(len(report['unresolved_contract_holders']), 2)

    def test_wrong_chain_runtime_binding_unsealed_or_retired_rejected(self):
        mutations = [lambda r: setattr(r, 'chain', 43),
                     lambda r: r.codes.update({addr(2): '0x00'}),
                     lambda r: r.set(addr(2), 'access()', 9),
                     lambda r: r.set(addr(1), 'isSealed()', 0),
                     lambda r: r.set(addr(1), 'canonicalState()', 3)]
        for mutate in mutations:
            rpc = FakeRPC(); mutate(rpc)
            with self.subTest(mutate=mutate), self.assertRaises(RpcError): self.scan(rpc)

    def test_reorg_and_missing_confirmations_rejected_after_reads(self):
        rpc = FakeRPC(); rpc.reorg = True
        with self.assertRaises(RpcError): self.scan(rpc)
        rpc = FakeRPC(); rpc.head = 111
        with self.assertRaises(RpcError): self.scan(rpc)

    def test_future_header_and_wrong_anchor_rejected(self):
        rpc = FakeRPC(); rpc.header['timestamp'] = '0xffff'
        with self.assertRaises(RpcError): self.scan(rpc)
        rpc = FakeRPC(); rpc.header['hash'] = encoded(123)
        with self.assertRaises(RpcError): self.scan(rpc)

    def test_zero_owner_duplicate_tokens_bad_code_rejected(self):
        for mutate in (
            lambda r: r.set(addr(2), 'ownerOf(uint256)', 0, 100),
            lambda r: r.set(addr(2), 'tokenAtOrdinal(uint256)', 100, 2),
            lambda r: r.codes.update({addr(11): '0xBAD'})):
            rpc = FakeRPC(); mutate(rpc)
            with self.assertRaises(RpcError): self.scan(rpc)

    def test_invalid_bounds_rejected_before_scanning(self):
        for args in ({'first': 0}, {'first': True}, {'limit': 51}, {'first': 1001}):
            with self.assertRaises(ValueError): self.scan(**args)
        rpc = FakeRPC(); rpc.set(addr(2), 'mintedCount()', 1001)
        with self.assertRaises(ValueError): self.scan(rpc)
        with self.assertRaises(ValueError): self.scan(FakeRPC(), first=4)

    def test_mixed_or_corrupted_pages_and_duplicate_rows_rejected(self):
        p = self.scan(limit=1); q = self.scan(first=2)
        with self.assertRaises(ValueError): summarize([p, p])
        corrupt = copy.deepcopy(q); corrupt['rows'][0]['owner'] = addr(99)
        with self.assertRaises(ValueError): summarize([p, corrupt])
        q['snapshot']['block_hash'] = encoded(999); q['sha256'] = digest({k: v for k, v in q.items() if k != 'sha256'})
        with self.assertRaises(ValueError): summarize([p, q])

    def test_replacement_must_be_distinct_sealed_and_inert(self):
        rpc = FakeRPC(); rpc.cfg['destination'] = rpc.cfg['source']
        with self.assertRaises(RpcError): self.scan(rpc)
        rpc = FakeRPC(); rpc.cfg['destination'] = rpc.binding(3, 4); rpc.set(addr(3), 'canonicalState()', 0)
        with self.assertRaises(RpcError): self.scan(rpc)

    def test_work_limit_propagates_without_partial_success(self):
        with patch('zzz_ops.holder_preflight.BudgetedRPC.call', side_effect=WorkLimit('deadline')):
            with self.assertRaises(WorkLimit): self.scan()


if __name__ == '__main__': unittest.main()
