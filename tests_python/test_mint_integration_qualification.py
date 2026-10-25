"""Offline capability gates; synthetic evidence never qualifies a service."""
import json
from pathlib import Path
import unittest

from tests_python.test_production_v2 import fixture, NOW, SHA, addr
from tests_python.fee_intake_fixtures import lp_only_fixture
from zzz_ops import production_v2 as P


def current_fixture():
    config = lp_only_fixture(fixture())
    config['mint_integration_version'] = 1
    chain = config['chains'][0]
    chain['services']['opensea']['integration'] = {
        'requested_product':'opensea_seadrop_v1',
        'implementation_profile':'vault_direct_v1',
    }
    vrf = chain['nft_inventory']['randomness']
    vrf.update(request_profile='subscription_v25_two_words_v1',
        request_selector='0x9b1c385e',num_words=2,
        recovery_policy={'unserved_request':'original_request_remains_valid',
            'refund_or_expiry':'cannot_invalidate_original_fulfillment',
            'failed_callback':'same_request_same_result','reroll':'none'},
        funding={'source':'external_subscription_reserve','owner':addr(9200)})
    vrf['integration_evidence'].update(recovery_request_id=1,
        original_result_sha256=SHA,recovered_result_sha256=SHA,
        request_selector='0x9b1c385e',callback_words_count=2,
        invalid_proof_rejection_sha256='33'*32,
        unauthenticated_callback_rejection_sha256='44'*32)
    return config


class MintIntegrationQualificationTests(unittest.TestCase):
    def report(self, config=None):
        return P.validate(current_fixture() if config is None else config,now=NOW)

    def codes(self, config):
        return {issue['code'] for issue in self.report(config)['issues']}

    def test_legacy_consistency_is_preserved_but_never_production_qualification(self):
        for explicit in (False,True):
            config = fixture()
            if explicit: config['mint_integration_version'] = 0
            result = self.report(config)
            self.assertTrue(result['ready'],result['issues'])
            self.assertFalse(result['production_qualification_supported'])
            self.assertEqual('legacy_manifest_consistency_only',result['approval_scope'])
            self.assertFalse(result['deployment_authorized'])
            self.assertFalse(result['opensea_primary_mint_supported'])

    def test_current_profile_cannot_invent_unsupported_opensea_mint(self):
        result = self.report()
        self.assertEqual({'mint.opensea_unsupported'},{i['code'] for i in result['issues']})
        self.assertTrue(result['production_qualification_supported'])
        self.assertFalse(result['ready'])
        self.assertEqual('vault_direct_v1',result['primary_mint_implementation'])
        self.assertFalse(result['deployment_authorized'])
        config = current_fixture()
        integration = config['chains'][0]['services']['opensea']['integration']
        integration.update(supports_seadrop=True,mintSeaDrop=True,accepted_by_opensea=True)
        self.assertIn('mint.opensea_unsupported',self.codes(config))

    def test_cannot_claim_a_different_implementation_or_secondary_product(self):
        for field,value,code in (
            ('implementation_profile','seadrop_compatible_v1','mint.implementation_profile'),
            ('requested_product','secondary_marketplace','mint.product'),
            ('requested_product','generic_robinhood_chain','mint.product'),
        ):
            with self.subTest(field=field,value=value):
                config = current_fixture()
                config['chains'][0]['services']['opensea']['integration'][field] = value
                self.assertIn(code,self.codes(config))
                self.assertIn('mint.opensea_unsupported',self.codes(config))

    def test_exact_request_abi_profile_and_two_words_required(self):
        for field,value in (
            ('request_profile','same_callback_only'),('request_selector','0x00000000'),
            ('num_words',1),('num_words',True),('num_words','2'),
        ):
            with self.subTest(field=field,value=value):
                config = current_fixture()
                config['chains'][0]['nft_inventory']['randomness'][field] = value
                self.assertIn('randomness.request_profile',self.codes(config))
        config = current_fixture()
        config['chains'][0]['nft_inventory']['randomness']['keyHash'] = P.ZERO_HASH
        self.assertTrue(any(i['path'].endswith('.randomness.keyHash') for i in self.report(config)['issues']))

    def test_irreversible_expiry_refund_or_reroll_does_not_qualify_original_draw(self):
        for field,value in (
            ('unserved_request','expires_after_timeout'),
            ('refund_or_expiry','refund_cancels_fulfillment'),
            ('failed_callback','request_new_words'),('reroll','administrator'),
        ):
            with self.subTest(field=field,value=value):
                config = current_fixture()
                config['chains'][0]['nft_inventory']['randomness']['recovery_policy'][field] = value
                self.assertIn('randomness.recovery_policy',self.codes(config))

    def test_recovery_must_preserve_original_request_and_actual_result(self):
        for field,value in (
            ('recovery_request_id',2),('recovered_result_sha256','55'*32),
            ('callback_words_count',1),('callback_words_count',True),
            ('request_selector','0x00000000'),
        ):
            with self.subTest(field=field,value=value):
                config = current_fixture()
                config['chains'][0]['nft_inventory']['randomness']['integration_evidence'][field] = value
                self.assertIn('randomness.original_result_recovery',self.codes(config))

    def test_negative_proof_and_callback_evidence_are_not_omitted(self):
        for field in ('invalid_proof_rejection_sha256','unauthenticated_callback_rejection_sha256'):
            config = current_fixture()
            del config['chains'][0]['nft_inventory']['randomness']['integration_evidence'][field]
            self.assertTrue(any(i['path'].endswith(field) for i in self.report(config)['issues']))

    def test_native_payment_choice_does_not_authorize_locked_principal_funding(self):
        config = current_fixture()
        config['chains'][0]['nft_inventory']['randomness']['funding']['source'] = 'vault_locked_lp'
        self.assertIn('randomness.funding',self.codes(config))
        config = current_fixture()
        config['chains'][0]['nft_inventory']['randomness']['funding']['owner'] = P.ZERO
        self.assertTrue(any(i['path'].endswith('.funding.owner') for i in self.report(config)['issues']))

    def test_profile_type_cannot_silently_select_legacy_or_current(self):
        for value in (True,False,'1',2,None):
            with self.subTest(value=value):
                config = current_fixture();config['mint_integration_version'] = value
                result = self.report(config)
                self.assertIn('mint.profile',{i['code'] for i in result['issues']})
                self.assertFalse(result['production_qualification_supported'])
                self.assertFalse(result['ready'])

    def test_current_template_declares_real_implementation_and_unselected_provider(self):
        config = json.loads((Path(__file__).resolve().parents[1]/'config/production.example.json').read_text(encoding='utf8'))
        self.assertEqual(1,config['mint_integration_version'])
        chain = config['chains'][0]
        self.assertEqual('vault_direct_v1',chain['services']['opensea']['integration']['implementation_profile'])
        self.assertIsNone(chain['nft_inventory']['randomness']['coordinator'])
        result = P.validate(config,now=NOW)
        self.assertFalse(result['ready'])
        self.assertIn('mint.opensea_unsupported',{i['code'] for i in result['issues']})

    def test_current_malformed_integration_records_fail_closed_without_exception(self):
        for field in ('randomness','integration'):
            for malformed in (None,[],True,'unverified'):
                with self.subTest(field=field,malformed=malformed):
                    config = current_fixture()
                    chain = config['chains'][0]
                    if field == 'randomness':
                        chain['nft_inventory']['randomness'] = malformed
                    else:
                        chain['services']['opensea']['integration'] = malformed
                    result = self.report(config)
                    self.assertFalse(result['ready'])
                    self.assertIn('mint.opensea_unsupported',{i['code'] for i in result['issues']})


if __name__ == '__main__':
    unittest.main()
