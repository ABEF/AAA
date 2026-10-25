"""Current custody/source events coexist with exact historical topic decoding."""
import unittest
from indexer.events import SCHEMA, decode
from zzz_ops.abi import keccak256


def event(signature, values):
    topic = '0x' + keccak256(signature.encode()).hex()
    fields = SCHEMA[topic]['fields']
    topics, data = [topic], []
    for field, value in zip(fields, values, strict=True):
        word = f'{value:064x}'
        (topics if field['indexed'] else data).append('0x'+word if field['indexed'] else word)
    return {'topics':topics, 'data':'0x'+''.join(data)}


class LPOnlyEventTests(unittest.TestCase):
    def test_current_and_legacy_custody_fields_are_not_reinterpreted(self):
        old = 'CustodyApproved(bytes32,uint256,address,uint256)'
        current = 'CustodyApproved(bytes32,uint256,address,address)'
        name, fields = decode(event(old, (1,2,3,4663)))
        self.assertEqual(name,'CustodyApproved');self.assertEqual(fields['destinationChain'],'4663')
        name, fields = decode(event(current, (1,2,3,4)))
        self.assertEqual(name,'CustodyApproved');self.assertNotIn('destinationChain',fields)
        self.assertEqual(fields['destinationCustody'],'0x'+f'{4:040x}')
        self.assertEqual(fields['recipient'],'0x'+f'{3:040x}')

    def test_fixed_source_identity_is_decoded_and_malformed_address_rejected(self):
        signature = 'ZZZIdentityConfigured(address,bytes32,bytes32)'
        name, fields = decode(event(signature, (3,4,5)))
        self.assertEqual(name,'ZZZIdentityConfigured')
        self.assertEqual(fields['token'],'0x'+f'{3:040x}')
        self.assertEqual(fields['codeHash'],'0x'+f'{4:064x}')
        with self.assertRaisesRegex(ValueError,'Noncanonical event address'):
            decode(event(signature, (1<<160,4,5)))


if __name__ == '__main__': unittest.main()
