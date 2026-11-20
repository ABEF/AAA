"""New offline intent-review cases; no actual OpenSea response or chain acceptance.

Calldata is independently assembled from ABI words. The existing phase fixture
uses synthetic source files; its tests are not inherited or re-run here.
"""
import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

from tests_python import test_opensea_drop as fixture
from zzz_ops import opensea_drop as O
from zzz_ops.abi import keccak256


def abi_word(value):
    if isinstance(value, str) and value.startswith('0x'):
        value = int(value, 16)
    return int(value).to_bytes(32, 'big')


def public_data(nft, fee, recipient, quantity):
    selector = keccak256(b'mintPublic(address,address,address,uint256)')[:4]
    return '0x' + (selector + b''.join(abi_word(x) for x in
                                     (nft, fee, recipient, quantity))).hex()


def allow_data(nft, fee, recipient, quantity, record):
    selector = keccak256(
        b'mintAllowList(address,address,address,uint256,'
        b'(uint256,uint256,uint256,uint256,uint256,uint256,uint256,bool),bytes32[])')[:4]
    params = record['mint_params']
    values = [nft, fee, recipient, quantity] + [params[k] for k in
        ('mintPrice', 'maxTotalMintableByWallet', 'startTime', 'endTime',
         'dropStageIndex', 'maxTokenSupplyForStage', 'feeBps')]
    values += [1, 13 * 32, len(record['proof']), *record['proof']]
    return '0x' + (selector + b''.join(abi_word(x) for x in values)).hex()


def change_word(data, index, value):
    raw = bytearray.fromhex(data[2:])
    raw[4 + index * 32:4 + (index + 1) * 32] = abi_word(value)
    return '0x' + raw.hex()


class OpenSeaMintReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.OpenSeaDropTests(
            methodName='test_defaults_preserve_full_supply_and_one_hour_opening')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

    def request(self, phase='public', *, gifted=False):
        request = self.fixture.request()
        caller = fixture.addr(77)
        if gifted:
            request['allowed_payers'] = [caller]
        manifest = self.fixture.prepare(request)
        if phase == 'public':
            minter = fixture.addr(88) if gifted else caller
            data = public_data(request['nft_contract'], request['fee_recipient'],
                               minter if gifted else 0, 1)
            timestamp = '300'
        else:
            record = next(x for x in manifest['proofs'] if x['phase'] == phase)
            minter = record['minter']
            if not gifted:
                caller = minter
            data = allow_data(request['nft_contract'], request['fee_recipient'],
                              minter if gifted else 0, 1, record)
            timestamp = record['mint_params']['startTime']
        return dict(schema=1, manifest=manifest,
            intent=dict(caller=caller, minter=minter, phase=phase, quantity='1',
                        review_timestamp=timestamp),
            unsigned_transaction=dict(chain_id='4663', **{'from': caller},
                to=request['seadrop'], value='0' if phase == 'team' else request['mint_price_wei'],
                data=data))

    def review(self, request):
        return O.review_mint(request, self.root)

    def test_public_exact_payload_is_retained_and_review_is_never_live_approval(self):
        request = self.request()
        original = copy.deepcopy(request)
        result = self.review(request)
        self.assertEqual(original, request)
        self.assertEqual(request['unsigned_transaction'], result['unsigned_transaction'])
        self.assertEqual(132, len(bytes.fromhex(result['unsigned_transaction']['data'][2:])))
        self.assertTrue(result['manifest_matches'])
        self.assertTrue(result['transaction_matches_reviewed_intent'])
        self.assertFalse(result['calldata_modified'])
        for field in ('ready_for_submission', 'onchain_snapshot_verified',
                      'authority_verified', 'simulation_performed',
                      'target_runtime_verified', 'opensea_primary_drop_accepted',
                      'network_access_performed', 'signing_performed'):
            self.assertFalse(result['boundaries'][field], field)
        unsigned = {k:v for k,v in result.items() if k != 'review_hash'}
        canonical = json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                               ensure_ascii=True, allow_nan=False).encode('ascii')
        expected = hashlib.sha256(b'ZZZ_POPL_OPENSEA_MINT_INTENT_REVIEW_V1\n' + canonical).hexdigest()
        self.assertEqual('0x' + expected, result['review_hash'])

    def test_free_team_and_paid_allowlist_use_their_exact_phase_proofs(self):
        for phase, expected in [('team', '0'), ('allowlist', '50000000000000000')]:
            request = self.request(phase)
            with self.subTest(phase=phase):
                result = self.review(request)
                self.assertEqual(expected, result['gross_native_value_wei'])
                self.assertEqual(phase, result['phase'])
                self.assertEqual(request['intent']['minter'], result['recipient'])

    def test_reviewed_delegated_payers_and_direct_nonzero_recipient_are_explicit(self):
        for phase in ('public', 'team', 'allowlist'):
            request = self.request(phase, gifted=True)
            with self.subTest(phase=phase):
                result = self.review(request)
                self.assertNotEqual(result['payer'], result['recipient'])
                self.assertEqual(request['intent']['caller'], result['payer'])
        request = self.request()
        request['unsigned_transaction']['data'] = change_word(
            request['unsigned_transaction']['data'], 2, request['intent']['minter'])
        self.assertTrue(self.review(request)['transaction_matches_reviewed_intent'])

    def test_identity_payment_and_quantity_changes_refuse(self):
        changes = [('chain_id', '4664'), ('from', fixture.addr(99)),
                   ('to', fixture.addr(99)), ('value', '0'),
                   ('value', '50000000000000001'), ('value', 50000000000000000),
                   ('value', True), ('value', '050000000000000000')]
        for key, value in changes:
            request = self.request()
            request['unsigned_transaction'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.review(request)
        for index, value in [(0, fixture.addr(99)), (1, fixture.addr(99)),
                             (2, fixture.addr(99)), (3, 0), (3, 2),
                             (0, 1 << 160), (1, 1 << 160), (2, 1 << 160)]:
            request = self.request()
            request['unsigned_transaction']['data'] = change_word(
                request['unsigned_transaction']['data'], index, value)
            with self.subTest(word=index, value=value), self.assertRaises(ValueError):
                self.review(request)

    def test_phase_timing_is_inclusive_but_only_supplied_intent_not_chain_time(self):
        for phase, start, end in [('team', 100, 199), ('allowlist', 200, 299), ('public', 300, 399)]:
            for stamp in (start, end):
                request = self.request(phase)
                request['intent']['review_timestamp'] = str(stamp)
                with self.subTest(phase=phase, stamp=stamp):
                    self.assertTrue(self.review(request)['transaction_matches_reviewed_intent'])
            for stamp in (start - 1, end + 1):
                request = self.request(phase)
                request['intent']['review_timestamp'] = str(stamp)
                with self.subTest(phase=phase, stamp=stamp), self.assertRaises(ValueError):
                    self.review(request)
        for key, value in [('phase', 'signed'), ('phase', 'team'), ('minter', fixture.addr(99)),
                           ('caller', fixture.addr(99)), ('quantity', '0'), ('quantity', '2'),
                           ('quantity', 1), ('review_timestamp', True)]:
            request = self.request()
            request['intent'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.review(request)

    def test_allowlist_terms_offsets_boolean_and_proof_tampering_refuse(self):
        for index, value in [(4, 0), (5, 2), (6, 199), (7, 300),
                             (8, 1), (9, 1000), (10, 0), (11, 0),
                             (11, 2), (12, 32), (12, 448), (13, 11), (14, 0)]:
            request = self.request('allowlist')
            request['unsigned_transaction']['data'] = change_word(
                request['unsigned_transaction']['data'], index, value)
            with self.subTest(word=index, value=value), self.assertRaises(ValueError):
                self.review(request)
        request = self.request('allowlist')
        request['intent']['minter'] = fixture.addr(99)
        request['intent']['caller'] = fixture.addr(99)
        request['unsigned_transaction']['from'] = fixture.addr(99)
        with self.assertRaises(ValueError):
            self.review(request)

    def test_payer_permissions_and_batch_wallet_bounds_are_not_assumed(self):
        for phase in ('public', 'team', 'allowlist'):
            request = self.request(phase, gifted=True)
            request['manifest']['request']['allowed_payers'] = []
            request['manifest'] = self.fixture.prepare(request['manifest']['request'])
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                self.review(request)
        request = self.request()
        request['intent']['quantity'] = '3'
        request['unsigned_transaction']['data'] = change_word(request['unsigned_transaction']['data'], 3, 3)
        request['unsigned_transaction']['value'] = '150000000000000000'
        with self.assertRaises(ValueError):  # public cumulative limit is2
            self.review(request)
        request = self.request('team')
        request['intent']['quantity'] = '5'
        request['unsigned_transaction']['data'] = change_word(request['unsigned_transaction']['data'], 3, 5)
        with self.assertRaises(ValueError):  # helper maxBatch is4
            self.review(request)

    def test_signed_configuration_trailing_and_noncanonical_data_refuse(self):
        for phase in ('public', 'allowlist'):
            original = self.request(phase)
            data = original['unsigned_transaction']['data']
            alternatives = [data + '00', data + '00' * 32, data[:-2], '0x',
                            data[:5], '0x' + 'ff' * (O.MAX_MINT_CALLDATA + 1)]
            for sig in (b'mintSigned()', b'multiConfigure()', b'approve(address,uint256)'):
                alternatives.append('0x' + keccak256(sig)[:4].hex() + data[10:])
            for mutated in alternatives:
                request = copy.deepcopy(original)
                request['unsigned_transaction']['data'] = mutated
                with self.subTest(phase=phase, prefix=mutated[:12]), self.assertRaises(ValueError):
                    self.review(request)

    def test_static_public_capacity_respects_team_reserve_and_allowlist_rollover(self):
        request = self.request()
        manifest_request = request['manifest']['request']
        manifest_request.update(team_allocation='1000', allowlist_allocation='0',
                                team=[dict(address=fixture.addr(10), quantity='1000')], allowlist=[])
        request['manifest'] = self.fixture.prepare(manifest_request)
        with self.assertRaises(ValueError):
            self.review(request)  # All supply is reserved; public can never mint.
        manifest_request.update(team_allocation='500', allowlist_allocation='500',
                                team=[dict(address=fixture.addr(10), quantity='500')],
                                allowlist=[fixture.addr(22)])
        request['manifest'] = self.fixture.prepare(manifest_request)
        self.assertEqual('0', request['manifest']['allocations']['public_base'])
        self.assertTrue(self.review(request)['transaction_matches_reviewed_intent'])
        # Unused allowlist supply can roll over; actual remaining supply is unknown.

    def test_unknown_fields_source_drift_and_forged_manifest_approval_refuse(self):
        for target in ('request', 'intent', 'unsigned_transaction'):
            request = self.request()
            (request if target == 'request' else request[target])['unexpected'] = 'DO_NOT_ECHO'
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.review(request)
        request = self.request()
        request['manifest']['boundaries']['ready_for_submission'] = True
        with self.assertRaises(ValueError):
            self.review(request)
        request = self.request()
        source = self.root / O.SOURCE_PATHS[0]
        source.write_bytes(source.read_bytes() + b'changed')
        with self.assertRaises(ValueError):
            self.review(request)

    def test_cli_review_is_offline_exclusive_and_rejection_is_sanitized(self):
        request = self.request()
        input_path, output_path = self.root / 'review.json', self.root / 'checked.json'
        input_path.write_bytes(O.render(request))
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), \
                patch.object(subprocess, 'run', side_effect=AssertionError('process forbidden')):
            self.assertEqual(0, O.main(['review-mint', str(input_path), '--output', str(output_path)], root=self.root))
        actual = json.loads(output_path.read_text(encoding='ascii'))
        self.assertFalse(actual['boundaries']['ready_for_submission'])
        original = output_path.read_bytes()
        with redirect_stderr(io.StringIO()):
            self.assertEqual(1, O.main(['review-mint', str(input_path), '--output', str(output_path)], root=self.root))
        self.assertEqual(original, output_path.read_bytes())
        request['unsigned_transaction']['private_key'] = 'DO_NOT_ECHO'
        input_path.write_bytes(O.render(request))
        absent = self.root / 'absent.json'
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(1, O.main(['review-mint', str(input_path), '--output', str(absent)], root=self.root))
        self.assertFalse(absent.exists())
        self.assertEqual('', stdout.getvalue())
        self.assertNotIn('DO_NOT_ECHO', stderr.getvalue())

    def test_singleton_allowlist_empty_proof_has_the_minimum_canonical_tail(self):
        request = self.request('allowlist')
        manifest_request = request['manifest']['request']
        manifest_request.update(team_allocation='0', team=[], allowlist_allocation='1',
                                allowlist=[fixture.addr(22)])
        request['manifest'] = self.fixture.prepare(manifest_request)
        record = request['manifest']['proofs'][0]
        request['intent'].update(caller=record['minter'], minter=record['minter'])
        request['unsigned_transaction']['from'] = record['minter']
        request['unsigned_transaction']['data'] = allow_data(
            manifest_request['nft_contract'], manifest_request['fee_recipient'], 0, 1, record)
        self.assertEqual([], record['proof'])
        self.assertEqual(4 + 14 * 32, len(bytes.fromhex(request['unsigned_transaction']['data'][2:])))
        self.assertTrue(self.review(request)['transaction_matches_reviewed_intent'])

    def test_maximum_depth_allowlist_proof_fills_the_bounded_calldata(self):
        request = self.request('allowlist')
        manifest_request = request['manifest']['request']
        manifest_request.update(team_allocation='0', team=[], allowlist_allocation='1000',
                                allowlist=[fixture.addr(5000 + i) for i in range(1000)])
        request['manifest'] = self.fixture.prepare(manifest_request)
        record = next(row for row in request['manifest']['proofs'] if len(row['proof']) == 10)
        request['intent'].update(caller=record['minter'], minter=record['minter'])
        request['unsigned_transaction']['from'] = record['minter']
        request['unsigned_transaction']['data'] = allow_data(
            manifest_request['nft_contract'], manifest_request['fee_recipient'], 0, 1, record)
        self.assertEqual(10, len(record['proof']))
        self.assertEqual(O.MAX_MINT_CALLDATA,
                         len(bytes.fromhex(request['unsigned_transaction']['data'][2:])))
        self.assertTrue(self.review(request)['transaction_matches_reviewed_intent'])

    def test_multi_quantity_free_team_and_paid_public_mints_match_exact_value(self):
        for phase in ('team', 'public'):
            request = self.request(phase)
            request['intent']['quantity'] = '2'
            request['unsigned_transaction']['data'] = change_word(
                request['unsigned_transaction']['data'], 3, 2)
            request['unsigned_transaction']['value'] = '0' if phase == 'team' else '100000000000000000'
            with self.subTest(phase=phase):
                result = self.review(request)
                self.assertEqual('2', result['quantity'])
                self.assertEqual(request['unsigned_transaction']['value'], result['gross_native_value_wei'])
                self.assertEqual(request['unsigned_transaction'], result['unsigned_transaction'])


if __name__ == '__main__':
    unittest.main()
