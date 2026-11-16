"""Reviewed prefix import: controlled histories, no transactions or live RPC.

The existing EpochFixture supplies explicit accounting7/mint2 observations.
Projection, canonical receipt/header checks, SQLite History, exact replay and
checkpoint codecs/builders are real. Getter/lifecycle truths are synthetic and
partly derived from full replay; this is not V10 EVM/provider qualification.
Only this module's new methods execute; old fixture helpers are reused.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from frontend_api.earnings_checkpoint import decode, encode
from frontend_api.earnings_checkpoint_build import BuildBudget, build, publish_candidate
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection
from tests_python.test_earnings_checkpoint_lineage import EpochFixture, digest
from tests_python.test_frontend_api import addr, words
from zzz_ops.abi import keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import request_scope


def prefix_configuration(fixture, last):
    cfg = copy.deepcopy(fixture.configs[last])
    if last:
        cfg['predecessors'] = copy.deepcopy(fixture.config['predecessors'][:last])
    cfg['earnings_history'] = dict(schema=1, deployments=copy.deepcopy(fixture.profiles[:last+1]), prices=None)
    return cfg


def approved_prefix(fixture, last=0, number=46, name='approved-prefix.json'):
    # Build the old graph at a head before its next handoff. The full fixture
    # already contains later rows, but canonical reads/replay remain cutoff-bound.
    safe = fixture.edges[last]-20
    with patch.object(fixture, 'safe', safe), patch.object(fixture, 'head', safe+11):
        engine = fixture.projection(prefix_configuration(fixture, last)).earnings_history
        raw = build(engine, number)
    path = fixture.root/name
    pin = publish_candidate(path, raw)
    return dict(path=str(path), sha256=pin), raw


def repin(fixture, document, name):
    raw = (json.dumps(document, sort_keys=True, separators=(',', ':'))+'\n').encode()
    path = fixture.root/name
    return dict(path=str(path), sha256=publish_candidate(path, raw)), raw


class EarningsCheckpointPrefixImportTests(unittest.TestCase):
    def fixture(self, count=3):
        fixture = EpochFixture(self, count)
        historical_verify = fixture.verify
        def verify(projection, block, allow_locked=False):
            result = historical_verify(projection, block, allow_locked)
            # The historical fixture simplifies this field to an address. New
            # import tests use the actual lifecycle reader's chain/vault shape.
            result['origin'] = dict(chain_id=projection.chain,
                                    vault=fixture.configs[0]['contracts']['vault']['address'])
            return result
        current = patch.object(Projection, '_verify_deployment', verify)
        current.start(); self.addCleanup(current.stop)
        return fixture

    def prepare(self, fixture, prefix, number=161, **kwargs):
        # Deferred so exact baseline-source execution can prove that the import
        # capability was absent, without changing any application file.
        from frontend_api.earnings_checkpoint_import import prepare
        engine = fixture.projection().earnings_history
        self.assertIsNone(engine.checkpoint)
        original = Path(prefix['path']).read_bytes()
        writes = tuple(index.db.total_changes for index in fixture.indexes)
        raw, review = prepare(engine, number, prefix, **kwargs)
        self.assertIs(type(raw), bytes)
        self.assertIs(type(review), bytes)
        data, audit = json.loads(raw), json.loads(review)
        self.assertEqual(3, data['schema'])
        self.assertIsInstance(audit, dict)
        self.assertIn(prefix['sha256'], json.dumps(audit, sort_keys=True))
        self.assertIn(hashlib.sha256(raw).hexdigest(), json.dumps(audit, sort_keys=True))
        self.assertEqual(prefix['sha256'], data['previous_sha256'])
        self.assertIsNone(engine.checkpoint)
        self.assertEqual(original, Path(prefix['path']).read_bytes())
        self.assertEqual(writes, tuple(index.db.total_changes for index in fixture.indexes))
        return raw, review

    def install(self, fixture, raw, name='new-graph-checkpoint.json'):
        path = fixture.root/name
        pin = publish_candidate(path, raw)
        fixture.config['earnings_history']['checkpoint'] = dict(path=str(path), sha256=pin)
        return path

    def equal_reports(self, fixture):
        seeded = fixture.projection(); full = fixture.projection(fixture.full_config())
        for identifier in (None, *map(str, fixture.ids)):
            a, b = seeded.earnings(identifier), full.earnings(identifier)
            for key in ('all_time', 'last_24h', 'window', 'event_count'):
                self.assertEqual(a[key], b[key], (identifier, key))
        wallet = fixture.owners(len(fixture.configs)-1, fixture.safe)[fixture.ids[0]]
        a = seeded.wallet_earnings(wallet, fixture.safe)
        b = full.wallet_earnings(wallet, fixture.safe)
        for key in ('all_time', 'last_24h', 'window', 'event_count', 'token_ids'):
            self.assertEqual(a[key], b[key], key)

    def test_original_exact_checkpoint_two_extends_without_flattening_its_raw_state(self):
        f = self.fixture(); prefix, original = approved_prefix(f)
        old = decode(json.loads(original)['state'])
        self.assertTrue(any(sum(v) for v in old['exact_lp']['direct'].values()))
        self.assertTrue(any(hi or lo for tree in old['exact_lp']['owner_trees'].values()
                            for book in tree['carry'] for hi, lo in book.values()))
        raw, _ = self.prepare(f, prefix, 46)
        data = json.loads(raw); state = decode(data['state'])
        self.assertEqual(0, state['cursor'])
        self.assertEqual(old['exact_lp'], state['active']['exact_lp'])
        self.assertEqual(old['accounts'], state['active']['accounts'])
        self.assertEqual(old['collection'], state['active']['collection'])
        self.install(f, raw); self.equal_reports(f)

    def test_shorter_graph_three_extends_and_preserves_completed_local_books(self):
        f = self.fixture(); prefix, original = approved_prefix(f, 1, 161)
        old = decode(json.loads(original)['state'])
        self.assertEqual(1, old['cursor']); self.assertEqual(1, len(old['completed']))
        raw, _ = self.prepare(f, prefix, 161)
        state = decode(json.loads(raw)['state'])
        self.assertEqual(old['active']['exact_lp'], state['active']['exact_lp'])
        self.assertEqual(old['active']['accounts'], state['active']['accounts'])
        for old_book, new_book in zip(old['completed'], state['completed']):
            for field in ('owners', 'claims', 'conversions', 'lp_conversions'):
                self.assertEqual(old_book['history'][field], new_book['history'][field])
        self.install(f, raw); self.equal_reports(f)

    def test_import_avoids_old_raw_prefix_but_keeps_suffix_event_limits(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        f.config['predecessors'][0]['history']['max_events'] = 1
        suffix = sum(161 < int(row['blockNumber'], 16) <= f.edges[1] for row in f.rows[1])
        f.config['predecessors'][1]['history']['max_events'] = suffix
        with self.assertRaisesRegex(HistoryError, 'bound exceeded'):
            build(f.projection().earnings_history, 161)
        raw, _ = self.prepare(f, prefix, 250)
        self.install(f, raw); f.extend(399)
        self.assertTrue(f.projection().earnings(str(f.ids[0]))['available'])
        f.config['predecessors'][1]['history']['max_events'] = suffix-1
        # The imported checkpoint is already beyond that old suffix; a new
        # independent import must still refuse its insufficient replay budget.
        f.config['earnings_history'].pop('checkpoint')
        with self.assertRaisesRegex(HistoryError, 'bound exceeded'):
            self.prepare(f, prefix, 250)

    def test_forward_import_replays_new_events_and_full_day_after_handoffs(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        raw, _ = self.prepare(f, prefix, 250)
        self.install(f, raw); f.extend(399)
        for asset in f.pair:
            old = len(f.rows[-1]); f.fees(2, asset, 350, 2)
            for row in f.rows[-1][old:]: f.append(2, row)
        self.equal_reports(f)
        result = f.projection().earnings()
        self.assertTrue(any(int(row['lp_processed_raw']) > 0 for row in result['last_24h']))

    def test_import_does_not_bypass_the_complete_rolling_day_requirement(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        raw, _ = self.prepare(f, prefix, 250)
        self.install(f, raw)
        with self.assertRaisesRegex(HistoryError, 'rolling day|complete.*day|86400'):
            f.projection().earnings(str(f.ids[0]))

    def test_wrong_digest_and_changed_semantic_source_are_rejected(self):
        f = self.fixture(); prefix, raw = approved_prefix(f)
        bad = dict(prefix, sha256='0'*64)
        with self.assertRaises(HistoryError): self.prepare(f, bad)
        data = json.loads(raw); data['sources']['frontend_api/earnings.py'] = '0'*64
        bad, _ = repin(f, data, 'wrong-sources.json')
        with self.assertRaises(HistoryError): self.prepare(f, bad)

    def test_indexed_fractional_format_cannot_be_relabelled_into_exact_import(self):
        f = self.fixture(); _, raw = approved_prefix(f)
        for value in (1, True, '2', 4):
            data = json.loads(raw); data['schema'] = value
            prefix, _ = repin(f, data, 'wrong-schema-'+str(value)+'.json')
            with self.subTest(schema=value), self.assertRaises(HistoryError):
                self.prepare(f, prefix)

    def test_input_graph_must_be_a_strict_prefix_not_equal_or_unrelated(self):
        f = self.fixture(); raw = f.candidate(161)
        path = f.root/'already-full-graph.json'
        prefix = dict(path=str(path), sha256=publish_candidate(path, raw))
        with self.assertRaises(HistoryError): self.prepare(f, prefix)
        prefix, raw = approved_prefix(f, 1, 161)
        data = json.loads(raw); bound = decode(data['identity'])
        bound[0], bound[1] = bound[1], bound[0]
        data['identity'] = encode(bound)
        prefix, _ = repin(f, data, 'reordered-graph.json')
        with self.assertRaises(HistoryError): self.prepare(f, prefix)

    def test_old_current_tail_cannot_supply_an_unreviewed_retirement_transaction(self):
        f = self.fixture(); _, raw = approved_prefix(f, 1, 161)
        data = json.loads(raw); bound = decode(data['identity'])
        self.assertIsNone(bound[-1]['retirement_transaction_hash'])
        bound[-1]['retirement_transaction_hash'] = f.transition_tx(1)
        data['identity'] = encode(bound)
        prefix, _ = repin(f, data, 'forged-old-tail.json')
        with self.assertRaises(HistoryError): self.prepare(f, prefix)

    def test_prefix_asset_meaning_or_contract_runtime_cannot_be_changed(self):
        f = self.fixture(); _, raw = approved_prefix(f)
        for variant in ('asset', 'runtime'):
            data = json.loads(raw); bound = decode(data['identity'])
            if variant == 'asset': bound['assets'][f.pair[1]]['decimals'] = 6
            else: bound['contracts']['rewards']['code_hash'] = digest(8888)
            data['identity'] = encode(bound)
            prefix, _ = repin(f, data, 'wrong-identity-'+variant+'.json')
            with self.subTest(variant=variant), self.assertRaises(HistoryError):
                self.prepare(f, prefix)

    def test_appended_handoff_receipt_and_terminal_commitments_remain_required(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        tx = f.transition_tx(1); receipt = f.receipts.pop(tx)
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 250)
        f.receipts[tx] = receipt
        for row in receipt['logs']: row['data'] = words(digest(99999))
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 250)

    def test_prefix_cursor_cannot_be_relabelled_at_or_after_its_retirement(self):
        f = self.fixture(); _, raw = approved_prefix(f)
        data = json.loads(raw); anchor = decode(data['anchor']); state = decode(data['state'])
        number = f.edges[0]
        anchor.update(number=number, hash=digest(number), timestamp=f.timestamp(number))
        state['history']['provenance'].update(through_block=number, block_hash=digest(number))
        data['anchor'] = encode(anchor); data['state'] = encode(state)
        prefix, _ = repin(f, data, 'retired-cursor.json')
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 250)

    def test_requested_cursor_cannot_precede_the_approved_prefix(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 160)

    def test_prefix_reorg_or_missing_historical_suffix_block_fails_without_fallback(self):
        f = self.fixture(); prefix, _ = approved_prefix(f)
        f.reorg = 46
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 161)
        f.reorg = None
        with f.indexes[0].db: f.indexes[0].db.execute('DELETE FROM blocks WHERE number=60')
        with self.assertRaises(HistoryError): self.prepare(f, prefix, 161)

    def test_existing_current_graph_checkpoint_cannot_be_silently_replaced(self):
        from frontend_api.earnings_checkpoint_import import prepare
        f = self.fixture(); prefix, _ = approved_prefix(f)
        f.install(f.candidate(161), 'current-approved.json')
        engine = f.projection().earnings_history; prior = engine.checkpoint
        with self.assertRaises(HistoryError): prepare(engine, 250, prefix)
        self.assertIs(prior, engine.checkpoint)

    def test_explicit_and_outer_offline_work_budgets_remain_enforced(self):
        f = self.fixture(); prefix, _ = approved_prefix(f)
        with self.assertRaises(WorkLimit):
            self.prepare(f, prefix, budget=BuildBudget(calls=1, posts=1))
        with request_scope(BuildBudget(calls=1, posts=1)):
            with self.assertRaises(WorkLimit):
                self.prepare(f, prefix, budget=BuildBudget(calls=4096, posts=8192))

    def test_prepare_is_read_only_and_new_output_publication_remains_exclusive(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        names = {p.name for p in f.root.iterdir()}
        original = Path(prefix['path']).read_bytes()
        raw, review = self.prepare(f, prefix)
        self.assertEqual(names, {p.name for p in f.root.iterdir()})
        self.assertEqual(original, Path(prefix['path']).read_bytes())
        path = f.root/'new-candidate.json'; publish_candidate(path, raw)
        with self.assertRaises(FileExistsError): publish_candidate(path, raw)
        self.assertEqual(raw, path.read_bytes()); self.assertNotEqual(raw, review)

    def test_every_appended_deployment_keeps_the_exact_native_fixed_token_pair(self):
        f = self.fixture(); prefix, _ = approved_prefix(f)
        def admitted(projection, block, **kwargs):
            pair, royalties = f.admitted(projection, block, **kwargs)
            if f._epoch(projection) == 2: pair = [ZERO, addr(21)]
            return pair, royalties
        with patch.object(Projection, '_admitted', admitted), \
                self.assertRaisesRegex(HistoryError, 'principal currencies differ'):
            # Even a candidate before the appended handoffs authenticates them.
            self.prepare(f, prefix, 46)

    def test_review_manifest_pins_the_complete_graph_producer_and_false_approval(self):
        from frontend_api.earnings_checkpoint_import import producer_sources
        from frontend_api.earnings_checkpoint_v3 import graph_identity, sources
        f = self.fixture(); prefix, _ = approved_prefix(f)
        raw, review = self.prepare(f, prefix, 46)
        audit, candidate = json.loads(review), json.loads(raw)
        self.assertEqual(1, audit['schema'])
        self.assertEqual('popl-offline-checkpoint-prefix-import', audit['kind'])
        for field in ('production_approved', 'approved', 'installed', 'ready_for_submission',
                      'transactions_submitted'):
            self.assertIs(audit[field], False, field)
        self.assertIs(audit['raw_retention_required'], True)
        self.assertEqual((2, 1, 3, 0), tuple(audit[k] for k in
                         ('prefix_schema', 'prefix_graph_length', 'target_graph_length', 'imported_cursor')))
        self.assertEqual(prefix['sha256'], audit['prefix_sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), audit['checkpoint_sha256'])
        self.assertEqual(producer_sources(), audit['producer_sources'])
        self.assertEqual(sources(), audit['output_semantic_sources'])
        self.assertEqual(graph_identity(f.projection().earnings_history), audit['target_graph'])
        self.assertEqual(f.projection().identity, audit['target_configuration_sha256'])
        self.assertEqual(decode(candidate['anchor']), audit['target_anchor'])
        self.assertEqual(46, audit['input_anchor']['number'])
        self.assertEqual(f.timestamp(46)+86400, audit['earliest_served_timestamp'])
        self.assertEqual(f.safe, audit['authenticated_graph_snapshot']['number'])
        self.assertEqual(f.edges, [r['block_number'] for r in audit['appended_handoffs']])
        self.assertEqual([f.transition_tx(i) for i in range(2)],
                         [r['retirement_transaction_hash'] for r in audit['appended_handoffs']])

    def test_old_tail_can_add_a_later_royalty_descriptor_but_cannot_change_existing_meaning(self):
        f = self.fixture(); prefix, _ = approved_prefix(f, 1, 161)
        asset = addr(22); code = b'\x60\x22'
        f.codes[asset] = '0x'+code.hex(); f.birth[asset] = 0
        descriptor = dict(address=asset, symbol='LATE', decimals=18,
                          code_hash='0x'+keccak256(code).hex())
        # Only the then-current tail gains this later-reviewed descriptor. The
        # earlier retired epoch remains exact; the successor imports the book.
        updated = set()
        for config in (f.configs[1], f.configs[2], f.config['predecessors'][1], f.config):
            if id(config['assets']) not in updated:
                updated.add(id(config['assets']))
                config['assets'].append(copy.deepcopy(descriptor))
        f.late_assets.extend(((1, 200, asset), (2, f.starts[2], asset)))
        for epoch, number in ((1, 200), (2, f.starts[2])):
            row = f.emit(epoch, 'royalties', 'AssetAdded(address,uint256)', (asset,), (0,), number)
            f.append(epoch, row)
        before = len(f.rows[1]); f.royalty(1, asset, 11, 201)
        for row in f.rows[1][before:]: f.append(1, row)
        raw, _ = self.prepare(f, prefix, 250)
        state = decode(json.loads(raw)['state'])
        self.assertIn(asset, state['completed'][1]['royalty_assets'])
        self.assertIn(asset, state['active']['royalty_assets'])
        self.install(f, raw); f.extend(399); self.equal_reports(f)
        totals = f.projection().earnings()['all_time']
        self.assertEqual('11', next(row for row in totals if row['asset'] == asset)['royalties_allocated_raw'])
        amounts = [int(next(row for row in f.projection().earnings(str(identifier))['all_time']
                            if row['asset'] == asset)['royalties_raw']) for identifier in f.ids]
        self.assertEqual(11, sum(amounts)); self.assertEqual(0, amounts[2])
        f.config['earnings_history'].pop('checkpoint')
        existing = next(row for row in f.config['predecessors'][1]['assets'] if row['address'] == addr(21))
        existing['symbol'] = 'CHANGED'
        with self.assertRaisesRegex(HistoryError, 'identities changed'):
            self.prepare(f, prefix, 250)


if __name__ == '__main__':
    unittest.main()
