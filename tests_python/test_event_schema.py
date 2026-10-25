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
    def test_keeper_range_policy_and_orientation_logs_are_exact_and_bounded(self):
        pool='0x'+'ab'*32;review='0x'+'cd'*32
        cases=(('RangeOrientationChanged(bytes32,uint8,uint8)',[word(0,'uint8'),word(1,'uint8')],
                {'poolId':pool,'previous':'0','current':'1'}),
            ('KeeperRangePolicyChanged(bytes32,bool,bytes32,bytes32)',[word(True,'bool'),word(pool,'bytes32'),word(review,'bytes32')],
                {'poolId':pool,'enabled':True,'configurationHash':pool,'reviewHash':review}),
            ('KeeperRangeSelected(bytes32,uint16,uint16,bytes32)',[word(5000,'uint16'),word(2500,'uint16'),word(review,'bytes32')],
                {'poolId':pool,'previous':'5000','current':'2500','reviewHash':review}))
        for signature,data,expected in cases:
            with self.subTest(signature=signature):
                self.assertEqual(decode(log(signature,[word(pool,'bytes32')],data)),(signature.split('(')[0],expected))
        with self.assertRaisesRegex(ValueError,'overflow'):
            decode(log(cases[0][0],[word(pool,'bytes32')],[word(256,'uint256'),word(1,'uint8')]))
        with self.assertRaisesRegex(ValueError,'boolean'):
            decode(log(cases[1][0],[word(pool,'bytes32')],[word(2,'uint256'),word(pool,'bytes32'),word(review,'bytes32')]))

    def test_dual_price_and_factual_contribution_events_are_exactly_decodable(self):
        signatures = (
            'DualPolicyRecorded(bytes32,address,address,address,bytes32,bytes32,uint16,bytes32)',
            'DualPolicyActivated(address,bytes32,bytes32)',
            'ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)',
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                entry = SCHEMA[topic(signature)]
                indexed, data, expected = [], [], {}
                for field in entry['fields']:
                    typ = field['type']
                    value = TOKEN if typ == 'address' else '0x'+'11'*32 if typ == 'bytes32' else 7
                    (indexed if field['indexed'] else data).append(word(value, typ))
                    expected[field['name']] = value if typ in ('address', 'bytes32') else str(value)
                self.assertEqual(decode(log(signature, indexed, data)), (entry['name'], expected))

    def test_reviewed_retired_topics_remain_decodable_without_enabling_old_modules(self):
        historical=json.loads((ROOT/'indexer/historical_event_schema.json').read_text())
        self.assertEqual(len(historical),33)  # 17 earlier plus 16 retired source descriptors.
        self.assertTrue({'FeedConfigured','BuybackTargetChanged','WrapperPolicyApproved',
            'ExternalRewardsFunded','RemoteAccountingImported'} <= {entry['name'] for entry in historical.values()})
        for event_topic,entry in historical.items():
            with self.subTest(signature=entry['signature']):
                self.assertEqual(SCHEMA[event_topic],entry)
                indexed=[];data=[];expected={}
                for field in entry['fields']:
                    typ=field['type'];value=TOKEN if typ=='address' else '0x'+'11'*32 if typ=='bytes32' else True if typ=='bool' else 1
                    (indexed if field['indexed'] else data).append(word(value,typ))
                    expected[field['name']]=value if typ in ('address','bytes32','bool') else str(value)
                self.assertEqual(decode(log(entry['signature'],indexed,data)),(entry['name'],expected))

    def test_historical_catalog_rejects_wrong_topics_and_indexed_collisions(self):
        entry=generator.build_schema(['event Example(uint256 indexed value);'])
        event_topic=next(iter(entry))
        with self.assertRaisesRegex(ValueError,'Historical event topic'):
            generator.merge_historical({}, {'0x'+'00'*32:entry[event_topic]})
        different=generator.build_schema(['event Example(uint256 value);'])
        with self.assertRaisesRegex(ValueError,'Conflicting historical'):
            generator.merge_historical(different,entry)

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

    def test_future_request_policy_changes_retain_old_and_new_values(self):
        self.assertEqual(decode(log('RandomnessRequestSettingsChanged(uint16,uint32,uint16,uint32)',
            data=[word(3,'uint16'),word(500000,'uint32'),word(10,'uint16'),word(1000000,'uint32')])),
            ('RandomnessRequestSettingsChanged', {'previousConfirmations':'3',
                'previousCallbackGasLimit':'500000','confirmations':'10','callbackGasLimit':'1000000'}))
        with self.assertRaisesRegex(ValueError,'Event integer overflow'):
            decode(log('RandomnessRequestSettingsChanged(uint16,uint32,uint16,uint32)',
                data=[word(3,'uint16'),word(500000,'uint32'),word(65536,'uint256'),word(1000000,'uint32')]))

    def test_buyback_operating_limit_stop_and_reopen_are_observable(self):
        for previous,current in ((1000,0),(0,500)):
            self.assertEqual(decode(log('OperatingTradeLimitChanged(uint256,uint256)',
                data=[word(previous,'uint256'),word(current,'uint256')])),
                ('OperatingTradeLimitChanged',{'previous':str(previous),'current':str(current)}))

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
