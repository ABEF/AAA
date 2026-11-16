"""Historical checkpoint descriptors; real admission logic, controlled reads."""
from types import SimpleNamespace
import unittest

from frontend_api.service import Projection, ProjectionError, ZERO


ZZZ = '0x'+'11'*20
FUTURE = '0x'+'22'*20
UNKNOWN = '0x'+'33'*20
BLOCK = {'blockHash': '0x'+'44'*32, 'requireCanonical': True}


class HistoricalAssetReads:
    """Exercise Projection._admitted without constructing or impersonating RPC."""
    accounting_version = 7
    royalty_reporting = SimpleNamespace(schema=5)

    def __init__(self, *, future=True):
        self.inventory = {'rewards': [ZERO, ZZZ], 'royalties': [ZERO]}
        self.assets = {a: SimpleNamespace(address=a, code_hash='0x'+'55'*32, decimals=18)
                       for a in ((ZERO, ZZZ, FUTURE) if future else (ZERO, ZZZ))}
        self.fixed = ZZZ
        self.reads = []
        self.bad_code = set()
        self.decimals = {ZZZ: 18, FUTURE: 18}

    @staticmethod
    def _block(block):
        if block != BLOCK:
            raise AssertionError('Admission must retain the exact historical anchor')

    def _uint(self, role, method, *, block):
        self._block(block)
        if method != 'assetCount()': raise AssertionError('Unexpected count read')
        return len(self.inventory[role])

    def _addr(self, role, method, *args, block, native=False):
        self._block(block)
        if (role, method) == ('principal_exit', 'currentZZZ()'): return self.fixed
        if method != 'assets(uint256)' or native is not True:
            raise AssertionError('Unexpected admitted-address read')
        return self.inventory[role][args[0]]

    def _code(self, target, expected, block):
        self._block(block)
        self.reads.append(('code', target))
        if expected != self.assets[target].code_hash or target in self.bad_code:
            raise ProjectionError('Controlled asset runtime differs')

    def _call(self, target, method, *, block):
        self._block(block)
        if method != 'decimals()': raise AssertionError('Unexpected asset call')
        self.reads.append(('decimals', target))
        return [f'{self.decimals[target]:064x}']

    def admitted(self, **kwargs):
        return Projection._admitted(self, BLOCK, **kwargs)


class HistoricalCheckpointAssetsTests(unittest.TestCase):
    def test_default_and_explicit_false_keep_exact_descriptor_union(self):
        for kwargs in ({}, {'historical_descriptors': False}):
            reads = HistoricalAssetReads()
            with self.subTest(kwargs=kwargs), self.assertRaises(ProjectionError):
                reads.admitted(**kwargs)
            self.assertEqual([], reads.reads)
        reads = HistoricalAssetReads(future=False)
        self.assertEqual(([ZERO, ZZZ], [ZERO]), reads.admitted())

    def test_historical_future_descriptor_is_allowed_without_future_token_reads(self):
        reads = HistoricalAssetReads()
        reads.bad_code.add(FUTURE)
        del reads.decimals[FUTURE]
        self.assertEqual(([ZERO, ZZZ], [ZERO]), reads.admitted(historical_descriptors=True))
        self.assertEqual([('code', ZZZ), ('decimals', ZZZ)], reads.reads)

    def test_historical_unknown_actual_currency_is_not_admitted(self):
        reads = HistoricalAssetReads()
        reads.inventory['royalties'].append(UNKNOWN)
        with self.assertRaisesRegex(ProjectionError, 'descriptor allowlist'):
            reads.admitted(historical_descriptors=True)
        self.assertEqual([], reads.reads)

    def test_historical_inventory_bounds_native_order_and_fixed_pair_are_retained(self):
        cases = [('rewards', [ZERO, ZZZ, FUTURE]), ('rewards', [ZERO]),
                 ('rewards', [ZZZ, ZERO]), ('rewards', [ZERO, FUTURE]),
                 ('royalties', []), ('royalties', [ZZZ, ZERO]),
                 ('royalties', [ZERO, ZERO]), ('royalties', [ZERO]*66)]
        for role, inventory in cases:
            reads = HistoricalAssetReads()
            reads.inventory[role] = inventory
            with self.subTest(role=role, inventory=inventory), self.assertRaises(ProjectionError):
                reads.admitted(historical_descriptors=True)

    def test_admitted_currency_runtime_and_decimals_still_fail_closed(self):
        for target in (ZZZ, FUTURE):
            for fault in ('code', 'decimals'):
                reads = HistoricalAssetReads()
                if target == FUTURE: reads.inventory['royalties'].append(FUTURE)
                if fault == 'code': reads.bad_code.add(target)
                else: reads.decimals[target] = 6
                with self.subTest(target=target, fault=fault), self.assertRaises(ProjectionError):
                    reads.admitted(historical_descriptors=True)

    def test_newly_admitted_reviewed_currency_gets_full_historical_validation(self):
        reads = HistoricalAssetReads()
        reads.inventory['royalties'].append(FUTURE)
        self.assertEqual(([ZERO, ZZZ], [ZERO, FUTURE]), reads.admitted(historical_descriptors=True))
        self.assertEqual([('code', ZZZ), ('decimals', ZZZ), ('code', FUTURE), ('decimals', FUTURE)], reads.reads)

    def test_historical_selection_requires_an_actual_boolean(self):
        for value in (None, 0, 1, 'true', [], {}):
            reads = HistoricalAssetReads()
            with self.subTest(value=value), self.assertRaises(ProjectionError):
                reads.admitted(historical_descriptors=value)
            self.assertEqual([], reads.reads)


if __name__ == '__main__':
    unittest.main()
