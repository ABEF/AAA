"""New prefix-import CLI and exclusive-publication boundaries, offline only.

CLI cases inject preparation/Projection and perform no network calls. Publication
cases reuse only controlled EpochFixture helpers, producing one actual imported
checkpoint3/review pair. Historical test methods are never selected or executed.
These checks do not approve adoption, archive completeness or a live provider.
"""
from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api import earnings_checkpoint_import as importer
from frontend_api.earnings_checkpoint_build import BuildBudget
from tests_python import test_earnings_checkpoint_prefix_import as fixture_helpers
from zzz_ops.errors import WorkLimit
from zzz_ops.rpc import RpcError
from zzz_ops import work_budget


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'checkpoint_prefix_import_cli_subject', ROOT/'scripts/import-earnings-checkpoint.py')
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


class CheckpointPrefixImportCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='popl-prefix-cli-test-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.config = self.root/'reviewed-config.json'
        self.prefix = self.root/'reviewed-prefix.json'
        self.output = self.root/'candidate.json'
        self.review_output = self.root/'import-review.json'
        self.config_bytes = json_bytes({'earnings_history': {'schema': 1}, 'note': 'Revue étudiée'})
        self.config.write_bytes(self.config_bytes)
        self.prefix.write_bytes(b'reviewed immutable prefix\n')
        self.prefix_digest = digest(self.prefix.read_bytes())
        self.raw = b'prepared candidate\n'
        self.review = json_bytes({'approved': False, 'installed': False, 'production_approved': False})
        self.engine = object()
        self.projection = SimpleNamespace(earnings_history=self.engine)

    def argv(self, **changes):
        values = {'--config': str(self.config), '--prefix': str(self.prefix),
                  '--prefix-sha256': self.prefix_digest, '--block': '250',
                  '--output': str(self.output), '--review-output': str(self.review_output)}
        values.update(changes)
        return [item for name, value in values.items() if value is not None for item in (name, str(value))]

    def invoke(self, argv=None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = CLI.main(self.argv() if argv is None else argv)
        return code, out.getvalue(), err.getvalue()

    def assert_not_started(self, argv):
        with patch.object(CLI, 'Projection') as projection, patch.object(CLI, 'prepare') as prepare, \
                patch.object(CLI, 'publish') as publish:
            code, out, err = self.invoke(argv)
        self.assertEqual(1, code)
        self.assertEqual('', out)
        self.assertIn('Inspect both requested output paths', err)
        projection.assert_not_called(); prepare.assert_not_called(); publish.assert_not_called()
        self.assertEqual(self.config_bytes, self.config.read_bytes())
        self.assertEqual(self.prefix_digest, digest(self.prefix.read_bytes()))

    def test_each_required_argument_is_enforced_before_any_projection(self):
        for option in ('--config', '--prefix', '--prefix-sha256', '--block', '--output', '--review-output'):
            with self.subTest(option=option), patch.object(CLI, 'Projection') as projection, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    CLI.main(self.argv(**{option: None}))
                self.assertEqual(2, failure.exception.code)
                projection.assert_not_called()

    def test_no_approval_installation_signing_or_http_switch_is_exposed(self):
        for flag in ('--approve', '--install', '--broadcast', '--sign', '--http'):
            with self.subTest(flag=flag), patch.object(CLI, 'Projection') as projection, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    CLI.main(self.argv()+[flag])
                self.assertEqual(2, failure.exception.code)
                projection.assert_not_called()

    def test_bad_prefix_digests_stop_before_config_or_rpc_work(self):
        for value in ('', 'a'*63, 'a'*65, 'A'*64, 'g'*64, '0x'+'a'*64, 'a'*63+'\n'):
            with self.subTest(value=value), patch.object(CLI, 'read_json') as read:
                self.assert_not_started(self.argv(**{'--prefix-sha256': value}))
                read.assert_not_called()

    def test_out_of_range_blocks_stop_before_config_or_rpc_work(self):
        for value in (0, -1, 1 << 63):
            with self.subTest(value=value), patch.object(CLI, 'read_json') as read:
                self.assert_not_started(self.argv(**{'--block': value}))
                read.assert_not_called()

    def test_existing_output_or_sidecar_is_preserved_before_config_or_rpc_work(self):
        for option, path in (('--output', self.output), ('--review-output', self.review_output)):
            with self.subTest(option=option):
                path.write_bytes(b'EXISTING ARTIFACT\n')
                with patch.object(CLI, 'read_json') as read:
                    self.assert_not_started(self.argv())
                    read.assert_not_called()
                self.assertEqual(b'EXISTING ARTIFACT\n', path.read_bytes())
                path.unlink()

    def test_output_aliases_and_missing_parents_are_rejected_before_reads(self):
        changes = ({'--review-output': self.output}, {'--output': self.prefix},
                   {'--review-output': self.prefix},
                   {'--output': self.root/'missing'/'candidate.json'},
                   {'--review-output': self.root/'missing'/'review.json'},
                   {'--review-output': self.root/'unused'/'..'/'candidate.json'})
        for change in changes:
            with self.subTest(change=change), patch.object(CLI, 'read_json') as read:
                self.assert_not_started(self.argv(**change))
                read.assert_not_called()

    def test_any_installed_checkpoint_key_is_rejected_before_projection(self):
        for installed in (None, {}, {'path': 'private-path', 'sha256': 'a'*64}):
            with self.subTest(installed=installed):
                self.config_bytes = json_bytes({'earnings_history': {'schema': 1, 'checkpoint': installed}})
                self.config.write_bytes(self.config_bytes)
                self.assert_not_started(self.argv())

    def test_missing_or_malformed_earnings_profile_never_constructs_projection(self):
        for config in (None, [], {}, {'earnings_history': None}, {'earnings_history': []}):
            with self.subTest(config=config):
                self.config_bytes = json_bytes(config)
                self.config.write_bytes(self.config_bytes)
                self.assert_not_started(self.argv())

    def test_build_budget_bounds_are_not_raised_or_silently_ignored(self):
        for option, value in (('--max-seconds', 0), ('--max-seconds', 3601),
                              ('--max-calls', 0), ('--max-calls', 65537),
                              ('--max-posts', 0), ('--max-posts', 65537)):
            with self.subTest(option=option, value=value), patch.object(CLI, 'read_json') as read:
                self.assert_not_started(self.argv(**{option: value}))
                read.assert_not_called()

    def test_success_uses_exact_inputs_utf8_and_prints_unapproved_pair_digests(self):
        original_reader = CLI.read_json
        with patch.object(CLI, 'read_json', wraps=original_reader) as read, \
                patch.object(CLI, 'Projection', return_value=self.projection) as projection, \
                patch.object(CLI, 'prepare', return_value=(self.raw, self.review)) as prepare, \
                patch.object(CLI, 'publish') as publish:
            code, out, err = self.invoke()
        self.assertEqual(0, code); self.assertEqual('', err)
        read.assert_called_once_with(self.config, encoding='utf-8')
        projection.assert_called_once_with(json.loads(self.config_bytes))
        self.assertEqual((self.engine, 250, {'path': str(self.prefix), 'sha256': self.prefix_digest}),
                         prepare.call_args.args)
        budget = prepare.call_args.kwargs['budget']
        self.assertIsInstance(budget, BuildBudget)
        self.assertEqual((4096, 8192), (budget.calls, budget.posts))
        publish.assert_called_once_with(self.output, self.review_output, self.raw, self.review)
        self.assertIn('Candidate SHA-256: '+digest(self.raw), out)
        self.assertIn('Import review SHA-256: '+digest(self.review), out)
        self.assertIn('Not approved or installed.', out)
        self.assertIn('full24-hour window', out)
        self.assertEqual(self.config_bytes, self.config.read_bytes())
        self.assertEqual(self.prefix_digest, digest(self.prefix.read_bytes()))

    def test_all_input_preparation_and_publication_share_existing_outer_budget(self):
        outer = work_budget.Budget(calls=4, posts=3)
        seen = []
        reader = CLI.read_json
        def consume(stage, kind):
            self.assertIs(outer, work_budget._current.get())
            seen.append(stage); work_budget.consume(kind)
        def read(*args, **kwargs):
            consume('input', 'calls'); return reader(*args, **kwargs)
        def projection(config):
            consume('projection', 'calls'); return self.projection
        def prepare(engine, number, prefix, *, budget):
            # A nested explicit BuildBudget must not replace tighter request work.
            with work_budget.request_scope(budget) as active:
                self.assertIs(outer, active); consume('prepare', 'posts')
            return self.raw, self.review
        def publish(*args):
            consume('publication', 'posts')
        with work_budget.request_scope(outer), patch.object(CLI, 'read_json', side_effect=read), \
                patch.object(CLI, 'Projection', side_effect=projection), \
                patch.object(CLI, 'prepare', side_effect=prepare), \
                patch.object(CLI, 'publish', side_effect=publish):
            code, _, err = self.invoke()
        self.assertEqual(0, code); self.assertEqual('', err)
        self.assertEqual(['input', 'projection', 'prepare', 'publication'], seen)
        self.assertEqual((2, 1), (outer.calls, outer.posts))

    def test_exhausted_outer_budget_cannot_be_refilled_by_cli_defaults(self):
        outer = work_budget.Budget(calls=1, posts=1)
        reader = CLI.read_json
        def read(*args, **kwargs):
            work_budget.consume('calls'); return reader(*args, **kwargs)
        def projection(config):
            work_budget.consume('calls'); self.fail('exhausted outer work was refilled')
        with work_budget.request_scope(outer), patch.object(CLI, 'read_json', side_effect=read), \
                patch.object(CLI, 'Projection', side_effect=projection), \
                patch.object(CLI, 'prepare') as prepare, patch.object(CLI, 'publish') as publish:
            code, _, err = self.invoke()
        self.assertEqual(1, code); self.assertIn('No artifact was approved or installed.', err)
        prepare.assert_not_called(); publish.assert_not_called()
        self.assertEqual(0, outer.calls)

    def test_errors_at_each_stage_are_sanitized_and_warn_of_possible_outputs(self):
        secret = 'SYNTHETIC_PRIVATE_ENDPOINT_AND_CREDENTIAL'
        for stage in ('read_json', 'Projection', 'prepare', 'publish'):
            for error in (OSError, ValueError, RpcError, KeyError, TypeError, RecursionError, WorkLimit):
                with self.subTest(stage=stage, error=error.__name__), \
                        patch.object(CLI, 'Projection', return_value=self.projection), \
                        patch.object(CLI, 'prepare', return_value=(self.raw, self.review)), \
                        patch.object(CLI, 'publish'), \
                        patch.object(CLI, stage, side_effect=error('rpc_budget' if error is WorkLimit else secret)):
                    code, out, err = self.invoke()
                    self.assertEqual(1, code); self.assertEqual('', out)
                    self.assertNotIn(secret, err)
                    self.assertIn('Inspect both requested output paths: unapproved artifacts may exist.', err)
                    self.assertIn('No artifact was approved or installed.', err)

    def test_late_publication_failure_keeps_artifacts_and_instructs_inspection(self):
        def publish(*args):
            self.review_output.write_bytes(self.review)
            raise OSError('synthetic sensitive path or endpoint')
        with patch.object(CLI, 'Projection', return_value=self.projection), \
                patch.object(CLI, 'prepare', return_value=(self.raw, self.review)), \
                patch.object(CLI, 'publish', side_effect=publish):
            code, _, err = self.invoke()
        self.assertEqual(1, code)
        self.assertEqual(self.review, self.review_output.read_bytes())
        self.assertFalse(self.output.exists())
        self.assertIn('Inspect both requested output paths', err)
        self.assertNotIn('sensitive', err)


class CheckpointPrefixImportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        owner = unittest.TestCase()
        cls.addClassCleanup(owner.doCleanups)
        fixture = fixture_helpers.EarningsCheckpointPrefixImportTests.fixture(owner)
        cls.prefix, cls.prefix_raw = fixture_helpers.approved_prefix(fixture, 1, 161)
        cls.raw, cls.review_raw = importer.prepare(fixture.projection().earnings_history, 250, cls.prefix)
        cls.document = json.loads(cls.raw)
        cls.review = json.loads(cls.review_raw)

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='popl-prefix-publication-test-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root/'candidate.json'
        self.sidecar = self.root/'review.json'

    def assert_unpublished(self, raw, review):
        with self.assertRaises((ValueError, OSError, RpcError)):
            importer.publish(self.output, self.sidecar, raw, review)
        self.assertFalse(self.output.exists()); self.assertFalse(self.sidecar.exists())

    def test_real_prepared_pair_publishes_exclusively_with_false_adoption_flags(self):
        pins = importer.publish(self.output, self.sidecar, self.raw, self.review_raw)
        self.assertEqual((digest(self.raw), digest(self.review_raw)), pins)
        self.assertEqual(self.raw, self.output.read_bytes())
        self.assertEqual(self.review_raw, self.sidecar.read_bytes())
        for flag in ('production_approved', 'approved', 'installed', 'ready_for_submission', 'transactions_submitted'):
            self.assertIs(False, self.review[flag])
        self.assertEqual(3, self.document['schema'])
        self.assertEqual(self.prefix['sha256'], self.document['previous_sha256'])
        self.assertEqual(self.prefix_raw, Path(self.prefix['path']).read_bytes())
        self.assertEqual(86400, self.review['earliest_served_timestamp']-self.review['target_anchor']['timestamp'])
        with self.assertRaises(FileExistsError):
            importer.publish(self.output, self.sidecar, self.raw, self.review_raw)
        self.assertEqual(self.raw, self.output.read_bytes())
        self.assertEqual(self.review_raw, self.sidecar.read_bytes())

    def test_existing_either_output_preserves_both_and_does_not_publish_other(self):
        for path in (self.output, self.sidecar):
            with self.subTest(path=path.name):
                path.write_bytes(b'ORIGINAL PRIVATE ARTIFACT\n')
                with self.assertRaises(FileExistsError):
                    importer.publish(self.output, self.sidecar, self.raw, self.review_raw)
                self.assertEqual(b'ORIGINAL PRIVATE ARTIFACT\n', path.read_bytes())
                self.assertFalse((self.sidecar if path == self.output else self.output).exists())
                path.unlink()

    def test_preflight_rejects_aliasing_prefix_or_outputs_and_missing_parents(self):
        cases = ((self.output, self.output), (self.prefix['path'], self.sidecar),
                 (self.output, self.prefix['path']), (self.root/'missing'/'c.json', self.sidecar))
        for output, review in cases:
            with self.subTest(output=str(output), review=str(review)), self.assertRaises((ValueError, OSError, RpcError)):
                importer.output_preflight(output, review, prefix_path=self.prefix['path'])
        self.assertEqual(self.prefix_raw, Path(self.prefix['path']).read_bytes())

    def test_producer_and_semantic_pins_must_match_before_any_publication(self):
        for field in ('producer_sources', 'output_semantic_sources'):
            audit = copy.deepcopy(self.review)
            key = next(iter(audit[field])); audit[field][key] = '0'*64
            with self.subTest(field=field):
                self.assert_unpublished(self.raw, json_bytes(audit))

    def test_every_false_adoption_flag_is_mandatory_and_cannot_be_true(self):
        for flag in ('production_approved', 'approved', 'installed', 'ready_for_submission', 'transactions_submitted'):
            for value in (True, 0, None, 'false'):
                audit = copy.deepcopy(self.review); audit[flag] = value
                with self.subTest(flag=flag, value=value):
                    self.assert_unpublished(self.raw, json_bytes(audit))
            audit = copy.deepcopy(self.review); del audit[flag]
            with self.subTest(flag=flag, missing=True):
                self.assert_unpublished(self.raw, json_bytes(audit))

    def test_candidate_digest_and_prefix_anchor_identity_cannot_be_detached(self):
        audit = copy.deepcopy(self.review); audit['checkpoint_sha256'] = '0'*64
        self.assert_unpublished(self.raw, json_bytes(audit))
        for field, replacement in (('previous_sha256', '0'*64), ('schema', 2), ('anchor', {}), ('sources', {})):
            data = copy.deepcopy(self.document); data[field] = replacement
            raw = json_bytes(data)
            audit = copy.deepcopy(self.review); audit['checkpoint_sha256'] = digest(raw)
            with self.subTest(field=field):
                self.assert_unpublished(raw, json_bytes(audit))

    def test_byte_type_and_bounded_candidate_review_size_precede_publication(self):
        self.assert_unpublished(self.raw.decode('utf-8'), self.review_raw)
        self.assert_unpublished(self.raw, self.review_raw.decode('utf-8'))
        with patch.object(importer, 'MAX_BYTES', len(self.raw)-1):
            self.assert_unpublished(self.raw, self.review_raw)
        with patch.object(importer, 'MAX_REVIEW_BYTES', len(self.review_raw)-1):
            self.assert_unpublished(self.raw, self.review_raw)

    def test_review_graph_counts_identity_and_full_day_retention_cannot_be_edited(self):
        mutations = []
        for field, value in (('target_graph_length', self.review['target_graph_length']+1),
                              ('prefix_graph_length', self.review['prefix_graph_length']-1),
                              ('earliest_served_timestamp', self.review['earliest_served_timestamp']-1),
                              ('raw_retention_required', False), ('target_graph', [])):
            audit = copy.deepcopy(self.review); audit[field] = value
            mutations.append((field, audit))
        audit = copy.deepcopy(self.review)
        audit['target_graph'][0]['deployment']['contracts']['access']['address'] = '0x'+'0'*40
        mutations.append(('target_graph controller', audit))
        for label, audit in mutations:
            with self.subTest(field=label):
                self.assert_unpublished(self.raw, json_bytes(audit))

    def test_appended_proof_controller_transaction_count_and_order_are_bound(self):
        mutations = []
        for field, value in (('source_controller', '0x'+'0'*40),
                              ('destination_controller', '0x'+'0'*40),
                              ('retirement_transaction_hash', '0x'+'0'*64),
                              ('block_number', self.review['input_anchor']['number']-1),
                              ('timestamp', self.review['input_anchor']['timestamp']-1),
                              ('block_hash', 'NOT A HASH'), ('handoff_id', '0x1'),
                              ('state_root', None)):
            audit = copy.deepcopy(self.review); audit['appended_handoffs'][0][field] = value
            mutations.append((field, audit))
        audit = copy.deepcopy(self.review); audit['appended_handoffs'] = []
        mutations.append(('missing proof', audit))
        audit = copy.deepcopy(self.review); audit['appended_handoffs'] *= 2
        mutations.append(('duplicate proof', audit))
        audit = copy.deepcopy(self.review); audit['appended_handoffs'][0]['unknown'] = 'extra'
        mutations.append(('unknown proof field', audit))
        for label, audit in mutations:
            with self.subTest(field=label):
                self.assert_unpublished(self.raw, json_bytes(audit))

    def test_sidecar_integer_aliases_unknown_fields_and_anchor_aliases_are_rejected(self):
        for field in ('schema', 'prefix_schema', 'prefix_graph_length', 'target_graph_length',
                      'imported_cursor', 'earliest_served_timestamp'):
            for value in (True, str(self.review[field]), float(self.review[field])):
                audit = copy.deepcopy(self.review); audit[field] = value
                with self.subTest(field=field, value=value):
                    self.assert_unpublished(self.raw, json_bytes(audit))
        for field in ('input_anchor', 'authenticated_graph_snapshot'):
            audit = copy.deepcopy(self.review); audit[field]['number'] = True
            with self.subTest(field=field):
                self.assert_unpublished(self.raw, json_bytes(audit))
        audit = copy.deepcopy(self.review); audit['unexpected_approval'] = True
        self.assert_unpublished(self.raw, json_bytes(audit))
        audit = copy.deepcopy(self.review); del audit['trust']
        self.assert_unpublished(self.raw, json_bytes(audit))

    def test_prepared_serialization_cannot_be_reformatted_before_publication(self):
        changed_candidate = json.dumps(self.document, indent=2).encode('utf-8')
        audit = copy.deepcopy(self.review); audit['checkpoint_sha256'] = digest(changed_candidate)
        self.assert_unpublished(changed_candidate, json_bytes(audit))
        changed_review = json.dumps(self.review, indent=2).encode('utf-8')
        self.assert_unpublished(self.raw, changed_review)

    def test_late_candidate_collision_preserves_first_sidecar_and_other_file(self):
        actual_publish = importer.publish_candidate
        calls = []
        def collide(path, raw):
            calls.append(Path(path))
            if Path(path) == self.output:
                self.output.write_bytes(b'OTHER WRITER\n')
            return actual_publish(path, raw)
        with patch.object(importer, 'publish_candidate', side_effect=collide):
            with self.assertRaises(FileExistsError):
                importer.publish(self.output, self.sidecar, self.raw, self.review_raw)
        self.assertEqual([self.sidecar, self.output], calls)
        self.assertEqual(self.review_raw, self.sidecar.read_bytes())
        self.assertIs(False, json.loads(self.sidecar.read_bytes())['approved'])
        self.assertEqual(b'OTHER WRITER\n', self.output.read_bytes())
        self.assertEqual(self.prefix_raw, Path(self.prefix['path']).read_bytes())


if __name__ == '__main__':
    unittest.main()
