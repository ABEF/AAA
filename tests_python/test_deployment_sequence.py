"""New conditional EOA deployment sequencing; offline math/constructor evidence.

No old test bodies, RPC, signing, node or deployment are executed. The original
local receipts below are an independent CREATE-address/nonce oracle only: they
retain their historical source/build scope and do not qualify a fresh release.
"""
import copy
import hashlib
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
import zipfile

from zzz_ops import deployment_plan as D

ROOT = Path(__file__).resolve().parents[1]
SENDER = '0x6ac7ea33f8831ea9dcc53393aaa88b25a785dbf0'
LOCAL_SENDER = '0x'+'0'*36+'a0a0'
MAX_TRANSACTION_NONCE = (1 << 64)-2


def subject():
    # Deferred so baseline capability can be inspected without importing a new
    # module that did not exist at the baseline revision.
    from zzz_ops import deployment_sequence
    return deployment_sequence


def deployment_input():
    value = D.template()
    value['inputs'].update(governance='0x'+'a1'*20, keeper='0x'+'a2'*20,
        guardian='0x'+'a3'*20, mint_recipient='0x'+'a4'*20, sequencer=D.ZERO,
        **D.NATIVE, seadrop=D.SEADROP, seadrop_codehash=D.SEADROP_HASH,
        base_uri='ipfs://conditional-deployment/é', buyback_maximum_trade_usd=str(100*10**18))
    return value


def constructor_steps():
    return [row for row in D.construction_order() if row['kind'] != 'unverified_setup_checklist']


class DeploymentSequenceTests(unittest.TestCase):
    def derive(self, nonce='0', sender=SENDER):
        return subject().derive(sender, nonce)

    def test_known_ethereum_create_vectors_are_independent_of_initcode(self):
        expected = {
            0: '0xcd234a471b72ba2f1ccf0a70fcaba648a5eecd8d',
            1: '0x343c43a37d37dff08ae8c4a11544c718abb4fcf8',
            2: '0xf778b86fa74e846c4f0a1fbd1335fe81c00a0c91',
        }
        for nonce, address in expected.items():
            with self.subTest(nonce=nonce):
                self.assertEqual(address, subject().create_address(SENDER, nonce))

    def test_offline_cast_vectors_cover_rlp_length_and_uint64_boundaries(self):
        # Generated once with the existing hash-pinned Cast1.4.4 executable,
        # explicit nonce and a minimal environment. No RPC or live nonce query.
        expected = {
            3: '0xfffd933a0bc612844eaf0c6fe3e5b8e9b6c1d19c',
            127: '0x06d9a77f5e4b311bae8d559db9cdb4df94104aa0',
            128: '0x08e190dcb7b73f5fcdabb43e102215c83659a76d',
            255: '0x3ef7c1a519e4b4431e317d7839340e3139b03c65',
            256: '0x3837c1ae70354f670550c746580199ac6a73cb0a',
            65535: '0x65260eecff4edebabe134f76f1f39a91defde56c',
            65536: '0xf666a819b370d38f44f2573464da3fba8479b917',
            (1 << 32)-1: '0x4c9958390a81acc68a5f19aa8e6188bebbbeefd7',
            1 << 32: '0xf4bf328880432064068338f915c49f817dc4ce18',
            MAX_TRANSACTION_NONCE: '0x9ab3917bcc9efbcf7de35bced143ed95c3b3cbf5',
        }
        for nonce, address in expected.items():
            with self.subTest(nonce=nonce):
                self.assertEqual(address, subject().create_address(SENDER, nonce))

    def test_nonce_type_range_and_address_shape_cannot_be_coerced(self):
        for nonce in (True, False, -1, 1.0, '1', None, 1 << 64, (1 << 64)-1):
            with self.subTest(nonce=nonce), self.assertRaises(ValueError):
                subject().create_address(SENDER, nonce)
        for sender in (None, True, D.ZERO, '0x1234', '0x'+'g'*40, SENDER+'\n', SENDER[2:]):
            with self.subTest(sender=sender), self.assertRaises(ValueError):
                subject().create_address(sender, 0)

    def test_start_nonce_requires_canonical_decimal_string(self):
        for nonce in ('', '00', '01', '+1', '-1', ' 1', '1 ', '1\n', '0x1', '1.0', '1e3', '١', 1, True, 0.0, None):
            with self.subTest(nonce=nonce), self.assertRaises(ValueError):
                subject().validate_sender_nonce(SENDER, nonce)
        for nonce in ('0', '127', '128', '65536'):
            with self.subTest(nonce=nonce):
                self.assertEqual((SENDER, int(nonce)), subject().validate_sender_nonce(SENDER.upper().replace('0X','0x'), nonce))

    def test_exact_sequence_includes_every_interleaved_binding_nonce(self):
        result = self.derive('73')
        rows = result['transactions']; expected = constructor_steps()
        self.assertEqual(44, len(rows))
        self.assertEqual([row['id'] for row in expected], [row['id'] for row in rows])
        self.assertEqual([str(n) for n in range(73, 117)], [row['nonce'] for row in rows])
        self.assertEqual('73', result['starting_nonce']); self.assertEqual('117', result['next_nonce'])
        self.assertEqual(25, len(result['predicted_addresses']))
        self.assertEqual(set(role for role, _name, _args in D.TOP), set(result['predicted_addresses']))
        for row in rows:
            self.assertEqual(SENDER, row['from'])
            self.assertIs(row['authority_verified'], False)
            if row['id'].startswith('create:'):
                role = row['id'][7:]
                self.assertIsNone(row['to'])
                self.assertEqual(subject().create_address(SENDER, int(row['nonce'])), row['predicted_address'])
                self.assertEqual(result['predicted_addresses'][role], row['predicted_address'])
            else:
                target = ('access' if row['id'] not in ('bind:lp_converter','bind:seadrop_mint')
                          else 'rewards' if row['id']=='bind:lp_converter' else 'nft')
                self.assertEqual(result['predicted_addresses'][target], row['to'])

    def test_policy_binding_consumes_a_nonce_before_third_creation(self):
        result = self.derive()
        self.assertEqual(['create:access','create:protocol_policy','bind:protocol_policy','create:migration_budget'],
                         [row['id'] for row in result['transactions'][:4]])
        self.assertEqual(subject().create_address(SENDER, 3), result['predicted_addresses']['migration_budget'])
        self.assertNotEqual(subject().create_address(SENDER, 2), result['predicted_addresses']['migration_budget'])

    def test_each_binding_is_same_declared_bootstrap_and_no_setup_or_seal_is_enqueued(self):
        rows = self.derive()['transactions']
        self.assertEqual(19, sum(row['id'].startswith('bind:') for row in rows))
        self.assertTrue(all(row['from']==SENDER for row in rows))
        self.assertFalse(any(row['id'].startswith('configure:') or 'seal' in row['id'] for row in rows))
        self.assertTrue(all(row['authority_verified'] is False for row in rows))

    def test_changing_sender_or_start_nonce_changes_all_conditional_addresses(self):
        first = self.derive(); later = self.derive('1'); other = self.derive(sender='0x'+'b1'*20)
        for role in first['predicted_addresses']:
            self.assertNotEqual(first['predicted_addresses'][role], later['predicted_addresses'][role])
            self.assertNotEqual(first['predicted_addresses'][role], other['predicted_addresses'][role])
        self.assertEqual([row['id'] for row in first['transactions']], [row['id'] for row in later['transactions']])

    def test_eip2681_headroom_rejects_exhaustion_without_inventing_setup_count(self):
        result = self.derive(str(MAX_TRANSACTION_NONCE-44))
        self.assertEqual(str(MAX_TRANSACTION_NONCE), result['next_nonce'])
        self.assertEqual(1, int(result['remaining_legal_transactions']))
        self.assertEqual(MAX_TRANSACTION_NONCE-1, int(result['transactions'][-1]['nonce']))
        for nonce in (MAX_TRANSACTION_NONCE-43, MAX_TRANSACTION_NONCE, MAX_TRANSACTION_NONCE+1):
            with self.subTest(nonce=nonce), self.assertRaises(ValueError):
                self.derive(str(nonce))

    def test_historical_actual_receipts_match_all_twentyfive_predictions_and_offsets(self):
        summary = json.loads((ROOT/'reports/local-deployment-rehearsal-20261115/GAS_SUMMARY.json').read_bytes())
        result = self.derive(sender=LOCAL_SENDER)
        expected_rows = result['transactions']; creations = 0
        with zipfile.ZipFile(ROOT/'reports/local-deployment-rehearsal-20261115/evidence.zip') as archive:
            for metadata, row in zip(summary['receipts'], expected_rows):
                self.assertEqual(metadata['label'], row['id'])
                self.assertEqual(metadata['nonce'], int(row['nonce']))
                raw = archive.read('attempt1/'+metadata['receipt_file'])
                self.assertEqual(metadata['receipt_sha256'], hashlib.sha256(raw).hexdigest())
                original = json.loads(raw)
                # Actual included transaction and receipt, not the original
                # aliased preflight request dictionaries.
                actual, receipt = original['transaction'], original['receipt']
                self.assertEqual(LOCAL_SENDER, actual['from'].lower())
                self.assertEqual(int(row['nonce']), int(actual['nonce'],16))
                if row['id'].startswith('create:'):
                    creations += 1
                    self.assertEqual(row['predicted_address'], receipt['contractAddress'].lower())
                else:
                    self.assertEqual(row['to'], actual['to'].lower())
        self.assertEqual(44, len(summary['receipts'])); self.assertEqual(25, creations)

    def test_sequence_rejects_removed_duplicated_unknown_or_reordered_steps(self):
        original = D.construction_order()
        variants=[]
        rows=copy.deepcopy(original); del rows[2]; variants.append(rows)
        rows=copy.deepcopy(original); rows.insert(3,copy.deepcopy(rows[2])); variants.append(rows)
        rows=copy.deepcopy(original); rows[2]['kind']='unknown_external_action'; variants.append(rows)
        rows=copy.deepcopy(original); rows[0],rows[1]=rows[1],rows[0]; variants.append(rows)
        for rows in variants:
            with self.subTest(ids=[r['id'] for r in rows[:4]]), patch.object(D,'construction_order',return_value=rows), self.assertRaises(ValueError):
                self.derive()

    def test_unresolved_or_changed_binding_caller_is_not_assumed_authorized(self):
        for field,value in (('caller','governance may execute instead'),('call','Access.unbind(moduleId)')):
            rows=copy.deepcopy(D.construction_order());rows[2][field]=value
            with self.subTest(field=field),patch.object(D,'construction_order',return_value=rows),self.assertRaises(ValueError):
                self.derive()

    def test_prepare_fills_only_matching_assignments_and_preserves_input_object(self):
        value=deployment_input(); original=copy.deepcopy(value)
        result=subject().prepare(value,SENDER,'7')
        self.assertEqual(original,value)
        self.assertEqual(result['predicted_addresses'], result['constructor_plan']['inputs']['planned_addresses'])
        self.assertEqual(D.DEFAULT_BUILD_PROFILE,result['constructor_plan']['build_profile'])
        self.assertTrue(result['constructor_plan']['top_level_constructor_payloads_complete'])
        self.assertTrue(result['constructor_plan']['input_assignments_complete'])
        self.assertEqual({'runtime_bytes':24576,'full_initcode_bytes':49152},result['constructor_plan']['limits'])
        self.assertEqual(100,result['constructor_plan']['accepted_build']['source_count'])
        self.assertEqual(48,result['constructor_plan']['accepted_build']['normal_size_gates'])
        self.assertIs(result['constructor_plan']['address_predictions_performed'],False)
        self.assertIs(result['address_predictions_performed'],True)
        for flag in ('ready_for_submission','production_approved','rpc_performed','simulation_performed','transaction_submitted'):
            self.assertIs(result[flag],False)

    def test_operator_assignments_can_confirm_but_never_override_predictions(self):
        expected=self.derive('4')['predicted_addresses'];value=deployment_input()
        value['planned_addresses'].update(expected)
        result=subject().prepare(value,SENDER,'4')
        self.assertEqual(expected,result['predicted_addresses'])
        bad=copy.deepcopy(value);bad['planned_addresses']['oracle']='0x'+'c2'*20
        with patch.object(D,'prepare',side_effect=AssertionError('Mismatch must fail before artifact work')),self.assertRaises(ValueError):
            subject().prepare(bad,SENDER,'4')

    def test_missing_release_inputs_remain_blocked_after_addresses_are_derived(self):
        result=subject().prepare(D.template(),SENDER,'0')
        plan=result['constructor_plan']
        self.assertEqual('blocked_preview_missing_inputs',plan['status'])
        self.assertTrue(any(n.startswith('inputs.') for n in plan['missing_inputs']))
        self.assertFalse(any(n.startswith('planned_addresses.') for n in plan['missing_inputs']))
        self.assertFalse(plan['top_level_constructor_payloads_complete'])
        self.assertFalse(result['ready_for_submission'])

    def test_factory_created_children_keep_getter_discovery_and_unknown_addresses(self):
        result=subject().prepare(deployment_input(),SENDER,'0')
        plan=result['constructor_plan']; children=[r for r in plan['instances'] if r['mode']!='top_level']
        self.assertEqual(14,len(children))
        self.assertTrue(all(r['planned_address'] is None for r in children))
        self.assertTrue(all(r['address_status']=='discover_actual_getter_no_nonce_prediction' for r in children))
        self.assertFalse(plan['all_instance_constructor_payloads_complete'])
        self.assertEqual(25,len(result['predicted_addresses']))

    def test_old_constructor_safeguards_and_qualification_flags_cannot_be_bypassed(self):
        variants=[]
        value=deployment_input();value['inputs']['pool_manager']='0x'+'d1'*20;variants.append(value)
        value=deployment_input();value['inputs']['buyback_maximum_trade_usd']='0';variants.append(value)
        value=deployment_input();value['inputs']['base_uri']='https://not-source-valid.invalid/';variants.append(value)
        value=deployment_input();value['inputs']['governance']=self.derive()['predicted_addresses']['vault'];variants.append(value)
        value=deployment_input();value['inputs']['mint_recipient']=self.derive()['predicted_addresses']['rewards'];variants.append(value)
        value=deployment_input();value['rpc_urls']=['https://not-allowed.invalid'];variants.append(value)
        for value in variants:
            with self.subTest(value=str(value)[:60]),self.assertRaises(ValueError):
                subject().prepare(value,SENDER,'0')

    def test_no_network_or_live_sender_observation_is_performed(self):
        with patch.object(socket,'create_connection',side_effect=AssertionError('Offline only')):
            result=subject().prepare(D.template(),SENDER,'0')
        self.assertFalse(result['rpc_performed']);self.assertFalse(result['simulation_performed'])
        self.assertFalse(result['transaction_submitted']);self.assertFalse(result['ready_for_submission'])


if __name__ == '__main__':
    unittest.main()
