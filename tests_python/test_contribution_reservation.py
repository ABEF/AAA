"""Read-only current-profile reservation/capacity and imported-alias controls."""
import copy
import unittest
from unittest.mock import patch

from zzz_ops import production_v4 as P
from zzz_ops import production_observer_v4 as O
from tests_python import production_v4_fixtures as F


class ContributionReservationTests(unittest.TestCase):
    def setUp(self):
        for context in (patch.object(F.old, 'HASH', F.RUNTIME),
                        patch.object(P.V, 'NATIVE_DEPENDENCIES', {
                            role: (address, F.RUNTIME) for role, (address, _) in P.V.NATIVE_DEPENDENCIES.items()})):
            context.start()
            self.addCleanup(context.stop)
        self.cfg = F.fixture()
        self.chain = self.cfg['chains'][0]

    def report(self, cfg=None):
        return P.validate(cfg or self.cfg, expected_commit=F.COMMIT, now=F.NOW)

    def gate(self):
        gate = P.V.Gate(F.COMMIT)
        result = P._contribution_reservation(gate, self.chain, 'chains[0]')
        return result, {i['code'] for i in gate.issues}

    def empty_bucket(self, identifier):
        self.chain['holder_exit']['observed']['buckets'].append(dict(
            id=identifier, position=[0]*8, total_shares=0, settlement=[0,0,0,0,0,0,False],
            lp_owner=None, lp_liquidity=None, lp_ticks=None, lp_pool_key=None, lp_position_info=None))
        self.chain['rebalance_confirmation']['observed']['buckets'].append(dict(
            id=identifier, condition_side=0, condition_identity=P.ZERO_HASH, manual=False,
            stored_identity=P.ZERO_HASH, first_seen=0, last_seen=0, stored_side=0,
            ready=False, raw_needed=False, range_pending=False, physical_side=None, reference_side=None))

    def observe_mapping(self, bucket, alias=None, *, missing=None):
        rpc = F.RPC(self.cfg)
        original = rpc.call
        chain = self.chain
        canonical = int(P.V.identity([
            (chain['canonical_handoff']['origin_chain_id'], 'uint256'),
            (chain['canonical_handoff']['origin_vault'], 'address'),
            (chain['contribution_pool'], 'bytes32')]), 16)
        values = {'poolBucket(bytes32)': bucket, 'aliasBucket(bytes32)': bucket if alias is None else alias,
                  'bucketIdentity(bytes32)': canonical,
                  'registeredBucket(uint256)': int(any(b['id'] == (bucket or canonical)
                      for b in chain['holder_exit']['observed']['buckets']))}
        called = []
        def call(method, params=None):
            if method == 'eth_call':
                for signature, value in values.items():
                    if params[0]['data'][:10] == F.selector(signature):
                        called.append((signature, copy.deepcopy(params[-1])))
                        if signature == missing:
                            raise ValueError('inert fixture failure')
                        return F.encoded(value)
            return original(method, params)
        rpc.call = call
        return O.observe(self.cfg, rpc), called

    def test_wrong_initial_reservation_is_observed_and_blocks_current_gate(self):
        self.empty_bucket(7)
        observed, _ = self.observe_mapping(7)
        self.assertTrue(observed['chains'][0]['observation']['complete'])
        report = self.report(observed)
        self.assertFalse(report['inventory_consistent'])
        self.assertIn('reservation.initial_identity', {i['code'] for i in report['issues']})

    def test_observer_reads_reservation_identities_and_registration_at_one_hash(self):
        observed, calls = self.observe_mapping(0)
        self.assertEqual({s for s, _ in calls}, {
            'poolBucket(bytes32)', 'aliasBucket(bytes32)', 'bucketIdentity(bytes32)', 'registeredBucket(uint256)'})
        self.assertTrue(all(block == {'blockHash': F.RUNTIME, 'requireCanonical': True} for _, block in calls))
        self.assertEqual(observed['chains'][0]['contribution_reservation']['bucket_id'], 0)
        self.assertTrue(self.report(observed)['inventory_consistent'])

    def test_first_activation_uses_exact_canonical_slot_or_real_remaining_capacity(self):
        status, codes = self.gate()
        self.assertTrue(status['available_by_reservation']); self.assertEqual(codes, set())
        canonical = self.chain['contribution_reservation']['canonical_bucket_id']
        self.empty_bucket(canonical)
        F.reservation(self.cfg, canonical)
        status, codes = self.gate()
        self.assertEqual(status['reason'], 'initial_canonical'); self.assertEqual(codes, set())
        for identifier in (7, 8, 9):
            self.empty_bucket(identifier)
        # All four slots are occupied, but reusing the existing canonical slot
        # is valid whether this pool's alias has already been reserved or not.
        for bucket in (canonical, 0):
            F.reservation(self.cfg, bucket)
            status, codes = self.gate()
            self.assertTrue(status['available_by_reservation']); self.assertEqual(codes, set())
        self.chain['holder_exit']['observed']['buckets'][0]['id'] = 10
        F.reservation(self.cfg)
        status, codes = self.gate()
        self.assertFalse(status['available_by_reservation'])
        self.assertEqual(codes, {'reservation.capacity'})

    def test_initialized_local_move_and_authenticated_import_preserve_original_bucket(self):
        F.active(self.cfg)
        self.assertNotEqual(self.chain['contribution_reservation']['bucket_id'],
                            self.chain['contribution_reservation']['canonical_bucket_id'])
        status, codes = self.gate()
        self.assertEqual(status['reason'], 'active_current_pool'); self.assertEqual(codes, set())
        self.assertTrue(self.report()['inventory_consistent'])
        canonical = self.chain['canonical_handoff']
        canonical.update(phase=5, incoming_source=F.old.addr(9901), origin_vault=F.old.addr(9902))
        proof = copy.deepcopy(canonical['review_evidence'])
        proof.update(kind='atomic_same_chain_canonical_activation', source_controller=canonical['incoming_source'],
                     source_permanently_retired=True, all_backing_verified=True,
                     origin_chain_id=canonical['origin_chain_id'], origin_vault=canonical['origin_vault'])
        canonical['activation_evidence'] = proof
        F.refresh_bindings(self.cfg); F.reservation(self.cfg, 7)
        status, codes = self.gate()
        self.assertTrue(status['available_by_reservation']); self.assertEqual(codes, set())
        self.assertTrue(self.report()['inventory_consistent'], self.report()['issues'])
        canonical['activation_evidence']['source_permanently_retired'] = False
        self.assertIn('canonical.activation', {i['code'] for i in self.report()['issues']})

    def test_alias_registration_identity_and_current_pool_cannot_contradict_inventory(self):
        F.active(self.cfg)
        original = copy.deepcopy(self.cfg)
        cases = [('alias_bucket_id', 8, 'reservation.alias'),
                 ('canonical_bucket_id', 8, 'reservation.canonical_identity'),
                 ('target_registered', False, 'reservation.registration'),
                 ('bucket_count', 0, 'reservation.inventory')]
        for field, value, code in cases:
            with self.subTest(field=field):
                self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
                self.chain['contribution_reservation'][field] = value
                status, codes = self.gate()
                self.assertFalse(status['available_by_reservation']); self.assertIn(code, codes)
        self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
        self.chain['holder_exit']['observed']['buckets'][0]['position'][0] += 1
        status, codes = self.gate()
        self.assertFalse(status['available_by_reservation']); self.assertIn('reservation.current_pool', codes)

    def test_lifecycle_stops_do_not_label_valid_aliases_as_initial_identity_corruption(self):
        F.active(self.cfg)
        original = copy.deepcopy(self.cfg)
        for reason in ('paused', 'canonical_transition', 'terminal_exit', 'parked'):
            with self.subTest(reason=reason):
                self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
                holder = self.chain['holder_exit']['observed']
                if reason == 'paused': holder['paused'] = True
                elif reason == 'canonical_transition': self.chain['canonical_handoff']['preparation_active'] = True
                elif reason == 'terminal_exit': holder['lp_exit_started'] = True
                else: holder['buckets'][0]['position'][7] = 4
                status, codes = self.gate()
                self.assertFalse(status['available_by_reservation']); self.assertEqual(status['reason'], reason)
                self.assertEqual(codes, set())

    def test_missing_observation_or_failed_getter_never_defaults_to_unreserved(self):
        self.chain.pop('contribution_reservation')
        report = self.report()
        self.assertFalse(report['inventory_consistent'])
        self.assertFalse(report['contribution_reservation_status']['available_by_reservation'])
        F.reservation(self.cfg)
        observed, _ = self.observe_mapping(0, missing='poolBucket(bytes32)')
        self.assertFalse(observed['chains'][0]['observation']['complete'])
        self.assertIsNone(observed['chains'][0]['contribution_reservation'])
        self.assertFalse(self.report(observed)['inventory_consistent'])

    def test_selected_custody_faults_cannot_advertise_partial_reservation_availability(self):
        original = F.active(copy.deepcopy(self.cfg))
        for field in ('lp_owner', 'lp_liquidity', 'lp_token', 'total_shares'):
            with self.subTest(field=field):
                self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
                bucket = self.chain['holder_exit']['observed']['buckets'][0]
                if field == 'lp_token': bucket['position'][1] = 0
                else: bucket[field] = F.old.addr(999) if field == 'lp_owner' else 0
                report = self.report()
                self.assertFalse(report['inventory_consistent'])
                self.assertFalse(report['contribution_reservation_status']['available_by_reservation'])
                self.assertEqual(report['contribution_reservation_status']['reason'], 'custody_unavailable')
        # An unrelated bucket fault still blocks the complete release inventory,
        # but cannot be attributed to this healthy selected reservation.
        self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
        self.empty_bucket(8)
        self.chain['holder_exit']['observed']['buckets'][1]['position'][1] = 42
        F.reservation(self.cfg, 7)
        report = self.report()
        self.assertFalse(report['inventory_consistent'])
        self.assertTrue(report['contribution_reservation_status']['available_by_reservation'])
        self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
        self.chain['holder_exit']['observed']['buckets'] = []
        self.chain['contribution_reservation']['bucket_count'] = 0
        report = self.report()
        self.assertFalse(report['inventory_consistent'])
        self.assertEqual(report['contribution_reservation_status']['reason'], 'inventory_unavailable')

    def test_missing_or_nonboolean_lifecycle_context_cannot_infer_operating(self):
        original = F.active(copy.deepcopy(self.cfg))
        for section, field, value in (
                ('holder', 'paused', None), ('holder', 'paused', 1),
                ('holder', 'lp_exit_started', None), ('holder', 'lp_exit_started', 1),
                ('canonical', 'state', False), ('canonical', 'state', None),
                ('canonical', 'preparation_active', None), ('canonical', 'preparation_active', 0),
                ('canonical', 'settling', None), ('canonical', 'settling', 0)):
            with self.subTest(section=section, field=field, value=value):
                self.cfg = copy.deepcopy(original); self.chain = self.cfg['chains'][0]
                target = self.chain['holder_exit']['observed'] if section == 'holder' else self.chain['canonical_handoff']
                target[field] = value
                report = self.report()
                self.assertFalse(report['inventory_consistent'])
                self.assertIsNotNone(report['contribution_reservation_status'])
                self.assertFalse(report['contribution_reservation_status']['available_by_reservation'])
                self.assertEqual(report['contribution_reservation_status']['reason'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
