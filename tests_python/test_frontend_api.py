"""Read-service contract/RPC boundary regressions, without a public network."""
import copy
import http.client
import json
import threading
import unittest

from frontend_api.server import ReadServer, handler
from frontend_api.service import Projection, ProjectionError, UnknownNFT, ZERO, token_id
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


def addr(n):
    return '0x' + f'{n:040x}'


def words(*values):
    return '0x' + ''.join(f'{int(value, 16) if isinstance(value, str) else value:064x}' for value in values)


def native_claim_data(nft_id):
    return calldata('claimable(uint256,address)', nft_id, addr(1))[:-64] + '0' * 64


def configuration():
    roles = ('access', 'nft', 'vault', 'rewards', 'royalties', 'claim_router', 'handoff', 'vault_canonical')
    return {
        'schema': 2, 'chain_id': 31337, 'rpc_urls': ['http://127.0.0.1:8545'],
        'deployment_block': 10, 'deployment_block_hash': '0x' + 'a' * 64,
        'confirmations': 12, 'max_block_age_seconds': 120,
        'contracts': {role: {'address': addr(n), 'code_hash': '0x' + keccak256(bytes([0x60, n, 0])).hex()}
                      for n, role in enumerate(roles, 1)},
        'assets': [{'address': ZERO, 'decimals': 18, 'symbol': 'ETH', 'code_hash': None},
                   {'address': addr(20), 'decimals': 18, 'symbol': 'ZZZ', 'code_hash': '0x' + keccak256(b'ZZZ').hex()},
                   {'address': addr(21), 'decimals': 6, 'symbol': 'USDC', 'code_hash': '0x' + keccak256(b'USDC').hex()}],
    }


class MockRPC:
    """Byte-level RPC fixture using real selectors, including native address(0).

    Claims are deliberately not computed by this server: exact deployed view
    values are the only admitted source. Pending royalties can differ from LP.
    """
    def __init__(self):
        self.head = 110
        self.chain = 31337
        self.hash = '0x' + 'b' * 64
        self.anchor = '0x' + 'a' * 64
        self.header_timestamp = 990
        self.calls = []
        self.responses = {}
        self.codes = {addr(n): '0x' + bytes([0x60, n, 0]).hex() for n in range(1, 9)}
        self.codes.update({addr(20): '0x' + b'ZZZ'.hex(), addr(21): '0x' + b'USDC'.hex()})
        self.fail_hash_pin = False
        self.reorg_after_calls = False
        self.header_reads = 0
        self.configure()

    def put(self, target, signature, arguments=(), values=(0,)):
        data = native_claim_data(arguments[0]) if signature == 'claimable(uint256,address)' and arguments[1] == ZERO else calldata(signature, *arguments)
        self.responses[(target, data)] = words(*values)

    def configure(self):
        self.put(addr(1), 'isSealed()', values=(1,))
        for signature in ('canonicalState()', 'preparationActive()', 'paused()', 'canonicalSettling()'):
            self.put(addr(1), signature)
        for n, label in ((7, 'ZZZCanonicalHandoff'), (8, 'ZZZVaultCanonical')):
            self.put(addr(1), 'module(bytes32)', ('0x' + keccak256(label.encode()).hex(),), (addr(n),))
            self.put(addr(n), 'access()', values=(addr(1),))
        self.put(addr(1), 'canonicalHandoff()', values=(addr(7),))
        self.put(addr(3), 'canonicalModule()', values=(addr(8),))
        self.put(addr(8), 'vault()', values=(addr(3),))
        self.put(addr(8), 'originChain()', values=(31337,))
        self.put(addr(8), 'originVault()', values=(addr(3),))
        for signature in ('phase()', 'incomingSource()', 'destinationController()'):
            self.put(addr(7), signature)
        for role, label, n in (('nft', 'ZZZNFT', 2), ('vault', 'ZZZVault', 3), ('rewards', 'ZZZRewards', 4)):
            self.put(addr(1), 'module(bytes32)', ('0x' + keccak256(label.encode()).hex(),), (addr(n),))
            self.put(addr(n), 'access()', values=(addr(1),))
        self.put(addr(3), 'canonicalChainId()', values=(31337,))
        for target, sig, destination in ((2, 'royaltyRewards()', 5), (2, 'claimRouter()', 6),
                                         (5, 'nft()', 2), (6, 'nft()', 2),
                                         (6, 'royalties()', 5), (6, 'access()', 1)):
            self.put(addr(target), sig, values=(addr(destination),))
        for target, assets in ((4, [addr(20), addr(21)]), (5, [ZERO, addr(21)])):
            self.put(addr(target), 'assetCount()', values=(len(assets),))
            for n, asset in enumerate(assets):
                self.put(addr(target), 'assets(uint256)', (n,), (asset,))
        self.put(addr(20), 'decimals()', values=(18,))
        self.put(addr(21), 'decimals()', values=(6,))
        # Hashed production identities are not short mint ordinals.
        self.nft_id = int.from_bytes(keccak256(b'canonical NFT identity'), 'big')
        i = self.nft_id
        for signature, value in (('mintOrdinalOf(uint256)', 444), ('traitsReady(uint256)', 1),
                                  ('rarityOf(uint256)', 1), ('paletteOf(uint256)', 24),
                                  ('patternOf(uint256)', 2)):
            self.put(addr(2), signature, (i,), (value,))
        self.put(addr(2), 'tokenAtOrdinal(uint256)', (444,), (i,))
        self.put(addr(2), 'ownerOf(uint256)', (i,), (addr(30),))
        for signature, value in (('nftStatus(uint256)', 1), ('nftBucket(uint256)', 5), ('sharesOf(uint256)', 10**36)):
            self.put(addr(3), signature, (i,), (value,))
        self.put(addr(5), 'weightOf(uint256)', (i,), (2,))
        self.put(addr(2), 'currentLPValue(uint256)', (i,), (1, 1432 * 10**18))
        self.put(addr(4), 'claimable(uint256,address)', (i, addr(20)), (5 * 10**18 + 17,))
        self.put(addr(4), 'claimable(uint256,address)', (i, addr(21)), (1234567,))
        # The actual royalty view includes unsynced admitted ETH; not LP revenue.
        self.put(addr(5), 'claimable(uint256,address)', (i, ZERO), (33333333333333333333,))
        self.put(addr(5), 'claimable(uint256,address)', (i, addr(21)), (25000001,))

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId':
            return self.chain
        if method == 'eth_blockNumber':
            return hex(self.head)
        if method == 'eth_getBlockByNumber':
            number = int(params[0], 16)
            self.header_reads += 1
            digest = self.anchor if number == 10 else self.hash
            if self.reorg_after_calls and self.header_reads > 2:
                digest = '0x' + 'c' * 64
            return {'number': hex(number), 'hash': digest, 'timestamp': hex(self.header_timestamp)}
        if method in ('eth_call', 'eth_getCode'):
            if params[-1] != {'blockHash': self.hash, 'requireCanonical': True} or self.fail_hash_pin:
                raise RpcError('Unsupported or noncanonical block hash')
            if method == 'eth_getCode':
                return self.codes[params[0]]
            tx = params[0]
            if set(tx) != {'to', 'data'}:
                raise AssertionError('RPC transaction contains non-read fields')
            return self.responses[(tx['to'], tx['data'])]
        raise AssertionError('Unapproved RPC method ' + method)


class FrontendProjectionTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration()
        self.rpc = MockRPC()
        self.projection = Projection(self.config, self.rpc, clock=lambda: 1000)

    def read(self):
        return self.projection.nft(str(self.rpc.nft_id))

    def test_exact_asset_units_native_royalties_and_real_value(self):
        result = self.read()
        self.assertEqual(result['owner'], addr(30))
        self.assertEqual(result['mint_ordinal'], 444)
        self.assertEqual(result['token_id'], str(self.rpc.nft_id))
        self.assertEqual(result['traits'], {'rarity': 'Rare', 'palette': 24, 'pattern': 2})
        self.assertEqual(result['position']['current_lp_value']['raw'], str(1432 * 10**18))
        self.assertEqual(result['position']['evolution'], 'enhanced')
        self.assertEqual([x['raw'] for x in result['claimable']['lp']], [str(5 * 10**18 + 17), '1234567'])
        self.assertEqual([x['decimals'] for x in result['claimable']['lp']], [18, 6])
        self.assertEqual(result['claimable']['royalties'][0]['asset'], ZERO)
        self.assertEqual(result['claimable']['royalties'][0]['raw'], '33333333333333333333')
        self.assertEqual(result['claimable']['royalties'][1]['raw'], '25000001')
        self.assertIn('pending admitted receipts', result['claimable']['royalty_scope'])
        self.assertFalse(result['position']['principal_redeemable'])

    def test_every_contract_read_hash_pinned_no_write_rpc(self):
        result = self.read()
        self.assertEqual(result['provenance']['block_number'], 99)
        self.assertEqual(result['provenance']['confirmations'], 12)
        self.assertEqual(result['provenance']['finality'], 'confirmation_depth_only')
        self.assertFalse(result['provenance']['protocol_finalized'])
        self.assertEqual(result['provenance']['block_hash'], self.rpc.hash)
        self.assertTrue(all(params[-1] == {'blockHash': self.rpc.hash, 'requireCanonical': True}
                            for method, params in self.rpc.calls if method in ('eth_call', 'eth_getCode')))
        self.assertFalse(any('send' in method.lower() or 'sign' in method.lower() for method, _ in self.rpc.calls))

    def test_no_invented_history_usd_or_wallet_inventory(self):
        result = self.read()
        self.assertEqual(set(result['unavailable_metrics']), {'wallet_inventory', 'previously_claimed', 'fees_all_time',
                         'fees_last_24h', 'reward_usd', 'individual_collective_breakdown'})
        self.assertNotIn('previously_claimed', result['claimable'])
        self.assertNotIn('total_usd', result['claimable'])
        self.assertIn('USD conversion', result['unavailable_metrics']['reward_usd'])

    def test_ownership_changes_are_not_cached(self):
        self.assertEqual(self.read()['owner'], addr(30))
        self.rpc.head += 1
        self.rpc.hash = '0x' + 'd' * 64
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(31),))
        second = self.read()
        self.assertEqual(second['owner'], addr(31))
        self.assertEqual(second['provenance']['block_number'], 100)
        self.assertEqual(second['provenance']['block_hash'], self.rpc.hash)

    def test_reorg_during_reads_discards_all_results(self):
        self.rpc.reorg_after_calls = True
        with self.assertRaisesRegex(ProjectionError, 'changed'):
            self.read()

    def test_changed_deployment_anchor_rejected_before_contract_reads(self):
        self.rpc.anchor = '0x' + 'e' * 64
        with self.assertRaisesRegex(ProjectionError, 'anchor'):
            self.read()
        self.assertFalse(any(method == 'eth_call' for method, _ in self.rpc.calls))

    def test_provider_without_eip1898_never_falls_back_to_latest(self):
        self.rpc.fail_hash_pin = True
        with self.assertRaises(RpcError):
            self.read()
        self.assertFalse(any(params and params[-1] == 'latest' for _, params in self.rpc.calls))

    def test_wrong_chain_rejected_before_calls(self):
        self.rpc.chain = 1
        with self.assertRaisesRegex(ProjectionError, 'chain'):
            self.read()
        self.assertEqual(len(self.rpc.calls), 1)

    def test_unsealed_or_unrelated_modules_rejected(self):
        modifications = ((addr(1), 'isSealed()', (), (0,)),
                         (addr(2), 'access()', (), (addr(40),)),
                         (addr(1), 'module(bytes32)', ('0x' + keccak256(b'ZZZVault').hex(),), (addr(41),)),
                         (addr(6), 'royalties()', (), (addr(42),)),
                         (addr(5), 'nft()', (), (addr(43),)),
                         (addr(3), 'canonicalChainId()', (), (4663,)))
        for target, method, args, values in modifications:
            with self.subTest(method=method, target=target):
                self.rpc = MockRPC()
                self.projection = Projection(self.config, self.rpc, clock=lambda: 1000)
                self.rpc.put(target, method, args, values)
                with self.assertRaises(ProjectionError):
                    self.read()

    def test_runtime_mismatch_rejected_for_module_and_asset(self):
        for target in (addr(2), addr(21)):
            with self.subTest(target=target):
                self.rpc = MockRPC()
                self.projection = Projection(self.config, self.rpc, clock=lambda: 1000)
                self.rpc.codes[target] = '0x6000'
                with self.assertRaisesRegex(ProjectionError, 'Runtime'):
                    self.read()

    def test_decimals_and_new_asset_admission_fail_closed(self):
        self.rpc.put(addr(21), 'decimals()', values=(18,))
        with self.assertRaisesRegex(ProjectionError, 'decimals'):
            self.read()
        self.rpc.put(addr(21), 'decimals()', values=(6,))
        self.rpc.put(addr(5), 'assets(uint256)', (1,), (addr(22),))
        with self.assertRaisesRegex(ProjectionError, 'allowlist'):
            self.read()

    def test_native_cannot_be_an_lp_asset(self):
        self.rpc.put(addr(4), 'assets(uint256)', (0,), (ZERO,))
        with self.assertRaisesRegex(ProjectionError, 'zero'):
            self.read()

    def test_asset_count_and_duplicates_bounded(self):
        self.rpc.put(addr(4), 'assetCount()', values=(33,))
        with self.assertRaisesRegex(ProjectionError, 'bound'):
            self.read()
        self.rpc.put(addr(4), 'assetCount()', values=(2,))
        self.rpc.put(addr(4), 'assets(uint256)', (1,), (addr(20),))
        with self.assertRaisesRegex(ProjectionError, 'inventory'):
            self.read()

    def test_unavailable_current_value_does_not_hide_claims_or_revoke_activation(self):
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (self.rpc.nft_id,), (0, 0))
        result = self.read()
        self.assertIsNone(result['position']['current_lp_value']['raw'])
        self.assertFalse(result['position']['current_lp_value']['available'])
        self.assertTrue(result['position']['activated'])
        self.assertEqual(result['position']['evolution'], 'activated')
        self.assertEqual(result['claimable']['royalties'][0]['raw'], '33333333333333333333')

    def parked(self):
        i = self.rpc.nft_id
        self.rpc.put(addr(3), 'nftStatus(uint256)', (i,), (6,))
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (i,), (0, 0))
        group = [444, 0, 123, 456, 1432 * 10**18, 0, 990, 6, 31337,
                 addr(3), addr(40), addr(20), addr(21), 31337, addr(3)]
        self.rpc.put(addr(3), 'group(uint256)', (5,), group)
        self.rpc.put(addr(3), 'bucketTotalShares(uint256)', (5,), (10**36,))
        return group

    def test_parked_principal_keeps_claims_and_eligibility_with_honest_unavailable_value(self):
        self.parked()
        result = self.read()
        self.assertEqual(result['position']['status'], 'parked')
        self.assertTrue(result['position']['activated'])
        self.assertEqual(result['position']['royalty_weight'], 2)
        self.assertEqual(result['position']['shares_raw'], str(10**36))
        self.assertFalse(result['position']['principal_redeemable'])
        self.assertIsNone(result['position']['current_lp_value']['raw'])
        self.assertIn('parked', result['position']['current_lp_value']['reason'])
        self.assertEqual(result['claimable']['lp'][0]['raw'], str(5 * 10**18 + 17))
        self.assertEqual(result['claimable']['royalties'][0]['raw'], '33333333333333333333')

    def test_parked_custody_lp_status_and_provenance_mismatch_fail_closed(self):
        for field, wrong in ((0, 0), (1, 99), (7, 1), (8, 4663), (9, addr(99)),
                             (13, 4663), (14, addr(99)), (14, 1 << 160)):
            with self.subTest(field=field):
                group = self.parked()
                group[field] = wrong
                self.rpc.put(addr(3), 'group(uint256)', (5,), group)
                with self.assertRaises(ProjectionError):
                    self.read()
        self.parked()
        self.rpc.put(addr(3), 'bucketTotalShares(uint256)', (5,), (10**36 - 1,))
        with self.assertRaises(ProjectionError):
            self.read()

    def test_parked_cannot_report_an_active_lp_mark(self):
        self.parked()
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (self.rpc.nft_id,), (1, 1432 * 10**18))
        with self.assertRaisesRegex(ProjectionError, 'Parked'):
            self.read()

    def test_current_value_can_downgrade_evolution_without_losing_royalty_weight(self):
        for usd, stage in ((10000, 'singularity'), (9999, 'enhanced'), (1000, 'enhanced'), (999, 'activated'), (1, 'activated')):
            with self.subTest(usd=usd):
                self.rpc.put(addr(2), 'currentLPValue(uint256)', (self.rpc.nft_id,), (1, usd * 10**18))
                result = self.read()
                self.assertEqual(result['position']['evolution'], stage)
                self.assertEqual(result['position']['royalty_weight'], 2)

    def test_dormant_unrevealed_traits_are_not_invented(self):
        i = self.rpc.nft_id
        self.rpc.put(addr(2), 'traitsReady(uint256)', (i,), (0,))
        self.rpc.put(addr(3), 'nftStatus(uint256)', (i,), (5,))
        self.rpc.put(addr(3), 'nftBucket(uint256)', (i,), (0,))
        self.rpc.put(addr(3), 'sharesOf(uint256)', (i,), (0,))
        self.rpc.put(addr(5), 'weightOf(uint256)', (i,), (0,))
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (i,), (1, 0))
        for target, assets in ((4, [addr(20), addr(21)]), (5, [ZERO, addr(21)])):
            for asset in assets:
                self.rpc.put(addr(target), 'claimable(uint256,address)', (i, asset), (0,))
        result = self.read()
        self.assertIsNone(result['traits'])
        self.assertEqual(result['position']['evolution'], 'dormant')
        self.assertFalse(result['position']['activated'])

    def test_malformed_boolean_address_and_value_rejected(self):
        mutations = ((addr(2), 'traitsReady(uint256)', (2,)),
                     (addr(2), 'ownerOf(uint256)', (1 << 160,)),
                     (addr(2), 'currentLPValue(uint256)', (0, 1)),
                     (addr(5), 'weightOf(uint256)', (3,)),
                     (addr(3), 'nftStatus(uint256)', (7,)))
        for target, method, values in mutations:
            with self.subTest(method=method):
                self.rpc = MockRPC()
                self.projection = Projection(self.config, self.rpc, clock=lambda: 1000)
                self.rpc.put(target, method, (self.rpc.nft_id,), values)
                with self.assertRaises(ProjectionError):
                    self.read()

    def test_malformed_abi_short_reply_rejected(self):
        key = (addr(4), calldata('claimable(uint256,address)', self.rpc.nft_id, addr(20)))
        self.rpc.responses[key] = '0x'
        with self.assertRaisesRegex(ProjectionError, 'length'):
            self.read()

    def test_missing_ordinal_and_inconsistent_hashed_identity(self):
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (self.rpc.nft_id,), (0,))
        with self.assertRaises(UnknownNFT):
            self.read()
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (self.rpc.nft_id,), (444,))
        self.rpc.put(addr(2), 'tokenAtOrdinal(uint256)', (444,), (445,))
        with self.assertRaisesRegex(ProjectionError, 'identity'):
            self.read()

    def test_stale_future_or_insufficiently_confirmed_chain_rejected(self):
        for timestamp in (879, 1031):
            self.rpc.header_timestamp = timestamp
            with self.assertRaisesRegex(ProjectionError, 'timestamp'):
                self.read()
        self.rpc.head = 20
        with self.assertRaisesRegex(ProjectionError, 'confirmation'):
            self.read()

    def test_snapshot_expiring_during_final_rpc_is_not_returned(self):
        now = [1000]
        self.projection.clock = lambda: now[0]
        original = self.rpc.call
        chain_reads = 0
        def delayed_final_chain(method, params):
            nonlocal chain_reads
            result = original(method, params)
            if method == 'eth_chainId':
                chain_reads += 1
                if chain_reads == 2:
                    now[0] = 1111  # 121 seconds since the selected block.
            return result
        self.rpc.call = delayed_final_chain
        with self.assertRaisesRegex(ProjectionError, 'timestamp'):
            self.read()
        self.assertEqual(chain_reads, 2)

    def test_final_freshness_boundary_and_clock_rollback(self):
        for final_time, succeeds in ((1110, True), (959, False)):
            with self.subTest(final_time=final_time):
                times = iter((1000, final_time))
                self.projection.clock = lambda: next(times)
                if succeeds:
                    self.assertEqual(self.read()['provenance']['block_timestamp'], 990)
                else:
                    with self.assertRaisesRegex(ProjectionError, 'timestamp'):
                        self.read()

    def test_retained_block_with_reduced_confirmation_depth_is_rejected(self):
        original = self.rpc.call
        reads = 0
        def rollback_head(method, params):
            nonlocal reads
            result = original(method, params)
            if method == 'eth_blockNumber':
                reads += 1
                if reads == 2:
                    return hex(109)  # Block 99 still exists, but has only 11 confirmations.
            return result
        self.rpc.call = rollback_head
        with self.assertRaisesRegex(ProjectionError, 'confirmation depth'):
            self.read()

    def test_inconsistent_timestamp_for_same_final_header_hash_is_rejected(self):
        original = self.rpc.call
        def inconsistent_header(method, params):
            result = original(method, params)
            if method == 'eth_getBlockByNumber' and params[0] == hex(99) and self.rpc.header_reads > 2:
                result['timestamp'] = hex(991)
            return result
        self.rpc.call = inconsistent_header
        with self.assertRaisesRegex(ProjectionError, 'changed'):
            self.read()

    def test_configuration_is_strict_and_cannot_override_deployment(self):
        bad = []
        extra = copy.deepcopy(self.config); extra['send_transactions'] = True; bad.append(extra)
        zero = copy.deepcopy(self.config); zero['contracts']['nft']['address'] = ZERO; bad.append(zero)
        duplicate = copy.deepcopy(self.config); duplicate['contracts']['rewards'] = duplicate['contracts']['nft']; bad.append(duplicate)
        unknown = copy.deepcopy(self.config); unknown['contracts']['random_contract'] = unknown['contracts']['nft']; bad.append(unknown)
        boolean = copy.deepcopy(self.config); boolean['chain_id'] = True; bad.append(boolean)
        floatdec = copy.deepcopy(self.config); floatdec['assets'][1]['decimals'] = 18.0; bad.append(floatdec)
        taxed = copy.deepcopy(self.config); taxed['assets'][0]['decimals'] = 6; bad.append(taxed)
        insecure = copy.deepcopy(self.config); insecure['rpc_urls'] = ['http://example.com']; bad.append(insecure)
        secret = copy.deepcopy(self.config); secret['private_key'] = 'FORBIDDEN'; bad.append(secret)
        for config in bad:
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    Projection(config, self.rpc)

    def test_invalid_token_ids_are_rejected_without_rpc(self):
        for item in (True, -1, 1.0, '0x123', '01', '+1', str(1 << 256), '9' * 10000, '/../../', None):
            with self.subTest(item=str(item)[:30]):
                with self.assertRaises(ValueError):
                    self.projection.nft(item)
        self.assertEqual(self.rpc.calls, [])
        self.assertEqual(token_id('0'), 0)

    def test_configuration_identity_excludes_private_rpc_endpoint(self):
        other = copy.deepcopy(self.config)
        other['rpc_urls'] = ['https://provider.invalid/private-key']
        self.assertEqual(self.projection.identity, Projection(other, self.rpc).identity)
        self.assertNotIn('private-key', json.dumps(self.read()))


class FrontendHTTPTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.projection = Projection(configuration(), self.rpc, clock=lambda: 1000)
        self.server = ReadServer(('127.0.0.1', 0), handler(self.projection))
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, headers=headers or {})
            result = connection.getresponse()
            return result.status, dict(result.getheaders()), json.loads(result.read())
        finally:
            connection.close()

    def test_http_read_is_exact_json_and_not_cacheable(self):
        status, headers, body = self.request('GET', f'/v1/nfts/{self.rpc.nft_id}')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(body['claimable']['royalties'][0]['raw'], '33333333333333333333')

    def test_host_queries_post_and_arbitrary_proxy_are_rejected_without_rpc(self):
        for method, path, headers, expected in (
                ('GET', f'/v1/nfts/{self.rpc.nft_id}', {'Host': 'evil.invalid'}, 400),
                ('GET', f'/v1/nfts/{self.rpc.nft_id}?rpc=https://evil.invalid', {}, 404),
                ('GET', '/v1/nfts/01', {}, 404),
                ('GET', '/v1/wallets/' + addr(30), {}, 404),
                ('POST', f'/v1/nfts/{self.rpc.nft_id}', {}, 405),
                ('GET', 'https://evil.invalid/v1/nfts/1', {}, 400)):
            with self.subTest(method=method, path=path):
                status, _, _ = self.request(method, path, headers)
                self.assertEqual(status, expected)
        self.assertEqual(self.rpc.calls, [])

    def test_unavailable_response_does_not_leak_provider_error(self):
        def fail(_):
            raise RpcError('SECRET provider endpoint and credential')
        self.projection.nft = fail
        status, headers, body = self.request('GET', '/v1/nfts/1')
        self.assertEqual(status, 503)
        self.assertEqual(body, {'error': 'confirmed_projection_unavailable'})
        self.assertNotIn('SECRET', json.dumps(body))

    def test_unknown_nft_is_not_a_zero_balance_position(self):
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', (self.rpc.nft_id,), (0,))
        status, _, body = self.request('GET', f'/v1/nfts/{self.rpc.nft_id}')
        self.assertEqual(status, 404)
        self.assertEqual(body, {'error': 'nft_not_minted'})


if __name__ == '__main__':
    unittest.main()
