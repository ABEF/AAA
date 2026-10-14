import unittest
from zzz_ops.abi import address,calldata,decode_words,keccak256,uint_result,word
from indexer.events import decode

class AbiTests(unittest.TestCase):
    def test_keccak_empty(self):self.assertEqual(keccak256(b'').hex(),'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
    def test_keccak_abc(self):self.assertEqual(keccak256(b'abc').hex(),'4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45')
    def test_transfer_selector(self):self.assertTrue(calldata('transfer(address,uint256)','0x'+'11'*20,1).startswith('0xa9059cbb'))
    def test_balance_of_selector(self):self.assertTrue(calldata('balanceOf(address)','0x'+'11'*20).startswith('0x70a08231'))
    def test_uint_limits(self):
        self.assertEqual(word(255,'uint8'),'0'*62+'ff')
        for value in (-1,256):
            with self.assertRaises(ValueError):word(value,'uint8')
    def test_invalid_address(self):
        for value in ('0x0','0x'+'00'*20,'alice',None):
            with self.assertRaises(ValueError):address(value)
    def test_unsupported_dynamic(self):
        with self.assertRaises(ValueError):calldata('f(bytes)','0x12')
    def test_arity(self):
        with self.assertRaises(ValueError):calldata('f(uint256)',1,2)
    def test_word_decode(self):self.assertEqual(uint_result('0x'+'f'*64),2**256-1)
    def test_malformed_decode(self):
        for v in ['0x1','0xzz','1234']:
            with self.assertRaises(ValueError):decode_words(v)
    def test_transfer_log(self):
        topic='0x'+keccak256(b'Transfer(address,address,uint256)').hex()
        log={'topics':[topic,'0x'+word('0x'+'11'*20,'address'),'0x'+word('0x'+'22'*20,'address'),'0x'+word(42,'uint256')],'data':'0x'}
        event,decoded=decode(log)
        self.assertEqual(event,'Transfer');self.assertEqual(decoded['tokenId'],'42');self.assertEqual(decoded['to'],'0x'+'22'*20)
    def test_unknown_event_retained(self):self.assertEqual(decode({'topics':['0x'+'ff'*32],'data':'0x'}),(None,None))
    def test_malformed_boolean(self):
        topic='0x'+keccak256(b'ApprovalForAll(address,address,bool)').hex()
        with self.assertRaises(ValueError):decode({'topics':[topic,'0x'+word('0x'+'11'*20,'address'),'0x'+word('0x'+'22'*20,'address')],'data':'0x'+word(2,'uint256')})
