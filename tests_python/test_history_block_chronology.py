"""Stored header chronology is required even when a block has no financial log."""
import copy
from pathlib import Path
import tempfile
import unittest

from frontend_api.history import CLAIMED, TRANSFER, History, HistoryError, ZERO
from indexer.monitor import Indexer


def hash_(number):
    return '0x'+f'{number:064x}'


def address_(number):
    return '0x'+f'{number:040x}'


class HistoryBlockChronologyTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path=Path(temporary.name)/'history.sqlite'
        self.contracts=[address_(i) for i in (1,2,3)]
        self.logs=[]
        for number,emitter,topics,data in (
            (11,self.contracts[0],[TRANSFER,hash_(0),hash_(4),hash_(7)],'0x'),
            # A valid unrecognized LOG0 is retained; filtered replay must not
            # make its block's header chronology optional.
            (12,self.contracts[0],[],'0x1234'),
            (13,self.contracts[2],[CLAIMED,hash_(7),hash_(0),hash_(4)],hash_(20)),
        ):
            self.logs.append(dict(address=emitter,blockNumber=hex(number),
                blockHash=hash_(number),transactionHash=hash_(100+number),
                logIndex='0x0',removed=False,topics=topics,data=data))
        config=dict(chain_id=1,start_block=10,start_parent_hash=hash_(9),
                    confirmations=1,block_chunk=5,contracts=self.contracts,database=str(self.path))
        self.index=Indexer(config,self)
        self.addCleanup(self.index.close)
        self.assertEqual(self.index.step(),5)
        self.history=History(dict(database=str(self.path),start_block=10,start_parent_hash=hash_(9),
            contracts=self.contracts,max_events=100),chain_id=1,nft=self.contracts[0],
            rewards=self.contracts[1],royalties=self.contracts[2])

    def call(self,method,params):
        if method=='eth_blockNumber':return hex(14)
        if method=='eth_getLogs':return copy.deepcopy(self.logs)
        if method=='eth_getBlockByNumber':
            number=int(params[0],16)
            return dict(number=hex(number),hash=hash_(number),parentHash=hash_(number-1),timestamp=hex(100+number))
        raise AssertionError(method)

    def read(self,*,consumer=None,timestamp=114):
        return self.history.read(block_number=14,block_hash=hash_(14),block_timestamp=timestamp,
            minted_count=1,lp_assets={ZERO},royalty_assets={ZERO},consumer=consumer)

    def change(self,number,timestamp):
        with self.index.db:
            self.index.db.execute('UPDATE blocks SET timestamp=? WHERE number=?',(timestamp,number))

    def test_eventless_starting_block_cannot_have_a_later_time_than_its_child(self):
        self.change(10,112)
        examined=[]
        before=list(self.index.db.iterdump())
        with self.assertRaises(HistoryError):
            self.read(consumer=lambda *row:examined.append(row))
        self.assertEqual(examined,[])
        self.assertEqual(list(self.index.db.iterdump()),before)

    def test_headers_without_replayed_events_still_require_canonical_timestamp_types(self):
        for number in (10,12):
            for value in (-1,112.5,'malformed'):
                with self.subTest(block=number,timestamp=value):
                    self.change(number,value)
                    with self.assertRaises(HistoryError):self.read()
                    self.change(number,100+number)

    def test_equal_l2_timestamps_and_valid_filtered_logs_remain_readable(self):
        with self.index.db:
            self.index.db.execute('UPDATE blocks SET timestamp=114')
        result=self.read()
        self.assertEqual(result.owners,{7:address_(4)})
        self.assertEqual(result.claims[7,ZERO],(0,20))
        self.assertEqual(result.provenance['logs_examined'],3)

    def test_snapshot_timestamp_is_an_exact_bounded_integer_and_failed_read_recovers(self):
        for value in (114.0,True,-1,1<<63):
            with self.subTest(timestamp=value):
                with self.assertRaises(HistoryError):self.read(timestamp=value)
        self.assertEqual(self.read().claims[7,ZERO],(0,20))


if __name__=='__main__':unittest.main()
