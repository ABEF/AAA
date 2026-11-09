"""Offline proof/policy fixtures; no deployed runtime or OpenSea acceptance."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import opensea_drop as O
from zzz_ops.abi import keccak256


def addr(n):
    return '0x' + f'{n:040x}'


class OpenSeaDropTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        # Deliberately synthetic source fixtures; only binding behavior is tested.
        for name in O.SOURCE_PATHS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'[profile.default]\nremappings=[]\n' if name == 'foundry.toml'
                               else ('offline fixture: ' + name + '\n').encode())

    def request(self):
        return dict(schema=1, chain_id='4663', nft_contract=addr(1), seadrop=addr(2),
            seadrop_runtime_keccak256='0x' + '3' * 64,
            creator_payout_address=addr(4), fee_bps='1000', fee_recipient=addr(5),
            mint_price_wei='50000000000000000', public_wallet_limit='2', max_batch='4',
            allowed_payers=[],
            team=[dict(address=addr(10), quantity='20')],
            allowlist=[addr(24), addr(22), addr(23)],
            team_window=dict(start='100', end='199'),
            allowlist_window=dict(start='200', end='299'),
            public_window=dict(start='300', end='399'),
            release_unused_team_to_public=False, review_notes_sha256='6' * 64,
            source_sha256=O.source_identity(self.root))

    def prepare(self, request=None):
        return O.prepare(self.request() if request is None else request, self.root)

    def test_defaults_preserve_full_supply_and_one_hour_opening(self):
        result = self.prepare()
        self.assertEqual(('20', '500', '480'), tuple(result['allocations'][key]
                         for key in ('team', 'allowlist', 'public_base')))
        self.assertEqual('3600', result['royalty_open_delay_seconds'])
        self.assertTrue(result['allocations']['unused_allowlist_to_public'])
        self.assertFalse(result['allocations']['release_unused_team_to_public'])
        self.assertFalse(result['boundaries']['ready_for_submission'])
        self.assertFalse(result['boundaries']['independent_phase_caps_verified'])
        self.assertFalse(result['boundaries']['opensea_primary_drop_accepted'])

    def test_exact_leaf_encoding_is_single_hash_of_nine_abi_words(self):
        record = self.prepare()['proofs'][1]
        params = record['mint_params']
        numbers = [int(params[field]) for field in O.PARAM_FIELDS[:-1]] + [1]
        encoded = int(record['minter'], 16).to_bytes(32, 'big')
        encoded += b''.join(number.to_bytes(32, 'big') for number in numbers)
        self.assertEqual(288, len(encoded))
        self.assertEqual('0x' + keccak256(encoded).hex(), record['leaf'])
        self.assertNotEqual('0x' + keccak256(keccak256(encoded)).hex(), record['leaf'])

    def test_all_combined_team_and_allowlist_proofs_verify(self):
        result = self.prepare()
        self.assertEqual(4, len(result['proofs']))
        for record in result['proofs']:
            self.assertTrue(O.verify_proof(O.mint_leaf(record['minter'], record['mint_params']),
                                          record['proof'], result['allowlist_root']))
        team, allow = result['proofs'][0], result['proofs'][1]
        self.assertEqual(('0', '20', '1', '20', '0'), tuple(team['mint_params'][field]
            for field in ('mintPrice', 'maxTotalMintableByWallet', 'dropStageIndex',
                          'maxTokenSupplyForStage', 'feeBps')))
        self.assertEqual(('50000000000000000', '1', '2', '520', '1000'),
            tuple(allow['mint_params'][field] for field in ('mintPrice',
            'maxTotalMintableByWallet', 'dropStageIndex', 'maxTokenSupplyForStage', 'feeBps')))

    def test_proofs_cover_every_small_tree_shape_including_promoted_odd_nodes(self):
        for count in range(1, 17):
            leaves = [keccak256(n.to_bytes(2, 'big')) for n in range(count)]
            root, proofs = O.merkle_tree(leaves)
            with self.subTest(count=count):
                self.assertEqual(count, len(proofs))
                for leaf in leaves:
                    self.assertTrue(O.verify_proof(leaf, proofs[leaf], root))

    def test_full_thousand_leaf_capacity_is_bounded_and_every_proof_verifies(self):
        leaves = [keccak256(n.to_bytes(2, 'big')) for n in range(1000)]
        root, proofs = O.merkle_tree(leaves)
        self.assertLessEqual(max(map(len, proofs.values())), 10)
        for leaf in leaves:
            self.assertTrue(O.verify_proof(leaf, proofs[leaf], root))
        with self.assertRaises(ValueError):
            O.merkle_tree(leaves + [keccak256(b'overflow')])

    def test_empty_and_single_leaf_cases_are_explicit(self):
        self.assertEqual((O.ZERO_HASH, {}), O.merkle_tree([]))
        request = self.request()
        request.update(team_allocation='0', allowlist_allocation='0', team=[], allowlist=[])
        empty = self.prepare(request)
        self.assertEqual((O.ZERO_HASH, [], '1000'),
            (empty['allowlist_root'], empty['proofs'], empty['allocations']['public_base']))
        request.update(team_allocation='1', team=[dict(address=addr(10), quantity='1')])
        single = self.prepare(request)
        self.assertEqual(single['proofs'][0]['leaf'], single['allowlist_root'])
        self.assertEqual([], single['proofs'][0]['proof'])

    def test_positive_reserved_phases_cannot_publish_a_zero_eligibility_root(self):
        for team_quota, allow_quota in (('20', '0'), ('0', '500'), ('20', '500')):
            request = self.request()
            request.update(team_allocation=team_quota, allowlist_allocation=allow_quota,
                           team=[], allowlist=[])
            with self.subTest(team=team_quota, allowlist=allow_quota), self.assertRaises(ValueError):
                self.prepare(request)

    def test_each_positive_phase_requires_its_own_reviewed_proof_leaf(self):
        for absent_phase in ('team', 'allowlist'):
            request = self.request()
            request[absent_phase] = []
            with self.subTest(phase=absent_phase), self.assertRaises(ValueError):
                self.prepare(request)
        for empty_phase, quota_key in (('team', 'team_allocation'), ('allowlist', 'allowlist_allocation')):
            request = self.request()
            request[empty_phase] = []
            request[quota_key] = '0'
            with self.subTest(disabled=empty_phase):
                self.assertTrue(self.prepare(request))

    def test_tampering_wallet_price_quota_or_sibling_invalidates_proof(self):
        result = self.prepare()
        original = result['proofs'][1]
        for field in O.PARAM_FIELDS:
            params = dict(original['mint_params'])
            params[field] = False if field == 'restrictFeeRecipients' else str(int(params[field]) + 1)
            with self.subTest(field=field):
                self.assertFalse(O.verify_proof(O.mint_leaf(original['minter'], params),
                    original['proof'], result['allowlist_root']))
        self.assertFalse(O.verify_proof(O.mint_leaf(addr(99), original['mint_params']),
            original['proof'], result['allowlist_root']))
        changed = list(original['proof'])
        changed[0] = '0x' + '7' * 64
        self.assertFalse(O.verify_proof(bytes.fromhex(original['leaf'][2:]), changed, result['allowlist_root']))

    def test_address_lists_are_normalized_sorted_and_input_order_independent(self):
        request = self.request()
        request['team'] = [dict(address=addr(12), quantity='4'), dict(address=addr(10), quantity='16')]
        first = self.prepare(request)
        request['team'].reverse()
        request['allowlist'].reverse()
        second = self.prepare(request)
        self.assertEqual(first, second)
        self.assertEqual([addr(22), addr(23), addr(24)], first['request']['allowlist'])

    def test_address_array_hash_matches_explicit_abi_offsets_and_lengths(self):
        addresses = [addr(10), addr(12)]
        raw = b''.join(n.to_bytes(32, 'big') for n in (32, 2, 10, 12))
        self.assertEqual('0x' + keccak256(raw).hex(), O.address_list_hash(addresses))
        team = [dict(address=addr(10), quantity='16'), dict(address=addr(12), quantity='4')]
        raw = b''.join(n.to_bytes(32, 'big') for n in (64, 160, 2, 10, 12, 2, 16, 4))
        self.assertEqual('0x' + keccak256(raw).hex(), O.team_list_hash(team))

    def test_explicit_payers_are_sorted_hashed_and_bound_into_helper_configuration(self):
        request = self.request()
        request['allowed_payers'] = [addr(52), addr(50)]
        result = self.prepare(request)
        self.assertEqual([addr(50), addr(52)], result['request']['allowed_payers'])
        expected = O.address_list_hash([addr(50), addr(52)])
        self.assertEqual(expected, result['allowed_payers_hash'])
        self.assertEqual(expected, result['mint_config']['allowedPayersHash'])
        self.assertEqual(expected, result['configure_arguments'][0][-1])
        for payers in ([addr(52)] * 2, [addr(0)], [addr(n) for n in range(1, 18)], None):
            request['allowed_payers'] = payers
            with self.subTest(payers=payers), self.assertRaises(ValueError):
                self.prepare(request)

    def test_allocations_and_rollover_are_explicit_configurable_future_policy(self):
        request = self.request()
        request.update(team_allocation='30', allowlist_allocation='600', release_unused_team_to_public=True)
        result = self.prepare(request)
        self.assertEqual('370', result['allocations']['public_base'])
        self.assertEqual('10', result['allocations']['unlisted_team_capacity'])
        self.assertEqual('630', result['proofs'][1]['mint_params']['maxTokenSupplyForStage'])
        self.assertTrue(result['mint_config']['releaseUnusedTeamToPublic'])

    def test_exact_configuration_tuple_and_domain_review_hash(self):
        result = self.prepare()
        self.assertEqual('4', result['mint_config']['maxBatch'])
        self.assertEqual('0x' + hashlib.sha256(O.DOMAIN + O.canonical({key: value
            for key, value in result.items() if key not in ('review_hash', 'configure_arguments')})).hexdigest(),
            result['review_hash'])
        self.assertEqual([[result['mint_config'][field] for field in O.CONFIG_FIELDS],
                          result['request']['mint_price_wei'], result['review_hash']],
                         result['configure_arguments'])
        self.assertTrue(O.check(result, self.root)['artifact_matches'])

    def test_each_material_config_change_changes_review_hash(self):
        original = self.prepare()['review_hash']
        for key, value in (('chain_id', '4664'), ('nft_contract', addr(30)),
                ('mint_price_wei', '60000000000000000'), ('fee_bps', '999'),
                ('fee_recipient', addr(31)), ('creator_payout_address', addr(32)),
                ('public_wallet_limit', '3'), ('max_batch', '5'),
                ('release_unused_team_to_public', True), ('review_notes_sha256', '8' * 64)):
            request = self.request()
            request[key] = value
            with self.subTest(key=key):
                self.assertNotEqual(original, self.prepare(request)['review_hash'])

    def test_duplicate_case_alias_and_cross_phase_addresses_reject(self):
        for change in ('team_duplicate', 'allowlist_duplicate', 'cross_phase', 'case_alias'):
            request = self.request()
            if change == 'team_duplicate':
                request['team'] = [dict(address=addr(10), quantity='1')] * 2
            elif change == 'allowlist_duplicate':
                request['allowlist'].append(addr(22))
            elif change == 'cross_phase':
                request['allowlist'].append(addr(10))
            else:
                request['allowlist'] = ['0x' + 'a' * 40, '0x' + 'A' * 40]
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.prepare(request)

    def test_missing_explicit_fee_wallet_limit_time_rollover_or_source_rejects(self):
        for field in ('fee_bps', 'fee_recipient', 'public_wallet_limit', 'max_batch',
                'team_window', 'allowlist_window', 'public_window',
                'release_unused_team_to_public', 'source_sha256'):
            request = self.request()
            del request[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.prepare(request)

    def test_float_boolean_noncanonical_and_out_of_bounds_numbers_reject(self):
        for field in ('chain_id', 'mint_price_wei', 'fee_bps', 'public_wallet_limit',
                      'max_batch', 'team_allocation', 'allowlist_allocation'):
            for value in (True, 1, 1.0, '-1', '01', '1.0', '1e3', '', '9' * 79):
                request = self.request()
                request[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.prepare(request)
        for field, value in (('chain_id', '0'), ('mint_price_wei', '0'), ('fee_bps', '10001'),
                ('public_wallet_limit', '0'), ('public_wallet_limit', '1001'),
                ('max_batch', '0'), ('max_batch', '11'), ('max_batch', '256'), ('allowlist_allocation', '981')):
            request = self.request()
            request[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.prepare(request)

    def test_phase_boundaries_are_inclusive_disjoint_and_uint48_bounded(self):
        for field, value in (('start', '199'), ('start', '198'), ('end', '300'),
                             ('start', '0'), ('end', str(1 << 48)), ('end', '199')):
            request = self.request()
            request['allowlist_window'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.prepare(request)
        request = self.request()
        request['team_window']['start'] = '199'
        self.assertTrue(self.prepare(request))  # A one-second inclusive stage is representable.

    def test_entitlements_cannot_exceed_reserved_supply_or_address_bound(self):
        for change in ('team', 'allowlist', 'list_length', 'unknown_field', 'bad_team_quantity'):
            request = self.request()
            if change == 'team':
                request['team'][0]['quantity'] = '21'
            elif change == 'allowlist':
                request['allowlist_allocation'] = '2'
            elif change == 'list_length':
                request['allowlist'] = [addr(22)] * 1001
            elif change == 'unknown_field':
                request['private_key'] = 'DO_NOT_ECHO'
            else:
                request['team'][0]['quantity'] = '0'
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.prepare(request)

    def test_bad_identity_zero_address_and_missing_source_reject(self):
        for field, value in (('nft_contract', addr(0)), ('seadrop', addr(1)),
                ('fee_recipient', 'not-an-address'), ('seadrop_runtime_keccak256', O.ZERO_HASH),
                ('review_notes_sha256', '0' * 64), ('release_unused_team_to_public', 1)):
            request = self.request()
            request[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.prepare(request)
        request = self.request()
        del request['source_sha256'][O.SOURCE_PATHS[0]]
        with self.assertRaises(ValueError):
            self.prepare(request)

    def test_source_drift_additional_bindings_and_path_escape(self):
        artifact = self.prepare()
        changed = self.root / O.SOURCE_PATHS[0]
        changed.write_bytes(changed.read_bytes() + b'changed')
        with self.assertRaises(ValueError):
            O.check(artifact, self.root)
        extra = self.root / 'src/Additional.sol'
        extra.write_text('reviewed additional source', encoding='utf-8')
        request = self.request()
        request['source_sha256'] = O.source_identity(self.root, ['src/Additional.sol'])
        self.assertTrue(self.prepare(request))
        for name in ('../outside.sol', '/src/ZZZNFT.sol', 'src/../file.sol', '.git/config', 'src//file.sol'):
            with self.subTest(path=name), self.assertRaises(ValueError):
                O.source_identity(self.root, [name])

    def test_source_bindings_include_external_modules_and_transitive_remapped_imports(self):
        external = self.root / 'src/SeparateModule.sol'
        external.write_text('import {Thing} from "fixture/Thing.sol";', encoding='utf-8')
        dependency = self.root / 'node_modules/fixture/Thing.sol'
        dependency.parent.mkdir(parents=True)
        dependency.write_text('import "./Other.sol";', encoding='utf-8')
        sibling = dependency.with_name('Other.sol')
        sibling.write_text('contract Other {}', encoding='utf-8')
        (self.root / 'foundry.toml').write_text(
            '[profile.default]\nremappings=["fixture/=node_modules/fixture/"]\n', encoding='utf-8')
        identity = O.source_identity(self.root)
        self.assertIn('src/SeparateModule.sol', identity)
        self.assertIn('node_modules/fixture/Thing.sol', identity)
        self.assertIn('node_modules/fixture/Other.sol', identity)
        artifact = self.prepare()
        sibling.write_text('contract Changed {}', encoding='utf-8')
        with self.assertRaises(ValueError):
            O.check(artifact, self.root)
        external.write_text('import "unknown/Thing.sol";', encoding='utf-8')
        with self.assertRaises(ValueError):
            O.source_identity(self.root)

    def test_full_artifact_check_rejects_every_derived_tamper(self):
        for change in ('review', 'proof', 'flags', 'config', 'list_hash', 'one_hour', 'argument', 'expected_price', 'extra'):
            artifact = self.prepare()
            if change == 'review':
                artifact['review_hash'] = '0x' + '9' * 64
            elif change == 'proof':
                artifact['proofs'][0]['proof'][0] = O.ZERO_HASH
            elif change == 'flags':
                artifact['boundaries']['ready_for_submission'] = True
            elif change == 'config':
                artifact['mint_config']['teamAllocation'] = '21'
            elif change == 'list_hash':
                artifact['allowlist_addresses_hash'] = O.ZERO_HASH
            elif change == 'one_hour':
                artifact['royalty_open_delay_seconds'] = '86400'
            elif change == 'argument':
                artifact['configure_arguments'][0][0] = '99'
            elif change == 'expected_price':
                artifact['configure_arguments'][1] = '60000000000000000'
            else:
                artifact['approved'] = True
            with self.subTest(change=change), self.assertRaises(ValueError):
                O.check(artifact, self.root)

    def test_decoder_rejects_duplicate_fields_floats_constants_and_nested_bombs(self):
        for raw in (b'{"schema":1,"schema":1}', b'{"x":1.0}', b'{"x":NaN}',
                    b'{"x":Infinity}', b'[' * 13 + b'0' + b']' * 13):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                O.decode(raw)
        with self.assertRaises(ValueError):
            O.decode(b' ' * (O.MAX_INPUT + 1))

    def test_cli_prepares_checks_and_never_contacts_network_or_processes(self):
        path, output, checked = (self.root / name for name in ('request.json', 'proofs.json', 'check.json'))
        path.write_bytes(O.render(self.request()))
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), \
                patch.object(subprocess, 'run', side_effect=AssertionError('process forbidden')):
            self.assertEqual(0, O.main(['prepare', str(path), '--output', str(output)], root=self.root))
            self.assertEqual(0, O.main(['check', str(output), '--output', str(checked)], root=self.root))
        self.assertTrue(json.loads(checked.read_text())['artifact_matches'])
        self.assertFalse(json.loads(output.read_text())['boundaries']['ready_for_submission'])

    def test_atomic_publication_never_replaces_existing_and_failure_leaves_no_partial(self):
        output = self.root / 'proofs.json'
        output.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            O.publish(output, b'candidate')
        self.assertEqual(b'original', output.read_bytes())
        absent = self.root / 'absent.json'
        with patch.object(O.os, 'link', side_effect=OSError('injected failure')), self.assertRaises(OSError):
            O.publish(absent, b'candidate')
        self.assertFalse(absent.exists())
        self.assertEqual([], list(self.root.glob('.popl-drop-*')))

    def test_cli_rejection_is_sanitized_and_creates_no_output(self):
        path, output = self.root / 'bad.json', self.root / 'absent.json'
        path.write_text('{"private_key":"DO_NOT_ECHO_THIS"}', encoding='utf-8')
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(1, O.main(['prepare', str(path), '--output', str(output)], root=self.root))
        self.assertEqual('', stdout.getvalue())
        self.assertNotIn('DO_NOT_ECHO_THIS', stderr.getvalue())
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
