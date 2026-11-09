"""Offline proof controls only; these small fixtures are not actual acceptance."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('source9_offline_verifier', ROOT/'scripts/check-source9-rehearsal-evidence.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class OfflineEvidenceControls(unittest.TestCase):
    def gas(self):
        return dict(schema=2, network_gas=dict(estimated_units='10000000', suggested_limit='12000000',
            price_wei='1', suggested_limit_cost_wei='12000000', estimated_fee_wei='10000000',
            configured_gas_limit='16000000', confirmed_block_gas_limit='12000000', effective_gas_limit='12000000',
            full_twenty_percent_headroom=True, policy_schema=2, includes_all_network_components=True,
            included_in_execution_loss=False, wallet_must_refresh=True))

    def test_full_headroom_and_confirmed_bound_cannot_be_replaced_with_success_flag(self):
        good = self.gas()
        self.assertEqual(CHECK.gas_review(good), (12000000, 1))
        for changes in ({'estimated_units':'11000000','estimated_fee_wei':'11000000'},
                        {'effective_gas_limit':'16000000'}, {'confirmed_block_gas_limit':'11999999'},
                        {'full_twenty_percent_headroom':False}, {'policy_schema':1}):
            bad = copy.deepcopy(good); bad['network_gas'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(CHECK.EvidenceError):
                CHECK.gas_review(bad)

    def test_missing_exact_units_are_not_guessed_zero(self):
        for bad in (None, 0, True, '', '00', '1.0', '-1'):
            with self.subTest(value=bad), self.assertRaises(CHECK.EvidenceError):
                CHECK.raw(bad)

    def test_removed_or_other_transaction_receipt_event_is_not_evidence(self):
        emitter = '0x'+'1'*40; txhash = '0x'+'2'*64
        signature = 'Approval(address,address,uint256)'
        row = dict(address=emitter, topics=[CHECK.topic(signature), '0x'+f'{3:064x}', '0x'+f'{4:064x}'],
                   data='0x'+f'{123:064x}', removed=False, transactionHash=txhash)
        receipt = dict(transactionHash=txhash, logs=[row])
        self.assertEqual(CHECK.receipt_event(receipt, emitter, signature, [3,4], 1), [123])
        for changes in ({'removed':True}, {'transactionHash':'0x'+'5'*64}, {'topics':[CHECK.topic(signature)]}):
            bad = copy.deepcopy(receipt); bad['logs'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(CHECK.EvidenceError):
                CHECK.receipt_event(bad, emitter, signature, [3,4], 1)

    def test_campaign_path_escape_and_missing_inputs_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory); campaign = folder/'campaign'; campaign.mkdir()
            (folder/'external.json').write_text('{}')
            bundle = CHECK.Bundle(campaign)
            for name in ('../external.json', 'missing.json', str(folder/'external.json')):
                with self.subTest(path=name), self.assertRaises(CHECK.EvidenceError):
                    bundle.read(name)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'retained.json'; output.write_bytes(b'original evidence\x00')
            with self.assertRaises(SystemExit) as result:
                CHECK.main(['--campaign',directory,'--inputs',str(Path(directory)/'missing.json'),'--output',str(output)])
            self.assertEqual(result.exception.code, 2)
            self.assertEqual(output.read_bytes(), b'original evidence\x00')


if __name__ == '__main__':
    unittest.main()
