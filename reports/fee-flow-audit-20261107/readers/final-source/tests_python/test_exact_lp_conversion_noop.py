"""Valid zero rows in funded LP conversions retain exact reader semantics."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.history import History, HistoryError, ZERO
from tests_python.test_exact_lp_backend import Feed, IDS, OTHER, OWNER, ROLES, ZZZ
from zzz_ops.abi import keccak256


CONVERTED = 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)'


def prepared():
    feed = Feed()
    for identifier in IDS:
        feed.mint(identifier)
    feed.activate(IDS[0], 101)
    feed.fees(ZZZ)
    return feed


def conversion(feed, identifier, amounts, source=ZZZ):
    return feed.emit('rewards', CONVERTED, [identifier, source], amounts)


def financial_state(model):
    return copy.deepcopy((model.owner_trees[7].__dict__, model.collective_tree.__dict__,
                          model.direct, model.account_totals, model.totals, model.day,
                          model.shares, model.members, model.weights))


class RecordingFeed(Feed):
    def __init__(self):
        self.logs = []
        super().__init__()

    def emit(self, role, signature, indexed, data):
        result = super().emit(role, signature, indexed, data)
        self.logs.append(dict(result, address=self.roles[role], removed=False,
            blockNumber='0x1', blockHash='0x'+'aa'*32,
            transactionHash='0x'+f'{self.tx:064x}', logIndex=hex(self.index)))
        return result


class ExactLPConversionNoopTests(unittest.TestCase):
    def test_mixed_funded_and_dormant_rows_preserve_books_and_income(self):
        feed = prepared()
        earned = copy.deepcopy(feed.model.account_totals)
        conversion(feed, IDS[0], [16, 2, 8, 1])
        before = financial_state(feed.model)
        conversion(feed, IDS[1], [0, 0, 0, 0])
        self.assertEqual(before, financial_state(feed.model))
        self.assertEqual(earned, feed.model.account_totals)
        self.assertEqual((8, 1), feed.model.components(IDS[0], ZERO))
        self.assertEqual((0, 0), feed.model.components(IDS[1], ZERO))
        self.assertEqual(9, feed.model.direct_liability(ZERO))
        self.assertEqual([0, 0], feed.model.owner_trees[7].outstanding)
        self.assertEqual([0, 0], feed.model.collective_tree.outstanding)
        feed.model.finish()

    def test_claimed_active_nft_can_have_zero_conversion_row(self):
        feed = prepared()
        feed.emit('rewards', 'Claimed(uint256,address,address,uint256)',
                  [IDS[0], ZZZ, OWNER], [18])
        earned = copy.deepcopy(feed.model.account_totals)
        before = financial_state(feed.model)
        conversion(feed, IDS[0], [0, 0, 0, 0])
        self.assertEqual(before, financial_state(feed.model))
        self.assertEqual(earned, feed.model.account_totals)
        self.assertEqual(0, feed.model.direct_liability(ZERO))

    def test_zero_source_cannot_credit_either_native_component(self):
        for amounts in ([0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 1, 1]):
            with self.subTest(amounts=amounts):
                feed = prepared()
                before = financial_state(feed.model)
                with self.assertRaises(HistoryError):
                    conversion(feed, IDS[1], amounts)
                self.assertEqual(before, financial_state(feed.model))

    def test_funded_row_cannot_credit_an_empty_source_component(self):
        feed = Feed()
        for identifier in IDS:
            feed.mint(identifier)
        feed.activate(IDS[0], 101, 7)
        feed.activate(IDS[1], 101, 8)
        feed.fees(ZZZ, 7)
        self.assertEqual((0, 1), feed.model.components(IDS[1], ZZZ))
        before = financial_state(feed.model)
        with self.assertRaisesRegex(HistoryError, 'empty source component'):
            conversion(feed, IDS[1], [0, 1, 1, 0])
        self.assertEqual(before, financial_state(feed.model))
        conversion(feed, IDS[1], [0, 1, 0, 1])
        self.assertEqual((0, 1), feed.model.components(IDS[1], ZERO))

    def test_positive_source_can_round_to_zero_native_without_new_income(self):
        feed = prepared()
        before = copy.deepcopy(feed.model.account_totals)
        conversion(feed, IDS[0], [16, 2, 0, 0])
        self.assertEqual(before, feed.model.account_totals)
        self.assertEqual((0, 0), feed.model.components(IDS[0], ZZZ))
        self.assertEqual((0, 0), feed.model.components(IDS[0], ZERO))
        self.assertEqual(0, feed.model.direct_liability(ZERO))

    def test_noop_requires_minted_nft_and_deployment_source(self):
        for identifier, source in ((IDS[1]+1, ZZZ), (IDS[1], ZERO), (IDS[1], OTHER)):
            with self.subTest(identifier=identifier, source=source):
                with self.assertRaises(HistoryError):
                    conversion(prepared(), identifier, [0, 0, 0, 0], source)

    def test_noop_cannot_hide_a_nonzero_unconverted_entitlement(self):
        with self.assertRaisesRegex(HistoryError, 'changed source rights'):
            conversion(prepared(), IDS[0], [0, 0, 0, 0])

    def test_noop_rejects_malformed_topics_and_data(self):
        for topics_count, words in ((1, 4), (3, 4), (2, 3), (2, 5)):
            with self.subTest(topics_count=topics_count, words=words):
                feed = prepared()
                topics = ['0x'+keccak256(CONVERTED.encode()).hex(),
                          '0x'+f'{IDS[1]:064x}', '0x'+f'{int(ZZZ,16):064x}']
                if topics_count == 1:
                    topics = topics[:2]
                elif topics_count == 3:
                    topics += ['0x'+'00'*32]
                with self.assertRaises(HistoryError):
                    feed.model(ROLES['rewards'], topics, '0x'+'0'*(64*words),
                               1, '0x'+'aa'*32, 100, '0x'+f'{feed.tx:064x}', feed.index+1)

    def test_noop_retains_retirement_and_timestamp_guards(self):
        for retired, timestamp in ((True, 100), (False, 99), (False, 10001)):
            with self.subTest(retired=retired, timestamp=timestamp):
                feed = prepared()
                feed.model.retired = retired
                raw = '0x'+'0'*(64*4)
                topics = ['0x'+keccak256(CONVERTED.encode()).hex(),
                          '0x'+f'{IDS[1]:064x}', '0x'+f'{int(ZZZ,16):064x}']
                with self.assertRaises(HistoryError):
                    feed.model(ROLES['rewards'], topics, raw, 1, '0x'+'aa'*32,
                               timestamp, '0x'+f'{feed.tx:064x}', feed.index+1)

    def test_noop_retains_same_transaction_funding_acknowledgment(self):
        feed = prepared()
        feed.tx += 1
        feed.emit('rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)',
                  [7, ZZZ], [16, 2])
        feed.tx += 1
        with self.assertRaisesRegex(HistoryError, 'crossed transactions'):
            conversion(feed, IDS[1], [0, 0, 0, 0])

    def test_history_and_exact_replay_keep_transferred_owner_claim_and_no_new_income(self):
        feed = RecordingFeed()
        for identifier in IDS:
            feed.mint(identifier)
        feed.activate(IDS[0], 101)
        feed.fees(ZZZ)
        earned = copy.deepcopy(feed.model.account_totals)
        conversion(feed, IDS[0], [16, 2, 8, 1])
        conversion(feed, IDS[1], [0, 0, 0, 0])
        feed.tx += 1
        feed.emit('nft', 'Transfer(address,address,uint256)', [OWNER, OTHER, IDS[0]], [])
        feed.emit('rewards', 'Claimed(uint256,address,address,uint256)',
                  [IDS[0], ZERO, OTHER], [9])
        feed.model.finish()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'history.sqlite'
            config = dict(database=str(path), start_block=1,
                start_parent_hash='0x'+'bb'*32, contracts=sorted(ROLES.values()), max_events=100)
            with closing(sqlite3.connect(path)) as database, database:
                database.execute('CREATE TABLE cursors(chain INTEGER,next_block INTEGER,config TEXT)')
                database.execute('CREATE TABLE blocks(chain INTEGER,number INTEGER,hash TEXT,parent TEXT,timestamp INTEGER)')
                database.execute('CREATE TABLE logs(chain INTEGER,block_number INTEGER,block_hash TEXT,transaction_hash TEXT,log_index INTEGER,address TEXT,raw TEXT)')
                database.execute('INSERT INTO cursors VALUES(?,?,?)', (31337, 2,
                    json.dumps(dict(contracts=config['contracts'], start=1, parent_hash=config['start_parent_hash']))))
                database.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                    (31337, 1, '0x'+'aa'*32, config['start_parent_hash'], 100))
                for log in feed.logs:
                    database.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?)',
                        (31337, 1, log['blockHash'], log['transactionHash'],
                         int(log['logIndex'],16), log['address'], json.dumps(log)))
            history = History(config, chain_id=31337, nft=ROLES['nft'],
                              rewards=ROLES['rewards'], royalties=ROLES['royalties'])
            model = ExactReplay(10000, selected=IDS)
            model.begin(ROLES, [ZERO, ZZZ], [ZERO], fee_intake_version=1, royalty_settlement_version=4)
            result = history.read(block_number=1, block_hash='0x'+'aa'*32, block_timestamp=100,
                minted_count=2, lp_assets={ZERO, ZZZ}, royalty_assets={ZERO}, consumer=model,
                extra_emitters=tuple(ROLES.values()))
            model.finish()
        self.assertEqual(OTHER, result.owners[IDS[0]])
        self.assertEqual((9, 0), result.claims[IDS[0], ZERO])
        self.assertEqual((18, 9), result.lp_conversions[IDS[0], ZZZ][:2])
        self.assertEqual((0, 0), result.lp_conversions[IDS[1], ZZZ][:2])
        self.assertEqual(2, result.provenance['lp_conversion_events'])
        self.assertEqual(earned, model.account_totals)
        self.assertEqual((0, 0), model.components(IDS[0], ZERO))
        self.assertEqual(0, model.direct_liability(ZERO))


if __name__ == '__main__':
    unittest.main()
