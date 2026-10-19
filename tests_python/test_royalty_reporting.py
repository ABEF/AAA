"""Currency-isolated reporting and conversion/claim separation; no network."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from frontend_api.history import ROYALTY_CONVERTED, HistoryError
from frontend_api.service import Projection, ProjectionError, ZERO
from indexer.monitor import Indexer
from tests_python.test_frontend_api import MockRPC, configuration, addr, words, native_claim_data
from tests_python.test_frontend_history import HistoryRPC, h, topic
from tests_python.test_frontend_lineage import LineageRPC, h as lh
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError, WorkLimit


def native_data(signature, *args):
    return calldata(signature, *args[:-1], addr(1))[:-64] + '0' * 64


def profile(config, rpc, *, ledger=addr(5), controller=addr(1), converter=True):
    cfg = copy.deepcopy(config)
    candidate = addr(90)
    code = '0x600190'
    cfg['royalty_reporting'] = {'schema': 1, 'converter': {
        'address': candidate, 'code_hash': '0x' + keccak256(bytes.fromhex(code[2:])).hex()} if converter else None}
    rpc.codes[candidate] = code
    def put(target, signature, args, values):
        data = native_data(signature, *args) if args and args[-1] == ZERO and signature in ('eligibleCount(address)', 'eligibleFor(uint256,address)') else calldata(signature, *args)
        rpc.responses[target, data] = words(*values)
    put(ledger, 'canonicalController()', (), (controller,))
    put(ledger, 'converter()', (), (candidate if converter else ZERO,))
    put(ledger, 'activationCount()', (), (5,))
    put(ledger, 'activationOrdinal(uint256)', (rpc.nft_id,), (3,))
    for asset in (ZERO, addr(21)):
        put(ledger, 'eligibleCount(address)', (asset,), (5,))
        put(ledger, 'eligibleFor(uint256,address)', (rpc.nft_id, asset), (1,))
    for sig, result in (('access()', controller), ('ledger()', ledger), ('enabled()', 1), ('MAX_LOSS_BPS()', 100)):
        put(candidate, sig, (), (result,))
    return cfg


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.rpc = MockRPC()
        self.cfg = profile(configuration(), self.rpc)
        self.p = Projection(self.cfg, self.rpc, clock=lambda: 1000)

    def read(self): return self.p.nft(str(self.rpc.nft_id))

    def test_native_eth_and_unconverted_currency_are_not_summed_or_promised(self):
        result = self.read()
        eth, stable = result['claimable']['royalties']
        self.assertEqual(eth['raw'], '33333333333333333333')
        self.assertIsNone(eth['unconverted_raw'])
        self.assertEqual(stable['unconverted_raw'], '25000001')
        self.assertTrue(stable['eligible']); self.assertEqual(stable['eligibility'], 'eligible')
        self.assertTrue(result['royalty_reporting']['balances_complete'])
        self.assertTrue(result['royalty_reporting']['converter']['enabled'])
        self.assertIsNone(result['royalty_reporting']['converter']['next_execution_at'])
        self.assertFalse(result['royalty_conversions']['available'])
        self.assertFalse(result['previously_claimed']['available'])
        self.assertIn('fees_all_time', result['unavailable_metrics'])

    def test_deferred_currency_eligibility_is_distinct_from_activation(self):
        self.rpc.put(addr(5), 'eligibleCount(address)', (addr(21),), (2,))
        self.rpc.put(addr(5), 'eligibleFor(uint256,address)', (self.rpc.nft_id, addr(21)), (0,))
        self.rpc.put(addr(5), 'claimable(uint256,address)', (self.rpc.nft_id, addr(21)), (0,))
        before = self.read()
        self.assertTrue(before['position']['activated'])
        self.assertEqual(before['claimable']['royalties'][1]['eligibility'], 'deferred')
        self.rpc.put(addr(5), 'eligibleCount(address)', (addr(21),), (5,))
        self.rpc.put(addr(5), 'eligibleFor(uint256,address)', (self.rpc.nft_id, addr(21)), (1,))
        self.assertEqual(self.read()['claimable']['royalties'][1]['eligibility'], 'eligible')

    def test_faulty_balance_returns_null_without_losing_healthy_rewards(self):
        original = self.rpc.call
        broken = calldata('claimable(uint256,address)', self.rpc.nft_id, addr(21))
        def fail(method, args):
            if method == 'eth_call' and args[0]['to'] == addr(5) and args[0]['data'] == broken:
                raise RpcError('SECRET provider URL credentials')
            return original(method, args)
        with patch.object(self.rpc, 'call', side_effect=fail): result = self.read()
        stable = result['claimable']['royalties'][1]
        self.assertFalse(stable['available']); self.assertIsNone(stable['raw']); self.assertIsNone(stable['unconverted_raw'])
        self.assertTrue(stable['eligible']); self.assertFalse(result['royalty_reporting']['balances_complete'])
        self.assertTrue(result['claimable']['royalties'][0]['available'])
        self.assertTrue(result['claimable']['lp'][1]['available'])
        self.assertNotIn('SECRET', json.dumps(result))

    def test_bad_token_pin_or_decimals_hides_only_that_currency(self):
        for mutate in (lambda: self.rpc.codes.update({addr(21): '0x6000'}),
                       lambda: self.rpc.put(addr(21), 'decimals()', values=(18,))):
            self.setUp(); mutate(); result = self.read()
            self.assertEqual(result['claimable']['royalties'][1]['reason'], 'asset_verification_unavailable')
            self.assertFalse(result['claimable']['lp'][1]['available'])
            self.assertTrue(result['claimable']['lp'][0]['available'])
            self.assertTrue(result['claimable']['royalties'][0]['available'])

    def test_old_profile_keeps_strict_fail_closed_asset_validation(self):
        self.rpc.codes[addr(21)] = '0x6000'
        p = Projection(configuration(), self.rpc, clock=lambda: 1000)
        with self.assertRaises(ProjectionError): p.nft(str(self.rpc.nft_id))

    def test_work_limits_are_not_swallowed_as_currency_or_converter_failures(self):
        original = self.rpc.call
        for target, sig in ((addr(21), 'decimals()'), (addr(5), 'claimable(uint256,address)'), (addr(90), 'enabled()')):
            def fail(method, args):
                if method == 'eth_call' and args[0]['to'] == target and args[0]['data'].startswith(calldata(sig, *([self.rpc.nft_id, addr(21)] if sig.startswith('claimable') else []))[:10]):
                    raise WorkLimit('rpc_budget')
                return original(method, args)
            with patch.object(self.rpc, 'call', side_effect=fail), self.assertRaises(WorkLimit): self.read()

    def test_broken_core_identity_or_eligibility_is_not_a_partial_success(self):
        for sig, args, values in (('canonicalController()', (), (addr(9),)),
                                  ('activationCount()', (), (1001,)),
                                  ('activationOrdinal(uint256)', (self.rpc.nft_id,), (0,)),
                                  ('eligibleCount(address)', (addr(21),), (6,)),
                                  ('eligibleFor(uint256,address)', (self.rpc.nft_id, addr(21)), (2,))):
            self.setUp(); self.rpc.put(addr(5), sig, args, values)
            with self.assertRaises(ProjectionError): self.read()

    def test_converter_missing_disabled_drift_never_promises_conversion(self):
        self.rpc.put(addr(90), 'enabled()', values=(0,))
        self.assertFalse(self.read()['royalty_reporting']['converter']['enabled'])
        self.rpc.codes[addr(90)] = '0x6000'
        self.assertFalse(self.read()['royalty_reporting']['converter']['available'])
        self.rpc.put(addr(5), 'converter()', values=(ZERO,))
        self.assertEqual(self.read()['royalty_reporting']['converter']['reason'], 'converter_not_bound')
        self.rpc.put(addr(5), 'converter()', values=(addr(91),))
        self.assertEqual(self.read()['royalty_reporting']['converter']['reason'], 'converter_pin_missing_or_mismatched')

    def test_reorg_and_expiry_discard_even_currency_isolated_results(self):
        self.rpc.reorg_after_calls = True
        with self.assertRaises(ProjectionError): self.read()
        self.rpc.reorg_after_calls = False
        original = self.p.royalty_reporting.read
        def expire(*args):
            value = original(*args); self.p.clock = lambda: 2000; return value
        with patch.object(self.p.royalty_reporting, 'read', side_effect=expire), self.assertRaises(RpcError): self.read()

    def test_reporting_config_strict_and_no_implicit_old_abi_probe(self):
        for value in ({'schema': 2, 'converter': None}, {'schema': True, 'converter': None},
                      {'schema': 1, 'converter': None, 'rpc_url': 'SECRET'},
                      {'schema': 1, 'converter': {'address': addr(2), 'code_hash': '0x' + '1' * 64}}):
            cfg = configuration(); cfg['royalty_reporting'] = value
            with self.assertRaises(ValueError): Projection(cfg, self.rpc)
        self.assertFalse(Projection(configuration(), self.rpc, clock=lambda: 1000).nft(str(self.rpc.nft_id))['royalty_reporting']['available'])

    def test_dormant_nft_is_inactive_without_fabricated_royalty_entitlement(self):
        i = self.rpc.nft_id
        for target, sig, value in ((2, 'traitsReady(uint256)', 0), (3, 'nftStatus(uint256)', 5),
                                   (3, 'nftBucket(uint256)', 0), (3, 'sharesOf(uint256)', 0),
                                   (5, 'weightOf(uint256)', 0), (5, 'activationOrdinal(uint256)', 0)):
            self.rpc.put(addr(target), sig, (i,), (value,))
        self.rpc.put(addr(2), 'currentLPValue(uint256)', (i,), (1, 0))
        for target, assets in ((4, [addr(20), addr(21)]), (5, [ZERO, addr(21)])):
            for asset in assets: self.rpc.put(addr(target), 'claimable(uint256,address)', (i, asset), (0,))
        for asset in (ZERO, addr(21)):
            data = native_data('eligibleFor(uint256,address)', i, asset) if asset == ZERO else calldata('eligibleFor(uint256,address)', i, asset)
            self.rpc.responses[addr(5), data] = words(0)
        result = self.read()
        self.assertFalse(result['position']['activated'])
        self.assertTrue(all(a['eligibility'] == 'inactive' and a['raw'] == '0' for a in result['claimable']['royalties']))

    def test_same_snapshot_ownership_change_preserves_unclaimed_rights(self):
        before = self.read()
        self.rpc.put(addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (addr(31),))
        after = self.read()
        self.assertEqual(after['owner'], addr(31))
        self.assertEqual(before['claimable'], after['claimable'])
        self.assertEqual(before['royalty_reporting'], after['royalty_reporting'])


class ConversionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.rpc = HistoryRPC()
        self.cfg = configuration()
        self.cfg['history'] = {'database': str(Path(self.temp.name)/'index.sqlite'), 'start_block': 10,
            'start_parent_hash': h(9), 'contracts': [addr(2), addr(4), addr(5)], 'max_events': 1000}
        index_cfg = dict(self.cfg['history'], chain_id=31337, rpc_urls=['http://127.0.0.1:8545'], confirmations=12,
                         block_chunk=200, max_reorg_depth=100, poll_seconds=1)
        index_cfg.pop('max_events')
        self.index = Indexer(index_cfg, self.rpc); self.index.step()
        self.p = Projection(self.cfg, self.rpc, clock=lambda: 1000)

    def tearDown(self): self.index.close(); self.temp.cleanup()

    def insert(self, block=50, index=0, emitter=None, token=None, source=None, amount=100, native=2, topics=None, data=None):
        log = self.rpc.raw(block, index, emitter or addr(5),
            topics or [ROYALTY_CONVERTED, topic(token or self.rpc.nft_id), topic(source or addr(21))],
            data if data is not None else words(amount, native))
        with self.index.db:
            self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)', (31337,block,log['blockHash'],
                log['transactionHash'],index,log['address'],'Claimed','{"amount":"999999999"}',json.dumps(log)))

    def read(self): return self.p.nft(str(self.rpc.nft_id))

    def test_conversion_separate_from_claims_income_and_other_nfts(self):
        before = self.read(); self.insert(); self.insert(block=51, amount=25, native=1)
        self.insert(block=52, token=self.rpc.other, amount=900, native=7)
        result = self.read(); report = result['royalty_conversions']
        self.assertEqual(result['previously_claimed']['assets'], before['previously_claimed']['assets'])
        self.assertEqual(result['claimable'], before['claimable'])
        self.assertEqual(report['total_eth_credited_raw'], '3')
        self.assertEqual(report['assets'][0]['source_converted_raw'], '125')
        self.assertEqual(report['assets'][0]['event_count'], 2)
        self.assertEqual(report['assets'][0]['last_event']['timestamp'], 942)
        self.assertIn('fees_all_time', result['unavailable_metrics'])

    def test_only_actual_later_claim_increases_previously_claimed(self):
        self.insert(); before = self.read()
        log = self.rpc.raw(51, 0, addr(5), [
            '0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex(), topic(self.rpc.nft_id),topic(ZERO),topic(addr(30))],words(2))
        with self.index.db:
            self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',(31337,51,log['blockHash'],log['transactionHash'],0,addr(5),None,None,json.dumps(log)))
        result=self.read(); eth=next(a for a in result['previously_claimed']['assets'] if a['asset']==ZERO)
        self.assertEqual(eth['royalties_raw'], '9')
        self.assertEqual(result['royalty_conversions'],before['royalty_conversions'] | {'provenance': result['royalty_conversions']['provenance']})

    def test_wrong_emitter_cannot_create_conversion_credit(self):
        self.insert(emitter=addr(4))
        self.assertEqual(self.read()['royalty_conversions']['total_eth_credited_raw'], '0')

    def test_zero_rounding_credits_are_valid_not_additional_income(self):
        self.insert(amount=0,native=0); self.insert(block=51,amount=1,native=0)
        self.assertEqual(self.read()['royalty_conversions']['total_eth_credited_raw'], '0')

    def test_invalid_currency_id_topics_amounts_rejected(self):
        bad = [dict(source=ZERO), dict(source=addr(20)), dict(token=123), dict(amount=0,native=1),
               dict(data=words(100)), dict(topics=[ROYALTY_CONVERTED,topic(self.rpc.nft_id),topic(addr(21)),topic(addr(30))])]
        for mutation in bad:
            self.insert(**mutation)
            with self.subTest(mutation=mutation), self.assertRaises(HistoryError): self.read()
            with self.index.db: self.index.db.execute('DELETE FROM logs WHERE block_number=50')

    def test_missing_coverage_is_unavailable_not_zero_conversion(self):
        self.insert()
        with self.index.db: self.index.db.execute('DELETE FROM blocks WHERE number=50')
        with self.assertRaises(HistoryError): self.read()


class ConversionLineageTests(unittest.TestCase):
    def test_two_handoffs_preserve_conversions_without_duplication_or_inherited_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            rpc=LineageRPC(Path(temp))
            try:
                for i,block in enumerate((15,45,80)):
                    emitter=addr(5+100*i)
                    log=rpc.raw(emitter,block,10,[ROYALTY_CONVERTED,words(rpc.nft_id),words(addr(21))],words(100*(i+1),i+1))
                    with rpc.indexes[i].db:
                        rpc.indexes[i].db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                            (31337,block,log['blockHash'],log['transactionHash'],10,emitter,None,None,json.dumps(log)))
                cfg=profile(rpc.config,rpc,ledger=addr(205),controller=addr(201),converter=False)
                p=Projection(cfg,rpc,clock=lambda:1000)
                result=p.nft(str(rpc.nft_id))
                self.assertEqual(result['royalty_conversions']['total_eth_credited_raw'],'6')
                self.assertEqual(result['royalty_conversions']['assets'][0]['source_converted_raw'],'600')
                eth=next(a for a in result['previously_claimed']['assets'] if a['asset']==ZERO)
                self.assertEqual(eth['royalties_raw'],'120')
                self.assertEqual(result['royalty_conversions']['assets'][0]['last_event']['ledger'],addr(205))
                self.assertTrue(all(e.projection.royalty_reporting is None for e in p.lineage.entries))
                del cfg['predecessors']
                missing=Projection(cfg,rpc,clock=lambda:1000).nft(str(rpc.nft_id))
                self.assertFalse(missing['royalty_conversions']['available'])
                self.assertIsNone(missing['royalty_conversions']['total_eth_credited_raw'])
            finally: rpc.close()

    def test_old_conversion_currency_survives_absence_from_current_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            rpc = LineageRPC(Path(temp))
            try:
                log = rpc.raw(addr(5), 15, 10, [ROYALTY_CONVERTED, words(rpc.nft_id), words(addr(21))], words(123, 7))
                with rpc.indexes[0].db:
                    rpc.indexes[0].db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                        (31337,15,log['blockHash'],log['transactionHash'],10,addr(5),None,None,json.dumps(log)))
                cfg = copy.deepcopy(rpc.config)
                cfg['assets'] = [a for a in cfg['assets'] if a['address'] != addr(21)]
                rpc.put(addr(204), 'assetCount()', 1); rpc.put(addr(205), 'assetCount()', 1)
                result = Projection(cfg, rpc, clock=lambda: 1000).nft(str(rpc.nft_id))
                self.assertEqual(result['royalty_conversions']['total_eth_credited_raw'], '7')
                self.assertEqual(result['royalty_conversions']['assets'][0]['asset'], addr(21))
                self.assertEqual(result['royalty_conversions']['assets'][0]['decimals'], 6)
            finally: rpc.close()


if __name__ == '__main__': unittest.main()
