"""Current local Position3 activation composition; all RPC/trace data are offline."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions, ActivationInputError
from frontend_api.service import Projection, ProjectionError, ZERO
from tests_python.test_dual_price_integration import DualActivationRPC, install
from tests_python.test_frontend_api import addr, configuration
from tests_python.test_native_backend_boundary import native_data
from zzz_ops.abi import calldata, keccak256


class CurrentActivationRPC(DualActivationRPC):
    """Use the established byte-level dual-price trace with explicit current bindings."""

    def __init__(self, **options):
        super().__init__(**options)
        self.put(addr(3), 'ACCOUNTING_VERSION()', values=(3,))
        self.put(addr(7), 'SCHEMA()', values=(
            '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4').hex(),))
        self.put(addr(1), 'GOVERNANCE_VERSION()', values=(2,))
        self.put(addr(1), 'governance()', values=(addr(70),))
        self.put(addr(3), 'nftStatus(uint256)', (self.nft_id,),
                 (1 if self.request['action'] == 'increase' else 3,))
        old = self.responses[addr(3), calldata('group(uint256)', self.bucket)]
        self.responses[addr(3), calldata('group(uint256)', self.bucket)] = old[:2 + 64 * 8]
        # Current inputs are native ETH and the actual pair's single ZZZ identity.
        zzz = addr(21)
        policy = '0x' + 'c' * 64
        self.config['sources'].append(dict(pool_id=self.pool, source_asset=zzz,
            route_id='0x' + '0' * 64, asset_policy_id=policy, route_kind=0))
        source_policy = self.pins['activation_assets']
        self.put(source_policy, 'SOURCE_POLICY_VERSION()', values=(1,))
        self.put(source_policy, 'zzz()', values=(zzz,))
        for token in (ZERO, zzz):
            self.native_put(source_policy, 'isContributionAsset(address)', (token,), (1,))
        self.put(source_policy, 'activePolicy(address)', (zzz,), (policy,))
        self.put(source_policy, 'policies(bytes32)', (policy,),
                 (zzz, 1, self.digest(zzz), '0x' + 'e' * 64, 18, 1))
        self.put(source_policy, 'value(address,uint256)', (zzz, self.original_amount), (100 * 10**18,))
        install(self)


class CurrentActivationProfileTests(unittest.TestCase):
    def service(self, *, version=3, **options):
        rpc = CurrentActivationRPC(**options) if version == 3 else install(DualActivationRPC(**options))
        config = configuration()
        config['accounting_version'] = version
        if version == 3:
            config['fee_intake_version'] = 1
            config['assets'] = [config['assets'][0], dict(address=addr(21), decimals=18,
                symbol='ZZZ', code_hash=rpc.digest(addr(21)))]
        projection = Projection(config, rpc, clock=lambda: 1000)
        return rpc, projection, ActivationTransactions(projection, rpc.config)

    def test_current_dormant_activation_new_pool_and_active_growth_prepare(self):
        for options in ({}, {'new_pool': True}, {'increase': True}):
            with self.subTest(options=options):
                rpc, p, service = self.service(**options)
                result = service.prepare(rpc.request)
                self.assertTrue(result['activation_ready'])
                self.assertEqual(result['provenance']['accounting_version'], 3)
                self.assertEqual(result['provenance']['review_policy_version'], 1)
                self.assertEqual(result['source']['asset'], ZERO)
                self.assertEqual(result['transaction']['value'], hex(rpc.original_amount))
                self.assertEqual(rpc.trace_count, 2)
                self.assertEqual(p.dormant_status, 3)

    def test_current_zzz_requires_only_exact_approval_before_fresh_review(self):
        rpc, _p, service = self.service()
        rpc.request['source_asset'] = addr(21)
        rpc.allowance = 0
        result = service.prepare(rpc.request)
        self.assertEqual(result['kind'], 'approval_required')
        self.assertFalse(result['activation_ready'])
        self.assertEqual(result['approval_steps'][0]['amount_raw'], str(rpc.original_amount))
        self.assertEqual(result['transaction']['data'],
            calldata('approve(address,uint256)', rpc.pins['entry'], rpc.original_amount))
        self.assertEqual(result['transaction']['to'], addr(21))
        self.assertEqual(result['transaction']['value'], '0x0')
        self.assertEqual(rpc.trace_count, 0)

    def test_current_native_policy_getter_is_typed_and_other_zero_uses_stay_rejected(self):
        rpc, p, _service = self.service()
        block = {'blockHash': rpc.hash, 'requireCanonical': True}
        target = rpc.pins['activation_assets']
        self.assertEqual(int(p._call(target, 'isContributionAsset(address)', ZERO, block=block)[0], 16), 1)
        self.assertEqual(rpc.calls[-1][1][0]['data'], native_data('isContributionAsset(address)', ZERO))
        for target, signature, args in ((ZERO, 'isContributionAsset(address)', (ZERO,)),
                (addr(2), 'ownerOf(address)', (ZERO,)),
                (addr(1), 'unreviewedAddress(address)', (ZERO,))):
            with self.subTest(signature=signature, target=target), self.assertRaises((ValueError, ProjectionError)):
                p._call(target, signature, *args, block=block)

    def test_explicit_historical_profile_keeps_old_dormant_value_and_native_preparation(self):
        rpc, p, service = self.service(version=2)
        self.assertEqual(p.dormant_status, 5)
        result = service.prepare(rpc.request)
        self.assertTrue(result['activation_ready'])
        self.assertEqual(result['provenance']['accounting_version'], 2)
        self.assertEqual(rpc.trace_count, 2)

    def test_dormant_codes_cannot_be_mixed_between_profiles_and_nonactive_growth_is_rejected(self):
        for version, status in ((3, 5), (3, 4), (3, 2), (2, 3), (2, 6)):
            with self.subTest(version=version, status=status):
                rpc, _p, service = self.service(version=version)
                rpc.put(addr(3), 'nftStatus(uint256)', (rpc.nft_id,), (status,))
                with self.assertRaisesRegex(ActivationInputError, 'custody state'):
                    service.prepare(rpc.request)
                self.assertEqual(rpc.trace_count, 0)
        for version in (2, 3):
            rpc, p, service = self.service(version=version, increase=True)
            rpc.put(addr(3), 'nftStatus(uint256)', (rpc.nft_id,), (p.dormant_status,))
            with self.subTest(version=version), self.assertRaisesRegex(ActivationInputError, 'custody state'):
                service.prepare(rpc.request)
            self.assertEqual(rpc.trace_count, 0)


if __name__ == '__main__':
    unittest.main()
