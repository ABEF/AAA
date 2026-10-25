"""Current LP-only profile boundaries; legacy fixtures are deliberately separate."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError
from frontend_api.activation_config import ActivationConfig
from frontend_api.activation import ActivationTransactions
from keeper.monitor import Keeper
from tests_python.test_frontend_api import configuration, addr
from tests_python.test_native_backend_boundary import NativeActivationRPC, BLOCK, ZERO
import tests_python.test_keeper_native as keeper_fixtures
from zzz_ops.abi import keccak256


class LPOnlyProjectionTests(unittest.TestCase):
    def test_activation_sources_are_bound_to_the_onchain_zzz_identity(self):
        rpc = NativeActivationRPC()
        cfg = configuration(); cfg.update(accounting_version=2, fee_intake_version=1)
        p = Projection(cfg, rpc, clock=lambda:1000)
        with self.assertRaisesRegex(ValueError, 'only native ETH'):
            ActivationConfig(rpc.config, p)
        source = copy.deepcopy(rpc.config['sources'][0]); source['source_asset'] = addr(21)
        rpc.config['sources'].append(source)
        parsed = ActivationConfig(rpc.config, p)
        self.assertEqual(parsed.zzz_input, addr(21))
        rpc.put(addr(7), 'SCHEMA()', values=('0x'+keccak256(
            b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V3').hex(),))
        rpc.put(rpc.pins['activation_assets'], 'SOURCE_POLICY_VERSION()', values=(1,))
        rpc.put(rpc.pins['activation_assets'], 'zzz()', values=(addr(22),))
        with self.assertRaisesRegex(ProjectionError, 'contribution identity differs'):
            ActivationTransactions(p, rpc.config).prepare(rpc.request)
        third = copy.deepcopy(source); third['source_asset'] = addr(22)
        rpc.config['sources'].append(third)
        with self.assertRaisesRegex(ValueError, 'only native ETH'):
            ActivationConfig(rpc.config, p)

    def test_current_schema_is_explicit_and_cannot_read_legacy_as_current(self):
        rpc = NativeActivationRPC()
        cfg = configuration(); cfg.update(accounting_version=2, fee_intake_version=1)
        service = Projection(cfg, rpc, clock=lambda: 1000)
        with self.assertRaisesRegex(ProjectionError, 'canonical schema'):
            service._verify_deployment(BLOCK)
        rpc.put(addr(7), 'SCHEMA()', values=('0x' + keccak256(
            b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V3').hex(),))
        service._verify_deployment(BLOCK)
        old = copy.deepcopy(cfg); old.pop('fee_intake_version')
        with self.assertRaisesRegex(ProjectionError, 'canonical schema'):
            Projection(old, rpc, clock=lambda: 1000)._verify_deployment(BLOCK)

    def test_unknown_profiles_never_coerce_or_downgrade(self):
        for version in (True, False, '1', 2, -1, None):
            cfg = configuration(); cfg.update(accounting_version=2, fee_intake_version=version)
            with self.subTest(version=version), self.assertRaises(ValueError):
                Projection(cfg, NativeActivationRPC())
        cfg = configuration(); cfg['fee_intake_version'] = 1
        with self.assertRaises(ValueError): Projection(cfg, NativeActivationRPC())


class LPOnlyKeeperTests(unittest.TestCase):
    def setUp(self):
        fixture = keeper_fixtures.NativeKeeperTests('runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f = fixture
        self.cfg = copy.deepcopy(fixture.cfg)
        self.cfg['fee_intake_version'] = 1
        self.cfg.setdefault('maintenance', {})['sync_external_rewards'] = False
        self.k = Keeper(self.cfg, rpc=fixture.rpc)

    def test_retired_job_and_direct_submission_fail_before_any_rpc(self):
        cfg = copy.deepcopy(self.cfg); cfg['maintenance']['sync_external_rewards'] = True
        with self.assertRaisesRegex(ValueError, 'creator-payment'):
            Keeper(cfg, rpc=self.f.rpc)
        with patch.object(self.f.rpc, 'call') as call:
            for method in ('syncExternal(uint256)', 'syncAllExternal()'):
                with self.assertRaisesRegex(ValueError, 'retired'):
                    self.k.submit('fees', method, (7,), 'retired')
            call.assert_not_called()

    def test_journal_version_cannot_be_silently_reinterpreted(self):
        self.k.save(); before = self.k.path.read_bytes()
        old = copy.deepcopy(self.cfg); old.pop('fee_intake_version')
        with self.assertRaisesRegex(ValueError, 'another fee-intake'):
            Keeper(old, rpc=self.f.rpc)
        self.assertEqual(before, self.k.path.read_bytes())

    def test_current_fee_runtime_and_version_are_required(self):
        with self.assertRaisesRegex(Exception, 'fee-controller runtime pin'):
            self.k._validate_accounting_version()
        self.cfg['code_hashes']['fees'] = '0x' + 'a' * 64
        with self.assertRaisesRegex(Exception, 'fee-controller runtime differs'):
            self.k._validate_accounting_version()


if __name__ == '__main__': unittest.main()
