"""Reject malformed head quantities before admitting a new confirmed log chunk."""
import unittest
from unittest.mock import patch

from indexer.monitor import IndexerSafetyError
from tests_python import test_indexer as fixtures


class IndexerHeadSafetyTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.IndexerTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.index,self.chain=self.f.idx,self.f.chain

    def test_malformed_head_never_silently_succeeds_or_ingests_new_history(self):
        original=self.chain.call
        for value in ('6','0x00','0x-1','0x+6','0x6 ','0X6',hex(2**63),None,True):
            with self.subTest(value=value):
                before=self.f.database_snapshot(self.index)
                def read(method,params):
                    return value if method=='eth_blockNumber' else original(method,params)
                with patch.object(self.chain,'call',side_effect=read),self.assertRaises(IndexerSafetyError):
                    self.index.step()
                self.assertEqual(before,self.f.database_snapshot(self.index))

    def test_canonical_zero_and_confirmed_head_keep_existing_ingestion_semantics(self):
        self.chain.head=0
        self.assertEqual(0,self.index.step());self.assertEqual(1,self.index.next_block)
        self.chain.head=6;self.chain.transfer(5,fixtures.B);self.chain.transfer(6,fixtures.C)
        self.assertEqual(5,self.index.step());self.assertEqual(6,self.index.next_block)
        self.assertEqual({'7':fixtures.B},self.index.nft_owners(fixtures.A))
        self.assertEqual(0,self.index.step())


if __name__=='__main__':unittest.main()
