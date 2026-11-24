"""NEW history-only checkpoint checks; existing fixtures supply setup, never tests.

The composed checks use new temporary SQLite databases and synthetic RPC views.
They do not adopt a checkpoint, qualify hosting, or execute an old test method.
"""
import copy
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock, call, patch, sentinel

from frontend_api import earnings_checkpoint as codec
from frontend_api.earnings import Earnings
from frontend_api.earnings_checkpoint_v2 import capture
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_replay import Replay, SCALE
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import ProjectionError
from tests_python.test_earnings_checkpoints import CheckpointAPITests
from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
from tests_python.test_frontend_api import addr
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget, request_scope


class CheckpointHistorySeedTests(unittest.TestCase):
    def fixture(self, version=2):
        fixture = (Checkpoint2APITests if version == 2 else CheckpointAPITests)('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    @staticmethod
    def snapshot(engine, seed=None):
        p = engine.p
        header, _, block = p._snapshot()
        lp, royalties = p._admitted(block)
        if seed is None:
            return engine.history_snapshot(p, header, block, lp, royalties)
        return p._history_snapshot(header, block, lp, royalties, seed=seed)

    @staticmethod
    def financial_history(history):
        return {name: dict(getattr(history, name)) for name in
                ('owners', 'claims', 'conversions', 'lp_conversions')}

    def test_new_constructor_fully_rejects_accounting_before_any_history_seed(self):
        for version in (1, 2):
            f = self.fixture(version)
            original = json.loads(f.candidate())
            mutations = [lambda state: state['shared']['supply'].__setitem__(5, 999)]
            if version == 2:
                mutations += [
                    lambda state: state['exact_lp']['collective_tree']['outstanding'].__setitem__(0, 999),
                    lambda state: state['accounts'][f.i].__setitem__(('lp_individual', ZERO), SCALE + 1),
                ]
            for index, mutate in enumerate(mutations):
                document = copy.deepcopy(original)
                state = codec.decode(document['state'])
                mutate(state)
                document['state'] = codec.encode(state)
                f.install(json.dumps(document).encode(), name=f'bad-{version}-{index}.json')
                with self.subTest(version=version, mutation=index), \
                        patch.object(codec.Checkpoint, 'seed', side_effect=AssertionError('seed before validation')) as seed:
                    with self.assertRaises(HistoryError):
                        f.projection()
                    seed.assert_not_called()

    def test_new_default_seed_keeps_full_schema1_and_schema2_restore(self):
        for version in (1, 2):
            f = self.fixture(version)
            path = f.install()
            checkpoint = f.projection().earnings_history.checkpoint
            seed = checkpoint.seed()
            payload = codec.decode(json.loads(path.read_bytes())['state'])
            self.assertEqual(version, seed.schema)
            self.assertEqual(payload, seed.payload)
            self.assertEqual(checkpoint.seed(history_only=False).payload, seed.payload)
            model = (ExactReplay if version == 2 else Replay)(seed.anchor['timestamp'], track_all=True)
            model.begin(payload['emitters'], payload['lp_assets'], payload['royalty_assets'],
                        fee_intake_version=1, royalty_settlement_version=payload['shared']['royalty_settlement_version'])
            seed.restore(model)
            model.finish()
            self.assertEqual(set(payload['shared']['mints']), model.minted)
            self.assertEqual(payload['accounts'], model.accounts)
            self.assertEqual(7 if version == 2 else 100, model.account_totals[f.i]['royalties', ZERO])
            if version == 2:
                self.assertEqual(payload['exact_lp'], capture(model))

    def test_new_history_seed_has_only_local_payout_state_and_minimal_identity(self):
        for version in (1, 2):
            f = self.fixture(version)
            document = json.loads(f.candidate())
            payload = codec.decode(document['state'])
            payload['history']['provenance']['review_note'] = '\u00e9'
            document['state'] = codec.encode(payload)
            f.install(json.dumps(document, ensure_ascii=False).encode())
            checkpoint = f.projection().earnings_history.checkpoint
            full, history = checkpoint.seed(), checkpoint.seed(history_only=True)
            self.assertEqual({'history', 'lp_assets', 'royalty_assets'}, set(history.payload))
            self.assertEqual({'chain', 'history'}, set(history.bound))
            self.assertEqual({name: full.payload[name] for name in history.payload}, history.payload)
            self.assertEqual({name: full.bound[name] for name in history.bound}, history.bound)
            self.assertEqual((full.digest, full.anchor, full.schema), (history.digest, history.anchor, history.schema))
            self.assertEqual(full.history, history.history)
            self.assertIn('\u00e9'.encode(), checkpoint._history_raw)

    def test_new_actual_suffix_history_matches_full_seed_and_unseeded_replay(self):
        for version in (1, 2):
            f = self.fixture(version)
            f.install()
            f.suffix()
            engine = f.projection().earnings_history
            compact = self.snapshot(engine)
            full = self.snapshot(engine, engine.checkpoint.seed())
            config = copy.deepcopy(f.config)
            del config['earnings_history']['checkpoint']
            raw = self.snapshot(f.projection(config).earnings_history)
            self.assertEqual(full, compact)
            self.assertEqual(self.financial_history(raw), self.financial_history(compact))
            for name in ('claim_events', 'royalty_conversion_events',
                         'lp_conversion_events', 'minted_count', 'through_block', 'block_hash'):
                self.assertEqual(raw.provenance[name], compact.provenance[name])
            self.assertGreaterEqual(compact.provenance['logs_examined'], raw.provenance['logs_examined'])

    def test_new_claims_conversions_transfer_and_earned_units_remain_exact(self):
        f = self.fixture()
        f.install()
        f.suffix()
        engine = f.projection().earnings_history
        history = self.snapshot(engine)
        self.assertEqual(addr(32), history.owners[f.i])
        self.assertEqual((0, 0, 1), history.lp_conversions[f.k, addr(20)][:3])
        model = f.model()
        original = sum(model.account_totals[f.i][name, addr(20)] for name in ('lp_individual', 'lp_collective'))
        native = sum(model.account_totals[f.i][name, ZERO] for name in ('lp_individual', 'lp_collective'))
        self.assertEqual(original, history.lp_conversions[f.i, addr(20)][0])
        self.assertEqual(native + original, history.claims[f.i, ZERO][0])
        self.assertEqual(model.account_totals[f.i]['royalties', ZERO], history.claims[f.i, ZERO][1])
        seeded = engine.p.earnings(str(f.i))
        config = copy.deepcopy(f.config)
        del config['earnings_history']['checkpoint']
        raw = f.projection(config).earnings(str(f.i))
        for name in ('all_time', 'last_24h', 'event_count', 'owner'):
            self.assertEqual(raw[name], seeded[name])

    def test_new_seed_maps_and_nested_conversion_provenance_are_independent(self):
        f = self.fixture()
        f.install()
        f.suffix()
        f.install(f.candidate(47), name='advanced.json')
        checkpoint = f.projection().earnings_history.checkpoint
        before = checkpoint._history_raw
        first, other = checkpoint.seed(history_only=True), checkpoint.seed(history_only=True)
        expected = copy.deepcopy(other.payload)
        first.payload['history']['owners'].clear()
        first.payload['lp_assets'].clear()
        first.bound['history']['contracts'].clear()
        first.anchor['number'] = 0
        first.history.lp_conversions[f.i, addr(20)][3]['block_number'] = 0
        self.assertEqual(expected, other.payload)
        self.assertEqual(expected, checkpoint.seed(history_only=True).payload)
        self.assertEqual(before, checkpoint._history_raw)
        with self.assertRaises(TypeError):
            other.history.owners[1] = addr(99)
        with self.assertRaises(TypeError):
            other.history.provenance['logs_examined'] = 0

    def test_new_parallel_history_seeds_do_not_share_any_mutable_maps(self):
        f = self.fixture()
        f.install()
        checkpoint = f.projection().earnings_history.checkpoint
        with ThreadPoolExecutor(max_workers=4) as workers:
            seeds = list(workers.map(lambda _: checkpoint.seed(history_only=True), range(8)))
        for name in ('payload', 'bound', 'anchor'):
            self.assertEqual(8, len({id(getattr(seed, name)) for seed in seeds}))
        self.assertEqual(8, len({id(seed.payload['history']['owners']) for seed in seeds}))
        seeds[0].payload['history']['owners'].clear()
        self.assertTrue(all(len(seed.history.owners) == 3 for seed in seeds[1:]))

    def test_new_real_earnings_selects_history_only_then_full_and_finishes_proofs(self):
        f = self.fixture()
        f.install()
        f.suffix()
        p = f.projection()
        checkpoint = p.earnings_history.checkpoint
        with patch.object(checkpoint, 'seed', wraps=checkpoint.seed) as seed, \
                patch.object(checkpoint, 'check_anchor', wraps=checkpoint.check_anchor) as anchor, \
                patch.object(p, '_finish', wraps=p._finish) as finish:
            self.assertTrue(p.earnings(str(f.i))['available'])
        self.assertEqual([call(history_only=True), call(history_only=False)], seed.call_args_list)
        self.assertEqual(3, anchor.call_count)
        finish.assert_called_once()

    def test_new_reorg_at_final_checkpoint_anchor_refuses_the_completed_report(self):
        f = self.fixture()
        f.install()
        p = f.projection()
        checkpoint = p.earnings_history.checkpoint
        original = checkpoint.check_anchor
        calls = []
        def change(current):
            calls.append(True)
            if len(calls) == 3:
                f.rpc.reorg = 21
            return original(current)
        with patch.object(checkpoint, 'check_anchor', side_effect=change):
            with self.assertRaisesRegex(HistoryError, 'anchor'):
                p.earnings(str(f.i))
        self.assertEqual(3, len(calls))

    def test_new_final_freshness_still_rejects_after_successful_checkpoint_replay(self):
        f = self.fixture()
        f.install()
        p = f.projection()
        original = p.earnings_history.finish_checkpoint
        def expire():
            original()
            f.now += 121
        with patch.object(p.earnings_history, 'finish_checkpoint', side_effect=expire):
            with self.assertRaises((ProjectionError, WorkLimit)):
                p.earnings(str(f.i))

    def test_new_history_seed_still_authenticates_indexed_anchor(self):
        f = self.fixture()
        f.install()
        p = f.projection()
        with f.index.db:
            f.index.db.execute('UPDATE blocks SET hash=? WHERE number=21', ('0x'+'a'*64,))
        with self.assertRaisesRegex(HistoryError, 'indexed canonical anchor'):
            self.snapshot(p.earnings_history)

    def test_new_history_flag_is_strict_boolean_and_keyword_only(self):
        f = self.fixture()
        f.install()
        checkpoint = f.projection().earnings_history.checkpoint
        with patch.object(codec, '_stored_json', side_effect=AssertionError('must reject before decode')):
            for value in (None, 0, 1, '', [], {}, 'true'):
                with self.subTest(value=value), self.assertRaisesRegex(HistoryError, 'history-only selection'):
                    checkpoint.seed(history_only=value)
        with self.assertRaises(TypeError):
            checkpoint.seed(True)

    def test_new_history_decode_is_immutable_compact_and_keeps_work_deadline(self):
        f = self.fixture()
        f.install()
        checkpoint = f.projection().earnings_history.checkpoint
        self.assertIs(type(checkpoint._history_raw), bytes)
        self.assertLess(len(checkpoint._history_raw), len(checkpoint._raw))
        self.assertLessEqual(len(checkpoint._history_raw), codec.MAX_BYTES)
        with self.assertRaises(TypeError):
            checkpoint._history_raw[0] = 0
        with patch.object(codec, '_stored_json', wraps=codec._stored_json) as parser:
            checkpoint.seed(history_only=True)
        self.assertEqual([call(checkpoint._history_raw.decode('utf-8'))], parser.call_args_list)
        # A synthetic 1,000-owner codec section crosses the unchanged periodic
        # work checkpoint. This injection tests decoding, not artifact admission.
        document = json.loads(checkpoint._history_raw)
        payload = codec.decode(document['state'])
        payload['history']['owners'] = {identifier: addr(30) for identifier in range(1, 1001)}
        document['state'] = codec.encode(payload)
        raw = json.dumps(document).encode()
        tick = [0.0]
        budget = Budget(seconds=1, clock=lambda: tick[0])
        with patch.object(checkpoint, '_history_raw', raw), request_scope(budget):
            tick[0] = 2.0
            with self.assertRaises(WorkLimit):
                checkpoint.seed(history_only=True)
            tick[0] = 0.0

    def test_new_oversized_artifact_still_refuses_before_history_decode(self):
        f = self.fixture()
        path = f.install()
        with patch.object(codec, 'MAX_BYTES', len(path.read_bytes()) - 1), \
                patch.object(codec, 'decode', side_effect=AssertionError('size checked before decode')) as decode:
            with self.assertRaisesRegex(HistoryError, 'bytes differ'):
                f.projection()
        decode.assert_not_called()

    def test_new_non_none_falsey_consumer_always_selects_full_state(self):
        f = self.fixture()
        f.install()
        engine = f.projection().earnings_history
        checkpoint = engine.checkpoint
        with patch.object(engine.p, '_history_snapshot', return_value=sentinel.history) as snapshot, \
                patch.object(checkpoint, 'seed', wraps=checkpoint.seed) as seed:
            for consumer in (False, 0, [], {}):
                result = engine.history_snapshot(engine.p, sentinel.header, sentinel.block,
                    sentinel.lp, sentinel.royalties, consumer=consumer)
                self.assertIs(sentinel.history, result)
                self.assertIn('shared', snapshot.call_args.kwargs['seed'].payload)
        self.assertEqual([call(history_only=False)] * 4, seed.call_args_list)

    def test_new_lineage_dispatch_retains_its_existing_snapshot_path(self):
        engine = Earnings.__new__(Earnings)
        engine.p = SimpleNamespace(lineage=sentinel.lineage)
        engine.checkpoint = SimpleNamespace(lineage_checkpoint=True, snapshot=Mock(return_value=sentinel.history))
        result = engine.history_snapshot(engine.p, sentinel.header, sentinel.block,
                                         sentinel.lp, sentinel.royalties, consumer=sentinel.consumer)
        self.assertIs(sentinel.history, result)
        engine.checkpoint.snapshot.assert_called_once_with(engine.p, sentinel.header, sentinel.block,
            sentinel.lp, sentinel.royalties, consumer=sentinel.consumer)


if __name__ == '__main__':
    unittest.main()
