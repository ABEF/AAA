"""New current-build and exact historical-identity checks; no RPC or EVM run."""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import unittest

from zzz_ops import deployment_plan as D, factory_code_v5 as F5

ROOT = Path(__file__).resolve().parents[1]
FACTORY_NATIVE_PINS = {
    'zzz_ops/factory_code_v5.py':
        '3e41c39666784e514d35a53e6ed7996b0bd3522126d22c55dcf63dfc943dfb46',
    'config/factory-code-storage-v5.json':
        'd3273a94c8ffa6347bedec98947d04644a9cc3e6a156ebeceafc3d2ad3c3fd20',
}


def archived_royalty():
    """Authenticate the explicit archive without claiming current-source readiness."""
    spec = D.trusted_build(D.ROYALTY_BUILD_PROFILE)
    raws = {}
    for name, pin in spec['files'].items():
        with (ROOT / spec['directory'] / name).open('rb') as stream:
            raw = stream.read(D.MAX_BUILD + 1)
        if len(raw) > D.MAX_BUILD or hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('Historical royalty archive changed')
        raws[name] = raw

    def unpack(name):
        with gzip.GzipFile(fileobj=io.BytesIO(raws[name])) as stream:
            return D.decode(stream.read(D.MAX_BUILD + 1), D.MAX_BUILD)

    source = unpack('compiler-input.json.gz')
    output = unpack('compiler-output.json.gz')
    manifest = D.decode(raws[spec['source_inventory']], D.MAX_BUILD)
    pins = manifest[spec['source_key']]
    if len(source['sources']) != 100 or {
            name: hashlib.sha256(row['content'].encode('utf-8')).hexdigest()
            for name, row in source['sources'].items()} != pins:
        raise ValueError('Historical royalty source closure changed')
    return source, output, pins


class ActivationBuild20261118Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = D.Artifacts()
        cls.archived_input, cls.archived_output, cls.archived_pins = archived_royalty()

    def test_new_current_build_authenticates_all_sources_and_48_normal_gates(self):
        current = self.current
        self.assertEqual(D.DEFAULT_BUILD_PROFILE, 'activation-gas-20261118')
        self.assertEqual(current.profile, D.DEFAULT_BUILD_PROFILE)
        self.assertEqual(len(current.input['sources']), 100)
        self.assertEqual(len(current.source_pins), 100)
        self.assertEqual(set(current.input['sources']), set(current.source_pins))
        self.assertEqual(len([name for name in current.source_pins
                              if name.startswith('src/')]), 61)
        current.check_sources()
        spec = D.trusted_build(current.profile)
        gates = json.loads((ROOT / spec['directory'] / spec['gates']).read_bytes())['gates']
        self.assertEqual(len(gates), 48)
        for gate in gates:
            body = current.output['contracts'][gate['path']][gate['name']]['evm']
            runtime = len(body['deployedBytecode']['object']) // 2
            creation = len(body['bytecode']['object']) // 2
            self.assertEqual((runtime, creation), (gate['runtime'], gate['creation']))
            self.assertLessEqual(runtime, D.LIMITS['runtime_bytes'])
            self.assertLessEqual(creation + gate['minimum_args'],
                                 D.LIMITS['full_initcode_bytes'])
        changed_pin = copy.copy(current)
        changed_pin.source_pins = dict(current.source_pins)
        changed_pin.source_pins['src/ZZZOracle.sol'] = '0' * 64
        with self.assertRaisesRegex(D.PlanError, 'source_changed'):
            changed_pin.check_sources()

    def test_factory5_creation_parts_and_native_identity_are_exactly_preserved(self):
        current = self.current.output
        self.assertTrue(F5.verify_compiler_output(current))
        self.assertTrue(F5.verify_compiler_output(self.archived_output))
        source = 'src/ZZZRoyaltyRewards.sol'
        name = 'ZZZRoyaltyRewards'
        code = bytes.fromhex(current['contracts'][source][name]['evm']['bytecode']['object'])
        old = bytes.fromhex(self.archived_output['contracts'][source][name]['evm']['bytecode']['object'])
        self.assertEqual(code, old)
        parts = ['0x' + row.hex() for row in F5.split_creation(code)]
        before = ['0x' + row.hex() for row in F5.split_creation(old)]
        self.assertEqual(parts, before)
        observations, whole = F5.verify_runtime_parts(parts)
        self.assertEqual(whole['observed_creation_code_hash'], F5.SPEC.creation_hash)
        self.assertEqual(whole['observed_creation_code_length'], 25543)
        self.assertEqual([row['observed_runtime_length'] for row in observations],
                         [part.runtime_length for part in F5.SPEC.parts])
        for path, pin in FACTORY_NATIVE_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), pin)
        corrupted = list(parts)
        corrupted[0] = corrupted[0][:-2] + ('00' if corrupted[0][-2:] != '00' else '01')
        with self.assertRaises(ValueError):
            F5.verify_runtime_parts(corrupted)

    def test_historical_royalty_loader_stays_exact_and_cannot_replace_current_source(self):
        self.assertEqual(D.ROYALTY_BUILD_PROFILE, 'royalty-rounds-20261118')
        self.assertNotEqual(D.ROYALTY_BUILD_PROFILE, D.DEFAULT_BUILD_PROFILE)
        self.assertEqual(len(self.archived_pins), 100)
        expected = {'src/ZZZOracle.sol', 'src/ZZZV4SpotPriceFeed.sol',
                    'src/base/ZZZExactLPRewardsCanonical.sol',
                    'src/libraries/ExactLPAllocation.sol'}
        actual = {name for name, row in self.archived_input['sources'].items()
                  if row != self.current.input['sources'][name]}
        self.assertEqual(actual, expected)
        self.assertEqual(self.archived_input['sources']['src/ZZZRoyaltyRewards.sol'],
                         self.current.input['sources']['src/ZZZRoyaltyRewards.sol'])
        self.assertTrue(F5.verify_compiler_output(self.archived_output))
        # Archived bytes remain inspectable, but preparation requires today's files.
        with self.assertRaisesRegex(D.PlanError, 'source_changed'):
            D.Artifacts(build_profile=D.ROYALTY_BUILD_PROFILE)
        with self.assertRaisesRegex(D.PlanError, 'unsupported_build_profile'):
            D.Artifacts(build_profile='activation-gas-20261118-unreviewed')


if __name__ == '__main__':
    unittest.main()
