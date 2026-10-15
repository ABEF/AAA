"""Source-schema compatibility and raw-log regressions for the new reward ledgers."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from indexer.events import SCHEMA, decode
from zzz_ops.abi import keccak256, word

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('event_generator', ROOT / 'scripts/generate_event_schema.py')
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)
TOKEN = '0x' + '11' * 20
OWNER = '0x' + '22' * 20
NATIVE = '0x' + '00' * 20


def topic(signature):
    return '0x' + keccak256(signature.encode()).hex()


def log(signature, indexed=(), data=(), emitter=TOKEN):
    return {'address': emitter, 'topics': [topic(signature)] + ['0x' + value for value in indexed],
            'data': '0x' + ''.join(data)}


class EventSchemaTests(unittest.TestCase):
    def test_generated_artifact_matches_current_contract_sources(self):
        stored = json.loads((ROOT / 'indexer/event_schema.json').read_text(encoding='utf-8'))
        self.assertEqual(stored, generator.source_schema())
        self.assertNotIn('PowerIncreased', {entry['name'] for entry in stored.values()})

    def test_equal_abi_alias_keeps_first_canonical_field_names(self):
        schemas = generator.build_schema([
            'event Claimed(uint256 indexed nftId, address indexed token, address indexed recipient, uint256 amount);',
            'event Claimed(uint256 indexed id, address indexed asset, address indexed owner, uint256 amount);',
        ])
        self.assertEqual(len(schemas), 1)
        entry = schemas[topic('Claimed(uint256,address,address,uint256)')]
        self.assertEqual([field['name'] for field in entry['fields']], ['nftId', 'token', 'recipient', 'amount'])

    def test_same_topic_indexed_layout_conflict_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting event topic'):
            generator.build_schema([
                'event Changed(address indexed owner, uint256 amount);',
                'event Changed(address owner, uint256 indexed amount);',
            ])

    def test_topic_collision_with_different_types_or_signature_fails_closed(self):
        for declaration in ('event Changed(address owner);', 'event Other(uint256 amount);'):
            with self.subTest(declaration=declaration), patch.object(generator, 'keccak256', return_value=b'\0' * 32):
                with self.assertRaisesRegex(ValueError, 'Conflicting event topic'):
                    generator.build_schema(['event Changed(uint256 amount);', declaration])

    def test_overloaded_asset_admissions_keep_both_distinct_abis(self):
        self.assertEqual(decode(log('AssetAdded(address)', [word(TOKEN, 'address')])),
                         ('AssetAdded', {'token': TOKEN}))
        self.assertEqual(decode(log('AssetAdded(address,uint256)', [word(TOKEN, 'address')], [word(19, 'uint256')])),
                         ('AssetAdded', {'asset': TOKEN, 'quarantined': '19'}))

    def test_membership_and_royalty_activation_logs_are_distinct(self):
        self.assertEqual(decode(log('MembershipActivated(uint256)', [word(42, 'uint256')])),
                         ('MembershipActivated', {'nftId': '42'}))
        self.assertEqual(decode(log('Activated(uint256,uint256)', [word(42, 'uint256')], [word(3, 'uint256')])),
                         ('Activated', {'id': '42', 'weight': '3'}))
        self.assertEqual(decode(log('MembershipDustSettled(uint256,address,uint256)',
            [word(7, 'uint256'), word(TOKEN, 'address')], [word(19, 'uint256')])),
            ('MembershipDustSettled', {'bucketId': '7', 'token': TOKEN, 'amount': '19'}))

    def test_native_and_token_royalty_receipts_include_eligibility(self):
        for asset, eligible in ((NATIVE, False), (TOKEN, True)):
            with self.subTest(asset=asset):
                self.assertEqual(decode(log('RoyaltiesReceived(address,uint256,bool)',
                    [f'{int(asset, 16):064x}'], [word(250, 'uint256'), word(eligible, 'bool')])),
                    ('RoyaltiesReceived', {'asset': asset, 'amount': '250', 'eligible': eligible}))

    def test_lp_and_royalty_claim_logs_preserve_existing_decoder_names(self):
        # Identical topic/layout: the log's emitting address identifies the
        # reward ledger. A new helper must not rename the LP decoder fields.
        for emitter in (TOKEN, OWNER):
            with self.subTest(emitter=emitter):
                self.assertEqual(decode(log('Claimed(uint256,address,address,uint256)',
                    [word(42, 'uint256'), word(TOKEN, 'address'), word(OWNER, 'address')],
                    [word(1234, 'uint256')], emitter=emitter)),
                    ('Claimed', {'nftId': '42', 'token': TOKEN, 'recipient': OWNER, 'amount': '1234'}))

    def test_vrf_configuration_and_ordered_request_logs(self):
        key = '0x' + 'ab' * 32
        self.assertEqual(decode(log('RandomnessConfigured(address,bytes32,uint256,uint16,uint32,bool)',
            [word(OWNER, 'address')], [word(key, 'bytes32'), word(123, 'uint256'), word(3, 'uint16'),
                word(500000, 'uint32'), word(True, 'bool')])),
            ('RandomnessConfigured', {'coordinator': OWNER, 'keyHash': key, 'subscriptionId': '123',
                'confirmations': '3', 'callbackGasLimit': '500000', 'nativePayment': True}))
        self.assertEqual(decode(log('RandomnessRequested(uint256,uint256,uint256)',
            [word(42, 'uint256'), word(9001, 'uint256'), word(17, 'uint256')])),
            ('RandomnessRequested', {'nftId': '42', 'requestId': '9001', 'ordinal': '17'}))
        self.assertEqual(decode(log('RandomnessReceived(uint256)', [word(9001, 'uint256')])),
                         ('RandomnessReceived', {'requestId': '9001'}))

    def test_finalized_traits_decode_narrow_integer_fields(self):
        self.assertEqual(decode(log('TraitsFinalized(uint256,uint8,uint8)', [word(42, 'uint256')],
            [word(2, 'uint8'), word(5, 'uint8')])),
            ('TraitsFinalized', {'nftId': '42', 'rarity': '2', 'color': '5'}))
        with self.assertRaisesRegex(ValueError, 'Event integer overflow'):
            decode(log('TraitsFinalized(uint256,uint8,uint8)', [word(42, 'uint256')],
                [word(256, 'uint256'), word(5, 'uint8')]))

    def test_erc4906_metadata_events_have_unindexed_data_arguments(self):
        self.assertEqual(decode(log('MetadataUpdate(uint256)', data=[word(42, 'uint256')])),
                         ('MetadataUpdate', {'tokenId': '42'}))
        self.assertEqual(decode(log('BatchMetadataUpdate(uint256,uint256)',
            data=[word(1, 'uint256'), word(1000, 'uint256')])),
            ('BatchMetadataUpdate', {'fromTokenId': '1', 'toTokenId': '1000'}))
        for signature in ('MetadataUpdate(uint256)', 'BatchMetadataUpdate(uint256,uint256)'):
            self.assertTrue(all(not field['indexed'] for field in SCHEMA[topic(signature)]['fields']))
        with self.assertRaisesRegex(ValueError, 'Indexed argument count mismatch'):
            decode(log('MetadataUpdate(uint256)', [word(42, 'uint256')]))

    def test_dynamic_metadata_and_obsolete_power_logs_remain_raw(self):
        data = [word(32, 'uint256'), word(7, 'uint256'), b'ipfs://'.hex().ljust(64, '0')]
        self.assertEqual(decode(log('MetadataBaseChanged(string)', data=data)), ('MetadataBaseChanged', None))
        self.assertEqual(decode(log('PowerIncreased(uint256,uint256,uint256)', [word(42, 'uint256')],
            [word(100, 'uint256'), word(1000, 'uint256')])), (None, None))


if __name__ == '__main__':
    unittest.main()
